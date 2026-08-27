from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings


def _preparar_db_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        caminho = database_url.replace("sqlite:///", "", 1)
        if caminho and not caminho.startswith(":") and not caminho.startswith("/"):
            p = Path(caminho)
            if p.is_absolute() is False:
                p = Path.cwd() / p
            p.parent.mkdir(parents=True, exist_ok=True)
    return database_url


_db_url = _preparar_db_url(settings.database_url)

engine = create_engine(
    _db_url,
    connect_args=(
        {"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {}
    ),
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
