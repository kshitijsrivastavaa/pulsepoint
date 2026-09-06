import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Uses Postgres in production (Render sets DATABASE_URL env var automatically).
# Falls back to a local SQLite file so you can run + test everything without
# setting up Postgres first.
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./pulsepoint.db"

# Render's Postgres URLs sometimes start with "postgres://" but SQLAlchemy
# needs "postgresql://" - this patches that automatically.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
