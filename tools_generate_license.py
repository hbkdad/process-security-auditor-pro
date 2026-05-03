import argparse, time
from app.services.license_manager import generate_license

p = argparse.ArgumentParser()
p.add_argument("--name", required=True)
p.add_argument("--tier", default="pro", choices=["lite","pro","business"])
p.add_argument("--days", type=int, default=365)
args = p.parse_args()

expires = int(time.time()) + args.days * 86400
print(generate_license(args.name, args.tier, expires))
