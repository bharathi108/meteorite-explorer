# Technical Design

## Overview

Meteorite Explorer is a full-stack web application that allows users to explore NASA's Meteorite Landings dataset through an interactive 3D globe, advanced filtering capabilities, and AI-generated explanations.

The application transforms raw meteorite data into an engaging educational experience by combining geospatial visualization with AI-powered explanations that help users understand the scientific significance of meteorites without requiring specialized knowledge.

The architecture prioritizes simplicity, maintainability, and ease of local development while demonstrating production-minded decisions around API design, caching, data modeling, and future extensibility.

For iteration history, tradeoffs, and planned improvements, see [considerations_and_improvements.md](considerations_and_improvements.md).

The repository is organized into separate frontend and backend services:

```text
meteorite-explorer/
├── backend/
├── frontend/
└── README.md
```

This separation creates clear ownership boundaries between the presentation layer and backend services while making it easier to evolve or deploy components independently.

---

# Technology Choices

## Backend

### Python

Python was chosen because it provides excellent support for:

- Data processing
- Dataset ingestion
- AI integration
- Rapid API development

The NASA dataset can be cleaned and transformed efficiently using Pandas before being loaded into the application database.

---

### FastAPI

FastAPI was selected because it provides:

- Lightweight API development
- Automatic request validation
- Strong typing support
- Excellent performance
- Automatic OpenAPI documentation

The built-in Swagger UI also makes it easy for reviewers to explore and test the API.

---

### SQLite

SQLite was chosen for the MVP because:

- The dataset is relatively small
- Data is largely static
- No external infrastructure is required
- The application can be run locally with minimal setup

For the MVP, latitude and longitude values are simply stored and returned to the frontend for visualization.

While a geospatial database such as PostGIS would be useful for advanced spatial analysis, it introduces unnecessary complexity for the current scope.

---

### Pandas

Pandas is used for dataset ingestion and transformation.

Responsibilities include:

- Cleaning missing values
- Parsing dates
- Standardizing fields
- Preparing records for database insertion

---

### OpenAI API

The OpenAI API is used to generate educational explanations for meteorites.

Rather than displaying scientific classifications directly, AI acts as a translation layer that converts technical meteorite data into concise, human-readable explanations.

---

## Frontend

### React

React was selected because the application is highly interactive and state-driven.

Users interact with:

- Search controls
- Filters
- Globe visualization
- Meteorite detail panels
- AI-generated explanations

React's component architecture naturally supports these requirements.

---

### TypeScript

TypeScript provides:

- Strong typing
- Better IDE support
- Safer API integrations
- Improved maintainability

Meteorite records and API responses are represented using shared interfaces across the application.

---

### Vite

Vite was chosen because it provides:

- Fast local development
- Minimal configuration
- Excellent TypeScript support

---

### React Three Fiber + Three Globe

Instead of using a traditional 2D map, the application uses a 3D globe visualization.

Libraries:

- React Three Fiber
- Three Globe

The 3D globe better aligns with the space and planetary science theme while providing a more engaging user experience.

Features include:

- Rotatable Earth visualization
- Zoom and pan controls
- Meteorite landing markers
- Click interactions for meteorite details

A traditional map would communicate the data effectively, but the globe creates a more memorable and visually compelling experience.

---

# High-Level Architecture

```text
NASA Meteorite Dataset
          │
          ▼
 Data Ingestion Script
          │
          ▼
      SQLite
          │
          ▼
      FastAPI
          │
          ▼
 React + TypeScript
          │
          ▼
      3D Globe
          │
          ▼
 Meteorite Details
 AI Explanations
```

---

# Backend Design

The backend is responsible for:

- Loading meteorite data
- Persisting meteorites into SQLite
- Supporting filtering and search
- Returning meteorite details
- Generating AI explanations
- Managing explanation caching

---

## Backend Folder Structure

```text
backend/
├── app/
│   ├── main.py
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
├── requirements.txt
└── README.md
```

---

# Database Design

## meteorites

Stores meteorite records imported from NASA.


| Column     | Description               |
| ---------- | ------------------------- |
| id         | Internal identifier       |
| name       | Meteorite name            |
| nametype   | Record validity indicator |
| recclass   | Meteorite classification  |
| mass_grams | Mass in grams             |
| fall       | Fell or Found             |
| year       | Discovery or fall year    |
| latitude   | Latitude                  |
| longitude  | Longitude                 |


---

## meteorite_ai_explanations

Stores AI-generated explanations.


| Column          | Description                |
| --------------- | -------------------------- |
| id              | Internal identifier        |
| meteorite_id    | Associated meteorite       |
| prompt_version  | Prompt version             |
| model           | LLM model used             |
| row_fingerprint | Hash of meteorite data     |
| explanation     | Generated explanation      |
| created_at      | Creation timestamp         |
| expires_at      | Cache expiration timestamp |


For this MVP, `expires_at` is set to 30 days after explanation generation.

---

# AI Explanation Caching

AI-generated explanations are cached to reduce:

- API costs
- Response latency
- Output variability

Caching solely by meteorite ID is insufficient because explanations depend on the meteorite data used within the prompt.

If attributes such as mass, classification, year, or location change, the existing explanation may no longer be accurate.

To ensure correctness, cache entries are keyed using:

```text
meteorite_id
+ prompt_version
+ model
+ row_fingerprint
```

The row fingerprint is generated from the meteorite attributes used in the prompt.

Example:

```python
sha256(
    f"{name}|{recclass}|{mass_grams}|{fall}|{year}|{latitude}|{longitude}"
)
```

Each cache entry also contains an expiration timestamp.

For this MVP, explanations expire after 30 days.

Explanation retrieval follows this process:

```text
Request Explanation
        │
        ▼
Check Cache
        │
        ▼
Valid Cache Entry?
├── Yes → Return Cached Explanation
└── No
       │
       ▼
Generate Explanation
       │
       ▼
Store New Cache Entry
       │
       ▼
Return Explanation
```

This strategy automatically invalidates cached content when:

- Prompt logic changes
- Model versions change
- Meteorite data changes
- Cached content expires

A cache entry is considered valid only if the `row_fingerprint`, `prompt_version`, and `model` match, and `expires_at` is greater than the current timestamp.

---

# API Design

## GET /meteorites

Returns meteorite records for globe visualization.

### Supported Filters

```text
search
recclass
fall
min_year
max_year
min_mass
max_mass
min_lat / max_lat / min_lng / max_lng   (optional viewport bounding box)
limit
offset
```

When a bounding box is provided, results are limited to meteorites whose coordinates fall inside the box (with antimeridian-aware handling on the backend).

---

## GET /meteorites/{id}

Returns detailed information for a selected meteorite.

---

## POST /meteorites/{id}/explanation

Returns an AI-generated explanation.

Workflow:

```text
Check Cache
     │
     ▼
Cache Hit?
├── Yes → Return Cached Explanation
└── No
       │
       ▼
Generate Explanation
       │
       ▼
Persist Cache Entry
       │
       ▼
Return Explanation
```

---

# Frontend Design

The frontend is responsible for:

- Rendering the 3D globe
- Displaying meteorite markers
- Managing filters
- Displaying meteorite details
- Displaying AI-generated explanations

---

## Frontend Folder Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── Globe.tsx
│   │   ├── FilterPanel.tsx
│   │   ├── MeteoriteDetails.tsx
│   │   └── AIExplanation.tsx
│   ├── api/
│   │   └── meteorites.ts
│   ├── types/
│   │   └── meteorite.ts
│   ├── utils/
│   │   ├── viewport.ts
│   │   ├── globe.ts
│   │   └── format.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── README.md
```

---

### Viewport-scoped data loading

> **Globe zoom behavior:** The frontend does not load all ~45k meteorites at once. When the camera shows most of the planet (“global” view), it fetches a worldwide sample (up to ~3,500 records, no bbox). When the user zooms in past a threshold, it switches to **viewport-scoped** fetching: only meteorites inside the visible lat/lng bounds are requested (up to ~2,500). The globe renders at most ~1,200 markers via even sampling, always keeping the selected meteorite visible.
>
> **Why we did this:** The full dataset is too large to push through the stack unchanged. Rendering tens of thousands of individual 3D markers tanks browser performance, and we need unmerged points (`pointsMerge={false}`) so each marker supports click and hover tooltips. Fetching everything on every camera move would also hammer the API and cause constant UI flicker. Viewport-scoped loading is the compromise: a lightweight worldwide sample for orientation when zoomed out, then progressively richer regional data as the user focuses on an area — without ever trying to draw all 45k points at once.
>
> **Why it can look denser when zoomed in:** The same render cap is concentrated in a smaller geographic area, so regional views (e.g. Antarctica) appear much busier than a worldwide view where dots are spread across the entire Earth. That density shift is a side effect of the design, not a bug — we accept sparser global views in exchange for meaningful local detail when exploring a region.
>
> **Refetch triggers:** Viewport updates fire when camera movement stops (not every animation frame). A refetch is skipped until the camera moves meaningfully (~4° latitude, ~6° longitude, or ~0.15 altitude). Viewport bounds are debounced (~500ms) before hitting the API. Filter changes always trigger a fresh fetch. These guardrails reduce redundant requests while the user is still dragging or making small adjustments.

---

# Primary User Flow

```text
Open Application
        │
        ▼
Load Meteorite Dataset
        │
        ▼
Display Meteorites on 3D Globe
        │
        ▼
Apply Filters
        │
        ▼
Select Meteorite
        │
        ▼
View Meteorite Details
        │
        ▼
View AI Explanation
```

---

# AI Design

The AI feature is intentionally scoped to educational explanation generation rather than open-ended chat.

This keeps the feature:

- Useful
- Predictable
- Cost effective
- Easy to validate

The prompt contains structured meteorite information including:

```text
Name
Classification
Mass
Year
Fell/Found Status
Location
```

The model is instructed to:

- Explain the meteorite classification
- Describe scientific significance
- Compare the meteorite to others in the dataset
- Use plain language suitable for non-experts

Example prompt objective:

```text
Explain this meteorite for a student or science enthusiast.

Describe what the classification means, why it may be scientifically interesting, and how its size compares to typical meteorites.

Use concise, easy-to-understand language.
```

---

# Why Not Use a Geospatial Database?

A geospatial database such as PostGIS would become valuable if the application introduced:

- Radius searches
- Spatial clustering
- Heatmaps
- Geospatial indexing
- Predictive discovery modeling

The MVP only needs latitude and longitude coordinates to place meteorites on the globe.

SQLite is sufficient for these requirements and keeps local setup simple.

---

# Future Technical Enhancements

## Postgres + PostGIS

Introduce PostGIS for advanced geospatial analytics and spatial indexing.

---

## Meteorite Discovery Predictor

A future version of the application could identify regions with a high likelihood of future meteorite discoveries.

Potential inputs include:

- Historical meteorite density
- Geographic clustering patterns
- Terrain information
- Climate data
- Land cover information

The resulting model could generate a global heatmap highlighting areas that resemble regions with historically high discovery rates.

---

## Background Jobs

Move AI explanation generation into asynchronous workers for larger-scale workloads.

---

## User Accounts

Allow users to save:

- Favorite meteorites
- Saved searches
- Learning progress

---

## Deployment

Potential deployment architecture:

```text
Frontend: Vercel
Backend: Render
Database: SQLite

Future:
Frontend: Vercel
Backend: Fly.io / AWS
Database: Postgres + PostGIS
```

---

# Summary

Meteorite Explorer is a lightweight, production-minded full-stack application that transforms NASA's meteorite dataset into an interactive educational experience.

By combining a 3D globe visualization, structured search capabilities, and AI-generated explanations, the application makes complex scientific data approachable for students, educators, and science enthusiasts while providing a foundation for future predictive and AI-powered exploration features.