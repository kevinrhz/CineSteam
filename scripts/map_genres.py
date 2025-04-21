from core.db import SessionLocal
from core.models import GenreMapping

# Define your mapping rules
GENRE_ALIASES = {
    'action': 'Action',
    'adventure': 'Adventure',
    'rpg': 'RPG',
    'strategy': 'Strategy',
    'simulation': 'Simulation',
    'horror': 'Horror',
    'indie': 'Indie',
    'casual': 'Casual',
    'sports': 'Sport',
    'sport': 'Sport',
    'sci-fi': 'Sci-Fi',
    'science fiction': 'Sci-Fi',
    'thriller': 'Thriller',
    'comedy': 'Comedy',
    'drama': 'Drama',
    'animation': 'Animation',
    'family': 'Family',
    'fantasy': 'Fantasy',
    'history': 'History',
    'war': 'War',
    'music': 'Music',
    'musical': 'Music',
    'crime': 'Crime',
    'documentary': 'Documentary',
    'romance': 'Romance',
    'mystery': 'Mystery',
    'western': 'Western',
    'nudity': 'Adult',
    'sexual content': 'Adult',
    'gore': 'Adult',
    'violent': 'Action',
    'massively multiplayer': 'Multiplayer',
    'free to play': 'Multiplayer',
    'episodic': 'TV-style',
    'design & illustration': 'Creative',
    'animation & modeling': 'Animation',
    'audio production': 'Creative',
    'photo editing': 'Creative',
    'utilities': 'Other',
    'education': 'Other',
    'software training': 'Other',
    'tutorial': 'Other',
    'game development': 'Other',
    'accounting': 'Other',
    'video production': 'Creative',
    'web publishing': 'Other',
}

def normalize(name: str) -> str:
    return name.strip("[]' ").lower()

def main():
    session = SessionLocal()

    try:
        mappings = session.query(GenreMapping).filter(GenreMapping.mapped_genre.is_(None)).all()
        updated = 0

        for mapping in mappings:
            raw = normalize(mapping.raw_genre)
            match = GENRE_ALIASES.get(raw)

            if match:
                mapping.mapped_genre = match
                updated += 1

        session.commit()
        print(f"✅ Updated {updated} mapped genres.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
