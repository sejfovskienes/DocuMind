import os 
from fastapi import HTTPException
from sqlalchemy.orm import Session 

# from app.workers import document_worker
from app.models.document import Document
# from app.services import document_metadata_service
# from app.models.document_metadata import DocumentMetadata

async def write_document_locally(
        file, 
        file_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        contents = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error writing file: {e}"
        )

def create_document(
        db: Session, 
        user_id: int, 
        filename: str, 
        file_path: str) -> Document:
    doc = Document(
        user_id=user_id, 
        filename=filename, 
        file_path=file_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document_by_id(
        db: Session, 
        id: int) -> Document | None:
    document =  db.query(Document).filter(Document.id == id).first()
    if not document:
        raise HTTPException(
            status_code=404, 
            detail=f"Document with id: {id}, not found!")
    return document

def delete_document_by_id(db: Session, id: int) -> bool:
    doc = get_document_by_id(db, id)
    if not doc:
        return False
    else:
        db.delete(doc)
        db.commit()
        return True
