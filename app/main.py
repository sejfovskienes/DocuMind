"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from art import tprint
from fastapi import FastAPI

from app.database_extension import initialize_database
from app.routes import (
    auth_router,
    document_metadata_router,
    document_router,
    nlp_router,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    tprint("DocuMind")
    initialize_database()
    yield


app = FastAPI(title="DocuMind API", lifespan=lifespan)


@app.get("/")
def main() -> dict[str, str]:
    return {"message": "connected to DocuMind API!"}


app.include_router(auth_router.router)
app.include_router(document_router.router)
app.include_router(document_metadata_router.router)
app.include_router(nlp_router.router)
