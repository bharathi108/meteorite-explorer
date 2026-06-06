from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Meteorite
from app.scripts import ingest_meteorites


SAMPLE_CSV = """name,id,nametype,recclass,mass (g),fall,year,reclat,reclong,GeoLocation
Aachen,1,Valid,L5,21,Fell,1880,50.775,6.083,"(50.775, 6.083)"
Rejected,2,Invalid,L6,100,Fell,1900,10,10,"(10, 10)"
No Coords,3,Valid,H6,,Found,2000,,,
Future Year,4,Valid,L5,50,Fell,9999,40,40,"(40, 40)"
"""


class TestParseYear:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (1880, 1880),
            ("1952", 1952),
            ("", None),
            (float("nan"), None),
            ("not-a-year", None),
            (9999, None),
            (-1, None),
        ],
    )
    def test_parse_year(self, raw, expected):
        assert ingest_meteorites._parse_year(raw) == expected


class TestLoadDataframe:
    def test_loads_and_cleans_csv(self, tmp_path: Path):
        csv_path = tmp_path / "meteorites.csv"
        csv_path.write_text(SAMPLE_CSV)

        df = ingest_meteorites.load_dataframe(csv_path)

        assert len(df) == 3
        assert set(df["name"]) == {"Aachen", "No Coords", "Future Year"}

        aachen = df[df["name"] == "Aachen"].iloc[0]
        assert aachen["mass_grams"] == 21
        assert aachen["latitude"] == pytest.approx(50.775)

        no_coords = df[df["name"] == "No Coords"].iloc[0]
        assert pd.isna(no_coords["mass_grams"])
        assert pd.isna(no_coords["latitude"])

        future_year = df[df["name"] == "Future Year"].iloc[0]
        assert pd.isna(future_year["year"])


class TestIngest:
    def test_ingest_replaces_existing_records(self, tmp_path: Path, engine, monkeypatch):
        csv_path = tmp_path / "meteorites.csv"
        csv_path.write_text(SAMPLE_CSV)

        test_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        monkeypatch.setattr(ingest_meteorites, "SessionLocal", test_session_local)
        monkeypatch.setattr(
            ingest_meteorites,
            "init_db",
            lambda: Base.metadata.create_all(engine),
        )

        count = ingest_meteorites.ingest(csv_path, replace=True)
        assert count == 3

        with test_session_local() as db:
            records = db.query(Meteorite).order_by(Meteorite.id).all()
            assert len(records) == 3
            assert records[0].name == "Aachen"
            assert records[1].name == "No Coords"
            assert records[2].year is None

    def test_ingest_append_mode(self, tmp_path: Path, engine, monkeypatch):
        csv_path = tmp_path / "meteorites.csv"
        csv_path.write_text(SAMPLE_CSV)
        append_csv = tmp_path / "append.csv"
        append_csv.write_text(
            'name,id,nametype,recclass,mass (g),fall,year,reclat,reclong,GeoLocation\n'
            'Extra,5,Valid,L5,10,Fell,1900,1,1,"(1, 1)"\n'
        )

        test_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        monkeypatch.setattr(ingest_meteorites, "SessionLocal", test_session_local)
        monkeypatch.setattr(
            ingest_meteorites,
            "init_db",
            lambda: Base.metadata.create_all(engine),
        )

        ingest_meteorites.ingest(csv_path, replace=True)

        with test_session_local() as db:
            db.add(
                Meteorite(
                    id=99,
                    name="Preexisting",
                    nametype="Valid",
                    recclass="L5",
                    mass_grams=1.0,
                    fall="Fell",
                    year=1900,
                    latitude=1.0,
                    longitude=1.0,
                )
            )
            db.commit()

        ingest_meteorites.ingest(append_csv, replace=False)

        with test_session_local() as db:
            assert db.query(Meteorite).count() == 5
            assert db.get(Meteorite, 99) is not None
            assert db.get(Meteorite, 5) is not None
