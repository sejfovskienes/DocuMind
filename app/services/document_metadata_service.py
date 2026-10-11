from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import DocumentMetadata


def get_document_metadata_by_document_id(
    db: Session, document_id: int
) -> DocumentMetadata:
    metadata = (
        db.query(DocumentMetadata)
        .filter(DocumentMetadata.document_id == document_id)
        .first()
    )
    if metadata is None:
        raise HTTPException(
            status_code=404,
            detail=f"Metadata for document: {document_id} not found!",
        )
    return metadata


def save_document_metadata_object(
    db: Session, document_metadata: DocumentMetadata
) -> DocumentMetadata:
    try:
        db.add(document_metadata)
        db.commit()
        db.refresh(document_metadata)
        return document_metadata
    except Exception:
        db.rollback()
        raise


def update_document_metadata(
    db: Session, document_id: int, new_data: dict[str, object]
) -> DocumentMetadata:
    metadata = get_document_metadata_by_document_id(db, document_id)
    column_names = {column.key for column in DocumentMetadata.__mapper__.column_attrs}
    unknown_fields = new_data.keys() - column_names
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise AttributeError(f"Metadata has no field named {field!r}")

    for key, value in new_data.items():
        setattr(metadata, key, value)

    try:
        db.add(metadata)
        db.commit()
        db.refresh(metadata)
        return metadata
    except Exception:
        db.rollback()
        raise


def get_named_entities(db: Session, document_id: int) -> Any | None:
    return get_document_metadata_by_document_id(db, document_id).global_entities


def get_global_topics(db: Session, document_id: int) -> Any | None:
    return get_document_metadata_by_document_id(db, document_id).global_topics
