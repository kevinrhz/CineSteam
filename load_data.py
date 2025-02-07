import pandas as pd
import psycopg2
import ast


# -------------------- DATABASE CONNECTION --------------------
def connect_db():
    return psycopg2.connect(
        dbname="CineSteam",
        user="postgres",
        password="sqlIsCool123",
        host="localhost",
        port=5432
    )


# -------------------- RESET DATABASE --------------------
def reset_database(conn):
    with conn.cursor() as cur:
        with open("create_tables.sql", "r") as f:
            cur.execute(f.read())
    conn.commit()
    print("✅ Database reset and tables recreated.")


# -------------------- EXTRACT UNIQUE VALUES --------------------
def extract_unique_values(imdb_df, steam_df):
    genre_set, developer_set, publisher_set, director_set, actor_set, platform_set = set(), set(), set(), set(), set(), set()

    # Extract from IMDB Movies
    for _, row in imdb_df.iterrows():
        genre_set.update(row['Genre'].split(", ") if pd.notnull(row['Genre']) else [])
        director_set.add(row['Director'])
        actor_set.update([row['Star1'], row['Star2'], row['Star3'], row['Star4']])
    
    # Extract from Steam Games
    for _, row in steam_df.iterrows():
        genre_set.update(ast.literal_eval(row['genres']) if pd.notnull(row['genres']) else [])
        developer_set.update(ast.literal_eval(row['developers']) if pd.notnull(row['developers']) else [])
        publisher_set.update(ast.literal_eval(row['publishers']) if pd.notnull(row['publishers']) else [])
        platform_set.update(ast.literal_eval(row['platforms']) if pd.notnull(row['platforms']) else [])

    return genre_set, developer_set, publisher_set, director_set, actor_set, platform_set


# -------------------- INSERT UNIQUE VALUES --------------------
def insert_unique_values(cur, genre_set, developer_set, publisher_set, director_set, actor_set, platform_set):
    cur.executemany("INSERT INTO genres (genre_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(genre,) for genre in genre_set])
    cur.executemany("INSERT INTO developers (dev_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(dev,) for dev in developer_set])
    cur.executemany("INSERT INTO publishers (pub_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(pub,) for pub in publisher_set])
    cur.executemany("INSERT INTO directors (director_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(director,) for director in director_set])
    cur.executemany("INSERT INTO actors (actor_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(actor,) for actor in actor_set])
    cur.executemany("INSERT INTO platforms (platform_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(platform,) for platform in platform_set])


# -------------------- INSERT MOVIES --------------------
def insert_movies(cur, imdb_df):
    for _, row in imdb_df.iterrows():
        try:
            # Convert data
            released_year = int(row['Released_Year']) if str(row['Released_Year']).isdigit() else None
            runtime_min = int(row['Runtime'].replace(" min", "")) if pd.notnull(row['Runtime']) else None
            meta_score = int(row['Meta_score']) if pd.notnull(row['Meta_score']) else None
            gross = int(row['Gross'].replace(",", "")) if pd.notnull(row['Gross']) and row['Gross'].replace(",", "").isdigit() else None

            # Insert Movie
            cur.execute("""
                INSERT INTO imdb_top_1000 (poster_link, series_title, released_year, certificate, runtime_min,
                                           imdb_rating, overview, meta_score, no_of_votes, gross)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING movie_id;
            """, (row['Poster_Link'], row['Series_Title'], released_year, row['Certificate'],
                  runtime_min, row['IMDB_Rating'], row['Overview'], meta_score, row['No_of_Votes'], gross))

            movie_id = cur.fetchone()[0]

            # Insert Movie Mappings
            for genre in row['Genre'].split(", "):
                cur.execute("INSERT INTO movie_genres (movie_id, genre_id) SELECT %s, genre_id FROM genres WHERE genre_name = %s ON CONFLICT DO NOTHING;", (movie_id, genre))
            cur.execute("INSERT INTO movie_directors (movie_id, director_id) SELECT %s, director_id FROM directors WHERE director_name = %s ON CONFLICT DO NOTHING;", (movie_id, row['Director']))
            for actor in [row['Star1'], row['Star2'], row['Star3'], row['Star4']]:
                cur.execute("INSERT INTO movie_actors (movie_id, actor_id) SELECT %s, actor_id FROM actors WHERE actor_name = %s ON CONFLICT DO NOTHING;", (movie_id, actor))

        except Exception as e:
            conn.rollback()
            print(f"❌ ERROR inserting movie: {row['Series_Title']} - {e}")


# -------------------- INSERT GAMES + MAPPINGS --------------------
def insert_games_and_mappings(cur, steam_df):
    game_data = []
    
    for _, row in steam_df.iterrows():
        try:
            # Convert data
            release_date = None if str(row['release_date']).lower() == "not released" else pd.to_datetime(row['release_date']).date()
            metacritic = int(row['metacritic']) if pd.notnull(row['metacritic']) else None
            price_initial = float(row['price_initial (USD)']) if pd.notnull(row['price_initial (USD)']) else None

            # Store game data
            game_data.append((row['steam_appid'], row['name'], row['required_age'], row['n_achievements'],
                              row['is_released'], release_date, row['total_reviews'], row['total_positive'],
                              row['total_negative'], row['review_score'], row['review_score_desc'],
                              row['positive_percentual'], metacritic, row['is_free'], price_initial))

        except Exception as e:
            print(f"❌ ERROR processing game: {row['name']} - {e}")

    # Insert games
    cur.executemany("""
        INSERT INTO steam_games (steam_appid, name, required_age, n_achievements, is_released, release_date,
                                total_reviews, total_positive, total_negative, review_score, review_score_desc,
                                positive_percentual, metacritic, is_free, price_initial)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (steam_appid) DO NOTHING;
    """, game_data)

    # Debug: Print inserted game IDs
    cur.execute("SELECT steam_appid FROM steam_games;")
    inserted_games = cur.fetchall()
    print(f"✅ Total Games Inserted: {len(inserted_games)}")




# -------------------- MAIN EXECUTION --------------------
if __name__ == "__main__":
    conn = connect_db()
    reset_database(conn)
    cur = conn.cursor()

    imdb_df = pd.read_csv("data/imdb_top_1000.csv")
    steam_df = pd.read_csv("data/steam_games.csv")

    genre_set, developer_set, publisher_set, director_set, actor_set, platform_set = extract_unique_values(imdb_df, steam_df)
    insert_unique_values(cur, genre_set, developer_set, publisher_set, director_set, actor_set, platform_set)
    conn.commit()

    insert_movies(cur, imdb_df)
    insert_games_and_mappings(cur, steam_df)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Data successfully loaded!")
