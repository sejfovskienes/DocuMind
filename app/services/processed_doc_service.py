import os
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.workers.ner_worker import NERWorker
from app.models.document_metadata import DocumentMetadata

def get_document_metadata_by_document_id(
        db: Session, 
        document_id: int) -> DocumentMetadata | None:
    document_metadata = db.query(DocumentMetadata) \
    .filter(DocumentMetadata.document_id == document_id).first()
    if not document_metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for document:{document_id} not found!")
    return document_metadata

def save_document_metadata_object(
        db: Session, 
        document_metadata: DocumentMetadata):
    db.add(document_metadata)
    db.commit()
    db.refresh(document_metadata)
    return document_metadata

def update_document_metadata(
        db: Session,
        document_id: int,
        new_data: dict[str: any]):
    document_metadata = get_document_metadata_by_document_id(db, document_id)
    if not document_metadata:
        raise ValueError(f"Document metadata for object with id: {id}, not found")
    for key, value in new_data.items():
            if hasattr(document_metadata, key):
                setattr(document_metadata, key, value)
            else:
                raise AttributeError(f"Metadata object has no attribute {key} to set")
    try:
        db.add(document_metadata)
        db.commit()
        db.refresh(document_metadata)
        return document_metadata
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Error occured while updating the document metadata object:\n{e}")

def get_named_entities(db: Session, document_id: int):
    document_metadata = get_document_metadata_by_document_id(db, document_id)
    if document_metadata.entities:
        return document_metadata.entities
    current_dir = os.path.dirname(__file__)
    model_path = os.path.join(current_dir, "..", "core", "onnx", "xlm_roberta_ner.onnx")
    model_path = os.path.abspath(model_path)
    ner_worker = NERWorker(model_path)
    entities = ner_worker.extract_entities(document_metadata.clean_text)
    # update_document_metadata(db, document_id, {"entities": entities})
    return entities
        