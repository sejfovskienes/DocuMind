from typing import Any
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.routes.auth import get_current_user
from app.services import task_service
from app.models.user import User

router = APIRouter(tags=["Worker Task"])

@router.get("get-task/{task-id}")
def get_worker_task(
    task_id: int, 
    db: Session = Depends(get_database_session), 
    user: User = Depends(get_current_user)):
    worker_task = task_service.get_worker_task_by_id(db, task_id)
    return {"message": worker_task}