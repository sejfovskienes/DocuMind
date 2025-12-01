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

def update_document_chunk(
        db: Session,
        document_chunk: DocumentChunk,
        new_data: dict[str, any]) -> None:
    if not document_chunk:
        raise AttributeError("Document chunk object not found")
    try:
        for key, value in new_data.items():
            if hasattr(document_chunk, key):
                setattr(document_chunk, key, value)
                db.add(document_chunk)
                db.commit()
                db.refresh(document_chunk)
            else:
                db.rollback()
                raise AttributeError(f"Document object has no attribut named:{key}")
    except RuntimeError:
        print("An error occured while updating DocumentChunk object")