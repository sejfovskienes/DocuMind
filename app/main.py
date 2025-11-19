from art import *
from fastapi import FastAPI

from app.routes import auth, files, process_document, nlp
from app.database import Base, engine


app = FastAPI(title="DocuMind API")

@app.on_event("startup")
async def startup_event():
    tprint("DocuMind")

@app.get("/")
def main():
    return {"message": "connected to DocuMind API!"}

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(process_document.router)
app.include_router(nlp.router)