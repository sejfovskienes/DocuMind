import os 
import re
import fitz
import unicodedata
from time import sleep
from pathlib import Path
from functools import wraps
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

from app.database import get_session
from app.models import document, document_chunk
from app.services import task_service, document_service

EMBEDDING_MODEL = SentenceTransformer("all-mpnet-base-v2")

def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
            return instances[cls]
    return get_instance

@singleton
class DocumentWorker:
    def __init__(self, max_tokens: int = 200, overlap: int = 150):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.embedding_model = EMBEDDING_MODEL
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        del self.embedding_model
    
    def document_worker_print(self, text: str) -> None: 
        print("\033[92m {}\033[00m".format(text))
    
    def extract_document_content(self, document_file_path: str | Path) -> str:
        content = ""
        with fitz.open(document_file_path) as pdf:
            for page in pdf:
                content += page.get_text("text")
        return content
    
    def clean_document_content(self, text: str) -> str:
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
    
    def to_document_chunk_object(
            self,
            chunks: list[str]) -> list[document_chunk.DocumentChunk]:
        document_chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk = document_chunk.DocumentChunk(
                document_id=self.document_id, 
                # metadata_id=self.document_metadata_id, 
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
        
    def delete_document_from_local_storage(self, db: Session, document: document.Document):
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

    def process_document(self, db: Session, document: document.Document) -> None:
        self.document_id = document.id
        document_content = self.extract_document_content(document.file_path)
        clean_text = self.clean_document_content(document_content)
        document_chunks = self.chunkify_clean_text(clean_text)
        chunk_objects = self.to_document_chunk_object(document_chunks)

        save_document_chunks = self.save_document_chunk_object(db, chunk_objects) #--- returns bool for the writing to database
        self.delete_document_from_local_storage(db, document)
        return save_document_chunks
    
    def worker_loop(self):
        self.document_worker_print("Document worker started and waiting for tasks...")
        while True:
            db = get_session()
            worker_task = task_service.get_new_task(db, task_type="document_processing")

            if not worker_task:
                db.close()
                self.document_worker_print("No tasks, worker going to sleep mode.")
                sleep(1)
                continue

            try:
                self.document_worker_print(
                    f"Processing task with id: {worker_task.id}, with type: {worker_task.task_type}")
                task_service.update_worker_task(db, worker_task, {"status": "processing"})
                document = document_service.get_document_by_id(db, worker_task.payload["document_id"])
                result = self.process_document(db, document)
                self.document_worker_print(f"Processing task for document with id:{document.id} is finished: {result}")
            except Exception as e:
                task_service.update_worker_task(db, worker_task, {"status": "queued"})
                self.document_worker_print(f"An error occured while processing the task: {e}")