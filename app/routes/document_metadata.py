from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import user
from app.database import get_database_session
from app.routes.auth import get_current_user
from app.services import document_metadata_service

router = APIRouter(prefix="/process-document", tags=["Document-Metadata"])

@router.get("/get-document-metadata/{id}")
def get_document_metadata(
    id: int, 
    db: Session = Depends(get_database_session), 
    current_user: user.User = Depends(get_current_user)):
    document_metadata = document_metadata_service.get_document_metadata_by_document_id(db, id)
    if document_metadata:
        return {"Processed document metadata": document_metadata}
    else:
        return {"Message": f"Could not find metadata for document with id: {id}"}