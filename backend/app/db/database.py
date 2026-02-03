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

else:
    # Local development or custom DATABASE_URL
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_FILE}")

def _check_and_fix_schema(db_path):
    """
    Auto-migration to ensure food_items has INTEGER PRIMARY KEY.
    Required for SQLite autoincrement to work correctly.
    """
    if not os.path.exists(db_path):
        return

    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check if food_id is PK
        c.execute("PRAGMA table_info(food_items)")
        cols = c.fetchall()
        has_pk = False
        for col in cols:
            if col[1] == 'food_id' and col[5] == 1:
                has_pk = True
                break
        
        if not has_pk:
            print(f"🔧 Migrating schema for {db_path}: Adding PRIMARY KEY to food_items...")
            c.execute("ALTER TABLE food_items RENAME TO food_items_old")
            c.execute("""
            CREATE TABLE food_items (
                food_id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT,
                main_name TEXT,
                subcategories_json TEXT,
                source TEXT,
                Calories_kcal FLOAT,
                Carbohydrates_g FLOAT,
                Protein_g FLOAT,
                Fats_g FLOAT,
                FreeSugar_g FLOAT,
                Fibre_g FLOAT,
                Sodium_mg FLOAT,
                Calcium_mg FLOAT,
                Iron_mg FLOAT,
                VitaminC_mg FLOAT,
                Folate_ug FLOAT
            )
            """)
            c.execute("""
            INSERT INTO food_items (
                food_id, food_name, main_name, subcategories_json, source,
                Calories_kcal, Carbohydrates_g, Protein_g, Fats_g,
                FreeSugar_g, Fibre_g, Sodium_mg, Calcium_mg, Iron_mg, VitaminC_mg, Folate_ug
            )
            SELECT 
                food_id, food_name, main_name, subcategories_json, source,
                Calories_kcal, Carbohydrates_g, Protein_g, Fats_g,
                FreeSugar_g, Fibre_g, Sodium_mg, Calcium_mg, Iron_mg, VitaminC_mg, Folate_ug
            FROM food_items_old
            """)
            c.execute("DROP TABLE food_items_old")
            conn.commit()
            print("✅ Schema migration completed.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Schema migration failed: {e}")

# Apply schema fix if using SQLite file
if DATABASE_URL.startswith("sqlite"):
    path = DATABASE_URL.replace("sqlite:///", "")
    _check_and_fix_schema(path)

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
