"""
tests/test_main_loop.py — Integration tests for the flagged barcode alert
behavior in FoodPantryListGenerator.py

These tests drive main() directly, mocking all I/O so no real files are
read or written.  They verify the contract between the main scan loop and
food_pantry/invalid_numbers.py: flagged scans must never be written to the
output CSV, must display a banner, and the loop must continue without
blocking.

If you change the scan loop control flow (e.g. the record counter, the
order of operations, or when InvNmbrs.csv is read) update these tests to
match.
"""

import FoodPantryListGenerator as app
import pytest
from unittest.mock import call, patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_main(inputs, flagged_set, contact, existing_records=0):
    """
    Run main() with fully mocked I/O.

    Returns (mock_append, printed_lines) where printed_lines is a flat list
    of strings that were passed to print().
    """
    printed_lines = []

    def capture_print(*args, **kwargs):
        printed_lines.append(args[0] if args else "")

    with (
        patch("builtins.input", side_effect=inputs),
        patch("FoodPantryListGenerator.count_existing_records", return_value=existing_records),
        patch("FoodPantryListGenerator.append_record") as mock_append,
        patch("FoodPantryListGenerator.append_flagged_record") as mock_flagged_append,
        patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
        patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
        patch("FoodPantryListGenerator.read_invalid_numbers", return_value=flagged_set),
        patch("FoodPantryListGenerator.read_admin_contact", return_value=contact),
        patch("builtins.print", side_effect=capture_print),
    ):
        app.main()

    return mock_append, mock_flagged_append, printed_lines


# ---------------------------------------------------------------------------
# Normal (unflagged) scan behavior — must be unchanged by this feature
# ---------------------------------------------------------------------------

class TestUnflaggedScan:
    def test_unflagged_scan_written_to_csv(self):
        """A scan not in InvNmbrs.csv is written to the output file."""
        mock_append, _, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        mock_append.assert_called_once()
        _, case_number, _ = mock_append.call_args[0]
        assert case_number == "C1052089"

    def test_multiple_unflagged_scans_all_written(self):
        """Multiple clean scans all reach the CSV writer."""
        mock_append, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert mock_append.call_count == 2

    def test_unflagged_scan_no_banner_printed(self):
        """A clean scan does not trigger any banner output."""
        _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert not any("FLAGGED" in line for line in printed)


# ---------------------------------------------------------------------------
# Flagged scan behavior
# ---------------------------------------------------------------------------

class TestFlaggedScan:
    def test_flagged_scan_not_written_to_csv(self):
        """A flagged scan must not be written to the output file."""
        mock_append, _, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        mock_append.assert_not_called()

    def test_flagged_scan_written_to_flagged_log(self):
        """A flagged scan is recorded in the flagged-barcode log."""
        _, mock_flagged_append, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        mock_flagged_append.assert_called_once()
        _, case_number, _ = mock_flagged_append.call_args[0]
        assert case_number == "C1052089"

    def test_unflagged_scan_not_written_to_flagged_log(self):
        """A clean scan must not appear in the flagged-barcode log."""
        _, mock_flagged_append, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        mock_flagged_append.assert_not_called()

    def test_flagged_scan_prints_banner(self):
        """A flagged scan triggers a printed banner."""
        _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        assert any("FLAGGED" in line for line in printed)

    def test_banner_contains_case_number(self):
        """The banner names the specific case number that was flagged."""
        _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        assert any("C1052089" in line for line in printed)

    def test_banner_contains_contact_info(self):
        """The banner includes the administrator contact from row 1."""
        _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        assert any("Jane Smith — 555-0100" in line for line in printed)

    def test_banner_no_contact_does_not_crash(self):
        """If InvNmbrs.csv has no contact info, the banner still shows."""
        _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact=None,
        )
        assert any("FLAGGED" in line for line in printed)

    def test_scanning_continues_after_flagged_scan(self):
        """After a flagged scan the loop continues; subsequent scans proceed."""
        mock_append, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        # Only the second (unflagged) barcode should be written
        assert mock_append.call_count == 1
        _, case_number, _ = mock_append.call_args[0]
        assert case_number == "C1052090"


# ---------------------------------------------------------------------------
# Record counter behavior
# ---------------------------------------------------------------------------

class TestRecordCounter:
    def test_flagged_scan_does_not_increment_record_counter(self):
        """
        The 'Record N' prompt reflects actual written records, not scan
        attempts.  A flagged scan should not advance the counter, so the
        next successful scan still shows the correct record number.
        """
        prompt_calls = []

        def capture_input(prompt=""):
            prompt_calls.append(prompt)
            # Yield three calls: flagged scan, unflagged scan, exit
            return ["{[C]01052089}", "{[C]01052090}", ""][len(prompt_calls) - 1]

        with (
            patch("builtins.input", side_effect=capture_input),
            patch("FoodPantryListGenerator.count_existing_records", return_value=0),
            patch("FoodPantryListGenerator.append_record"),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers",
                  side_effect=[{"C1052089"}, set()]),
            patch("FoodPantryListGenerator.read_admin_contact", return_value="Admin — 555"),
            patch("builtins.print"),
        ):
            app.main()

        # prompt_calls[0]: flagged scan → "Record 1"
        # prompt_calls[1]: unflagged scan → should still say "Record 1", not "Record 2"
        # prompt_calls[2]: exit prompt → "Record 2"
        assert "Record 1" in prompt_calls[0]
        assert "Record 1" in prompt_calls[1]
        assert "Record 2" in prompt_calls[2]


# ---------------------------------------------------------------------------
# Dynamic file update mid-session
# ---------------------------------------------------------------------------

class TestMidSessionFileUpdate:
    def test_case_added_to_invnmbrs_mid_session_is_caught(self):
        """
        If InvNmbrs.csv is updated between scans (case number added), the
        next scan of that barcode should be blocked.  The file is re-read
        on every scan.
        """
        read_call_count = [0]

        def dynamic_flagged(*_):
            read_call_count[0] += 1
            # First scan: not yet flagged; second scan: now flagged
            return set() if read_call_count[0] == 1 else {"C1052089"}

        mock_append, _ = _run_main.__wrapped__ if hasattr(_run_main, "__wrapped__") else (None, None)

        printed_lines = []

        def capture_print(*args, **kwargs):
            printed_lines.append(args[0] if args else "")

        mock_appends = []
        with (
            patch("builtins.input", side_effect=["{[C]01052089}", "{[C]01052089}", ""]),
            patch("FoodPantryListGenerator.count_existing_records", return_value=0),
            patch("FoodPantryListGenerator.append_record",
                  side_effect=lambda *a: mock_appends.append(a)),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers",
                  side_effect=dynamic_flagged),
            patch("FoodPantryListGenerator.read_admin_contact", return_value="Admin — 555"),
            patch("builtins.print", side_effect=capture_print),
        ):
            app.main()

        assert len(mock_appends) == 1          # only first scan written
        assert any("FLAGGED" in l for l in printed_lines)  # banner on second scan

    def test_case_removed_from_invnmbrs_mid_session_is_logged(self):
        """
        If a case number is removed from InvNmbrs.csv during a session,
        the next scan of that barcode should be logged normally.
        """
        read_call_count = [0]

        def dynamic_flagged(*_):
            read_call_count[0] += 1
            # First scan: flagged; second scan: removed from file
            return {"C1052089"} if read_call_count[0] == 1 else set()

        mock_appends = []
        with (
            patch("builtins.input", side_effect=["{[C]01052089}", "{[C]01052089}", ""]),
            patch("FoodPantryListGenerator.count_existing_records", return_value=0),
            patch("FoodPantryListGenerator.append_record",
                  side_effect=lambda *a: mock_appends.append(a)),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers",
                  side_effect=dynamic_flagged),
            patch("FoodPantryListGenerator.read_admin_contact", return_value="Admin — 555"),
            patch("builtins.print"),
        ):
            app.main()

        assert len(mock_appends) == 1          # second scan written after removal
        assert mock_appends[0][1] == "C1052089"
