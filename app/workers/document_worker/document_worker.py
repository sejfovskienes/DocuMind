import os 
import re
import sys
import fitz
import unicodedata
from time import sleep
from pathlib import Path
from functools import wraps
from datetime import datetime
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

from app.services import (
    task_service, 
    document_service, 
    document_chunk_service
    )
from app.database import get_session
from app.models import document, document_chunk
from app.core.enum import worker_task_type, worker_task_status
from app.vector_database.qdrant_client import DocumindQdrantClient


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
    def __init__(self, max_tokens: int = 100, overlap: int = 90):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.embedding_model = EMBEDDING_MODEL
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        del self.embedding_model
    
    def document_worker_print(self, text: str) -> None: 
        print("\033[92m {}\033[00m".format("[DocumentWorker]" + f"\t{text}"))

    def delete_finished_doc_proc_tasks(self, db: Session) -> None:
        finished_doc_proc_tasks = task_service.get_finished_tasks(
            db, 
            worker_task_type.WorkerTaskType.DOCUMENT_PROCESSING
        )
        if len(finished_doc_proc_tasks) == 0:
            self.document_worker_print("[info]\tFound 0 tasks for cleaning")
        db.delete(finished_doc_proc_tasks)
        db.commit()
        count_deleted = len(finished_doc_proc_tasks)
        message = f"[info]\tDeleted: {count_deleted} tasks from database"
        self.document_worker_print(message)
    
    def extract_document_content(
            self, 
            document_file_path: str | Path) -> str:
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
    
    def chunkify_clean_text(
            self, 
            clean_text: str) -> list[str]:
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
                message = "Overlap must be smaller than max_tokens"
                raise ValueError(message)
        return chunks 
    
    def convert_to_embeddings(
            self, 
            chunk_text: str) -> list[float]:
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
        
    def delete_document_from_local_storage(
            self, 
            db: Session, 
            document: document.Document):
        if not document:
            raise ValueError(f"Document with id: {document.id} not found")
        try: 
            os.remove(document.file_path)
            setattr(document, "file_path", None)
            db.add(document)
            db.commit()
        except Exception as e:
            message = f"An error occured while deleting document from local storage.\nError message: {e}"
            raise RuntimeError(message)
        
    def upload_embeddings(
            self,
            db: Session, 
            document:document.Document) -> None:
        user_id = document.user_id
        payload = {"user_id": user_id}
        document_chunks = document_chunk_service.get_chunks_by_document_id(document.id)
        client = DocumindQdrantClient(user_id)
        try: 
            for chunk in document_chunks:
                client.upsert_embedding(document_chunk, payload)
        except Exception as e:
            raise RuntimeError(f"An error occured while uploading embeddings!:{e}")

    def process_document(
            self, 
            db: Session, 
            document: document.Document) -> None:
        self.document_id = document.id
        document_content = self.extract_document_content(document.file_path)
        clean_text = self.clean_document_content(document_content)
        document_chunks = self.chunkify_clean_text(clean_text)
        chunk_objects = self.to_document_chunk_object(document_chunks)
        #--- returns bool for the writing to database
        save_document_chunks = self.save_document_chunk_object(db, chunk_objects)
        return save_document_chunks
    
    def worker_loop(self):
        db = get_session()
        self.document_worker_print("Document worker started...")
        self.delete_finished_doc_proc_tasks(db)
        self.document_worker_print("Waiting for tasks...")
        try: 
            while True:
                worker_task = task_service.get_new_task(
                    db, task_type=worker_task_type.WorkerTaskType.DOCUMENT_PROCESSING)
                if not worker_task:
                    db.close()
                    self.document_worker_print("No tasks, worker going to sleep mode.")
                    sleep(1)
                    continue
                try:
                    self.document_worker_print(
                        f"\tProcessing task with id: {worker_task.id}, with type: {worker_task.task_type}")
                    task_service.update_worker_task(
                        db, 
                        worker_task, 
                        {"status": worker_task_status.WorkerTaskStatus.PROCESSING})
                    document = document_service.get_document_by_id(db, worker_task.payload["document_id"])
                    result = self.process_document(db, document)
                    
                except Exception as e:
                    task_service.update_worker_task(
                        db, 
                        worker_task, 
                        {"status": worker_task_status.WorkerTaskStatus.FAILED})
                    self.document_worker_print(f"An error occured while processing the task: {e}")
                finally:
                    task_service.update_worker_task(
                        db, 
                        worker_task, 
                        {"status": worker_task_status.WorkerTaskStatus.FINISHED,
                        "finshed_at": datetime.utcnow()})
                    self.document_worker_print(
                        f"\tProcessing task for document with id:{document.id} is finished: {result}")
                    self.delete_document_from_local_storage(db, document)
        except KeyboardInterrupt:
            self.document_worker_print("Worker stopped.\n\n")
            self.document_worker_print("="*55)
            sys.exit(0)
        