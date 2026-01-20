# inference.py
import joblib
import numpy as np
import pandas as pd

ARTIFACT = "model.joblib"  # created above

def load_artifact(path=ARTIFACT):
    d = joblib.load(path)
    return d["model"], d["scaler"], d["feat_cols"]

MODEL, SCALER, FEAT_COLS = load_artifact()

def score_candidate(deficit_vector, food_row):
    """
    deficit_vector: dict with keys matching FEAT_COLS
    food_row: dict or pandas row containing FEAT_COLS
    returns: score (float)
    """
    # build array: [deficit_vector (len 11), food_features (len 11)]
    deficits = np.array([deficit_vector.get(k, 0.0) for k in FEAT_COLS])
    food_feats = np.array([food_row.get(k, 0.0) for k in FEAT_COLS])
    X = np.concatenate([deficits, food_feats]).reshape(1, -1)
    Xs = SCALER.transform(X)
    score = float(MODEL.predict(Xs)[0])
    return score

def score_candidates(deficit_dict, foods_df, top_k=10):
    rows = []
    for _, r in foods_df.iterrows():
        s = score_candidate(deficit_dict, r.to_dict())
        rows.append((s, r.to_dict()))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [ {"score": float(s), "food": f} for s,f in rows[:top_k] ]