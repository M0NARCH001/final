# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import User
import csv
import io

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
    region: Optional[str] = "All India"


class UserOut(BaseModel):
    user_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    region: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_with_str_date(cls, user):
        """Convert User ORM object to UserOut with string date"""
        return cls(
            user_id=user.user_id,
            username=user.username,
            name=user.name,
            age=user.age,
            gender=user.gender,
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            target_weight_kg=user.target_weight_kg,
            activity_level=user.activity_level,
            region=user.region,
            created_at=str(user.created_at) if user.created_at else None,
        )


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
        region=payload.region,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.from_orm_with_str_date(user)


# ============================================================
# GET /users/by-username/{username} → Get user by username
# ============================================================
@router.get("/by-username/{username}", response_model=UserOut)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_orm_with_str_date(user)


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
        region=payload.region,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.from_orm_with_str_date(user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_orm_with_str_date(user)


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
    return UserOut.from_orm_with_str_date(user)


# ============================================================
# GET /users/admin/list  → All registered users (admin view)
# ============================================================
@router.get("/admin/list")
def list_all_users(db: Session = Depends(get_db)):
    """Return all registered users — for admin/capstone review purposes."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "user_id": u.user_id,
            "username": u.username or "—",
            "name": u.name or "—",
            "gender": u.gender or "—",
            "age": u.age,
            "region": u.region or "All India",
            "dietary_preference": getattr(u, "dietary_preference", "any") or "any",
            "goal": u.goal or "—",
            "activity_level": u.activity_level or "—",
            "has_diabetes": bool(u.has_diabetes),
            "has_hypertension": bool(u.has_hypertension),
            "has_pcos": bool(u.has_pcos),
            "muscle_gain_focus": bool(u.muscle_gain_focus),
            "heart_health_focus": bool(u.heart_health_focus),
            "created_at": str(u.created_at) if u.created_at else "—",
        }
        for u in users
    ]


# ============================================================
# GET /users/admin/export.csv  → Download all users as CSV
# ============================================================
@router.get("/admin/export.csv")
def export_users_csv(db: Session = Depends(get_db)):
    """Download all registered users as a CSV file."""
    users = db.query(User).order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "user_id", "username", "name", "gender", "age",
        "region", "dietary_preference", "goal", "activity_level",
        "height_cm", "weight_kg", "target_weight_kg",
        "has_diabetes", "has_hypertension", "has_pcos",
        "muscle_gain_focus", "heart_health_focus", "created_at",
    ])
    for u in users:
        writer.writerow([
            u.user_id,
            u.username or "",
            u.name or "",
            u.gender or "",
            u.age or "",
            u.region or "All India",
            getattr(u, "dietary_preference", "any") or "any",
            u.goal or "",
            u.activity_level or "",
            u.height_cm or "",
            u.weight_kg or "",
            u.target_weight_kg or "",
            int(bool(u.has_diabetes)),
            int(bool(u.has_hypertension)),
            int(bool(u.has_pcos)),
            int(bool(u.muscle_gain_focus)),
            int(bool(u.heart_health_focus)),
            str(u.created_at) if u.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nutrimate_users.csv"},
    )