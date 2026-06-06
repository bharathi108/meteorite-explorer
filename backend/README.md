# Meteorite Explorer — Backend

FastAPI backend for the Meteorite Explorer application.

## Setup

**Python 3.11+** required. Check with `python3 --version`; on Render set `PYTHON_VERSION=3.11.9`.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data Ingestion

Load the NASA meteorite landings dataset into SQLite:

```bash
python -m app.scripts.ingest_meteorites
```

This reads `meteorite_landings.csv` and writes records to `meteorites.db`.

## Run the API

```bash
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Environment configuration

Config is loaded from env files via `python-dotenv`, selected by `APP_ENV` (default: `development`).

| File | When |
|------|------|
| `.env.development` | Local dev (`APP_ENV=development`, default) |
| `.env.production` | Production (`APP_ENV=production`) |
| `.env` | Optional shared fallback loaded before the env-specific file |

Copy the example for your environment and fill in secrets:

```bash
cp .env.development.example .env.development
# edit .env.development — add OPENAI_API_KEY, etc.
uvicorn app.main:app --reload
```

For production, set variables in your host (Render, Fly, etc.) **or** use `.env.production` on the server:

```bash
APP_ENV=production uvicorn app.main:app --host 0.0.0.0 --port 8000
```

| Variable | Dev default | Description |
|----------|-------------|-------------|
| `APP_ENV` | `development` | Selects `.env.{APP_ENV}` |
| `OPENAI_API_KEY` | — | Required for new AI summaries |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `DATABASE_URL` | `sqlite:///…/meteorites.db` | SQLAlchemy database URL |
| `CORS_ORIGINS` | `http://localhost:5173,…` | Comma-separated frontend origins (`*` in dev if unset) |
| `LOG_LEVEL` | `INFO` | Python log level |

`.env.development` and `.env.production` are gitignored. Only `*.example` templates are committed.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/meteorites` | List meteorites with optional filters |
| GET | `/meteorites/recclasses` | Distinct classification values (for filter dropdown) |
| GET | `/meteorites/{id}` | Get a single meteorite |
| POST | `/meteorites/{id}/explanation` | Get or generate AI explanation (requires `OPENAI_API_KEY` for new summaries) |

### Filter parameters for `GET /meteorites`

- `search` — meteorite name substring
- `recclass` — classification filter (exact match; see `GET /meteorites/recclasses` for options)
- `fall` — `Fell` or `Found`
- `min_year`, `max_year` — year range
- `min_mass`, `max_mass` — mass range in grams
- `min_lat`, `max_lat`, `min_lng`, `max_lng` — map viewport bounding box
- `limit` (default 1000), `offset` (default 0)

## Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes/
│   │   ├── meteorites.py
│   │   └── ai.py
│   ├── services/
│   │   ├── meteorite_service.py
│   │   └── ai_service.py
│   └── scripts/
│       └── ingest_meteorites.py
├── meteorite_landings.csv
├── requirements.txt
└── README.md
```
