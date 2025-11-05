import os 
from jose import jwt 
from typing import Optional
from dotenv import load_dotenv
from datetime import timedelta
from passlib.context import CryptContext

load_dotenv(override=True)

JWT_SECRET = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("HASHING_ALGORITHM")
ACCESS_TOKEN_EXPIRES_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    now = timedelta.now()
    if expires_delta:
        expire = now + expires_delta
    else: 
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)

    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expire
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    if isinstance(token, bytes):
        token = token.decode("utf-8")
    
    return token

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        print(f"Expired signature error:\n {e}")
        raise 
    except jwt.PyJWTError as e:
        print(f"PyJWT error:\n {e}")
        raise