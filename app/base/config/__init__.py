"""Class-based domain settings for DocuMind."""

from .auth_config import AuthConfig
from .database_config import DatabaseConfig
from .document_config import DocumentConfig
from .environment_config import EnvironmentConfig
from .model_config import ModelConfig
from .vector_database_config import VectorDatabaseConfig
from .worker_config import WorkerConfig

__all__ = [
    "AuthConfig",
    "DatabaseConfig",
    "DocumentConfig",
    "ModelConfig",
    "VectorDatabaseConfig",
    "WorkerConfig",
    "EnvironmentConfig",
]
