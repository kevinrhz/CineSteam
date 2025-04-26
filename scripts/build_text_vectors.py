import os
import json
from tqdm import tqdm
from scipy import sparse
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from core.db import SessionLocal
from core.models import Game, Movie

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    session = SessionLocal()
    games  = session.query(Game).filter(Game.description.isnot(None)).all()
    movies = session.query(Movie).filter(Movie.overview.isnot(None)).all()

    game_texts  = [g.description for g in games]
    movie_texts = [m.overview    for m in movies]

    vectorizer = TfidfVectorizer(
        max_features=50_000,
        stop_words="english",
        ngram_range=(1,2)
    )
    all_texts = game_texts + movie_texts
    X = vectorizer.fit_transform(tqdm(all_texts, desc="TF-IDF"))

    G = X[: len(games)]
    M = X[len(games):]

    # save sparse matrices
    sparse.save_npz(os.path.join(DATA_DIR, "game_text.npz"), G)
    sparse.save_npz(os.path.join(DATA_DIR, "movie_text.npz"), M)

    # cast everything to built-in ints for JSON
    vocab = { term: int(idx)
              for term, idx in vectorizer.vocabulary_.items() }
    meta = {
        "vocabulary": vocab,
        "game_ids":   [int(g.id) for g in games],
        "movie_ids":  [int(m.id) for m in movies]
    }
    with open(os.path.join(DATA_DIR, "text_meta.json"), "w") as f:
        json.dump(meta, f)

    print("✅ Text vectors built and saved.")
    session.close()

if __name__ == "__main__":
    main()
