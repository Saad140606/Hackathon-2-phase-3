"""Configuration management using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    # Provide a development default so Spaces can build without secrets.
    # Use synchronous sqlite driver to avoid async driver initialization during
    # the build/startup phase (avoids greenlet_spawn errors).
    # In production, set `DATABASE_URL` in the environment or Spaces secret.
    database_url: str = "sqlite:///./dev.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # JWT Authentication
    # Provide a non-sensitive default for development. Replace with a secure
    # secret via environment variables in production (e.g., Spaces secrets).
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15  # Short-lived access tokens
    jwt_refresh_expiration_hours: int = 168  # Longer refresh tokens
    bcrypt_rounds: int = 12

    # Security
    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    csrf_token_header_name: str = "x-csrf-token"
    csrf_secret: str = ""

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # in seconds

    # Debug
    debug: bool = False

    # Logging
    log_level: str = "info"

    # OpenAI Configuration
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Cohere Configuration (optional - used when COHERE_API_KEY is provided)
    cohere_api_key: str | None = None
    cohere_model: str = "xlarge"

    # MCP Server
    mcp_base_url: str = "http://localhost:8001"
    # Allow frontend to provide a public API URL (optional, used in dev)
    next_public_api_url: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
