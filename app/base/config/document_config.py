from pathlib import Path
from typing import ClassVar

from .environment_config import EnvironmentConfig


class DocumentConfig:
    """Document settings for DocuMind."""

    UPLOAD_DIR: ClassVar[Path] = Path(
        EnvironmentConfig.get_env("UPLOAD_DIR") or "documents"
    ).expanduser()
    UPLOAD_READ_CHUNK_SIZE: ClassVar[int] = 1024 * 1024
