import os 
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import (
    APIRouter, UploadFile, File, Depends, HTTPException)

from app import database
from .auth import get_current_user
from app.models import user, worker_task
from app.services import document_service, task_service
from app.core.enum.worker_task_type import WorkerTaskType

load_dotenv(override=True)

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upsert-file")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_database_session), 
    current_user: user.User = Depends(get_current_user)):
    unique_name = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    document = document_service.create_document(
        db, 
        current_user.id, 
        filename=file.filename, file_path=file_path)

    document_processing_task = worker_task.WorkerTask(
        payload={"document_id": document.id},
        task_type=WorkerTaskType.DOCUMENT_PROCESSING)
    task_service.save_worker_task(db, document_processing_task)
    if document:
        return{
            "message": "Document uploaded successfully",
            "document": document,
            "worker_task": document_processing_task
        }
    else:
        return {"message": "An error occured while uploading the file!"}
    
@router.get("/get-document/{document-id}")
def get_document_by_id(
    id: int,
    current_user: user.User = Depends(get_current_user),
    db: Session = Depends(database.get_database_session)):
    file = document_service.get_document_by_id(db, id)
    if file:
        return {f"file:{id} object": file}
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"File with id: {id} not found!")

@router.get("/delete-document/{document-id}")
def delete_file(
    id: int,
    db: Session = Depends(database.get_database_session),
    current_user: user.User = Depends(get_current_user)):
    success = document_service.delete_document_by_id(db, id)
    if success:
        return {
            "message": f"Document with id: {id} has been deleted successfully!"}
    else:
        return {
            "message": f"Error occured while deleting document with id: {id}!"}
    