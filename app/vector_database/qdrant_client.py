import os 
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

load_dotenv(override=True)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("QDRANT_COLLECTION_NAME")
VECTOR_SIZE = 100

"""
    TODO:
    implement logic for mapping the collections 1:1 with user, by changing the collection name to id of the user.
    it can be made using payload for each vector where data isolation can be provided between different users.
    but this approach can lead to heavier operations.
    research for the best approach.
""" 

def get_qdrant_client() -> QdrantClient:
    qdrant_client = QdrantClient(
        url=QDRANT_URL, 
        api_key=QDRANT_API_KEY,
    )

    qdrant_client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )

    return qdrant_client