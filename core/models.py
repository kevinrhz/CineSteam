from sqlalchemy import Column, Integer, String, ForeignKey, Table, Boolean, Float
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

# --- Core Tables ---

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    release_year = Column(Integer)
    is_adult = Column(Boolean, default=False)
    is_multiplayer = Column(Boolean, default=False)
    is_tv_format = Column(Boolean, default=False)

    genres = relationship("Genre", secondary=game_genres, backref="games")
    developers = relationship("Developer", secondary=game_developers, backref="games")
    publishers = relationship("Publisher", secondary=game_publishers, backref="games")
    platforms = relationship("Platform", secondary=game_platforms, backref="games")


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    release_year = Column(Integer)
    is_adult = Column(Boolean, default=False)
    is_multiplayer = Column(Boolean, default=False)
    is_tv_format = Column(Boolean, default=False)

    genres = relationship("Genre", secondary=movie_genres, backref="movies")
    directors = relationship("Director", secondary=movie_directors, backref="movies")
    actors = relationship("Actor", secondary=movie_actors, backref="movies")


class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)


class GenreAlias(Base):
    __tablename__ = "genre_alias"
    id = Column(Integer, primary_key=True)
    alias = Column(String, index=True)
    source = Column(String, nullable=False)

    canonical_genres = relationship("AliasGenre", back_populates="alias")


class AliasGenre(Base):
    __tablename__ = "alias_genres"
    alias_id = Column(Integer, ForeignKey("genre_alias.id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genres.id"), primary_key=True)

    alias = relationship("GenreAlias", back_populates="canonical_genres")
    genre = relationship("Genre")


class Developer(Base):
    __tablename__ = "developers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)


class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)


class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)


class Director(Base):
    __tablename__ = "directors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)


class Actor(Base):
    __tablename__ = "actors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)


class Recommendation(Base):
    __tablename__ = "recommendations"
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), primary_key=True)
    score = Column(Float, nullable=False)
