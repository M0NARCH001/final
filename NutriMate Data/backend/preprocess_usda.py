import pandas as pd
foods = pd.read_csv("./Datasets/USDA/food.csv")
nutrients = pd.read_csv("./Datasets/USDA/nutrient.csv")
food_nutrients = pd.read_csv("./Datasets/USDA/food_nutrient.csv", low_memory=False)
fn = food_nutrients.merge(nutrients, left_on="nutrient_id", right_on="id")
fn = fn.merge(foods[["fdc_id", "description"]], on="fdc_id")
pivoted = fn.pivot_table(
    index=["fdc_id", "description"],
    columns="name",
    values="amount",
    aggfunc="first"
).reset_index()
rename_map = {
    "Energy": "Calories_kcal",
    "Protein": "Protein_g",
    "Carbohydrate, by difference": "Carbohydrates_g",
    "Total lipid (fat)": "Fats_g",
    "Sugars, total including NLEA": "FreeSugar_g",
    "Fiber, total dietary": "Fibre_g",
    "Sodium, Na": "Sodium_mg",
    "Calcium, Ca": "Calcium_mg",
    "Iron, Fe": "Iron_mg",
    "Vitamin C, total ascorbic acid": "VitaminC_mg",
    "Folate, total": "Folate_ug"
}
pivoted = pivoted.rename(columns=rename_map)
available_cols = ["fdc_id", "description"] + [
    col for col in rename_map.values() if col in pivoted.columns
]
final = pivoted[available_cols]
final.to_csv("USDA_Foods_Cleaned.csv", index=False)
print("Done")