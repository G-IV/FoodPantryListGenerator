"""
tests/test_lock.py — Unit tests for food_pantry/lock.py

Tests cover the single-instance lock file: acquiring a fresh lock, detecting a
live duplicate instance, ignoring stale/corrupt lock files, and releasing the
lock on exit.
"""

import os
import pytest
from unittest.mock import patch

from food_pantry.lock import acquire_lock, release_lock, _is_pid_running


# ---------------------------------------------------------------------------
# _is_pid_running
# ---------------------------------------------------------------------------

class TestIsPidRunning:
    def test_returns_true_for_own_pid(self):
        """Our own process is always running."""
        assert _is_pid_running(os.getpid()) is True

    def test_returns_false_for_nonexistent_pid(self):
        """A PID that cannot possibly exist (e.g. 0 on all platforms) returns False.
        We use a very large PID that is extremely unlikely to be in use."""
        # PID 99999999 is beyond the range of valid PIDs on all supported OSes.
        assert _is_pid_running(99999999) is False


# ---------------------------------------------------------------------------
# acquire_lock
# ---------------------------------------------------------------------------

class TestAcquireLock:
    def test_acquires_lock_when_no_file_exists(self, tmp_path):
        """acquire_lock() returns True and writes the lock file when none exists."""
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = acquire_lock()
        assert result is True
        assert (tmp_path / "FoodPantryListGenerator.lock").exists()

    def test_lock_file_contains_pid(self, tmp_path):
        """The lock file written by acquire_lock() contains the current PID."""
        with patch("os.getcwd", return_value=str(tmp_path)):
            acquire_lock()
        content = (tmp_path / "FoodPantryListGenerator.lock").read_text().strip()
        assert content == str(os.getpid())

    def test_blocks_when_live_pid_in_lock_file(self, tmp_path):
        """Returns False when the lock file contains a PID of a running process."""
        lock_file = tmp_path / "FoodPantryListGenerator.lock"
        lock_file.write_text(str(os.getpid()))  # our own PID — definitely running
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = acquire_lock()
        assert result is False

    def test_acquires_stale_lock_dead_pid(self, tmp_path):
        """Returns True and replaces the lock file when the stored PID is not running."""
        lock_file = tmp_path / "FoodPantryListGenerator.lock"
        lock_file.write_text("99999999")  # PID that cannot exist
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = acquire_lock()
        assert result is True

    def test_acquires_corrupted_lock_file(self, tmp_path):
        """Returns True when the lock file contains unreadable/non-integer content."""
        lock_file = tmp_path / "FoodPantryListGenerator.lock"
        lock_file.write_text("not-a-pid")
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = acquire_lock()
        assert result is True


# ---------------------------------------------------------------------------
# release_lock
# ---------------------------------------------------------------------------

class TestReleaseLock:
    def test_removes_lock_file(self, tmp_path):
        """release_lock() deletes the lock file."""
        lock_file = tmp_path / "FoodPantryListGenerator.lock"
        lock_file.write_text(str(os.getpid()))
        with patch("os.getcwd", return_value=str(tmp_path)):
            release_lock()
        assert not lock_file.exists()

    def test_release_is_safe_when_no_file(self, tmp_path):
        """release_lock() does not raise if the lock file is already absent."""
        with patch("os.getcwd", return_value=str(tmp_path)):
            release_lock()  # should not raise


# ---------------------------------------------------------------------------
# main() — duplicate-instance guard
# ---------------------------------------------------------------------------

class TestMainLockGuard:
    def test_main_exits_when_lock_not_acquired(self):
        """main() prints a message and exits when acquire_lock() returns False."""
        import FoodPantryListGenerator as app
        printed = []
        with (
            patch("FoodPantryListGenerator.acquire_lock", return_value=False),
            patch("builtins.print", side_effect=lambda *a, **k: printed.append(a[0] if a else "")),
            patch("builtins.input"),
            pytest.raises(SystemExit),
        ):
            app.main()
        assert any("already running" in line for line in printed)

    def test_main_releases_lock_on_clean_exit(self):
        """release_lock() is called after a normal session completes."""
        import FoodPantryListGenerator as app
        with (
            patch("FoodPantryListGenerator.acquire_lock", return_value=True),
            patch("FoodPantryListGenerator.release_lock") as mock_release,
            patch("builtins.input", side_effect=[""]),
            patch("FoodPantryListGenerator.count_existing_records", return_value=0),
            patch("FoodPantryListGenerator.read_last_case_number", return_value=None),
            patch("FoodPantryListGenerator.read_existing_case_numbers", return_value=set()),
            patch("FoodPantryListGenerator.append_record"),
            patch("FoodPantryListGenerator.append_flagged_record"),
            patch("FoodPantryListGenerator.validate_and_clean_invnmbrs"),
            patch("FoodPantryListGenerator.read_invalid_numbers", return_value=set()),
            patch("FoodPantryListGenerator.read_admin_contact", return_value=None),
            patch("os.path.isfile", return_value=True),
            patch("os.path.getmtime", return_value=1000.0),
            patch("builtins.print"),
        ):
            app.main()
        mock_release.assert_called_once()
