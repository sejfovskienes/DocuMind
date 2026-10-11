from sqlalchemy.orm import Session

from app import auth_extension as authentication
from app.models import User
from app.schemas import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        email=user_in.email,
        hashed_password=authentication.get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_email(db, username)
    if user is None or not authentication.verify_password(
        password, user.hashed_password
    ):
        return None
    return user
