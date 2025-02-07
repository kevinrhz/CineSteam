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




# -------------------- INSERT MOVIES --------------------
def insert_movies(cur, imdb_df):
    """Inserts movies into imdb_top_1000 table."""
    movie_data = []

    for _, row in imdb_df.iterrows():
        try:
            # Convert Data Safely
            released_year = int(row['Released_Year']) if str(row['Released_Year']).isdigit() else None
            runtime_min = int(row['Runtime'].replace(" min", "")) if pd.notnull(row['Runtime']) else None
            meta_score = int(row['Meta_score']) if pd.notnull(row['Meta_score']) else None
            gross = int(row['Gross'].replace(",", "")) if pd.notnull(row['Gross']) and row['Gross'].replace(",", "").isdigit() else None

            # Store for batch insert
            movie_data.append((row['Poster_Link'], row['Series_Title'], released_year, row['Certificate'],
                               runtime_min, row['IMDB_Rating'], row['Overview'], meta_score, row['No_of_Votes'], gross))

        except Exception as e:
            print(f"❌ ERROR processing movie: {row['Series_Title']} - {e}")

    # Batch Insert Movies
    if movie_data:
        cur.executemany("""
            INSERT INTO imdb_top_1000 (poster_link, series_title, released_year, certificate, runtime_min,
                                       imdb_rating, overview, meta_score, no_of_votes, gross)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, movie_data)

    print(f"✅ Inserted {len(movie_data)} movies into imdb_top_1000.")



# -------------------- INSERT MOVIE MAPPINGS--------------------
def insert_movie_mappings(cur, imdb_df):
    """Inserts movie mappings into movie_genres, movie_directors, movie_actors tables."""
    movie_genres, movie_directors, movie_actors = [], [], []

    for _, row in imdb_df.iterrows():
        # Get movie_id
        cur.execute("SELECT movie_id FROM imdb_top_1000 WHERE series_title = %s;", (row['Series_Title'],))
        movie_id_result = cur.fetchone()
        if not movie_id_result:
            print(f"⚠️ Skipping {row['Series_Title']} - Movie not found in imdb_top_1000.")
            continue

        movie_id = movie_id_result[0]

        # Extract Genres
        if pd.notnull(row['Genre']):
            genres_list = row['Genre'].split(", ")
            movie_genres.extend((movie_id, genre) for genre in genres_list)

        # Extract Director
        if pd.notnull(row['Director']):
            movie_directors.append((movie_id, row['Director']))

        # Extract Actors
        for actor in [row['Star1'], row['Star2'], row['Star3'], row['Star4']]:
            if pd.notnull(actor):
                movie_actors.append((movie_id, actor))

    # Batch Insert Mappings
    if movie_genres:
        cur.executemany("""
            INSERT INTO movie_genres (movie_id, genre_id)
            SELECT %s, genre_id FROM genres WHERE genre_name = %s
            ON CONFLICT DO NOTHING;
        """, movie_genres)

    if movie_directors:
        cur.executemany("""
            INSERT INTO movie_directors (movie_id, director_id)
            SELECT %s, director_id FROM directors WHERE director_name = %s
            ON CONFLICT DO NOTHING;
        """, movie_directors)

    if movie_actors:
        cur.executemany("""
            INSERT INTO movie_actors (movie_id, actor_id)
            SELECT %s, actor_id FROM actors WHERE actor_name = %s
            ON CONFLICT DO NOTHING;
        """, movie_actors)

    print(f"✅ Inserted {len(movie_genres)} movie-genre pairs.")
    print(f"✅ Inserted {len(movie_directors)} movie-director pairs.")
    print(f"✅ Inserted {len(movie_actors)} movie-actor pairs.")





# -------------------- INSERT GAMES --------------------
def insert_games(cur, steam_df):
    """Inserts games into steam_games table."""
    game_data = []

    for _, row in steam_df.iterrows():
        try:
            # Convert data safely
            release_date = None if str(row['release_date']).lower() == "not released" else pd.to_datetime(row['release_date']).date()
            metacritic = int(row['metacritic']) if pd.notnull(row['metacritic']) else None
            price_initial = float(row['price_initial (USD)']) if pd.notnull(row['price_initial (USD)']) else None

            # Store game data for batch insert
            game_data.append((row['steam_appid'], row['name'], row['required_age'], row['n_achievements'],
                              row['is_released'], release_date, row['total_reviews'], row['total_positive'],
                              row['total_negative'], row['review_score'], row['review_score_desc'],
                              row['positive_percentual'], metacritic, row['is_free'], price_initial))

        except Exception as e:
            print(f"❌ ERROR processing game: {row['name']} - {e}")

    # Batch Insert Games
    if game_data:
        cur.executemany("""
            INSERT INTO steam_games (steam_appid, name, required_age, n_achievements, is_released, release_date,
                                    total_reviews, total_positive, total_negative, review_score, review_score_desc,
                                    positive_percentual, metacritic, is_free, price_initial)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (steam_appid) DO NOTHING;
        """, game_data)

    print(f"✅ Inserted {len(game_data)} games into steam_games.")



# -------------------- INSERT GAME MAPPINGS --------------------
def insert_game_mappings(cur, steam_df):
    """Inserts game mappings into game_genres, game_developers, game_publishers, game_platforms tables."""
    game_genres, game_developers, game_publishers, game_platforms = [], [], [], []

    for _, row in steam_df.iterrows():
        # Get game_id
        cur.execute("SELECT game_id FROM steam_games WHERE steam_appid = %s;", (row['steam_appid'],))
        game_id_result = cur.fetchone()
        if not game_id_result:
            print(f"⚠️ Skipping {row['name']} - Game not found in steam_games.")
            continue

        game_id = game_id_result[0]

        # Extract Mappings
        if pd.notnull(row['genres']):
            try:
                genres_list = ast.literal_eval(row['genres'])
                game_genres.extend((game_id, genre) for genre in genres_list)
            except Exception as e:
                print(f"❌ Error extracting genres for {row['name']}: {e}")

        if pd.notnull(row['developers']):
            try:
                developers_list = ast.literal_eval(row['developers'])
                game_developers.extend((game_id, dev) for dev in developers_list)
            except Exception as e:
                print(f"❌ Error extracting developers for {row['name']}: {e}")

        if pd.notnull(row['publishers']):
            try:
                publishers_list = ast.literal_eval(row['publishers'])
                game_publishers.extend((game_id, pub) for pub in publishers_list)
            except Exception as e:
                print(f"❌ Error extracting publishers for {row['name']}: {e}")

        if pd.notnull(row['platforms']):
            try:
                platforms_list = ast.literal_eval(row['platforms'])
                game_platforms.extend((game_id, platform) for platform in platforms_list)
            except Exception as e:
                print(f"❌ Error extracting platforms for {row['name']}: {e}")

    # Batch Insert Mappings
    if game_genres:
        cur.executemany("""
            INSERT INTO game_genres (game_id, genre_id)
            SELECT %s, genre_id FROM genres WHERE genre_name = %s
            ON CONFLICT DO NOTHING;
        """, game_genres)

    if game_developers:
        cur.executemany("""
            INSERT INTO game_developers (game_id, dev_id)
            SELECT %s, dev_id FROM developers WHERE dev_name = %s
            ON CONFLICT DO NOTHING;
        """, game_developers)

    if game_publishers:
        cur.executemany("""
            INSERT INTO game_publishers (game_id, pub_id)
            SELECT %s, pub_id FROM publishers WHERE pub_name = %s
            ON CONFLICT DO NOTHING;
        """, game_publishers)

    if game_platforms:
        cur.executemany("""
            INSERT INTO game_platforms (game_id, platform_id)
            SELECT %s, platform_id FROM platforms WHERE platform_name = %s
            ON CONFLICT DO NOTHING;
        """, game_platforms)

    print(f"✅ Inserted {len(game_genres)} game-genre pairs.")
    print(f"✅ Inserted {len(game_developers)} game-developer pairs.")
    print(f"✅ Inserted {len(game_publishers)} game-publisher pairs.")
    print(f"✅ Inserted {len(game_platforms)} game-platform pairs.")






# -------------------- EXTRACT UNIQUE VALUES --------------------
def extract_unique_values(imdb_df, steam_df):
    """Extracts unique genres, developers, publishers, directors, actors, and platforms from movie and game data."""
    genre_set, developer_set, publisher_set, director_set, actor_set, platform_set = set(), set(), set(), set(), set(), set()

    # Extract from IMDB Movies
    for _, row in imdb_df.iterrows():
        if pd.notnull(row['Genre']):
            genre_set.update(row['Genre'].split(", "))
        if pd.notnull(row['Director']):
            director_set.add(row['Director'])
        for actor in [row['Star1'], row['Star2'], row['Star3'], row['Star4']]:
            if pd.notnull(actor):
                actor_set.add(actor)

    # Extract from Steam Games
    for _, row in steam_df.iterrows():
        if pd.notnull(row['genres']):
            try:
                genre_set.update(ast.literal_eval(row['genres']))
            except Exception as e:
                print(f"❌ Error extracting genres for {row['name']}: {e}")

        if pd.notnull(row['developers']):
            try:
                developer_set.update(ast.literal_eval(row['developers']))
            except Exception as e:
                print(f"❌ Error extracting developers for {row['name']}: {e}")

        if pd.notnull(row['publishers']):
            try:
                publisher_set.update(ast.literal_eval(row['publishers']))
            except Exception as e:
                print(f"❌ Error extracting publishers for {row['name']}: {e}")

        if pd.notnull(row['platforms']):
            try:
                platform_set.update(ast.literal_eval(row['platforms']))
            except Exception as e:
                print(f"❌ Error extracting platforms for {row['name']}: {e}")

    return genre_set, developer_set, publisher_set, director_set, actor_set, platform_set



# -------------------- INSERT UNIQUE VALUES --------------------
def insert_unique_values(cur, genre_set, developer_set, publisher_set, director_set, actor_set, platform_set):
    """Inserts unique values into genres, developers, publishers, directors, actors, and platforms tables."""
    if genre_set:
        cur.executemany("INSERT INTO genres (genre_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(genre,) for genre in genre_set])

    if developer_set:
        cur.executemany("INSERT INTO developers (dev_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(dev,) for dev in developer_set])

    if publisher_set:
        cur.executemany("INSERT INTO publishers (pub_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(pub,) for pub in publisher_set])

    if director_set:
        cur.executemany("INSERT INTO directors (director_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(director,) for director in director_set])

    if actor_set:
        cur.executemany("INSERT INTO actors (actor_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(actor,) for actor in actor_set])

    if platform_set:
        cur.executemany("INSERT INTO platforms (platform_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(platform,) for platform in platform_set])

    print(f"✅ Inserted {len(genre_set)} genres.")
    print(f"✅ Inserted {len(developer_set)} developers.")
    print(f"✅ Inserted {len(publisher_set)} publishers.")
    print(f"✅ Inserted {len(director_set)} directors.")
    print(f"✅ Inserted {len(actor_set)} actors.")
    print(f"✅ Inserted {len(platform_set)} platforms.")







# -------------------- MAIN EXECUTION --------------------
if __name__ == "__main__":
    conn = connect_db()
    reset_database(conn)
    cur = conn.cursor()

    imdb_df = pd.read_csv("data/imdb_top_1000.csv")
    steam_df = pd.read_csv("data/steam_games.csv")

    # Extract and insert unique values
    genre_set, developer_set, publisher_set, director_set, actor_set, platform_set = extract_unique_values(imdb_df, steam_df)
    insert_unique_values(cur, genre_set, developer_set, publisher_set, director_set, actor_set, platform_set)
    conn.commit()

    # Insert movies and mappings
    insert_movies(cur, imdb_df)
    insert_movie_mappings(cur, imdb_df)

    
    # Insert games and mappings
    insert_games(cur, steam_df)
    insert_game_mappings(cur, steam_df)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Data successfully loaded!")
