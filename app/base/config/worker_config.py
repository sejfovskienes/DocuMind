from typing import ClassVar


class WorkerConfig:
    """Worker settings for DocuMind."""

    DOC_CHUNK_SIZE: ClassVar[int] = 100
    DOC_CHUNK_OVERLAP: ClassVar[int] = 90
    DOCUMENT_POLL_INTERVAL_SECONDS: ClassVar[int] = 10
    NER_POLL_INTERVAL_SECONDS: ClassVar[int] = 1
    SUMMARIZATION_POLL_INTERVAL_SECONDS: ClassVar[int] = 5
