import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.enum import WorkerTaskStatus
from app.services.worker_task_service import update_worker_task

logger = logging.getLogger(__name__)


def run_task(db: Session, task: Any, process: Callable[[], Any]) -> bool:
    """Run one task and persist exactly one matching terminal status."""
    task_id = getattr(task, "id", "unknown")
    try:
        update_worker_task(
            db,
            task,
            {"status": WorkerTaskStatus.PROCESSING, "finshed_at": None},
        )
        result = process()
        if result is False:
            raise RuntimeError("Task processor reported failure.")
        update_worker_task(
            db,
            task,
            {
                "status": WorkerTaskStatus.FINISHED,
                "finshed_at": datetime.now(UTC).replace(tzinfo=None),
            },
        )
        return True
    except Exception as error:
        db.rollback()
        logger.warning("Worker task %s failed (%s)", task_id, type(error).__name__)
        update_worker_task(
            db,
            task,
            {"status": WorkerTaskStatus.FAILED, "finshed_at": None},
        )
        return False
