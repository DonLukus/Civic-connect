"""Combine and validate the AI usage register.

The register is the historical CSV (docs/governance/ai-usage-register.csv, AI-001 to AI-056)
plus one single-row file per later record in docs/governance/ai-usage/AI-nnn.csv. Separate files
mean two pull requests can never edit the same line, so they cannot conflict; two pull requests
that pick the same ID do collide on the same file name, which is a real problem and is reported.

    python tools/ai_register.py            print the combined register as CSV
    python tools/ai_register.py --check    validate and exit non-zero on a problem
    python tools/ai_register.py --next     print the next unused ID
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "docs/governance/ai-usage-register.csv"
RECORDS = ROOT / "docs/governance/ai-usage"
ID_PATTERN = re.compile(r"^AI-\d{3}$")


def load():
    """Return (header, rows, problems); each row is (source, fields)."""
    problems = []
    with LEGACY.open(encoding="utf-8", newline="") as handle:
        table = list(csv.reader(handle))
    header, rows = table[0], [(LEGACY.name, r) for r in table[1:] if r]
    for path in sorted(RECORDS.glob("AI-*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            records = [r for r in csv.reader(handle) if r]
        if len(records) != 1:
            problems.append(f"{path.name}: must contain exactly one row, found {len(records)}")
            continue
        if records[0][0] != path.stem:
            problems.append(f"{path.name}: first field is {records[0][0]!r}, expected {path.stem!r}")
        rows.append((path.name, records[0]))
    seen = {}
    for source, fields in rows:
        if len(fields) != len(header):
            problems.append(f"{source}: {fields[0]} has {len(fields)} columns, expected {len(header)}")
        if not ID_PATTERN.match(fields[0]):
            problems.append(f"{source}: malformed ID {fields[0]!r}")
        if fields[0] in seen:
            problems.append(f"duplicate ID {fields[0]} in {seen[fields[0]]} and {source}")
        seen[fields[0]] = source
    return header, rows, problems


def main(argv):
    header, rows, problems = load()
    if "--check" in argv:
        for problem in problems:
            print(f"::error::{problem}")
        print(f"AI register: {len(rows)} records, {len(problems)} problems")
        return 1 if problems else 0
    if "--next" in argv:
        numbers = [int(r[1][0][3:]) for r in rows if ID_PATTERN.match(r[1][0])]
        print(f"AI-{max(numbers) + 1:03d}")
        return 0
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(header)
    for _source, fields in sorted(rows, key=lambda r: r[1][0]):
        writer.writerow(fields)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
