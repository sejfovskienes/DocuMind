import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.base.config import ModelConfig
from app.vector_database import DocumindQdrantClient


class VectorDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client_patcher = patch("app.vector_database.qdrant_client.QdrantClient")
        self.client_factory = self.client_patcher.start()
        self.addCleanup(self.client_patcher.stop)
        self.remote = self.client_factory.return_value
        self.remote.collection_exists.return_value = True
        self.url_patcher = patch(
            "app.base.config.VectorDatabaseConfig.QDRANT_URL", "http://localhost"
        )
        self.collection_patcher = patch(
            "app.base.config.VectorDatabaseConfig.COLLECTION", "chunks"
        )
        self.url_patcher.start()
        self.collection_patcher.start()
        self.addCleanup(self.url_patcher.stop)
        self.addCleanup(self.collection_patcher.stop)
        self.client = DocumindQdrantClient(user_id=12)

    def test_scroll_paginates_and_orders_chunks(self) -> None:
        first = [
            SimpleNamespace(payload={"chunk_index": 2, "text": "third"}),
            SimpleNamespace(payload={"chunk_index": 0, "text": "first"}),
        ]
        second = [SimpleNamespace(payload={"chunk_index": 1, "text": "second"})]
        self.remote.scroll.side_effect = [(first, "next"), (second, None)]

        self.assertEqual(
            self.client.get_document_chunks(document_id=4, limit=2),
            ["first", "second", "third"],
        )
        self.assertEqual(self.remote.scroll.call_count, 2)

    def test_vector_dimension_mismatch_is_rejected(self) -> None:
        chunk = SimpleNamespace(id=1, document_id=4, index=0, text="chunk")
        with self.assertRaisesRegex(ValueError, "dimensional"):
            self.client.upsert_embeddings(
                [[0.0] * (ModelConfig.EMBEDDING_VECTOR_SIZE - 1)], [chunk]
            )
        self.remote.upsert.assert_not_called()

    def test_qdrant_upsert_failure_is_visible(self) -> None:
        chunk = SimpleNamespace(id=1, document_id=4, index=0, text="chunk")
        self.remote.upsert.side_effect = RuntimeError("offline")
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.client.upsert_embeddings(
                [[0.0] * ModelConfig.EMBEDDING_VECTOR_SIZE], [chunk]
            )

    def test_scroll_failure_is_visible(self) -> None:
        self.remote.scroll.side_effect = RuntimeError("offline")
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.client.get_document_chunks(document_id=4)

    def test_setup_failure_closes_client(self) -> None:
        self.remote.create_payload_index.side_effect = RuntimeError("setup failed")
        with self.assertRaisesRegex(RuntimeError, "setup failed"):
            DocumindQdrantClient(user_id=12)
        self.remote.close.assert_called_once_with()

    def test_upsert_uses_stable_chunk_id_and_waits_for_completion(self) -> None:
        chunk = SimpleNamespace(id=42, document_id=4, index=0, text="chunk")
        for _attempt in range(2):
            self.assertTrue(
                self.client.upsert_embeddings(
                    [[0.0] * ModelConfig.EMBEDDING_VECTOR_SIZE], [chunk]
                )
            )
        for call in self.remote.upsert.call_args_list:
            self.assertTrue(call.kwargs["wait"])
            point = call.kwargs["points"][0]
            self.assertEqual(point.id, 42)
            self.assertEqual(point.payload["chunk_id"], 42)
            self.assertEqual(point.payload["chunkk_id"], 42)
            self.assertEqual(point.payload["user_id"], 12)


if __name__ == "__main__":
    unittest.main()
