from typing import ClassVar

from .environment_config import EnvironmentConfig


class VectorDatabaseConfig:
    """VectorDatabase settings for DocuMind."""

    QDRANT_URL: ClassVar[str | None] = EnvironmentConfig.get_env("QDRANT_URL")
    QDRANT_API_KEY: ClassVar[str | None] = EnvironmentConfig.get_env("QDRANT_API_KEY")
    COLLECTION: ClassVar[str | None] = EnvironmentConfig.get_env(
        "QDRANT_COLLECTION_NAME"
    )
