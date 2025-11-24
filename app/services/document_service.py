from fastapi import HTTPException
from sqlalchemy.orm import Session 

from app.workers import document_worker
from app.models.document import Document
from app.services import document_metadata_service
from app.models.document_metadata import DocumentMetadata

def create_document(db: Session, user_id: int, filename: str, file_path: str) -> Document:
    doc = Document(user_id=user_id, filename=filename, file_path=file_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document_by_id(db: Session, id: int) -> Document | None:
    document =  db.query(Document).filter(Document.id == id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with id: {id}, not found!")
    return document

def delete_document_by_id(db: Session, id: int) -> bool:
    doc = get_document_by_id(db, id)
    if not doc:
        return False
    else:
        db.delete(doc)
        db.commit()
        return True

def process_document(db: Session, document: Document):
    document_metadata = DocumentMetadata(
                document_id=document.id,
                status="pending")
    document_metadata_saved = document_metadata_service.save_document_metadata_object(db, document_metadata)
    with document_worker.DocumentWorker(document) as worker:
        chunk_objects, chunk_number, save_chunks_result = worker.document_processing_pipeline(db)
    document_metadata_service.update_document_metadata(db, document.id, {"status": "ready", "total_chunks":chunk_number})
    return save_chunks_result, chunk_objects, document_metadata_saved