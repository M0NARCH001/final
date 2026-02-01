# ml/trainer.py
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from functools import wraps
import time

from .config import logger, MIN_IMPRESSIONS, MIN_ACCEPTS, MIN_HOURS_BETWEEN, MODEL_PATH, SCALER_PATH, LAST_TRAIN_PATH
from .predictor import extract_features, load_model_and_scaler


def retry(max_attempts=3, delay=2, backoff=1.8, exceptions=(OperationalError, SQLAlchemyError, OSError)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            att = 0
            cur_delay = delay
            while att < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    att += 1
                    if att == max_attempts:
                        logger.error(f"Retry failed after {max_attempts} attempts | {func.__name__} | {str(e)}")
                        raise
                    logger.warning(f"Retry {att}/{max_attempts} | {func.__name__} | {str(e)}")
                    time.sleep(cur_delay)
                    cur_delay *= backoff
        return wrapper
    return decorator


@retry()
def train_model(db: Session):
    """Train the ML model using collected impression data"""
    try:
        # Import here to avoid circular imports
        from app.models import RecommendationImpression, FoodItem
        
        impressions = db.query(RecommendationImpression).all()
        n_imp = len(impressions)
        if n_imp < MIN_IMPRESSIONS:
            logger.info(f"Skip training — only {n_imp} impressions")
            return False, "not_enough_data"

        accepts = db.query(RecommendationImpression).filter_by(added=True).count()
        if accepts < MIN_ACCEPTS:
            logger.info(f"Skip training — only {accepts} accepts")
            return False, "too_few_accepts"

        # Cache foods to avoid repeated queries
        foods = {}
        for f in db.query(FoodItem).all():
            foods[f.food_id] = f

        X, y = [], []
        skipped = 0
        for imp in impressions:
            food = foods.get(imp.food_id)
            if not food:
                skipped += 1
                continue
            try:
                feat = extract_features(imp, food)
                X.append(feat)
                y.append(1 if imp.added else 0)
            except Exception as e:
                logger.warning(f"Skipped impression {imp.id} — feature extraction failed: {str(e)}")
                skipped += 1

        if len(X) < MIN_IMPRESSIONS // 2:
            logger.warning(f"Too few valid samples after skipping {skipped}")
            return False, "too_few_valid_samples"

        X = np.array(X)
        y = np.array(y)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        stratify = y if len(np.unique(y)) > 1 else None
        X_tr, X_te, y_tr, y_te = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=stratify
        )

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_tr, y_tr)

        auc = None
        if len(y_te) > 0 and len(np.unique(y_te)) > 1:
            preds = model.predict_proba(X_te)[:, 1]
            auc = roc_auc_score(y_te, preds)

        auc_str = f"{auc:.3f}" if auc else "n/a"
        logger.info(
            f"Model trained | n={len(X)} | accepts={sum(y)} | "
            f"auc={auc_str} | skipped={skipped}"
        )

        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)

        with open(LAST_TRAIN_PATH, "w") as f:
            f.write(datetime.now().isoformat())

        load_model_and_scaler()     # refresh globals

        # Push to GitHub
        try:
            from .git_push import push_model_to_github
            push_model_to_github(auc_score=auc, n_samples=len(X))
        except Exception as e:
            logger.warning(f"GitHub push failed (non-fatal): {e}")

        return True, "trained"

    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        return False, "training_error"


def should_retrain(db: Session) -> bool:
    """Check if model should be retrained based on time and data thresholds"""
    try:
        from app.models import RecommendationImpression
        
        if not os.path.exists(LAST_TRAIN_PATH):
            return db.query(RecommendationImpression).count() >= MIN_IMPRESSIONS

        with open(LAST_TRAIN_PATH, "r") as f:
            last_str = f.read().strip()
        last_time = datetime.fromisoformat(last_str)
        hours_elapsed = (datetime.now() - last_time).total_seconds() / 3600
        return hours_elapsed > MIN_HOURS_BETWEEN
    except Exception as e:
        logger.warning(f"should_retrain failed: {str(e)}")
        return False


def check_and_retrain_in_background(db: Session, user_id: str = None):
    """Background task to check and retrain model if needed"""
    try:
        if should_retrain(db):
            logger.info(f"Background retrain started (trigger: {user_id or 'system'})")
            success, reason = train_model(db)
            if success:
                logger.info("Background retrain completed successfully")
            else:
                logger.info(f"Background retrain skipped: {reason}")
    except Exception as e:
        logger.error(f"Background retrain task crashed: {str(e)}", exc_info=True)
