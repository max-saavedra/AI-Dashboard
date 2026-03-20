"""
app/core/exceptions.py

Domain-level exceptions used across services.
Each exception maps to a specific HTTP status or error type.
"""


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the configured size limit."""


class UnsupportedFileFormatError(Exception):
    """Raised when the uploaded file is not .xlsx or .csv."""


class EmptyFileError(Exception):
    """Raised when the uploaded file contains no interpretable table."""


class SchemaDetectionError(Exception):
    """Raised when neither AI nor heuristics can determine the schema."""


class AIProviderError(Exception):
    """Raised when all AI providers fail (primary + fallback)."""


class AITimeoutError(AIProviderError):
    """Raised when the primary provider exceeds the configured timeout."""


class DataNotFoundError(Exception):
    """Raised when a requested dashboard or chat does not exist."""


class AuthorizationError(Exception):
    """Raised when a user attempts to access another user's data."""
