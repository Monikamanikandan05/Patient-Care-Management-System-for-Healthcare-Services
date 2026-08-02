from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    """Create all tables (including new pharmacy tables) if they don't exist."""
    import models.models  # noqa: F401 — ensures all models are registered
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

from contextlib import contextmanager

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

