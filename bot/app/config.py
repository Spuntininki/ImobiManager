"""Bot configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings read from the environment or a local `.env` file.

    The bot pod never sees `DATABASE_URL`: it reaches the backend over HTTP
    only (admin/MCP/auth/logs), keeping the pod isolated from the data layer.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Telegram ---
    telegram_bot_token: str
    telegram_polling_timeout: int = 30
    telegram_polling_error_backoff: float = 5.0

    # --- Backend (HTTP only) ---
    bot_backend_base_url: str = "http://backend:8000"
    bot_mcp_api_key: str

    # --- Auth cache ---
    bot_validate_cache_ttl: int = 60

    # --- Message log publisher ---
    bot_log_flush_interval: float = 30.0
    bot_log_flush_batch_size: int = 100

    # --- OpenRouter (OpenAI-compatible) ---
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"

    # --- Rate limits (hard reject) ---
    bot_rate_limit_user_per_min: int = 10
    bot_rate_limit_user_per_day: int = 200
    bot_rate_limit_renter_per_min: int = 5
    bot_rate_limit_renter_per_day: int = 50
    bot_rate_limit_chat_per_min: int = 15


settings = Settings()
