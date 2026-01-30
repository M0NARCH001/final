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


def verify_password(pw, hashed):
    return pwd_context.verify(pw, hashed)


# ---------------- SIGNUP ----------------

@router.post("/signup")
def signup(data: dict, db: Session = Depends(get_db)):

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(400, "username + password required")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "User already exists")

    u = User(
        username=username,
        password_hash=hash_password(password),
        name=data.get("name"),
        age=data.get("age"),
        gender=data.get("gender"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        goal=data.get("goal"),
    )

    db.add(u)
    db.commit()
    db.refresh(u)

    return {"user_id": u.user_id, "username": u.username}


# ---------------- LOGIN ----------------

@router.post("/login")
def login(data: dict, db: Session = Depends(get_db)):

    username = data.get("username")
    password = data.get("password")

    u = db.query(User).filter(User.username == username).first()

    if not u or not verify_password(password, u.password_hash):
        raise HTTPException(401, "Invalid credentials")

    return {
        "user_id": u.user_id,
        "username": u.username,
        "goal": u.goal,
    }
