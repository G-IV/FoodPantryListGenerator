"""
scanner.py — Barcode input parsing

This module is responsible for turning raw input into a normalized case
number, regardless of whether the input came from the Tera barcode scanner
or was typed manually by a volunteer.

Background
----------
The Tera scanner sends keystrokes to the computer as if the volunteer had
typed them. The raw string it produces wraps the case number in a specific
format that includes bracket and brace characters. This module strips that
formatting and normalizes the result.

Manual entry is needed when a barcode will not scan, or when the customer
presents a "Forgot Card" slip. In that case, the volunteer types the numeric
case number directly. They are instructed to type it WITHOUT the leading C,
but this module handles the case where they include it anyway.

Input formats
-------------
Scanner:  {[C]01052089}
  - Starts with the literal characters {[C]
  - Followed by the case number digits, possibly with leading zeros
  - Ends with }

Manual:   1052089
  - Just the numeric case number
  - No brackets, braces, or prefix

Normalized output
-----------------
Both formats produce the same result: C1052089
  - Always prefixed with a capital C
  - Leading zeros stripped
  - No brackets, braces, or other characters

If this ever needs to change (e.g. a new scanner model with a different
output format), only this module needs to be updated. The rest of the
application works with normalized case numbers exclusively.
"""

from typing import Optional

# The character sequence the Tera scanner places before every case number.
# Defined as a constant so it is easy to find and update if the scanner
# firmware or model ever changes.
SCANNER_PREFIX = "{[C]"


def parse_barcode(raw_input: str) -> Optional[str]:
    """
    Parse a raw line of input into a normalized case number.

    This is the main public function of this module. It detects whether
    the input came from the scanner or was typed manually, delegates to
    the appropriate internal parser, and returns a consistent result.

    Args:
        raw_input: The raw string as received from stdin, including any
                   surrounding whitespace or newline characters.

    Returns:
        A normalized case number string such as "C1052089", or None if
        the input is blank. Blank input is the signal the volunteer uses
        to exit the program (pressing Enter on an empty prompt).

    Examples:
        >>> parse_barcode("{[C]01052089}")
        'C1052089'
        >>> parse_barcode("{[C]00012345}")
        'C12345'
        >>> parse_barcode("1052089")
        'C1052089'
        >>> parse_barcode("  1052089  ")
        'C1052089'
        >>> parse_barcode("") is None
        True
        >>> parse_barcode("\\n") is None
        True
    """
    stripped = raw_input.strip()

    if not stripped:
        # Blank input is the exit signal — the volunteer pressed Enter
        # on an empty scan prompt to close the program.
        return None

    if stripped.startswith(SCANNER_PREFIX):
        return _parse_scanner_input(stripped)
    else:
        return _parse_manual_input(stripped)


def _parse_scanner_input(raw: str) -> str:
    """
    Parse scanner-format input into a normalized case number.

    Scanner format: {[C]01052089} → C1052089

    The approach:
      1. Strip the 4-character prefix {[C]
      2. Strip the trailing }
      3. Strip leading zeros
      4. Prepend C

    Args:
        raw: A stripped string that begins with the SCANNER_PREFIX.

    Returns:
        Normalized case number, e.g. "C1052089".
    """
    # Remove the prefix {[C] from the front and } from the back.
    inner = raw[len(SCANNER_PREFIX):].rstrip("}")

    # Strip leading zeros. The guard against an empty result (e.g. if the
    # scanner somehow sent "{[C]}") keeps us from returning just "C".
    digits = inner.lstrip("0") or "0"

    return f"C{digits}"


def _parse_manual_input(raw: str) -> str:
    """
    Parse manually typed input into a normalized case number.

    Manual format: 1052089 → C1052089

    Volunteers are instructed to type the case number WITHOUT the C prefix,
    but some may include it anyway. Both are handled here.

    Args:
        raw: A stripped string that does not begin with SCANNER_PREFIX.

    Returns:
        Normalized case number, e.g. "C1052089".
    """
    # Strip a leading C or c in case the volunteer typed it.
    number = raw.lstrip("Cc")

    # Strip leading zeros, consistent with the scanner path.
    digits = number.lstrip("0") or "0"

    return f"C{digits}"
