import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.base.extensions.document_extension import chunk_document_text
from app.base.extensions.worker_extension import run_worker_loop
from app.core.enum import WorkerTaskStatus
from app.workers.document_worker.document_worker import DocumentWorker
from app.workers.worker_task_runner import run_task


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def add(self, _item):
        pass

    def commit(self):
        self.commits += 1

    def refresh(self, _item):
        pass

    def rollback(self):
        self.rollbacks += 1


class TaskRunnerTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        self.task = SimpleNamespace(status=None, finshed_at=None)

    def test_success_marks_task_finished(self):
        result = run_task(self.db, self.task, lambda: True)

        self.assertTrue(result)
        self.assertEqual(self.task.status, WorkerTaskStatus.FINISHED)
        self.assertIsNotNone(self.task.finshed_at)

    def test_false_result_marks_task_failed(self):
        result = run_task(self.db, self.task, lambda: False)

        self.assertFalse(result)
        self.assertEqual(self.task.status, WorkerTaskStatus.FAILED)
        self.assertIsNone(self.task.finshed_at)
        self.assertEqual(self.db.rollbacks, 1)

    def test_exception_marks_task_failed(self):
        def fail():
            raise RuntimeError("offline failure")

        result = run_task(self.db, self.task, fail)

        self.assertFalse(result)
        self.assertEqual(self.task.status, WorkerTaskStatus.FAILED)
        self.assertIsNone(self.task.finshed_at)


class DocumentChunkingTests(unittest.TestCase):
    def test_chunking_stops_after_final_word(self):
        words = [f"word{index}" for index in range(150)]

        chunks = chunk_document_text(" ".join(words))

        self.assertEqual(len(chunks), 6)
        self.assertTrue(all(len(chunk.split()) == 100 for chunk in chunks))
        self.assertEqual(chunks[-1].split()[-1], words[-1])

    def test_empty_text_produces_no_chunks(self):
        self.assertEqual(chunk_document_text(""), [])


class WorkerLoopTests(unittest.TestCase):
    def test_idle_sessions_close_before_sleep(self):
        sessions = []

        class Session:
            def __init__(self):
                self.closed = False
                sessions.append(self)

            def close(self):
                self.closed = True

        def stop_after_one_idle_poll(_interval):
            self.assertTrue(sessions[-1].closed)
            raise StopIteration

        with self.assertRaises(StopIteration):
            run_worker_loop(
                create_session=Session,
                fetch_task=lambda _session: None,
                process_task=lambda _session, _task: None,
                cleanup_finished=lambda _session: None,
                interval_seconds=1,
                log=lambda _message: None,
                sleep_fn=stop_after_one_idle_poll,
            )

        self.assertEqual(len(sessions), 2)
        self.assertTrue(all(session.closed for session in sessions))


class RetrySession(FakeSession):
    def __init__(self):
        super().__init__()
        self.chunks = []
        self.next_chunk_id = 1
        self.add_all_calls = 0

    def query(self, _model):
        return FakeChunkQuery(self.chunks)

    def add_all(self, chunks):
        self.add_all_calls += 1
        for chunk in chunks:
            chunk.id = self.next_chunk_id
            self.next_chunk_id += 1
            self.chunks.append(chunk)


class FakeChunkQuery:
    def __init__(self, chunks):
        self.chunks = chunks

    def filter(self, _condition):
        return self

    def order_by(self, _column):
        return self

    def all(self):
        return sorted(self.chunks, key=lambda chunk: chunk.index)


class DocumentRetryTests(unittest.TestCase):
    def test_qdrant_failure_retry_reuses_chunks_and_cleans_only_on_success(self):
        document = SimpleNamespace(id=7, user_id=3, file_path="source.pdf")
        db = RetrySession()
        embed_calls = []
        upload_results = iter([False, True])
        closed_clients = []

        class EmbeddingModel:
            def embed(self, text):
                embed_calls.append(text)
                return [float(len(text))]

        class QdrantClient:
            def __init__(self, _user_id):
                self.qdrant_client = self

            def upsert_embeddings(self, _embeddings, chunks):
                self.chunk_ids = [chunk.id for chunk in chunks]
                return next(upload_results)

            def close(self):
                closed_clients.append(True)

        worker = DocumentWorker(
            max_tokens=4,
            overlap=2,
            embedding_model=EmbeddingModel(),
            qdrant_client_factory=QdrantClient,
        )
        cleanup = Mock()
        task_one = SimpleNamespace(
            id=101, status=None, finshed_at=None, payload={"document_id": document.id}
        )
        task_two = SimpleNamespace(
            id=102, status=None, finshed_at=None, payload={"document_id": document.id}
        )

        with (
            patch.object(
                worker,
                "extract_document_content",
                return_value="one two three four five six",
            ),
            patch.object(
                worker,
                "to_document_chunk_object",
                side_effect=lambda chunks, document_id: [
                    SimpleNamespace(
                        document_id=document_id,
                        index=index,
                        text=chunk_text,
                        embeddings=worker.convert_to_embeddings(chunk_text),
                        document=document,
                    )
                    for index, chunk_text in enumerate(chunks)
                ],
            ),
            patch.object(worker, "delete_document_from_local_storage", cleanup),
            patch(
                "app.workers.document_worker.document_worker.document_service.get_document_by_id",
                return_value=document,
            ),
        ):
            self.assertFalse(worker._process_task(db, task_one))
            cleanup.assert_not_called()
            first_chunk_ids = [chunk.id for chunk in db.chunks]

            self.assertTrue(worker._process_task(db, task_two))

        self.assertEqual(db.add_all_calls, 1)
        self.assertEqual(len(db.chunks), 2)
        self.assertEqual(len(embed_calls), 2)
        self.assertEqual(first_chunk_ids, [chunk.id for chunk in db.chunks])
        self.assertEqual(len(closed_clients), 2)
        cleanup.assert_called_once_with(db, document)

    def test_mismatched_persisted_chunks_fail_without_appending(self):
        document = SimpleNamespace(id=8, user_id=3, file_path="source.pdf")
        db = RetrySession()
        db.chunks.append(SimpleNamespace(index=0, text="old content", embeddings=[0.1]))
        worker = DocumentWorker(
            max_tokens=4,
            overlap=2,
            embedding_model=SimpleNamespace(embed=lambda _text: [0.1]),
        )

        with (
            patch.object(
                worker, "extract_document_content", return_value="new source content"
            ),
            self.assertRaisesRegex(RuntimeError, "do not match"),
        ):
            worker.process_document(db, document)

        self.assertEqual(db.add_all_calls, 0)
