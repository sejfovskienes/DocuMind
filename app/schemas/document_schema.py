from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .worker_task_schema import WorkerTaskSchema


class DocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_path: str | None = None
    uploaded_at: datetime | None = None
    user_id: int | None = None


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentSchema
    worker_task: WorkerTaskSchema


class DocumentMetadataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int | None = None
    total_chunks: int
    summary: str | None = None
    topic_summary: str | None = None
    global_entities: Any = None
    global_topics: Any = None
    last_updated: datetime | None = None
