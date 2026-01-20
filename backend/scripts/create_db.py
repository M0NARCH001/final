# backend/scripts/create_db.py
from sqlalchemy import create_engine
from app.models import Base
import os

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///nutri.db")

def main():
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
    Base.metadata.create_all(bind=engine)
    print("Database created at", DB_URL)

if __name__ == "__main__":
    main()