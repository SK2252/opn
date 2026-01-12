from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from app.models.base import Base
from app.logger import logger

load_dotenv()

# =====================
# DATABASE CONNECTION
# =====================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL is missing. Please set it in your .env file.")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database tables."""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully.")


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
