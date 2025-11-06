from sqlalchemy.orm import Session 
from app import models, schemas
from app.auth import get_password_hash, verify_password
from app.models import user
from app.schemas import user

def get_user_by_email(db: Session, email: str) :
    return db.query(models.user.User).filter(models.user.User.email == email).first()

def create_user(db: Session, user_in: user.UserCreate):
    hashed = get_password_hash(user_in.password)
    db_user = models.user.User(email=user_in.email, hashed_password=hashed, full_name=user_in.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_email(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user