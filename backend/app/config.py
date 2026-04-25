from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://agente:agente@db:5432/agente_saas"

    jwt_secret: str = "troque-este-segredo"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 dias

    # LLM (OpenAI-compatible: OpenRouter, DeepSeek, etc.)
    llm_api_key: str = ""
    llm_api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    llm_model: str = "deepseek/deepseek-chat"
    llm_provider: str = "openrouter"  # apenas para registro em usage_logs

    # OpenRouter pede esses headers (opcional, mas recomendado)
    openrouter_referer: str = "https://meuchat.fbautomacao.space"
    openrouter_title: str = "Hermes Agente SaaS"

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    # WhatsApp
    whatsapp_api_url: str = ""
    whatsapp_api_token: str = ""
    whatsapp_verify_token: str = ""

    cors_origins: str = (
        "http://localhost:5173,"
        "http://localhost:8080,"
        "https://meuchat.fbautomacao.space"
    )
    environment: str = "development"

    initial_credits: int = 10000

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
