import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv(override=True)

DATABASE_URL = os.getenv("DB_CONNECTION_STRING")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#--- inside FastAPI application use
def get_database_session() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#--- outside FastAPI application
def get_session():
    return SessionLocal()
