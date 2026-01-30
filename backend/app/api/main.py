# app/api/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import json, math, difflib, logging
from app.api.auth import router as auth_router
from app.api.plan import router as plan_router
from app.api.goals import router as goals_router
from pydantic import BaseModel

# DB and models
from app.db.database import SessionLocal, engine
from app.models import FoodItem, FoodLog, RDA, User  # import classes directly

# Routers
from app.api import users as users_router
from app.api import food_logs as food_logs_router

# Create tables if they don't exist
from app.models import Base as ModelsBase
ModelsBase.metadata.create_all(bind=engine)

class ComputeRequest(BaseModel):
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str
    target_weight: float | None = None
    days: int | None = None

# FastAPI app
app = FastAPI(title="NutriMate API (dev)")
app.include_router(auth_router)
app.include_router(plan_router)
app.include_router(goals_router)
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
from app.api import foods as foods_router
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
    food_logs: list = []
    daily_calories: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    carbs_g: float | None = None

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
def get_today_logs(user_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(FoodLog, FoodItem)
        .join(FoodItem, FoodItem.food_id == FoodLog.food_id)
        .filter(FoodLog.user_id == user_id)
        .all()
    )

    results = []

    for log, food in logs:
        qty = log.quantity or 1

        results.append({
            "log_id": log.log_id,
            "food_id": food.food_id,
            "food_name": food.food_name,
            "quantity": qty,
            "Calories_kcal": round((food.Calories_kcal or 0) * qty, 2),
            "Protein_g": round((food.Protein_g or 0) * qty, 2),
            "Carbohydrates_g": round((food.Carbohydrates_g or 0) * qty, 2),
            "Fats_g": round((food.Fats_g or 0) * qty, 2),
        })

    return results

# -----------------------
# Recommendation utilities & generator
# -----------------------
def safe_get(food, k):
    v = getattr(food, k, 0.0)
    return float(v or 0.0)

def score_food(f, deficits):
    kcal = f.Calories_kcal or 0
    protein = f.Protein_g or 0
    fat = f.Fats_g or 0
    carbs = f.Carbohydrates_g or 0
    # clamp negative deficits to zero
    d_cal = max(deficits.get("Calories_kcal", 0), 0)
    d_pro = max(deficits.get("Protein_g", 0), 0)
    d_car = max(deficits.get("Carbohydrates_g", 0), 0)
    d_fat = max(deficits.get("Fats_g", 0), 0)
    score = 0

    # calories small weight
    score += min(kcal, d_cal) * 0.2

    # protein is king
    score += min(protein, d_pro) * 4

    # carbs moderate
    score += min(carbs, d_car) * 1

    # fats low
    score += min(fat, d_fat) * 0.5

    if fat > 20:
        score -= fat * 2

    name = (f.food_name or "").lower()
    # hard penalty for sweets / desserts
    junk_words = ["burfi", "laddu", "halwa", "icing", "cake", "sweet", "pudding", "pastry", "cookie"]
    if any(j in name for j in junk_words):
        score -= 80

    preferred = ["paneer","egg","dal","chicken","curd","rice","roti","channa"]
    if any(p in name for p in preferred):
        score += 20

    return score


def generate_recs(db, totals, targets, user=None, max_items=5):

    # targets now come directly from compute endpoint
    # expected keys:
    # Calories_kcal, Protein_g, Fats_g, Carbohydrates_g

    deficits = {
        "Calories_kcal": max(0, targets["Calories_kcal"] - totals.get("Calories_kcal", 0)),
        "Protein_g": max(0, targets["Protein_g"] - totals.get("Protein_g", 0)),
        "Fats_g": max(0, targets["Fats_g"] - totals.get("Fats_g", 0)),
        "Carbohydrates_g": max(0, targets["Carbohydrates_g"] - totals.get("Carbohydrates_g", 0)),
    }

    print("DEFICITS:", deficits)

    foods = db.query(FoodItem).all()

    # ---- basic junk filter ----
    clean = []

    for f in foods:
        kcal = f.Calories_kcal or 0
        protein = f.Protein_g or 0
        fat = f.Fats_g or 0
        carbs = f.Carbohydrates_g or 0

    # remove ultra-empty + sugar bombs
        # remove ultra-empty
        if kcal < 40:
            continue

        # remove sugar bombs
        if carbs > 40 and protein < 5:
            continue

        # remove pure fat junk
        if fat > 20 and protein < 5:
            continue

        clean.append(f)

    foods = clean

    scored = []

    for f in foods:
        score = score_food(f, deficits)
        if score > 0:
            scored.append((score, f))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for s, f in scored[:max_items]:
        results.append({
            "food_id": f.food_id,
            "food_name": f.food_name,
            "score": round(float(s), 2)
        })

    return results

@app.post("/recommendations/generate")
def recommendations_generate(req: RecommendationRequest, db: Session = Depends(get_db)):

    logs = []
    for fl in req.food_logs:
        logs.append({
            "food_id": fl["food_id"],
            "quantity": fl.get("quantity", 1)
        })

    totals = compute_totals_from_logs(db, logs)

    targets = {
        "Calories_kcal": req.daily_calories or 0,
        "Protein_g": req.protein_g or 0,
        "Fats_g": req.fat_g or 0,
        "Carbohydrates_g": req.carbs_g or 0,
    }

    recs = generate_recs(db, totals, targets, max_items=5)

    return {
        "totals": totals,
        "targets": targets,
        "recommendations": recs
    }


app.include_router(auth_router)

@app.post("/compute")
def compute_targets(req: ComputeRequest):

    # --- BMR (Mifflin St Jeor) ---
    if req.gender.lower() == "male":
        bmr = 10 * req.weight_kg + 6.25 * req.height_cm - 5 * req.age + 5
    else:
        bmr = 10 * req.weight_kg + 6.25 * req.height_cm - 5 * req.age - 161

    # --- Activity multiplier ---
    activity_map = {
        "Low": 1.2,
        "Moderate": 1.55,
        "High": 1.75,
    }

    multiplier = activity_map.get(req.activity_level, 1.55)
    tdee = bmr * multiplier

    daily_calories = tdee

    # --- Goal adjustments ---
    if req.goal == "Weight Loss" and req.target_weight:
        diff = req.weight_kg - req.target_weight
        total_deficit = diff * 7700
        daily_calories = tdee - (total_deficit / max(req.days or 60, 30))

    if req.goal == "Weight Gain" and req.target_weight:
        diff = req.target_weight - req.weight_kg
        total_surplus = diff * 7700
        daily_calories = tdee + (total_surplus / max(req.days or 60, 30))

    # --- Safety clamps ---
    daily_calories = max(1200, daily_calories)

    # --- Macros ---
    protein_g = req.weight_kg * (2 if req.goal == "Weight Gain" else 1.6)
    fat_g = (daily_calories * 0.25) / 9
    carbs_g = (daily_calories - protein_g * 4 - fat_g * 9) / 4

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_calories": round(daily_calories),
        "protein_g": round(protein_g),
        "fat_g": round(fat_g),
        "carbs_g": round(carbs_g),
    }