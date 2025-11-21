# from typing import Generator 
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from app.models import user
from app import schemas, database
from app.services import user_service
from app.auth import create_access_token, decode_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=schemas.user.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.user.UserCreate, db: Session = Depends(database.get_database_session)):
    existing = user_service.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = user_service.create_user(db, user_in)
    return user

@router.post("/token", response_model=schemas.user.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_database_session)):
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(subject=user.email, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_database_session)) -> user.User:
    from jwt import ExpiredSignatureError, PyJWTError
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except ExpiredSignatureError as ese:
        raise HTTPException(status_code=401, detail=f"Token expired:\n {ese}")
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: {e}")
    
    user = user_service.get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/me", response_model=schemas.user.UserOut)
def read_user_me(current_user: user.User = Depends(get_current_user)):
    return current_user