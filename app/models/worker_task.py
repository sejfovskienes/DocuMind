from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON

from app.database import Base

class WorkerTask(Base):
    __tablename__="worker_tasks"

    id = Column(Integer, primary_key=True, index=True)
    payload = Column(JSON) 
    task_type = Column(String, nullable=False)
    status = Column(String, insert_default="Queued")
    started_at = Column(DateTime, insert_default=datetime.utcnow())
    finshed_at = Column(DateTime, nullable=True)

    