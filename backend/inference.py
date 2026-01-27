# backend/inference.py
import joblib
import numpy as np
import pandas as pd

ARTIFACT = "model.joblib"

BANNED_SODIUM = 800
BANNED_SUGAR = 10
CAL_LIMIT = 600

# load trained model
_bundle = joblib.load(ARTIFACT)
MODEL = _bundle["model"]
SCALER = _bundle["scaler"]
FEATS = _bundle["features"]

DEFICIT_COLS = ["Protein_g","Fibre_g","Calcium_mg","Iron_mg","VitaminC_mg","Folate_ug"]

def _safe(v):
    try:
        return float(v)
    except:
        return 0.0


def score_candidate(deficits: dict, food: dict):
    row = []

    # food nutrients
    for f in FEATS:
        row.append(_safe(food.get(f)))

    # user deficits
    for d in DEFICIT_COLS:
        row.append(_safe(deficits.get(d)))

    X = np.array(row).reshape(1,-1)
    Xs = SCALER.transform(X)

    return float(MODEL.predict(Xs)[0])


def violates_constraints(food):
    if _safe(food.get("Sodium_mg")) > BANNED_SODIUM:
        return True
    if _safe(food.get("FreeSugar_g")) > BANNED_SUGAR:
        return True
    if _safe(food.get("Calories_kcal")) > CAL_LIMIT:
        return True
    return False


def score_candidates(deficit_dict, foods_df: pd.DataFrame, top_k=10):
    scored = []

    for _, r in foods_df.iterrows():
        if str(r.get("source")).strip() != "Indian":
            continue

        food = r.to_dict()

        if violates_constraints(food):
            continue

        s = score_candidate(deficit_dict, food)

        # prefer Indian foods
        if food.get("source") == "Indian":
            s *= 1.3
        else:
            s *= 0.6

        name = (food.get("food_name") or "").lower()

        # penalize exotic / supplement-like items
        BAD_WORDS = ["powder","dried","native","supplement","mix","blend"]
        if any(w in name for w in BAD_WORDS):
            s *= 0.4

        scored.append((s, food))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen = set()

    for s,f in scored:
        name = f.get("main_name") or f.get("food_name")
        if name in seen:
            continue

        seen.add(name)

        results.append({
            "score": round(float(s),4),
            "food_id": f.get("food_id"),
            "food_name": f.get("food_name"),
            "main_name": f.get("main_name"),
            "source": f.get("source")
        })

        if len(results) >= top_k:
            break

    return results
