import os
import json
import argparse
import numpy as np
from scipy import sparse
from tqdm import tqdm
from core.db import SessionLocal
from core.models import Recommendation

def normalize_rows(X):
    # L2 normalize each row of a CSR matrix
    norms = np.sqrt(X.multiply(X).sum(axis=1)).A1
    norms[norms == 0] = 1.0
    inv = sparse.diags(1.0 / norms)
    return inv.dot(X)

def main(alpha: float, top_k: int = 10):
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

    # — load genre vectors
    with open(os.path.join(DATA_DIR, "genre_vectors.json")) as f:
        gv = json.load(f)
    genre_game_ids  = list(map(int, gv["game_vectors"].keys()))
    genre_movie_ids = list(map(int, gv["movie_vectors"].keys()))
    G_genre = sparse.csr_matrix(list(gv["game_vectors"].values()))
    M_genre = sparse.csr_matrix(list(gv["movie_vectors"].values()))

    # — load text vectors & metadata
    G_text = sparse.load_npz(os.path.join(DATA_DIR, "game_text.npz"))
    M_text = sparse.load_npz(os.path.join(DATA_DIR, "movie_text.npz"))
    with open(os.path.join(DATA_DIR, "text_meta.json")) as f:
        tm = json.load(f)
    text_game_ids  = tm["game_ids"]
    text_movie_ids = tm["movie_ids"]

    # Normalize for cosine similarity
    G_genre = normalize_rows(G_genre)
    M_genre = normalize_rows(M_genre)
    G_text  = normalize_rows(G_text)
    M_text  = normalize_rows(M_text)

    # We'll assume the same ordering for genre & text IDs:
    game_ids  = genre_game_ids
    movie_ids = genre_movie_ids

    session = SessionLocal()
    session.query(Recommendation).delete()
    session.commit()

    total = 0
    print(f"🔧 Scoring recommendations with alpha={alpha:.2f} (genre×{alpha:.2f} + text×{1-alpha:.2f})")
    for i, g_id in enumerate(tqdm(game_ids, desc="Games")):
        vg = G_genre[i].toarray().ravel()
        vt = G_text[i].toarray().ravel()

        # Cosine scores
        mg = M_genre.dot(vg)           # genre cosine
        mt = M_text.dot(vt)            # text cosine

        scores = alpha * mg + (1 - alpha) * mt
        top_idx = np.argsort(-scores)[:top_k]

        recs = []
        for j in top_idx:
            score = float(scores[j])
            if score > 0.0:
                recs.append(
                    Recommendation(
                        game_id=g_id,
                        movie_id=movie_ids[j],
                        score=score
                    )
                )
        session.bulk_save_objects(recs)
        total += len(recs)
        if i and i % 500 == 0:
            session.commit()

    session.commit()
    session.close()
    print(f"✅ Done. {total} recommendations stored (top {top_k} per game).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score game→movie recommendations by hybrid genre/text cosine similarity"
    )
    parser.add_argument(
        "--alpha", type=float, default=0.5,
        help="weight for genre vs text (0.0=text-only, 1.0=genre-only)"
    )
    parser.add_argument(
        "--top_k", type=int, default=10,
        help="number of top matches to save per game"
    )
    args = parser.parse_args()
    main(alpha=args.alpha, top_k=args.top_k)
