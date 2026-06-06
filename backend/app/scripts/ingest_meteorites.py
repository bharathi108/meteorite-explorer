"""Load NASA meteorite landings CSV into SQLite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typing import Optional

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV = BACKEND_DIR / "meteorite_landings.csv"

sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import Meteorite  # noqa: E402


def _parse_year(value) -> Optional[int]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        year = int(float(text))
    except ValueError:
        return None
    if year < 0 or year > 2100:
        return None
    return year


def load_dataframe(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    df = df.rename(
        columns={
            "mass (g)": "mass_grams",
            "reclat": "latitude",
            "reclong": "longitude",
        }
    )

    df = df[df["nametype"] == "Valid"].copy()

    df["mass_grams"] = pd.to_numeric(df["mass_grams"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["year"] = df["year"].apply(_parse_year)
    df["recclass"] = df["recclass"].where(df["recclass"].notna(), None)
    df["fall"] = df["fall"].where(df["fall"].notna(), None)

    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["id", "name"])
    df["id"] = df["id"].astype(int)

    return df[
        ["id", "name", "nametype", "recclass", "mass_grams", "fall", "year", "latitude", "longitude"]
    ]


def ingest(csv_path: Path, replace: bool = True) -> int:
    init_db()
    df = load_dataframe(csv_path)

    with SessionLocal() as db:
        if replace:
            db.query(Meteorite).delete()
            db.commit()

        records = [
            Meteorite(
                id=row.id,
                name=row.name,
                nametype=row.nametype,
                recclass=row.recclass,
                mass_grams=row.mass_grams if pd.notna(row.mass_grams) else None,
                fall=row.fall,
                year=row.year,
                latitude=row.latitude if pd.notna(row.latitude) else None,
                longitude=row.longitude if pd.notna(row.longitude) else None,
            )
            for row in df.itertuples(index=False)
        ]
        db.bulk_save_objects(records)
        db.commit()

    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Ingest meteorite landings CSV into SQLite")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="Path to meteorite_landings.csv",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append records instead of replacing existing data",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        raise SystemExit(f"CSV not found: {args.csv}")

    count = ingest(args.csv, replace=not args.append)
    print(f"Ingested {count} meteorite records into the database.")


if __name__ == "__main__":
    main()
