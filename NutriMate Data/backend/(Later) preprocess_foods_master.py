# Yes, useful for later if:
# You want to explain why some foods have missing nutrients.
# You want to filter/search by food source type (e.g., only branded foods for barcode scanning).
# You want to prioritize higher quality data (Foundation > Branded).


import pandas as pd

master = pd.read_csv("Foods_Master.csv")

# Load USDA metadata (to get data_type)
usda_meta = pd.read_csv("./Datasets/USDA/food.csv")[["fdc_id", "data_type"]]

# Merge data_type into master
master = master.merge(usda_meta, on="fdc_id", how="left")

# Fill Indian foods with "Indian"
master["data_type"] = master["data_type"].fillna("Indian")

# Reorder columns for clarity
ordered_cols = ["food_id", "source", "data_type", "fdc_id", "food_name",
                "Calories_kcal", "Carbohydrates_g", "Protein_g", "Fats_g",
                "FreeSugar_g", "Fibre_g", "Sodium_mg", "Calcium_mg",
                "Iron_mg", "VitaminC_mg", "Folate_ug"]

# Keep only existing columns
ordered_cols = [c for c in ordered_cols if c in master.columns]
master = master[ordered_cols]

# Save cleaned master
master.to_csv("Foods_Master_Updated.csv", index=False)
