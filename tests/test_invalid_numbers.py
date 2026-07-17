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
    DEFAULT_FLAGGED_MESSAGE_LINES,
    ensure_invnmbrs_exists,
    format_already_served_banner,
    format_duplicate_banner,
    format_flag_banner,
    read_flagged_message,
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
        """A file with just the header row and no case rows flags nothing."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\n")
        assert read_invalid_numbers(str(f)) == set()

    def test_single_case_number(self, tmp_path):
        """A file with one case number returns a one-element set."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nC1052089\n")
        assert read_invalid_numbers(str(f)) == {"C1052089"}

    def test_multiple_case_numbers(self, tmp_path):
        """All case numbers beyond row 1 are returned."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nC1052089\nC1052090\nC1052091\n")
        assert read_invalid_numbers(str(f)) == {"C1052089", "C1052090", "C1052091"}

    def test_header_row_not_in_set(self, tmp_path):
        """Row 1 (column header) is never included in the flagged set."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nC1052089\n")
        result = read_invalid_numbers(str(f))
        assert "Case #" not in result

    def test_trailing_comma_stripped(self, tmp_path):
        """A trailing comma on a case number row (CSV artifact) is stripped."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nC1052089,\n")
        assert read_invalid_numbers(str(f)) == {"C1052089"}

    def test_leading_trailing_whitespace_stripped(self, tmp_path):
        """Surrounding whitespace on a case number row is stripped."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\n  C1052089  \n")
        assert read_invalid_numbers(str(f)) == {"C1052089"}

    def test_crlf_line_endings(self, tmp_path):
        """Windows-style CRLF line endings are handled correctly."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_bytes(b"Case #\r\nC1052089\r\nC1052090\r\n")
        assert read_invalid_numbers(str(f)) == {"C1052089", "C1052090"}

    def test_blank_lines_ignored(self, tmp_path):
        """Blank lines after the header row do not produce empty-string entries."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nC1052089\n\nC1052090\n")
        result = read_invalid_numbers(str(f))
        assert "" not in result
        assert result == {"C1052089", "C1052090"}


# ---------------------------------------------------------------------------
# format_flag_banner — builds the ANSI red banner lines
# ---------------------------------------------------------------------------

class TestFormatFlagBanner:
    def test_shows_customer_scan_in_problems_instruction(self):
        """The flagged banner tells the volunteer where to write scan-in details."""
        lines = format_flag_banner("C1052089")
        combined = "\n".join(lines)
        assert "Customer Scan-In Problems" in combined

    def test_includes_contact_line(self):
        """The default banner includes administrator contact info."""
        lines = format_flag_banner("C1052089")
        assert any("Oasis Administrator" in line for line in lines)

    def test_uses_red_ansi(self):
        """The flagged banner uses ANSI red escape codes."""
        lines = format_flag_banner("C1052089")
        assert any("\033[" in line for line in lines)

    def test_body_explains_flagged_reason(self):
        """The banner body includes the write-down and text-image instructions."""
        lines = format_flag_banner("C1052089")
        assert any("write the data from the barcode card/image" in line for line in lines)
        assert any("Text the image to the Oasis Administrator" in line for line in lines)

    def test_custom_message_lines_override_default(self):
        """Caller-provided message lines are used when supplied."""
        lines = format_flag_banner("C1052089", ["Line A", "Line B"])
        assert any("Line A" in line for line in lines)
        assert any("Line B" in line for line in lines)
        assert not any("Customer Scan-In Problems" in line for line in lines)


# ---------------------------------------------------------------------------
# read_flagged_message — file-based flagged message with fallback defaults
# ---------------------------------------------------------------------------

class TestReadFlaggedMessage:
    def test_absent_file_returns_default(self, tmp_path):
        """When message file is absent, default message lines are used."""
        result = read_flagged_message(str(tmp_path / "flagged_message.txt"))
        assert result == DEFAULT_FLAGGED_MESSAGE_LINES

    def test_non_empty_file_returns_exact_lines(self, tmp_path):
        """A populated message file is returned line-for-line."""
        f = tmp_path / "flagged_message.txt"
        f.write_text("Line 1\n   Indented line\nLine 3\n")
        result = read_flagged_message(str(f))
        assert result == ["Line 1", "   Indented line", "Line 3"]

    def test_blank_only_file_returns_default(self, tmp_path):
        """A file with only blank lines falls back to defaults."""
        f = tmp_path / "flagged_message.txt"
        f.write_text("\n   \n\n")
        result = read_flagged_message(str(f))
        assert result == DEFAULT_FLAGGED_MESSAGE_LINES

    def test_read_error_returns_default(self, tmp_path, monkeypatch):
        """I/O errors while reading the file fall back to defaults."""
        f = tmp_path / "flagged_message.txt"
        f.write_text("Line 1\n")

        def _boom(*args, **kwargs):
            raise OSError("simulated read failure")

        monkeypatch.setattr("builtins.open", _boom)
        result = read_flagged_message(str(f))
        assert result == DEFAULT_FLAGGED_MESSAGE_LINES


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

    def test_skeleton_has_one_row(self, tmp_path):
        """The generated skeleton contains exactly one non-empty row."""
        path = str(tmp_path / "InvNmbrs.csv")
        ensure_invnmbrs_exists(path)
        with open(path, newline="", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.readlines() if ln.strip()]
        assert len(lines) == 1

    def test_skeleton_row_is_case_header(self, tmp_path):
        """Row 1 of the skeleton is 'Case #'."""
        path = str(tmp_path / "InvNmbrs.csv")
        ensure_invnmbrs_exists(path)
        with open(path, newline="", encoding="utf-8") as fh:
            lines = fh.readlines()
        assert lines[0].strip() == "Case #"

    def test_does_not_overwrite_existing_file(self, tmp_path):
        """If InvNmbrs.csv already exists, it is left untouched."""
        f = tmp_path / "InvNmbrs.csv"
        original = "Case #\nC1052089\n"
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
        f.write_text("Case #\nC1052089\nC1052090\n")
        result = validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        assert result == []

    def test_clean_file_is_not_rewritten(self, tmp_path):
        """A valid file is not modified."""
        f = tmp_path / "InvNmbrs.csv"
        original = "Case #\nC1052089\n"
        f.write_text(original)
        validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        assert f.read_text() == original

    def test_malformed_row_removed_from_file(self, tmp_path):
        """A non-case-number row in rows 2+ is removed from the file."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nC1052089\nNOTANUMBER\nC1052090\n")
        validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        result = read_invalid_numbers(str(f))
        assert "NOTANUMBER" not in result
        assert result == {"C1052089", "C1052090"}

    def test_malformed_row_returned_in_list(self, tmp_path):
        """The bad row is included in the return value with its row number."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nNOTANUMBER\n")
        result = validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        assert len(result) == 1
        row_num, value = result[0]
        assert row_num == 2
        assert value == "NOTANUMBER"

    def test_malformed_row_written_to_error_log(self, tmp_path):
        """The bad row value is appended to the error log."""
        f = tmp_path / "InvNmbrs.csv"
        log = tmp_path / "InvNmbrs_errors.log"
        f.write_text("Case #\nNOTANUMBER\n")
        validate_and_clean_invnmbrs(str(f), str(log))
        assert log.exists()
        assert "NOTANUMBER" in log.read_text()

    def test_blank_rows_dropped_silently_not_logged(self, tmp_path):
        """Blank rows are removed without being written to the error log."""
        f = tmp_path / "InvNmbrs.csv"
        log = tmp_path / "InvNmbrs_errors.log"
        f.write_text("Case #\nC1052089\n\nC1052090\n")
        result = validate_and_clean_invnmbrs(str(f), str(log))
        assert result == []
        assert not log.exists()

    def test_header_rows_preserved_after_cleanup(self, tmp_path):
        """Row 1 is always kept, even when bad case rows are removed."""
        f = tmp_path / "InvNmbrs.csv"
        f.write_text("Case #\nNOTANUMBER\n")
        validate_and_clean_invnmbrs(str(f), str(tmp_path / "InvNmbrs_errors.log"))
        with open(str(f), newline="", encoding="utf-8") as fh:
            lines = fh.readlines()
        assert lines[0].strip() == "Case #"


# ---------------------------------------------------------------------------
# format_duplicate_banner — consecutive duplicate alert
# ---------------------------------------------------------------------------

class TestFormatDuplicateBanner:
    def test_contains_reassurance_message(self):
        """The banner shows a calm reassurance message telling the volunteer to proceed."""
        lines = format_duplicate_banner("C1052089")
        assert any("proceed to next customer" in line for line in lines)

    def test_does_not_contain_do_not_issue(self):
        """The consecutive duplicate banner is not an alert — it must not say DO NOT ISSUE."""
        lines = format_duplicate_banner("C1052089")
        assert not any("DO NOT ISSUE" in line for line in lines)

    def test_does_not_contain_contact(self):
        """No contact info is shown."""
        lines = format_duplicate_banner("C1052089")
        assert not any("Contact" in line for line in lines)

    def test_uses_green_ansi(self):
        """The duplicate banner uses green ANSI colour codes, not red."""
        lines = format_duplicate_banner("C1052089")
        colored = [l for l in lines if "proceed to next customer" in l]
        assert all("\033[1;32m" in line for line in colored)


# ---------------------------------------------------------------------------
# format_already_served_banner — amber alert for non-consecutive re-scans
# ---------------------------------------------------------------------------

class TestFormatAlreadyServedBanner:
    def test_contains_case_number(self):
        """The banner names the specific case number that was scanned again."""
        lines = format_already_served_banner("C1052089")
        assert any("C1052089" in line for line in lines)

    def test_contains_already_served_keyword(self):
        """The banner uses ALREADY SERVED so it is distinguishable from other alerts."""
        lines = format_already_served_banner("C1052089")
        assert any("ALREADY SERVED" in line for line in lines)

    def test_no_contact_line(self):
        """No contact info appears in the already-served banner."""
        lines = format_already_served_banner("C1052089")
        assert not any("Contact" in line for line in lines)

    def test_uses_ansi_escape_codes(self):
        """The already-served banner uses ANSI escape codes for colour."""
        lines = format_already_served_banner("C1052089")
        colored = [l for l in lines if "ALREADY SERVED" in l]
        assert all("\033[" in line for line in colored)

    def test_body_explains_already_served_reason(self):
        """The banner body states the barcode has been serviced earlier today."""
        lines = format_already_served_banner("C1052089")
        assert any("serviced earlier today" in line for line in lines)
