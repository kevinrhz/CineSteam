import pandas as pd
import psycopg2


def main():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname="CineSteam",
        user="postgres",
        password="sqlIsCool123",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()

    # Read CSV files with pandas
    imdb_df = pd.read_csv("data/imdb_top_1000.csv")
    steam_df = pd.read_csv("data/steam_games.csv")



    # Insert IMDB movies
    for idx, row in imdb_df.iterrows():
        poster_link = row['Poster_Link']
        series_title = row['Series_Title']
        released_year = row['Released_Year']

        # Change 'Runtime' from "142 min" to  (int)142
        runtime_str = row['Runtime']
        runtime_min = None
        if pd.notnull(runtime_str):
            runtime_min = int(runtime_str.replace(" min", ""))

        genre = row ['Genre']
        imdb_rating = row['IMDB_Rating']
        overview = row['Overview']
        meta_score = row['Meta_score']
        director = row['Director']
        star1 = row['Star1']
        star2 = row['Star2']
        star3 = row['Star3']
        star4 = row['Star4']
        no_of_votes = row['No_of_Votes']

        # Change 'Gross' from "28,000,000" to (int)28000000
        gross_str = row['Gross']
        gross = None
        if pd.notnull(gross_str):
            gross = int(gross_str.replace(",", ""))


        cur.execute("""
            INSERT INTO imdb_top_1000 (
                poster_link, series_title, released_year, certificate, runtime_min,
                genre, imdb_rating, overview, meta_score, director,
                star1, star2, star3, star4, no_of_votes, gross
            )
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s);
        """, (
            poster_link, series_title, released_year, row['Certificate'], runtime_min,
            genre, imdb_rating, overview, meta_score, director,
            star1, star2, star3, star4, no_of_votes, gross
        ))

    

    # Insert Steam games
    for idx, row in steam_df.iterrows():
        steam_appid = row['steam_appid']
        name = row['name']
        developers = str(row['developers'])
        publishers = str(row['publishers'])
        categories = str(row['categories'])
        genres = str(row['genres'])
        required_age = row['required_age']
        n_achievements = row['n_achievements']
        platforms = str(row['platforms'])

        # check if is_released is boolean or string
        is_released_raw = row['is_released']
        if isinstance(is_released_raw, bool):
            is_released = is_released_raw
        else:
            is_released = (str(is_released_raw).lower() == "true")

        # Make release_date into a real DATE is possible
        release_date_str = str(row['release_date']).strip()
        parsed_release_date = None
        if release_date_str.lower() != 'not released':
            try:
                parsed_dt = pd.to_datetime(release_date_str)
                parsed_release_date = parsed_dt.date()
            except:
                parsed_release_date = None


        additional_content = str(row['additional_content'])
        total_reviews = row['total_reviews']
        total_positive = row['total_positive']
        total_negative = row['total_negative']
        review_score = row['review_score']
        review_score_desc = row['review_score_desc']
        positive_percentual = row['positive_percentual']
        metacritic = row['metacritic']

        # check if is_free is boolean
        is_free_raw = row['is_free']
        if isinstance(is_free_raw, bool):
            is_free = is_free_raw
        else:
            is_free = (str(is_free_raw).lower() == "true")
        
        price_initial = row['price_initial']


        cur.execute("""
            INSERT INTO steam_games (
                steam_appid, name, developers, publishers, categories,
                genres, required_age, n_achievements, platforms, is_released,
                release_date, additional_content, total_reviews, total_positive,
                total_negative, review_score, review_score_desc, positive_percentual,
                metacritic, is_free, price_initial
            )
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s);
        """, (
            steam_appid, name, developers, publishers, categories,
            genres, required_age, n_achievements, platforms, is_released,
            parsed_release_date, additional_content, total_reviews, total_positive,
            total_negative, review_score, review_score_desc, positive_percentual,
            metacritic, is_free, price_initial
        ))



    # Commit and close
    conn.commit()
    cur.close()
    conn.close()
    print("Data loaded successfully!")


if __name__ == "__main__":
    main()