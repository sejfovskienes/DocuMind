from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.models.user import User
from app.services import task_service
from app.routes.auth import get_current_user
from app.database import get_database_session
from app.models.worker_task import WorkerTask
from app.core.enum.worker_task_type import WorkerTaskType

router = APIRouter(prefix="/nlp", tags=["NLP"])

@router.post("/extract-entities/{document_id}")
def run_ner(
    document_id: int, 
    db: Session = Depends(get_database_session), 
    current_user: User = Depends(get_current_user)):
    ner_task = WorkerTask(payload={"document_id": document_id}, task_type=WorkerTaskType.ENTITY_EXTRACTION)
    task_service.save_worker_task(db, ner_task)
    return {"NER task": ner_task}