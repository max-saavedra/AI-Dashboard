"""
tests/unit/test_validator.py

Unit tests for app/services/etl/validator.py.
Tests cover size limits, extension checks, and magic byte validation.
"""

import pytest

from app.core.exceptions import FileTooLargeError, UnsupportedFileFormatError
from app.services.etl.validator import validate_upload


class TestFileSizeValidation:
    def test_accepts_file_within_limit(self, excel_bytes_clean: bytes):
        # Should not raise for a small valid file
        validate_upload("data.xlsx", excel_bytes_clean)

    def test_rejects_file_exceeding_limit(self):
        # 11 MB of zeros should exceed the default 10 MB limit
        oversized = b"\x00" * (11 * 1024 * 1024)
        with pytest.raises(FileTooLargeError):
            validate_upload("big.xlsx", oversized)


class TestExtensionValidation:
    def test_accepts_xlsx_extension(self, excel_bytes_clean: bytes):
        validate_upload("report.xlsx", excel_bytes_clean)

    def test_accepts_csv_extension(self, csv_bytes_clean: bytes):
        validate_upload("data.csv", csv_bytes_clean)

    def test_rejects_pdf_extension(self):
        with pytest.raises(UnsupportedFileFormatError):
            validate_upload("document.pdf", b"some bytes")

    def test_rejects_no_extension(self):
        with pytest.raises(UnsupportedFileFormatError):
            validate_upload("datafile", b"some bytes")

    def test_extension_check_is_case_insensitive(self, excel_bytes_clean: bytes):
        # .XLSX (uppercase) should be accepted
        validate_upload("REPORT.XLSX", excel_bytes_clean)


class TestMagicBytesValidation:
    def test_rejects_xlsx_with_wrong_magic(self):
        # A file named .xlsx but containing plain text bytes
        fake_xlsx = b"This is not a zip file"
        with pytest.raises(UnsupportedFileFormatError, match="valid Excel"):
            validate_upload("fake.xlsx", fake_xlsx)

    def test_csv_skips_magic_check(self, csv_bytes_clean: bytes):
        # CSVs are plain text so no magic byte check applies
        validate_upload("data.csv", csv_bytes_clean)
