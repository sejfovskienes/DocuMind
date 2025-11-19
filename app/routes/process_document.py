from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import user
from app.database import get_db
from app.routes.auth import get_current_user
from app.services import processed_doc_service

router = APIRouter(prefix="/processed", tags=["document-metadata"])

@router.get("/get-document-metadata/{id}")
def get_document_metadata(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: user.User = Depends(get_current_user)):
    document_metadata = processed_doc_service.get_document_metadata_by_id(db, id)
    if document_metadata:
        return {"Processed document metadata": document_metadata}
    else:
        return {"Message": f"Could not find metadata for document with id: {id}"}