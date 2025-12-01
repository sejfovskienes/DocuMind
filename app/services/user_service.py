from sqlalchemy.orm import Session 

from app.models.user import User
from app.schemas.user import UserCreate
from app.auth import get_password_hash, verify_password

def create_user(
        db: Session, 
        user_in: UserCreate) -> User:
    hashed = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email, 
        hashed_password=hashed, 
        full_name=user_in.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(
        db: Session, 
        email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def authenticate_user(
        db: Session, 
        username: str, 
        password: str) -> User | None:
    user = get_user_by_email(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
