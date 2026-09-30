# Technology Versions — Verification Record

Per the M2 documentation guideline: record exact versions and licences, verified against the
official source, not asserted by an AI model from memory. This file is that verification record;
`requirements.txt` is the pinned, machine-read result.

| Package | Version | Licence | Verified against | Date |
|---|---|---|---|---|
| Flask | 3.1.3 | BSD-3-Clause | `https://pypi.org/pypi/Flask/json` (published package metadata) | 2026-09-30 |
| pytest | 9.1.1 | MIT | `https://pypi.org/pypi/pytest/json` (published package metadata) | 2026-09-30 |
| Python | 3.11 (proposed) | PSF License | Not yet verified against the Belgium Campus desktop platform — see below | — |
| sqlite3 | stdlib (ships with Python) | PSF License | Part of the CPython standard library; no separate install or licence | — |
| gunicorn | 26.2.0 | MIT | `https://pypi.org/pypi/gunicorn/json` (published package metadata) | 2026-09-30 |

**gunicorn note**: installs cleanly on Windows via pip, but fails at import (`ModuleNotFoundError:
No module named 'fcntl'`) — confirmed by actually installing and running it, not assumed. It
imports the Unix-only `fcntl` module. This is expected and does not block anything: gunicorn is
only needed for the Render (Linux) production deployment; local development keeps using
`python -m src.web.app` (Flask's own dev server), which is unaffected.

## What this does not yet verify

CN-07: Belgium Campus gives no guarantee that any of the above runs on the institutional desktop
platform. This table verifies the packages exist, at these versions, under these licences, on the
public internet — it does not verify they install and run in the actual environment students
build in. That verification is the DEC-008 proof-of-concept action (ADR-001, "What this does not
decide yet") and must happen before ADR-001 moves from Proposed to Accepted.

## Re-verification

Re-check this table before treating any version as current beyond the M2 gate — pinned versions
drift, and "AI generated it" citing an unverified version is not an acceptable defence (PED §13).
