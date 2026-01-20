# train_recommender.py
# Trains a simple RandomForest regressor to score candidate foods for deficits.
# Usage: python train_recommender.py --foods Foods_Master.csv --out model.joblib

import argparse
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from sklearn.metrics import mean_squared_error

def build_synthetic_examples(df_foods, n_users=2000, n_candidates=50):
    """
    Create synthetic training examples:
      - sample a random 'user deficit' vector (simulate deficits for macros/micros)
      - sample some candidate foods
      - compute a synthetic usefulness score = normalized dot(deficit, food_nutrients)
    Returns X, y where X includes deficit vector + candidate food features
    """
    # features to use (ensure columns present in your Foods_Master)
    feat_cols = ["Calories_kcal","Carbohydrates_g","Protein_g","Fats_g","FreeSugar_g",
                 "Fibre_g","Sodium_mg","Calcium_mg","Iron_mg","VitaminC_mg","Folate_ug"]
    # fill missing with 0
    for c in feat_cols:
        if c not in df_foods.columns:
            df_foods[c] = 0.0
    df_foods = df_foods.fillna(0.0)

    rows_X = []
    rows_y = []
    for _ in range(n_users):
        # simulate a user deficit vector: sample values from typical RDA ranges
        deficit = np.array([
            np.random.uniform(0, 2000),   # calories
            np.random.uniform(0, 300),    # carbs g
            np.random.uniform(0, 150),    # protein g
            np.random.uniform(0, 120),    # fats g
            np.random.uniform(0, 80),     # sugar g
            np.random.uniform(0, 50),     # fibre g
            np.random.uniform(0, 4000),   # sodium mg
            np.random.uniform(0, 1500),   # calcium mg
            np.random.uniform(0, 50),     # iron mg
            np.random.uniform(0, 300),    # vitamin C mg
            np.random.uniform(0, 400)     # folate ug
        ])
        # pick candidate foods
        cand = df_foods.sample(n=min(n_candidates, len(df_foods)), replace=False)
        cand_feats = cand[feat_cols].values.astype(float)
        # compute "usefulness": dot(deficit, food_features) normalized by energy (or 1)
        # We'll scale by nutritional density: sum(min(deficit, food))
        # This is synthetic but makes model learn sensible patterns.
        for cf in cand_feats:
            # element-wise min(deficit, contribution) as a proxy for how much it helps
            impact = np.minimum(deficit, cf).sum()
            # normalize by calorie or by sum
            score = impact / (1.0 + cf[0])  # prefer high-impact low-calorie
            rows_X.append(np.concatenate([deficit, cf]))
            rows_y.append(score)
    X = np.vstack(rows_X)
    y = np.array(rows_y)
    return X, y, feat_cols

def main(args):
    df = pd.read_csv(args.foods)
    print("Foods rows:", len(df))
    X, y, feat_cols = build_synthetic_examples(df, n_users=args.n_users, n_candidates=args.n_candidates)
    print("Generated examples:", X.shape)
    # split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.12, random_state=42)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print("Training RandomForest...")
    model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
    model.fit(X_train_s, y_train)

    preds = model.predict(X_test_s)
    import math
    mse = mean_squared_error(y_test, preds)
    rmse = math.sqrt(mse)
    print("RMSE:", rmse)
    
    # save artifacts
    joblib.dump({"model": model, "scaler": scaler, "feat_cols": feat_cols}, args.out)
    print("Saved to", args.out)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--foods", required=True)
    p.add_argument("--out", default="model.joblib")
    p.add_argument("--n_users", type=int, default=2000)
    p.add_argument("--n_candidates", type=int, default=40)
    args = p.parse_args()
    main(args)