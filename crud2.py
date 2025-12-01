# crud.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session, sessionmaker, relationship
from sqlalchemy import create_engine, String, Integer, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

# -----------------------------
# DATABASE SETUP
# -----------------------------
DATABASE_URL = "sqlite:///movies.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# MODELS
# -----------------------------
class Base(DeclarativeBase):
    pass

class Movies(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    genres: Mapped[str] = mapped_column(String(255), nullable=False)
    ratings: Mapped[list["Ratings"]] = relationship(back_populates="movie")
    tags: Mapped[list["Tags"]] = relationship(back_populates="movie")
    links: Mapped["Links"] = relationship(back_populates="movie", uselist=False)

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
        return f"Links(id={self.id!r}, movie_id={self.movie_id!r}, imdb_id={self.imdb_id!r}, tmdb_id={self.tmdb_id!r})"

class Ratings(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    rating: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[int] = mapped_column(Integer)

    movie: Mapped["Movies"] = relationship(back_populates="ratings")

    def __repr__(self) -> str:
        return f"Ratings(id={self.id!r}, user_id={self.user_id!r}, movie_id={self.movie_id!r}, rating={self.rating!r}, timestamp={self.timestamp!r})"

class Tags(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    tag: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[int] = mapped_column(Integer)

    movie: Mapped["Movies"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return f"Tags(id={self.id!r}, user_id={self.user_id!r}, movie_id={self.movie_id!r}, tag={self.tag!r}, timestamp={self.timestamp!r})"

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[str] = mapped_column(String(255), default="USER")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, roles={self.roles!r})"

Base.metadata.create_all(engine)

# -----------------------------
# JWT SETUP
# -----------------------------
SECRET_KEY = "super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    to_encode.update({"iat": now})
    if expires_delta:
        to_encode.update({"exp": now + expires_delta})
    else:
        to_encode.update({"exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: str = payload.get("roles")
        if username is None or roles is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Users).filter_by(username=username).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(user: Users = Depends(get_current_user)):
    if "ROLE_ADMIN" not in user.roles.split(","):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# -----------------------------
# Pydantic Schemas
# -----------------------------
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
class LoginData(BaseModel):
    username: str
    password: str
class UserCreate(BaseModel):
    username: str
    password: str
    roles: str = "USER"
class Token(BaseModel):
    access_token: str
    token_type: str

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI()

# -----------------------------
# LOGIN & USER ENDPOINTS
# -----------------------------
@app.post("/login", response_model=Token)
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(Users).filter_by(username=data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.username, "roles": user.roles})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db), _: Users = Depends(require_admin)):
    existing = db.query(Users).filter_by(username=user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    db_user = Users(username=user.username, hashed_password=hashed_pw, roles=user.roles)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"username": db_user.username, "roles": db_user.roles}

@app.get("/user_details")
def user_details(current_user: Users = Depends(get_current_user)):
    return {"username": current_user.username, "roles": current_user.roles}

# -----------------------------
# MOVIES CRUD
# -----------------------------
@app.post("/movies")
def create_movie(movie: MovieCreate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = Movies(title=movie.title, genres=movie.genres)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/movies/{movie_id}")
def read_movie(movie_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, update: MovieUpdate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
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
def delete_movie(movie_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    movie = db.get(Movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    db.delete(movie)
    db.commit()
    return {"msg": "Movie deleted"}

# -----------------------------
# LINKS CRUD
# -----------------------------
@app.post("/links")
def create_link(data: LinkCreate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = Links(movie_id=data.movie_id, imdb_id=data.imdb_id, tmdb_id=data.tmdb_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/links/{link_id}")
def read_link(link_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = db.get(Links, link_id)
    if not obj:
        raise HTTPException(404, "Link not found")
    return obj

@app.put("/links/{link_id}")
def update_link(link_id: int, update: LinkUpdate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
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
def delete_link(link_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = db.get(Links, link_id)
    if not obj:
        raise HTTPException(404, "Link not found")
    db.delete(obj)
    db.commit()
    return {"msg": "Link deleted"}

# -----------------------------
# RATINGS CRUD
# -----------------------------
@app.post("/ratings")
def create_rating(data: RatingCreate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = Ratings(user_id=data.user_id, movie_id=data.movie_id, rating=data.rating, timestamp=data.timestamp)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/ratings/{rating_id}")
def read_rating(rating_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = db.get(Ratings, rating_id)
    if not obj:
        raise HTTPException(404, "Rating not found")
    return obj

@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, update: RatingUpdate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
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
def delete_rating(rating_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = db.get(Ratings, rating_id)
    if not obj:
        raise HTTPException(404, "Rating not found")
    db.delete(obj)
    db.commit()
    return {"msg": "Rating deleted"}

# -----------------------------
# TAGS CRUD
# -----------------------------
@app.post("/tags")
def create_tag(data: TagCreate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = Tags(user_id=data.user_id, movie_id=data.movie_id, tag=data.tag, timestamp=data.timestamp)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/tags/{tag_id}")
def read_tag(tag_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = db.get(Tags, tag_id)
    if not obj:
        raise HTTPException(404, "Tag not found")
    return obj

@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, update: TagUpdate, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
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
def delete_tag(tag_id: int, db: Session = Depends(get_db), _: Users = Depends(get_current_user)):
    obj = db.get(Tags, tag_id)
    if not obj:
        raise HTTPException(404, "Tag not found")
    db.delete(obj)
    db.commit()
    return {"msg": "Tag deleted"}
