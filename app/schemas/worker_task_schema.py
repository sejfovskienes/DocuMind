from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.enum import WorkerTaskStatus, WorkerTaskType


class WorkerTaskSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payload: dict[str, Any]
    task_type: WorkerTaskType
    status: WorkerTaskStatus
    started_at: datetime
    finshed_at: datetime | None = None
