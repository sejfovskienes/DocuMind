from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, JSON, Text

from app.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    metadata_id = Column(Integer, ForeignKey("processed_documents.id"))
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=False)
    embeddings = Column(JSON, nullable=True)
    ner_entities = Column(JSON, nullable=True)
    topic_keywords = Column(JSON, nullable=True)

    document = relationship("Document", back_populates="chunks")
    document_metadata = relationship("DocumentMetadata", back_populates="chunks")
