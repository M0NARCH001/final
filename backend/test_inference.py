# test_inference.py
import joblib
import pandas as pd
import numpy as np
from inference import score_candidates  # if you created inference.py earlier
# fallback: if you didn't create inference.py, we'll load artifact directly

def load_artifact(path="model.joblib"):
    d = joblib.load(path)
    return d["model"], d["scaler"], d["feat_cols"]

def local_score_demo(model_path="model.joblib", foods_csv="Foods_Master.csv", top_k=8):
    # load model artifacts
    try:
        model, scaler, feat_cols = load_artifact(model_path)
        print("Loaded model artifact (scaler + feat_cols).")
    except Exception as e:
        print("Failed to load artifact via load_artifact():", e)
        print("Trying direct joblib load fallback.")
        obj = joblib.load(model_path)
        model = obj["model"]; scaler = obj["scaler"]; feat_cols = obj["feat_cols"]

    # load foods (small sample for speed)
    df = pd.read_csv(foods_csv)
    print("Foods rows total:", len(df))
    # pick a small sample
    sample = df.sample(n=min(200, len(df)), random_state=42).fillna(0.0)

    # Example deficit vector (simulate user needing protein + iron + vitamin C)
    deficit = {
        "Calories_kcal": 500.0,
        "Carbohydrates_g": 50.0,
        "Protein_g": 40.0,
        "Fats_g": 20.0,
        "FreeSugar_g": 10.0,
        "Fibre_g": 10.0,
        "Sodium_mg": 500.0,
        "Calcium_mg": 200.0,
        "Iron_mg": 8.0,
        "VitaminC_mg": 60.0,
        "Folate_ug": 200.0
    }

    # Build X rows as in training: [deficit_vector, food_features]
    X = []
    foods = []
    for _, r in sample.iterrows():
        foods.append(r)
    # prepare arrays
    def mk_row(food_row):
        deficits = np.array([deficit.get(c, 0.0) for c in feat_cols], dtype=float)
        food_feats = np.array([food_row.get(c, 0.0) for c in feat_cols], dtype=float)
        return np.concatenate([deficits, food_feats])

    X_raw = np.vstack([mk_row(r) for r in foods])
    Xs = scaler.transform(X_raw)
    preds = model.predict(Xs)

    # attach scores to names
    scored = []
    for score, r in zip(preds, foods):
        scored.append((float(score), r.get("food_name", r.get("description", "unknown")), r.get("food_id", None)))
    scored.sort(key=lambda x: x[0], reverse=True)
    print("\nTop recommendations (sample):")
    for s, name, fid in scored[:top_k]:
        print(f"score={s:.4f}\tfood_id={fid}\t{name}")

if __name__ == "__main__":
    local_score_demo()