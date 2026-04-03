# app/api/food_logs.py

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.database import SessionLocal
from app.models import FoodLog, FoodItem

router = APIRouter(prefix="/food-logs", tags=["food-logs"])

# ------------------------
# DB Dependency
# ------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------
# Schemas
# ------------------------
class FoodLogIn(BaseModel):
    user_id: Optional[int] = None      # allow mobile to omit, we fix to 1
    food_id: int
    quantity: float = 1.0
    unit: Optional[str] = "serving"
    portion_g_cooked: Optional[float] = None
    cooking_method: Optional[str] = None
    custom_grams: Optional[float] = None
    serving_unit: Optional[str] = None


class FoodLogOut(BaseModel):
    log_id: int
    user_id: Optional[int]
    food_id: int
    quantity: float
    unit: Optional[str]
    portion_g_cooked: Optional[float]
    cooking_method: Optional[str]
    grams_logged: Optional[float] = None
    serving_unit_used: Optional[str] = None
    logged_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================
# POST /food-logs  → Save a new food log (with auto-user-id)
# ============================================================
@router.post("", response_model=FoodLogOut)
def add_food_log(payload: FoodLogIn, db: Session = Depends(get_db)):
    # Require user_id - no more fallback to 1
    if payload.user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Validate food exists
    exists = db.query(FoodItem).filter(FoodItem.food_id == payload.food_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Food id {payload.food_id} not found")

    # Calculate grams_logged
    grams_logged = None
    serving_unit_used = payload.serving_unit or exists.serving_unit
    
    if payload.custom_grams is not None:
        grams_logged = payload.custom_grams
    else:
        weight = exists.serving_weight_g if exists.serving_weight_g else 100.0
        grams_logged = payload.quantity * weight

    entry = FoodLog(
        user_id=payload.user_id,
        food_id=payload.food_id,
        quantity=payload.quantity,
        unit=payload.unit,
        portion_g_cooked=payload.portion_g_cooked,
        cooking_method=payload.cooking_method,
        grams_logged=grams_logged,
        serving_unit_used=serving_unit_used,
    )
    db.add(entry)
    db.flush()  # Get generated log_id
    
    # Capture result before commit
    result = FoodLogOut(
        log_id=entry.log_id,
        user_id=entry.user_id,
        food_id=entry.food_id,
        quantity=entry.quantity,
        unit=entry.unit,
        portion_g_cooked=entry.portion_g_cooked,
        cooking_method=entry.cooking_method,
        grams_logged=entry.grams_logged,
        serving_unit_used=entry.serving_unit_used,
        logged_at=entry.logged_at,
    )
    
    db.commit()
    return result


# ============================================================
# GET /food-logs → list logs (optionally filter by user_id + date)
# ============================================================
@router.get("", response_model=List[FoodLogOut])
def list_food_logs(
    user_id: Optional[int] = Query(None),
    date_str: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db)
):
    q = db.query(FoodLog)

    if user_id is not None:
        q = q.filter(FoodLog.user_id == user_id)

    if date_str:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        q = q.filter(and_(FoodLog.logged_at >= start, FoodLog.logged_at <= end))

    rows = q.order_by(FoodLog.logged_at.desc()).all()
    return rows


# ============================================================
# GET /food-logs/today → logs for *today* for a user
# Handles timezone safely
# ============================================================
# @router.get("/today", response_model=List[FoodLogOut])
# def logs_today(
#     user_id: int = Query(...),
#     db: Session = Depends(get_db)
# ):
#     today_local = datetime.now().date()
#     start = datetime.combine(today_local, time.min)
#     end = datetime.combine(today_local, time.max)

#     rows = (
#         db.query(FoodLog)
#         .filter(
#             FoodLog.user_id == user_id,
#             FoodLog.logged_at >= start,
#             FoodLog.logged_at <= end,
#         )
#         .order_by(FoodLog.logged_at.desc())
#         .all()
#     )
#     return rows


# ============================================================
# DELETE /food-logs/{log_id}
# ============================================================
@router.delete("/{log_id}")
def delete_food_log(log_id: int, db: Session = Depends(get_db)):
    row = db.query(FoodLog).filter(FoodLog.log_id == log_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")

    db.delete(row)
    db.commit()
    return {"ok": True}