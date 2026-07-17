"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings read from the environment or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ImobiManager"
    database_url: str
    test_database_url: str = ""
    secret_key: str = "dev-only-placeholder-override-SECRET_KEY-in-production"
    # CORS allowlist. Default permits the Vite dev server origin. In
    # production, set via the CORS_ORIGINS env var (comma-separated or JSON
    # array) to the real frontend origin(s).
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
