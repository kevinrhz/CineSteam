import logging
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

import csv, sys, os, ast
from dateutil.parser import parse
from tqdm import tqdm
from core.db import SessionLocal
from core.models import (
    Game, Movie, Genre,
    Developer, Publisher, Platform,
    Director, Actor
)

csv.field_size_limit(sys.maxsize)
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
BATCH_SIZE = 500     # commit every N rows

# Tags that are NOT real content genres
BANNED_GENRES = {
    "tutorial","software training","web publishing","game development",
    "early access","free to play","multiplayer","massively multiplayer",
    "online co-op","cross-platform multiplayer","episodic","tv-style",
    "nudity","sexual content","gore","video production",
    "utilities","photo editing","audio production","accounting"
}

# ---------- helpers ----------------------------------------------------------
def load_csv(name):
    path = os.path.join(DATA_DIR, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def get_or_create(session, model, **kw):
    obj = session.query(model).filter_by(**kw).first()
    if not obj:
        obj = model(**kw)
        session.add(obj)
    return obj

def canon(name: str) -> str:
    """Title-case / strip for canonical Genre names."""
    return " ".join(w.capitalize() for w in name.strip().split())

def extract_year(s: str) -> int:
    try:
        return parse(s).year
    except Exception:
        return 0
# -----------------------------------------------------------------------------


def load_games(session):
    print("📥 Loading Steam games…")
    rows, n = load_csv("steam_games.csv"), 0

    for row in tqdm(rows, desc="Games", leave=True):
        try:
            game = get_or_create(
                session, Game,
                name=row["name"],
                release_year=extract_year(row.get("release_date",""))
            )

            # ------- genres -------
            try:
                raw_genres = ast.literal_eval(row.get("genres","[]"))
            except Exception:
                raw_genres = []
            for g in raw_genres:
                g_norm = g.strip().lower()
                if not g_norm or g_norm in BANNED_GENRES:
                    continue
                genre = get_or_create(session, Genre, name=canon(g_norm))
                if genre not in game.genres:
                    game.genres.append(genre)

            # developers
            for dn in row.get("developers","").split(","):
                d = dn.strip()
                if d:
                    dev = get_or_create(session, Developer, name=d)
                    if dev not in game.developers:
                        game.developers.append(dev)

            # publishers
            for pn in row.get("publishers","").split(","):
                p = pn.strip()
                if p:
                    pub = get_or_create(session, Publisher, name=p)
                    if pub not in game.publishers:
                        game.publishers.append(pub)

            # platforms
            try:
                plats = ast.literal_eval(row.get("platforms","[]"))
            except Exception:
                plats = []
            for pl in plats:
                pl_norm = pl.strip().lower()
                if pl_norm:
                    plat = get_or_create(session, Platform, name=pl_norm)
                    if plat not in game.platforms:
                        game.platforms.append(plat)

            n += 1
            if n % BATCH_SIZE == 0:
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"❌ Error loading game {row.get('name')}: {e}")

    session.commit()
    print("✅ Steam games loaded.\n")


def load_movies(session):
    print("📥 Loading IMDb movies…")
    rows, n = load_csv("imdb_top_1000.csv"), 0

    for row in tqdm(rows, desc="Movies", leave=True):
        try:
            movie = get_or_create(
                session, Movie,
                title=row["Series_Title"],
                release_year=int(row.get("Released_Year") or 0)
            )

            # ------- genres -------
            for g in row.get("Genre","").split(","):
                g_norm = g.strip().lower()
                if not g_norm or g_norm in BANNED_GENRES:
                    continue
                genre = get_or_create(session, Genre, name=canon(g_norm))
                if genre not in movie.genres:
                    movie.genres.append(genre)

            # directors
            for dn in row.get("Director","").split(","):
                d = dn.strip()
                if d:
                    director = get_or_create(session, Director, name=d)
                    if director not in movie.directors:
                        movie.directors.append(director)

            # actors
            for key in ("Star1","Star2","Star3","Star4"):
                actor_name = row.get(key,"").strip()
                if actor_name:
                    actor = get_or_create(session, Actor, name=actor_name)
                    if actor not in movie.actors:
                        movie.actors.append(actor)

            n += 1
            if n % BATCH_SIZE == 0:
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"❌ Error loading movie {row.get('Series_Title')}: {e}")

    session.commit()
    print("✅ IMDb movies loaded.\n")


# -----------------------------------------------------------------------------


def main():
    session = SessionLocal()
    try:
        load_games(session)
        load_movies(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
