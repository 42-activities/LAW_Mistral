from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    api_key_header: str = "X-API-Key"
    environment: str = "local"
    # LLM (spec §5). No key → summaries fall back to the deterministic template, NL Q&A is off.
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"
    mistral_base_url: str = "https://api.mistral.ai/v1"
    llm_timeout_s: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
