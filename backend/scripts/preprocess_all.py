#!/usr/bin/env python3
"""
Preprocess the provided CSV files to create a unified Foods_Master.csv

Usage example:
python -m scripts.preprocess_all \
  --indian ./Datasets/Indian_Foods_Cleaned.csv \
  --usda ./Datasets/USDA_Foods_Cleaned.csv \
  --out ./Foods_Master.csv
"""
import argparse
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

NUTRIENT_COLUMNS = [
    "Calories_kcal", "Carbohydrates_g", "Protein_g", "Fats_g",
    "FreeSugar_g", "Fibre_g", "Sodium_mg", "Calcium_mg",
    "Iron_mg", "VitaminC_mg", "Folate_ug"
]

def _choose_name_column(df, prefer_candidates=None):
    if prefer_candidates is None:
        prefer_candidates = ["dish name", "dish_name", "food_name", "Food_Name", "food name",
                             "description", "Description", "name", "Name", "food", "Food", "dish"]
    lc_map = {c.lower(): c for c in df.columns}
    for cand in prefer_candidates:
        if cand.lower() in lc_map:
            return lc_map[cand.lower()]
    keywords = ["dish", "food", "name", "description", "item", "title"]
    for col in df.columns:
        cl = col.lower()
        if any(k in cl for k in keywords):
            return col
    text_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype).startswith("string")]
    if len(text_cols) >= 1:
        return text_cols[0]
    return df.columns[0] if len(df.columns) > 0 else None

def normalize_df(df: pd.DataFrame, source_label: str, prefer_name_candidates=None):
    import numpy as np
    if prefer_name_candidates is None:
        prefer_name_candidates = ["dish name", "food_name", "Food_Name", "description", "dish_name", "food"]
    chosen = _choose_name_column(df, prefer_name_candidates)
    if chosen is None:
        raise ValueError(f"Cannot find a name column in source: {source_label}. Columns: {list(df.columns)}")
    print(f"[normalize_df] source={source_label} - using name column: {chosen!r}")

    df2 = df.copy()

    colmap = {}
    for col in df2.columns:
        c = col.strip()
        low = c.lower()
        if "calori" in low and "Calories_kcal" not in colmap.values():
            colmap[col] = "Calories_kcal"
        if "protein" in low and "Protein_g" not in colmap.values():
            colmap[col] = "Protein_g"
        if "carbohyd" in low and "Carbohydrates_g" not in colmap.values():
            colmap[col] = "Carbohydrates_g"
        if re.search(r"\b(total lipid|fat|lipid)\b", low) and "Fats_g" not in colmap.values():
            colmap[col] = "Fats_g"
        if "fibre" in low or "fiber" in low:
            colmap[col] = "Fibre_g"
        if "sodium" in low:
            colmap[col] = "Sodium_mg"
        if "calcium" in low:
            colmap[col] = "Calcium_mg"
        if "iron" in low and "Iron_mg" not in colmap.values():
            colmap[col] = "Iron_mg"
        if "vitamin c" in low or "vitaminc" in low or "ascorbic" in low:
            colmap[col] = "VitaminC_mg"
        if "folate" in low:
            colmap[col] = "Folate_ug"
        if "sugar" in low or "sugars" in low:
            colmap[col] = "FreeSugar_g"
        if "carbohydrate" in low and "Carbohydrates_g" not in colmap.values():
            colmap[col] = "Carbohydrates_g"

    df2 = df2.rename(columns=colmap)

    for n in NUTRIENT_COLUMNS:
        if n not in df2.columns:
            df2[n] = np.nan

    df2 = df2.rename(columns={chosen: "food_name"})
    df2[NUTRIENT_COLUMNS] = df2[NUTRIENT_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    df2["source"] = source_label

    out_cols = ["food_name"] + NUTRIENT_COLUMNS + ["source"]
    return df2[out_cols]

def clean_main_subs(food_name: str):
    if not isinstance(food_name, str) or not food_name.strip():
        return ("", [])
    import re
    def clean_part(s):
        s = s.strip()
        # remove surrounding quotes/parens/brackets and trailing punctuation
        s = re.sub(r'^[\s"\'\(\)\[\]\-:]+|[\s"\'\(\)\[\]\-:]+$', '', s)
        s = re.sub(r'\s+', ' ', s)
        # fix unmatched parentheses: remove trailing "(" or ")"
        s = re.sub(r'^[\(\)\s]+|[\(\)\s]+$', '', s)
        s = s.strip()
        return s
    parts = [clean_part(p) for p in food_name.split(",")]
    parts = [p for p in parts if p]
    if not parts:
        return ("", [])
    main = parts[0]
    subs = parts[1:]
    trivial = {"raw","cooked","uncooked","dried"}
    subs = [s for s in subs if s.lower() not in trivial]
    return (main, subs)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indian", required=False)
    parser.add_argument("--usda", required=False)
    parser.add_argument("--rda", required=False)
    parser.add_argument("--out", default="Foods_Master.csv")
    args = parser.parse_args()

    parts = []
    if args.indian:
        print("Reading Indian dataset:", args.indian)
        df_ind = pd.read_csv(args.indian, low_memory=False)
        parts.append(normalize_df(df_ind, "Indian", ["Dish Name","dish name","food_name","Food_Name","description","dish_name","food"]))

    if args.usda:
        print("Reading USDA dataset:", args.usda)
        df_usda = pd.read_csv(args.usda, low_memory=False)
        parts.append(normalize_df(df_usda, "USDA", ["description", "food_name", "Food_Name"]))

    if len(parts) == 0:
        raise ValueError("No datasets provided (pass --indian and/or --usda)")

    master = pd.concat(parts, ignore_index=True)
    master["food_name"] = master["food_name"].astype(str).map(lambda s: re.sub(r"\s+", " ", s).strip())
    master["food_name_lower"] = master["food_name"].str.lower()
    master = master.drop_duplicates("food_name_lower").drop(columns=["food_name_lower"])

    mains = []
    subs_list = []
    for fm in master["food_name"].tolist():
        m, subs = clean_main_subs(fm)
        mains.append(m)
        subs_list.append(subs)
    master["main_name"] = mains
    master["subcategories_json"] = [json.dumps(s) if s else "[]" for s in subs_list]

    out_path = Path(args.out)
    master.to_csv(out_path, index=False)
    print("Wrote:", out_path.resolve())
    master.head(500).to_csv("Foods_Master_sample.csv", index=False)
    print("Sample exported to Foods_Master_sample.csv (500 rows)")

if __name__ == "__main__":
    main()