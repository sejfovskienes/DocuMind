from typing import Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.models.user import User
from app.services import task_service
from app.routes.auth import get_current_user
from app.database import get_database_session
from app.models.worker_task import WorkerTask
from app.schemas.task import WorkerTaskSchema
from app.core.enum.worker_task_type import WorkerTaskType

router = APIRouter(prefix="/nlp", tags=["NLP"])

@router.post("/extract-entities/{document_id}")
def run_ner(
    document_id: int, 
    db: Session = Depends(get_database_session), 
    current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    ner_task = WorkerTask(payload={"document_id": document_id}, task_type=WorkerTaskType.ENTITY_EXTRACTION)
    task_service.save_worker_task(db, ner_task)
    return {"ner_task": WorkerTaskSchema.model_validate(ner_task)}

@router.get("/get-task/{task_id}")
def get_task_by_id(
    task_id: int, 
    db: Session = Depends(get_database_session), 
    current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    worker_task = task_service.get_task_by_id(db, task_id)
    return {
        "worker_task": WorkerTaskSchema.model_validate(worker_task)}

@router.get("/summarize/{document_id}")
def summarization_endpoint(
    document_id: int, 
    db: Session = Depends(get_database_session), 
    current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    summarization_task = WorkerTask(
        payload={"document_id": document_id},
        task_type=WorkerTaskType.SUMMARIZATION,
    )
    task_service.save_worker_task(db, summarization_task)
    return {"summarization_task": WorkerTaskSchema.model_validate(summarization_task)}