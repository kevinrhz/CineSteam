from sqlalchemy import func
from core.db import SessionLocal
from core.models import Game, Recommendation, Movie

def main():
    s = SessionLocal()
    try:
        while True:
            q = input("\nType a game name (exact/partial), blank to exit:\n→ ").strip()
            if not q: break

            game = s.query(Game).filter(func.lower(Game.name)==q.lower()).first()
            if not game:
                game = s.query(Game)\
                        .filter(Game.name.ilike(f"%{q}%"))\
                        .order_by(Game.release_year.desc())\
                        .first()

            if not game:
                print(f"❌ No game matches “{q}”.")
                continue

            print(f"\n🎮  {game.name}  ({game.release_year})")
            recs = s.query(Recommendation, Movie)\
                    .join(Movie, Recommendation.movie_id==Movie.id)\
                    .filter(Recommendation.game_id==game.id)\
                    .order_by(Recommendation.score.desc())\
                    .limit(10).all()

            if not recs:
                print("📽️  (no recommendations)")
            else:
                print("📽️  Top 10 movies:\n")
                for i,(r,m) in enumerate(recs,1):
                    print(f" {i:2d}. {m.title} ({m.release_year}) — {r.score:.3f}")
    finally:
        s.close()

if __name__=="__main__":
    main()
