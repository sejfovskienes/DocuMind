from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk

def get_chunks_by_document_id(
        db: Session, 
        document_id: int) -> list[DocumentChunk]:
    document_chunks = db.query(DocumentChunk) \
    .filter(DocumentChunk.document_id==document_id).all()
    if not document_chunks:
        raise HTTPException(
            status_code=404, 
            detail=f"No document chunks for document with id: {id}")
    return document_chunks