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
    #--- get not mixing vector spaces, in cost of uploading the vectors with user id in payload
    def __init__(self, user_id: int):
        self.qdrant_client = QdrantClient(
        url=QDRANT_URL, 
        api_key=QDRANT_API_KEY,
    )
        self.user_id = user_id
        
    def __enter__(self):
        self.qdrant_client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE, 
                distance=Distance.COSINE
        ))
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass 
    
    def upsert_embeddings(
            self,
            embeddings: list[float],
            document_chunks: list[DocumentChunk]
    )-> bool:
        try: 
            points = []
            for embedding, chunk in zip(embeddings, document_chunks):
                point_id = str(chunk.id)
                payload = {
                    "user_id": self.user_id,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.index,
                    "text": chunk.text,
                }
                points.append(
                    PointStruct(
                        id = point_id,
                        vector=embedding,
                        payload=payload
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