from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.base.config import WorkerConfig
from app.base.extensions import run_worker_loop
from app.core.enum import WorkerTaskType
from app.database_extension import get_session
from app.ml import ONNXNERModel, TransformersNERModel
from app.models import DocumentChunk, WorkerTask
from app.services import document_chunk_service, worker_task_service
from app.workers.worker_task_runner import run_task


class NERWorker:
    def __init__(
        self,
        model_path: str | Path | None = None,
        model: Any | None = None,
        onnx_model: ONNXNERModel | None = None,
    ):
        self.model = model if model is not None else TransformersNERModel()
        self.onnx_model = onnx_model or (
            ONNXNERModel(model_path) if model_path is not None else None
        )

    def ner_worker_print(self, text: str) -> None:
        print(f"[NERWorker] {text}")

    def delete_finished_tasks(self, db: Session) -> None:
        tasks = worker_task_service.get_finished_tasks(
            db, WorkerTaskType.ENTITY_EXTRACTION
        )
        for task in tasks:
            db.delete(task)
        if tasks:
            db.commit()

    def convert_text_to_tokens(self, chunk: DocumentChunk) -> dict[str, Any]:
        if self.onnx_model is None:
            raise RuntimeError("ONNX model path was not configured")
        return self.onnx_model.tokenize(chunk.text)

    def extract_named_entities(self, inputs: dict[str, Any]) -> Any:
        if self.onnx_model is None:
            raise RuntimeError("ONNX model path was not configured")
        return self.onnx_model.infer(inputs)

    def convert_ids_to_tokens(self, pred_ids: Any, inputs: dict[str, Any]) -> Any:
        if self.onnx_model is None:
            raise RuntimeError("ONNX model path was not configured")
        return self.onnx_model.tokens(inputs)

    def extract_entities(self, chunk: DocumentChunk) -> list[dict[str, Any]]:
        return self.model.extract(chunk.text)

    def ner_processing(self, db: Session, ner_task: WorkerTask) -> None:
        document_id = int(ner_task.payload["document_id"])
        chunks = document_chunk_service.get_chunks_by_document_id(db, document_id)
        if not chunks:
            raise ValueError(f"No chunks found for document {document_id}")
        for chunk in chunks:
            entities = self.extract_entities(chunk)
            document_chunk_service.update_document_chunk(
                db, chunk, {"ner_entities": entities}
            )

    def _process_task(self, db: Session, task: WorkerTask) -> bool:
        completed = run_task(db, task, lambda: self.ner_processing(db, task))
        if not completed:
            self.ner_worker_print(f"Entity extraction task {task.id} failed")
        return completed

    def ner_worker_loop(self) -> None:
        self.ner_worker_print("NER worker started")
        run_worker_loop(
            create_session=get_session,
            fetch_task=lambda db: worker_task_service.get_new_task(
                db, WorkerTaskType.ENTITY_EXTRACTION
            ),
            process_task=self._process_task,
            cleanup_finished=self.delete_finished_tasks,
            interval_seconds=WorkerConfig.NER_POLL_INTERVAL_SECONDS,
            log=self.ner_worker_print,
        )
