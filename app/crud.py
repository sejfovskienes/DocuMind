from sqlalchemy.orm import Session 
from app import models, schemas
from app.auth import get_password_hash, verify_password

def get_user_by_email(db: Session, email: str) -> models.user.User:
    return db.query(models.user.User).filter(models.user.User.email == email).first()

def create_user(db: Session, user_in: schemas.user.UserCreate):
    hashed = get_password_hash(user_in.password)
    db_user = models.user.User(email=user_in.email, hashed_password=hashed, full_name=user_in.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> models.user.User:
    with get_user_by_email(email) as user:
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user