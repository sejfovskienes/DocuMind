import os
# from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.workers.ner_worker import NERWorker
from app.models.processed_document import ProcessedDocumentMetadata

def get_document_metadata_by_document_id(
        db: Session, 
        document_id: int) -> ProcessedDocumentMetadata | None:
    document_metadata = db.query(ProcessedDocumentMetadata) \
    .filter(ProcessedDocumentMetadata.document_id == document_id).first()
    if not document_metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for document:{document_id} not found!")
    return document_metadata

def save_document_metadata_object(
        db: Session, 
        document_id: int, 
        raw_text: str):
    metadata_object = ProcessedDocumentMetadata(document_id=document_id, clean_text=raw_text)
    db.add(metadata_object)
    db.commit()
    db.refresh(metadata_object)
    return metadata_object

def update_document_metadata(
        db: Session,
        document_id: int,
        new_data: dict[str: any]):
    document_metadata = get_document_metadata_by_document_id(db, document_id)
    try:
        for key, value in new_data.items():
            setattr(document_metadata, key, value)
    except Exception as e:
        print(f"Error occured while updating the document metadata object:\n{e}")

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
        