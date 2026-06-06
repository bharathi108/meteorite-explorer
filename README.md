# Meteorite Explorer

Interactive educational app for exploring NASA's Meteorite Landings dataset with a 3D globe and AI-powered explanations.

## Project Structure

```text
├── backend/    FastAPI + SQLite API
├── frontend/   React + TypeScript + 3D globe
├── product.md  Product requirements
├── tech_spec.md  Technical design
└── considerations_and_improvements.md  Tradeoffs, iteration history, future work
```

## First-Time Setup

**Requirements:** Python 3.11+ (backend), **Node.js 22.13.0** (frontend — pinned in `frontend/package.json`).

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.scripts.ingest_meteorites
```

This creates a virtual environment, installs dependencies, and loads `meteorite_landings.csv` into `meteorites.db`.

### Frontend

Node is pinned to **22.13.0**. If your system Node differs, use [nvm](https://github.com/nvm-sh/nvm) or [fnm](https://github.com/Schniz/fnm) (optional — reads `frontend/.nvmrc`):

```bash
# nvm (first time only)
nvm install 22.13.0

cd frontend
nvm use          # or: fnm use
node -v          # should print v22.13.0
npm install
```

`npm install` fails on the wrong Node version (`engine-strict` in `frontend/.npmrc`).

The frontend proxies API requests to the backend during development (see `frontend/vite.config.ts`).

---

## Quick Start

Run both services from the project root in separate terminals.

**Backend**

```bash
cd backend
source .venv/bin/activate
cp .env.development.example .env.development   # once — add your OpenAI key
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

**Frontend**

```bash
cd frontend
nvm use          # or: fnm use — Node 22.13.0
npm run dev
```

App: http://localhost:5173

---

## Deploy (take-home)

**Recommended:** [Render](https://render.com) for both frontend (static site) and backend (web service + SQLite).

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for Blueprint setup, env vars, and a pre-deploy checklist.

---

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for API docs, tests, and additional details.
