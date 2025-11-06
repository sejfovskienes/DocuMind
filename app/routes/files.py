import os 
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from dotenv import load_dotenv

from app import database, crud
from app.models import user
from .auth import get_current_user

load_dotenv(override=True)

router = APIRouter(prefix="/files", tags=["files"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upsert-file")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db), 
    current_user: user.User = Depends(get_current_user)):

    unique_name = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    document = crud.create_document(db, current_user.id, filename=file.filename, file_path=file_path)

    return {"message": "File uploaded successfully", "file_id": document.id}

@router.get("/get-file-{id}")
def get_document_by_id(
    id: int,
    current_user: user.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)):
    file = crud.get_document_by_id(db, id)
    if file:
        return {"file_id": id, "content": file}
    else:
        raise HTTPException(status_code=404, detail=f"File with id: {id} not found!")

@router.get("/delete-file-{id}")
def delete_file(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: user.User = Depends(get_current_user)):
    success = crud.delete_document_by_id(db, id)
    if success:
        return {"message": f"Document with id: {id} has been deleted successfully!"}
    else:
        return {"message": f"Error occured while deleting document with id: {id}!"}