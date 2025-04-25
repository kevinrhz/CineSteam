import os
import csv
import time
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from core.db import SessionLocal
from core.models import Game

DATA_DIR      = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_CSV       = os.path.join(DATA_DIR, "steam_descriptions.csv")
MAX_WORKERS   = 32
RATE_LIMIT_SEC= 0.1  # 10 req/sec per thread

def fetch_description(args):
    """Fetch + return (appid, description). Sleeps to rate-limit."""
    appid, key, session = args
    time.sleep(RATE_LIMIT_SEC)
    try:
        r = session.get(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": appid, "cc":"us","l":"en","key":key},
            timeout=5
        ).json()[str(appid)]
        if r.get("success"):
            data = r["data"]
            return appid, data.get("short_description") or data.get("about_the_game","")
    except:
        pass
    return appid, ""

def main():
    load_dotenv()
    key = os.getenv("STEAM_API_KEY")
    if not key:
        raise RuntimeError("STEAM_API_KEY missing in .env")

    # pull all Steam appids out of your DB
    session_db = SessionLocal()
    apps = [g.steam_appid for g in session_db.query(Game)
                              .filter(Game.steam_appid.isnot(None))]
    session_db.close()

    # one HTTP session for all workers
    http = requests.Session()

    with ThreadPoolExecutor(MAX_WORKERS) as exe, \
         open(OUT_CSV, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)
        writer.writerow(["steam_appid","description"])

        # prepare the work items
        work = ((appid, key, http) for appid in apps)
        futures = {exe.submit(fetch_description, w): w[0] for w in work}

        # as they finish, write immediately—no global sleep here
        for fut in tqdm(as_completed(futures),
                        total=len(futures),
                        desc="Fetching descriptions",
                        unit="app"):
            appid = futures[fut]
            _, desc = fut.result()
            writer.writerow([appid, desc])

    print(f"✅ Wrote {OUT_CSV}")

if __name__ == "__main__":
    main()
