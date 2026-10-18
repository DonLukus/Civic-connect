"""Print the project history, newest first.

Entries before 2026-10-19 are in PROJECT_HISTORY.md. Later entries are one file each in
docs/history/ (named YYYY-MM-DD-slug.md), so pull requests never edit the same file.

    python tools/history.py            all entries, newest first (file entries, then the archive)
    python tools/history.py --list     file names only
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = ROOT / "docs/history"


def entry_files():
    return sorted((p for p in ENTRIES.glob("2*.md")), reverse=True)


def main(argv):
    files = entry_files()
    if "--list" in argv:
        print("\n".join(p.name for p in files))
        return 0
    for path in files:
        print(path.read_text(encoding="utf-8").rstrip() + "\n")
    print((ROOT / "PROJECT_HISTORY.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
