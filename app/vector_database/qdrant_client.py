import os 
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct
)

from app.models.document_chunk import DocumentChunk

load_dotenv(override=True)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("QDRANT_COLLECTION_NAME")
VECTOR_SIZE = 100

class DocumindQdrantClient:
    def __init__(self, user_id: int):
        self.user_id = user_id

        self.qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )

        collections = self.qdrant_client.get_collections().collections
        if COLLECTION not in [c.name for c in collections]:
            self.qdrant_client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE
                )
            )
        print(f"000000000000qdrant status check: {self.qdrant_client.get_collections()}")
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass 
    
    def upsert_embeddings(
            self,
            embeddings: list[list[float]],
            document_chunks: list[DocumentChunk])-> bool:
        try: 
            points = []
            for embedding, chunk in zip(embeddings, document_chunks):
                points.append(
                    PointStruct(
                        id=id(chunk.id),
                        vector=list(embedding),
                        payload={
                            "user_id": self.user_id,
                            "document_id": chunk.document_id,
                            "chunkk_id": chunk.id,
                            "chunk_index": chunk.index,
                            "text": chunk.text
                        }
                    )
                )
            
            self.qdrant_client.upsert(
                collection_name=COLLECTION,
                points=points
            )
            return True
        except Exception as e: 
            message = f"An error occured while uploading embeddings:\n{e}"
            print(message)
            return False 