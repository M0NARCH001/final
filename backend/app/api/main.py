# app/api/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import json, math, difflib, logging

# DB and models
from backend.app.db.database import SessionLocal, engine
from backend.app.models import FoodItem, FoodLog, RDA, User  # import classes directly

# Routers
from backend.app.api import users as users_router
from backend.app.api import food_logs as food_logs_router

# Create tables if they don't exist
from backend.app.models import Base as ModelsBase
ModelsBase.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="NutriMate API (dev)")
logger = logging.getLogger("nutrimate")

# CORS - dev-friendly
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost:19006",
    "http://localhost:19000",
    "http://127.0.0.1:19000",
    "http://localhost:3000",
    # add other dev origins as needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: allow all; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
from backend.app.api import foods as foods_router
app.include_router(foods_router.router)
app.include_router(users_router.router)
app.include_router(food_logs_router.router)

# -----------------------
# DB dependency
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Request models
# -----------------------
class FoodLogIn(BaseModel):
    user_id: Optional[int] = None
    food_id: int
    quantity: float = 1.0
    unit: Optional[str] = None

class ReportRequest(BaseModel):
    user_id: Optional[int] = None
    date: Optional[str] = None
    food_logs: Optional[List[FoodLogIn]] = None
    life_stage: Optional[str] = "Adult Male"

class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    food_logs: Optional[List[FoodLogIn]] = None
    life_stage: Optional[str] = "Adult Male"
    strategy: Optional[str] = "greedy"

# -----------------------
# Nutrient keys
# -----------------------
NUTS = [
    "Calories_kcal", "Carbohydrates_g", "Protein_g", "Fats_g",
    "FreeSugar_g", "Fibre_g", "Sodium_mg", "Calcium_mg",
    "Iron_mg", "VitaminC_mg", "Folate_ug"
]

# -----------------------
# Helpers
# -----------------------
def compute_totals_from_logs(db: Session, logs: List[Dict]) -> Dict[str, float]:
    totals = {k: 0.0 for k in NUTS}
    for l in logs:
        food = db.query(FoodItem).filter(FoodItem.food_id == l["food_id"]).first()
        if not food:
            continue
        q = float(l.get("quantity", 1.0))
        for k in NUTS:
            val = getattr(food, k, None)
            if val is None:
                v = 0.0
            else:
                try:
                    v = float(val)
                except Exception:
                    v = 0.0
            totals[k] += v * q
    # round totals a bit for nicer output
    return {k: round(v, 4) for k, v in totals.items()}

def rda_row_to_dict(r: RDA):
    if not r:
        return {}
    out = {}
    for k in NUTS:
        v = getattr(r, k, None)
        try:
            out[k] = float(v) if v is not None else 0.0
        except Exception:
            out[k] = 0.0
    return out

# life-stage mapping / fuzzy match
LIFE_STAGE_ALIASES = {
    "adult male": "Males 19-30 y",
    "adult female": "Females 19-30 y",
    "male": "Males 19-30 y",
    "female": "Females 19-30 y",
    "adult": "Males 19-30 y"
}

def find_rda_row(db: Session, requested: str):
    if not requested:
        return (None, "none", None)

    rs = requested.strip()
    low = rs.lower()

    # alias
    if low in LIFE_STAGE_ALIASES:
        target = LIFE_STAGE_ALIASES[low]
        row = db.query(RDA).filter(RDA.life_stage == target).first()
        if row:
            return (row, "alias", target)

    # exact
    row = db.query(RDA).filter(RDA.life_stage == rs).first()
    if row:
        return (row, "exact", rs)

    # ci exact
    row = db.query(RDA).filter(func.lower(RDA.life_stage) == low).first()
    if row:
        return (row, "ci_exact", rs)

    # substring
    row = db.query(RDA).filter(RDA.life_stage.ilike(f"%{rs}%")).first()
    if row:
        return (row, "substring", row.life_stage)

    # token-based
    tokens = [t for t in low.split() if t.isalpha()]
    for t in tokens:
        row = db.query(RDA).filter(RDA.life_stage.ilike(f"%{t}%")).first()
        if row:
            return (row, "token", row.life_stage)

    # fuzzy
    all_rows = [r.life_stage for r in db.query(RDA).all()]
    matches = difflib.get_close_matches(rs, all_rows, n=1, cutoff=0.6)
    if matches:
        match = matches[0]
        row = db.query(RDA).filter(RDA.life_stage == match).first()
        if row:
            return (row, "fuzzy", match)

    return (None, "none", None)

# -----------------------
# Search endpoint
# -----------------------
@app.get("/foods")
def search_foods(query: Optional[str] = Query(None), limit: int = Query(10), db: Session = Depends(get_db)):
    q = db.query(FoodItem)
    if query:
        q = q.filter(FoodItem.food_name.ilike(f"%{query}%"))
    results = q.limit(limit).all()
    out = []
    for f in results:
        try:
            subs = json.loads(f.subcategories_json) if f.subcategories_json else []
        except Exception:
            subs = []
        out.append({
            "food_id": f.food_id,
            "food_name": f.food_name,
            "main_name": f.main_name,
            "subcategories": subs if subs else None,
            "source": f.source,
            "Calories_kcal": f.Calories_kcal,
            "Protein_g": f.Protein_g,
            "Carbohydrates_g": f.Carbohydrates_g,
            "Fats_g": f.Fats_g
        })
    return out

# -----------------------
# Health check
# -----------------------
@app.get("/health")
def health():
    return {"ok": True}

# -----------------------
# Add food log (simple)
# -----------------------
@app.post("/food-logs", status_code=201)
def add_food_log(payload: FoodLogIn, db: Session = Depends(get_db)):
    food = db.query(FoodItem).filter(FoodItem.food_id == payload.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    entry = FoodLog(
        user_id=payload.user_id,
        food_id=payload.food_id,
        quantity=payload.quantity,
        unit=payload.unit
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"ok": True, "log_id": entry.log_id}

# -----------------------
# Daily report
# -----------------------
@app.post("/reports/daily")
def daily_report(req: ReportRequest, db: Session = Depends(get_db)):
    # Build logs list
    logs = []
    if req.food_logs:
        for fl in req.food_logs:
            logs.append({"food_id": fl.food_id, "quantity": fl.quantity})
    else:
        if not req.user_id or not req.date:
            raise HTTPException(status_code=400, detail="Provide either food_logs or both user_id and date")
        try:
            qdate = datetime.strptime(req.date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD expected)")
        rows = db.query(FoodLog).filter(
            FoodLog.user_id == req.user_id,
            func.date(FoodLog.logged_at) == qdate
        ).all()
        for r in rows:
            logs.append({"food_id": r.food_id, "quantity": r.quantity})

    totals = compute_totals_from_logs(db, logs)

    rda_row, method, matched = find_rda_row(db, req.life_stage)
    if not rda_row:
        raise HTTPException(status_code=404, detail=f"No RDA found for '{req.life_stage}'.")

    targets = rda_row_to_dict(rda_row)

    # compare three major nutrients
    comparison = {}
    for k in ["Carbohydrates_g", "Protein_g", "Fibre_g"]:
        r = targets.get(k, 0.0)
        intake = totals.get(k, 0.0)
        percent = None
        if r and r != 0:
            percent = round((intake / r) * 100.0, 1)
        comparison[k] = {
            "intake": round(intake, 2),
            "rda": float(r),
            "percent": percent
        }

    low = [k for k, v in comparison.items() if v["percent"] is not None and v["percent"] < 90]
    high = [k for k, v in comparison.items() if v["percent"] is not None and v["percent"] > 110]

    return {
        "date": req.date or str(date.today()),
        "totals": totals,
        "rda_comparison": comparison,
        "flags": {"low": low, "high": high}
    }

# GET /reports/today?user_id=...
from fastapi import Query
from datetime import date

@app.get("/reports/today")
def report_today(user_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """
    Return today's totals and RDA comparison for a given user_id or empty totals if no logs.
    If user_id is not provided, return zero totals (useful for guest/testing).
    """
    # fetch today's logs if user_id provided
    logs = []
    if user_id:
        rows = db.query(FoodLog).filter(
            FoodLog.user_id == user_id,
            func.date(FoodLog.logged_at) == date.today()
        ).all()
        for r in rows:
            logs.append({"food_id": r.food_id, "quantity": r.quantity})

    totals = compute_totals_from_logs(db, logs)

    # default life_stage mapping if user not provided - we'll use Adult Male default
    life_stage = "Adult Male"
    # If you want to derive life_stage from User.profile later, do it.
    rda_row, method, matched = find_rda_row(db, life_stage)
    targets = rda_row_to_dict(rda_row) if rda_row else {}

    # build compact rda comparison for main nutrients
    comp = {}
    for k in ["Calories_kcal", "Carbohydrates_g", "Protein_g", "Fats_g"]:
        r = targets.get(k, 0.0)
        intake = totals.get(k, 0.0)
        percent = (intake / r * 100.0) if r and r != 0 else None
        comp[k] = {"intake": round(intake,2), "rda": float(r), "percent": round(percent,1) if percent is not None else None}

    return {"date": str(date.today()), "totals": totals, "rda_comparison": comp}

@app.get("/food-logs/today")
def food_logs_today(user_id: int = Query(...), db: Session = Depends(get_db)):
    """
    Return today's food logs for the user with expanded food info.
    """
    rows = db.query(FoodLog).filter(
        FoodLog.user_id == user_id,
        func.date(FoodLog.logged_at) == date.today()
    ).order_by(FoodLog.logged_at.desc()).all()

    out = []
    for r in rows:
        f = db.query(FoodItem).filter(FoodItem.food_id == r.food_id).first()
        out.append({
            "log_id": r.log_id,
            "food_id": r.food_id,
            "food_name": f.food_name if f else None,
            "quantity": r.quantity,
            "unit": r.unit,
            "calories": round((f.Calories_kcal or 0.0) * (r.quantity or 1.0), 2) if f else None,
            "logged_at": r.logged_at.isoformat()
        })
    return out

# -----------------------
# Recommendation utilities & generator
# -----------------------
def safe_get(food, key):
    try:
        v = getattr(food, key)
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0

def score_food(food, deficits, user_conditions=None):
    total_deficit = sum(v for v in deficits.values() if v > 0) or 1.0
    contribution = 0.0
    for k, deficit_val in deficits.items():
        if deficit_val <= 0:
            continue
        amount = safe_get(food, k)
        if amount <= 0:
            continue
        prop = min(1.0, amount / (deficit_val if deficit_val > 0 else 1.0))
        weight = (deficit_val / total_deficit)
        contribution += prop * weight

    raw_score = contribution
    sugar = safe_get(food, "FreeSugar_g")
    sodium = safe_get(food, "Sodium_mg")
    sugar_penalty = max(0.0, (sugar - 5.0) / 10.0)
    sodium_penalty = max(0.0, (sodium - 300.0) / 500.0)
    penalized = raw_score - (0.5 * sugar_penalty + 0.5 * sodium_penalty)
    cals = safe_get(food, "Calories_kcal") or 1.0
    density_factor = (cals / 100.0) + 1.0
    final_score = penalized / density_factor
    return max(final_score, -1.0)

def generate_recs(db, totals, targets, user=None, max_items=5, candidate_limit=3000):
    deficits = {k: max(0.0, targets.get(k, 0.0) - totals.get(k, 0.0)) for k in targets}
    if all(v <= 0 for v in deficits.values()):
        return []
    candidates = db.query(FoodItem).limit(candidate_limit).all()
    selected = []
    for _ in range(max_items):
        best = None
        best_score = -1e9
        for food in candidates:
            sc = score_food(food, deficits, user_conditions=(user.medical_conditions if user else None))
            if sc > best_score:
                best_score = sc
                best = food
        if best is None or best_score <= 0:
            break
        servings = 1.0
        impact = {k: safe_get(best, k) * servings for k in deficits.keys()}
        selected.append({
            "food_id": best.food_id,
            "food_name": best.food_name,
            "servings": servings,
            "score": round(best_score, 4),
            "estimated_impact": {k: round(v, 2) for k, v in impact.items()}
        })
        for k in deficits:
            deficits[k] = max(0.0, deficits[k] - impact.get(k, 0.0))
        candidates = [c for c in candidates if c.food_id != best.food_id]
        if sum(deficits.values()) <= 0.1:
            break
    return selected

@app.post("/recommendations/generate")
def recommendations_generate(req: RecommendationRequest, db: Session = Depends(get_db)):
    logs = []
    if req.food_logs:
        for fl in req.food_logs:
            logs.append({"food_id": fl.food_id, "quantity": fl.quantity})

    totals = compute_totals_from_logs(db, logs)

    rda_row, method, matched = find_rda_row(db, req.life_stage)
    if not rda_row:
        return {"totals": totals, "targets": {}, "recommendations": []}

    targets = rda_row_to_dict(rda_row)

    # load user if provided (to pass medical conditions etc.)
    user_obj = None
    if req.user_id:
        user_obj = db.query(User).filter(User.user_id == req.user_id).first()

    recs = generate_recs(db, totals, targets, user=user_obj, max_items=5)

    return {
        "totals": totals,
        "targets": targets,
        "recommendations": recs
    }