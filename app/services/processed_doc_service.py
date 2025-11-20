from fastapi import HTTPException
from sqlalchemy.orm import Session 

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

# def update_document_metadata_object(
#         document_metadata: ProcessedDocumentMetadata,
#         new_data: dict[str, any]) -> bool:
    