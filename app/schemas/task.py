from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class WorkerTaskSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payload: dict[str, Any]
    task_type: str
    status: str
    started_at: datetime
    finshed_at: Optional[datetime] = None