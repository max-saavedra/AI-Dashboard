"""
app/services/etl/cleaner.py

Reads raw bytes into a clean, typed Pandas DataFrame.

Key responsibilities (RF-01, DA section 2.2):
  - Detect true header row using a data-density heuristic
  - Resolve merged cells via forward-fill
  - Normalize column names to snake_case
  - Strip formula injection patterns (RNF-07)
  - Drop fully empty rows and columns
"""

import io
import re
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.exceptions import EmptyFileError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Threshold: if a row has more than this fraction of nulls it is treated
# as part of the offset (DA section 2.2 – offset detection heuristic).
NULL_DENSITY_THRESHOLD = 0.80

# Patterns that indicate formula injection (e.g., =CMD|... in CSV cells).
FORMULA_INJECTION_PATTERN = re.compile(r"^[=+\-@\t\r]")


def clean_file(filename: str, content: bytes) -> pd.DataFrame:
    """
    Parse and clean a raw Excel or CSV file.

    Returns a normalised DataFrame ready for schema detection and analytics.

    Raises:
        EmptyFileError: when no interpretable table is found.
    """
    ext = Path(filename).suffix.lower()
    raw_df = _read_raw(ext, content)

    df = _drop_empty_offset_rows(raw_df)
    df = _promote_header(df)
    df = _resolve_merged_cells(df)
    df = _drop_empty_columns(df)
    df = _normalize_column_names(df)
    df = _sanitize_cell_values(df)
    df = df.reset_index(drop=True)

    if df.empty or len(df.columns) == 0:
        raise EmptyFileError("No interpretable table found in the uploaded file.")

    logger.info(
        "file_cleaned",
        filename=filename,
        rows=len(df),
        columns=len(df.columns),
    )
    return df


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #


def _read_raw(ext: str, content: bytes) -> pd.DataFrame:
    """
    Load the raw file into a DataFrame without any processing.
    header=None so we can inspect every row before deciding the header.
    """
    buffer = io.BytesIO(content)
    if ext == ".xlsx":
        return pd.read_excel(buffer, header=None, dtype=str, engine="openpyxl")
    # CSV – try common encodings
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            buffer.seek(0)
            return pd.read_csv(buffer, header=None, dtype=str, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise EmptyFileError("Could not decode the CSV file with supported encodings.")


def _null_density(row: pd.Series) -> float:
    """Return the fraction of null / empty values in a row."""
    total = len(row)
    if total == 0:
        return 1.0
    nulls = row.isna().sum() + (row == "").sum()
    return nulls / total


def _drop_empty_offset_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove leading rows that are mostly null (offset / decorative rows).
    Keeps scanning until a row with enough data is found.
    """
    first_data_idx = 0
    for idx, row in df.iterrows():
        if _null_density(row) <= NULL_DENSITY_THRESHOLD:
            first_data_idx = idx  # type: ignore[assignment]
            break
    return df.iloc[first_data_idx:].copy()


def _promote_header(df: pd.DataFrame) -> pd.DataFrame:
    """
    Use the first remaining row as the column header and drop it from data.
    """
    df.columns = df.iloc[0].tolist()
    return df.iloc[1:].copy()


def _resolve_merged_cells(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel merged cells read as NaN for continuation cells.
    Forward-fill propagates the primary cell value across the merge (DA 2.2).
    """
    df.columns = pd.Series(df.columns).ffill().tolist()
    df = df.ffill(axis=0)
    return df


def _drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove columns that are entirely null or have no meaningful name."""
    df = df.dropna(axis=1, how="all")
    # Drop columns whose header resolved to NaN or empty string
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, df.columns.astype(str).str.strip() != ""]
    return df


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert column names to lowercase snake_case.
    Handles duplicate names by appending a numeric suffix.
    """
    seen: dict[str, int] = {}
    new_names = []
    for col in df.columns:
        normalized = _to_snake_case(str(col))
        if normalized in seen:
            seen[normalized] += 1
            normalized = f"{normalized}_{seen[normalized]}"
        else:
            seen[normalized] = 0
        new_names.append(normalized)
    df.columns = new_names
    return df


def _to_snake_case(text: str) -> str:
    """Convert an arbitrary string to snake_case."""
    text = text.strip().lower()
    text = re.sub(r"[\s\-/\\\.]+", "_", text)   # spaces and separators → _
    text = re.sub(r"[^\w]", "", text)             # remove non-word chars
    text = re.sub(r"_+", "_", text)               # collapse multiple underscores
    return text.strip("_") or "col"


def _sanitize_cell_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip formula injection characters from string cells (RNF-07).
    Numeric and date columns are not affected.
    """
    def _sanitize_value(val: object) -> object:
        if isinstance(val, str) and FORMULA_INJECTION_PATTERN.match(val):
            return val[1:]  # remove leading dangerous character
        return val

    return df.apply(lambda col: col.map(_sanitize_value))
