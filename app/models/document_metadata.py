from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, JSON, DateTime, Text

from app.database import Base

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    total_chunks = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    topic_summary = Column(Text, nullable=True)
    global_entities = Column(JSON, nullable=True)
    global_topics = Column(JSON, nullable=True)
    last_updated = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship(
        "Document", 
        back_populates="processed_document_metadata"
    )
    
