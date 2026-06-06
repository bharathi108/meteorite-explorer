from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.models import Meteorite, MeteoriteAIExplanation
from app.services import ai_service


class TestHealth:
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestListMeteoritesApi:
    def test_list_returns_mappable_meteorites_only(self, client: TestClient):
        response = client.get("/meteorites")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 4
        assert len(body["items"]) == 4
        assert all(item["latitude"] is not None for item in body["items"])

    def test_filter_by_search(self, client: TestClient):
        response = client.get("/meteorites", params={"search": "Abee"})
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Abee"

    def test_filter_by_recclass(self, client: TestClient):
        response = client.get("/meteorites", params={"recclass": "L5"})
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Aachen"

    def test_list_recclasses(self, client: TestClient):
        response = client.get("/meteorites/recclasses")
        assert response.status_code == 200
        recclasses = response.json()
        assert recclasses == sorted(recclasses)
        assert "L5" in recclasses
        assert "EH4" in recclasses

    def test_filter_by_fall(self, client: TestClient):
        response = client.get("/meteorites", params={"fall": "Found"})
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Antarctic Sample"

    def test_filter_by_year_range(self, client: TestClient):
        response = client.get(
            "/meteorites",
            params={"min_year": 1950, "max_year": 2010},
        )
        body = response.json()
        assert body["total"] == 2
        names = {item["name"] for item in body["items"]}
        assert names == {"Abee", "Antarctic Sample"}

    def test_filter_by_mass_range(self, client: TestClient):
        response = client.get(
            "/meteorites",
            params={"min_mass": 60000, "max_mass": 200000},
        )
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Abee"

    def test_combined_filters(self, client: TestClient):
        response = client.get(
            "/meteorites",
            params={"fall": "Fell", "min_mass": 10000},
        )
        body = response.json()
        assert body["total"] == 2
        names = {item["name"] for item in body["items"]}
        assert names == {"Abee", "Heavy Iron"}

    def test_pagination(self, client: TestClient):
        response = client.get("/meteorites", params={"limit": 2, "offset": 0})
        page1 = response.json()
        response = client.get("/meteorites", params={"limit": 2, "offset": 2})
        page2 = response.json()

        assert page1["total"] == 4
        assert len(page1["items"]) == 2
        assert len(page2["items"]) == 2
        page1_ids = {item["id"] for item in page1["items"]}
        page2_ids = {item["id"] for item in page2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    def test_invalid_fall_returns_422(self, client: TestClient):
        response = client.get("/meteorites", params={"fall": "Maybe"})
        assert response.status_code == 422

    def test_inverted_year_range_returns_422(self, client: TestClient):
        response = client.get(
            "/meteorites",
            params={"min_year": 2000, "max_year": 1900},
        )
        assert response.status_code == 422

    def test_inverted_mass_range_returns_422(self, client: TestClient):
        response = client.get(
            "/meteorites",
            params={"min_mass": 100, "max_mass": 10},
        )
        assert response.status_code == 422


class TestGetMeteoriteApi:
    def test_get_meteorite_by_id(self, client: TestClient):
        response = client.get("/meteorites/2")
        assert response.status_code == 200
        assert response.json()["name"] == "Abee"

    def test_get_meteorite_not_found(self, client: TestClient):
        response = client.get("/meteorites/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_meteorite_invalid_id(self, client: TestClient):
        response = client.get("/meteorites/0")
        assert response.status_code == 422


class TestExplanationApi:
    def test_explanation_not_configured(self, client: TestClient, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        response = client.post("/meteorites/2/explanation")
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    def test_explanation_meteorite_not_found(self, client: TestClient):
        response = client.post("/meteorites/999/explanation")
        assert response.status_code == 404

    def test_explanation_returns_cached_entry(
        self,
        client: TestClient,
        db_session,
        sample_meteorites: list[Meteorite],
    ):
        meteorite = sample_meteorites[1]
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        entry = MeteoriteAIExplanation(
            meteorite_id=meteorite.id,
            prompt_version=ai_service.PROMPT_VERSION,
            model=ai_service.MODEL,
            row_fingerprint=ai_service.compute_row_fingerprint(meteorite),
            explanation="Cached from test.",
            created_at=now,
            expires_at=now + timedelta(days=30),
        )
        db_session.add(entry)
        db_session.commit()

        response = client.post(f"/meteorites/{meteorite.id}/explanation")
        assert response.status_code == 200
        body = response.json()
        assert body["cached"] is True
        assert body["explanation"] == "Cached from test."

    @patch("app.services.ai_service.generate_explanation")
    def test_explanation_generates_and_caches(
        self,
        mock_generate,
        client: TestClient,
        db_session,
        sample_meteorites: list[Meteorite],
    ):
        meteorite = sample_meteorites[1]
        mock_generate.return_value = "Fresh AI summary for Abee."

        response = client.post(f"/meteorites/{meteorite.id}/explanation")
        assert response.status_code == 200
        body = response.json()
        assert body["cached"] is False
        assert body["explanation"] == "Fresh AI summary for Abee."
        mock_generate.assert_called_once()

        mock_generate.reset_mock()
        response = client.post(f"/meteorites/{meteorite.id}/explanation")
        assert response.status_code == 200
        assert response.json()["cached"] is True
        mock_generate.assert_not_called()
