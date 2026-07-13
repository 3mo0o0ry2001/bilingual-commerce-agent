"""
Database engine and session configuration.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://perfume_admin:dev_password_change_me@localhost:5432/perfume_agent",
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and ensures it's closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()