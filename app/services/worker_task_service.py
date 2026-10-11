from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enum import WorkerTaskStatus, WorkerTaskType
from app.models import Document, WorkerTask


def save_worker_task(
    db: Session, worker_task: WorkerTask, *, commit: bool = True
) -> WorkerTask:
    try:
        db.add(worker_task)
        if commit:
            db.commit()
            db.refresh(worker_task)
        else:
            db.flush()
        return worker_task
    except Exception:
        db.rollback()
        raise


def update_worker_task(
    db: Session, worker_task: WorkerTask | None, data: dict[str, object]
) -> WorkerTask:
    if worker_task is None:
        raise HTTPException(status_code=404, detail="Worker task not found")

    column_names = {column.key for column in WorkerTask.__mapper__.column_attrs}
    unknown_fields = data.keys() - column_names
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise HTTPException(
            status_code=400,
            detail=f"Task object does not have field: {field}",
        )

    for key, value in data.items():
        setattr(worker_task, key, value)

    try:
        db.add(worker_task)
        db.commit()
        db.refresh(worker_task)
        return worker_task
    except Exception:
        db.rollback()
        raise


def get_new_task(db: Session, task_type: WorkerTaskType) -> WorkerTask | None:
    while True:
        candidate = (
            db.query(WorkerTask)
            .filter(
                WorkerTask.task_type == task_type,
                WorkerTask.status == WorkerTaskStatus.QUEUED,
            )
            .order_by(WorkerTask.id)
            .first()
        )
        if candidate is None:
            return None

        claimed = (
            db.query(WorkerTask)
            .filter(
                WorkerTask.id == candidate.id,
                WorkerTask.status == WorkerTaskStatus.QUEUED,
            )
            .update(
                {WorkerTask.status: WorkerTaskStatus.PROCESSING},
                synchronize_session=False,
            )
        )
        if claimed == 1:
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            return get_worker_task_by_id(db, candidate.id)
        db.rollback()


def get_worker_task_by_id(db: Session, worker_task_id: int) -> WorkerTask:
    worker_task = db.query(WorkerTask).filter(WorkerTask.id == worker_task_id).first()
    if worker_task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Worker task with id: {worker_task_id} not found!",
        )
    return worker_task


def get_task_by_id(db: Session, task_id: int, user_id: int | None = None) -> WorkerTask:
    task = get_worker_task_by_id(db, task_id)
    if user_id is not None:
        payload = task.payload
        if not isinstance(payload, dict):
            raise HTTPException(status_code=404, detail="Worker task not found")
        task_user_id = payload.get("user_id")
        document_id = payload.get("document_id")
        user_id_matches = task_user_id is None or task_user_id == user_id
        if document_id is not None:
            document_belongs_to_user = (
                db.query(Document.id)
                .filter(
                    Document.id == document_id,
                    Document.user_id == user_id,
                )
                .first()
                is not None
            )
            belongs_to_user = user_id_matches and document_belongs_to_user
        else:
            belongs_to_user = task_user_id == user_id
        if not belongs_to_user:
            raise HTTPException(status_code=404, detail="Worker task not found")
    return task


def get_finished_tasks(db: Session, task_type: WorkerTaskType) -> list[WorkerTask]:
    return (
        db.query(WorkerTask)
        .filter(WorkerTask.task_type == task_type)
        .filter(WorkerTask.status == WorkerTaskStatus.FINISHED)
        .all()
    )
