from core.db import SessionLocal
from core.models import GenreAlias, Game, Movie

# Keywords in aliases that should trigger flags
ADULT_FLAGS = {'nudity', 'adult', 'sexual content'}
MULTIPLAYER_FLAGS = {'multiplayer', 'online co-op', 'massively multiplayer'}
TV_FLAGS = {'episodic', 'tv-style'}

def normalize(name: str) -> str:
    return name.strip("[]' ").lower()

def main():
    session = SessionLocal()
    try:
        # Build lookup
        alias_lookup = session.query(GenreAlias).all()
        flag_map = {}
        for alias in alias_lookup:
            norm = normalize(alias.alias)
            if norm in ADULT_FLAGS:
                flag_map[norm] = 'is_adult'
            elif norm in MULTIPLAYER_FLAGS:
                flag_map[norm] = 'is_multiplayer'
            elif norm in TV_FLAGS:
                flag_map[norm] = 'is_tv_format'

        # Flag games
        games = session.query(Game).all()
        for game in games:
            for genre in game.genres:
                gname = normalize(genre.name)
                if gname in flag_map:
                    setattr(game, flag_map[gname], True)

        # Flag movies
        movies = session.query(Movie).all()
        for movie in movies:
            for genre in movie.genres:
                gname = normalize(genre.name)
                if gname in flag_map:
                    setattr(movie, flag_map[gname], True)

        session.commit()
        print("✅ Flags applied to all games and movies.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
