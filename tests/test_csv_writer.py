"""
tests/test_csv_writer.py — Unit tests for food_pantry/csv_writer.py

Tests cover filename generation, timestamp formatting, record counting,
and the format of rows written to the output file.

If you change the output format (e.g. add columns, change the timestamp
style, or change the filename convention), update these tests first so
the change is intentional and documented.
"""

import datetime
import os
import tempfile

import pytest
from food_pantry.csv_writer import (
    append_flagged_record,
    append_record,
    build_flagged_filename,
    build_output_filename,
    count_existing_records,
    format_timestamp,
)


# ---------------------------------------------------------------------------
# build_output_filename — produces the dated CSV filename
# ---------------------------------------------------------------------------

class TestBuildOutputFilename:
    def test_standard_date(self):
        """A typical pantry date produces the correct filename."""
        assert build_output_filename(datetime.date(2026, 5, 4)) == "scanned_barcodes20260504.csv"

    def test_single_digit_month_and_day_are_zero_padded(self):
        """Month and day are zero-padded in the filename (Jan 5 → 0105)."""
        assert build_output_filename(datetime.date(2026, 1, 5)) == "scanned_barcodes20260105.csv"

    def test_end_of_year(self):
        """December 31 is handled correctly."""
        assert build_output_filename(datetime.date(2026, 12, 31)) == "scanned_barcodes20261231.csv"

    def test_filename_ends_with_csv(self):
        """Output is always a .csv file."""
        filename = build_output_filename(datetime.date(2026, 5, 4))
        assert filename.endswith(".csv")

    def test_filename_contains_correct_prefix(self):
        """The filename prefix matches the original C implementation."""
        filename = build_output_filename(datetime.date(2026, 5, 4))
        assert filename.startswith("scanned_barcodes20")


# ---------------------------------------------------------------------------
# format_timestamp — human-readable, non-zero-padded timestamp
# ---------------------------------------------------------------------------

class TestFormatTimestamp:
    def test_single_digit_month_and_day(self):
        """Month and day are NOT zero-padded (1/5 not 01/05)."""
        dt = datetime.datetime(2026, 1, 5, 9, 7)
        assert format_timestamp(dt) == "1/5/2026 9:07"

    def test_double_digit_month_and_day(self):
        """Double-digit month and day are written as-is."""
        dt = datetime.datetime(2026, 12, 25, 14, 30)
        assert format_timestamp(dt) == "12/25/2026 14:30"

    def test_minutes_are_zero_padded(self):
        """Minutes are zero-padded to two digits (9:07 not 9:7)."""
        dt = datetime.datetime(2026, 1, 5, 9, 3)
        assert format_timestamp(dt) == "1/5/2026 9:03"

    def test_midnight(self):
        """Midnight is represented as 0:00."""
        dt = datetime.datetime(2026, 5, 4, 0, 0)
        assert format_timestamp(dt) == "5/4/2026 0:00"

    def test_noon(self):
        """Noon (12:00) is represented correctly."""
        dt = datetime.datetime(2026, 5, 4, 12, 0)
        assert format_timestamp(dt) == "5/4/2026 12:00"

    def test_no_leading_space_before_hour(self):
        """
        The original C code had a bug ('%d/%d/%d% d:%d') that added a
        space before the hour. Confirm that bug is NOT present here.
        """
        dt = datetime.datetime(2026, 1, 5, 9, 7)
        timestamp = format_timestamp(dt)
        # The character immediately after the year and space should be
        # the hour digit, not another space.
        assert "2026  " not in timestamp
        assert timestamp == "1/5/2026 9:07"


# ---------------------------------------------------------------------------
# count_existing_records — counts rows in the file on startup
# ---------------------------------------------------------------------------

class TestCountExistingRecords:
    def test_returns_zero_when_file_does_not_exist(self):
        """A nonexistent file path returns 0, not an error."""
        assert count_existing_records("/nonexistent/path/file.csv") == 0

    def test_returns_zero_for_empty_file(self):
        """An empty file has 0 records."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            assert count_existing_records(path) == 0
        finally:
            os.unlink(path)

    def test_counts_rows_correctly(self):
        """A file with N rows returns N."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("C1052089,,,,,1/5/2026 9:07\n")
            f.write("C1234567,,,,,1/5/2026 9:08\n")
            f.write("C9876543,,,,,1/5/2026 9:09\n")
            path = f.name
        try:
            assert count_existing_records(path) == 3
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# append_record — writes rows to the output file
# ---------------------------------------------------------------------------

class TestAppendRecord:
    def test_creates_file_if_not_exists(self):
        """append_record creates the file when it does not already exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_output.csv")
            assert not os.path.exists(filepath)
            append_record(filepath, "C1052089", datetime.datetime(2026, 1, 5, 9, 7))
            assert os.path.exists(filepath)

    def test_row_format_matches_expected(self):
        """
        The written row must exactly match the format expected by the
        downstream Oasis report merge process:
          case_number,,,,,timestamp
        Five commas, four empty fields, then the timestamp.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_output.csv")
            append_record(filepath, "C1052089", datetime.datetime(2026, 1, 5, 9, 7))
            with open(filepath, "r", encoding="utf-8") as f:
                line = f.readline()
            assert line == "C1052089,,,,, 1/5/2026 9:07\n"

    def test_appends_without_overwriting(self):
        """Multiple calls append new rows; existing rows are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_output.csv")
            append_record(filepath, "C1052089", datetime.datetime(2026, 1, 5, 9, 7))
            append_record(filepath, "C1234567", datetime.datetime(2026, 1, 5, 9, 8))
            append_record(filepath, "C9876543", datetime.datetime(2026, 1, 5, 9, 9))
            assert count_existing_records(filepath) == 3

    def test_case_number_appears_first_in_row(self):
        """The case number is the first field in every row."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_output.csv")
            append_record(filepath, "C5551234", datetime.datetime(2026, 5, 4, 10, 0))
            with open(filepath, "r", encoding="utf-8") as f:
                line = f.readline()
            assert line.startswith("C5551234,")


# ---------------------------------------------------------------------------
# build_flagged_filename — produces the dated flagged-barcode log filename
# ---------------------------------------------------------------------------

class TestBuildFlaggedFilename:
    def test_standard_date(self):
        """A typical pantry date produces the correct filename."""
        assert build_flagged_filename(datetime.date(2026, 5, 4)) == "flagged_barcodes20260504.csv"

    def test_single_digit_month_and_day_are_zero_padded(self):
        """Month and day are zero-padded in the filename."""
        assert build_flagged_filename(datetime.date(2026, 1, 5)) == "flagged_barcodes20260105.csv"

    def test_filename_ends_with_csv(self):
        """Output is always a .csv file."""
        assert build_flagged_filename(datetime.date(2026, 5, 4)).endswith(".csv")

    def test_filename_contains_correct_prefix(self):
        """The filename prefix distinguishes it from the scanned log."""
        assert build_flagged_filename(datetime.date(2026, 5, 4)).startswith("flagged_barcodes20")


# ---------------------------------------------------------------------------
# append_flagged_record — writes rows to the flagged-barcode log
# ---------------------------------------------------------------------------

class TestAppendFlaggedRecord:
    def test_creates_file_if_not_exists(self):
        """append_flagged_record creates the file when it does not already exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "flagged.csv")
            assert not os.path.exists(filepath)
            append_flagged_record(filepath, "C1200001", datetime.datetime(2026, 5, 4, 9, 15))
            assert os.path.exists(filepath)

    def test_row_format_is_case_number_and_timestamp(self):
        """Each row is: case_number,timestamp — no empty merge columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "flagged.csv")
            append_flagged_record(filepath, "C1200001", datetime.datetime(2026, 5, 4, 9, 15))
            with open(filepath, "r", encoding="utf-8") as f:
                line = f.readline()
            assert line == "C1200001,5/4/2026 9:15\n"

    def test_appends_without_overwriting(self):
        """Multiple flagged scans accumulate in the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "flagged.csv")
            append_flagged_record(filepath, "C1200001", datetime.datetime(2026, 5, 4, 9, 15))
            append_flagged_record(filepath, "C1300001", datetime.datetime(2026, 5, 4, 9, 16))
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            assert len(lines) == 2
            assert lines[0].startswith("C1200001,")
            assert lines[1].startswith("C1300001,")
