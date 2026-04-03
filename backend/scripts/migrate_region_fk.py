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

    # 1. Create regions table
    print("Creating regions table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR UNIQUE,
            description VARCHAR
        )
    """)
    conn.commit()

    # 2. Add region_id to food_items and user if it doesn't exist
    print("Adding region_id to food_items and user...")
    try:
        c.execute("ALTER TABLE food_items ADD COLUMN region_id INTEGER REFERENCES regions(id)")
    except sqlite3.OperationalError:
        print("food_items.region_id already exists")
        
    try:
        c.execute("ALTER TABLE user ADD COLUMN region_id INTEGER REFERENCES regions(id)")
    except sqlite3.OperationalError:
        print("user.region_id already exists")
    conn.commit()

    # 3. Extract unique regions from existing food items
    c.execute("SELECT DISTINCT region FROM food_items WHERE region IS NOT NULL AND region != ''")
    distinct_regions = [row[0] for row in c.fetchall()]

    # Also add regions from Users if they exist and are distinct
    try:
        c.execute("SELECT DISTINCT region FROM user WHERE region IS NOT NULL AND region != ''")
        for row in c.fetchall():
            if row[0] not in distinct_regions:
                distinct_regions.append(row[0])
    except sqlite3.OperationalError:
        pass # If legacy user region doesn't exist, ignore

    print(f"Discovered regions: {distinct_regions}")

    # 4. Insert regions into the `regions` table
    for r_name in distinct_regions:
        try:
            c.execute("INSERT OR IGNORE INTO regions (name) VALUES (?)", (r_name,))
        except Exception as e:
            print(f"Error inserting region {r_name}: {str(e)}")
    conn.commit()

    # 5. Map the existing region strings to region_id in both tables
    print("Mapping region_id back to tables...")
    c.execute("""
        UPDATE food_items 
        SET region_id = (SELECT id FROM regions WHERE regions.name = food_items.region)
        WHERE region IS NOT NULL
    """)
    foods_updated = c.rowcount

    try:
        c.execute("""
            UPDATE user 
            SET region_id = (SELECT id FROM regions WHERE regions.name = user.region)
            WHERE region IS NOT NULL
        """)
        users_updated = c.rowcount
    except sqlite3.OperationalError:
        users_updated = 0

    conn.commit()
    conn.close()

    print(f"Migration completed successfully.")
    print(f"Foods updated: {foods_updated}")
    print(f"Users updated: {users_updated}")

if __name__ == "__main__":
    execute()
