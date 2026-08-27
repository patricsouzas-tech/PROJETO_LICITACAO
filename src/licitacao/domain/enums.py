from enum import Enum


class TipoDocumento(str, Enum):
    EDITAL = "EDITAL"
    TERMO_REFERENCIA = "TERMO_REFERENCIA"
    ANEXO = "ANEXO"
    PLANILHA = "PLANILHA"
    OUTRO = "OUTRO"


class StatusProcessamento(str, Enum):
    RECEBIDO = "RECEBIDO"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    OCR_REQUIRED = "OCR_REQUIRED"
    ERRO = "ERRO"


class TipoLocalizador(str, Enum):
    PAGINA = "PAGINA"
    PARAGRAFO = "PARAGRAFO"
    CELULA = "CELULA"
    TABELA = "TABELA"


class CondicaoProduto(str, Enum):
    NOVO = "NOVO"
    USADO = "USADO"
    RECONDICIONADO = "RECONDICIONADO"
    NAO_CONFIRMADO = "NAO_CONFIRMADO"


class SimNaoConfirmado(str, Enum):
    SIM = "SIM"
    NAO = "NAO"
    NAO_CONFIRMADO = "NAO_CONFIRMADO"


class NotaFiscal(str, Enum):
    SIM = "SIM"
    NAO = "NAO"
    NAO_CONFIRMADO = "NAO_CONFIRMADO"


class Marketplace(str, Enum):
    MERCADO_LIVRE = "MERCADO_LIVRE"
    OLX = "OLX"
    ENJOEI = "ENJOEI"
    OUTRO = "OUTRO"


class ValidacaoResultado(str, Enum):
    ATENDE = "ATENDE"
    NAO_ATENDE = "NAO_ATENDE"
    NAO_COMPROVADO = "NAO_COMPROVADO"


class EntidadeTipo(str, Enum):
    LOTE = "LOTE"
    ITEM = "ITEM"
    REQUISITO = "REQUISITO"


class StatusParsing(str, Enum):
    INICIADO = "INICIADO"
    CONCLUIDO = "CONCLUIDO"
    PARCIAL = "PARCIAL"
    ERRO = "ERRO"
