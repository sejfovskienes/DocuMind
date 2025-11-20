from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.services import  processed_doc_service

router = APIRouter(prefix="/nlp", tags=["NLP"])

@router.post("/ner/{document_id}")
def run_ner(
    document_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)):
    entities = processed_doc_service.get_named_entities(db, document_id)
    return {"entities": entities}