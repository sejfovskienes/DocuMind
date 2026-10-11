"""Helpers for document text and file storage."""

import re
import unicodedata
from pathlib import Path

from app.base.config import DocumentConfig, WorkerConfig


def ensure_upload_dir() -> Path:
    """Create and return the configured upload directory."""
    DocumentConfig.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return DocumentConfig.UPLOAD_DIR


def create_upload_path(filename: str) -> Path:
    """Return a path in upload storage using only the supplied filename."""
    return ensure_upload_dir() / Path(filename).name


def clean_document_text(text: str) -> str:
    """Normalize extracted text and remove unsupported control characters."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\x20-\x7E\n\t]", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def chunk_document_text(
    text: str,
    chunk_size: int = WorkerConfig.DOC_CHUNK_SIZE,
    overlap: int = WorkerConfig.DOC_CHUNK_OVERLAP,
) -> list[str]:
    """Split whitespace-delimited text into overlapping chunks."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += step
    return chunks
