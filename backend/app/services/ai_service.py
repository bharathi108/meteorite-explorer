from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import AIConfigurationError, AIGenerationError
from app.models import Meteorite, MeteoriteAIExplanation

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v2"
DEFAULT_MODEL = "gpt-4o-mini"
MODEL = DEFAULT_MODEL  # backwards compat for tests/docs
CACHE_TTL_DAYS = 30
MAX_COMPLETION_TOKENS = 180


def _active_model() -> str:
    return get_settings().openai_model

SYSTEM_PROMPT = """You are a science educator explaining meteorites from NASA's dataset to curious non-experts.

Write exactly one short paragraph (3-5 sentences, under 100 words) that:
- Briefly explains what the classification means
- Notes one interesting fact about this meteorite (mass, fall vs found, or age)
- Uses plain language — no bullet lists, headings, or markdown

Do not invent facts. Skip unknown fields. Be direct and conversational."""

USER_PROMPT_TEMPLATE = """Meteorite: {name}
Classification: {recclass} | Mass: {mass} | {fall} | {year}
Location: {location}

One short paragraph for a sidebar summary."""


def compute_row_fingerprint(meteorite: Meteorite) -> str:
    payload = (
        f"{meteorite.name}|{meteorite.recclass}|{meteorite.mass_grams}|"
        f"{meteorite.fall}|{meteorite.year}|{meteorite.latitude}|{meteorite.longitude}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def format_mass_for_prompt(grams: float | None) -> str:
    if grams is None:
        return "Unknown"
    if grams >= 1_000_000:
        return f"{grams / 1_000_000:.2f} metric tons ({grams:,.0f} g)"
    if grams >= 1_000:
        return f"{grams / 1_000:.2f} kg ({grams:,.0f} g)"
    return f"{grams:,.0f} g"


def format_location_for_prompt(
    latitude: float | None,
    longitude: float | None,
) -> str:
    if latitude is None or longitude is None:
        return "Unknown"
    lat_dir = "N" if latitude >= 0 else "S"
    lng_dir = "E" if longitude >= 0 else "W"
    return (
        f"{abs(latitude):.2f}°{lat_dir}, {abs(longitude):.2f}°{lng_dir}"
    )


def build_user_prompt(meteorite: Meteorite) -> str:
    return USER_PROMPT_TEMPLATE.format(
        name=meteorite.name,
        recclass=meteorite.recclass or "Unknown",
        mass=format_mass_for_prompt(meteorite.mass_grams),
        fall=meteorite.fall or "Unknown",
        year=meteorite.year if meteorite.year is not None else "Unknown",
        location=format_location_for_prompt(meteorite.latitude, meteorite.longitude),
    )


def get_cached_explanation(
    db: Session,
    meteorite: Meteorite,
) -> Optional[MeteoriteAIExplanation]:
    fingerprint = compute_row_fingerprint(meteorite)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stmt = (
        select(MeteoriteAIExplanation)
        .where(
            MeteoriteAIExplanation.meteorite_id == meteorite.id,
            MeteoriteAIExplanation.prompt_version == PROMPT_VERSION,
            MeteoriteAIExplanation.model == _active_model(),
            MeteoriteAIExplanation.row_fingerprint == fingerprint,
            MeteoriteAIExplanation.expires_at > now,
        )
        .order_by(MeteoriteAIExplanation.created_at.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def store_explanation(
    db: Session,
    meteorite: Meteorite,
    explanation: str,
) -> MeteoriteAIExplanation:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    entry = MeteoriteAIExplanation(
        meteorite_id=meteorite.id,
        prompt_version=PROMPT_VERSION,
        model=_active_model(),
        row_fingerprint=compute_row_fingerprint(meteorite),
        explanation=explanation,
        created_at=now,
        expires_at=now + timedelta(days=CACHE_TTL_DAYS),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _create_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise AIConfigurationError()
    return OpenAI(api_key=settings.openai_api_key)


def _request_completion(client: OpenAI, user_prompt: str) -> str:
    settings = get_settings()
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=MAX_COMPLETION_TOKENS,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise AIGenerationError("The AI returned an empty explanation.")
    return content.strip()


def generate_explanation(meteorite: Meteorite) -> str:
    """Generate an AI explanation via OpenAI. Requires OPENAI_API_KEY."""
    client = _create_openai_client()
    user_prompt = build_user_prompt(meteorite)

    try:
        return _request_completion(client, user_prompt)
    except AIConfigurationError:
        raise
    except RateLimitError as exc:
        logger.warning("OpenAI rate limit: %s", exc)
        raise AIGenerationError(
            "AI service is temporarily busy. Please try again in a moment."
        ) from exc
    except APIConnectionError as exc:
        logger.warning("OpenAI connection error: %s", exc)
        raise AIGenerationError(
            "Could not reach the AI service. Please try again later."
        ) from exc
    except APIStatusError as exc:
        logger.warning("OpenAI API error: %s", exc)
        raise AIGenerationError(
            "The AI service returned an error. Please try again later."
        ) from exc
    except AIGenerationError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error generating AI explanation")
        raise AIGenerationError() from exc
