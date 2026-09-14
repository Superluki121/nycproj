import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("NYCPROJ_DATA", "/srv/nycproj/data"))
RAW = DATA_DIR / "raw"
INTERIM = DATA_DIR / "interim"
PROCESSED = DATA_DIR / "processed"
