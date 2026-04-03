# ml/predictor.py
import joblib
import os
import numpy as np

from .config import logger, MODEL_PATH, SCALER_PATH

# Globals — refreshed on startup & after training
MODEL  = None
SCALER = None


def extract_features(impression, food):
    """Extract features for ML model - moved here to avoid circular import"""
    d = impression.deficits if hasattr(impression, 'deficits') else (impression.get('deficits') or {})
    if isinstance(d, str):
        import json
        d = json.loads(d)
    user_region = d.get('user_region', '')
    # Prefer relational region, fall back to legacy string column
    food_region_obj = getattr(food, 'region_rel', None)
    food_region = food_region_obj.name if food_region_obj else getattr(food, 'region', '')
    is_region_match = 1.0 if (user_region and food_region and user_region != 'All India' and user_region == food_region) else 0.0
    has_specific_region = 1.0 if (food_region and food_region not in ('All India', 'Generic')) else 0.0

    return np.array([
        d.get('Calories_kcal',      0) / 500.0,
        d.get('Protein_g',          0) / 100.0,
        d.get('Fats_g',             0) /  80.0,
        d.get('Carbohydrates_g',    0) / 200.0,
        getattr(food, 'Calories_kcal', 0) / 500.0,
        getattr(food, 'Protein_g', 0)    /  30.0,
        getattr(food, 'Fats_g', 0)       /  20.0,
        getattr(food, 'Carbohydrates_g', 0) /  60.0,
        getattr(impression, 'rank', 0)   /  10.0,
        (getattr(impression, 'rule_score', 0) or 0) / 100.0,
        is_region_match,
        has_specific_region
    ], dtype=np.float32)


def load_model_and_scaler():
    global MODEL, SCALER
    try:
        if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)):
            logger.info("No trained model found -> using rule-based only")
            MODEL = SCALER = None
            return False

        MODEL  = joblib.load(MODEL_PATH)
        SCALER = joblib.load(SCALER_PATH)
        logger.info("ML model and scaler loaded successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to load ML model: {str(e)} -> fallback to rule-based")
        MODEL = SCALER = None
        return False


def get_hybrid_score(food, deficits, rule_score: float, rank: int, db=None) -> float | None:
    """
    Returns hybrid score or None (→ caller should use rule_score)
    """
    global MODEL, SCALER
    if MODEL is None or SCALER is None:
        return None

    try:
        # Dummy impression for feature extraction
        class DummyImpression:
            pass
        dummy_imp = DummyImpression()
        dummy_imp.deficits = deficits
        dummy_imp.rank = rank
        dummy_imp.rule_score = rule_score

        feat = extract_features(dummy_imp, food).reshape(1, -1)
        feat_scaled = SCALER.transform(feat)
        ml_prob = MODEL.predict_proba(feat_scaled)[0, 1]

        # Simple linear blend — tune weights later
        # 70% rule + 30% ML probability scaled to same range
        hybrid = 0.70 * rule_score + 0.30 * (ml_prob * 100)
        return hybrid

    except Exception as e:
        logger.warning(f"Hybrid score failed for food {getattr(food, 'food_id', '?')}: {str(e)}")
        return None
