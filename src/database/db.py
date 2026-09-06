from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_DSN = os.getenv("DATABASE_DSN")
"""
The engine manages the connection to the database and handles query execution.
"""
engine = create_engine(DATABASE_DSN)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()