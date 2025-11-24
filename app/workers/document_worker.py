import os
import re
import fitz
import unicodedata
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

from app.models import document, document_chunk

#--- TODO: in v1.1 add OCR and table data analysis.

EMBEDDING_MODEL = SentenceTransformer("all-mpnet-base-v2")

class DocumentWorker:
    def __init__(self, document: document.Document, max_tokens: int = 200, overlap: int = 150):
        self.document_path = document.file_path
        self.document_id = document.id
        self.document_metadata_id = document.processed_document_metadata.id
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.embedding_model = None
    
    def __enter__(self):
        self.embedding_model = EMBEDDING_MODEL
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        del self.embedding_model

    def extract_text_from_pdf(self) -> str:
        text = ""
        with fitz.open(self.document_path) as pdf:
            for page in pdf:
                text += page.get_text("text")
        return text
    
    def clean_raw_text(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
        text = re.sub(r'\s*\n\s*', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = text.strip()
        return text
    
    def tokenize(self, text: str) -> list[str]:
        return text.split()
    
    def detokenize(self, tokens: list[str]):
        return " ".join(tokens)
    
    def chunkify_clean_text(self, clean_text: str) -> list[str]:
        tokens = self.tokenize(clean_text)
        total_tokens = len(tokens) 
        start = 0
        chunks = []
        while start < total_tokens:
            end = start + self.max_tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.detokenize(chunk_tokens)
            chunks.append(chunk_text)

            start = end-self.overlap
            if self.overlap >= self.max_tokens: 
                raise ValueError("Overlap must be smaller than max_tokens")
        return chunks 
    
    def convert_to_embeddings(self, chunk_text: str) -> list[float]:
        embeddings = self.embedding_model.encode(chunk_text)
        return embeddings.tolist()
    
    def to_document_chunk_object(self, chunks: list[str]) -> list[document_chunk.DocumentChunk]:
        document_chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk = document_chunk.DocumentChunk(
                document_id=self.document_id, 
                metadata_id=self.document_metadata_id, 
                index = i,
                text=chunk_text,
                tokens=len(chunk_text.split()),
                embeddings=self.convert_to_embeddings(chunk_text))
            document_chunk_objects.append(chunk)
        return document_chunk_objects
    
    def save_document_chunk_object(
            self,
            db: Session,
            document_chunk_objects: list[document_chunk.DocumentChunk]) -> bool:
        try:
            db.add_all(document_chunk_objects)
            db.commit()
            return True
        except Exception as e:
            print(f"An error occured while saving the document chunk objects:\n{e}")
            return False
    
    def delete_document_from_local_storage(db: Session, document: document.Document):
        if not document:
            raise ValueError(f"Document with id: {document.id} not found")
        try: 
            os.remove(document.file_path)
            setattr(document, "file_path", None)
            db.add(document)
            db.commit()
        except Exception as e:
            raise RuntimeError("An error occured while deleting document from local storage.")
            print(f"Error message: {e}")

    def document_processing_pipeline(self, db: Session) -> bool:
        text = self.extract_text_from_pdf()
        clean_text = self.clean_raw_text(text)
        chunks = self.chunkify_clean_text(clean_text)
        chunk_objects = self.to_document_chunk_object(chunks)
        save_chunks_result = self.save_document_chunk_object(db, chunk_objects)
        self.delete_document_from_local_storage(db, document)
        return chunk_objects, len(chunk_objects), save_chunks_result 