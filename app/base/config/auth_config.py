from typing import ClassVar

from .environment_config import EnvironmentConfig


class AuthConfig:
    """Auth settings for DocuMind."""

    JWT_SECRET: ClassVar[str | None] = EnvironmentConfig.get_env("SECRET_KEY")
    JWT_ALGORITHM: ClassVar[str | None] = EnvironmentConfig.get_env("HASHING_ALGORITHM")
    ACCESS_TOKEN_EXPIRES_MINUTES: ClassVar[int] = 60
