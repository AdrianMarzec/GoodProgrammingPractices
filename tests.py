import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Tags, Movies, Ratings, Links
from main import app, get_db


# --------------------------------------------------------------
# 1) Baza testowa SQLite in-memory
# --------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# --------------------------------------------------------------
# 2) Tworzenie tabel raz na całą sesję testów
# --------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """Tworzy wszystkie tabele w pamięci."""
    Base.metadata.create_all(engine_test)


# --------------------------------------------------------------
# 3) Oddzielna sesja DB na każdy test
# --------------------------------------------------------------

@pytest.fixture()
def db_session():
    """Nowa czysta sesja DB dla każdego testu."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------
# 4) TestClient z podmienionym get_db
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
# 5) Dane testowe – filmy w bazie
# --------------------------------------------------------------

@pytest.fixture()
def example_movies(db_session):
    movie1 = Movies(id=1, title="Matrix", genres="Action|Sci-Fi")
    movie2 = Movies(id=2, title="Inception", genres="Thriller|Sci-Fi")

    db_session.add_all([movie1, movie2])
    db_session.commit()

    return [movie1, movie2]


# --------------------------------------------------------------
# 6) TESTY CRUD
# --------------------------------------------------------------

def test_read_movie(client, example_movies):
    response = client.get("/movies/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["title"] == "Matrix"


def test_read_movie_not_found(client):
    response = client.get("/movies/12345")
    assert response.status_code == 404


def test_create_movie(client):
    payload = {"title": "Interstellar", "genres": "Sci-Fi"}
    response = client.post("/movies", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Interstellar"


def test_update_movie(client, example_movies):
    payload = {"title": "Matrix Reloaded"}
    response = client.put("/movies/1", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Matrix Reloaded"


def test_delete_movie(client, example_movies):
    response = client.delete("/movies/1")
    assert response.status_code == 200

    # item should be gone
    response2 = client.get("/movies/1")
    assert response2.status_code == 404




# ============================================================
#   4) TESTY CRUD — LINKS
# ============================================================

def test_link_post(client, example_movies):
    payload = {"movie_id": 1, "imdb_id": "tt9999999", "tmdb_id": 123}
    res = client.post("/links", json=payload)

    assert res.status_code == 200
    assert res.json()["movie_id"] == 1


def test_link_get(client, example_links):
    res = client.get("/links/1")

    assert res.status_code == 200
    assert res.json()["imdb_id"] == "tt0133093"


def test_link_put(client, example_links):
    res = client.put("/links/1", json={"tmdb_id": 777})

    assert res.status_code == 200
    assert res.json()["tmdb_id"] == 777


def test_link_delete(client, example_links):
    res = client.delete("/links/1")
    assert res.status_code == 200

    res2 = client.get("/links/1")
    assert res2.status_code == 404


# ============================================================
#   5) TESTY CRUD — RATINGS
# ============================================================

def test_rating_post(client, example_movies):
    payload = {
        "user_id": 99,
        "movie_id": 1,
        "rating": 3.5,
        "timestamp": 455
    }
    res = client.post("/ratings", json=payload)

    assert res.status_code == 200
    assert res.json()["rating"] == 3.5


def test_rating_get(client, example_ratings):
    res = client.get("/ratings/1")

    assert res.status_code == 200
    assert res.json()["user_id"] == 10


def test_rating_put(client, example_ratings):
    res = client.put("/ratings/1", json={"rating": 2.0})

    assert res.status_code == 200
    assert res.json()["rating"] == 2.0


def test_rating_delete(client, example_ratings):
    res = client.delete("/ratings/1")
    assert res.status_code == 200

    res2 = client.get("/ratings/1")
    assert res2.status_code == 404


# ============================================================
#   6) TESTY CRUD — TAGS
# ============================================================

def test_tag_post(client, example_movies):
    payload = {
        "user_id": 7,
        "movie_id": 1,
        "tag": "great",
        "timestamp": 999
    }
    res = client.post("/tags", json=payload)

    assert res.status_code == 200
    assert res.json()["tag"] == "great"


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
    