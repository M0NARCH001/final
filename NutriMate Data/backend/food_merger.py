import pandas as pd
indian = pd.read_csv("Indian_Foods_Cleaned.csv")
usda = pd.read_csv("USDA_Foods_Cleaned.csv")
indian["source"] = "Indian"
usda["source"] = "USDA"
indian["food_name"] = indian["Dish Name"]
usda["food_name"] = usda["description"]
drop_cols = ["Dish Name", "description"]
indian = indian.drop(columns=[c for c in drop_cols if c in indian.columns], errors="ignore")
usda = usda.drop(columns=[c for c in drop_cols if c in usda.columns], errors="ignore")
all_cols = set(indian.columns).union(set(usda.columns))
for col in all_cols:
    if col not in indian.columns:
        indian[col] = 0
    if col not in usda.columns:
        usda[col] = 0
ordered_cols = ["source", "fdc_id", "food_name",
                "Calories_kcal", "Carbohydrates_g", "Protein_g", "Fats_g",
                "FreeSugar_g", "Fibre_g", "Sodium_mg", "Calcium_mg",
                "Iron_mg", "VitaminC_mg", "Folate_ug"]
ordered_cols = [c for c in ordered_cols if c in all_cols]
master = pd.concat([indian[ordered_cols], usda[ordered_cols]], ignore_index=True)
master.insert(0, "food_id", range(1, len(master) + 1))
master.to_csv("Foods_Master.csv", index=False)
print("Shape:", master.shape)
print("Columns:", master.columns.tolist())