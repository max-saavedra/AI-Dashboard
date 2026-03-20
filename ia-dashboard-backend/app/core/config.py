"""
app/core/config.py

Centralised settings loaded from environment variables.
All secrets must be stored in .env (never committed to version control).
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings resolved from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_env: str = Field(default="development")
    app_secret_key: str = Field(default="insecure-dev-key")
    app_debug: bool = Field(default=False)
    allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # ------------------------------------------------------------------ #
    # AI providers
    # ------------------------------------------------------------------ #
    gemini_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    ai_primary_provider: str = Field(default="gemini")
    ai_timeout_seconds: int = Field(default=8)
    ai_fallback_enabled: bool = Field(default=True)

    # ------------------------------------------------------------------ #
    # Database (Supabase / PostgreSQL)
    # ------------------------------------------------------------------ #
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    database_url: str = Field(default="")

    # ------------------------------------------------------------------ #
    # File upload
    # ------------------------------------------------------------------ #
    max_file_size_mb: int = Field(default=10)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    # ------------------------------------------------------------------ #
    # Session / persistence
    # ------------------------------------------------------------------ #
    anon_data_ttl_hours: int = Field(default=24)
    session_inactivity_minutes: int = Field(default=30)

    def has_ai_providers(self) -> tuple[bool, bool]:
        """
        Check if AI providers are configured.
        Returns (has_gemini, has_openai).
        """
        has_gemini = bool(self.gemini_api_key and self.gemini_api_key.strip())
        has_openai = bool(self.openai_api_key and self.openai_api_key.strip())
        return has_gemini, has_openai


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of Settings."""
    return Settings()
