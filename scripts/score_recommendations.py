import os, json, numpy as np
from tqdm import tqdm
from scipy import sparse
from core.db import SessionLocal
from core.models import Recommendation
from sqlalchemy.orm import Session

# weight between genres and text [0.0 → text-only, 1.0 → genre-only]
ALPHA = 0.5

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# load genre vectors
with open(os.path.join(DATA_DIR, "genre_vectors.json")) as f:
    gv = json.load(f)
genre_game_ids  = list(map(int, gv["game_vectors"].keys()))
genre_movie_ids = list(map(int, gv["movie_vectors"].keys()))
G_genre = sparse.csr_matrix(list(gv["game_vectors"].values()))
M_genre = sparse.csr_matrix(list(gv["movie_vectors"].values()))

# load text vectors & meta
G_text = sparse.load_npz(os.path.join(DATA_DIR, "game_text.npz"))
M_text = sparse.load_npz(os.path.join(DATA_DIR, "movie_text.npz"))
with open(os.path.join(DATA_DIR, "text_meta.json")) as f:
    tm = json.load(f)
text_game_ids  = tm["game_ids"]
text_movie_ids = tm["movie_ids"]

# normalize for cosine
def normalize_rows(X):
    norms = np.sqrt(X.multiply(X).sum(axis=1)).A1
    norms[norms == 0] = 1.0
    inv = sparse.diags(1.0 / norms)
    return inv.dot(X)

G_text = normalize_rows(G_text)
M_text = normalize_rows(M_text)

session: Session = SessionLocal()
session.query(Recommendation).delete()
session.commit()

# pick whichever ID mapping matches; here we assume same order for genre & text
game_ids  = genre_game_ids
movie_ids = genre_movie_ids

for i, g_id in enumerate(tqdm(game_ids, desc="Scoring")):
    vg = G_genre[i].toarray().ravel()
    vt = G_text[i].toarray().ravel()

    # cosine on genres (binary vectors)
    mg = M_genre.dot(vg) / (np.linalg.norm(vg) * np.linalg.norm(M_genre, axis=1))
    # cosine on text
    mt = M_text.dot(vt)

    scores = ALPHA * mg + (1 - ALPHA) * mt
    top_idx = np.argsort(-scores)[:10]
    recs = [
        Recommendation(game_id=g_id,
                       movie_id=movie_ids[j],
                       score=float(scores[j]))
        for j in top_idx if scores[j] > 0.0
    ]

    session.bulk_save_objects(recs)
    if i % 500 == 0:
        session.commit()

session.commit()
session.close()
print("✅ Recommendations updated.")
