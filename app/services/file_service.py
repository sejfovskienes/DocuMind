import re
import fitz
import unicodedata
from sqlalchemy.orm import Session

from app.services import processed_doc_service
from app.models.processed_document import ProcessedDocumentMetadata

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text("text")
    return text

def clean_raw_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()
    return text

def preprocess_file_pipeline(db: Session, document_id: int,  file_path: str) -> ProcessedDocumentMetadata:
    text = extract_text_from_pdf(file_path=file_path)
    clean_text = clean_raw_text(text)
    metadata_object = processed_doc_service.save_document_metadata_object(db, document_id, clean_text)
    
    return metadata_object