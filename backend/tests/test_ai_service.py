from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import AIConfigurationError, AIGenerationError
from app.models import Meteorite, MeteoriteAIExplanation
from app.services import ai_service


def _make_meteorite(**overrides) -> Meteorite:
    defaults = dict(
        id=1,
        name="Abee",
        nametype="Valid",
        recclass="EH4",
        mass_grams=107000.0,
        fall="Fell",
        year=1952,
        latitude=54.217,
        longitude=-113.0,
    )
    defaults.update(overrides)
    return Meteorite(**defaults)


class TestComputeRowFingerprint:
    def test_fingerprint_is_deterministic(self):
        meteorite = _make_meteorite()
        assert ai_service.compute_row_fingerprint(meteorite) == ai_service.compute_row_fingerprint(
            meteorite
        )

    def test_fingerprint_changes_when_data_changes(self):
        base = _make_meteorite()
        changed = _make_meteorite(mass_grams=108000.0)
        assert ai_service.compute_row_fingerprint(base) != ai_service.compute_row_fingerprint(
            changed
        )


class TestBuildUserPrompt:
    def test_includes_key_meteorite_fields(self):
        prompt = ai_service.build_user_prompt(_make_meteorite())
        assert "Abee" in prompt
        assert "EH4" in prompt
        assert "107.00 kg" in prompt
        assert "Fell" in prompt
        assert "1952" in prompt
        assert "54.22°N" in prompt

    def test_handles_missing_optional_fields(self):
        prompt = ai_service.build_user_prompt(
            _make_meteorite(recclass=None, mass_grams=None, fall=None, year=None)
        )
        assert "Unknown" in prompt


class TestExplanationCache:
    def test_store_and_retrieve_cached_explanation(self, db_session):
        meteorite = _make_meteorite()
        db_session.add(meteorite)
        db_session.commit()

        ai_service.store_explanation(db_session, meteorite, "Test explanation.")
        cached = ai_service.get_cached_explanation(db_session, meteorite)

        assert cached is not None
        assert cached.explanation == "Test explanation."
        assert cached.prompt_version == ai_service.PROMPT_VERSION
        assert cached.model == ai_service.MODEL

    def test_expired_cache_is_not_returned(self, db_session):
        meteorite = _make_meteorite()
        db_session.add(meteorite)
        db_session.commit()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expired_entry = MeteoriteAIExplanation(
            meteorite_id=meteorite.id,
            prompt_version=ai_service.PROMPT_VERSION,
            model=ai_service.MODEL,
            row_fingerprint=ai_service.compute_row_fingerprint(meteorite),
            explanation="Old explanation.",
            created_at=now - timedelta(days=60),
            expires_at=now - timedelta(days=1),
        )
        db_session.add(expired_entry)
        db_session.commit()

        assert ai_service.get_cached_explanation(db_session, meteorite) is None

    def test_cache_miss_when_fingerprint_changes(self, db_session):
        meteorite = _make_meteorite()
        db_session.add(meteorite)
        db_session.commit()

        ai_service.store_explanation(db_session, meteorite, "Cached explanation.")
        meteorite.mass_grams = 999.0

        assert ai_service.get_cached_explanation(db_session, meteorite) is None


class TestGenerateExplanation:
    def test_raises_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(AIConfigurationError):
            ai_service.generate_explanation(_make_meteorite())

    @patch("app.services.ai_service._request_completion")
    @patch("app.services.ai_service._create_openai_client")
    def test_returns_model_text(self, mock_create_client, mock_request, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_create_client.return_value = MagicMock()
        mock_request.return_value = "This EH4 meteorite is scientifically interesting."

        result = ai_service.generate_explanation(_make_meteorite())

        assert result == "This EH4 meteorite is scientifically interesting."
        mock_request.assert_called_once()

    @patch("app.services.ai_service._request_completion")
    @patch("app.services.ai_service._create_openai_client")
    def test_wraps_empty_response(self, mock_create_client, mock_request, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_create_client.return_value = MagicMock()
        mock_request.side_effect = AIGenerationError("The AI returned an empty explanation.")

        with pytest.raises(AIGenerationError, match="empty"):
            ai_service.generate_explanation(_make_meteorite())
