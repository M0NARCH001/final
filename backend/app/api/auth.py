from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db.database import SessionLocal
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(pw: str):
    return pwd_context.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(pw, hashed)
    except Exception:
        return False


def _user_profile(u: User) -> dict:
    """Serialize full user profile for mobile consumption."""
    return {
        "user_id": u.user_id,
        "username": u.username,
        "name": u.name,
        "age": u.age,
        "gender": u.gender,
        "height_cm": u.height_cm,
        "weight_kg": u.weight_kg,
        "target_weight_kg": u.target_weight_kg,
        "activity_level": u.activity_level,
        "region": u.region or "All India",
        "dietary_preference": getattr(u, "dietary_preference", "any") or "any",
        "goal": u.goal,
        "has_diabetes": bool(u.has_diabetes),
        "has_hypertension": bool(u.has_hypertension),
        "has_pcos": bool(u.has_pcos),
        "muscle_gain_focus": bool(u.muscle_gain_focus),
        "heart_health_focus": bool(u.heart_health_focus),
    }


# ---------------- SIGNUP ----------------

@router.post("/signup")
def signup(data: dict, db: Session = Depends(get_db)):
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not password:
        raise HTTPException(400, "username and password are required")
    if len(password) < 6:
        raise HTTPException(400, "password must be at least 6 characters")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(409, "Username already taken")

    u = User(
        username=username,
        password_hash=hash_password(password),
        name=data.get("name"),
        age=data.get("age"),
        gender=data.get("gender"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        target_weight_kg=data.get("target_weight_kg"),
        activity_level=data.get("activity_level"),
        region=data.get("region", "All India"),
        goal=data.get("goal"),
        has_diabetes=bool(data.get("has_diabetes", False)),
        has_hypertension=bool(data.get("has_hypertension", False)),
        has_pcos=bool(data.get("has_pcos", False)),
        muscle_gain_focus=bool(data.get("muscle_gain_focus", False)),
        heart_health_focus=bool(data.get("heart_health_focus", False)),
    )
    # dietary_preference added via migration — set safely
    if hasattr(u, "dietary_preference"):
        u.dietary_preference = data.get("dietary_preference", "any")

    db.add(u)
    db.commit()
    db.refresh(u)
    return _user_profile(u)


# ---------------- LOGIN ----------------

@router.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username:
        raise HTTPException(400, "username is required")

    u = db.query(User).filter(User.username == username).first()
    if not u:
        raise HTTPException(401, "Invalid username or password")

    if u.password_hash is None:
        # Legacy user registered without a password — set one now
        if password:
            u.password_hash = hash_password(password)
            db.commit()
        # Allow login (no verification possible for legacy accounts)
    else:
        if not password or not verify_password(password, u.password_hash):
            raise HTTPException(401, "Invalid username or password")

    return _user_profile(u)
