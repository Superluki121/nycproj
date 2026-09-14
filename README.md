# nycproj

NYC event data collection. Pulls event data from Ticketmaster (and, planned, Setlist.fm and NYC Open Data via Socrata) into raw/interim/processed data layers for later analysis.

Early stage: one working source script, no tests, venue filter config still empty.

## Setup

```bash
uv sync
cp .env.example .env   # fill in API keys, then move/point to DATA_DIR.parent/.env
```

Config (`src/nycproj/config.py`) reads:

- `NYCPROJ_DATA` — data directory root (default `/srv/nycproj/data`), holding `raw/`, `interim/`, `processed/`
- `.env` loaded from `NYCPROJ_DATA`'s **parent** directory, not the repo root
- Required keys: `SETLISTFM_API_KEY`, `SOCRATA_APP_TOKEN`, `TICKETMASTER_API_KEY`

## Usage

```bash
uv run python src/nycproj/sources/ticketmaster_snapshot.py
```

Fetches a daily snapshot of events within a 20-mile radius of Greenpoint (covers all five boroughs plus MetLife and part of Long Island) and writes JSON pages to `raw/ticketmaster/date=YYYY-MM-DD/`. Borough/venue filtering happens downstream via `config/venues_nyc.csv`, not at fetch time.

## Development

```bash
uv run ruff check .
uv run jupyter lab
```
