import asyncio
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.enum import WorkerTaskType
    from app.database_extension import Base
    from app.models import Document, DocumentChunk, DocumentMetadata, User, WorkerTask
    from app.routes import document_router as document_routes
    from app.schemas import DocumentChunkSchema, WorkerTaskSchema
    from app.services import (
        document_metadata_service,
        document_service,
        worker_task_service,
    )
except ImportError as exc:
    raise unittest.SkipTest(f"Service dependencies are unavailable: {exc}")


class ServiceOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self) -> None:
        self.db = Session(self.engine)
        self.db.query(WorkerTask).delete()
        self.db.query(DocumentChunk).delete()
        self.db.query(DocumentMetadata).delete()
        self.db.query(Document).delete()
        self.db.query(User).delete()
        self.db.commit()

        self.owner = User(
            email="owner@example.test",
            full_name="Owner",
            hashed_password="unused",
        )
        self.other_user = User(
            email="other@example.test",
            full_name="Other",
            hashed_password="unused",
        )
        self.db.add_all([self.owner, self.other_user])
        self.db.commit()
        self.db.refresh(self.owner)
        self.db.refresh(self.other_user)

        self.document = Document(
            user_id=self.owner.id,
            filename="sample.pdf",
            file_path="sample.pdf",
        )
        self.db.add(self.document)
        self.db.commit()
        self.db.refresh(self.document)

    def tearDown(self) -> None:
        self.db.close()

    def test_document_lookup_hides_documents_from_other_users(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            document_service.get_document_by_id(
                self.db,
                self.document.id,
                user_id=self.other_user.id,
            )
        self.assertEqual(raised.exception.status_code, 404)

    def test_task_lookup_checks_document_ownership(self) -> None:
        task = WorkerTask(
            payload={"document_id": self.document.id},
            task_type=WorkerTaskType.ENTITY_EXTRACTION,
        )
        worker_task_service.save_worker_task(self.db, task)

        with self.assertRaises(HTTPException) as raised:
            worker_task_service.get_task_by_id(
                self.db,
                task.id,
                user_id=self.other_user.id,
            )
        self.assertEqual(raised.exception.status_code, 404)

        accessible = worker_task_service.get_task_by_id(
            self.db,
            task.id,
            user_id=self.owner.id,
        )
        self.assertEqual(accessible.id, task.id)

    def test_task_lookup_rejects_conflicting_payload_owners(self) -> None:
        task = WorkerTask(
            payload={
                "document_id": self.document.id,
                "user_id": self.other_user.id,
            },
            task_type=WorkerTaskType.SUMMARIZATION,
        )
        worker_task_service.save_worker_task(self.db, task)

        for user in (self.owner, self.other_user):
            with self.subTest(user_id=user.id), self.assertRaises(HTTPException):
                worker_task_service.get_task_by_id(self.db, task.id, user_id=user.id)

    def test_metadata_getter_uses_stored_global_entities(self) -> None:
        from app.models import DocumentMetadata

        metadata = DocumentMetadata(
            document_id=self.document.id,
            global_entities={"PERSON": ["Ada"]},
        )
        self.db.add(metadata)
        self.db.commit()

        self.assertEqual(
            document_metadata_service.get_named_entities(
                self.db,
                self.document.id,
            ),
            {"PERSON": ["Ada"]},
        )

    def test_worker_task_schema_reads_orm_values(self) -> None:
        task = WorkerTask(
            payload={"document_id": self.document.id},
            task_type=WorkerTaskType.ENTITY_EXTRACTION,
        )
        worker_task_service.save_worker_task(self.db, task)

        schema = WorkerTaskSchema.model_validate(task)
        self.assertEqual(schema.id, task.id)
        self.assertEqual(schema.task_type, WorkerTaskType.ENTITY_EXTRACTION)

    def test_document_chunk_schema_accepts_legacy_and_structured_entities(self) -> None:
        from app.models import DocumentChunk

        for entities in ('["Ada"]', ["Ada"]):
            with self.subTest(entities=entities):
                chunk = DocumentChunk(
                    id=1,
                    document_id=self.document.id,
                    index=0,
                    text="Ada Lovelace",
                    tokens=2,
                    ner_entities=entities,
                )
                schema = DocumentChunkSchema.model_validate(chunk)
                self.assertEqual(schema.ner_entities, entities)
                self.assertIsNone(schema.metadata_id)

    def test_task_claim_moves_queued_task_to_processing(self) -> None:
        task = WorkerTask(
            payload={"document_id": self.document.id},
            task_type=WorkerTaskType.ENTITY_EXTRACTION,
        )
        worker_task_service.save_worker_task(self.db, task)

        second = WorkerTask(
            payload={"document_id": self.document.id},
            task_type=WorkerTaskType.ENTITY_EXTRACTION,
        )
        worker_task_service.save_worker_task(self.db, second)

        claimed = worker_task_service.get_new_task(
            self.db,
            WorkerTaskType.ENTITY_EXTRACTION,
        )

        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.status, "PROCESSING")
        self.assertEqual(claimed.id, task.id)
        next_claim = worker_task_service.get_new_task(
            self.db,
            WorkerTaskType.ENTITY_EXTRACTION,
        )
        self.assertEqual(next_claim.id, second.id)
        self.assertIsNone(
            worker_task_service.get_new_task(self.db, WorkerTaskType.ENTITY_EXTRACTION)
        )

    def test_task_save_rolls_back_after_commit_failure(self) -> None:
        db = Mock()
        db.commit.side_effect = RuntimeError("commit failed")

        with self.assertRaises(RuntimeError):
            worker_task_service.save_worker_task(db, WorkerTask(payload={}))

        db.rollback.assert_called_once_with()

    def test_task_claim_rechecks_queued_status_after_candidate_read(self) -> None:
        candidate = SimpleNamespace(id=42)
        candidate_query = Mock()
        candidate_query.filter.return_value = candidate_query
        candidate_query.order_by.return_value = candidate_query
        candidate_query.first.return_value = candidate
        claim_query = Mock()
        claim_query.filter.return_value = claim_query
        claim_query.update.return_value = 0
        empty_query = Mock()
        empty_query.filter.return_value = empty_query
        empty_query.order_by.return_value = empty_query
        empty_query.first.return_value = None
        db = Mock()
        db.query.side_effect = [candidate_query, claim_query, empty_query]

        self.assertIsNone(
            worker_task_service.get_new_task(db, WorkerTaskType.ENTITY_EXTRACTION)
        )

        claim_predicates = claim_query.filter.call_args.args
        self.assertEqual(len(claim_predicates), 2)
        self.assertIn("worker_tasks.status =", str(claim_predicates[1]))
        claim_query.update.assert_called_once()
        db.rollback.assert_called_once_with()

    def test_worker_task_update_rolls_back_after_commit_failure(self) -> None:
        db = Mock()
        db.commit.side_effect = RuntimeError("commit failed")
        task = WorkerTask(payload={}, task_type=WorkerTaskType.ENTITY_EXTRACTION)

        with self.assertRaises(RuntimeError):
            worker_task_service.update_worker_task(db, task, {"status": "FINISHED"})

        db.rollback.assert_called_once_with()

    def test_upload_enqueue_failure_rolls_back_document_and_file(self) -> None:
        document_count = self.db.query(Document).count()
        with TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir)
            upload = document_routes.UploadFile(
                filename="sample.pdf",
                file=BytesIO(b"document bytes"),
            )
            with (
                patch.object(
                    document_routes,
                    "ensure_upload_dir",
                    return_value=upload_dir,
                ),
                patch.object(
                    document_routes.worker_task_service,
                    "save_worker_task",
                    side_effect=RuntimeError("queue unavailable"),
                ),
            ):
                with self.assertRaises(RuntimeError):
                    asyncio.run(
                        document_routes.upload_file(upload, self.db, self.owner)
                    )

            self.assertEqual(self.db.query(Document).count(), document_count)
            self.assertEqual(list(upload_dir.iterdir()), [])

    def test_refresh_failure_after_upload_commit_keeps_source_and_rows(self) -> None:
        document_count = self.db.query(Document).count()
        with TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir)
            upload = document_routes.UploadFile(
                filename="sample.pdf", file=BytesIO(b"document bytes")
            )
            with (
                patch.object(
                    document_routes, "ensure_upload_dir", return_value=upload_dir
                ),
                patch.object(
                    self.db, "refresh", side_effect=RuntimeError("refresh failed")
                ),
                self.assertRaisesRegex(RuntimeError, "refresh failed"),
            ):
                asyncio.run(document_routes.upload_file(upload, self.db, self.owner))
            self.assertEqual(self.db.query(Document).count(), document_count + 1)
            self.assertEqual(self.db.query(WorkerTask).count(), 1)
            files = list(upload_dir.iterdir())
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].read_bytes(), b"document bytes")

    def test_ner_persists_structured_entities_in_json_column(self) -> None:
        from app.models import DocumentChunk
        from app.workers.ner_worker import NERWorker

        chunk = DocumentChunk(
            document_id=self.document.id, index=0, text="Ada", tokens=1
        )
        self.db.add(chunk)
        self.db.commit()
        entities = [{"entity": "B-PER", "word": "Ada", "score": 0.9}]
        worker = NERWorker(model=SimpleNamespace(extract=lambda _text: entities))
        worker.ner_processing(
            self.db, SimpleNamespace(payload={"document_id": self.document.id})
        )
        self.db.expire_all()
        self.assertEqual(self.db.get(DocumentChunk, chunk.id).ner_entities, entities)


if __name__ == "__main__":
    unittest.main()
