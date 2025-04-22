from core.db import SessionLocal
from core.models import Genre, GenreAlias, AliasGenre

GENRE_ALIASES = {
    # Single-map
    'action': ['Action'],
    'adventure': ['Adventure'],
    'rpg': ['RPG'],
    'strategy': ['Strategy'],
    'simulation': ['Simulation'],
    'sports': ['Sport'],
    'sport': ['Sport'],
    'racing': ['Sport'],
    'casual': ['Casual'],
    'indie': ['Indie'],
    'horror': ['Horror'],
    'gore': ['Horror'],
    'thriller': ['Thriller'],
    'mystery': ['Mystery'],
    'crime': ['Crime'],
    'drama': ['Drama'],
    'comedy': ['Comedy'],
    'family': ['Family'],
    'fantasy': ['Fantasy'],
    'sci-fi': ['Sci-Fi'],
    'science fiction': ['Sci-Fi'],
    'animation': ['Animation'],
    'music': ['Music'],
    'musical': ['Music'],
    'war': ['War'],
    'western': ['Western'],
    'history': ['History'],
    'documentary': ['Documentary'],
    'romance': ['Romance'],

    # Multi-map
    'biography': ['Documentary', 'History'],
    'film-noir': ['Crime', 'Thriller', 'Drama'],
    'violent': ['Action'],

    # Flags (ignored from linking to genre_id)
    'adult': ['_FLAG_ADULT'],
    'nudity': ['_FLAG_ADULT'],
    'sexual content': ['_FLAG_ADULT'],
    'episodic': ['_FLAG_TV'],
    'tv-style': ['_FLAG_TV'],
    'free to play': ['_FLAG_BUSINESS'],
    'massively multiplayer': ['_FLAG_MULTIPLAYER'],
    'multiplayer': ['_FLAG_MULTIPLAYER'],
    'online co-op': ['_FLAG_MULTIPLAYER'],
}

def normalize(name: str) -> str:
    return name.strip("[]' ").lower()

def main():
    session = SessionLocal()
    try:
        count = 0
        for raw, canon_list in GENRE_ALIASES.items():
            alias_entry = GenreAlias(alias=raw, source='game')  # or 'movie' if needed later
            session.add(alias_entry)
            session.flush()  # get alias.id

            for target in canon_list:
                if not target.startswith("_FLAG"):
                    genre = session.query(Genre).filter(Genre.name == target).first()
                    if not genre:
                        genre = Genre(name=target)
                        session.add(genre)
                        session.flush()
                    session.add(AliasGenre(alias_id=alias_entry.id, genre_id=genre.id))
                    count += 1

        session.commit()
        print(f"✅ Loaded {count} genre alias mappings.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
