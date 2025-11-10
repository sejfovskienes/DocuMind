from fastapi import HTTPException
from sqlalchemy.orm import Session 

from app import models
from app.models.document import Document
from app.schemas import user as user_schema
from app.auth import get_password_hash, verify_password
from app.models.processed_document import ProcessedFileMetadata

#--- TODO: rework the methods to throw errors  
def get_user_by_email(db: Session, email: str) :
    return db.query(models.user.User).filter(models.user.User.email == email).first()

def get_document_by_id(db: Session, id: int):
    return db.query(Document).filter(Document.id == id).first()

def delete_document_by_id(db: Session, id: int) -> bool:
    doc = get_document_by_id(db, id)
    if not doc:
        return False
    else:
        db.delete(doc)
        db.commit()
        return True
def get_document_metadata_by_id(db: Session, document_id: int):
    document_metadata = db.query(ProcessedFileMetadata).filter(ProcessedFileMetadata.document_id == document_id).first()
    if not document_metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for document:{document_id} not found!")
    return document_metadata

def create_user(db: Session, user_in: user_schema.UserCreate):
    hashed = get_password_hash(user_in.password)
    db_user = models.user.User(email=user_in.email, hashed_password=hashed, full_name=user_in.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_email(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_document(db: Session, user_id: int, filename: str, file_path: str):
    doc = Document(user_id=user_id, filename=filename, file_path=file_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def save_metadata_object(db: Session, document_id: int, raw_text: str):
    metadata_object = ProcessedFileMetadata(document_id=document_id, clean_text=raw_text)
    db.add(metadata_object)
    db.commit()
    db.refresh(metadata_object)
    return metadata_object