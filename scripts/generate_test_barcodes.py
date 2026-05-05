"""
Generate a printable Code 128 barcode test sheet from sample_scanned_barcodes.csv.

Usage:
    python scripts/generate_test_barcodes.py

Output:
    tests/fixtures/test_barcodes.html

Each barcode encodes the numeric portion of the case number only (no 'C' prefix),
which matches the raw value the Tera D5100 scanner reads from physical Oasis client
cards.  The 'C' prefix is added by scanner.py after stripping the scanner's own
{[C]…} wrapper and any leading zeros.
"""

import csv
import io
import os
import re
import sys

import barcode
from barcode.writer import SVGWriter

# ---------------------------------------------------------------------------
# Paths (relative to repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_CSV = os.path.join(REPO_ROOT, "tests", "fixtures", "sample_scanned_barcodes.csv")
OUTPUT_HTML = os.path.join(REPO_ROOT, "tests", "manual_tests", "test_barcodes.html")


def barcode_svg(value: str) -> str:
    """Return an inline SVG string for a Code 128 barcode encoding *value*.

    The hardcoded width/height attributes are replaced with a viewBox so that
    CSS can freely resize the element.
    """
    writer = SVGWriter()
    code = barcode.Code128(value, writer=writer)
    buf = io.BytesIO()
    code.write(buf, options={"write_text": True, "module_height": 12.0, "font_size": 8})
    svg_str = buf.getvalue().decode("utf-8")

    # Extract width and height in mm so we can build a viewBox.
    # The SVG writer emits values like: width="23.080mm" height="23.411mm"
    w_match = re.search(r'<svg[^>]*\swidth="([\d.]+)mm"', svg_str)
    h_match = re.search(r'<svg[^>]*\sheight="([\d.]+)mm"', svg_str)
    if w_match and h_match:
        w_mm = float(w_match.group(1))
        h_mm = float(h_match.group(1))
        # Replace the opening <svg …> tag: remove fixed dimensions, add viewBox.
        svg_str = re.sub(
            r'(<svg\b[^>]*?)\s+width="[\d.]+mm"\s+height="[\d.]+mm"',
            rf'\1 viewBox="0 0 {w_mm} {h_mm}"',
            svg_str,
        )
        # Strip 'mm' unit suffixes from all attribute values so element
        # coordinates are unitless user units that align with the viewBox.
        svg_str = re.sub(r'((?:x|y|width|height|x1|y1|x2|y2)="[\d.]+)mm"', r'\1"', svg_str)
        # Replace absolute font-size (e.g. 8pt) with a user-unit value so the
        # text scales in proportion with the bars as the SVG is resized.
        svg_str = re.sub(r'font-size:[\d.]+pt', 'font-size:2', svg_str)

    # Drop the XML declaration and DOCTYPE lines so it embeds cleanly in HTML.
    lines = [l for l in svg_str.splitlines() if not l.startswith("<?xml")]
    return "\n".join(lines)


def load_case_numbers(csv_path: str) -> list[str]:
    """Return deduplicated, sorted case numbers from the first column."""
    seen: set[str] = set()
    ordered: list[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row:
                continue
            value = row[0].strip()
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
    return ordered


def numeric_part(case_number: str) -> str:
    """Strip the leading 'C' from a case number like C1100001 → '1100001'."""
    return case_number.lstrip("C").lstrip("c")


# ---------------------------------------------------------------------------
# HTML template helpers
# ---------------------------------------------------------------------------
HTML_HEAD = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Food Pantry – Barcode Test Sheet</title>
  <style>
    body  { font-family: Arial, sans-serif; margin: 20px; }
    h1    { font-size: 16px; margin-bottom: 4px; }
    p.sub { font-size: 11px; color: #555; margin-top: 0; margin-bottom: 16px; }
    .grid { display: flex; flex-direction: column; align-items: center; gap: 12px; }
    .card {
      padding: 6px 10px;
      text-align: center;
    }
    .card svg { width: 500px; height: 350px; }
    .card .label {
      font-size: 11px;
      font-weight: bold;
      margin-bottom: 4px;
      color: #333;
    }
    @media print {
      body { margin: 8px; }
      h1, p.sub { display: none; }
      .card { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <h1>Food Pantry List Generator – Code 128 Barcode Test Sheet</h1>
  <p class="sub">
    Each barcode encodes the <strong>numeric portion only</strong> (no&nbsp;C&nbsp;prefix).<br>
    Scan with the Tera D5100 to verify the application resolves the correct case number.
  </p>
  <div class="grid">
"""

HTML_FOOT = """\
  </div>
</body>
</html>
"""


def main() -> None:
    case_numbers = load_case_numbers(FIXTURE_CSV)
    if not case_numbers:
        print("ERROR: no case numbers found in fixture CSV.", file=sys.stderr)
        sys.exit(1)

    cards: list[str] = []
    for cn in case_numbers:
        num = numeric_part(cn)
        try:
            svg = barcode_svg(num)
        except Exception as exc:
            print(f"WARNING: could not generate barcode for {cn}: {exc}", file=sys.stderr)
            continue
        card = (
            f'    <div class="card">\n'
            f'      <div class="label">{cn}</div>\n'
            f'      {svg}\n'
            f'    </div>'
        )
        cards.append(card)

    html = HTML_HEAD + "\n".join(cards) + "\n" + HTML_FOOT
    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    print(f"Generated {len(cards)} barcodes → {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
