from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.exceptions import MeteoriteNotFoundError
from app.models import Meteorite
from app.schemas import MeteoriteListParams
from app.services.meteorite_service import (
    get_meteorite_by_id,
    get_meteorite_or_raise,
    list_meteorites,
)


class TestMeteoriteListParams:
    def test_rejects_inverted_year_range(self):
        with pytest.raises(ValidationError, match="min_year cannot be greater than max_year"):
            MeteoriteListParams(min_year=2000, max_year=1900)

    def test_rejects_inverted_mass_range(self):
        with pytest.raises(ValidationError, match="min_mass cannot be greater than max_mass"):
            MeteoriteListParams(min_mass=100, max_mass=10)

    def test_empty_search_becomes_none(self):
        params = MeteoriteListParams(search="   ")
        assert params.search is None

    def test_accepts_antimeridian_lng_range(self):
        params = MeteoriteListParams(min_lng=170, max_lng=-170)
        assert params.min_lng == 170
        assert params.max_lng == -170


class TestListMeteorites:
    def test_excludes_records_without_coordinates(self, db_session, sample_meteorites):
        items, total = list_meteorites(db_session, MeteoriteListParams())
        assert total == 4
        assert all(item.latitude is not None for item in items)
        assert all(item.longitude is not None for item in items)

    def test_filter_by_search_name(self, db_session, sample_meteorites):
        items, total = list_meteorites(db_session, MeteoriteListParams(search="Abee"))
        assert total == 1
        assert items[0].name == "Abee"

    def test_filter_by_search_does_not_match_recclass(self, db_session, sample_meteorites):
        items, total = list_meteorites(db_session, MeteoriteListParams(search="EH4"))
        assert total == 0
        assert items == []

    def test_filter_by_recclass(self, db_session, sample_meteorites):
        items, total = list_meteorites(db_session, MeteoriteListParams(recclass="L5"))
        assert total == 1
        assert items[0].name == "Aachen"

    def test_filter_by_fall(self, db_session, sample_meteorites):
        items, total = list_meteorites(db_session, MeteoriteListParams(fall="Found"))
        assert total == 1
        assert items[0].name == "Antarctic Sample"

    def test_filter_by_year_range(self, db_session, sample_meteorites):
        items, total = list_meteorites(
            db_session,
            MeteoriteListParams(min_year=1950, max_year=2010),
        )
        assert total == 2
        names = {item.name for item in items}
        assert names == {"Abee", "Antarctic Sample"}

    def test_filter_by_mass_range(self, db_session, sample_meteorites):
        items, total = list_meteorites(
            db_session,
            MeteoriteListParams(min_mass=60000, max_mass=200000),
        )
        assert total == 1
        assert items[0].name == "Abee"

    def test_filter_by_viewport_bounds(self, db_session, sample_meteorites):
        items, total = list_meteorites(
            db_session,
            MeteoriteListParams(min_lat=50, max_lat=56, min_lng=0, max_lng=12),
        )
        assert total == 1
        assert items[0].name == "Aachen"

    def test_filter_by_antimeridian_viewport(self, db_session, sample_meteorites):
        db_session.add_all(
            [
                Meteorite(
                    id=6,
                    name="Pacific East",
                    nametype="Valid",
                    recclass="L6",
                    mass_grams=100.0,
                    fall="Found",
                    year=2000,
                    latitude=10.0,
                    longitude=175.0,
                ),
                Meteorite(
                    id=7,
                    name="Pacific West",
                    nametype="Valid",
                    recclass="L6",
                    mass_grams=100.0,
                    fall="Found",
                    year=2000,
                    latitude=10.0,
                    longitude=-175.0,
                ),
                Meteorite(
                    id=8,
                    name="Japan",
                    nametype="Valid",
                    recclass="L6",
                    mass_grams=100.0,
                    fall="Found",
                    year=2000,
                    latitude=35.0,
                    longitude=139.0,
                ),
            ]
        )
        db_session.commit()

        items, total = list_meteorites(
            db_session,
            MeteoriteListParams(min_lat=-90, max_lat=90, min_lng=170, max_lng=-170),
        )
        assert total == 2
        assert {item.name for item in items} == {"Pacific East", "Pacific West"}

    def test_rejects_inverted_lat_range(self):
        with pytest.raises(ValidationError, match="min_lat cannot be greater than max_lat"):
            MeteoriteListParams(min_lat=10, max_lat=0)

    def test_combined_filters(self, db_session, sample_meteorites):
        items, total = list_meteorites(
            db_session,
            MeteoriteListParams(fall="Fell", min_mass=10000),
        )
        assert total == 2
        names = {item.name for item in items}
        assert names == {"Abee", "Heavy Iron"}

    def test_pagination_limit_and_offset(self, db_session, sample_meteorites):
        _, total = list_meteorites(db_session, MeteoriteListParams())
        assert total == 4

        page1, _ = list_meteorites(db_session, MeteoriteListParams(limit=2, offset=0))
        page2, _ = list_meteorites(db_session, MeteoriteListParams(limit=2, offset=2))

        assert len(page1) == 2
        assert len(page2) == 2
        assert {item.id for item in page1}.isdisjoint({item.id for item in page2})

    def test_results_sorted_by_name(self, db_session, sample_meteorites):
        items, _ = list_meteorites(db_session, MeteoriteListParams())
        names = [item.name for item in items]
        assert names == sorted(names)


class TestGetMeteorite:
    def test_get_meteorite_by_id(self, db_session, sample_meteorites):
        meteorite = get_meteorite_by_id(db_session, 2)
        assert meteorite is not None
        assert meteorite.name == "Abee"

    def test_get_meteorite_by_id_missing(self, db_session, sample_meteorites):
        assert get_meteorite_by_id(db_session, 999) is None

    def test_get_meteorite_or_raise_found(self, db_session, sample_meteorites):
        meteorite = get_meteorite_or_raise(db_session, 1)
        assert meteorite.name == "Aachen"

    def test_get_meteorite_or_raise_not_found(self, db_session, sample_meteorites):
        with pytest.raises(MeteoriteNotFoundError, match="Meteorite 999 not found"):
            get_meteorite_or_raise(db_session, 999)
