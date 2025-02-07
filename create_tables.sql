-- Drop tables if they exist
DROP TABLE IF EXISTS movie_actors, movie_directors, game_publishers, game_developers, game_platforms, 
                      movie_genres, game_genres, recommendations, imdb_top_1000, steam_games, 
                      genres, developers, publishers, directors, actors, platforms CASCADE;

-- Genres Table
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE
);

-- Movies Table
CREATE TABLE imdb_top_1000 (
    movie_id SERIAL PRIMARY KEY,
    poster_link TEXT,
    series_title VARCHAR(255),
    released_year INT,
    certificate VARCHAR(10),
    runtime_min INT,
    imdb_rating NUMERIC(3,1),
    overview TEXT,
    meta_score INT,
    no_of_votes BIGINT,
    gross BIGINT
);

-- Games Table
CREATE TABLE steam_games (
    game_id SERIAL PRIMARY KEY,
    steam_appid BIGINT UNIQUE,
    name VARCHAR(255),
    required_age INT,
    n_achievements INT,
    is_released BOOLEAN,
    release_date DATE,
    total_reviews BIGINT,
    total_positive BIGINT,
    total_negative BIGINT,
    review_score NUMERIC(4,1),
    review_score_desc VARCHAR(50),
    positive_percentual NUMERIC(5,2),
    metacritic INT,
    is_free BOOLEAN,
    price_initial NUMERIC(10,2)
);

-- Movie-Genre Relationship
CREATE TABLE movie_genres (
    movie_id INT REFERENCES imdb_top_1000(movie_id) ON DELETE CASCADE,
    genre_id INT REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- Game-Genre Relationship
CREATE TABLE game_genres (
    game_id INT REFERENCES steam_games(game_id) ON DELETE CASCADE,
    genre_id INT REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, genre_id)
);

-- Developers Table
CREATE TABLE developers (
    dev_id SERIAL PRIMARY KEY,
    dev_name VARCHAR(255) UNIQUE
);

-- Publishers Table
CREATE TABLE publishers (
    pub_id SERIAL PRIMARY KEY,
    pub_name VARCHAR(255) UNIQUE
);

-- Directors Table
CREATE TABLE directors (
    director_id SERIAL PRIMARY KEY,
    director_name VARCHAR(255) UNIQUE
);

-- Actors Table
CREATE TABLE actors (
    actor_id SERIAL PRIMARY KEY,
    actor_name VARCHAR(255) UNIQUE
);

-- Platforms Table
CREATE TABLE platforms (
    platform_id SERIAL PRIMARY KEY,
    platform_name VARCHAR(50) UNIQUE
);

-- Game-Developer Relationship
CREATE TABLE game_developers (
    game_id INT REFERENCES steam_games(game_id) ON DELETE CASCADE,
    dev_id INT REFERENCES developers(dev_id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, dev_id)
);

-- Game-Publisher Relationship
CREATE TABLE game_publishers (
    game_id INT REFERENCES steam_games(game_id) ON DELETE CASCADE,
    pub_id INT REFERENCES publishers(pub_id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, pub_id)
);

-- Game-Platform Relationship
CREATE TABLE game_platforms (
    game_id INT REFERENCES steam_games(game_id) ON DELETE CASCADE,
    platform_id INT REFERENCES platforms(platform_id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, platform_id)
);

-- Movie-Director Relationship
CREATE TABLE movie_directors (
    movie_id INT REFERENCES imdb_top_1000(movie_id) ON DELETE CASCADE,
    director_id INT REFERENCES directors(director_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, director_id)
);

-- Movie-Actor Relationship
CREATE TABLE movie_actors (
    movie_id INT REFERENCES imdb_top_1000(movie_id) ON DELETE CASCADE,
    actor_id INT REFERENCES actors(actor_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, actor_id)
);

-- Recommendations Table (Game → Movie Matches)
CREATE TABLE recommendations (
    game_id INT REFERENCES steam_games(game_id) ON DELETE CASCADE,
    movie_id INT REFERENCES imdb_top_1000(movie_id) ON DELETE CASCADE,
    similarity_score FLOAT DEFAULT 1.0,
    PRIMARY KEY (game_id, movie_id)
);
