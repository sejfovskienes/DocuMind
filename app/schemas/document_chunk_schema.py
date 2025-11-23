from typing import List
from pydantic import BaseModel

class DocumentChunkSchema(BaseModel):
    id: int 
    document_id: int
    metadata_id: int
    index: int 
    text: str
    tokens: int
    embeddings: List[float]

    model_config = {"from_attributes": True}