import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database_extension import Base, get_database_session
from app.main import app
from app.models import Document, DocumentMetadata, User, WorkerTask
from app.routes import document_router as document_routes
from app.routes.auth_router import get_current_user


class ApiOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            owner = User(
                email="owner@example.test", full_name="Owner", hashed_password="unused"
            )
            other = User(
                email="other@example.test", full_name="Other", hashed_password="unused"
            )
            db.add_all([owner, other])
            db.flush()
            self.owner_id, self.other_id = owner.id, other.id
            document = Document(user_id=owner.id, filename="sample.pdf")
            db.add(document)
            db.flush()
            self.document_id = document.id
            db.add(
                DocumentMetadata(
                    document_id=document.id, global_entities={"PER": ["Ada"]}
                )
            )
            task = WorkerTask(
                payload={"document_id": document.id}, task_type="ENTITY_EXTRACTION"
            )
            db.add(task)
            db.flush()
            self.task_id = task.id
            db.commit()

        def get_session():
            with Session(self.engine) as db:
                yield db

        self.user = SimpleNamespace(id=self.owner_id)
        self.previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_database_session] = get_session
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides = self.previous_overrides
        self.engine.dispose()

    def test_document_path_parameter_works_without_extra_query_parameter(self):
        response = self.client.get(f"/documents/get-document/{self.document_id}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(next(iter(response.json().values()))["id"], self.document_id)

    def test_other_user_cannot_read_delete_or_queue_document_work(self):
        self.user.id = self.other_id
        requests = [
            ("get", f"/documents/get-document/{self.document_id}"),
            ("get", f"/documents/delete-document/{self.document_id}"),
            ("post", f"/nlp/extract-entities/{self.document_id}"),
            ("get", f"/nlp/summarize/{self.document_id}"),
            ("get", f"/nlp/get-task/{self.task_id}"),
            ("get", f"/process-document/get-document-metadata/{self.document_id}"),
        ]
        for method, url in requests:
            with self.subTest(url=url):
                response = self.client.request(method, url)
                self.assertEqual(response.status_code, 404, response.text)
        with Session(self.engine) as db:
            self.assertEqual(db.query(Document).count(), 1)
            self.assertEqual(db.query(WorkerTask).count(), 1)

    def test_owner_can_queue_ner_and_read_serialized_task(self):
        response = self.client.post(f"/nlp/extract-entities/{self.document_id}")
        self.assertEqual(response.status_code, 200, response.text)
        task = response.json()["ner_task"]
        self.assertEqual(task["status"], "QUEUED")
        self.assertIn("finshed_at", task)
        response = self.client.get(f"/nlp/get-task/{task['id']}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["worker_task"]["id"], task["id"])

    def test_document_metadata_uses_serializable_schema(self):
        response = self.client.get(
            f"/process-document/get-document-metadata/{self.document_id}"
        )
        self.assertEqual(response.status_code, 200, response.text)
        metadata = response.json()["Processed document metadata"]
        self.assertEqual(metadata["document_id"], self.document_id)
        self.assertEqual(metadata["global_entities"], {"PER": ["Ada"]})

    def test_upload_returns_document_and_queued_task_with_existing_keys(self):
        with TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir)
            with patch.object(
                document_routes, "ensure_upload_dir", return_value=upload_dir
            ):
                response = self.client.post(
                    "/documents/upsert-file",
                    files={
                        "file": ("sample.pdf", b"document bytes", "application/pdf")
                    },
                )
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
            self.assertEqual(set(result), {"message", "document", "worker_task"})
            self.assertEqual(result["document"]["user_id"], self.owner_id)
            self.assertEqual(result["worker_task"]["status"], "QUEUED")
            self.assertEqual(
                result["worker_task"]["payload"]["document_id"],
                result["document"]["id"],
            )
            self.assertEqual(len(list(upload_dir.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
