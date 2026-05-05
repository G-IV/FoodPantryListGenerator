"""
tests/test_invalid_numbers.py — Unit tests for food_pantry/invalid_numbers.py

Tests cover the two public data-reading functions and the banner formatter.
Each test is named to describe the exact scenario being checked.

If you change InvNmbrs.csv's format or the banner rendering, update these
tests first so the change is intentional and documented.
"""

import pytest
from food_pantry.invalid_numbers import (
    format_flag_banner,
    read_admin_contact,
    read_invalid_numbers,
)


# ---------------------------------------------------------------------------
# read_invalid_numbers — parses the set of flagged case numbers
# ---------------------------------------------------------------------------

class TestReadInvalidNumbers:
    def test_file_absent_returns_empty_set(self, tmp_path):
        """When InvNmbrs.csv does not exist, no case numbers are flagged."""
        result = read_invalid_numbers(str(tmp_path / "InvNmbrs.csv"))
        assert result == set()

    def test_only_header_rows_returns_empty_set(self, tmp_path):
        """A file with contact info and header but no case rows flags nothing."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\n")
        assert read_invalid_numbers(str(f)) == set()

    def test_single_case_number(self, tmp_path):
        """A file with one case number returns a one-element set."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\nC1052089\n")
        assert read_invalid_numbers(str(f)) == {"C1052089"}

    def test_multiple_case_numbers(self, tmp_path):
        """All case numbers beyond row 2 are returned."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\nC1052089\nC1052090\nC1052091\n")
        assert read_invalid_numbers(str(f)) == {"C1052089", "C1052090", "C1052091"}

    def test_contact_row_not_in_set(self, tmp_path):
        """Row 1 (contact info) is never included in the flagged set."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\nC1052089\n")
        result = read_invalid_numbers(str(f))
        assert "Pantry Admin,555-0100" not in result

    def test_header_row_not_in_set(self, tmp_path):
        """Row 2 (column header) is never included in the flagged set."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\nC1052089\n")
        result = read_invalid_numbers(str(f))
        assert "Case #" not in result

    def test_trailing_comma_stripped(self, tmp_path):
        """A trailing comma on a case number row (CSV artifact) is stripped."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\nC1052089,\n")
        assert read_invalid_numbers(str(f)) == {"C1052089"}

    def test_leading_trailing_whitespace_stripped(self, tmp_path):
        """Surrounding whitespace on a case number row is stripped."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\n  C1052089  \n")
        assert read_invalid_numbers(str(f)) == {"C1052089"}

    def test_crlf_line_endings(self, tmp_path):
        """Windows-style CRLF line endings are handled correctly."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_bytes(b"Pantry Admin,555-0100\r\nCase #\r\nC1052089\r\nC1052090\r\n")
        assert read_invalid_numbers(str(f)) == {"C1052089", "C1052090"}

    def test_blank_lines_ignored(self, tmp_path):
        """Blank lines after the header rows do not produce empty-string entries."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Pantry Admin,555-0100\nCase #\nC1052089\n\nC1052090\n")
        result = read_invalid_numbers(str(f))
        assert "" not in result
        assert result == {"C1052089", "C1052090"}


# ---------------------------------------------------------------------------
# read_admin_contact — parses the administrator contact from row 1
# ---------------------------------------------------------------------------

class TestReadAdminContact:
    def test_file_absent_returns_none(self, tmp_path):
        """When InvNmbrs.csv does not exist, contact returns None."""
        result = read_admin_contact(str(tmp_path / "InvNmbrs.csv"))
        assert result is None

    def test_name_and_phone_formatted_with_dash(self, tmp_path):
        """Name and phone from row 1 are joined with ' — '."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Jane Smith,555-1234\nCase #\nC1052089\n")
        assert read_admin_contact(str(f)) == "Jane Smith — 555-1234"

    def test_whitespace_around_fields_stripped(self, tmp_path):
        """Extra whitespace around name or phone is stripped."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text(" Jane Smith , 555-1234 \nCase #\n")
        assert read_admin_contact(str(f)) == "Jane Smith — 555-1234"

    def test_blank_row1_returns_none(self, tmp_path):
        """A blank row 1 (no contact info) returns None rather than crashing."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("\nCase #\nC1052089\n")
        assert read_admin_contact(str(f)) is None

    def test_row1_without_comma_returned_as_is(self, tmp_path):
        """If row 1 has no comma, the whole string is returned unchanged."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("PantryAdmin\nCase #\n")
        assert read_admin_contact(str(f)) == "PantryAdmin"


# ---------------------------------------------------------------------------
# format_flag_banner — builds the ANSI red banner lines
# ---------------------------------------------------------------------------

class TestFormatFlagBanner:
    def test_case_number_in_banner(self):
        """The flagged case number appears in the banner output."""
        lines = format_flag_banner("C1052089", "Jane Smith — 555-1234")
        combined = "\n".join(lines)
        assert "C1052089" in combined

    def test_contact_in_banner(self):
        """The contact string appears in the banner when provided."""
        lines = format_flag_banner("C1052089", "Jane Smith — 555-1234")
        combined = "\n".join(lines)
        assert "Jane Smith — 555-1234" in combined

    def test_no_contact_still_shows_case_number(self):
        """When contact is None, the case number line is still present."""
        lines = format_flag_banner("C1052089", None)
        combined = "\n".join(lines)
        assert "C1052089" in combined

    def test_no_contact_omits_contact_line(self):
        """When contact is None, no contact line appears in the output."""
        lines = format_flag_banner("C1052089", None)
        assert not any("Contact" in line for line in lines)
