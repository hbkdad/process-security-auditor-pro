import base64, json, hashlib, hmac, time
from app.core.paths import LICENSE_PATH

SECRET = b"CHANGE_THIS_BEFORE_SELLING"

TIERS = {
    "lite": {"live_monitor": False, "threat_intel": False, "quarantine": False, "exports": True},
    "pro": {"live_monitor": True, "threat_intel": True, "quarantine": True, "exports": True},
    "business": {"live_monitor": True, "threat_intel": True, "quarantine": True, "exports": True, "fleet": True},
}

def _sign(payload: str) -> str:
    return hmac.new(SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()

def generate_license(name: str, tier: str, expires_at: int) -> str:
    data = {"name": name, "tier": tier, "expires_at": expires_at}
    payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    sig = _sign(payload)
    return f"{payload}.{sig}"

def validate_license(key: str):
    try:
        payload, sig = key.strip().split(".", 1)
        if not hmac.compare_digest(_sign(payload), sig):
            return {"valid": False, "tier": "lite", "reason": "Bad signature", "features": TIERS["lite"]}
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        if int(data.get("expires_at", 0)) < int(time.time()):
            return {"valid": False, "tier": "lite", "reason": "Expired", "features": TIERS["lite"]}
        tier = data.get("tier", "lite").lower()
        return {"valid": True, **data, "features": TIERS.get(tier, TIERS["lite"])}
    except Exception as e:
        return {"valid": False, "tier": "lite", "reason": str(e), "features": TIERS["lite"]}

def save_license(key: str):
    LICENSE_PATH.write_text(json.dumps({"key": key}, indent=2), encoding="utf-8")

def load_license():
    if not LICENSE_PATH.exists():
        return {"valid": False, "tier": "lite", "reason": "No license", "features": TIERS["lite"]}
    try:
        key = json.loads(LICENSE_PATH.read_text(encoding="utf-8")).get("key", "")
        return validate_license(key)
    except Exception as e:
        return {"valid": False, "tier": "lite", "reason": str(e), "features": TIERS["lite"]}
