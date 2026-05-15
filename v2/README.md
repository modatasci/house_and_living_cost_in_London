# Housing in London — v2

Modern rewrite of the original Streamlit prototype (`../src/`). The legacy app is left untouched for reference.

## Layout

```
v2/
├── api/    FastAPI backend (Python 3.11+) — deployed to Fly.io
└── web/    React + Vite + MapLibre SPA   — deployed to Cloudflare Pages (next step)
```

## Backend — `api/`

### Local dev

```bash
cd v2/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then fill TFL_APP_KEY
uvicorn app.main:app --reload --port 8000
```

Smoke test:

```bash
curl http://localhost:8000/api/healthz
curl "http://localhost:8000/api/postcodes/search?q=SW1A"
curl -X POST http://localhost:8000/api/compare \
  -H 'content-type: application/json' \
  -d '{"destination":"EC2Y 5BL","origins":["UB7 7GJ"],"prefs":{"days_per_week":3}}'
```

### Endpoints

| Method | Path                          | Purpose |
| ------ | ----------------------------- | ------- |
| GET    | `/api/healthz`                | Liveness + config snapshot |
| GET    | `/api/postcodes/search?q=`    | Prefix autocomplete |
| GET    | `/api/postcodes/lookup?postcode=` | Single postcode → borough |
| GET    | `/api/postcodes/nearest?lat=&lng=` | Reverse geocode (needs coord index) |
| GET    | `/api/boroughs`               | All 33 London boroughs |
| POST   | `/api/compare`                | Multi-origin commute + cost comparison |

### Building the postcode coordinate index (optional but needed for map-click reverse geocoding)

```bash
cd v2/api
pip install -e ".[build]"   # adds geopandas, pyproj, pyarrow
python scripts/build_postcode_index.py
# writes app/data/postcodes.parquet (~10 MB)
```

This reads `data/geodata/Code-Point London (shapefile)/CodePointOpen_London_201709.shp`, reprojects to WGS84, and joins lat/lng onto the borough lookup. Run once locally, then commit nothing — the Dockerfile bakes it in via `COPY v2/api/app/data` if present, or build it inside the image.

### Deploy to Fly.io

Build context is the **repo root** so the image can include `data/` and the optional parquet:

```bash
fly launch --no-deploy --copy-config --config v2/api/fly.toml --dockerfile v2/api/Dockerfile
fly secrets set TFL_APP_KEY=xxxx --config v2/api/fly.toml
fly deploy --config v2/api/fly.toml --dockerfile v2/api/Dockerfile
```

## Frontend — `web/`

Not yet scaffolded. Next phase: Vite + React + TS + Tailwind + shadcn/ui + MapLibre.
