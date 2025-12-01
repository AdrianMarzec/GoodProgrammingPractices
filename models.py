from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class Movies(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)  # movieId
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    genres: Mapped[str] = mapped_column(String(255), nullable=False)
    ratings: Mapped[list["Ratings"]] = relationship(back_populates="movie")
    tags: Mapped[list["Tags"]] = relationship(back_populates="movie")
    links: Mapped["Links"] = relationship(
        back_populates="movie",
        uselist=False  # links.csv ma 1 rekord na film
    )

    def __repr__(self) -> str:
        return f"Movie(id={self.id!r}, title={self.title!r}, genres={self.genres!r})"


class Links(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    imdb_id: Mapped[str] = mapped_column(String(20))
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=True)

    movie: Mapped["Movies"] = relationship(back_populates="links")

    def __repr__(self) -> str:
        return (
            f"Links(id={self.id!r}, movie_id={self.movie_id!r}, "
            f"imdb_id={self.imdb_id!r}, tmdb_id={self.tmdb_id!r})"
        )



class Ratings(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column()
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))

    rating: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[int] = mapped_column(Integer)

    movie: Mapped["Movies"] = relationship(back_populates="ratings")

    def __repr__(self) -> str:
        return (
            f"Ratings(id={self.id!r}, user_id={self.user_id!r}, "
            f"movie_id={self.movie_id!r}, rating={self.rating!r}, "
            f"timestamp={self.timestamp!r})"
        )


class Tags(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column()
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))

    tag: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[int] = mapped_column(Integer)

    movie: Mapped["Movies"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return (
            f"Tags(id={self.id!r}, user_id={self.user_id!r}, movie_id={self.movie_id!r}, "
            f"tag={self.tag!r}, timestamp={self.timestamp!r})"
        )


from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# silnik SQLite (plik baza będzie w katalogu projektu)
engine = create_engine("sqlite:///movies.db", echo=True)

# wszystkie tabele zdefiniowane w modelach
Base.metadata.create_all(engine)

import csv

def load_movies(session, filename="database/movies.csv"):
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie = Movies(
                id=int(row["movieId"]),
                title=row["title"],
                genres=row["genres"]
            )
            session.add(movie)
    session.commit()

def load_links(session, filename="database/links.csv"):
    movie_ids = {m.id for m in session.query(Movies.id).all()}

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = int(row["movieId"])
            if mid not in movie_ids:
                print(f"Film {mid} nie istnieje w movies. Pomijam rekord links.")
                continue
            link = Links(
                movie_id=mid,
                imdb_id=row.get("imdbId", None),
                tmdb_id=int(row["tmdbId"]) if row.get("tmdbId") else None
            )
            session.add(link)
    session.commit()


def load_ratings(session, filename="database/ratings.csv"):
    # Pobieramy wszystkie ID filmów
    movie_ids = {m.id for m in session.query(Movies.id).all()}

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = int(row["movieId"])
            if mid not in movie_ids:
                print(f"Film {mid} nie istnieje w movies. Pomijam rekord.")
                continue
            rating = Ratings(
                user_id=int(row["userId"]),
                movie_id=mid,
                rating=float(row["rating"]),
                timestamp=int(row["timestamp"])
            )
            session.add(rating)
    session.commit()


def load_tags(session, filename="database/tags.csv"):
    movie_ids = {m.id for m in session.query(Movies.id).all()}

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = int(row["movieId"])
            if mid not in movie_ids:
                print(f"Film {mid} nie istnieje w movies. Pomijam rekord tags.")
                continue
            tag = Tags(
                user_id=int(row["userId"]),
                movie_id=mid,
                tag=row["tag"],
                timestamp=int(row["timestamp"])
            )
            session.add(tag)
    session.commit()


"""# sesja i wczytanie danych
with Session(engine) as session:
    load_movies(session)
    load_links(session)
    load_ratings(session)
    load_tags(session)"""

with Session(engine) as session:
    # Wszystkie filmy
    movies = session.query(Movies).all()
    for x in movies[:5]:
        print(x)

    # Film o konkretnym ID
    movie = session.get(Movies, 1)
    print(25*"=")
    print(movie)
    print(25*"=")

    # Wszystkie oceny dla filmu
    ratings = session.query(Ratings).filter_by(movie_id=1).all()
    for x in ratings[:10]:
        print(x)



class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[str] = mapped_column(String(255), default="USER")  # np. ROLE_ADMIN,ROLE_USER

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, roles={self.roles!r})"
