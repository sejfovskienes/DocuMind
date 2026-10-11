from pydantic import BaseModel, ConfigDict


class DocumentChunkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    metadata_id: int | None = None
    index: int
    text: str
    tokens: int
    embeddings: list[float] | None = None
    ner_entities: list[object] | dict[str, object] | str | None = None
    topic_keywords: list[object] | dict[str, object] | None = None
