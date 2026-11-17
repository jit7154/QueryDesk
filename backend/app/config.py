from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql://querydesk_user:querydesk_password@localhost:5432/querydesk"
    )
    database_readonly_url: str = (
        "postgresql://querydesk_ro:querydesk_ro_password@localhost:5432/querydesk"
    )
    gemini_api_key: str = ""
    llm_model: str = "gemini-3.5-flash-lite"
    embedding_model: str = "models/gemini-embedding-001"
    embedding_dim: int = 768
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    environment: str = "development"
    port: int = 8000

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list of strings."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
