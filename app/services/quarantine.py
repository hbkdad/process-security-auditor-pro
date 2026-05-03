import shutil, json, os, time, hashlib
from pathlib import Path
from app.core.paths import QUARANTINE_DIR

def quarantine_file(path):
    src = Path(path)
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(path)
    h = hashlib.sha256(src.read_bytes()).hexdigest()
    dest = QUARANTINE_DIR / f"{int(time.time())}_{src.name}.quarantine"
    shutil.move(str(src), str(dest))
    meta = {"original_path": str(src), "quarantine_path": str(dest), "sha256": h, "time": int(time.time())}
    (dest.with_suffix(dest.suffix + ".json")).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta
