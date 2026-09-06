from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_DSN = os.getenv("DATABASE_DSN")
"""
The engine manages the connection to the database and handles query execution.
"""
if not DATABASE_DSN:
    raise RuntimeError("Set DATABASE_DSN in your environment or .env file")
engine = create_engine(DATABASE_DSN, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
