from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.enum import WorkerTaskType
from app.database_extension import get_database_session
from app.models import User, WorkerTask
from app.routes.auth_router import get_current_user
from app.schemas import WorkerTaskSchema
from app.services import document_service, worker_task_service

router = APIRouter(prefix="/nlp", tags=["NLP"])


@router.post("/extract-entities/{document_id}")
def run_ner(
    document_id: int,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, WorkerTaskSchema]:
    document_service.get_document_by_id(
        db,
        document_id,
        user_id=current_user.id,
    )
    task = WorkerTask(
        payload={"document_id": document_id},
        task_type=WorkerTaskType.ENTITY_EXTRACTION,
    )
    worker_task_service.save_worker_task(db, task)
    return {"ner_task": WorkerTaskSchema.model_validate(task)}


@router.get("/get-task/{task_id}")
def get_task_by_id(
    task_id: int,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, WorkerTaskSchema]:
    task = worker_task_service.get_task_by_id(db, task_id, user_id=current_user.id)
    return {"worker_task": WorkerTaskSchema.model_validate(task)}


@router.get("/summarize/{document_id}")
def summarization_endpoint(
    document_id: int,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, WorkerTaskSchema]:
    document_service.get_document_by_id(
        db,
        document_id,
        user_id=current_user.id,
    )
    task = WorkerTask(
        payload={
            "document_id": document_id,
            "user_id": current_user.id,
        },
        task_type=WorkerTaskType.SUMMARIZATION,
    )
    worker_task_service.save_worker_task(db, task)
    return {"summarization_task": WorkerTaskSchema.model_validate(task)}
