"""
Resume-able Steam description fetcher.

• Single-threaded ≈0.63 req/s (190 calls/5 min) to avoid 429/403.
• Exponential backoff on network errors; 5 min window sleep on 429.
• Never deletes your CSV; merges new descriptions in place.
• Overwrites steam_descriptions.csv when done.
"""

import csv, os, sys, time, signal, requests
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# ── CONFIG ────────────────────────────────────────────────────────────────
WINDOW_HITS    = 190               # max calls per 5 min
WINDOW_SEC     = 300               # window length (sec)
PAUSE_PER_CALL = WINDOW_SEC / WINDOW_HITS  # ≈1.5789 s
MAX_RETRIES    = 5
TIMEOUT_SEC    = 10
SRC_CSV        = Path("data/steam_games.csv")
DST_CSV        = Path("data/steam_descriptions.csv")
ENDPOINT       = "https://store.steampowered.com/api/appdetails"
# ─────────────────────────────────────────────────────────────────────────

# bump CSV field-size limit
max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int //= 10

load_dotenv()  # optional: you can store STEAM_API_KEY here
API_KEY = os.getenv("STEAM_API_KEY", "").strip()

session = requests.Session()
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

def fetch_description(appid: str) -> str:
    """Fetch one app's description or ''."""
    params = {
        "appids": appid,
        "cc": "us",
        "l": "en",
        "filters": "short_description,about_the_game",
    }
    if API_KEY:
        params["key"] = API_KEY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(ENDPOINT, params=params, timeout=TIMEOUT_SEC)
            if r.status_code == 429:
                # rate window hit
                time.sleep(WINDOW_SEC)
                continue
            r.raise_for_status()
            info = r.json().get(appid, {})
            if info.get("success"):
                d = info["data"]
                return (d.get("short_description") or
                        d.get("about_the_game") or ""
                       ).replace("\n", " ").strip()
            return ""
        except Exception:
            if attempt == MAX_RETRIES:
                return ""
            time.sleep(2 ** attempt)
    return ""

def main():
    # load existing descriptions
    existing = {}
    if DST_CSV.exists():
        with DST_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if row and row[0].isdigit():
                    existing[row[0]] = row[1]

    # load all IDs
    with SRC_CSV.open(newline="", encoding="utf-8") as fh:
        all_ids = [r["steam_appid"] for r in csv.DictReader(fh)]

    # identify which need fetching
    to_fetch = [aid for aid in all_ids if existing.get(aid, "").strip() == ""]

    if not to_fetch:
        print("✓ All descriptions already populated.")
    else:
        est_h = len(to_fetch) * PAUSE_PER_CALL / 3600
        print(f"Fetching {len(to_fetch):,} descriptions (~{est_h:.1f} h)")

        hits, window_start = 0, time.time()

        for aid in tqdm(to_fetch, desc="Scraping"):
            # enforce 5-min window
            if hits >= WINDOW_HITS:
                elapsed = time.time() - window_start
                if elapsed < WINDOW_SEC:
                    time.sleep(WINDOW_SEC - elapsed)
                window_start, hits = time.time(), 0

            desc = fetch_description(aid)
            existing[aid] = desc
            hits += 1
            time.sleep(PAUSE_PER_CALL)

    # write out merged CSV
    with DST_CSV.open("w", newline="", encoding="utf-8") as fo:
        writer = csv.writer(fo)
        writer.writerow(["steam_appid", "description"])
        for aid in all_ids:
            writer.writerow([aid, existing.get(aid, "")])

    print(f"✅ steam_descriptions.csv updated with {len(all_ids)} entries.")

if __name__ == "__main__":
    main()
