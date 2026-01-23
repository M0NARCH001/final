import pandas as pd
df_rda = pd.read_csv("./Datasets/macros-RDAs.csv")
df_rda = df_rda.rename(columns={
    "Total Water (L)": "TotalWater_L",
    "Carbohydrate (g)": "Carbohydrates_g",
    "Total Fiber (g)": "Fibre_g",
    "Fat (g)": "Fats_g",
    "Linoleic Acid (g)": "Linoleic_Acid_g",
    "α-Linolenic Acid (g)": "Alpha_Linolenic_Acid_g",
    "Protein (g)": "Protein_g"
})
print(df_rda.head())
print("\nColumns:", df_rda.columns)
df_rda.to_csv("RDA_Cleaned.csv", index=False)