from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import MeteoriteNotFoundError
from app.models import Meteorite
from app.schemas import MeteoriteListParams


def _apply_filters(query, filters: MeteoriteListParams):
    if filters.search:
        term = f"%{filters.search.strip()}%"
        query = query.where(Meteorite.name.ilike(term))

    if filters.recclass:
        query = query.where(Meteorite.recclass.ilike(filters.recclass.strip()))

    if filters.fall:
        query = query.where(Meteorite.fall == filters.fall)

    if filters.min_year is not None:
        query = query.where(Meteorite.year >= filters.min_year)

    if filters.max_year is not None:
        query = query.where(Meteorite.year <= filters.max_year)

    if filters.min_mass is not None:
        query = query.where(Meteorite.mass_grams >= filters.min_mass)

    if filters.max_mass is not None:
        query = query.where(Meteorite.mass_grams <= filters.max_mass)

    if filters.min_lat is not None:
        query = query.where(Meteorite.latitude >= filters.min_lat)

    if filters.max_lat is not None:
        query = query.where(Meteorite.latitude <= filters.max_lat)

    if filters.min_lng is not None and filters.max_lng is not None:
        if filters.min_lng <= filters.max_lng:
            query = query.where(
                Meteorite.longitude >= filters.min_lng,
                Meteorite.longitude <= filters.max_lng,
            )
        else:
            # Viewport crosses the antimeridian (e.g. Pacific view).
            query = query.where(
                (Meteorite.longitude >= filters.min_lng)
                | (Meteorite.longitude <= filters.max_lng)
            )
    elif filters.min_lng is not None:
        query = query.where(Meteorite.longitude >= filters.min_lng)
    elif filters.max_lng is not None:
        query = query.where(Meteorite.longitude <= filters.max_lng)

    return query


def list_meteorites(db: Session, filters: MeteoriteListParams) -> tuple[list[Meteorite], int]:
    base_query = select(Meteorite).where(
        Meteorite.latitude.isnot(None),
        Meteorite.longitude.isnot(None),
    )
    filtered_query = _apply_filters(base_query, filters)

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = db.scalar(count_query) or 0

    items_query = (
        filtered_query.order_by(Meteorite.name)
        .offset(filters.offset)
        .limit(filters.limit)
    )
    items = list(db.scalars(items_query).all())

    return items, total


def get_meteorite_by_id(db: Session, meteorite_id: int) -> Optional[Meteorite]:
    return db.get(Meteorite, meteorite_id)


def get_meteorite_or_raise(db: Session, meteorite_id: int) -> Meteorite:
    meteorite = get_meteorite_by_id(db, meteorite_id)
    if meteorite is None:
        raise MeteoriteNotFoundError(meteorite_id)
    return meteorite
