from fastapi import HTTPException
from sqlalchemy.orm import Session 

from app import models
from app.models.document import Document
from app.schemas import user as user_schema
from app.auth import get_password_hash, verify_password
from app.models.processed_document import ProcessedFileMetadata

#--- TODO: rework the methods to throw errors  




def get_document_metadata_by_id(db: Session, document_id: int):
    document_metadata = db.query(ProcessedFileMetadata).filter(ProcessedFileMetadata.document_id == document_id).first()
    if not document_metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for document:{document_id} not found!")
    return document_metadata







def save_metadata_object(db: Session, document_id: int, raw_text: str):
    metadata_object = ProcessedFileMetadata(document_id=document_id, clean_text=raw_text)
    db.add(metadata_object)
    db.commit()
    db.refresh(metadata_object)
    return metadata_object