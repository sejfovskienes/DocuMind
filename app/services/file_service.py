import re
import fitz
import unicodedata
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import save_metadata_object
from app.models.processed_document import ProcessedFileMetadata

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text("text")
    print(f"PDF file content:\n {text}")
    return text

def clean_raw_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()
    return text

def make_metadata_object(db: Session, document_id: int , raw_text: str) -> ProcessedFileMetadata:
    document_metadata = save_metadata_object(db, document_id, raw_text)
    if not document_metadata:
        raise HTTPException(status_code=500, detail="An error occured while saving the metadata object!")
    return document_metadata

def preprocess_file_pipeline(db: Session, document_id: int,  file_path: str):
    text = extract_text_from_pdf(file_path=file_path)
    clean_text = clean_raw_text(text)
    metadata_object = make_metadata_object(db, document_id, clean_text)
    
    return metadata_object