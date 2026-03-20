"""
app/services/etl/validator.py

Validates uploaded files before any processing occurs (RF-01, RNF-07).
Checks file size, extension, and basic MIME content.
"""

import io
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import (
    FileTooLargeError,
    UnsupportedFileFormatError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
# Magic bytes for OOXML (xlsx) and plain text (csv does not have one)
XLSX_MAGIC = b"PK\x03\x04"


def validate_upload(filename: str, content: bytes) -> None:
    """
    Run all pre-processing validation checks on an uploaded file.

    Raises:
        FileTooLargeError: when the file exceeds MAX_FILE_SIZE_MB.
        UnsupportedFileFormatError: when the extension is not .xlsx/.csv.
    """
    _check_size(filename, content)
    _check_extension(filename)
    _check_magic_bytes(filename, content)
    logger.info("file_validation_passed", filename=filename, size_bytes=len(content))


def _check_size(filename: str, content: bytes) -> None:
    if len(content) > settings.max_file_size_bytes:
        raise FileTooLargeError(
            f"File '{filename}' exceeds the {settings.max_file_size_mb} MB limit."
        )


def _check_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileFormatError(
            f"File extension '{ext}' is not supported. Allowed: {ALLOWED_EXTENSIONS}"
        )


def _check_magic_bytes(filename: str, content: bytes) -> None:
    """
    For .xlsx files, verify the OOXML ZIP magic bytes to catch
    renamed files and prevent formula / script injection (RNF-07).
    CSV files are plain text so no magic byte check is needed.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".xlsx" and not content.startswith(XLSX_MAGIC):
        raise UnsupportedFileFormatError(
            f"File '{filename}' does not appear to be a valid Excel workbook."
        )
