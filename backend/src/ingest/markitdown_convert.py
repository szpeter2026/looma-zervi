"""
MarkItDown: multi-format document → Markdown conversion.

Supports Word, Excel, PDF, PPT, etc. Converts binary document streams
into clean Markdown text, ready for LLM structured extraction and RAG indexing.
Scanned documents or complex table/chart layouts may produce suboptimal results;
this layer focuses on the text layer.

Migrated from Tatha project (markitdown_convert.py).
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import BinaryIO

from markitdown import MarkItDown
from markitdown._base_converter import DocumentConverterResult
from markitdown._stream_info import StreamInfo


_converter_instance: MarkItDown | None = None


def _converter() -> MarkItDown:
    """Singleton converter instance to avoid repeated initialization overhead."""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = MarkItDown()
    return _converter_instance


def convert_file(path: str | Path) -> DocumentConverterResult:
    """
    Convert a local file to Markdown.

    Args:
        path: Local file path (.pdf / .docx / .xlsx etc.)

    Returns:
        DocumentConverterResult with .markdown and .metadata fields.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return _converter().convert(str(path))


def convert_stream(
    stream: BinaryIO,
    *,
    filename: str | None = None,
    file_extension: str | None = None,
) -> DocumentConverterResult:
    """
    Convert a binary stream (e.g. uploaded file) to Markdown.

    Args:
        stream: Binary file stream (io.BytesIO or similar).
        filename: Original filename, used to infer type (e.g. "resume.pdf").
        file_extension: Known extension (e.g. ".pdf"); inferred from filename if not given.

    Returns:
        DocumentConverterResult with .markdown and .metadata fields.
    """
    ext = file_extension
    if not ext and filename:
        ext = os.path.splitext(filename)[1]
    stream_info = (
        StreamInfo(extension=ext or None, filename=filename)
        if (ext or filename)
        else None
    )
    return _converter().convert_stream(
        stream, stream_info=stream_info, file_extension=ext
    )


def file_to_markdown(path: str | Path) -> str:
    """Convenience: local file → Markdown string."""
    return convert_file(path).markdown


def stream_to_markdown(
    stream: BinaryIO,
    *,
    filename: str | None = None,
    file_extension: str | None = None,
) -> str:
    """Convenience: binary stream → Markdown string."""
    return convert_stream(
        stream, filename=filename, file_extension=file_extension
    ).markdown
