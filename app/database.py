import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings
import os

if os.getenv("DEBUG", "false").lower() == "true":
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine = create_engine(settings.DATABASE_URL, echo=False)

# autoflush=False: we control flushes manually (e.g. db.flush() before
# reading auto-generated IDs) to avoid premature DB round-trips.
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
