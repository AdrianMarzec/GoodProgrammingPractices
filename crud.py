# crud.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Movies, Tags, Links, Ratings
from sqlalchemy import create_engine

# Silnik SQLite
engine = create_engine("sqlite:///movies.db", echo=True)

# SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tworzymy tabele
Base.metadata.create_all(engine)

# FastAPI
app = FastAPI()


# -------------------------
# Dependency get_db
# -------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    obj = Movies(title=movie.title, genres=movie.genres)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/movies/{movie_id}")
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, update: MovieUpdate, db: Session = Depends(get_db)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    if update.title is not None:
        movie.title = update.title
    if update.genres is not None:
        movie.genres = update.genres

    db.commit()
    db.refresh(movie)
    return movie


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    db.delete(movie)
    db.commit()
    return {"msg": "Movie deleted"}


# -----------------------------------------------------
# ---------------------- LINKS ------------------------
# -----------------------------------------------------

@app.post("/links")
def create_link(data: LinkCreate, db: Session = Depends(get_db)):
    obj = Links(
        movie_id=data.movie_id,
        imdb_id=data.imdb_id,
        tmdb_id=data.tmdb_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/links/{link_id}")
def read_link(link_id: int, db: Session = Depends(get_db)):
    obj = db.get(Links, link_id)
    if not obj:
        raise HTTPException(404, "Link not found")
    return obj


@app.put("/links/{link_id}")
def update_link(link_id: int, update: LinkUpdate, db: Session = Depends(get_db)):
    obj = db.get(Links, link_id)
    if not obj:
        raise HTTPException(404, "Link not found")

    if update.imdb_id is not None:
        obj.imdb_id = update.imdb_id
    if update.tmdb_id is not None:
        obj.tmdb_id = update.tmdb_id

    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/links/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    obj = db.get(Links, link_id)
    if not obj:
        raise HTTPException(404, "Link not found")
    db.delete(obj)
    db.commit()
    return {"msg": "Link deleted"}


# -----------------------------------------------------
# ---------------------- RATINGS ----------------------
# -----------------------------------------------------

@app.post("/ratings")
def create_rating(data: RatingCreate, db: Session = Depends(get_db)):
    obj = Ratings(
        user_id=data.user_id,
        movie_id=data.movie_id,
        rating=data.rating,
        timestamp=data.timestamp
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/ratings/{rating_id}")
def read_rating(rating_id: int, db: Session = Depends(get_db)):
    obj = db.get(Ratings, rating_id)
    if not obj:
        raise HTTPException(404, "Rating not found")
    return obj


@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, update: RatingUpdate, db: Session = Depends(get_db)):
    obj = db.get(Ratings, rating_id)
    if not obj:
        raise HTTPException(404, "Rating not found")

    if update.user_id is not None:
        obj.user_id = update.user_id
    if update.rating is not None:
        obj.rating = update.rating
    if update.timestamp is not None:
        obj.timestamp = update.timestamp

    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/ratings/{rating_id}")
def delete_rating(rating_id: int, db: Session = Depends(get_db)):
    obj = db.get(Ratings, rating_id)
    if not obj:
        raise HTTPException(404, "Rating not found")
    db.delete(obj)
    db.commit()
    return {"msg": "Rating deleted"}


# -----------------------------------------------------
# ------------------------ TAGS -----------------------
# -----------------------------------------------------

@app.post("/tags")
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    obj = Tags(
        user_id=data.user_id,
        movie_id=data.movie_id,
        tag=data.tag,
        timestamp=data.timestamp
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/tags/{tag_id}")
def read_tag(tag_id: int, db: Session = Depends(get_db)):
    obj = db.get(Tags, tag_id)
    if not obj:
        raise HTTPException(404, "Tag not found")
    return obj


@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, update: TagUpdate, db: Session = Depends(get_db)):
    obj = db.get(Tags, tag_id)
    if not obj:
        raise HTTPException(404, "Tag not found")

    if update.tag is not None:
        obj.tag = update.tag
    if update.timestamp is not None:
        obj.timestamp = update.timestamp

    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    obj = db.get(Tags, tag_id)
    if not obj:
        raise HTTPException(404, "Tag not found")
    db.delete(obj)
    db.commit()
    return {"msg": "Tag deleted"}
