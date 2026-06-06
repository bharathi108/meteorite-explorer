from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MeteoriteBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nametype: str
    recclass: Optional[str]
    mass_grams: Optional[float]
    fall: Optional[str]
    year: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]


class MeteoriteListParams(BaseModel):
    search: Optional[str] = None
    recclass: Optional[str] = None
    fall: Optional[Literal["Fell", "Found"]] = None
    min_year: Optional[int] = Field(None, ge=0, le=2100)
    max_year: Optional[int] = Field(None, ge=0, le=2100)
    min_mass: Optional[float] = Field(None, ge=0)
    max_mass: Optional[float] = Field(None, ge=0)
    min_lat: Optional[float] = Field(None, ge=-90, le=90)
    max_lat: Optional[float] = Field(None, ge=-90, le=90)
    min_lng: Optional[float] = Field(None, ge=-180, le=180)
    max_lng: Optional[float] = Field(None, ge=-180, le=180)
    limit: int = Field(1000, ge=1, le=10000)
    offset: int = Field(0, ge=0)

    @field_validator("search", "recclass", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.min_year is not None
            and self.max_year is not None
            and self.min_year > self.max_year
        ):
            raise ValueError("min_year cannot be greater than max_year")
        if (
            self.min_mass is not None
            and self.max_mass is not None
            and self.min_mass > self.max_mass
        ):
            raise ValueError("min_mass cannot be greater than max_mass")
        if (
            self.min_lat is not None
            and self.max_lat is not None
            and self.min_lat > self.max_lat
        ):
            raise ValueError("min_lat cannot be greater than max_lat")
        # min_lng > max_lng is valid when the viewport crosses the antimeridian
        # (e.g. Pacific view); meteorite_service handles that case.
        return self


class MeteoriteListResponse(BaseModel):
    items: list[MeteoriteBase]
    total: int
    limit: int
    offset: int


class AIExplanationResponse(BaseModel):
    meteorite_id: int
    explanation: str
    cached: bool
    model: str
    prompt_version: str
    created_at: Optional[datetime] = None
