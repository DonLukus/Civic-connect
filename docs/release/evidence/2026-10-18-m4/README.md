# M4 functional build: live verification, 2026-10-18

Machine-run evidence for the functional requirements added in PRs `m4/fr-lifecycle`, `m4/fr-admin` and
`m4/fr-management`. It is not a student's personal test execution and not an independent acceptance.

| Item | Value |
|---|---|
| Source | commit `fe9092471d8c8e2da2e1830bd8db244ae590fb95` (`m4/fr-management`), clean checkout in a separate folder, fresh database |
| One exception | `scripts/m3_verify_recovery.py` was extended to cover every table after this run started; the restore drill was run with that version, which is the version committed with these files |
| Environment | Windows, Python 3.14, Waitress on loopback HTTP, SQLite, local STARTTLS mail sink, 14 synthetic accounts, 500 synthetic requests |
| Full test suite at this commit | 274 passed (local, Python 3.14); CI runs Python 3.11 and has not yet run on these branches |

| File | What it shows |
|---|---|
| `performance.json` | NFR-001: 10 distinct Staff users, exactly 500 records, 300 s, warm instance, status filter. **3,789 of 3,789 requests succeeded, p95 0.763 s** against the 2.0 s limit |
| `live-system-journeys.json` | Existing Requester and Staff journeys over real HTTP still pass (notification seen in 1.25 s) |
| `workflow-journey.json` | New journey over real HTTP: submit, duplicate prompt confirmed, Manager assigns, Staff work and comment, Resolved refused without a note, Staff refused closing (403), Manager closes, in-app and email notifications, dashboard total equals the stored count, CSV export, Administrator creates an account, single-use setup link, reset by emailed link, deactivation blocks sign-in, category added, administration audit rows present |
| `process-restart.json` | A request survives a stop and start of the server on the same SQLite file |
| `backup-restore.json` | Online backup and a separate restore of all ten tables: integrity check ok and every row count identical |

## Things to read before relying on this

- **The load test needed a fix first.** `performance/load_test_staff_queue.py` parsed the table markup from
  before the UI restyle (PR #94), so it could not run on `main` at all. It now reads labelled cells. Earlier
  p95 figures (0.28 to 0.42 s) were measured on the older page; the page now computes overdue flags, so
  0.6 to 0.76 s across two runs on this machine (0.619 s on an intermediate commit, 0.763 s here) is the honest
  comparison. Both are inside the limit; neither is a hosted or cold-start result.
- Local machine, loopback, synthetic data. No hosted availability, cold-start, capacity (NFR-013) or
  production claim. Email went to a local sink, not an external inbox.
- The 5,000-request capacity test and a moderated usability test were not run.
