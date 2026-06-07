"""
tests/test_invalid_numbers.py — Unit tests for food_pantry/invalid_numbers.py

Tests cover the two public data-reading functions and the banner formatter.
Each test is named to describe the exact scenario being checked.

If you change InvNmbrs.csv's format or the banner rendering, update these
tests first so the change is intentional and documented.
"""

import os
import pytest
from food_pantry.invalid_numbers import (
    ensure_invnmbrs_exists,
    format_already_served_banner,
    format_duplicate_banner,
    format_flag_banner,
    read_admin_contact,
    read_invalid_numbers,
    validate_and_clean_invnmbrs,
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

    def test_body_explains_flagged_reason(self):
        """The banner body states an administrator has flagged the barcode."""
        lines = format_flag_banner("C1052089", None)
        assert any("An administrator has flagged this barcode" in line for line in lines)


# ---------------------------------------------------------------------------
# ensure_invnmbrs_exists — creates a skeleton file if absent
# ---------------------------------------------------------------------------

class TestEnsureInvnmbrsExists:
    def test_creates_file_when_absent(self, tmp_path):
        """If InvNmbrs.csv does not exist, a skeleton file is created."""
        path = str(tmp_path / "InvNmbrs.csv")
        result = ensure_invnmbrs_exists(path)
        assert result is True
        assert os.path.isfile(path)

    def test_skeleton_has_two_rows(self, tmp_path):
        """The generated skeleton contains exactly two non-empty rows."""
        path = str(tmp_path / "InvNmbrs.csv")
        ensure_invnmbrs_exists(path)
        with open(path, newline="", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.readlines() if ln.strip()]
        assert len(lines) == 2

    def test_skeleton_second_row_is_case_header(self, tmp_path):
        """Row 2 of the skeleton is 'Case #'."""
        path = str(tmp_path / "InvNmbrs.csv")
        ensure_invnmbrs_exists(path)
        with open(path, newline="", encoding="utf-8") as fh:
            lines = fh.readlines()
        assert lines[1].strip() == "Case #"

    def test_skeleton_first_row_has_placeholder(self, tmp_path):
        """Row 1 of the skeleton contains the name and phone placeholders."""
        path = str(tmp_path / "InvNmbrs.csv")
        ensure_invnmbrs_exists(path)
        with open(path, newline="", encoding="utf-8") as fh:
            lines = fh.readlines()
        assert lines[0].strip() == "Name,(xxx) xxx-xxxx"

    def test_does_not_overwrite_existing_file(self, tmp_path):
        """If InvNmbrs.csv already exists, it is left untouched."""
        f = tmp_path / "InvNmbrs.csv"
        original = "Jane Smith,(555) 867-5309\nCase #\nC1052089\n"
        f.write_text(original)
        result = ensure_invnmbrs_exists(str(f))
        assert result is False
        assert f.read_text() == original


# ---------------------------------------------------------------------------
# validate_and_clean_invnmbrs — removes malformed rows and logs them
# ---------------------------------------------------------------------------

class TestValidateAndClean:
    def test_absent_file_returns_empty_list(self, tmp_path):
        """No error if InvNmbrs.csv doesn't exist — returns empty list."""
        result = validate_and_clean_invnmbrs(
            str(tmp_path / "InvNmbrs.csv"),
            str(tmp_path / "InvNmbrs_errors.log"),
        )
        assert result == []

    def test_clean_file_returns_empty_list(self, tmp_path):
        """A file with only valid case numbers returns an empty list."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Jane Smith,(555) 867-5309\nCase #\nC1052089\nC1052090\n")
        result = validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        assert result == []

    def test_clean_file_is_not_rewritten(self, tmp_path):
        """A valid file is not modified."""
        f = tmp_path / "InvNmbrs.csv"
        original = "Jane Smith,(555) 867-5309\nCase #\nC1052089\n"
        f.write_text(original)
        validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        assert f.read_text() == original

    def test_malformed_row_removed_from_file(self, tmp_path):
        """A non-case-number row in rows 3+ is removed from the file."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Jane Smith,(555) 867-5309\nCase #\nC1052089\nNOTANUMBER\nC1052090\n")
        validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        result = read_invalid_numbers(str(f))
        assert "NOTANUMBER" not in result
        assert result == {"C1052089", "C1052090"}

    def test_malformed_row_returned_in_list(self, tmp_path):
        """The bad row is included in the return value with its row number."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Jane Smith,(555) 867-5309\nCase #\nNOTANUMBER\n")
        result = validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        assert len(result) == 1
        row_num, value = result[0]
        assert row_num == 3
        assert value == "NOTANUMBER"

    def test_malformed_row_written_to_error_log(self, tmp_path):
        """The bad row value is appended to the error log."""
        f = tmp_path / "InvNmbrs.csv"
        log = tmp_path / "InvNmbrs_errors.log"
        f.write_text("Jane Smith,(555) 867-5309\nCase #\nNOTANUMBER\n")
        validate_and_clean_invnmbrs(str(f), str(log))
        assert log.exists()
        assert "NOTANUMBER" in log.read_text()

    def test_blank_rows_dropped_silently_not_logged(self, tmp_path):
        """Blank rows are removed without being written to the error log."""
        f = tmp_path / "InvNmbrs.csv"
        log = tmp_path / "InvNmbrs_errors.log"
        f.write_text("Jane Smith,(555) 867-5309\nCase #\nC1052089\n\nC1052090\n")
        result = validate_and_clean_invnmbrs(str(f), str(log))
        assert result == []
        assert not log.exists()

    def test_header_rows_preserved_after_cleanup(self, tmp_path):
        """Rows 1 and 2 are always kept, even when bad case rows are removed."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Jane Smith,(555) 867-5309\nCase #\nNOTANUMBER\n")
        validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        with open(str(f), newline="", encoding="utf-8") as fh:
            lines = fh.readlines()
        assert "Jane Smith" in lines[0]
        assert lines[1].strip() == "Case #"


# ---------------------------------------------------------------------------
# format_duplicate_banner — consecutive duplicate alert
# ---------------------------------------------------------------------------

class TestFormatDuplicateBanner:
    def test_contains_reassurance_message(self):
        """The banner shows a calm reassurance message telling the volunteer to proceed."""
        lines = format_duplicate_banner("C1052089", None)
        assert any("proceed to next customer" in line for line in lines)

    def test_does_not_contain_do_not_issue(self):
        """The consecutive duplicate banner is not an alert — it must not say DO NOT ISSUE."""
        lines = format_duplicate_banner("C1052089", None)
        assert not any("DO NOT ISSUE" in line for line in lines)

    def test_does_not_contain_contact(self):
        """Contact info is not shown — the duplicate reassurance message is not an alert."""
        lines = format_duplicate_banner("C1052089", "Jane Smith — 555-0100")
        assert not any("Jane Smith" in line for line in lines)

    def test_uses_green_ansi(self):
        """The duplicate banner uses green ANSI colour codes, not red."""
        lines = format_duplicate_banner("C1052089", None)
        colored = [l for l in lines if "proceed to next customer" in l]
        assert all("\033[1;32m" in line for line in colored)


# ---------------------------------------------------------------------------
# format_already_served_banner — amber alert for non-consecutive re-scans
# ---------------------------------------------------------------------------

class TestFormatAlreadyServedBanner:
    def test_contains_case_number(self):
        """The banner names the specific case number that was scanned again."""
        lines = format_already_served_banner("C1052089", None)
        assert any("C1052089" in line for line in lines)

    def test_contains_already_served_keyword(self):
        """The banner uses ALREADY SERVED so it is distinguishable from other alerts."""
        lines = format_already_served_banner("C1052089", None)
        assert any("ALREADY SERVED" in line for line in lines)

    def test_contains_contact_when_provided(self):
        """The administrator contact is shown when available."""
        lines = format_already_served_banner("C1052089", "Jane Smith — 555-0100")
        assert any("Jane Smith — 555-0100" in line for line in lines)

    def test_no_contact_line_when_contact_is_none(self):
        """If contact is None, no Contact line is added."""
        lines = format_already_served_banner("C1052089", None)
        assert not any("Contact" in line for line in lines)

    def test_uses_ansi_escape_codes(self):
        """The already-served banner uses ANSI escape codes for colour."""
        lines = format_already_served_banner("C1052089", "Jane — 555")
        colored = [l for l in lines if "ALREADY SERVED" in l or "Contact" in l]
        assert all("\033[" in line for line in colored)

    def test_body_explains_already_served_reason(self):
        """The banner body states the barcode has been serviced earlier today."""
        lines = format_already_served_banner("C1052089", None)
        assert any("serviced earlier today" in line for line in lines)
