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

    # ================== ADDITIONAL TAMIL NADU ==================
    ("Keerai Masiyal (Spinach Mash)", '["Side", "Veg"]', "Tamil Nadu", "South Indian", "cup", 100, 52, 4, 3, 2, 0, 2, 150, 80, 2, 10, 30),
    ("Vengaya Sambar (Onion Sambar)", '["Curry", "Veg"]', "Tamil Nadu", "South Indian", "cup", 150, 95, 14, 5, 2, 2, 4, 380, 35, 1.5, 8, 14),
    ("Puli Kulambu (Tamarind Curry)", '["Curry", "Veg"]', "Tamil Nadu", "South Indian", "cup", 150, 120, 16, 3, 5, 1, 3, 450, 40, 1.5, 4, 8),
    ("Kavuni Arisi (Black Rice Pudding)", '["Sweet"]', "Tamil Nadu", "South Indian", "cup", 150, 300, 55, 5, 7, 28, 2, 40, 30, 2, 0, 5),
    ("Neer Mor (Buttermilk)", '["Beverage", "Veg"]', "Tamil Nadu", "South Indian", "cup", 200, 40, 4, 2, 1.5, 4, 0, 80, 100, 0.1, 0, 5),
    ("Vazhaipoo Vadai (Banana Flower)", '["Snack", "Veg"]', "Tamil Nadu", "South Indian", "piece", 50, 120, 14, 5, 5, 0, 3, 200, 30, 1.5, 2, 10),
    ("Crab Curry (Nandu Kulambu)", '["Main", "Non-Veg"]', "Tamil Nadu", "South Indian", "cup", 200, 210, 6, 18, 11, 1, 2, 700, 80, 3, 4, 15),
    ("Mutton Kheema", '["Main", "Non-Veg"]', "Tamil Nadu", "South Indian", "cup", 150, 290, 8, 20, 20, 2, 2, 550, 30, 4, 3, 10),

    # ================== ADDITIONAL ANDHRA PRADESH ==================
    ("Gutti Vankaya (Stuffed Brinjal)", '["Main", "Veg"]', "Andhra Pradesh", "South Indian", "cup", 150, 180, 14, 4, 12, 3, 5, 400, 50, 1.5, 5, 12),
    ("Pappu (Toor Dal Andhra)", '["Main", "Veg"]', "Andhra Pradesh", "South Indian", "cup", 150, 170, 22, 10, 4, 2, 7, 380, 45, 2, 4, 20),
    ("Royyala Pulusu (Prawn Curry)", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "cup", 200, 220, 10, 18, 12, 2, 2, 600, 80, 3, 5, 20),
    ("Kandi Podi Rice", '["Main", "Veg"]', "Andhra Pradesh", "South Indian", "cup", 150, 310, 48, 8, 10, 0, 4, 350, 30, 2, 0, 10),
    ("Pesara Garelu (Moong Dal Vada)", '["Snack", "Veg"]', "Andhra Pradesh", "South Indian", "piece", 50, 130, 14, 6, 5, 0, 3, 180, 30, 1.5, 2, 14),
    ("Chicken 65", '["Snack", "Non-Veg"]', "Andhra Pradesh", "South Indian", "piece", 100, 250, 12, 18, 14, 1, 1, 600, 30, 2, 2, 8),
    ("Natu Kodi Pulusu (Country Chicken)", '["Main", "Non-Veg"]', "Andhra Pradesh", "South Indian", "cup", 200, 300, 8, 22, 18, 2, 2, 650, 40, 3.5, 4, 12),

    # ================== ADDITIONAL KERALA ==================
    ("Avial (Mixed Vegetables)", '["Side", "Veg"]', "Kerala", "Kerala", "cup", 150, 140, 14, 3, 8, 3, 5, 300, 40, 1, 5, 15),
    ("Erissery (Pumpkin Lentil)", '["Main", "Veg"]', "Kerala", "Kerala", "cup", 150, 190, 22, 8, 9, 4, 7, 350, 60, 2, 8, 18),
    ("Meen Moilee (Fish in Coconut)", '["Main", "Non-Veg"]', "Kerala", "Kerala", "cup", 200, 220, 6, 20, 13, 2, 1, 500, 60, 2, 4, 15),
    ("Kerala Prawn Curry", '["Main", "Non-Veg"]', "Kerala", "Kerala", "cup", 200, 230, 8, 18, 14, 2, 2, 580, 90, 3, 5, 18),
    ("Thoran (Stir-fried Vegetables)", '["Side", "Veg"]', "Kerala", "Kerala", "cup", 100, 120, 10, 3, 7, 2, 4, 200, 30, 1, 4, 12),
    ("Mutton Stew (Kerala)", '["Main", "Non-Veg"]', "Kerala", "Kerala", "cup", 200, 280, 10, 20, 18, 2, 2, 550, 50, 3.5, 3, 10),
    ("Olan (Ash Gourd Curry)", '["Side", "Veg"]', "Kerala", "Kerala", "cup", 150, 130, 12, 3, 8, 2, 4, 250, 35, 1, 5, 10),
    ("Kerala Fish Fry (Meen Fry)", '["Side", "Non-Veg"]', "Kerala", "Kerala", "piece", 100, 200, 5, 22, 10, 1, 1, 450, 40, 2, 2, 12),

    # ================== ADDITIONAL KARNATAKA ==================
    ("Jolada Rotti (Jowar Roti)", '["Staple", "Veg"]', "Karnataka", "Karnataka", "piece", 60, 130, 26, 4, 1, 0, 4, 30, 15, 1.5, 0, 5),
    ("Akki Rotti (Rice Flour Roti)", '["Breakfast", "Veg"]', "Karnataka", "Karnataka", "piece", 60, 155, 30, 3, 3, 0, 2, 120, 20, 1, 2, 6),
    ("Rave Idli (Semolina Idli)", '["Breakfast", "Veg"]', "Karnataka", "Karnataka", "piece", 60, 110, 20, 3, 2, 1, 1, 200, 20, 0.8, 0, 8),
    ("Chicken Saagu", '["Main", "Non-Veg"]', "Karnataka", "Karnataka", "cup", 200, 280, 10, 22, 16, 2, 2, 600, 40, 3, 3, 10),
    ("Vangi Bath (Brinjal Rice)", '["Main", "Veg"]', "Karnataka", "Karnataka", "cup", 200, 300, 48, 6, 9, 3, 5, 450, 35, 2, 4, 12),
    ("Coorgi Pandi Curry (Pork)", '["Main", "Non-Veg"]', "Karnataka", "Karnataka", "cup", 200, 350, 6, 22, 26, 1, 2, 650, 30, 3.5, 2, 10),
    ("Mandige (Sweet Crepe)", '["Sweet"]', "Karnataka", "Karnataka", "piece", 60, 200, 35, 4, 6, 18, 1, 100, 50, 1, 0, 5),
    ("Thambuli (Herb Buttermilk)", '["Side", "Veg"]', "Karnataka", "Karnataka", "cup", 100, 50, 5, 2, 2, 3, 1, 80, 80, 0.2, 2, 4),

    # ================== ADDITIONAL MAHARASHTRA ==================
    ("Usal (Sprouted Moth Beans)", '["Main", "Veg"]', "Maharashtra", "Maharashtrian", "cup", 150, 200, 28, 12, 5, 2, 8, 350, 50, 3, 5, 25),
    ("Pitla (Gram Flour Curry)", '["Main", "Veg"]', "Maharashtra", "Maharashtrian", "cup", 150, 170, 18, 8, 7, 2, 5, 400, 40, 2.5, 3, 18),
    ("Kolhapuri Chicken", '["Main", "Non-Veg"]', "Maharashtra", "Maharashtrian", "cup", 200, 320, 8, 24, 20, 2, 2, 700, 40, 3.5, 4, 12),
    ("Solkadhi (Kokum Drink)", '["Beverage", "Veg"]', "Maharashtra", "Maharashtrian", "cup", 200, 50, 10, 1, 1, 8, 0, 60, 20, 0.3, 4, 3),
    ("Batata Bhaji (Potato Stir-fry)", '["Side", "Veg"]', "Maharashtra", "Maharashtrian", "cup", 100, 160, 22, 3, 7, 1, 3, 300, 20, 1, 12, 12),
    ("Chicken Kolhapuri", '["Main", "Non-Veg"]', "Maharashtra", "Maharashtrian", "cup", 200, 340, 10, 26, 22, 2, 2, 750, 45, 4, 4, 14),
    ("Bhakri (Jowar)", '["Staple", "Veg"]', "Maharashtra", "Maharashtrian", "piece", 70, 145, 28, 5, 1, 0, 5, 35, 18, 2, 0, 6),
    ("Thalipeeth (Multigrain Flatbread)", '["Breakfast", "Veg"]', "Maharashtra", "Maharashtrian", "piece", 80, 200, 28, 7, 7, 1, 4, 280, 40, 2, 2, 15),

    # ================== ADDITIONAL PUNJAB ==================
    ("Makki Di Roti", '["Staple", "Veg"]', "Punjab", "North Indian", "piece", 60, 165, 30, 4, 4, 0, 3, 30, 10, 1.5, 0, 8),
    ("Aloo Paratha", '["Breakfast", "Veg"]', "Punjab", "North Indian", "piece", 100, 280, 38, 6, 12, 1, 3, 400, 40, 2, 5, 12),
    ("Chana Masala", '["Main", "Veg"]', "Punjab", "North Indian", "cup", 150, 210, 30, 11, 6, 2, 9, 450, 80, 4, 5, 50),
    ("Mutton Rogan Josh", '["Main", "Non-Veg"]', "Punjab", "North Indian", "cup", 200, 350, 8, 26, 24, 2, 2, 650, 50, 4, 4, 12),
    ("Dal Makhani", '["Main", "Veg"]', "Punjab", "North Indian", "cup", 150, 250, 28, 12, 12, 2, 8, 500, 80, 3, 3, 25),
    ("Palak Paneer", '["Main", "Veg"]', "Punjab", "North Indian", "cup", 150, 240, 12, 12, 16, 2, 4, 450, 300, 3, 20, 40),
    ("Kadai Chicken", '["Main", "Non-Veg"]', "Punjab", "North Indian", "cup", 200, 300, 10, 24, 18, 3, 2, 600, 50, 3, 8, 12),
    ("Tandoori Chicken", '["Main", "Non-Veg"]', "Punjab", "North Indian", "piece", 150, 230, 5, 30, 10, 2, 1, 500, 30, 2, 2, 8),
    ("Rajma Masala", '["Main", "Veg"]', "Punjab", "North Indian", "cup", 150, 210, 32, 12, 5, 2, 9, 400, 60, 4, 3, 40),
    ("Aloo Gobi", '["Side", "Veg"]', "Punjab", "North Indian", "cup", 150, 180, 22, 5, 9, 3, 5, 400, 40, 2, 30, 20),

    # ================== ADDITIONAL ALL INDIA ==================
    ("Brown Rice (Cooked)", '["Staple", "Veg"]', "All India", "Generic", "cup", 150, 190, 40, 4, 1.5, 0, 3, 5, 20, 1, 0, 8),
    ("Oats (Cooked)", '["Breakfast", "Veg"]', "All India", "Generic", "cup", 150, 140, 25, 5, 2.5, 0, 4, 60, 20, 2, 0, 14),
    ("Moong Dal Khichdi", '["Main", "Veg"]', "All India", "Generic", "cup", 200, 230, 38, 10, 3, 1, 5, 350, 40, 2.5, 3, 20),
    ("Sprouts Salad", '["Snack", "Veg"]', "All India", "Generic", "cup", 100, 110, 16, 8, 2, 2, 5, 50, 30, 2.5, 5, 30),
    ("Paneer (Cottage Cheese)", '["Dairy", "Veg"]', "All India", "Generic", "piece", 50, 120, 2, 7, 9, 0, 0, 30, 200, 0.2, 0, 8),
    ("Mango (Fresh)", '["Fruit"]', "All India", "Generic", "piece", 150, 100, 25, 1, 0.5, 22, 2, 5, 20, 0.3, 40, 30),
    ("Papaya (Fresh)", '["Fruit", "Veg"]', "All India", "Generic", "cup", 150, 60, 15, 0.5, 0.2, 9, 2, 5, 30, 0.2, 60, 20),
    ("Sweet Potato (Boiled)", '["Vegetable", "Veg"]', "All India", "Generic", "piece", 100, 90, 21, 2, 0.1, 4, 3, 50, 30, 0.6, 20, 14),
    ("Fish (Rohu Steamed)", '["Protein", "Non-Veg"]', "All India", "Generic", "piece", 100, 110, 0, 20, 3, 0, 0, 50, 40, 2, 2, 12),
    ("Egg Bhurji (Scrambled Egg)", '["Breakfast", "Non-Veg"]', "All India", "Generic", "serving", 100, 190, 4, 12, 14, 1, 0, 300, 50, 2, 2, 20),
    ("Tofu Stir-fry", '["Protein", "Veg"]', "All India", "Generic", "cup", 100, 120, 4, 12, 6, 1, 1, 180, 200, 2, 0, 15),
    ("Vegetable Upma", '["Breakfast", "Veg"]', "All India", "Generic", "cup", 150, 200, 30, 5, 6, 2, 3, 380, 25, 1.5, 5, 10),
    ("Mixed Vegetable Sabzi", '["Side", "Veg"]', "All India", "Generic", "cup", 150, 130, 15, 4, 6, 3, 5, 300, 50, 1.5, 15, 20),
    ("Masoor Dal (Red Lentil)", '["Main", "Veg"]', "All India", "Generic", "cup", 150, 170, 22, 12, 3, 1, 7, 350, 30, 3.5, 3, 50),
    ("Chicken Curry (Home Style)", '["Main", "Non-Veg"]', "All India", "Generic", "cup", 200, 280, 8, 22, 17, 2, 2, 580, 40, 3, 4, 12),
    ("Palak (Spinach Stir-fry)", '["Side", "Veg"]', "All India", "Generic", "cup", 100, 55, 5, 3, 2, 0, 3, 200, 100, 2.5, 20, 40),
    ("Greek Yogurt (Plain)", '["Dairy", "Veg"]', "All India", "Generic", "cup", 100, 75, 5, 10, 1, 4, 0, 35, 120, 0.1, 0, 8),
    ("Watermelon", '["Fruit"]', "All India", "Generic", "cup", 150, 50, 12, 1, 0.2, 10, 0.5, 5, 10, 0.2, 10, 2),
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

    # ── Step 3.5: Ensure is_vegetarian column exists ──────────────────────────
    c.execute("PRAGMA table_info(food_items)")
    existing_cols = {row[1] for row in c.fetchall()}
    if "is_vegetarian" not in existing_cols:
        c.execute("ALTER TABLE food_items ADD COLUMN is_vegetarian BOOLEAN")
        conn.commit()
        print("  Added is_vegetarian column to food_items")

    # ── Step 4: Insert regional foods with proper region_id FK ──
    print("Seeding food items...")
    inserted = 0
    skipped = 0
    updated = 0

    def derive_is_veg(sub_json, food_name_lower):
        """Determine veg status from subcategories JSON string."""
        if "Non-Veg" in sub_json or "NonVeg" in sub_json:
            return 0
        if "egg" in food_name_lower or '"Egg"' in sub_json:
            return 0
        if "Veg" in sub_json:
            return 1
        # Known non-veg keywords in food name
        non_veg_keywords = ["chicken", "mutton", "fish", "prawn", "crab", "lamb",
                             "beef", "pork", "egg", "meat", "seafood", "shrimp",
                             "meen", "kodi", "koli", "nandu", "rohu", "tilapia"]
        if any(kw in food_name_lower for kw in non_veg_keywords):
            return 0
        return 1

    for f in RAW_DATA:
        food_name   = f[0]
        sub_json    = f[1]
        region_name = f[2]
        cuisine     = f[3]
        unit        = f[4]
        weight_g    = f[5]
        kcal, carbs, pro, fat, sug, fib, sod, cal_mg, iron, vitc, folate = f[6:]

        is_veg = derive_is_veg(sub_json, food_name.lower())

        # Resolve region_id from the regions table
        region_id = region_map.get(region_name)

        # Check if already exists
        c.execute("SELECT food_id, is_vegetarian FROM food_items WHERE food_name = ?", (food_name,))
        row = c.fetchone()
        if row:
            # Update is_vegetarian if it's not set yet
            if row[1] is None:
                c.execute("UPDATE food_items SET is_vegetarian = ? WHERE food_id = ?", (is_veg, row[0]))
                updated += 1
            skipped += 1
            continue

        c.execute("""
            INSERT INTO food_items (
                food_name, main_name, subcategories_json, source,
                region, region_id, cuisine_type,
                serving_unit, serving_weight_g,
                is_vegetarian,
                Calories_kcal, Carbohydrates_g, Protein_g, Fats_g,
                FreeSugar_g, Fibre_g, Sodium_mg, Calcium_mg,
                Iron_mg, VitaminC_mg, Folate_ug
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            food_name, food_name, sub_json, "NIN/IFCT Synthesized",
            region_name, region_id, cuisine,
            unit, weight_g,
            is_veg,
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
    print(f"  Foods updated    : {updated} (is_vegetarian backfilled)")
    print(f"  Foods skipped    : {skipped} (already existed)")
    print(f"  FK backfilled    : {backfilled}")


if __name__ == "__main__":
    execute()
