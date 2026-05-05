"""
tests/conftest.py — shared pytest configuration and session-level fixtures.

Automatic fixture restoration
------------------------------
tests/fixtures/InvNmbrs.csv is committed to the repo as the canonical test
fixture but may be modified during manual scanner testing sessions.  The
`restore_invnmbrs_fixture` fixture below resets it to the committed state
before every test session so automated tests always start from a known
baseline — no manual cleanup step required.
"""

import subprocess
import pytest


FIXTURE_PATH = "tests/fixtures/InvNmbrs.csv"


@pytest.fixture(scope="session", autouse=True)
def restore_invnmbrs_fixture():
    """Reset tests/fixtures/InvNmbrs.csv to its committed state before the session."""
    subprocess.run(
        ["git", "checkout", "HEAD", "--", FIXTURE_PATH],
        check=True,
        capture_output=True,
    )
