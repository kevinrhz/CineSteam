import csv
import sys
import os
import ast
from dateutil.parser import parse
from sqlalchemy.exc import IntegrityError
from core.db import SessionLocal
from core.models import Game, Movie, Genre, Developer, Publisher, Platform, Director, Actor

csv.field_size_limit(sys.maxsize)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    instance = model(**kwargs)
    session.add(instance)
    return instance

def extract_year(date_str):
    try:
        return parse(date_str).year
    except Exception:
        return 0

def load_games(session):
    print("📥 Loading Steam games...")
    games = load_csv("steam_games.csv")

    for row in games:
        try:
            year = extract_year(row.get("release_date", ""))
            game = get_or_create(session, Game, name=row["name"], release_year=year)

            # genres
            genres_raw = row.get("genres", "")
            try:
                genre_list = ast.literal_eval(genres_raw)
            except:
                genre_list = []
            for genre_name in genre_list:
                genre_name = genre_name.strip()
                if genre_name:
                    genre = get_or_create(session, Genre, name=genre_name)
                    if genre not in game.genres:
                        game.genres.append(genre)

            # developers
            for dev_name in row.get("developers", "").split(","):
                dev_name = dev_name.strip()
                if dev_name:
                    dev = get_or_create(session, Developer, name=dev_name)
                    if dev not in game.developers:
                        game.developers.append(dev)

            # publishers
            for pub_name in row.get("publishers", "").split(","):
                pub_name = pub_name.strip()
                if pub_name:
                    pub = get_or_create(session, Publisher, name=pub_name)
                    if pub not in game.publishers:
                        game.publishers.append(pub)

            # platforms
            platforms_raw = row.get("platforms", "")
            try:
                platform_list = ast.literal_eval(platforms_raw)
            except:
                platform_list = []
            for plat_name in platform_list:
                plat_name = plat_name.strip().lower()
                if plat_name:
                    plat = get_or_create(session, Platform, name=plat_name)
                    if plat not in game.platforms:
                        game.platforms.append(plat)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"❌ Error loading game {row.get('name')}: {e}")

    print("✅ Steam games loaded.\n")

def load_movies(session):
    print("📥 Loading IMDb movies...")
    movies = load_csv("imdb_top_1000.csv")

    for row in movies:
        try:
            year = int(row.get("Released_Year", 0)) if row.get("Released_Year") else 0
            movie = get_or_create(session, Movie, title=row["Series_Title"], release_year=year)

            for genre_name in row.get("Genre", "").split(","):
                genre_name = genre_name.strip()
                if genre_name:
                    genre = get_or_create(session, Genre, name=genre_name)
                    if genre not in movie.genres:
                        movie.genres.append(genre)

            for director_name in row.get("Director", "").split(","):
                director_name = director_name.strip()
                if director_name:
                    director = get_or_create(session, Director, name=director_name)
                    if director not in movie.directors:
                        movie.directors.append(director)

            for key in ["Star1", "Star2", "Star3", "Star4"]:
                actor_name = row.get(key, "").strip()
                if actor_name:
                    actor = get_or_create(session, Actor, name=actor_name)
                    if actor not in movie.actors:
                        movie.actors.append(actor)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"❌ Error loading movie {row.get('Series_Title')}: {e}")

    print("✅ IMDb movies loaded.\n")

def main():
    session = SessionLocal()

    try:
        load_games(session)
        load_movies(session)
    finally:
        session.close()

if __name__ == "__main__":
    main()