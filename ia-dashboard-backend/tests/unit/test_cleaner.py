"""
tests/unit/test_cleaner.py

Unit tests for app/services/etl/cleaner.py.
Covers offset detection, merged cell resolution, column normalisation,
and formula injection sanitisation.
"""

import io

import openpyxl
import pandas as pd
import pytest

from app.core.exceptions import EmptyFileError
from app.services.etl.cleaner import (
    _normalize_column_names,
    _sanitize_cell_values,
    _to_snake_case,
    clean_file,
)


class TestSnakeCaseConversion:
    def test_spaces_become_underscores(self):
        assert _to_snake_case("Sales Revenue") == "sales_revenue"

    def test_mixed_case_lowercased(self):
        assert _to_snake_case("TotalSales") == "totalsales"

    def test_special_chars_removed(self):
        assert _to_snake_case("Revenue (USD)") == "revenue_usd"

    def test_multiple_spaces_collapsed(self):
        assert _to_snake_case("  col   name  ") == "col_name"

    def test_slashes_become_underscores(self):
        assert _to_snake_case("Year/Month") == "year_month"

    def test_empty_string_returns_col(self):
        assert _to_snake_case("") == "col"

    def test_leading_underscores_stripped(self):
        assert _to_snake_case("_hidden") == "hidden"


class TestColumnNameNormalisation:
    def test_basic_normalisation(self):
        df = pd.DataFrame(columns=["Product Name", "Sales USD", "Year"])
        result = _normalize_column_names(df)
        assert list(result.columns) == ["product_name", "sales_usd", "year"]

    def test_duplicate_names_get_suffix(self):
        df = pd.DataFrame(columns=["Sales", "Sales", "Sales"])
        result = _normalize_column_names(df)
        # First occurrence keeps the name; duplicates get _1, _2
        assert result.columns[0] == "sales"
        assert result.columns[1] == "sales_1"
        assert result.columns[2] == "sales_2"


class TestFormulaSanitisation:
    def test_strips_leading_equals(self):
        df = pd.DataFrame({"col": ["=CMD|' /C calc'!A0", "normal value"]})
        result = _sanitize_cell_values(df)
        assert result["col"].iloc[0] == "CMD|' /C calc'!A0"

    def test_strips_leading_plus(self):
        df = pd.DataFrame({"col": ["+1234"]})
        result = _sanitize_cell_values(df)
        assert result["col"].iloc[0] == "1234"

    def test_leaves_normal_values_untouched(self):
        df = pd.DataFrame({"col": ["hello", "world", "100"]})
        result = _sanitize_cell_values(df)
        assert list(result["col"]) == ["hello", "world", "100"]


class TestCleanFile:
    def test_cleans_simple_csv(self, csv_bytes_clean: bytes):
        df = clean_file("data.csv", csv_bytes_clean)
        assert not df.empty
        assert "name" in df.columns
        assert "score" in df.columns
        assert "category" in df.columns

    def test_cleans_simple_excel(self, excel_bytes_clean: bytes):
        df = clean_file("data.xlsx", excel_bytes_clean)
        assert not df.empty
        assert len(df) == 3

    def test_offset_rows_are_removed(self, excel_bytes_with_offset: bytes):
        df = clean_file("offset.xlsx", excel_bytes_with_offset)
        # Only 2 actual data rows should survive
        assert len(df) == 2
        assert "product" in df.columns

    def test_column_names_are_snake_case(self, excel_bytes_clean: bytes):
        df = clean_file("data.xlsx", excel_bytes_clean)
        for col in df.columns:
            assert col == col.lower(), f"Column '{col}' is not lowercase"
            assert " " not in col, f"Column '{col}' contains spaces"

    def test_raises_on_empty_content(self):
        # A valid but empty CSV
        empty_csv = b"col1,col2\n"
        with pytest.raises(EmptyFileError):
            clean_file("empty.csv", empty_csv)

    def test_merged_cells_forward_filled(self):
        """
        Simulate a sheet where a merged header cell leaves NaN in continuation
        columns. After cleaning every row should have a non-null column name.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Region", None, "Sales"])
        ws.append(["North", "East", 1000])
        ws.append(["South", "West", 2000])

        buf = io.BytesIO()
        wb.save(buf)
        df = clean_file("merged.xlsx", buf.getvalue())

        # The None column name should have been forward-filled to "Region"
        assert None not in df.columns
        assert "" not in df.columns
