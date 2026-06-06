# Deployment Guide (Take-Home)

For a take-home interview, keep it simple: **Vercel for the frontend**, **Render for the backend + SQLite**. No Kubernetes, no separate DB host.

```text
Browser → Vercel (static React app)
              ↓  VITE_API_URL
         Render Web Service (FastAPI)
              ↓
         SQLite file on disk (meteorites.db)
              ↑
         Built from meteorite_landings.csv on deploy
```

## Why this stack?

| Piece | Service | Why |
|-------|---------|-----|
| Frontend | [Vercel](https://vercel.com) | Free, fast CDN, great for Vite/React |
| Backend | [Render](https://render.com) | Free tier, runs Python/FastAPI with minimal config |
| Database | SQLite on Render | Already in the project; ~45k rows is fine for a demo |

You do **not** need a managed Postgres instance for this app. SQLite ships with the backend and is rebuilt from the CSV on each deploy.

**Tradeoff:** On Render’s free tier, the filesystem is reset when you redeploy — the build step re-runs ingestion, which is acceptable for a take-home.

---

## Prerequisites

- GitHub repo with this project pushed
- [Render](https://render.com) account
- [Vercel](https://vercel.com) account
- OpenAI API key (for AI summaries)

---

## 1. Deploy the backend (Render)

### Option A — Blueprint (easiest)

1. Push this repo to GitHub.
2. In Render: **New → Blueprint** → connect the repo.
3. Render reads [`render.yaml`](render.yaml) at the repo root.
4. In the Render dashboard, add secret env var **`OPENAI_API_KEY`** to the web service.
5. After deploy, note the URL (e.g. `https://meteorite-explorer-api.onrender.com`).

### Option B — Manual web service

1. **New → Web Service** → connect GitHub repo.
2. Settings:
   - **Root directory:** `backend`
   - **Runtime:** Python 3
   - **Build command:**
     ```bash
     pip install -r requirements.txt && python -m app.scripts.ingest_meteorites
     ```
   - **Start command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
3. **Environment variables:**

   | Key | Value |
   |-----|--------|
   | `APP_ENV` | `production` |
   | `OPENAI_API_KEY` | your key (secret) |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` (set after frontend deploy) |
   | `LOG_LEVEL` | `INFO` |

4. Deploy. Verify: `GET https://<your-api>/health` → `{"status":"ok"}`  
   And: `GET https://<your-api>/meteorites?limit=1` returns data.

**Note:** Free-tier Render services spin down after inactivity; first request may take ~30s.

---

## 2. Deploy the frontend (Vercel)

1. **New Project** → import the same GitHub repo.
2. Settings:
   - **Root directory:** `frontend`
   - **Framework preset:** Vite
   - **Build command:** `npm run build`
   - **Output directory:** `dist`
3. **Environment variable:**

   | Key | Value |
   |-----|--------|
   | `VITE_API_URL` | `https://<your-render-api-url>` (no trailing slash) |

4. Deploy. Vercel gives you e.g. `https://meteorite-explorer.vercel.app`.

5. **Update Render CORS:** Go back to Render → backend service → Environment → set  
   `CORS_ORIGINS=https://meteorite-explorer.vercel.app`  
   (use your actual Vercel URL; add preview URL too if you want PR previews to work).

6. Redeploy backend (or wait for env reload).

---

## 3. Database — what actually happens

There is no separate “DB deploy” step:

1. `meteorite_landings.csv` lives in `backend/` (committed to git).
2. Render **build** runs `python -m app.scripts.ingest_meteorites` → creates `meteorites.db`.
3. FastAPI reads SQLite via `DATABASE_URL` (defaults to `backend/meteorites.db`).
4. AI explanation cache is also stored in the same SQLite file.

Optional: override `DATABASE_URL` if you ever mount a persistent disk (Fly.io volume, Render paid disk). Not needed for the take-home.

---

## 4. Checklist before sharing the link

- [ ] `GET /health` returns OK on production API
- [ ] Globe loads meteorites (not empty / CORS errors in browser console)
- [ ] Click a meteorite → details + AI insight work
- [ ] README or submission email includes **live frontend URL** and **API URL**
- [ ] `.env.development` / `.env.production` with secrets are **not** committed

---

## 5. Alternatives (if you prefer)

| Stack | When to use |
|-------|-------------|
| **Railway** (backend + frontend) | One dashboard, similar to Render; good monorepo support |
| **Fly.io** + volume | If you want SQLite to survive redeploys without re-ingesting |
| **Render static site** for frontend | Skip Vercel; works, but Vercel is smoother for Vite |

Avoid for a take-home: AWS ECS/EKS, self-managed Postgres, Docker Compose on a VPS (unless the job explicitly asks for it).

---

## 6. Local production smoke test

Before deploying, you can mimic production locally:

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate
APP_ENV=production CORS_ORIGINS=http://localhost:4173 uvicorn app.main:app --port 8000

# Terminal 2 — frontend production build
cd frontend
VITE_API_URL=http://127.0.0.1:8000 npm run build
npm run preview
```

Open http://localhost:4173 and confirm the globe talks to the API without the Vite dev proxy.
