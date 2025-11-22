from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, JSON, DateTime, Text

class DocumentMetadata(Base):
    __tablename__ = "processed_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    status = Column(String, default="pending")
    total_chunks = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    topic_summary = Column(Text, nullable=True)
    global_entities = Column(JSON, nullable=True)
    global_topics = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship(
        "Document", 
        back_populates="processed_document_metadata"
    )
    chunks = relationship("DocumentChunk", back_populates="metadata", cascade="all, delete-orphan")
