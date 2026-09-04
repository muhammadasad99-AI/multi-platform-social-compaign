"""
Database setup. Defaults to SQLite for zero-config local dev,
but works unchanged against Postgres if DATABASE_URL is set to one.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./social_campaigns.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models here so they're registered on Base before create_all
    from app.models import campaign, social_post, idempotency_record, platform_token  # noqa: F401
    Base.metadata.create_all(bind=engine)