import re
import fitz
import unicodedata
from sqlalchemy.orm import Session

from app.models import document, document_chunk

#--- TODO: in v1.1 add OCR and table data analysis.

class DocumentWorker:
    def __init__(self, document: document.Document, max_tokens: int = 500, overlap: int = 500):
        self.document_path = document.file_path
        self.document_id = document.id
        self.document_metadata_id = document.processed_document_metadata.id
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.embedding_model = None
    
    def __enter__(self):
        from sentence_transformers import SentenceTransformer
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
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
            if start < 0: 
                start = 0
        return chunks 
    
    def convert_to_embeddings(self, chunk_text: str) -> list[float]:
        embeddings = self.embedding_model.encode(chunk_text)
        return embeddings.tolist()
    
    def to_document_chunk_object(self, chunks: list[str]) -> list[document_chunk.DocumentChunk]:
        document_chunk_objects = []
        for chunk_text, i in enumerate(chunks):
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
        
    def document_processing_pipeline(self) -> bool:
        text = self.extract_text_from_pdf()
        clean_text = self.clean_raw_text(text)
        chunks = self.chunkify_clean_text(clean_text)
        chunk_objects = self.to_document_chunk_object(chunks)
        result = self.save_document_chunk_object(chunk_objects)
        return self.document_id, chunk_objects, len(chunk_objects), result 