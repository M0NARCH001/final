# app/api/foods.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import FoodItem, FoodLog

router = APIRouter(prefix="/foods", tags=["foods"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FoodCreate(BaseModel):
    food_name: str
    main_name: Optional[str] = None
    subcategories_json: Optional[str] = None  # JSON string or None
    source: Optional[str] = "Imported"
    Calories_kcal: Optional[float] = None
    Carbohydrates_g: Optional[float] = None
    Protein_g: Optional[float] = None
    Fats_g: Optional[float] = None
    FreeSugar_g: Optional[float] = None
    Fibre_g: Optional[float] = None
    Sodium_mg: Optional[float] = None
    Calcium_mg: Optional[float] = None
    Iron_mg: Optional[float] = None
    VitaminC_mg: Optional[float] = None
    Folate_ug: Optional[float] = None
    serving_size: Optional[str] = None  # optional extra field

class FoodCreateAndLog(FoodCreate):
    user_id: int
    quantity: float = 1.0
    unit: Optional[str] = "serving"

@router.post("", status_code=201)
def create_food(payload: FoodCreate, db: Session = Depends(get_db)):
    # minimal validation
    if not payload.food_name:
        raise HTTPException(400, "food_name required")
    f = FoodItem(
        food_name=payload.food_name,
        main_name=payload.main_name or payload.food_name,
        subcategories_json=payload.subcategories_json,
        source=payload.source,
        Calories_kcal=payload.Calories_kcal,
        Carbohydrates_g=payload.Carbohydrates_g,
        Protein_g=payload.Protein_g,
        Fats_g=payload.Fats_g,
        FreeSugar_g=payload.FreeSugar_g,
        Fibre_g=payload.Fibre_g,
        Sodium_mg=payload.Sodium_mg,
        Calcium_mg=payload.Calcium_mg,
        Iron_mg=payload.Iron_mg,
        VitaminC_mg=payload.VitaminC_mg,
        Folate_ug=payload.Folate_ug
    )
    db.add(f)
    db.flush()  # Get the generated food_id
    
    # Capture values before commit
    result = {
        "food_id": f.food_id,
        "food_name": f.food_name,
        "Calories_kcal": f.Calories_kcal,
        "Protein_g": f.Protein_g,
        "Carbohydrates_g": f.Carbohydrates_g,
        "Fats_g": f.Fats_g,
        "serving_size": getattr(payload, "serving_size", None)
    }
    
    db.commit()
    return result


# Combined endpoint: Create food AND log it in ONE transaction
@router.post("/create-and-log", status_code=201)
def create_food_and_log(payload: FoodCreateAndLog, db: Session = Depends(get_db)):
    """Create a new food item and immediately log it for the user"""
    if not payload.food_name:
        raise HTTPException(400, "food_name required")
    if not payload.user_id:
        raise HTTPException(400, "user_id required")
    
    # Create the food item
    f = FoodItem(
        food_name=payload.food_name,
        main_name=payload.main_name or payload.food_name,
        subcategories_json=payload.subcategories_json,
        source=payload.source,
        Calories_kcal=payload.Calories_kcal,
        Carbohydrates_g=payload.Carbohydrates_g,
        Protein_g=payload.Protein_g,
        Fats_g=payload.Fats_g,
        FreeSugar_g=payload.FreeSugar_g,
        Fibre_g=payload.Fibre_g,
        Sodium_mg=payload.Sodium_mg,
        Calcium_mg=payload.Calcium_mg,
        Iron_mg=payload.Iron_mg,
        VitaminC_mg=payload.VitaminC_mg,
        Folate_ug=payload.Folate_ug
    )
    db.add(f)
    db.flush()  # Get food_id
    
    # Create the food log entry in the SAME transaction
    log_entry = FoodLog(
        user_id=payload.user_id,
        food_id=f.food_id,
        quantity=payload.quantity,
        unit=payload.unit,
    )
    db.add(log_entry)
    db.flush()  # Get log_id
    
    # Capture result
    result = {
        "food_id": f.food_id,
        "food_name": f.food_name,
        "log_id": log_entry.log_id,
        "user_id": log_entry.user_id,
        "quantity": log_entry.quantity,
        "logged_at": str(log_entry.logged_at) if log_entry.logged_at else None,
        "message": f"Created and logged '{f.food_name}'"
    }
    
    db.commit()
    return result