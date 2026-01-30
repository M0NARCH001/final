# backend/app/api/goals.py

from fastapi import APIRouter
from pydantic import BaseModel
import math

router = APIRouter(prefix="/goals", tags=["goals"])


# ---------------- SCHEMAS ----------------

class GoalRequest(BaseModel):
    age: int
    gender: str               # "male" | "female"
    height_cm: float
    weight_kg: float
    activity_level: str      # low | medium | high
    goal: str                # loss | gain | maintain
    target_weight_kg: float | None = None
    target_days: int | None = None


# ---------------- HELPERS ----------------

def calc_bmr(weight, height, age, gender):
    if gender.lower() == "female":
        return 10 * weight + 6.25 * height - 5 * age - 161
    return 10 * weight + 6.25 * height - 5 * age + 5


def activity_multiplier(level):
    return {
        "low": 1.2,
        "medium": 1.55,
        "high": 1.75
    }.get(level, 1.2)


def min_safe_days(weight_delta):
    # never allow extreme change
    return abs(weight_delta) * 14   # 0.5kg/week


# ---------------- MAIN ENDPOINT ----------------

@router.post("/compute")
def compute_goal(req: GoalRequest):

    # ---- BMR + TDEE ----
    bmr = calc_bmr(req.weight_kg, req.height_cm, req.age, req.gender)
    tdee = bmr * activity_multiplier(req.activity_level)

    daily_cal = tdee

    # ---- Goal calories ----
    if req.goal == "loss":
        daily_cal -= 500
    elif req.goal == "gain":
        daily_cal += 300

    daily_cal = round(daily_cal)

    # ---- Protein ----
    if req.goal == "loss":
        protein = req.weight_kg * 1.6
    elif req.goal == "gain":
        protein = req.weight_kg * 2.0
    else:
        protein = req.weight_kg * 0.8

    # ---- Fat (25%) ----
    fat = (daily_cal * 0.25) / 9

    # ---- Carbs = remainder ----
    protein_cal = protein * 4
    fat_cal = fat * 9
    carbs = (daily_cal - protein_cal - fat_cal) / 4

    # ---- Days ----
    required_days = None
    final_days = None

    if req.target_weight_kg is not None:
        delta = req.target_weight_kg - req.weight_kg
        kcal_total = abs(delta) * 7700
        daily_delta = abs(daily_cal - tdee)

        if daily_delta < 200:
            daily_delta = 200

        required_days = math.ceil(kcal_total / daily_delta)

        min_days = min_safe_days(delta)

        final_days = max(required_days, min_days)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_calories": round(daily_cal),
        "protein_g": round(protein),
        "fat_g": round(fat),
        "carbs_g": round(carbs),
        "required_days": required_days,
        "final_days": final_days,
    }