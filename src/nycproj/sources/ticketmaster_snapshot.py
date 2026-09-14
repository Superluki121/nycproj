#!/usr/bin/env python3
import json, os, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

API = "https://app.ticketmaster.com/discovery/v2/events.json"
KEY = os.environ["TICKETMASTER_API_KEY"]
OUT = Path(os.environ.get("NYCPROJ_DATA", "/srv/nycproj/data")) / "raw" / "ticketmaster"

SIZE = 200
MAX_PAGES = 1000 // SIZE      # harte Grenze der API
DAYS_BACK = 7                 # kuerzlich Vergangenes mitnehmen
DAYS_AHEAD = 400
PAUSE = 0.3                   # Sekunden zwischen Requests


def tm_time(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(page, start, end):
    for versuch in range(5):
        r = requests.get(API, params={
            "apikey": KEY, "city": "New York", "stateCode": "NY",
            "startDateTime": tm_time(start), "endDateTime": tm_time(end),
            "size": SIZE, "page": page, "sort": "date,asc",
        }, timeout=60)
        if r.status_code == 429:
            time.sleep(2 ** versuch)
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    r.raise_for_status()


def scheibe(start, end, target, stamp, tiefe=0):
    """Holt eine Zeitscheibe. Teilt sich selbst, wenn sie zu gross ist."""
    erste = fetch(0, start, end)
    gesamt = erste["page"]["totalElements"]

    if gesamt > 1000 and tiefe < 3:
        mitte = start + (end - start) / 2
        return (scheibe(start, mitte, target, stamp, tiefe + 1)
                + scheibe(mitte, end, target, stamp, tiefe + 1))

    if gesamt > 1000:
        print(f"WARNUNG: {start:%Y-%m-%d} bis {end:%Y-%m-%d} hat {gesamt} "
              f"Events, nicht weiter teilbar", file=sys.stderr)

    label = f"{start:%Y%m%d}-{end:%Y%m%d}"
    seiten = min(erste["page"]["totalPages"], MAX_PAGES)
    geholt = 0

    for p in range(seiten):
        data = erste if p == 0 else fetch(p, start, end)
        tmp = target / f"slice-{label}_page-{p:03d}-{stamp}.json.tmp"
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.rename(target / f"slice-{label}_page-{p:03d}-{stamp}.json")
        geholt += len(data.get("_embedded", {}).get("events", []))

    return geholt


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    target = OUT / f"date={now:%Y-%m-%d}"
    target.mkdir(parents=True, exist_ok=True)

    start = (now - timedelta(days=DAYS_BACK)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    ende = now + timedelta(days=DAYS_AHEAD)

    gesamt = 0
    while start < ende:
        bis = min(start + timedelta(days=7), ende) - timedelta(seconds=1)
        gesamt += scheibe(start, bis, target, stamp)
        start += timedelta(days=7)

    print(f"{gesamt} Events -> {target}", file=sys.stderr)


if __name__ == "__main__":
    main()