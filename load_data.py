import pandas as pd
import psycopg2


def main():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname="CineSteam",
        user="postgres",
        password="sqlIsCool123"
        host="localhost",
        port=5432
    )
    cur = conn.cursor()

    # Read CSV files with pandas
    imdb_df = pd.read_csv("data/imdb_top_1000.csv")
    steam_df = pd.read_csv("data/steam_games.csv")
