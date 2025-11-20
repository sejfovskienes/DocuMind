from fastapi import HTTPException
from sqlalchemy.orm import Session 

from app.models.processed_document import ProcessedFileMetadata

def get_document_metadata_by_document_id(
        db: Session, 
        document_id: int) -> ProcessedFileMetadata | None:
    document_metadata = db.query(ProcessedFileMetadata) \
    .filter(ProcessedFileMetadata.document_id == document_id).first()
    if not document_metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for document:{document_id} not found!")
    return document_metadata

def save_document_metadata_object(
        db: Session, 
        document_id: int, 
        raw_text: str):
    metadata_object = ProcessedFileMetadata(document_id=document_id, clean_text=raw_text)
    db.add(metadata_object)
    db.commit()
    db.refresh(metadata_object)
    return metadata_object

# def update_document_metadata_object(
#         document_metadata: ProcessedFileMetadata,
#         new_data: dict[str, any]) -> bool:
    