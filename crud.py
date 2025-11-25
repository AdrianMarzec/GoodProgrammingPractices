from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from models import Base, Movies, Tags, Links, Ratings

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# silnik SQLite (plik baza będzie w katalogu projektu)
engine = create_engine("sqlite:///movies.db", echo=True)

# wszystkie tabele zdefiniowane w modelach
# Base.metadata.create_all(engine)

app = FastAPI()

# -------------------------
# Schemy Pydantic
# -------------------------

class MovieCreate(BaseModel):
    title: str
    genres: str

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    genres: Optional[str] = None


class LinkCreate(BaseModel):
    movie_id: int
    imdb_id: str
    tmdb_id: Optional[int]

class LinkUpdate(BaseModel):
    imdb_id: Optional[str] = None
    tmdb_id: Optional[int] = None


class RatingCreate(BaseModel):
    user_id: int
    movie_id: int
    rating: float
    timestamp: int

class RatingUpdate(BaseModel):
    user_id: Optional[int] = None
    rating: Optional[float] = None
    timestamp: Optional[int] = None


class TagCreate(BaseModel):
    user_id: int
    movie_id: int
    tag: str
    timestamp: int

class TagUpdate(BaseModel):
    tag: Optional[str] = None
    timestamp: Optional[int] = None


# -----------------------------------------------------
# ---------------------- MOVIES -----------------------
# -----------------------------------------------------

@app.post("/movies")
def create_movie(movie: MovieCreate):
    with Session(engine) as session:
        obj = Movies(title=movie.title, genres=movie.genres)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj


@app.get("/movies/{movie_id}")
def read_movie(movie_id: int):
    with Session(engine) as session:
        movie = session.get(Movies, movie_id)
        if not movie:
            raise HTTPException(404, "Movie not found")
        return movie


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, update: MovieUpdate):
    with Session(engine) as session:
        movie = session.get(Movies, movie_id)
        if not movie:
            raise HTTPException(404, "Movie not found")

        if update.title is not None:
            movie.title = update.title
        if update.genres is not None:
            movie.genres = update.genres

        session.commit()
        return movie


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    with Session(engine) as session:
        movie = session.get(Movies, movie_id)
        if not movie:
            raise HTTPException(404, "Movie not found")
        session.delete(movie)
        session.commit()
        return {"msg": "Movie deleted"}


# -----------------------------------------------------
# ---------------------- LINKS ------------------------
# -----------------------------------------------------

@app.post("/links")
def create_link(data: LinkCreate):
    with Session(engine) as session:
        obj = Links(
            movie_id=data.movie_id,
            imdb_id=data.imdb_id,
            tmdb_id=data.tmdb_id
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj


@app.get("/links/{link_id}")
def read_link(link_id: int):
    with Session(engine) as session:
        obj = session.get(Links, link_id)
        if not obj:
            raise HTTPException(404, "Link not found")
        return obj


@app.put("/links/{link_id}")
def update_link(link_id: int, update: LinkUpdate):
    with Session(engine) as session:
        obj = session.get(Links, link_id)
        if not obj:
            raise HTTPException(404, "Link not found")

        if update.imdb_id is not None:
            obj.imdb_id = update.imdb_id
        if update.tmdb_id is not None:
            obj.tmdb_id = update.tmdb_id

        session.commit()
        return obj


@app.delete("/links/{link_id}")
def delete_link(link_id: int):
    with Session(engine) as session:
        obj = session.get(Links, link_id)
        if not obj:
            raise HTTPException(404, "Link not found")
        session.delete(obj)
        session.commit()
        return {"msg": "Link deleted"}


# -----------------------------------------------------
# ---------------------- RATINGS ----------------------
# -----------------------------------------------------

@app.post("/ratings")
def create_rating(data: RatingCreate):
    with Session(engine) as session:
        obj = Ratings(
            user_id=data.user_id,
            movie_id=data.movie_id,
            rating=data.rating,
            timestamp=data.timestamp
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj


@app.get("/ratings/{rating_id}")
def read_rating(rating_id: int):
    with Session(engine) as session:
        obj = session.get(Ratings, rating_id)
        if not obj:
            raise HTTPException(404, "Rating not found")
        return obj


@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, update: RatingUpdate):
    with Session(engine) as session:
        obj = session.get(Ratings, rating_id)
        if not obj:
            raise HTTPException(404, "Rating not found")

        if update.user_id is not None:
            obj.user_id = update.user_id
        if update.rating is not None:
            obj.rating = update.rating
        if update.timestamp is not None:
            obj.timestamp = update.timestamp

        session.commit()
        return obj


@app.delete("/ratings/{rating_id}")
def delete_rating(rating_id: int):
    with Session(engine) as session:
        obj = session.get(Ratings, rating_id)
        if not obj:
            raise HTTPException(404, "Rating not found")
        session.delete(obj)
        session.commit()
        return {"msg": "Rating deleted"}


# -----------------------------------------------------
# ------------------------ TAGS -----------------------
# -----------------------------------------------------

@app.post("/tags")
def create_tag(data: TagCreate):
    with Session(engine) as session:
        obj = Tags(
            user_id=data.user_id,
            movie_id=data.movie_id,
            tag=data.tag,
            timestamp=data.timestamp
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj


@app.get("/tags/{tag_id}")
def read_tag(tag_id: int):
    with Session(engine) as session:
        obj = session.get(Tags, tag_id)
        if not obj:
            raise HTTPException(404, "Tag not found")
        return obj


@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, update: TagUpdate):
    with Session(engine) as session:
        obj = session.get(Tags, tag_id)
        if not obj:
            raise HTTPException(404, "Tag not found")

        if update.tag is not None:
            obj.tag = update.tag
        if update.timestamp is not None:
            obj.timestamp = update.timestamp

        session.commit()
        return obj


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int):
    with Session(engine) as session:
        obj = session.get(Tags, tag_id)
        if not obj:
            raise HTTPException(404, "Tag not found")
        session.delete(obj)
        session.commit()
        return {"msg": "Tag deleted"}
