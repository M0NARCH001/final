import pandas as pd
df_ind = pd.read_csv("./Datasets/Indian_Food_Nutrition_Processed.csv")
df_ind = df_ind.rename(columns={
    "Calories (kcal)": "Calories_kcal",
    "Carbohydrates (g)": "Carbohydrates_g",
    "Protein (g)": "Protein_g",
    "Fats (g)": "Fats_g",
    "Free Sugar (g)": "FreeSugar_g",
    "Fibre (g)": "Fibre_g",
    "Sodium (mg)": "Sodium_mg",
    "Calcium (mg)": "Calcium_mg",
    "Iron (mg)": "Iron_mg",
    "Vitamin C (mg)": "VitaminC_mg",
    "Folate (µg)": "Folate_ug"
})
print(df_ind.head())
print("\nColumns:", df_ind.columns)
df_ind.to_csv("Indian_Foods_Cleaned.csv", index=False)