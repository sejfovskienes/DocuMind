from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, JSON, DateTime

class ProcessedFileMetadata(Base):
    __tablename__ = "processed_files"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    clean_text = Column(String, nullable=True)
    topics = Column(JSON, nullable=True)
    entities = Column(JSON, nullable=True)
    summaries = Column(JSON, nullable=True)
    last_proceed = Column(DateTime, default=datetime.utcnow)

    document = relationship(
        "Document", 
        back_populates="processed_document_metadata"
    )