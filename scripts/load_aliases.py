from core.db import SessionLocal
from core.models import Genre, GenreAlias

GENRE_ALIASES = {
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
    'science fiction':['Sci-Fi'],
    'animation':     ['Animation'],
    'music':         ['Music'],
    'musical':       ['Music'],
    'war':           ['War'],
    'western':       ['Western'],
    'history':       ['History'],
    'documentary':   ['Documentary'],
    'romance':       ['Romance'],
    'biography':     ['Documentary','History'],
    'film-noir':     ['Crime','Thriller','Drama'],
    'violent':       ['Action'],
    'adult':         ['_FLAG_ADULT'],
    'nudity':        ['_FLAG_ADULT'],
    'sexual content':['_FLAG_ADULT'],
    'episodic':      ['_FLAG_TV'],
    'tv-style':      ['_FLAG_TV'],
    'free to play':  ['_FLAG_BUSINESS'],
    'multiplayer':   ['_FLAG_MULTIPLAYER'],
    'massively multiplayer':['_FLAG_MULTIPLAYER'],
    'online co-op':  ['_FLAG_MULTIPLAYER'],
}

def normalize(s: str) -> str:
    return s.strip("[]'\" ").lower()

def main():
    session = SessionLocal()
    try:
        # ensure every canonical genre row exists
        canons = {c for lst in GENRE_ALIASES.values() for c in lst if not c.startswith("_FLAG_")}
        for c in canons:
            session.query(Genre).filter_by(name=c).first() \
                or session.add(Genre(name=c))
        session.commit()

        # clear old
        session.query(GenreAlias).delete()
        session.commit()

        added = 0
        for raw, canon_list in GENRE_ALIASES.items():
            key = normalize(raw)
            ga = GenreAlias(alias=key, source='both')
            for canon in canon_list:
                g = session.query(Genre).filter_by(name=canon).one_or_none()
                if g:
                    ga.genres.append(g)
                else:
                    print(f"⚠️  Canonical genre missing: {canon}")
            session.add(ga)
            added += 1

        session.commit()
        print(f"✅ Inserted {added} genre aliases.")
    except Exception as e:
        session.rollback()
        print(f"❌ load_aliases error: {e}")
        raise
    finally:
        session.close()

if __name__=="__main__":
    main()
