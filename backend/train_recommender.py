import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

DATA = "Datasets/Indian_Foods_Cleaned.csv"
OUT = "model.joblib"

# Nutrients we use
FEATS = [
    "Calories_kcal",
    "Protein_g",
    "Carbohydrates_g",
    "Fats_g",
    "Fibre_g",
    "Calcium_mg",
    "Iron_mg",
    "VitaminC_mg",
    "Folate_ug",
]

print("Loading foods...")
df = pd.read_csv(DATA)

df = df.fillna(0)

# Generate synthetic user deficits (random realistic)
def random_deficits():
    return {
        "Protein_g": np.random.uniform(20, 60),
        "Fibre_g": np.random.uniform(10, 30),
        "Calcium_mg": np.random.uniform(300, 800),
        "Iron_mg": np.random.uniform(5, 15),
        "VitaminC_mg": np.random.uniform(20, 80),
        "Folate_ug": np.random.uniform(100, 300),
    }

X = []
y = []

print("Generating training samples...")

for _ in range(4000):
    deficits = random_deficits()
    food = df.sample(1).iloc[0]

    row = []

    # food nutrients
    for f in FEATS:
        row.append(food[f])

    # deficits
    for k in ["Protein_g","Fibre_g","Calcium_mg","Iron_mg","VitaminC_mg","Folate_ug"]:
        row.append(deficits.get(k,0))

    # synthetic utility label
    utility = (
        deficits["Protein_g"] * food["Protein_g"] +
        deficits["Fibre_g"] * food["Fibre_g"] +
        deficits["Calcium_mg"] * food["Calcium_mg"] / 100 +
        deficits["Iron_mg"] * food["Iron_mg"] * 5 +
        deficits["VitaminC_mg"] * food["VitaminC_mg"] +
        deficits["Folate_ug"] * food["Folate_ug"] / 50
    )

    # calorie penalty
    utility -= food["Calories_kcal"] * 0.3

    X.append(row)
    y.append(utility)

X = np.array(X)
y = np.array(y)

print("Scaling...")
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

print("Training model...")
model = GradientBoostingRegressor(n_estimators=150, max_depth=4)
model.fit(Xs, y)

joblib.dump({
    "model": model,
    "scaler": scaler,
    "features": FEATS
}, OUT)

print("Saved", OUT)
