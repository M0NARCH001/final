from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Original DB file in the project
DB_FILE = os.path.join(BASE_DIR, "..", "..", "nutri_indian.db")
DB_FILE = os.path.abspath(DB_FILE)

# In Vercel, we can't write to the project directory.
# We must copy the DB to /tmp to make it writable (ephemeral).
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    TMP_DB = "/tmp/nutri_indian.db"
    if not os.path.exists(TMP_DB):
        if os.path.exists(DB_FILE):
             shutil.copy2(DB_FILE, TMP_DB)
    DATABASE_URL = f"sqlite:///{TMP_DB}"

# Railway with persistent volume
elif os.environ.get("RAILWAY_VOLUME_MOUNT_PATH"):
    RAILWAY_DB = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH"), "nutri_indian.db")
    # Copy initial DB to volume if not exists
    if not os.path.exists(RAILWAY_DB) and os.path.exists(DB_FILE):
        shutil.copy2(DB_FILE, RAILWAY_DB)
    DATABASE_URL = f"sqlite:///{RAILWAY_DB}"

# PythonAnywhere - uses project directory (persistent by default)
elif os.environ.get("PYTHONANYWHERE_SITE"):
    # DB_FILE already points to project directory, which is persistent
    DATABASE_URL = f"sqlite:///{DB_FILE}"

else:
    # Local development or custom DATABASE_URL
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_FILE}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
