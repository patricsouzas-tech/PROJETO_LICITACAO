"""Conftest: prepara banco de testes SQLite em arquivo temporario e sessao."""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_licitacao.db")
os.environ.setdefault("DATA_DIR", "./data/test_documentos")

from licitacao.db.base import Base  # noqa: E402
from licitacao.db.session import SessionLocal, engine  # noqa: E402


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
