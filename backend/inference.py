# backend/inference.py
import pandas as pd

# Nutrients we care about (must match DB columns)
NUTRIENTS = [
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

SODIUM_COL = "Sodium_mg"
SUGAR_COL = "FreeSugar_g"

def _safe(v):
    try:
        return float(v)
    except:
        return 0.0


def score_food(deficits: dict, food: dict):
    """
    Science-based heuristic score.
    Higher = better.
    """

    score = 0.0

    calories = max(_safe(food.get("Calories_kcal")), 1.0)

    # 1. Reward nutrients that are deficient
    for n in NUTRIENTS:
        d = max(deficits.get(n, 0), 0)
        f = _safe(food.get(n))

        if d > 0 and f > 0:
            score += (f / calories) * d

    # 2. Protein bonus
    score += (_safe(food.get("Protein_g")) / calories) * 2.0

    # 3. Fiber bonus
    score += (_safe(food.get("Fibre_g")) / calories) * 1.5

    # 4. Sodium penalty
    sodium = _safe(food.get(SODIUM_COL))
    if sodium > 400:
        score -= sodium / 1000

    # 5. Sugar penalty
    sugar = _safe(food.get(SUGAR_COL))
    if sugar > 8:
        score -= sugar / 10

    # 6. Calorie normalization
    if calories > 600:
        score *= 0.5

    return float(score)


def score_candidates(deficit_dict, foods_df: pd.DataFrame, top_k=10):
    rows = []

    for _, r in foods_df.iterrows():
        food = r.to_dict()
        s = score_food(deficit_dict, food)
        rows.append((s, food))

    rows.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen = set()

    # diversity: avoid same main_name repeatedly
    for s, f in rows:
        name = f.get("main_name") or f.get("food_name")
        if name in seen:
            continue
        seen.add(name)

        results.append({
            "score": round(float(s), 4),
            "food_id": f.get("food_id"),
            "food_name": f.get("food_name"),
            "main_name": f.get("main_name"),
            "source": f.get("source"),
        })

        if len(results) >= top_k:
            break

    return results
