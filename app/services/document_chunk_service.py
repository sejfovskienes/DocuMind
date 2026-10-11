from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import DocumentChunk


def get_chunks_by_document_id(db: Session, document_id: int) -> list[DocumentChunk]:
    chunks = (
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    )
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=f"No document chunks for document with id: {document_id}",
        )
    return chunks


def update_document_chunk(
    db: Session,
    document_chunk: DocumentChunk | None,
    new_data: dict[str, Any],
) -> None:
    if document_chunk is None:
        raise HTTPException(status_code=404, detail="Document chunk not found")

    column_names = {column.key for column in DocumentChunk.__mapper__.column_attrs}
    unknown_fields = new_data.keys() - column_names
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise AttributeError(f"Document chunk has no field named {field!r}")

    for key, value in new_data.items():
        setattr(document_chunk, key, value)

    try:
        db.add(document_chunk)
        db.commit()
        db.refresh(document_chunk)
    except Exception:
        db.rollback()
        raise
