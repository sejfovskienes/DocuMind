"""Helpers for vector payload ordering."""

from collections.abc import Iterable
from typing import Any


def ordered_chunk_texts(points: Iterable[Any]) -> list[str]:
    """Return point payload text sorted by chunk index."""
    ordered = sorted(
        points,
        key=lambda point: (point.payload or {}).get("chunk_index", 0),
    )
    return [(point.payload or {}).get("text", "") for point in ordered]
