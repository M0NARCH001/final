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
from app.models import FoodItem, FoodLog, RDA, User, RecommendationImpression  # import classes directly

# ML components for hybrid recommendations
try:
    from ml.config import logger as ml_logger
    from ml.predictor import load_model_and_scaler, get_hybrid_score
    from ml.trainer import check_and_retrain_in_background
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    ml_logger = None

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
    # Health conditions for dietary adjustments
    has_diabetes: bool = False
    has_hypertension: bool = False
    has_pcos: bool = False
    muscle_gain_focus: bool = False
    heart_health_focus: bool = False

# FastAPI app
from contextlib import asynccontextmanager
from fastapi import BackgroundTasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML model if available
    if ML_AVAILABLE:
        load_model_and_scaler()
        ml_logger.info("NutriMate API started with ML support")
    yield

app = FastAPI(title="NutriMate API (dev)", lifespan=lifespan)
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
# Database Migration (run once to add missing columns)
# -----------------------
from sqlalchemy import text

@app.get("/migrate-db")
def migrate_database():
    """Add missing columns to existing tables (safe to run multiple times)"""
    results = []
    
    try:
        with engine.connect() as conn:
            # Check if username column exists in user table
            result = conn.execute(text("PRAGMA table_info(user)")).fetchall()
            columns = [row[1] for row in result]
            
            if "username" not in columns:
                conn.execute(text("ALTER TABLE user ADD COLUMN username TEXT"))
                results.append("Added 'username' column to user table")
            else:
                results.append("'username' column already exists")
            
            conn.commit()
        
        return {"status": "success", "changes": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    # Micronutrient targets
    fiber_g: float = 25
    sugar_limit_g: float = 50
    sodium_limit_mg: float = 2300
    calcium_mg: float = 1000
    iron_mg: float = 18
    vitaminC_mg: float = 90
    folate_ug: float = 400
    # Health conditions for scoring adjustments
    has_diabetes: bool = False
    has_hypertension: bool = False
    has_pcos: bool = False
    muscle_gain_focus: bool = False
    heart_health_focus: bool = False

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

@app.get("/")
def read_root():
    return {
        "message": "Welcome to NutriMate v2 API",
        "docs": "/docs",
        "health": "/health",
        "mobile_status": "Online"
    }

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
            # Macros
            "Calories_kcal": round((food.Calories_kcal or 0) * qty, 2),
            "Protein_g": round((food.Protein_g or 0) * qty, 2),
            "Carbohydrates_g": round((food.Carbohydrates_g or 0) * qty, 2),
            "Fats_g": round((food.Fats_g or 0) * qty, 2),
            # Micronutrients
            "FreeSugar_g": round((food.FreeSugar_g or 0) * qty, 2),
            "Fibre_g": round((food.Fibre_g or 0) * qty, 2),
            "Sodium_mg": round((food.Sodium_mg or 0) * qty, 2),
            "Calcium_mg": round((food.Calcium_mg or 0) * qty, 2),
            "Iron_mg": round((food.Iron_mg or 0) * qty, 2),
            "VitaminC_mg": round((food.VitaminC_mg or 0) * qty, 2),
            "Folate_ug": round((food.Folate_ug or 0) * qty, 2),
        })

    return results

# -----------------------
# Warning Generation
# -----------------------
def generate_warnings(totals: dict, targets: dict) -> list:
    """Generate warnings based on nutrient intake vs targets."""
    warnings = []
    
    # High sugar warning
    sugar_intake = totals.get("FreeSugar_g", 0)
    sugar_limit = targets.get("sugar_limit_g", 50)
    if sugar_intake > sugar_limit:
        excess = round(sugar_intake - sugar_limit, 1)
        warnings.append({
            "type": "high_sugar",
            "severity": "warning",
            "message": f"High sugar intake today (+{excess}g above {sugar_limit}g limit)"
        })
    
    # High sodium warning
    sodium_intake = totals.get("Sodium_mg", 0)
    sodium_limit = targets.get("sodium_limit_mg", 2300)
    if sodium_intake > sodium_limit:
        excess = round(sodium_intake - sodium_limit, 0)
        warnings.append({
            "type": "high_sodium",
            "severity": "warning",
            "message": f"Sodium is high (+{int(excess)}mg above limit) — consider lower-salt options tomorrow"
        })
    
    # Low fiber warning (< 70% of target)
    fiber_intake = totals.get("Fibre_g", 0)
    fiber_target = targets.get("fiber_g", 25)
    if fiber_target > 0 and fiber_intake < fiber_target * 0.70:
        warnings.append({
            "type": "low_fiber",
            "severity": "info",
            "message": f"Low fiber intake ({round(fiber_intake, 1)}g of {fiber_target}g) — add whole grains, vegetables, or legumes"
        })
    
    # Low iron warning (< 60% of target)
    iron_intake = totals.get("Iron_mg", 0)
    iron_target = targets.get("iron_mg", 18)
    if iron_target > 0 and iron_intake < iron_target * 0.60:
        warnings.append({
            "type": "low_iron",
            "severity": "info",
            "message": f"Low iron intake — consider spinach, lentils, or fortified foods"
        })
    
    # Low calcium warning (< 60% of target)
    calcium_intake = totals.get("Calcium_mg", 0)
    calcium_target = targets.get("calcium_mg", 1000)
    if calcium_target > 0 and calcium_intake < calcium_target * 0.60:
        warnings.append({
            "type": "low_calcium",
            "severity": "info",
            "message": f"Low calcium — consider dairy, fortified foods, or leafy greens"
        })
    
    # Low vitamin C warning (< 60% of target)
    vitc_intake = totals.get("VitaminC_mg", 0)
    vitc_target = targets.get("vitaminC_mg", 90)
    if vitc_target > 0 and vitc_intake < vitc_target * 0.60:
        warnings.append({
            "type": "low_vitaminC",
            "severity": "info",
            "message": f"Low vitamin C — add citrus fruits, peppers, or guava"
        })
    
    return warnings

# -----------------------
# Daily Summary Endpoint
# -----------------------
class DailySummaryRequest(BaseModel):
    user_id: int
    # Targets from frontend (computed via /compute)
    daily_calories: float = 2000
    protein_g: float = 100
    fat_g: float = 60
    carbs_g: float = 250
    fiber_g: float = 25
    sugar_limit_g: float = 50
    sodium_limit_mg: float = 2300
    calcium_mg: float = 1000
    iron_mg: float = 18
    vitaminC_mg: float = 90
    folate_ug: float = 400

@app.post("/daily-summary")
def daily_summary(req: DailySummaryRequest, db: Session = Depends(get_db)):
    """Get today's nutrient totals, progress vs targets, and warnings."""
    
    # Fetch today's logs
    logs_rows = (
        db.query(FoodLog, FoodItem)
        .join(FoodItem, FoodItem.food_id == FoodLog.food_id)
        .filter(FoodLog.user_id == req.user_id)
        .filter(func.date(FoodLog.logged_at) == date.today())
        .all()
    )
    
    # Compute totals
    totals = {k: 0.0 for k in NUTS}
    for log, food in logs_rows:
        qty = log.quantity or 1
        for k in NUTS:
            val = getattr(food, k, None)
            if val is not None:
                try:
                    totals[k] += float(val) * qty
                except:
                    pass
    totals = {k: round(v, 2) for k, v in totals.items()}
    
    # Build targets dict
    targets = {
        "Calories_kcal": req.daily_calories,
        "Protein_g": req.protein_g,
        "Fats_g": req.fat_g,
        "Carbohydrates_g": req.carbs_g,
        "fiber_g": req.fiber_g,
        "sugar_limit_g": req.sugar_limit_g,
        "sodium_limit_mg": req.sodium_limit_mg,
        "calcium_mg": req.calcium_mg,
        "iron_mg": req.iron_mg,
        "vitaminC_mg": req.vitaminC_mg,
        "folate_ug": req.folate_ug,
    }
    
    # Generate warnings
    warnings = generate_warnings(totals, targets)
    
    # Calculate progress percentages for macros
    progress = {}
    for k in ["Calories_kcal", "Protein_g", "Fats_g", "Carbohydrates_g"]:
        target_val = targets.get(k, 0)
        intake = totals.get(k, 0)
        pct = round((intake / target_val * 100), 1) if target_val > 0 else 0
        progress[k] = {"intake": intake, "target": target_val, "percent": pct}
    
    # Add micronutrient progress
    micro_map = {
        "Fibre_g": "fiber_g",
        "Sodium_mg": "sodium_limit_mg",
        "Calcium_mg": "calcium_mg",
        "Iron_mg": "iron_mg",
        "VitaminC_mg": "vitaminC_mg",
        "Folate_ug": "folate_ug",
    }
    for total_key, target_key in micro_map.items():
        target_val = targets.get(target_key, 0)
        intake = totals.get(total_key, 0)
        pct = round((intake / target_val * 100), 1) if target_val > 0 else 0
        progress[total_key] = {"intake": intake, "target": target_val, "percent": pct}
    
    return {
        "date": str(date.today()),
        "totals": totals,
        "targets": targets,
        "progress": progress,
        "warnings": warnings,
        "warnings_count": len(warnings),
    }

# -----------------------
# Recommendation utilities & generator
# -----------------------
def safe_get(food, k):
    v = getattr(food, k, 0.0)
    return float(v or 0.0)

def score_food(f, deficits, conditions=None):
    """
    Enhanced food scoring with micronutrient bonuses and condition-based penalties.
    Returns (score, reasons_list) tuple.
    """
    conditions = conditions or {}
    kcal = f.Calories_kcal or 0
    protein = f.Protein_g or 0
    fat = f.Fats_g or 0
    carbs = f.Carbohydrates_g or 0
    fiber = f.Fibre_g or 0
    sugar = f.FreeSugar_g or 0
    sodium = f.Sodium_mg or 0
    iron = f.Iron_mg or 0
    calcium = f.Calcium_mg or 0
    vitc = f.VitaminC_mg or 0
    
    # clamp negative deficits to zero
    d_cal = max(deficits.get("Calories_kcal", 0), 0)
    d_pro = max(deficits.get("Protein_g", 0), 0)
    d_car = max(deficits.get("Carbohydrates_g", 0), 0)
    d_fat = max(deficits.get("Fats_g", 0), 0)
    d_fiber = max(deficits.get("Fibre_g", 0), 0)
    d_iron = max(deficits.get("Iron_mg", 0), 0)
    d_calcium = max(deficits.get("Calcium_mg", 0), 0)
    d_vitc = max(deficits.get("VitaminC_mg", 0), 0)
    
    score = 0
    reasons = []

    # --- Macronutrient scoring ---
    # calories small weight
    score += min(kcal, d_cal) * 0.2

    # protein is king
    if protein > 10 and d_pro > 0:
        protein_score = min(protein, d_pro) * 4
        score += protein_score
        if protein > 15:
            reasons.append("High protein")

    # carbs moderate
    score += min(carbs, d_car) * 1

    # fats low
    score += min(fat, d_fat) * 0.5

    # --- Micronutrient bonuses ---
    # High fiber bonus (+10)
    if fiber >= 3:
        score += 10
        if fiber >= 5:
            reasons.append("High fiber")
    
    # Low sugar bonus (+8)
    if sugar < 5:
        score += 8
        if sugar < 2:
            reasons.append("Low sugar")
    
    # Low sodium bonus (+5)
    if sodium < 200:
        score += 5
        if sodium < 100:
            reasons.append("Low sodium")
    
    # Micronutrient deficit addressing
    if d_iron > 0 and iron > 2:
        score += min(iron, d_iron) * 2
        if iron > 3:
            reasons.append("Good iron source")
    
    if d_calcium > 0 and calcium > 50:
        score += min(calcium / 50, d_calcium / 50) * 3
        if calcium > 100:
            reasons.append("Good calcium source")
    
    if d_vitc > 0 and vitc > 10:
        score += min(vitc, d_vitc) * 0.5
        if vitc > 20:
            reasons.append("Rich in Vitamin C")

    # --- Penalties ---
    if fat > 20:
        score -= fat * 2

    name = (f.food_name or "").lower()
    # hard penalty for sweets / desserts
    junk_words = ["burfi", "laddu", "halwa", "icing", "cake", "sweet", "pudding", "pastry", "cookie"]
    if any(j in name for j in junk_words):
        score -= 80

    # --- Condition-based penalties ---
    # Diabetes: penalize high carb foods
    if conditions.get("has_diabetes") or conditions.get("has_pcos"):
        if carbs > 30:
            score -= 30
        if sugar > 10:
            score -= 25
    
    # Hypertension: penalize high sodium
    if conditions.get("has_hypertension") or conditions.get("heart_health_focus"):
        if sodium > 400:
            score -= 25
        elif sodium > 200:
            score -= 10

    # --- Preferred foods bonus ---
    preferred = ["paneer","egg","dal","chicken","curd","rice","roti","channa","fish","tofu"]
    if any(p in name for p in preferred):
        score += 20

    return (score, reasons)


def generate_recs(db, totals, targets, conditions=None, max_items=5):
    """
    Generate food recommendations with reasons and portion suggestions.
    """
    conditions = conditions or {}
    
    # Build deficits including micronutrients
    deficits = {
        "Calories_kcal": max(0, targets.get("Calories_kcal", 0) - totals.get("Calories_kcal", 0)),
        "Protein_g": max(0, targets.get("Protein_g", 0) - totals.get("Protein_g", 0)),
        "Fats_g": max(0, targets.get("Fats_g", 0) - totals.get("Fats_g", 0)),
        "Carbohydrates_g": max(0, targets.get("Carbohydrates_g", 0) - totals.get("Carbohydrates_g", 0)),
        "Fibre_g": max(0, targets.get("fiber_g", 25) - totals.get("Fibre_g", 0)),
        "Iron_mg": max(0, targets.get("iron_mg", 18) - totals.get("Iron_mg", 0)),
        "Calcium_mg": max(0, targets.get("calcium_mg", 1000) - totals.get("Calcium_mg", 0)),
        "VitaminC_mg": max(0, targets.get("vitaminC_mg", 90) - totals.get("VitaminC_mg", 0)),
    }

    logger.info(f"DEFICITS: {deficits}")

    foods = db.query(FoodItem).all()

    # ---- basic junk filter ----
    clean = []

    for f in foods:
        kcal = f.Calories_kcal or 0
        protein = f.Protein_g or 0
        fat = f.Fats_g or 0
        carbs = f.Carbohydrates_g or 0
        sugar = f.FreeSugar_g or 0

        # remove ultra-empty
        if kcal < 40:
            continue

        # remove sugar bombs (unless low cal)
        if carbs > 40 and protein < 5 and sugar > 15:
            continue

        # remove pure fat junk
        if fat > 20 and protein < 5:
            continue
        
        # For diabetes, skip very high carb items
        if (conditions.get("has_diabetes") or conditions.get("has_pcos")) and carbs > 50:
            continue

        clean.append(f)

    foods = clean

    scored = []

    for rank, f in enumerate(foods):
        rule_score, reasons = score_food(f, deficits, conditions)
        
        # Try hybrid scoring if ML is available
        if ML_AVAILABLE:
            hybrid = get_hybrid_score(f, deficits, rule_score, rank)
            final_score = hybrid if hybrid is not None else rule_score
        else:
            final_score = rule_score
        
        if final_score > 0:
            scored.append((final_score, rule_score, f, reasons, rank))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for s, rule_score, f, reasons, rank in scored[:max_items]:
        # Calculate suggested portion based on remaining calorie deficit
        kcal = f.Calories_kcal or 100
        remaining_cal = deficits.get("Calories_kcal", 500)
        suggested_portion_g = min(200, max(50, round(remaining_cal / (kcal / 100) * 100 / 4)))
        
        # Build reason string
        if reasons:
            reason_str = ", ".join(reasons[:3])  # Max 3 reasons
        else:
            reason_str = "Helps meet your nutritional targets"
        
        results.append({
            "food_id": f.food_id,
            "food_name": f.food_name,
            "score": round(float(s), 2),
            "reason": reason_str,
            "suggested_portion_g": suggested_portion_g,
            # Include nutrient highlights
            "nutrients": {
                "Calories_kcal": round(f.Calories_kcal or 0, 1),
                "Protein_g": round(f.Protein_g or 0, 1),
                "Fibre_g": round(f.Fibre_g or 0, 1),
                "FreeSugar_g": round(f.FreeSugar_g or 0, 1),
            }
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
        "fiber_g": req.fiber_g,
        "sugar_limit_g": req.sugar_limit_g,
        "sodium_limit_mg": req.sodium_limit_mg,
        "calcium_mg": req.calcium_mg,
        "iron_mg": req.iron_mg,
        "vitaminC_mg": req.vitaminC_mg,
        "folate_ug": req.folate_ug,
    }
    
    conditions = {
        "has_diabetes": req.has_diabetes,
        "has_hypertension": req.has_hypertension,
        "has_pcos": req.has_pcos,
        "muscle_gain_focus": req.muscle_gain_focus,
        "heart_health_focus": req.heart_health_focus,
    }

    recs = generate_recs(db, totals, targets, conditions=conditions, max_items=5)

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

    # --- Base protein calculation ---
    base_protein_mult = 1.6
    if req.goal == "Weight Gain":
        base_protein_mult = 2.0
    if req.muscle_gain_focus:
        base_protein_mult = 2.2  # Higher for muscle focus
    
    protein_g = req.weight_kg * base_protein_mult

    # --- Condition-based macro adjustments ---
    # Default carb percentage: ~50% of calories
    carb_percent = 0.50
    
    # Diabetes/PCOS: lower carbs to ~40%
    if req.has_diabetes or req.has_pcos:
        carb_percent = 0.40
    
    # Fat: 25% default, 30% for heart health (healthy fats emphasis)
    fat_percent = 0.25
    if req.heart_health_focus:
        fat_percent = 0.30
    
    fat_g = (daily_calories * fat_percent) / 9
    
    # Carbs: fill remaining after protein and fat
    protein_cal = protein_g * 4
    fat_cal = fat_g * 9
    remaining_cal = daily_calories - protein_cal - fat_cal
    carbs_g = max(remaining_cal / 4, 50)  # Minimum 50g carbs

    # --- Micronutrient targets (RDA-based) ---
    # Sugar limit: WHO recommends < 10% of calories, stricter for diabetes
    sugar_limit_g = round((daily_calories * 0.10) / 4)  # ~10% of calories
    if req.has_diabetes or req.has_pcos:
        sugar_limit_g = 25  # Stricter: ~25g max for blood sugar control
    
    # Sodium: 2300mg default, 2000mg for hypertension/heart health
    sodium_limit_mg = 2300
    if req.has_hypertension or req.heart_health_focus:
        sodium_limit_mg = 2000
    
    # Fiber: 25-30g based on gender (ICMR/USDA)
    fiber_g = 30 if req.gender.lower() == "male" else 25
    
    # Iron: gender-based RDA
    iron_mg = 8 if req.gender.lower() == "male" else 18
    
    # Calcium: 1000mg for adults (ICMR)
    calcium_mg = 1000
    
    # Vitamin C: 90mg male, 75mg female (RDA)
    vitaminC_mg = 90 if req.gender.lower() == "male" else 75
    
    # Folate: 400mcg adults (RDA)
    folate_ug = 400

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_calories": round(daily_calories),
        "protein_g": round(protein_g),
        "fat_g": round(fat_g),
        "carbs_g": round(carbs_g),
        # Micronutrient targets
        "fiber_g": fiber_g,
        "sugar_limit_g": sugar_limit_g,
        "sodium_limit_mg": sodium_limit_mg,
        "calcium_mg": calcium_mg,
        "iron_mg": iron_mg,
        "vitaminC_mg": vitaminC_mg,
        "folate_ug": folate_ug,
        # Echo conditions for frontend reference
        "conditions": {
            "has_diabetes": req.has_diabetes,
            "has_hypertension": req.has_hypertension,
            "has_pcos": req.has_pcos,
            "muscle_gain_focus": req.muscle_gain_focus,
            "heart_health_focus": req.heart_health_focus,
        }
    }


# -----------------------
# ML Impression Logging (for training data)
# -----------------------
class ImpressionLogRequest(BaseModel):
    user_id: int
    food_id: int
    deficits: dict = {}
    rank: int
    rule_score: float = 0.0
    added: bool = False

class ImpressionBatchRequest(BaseModel):
    impressions: List[ImpressionLogRequest]

@app.post("/impressions/log")
def log_impression(req: ImpressionLogRequest, db: Session = Depends(get_db)):
    """Log a single recommendation impression for ML training."""
    impression = RecommendationImpression(
        user_id=req.user_id,
        food_id=req.food_id,
        deficits=json.dumps(req.deficits),
        rank=req.rank,
        rule_score=req.rule_score,
        added=req.added,
        added_at=datetime.now() if req.added else None
    )
    db.add(impression)
    db.commit()
    return {"status": "logged", "id": impression.id}

@app.post("/impressions/batch")
def log_impressions_batch(req: ImpressionBatchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Log multiple impressions at once (when recommendations are shown)."""
    ids = []
    for imp in req.impressions:
        impression = RecommendationImpression(
            user_id=imp.user_id,
            food_id=imp.food_id,
            deficits=json.dumps(imp.deficits),
            rank=imp.rank,
            rule_score=imp.rule_score,
            added=imp.added,
            added_at=datetime.now() if imp.added else None
        )
        db.add(impression)
        db.flush()
        ids.append(impression.id)
    db.commit()
    
    # Trigger background retraining check
    if ML_AVAILABLE:
        background_tasks.add_task(check_and_retrain_in_background, db, str(req.impressions[0].user_id if req.impressions else "system"))
    
    return {"status": "logged", "count": len(ids), "ids": ids}

@app.put("/impressions/{impression_id}/mark-added")
def mark_impression_added(impression_id: int, db: Session = Depends(get_db)):
    """Mark an impression as added (user logged food from recommendation)."""
    imp = db.query(RecommendationImpression).filter_by(id=impression_id).first()
    if not imp:
        raise HTTPException(status_code=404, detail="Impression not found")
    imp.added = True
    imp.added_at = datetime.now()
    db.commit()
    return {"status": "updated", "id": impression_id}

@app.get("/ml/status")
def ml_status(db: Session = Depends(get_db)):
    """Get ML model status and training statistics."""
    import os
    from ml.config import MODEL_PATH, LAST_TRAIN_PATH
    
    total_impressions = db.query(RecommendationImpression).count()
    total_accepts = db.query(RecommendationImpression).filter_by(added=True).count()
    
    model_exists = os.path.exists(MODEL_PATH)
    last_trained = None
    if os.path.exists(LAST_TRAIN_PATH):
        with open(LAST_TRAIN_PATH, "r") as f:
            last_trained = f.read().strip()
    
    return {
        "ml_available": ML_AVAILABLE,
        "model_exists": model_exists,
        "last_trained": last_trained,
        "total_impressions": total_impressions,
        "total_accepts": total_accepts,
        "accept_rate": round(total_accepts / total_impressions * 100, 1) if total_impressions > 0 else 0
    }