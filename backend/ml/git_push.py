# ml/git_push.py
"""
Auto-push trained ML models to GitHub repository.
Requires GITHUB_TOKEN environment variable with 'repo' scope.
"""
import os
import base64
import json
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .config import logger, MODEL_PATH, SCALER_PATH

# ─── Configuration ─────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "veerendravirothi/Nutrimate-v2")  # owner/repo
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
MODEL_REPO_PATH = "backend/ml_artifacts"

MAX_FILE_SIZE_MB = 90  # Skip if file > 90 MB (GitHub limit is 100 MB)


def _github_api(method: str, endpoint: str, data: dict = None) -> dict:
    """Make authenticated GitHub API request"""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "NutriMate-ML"
    }
    
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        logger.error(f"GitHub API error {e.code}: {error_body}")
        raise
    except URLError as e:
        logger.error(f"GitHub network error: {e.reason}")
        raise


def _get_file_sha(file_path: str) -> str | None:
    """Get existing file SHA (needed for updates)"""
    try:
        resp = _github_api("GET", f"/repos/{GITHUB_REPO}/contents/{file_path}?ref={GITHUB_BRANCH}")
        return resp.get("sha")
    except HTTPError as e:
        if e.code == 404:
            return None  # File doesn't exist yet
        raise


def _upload_file(local_path: str, repo_path: str, commit_msg: str) -> bool:
    """Upload a single file to GitHub"""
    if not os.path.exists(local_path):
        logger.warning(f"File not found: {local_path}")
        return False
    
    # Size check
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        logger.error(f"File too large ({size_mb:.1f} MB > {MAX_FILE_SIZE_MB} MB): {local_path}")
        return False
    
    # Read and encode file
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    
    # Check if file exists (need SHA for update)
    sha = _get_file_sha(repo_path)
    
    data = {
        "message": commit_msg,
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha  # Required for updating existing file
    
    _github_api("PUT", f"/repos/{GITHUB_REPO}/contents/{repo_path}", data)
    logger.info(f"Uploaded to GitHub: {repo_path} ({size_mb:.2f} MB)")
    return True


def push_model_to_github(auc_score: float = None, n_samples: int = None) -> bool:
    """
    Push trained model files to GitHub.
    Call this after successful training.
    
    Returns True if successful, False otherwise.
    """
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set — skipping GitHub push")
        return False
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    auc_str = f"AUC={auc_score:.3f}" if auc_score else "AUC=n/a"
    samples_str = f"n={n_samples}" if n_samples else ""
    
    commit_msg = f"🤖 ML model update | {timestamp} | {auc_str} {samples_str}".strip()
    
    success = True
    
    # Upload model file
    try:
        if not _upload_file(MODEL_PATH, f"{MODEL_REPO_PATH}/rf_recommender.joblib", commit_msg):
            success = False
    except Exception as e:
        logger.error(f"Failed to upload model: {e}")
        success = False
    
    # Upload scaler file
    try:
        if not _upload_file(SCALER_PATH, f"{MODEL_REPO_PATH}/scaler.joblib", commit_msg):
            success = False
    except Exception as e:
        logger.error(f"Failed to upload scaler: {e}")
        success = False
    
    return success
