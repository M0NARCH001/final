import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "..", "nutri_indian.db")
DB_FILE = os.path.abspath(DB_FILE)

def add_column_if_not_exists(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    if column not in columns:
        print(f"Adding column '{column}' to '{table}'...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        return True
    return False

def migrate():
    print(f"Migrating database: {DB_FILE}")
    if not os.path.exists(DB_FILE):
        print("Database not found! Migration skipped.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # User table
    add_column_if_not_exists(c, "user", "region", "TEXT DEFAULT 'All India'")

    # FoodItems table
    add_column_if_not_exists(c, "food_items", "region", "TEXT")
    add_column_if_not_exists(c, "food_items", "cuisine_type", "TEXT")
    add_column_if_not_exists(c, "food_items", "serving_unit", "TEXT")
    add_column_if_not_exists(c, "food_items", "serving_weight_g", "FLOAT")

    # FoodLog table
    add_column_if_not_exists(c, "food_log", "grams_logged", "FLOAT")
    add_column_if_not_exists(c, "food_log", "serving_unit_used", "TEXT")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
