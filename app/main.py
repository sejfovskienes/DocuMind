from art import *  # noqa: F403
from fastapi import FastAPI

from app.routes import auth, document, document_metadata, nlp
from app.database import Base, engine


app = FastAPI(title="DocuMind API")

@app.on_event("startup")
async def startup_event():
    tprint("DocuMind") # noqa

@app.get("/")
def main():
    return {"message": "connected to DocuMind API!"}

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(document.router)
app.include_router(document_metadata.router)
app.include_router(nlp.router)