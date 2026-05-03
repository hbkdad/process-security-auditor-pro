import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.services.updater import check_for_update, download_update

def main():
    result = check_for_update()
    print(json.dumps(result.__dict__, indent=2))

    if result.update_available:
        print("\nUpdate detection OK.")
        print(f"Latest: {result.latest_version}")
        print(f"Asset: {result.asset_name}")
        print(f"Download URL: {result.download_url}")
    else:
        print("\nNo update detected or update check failed.")
        print(result.message)

if __name__ == "__main__":
    main()
