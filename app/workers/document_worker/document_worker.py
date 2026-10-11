import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import fitz
from sqlalchemy.orm import Session

from app.base.config import ModelConfig, WorkerConfig
from app.base.extensions import (
    chunk_document_text,
    clean_document_text,
    run_worker_loop,
)
from app.core.enum import WorkerTaskType
from app.database_extension import get_session
from app.ml import SentenceTransformerEmbeddingModel
from app.models import Document, DocumentChunk, WorkerTask
from app.services import document_service, worker_task_service
from app.workers.worker_task_runner import run_task


class DocumentWorker:
    def __init__(
        self,
        max_tokens: int = WorkerConfig.DOC_CHUNK_SIZE,
        overlap: int = WorkerConfig.DOC_CHUNK_OVERLAP,
        embedding_model: Any | None = None,
        qdrant_client_factory: Callable[..., Any] | None = None,
    ):
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if overlap < 0 or overlap >= max_tokens:
            raise ValueError("overlap must be between zero and max_tokens")
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.embedding_model = (
            embedding_model
            if embedding_model is not None
            else SentenceTransformerEmbeddingModel(ModelConfig.EMBEDDING_MODEL_NAME)
        )
        self.qdrant_client_factory = qdrant_client_factory

    def document_worker_print(self, text: str) -> None:
        print(f"[DocumentWorker] {text}")

    def delete_finished_doc_proc_tasks(self, db: Session) -> None:
        tasks = worker_task_service.get_finished_tasks(
            db, WorkerTaskType.DOCUMENT_PROCESSING
        )
        for task in tasks:
            db.delete(task)
        if tasks:
            db.commit()

    def extract_document_content(self, document_file_path: str | Path) -> str:
        with fitz.open(document_file_path) as pdf:
            return "".join(page.get_text("text") for page in pdf)

    def clean_document_content(self, text: str) -> str:
        return clean_document_text(text)

    def tokenize(self, text: str) -> list[str]:
        return text.split()

    def detokenize(self, tokens: list[str]) -> str:
        return " ".join(tokens)

    def chunkify_clean_text(self, clean_text: str) -> list[str]:
        return chunk_document_text(clean_text, self.max_tokens, self.overlap)

    def convert_to_embeddings(self, chunk_text: str) -> list[float]:
        return self.embedding_model.embed(chunk_text)

    def to_document_chunk_object(
        self, chunks: list[str], document_id: int
    ) -> list[DocumentChunk]:
        return [
            DocumentChunk(
                document_id=document_id,
                index=index,
                text=chunk_text,
                tokens=len(chunk_text.split()),
                embeddings=self.convert_to_embeddings(chunk_text),
            )
            for index, chunk_text in enumerate(chunks)
        ]

    def save_document_chunk_object(
        self, db: Session, chunks: list[DocumentChunk]
    ) -> bool:
        try:
            db.add_all(chunks)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def delete_document_from_local_storage(
        self, db: Session, document: Document
    ) -> None:
        if document is None:
            raise ValueError("Document was not found")
        try:
            os.remove(document.file_path)
            document.file_path = None
            db.add(document)
            db.commit()
        except Exception as error:
            db.rollback()
            raise RuntimeError(
                "Could not remove the processed document from local storage"
            ) from error

    def upload_embeddings(self, chunks: list[DocumentChunk]) -> bool:
        if not chunks:
            return False
        client_factory = self.qdrant_client_factory
        if client_factory is None:
            from app.vector_database.qdrant_client import DocumindQdrantClient

            client_factory = DocumindQdrantClient
        client = client_factory(chunks[0].document.user_id)
        embeddings = [chunk.embeddings for chunk in chunks]
        try:
            return bool(client.upsert_embeddings(embeddings, chunks))
        finally:
            qdrant_client = getattr(client, "qdrant_client", client)
            close = getattr(qdrant_client, "close", None)
            if close is not None:
                close()

    def _get_or_create_document_chunks(
        self, db: Session, document: Document, chunk_texts: list[str]
    ) -> list[DocumentChunk]:
        existing_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.index)
            .all()
        )
        if existing_chunks:
            matches_source = len(existing_chunks) == len(chunk_texts) and all(
                chunk.index == index and chunk.text == text
                for index, (chunk, text) in enumerate(zip(existing_chunks, chunk_texts))
            )
            if not matches_source:
                raise RuntimeError(
                    f"Persisted chunks for document {document.id} do not match "
                    "the current source; refusing to append duplicates."
                )
            if any(not chunk.embeddings for chunk in existing_chunks):
                raise RuntimeError(
                    f"Persisted chunks for document {document.id} are missing embeddings."
                )
            return existing_chunks

        chunk_objects = self.to_document_chunk_object(chunk_texts, document.id)
        if not self.save_document_chunk_object(db, chunk_objects):
            raise RuntimeError("Could not save document chunks")
        return chunk_objects

    def process_document(self, db: Session, document: Document) -> bool:
        if document is None:
            raise ValueError("Document was not found")
        if not document.file_path:
            raise ValueError("Document has no local file path")
        content = self.clean_document_content(
            self.extract_document_content(document.file_path)
        )
        if not content:
            raise ValueError("Document contains no extractable text")
        chunk_texts = self.chunkify_clean_text(content)
        if not chunk_texts:
            raise ValueError("Document contains no chunkable text")
        chunk_objects = self._get_or_create_document_chunks(db, document, chunk_texts)
        if not self.upload_embeddings(chunk_objects):
            raise RuntimeError("Could not upload document embeddings")
        return True

    def _process_task(self, db: Session, task: WorkerTask) -> bool:
        task_id = task.id
        processed_documents: list[Document] = []

        def process() -> bool:
            document = document_service.get_document_by_id(
                db, task.payload["document_id"]
            )
            processed_documents.append(document)
            return self.process_document(db, document)

        completed = run_task(db, task, process)
        if completed:
            try:
                self.delete_document_from_local_storage(db, processed_documents[0])
            except Exception as error:
                self.document_worker_print(
                    f"Processed document cleanup failed ({type(error).__name__})"
                )
        else:
            self.document_worker_print(f"Document task {task_id} failed")
        return completed

    def worker_loop(self) -> None:
        self.document_worker_print("Document worker started")
        run_worker_loop(
            create_session=get_session,
            fetch_task=lambda db: worker_task_service.get_new_task(
                db, WorkerTaskType.DOCUMENT_PROCESSING
            ),
            process_task=self._process_task,
            cleanup_finished=self.delete_finished_doc_proc_tasks,
            interval_seconds=WorkerConfig.DOCUMENT_POLL_INTERVAL_SECONDS,
            log=self.document_worker_print,
        )
