#!/usr/bin/env python
from core.db import SessionLocal
from core.models import Game, Movie, Recommendation

def get_movie_recs_for_game(game_name: str, top_k: int = 10):
    session = SessionLocal()
    try:
        game = session.query(Game).filter(Game.name.ilike(game_name)).first()
        if not game:
            print(f"❌ No game found matching “{game_name}”.")
            return

        print(f"\n🎮 Game: {game.name}  (ID {game.id}, {game.release_year})")
        print(f"📽️  Top {top_k} movie recommendations:\n")

        recs = (
            session.query(Recommendation, Movie)
                   .join(Movie, Recommendation.movie_id == Movie.id)
                   .filter(Recommendation.game_id == game.id)
                   .order_by(Recommendation.score.desc())
                   .limit(top_k)
                   .all()
        )

        for rank, (rec, movie) in enumerate(recs, start=1):
            print(f"{rank:2d}. {movie.title} ({movie.release_year}) — score {rec.score:.3f}")
    finally:
        session.close()

def main():
    print("Enter a Steam game name (or part of it), then ⏎ to see recs. Empty = exit.")
    while True:
        q = input("\nGame name → ").strip()
        if not q:
            break
        get_movie_recs_for_game(q)

if __name__ == "__main__":
    main()
