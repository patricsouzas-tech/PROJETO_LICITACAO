"""Testes de integracao da API (ETAPA 01B)."""


def test_health_seguro(api_client):
    r = api_client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok"}
    # nao deve vazar configuracoes internas
    assert "database_url" not in r.text
    assert "DATABASE_URL" not in r.text


def test_criar_e_obter_licitacao(api_client):
    r = api_client.post(
        "/api/v1/licitacoes",
        json={"titulo": "Edital API", "numero_processo": "999/2026"},
    )
    assert r.status_code == 201
    lic = r.json()
    assert lic["id"] >= 1

    r2 = api_client.get(f"/api/v1/licitacoes/{lic['id']}")
    assert r2.status_code == 200
    assert r2.json()["titulo"] == "Edital API"


def test_listar_licitacoes(api_client):
    api_client.post("/api/v1/licitacoes", json={"titulo": "L1"})
    api_client.post("/api/v1/licitacoes", json={"titulo": "L2"})
    r = api_client.get("/api/v1/licitacoes")
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_obter_licitacao_404(api_client):
    r = api_client.get("/api/v1/licitacoes/999999")
    assert r.status_code == 404


def test_upload_documento_e_trechos(api_client):
    r = api_client.post(
        "/api/v1/licitacoes",
        json={"titulo": "Edital com upload"},
    )
    lic_id = r.json()["id"]

    conteudo = "Item 1: cadeira.\nItem 2: mesa.".encode("utf-8")
    r = api_client.post(
        f"/api/v1/licitacoes/{lic_id}/documentos",
        files={"arquivo": ("TERMO DE REFERENCIA.txt", conteudo, "text/plain")},
        data={"tipo_documento": "TERMO_REFERENCIA"},
    )
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "CONCLUIDO"
    assert res["trechos_criados"] >= 1
    doc_id = res["documento_id"]

    # nome_original preservado (nao nome temporario)
    rd = api_client.get(f"/api/v1/documentos/{doc_id}")
    assert rd.status_code == 200
    assert rd.json()["nome_original"] == "TERMO DE REFERENCIA.txt"

    rt = api_client.get(f"/api/v1/documentos/{doc_id}/trechos")
    assert rt.status_code == 200
    assert len(rt.json()) == res["trechos_criados"]


def test_listar_documentos(api_client):
    r = api_client.post("/api/v1/licitacoes", json={"titulo": "Doc list"})
    lic_id = r.json()["id"]
    api_client.post(
        f"/api/v1/licitacoes/{lic_id}/documentos",
        files={"arquivo": ("e.txt", b"texto", "text/plain")},
        data={"tipo_documento": "EDITAL"},
    )
    r = api_client.get(f"/api/v1/licitacoes/{lic_id}/documentos")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_documento_404(api_client):
    r = api_client.get("/api/v1/documentos/999999")
    assert r.status_code == 404
