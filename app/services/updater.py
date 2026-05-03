import json
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Dict, Any

GITHUB_REPO = "hbkdad/process-security-auditor-pro"
PREFERRED_ASSET_NAMES = [
    "ProcessSecurityAuditorAVPro.exe",
    "ProcessSecurityAuditor.exe",
]

@dataclass
class UpdateResult:
    update_available: bool
    current_version: str
    latest_version: str
    asset_name: Optional[str]
    download_url: Optional[str]
    release_url: Optional[str]
    message: str

def project_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))

def read_local_version() -> str:
    version_path = os.path.join(project_root(), "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def normalize_version(version: str) -> tuple:
    """
    Converts 'v0.3.0', '0.3.0', '0.3.0-beta' into comparable integer tuple.
    Non-numeric suffixes are ignored for simple desktop release checks.
    """
    if not version:
        return (0, 0, 0)
    clean = version.strip().lower()
    if clean.startswith("v"):
        clean = clean[1:]
    clean = re.sub(r"[^0-9.].*$", "", clean)
    parts = []
    for part in clean.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def fetch_latest_release(repo: str = GITHUB_REPO) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ProcessSecurityAuditorAVPro-Updater",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def pick_release_asset(release: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    assets = release.get("assets", []) or []

    # Prefer known executable names first.
    for wanted in PREFERRED_ASSET_NAMES:
        for asset in assets:
            if asset.get("name") == wanted:
                return asset.get("name"), asset.get("browser_download_url")

    # Fallback: any .exe asset.
    for asset in assets:
        name = asset.get("name", "")
        if name.lower().endswith(".exe"):
            return name, asset.get("browser_download_url")

    return None, None

def check_for_update(repo: str = GITHUB_REPO) -> UpdateResult:
    current = read_local_version()

    try:
        release = fetch_latest_release(repo)
    except urllib.error.HTTPError as e:
        return UpdateResult(False, current, current, None, None, None, f"GitHub API error: HTTP {e.code}")
    except Exception as e:
        return UpdateResult(False, current, current, None, None, None, f"Could not check updates: {e}")

    latest_tag = release.get("tag_name", "0.0.0")
    asset_name, download_url = pick_release_asset(release)
    release_url = release.get("html_url")

    if not asset_name or not download_url:
        return UpdateResult(False, current, latest_tag, None, None, release_url, "Release found, but no .exe asset was attached.")

    update_available = normalize_version(latest_tag) > normalize_version(current)
    if update_available:
        msg = f"Update available: {latest_tag} ({asset_name})"
    else:
        msg = f"Up to date. Current: {current}, latest: {latest_tag}"

    return UpdateResult(update_available, current, latest_tag, asset_name, download_url, release_url, msg)

def download_update(download_url: str, destination_folder: Optional[str] = None) -> str:
    if destination_folder is None:
        destination_folder = os.path.join(project_root(), "updates")
    os.makedirs(destination_folder, exist_ok=True)

    filename = os.path.basename(download_url.split("?")[0]) or "ProcessSecurityAuditorAVPro.exe"
    destination = os.path.join(destination_folder, filename)

    req = urllib.request.Request(download_url, headers={"User-Agent": "ProcessSecurityAuditorAVPro-Updater"})
    with urllib.request.urlopen(req, timeout=60) as response, open(destination, "wb") as out:
        out.write(response.read())

    return destination

if __name__ == "__main__":
    result = check_for_update()
    print(json.dumps(result.__dict__, indent=2))
