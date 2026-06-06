from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Meteorite(Base):
    __tablename__ = "meteorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    nametype: Mapped[str] = mapped_column(String, nullable=False)
    recclass: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mass_grams: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fall: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    explanations: Mapped[list["MeteoriteAIExplanation"]] = relationship(
        back_populates="meteorite"
    )


class MeteoriteAIExplanation(Base):
    __tablename__ = "meteorite_ai_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meteorite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meteorites.id"), nullable=False, index=True
    )
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    row_fingerprint: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    meteorite: Mapped["Meteorite"] = relationship(back_populates="explanations")
