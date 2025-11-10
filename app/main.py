from fastapi import FastAPI

from app.routes import auth, files, process_document
from app.database import Base, engine
# from app.models import user as user_model

app = FastAPI(title="DocuMind API")

@app.get("/")
def main():
    return {"message": "connected to DocuMind API!"}

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(process_document.router)