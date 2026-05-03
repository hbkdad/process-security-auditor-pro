from pathlib import Path
import os, sys

APPDATA = Path(os.getenv("APPDATA", Path.home())) / "ProcessSecurityAuditorAVPro"
APPDATA.mkdir(parents=True, exist_ok=True)

DB_PATH = APPDATA / "auditor.db"
LOG_PATH = APPDATA / "auditor.log"
LICENSE_PATH = APPDATA / "license.json"
QUARANTINE_DIR = APPDATA / "quarantine"
QUARANTINE_DIR.mkdir(exist_ok=True)

def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / relative
