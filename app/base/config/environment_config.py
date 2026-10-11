import os
from typing import ClassVar

from dotenv import load_dotenv


class EnvironmentConfig:
    """Load dotenv once and read environment configuration."""

    _dotenv_loaded: ClassVar[bool] = load_dotenv(override=True)

    @staticmethod
    def get_env(name: str, default: str | None = None) -> str | None:
        return os.getenv(name, default)
