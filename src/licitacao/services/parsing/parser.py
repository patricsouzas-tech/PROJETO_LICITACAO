"""Parser rastreável e determinístico (ETAPA 02).

Converte TrechoDocumento já ingeridos em Lote -> Item -> RequisitoTecnico,
preservando a evidência exata de origem em EvidenciaParsing e garantindo
idempotência via fingerprint. Não inventa dados ausentes.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...db.models import (
    DocumentoFonte,
    EntidadeTipo,
    EvidenciaParsing,
    ExecucaoParsing,
    Item,
    Lote,
    RequisitoTecnico,
    StatusParsing,
    TrechoDocumento,
    _fingerprint,
)
from ...domain import enums
from .detectors import (
    detectar_cabecalho_tabela,
    detectar_item_forte,
    detectar_item_fraco,
    detectar_lote,
    extrair_quantidade_unidade,
)
from .normalizers import normalizar_numero_br, normalizar_texto_requisito
from .units import normalizar_unidade

_DOCUMENTOS_ELEGIVEIS = {
    enums.TipoDocumento.EDITAL,
    enums.TipoDocumento.TERMO_REFERENCIA,
    enums.TipoDocumento.ANEXO,
    enums.TipoDocumento.PLANILHA,
}


def _split_celulas(texto: str) -> list[str]:
    return [c for c in (texto or "").split("\n") if c.strip()]


class ParserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._lote_atual: Lote | None = None
        self._item_atual: Item | None = None
        self._header_tabela: dict | None = None
        self._header_doc_id: int | None = None

    def processar(self, licitacao_id: int) -> ExecucaoParsing:
        execucao = ExecucaoParsing(licitacao_id=licitacao_id)
        self.db.add(execucao)
        self.db.flush()

        documentos = (
            self.db.query(DocumentoFonte)
            .filter(DocumentoFonte.licitacao_id == licitacao_id)
            .order_by(DocumentoFonte.id)
            .all()
        )

        ocr_pendentes: list[int] = []
        processados = 0
        for doc in documentos:
            if doc.tipo_documento not in _DOCUMENTOS_ELEGIVEIS:
                continue
            if doc.status_processamento == enums.StatusProcessamento.ERRO:
                continue
            if doc.status_processamento == enums.StatusProcessamento.OCR_REQUIRED:
                ocr_pendentes.append(doc.id)
                continue

            trechos = (
                self.db.query(TrechoDocumento)
                .filter(TrechoDocumento.documento_id == doc.id)
                .order_by(TrechoDocumento.ordem)
                .all()
            )
            for trecho in trechos:
                self._processar_trecho(licitacao_id, doc.id, trecho)
            processados += 1

        execucao.documentos_processados = processados
        execucao.lotes_criados = (
            self.db.query(Lote).filter(Lote.licitacao_id == licitacao_id).count()
        )
        execucao.itens_criados = (
            self.db.query(Item)
            .join(Lote)
            .filter(Lote.licitacao_id == licitacao_id)
            .count()
        )
        execucao.requisitos_criados = (
            self.db.query(RequisitoTecnico)
            .join(Item)
            .join(Lote)
            .filter(Lote.licitacao_id == licitacao_id)
            .count()
        )
        execucao.concluido_em = datetime.now(timezone.utc)
        if ocr_pendentes:
            execucao.status = StatusParsing.PARCIAL
            execucao.erros = (
                "Documentos requerem OCR e foram ignorados: "
                + ", ".join(str(i) for i in ocr_pendentes)
            )
        else:
            execucao.status = StatusParsing.CONCLUIDO
        execucao.resumo = (
            f"docs={processados} lotes={execucao.lotes_criados} "
            f"itens={execucao.itens_criados} requisitos={execucao.requisitos_criados}"
        )
        self.db.commit()
        self.db.refresh(execucao)
        return execucao

    def _processar_trecho(self, licitacao_id: int, doc_id: int, trecho: TrechoDocumento) -> None:
        texto = trecho.texto_bruto or ""

        # 1) cabeçalho de tabela
        celulas = _split_celulas(texto)
        if len(celulas) >= 2:
            header = detectar_cabecalho_tabela([c for c in celulas if c is not None])
            if header:
                self._header_tabela = header
                self._header_doc_id = doc_id
                return

        # 2) dados de tabela (linha após cabeçalho)
        if self._header_tabela is not None and self._header_doc_id == doc_id and len(celulas) >= 2:
            self._processar_linha_tabela(licitacao_id, doc_id, trecho, celulas)
            return

        # 3) lote
        ok_lote, num_lote, raw_lote = detectar_lote(texto)
        if ok_lote:
            self._lote_atual = self._upsert_lote(
                licitacao_id, num_lote, doc_id, trecho.id, titulo=raw_lote
            )
            self._item_atual = None
            self._header_tabela = None
            return

        # 4) item forte
        ok_item, num_item = detectar_item_forte(texto)
        if ok_item:
            resto = self._resto_apos_cabecalho(texto, r"ITEM\b[\s:.\-]*?(N[º°]\.?\s*)?[0-9]+\b")
            self._item_atual = self._upsert_item(
                licitacao_id, num_item, doc_id, trecho.id, descricao=resto
            )
            self._header_tabela = None
            return

        # 5) item fraco (somente com contexto)
        ok_fraco, num_fraco = detectar_item_fraco(texto)
        if ok_fraco and (self._item_atual is not None or len(resto := texto.strip()) > 3):
            self._item_atual = self._upsert_item(
                licitacao_id, num_fraco, doc_id, trecho.id, descricao=resto
            )
            self._header_tabela = None
            return

        # 6) quantidade / unidade do item atual
        if self._item_atual is not None:
            val, un = extrair_quantidade_unidade(texto)
            if val:
                dec = normalizar_numero_br(val)
                if dec is not None:
                    self._item_atual.quantidade = dec
                    self._registrar_evidencia(
                        licitacao_id, EntidadeTipo.ITEM, self._item_atual.id,
                        "quantidade", doc_id, trecho.id, val,
                    )
            if un:
                orig, norm = normalizar_unidade(un)
                self._item_atual.unidade = orig
                self._item_atual.unidade_original = orig
                self._item_atual.unidade_normalizada = norm
                self._registrar_evidencia(
                    licitacao_id, EntidadeTipo.ITEM, self._item_atual.id,
                    "unidade", doc_id, trecho.id, un,
                )

            # 7) especificação -> requisito (apenas trechos subsequentes ao item)
            if texto.strip() and not val and not un:
                self._upsert_requisito(
                    licitacao_id, self._item_atual.id, doc_id, trecho.id, texto
                )

    def _processar_linha_tabela(
        self, licitacao_id: int, doc_id: int, trecho: TrechoDocumento, celulas: list
    ) -> None:
        h = self._header_tabela

        def get(nome):
            return celulas[h[nome]] if nome in h and h[nome] < len(celulas) else None

        num = get("ITEM") or get("NUMERO") or get("CODIGO")
        desc = get("DESCRICAO")
        qtd = get("QUANTIDADE")
        un = get("UNIDADE")
        if num is None and desc is None:
            return
        numero = re.sub(r"\D", "", str(num or "")) or "1"
        item = self._upsert_item(
            licitacao_id, numero, doc_id, trecho.id, descricao=(desc or "").strip()
        )
        if qtd:
            dec = normalizar_numero_br(qtd)
            if dec is not None:
                item.quantidade = dec
                self._registrar_evidencia(
                    licitacao_id, EntidadeTipo.ITEM, item.id,
                    "quantidade", doc_id, trecho.id, qtd,
                )
        if un:
            orig, norm = normalizar_unidade(un)
            item.unidade = orig
            item.unidade_original = orig
            item.unidade_normalizada = norm

    def _resto_apos_cabecalho(self, texto: str, padrao: str) -> str:
        m = re.search(padrao, texto, re.IGNORECASE)
        if not m:
            return texto.strip()
        resto = texto[m.end():]
        resto = re.sub(r"^[\s\-–)\.:]+", "", resto)
        return resto.strip()

    def _upsert_lote(
        self, licitacao_id, numero, doc_id, trecho_id, titulo=None, sintetico=False
    ) -> Lote:
        fp = _fingerprint(
            str(licitacao_id), "LOTE", str(numero), str(doc_id or ""),
            str(trecho_id or ""), "S" if sintetico else "",
        )
        exist = (
            self.db.query(Lote)
            .filter(Lote.licitacao_id == licitacao_id, Lote.fingerprint == fp)
            .first()
        )
        if exist:
            if titulo:
                exist.titulo = titulo
            exist.sintetico = sintetico
            lote = exist
        else:
            lote = Lote(
                licitacao_id=licitacao_id,
                numero=str(numero),
                titulo=titulo,
                sintetico=sintetico,
                documento_origem_id=doc_id,
                trecho_origem_id=trecho_id,
                fingerprint=fp,
            )
            self.db.add(lote)
            self.db.flush()
        self._registrar_evidencia(
            licitacao_id, EntidadeTipo.LOTE, lote.id, "numero",
            doc_id, trecho_id, str(numero),
        )
        return lote

    def _upsert_item(
        self, licitacao_id, numero, doc_id, trecho_id, descricao=None
    ) -> Item:
        if self._lote_atual is None:
            self._lote_atual = self._upsert_lote_sintetico(licitacao_id, doc_id, trecho_id)
        lote = self._lote_atual
        fp = _fingerprint(
            str(licitacao_id), str(lote.id), "ITEM", str(numero),
            str(doc_id or ""), str(trecho_id or ""),
        )
        exist = (
            self.db.query(Item)
            .filter(Item.lote_id == lote.id, Item.fingerprint == fp)
            .first()
        )
        if exist:
            if descricao:
                exist.descricao_original = descricao
            item = exist
        else:
            item = Item(
                lote_id=lote.id,
                numero=str(numero),
                descricao_original=descricao,
                documento_origem_id=doc_id,
                trecho_origem_id=trecho_id,
                fingerprint=fp,
            )
            self.db.add(item)
            self.db.flush()
        self._registrar_evidencia(
            licitacao_id, EntidadeTipo.ITEM, item.id, "numero",
            doc_id, trecho_id, str(numero),
        )
        if descricao:
            self._registrar_evidencia(
                licitacao_id, EntidadeTipo.ITEM, item.id, "descricao_original",
                doc_id, trecho_id, descricao,
            )
        return item

    def _upsert_lote_sintetico(self, licitacao_id, doc_id, trecho_id) -> Lote:
        fp = _fingerprint(str(licitacao_id), "LOTE", "UNICO-SINTETICO")
        exist = (
            self.db.query(Lote)
            .filter(Lote.licitacao_id == licitacao_id, Lote.fingerprint == fp)
            .first()
        )
        if exist:
            return exist
        lote = Lote(
            licitacao_id=licitacao_id,
            numero="UNICO",
            titulo="Lote técnico sem identificação explícita no documento",
            sintetico=True,
            fingerprint=fp,
        )
        self.db.add(lote)
        self.db.flush()
        return lote

    def _upsert_requisito(self, licitacao_id, item_id, doc_id, trecho_id, texto) -> None:
        normalizado = normalizar_texto_requisito(texto)
        if not normalizado:
            return
        if re.search(r"(?i)observa[çc][ãa]o|exemplo|informa[çc][õo]es comerciais", normalizado):
            return
        fp = _fingerprint(
            str(licitacao_id), str(item_id), "REQUISITO",
            str(trecho_id or ""), normalizado,
        )
        exist = (
            self.db.query(RequisitoTecnico)
            .filter(RequisitoTecnico.item_id == item_id, RequisitoTecnico.fingerprint == fp)
            .first()
        )
        if exist:
            return
        req = RequisitoTecnico(
            item_id=item_id,
            texto_original=normalizado,
            texto_normalizado=normalizado,
            obrigatorio=True,
            documento_origem_id=doc_id,
            trecho_origem_id=trecho_id,
            fingerprint=fp,
        )
        self.db.add(req)
        self.db.flush()
        self._registrar_evidencia(
            licitacao_id, EntidadeTipo.REQUISITO, req.id, "texto_original",
            doc_id, trecho_id, normalizado,
        )

    def _registrar_evidencia(
        self, licitacao_id, entidade_tipo, entidade_id, campo,
        doc_id, trecho_id, texto
    ) -> None:
        fp = _fingerprint(
            str(licitacao_id), entidade_tipo.value, str(entidade_id),
            campo, str(doc_id or ""), str(trecho_id or ""), str(texto),
        )
        exist = (
            self.db.query(EvidenciaParsing)
            .filter(EvidenciaParsing.fingerprint == fp)
            .first()
        )
        if exist:
            return
        ev = EvidenciaParsing(
            licitacao_id=licitacao_id,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            campo=campo,
            documento_id=doc_id,
            trecho_id=trecho_id,
            ordem=0,
            texto_evidencia=str(texto),
            fingerprint=fp,
        )
        self.db.add(ev)
        self.db.flush()
