from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BACKEND_DIR / "meteorites.db"


def _parse_app_env() -> str:
    return os.environ.get("APP_ENV", "development").strip().lower()


def load_env_files() -> None:
    """Load env files for local/dev/prod. Skipped when APP_ENV=test (pytest)."""
    app_env = _parse_app_env()
    if app_env == "test":
        return

    load_dotenv(BACKEND_DIR / ".env", override=False)

    env_file = BACKEND_DIR / f".env.{app_env}"
    if env_file.is_file():
        load_dotenv(env_file, override=True)


def _parse_cors_origins(raw: str, app_env: str) -> list[str]:
    value = raw.strip()
    if not value:
        return ["*"] if app_env == "development" else []
    if value == "*":
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str
    openai_api_key: str | None
    openai_model: str
    database_url: str
    cors_origins: list[str]
    log_level: str

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_openai_configured(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    app_env = _parse_app_env()
    default_db = f"sqlite:///{DEFAULT_SQLITE_PATH}"

    return Settings(
        app_env=app_env,
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip() or None,
        openai_model=os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini",
        database_url=os.environ.get("DATABASE_URL", "").strip() or default_db,
        cors_origins=_parse_cors_origins(
            os.environ.get("CORS_ORIGINS", ""),
            app_env,
        ),
        log_level=os.environ.get("LOG_LEVEL", "INFO").strip().upper(),
    )


load_env_files()
