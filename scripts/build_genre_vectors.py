import json
import os
import math
from collections import defaultdict
from core.db import SessionLocal
from core.models import Game, Movie, Genre
from sqlalchemy.orm import joinedload

# where to dump vectors
VEC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "genre_vectors.json")

def build_vectors():
    session = SessionLocal()
    try:
        # 1) Load all canonical genres
        genres = session.query(Genre).all()
        # build a 0-based index only over unique lower-cased names
        genre_index = {}
        for g in genres:
            key = g.name.strip().lower()
            if key not in genre_index:
                genre_index[key] = len(genre_index)

        # 2) Eager-load every game's & movie's genres
        games = session.query(Game).options(joinedload(Game.genres)).all()
        movies = session.query(Movie).options(joinedload(Movie.genres)).all()

        # 3) Document frequency for each genre
        df = defaultdict(int)
        for obj in games + movies:
            seen = set()
            for g in obj.genres:
                name = g.name.strip().lower()
                if name in genre_index and name not in seen:
                    df[name] += 1
                    seen.add(name)

        # 4) Compute IDF weights
        idf = {name: 1.0 / math.log(1 + count) for name, count in df.items()}

        # helper: build TF-IDF vector
        def encode(obj):
            vec = [0.0] * len(genre_index)
            for g in obj.genres:
                name = g.name.strip().lower()
                idx = genre_index.get(name)
                if idx is not None:
                    vec[idx] = idf.get(name, 0.0)
            if all(v == 0.0 for v in vec):
                # skip if truly genreless
                return None
            return vec

        # 5) Build and filter out None
        game_vectors = {g.id: encode(g) for g in games}
        game_vectors = {gid: vec for gid, vec in game_vectors.items() if vec is not None}

        movie_vectors = {m.id: encode(m) for m in movies}
        movie_vectors = {mid: vec for mid, vec in movie_vectors.items() if vec is not None}

        # 6) Write out
        with open(VEC_PATH, "w") as f:
            json.dump({
                "genre_index": genre_index,
                "game_vectors": game_vectors,
                "movie_vectors": movie_vectors,
                "idf": idf
            }, f)

        print(f"✅ Genre vectors saved to {VEC_PATH}")
    except Exception as e:
        session.rollback()
        print(f"❌ Error building genre vectors: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    build_vectors()
