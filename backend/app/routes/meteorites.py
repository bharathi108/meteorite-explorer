from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MeteoriteBase, MeteoriteListParams, MeteoriteListResponse
from app.services.meteorite_service import get_meteorite_or_raise, list_meteorites, list_recclasses

router = APIRouter(prefix="/meteorites", tags=["meteorites"])


@router.get("", response_model=MeteoriteListResponse)
def get_meteorites(
    filters: MeteoriteListParams = Depends(),
    db: Session = Depends(get_db),
):
    items, total = list_meteorites(db, filters)
    return MeteoriteListResponse(
        items=items,
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.get("/recclasses", response_model=list[str])
def get_recclasses(db: Session = Depends(get_db)):
    return list_recclasses(db)


@router.get("/{meteorite_id}", response_model=MeteoriteBase)
def get_meteorite(
    meteorite_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    return get_meteorite_or_raise(db, meteorite_id)
