from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from .db import Base

# --- Association Tables ---

game_genres = Table(
    "game_genres", Base.metadata,
    Column("game_id", ForeignKey("games.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True)
)

movie_genres = Table(
    "movie_genres", Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True)
)

game_developers = Table(
    "game_developers", Base.metadata,
    Column("game_id", ForeignKey("games.id"), primary_key=True),
    Column("developer_id", ForeignKey("developers.id"), primary_key=True)
)

game_publishers = Table(
    "game_publishers", Base.metadata,
    Column("game_id", ForeignKey("games.id"), primary_key=True),
    Column("publisher_id", ForeignKey("publishers.id"), primary_key=True)
)

game_platforms = Table(
    "game_platforms", Base.metadata,
    Column("game_id", ForeignKey("games.id"), primary_key=True),
    Column("platform_id", ForeignKey("platforms.id"), primary_key=True)
)

movie_directors = Table(
    "movie_directors", Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("director_id", ForeignKey("directors.id"), primary_key=True)
)

movie_actors = Table(
    "movie_actors", Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("actor_id", ForeignKey("actors.id"), primary_key=True)
)

# --- Entity Models ---

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    release_year = Column(Integer)

    genres = relationship("Genre", secondary=game_genres, back_populates="games")
    developers = relationship("Developer", secondary=game_developers, back_populates="games")
    publishers = relationship("Publisher", secondary=game_publishers, back_populates="games")
    platforms = relationship("Platform", secondary=game_platforms, back_populates="games")

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    release_year = Column(Integer)

    genres = relationship("Genre", secondary=movie_genres, back_populates="movies")
    directors = relationship("Director", secondary=movie_directors, back_populates="movies")
    actors = relationship("Actor", secondary=movie_actors, back_populates="movies")

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    games = relationship("Game", secondary=game_genres, back_populates="genres")
    movies = relationship("Movie", secondary=movie_genres, back_populates="genres")

class Developer(Base):
    __tablename__ = "developers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    games = relationship("Game", secondary=game_developers, back_populates="developers")

class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    games = relationship("Game", secondary=game_publishers, back_populates="publishers")

class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    games = relationship("Game", secondary=game_platforms, back_populates="platforms")

class Director(Base):
    __tablename__ = "directors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    movies = relationship("Movie", secondary=movie_directors, back_populates="directors")

class Actor(Base):
    __tablename__ = "actors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    movies = relationship("Movie", secondary=movie_actors, back_populates="actors")

class GenreMapping(Base):
    __tablename__ = "genre_mapping"
    id = Column(Integer, primary_key=True)
    raw_genre = Column(String)
    source = Column(String)  # 'steam' or 'imdb'
    mapped_genre = Column(String)  # canonical genre name