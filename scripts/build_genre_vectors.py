import json, os
from collections import defaultdict
from core.db import SessionLocal
from core.models import Game, Movie, Genre
from sqlalchemy.orm import joinedload

VEC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "genre_vectors.json")

def build_vectors():
    session = SessionLocal()
    genre_index, genre_counts = {}, defaultdict(int)

    try:
        # 1 — canonical genre index
        for i, g in enumerate(session.query(Genre).all()):
            genre_index[g.name.lower()] = i

        # 2 — eager-load genres
        games  = session.query(Game ).options(joinedload(Game .genres)).all()
        movies = session.query(Movie).options(joinedload(Movie.genres)).all()

        def encode(obj):
            vec = [0]*len(genre_index)
            for g in obj.genres:
                k = g.name.lower()
                genre_counts[k] += 1
                vec[genre_index[k]] = 1
            return vec

        game_vectors  = {}
        movie_vectors = {}

        skipped_games = skipped_movies = 0

        for g in games:
            v = encode(g)
            if any(v):
                game_vectors[g.id] = v
            else:
                skipped_games += 1

        for m in movies:
            v = encode(m)
            if any(v):
                movie_vectors[m.id] = v
            else:
                skipped_movies += 1

        with open(VEC_PATH, "w") as f:
            json.dump({
                "genre_index"  : genre_index,
                "game_vectors" : game_vectors,
                "movie_vectors": movie_vectors,
                "genre_counts" : genre_counts
            }, f)

        print(f"✅ Genre vectors saved → {VEC_PATH}")
        if skipped_games or skipped_movies:
            print(f"ℹ️  Skipped {skipped_games} games and {skipped_movies} movies with no genres.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    build_vectors()
