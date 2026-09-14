import os
from pathlib import Path
from dotenv import load_dotenv

DATA_DIR = Path(os.environ.get("NYCPROJ_DATA", "/srv/nycproj/data"))
RAW = DATA_DIR / "raw"
INTERIM = DATA_DIR / "interim"
PROCESSED = DATA_DIR / "processed"

load_dotenv(DATA_DIR.parent / ".env")

SETLISTFM_API_KEY = os.environ["SETLISTFM_API_KEY"]
SOCRATA_APP_TOKEN = os.environ["SOCRATA_APP_TOKEN"]
TICKETMASTER_API_KEY = os.environ["TICKETMASTER_API_KEY"]