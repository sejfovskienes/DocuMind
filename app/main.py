from fastapi import FastAPI

from app.routes import auth
from app.database import Base, engine
from app.models import user as user_model

app = FastAPI(title="DocuMind API")
Base.metadata.create_all(bind=engine)
app.include_router(auth.router)