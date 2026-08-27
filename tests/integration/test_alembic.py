"""Teste de migration Alembic isolado (nao depende de create_all)."""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

TABELAS_ESPERADAS = [
    "licitacao",
    "documento_fonte",
    "trecho_documento",
    "lote",
    "item",
    "requisito_tecnico",
    "produto_candidato",
    "oferta",
    "validacao_requisito",
]


def _run(args, url):
    env = dict(os.environ)
    env["DATABASE_URL"] = url
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(ROOT),
        env=env,
        check=True,
        capture_output=True,
    )


def test_alembic_upgrade_downgrade_upgrade():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()
    url = f"sqlite:///{db_path}"

    _run(["upgrade", "head"], url)
    conn = sqlite3.connect(db_path)
    tabelas = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    for t in TABELAS_ESPERADAS:
        assert t in tabelas, f"tabela ausente apos upgrade: {t}"

    _run(["downgrade", "base"], url)
    conn = sqlite3.connect(db_path)
    tabelas_pos = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    for t in TABELAS_ESPERADAS:
        assert t not in tabelas_pos, f"tabela nao removida no downgrade: {t}"

    _run(["upgrade", "head"], url)
    conn = sqlite3.connect(db_path)
    tabelas_final = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert "licitacao" in tabelas_final
