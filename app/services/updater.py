import os, sys, tempfile, requests, subprocess
from packaging.version import Version
from app.core.config import APP_VERSION, GITHUB_OWNER, GITHUB_REPO, GITHUB_ASSET_NAME

def check_latest():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    r = requests.get(url, timeout=15, headers={"Accept":"application/vnd.github+json"})
    r.raise_for_status()
    data = r.json()
    tag = data.get("tag_name","").lstrip("v")
    asset = None
    for a in data.get("assets", []):
        if a.get("name") == GITHUB_ASSET_NAME:
            asset = a.get("browser_download_url")
            break
    return {"latest": tag, "current": APP_VERSION, "download_url": asset, "release_url": data.get("html_url"), "body": data.get("body","")}

def update_available(info):
    try:
        return Version(info["latest"]) > Version(APP_VERSION)
    except Exception:
        return False

def download_update(download_url, progress=None):
    local = os.path.join(tempfile.gettempdir(), GITHUB_ASSET_NAME)
    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(local, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*256):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if progress and total:
                        progress(done, total)
    return local

def launch_downloaded_update(path):
    # Safer MVP: download and open installer/new exe; user chooses replacement.
    subprocess.Popen([path], shell=False)
