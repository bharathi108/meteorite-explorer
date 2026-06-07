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

**Requirements:** Python 3.11+ (backend), **Node.js 22.13.0** (frontend — pinned in `frontend/package.json`). Wrong Node version fails at `npm install`. Optionally use [nvm](https://github.com/nvm-sh/nvm) — `cd frontend && nvm use` reads `.nvmrc`.

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

If your system Node is not 22.13.0, use [nvm](https://github.com/nvm-sh/nvm) — `frontend/.nvmrc` pins the version (`nvm use` in that directory).

```bash
# nvm (first time only)
nvm install 22.13.0

cd frontend
nvm use
node -v          # should print v22.13.0
npm install
```

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
nvm use          # if using nvm
npm run dev
```

App: http://localhost:5173

---

## Deploy (take-home)

[Render](https://render.com) for both frontend (static site) and backend (web service + SQLite).

Deployed on: https://meteorite-explorer.onrender.com/
API Docs: https://meteorite-explorer-api.onrender.com/docs 

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for Blueprint setup, env vars, and a pre-deploy checklist.

---

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for API docs, tests, and additional details.
