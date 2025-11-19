from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base

# Łączenie z plikiem movies.db
SQLALCHEMY_DATABASE_URL = "sqlite:///movies.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Sesja SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Funkcja dependency do FastAPI
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
