import os

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.base.config import DocumentConfig
from app.models import Document


async def write_document_locally(file: UploadFile, file_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            while contents := await file.read(DocumentConfig.UPLOAD_READ_CHUNK_SIZE):
                buffer.write(contents)
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail=f"Error writing file: {exc}"
        ) from exc


def create_document(
    db: Session,
    user_id: int,
    filename: str,
    file_path: str,
    *,
    commit: bool = True,
) -> Document:
    document = Document(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
    )
    try:
        db.add(document)
        if commit:
            db.commit()
            db.refresh(document)
        else:
            db.flush()
        return document
    except Exception:
        db.rollback()
        raise


def get_document_by_id(
    db: Session, document_id: int, user_id: int | None = None
) -> Document:
    query = db.query(Document).filter(Document.id == document_id)
    if user_id is not None:
        query = query.filter(Document.user_id == user_id)
    document = query.first()
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document with id: {document_id} not found!",
        )
    return document


def delete_document_by_id(
    db: Session, document_id: int, user_id: int | None = None
) -> bool:
    document = get_document_by_id(db, document_id, user_id)
    try:
        db.delete(document)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
