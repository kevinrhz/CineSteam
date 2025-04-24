from core.db import SessionLocal
from core.models import Genre, GenreAlias


GENRE_ALIASES = {
    # 1-to-1 canonical matches
    'action':        ['Action'],
    'adventure':     ['Adventure'],
    'rpg':           ['RPG'],
    'strategy':      ['Strategy'],
    'simulation':    ['Simulation'],
    'sports':        ['Sport'],
    'sport':         ['Sport'],
    'racing':        ['Sport'],
    'casual':        ['Casual'],
    'indie':         ['Indie'],
    'horror':        ['Horror'],
    'gore':          ['Horror'],
    'thriller':      ['Thriller'],
    'mystery':       ['Mystery'],
    'crime':         ['Crime'],
    'drama':         ['Drama'],
    'comedy':        ['Comedy'],
    'family':        ['Family'],
    'fantasy':       ['Fantasy'],
    'sci-fi':        ['Sci-Fi'],
    'science fiction': ['Sci-Fi'],
    'animation':     ['Animation'],
    'music':         ['Music'],
    'musical':       ['Music'],
    'war':           ['War'],
    'western':       ['Western'],
    'history':       ['History'],
    'documentary':   ['Documentary'],
    'romance':       ['Romance'],

    # Multi-mapping 
    'biography':     ['Documentary', 'History'],
    'film-noir':     ['Crime', 'Thriller', 'Drama'],
    'violent':       ['Action'],

    # Flags (will live in alias_genres but not used in vector dims)
    'adult':         ['_FLAG_ADULT'],
    'nudity':        ['_FLAG_ADULT'],
    'sexual content':['_FLAG_ADULT'],
    'episodic':      ['_FLAG_TV'],
    'tv-style':      ['_FLAG_TV'],
    'free to play':  ['_FLAG_BUSINESS'],
    'massively multiplayer':['_FLAG_MULTIPLAYER'],
    'multiplayer':   ['_FLAG_MULTIPLAYER'],
    'online co-op':  ['_FLAG_MULTIPLAYER'],
}

def normalize(raw: str) -> str:
    """Strip quotes/brackets and lowercase."""
    return raw.strip("[]'\" ").lower()

def main():
    session = SessionLocal()
    try:
        # Clear out old aliases
        session.query(GenreAlias).delete()
        session.commit()

        added = 0
        for raw_alias, canon_list in GENRE_ALIASES.items():
            alias_key = normalize(raw_alias)
            # Create a new GenreAlias row
            ga = GenreAlias(alias=alias_key, source="both")  # or 'game'/'movie' if you split
            # Link to each canonical Genre
            for canon in canon_list:
                genre = session.query(Genre).filter_by(name=canon).one_or_none()
                if genre:
                    ga.genres.append(genre)
                else:
                    print(f"⚠️  Canonical genre not found: {canon}")
            session.add(ga)
            added += 1

        session.commit()
        print(f"✅ Inserted {added} genre aliases.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error in load_aliases: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()

