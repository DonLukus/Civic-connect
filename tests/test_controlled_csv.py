"""Every controlled CSV register must be well formed: each row has as many fields as the header.

A comma inside an unquoted cell silently splits it into extra columns. The traceability workflow only
reads the first few columns, so such a row can pass CI while corrupting the rest of the register.
"""

import csv
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
CSV_FILES = sorted(p for p in DOCS.rglob("*.csv"))
# Single-row record files carry no header; they are checked by tools/ai_register.py instead.
CSV_FILES = [p for p in CSV_FILES if p.parent.name != "ai-usage"]


# The NFR register's last column ("architecturally significant ...") is filled only for some rows, so
# those rows legitimately end one field early. Extra fields are never allowed anywhere.
OPTIONAL_TRAILING_FIELDS = {"non-functional-requirements.csv": 1}


@pytest.mark.parametrize("path", CSV_FILES, ids=lambda p: str(p.relative_to(DOCS)))
def test_every_row_has_the_same_number_of_fields_as_the_header(path):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.reader(handle) if row]
    width = len(rows[0])
    shortest = width - OPTIONAL_TRAILING_FIELDS.get(path.name, 0)
    bad = [(row[0], len(row)) for row in rows[1:] if not shortest <= len(row) <= width]
    assert not bad, f"{path.name}: header has {width} fields but these rows differ: {bad[:5]}"
