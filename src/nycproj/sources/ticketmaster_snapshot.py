#!/usr/bin/env python3
"""Taeglicher Snapshot der Ticketmaster Discovery API fuer den Grossraum NYC.

Die API laesst sich nicht beliebig tief durchblaettern (harte Grenze bei rund
1000 Treffern pro Abfrage). Deshalb wird der Zeitraum in Wochenscheiben
zerlegt; zu volle Scheiben halbieren sich selbst.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API = "https://app.ticketmaster.com/discovery/v2/events.json"
KEY = os.environ["TICKETMASTER_API_KEY"]
OUT = Path(os.environ.get("NYCPROJ_DATA", "/srv/nycproj/data")) / "raw" / "ticketmaster"

SIZE = 200                    # Treffer pro Seite, Maximum der API
MAX_PAGES = 1000 // SIZE      # harte Paging-Grenze
DAYS_BACK = 7                 # kuerzlich Vergangenes mitnehmen
DAYS_AHEAD = 400
SLICE_DAYS = 7
MAX_SPLIT = 3                 # maximale Halbierungstiefe pro Scheibe
PAUSE = 0.3                   # Sekunden zwischen Requests

# Greenpoint als Mittelpunkt, 20 Meilen decken alle fuenf Boroughs ab
# sowie MetLife (NJ) und ein Stueck Long Island. Aussortiert wird spaeter
# ueber config/venues_nyc.csv, nicht beim Abruf.
LATLONG = "40.7328,-73.9510"
RADIUS = "20"
UNIT = "miles"


def tm_time(dt):
    """Ticketmaster erwartet UTC ohne Millisekunden."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(page, start, end):
    """Eine Seite holen, mit Backoff bei 429."""
    for versuch in range(5):
        r = requests.get(
            API,
            params={
                "apikey": KEY,
                "latlong": LATLONG,
                "radius": RADIUS,
                "unit": UNIT,
                "startDateTime": tm_time(start),
                "endDateTime": tm_time(end),
                "size": SIZE,
                "page": page,
                "sort": "date,asc",
            },
            timeout=60,
        )
        if r.status_code == 429:
            time.sleep(2 ** versuch)
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    r.raise_for_status()


def scheibe(start, end, target, stamp, tiefe=0):
    """Holt eine Zeitscheibe. Halbiert sich selbst, wenn sie zu voll ist."""
    erste = fetch(0, start, end)
    gesamt = erste["page"]["totalElements"]

    if gesamt > 1000 and tiefe < MAX_SPLIT:
        mitte = start + (end - start) / 2
        return (scheibe(start, mitte, target, stamp, tiefe + 1)
                + scheibe(mitte, end, target, stamp, tiefe + 1))

    if gesamt > 1000:
        print(f"WARNUNG: {start:%Y-%m-%d} bis {end:%Y-%m-%d} meldet {gesamt} "
              f"Events und laesst sich nicht weiter teilen", file=sys.stderr)

    label = f"{start:%Y%m%dT%H%M}-{end:%Y%m%dT%H%M}"
    seiten = min(erste["page"]["totalPages"], MAX_PAGES)
    geholt = 0

    for p in range(seiten):
        data = erste if p == 0 else fetch(p, start, end)
        # erst .tmp, dann umbenennen: ein Abbruch hinterlaesst keine
        # halbe Datei, und das Umbenennen bleibt im selben Verzeichnis,
        # damit die Default-ACL greift
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

    gesamt, scheiben = 0, 0
    while start < ende:
        bis = min(start + timedelta(days=SLICE_DAYS), ende) - timedelta(seconds=1)
        gesamt += scheibe(start, bis, target, stamp)
        scheiben += 1
        start += timedelta(days=SLICE_DAYS)

    print(f"{gesamt} Events aus {scheiben} Zeitscheiben -> {target}", file=sys.stderr)


if __name__ == "__main__":
    main()