import json
import os
import heapq
import numpy as np
from core.db import SessionLocal
from core.models import Recommendation
from tqdm import tqdm

# paths & parameters
VEC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "genre_vectors.json")
TOP_K = 10
BATCH_SIZE = 500

def main():
    # 1) load precomputed vectors
    data = json.load(open(VEC_PATH))
    gv = {int(k): np.array(v, dtype=float) for k, v in data["game_vectors"].items()}
    mv = {int(k): np.array(v, dtype=float) for k, v in data["movie_vectors"].items()}

    session = SessionLocal()
    try:
        # clear old
        session.query(Recommendation).delete()
        session.commit()

        buffer = []
        # 2) for each game, score every movie
        for game_id, gvec in tqdm(gv.items(), desc="Scoring games"):
            sum_g = gvec.sum()
            if sum_g == 0:
                continue

            heap = []
            for movie_id, mvec in mv.items():
                sum_m = mvec.sum()
                if sum_m == 0:
                    continue

                inter = np.minimum(gvec, mvec).sum()
                score = inter / min(sum_g, sum_m)
                if score > 0:
                    heapq.heappush(heap, (score, movie_id))
                    if len(heap) > TOP_K:
                        heapq.heappop(heap)

            # collect top K
            for score, mid in sorted(heap, reverse=True):
                buffer.append(Recommendation(game_id=game_id, movie_id=mid, score=float(score)))

            # batch insert
            if len(buffer) >= BATCH_SIZE:
                session.bulk_save_objects(buffer)
                session.commit()
                buffer.clear()

        # final flush
        if buffer:
            session.bulk_save_objects(buffer)
            session.commit()

        print("✅ Saved all recommendations.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error during scoring: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
