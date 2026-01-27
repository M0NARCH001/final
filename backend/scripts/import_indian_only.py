import pandas as pd
from sqlalchemy import create_engine

CSV = "Datasets/Indian_Foods_Cleaned.csv"
DB = "sqlite:///./nutri_indian.db"

df = pd.read_csv(CSV).fillna(0)

# rename
df = df.rename(columns={
    "Dish Name": "food_name"
})

# required fields
df["main_name"] = df["food_name"]
df["source"] = "Indian"
df["subcategories_json"] = "[]"

# add id
df.insert(0, "food_id", range(1, len(df)+1))

engine = create_engine(DB)
df.to_sql("food_items", engine, if_exists="replace", index=False)

print("Indian DB schema aligned.")
