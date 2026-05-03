import requests
from app.core.config import VIRUSTOTAL_API_KEY, ABUSEIPDB_API_KEY

def virustotal_hash_lookup(sha256):
    if not VIRUSTOTAL_API_KEY or not sha256:
        return {"enabled": False}
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    r = requests.get(url, headers={"x-apikey": VIRUSTOTAL_API_KEY}, timeout=20)
    if r.status_code == 404:
        return {"enabled": True, "found": False}
    r.raise_for_status()
    data = r.json()
    stats = data.get("data",{}).get("attributes",{}).get("last_analysis_stats",{})
    return {"enabled": True, "found": True, "stats": stats}

def abuseipdb_lookup(ip):
    if not ABUSEIPDB_API_KEY or not ip:
        return {"enabled": False}
    url = "https://api.abuseipdb.com/api/v2/check"
    r = requests.get(url, headers={"Key": ABUSEIPDB_API_KEY, "Accept":"application/json"}, params={"ipAddress": ip, "maxAgeInDays":90}, timeout=20)
    r.raise_for_status()
    d = r.json().get("data",{})
    return {"enabled": True, "abuseConfidenceScore": d.get("abuseConfidenceScore"), "countryCode": d.get("countryCode")}
