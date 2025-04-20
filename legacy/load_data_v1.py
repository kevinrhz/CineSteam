import pandas as pd
import psycopg2
import ast


# Database Connection
def connect_db():
    return psycopg2.connect(
        dbname="CineSteam",
        user="postgres",
        password="sqlIsCool123",
        host="localhost",
        port=5432
    )


# Drop and Recreate Tables
def reset_database(conn):
    with conn.cursor() as cur:
        with open("create_tables.sql", "r") as f:
            sql_commands = f.read()
        cur.execute(sql_commands)
    conn.commit()
    print("Database reset and tables recreated.")


# Extract Unique Values (Genres, Developers, Publishers, Actors, Directors)
def extract_unique_values(imdb_df, steam_df):
    genre_set, developer_set, publisher_set, director_set, actor_set, platform_set = set(), set(), set(), set(), set(), set()

    # Extract from IMDB Moves
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


# Insert Unique Values (Genres, Developers, Publishers, Actors, Directors)
# Batch Inserts sends all insertions in a single query per table making it much faster than the separate loops I had before
def insert_unique_values(cur, genre_set, developer_set, publisher_set, director_set, actor_set, platform_set):
    cur.executemany("INSERT INTO genres (genre_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(genre,) for genre in genre_set])
    cur.executemany("INSERT INTO developers (dev_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(dev,) for dev in developer_set])
    cur.executemany("INSERT INTO publishers (pub_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(pub,) for pub in publisher_set])
    cur.executemany("INSERT INTO directors (director_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(director,) for director in director_set])
    cur.executemany("INSERT INTO actors (actor_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(actor,) for actor in actor_set])
    cur.executemany("INSERT INTO platforms (platform_name) VALUES (%s) ON CONFLICT DO NOTHING;", [(platform,) for platform in platform_set])


# Insert IMDB Movies and their relationships
def insert_movies(cur, imdb_df):
    for _, row in imdb_df.iterrows():
        try:
            # Some released_year entries mistakenly have 'Certified' data entires i.e. "G" or "PG"
            # Ensure released_year is either INT or NULL type
            released_year = str(row['Released_Year']).strip()
            released_year = int(released_year) if released_year.isdigit() else None

            # Convert "142 min" -> int(142)
            runtime_min = None
            if pd.notnull(row['Runtime']):
                runtime_str = row['Runtime'].replace(" min", "")
                runtime_min = int(runtime_str) if runtime_str.isdigit() else None
            
            meta_score = int(row['Meta_score']) if pd.notnull(row['Meta_score']) else None
            gross = int(row['Gross'].replace(",", "")) if pd.notnull(row['Gross']) and row['Gross'].replace(",", "").isdigit() else None

            # Insert Movie
            cur.execute("""
                INSERT INTO imdb_top_1000 (
                    poster_link, series_title, released_year, certificate, runtime_min,
                    imdb_rating, overview, meta_score, no_of_votes, gross
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING movie_id;
            """, (
                row['Poster_Link'], row['Series_Title'], released_year, row['Certificate'],
                runtime_min, row['IMDB_Rating'], row['Overview'], meta_score, row['No_of_Votes'], gross
            ))
            movie_id = cur.fetchone()[0]


            # Link Genres
            for genre in row['Genre'].split(", "):
                cur.execute("INSERT INTO movie_genres (movie_id, genre_id) SELECT %s, genre_id FROM genres WHERE genre_name = %s;", (movie_id, genre))

            # Link Director
            cur.execute("INSERT INTO movie_directors (movie_id, director_id) SELECT %s, director_id FROM directors WHERE director_name = %s;", (movie_id, row['Director']))

            # Link Actors
            for actor in [row['Star1'], row['Star2'], row['Star3'], row['Star4']]:
                cur.execute("INSERT INTO movie_actors (movie_id, actor_id) SELECT %s, actor_id FROM actors WHERE actor_name = %s;", (movie_id, actor))


        except Exception as e:
            conn.rollback()
            print(f"ERROR inserting movie: {row['Series_Title']} - {e}")
            print(f"Query values: {row['Poster_Link'], row['Series_Title'], released_year, row['Certificate'], runtime_min, row['IMDB_Rating'], row['Overview'], meta_score, row['No_of_Votes'], gross}")
            continue





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

    # Insert movies and games
    insert_movies(cur, imdb_df)
    # insert_games(cur, steam_df)

    conn.commit()
    cur.close()
    conn.close()
    print("Data successfully loaded!")