import json, os
from collections import defaultdict
from core.db import SessionLocal
from core.models import GenreAlias, Game, Movie
from sqlalchemy.orm import joinedload

VEC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "genre_vectors.json")

def build_vectors():
    session = SessionLocal()
    try:
        # load alias→canon
        aliases = session.query(GenreAlias).options(joinedload(GenreAlias.genres)).all()
        alias_map = {
            a.alias: [g.name for g in a.genres if not g.name.startswith("_FLAG_")]
            for a in aliases
        }
        # dims = sorted canon
        dims = sorted({c for lst in alias_map.values() for c in lst})
        idx  = {c:i for i,c in enumerate(dims)}
        counts = defaultdict(int)

        def encode(obj):
            v = [0]*len(dims)
            raws = [g.name.lower() for g in obj.genres]
            for raw in raws:
                for canon in alias_map.get(raw, []):
                    v[idx[canon]] = 1
                    counts[canon] += 1
            return v

        games  = session.query(Game).options(joinedload(Game.genres)).all()
        movies = session.query(Movie).options(joinedload(Movie.genres)).all()

        gv = {g.id: encode(g) for g in games}
        mv = {m.id: encode(m) for m in movies}

        with open(VEC_PATH,"w") as f:
            json.dump({
                "genre_index": idx,
                "game_vectors": gv,
                "movie_vectors": mv,
                "genre_counts": counts
            }, f)

        print(f"✅ Genre vectors saved → {VEC_PATH}")
    except Exception as e:
        session.rollback()
        print(f"❌ build_genre_vectors error: {e}")
    finally:
        session.close()

if __name__=="__main__":
    build_vectors()
