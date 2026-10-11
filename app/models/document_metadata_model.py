from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database_extension import Base


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
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    document = relationship("Document", back_populates="processed_document_metadata")
