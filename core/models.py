from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# === Association Tables ===

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

alias_genres = Table(
    "alias_genres", Base.metadata,
    Column("alias_id", ForeignKey("genre_alias.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True)
)

# === Core Tables ===

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    release_year = Column(Integer)
    is_adult = Column(Boolean)
    is_multiplayer = Column(Boolean)
    is_tv_format = Column(Boolean)

    genres = relationship("Genre", secondary=game_genres, backref="games")
    developers = relationship("Developer", secondary=game_developers, backref="games")
    publishers = relationship("Publisher", secondary=game_publishers, backref="games")
    platforms = relationship("Platform", secondary=game_platforms, backref="games")
    recommendations = relationship("Recommendation", back_populates="game")


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    release_year = Column(Integer)
    is_adult = Column(Boolean)
    is_multiplayer = Column(Boolean)
    is_tv_format = Column(Boolean)

    genres = relationship("Genre", secondary=movie_genres, backref="movies")
    directors = relationship("Director", secondary=movie_directors, backref="movies")
    actors = relationship("Actor", secondary=movie_actors, backref="movies")
    recommendations = relationship("Recommendation", back_populates="movie")


class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class GenreAlias(Base):
    __tablename__ = "genre_alias"
    id = Column(Integer, primary_key=True)
    alias = Column(String)
    source = Column(String)
    genres = relationship("Genre", secondary=alias_genres, backref="aliases")


class Recommendation(Base):
    __tablename__ = "recommendations"
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), primary_key=True)
    score = Column(Float, index=True)

    game = relationship("Game", back_populates="recommendations")
    movie = relationship("Movie", back_populates="recommendations")

    __table_args__ = (UniqueConstraint("game_id", "movie_id", name="uq_game_movie"),)


# === Supporting Entities ===

class Developer(Base):
    __tablename__ = "developers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Director(Base):
    __tablename__ = "directors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Actor(Base):
    __tablename__ = "actors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
