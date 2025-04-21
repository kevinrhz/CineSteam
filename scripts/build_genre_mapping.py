from core.db import SessionLocal
from core.models import Genre, Game, Movie, GenreMapping

def main():
    session = SessionLocal()

    try:
        # Get genre usage in games
        game_genres = (
            session.query(Genre.name)
            .join(Game.genres)
            .distinct()
            .all()
        )

        # Get genre usage in movies
        movie_genres = (
            session.query(Genre.name)
            .join(Movie.genres)
            .distinct()
            .all()
        )

        game_genre_names = set(g[0] for g in game_genres)
        movie_genre_names = set(m[0] for m in movie_genres)

        all_used_genres = game_genre_names.union(movie_genre_names)

        print(f"Found {len(game_genre_names)} game genres, {len(movie_genre_names)} movie genres")

        count = 0
        for genre in sorted(all_used_genres):
            if genre is None:
                continue

            sources = []
            if genre in game_genre_names:
                sources.append("game")
            if genre in movie_genre_names:
                sources.append("movie")

            for source in sources:
                mapping = GenreMapping(
                    raw_genre=genre,
                    source=source,
                    mapped_genre=None  # You can update these later manually
                )
                session.add(mapping)
                count += 1

        session.commit()
        print(f"✅ Inserted {count} mappings into genre_mapping")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
