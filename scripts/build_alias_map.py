import os
import json
from core.db import SessionLocal
from core.models import Game, Movie

# Paths
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
alias_keywords_path = os.path.join(data_dir, 'alias_keywords.json')
alias_map_path      = os.path.join(data_dir, 'alias_map.json')


def load_alias_keywords():
    with open(alias_keywords_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_aliases(text: str, alias_map: dict) -> list:
    txt = (text or '').lower()
    hits = []
    for alias, keywords in alias_map.items():
        for kw in keywords:
            if kw in txt:
                hits.append(alias)
                break
    return hits


def main():
    alias_keywords = load_alias_keywords()
    session = SessionLocal()

    game_aliases = {}
    for game in session.query(Game).all():
        game_aliases[str(game.id)] = find_aliases(game.description, alias_keywords)

    movie_aliases = {}
    for movie in session.query(Movie).all():
        movie_aliases[str(movie.id)] = find_aliases(movie.overview, alias_keywords)

    session.close()

    with open(alias_map_path, 'w', encoding='utf-8') as f:
        json.dump({
            'aliases': list(alias_keywords.keys()),
            'game_aliases': game_aliases,
            'movie_aliases': movie_aliases
        }, f, indent=2)

    print(f"✅ Alias map written to {alias_map_path}")


if __name__ == '__main__':
    main()