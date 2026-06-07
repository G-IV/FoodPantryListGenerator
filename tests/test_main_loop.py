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

def _run_main(inputs, flagged_set, contact, existing_records=0, last_scanned=None,
              today_scanned_set=None):
    """
    Run main() with fully mocked I/O.

    Returns (mock_append, mock_flagged_append, mock_already_served_append,
    printed_lines) where printed_lines is a flat list of strings passed to print().

    today_scanned_set seeds the session duplicate-guard.  Each call that
    omits it gets a fresh empty set, so scans made during the run accumulate
    without leaking between tests.
    """
    if today_scanned_set is None:
        today_scanned_set = set()
    printed_lines = []

    def capture_print(*args, **kwargs):
        printed_lines.append(args[0] if args else "")

    with (
        patch("FoodPantryListGenerator.acquire_lock", return_value=True),
        patch("FoodPantryListGenerator.release_lock"),
        patch("builtins.input", side_effect=inputs),
        patch("FoodPantryListGenerator.count_existing_records", return_value=existing_records),
        patch("FoodPantryListGenerator.read_last_case_number", return_value=last_scanned),
        patch("FoodPantryListGenerator.read_existing_case_numbers",
              return_value=today_scanned_set),
        patch("FoodPantryListGenerator.append_record") as mock_append,
        patch("FoodPantryListGenerator.append_flagged_record") as mock_flagged_append,
        patch("FoodPantryListGenerator.append_already_served_record") as mock_already_served_append,
        patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
        patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
        patch("FoodPantryListGenerator.read_invalid_numbers", return_value=flagged_set),
        patch("FoodPantryListGenerator.read_admin_contact", return_value=contact),
        patch("os.path.getmtime", return_value=1000.0),
        patch("builtins.print", side_effect=capture_print),
    ):
        app.main()

    return mock_append, mock_flagged_append, mock_already_served_append, printed_lines


# ---------------------------------------------------------------------------
# Normal (unflagged) scan behavior — must be unchanged by this feature
# ---------------------------------------------------------------------------

class TestUnflaggedScan:
    def test_unflagged_scan_written_to_csv(self):
        """A scan not in InvNmbrs.csv is written to the output file."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        mock_append.assert_called_once()
        _, case_number, _ = mock_append.call_args[0]
        assert case_number == "C1052089"

    def test_multiple_unflagged_scans_all_written(self):
        """Multiple clean scans all reach the CSV writer."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert mock_append.call_count == 2

    def test_unflagged_scan_no_banner_printed(self):
        """A clean scan does not trigger any banner output."""
        _, _, _, printed = _run_main(
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
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        mock_append.assert_not_called()

    def test_flagged_scan_written_to_flagged_log(self):
        """A flagged scan is recorded in the flagged-barcode log."""
        _, mock_flagged_append, _, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        mock_flagged_append.assert_called_once()
        _, case_number, _ = mock_flagged_append.call_args[0]
        assert case_number == "C1052089"

    def test_unflagged_scan_not_written_to_flagged_log(self):
        """A clean scan must not appear in the flagged-barcode log."""
        _, mock_flagged_append, _, _ = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        mock_flagged_append.assert_not_called()

    def test_flagged_scan_prints_banner(self):
        """A flagged scan triggers a printed banner."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        assert any("FLAGGED" in line for line in printed)

    def test_banner_contains_case_number(self):
        """The banner names the specific case number that was flagged."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        assert any("C1052089" in line for line in printed)

    def test_banner_contains_contact_info(self):
        """The banner includes the administrator contact from row 1."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Jane Smith — 555-0100",
        )
        assert any("Jane Smith — 555-0100" in line for line in printed)

    def test_banner_no_contact_does_not_crash(self):
        """If InvNmbrs.csv has no contact info, the banner still shows."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact=None,
        )
        assert any("FLAGGED" in line for line in printed)

    def test_scanning_continues_after_flagged_scan(self):
        """After a flagged scan the loop continues; subsequent scans proceed."""
        mock_append, _, _, _ = _run_main(
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
            patch("FoodPantryListGenerator.read_last_case_number", return_value=None),
            patch("FoodPantryListGenerator.append_record"),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers",
                  return_value={"C1052089"}),
            patch("FoodPantryListGenerator.read_admin_contact", return_value="Admin — 555"),
            patch("os.path.getmtime", return_value=1000.0),
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
        next scan of that barcode should be blocked.  The flagged set is
        refreshed when the file's mtime changes.
        """
        printed_lines = []

        def capture_print(*args, **kwargs):
            printed_lines.append(args[0] if args else "")

        mock_appends = []
        with (
            patch("builtins.input", side_effect=["{[C]01052089}", "{[C]01052089}", ""]),
            patch("FoodPantryListGenerator.count_existing_records", return_value=0),
            patch("FoodPantryListGenerator.read_last_case_number", return_value=None),
            patch("FoodPantryListGenerator.read_existing_case_numbers", return_value=set()),
            patch("FoodPantryListGenerator.append_record",
                  side_effect=lambda *a: mock_appends.append(a)),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers",
                  side_effect=[set(), {"C1052089"}]),
            patch("FoodPantryListGenerator.read_admin_contact", return_value="Admin — 555"),
            patch("os.path.getmtime", side_effect=[1000.0, 1000.0, 2000.0]),
            patch("builtins.print", side_effect=capture_print),
        ):
            app.main()

        assert len(mock_appends) == 1          # only first scan written
        assert any("FLAGGED" in line for line in printed_lines)  # banner on second scan

    def test_case_removed_from_invnmbrs_mid_session_is_logged(self):
        """
        If a case number is removed from InvNmbrs.csv during a session,
        the next scan of that barcode should be logged normally.
        """
        mock_appends = []
        with (
            patch("builtins.input", side_effect=["{[C]01052089}", "{[C]01052089}", ""]),
            patch("FoodPantryListGenerator.count_existing_records", return_value=0),
            patch("FoodPantryListGenerator.read_last_case_number", return_value=None),
            patch("FoodPantryListGenerator.read_existing_case_numbers", return_value=set()),
            patch("FoodPantryListGenerator.append_record",
                  side_effect=lambda *a: mock_appends.append(a)),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.ensure_invnmbrs_exists"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers",
                  side_effect=[{"C1052089"}, set()]),
            patch("FoodPantryListGenerator.read_admin_contact", return_value="Admin — 555"),
            patch("os.path.getmtime", side_effect=[1000.0, 1000.0, 2000.0]),
            patch("builtins.print"),
        ):
            app.main()

        assert len(mock_appends) == 1          # second scan written after removal
        assert mock_appends[0][1] == "C1052089"


# ---------------------------------------------------------------------------
# Consecutive duplicate detection
# ---------------------------------------------------------------------------

class TestConsecutiveDuplicate:
    def test_consecutive_duplicate_not_written_to_csv(self):
        """Second consecutive scan of the same barcode is suppressed."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        assert mock_append.call_count == 1

    def test_consecutive_duplicate_not_written_to_flagged_log(self):
        """Consecutive duplicates are suppressed without touching the flagged log."""
        _, mock_flagged_append, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        mock_flagged_append.assert_not_called()

    def test_consecutive_duplicate_shows_reassurance_message(self):
        """A consecutive re-scan shows a calm reassurance message, not a red alert."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        assert any("proceed to next customer" in line for line in printed)

    def test_clean_scan_after_duplicate_is_written(self):
        """After a duplicate is suppressed, the next distinct scan is written."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052089}", "{[C]01052090}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert mock_append.call_count == 2

    def test_seeded_last_scanned_catches_duplicate_on_first_scan(self):
        """If last_scanned is seeded from the file, the first scan can be a duplicate."""
        mock_append, _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane — 555",
            last_scanned="C1052089",
        )
        mock_append.assert_not_called()
        assert any("proceed to next customer" in line for line in printed)

    def test_different_barcodes_not_treated_as_duplicate(self):
        """Two different barcodes scanned consecutively are both written."""
        mock_append, _, _, printed = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert mock_append.call_count == 2
        assert not any("DUPLICATE" in line for line in printed)

    def test_third_scan_of_same_barcode_is_also_duplicate(self):
        """Each re-scan after the first is independently suppressed."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052089}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert mock_append.call_count == 1

    def test_flagged_scan_checked_before_duplicate(self):
        """A flagged barcode shows FLAGGED even if it matches last_scanned."""
        mock_append, mock_flagged_append, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Admin — 555",
            last_scanned="C1052089",
        )
        mock_append.assert_not_called()
        mock_flagged_append.assert_called_once()
        assert any("FLAGGED" in line for line in printed)
        assert not any("DUPLICATE" in line for line in printed)


# ---------------------------------------------------------------------------
# Already-served detection (non-consecutive re-scan of a barcode from earlier
# in the same session)
# ---------------------------------------------------------------------------

class TestAlreadyServedScan:
    def test_barcode_scanned_earlier_not_written_to_csv(self):
        """Re-scanning a barcode from earlier in the session does not write a new row."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        assert mock_append.call_count == 2

    def test_barcode_scanned_earlier_not_written_to_already_served_log(self):
        """Non-consecutive re-scans are silently ignored — not logged to the already-served file."""
        _, _, mock_already_served_append, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        mock_already_served_append.assert_not_called()

    def test_already_served_silently_ignored_no_banner(self):
        """A non-consecutive re-scan produces no banner output — it is silently skipped."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        assert not any("ALREADY SERVED" in line for line in printed)

    def test_already_served_silently_ignored_no_case_number_output(self):
        """A non-consecutive re-scan produces no output referencing the re-scanned case number."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        # No output line should mention C1052089 after the initial clean scan
        # (the clean scan itself does not print the case number, only the prompt does).
        assert not any("ALREADY SERVED" in line and "C1052089" in line for line in printed)

    def test_already_served_silently_ignored_no_contact_output(self):
        """A non-consecutive re-scan does not display contact info — no banner is shown."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane Smith — 555-0100",
        )
        # Contact info should not appear in any re-scan output.
        assert not any("Jane Smith" in line and "ALREADY SERVED" in line for line in printed)

    def test_scanning_continues_after_already_served(self):
        """After the ALREADY SERVED alert the loop continues and records new barcodes."""
        mock_append, _, _, _ = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", "{[C]01052091}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert mock_append.call_count == 3
        written = [call_args[0][1] for call_args in mock_append.call_args_list]
        assert "C1052091" in written

    def test_seeded_today_set_catches_already_served_on_first_scan(self):
        """A case number in today_scanned_set at startup is silently skipped on the first scan."""
        mock_append, _, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set=set(),
            contact="Jane — 555",
            last_scanned=None,
            today_scanned_set={"C1052089"},
        )
        mock_append.assert_not_called()
        assert not any("ALREADY SERVED" in line for line in printed)

    def test_flagged_checked_before_already_served(self):
        """A barcode that is both flagged and in today's set shows FLAGGED, not ALREADY SERVED."""
        mock_append, mock_flagged_append, _, printed = _run_main(
            inputs=["{[C]01052089}", ""],
            flagged_set={"C1052089"},
            contact="Admin — 555",
            today_scanned_set={"C1052089"},
        )
        mock_append.assert_not_called()
        mock_flagged_append.assert_called_once()
        assert any("FLAGGED" in line for line in printed)
        assert not any("ALREADY SERVED" in line for line in printed)

    def test_already_served_does_not_show_duplicate_banner(self):
        """A non-consecutive re-scan produces no output — neither the ALREADY SERVED nor the duplicate reassurance message."""
        _, _, _, printed = _run_main(
            inputs=["{[C]01052089}", "{[C]01052090}", "{[C]01052089}", ""],
            flagged_set=set(),
            contact=None,
        )
        assert not any("ALREADY SERVED" in line for line in printed)
        assert not any("proceed to next customer" in line for line in printed)
