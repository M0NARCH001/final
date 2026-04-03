import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "..", "nutri_indian.db")
DB_FILE = os.path.abspath(DB_FILE)

def execute():
    if not os.path.exists(DB_FILE):
        print("DB File not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("UPDATE food_items SET region = 'All India', cuisine_type = 'Generic' WHERE region IS NULL")
    updated = c.rowcount
    
    conn.commit()
    conn.close()

    print(f"Backfilled {updated} existing food items with 'All India' region.")

if __name__ == "__main__":
    execute()
