from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    jwt_secret: str
    ai_provider: str = "hermes"
    hermes_agent_url: str = "https://apihermes.fbautomacao.space"
    hermes_agent_path: str = "/chat"
    hermes_agent_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    telegram_bot_token: str = ""
    redis_url: str = ""
    access_token_expire_minutes: int = 1440
    bootstrap_token: str = "hermes-bootstrap"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
