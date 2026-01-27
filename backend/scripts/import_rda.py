#!/usr/bin/env python3
# backend/scripts/import_rda.py
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import RDA
import os, sys

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///nutri_indian.db")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def import_rda(path):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df = df.replace({"ND": None, "": None})
    df.columns = [c.strip() for c in df.columns]

    def tofloat(val):
        try:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            return float(val)
        except Exception:
            return None

    sess = Session()
    count = 0
    for _, row in df.iterrows():
        life_stage = row.get("Life-Stage Group") or row.get("Life-Stage") or row.get("life_stage") or None
        r = RDA(
            life_stage = life_stage,
            Calories_kcal = tofloat(row.get("Calories_kcal") or row.get("Calories") or None),
            Carbohydrates_g = tofloat(row.get("Carbohydrates_g")),
            Protein_g = tofloat(row.get("Protein_g")),
            Fats_g = tofloat(row.get("Fats_g")),
            FreeSugar_g = tofloat(row.get("FreeSugar_g")),
            Fibre_g = tofloat(row.get("Fibre_g")),
            Sodium_mg = tofloat(row.get("Sodium_mg")),
            Calcium_mg = tofloat(row.get("Calcium_mg")),
            Iron_mg = tofloat(row.get("Iron_mg")),
            VitaminC_mg = tofloat(row.get("VitaminC_mg")),
            Folate_ug = tofloat(row.get("Folate_ug"))
        )
        sess.add(r)
        count += 1
    sess.commit()
    sess.close()
    print("Imported RDA rows:", count)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_rda path/to/RDA_Cleaned.csv")
    else:
        import_rda(sys.argv[1])