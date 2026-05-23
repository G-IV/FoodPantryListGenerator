"""
food_pantry/lock.py — Single-instance enforcement via a PID lock file.

On startup, FoodPantryListGenerator calls acquire_lock().  If another instance
is already running it returns False and the caller should print a message and
exit.  On clean exit the caller should call release_lock() to remove the file.

The lock file is written to the current working directory (C:\\DoubleCheck\\ in
production), consistent with how all other files (CSV output, InvNmbrs.csv)
are located.

Stale lock files left behind by a crash are detected automatically: if the PID
stored in the file no longer belongs to a running process the lock is treated as
absent and replaced with a fresh one.
"""

import os

_LOCK_FILENAME = "FoodPantryListGenerator.lock"


def _lock_path() -> str:
    return os.path.join(os.getcwd(), _LOCK_FILENAME)


def _is_pid_running(pid: int) -> bool:
    """Return True if a process with *pid* is currently alive."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't have permission to signal it.
        return True
    except OSError:
        return False


def acquire_lock() -> bool:
    """
    Try to acquire the single-instance lock.

    Returns True on success (lock file written, safe to proceed).
    Returns False if another instance with a live PID already holds the lock.

    A stale lock file (PID no longer running) is silently replaced.
    An unreadable or corrupt lock file is treated as stale.
    """
    path = _lock_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                pid = int(fh.read().strip())
            if _is_pid_running(pid):
                return False
        except (ValueError, OSError):
            pass  # corrupt or unreadable — treat as stale

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))
    return True


def release_lock() -> None:
    """Remove the lock file on clean exit.  Safe to call even if the file is absent."""
    try:
        os.remove(_lock_path())
    except OSError:
        pass
