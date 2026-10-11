"""Qdrant storage for document embeddings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.base.config import ModelConfig, VectorDatabaseConfig
from app.base.extensions import ordered_chunk_texts

if TYPE_CHECKING:
    from app.models.document_chunk_model import DocumentChunk


class DocumindQdrantClient:
    """Store and retrieve a user's document chunks in Qdrant."""

    def __init__(self, user_id: int):
        if not VectorDatabaseConfig.QDRANT_URL or not VectorDatabaseConfig.COLLECTION:
            raise RuntimeError(
                "QDRANT_URL and QDRANT_COLLECTION_NAME must be configured."
            )
        self.user_id = user_id
        self.qdrant_client = QdrantClient(
            url=VectorDatabaseConfig.QDRANT_URL,
            api_key=VectorDatabaseConfig.QDRANT_API_KEY,
        )
        try:
            self._ensure_collection()
            self._ensure_indexes()
        except Exception:
            self.qdrant_client.close()
            raise

    def _ensure_collection(self) -> None:
        if not self.qdrant_client.collection_exists(VectorDatabaseConfig.COLLECTION):
            self.qdrant_client.create_collection(
                collection_name=VectorDatabaseConfig.COLLECTION,
                vectors_config=VectorParams(
                    size=ModelConfig.EMBEDDING_VECTOR_SIZE, distance=Distance.COSINE
                ),
            )

    def _ensure_indexes(self) -> None:
        indexes = {
            "user_id": PayloadSchemaType.INTEGER,
            "document_id": PayloadSchemaType.INTEGER,
            "chunk_index": PayloadSchemaType.INTEGER,
        }
        for field, schema in indexes.items():
            self.qdrant_client.create_payload_index(
                collection_name=VectorDatabaseConfig.COLLECTION,
                field_name=field,
                field_schema=schema,
            )

    def close(self) -> None:
        self.qdrant_client.close()

    def __enter__(self) -> DocumindQdrantClient:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def upsert_embeddings(
        self, embeddings: list[list[float]], document_chunks: list[DocumentChunk]
    ) -> bool:
        if len(embeddings) != len(document_chunks):
            raise ValueError("Each document chunk must have exactly one embedding.")
        if not embeddings:
            return True

        points = []
        for embedding, chunk in zip(embeddings, document_chunks, strict=True):
            if len(embedding) != ModelConfig.EMBEDDING_VECTOR_SIZE:
                raise ValueError(
                    f"Expected {ModelConfig.EMBEDDING_VECTOR_SIZE}-dimensional embeddings; "
                    f"received {len(embedding)} dimensions."
                )
            if chunk.id is None:
                raise ValueError(
                    "Document chunks must be persisted before vector upload."
                )
            points.append(
                PointStruct(
                    id=chunk.id,
                    vector=embedding,
                    payload={
                        "user_id": self.user_id,
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "chunkk_id": chunk.id,
                        "chunk_index": chunk.index,
                        "text": chunk.text,
                    },
                )
            )

        self.qdrant_client.upsert(
            collection_name=VectorDatabaseConfig.COLLECTION, points=points, wait=True
        )
        return True

    def get_document_chunks(self, document_id: int, limit: int = 1000) -> list[str]:
        if limit < 1:
            raise ValueError("limit must be a positive integer.")
        scroll_filter = Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=self.user_id)),
                FieldCondition(key="document_id", match=MatchValue(value=document_id)),
            ]
        )
        points: list[Any] = []
        offset = None
        while True:
            batch, offset = self.qdrant_client.scroll(
                collection_name=VectorDatabaseConfig.COLLECTION,
                scroll_filter=scroll_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            points.extend(batch)
            if offset is None:
                break
        return ordered_chunk_texts(points)
