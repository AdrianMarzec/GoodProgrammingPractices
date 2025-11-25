# tests.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Movies, Links, Ratings, Tags
from crud import app, get_db


# --------------------------------------------------------------
# 1) Baza testowa SQLite in-memory
# --------------------------------------------------------------

TEST_DB = "sqlite:///:memory:"

engine_test = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)


# --------------------------------------------------------------
# 2) Tworzenie tabel raz
# --------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.create_all(engine_test)


# --------------------------------------------------------------
# 3) Nowa sesja na test
# --------------------------------------------------------------

@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------
# 4) TestClient z override get_db
# --------------------------------------------------------------

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# --------------------------------------------------------------
# 5) Fixtury danych
# --------------------------------------------------------------

@pytest.fixture()
def example_movies(db_session):
    m1 = Movies(id=1, title="Matrix", genres="Sci-Fi")
    m2 = Movies(id=2, title="Inception", genres="Sci-Fi|Thriller")
    db_session.add_all([m1, m2])
    db_session.commit()
    return [m1, m2]


@pytest.fixture()
def example_links(db_session, example_movies):
    l1 = Links(id=1, movie_id=1, imdb_id="tt0133093", tmdb_id=603)
    db_session.add(l1)
    db_session.commit()
    return [l1]


@pytest.fixture()
def example_ratings(db_session, example_movies):
    r1 = Ratings(id=1, user_id=10, movie_id=1, rating=4.5, timestamp=100)
    db_session.add(r1)
    db_session.commit()
    return [r1]


@pytest.fixture()
def example_tags(db_session, example_movies):
    t1 = Tags(id=1, user_id=5, movie_id=1, tag="classic", timestamp=200)
    db_session.add(t1)
    db_session.commit()
    return [t1]


# ============================================================
#   TESTY CRUD — MOVIES
# ============================================================

def test_read_movie(client, example_movies):
    res = client.get("/movies/1")
    assert res.status_code == 200
    assert res.json()["title"] == "Matrix"


def test_read_movie_not_found(client):
    res = client.get("/movies/999")
    assert res.status_code == 404


def test_create_movie(client):
    res = client.post("/movies", json={"title": "Interstellar", "genres": "Sci-Fi"})
    assert res.status_code == 200
    assert res.json()["title"] == "Interstellar"


def test_update_movie(client, example_movies):
    res = client.put("/movies/1", json={"title": "Matrix Reloaded"})
    assert res.status_code == 200
    assert res.json()["title"] == "Matrix Reloaded"


def test_delete_movie(client, example_movies):
    res = client.delete("/movies/1")
    assert res.status_code == 200
    res2 = client.get("/movies/1")
    assert res2.status_code == 404


# ============================================================
#   TESTY CRUD — LINKS
# ============================================================

def test_link_post(client, example_movies):
    res = client.post("/links", json={"movie_id": 1, "imdb_id": "tt0000001", "tmdb_id": 99})
    assert res.status_code == 200
    assert res.json()["movie_id"] == 1


def test_link_get(client, example_links):
    res = client.get("/links/1")
    assert res.status_code == 200
    assert res.json()["imdb_id"] == "tt0133093"


def test_link_put(client, example_links):
    res = client.put("/links/1", json={"tmdb_id": 999})
    assert res.status_code == 200
    assert res.json()["tmdb_id"] == 999


def test_link_delete(client, example_links):
    res = client.delete("/links/1")
    assert res.status_code == 200
    res2 = client.get("/links/1")
    assert res2.status_code == 404


# ============================================================
#   TESTY CRUD — RATINGS
# ============================================================

def test_rating_post(client, example_movies):
    res = client.post("/ratings", json={
        "user_id": 100, "movie_id": 1, "rating": 5.0, "timestamp": 111
    })
    assert res.status_code == 200
    assert res.json()["rating"] == 5.0


def test_rating_get(client, example_ratings):
    res = client.get("/ratings/1")
    assert res.status_code == 200
    assert res.json()["user_id"] == 10


def test_rating_put(client, example_ratings):
    res = client.put("/ratings/1", json={"rating": 1.0})
    assert res.status_code == 200
    assert res.json()["rating"] == 1.0


def test_rating_delete(client, example_ratings):
    res = client.delete("/ratings/1")
    assert res.status_code == 200
    res2 = client.get("/ratings/1")
    assert res2.status_code == 404


# ============================================================
#   TESTY CRUD — TAGS
# ============================================================

def test_tag_post(client, example_movies):
    res = client.post("/tags", json={
        "user_id": 50, "movie_id": 1, "tag": "awesome", "timestamp": 999
    })
    assert res.status_code == 200
    assert res.json()["tag"] == "awesome"


def test_tag_get(client, example_tags):
    res = client.get("/tags/1")
    assert res.status_code == 200
    assert res.json()["tag"] == "classic"


def test_tag_put(client, example_tags):
    res = client.put("/tags/1", json={"tag": "updated"})
    assert res.status_code == 200
    assert res.json()["tag"] == "updated"


def test_tag_delete(client, example_tags):
    res = client.delete("/tags/1")
    assert res.status_code == 200
    res2 = client.get("/tags/1")
    assert res2.status_code == 404
