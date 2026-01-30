from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/plan")

class PlanRequest(BaseModel):
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity: str
    goal: str
    target_weight: float
    days: int


@router.post("/generate")
def generate_plan(req: PlanRequest):

    # BMR
    if req.gender.lower().startswith("m"):
        bmr = 10*req.weight_kg + 6.25*req.height_cm - 5*req.age + 5
    else:
        bmr = 10*req.weight_kg + 6.25*req.height_cm - 5*req.age - 161

    activity_map = {
        "low": 1.2,
        "moderate": 1.55,
        "high": 1.75
    }

    mult = activity_map.get(req.activity.lower(), 1.55)

    tdee = bmr * mult

    diff = req.weight_kg - req.target_weight
    if diff <= 0:
        return {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "daily_calories": round(tdee),
            "message": "Maintain weight"
        }

    total_deficit = diff * 7700

    max_daily_deficit = 500

    min_days = int(total_deficit / max_daily_deficit)

    final_days = max(req.days, min_days)

    daily_deficit = total_deficit / final_days

    daily_calories = tdee - daily_deficit

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_calories": round(daily_calories),
        "required_days": min_days,
        "final_days": final_days,
        "daily_deficit": round(daily_deficit),
    }
