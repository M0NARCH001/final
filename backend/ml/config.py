# ml/config.py
import logging
import os
from logging.handlers import RotatingFileHandler

# ─── Paths & Constants ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use Railway persistent volume if available, otherwise local
RAILWAY_VOLUME = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
if RAILWAY_VOLUME:
    MODEL_DIR = os.path.join(RAILWAY_VOLUME, "ml_artifacts")
else:
    MODEL_DIR = os.path.join(BASE_DIR, "ml_artifacts")

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH      = os.path.join(MODEL_DIR, "rf_recommender.joblib")
SCALER_PATH     = os.path.join(MODEL_DIR, "scaler.joblib")
LAST_TRAIN_PATH = os.path.join(MODEL_DIR, "last_train.txt")

MIN_IMPRESSIONS     = 80
MIN_ACCEPTS         = 15
MIN_HOURS_BETWEEN   = 6

# ─── Logging Setup ────────────────────────────────────────────────────────────
def setup_logging(log_level=logging.INFO, log_file=None):
    logger = logging.getLogger("nutrimate.ml")
    logger.setLevel(log_level)
    logger.propagate = False

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File (optional)
    if log_file:
        log_path = os.path.join(BASE_DIR, log_file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# Global logger — import from anywhere as:
# from ml.config import logger
logger = setup_logging(
    log_level=logging.INFO,
    log_file="logs/ml.log"   # comment out or set to None to disable file logging
)
