# Considerations & Improvements

This document captures design decisions, tradeoffs, and iteration history from building Meteorite Explorer — especially areas refined during development that are not fully spelled out in [product.md](product.md) or [tech_spec.md](tech_spec.md).

Use it as a companion when reviewing the project, onboarding, or planning next steps.

---

## What We Built & Iterated On

### AI explanation caching

Generated explanations are cached in SQLite (`meteorite_ai_explanations`) rather than calling the model on every request.

A cache hit requires all of the following to match:

- `meteorite_id`
- `prompt_version`
- `model`
- `row_fingerprint` (hash of meteorite fields used in the prompt)
- `expires_at` still in the future (30-day TTL for the MVP)

This avoids stale explanations when underlying meteorite data or prompt logic changes, while still reducing cost and latency for repeat views. Generation uses OpenAI (`gpt-4o-mini` by default) when `OPENAI_API_KEY` is set on the server.

### Backend error handling

FastAPI global exception handlers normalize errors into consistent JSON responses:

- `AppError` subclasses (e.g. `MeteoriteNotFoundError` → 404)
- Pydantic `ValidationError` → 422 with structured `detail`
- SQLAlchemy errors → generic 500 message (logged server-side)
- Unhandled exceptions → generic 500 message (logged server-side)

The frontend can rely on a predictable `{ detail: ... }` shape instead of parsing ad hoc error formats.

### Paginated list API

`GET /meteorites` supports `limit` and `offset` (validated via `MeteoriteListParams`, default limit 1000, max 10000). Responses include:

```json
{ "items": [...], "total": N, "limit": L, "offset": O }
```

Pagination keeps payloads bounded and lets the frontend request only what the globe can usefully display.

### Viewport-scoped fetching

Instead of loading all ~45k meteorites at once, the frontend:

1. Estimates visible lat/lng bounds from the globe camera (`utils/viewport.ts`)
2. Sends `min_lat`, `max_lat`, `min_lng`, `max_lng` to the API when zoomed in
3. Falls back to a worldwide sample when the view is effectively global

The backend applies bbox filtering with antimeridian-aware logic for regions crossing the date line.

See the **Viewport-scoped data loading** callout in [tech_spec.md](tech_spec.md) for current fetch limits and refetch rules.

### Viewport refetch tuning (explored, partially reverted)

We iterated on how aggressively to refetch as the user pans and zooms:

- Fetch on camera `end` (not every frame), 500ms debounce, significance thresholds (~4° lat / ~6° lng / ~0.15 altitude) before updating viewport state

### 2D map → 3D globe

The product originally described a flat interactive map. During implementation we moved to **react-globe.gl** for a 3D Earth visualization — better aligned with the space/science theme and more engaging for exploration.

Globe-specific UX that followed:

- Individual 3D markers (`pointsMerge={false}`) so each meteorite supports click and hover tooltips
- Mass-based **width** scaling (log scale, capped) plus subtle **height** variation
- Hover tooltips (name, class, fall, year) with styling fixed for the library’s dark tooltip background
- Fly-to animation when a meteorite is selected from the sidebar

### Performance-oriented globe choices

Several approaches were tried and adjusted:

| Approach | Outcome |
| -------- | ------- |
| Hex bin aggregation when zoomed out | Removed — column height (`sumWeight × 0.01`) produced misleading “skyscraper” visuals in dense regions |
| Merged point geometry | Avoided — disables per-point click/hover in globe.gl |
| Render cap (~1,200 points) | Kept — even sampling from fetched set, always retaining selected meteorite |
| Stale-while-revalidate | Kept — previous markers stay visible while a viewport refetch is in flight |

### Filter & validation improvements

- Shared `MeteoriteListParams` schema validates query params (year ranges, mass bounds, fall enum, etc.)
- `search` matches **meteorite name only**; classification uses the dedicated `recclass` filter
- Sidebar copy reflects viewport-scoped vs worldwide totals

---

## Considerations

These are ongoing tradeoffs to keep in mind when changing the globe or API.

### Scale

~45k records is small for a database but large for unconstrained browser rendering. Any design that loads or draws the full dataset will feel slow. Caps and sampling are intentional, not oversights.

### Viewports & density

Zoomed-out views fetch a **global sample**; zoomed-in views fetch **regional** data. The same ~1,200 render budget concentrated in a smaller area makes zoomed-in regions look much denser — that is expected, not a bug.

Switching between global and regional mode also changes what `total` means in the sidebar (worldwide matching count vs in-view matching count).

### Filtering vs. map bounds

Filters (search, class, year, mass, fall) apply on top of viewport bounds when zoomed in. Tight filters + regional view can legitimately return very few markers; loose filters in Antarctica can still hit fetch/render caps.

### Performance

The main bottleneck is **unmerged 3D meshes** on the globe, not the SQLite query. Improvements that add more on-screen objects or refetch on every camera frame will hurt responsiveness quickly.

Significance thresholds for refetch are a blunt instrument: small pans may not update data, while large pans do. Finer-grained tuning (or padded prefetch) remains open work.

### AI cost & latency

Even with caching, the first explanation for a meteorite will incur model latency and cost. Long term, sync request/response may not scale if explanations become popular or prompts grow richer.

### SQLite & spatial queries

Bbox filtering uses simple lat/lng comparisons on indexed columns — sufficient for the MVP. Complex spatial analytics (radius search, clustering, heatmaps) would push toward PostGIS or similar.

---

## Future Improvements

### Caching meteorite list data

| Layer | Idea |
| ----- | ---- |
| **Client** | Cache recent viewport responses (keyed by bbox + filter hash) to avoid refetching when panning back to a visited region |
| **Server** | Short TTL cache (Redis/in-memory) for common bbox + filter combinations |
| **CDN / HTTP** | `Cache-Control` on read-only list endpoints where appropriate |

Distinct from AI explanation caching — this targets the high-churn globe fetch path.

### AI: async jobs & pre-generation

| Improvement | Benefit |
| ----------- | ------- |
| **Async job queue** | `POST /explanation` enqueues work; client polls or receives a webhook/SSE when ready — avoids long HTTP hangs |
| **Pre-generate summaries** | Batch job over top-N or all meteorites after ingestion; most selections become instant cache hits |
| **Streaming** | Stream tokens to the UI for perceived faster response on cache miss |

The cache schema (`row_fingerprint`, `prompt_version`, TTL) already supports pre-generation — workers would call the same store path as the live API.

### Viewport & globe UX

- Revisit **padded fetch bounds** with proper tuning and tests
- **Zoom-adaptive** significance thresholds (stricter when zoomed in, looser when zoomed out)
- Optional **flat 2D mode** or map fallback for low-power devices
- Revisit **hex aggregation** only if height is decoupled from mass/count (e.g. flat hex tiles, color by density)

### Backend & data

- **PostGIS** for spatial indexing and richer queries
- **Background ingestion** pipeline if the dataset becomes dynamic
- **Rate limiting** on AI endpoints before production traffic

### Product & deployment

- Wire up **OpenAI** in production — set `OPENAI_API_KEY` (see `backend/.env.example`)
- Deploy frontend (e.g. Vercel) + backend (e.g. Render/Fly) with env-based config
- Align [product.md](product.md) copy with 3D globe (still references a flat map in places)

### Observability

- Structured logging around viewport fetches (bbox, duration, result count)
- Client metrics for time-to-interactive globe and refetch frequency
- AI cache hit rate dashboard

---

## Quick Reference: Current Frontend Limits

| Constant | Value | Purpose |
| -------- | ----- | ------- |
| `MAX_RENDER_POINTS` | 1,200 | Max markers drawn on globe |
| `MAX_FETCH_GLOBAL` | 3,500 | Worldwide fetch cap |
| `MAX_FETCH_VIEWPORT` | 2,500 | Regional fetch cap |
| Viewport debounce | 500ms | Delay before API call after camera stop |
| Significance thresholds | 4° lat, 6° lng, 0.15 alt | Minimum camera move before viewport state updates |

---

## Related Docs

- [product.md](product.md) — product vision, users, features
- [tech_spec.md](tech_spec.md) — architecture, API, database, viewport callout
- [backend/README.md](backend/README.md) — API filters, local setup, tests
- [frontend/README.md](frontend/README.md) — frontend setup
