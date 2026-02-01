# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic schemas
class UserIn(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    medical_conditions: Optional[str] = None
    diet_preferences: Optional[str] = None


class UserOut(UserIn):
    user_id: int
    created_at: Optional[str] = None


class UsernameCheck(BaseModel):
    username: str


class UsernameCheckResponse(BaseModel):
    available: bool
    user_id: Optional[int] = None


# ============================================================
# POST /users/check-username → Check if username exists
# Returns user_id if exists (for login), available=True if new
# ============================================================
@router.post("/check-username", response_model=UsernameCheckResponse)
def check_username(payload: UsernameCheck, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    existing = db.query(User).filter(User.username == username).first()
    
    if existing:
        return {"available": False, "user_id": existing.user_id}
    else:
        return {"available": True, "user_id": None}


# ============================================================
# POST /users/register → Register new user with username
# ============================================================
@router.post("/register", response_model=UserOut)
def register_user(payload: UserIn, db: Session = Depends(get_db)):
    if not payload.username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    username = payload.username.strip().lower()
    
    # Check if username already exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    
    user = User(
        username=username,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        target_weight_kg=payload.target_weight_kg,
        activity_level=payload.activity_level,
        medical_conditions=payload.medical_conditions,
        diet_preferences=payload.diet_preferences,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# GET /users/by-username/{username} → Get user by username
# ============================================================
@router.get("/by-username/{username}", response_model=UserOut)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Create user (legacy - for backward compatibility)
@router.post("", response_model=UserOut)
def create_user(payload: UserIn, db: Session = Depends(get_db)):
    user = User(
        username=payload.username,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        target_weight_kg=payload.target_weight_kg,
        activity_level=payload.activity_level,
        medical_conditions=payload.medical_conditions,
        diet_preferences=payload.diet_preferences,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in payload.dict(exclude_unset=True).items():
        if k != "username":  # Don't allow changing username
            setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user