"""Configurações da aplicação carregadas de variáveis de ambiente."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações tipadas da aplicação."""

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/library.db"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a instância única de Settings (cacheada)."""
    return Settings()


settings = get_settings()
