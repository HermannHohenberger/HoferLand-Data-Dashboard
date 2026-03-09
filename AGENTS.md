# AGENTS.md

## Purpose
This file provides persistent project context for AI coding agents working in this repository.

## Project Snapshot
- Name: `HoferLand Data Dashboard`
- Goal: compare population time series across selected regions
- Stack:
  - Backend: FastAPI + SQLAlchemy + SQLite
  - Frontend: React (Vite + TypeScript) + Recharts + Tailwind
  - Source: Genesis REST API (`regionalstatistik.de`)

## Working Language
- Prefer German in user-facing communication unless the user asks otherwise.

## Runbook

### First-time setup
- Backend: create `backend/.venv` and install `backend/requirements.txt`
- Frontend: run `npm install` in `frontend`
- Configure root `.env` (see `.env.example`)

### Daily start
- Backend:
  - `cd backend`
  - `source .venv/bin/activate`
  - `uvicorn app.main:app --reload`
- Frontend:
  - `cd frontend`
  - `npm run dev`

## Backend Conventions
- Seed regions in `backend/app/main.py` via `seed_regions()`
- Seeding must be idempotent (insert missing, update renamed entries)
- Population indicator code is `BEV001`
- Core tables: `regions`, `indicators`, `data_points`
- `indicators` includes `description` (used by frontend source box)

## Genesis API Conventions
- Auth is sent via HTTP headers:
  - `username`
  - `password`
- Main population table currently used: `12411-01-01-4`
- `data/table` returns JSON where tabular content is in `Object.Content` (CSV-like text)

## ETL Behavior
- Detail ETL endpoint: `POST /api/etl/run`
  - loads 5-digit AGS regions (Kreise/kreisfreie Städte)
- Main area-based ETL endpoint: `POST /api/etl/run-sequential`
  - supports `areas=...` and `start_year=...`
  - returns per-area payload: `inserted_or_updated`, `status`, `message`
- Aggregate ETL endpoint: `POST /api/etl/run-aggregates`
  - fills aggregate regions `09` (Bayern) and `094` (Oberfranken)
- Frontend button triggers both ETLs (`runEtlAll`)
- ETL updates indicator metadata (table code + description)
- `durchschnittsalter` ETL handles partial source failures gracefully:
  - if data was loaded, keep area status `ok` and append partial-error hint to message
  - set `error` only if no data could be loaded at all

## Frontend Notes
- Dashboard page: `frontend/src/pages/Dashboard.tsx`
- Region selection is checkbox-based (multi-select, up to all 11 regions)
- Indicator/bereich selection is checkbox-based and supports multi-select
- Line chart renders one series per region+indicator combination
  - labels adapt based on selection scope (`Region - Bereich`, only Bereich, or only Region)
- Lower table box is `Veraenderung` with columns:
  - Region
  - Aktueller Wert
  - Veraenderung absolut
  - Veraenderung in %
- Comparison year dropdown is inside the lower `Veraenderung` box
- Top-right card is `Datenquelle` and shows:
  - link to `https://www.regionalstatistik.de`
  - active Genesis table code
  - indicator description
- Region row color in `Veraenderung` table must match line chart color
- ETL success and error messages are shown in the UI
- Decimal display defaults:
  - `AGE_*`, `AL_RATE`, `BEV_FOREIGN_SHARE` with 1 decimal
  - other indicators with 0 decimals
- Top navigation includes `Dashboard`, `Ueber`, `Impressum`
  - `Maintenance` is intentionally not linked in public navigation
- Static content pages:
  - `frontend/src/pages/Ueber.tsx` loads `frontend/public/ueber.md`
  - `frontend/src/pages/Impressum.tsx` loads `frontend/public/impressum.md`

## Important Endpoints
- `GET /health`
- `GET /api/regions`
- `GET /api/indicators`
- `GET /api/data`
- `GET /api/data/latest`
- `POST /api/etl/run`
- `POST /api/etl/run-sequential`
- `POST /api/etl/run-aggregates`
