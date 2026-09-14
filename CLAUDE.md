# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`nycproj` collects NYC-area event data (Ticketmaster, and planned Setlist.fm / NYC Open Data via Socrata) into raw/interim/processed data layers for later analysis. Very early stage: one working source script, no tests yet, README/notebooks/venues config still empty.

## Commands

Package manager is `uv` (build backend `uv_build`), Python >=3.12.

- Install deps: `uv sync`
- Run a script: `uv run python src/nycproj/sources/ticketmaster_snapshot.py`
- Lint: `uv run ruff check .`
- Jupyter (dev dep): `uv run jupyter lab`

No test suite exists yet.

## Architecture

- `src/nycproj/config.py` — central config. Defines `DATA_DIR` (from env var `NYCPROJ_DATA`, default `/srv/nycproj/data`) with `RAW`/`INTERIM`/`PROCESSED` subdirs, and loads `.env` from **`DATA_DIR.parent/.env`** (not the repo root). Required env vars: `SETLISTFM_API_KEY`, `SOCRATA_APP_TOKEN`, `TICKETMASTER_API_KEY` (accessed via `os.environ[...]`, so missing vars raise `KeyError` at import time). Note `.env.example` currently lists only `SETLISTFM_API_KEY` and `TICKETMASTER_API_KEY` — `SOCRATA_APP_TOKEN` must be added when the Socrata source is added.
- `src/nycproj/sources/` — one script per external data source. Each is a standalone daily-snapshot script (reads its own env vars directly via `os.environ`, not via `config.py`), writes newline-free JSON pages under `RAW/<source>/date=YYYY-MM-DD/`, using a write-to-`.tmp`-then-`rename` pattern so a crash never leaves a partial file in place.
  - `ticketmaster_snapshot.py`: pulls the Ticketmaster Discovery API for a 20-mile radius around Greenpoint (covers all five boroughs + MetLife/Long Island). Because the API hard-caps at ~1000 results per query, the date range is split into weekly slices, and any slice still over 1000 results recursively bisects (up to `MAX_SPLIT` times). Venue filtering by borough/city is intentionally deferred to `config/venues_nyc.csv` (not yet populated) rather than done at fetch time.
- `config/venues_nyc.csv` — post-hoc venue allowlist/filter, applied downstream of raw ingestion (currently empty).
- Data itself (`data/`, `*.parquet`, `.env`) is gitignored — this repo holds only code/config, not data.

## Conventions

- Source comments/docstrings in `ticketmaster_snapshot.py` are written in German; match that when editing the file.
