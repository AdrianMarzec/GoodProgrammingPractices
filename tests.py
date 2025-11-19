from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Movies
from crud import app, get_db  # Twój FastAPI app i get_db dependency

# --- TestClient ---
client = TestClient(app)

# --- Fixture do bazy danych ---
@pytest.fixture(scope='function')
def setup_database():
    engine = create_engine("sqlite:///:memory:")  # in-memory DB
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

# --- Fixture do danych testowych ---
@pytest.fixture(scope='function')
def setup_movies(setup_database):
    db = setup_database

    movie1 = Movies(id=1, title="The Matrix", genres="Action|Sci-Fi")
    movie2 = Movies(id=2, title="Inception", genres="Action|Thriller|Sci-Fi")
    db.add_all([movie1, movie2])
    db.commit()

    # nadpisujemy dependency FastAPI
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db

    yield db

# --- Testy CRUD ---
def test_read_movie(setup_movies):
    response = client.get("/movies/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "The Matrix"

def test_read_movie_not_found(setup_movies):
    response = client.get("/movies/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Movie not found"

def test_create_movie(setup_movies):
    new_movie = {"id": 3, "title": "Interstellar", "genres": "Sci-Fi|Drama"}
    response = client.post("/movies/", json=new_movie)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 3
    assert data["title"] == "Interstellar"

def test_update_movie(setup_movies):
    updated_movie = {"id": 2, "title": "Inception Updated", "genres": "Action|Thriller|Sci-Fi"}
    response = client.put("/movies/2", json=updated_movie)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Inception Updated"

def test_delete_movie(setup_movies):
    response = client.delete("/movies/1")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    # movie 1 should be gone
    response = client.get("/movies/1")
    assert response.status_code == 404
