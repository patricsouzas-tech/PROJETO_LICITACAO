from pathlib import Path

from licitacao.services.ingestion.ingest import _sanitizar_nome, _sha256_arquivo


def test_sanitiza_path_traversal_unix():
    assert _sanitizar_nome("../../evil.pdf") == "evil.pdf"


def test_sanitiza_path_traversal_windows():
    assert _sanitizar_nome(r"..\..\evil.pdf") == "evil.pdf"


def test_sanitiza_caminho_absoluto_windows():
    assert _sanitizar_nome(r"C:\Windows\System32\evil.pdf") == "evil.pdf"


def test_sanitiza_caracteres_perigosos():
    nome = _sanitizar_nome("arq/../../x*:?nome.pdf")
    assert "/" not in nome
    assert "\\" not in nome
    assert ".." not in nome


def test_sha256_deterministico(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"conteudo unico")
    b.write_bytes(b"conteudo unico")
    assert _sha256_arquivo(a) == _sha256_arquivo(b)


def test_sha256_muda_com_conteudo(tmp_path: Path):
    a = tmp_path / "a.txt"
    a.write_bytes(b"conteudo A")
    b = tmp_path / "b.txt"
    b.write_bytes(b"conteudo B bem diferente")
    assert _sha256_arquivo(a) != _sha256_arquivo(b)
