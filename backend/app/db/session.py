from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create engine for PostgreSQL
engine = create_engine(settings.get_database_url(), pool_pre_ping=True)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting DB session
    
    Yields:
        Generator[Session, None, None]: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()