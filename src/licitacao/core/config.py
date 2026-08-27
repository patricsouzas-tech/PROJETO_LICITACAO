import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./data/licitacao.db"
        )
        self.data_dir: str = os.getenv("DATA_DIR", "./data/documentos")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
