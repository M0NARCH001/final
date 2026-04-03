"""
seed_indian_foods.py
--------------------
Seeds the `regions` table and `food_items` table with regional Indian foods.
Uses the normalised Region foreign-key relationship introduced in v2.1.

Safety: The script uses nutri_indian.db and is idempotent — running it
multiple times will not create duplicates.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "..", "nutri_indian.db")
DB_FILE = os.path.abspath(DB_FILE)

# ── Region definitions ──────────────────────────────────────────────
REGIONS = [
    ("All India",        "Pan-Indian / generic foods common across the country"),
    ("Tamil Nadu",       "Traditional Tamil cuisine from South India"),
    ("Andhra Pradesh",   "Spicy Andhra and Telangana cuisines"),
    ("Kerala",           "Kerala cuisine with coconut-based dishes"),
    ("Karnataka",        "Karnataka cuisine including Udupi and Coorgi"),
    ("Maharashtra",      "Maharashtrian street food and home cooking"),
    ("Punjab",           "Rich North Indian / Punjabi cuisine"),
]

# ── Food data ───────────────────────────────────────────────────────
# Format:
# (food_name, subcategories_json, region_name, cuisine, unit, weight_g,
#  kcal, carbs, protein, fat, sugar, fibre, sodium, calcium, iron, vitC, folate)

RAW_DATA = [
    # ================== TAMIL NADU ==================
    ("Idli", '["Breakfast", "Steamed"]', "Tamil Nadu", "South Indian", "piece", 50, 39, 8, 1, 0.1, 0, 1, 15, 12, 0.5, 0, 5),
    ("Medu Vada", '["Breakfast", "Snack"]', "Tamil Nadu", "South Indian", "piece", 45, 140, 15, 4, 7, 0, 2, 200, 20, 1, 0, 10),
    ("Sambar", '["Accompaniment", "Lunch"]', "Tamil Nadu", "South Indian", "cup", 150, 110, 16, 5, 3, 2, 4, 350, 30, 1.5, 6, 12),
    ("Ponnaganti Keerai Poriyal", '["Side", "Dinner"]', "Tamil Nadu", "South Indian", "cup", 100, 85, 8, 3, 4, 1, 5, 200, 150, 3, 15, 40),
    ("Ven Pongal", '["Breakfast"]', "Tamil Nadu", "South Indian", "cup", 200, 280, 42, 6, 10, 0, 4, 400, 30, 2, 0, 15),
    ("Sakkarai Pongal", '["Sweet", "Festival"]', "Tamil Nadu", "South Indian", "cup", 150, 350, 60, 4, 12, 35, 2, 50, 40, 1, 0, 5),
    ("Chettinad Chicken", '["Main", "Non-Veg"]', "Tamil Nadu", "South Indian", "serving", 200, 320, 10, 25, 20, 2, 3, 600, 40, 3, 5, 10),
    ("Filter Coffee", '["Beverage"]', "Tamil Nadu", "South Indian", "cup", 150, 80, 10, 2, 4, 8, 0, 50, 100, 0.2, 0, 0),
    ("Appam", '["Breakfast"]', "Tamil Nadu", "South Indian", "piece", 80, 120, 24, 2, 1, 2, 1, 100, 15, 0.5, 0, 2),
    ("Coconut Chutney", '["Accompaniment"]', "Tamil Nadu", "South Indian", "tbsp", 15, 50, 2, 1, 4, 0, 1, 150, 5, 0.2, 0, 1),
    ("Tomato Chutney", '["Accompaniment"]', "Tamil Nadu", "South Indian", "tbsp", 20, 25, 4, 0.5, 1, 1, 1, 120, 5, 0.3, 4, 2),
    ("Kuzhi Paniyaram", '["Snack"]', "Tamil Nadu", "South Indian", "piece", 20, 45, 8, 1, 1, 0, 0.5, 80, 5, 0.2, 0, 1),
    ("More Kuzhambu", '["Curry"]', "Tamil Nadu", "South Indian", "cup", 150, 130, 12, 4, 7, 2, 2, 300, 100, 1, 2, 8),
    ("Rasam", '["Soup"]', "Tamil Nadu", "South Indian", "cup", 150, 60, 10, 2, 1, 1, 2, 400, 25, 1, 8, 5),
    ("Kothu Parotta", '["Dinner", "Street"]', "Tamil Nadu", "South Indian", "serving", 250, 480, 55, 12, 22, 5, 4, 750, 50, 4, 10, 20),
    ("Thalappakatti Biryani", '["Main", "Non-Veg"]', "Tamil Nadu", "South Indian", "serving", 300, 550, 60, 25, 22, 2, 5, 800, 60, 4.5, 8, 25),
    ("Milagu Rasam (Pepper)", '["Soup"]', "Tamil Nadu", "South Indian", "cup", 100, 45, 8, 1, 1, 1, 2, 300, 20, 1, 5, 4),
    ("Sundal", '["Snack", "Festival"]', "Tamil Nadu", "South Indian", "cup", 100, 140, 22, 8, 3, 1, 6, 250, 40, 2.5, 0, 15),
    ("Payasam", '["Sweet"]', "Tamil Nadu", "South Indian", "cup", 150, 280, 45, 5, 8, 30, 1, 60, 80, 0.5, 0, 2),
    ("Adai Dosa", '["Breakfast"]', "Tamil Nadu", "South Indian", "piece", 80, 180, 25, 8, 5, 1, 3, 200, 30, 2, 0, 10),

    # ================== ANDHRA PRADESH / TELANGANA ==================
    ("Pesarattu", '["Breakfast"]', "Andhra Pradesh", "South Indian", "piece", 100, 210, 30, 9, 6, 1, 4, 250, 40, 2.5, 5, 15),
    ("Gongura Pachadi", '["Accompaniment"]', "Andhra Pradesh", "South Indian", "tbsp", 20, 45, 3, 1, 3, 0, 1, 200, 35, 1.5, 8, 5),
    ("Hyderabadi Chicken Biryani", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "serving", 300, 490, 55, 25, 18, 2, 4, 850, 60, 4, 6, 20),
    ("Pulihora (Tamarind Rice)", '["Lunch"]', "Andhra Pradesh", "South Indian", "cup", 200, 310, 55, 6, 8, 2, 3, 400, 30, 2, 2, 10),
    ("Gutti Vankaya Kura", '["Curry"]', "Andhra Pradesh", "South Indian", "cup", 150, 190, 14, 4, 13, 2, 5, 350, 45, 1.5, 6, 12),
    ("Natukodi Pulusu", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "serving", 200, 340, 12, 26, 22, 1, 2, 650, 30, 3.5, 5, 15),
    ("Mirchi Bajji", '["Snack"]', "Andhra Pradesh", "South Indian", "piece", 50, 120, 12, 3, 7, 0, 1, 300, 15, 0.5, 10, 5),
    ("Bobbatlu", '["Sweet"]', "Andhra Pradesh", "South Indian", "piece", 60, 220, 35, 4, 8, 15, 2, 50, 10, 1, 0, 4),
    ("Avakaya (Mango Pickle)", '["Accompaniment"]', "Andhra Pradesh", "South Indian", "tbsp", 15, 60, 4, 0.5, 5, 1, 1, 400, 10, 0.5, 5, 2),
    ("Andhra Chicken Curry", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "serving", 200, 310, 8, 24, 18, 1, 2, 700, 25, 2.5, 5, 10),
    ("Mla Pesarattu", '["Breakfast"]', "Andhra Pradesh", "South Indian", "piece", 120, 280, 35, 12, 10, 1, 5, 350, 50, 3, 5, 18),
    ("Royyala Iguru (Prawns)", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "serving", 150, 220, 6, 22, 12, 1, 1, 550, 60, 2.5, 2, 8),
    ("Ariselu", '["Sweet"]', "Andhra Pradesh", "South Indian", "piece", 40, 180, 28, 2, 7, 18, 1, 10, 5, 0.5, 0, 2),
    ("Andhra Meals (Thali avg)", '["Main"]', "Andhra Pradesh", "South Indian", "serving", 600, 850, 120, 25, 30, 10, 12, 1500, 100, 8, 30, 40),
    ("Chepala Pulusu (Fish)", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "serving", 200, 240, 15, 20, 12, 2, 2, 650, 45, 2, 10, 15),

    # ================== KERALA ==================
    ("Puttu", '["Breakfast"]', "Kerala", "South Indian", "piece", 100, 180, 38, 4, 1, 1, 4, 100, 20, 1, 0, 5),
    ("Kadala Curry", '["Curry", "Breakfast"]', "Kerala", "South Indian", "cup", 150, 210, 25, 10, 8, 2, 8, 300, 50, 3, 6, 25),
    ("Appam with Stew", '["Breakfast"]', "Kerala", "South Indian", "serving", 250, 260, 32, 5, 12, 4, 5, 350, 40, 2, 15, 10),
    ("Kerala Beef Roast", '["Main", "Non-Veg"]', "Kerala", "South Indian", "serving", 150, 350, 8, 24, 25, 2, 2, 600, 30, 4, 2, 8),
    ("Karimeen Pollichathu", '["Main", "Non-Veg"]', "Kerala", "South Indian", "piece", 200, 280, 5, 25, 16, 1, 1, 500, 40, 2, 5, 10),

    # ================== KARNATAKA ==================
    ("Bisi Bele Bath", '["Lunch"]', "Karnataka", "South Indian", "cup", 250, 380, 55, 12, 14, 4, 7, 600, 60, 3.5, 15, 20),
    ("Mysore Masala Dosa", '["Breakfast"]', "Karnataka", "South Indian", "piece", 150, 320, 45, 6, 12, 2, 4, 450, 30, 2, 5, 10),
    ("Ragi Mudde", '["Lunch"]', "Karnataka", "South Indian", "piece", 150, 210, 45, 5, 1, 0, 8, 10, 250, 3, 0, 5),
    ("Neer Dosa", '["Breakfast"]', "Karnataka", "South Indian", "piece", 50, 80, 16, 1, 1, 0, 0.5, 100, 5, 0.2, 0, 2),
    ("Akki Roti", '["Breakfast", "Dinner"]', "Karnataka", "South Indian", "piece", 80, 160, 28, 3, 4, 1, 3, 200, 15, 1, 2, 5),

    # ================== MAHARASHTRA ==================
    ("Misal Pav", '["Breakfast", "Street"]', "Maharashtra", "West Indian", "serving", 250, 420, 50, 14, 18, 4, 8, 800, 60, 4, 12, 25),
    ("Vada Pav", '["Snack", "Street"]', "Maharashtra", "West Indian", "piece", 150, 300, 38, 6, 14, 2, 4, 600, 40, 2, 5, 10),
    ("Puran Poli", '["Sweet", "Festival"]', "Maharashtra", "West Indian", "piece", 80, 250, 40, 6, 8, 15, 3, 50, 30, 1.5, 0, 8),
    ("Zhunka Bhakar", '["Lunch", "Dinner"]', "Maharashtra", "West Indian", "serving", 200, 310, 42, 10, 11, 2, 7, 450, 50, 3, 5, 15),
    ("Pav Bhaji", '["Street", "Dinner"]', "Maharashtra", "West Indian", "serving", 300, 450, 60, 12, 18, 6, 8, 850, 80, 3, 25, 20),

    # ================== PUNJAB / NORTH ==================
    ("Chole Bhature", '["Lunch", "Street"]', "Punjab", "North Indian", "serving", 350, 650, 75, 18, 30, 5, 12, 900, 80, 5, 10, 30),
    ("Butter Chicken", '["Main", "Non-Veg"]', "Punjab", "North Indian", "serving", 200, 450, 12, 28, 32, 4, 2, 800, 50, 2, 8, 10),
    ("Makki Roti + Sarson Saag", '["Dinner", "Winter"]', "Punjab", "North Indian", "serving", 300, 380, 48, 14, 15, 3, 12, 600, 200, 6, 25, 45),
    ("Aloo Paratha", '["Breakfast"]', "Punjab", "North Indian", "piece", 150, 300, 42, 8, 12, 2, 4, 450, 30, 2, 10, 12),
    ("Paneer Tikka Masala", '["Main", "Veg"]', "Punjab", "North Indian", "cup", 200, 350, 15, 18, 25, 6, 3, 700, 250, 2, 15, 15),

    # ================== GENERIC / ALL INDIA ==================
    ("Plain Rice", '["Staple"]', "All India", "Generic", "cup", 150, 200, 45, 4, 0.5, 0, 1, 5, 10, 1, 0, 2),
    ("Plain Roti (Chapati)", '["Staple"]', "All India", "Generic", "piece", 40, 120, 22, 4, 1, 0, 3, 50, 20, 1, 0, 10),
    ("Dal Tadka", '["Main", "Veg"]', "All India", "Generic", "cup", 150, 180, 20, 10, 6, 2, 8, 400, 40, 2.5, 5, 20),
    ("Masala Dosa", '["Breakfast"]', "All India", "South Indian", "piece", 120, 240, 35, 5, 9, 2, 3, 350, 25, 1.5, 5, 8),
    ("Boiled Egg", '["Protein", "Non-Veg"]', "All India", "Generic", "piece", 50, 70, 0.5, 6, 5, 0, 0, 60, 25, 1, 0, 12),
    ("Chicken Breast (Grilled)", '["Protein", "Non-Veg"]', "All India", "Generic", "piece", 100, 150, 0, 30, 3, 0, 0, 70, 15, 1, 0, 5),
    ("Banana", '["Fruit", "Snack"]', "All India", "Generic", "piece", 120, 105, 27, 1, 0.5, 14, 3, 1, 5, 0.3, 10, 24),
    ("Curd (Dahi)", '["Dairy"]', "All India", "Generic", "cup", 100, 60, 5, 3, 3, 4, 0, 40, 120, 0.1, 0, 5),
]


def execute():
    if not os.path.exists(DB_FILE):
        print(f"ERROR: DB file {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ── Step 1: Ensure the regions table exists ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR UNIQUE,
            description VARCHAR
        )
    """)
    conn.commit()

    # ── Step 2: Seed / upsert regions ──
    print("Seeding regions table...")
    for name, desc in REGIONS:
        c.execute("INSERT OR IGNORE INTO regions (name, description) VALUES (?, ?)", (name, desc))
    conn.commit()

    # Build a name → id lookup
    c.execute("SELECT id, name FROM regions")
    region_map = {name: rid for rid, name in c.fetchall()}
    print(f"  Region map: {region_map}")

    # ── Step 3: Clear old auto-generated placeholder foods ──
    c.execute("DELETE FROM food_items WHERE food_name LIKE 'Indian Setup Food %'")
    conn.commit()

    # ── Step 4: Insert regional foods with proper region_id FK ──
    print("Seeding food items...")
    inserted = 0
    skipped = 0

    for f in RAW_DATA:
        food_name   = f[0]
        sub_json    = f[1]
        region_name = f[2]
        cuisine     = f[3]
        unit        = f[4]
        weight_g    = f[5]
        kcal, carbs, pro, fat, sug, fib, sod, cal_mg, iron, vitc, folate = f[6:]

        # Resolve region_id from the regions table
        region_id = region_map.get(region_name)

        # Skip duplicates
        c.execute("SELECT food_id FROM food_items WHERE food_name = ?", (food_name,))
        if c.fetchone():
            skipped += 1
            continue

        c.execute("""
            INSERT INTO food_items (
                food_name, main_name, subcategories_json, source,
                region, region_id, cuisine_type,
                serving_unit, serving_weight_g,
                Calories_kcal, Carbohydrates_g, Protein_g, Fats_g,
                FreeSugar_g, Fibre_g, Sodium_mg, Calcium_mg,
                Iron_mg, VitaminC_mg, Folate_ug
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food_name, food_name, sub_json, "NIN/IFCT Synthesized",
            region_name, region_id, cuisine,
            unit, weight_g,
            kcal, carbs, pro, fat,
            sug, fib, sod, cal_mg,
            iron, vitc, folate
        ))
        inserted += 1

    conn.commit()

    # ── Step 5: Backfill region_id for any existing foods with region text but no FK ──
    c.execute("""
        UPDATE food_items
        SET region_id = (SELECT id FROM regions WHERE regions.name = food_items.region)
        WHERE region IS NOT NULL AND (region_id IS NULL)
    """)
    backfilled = c.rowcount
    conn.commit()

    conn.close()

    print(f"\nDone!")
    print(f"  Regions in table : {len(region_map)}")
    print(f"  Foods inserted   : {inserted}")
    print(f"  Foods skipped    : {skipped} (already existed)")
    print(f"  FK backfilled    : {backfilled}")


if __name__ == "__main__":
    execute()
