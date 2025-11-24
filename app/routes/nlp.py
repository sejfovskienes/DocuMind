from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_database_session
from app.models.user import User
from app.routes.auth import get_current_user
from app.services import  document_metadata_service

router = APIRouter(prefix="/nlp", tags=["NLP"])

@router.post("/extract-entities/{document_id}")
def run_ner(
    document_id: int, 
    db: Session = Depends(get_database_session), 
    current_user: User = Depends(get_current_user)):
    entities = document_metadata_service.get_named_entities(db, document_id)
    return {"entities": entities}