#!/usr/bin/env python3
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
import requests

API = "https://app.ticketmaster.com/discovery/v2/events.json"
KEY = os.environ["TICKETMASTER_API_KEY"]
OUT = Path(os.environ.get("NYCPROJ_DATA", "/srv/nycproj/data")) / "raw" / "ticketmaster"
SIZE = 200
MAX_PAGES = 1000 // SIZE

def fetch(page):
    r = requests.get(API, params={
        "apikey": KEY, "city": "New York", "stateCode": "NY",
        "size": SIZE, "page": page, "sort": "date,asc",
    }, timeout=60)
    r.raise_for_status()
    return r.json()

def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    target = OUT / f"date={now:%Y-%m-%d}"
    target.mkdir(parents=True, exist_ok=True)

    page, pages, written = 0, 1, 0
    while page < pages and page < MAX_PAGES:
        data = fetch(page)
        pages = data["page"]["totalPages"]

        tmp = target / f"page-{page:03d}-{stamp}.json.tmp"
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.rename(target / f"page-{page:03d}-{stamp}.json")

        written += len(data.get("_embedded", {}).get("events", []))
        page += 1

    print(f"{written} Events, {page} Seiten, gemeldet {pages} -> {target}", file=sys.stderr)

if __name__ == "__main__":
    main()