from typing import ClassVar

from .environment_config import EnvironmentConfig


class DatabaseConfig:
    """Database settings for DocuMind."""

    DATABASE_URL: ClassVar[str | None] = EnvironmentConfig.get_env(
        "DB_CONNECTION_STRING"
    )
