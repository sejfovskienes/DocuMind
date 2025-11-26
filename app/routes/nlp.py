from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_database_session
from app.models.user import User
from app.routes.auth import get_current_user
from app.services import  document_metadata_service, task_service
from app.models.worker_task import WorkerTask

router = APIRouter(prefix="/nlp", tags=["NLP"])

@router.post("/extract-entities/{document_id}")
def run_ner(
    document_id: int, 
    db: Session = Depends(get_database_session), 
    current_user: User = Depends(get_current_user)):
    ner_task = WorkerTask(payload={"document_id": document_id}, task_type="ner_task")
    task_service.save_worker_task(ner_task)
    return {"NER task": ner_task}