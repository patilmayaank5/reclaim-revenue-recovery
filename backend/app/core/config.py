"""Application configuration via pydantic-settings.

Follows 12-factor app principles. All configuration is loaded from
environment variables with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.

    Values are loaded from environment variables.
    A .env file is supported for local development.
    """

    # Application
    PROJECT_NAME: str = "Reclaim"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/reclaim"

    # AI
    ANTHROPIC_API_KEY: str | None = None
    AI_MODEL: str = "claude-3-5-sonnet-latest"
    AI_MAX_TOKENS: int = 1024

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # Execution Providers
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None
    EXECUTION_DEFAULT_PROVIDER: str = "simulator"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
