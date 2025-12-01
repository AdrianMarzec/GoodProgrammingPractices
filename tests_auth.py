import pytest
from fastapi.testclient import TestClient
from crud import app
from models import Base, Users
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt
from database import get_db

# in-memory SQLite
TEST_DB = "sqlite:///:memory:"
engine_test = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)

# override get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def prepare_db():
    Base.metadata.create_all(engine_test)
    # dodajemy admina
    db = TestingSessionLocal()
    hashed_pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
    admin = Users(username="admin", hashed_password=hashed_pw, roles="ROLE_ADMIN")
    db.add(admin)
    db.commit()
    db.close()

def test_login_success():
    res = client.post("/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_fail():
    res = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401

def test_user_details_success():
    res = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = res.json()["access_token"]
    res2 = client.get("/user_details", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert res2.json()["username"] == "admin"

def test_user_details_no_token():
    res = client.get("/user_details")
    assert res.status_code == 401

def test_create_user_as_admin():
    res = client.post("/login", json={"username": "admin", "password": "admin123"})
    token = res.json()["access_token"]
    res2 = client.post("/users",
                        json={"username": "testuser", "password": "pass", "roles": "USER"},
                        headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert res2.json()["username"] == "testuser"

def test_create_user_as_non_admin():
    # dodajemy zwykłego usera
    db = TestingSessionLocal()
    hashed_pw = bcrypt.hashpw(b"user123", bcrypt.gensalt())
    user = Users(username="user", hashed_password=hashed_pw, roles="USER")
    db.add(user)
    db.commit()
    db.close()

    # logujemy się jako zwykły user
    res = client.post("/login", json={"username": "user", "password": "user123"})
    token = res.json()["access_token"]
    res2 = client.post("/users",
                        json={"username": "failuser", "password": "pass", "roles": "USER"},
                        headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403
