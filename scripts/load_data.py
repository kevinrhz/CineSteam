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
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BATCH_SIZE = 500

BANNED_GENRES = {
    "tutorial","software training","web publishing","game development",
    "early access","free to play","multiplayer","massively multiplayer",
    "online co-op","cross-platform multiplayer","episodic","tv-style",
    "nudity","sexual content","gore","video production",
    "utilities","photo editing","audio production","accounting"
}

def load_csv(fn):
    path = os.path.join(DATA_DIR, fn)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def extract_year(s):
    try: return parse(s).year
    except: return 0

def get_or_create(s, model, **kw):
    inst = s.query(model).filter_by(**kw).first()
    if inst: return inst
    inst = model(**kw)
    s.add(inst)
    return inst

def load_raw_genres(session):
    raw_set = set()
    # Steam
    for r in load_csv("steam_games.csv"):
        try: gl = ast.literal_eval(r.get("genres","[]"))
        except: continue
        for raw in gl:
            n = str(raw).strip().lower()
            if n and n not in BANNED_GENRES:
                raw_set.add(n)
    # IMDb
    for r in load_csv("imdb_top_1000.csv"):
        for raw in r.get("Genre","").split(","):
            n = raw.strip().lower()
            if n and n not in BANNED_GENRES:
                raw_set.add(n)
    for name in raw_set:
        get_or_create(session, Genre, name=name)
    session.commit()

def load_games(session):
    print("📥 Loading Steam games…")
    rows, cnt = load_csv("steam_games.csv"), 0
    for row in tqdm(rows, desc="Games", leave=True):
        try:
            year = extract_year(row.get("release_date",""))
            game = get_or_create(session, Game, name=row["name"], release_year=year)
            # genres
            try: gl = ast.literal_eval(row.get("genres","[]"))
            except: gl = []
            for raw in gl:
                n = str(raw).strip().lower()
                if not n or n in BANNED_GENRES: continue
                g = session.query(Genre).filter(Genre.name.ilike(n)).first()
                if g and g not in game.genres:
                    game.genres.append(g)
            # devs
            for dn in row.get("developers","").split(","):
                dn = dn.strip()
                if dn:
                    d = get_or_create(session, Developer, name=dn)
                    if d not in game.developers:
                        game.developers.append(d)
            # pubs
            for pn in row.get("publishers","").split(","):
                pn = pn.strip()
                if pn:
                    p = get_or_create(session, Publisher, name=pn)
                    if p not in game.publishers:
                        game.publishers.append(p)
            # plats
            try: pl = ast.literal_eval(row.get("platforms","[]"))
            except: pl = []
            for raw in pl:
                n = str(raw).strip().lower()
                if n:
                    p = get_or_create(session, Platform, name=n)
                    if p not in game.platforms:
                        game.platforms.append(p)

            cnt += 1
            if cnt % BATCH_SIZE == 0:
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"❌ Error loading game {row.get('name')}: {e}")
    session.commit()
    print("✅ Steam games loaded.\n")

def load_movies(session):
    print("📥 Loading IMDb movies…")
    rows, cnt = load_csv("imdb_top_1000.csv"), 0
    for row in tqdm(rows, desc="Movies", leave=True):
        try:
            year = int(row.get("Released_Year") or 0)
            movie = get_or_create(session, Movie, title=row["Series_Title"], release_year=year)
            # genres
            for raw in row.get("Genre","").split(","):
                n = raw.strip().lower()
                if not n or n in BANNED_GENRES: continue
                g = session.query(Genre).filter(Genre.name.ilike(n)).first()
                if g and g not in movie.genres:
                    movie.genres.append(g)
            # directors
            for dn in row.get("Director","").split(","):
                dn = dn.strip()
                if dn:
                    d = get_or_create(session, Director, name=dn)
                    if d not in movie.directors:
                        movie.directors.append(d)
            # actors
            for key in ["Star1","Star2","Star3","Star4"]:
                star = row.get(key,"").strip()
                if star:
                    a = get_or_create(session, Actor, name=star)
                    if a not in movie.actors:
                        movie.actors.append(a)

            cnt += 1
            if cnt % BATCH_SIZE == 0:
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"❌ Error loading movie {row.get('Series_Title')}: {e}")
    session.commit()
    print("✅ IMDb movies loaded.\n")

def main():
    session = SessionLocal()
    try:
        load_raw_genres(session)
        load_games(session)
        load_movies(session)
    finally:
        session.close()

if __name__=="__main__":
    main()
