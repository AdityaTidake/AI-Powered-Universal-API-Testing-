"""
Application configuration using pydantic-settings.
All values are loaded from environment variables or .env file.
Use `settings` singleton throughout the application.

SOLID Principle: Single Responsibility — this class only holds config values and their validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ─── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "SpecGuard AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ─── Database (MongoDB via Motor + Beanie) ─────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "specguard"

    # ─── Cache (Redis) ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── JWT Authentication ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "changeme-generate-a-real-jwt-secret-at-least-64-chars-long-for-safety"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── AI Provider ─────────────────────────────────────────────────────────
    # "gemini"  = Google Gemini (cloud).
    # "ollama"  = local Ollama model (cost-free for dev).
    # "auto"    = use Gemini if API key is set, else Ollama.
    AI_PROVIDER: Literal["gemini", "ollama", "auto"] = "auto"
    AI_MAX_RETRIES: int = 3

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # Ollama (local LLM — cost-free for dev)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # LLM Usage Monitoring
    LLM_USAGE_LOG_ENABLED: bool = True

    # ─── Test Execution ───────────────────────────────────────────────────────
    MAX_CONCURRENT_TESTS: int = 50
    REQUEST_TIMEOUT_SECONDS: float = 30.0

    # ─── Reports ──────────────────────────────────────────────────────────────
    REPORT_OUTPUT_DIR: str = "./reports"

    # ─── Security (legacy API key — kept for CI/CD compatibility) ────────────
    SECRET_KEY: str = "changeme-generate-a-real-secret-key-at-least-32-chars"
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY: str = ""

    # ─── Async Worker (Celery + Redis) ────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ─── Usage / Plan Limits ──────────────────────────────────────────────────
    FREE_PLAN_MONTHLY_RUNS: int = 10
    FREE_PLAN_MAX_ENDPOINTS: int = 20
    PRO_PLAN_MONTHLY_RUNS: int = 500

    # ─── Validators ───────────────────────────────────────────────────────────
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("MAX_CONCURRENT_TESTS")
    @classmethod
    def validate_concurrency(cls, v: int) -> int:
        if v < 1 or v > 500:
            raise ValueError(f"MAX_CONCURRENT_TESTS must be between 1 and 500, got {v}")
        return v

    @field_validator("REQUEST_TIMEOUT_SECONDS")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"REQUEST_TIMEOUT_SECONDS must be positive, got {v}")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        lower = v.lower()
        if lower not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return lower

    # ─── Derived helpers ──────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def mongodb_connection_string(self) -> str:
        """Full MongoDB connection string (alias for MONGODB_URL)."""
        return self.MONGODB_URL

    @property
    def effective_ai_provider(self) -> str:
        """
        Resolve 'auto' → 'gemini' if API key present, else 'ollama'.
        Open/Closed Principle: new providers extend without modifying this logic.
        """
        if self.AI_PROVIDER != "auto":
            return self.AI_PROVIDER
        return "gemini" if self.GEMINI_API_KEY else "ollama"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this anywhere to get the singleton."""
    return Settings()


# Module-level singleton for convenience: `from aitester.core.config import settings`
settings = get_settings()
