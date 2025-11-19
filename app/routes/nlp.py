from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.database import get_db
from app.models.user import User
from app.routes.auth import get_current_user
# from app.services.ner_service import extract_entities

router = APIRouter(prefix="/nlp", tags=["NLP"])

@router.post("/ner/{id}")
def run_ner(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)):
    document = crud.get_document_by_id(db, id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with id:{id}, not found!")
    document_metadata = crud.get_document_metadata_by_id(id)
    if not document_metadata:
        raise HTTPException(status_code=400, detail=f"Document with id:{id}, is not processed yet!")
    # entities = extract_entities(document_metadata.clean_text)
    entities = "asd"
    return {"entities": entities}