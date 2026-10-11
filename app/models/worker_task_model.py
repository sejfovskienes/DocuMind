from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.core.enum import WorkerTaskStatus
from app.database_extension import Base


class WorkerTask(Base):
    __tablename__ = "worker_tasks"

    id = Column(Integer, primary_key=True, index=True)
    payload = Column(JSON)
    task_type = Column(String, nullable=False)
    status = Column(String, default=WorkerTaskStatus.QUEUED.value)
    started_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
    finshed_at = Column(DateTime, nullable=True)
