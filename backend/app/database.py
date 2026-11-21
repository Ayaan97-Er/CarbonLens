from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Database connection arguments (connect_args only for SQLite)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # Timeout set to 30s to prevent 'database is locked' errors during concurrent multi-user transactions
    connect_args = {"check_same_thread": False, "timeout": 30.0}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to yield database session per request.
    Ensures session is always cleanly closed even on exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
