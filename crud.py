from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Base, Movies, Links, Ratings, Tags
from database import get_db

app = FastAPI()

@app.post("/movies/")
def create_movie(movie: Movies, db: Session = Depends(get_db)):
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie

@app.get("/movies/{movie_id}")
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, updated_movie: Movies, db: Session = Depends(get_db)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    for key, value in updated_movie.__dict__.items():
        if key != "_sa_instance_state":
            setattr(movie, key, value)
    db.commit()
    db.refresh(movie)
    return movie

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(movie)
    db.commit()
    return {"ok": True}


