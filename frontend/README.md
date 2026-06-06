# Meteorite Explorer — Frontend

React + TypeScript frontend with an interactive 3D globe for exploring NASA meteorite landings.

## Setup

**Node.js 20.19+ or 22.12+** required (Vite 8). Check with `node -v`.

```bash
cd frontend
npm install
```

## Development

Start the backend first (from `backend/`):

```bash
uvicorn app.main:app --reload
```

Then run the frontend:

```bash
npm run dev
```

Open http://localhost:5173

Vite proxies `/api` to `http://127.0.0.1:8000` during development.

## Environment

Vite loads env files by mode — no manual exports needed for local dev.

| File | Mode | Purpose |
|------|------|---------|
| `.env.development` | `npm run dev` | Dev API proxy path (gitignored) |
| `.env.production` | `npm run build` | Deployed API URL (gitignored; copy from `.env.production.example`) |
| `.env.local` | both | Optional local overrides (gitignored) |

| Variable | Dev default | Description |
|----------|-------------|-------------|
| `VITE_API_URL` | `/api` | Backend API base URL |

Production build (local) or set `VITE_API_URL` in Render static site env for deploy:

```bash
cp .env.production.example .env.production
npm run build
```

## Build

```bash
npm run build
npm run preview
```

## Structure

```text
src/
├── api/meteorites.ts
├── components/
│   ├── Globe.tsx
│   ├── Globe.tsx
│   ├── GlobeInsightCard.tsx
│   ├── FilterPanel.tsx
│   └── MeteoriteDetails.tsx
├── types/meteorite.ts
├── utils/format.ts
├── App.tsx
└── main.tsx
```
