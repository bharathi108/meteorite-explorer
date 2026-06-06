from __future__ import annotations

import os

# Must run before app imports so pytest never loads developer .env files.
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Meteorite


@pytest.fixture
def engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine) -> Session:
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    yield session
    session.close()


@pytest.fixture
def sample_meteorites(db_session: Session) -> list[Meteorite]:
    records = [
        Meteorite(
            id=1,
            name="Aachen",
            nametype="Valid",
            recclass="L5",
            mass_grams=21.0,
            fall="Fell",
            year=1880,
            latitude=50.775,
            longitude=6.083,
        ),
        Meteorite(
            id=2,
            name="Abee",
            nametype="Valid",
            recclass="EH4",
            mass_grams=107000.0,
            fall="Fell",
            year=1952,
            latitude=54.217,
            longitude=-113.0,
        ),
        Meteorite(
            id=3,
            name="Antarctic Sample",
            nametype="Valid",
            recclass="H6",
            mass_grams=500.0,
            fall="Found",
            year=2005,
            latitude=-75.0,
            longitude=0.0,
        ),
        Meteorite(
            id=4,
            name="No Coordinates",
            nametype="Valid",
            recclass="L6",
            mass_grams=100.0,
            fall="Found",
            year=1990,
            latitude=None,
            longitude=None,
        ),
        Meteorite(
            id=5,
            name="Heavy Iron",
            nametype="Valid",
            recclass="Iron, IVA",
            mass_grams=50000.0,
            fall="Fell",
            year=1814,
            latitude=44.0,
            longitude=0.6,
        ),
    ]
    db_session.add_all(records)
    db_session.commit()
    return records


@pytest.fixture
def client(db_session: Session, sample_meteorites: list[Meteorite]) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
