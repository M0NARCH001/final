#!/usr/bin/env python3
# backend/scripts/import_foods.py
import pandas as pd
from sqlalchemy import create_engine
from app.models import FoodItem
from sqlalchemy.orm import sessionmaker
import os, json, sys

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///nutri.db")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def import_csv(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.fillna(0)
    sess = Session()
    count = 0
    for _, row in df.iterrows():
        fi = FoodItem(
            food_name=row.get("food_name"),
            main_name=row.get("main_name") if "main_name" in row else None,
            subcategories_json=(row.get("subcategories_json") if "subcategories_json" in row else "[]"),
            source=row.get("source"),
            Calories_kcal=row.get("Calories_kcal", 0) or 0,
            Carbohydrates_g=row.get("Carbohydrates_g", 0) or 0,
            Protein_g=row.get("Protein_g", 0) or 0,
            Fats_g=row.get("Fats_g", 0) or 0,
            FreeSugar_g=row.get("FreeSugar_g", 0) or 0,
            Fibre_g=row.get("Fibre_g", 0) or 0,
            Sodium_mg=row.get("Sodium_mg", 0) or 0,
            Calcium_mg=row.get("Calcium_mg", 0) or 0,
            Iron_mg=row.get("Iron_mg", 0) or 0,
            VitaminC_mg=row.get("VitaminC_mg", 0) or 0,
            Folate_ug=row.get("Folate_ug", 0) or 0
        )
        sess.add(fi)
        count += 1
        if count % 1000 == 0:
            sess.commit()
            print("Inserted", count)
    sess.commit()
    sess.close()
    print("Import finished. Total inserted:", count)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_foods path/to/Foods_Master.csv")
    else:
        import_csv(sys.argv[1])