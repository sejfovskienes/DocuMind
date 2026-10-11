"""SQLAlchemy engine, sessions, and declarative base."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.base.config import DatabaseConfig

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
engine: Engine | None = None


def get_engine() -> Engine:
    """Create the database engine on first use."""
    global engine
    if engine is None:
        if not DatabaseConfig.DATABASE_URL:
            raise RuntimeError("DB_CONNECTION_STRING must be set to use the database.")
        engine = create_engine(DatabaseConfig.DATABASE_URL, pool_pre_ping=True)
        SessionLocal.configure(bind=engine)
    return engine


def initialize_database() -> None:
    """Create tables for the application during explicit startup."""
    get_engine()
    Base.metadata.create_all(bind=engine)


def get_database_session() -> Generator:
    """Yield a request-scoped database session."""
    db = SessionLocal(bind=get_engine())
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Return a database session for worker or script use."""
    return SessionLocal(bind=get_engine())
