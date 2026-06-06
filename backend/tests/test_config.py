from __future__ import annotations

import pytest

from app.config import get_settings, load_env_files


class TestConfig:
    def test_test_env_skips_dotenv_files(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "test")
        load_env_files()

    def test_get_settings_defaults(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.app_env == "test"
        assert settings.openai_api_key is None
        assert settings.openai_model == "gpt-4o-mini"
        assert settings.database_url.startswith("sqlite:///")

        get_settings.cache_clear()

    def test_cors_origins_from_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://www.example.com")
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.cors_origins == [
            "https://app.example.com",
            "https://www.example.com",
        ]

        get_settings.cache_clear()
