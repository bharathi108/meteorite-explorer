# Deployment Guide (Take-Home)

Deploy everything on **[Render](https://render.com)** from GitHub: one Blueprint for the FastAPI backend and the React static frontend. SQLite lives on the backend service — no separate database host.

```text
Browser → Render Static Site (React build)
              ↓  VITE_API_URL
         Render Web Service (FastAPI)
              ↓
         SQLite file on disk (meteorites.db)
              ↑
         Built from meteorite_landings.csv on deploy
```

## Why Render for both?

| Piece | Render service type | Why |
|-------|---------------------|-----|
| Frontend | Static Site | Free CDN, auto-deploy on git push |
| Backend | Web Service | Runs Python/FastAPI with minimal config |
| Database | SQLite on backend | ~45k rows; rebuilt from CSV on each deploy |

**Tradeoff:** Free-tier web services spin down after inactivity (~30s cold start). The static frontend does not sleep. Backend disk resets on redeploy — ingestion runs again on each build.

---

## Prerequisites

- Code pushed to [GitHub](https://github.com/bharathi108/meteorite-explorer)
- [Render](https://render.com) account (sign in with GitHub)
- OpenAI API key (for AI summaries)

---

## 1. Deploy with Blueprint (recommended)

1. In Render: **New + → Blueprint**.
2. Connect **`bharathi108/meteorite-explorer`** (or your fork).
3. Render reads [`render.yaml`](render.yaml) and creates two services:
   - **`meteorite-explorer-api`** — Python web service (`backend/`)
   - **`meteorite-explorer`** — static site (`frontend/`)
4. When prompted, set **`OPENAI_API_KEY`** on the API service (secret).
5. Click **Apply** and wait for both deploys (API build includes CSV ingestion).

**Default URLs** (if Render accepts these service names):

| Service | URL |
|---------|-----|
| Frontend | `https://meteorite-explorer.onrender.com` |
| API | `https://meteorite-explorer-api.onrender.com` |

The blueprint pre-wires `VITE_API_URL` and `CORS_ORIGINS` for those names. If Render assigns different URLs, update env vars in the dashboard (see [§3 Wire up the URLs](#3-wire-up-the-urls)).

**Verify API:**

```bash
curl https://meteorite-explorer-api.onrender.com/health
curl "https://meteorite-explorer-api.onrender.com/meteorites?limit=1"
```

Open the frontend URL — globe should load meteorites.

---

## 2. Manual setup (alternative)

### Backend — Web Service

1. **New + → Web Service** → connect repo.
2. Settings:

   | Setting | Value |
   |---------|--------|
   | Root directory | `backend` |
   | Runtime | Python 3 |
   | Build command | `pip install -r requirements.txt && python -m app.scripts.ingest_meteorites` |
   | Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

3. Environment:

   | Key | Value |
   |-----|--------|
   | `APP_ENV` | `production` |
   | `OPENAI_API_KEY` | your key |
   | `CORS_ORIGINS` | frontend URL (see below) |
   | `LOG_LEVEL` | `INFO` |

### Frontend — Static Site

1. **New + → Static Site** → same repo.
2. Settings:

   | Setting | Value |
   |---------|--------|
   | Root directory | `frontend` |
   | Build command | `npm install && npm run build` |
   | Publish directory | `dist` |

3. Environment:

   | Key | Value |
   |-----|--------|
   | `VITE_API_URL` | `https://<your-api>.onrender.com` (no trailing slash) |

4. **Redirects/Rewrites** (SPA routing): add a rewrite rule  
   `/*` → `/index.html`  
   (Blueprint does this via `routes` in `render.yaml`.)

---

## 3. Wire up the URLs

The browser calls the API directly in production (no Vite proxy).

| Where | Variable | Value |
|-------|----------|--------|
| Static site → **Environment** | `VITE_API_URL` | `https://meteorite-explorer-api.onrender.com` |
| Web service → **Environment** | `CORS_ORIGINS` | `https://meteorite-explorer.onrender.com` |

- **No trailing slashes.**
- **No `/api` prefix** — backend routes are `/meteorites`, `/health`, etc.
- After changing `VITE_API_URL`, **redeploy the static site** (value is baked in at build time).
- After changing `CORS_ORIGINS`, redeploy or restart the API service.

---

## 4. Database — what actually happens

No separate DB deploy:

1. `meteorite_landings.csv` is in `backend/` (committed).
2. API **build** runs `python -m app.scripts.ingest_meteorites` → `meteorites.db`.
3. AI explanation cache lives in the same SQLite file.

---

## 5. Auto-deploy

Both services redeploy on push to `main` by default. Future changes: `git push` and wait for Render builds.

---

## 6. Checklist before sharing the link

- [ ] `GET /health` returns OK on production API
- [ ] Frontend loads globe with meteorites (no CORS errors in console)
- [ ] Click a meteorite → details + AI insight work
- [ ] Submission includes **frontend URL** and **API URL**
- [ ] `.env.development` / secrets are not committed

---

## 7. Local production smoke test

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
