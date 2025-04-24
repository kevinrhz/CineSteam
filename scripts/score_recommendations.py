#!/usr/bin/env python
import os
import json
from tqdm import tqdm
import numpy as np

from sqlalchemy import insert
from sqlalchemy.orm import Session
from core.db import engine
from core.models import Recommendation

VEC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "genre_vectors.json")
TOP_K = 10  # number of recommendations per game

def score_recommendations():
    # 1) Load precomputed genre vectors
    with open(VEC_PATH, "r") as f:
        data = json.load(f)
    game_vectors = {int(k): np.array(v) for k, v in data["game_vectors"].items()}
    movie_vectors = {int(k): np.array(v) for k, v in data["movie_vectors"].items()}

    # 2) For each game, compute cosine similarity against all movies
    recs = []
    for game_id, gvec in tqdm(game_vectors.items(), desc="Scoring games"):
        # pre-normalize
        gn = np.linalg.norm(gvec)
        if gn == 0:
            continue
        g_unit = gvec / gn

        # compute dot with each movie
        sims = []
        for movie_id, mvec in movie_vectors.items():
            mn = np.linalg.norm(mvec)
            if mn == 0:
                continue
            score = float(np.dot(g_unit, mvec / mn))  # ensure Python float
            if score > 0:
                sims.append((movie_id, score))

        # take top K
        top = sorted(sims, key=lambda x: x[1], reverse=True)[:TOP_K]
        for movie_id, score in top:
            recs.append({"game_id": game_id, "movie_id": movie_id, "score": score})

    # 3) Bulk-insert into recommendations table
    with Session(engine) as session:
        # wipe old
        session.execute(Recommendation.__table__.delete())
        session.commit()

        # batch insert
        for i in range(0, len(recs), 1000):
            batch = recs[i : i + 1000]
            session.bulk_insert_mappings(Recommendation, batch)
            session.commit()

    print(f"✅ Saved {len(recs)} recommendations.")

if __name__ == "__main__":
    score_recommendations()
