import json, os
from scipy.spatial.distance import cosine
from core.db import SessionLocal
from core.models import Recommendation
from tqdm import tqdm

VEC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "genre_vectors.json")

def main():
    data = json.load(open(VEC_PATH))
    games = data["game_vectors"]
    movies= data["movie_vectors"]

    session = SessionLocal()
    try:
        session.query(Recommendation).delete()
        session.commit()

        batch = []
        for gid, gvec in tqdm(games.items(), desc="Scoring games"):
            for mid, mvec in movies.items():
                if not any(gvec) or not any(mvec):
                    continue
                score = 1 - cosine(gvec, mvec)
                if score>0:
                    batch.append(Recommendation(
                        game_id=int(gid),
                        movie_id=int(mid),
                        score=float(score)
                    ))
            if len(batch)>10000:
                session.bulk_save_objects(batch)
                session.commit()
                batch.clear()

        if batch:
            session.bulk_save_objects(batch)
            session.commit()

        print("✅ Saved recommendations.")
    except Exception as e:
        session.rollback()
        print(f"❌ scoring error: {e}")
    finally:
        session.close()

if __name__=="__main__":
    main()
