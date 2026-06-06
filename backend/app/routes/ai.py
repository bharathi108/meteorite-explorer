from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AIExplanationResponse
from app.services import ai_service
from app.services.meteorite_service import get_meteorite_or_raise

router = APIRouter(prefix="/meteorites", tags=["ai"])


@router.post("/{meteorite_id}/explanation", response_model=AIExplanationResponse)
def get_meteorite_explanation(
    meteorite_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    meteorite = get_meteorite_or_raise(db, meteorite_id)

    cached = ai_service.get_cached_explanation(db, meteorite)
    if cached is not None:
        return AIExplanationResponse(
            meteorite_id=meteorite.id,
            explanation=cached.explanation,
            cached=True,
            model=cached.model,
            prompt_version=cached.prompt_version,
            created_at=cached.created_at,
        )

    explanation = ai_service.generate_explanation(meteorite)
    entry = ai_service.store_explanation(db, meteorite, explanation)
    return AIExplanationResponse(
        meteorite_id=meteorite.id,
        explanation=entry.explanation,
        cached=False,
        model=entry.model,
        prompt_version=entry.prompt_version,
        created_at=entry.created_at,
    )
