from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.worker_task import WorkerTask

def save_worker_task(
        db: Session, 
        worker_task: WorkerTask) -> WorkerTask | None:
    try:
        db.add(worker_task)
        db.commit()
        db.refresh(worker_task)
        return worker_task
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occured while saving the task: {e}")
    
def update_worker_task(
        db: Session, 
        worker_task: WorkerTask, 
        data: dict) -> WorkerTask | None:
    if not worker_task:
        raise HTTPException(
            status_code=400, 
            detail=f"Task with id: {worker_task.id} not found!")
    for key, value in data.items():
        if hasattr(worker_task, key):
            setattr(worker_task, key, value)
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Task object do not have attribute: {key}")
    try:
        db.add(worker_task)
        db.commit()
        db.refresh(worker_task)
        return worker_task
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occured while updating the task object: {e}")
    
def get_new_task(db: Session, task_type: str) -> WorkerTask | None:
    worker_task = db.query(WorkerTask) \
    .filter(WorkerTask.task_type==task_type) \
    .filter(WorkerTask.status=="queued").first()

    if not worker_task:
        return None
    return worker_task

def get_worker_task_by_id(
        db: Session, 
        document_worker_task_id: int) -> WorkerTask | None:
    worker_task = db.query(WorkerTask) \
    .filter(WorkerTask.id == document_worker_task_id).first()
    if not worker_task:
        raise HTTPException(
            status_code=404, 
            detail=f"Worker task with id: {id} not found!")
    return worker_task

