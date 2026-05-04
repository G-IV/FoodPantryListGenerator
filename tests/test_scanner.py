"""
tests/test_scanner.py — Unit tests for food_pantry/scanner.py

Each test is named to describe the exact scenario being checked. This makes
the test output readable as documentation — if a test fails, the name tells
you immediately what broke and under what conditions.

If you add a new input format or change parsing behavior in scanner.py,
add corresponding tests here before merging.
"""

import pytest
from food_pantry.scanner import parse_barcode, SCANNER_PREFIX


# ---------------------------------------------------------------------------
# Scanner input — the Tera scanner sends input in the format {[C]01052089}
# ---------------------------------------------------------------------------

class TestScannerInput:
    def test_typical_case_number(self):
        """Standard scanner input with leading zeros strips correctly."""
        assert parse_barcode("{[C]01052089}") == "C1052089"

    def test_multiple_leading_zeros(self):
        """Multiple leading zeros are all stripped."""
        assert parse_barcode("{[C]00012345}") == "C12345"

    def test_single_leading_zero(self):
        """A single leading zero is stripped."""
        assert parse_barcode("{[C]0123456}") == "C123456"

    def test_no_leading_zeros(self):
        """A case number with no leading zeros passes through unchanged."""
        assert parse_barcode("{[C]1052089}") == "C1052089"

    def test_large_case_number(self):
        """A larger case number is handled without truncation."""
        assert parse_barcode("{[C]9999999}") == "C9999999"

    def test_input_with_trailing_newline(self):
        """Input ending with a newline (as read from stdin) is handled."""
        assert parse_barcode("{[C]01052089}\n") == "C1052089"

    def test_input_with_surrounding_whitespace(self):
        """Leading/trailing whitespace is stripped before parsing."""
        assert parse_barcode("  {[C]01052089}  ") == "C1052089"


# ---------------------------------------------------------------------------
# Manual entry — volunteer types the case number without the C prefix
# ---------------------------------------------------------------------------

class TestManualInput:
    def test_numeric_only(self):
        """Volunteer types the number without C — C is prepended."""
        assert parse_barcode("1052089") == "C1052089"

    def test_with_uppercase_c_prefix(self):
        """Volunteer typed the C anyway — it is stripped and re-added."""
        assert parse_barcode("C1052089") == "C1052089"

    def test_with_lowercase_c_prefix(self):
        """Lowercase c is also handled defensively."""
        assert parse_barcode("c1052089") == "C1052089"

    def test_with_leading_zeros(self):
        """Leading zeros in manual entry are stripped, same as scanner."""
        assert parse_barcode("0012345") == "C12345"

    def test_with_trailing_newline(self):
        """Input ending with a newline (as read from stdin) is handled."""
        assert parse_barcode("1052089\n") == "C1052089"

    def test_with_surrounding_whitespace(self):
        """Whitespace around a manually typed number is stripped."""
        assert parse_barcode("  1052089  ") == "C1052089"


# ---------------------------------------------------------------------------
# Exit signal — blank input tells the program to stop
# ---------------------------------------------------------------------------

class TestExitSignal:
    def test_empty_string_returns_none(self):
        """Empty string is the exit signal — returns None."""
        assert parse_barcode("") is None

    def test_newline_only_returns_none(self):
        """A bare newline (volunteer just pressed Enter) returns None."""
        assert parse_barcode("\n") is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only input (spaces/tabs) returns None."""
        assert parse_barcode("   ") is None
        assert parse_barcode("\t") is None
