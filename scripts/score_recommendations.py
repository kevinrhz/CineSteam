import os
import json
import argparse
import numpy as np
from tqdm import tqdm
from scipy import sparse
from core.db import SessionLocal
from core.models import Recommendation


def normalize_rows(X):
    norms = np.sqrt(X.multiply(X).sum(axis=1)).A1
    norms[norms == 0] = 1.0
    inv = sparse.diags(1.0 / norms)
    return inv.dot(X)


def main(alpha: float, beta: float, top_k: int = 10):
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

    # load genre vectors
    with open(os.path.join(data_dir, 'genre_vectors.json')) as f:
        gv = json.load(f)
    genre_game_ids  = list(map(int, gv['game_vectors'].keys()))
    genre_movie_ids = list(map(int, gv['movie_vectors'].keys()))
    G_genre = sparse.csr_matrix(list(gv['game_vectors'].values()))
    M_genre = sparse.csr_matrix(list(gv['movie_vectors'].values()))

    # load text vectors & meta
    G_text = sparse.load_npz(os.path.join(data_dir, 'game_text.npz'))
    M_text = sparse.load_npz(os.path.join(data_dir, 'movie_text.npz'))
    with open(os.path.join(data_dir, 'text_meta.json')) as f:
        tm = json.load(f)
    text_game_ids  = tm['game_ids']
    text_movie_ids = tm['movie_ids']

    # load alias map
    with open(os.path.join(data_dir, 'alias_map.json')) as f:
        amap = json.load(f)
    game_alias_map  = {int(k): set(v) for k, v in amap['game_aliases'].items()}
    movie_alias_map = {int(k): set(v) for k, v in amap['movie_aliases'].items()}

    # normalize
    G_genre = normalize_rows(G_genre)
    M_genre = normalize_rows(M_genre)
    G_text  = normalize_rows(G_text)
    M_text  = normalize_rows(M_text)

    # assume consistent ordering
    game_ids  = genre_game_ids
    movie_ids = genre_movie_ids

    session = SessionLocal()
    session.query(Recommendation).delete()
    session.commit()

    total = 0
    print(f"🔧 Scoring with alpha={alpha:.2f}, beta={beta:.2f}, top_k={top_k}")
    for i, g_id in enumerate(tqdm(game_ids, desc="Games")):
        vg = G_genre[i].toarray().ravel()
        vt = G_text[i].toarray().ravel()
        mg = M_genre.dot(vg)           # genre score
        mt = M_text.dot(vt)            # text score

        recs = []
        # compute combined scores for all movies
        for j, m_id in enumerate(movie_ids):
            alias_bonus = 1.0 if (game_alias_map.get(g_id, set()) & movie_alias_map.get(m_id, set())) else 0.0
            score = alpha * mg[j] + (1-alpha) * mt[j] + beta * alias_bonus
            recs.append((j, score))
        # pick top_k
        top = sorted(recs, key=lambda x: -x[1])[:top_k]
        objs = [Recommendation(game_id=g_id, movie_id=movie_ids[j], score=float(s))
                for j, s in top if s > 0]

        session.bulk_save_objects(objs)
        total += len(objs)
        if i and i % 500 == 0:
            session.commit()

    session.commit()
    session.close()
    print(f"✅ Stored {total} recommendations.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--alpha', type=float, default=0.5,
                        help='genre weight (0=text-only, 1=genre-only)')
    parser.add_argument('--beta',  type=float, default=0.1,
                        help='alias boost weight')
    parser.add_argument('--top_k',type=int,   default=10,
                        help='number of recs per game')
    args = parser.parse_args()
    main(args.alpha, args.beta, args.top_k)
