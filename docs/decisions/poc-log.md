# M2 Deployment Proof-of-Concept Log

Evidence for DEC-008 (`docs/decisions/decision-log.csv`, `docs/PED/10-decision-log.md`), gated on
"a small proof of concept covering login, saving data and deploying" on the actual Belgium
Campus platform. This log records what was actually done and observed. It does **not** move
ADR-001 or DEC-008 to Accepted/Decided — that stays a team decision made once this evidence
exists, not something written in here unilaterally.

**Scope, stated up front**: the original PoC tested persistence/bootstrap. A subsequent login
slice exercises email/password sign-in, session-gated request submission and a saved request.
It has now been exercised on Render and interactively on the BC desktop, but this is not the
full FR-001–FR-004 authentication/authorisation feature set. RSK-16/ADR-007 remain open for
team review.

## What was built and verified locally

| Item | Status | Evidence |
|---|---|---|
| `gunicorn` added to `requirements.txt` | Done | Version 26.2.0, licence MIT, verified against `pypi.org/pypi/gunicorn/json` — see `docs/decisions/technology-versions.md` |
| `wsgi.py` production entrypoint | Done | Repo root; checked first that `RequestService`/`RequestRepository` do **not** initialise the schema themselves (no `CREATE TABLE`/`executescript` in either file) — confirmed by reading both, not assumed |
| Schema bootstrap on first run | Done, tested | `wsgi.py`'s `bootstrap()` checks for the `requests` table before running `schema.sql`, and uses `INSERT OR IGNORE` for the demo user/category — verified idempotent by importing `wsgi.py` twice against the same file in separate processes and confirming no error and no duplicate rows on the second run |
| Full request flow via `wsgi.app` | Done, tested | `wsgi.app.test_client()`: `GET /requests/new` → 200, `POST /requests` with valid data → 302 to the confirmation page, one row present after |
| Existing test suite before login work | Unaffected | `python -m pytest tests/ -v` → 10/10 passing at the original PoC checkpoint |
| Local login/save extension | Implemented and unit tested locally; later hosted and BC interactive checks are recorded below | `wsgi.py` provisions a password-hashed PoC Requester only when email/password secrets are supplied; Flask session gates the form, POST uses CSRF token, service checks actor role. `python -m pytest tests -q` → 15/15 passing on local Windows Python 3.12, including WSGI login → save and repeat bootstrap. |
| `gunicorn wsgi:app` run locally | **Not possible from this environment** | Installed cleanly via pip, but fails at import: `ModuleNotFoundError: No module named 'fcntl'` — gunicorn needs a Unix-only module. Confirmed by actually installing and importing it in an isolated venv, not assumed. This is expected: gunicorn only needs to run on Render (Linux); it was never going to run natively on this Windows dev machine, and that is not itself evidence about Render |

## Hosted deployment and persistence evidence

### 1. Render deployment status (updated 5 October 2026)

The Render service at `https://civic-connect-bcx2.onrender.com` was manually deployed from the
latest `main` commit after PR #71 was merged. The deployment page showed **Deploy succeeded / Live**
for commit `6beeb7a` on 5 October 2026, and the Render logs showed `GET /login` returning 200.
The user then signed in and submitted a throwaway test request; the app displayed “Request
received” and reference **#1**. This confirms that the hosted login and submission flow was
reachable and usable for that test. It does not by itself establish persistence across a restart.
The service uses `pip install -r requirements.txt` as its build command and
`gunicorn --bind 0.0.0.0:$PORT wsgi:app` as its start command. The environment variable names
are recorded in the deployment configuration; secret values are deliberately omitted here.

The prior 1 October deployment and PR #62 checks are historical evidence only. The later PR #71
fix addressed the login CSRF/session issue observed during hosted testing; it supersedes the old
status above for the current deployment.

### 2. The persistence/idle-timeout observation

**Checked on 5 October 2026 using a successful manual redeploy.** After the redeploy completed,
the user signed in again and checked the confirmation route for request #1. It returned **Not
Found (404)**, so the request could not be retrieved through that route after the redeploy. The
captured browser screenshot is preserved at
[`evidence/render-request-1-not-found-after-redeploy-2026-10-05.png`](evidence/render-request-1-not-found-after-redeploy-2026-10-05.png).
This records the observed result; it does not identify the underlying cause or prove that every
request was deleted.

| Field | Result |
|---|---|
| Service URL | `https://civic-connect-bcx2.onrender.com` |
| Request submitted, reference # | Test request #1; app showed “Request received” |
| How restart was triggered | Render manual deploy of latest commit; deployment reported succeeded/live |
| Data present after redeploy? | No: after signing in again, the confirmation route for #1 returned 404 Not Found |
| Evidence | Screenshot linked above; user observed successful redeploy and subsequent 404 |
| Conclusion for ADR-001's SQLite-vs-PostgreSQL question | The record was unavailable after this redeploy. This is evidence of a persistence problem in the tested setup, but the cause is not established and the observation alone does not choose a database or storage design. |

### 3. Belgium Campus platform check

**Partly checked on 2026-09-30.** On the Belgium Campus remote desktop, the public repository was
cloned into `C:\Users\BC-STUDENT\PycharmProjects\civic-connect` and opened in PyCharm. The desktop
provided Python 3.14, not the proposed Python 3.11. A fresh project virtual environment was
created. PyCharm installed Flask 3.1.3 and pytest 9.1.1 into that environment, then ran the
repository's `tests/` folder with pytest. Its test runner reported **10 tests passed, 10 total,
600 ms**. This is real evidence that the current test suite runs on that BC desktop.

The clone's commit SHA was not captured, so the 2026-09-30 result must not be attributed to a
later main commit. `gunicorn` was intentionally not installed or run in this Windows environment;
that test used Flask and pytest rather than the full `requirements.txt`. Python 3.11 and the
production WSGI server remain **unverified on the BC platform**. The earlier Local Windows Python
3.12 results above are separate data points, not campus evidence.

**Repeat check on 5 October 2026.** A fresh checkout of the public `main` branch was opened in
PyCharm at `C:\Users\BC-STUDENT\PycharmProjects\Civic-connect`. On Python **3.14.5**, an
isolated `.venv` was created and Flask 3.1.3 plus pytest 9.1.1 were installed. The full
`tests/` suite reported **15 passed in 7.75 seconds**; the terminal screenshot is preserved at
[`evidence/bc-desktop-pytest-15-passed-2026-10-05.png`](evidence/bc-desktop-pytest-15-passed-2026-10-05.png).
The exact checked-out commit SHA was not captured during this first run.

**Commit and dependency verification, later on 5 October.** Emile then captured the checkout
identity and repeated the test command from the same BC Desktop project. `git rev-parse HEAD` and
`git rev-parse origin/main` both returned
`6beeb7a1353fdfdf8a9ed6966e1028b7fd3e0d75`, confirming that this run tested the then-current
`main` commit. Installing `requirements.txt` in the project's isolated `.venv` completed
successfully, including Gunicorn 26.2.0. The repeat run reported **15 passed in 5.88 seconds**.
The supplied terminal screenshots are preserved at
[`evidence/bc-desktop-requirements-installed-2026-10-05.png`](evidence/bc-desktop-requirements-installed-2026-10-05.png),
[`evidence/bc-desktop-pytest-current-main-2026-10-05.png`](evidence/bc-desktop-pytest-current-main-2026-10-05.png)
and
[`evidence/bc-desktop-main-sha-python-2026-10-05.png`](evidence/bc-desktop-main-sha-python-2026-10-05.png).
These confirm the test suite and dependency installation for that commit on this desktop; they do
not establish that Python 3.11 is available there or prove production deployment behaviour.

The interactive PoC was then run with Flask's development server bound only to
`127.0.0.1:5000`, using a disposable test account, an ephemeral secret key in the terminal
session, and a SQLite database under the BC user's temporary folder. No credentials or personal
data were added to the repository. Login succeeded, and submitting a test-only request returned
reference **#1**. After stopping and restarting the Flask process in the same terminal session,
reloading `/requests/1/submitted` still showed the receipt for #1. The server log shows repeated
`200` responses for that route after the restart. The check was tried twice, leaving two receipt
tabs open; they show the same reference #1 and are not evidence of two separate submissions. This
verifies local-file persistence across an application-process restart in that BC desktop session;
it does not test survival across a VM restart, service replacement or Render redeploy. The
post-restart receipt screenshot and server-log screenshot are preserved at
[`evidence/bc-desktop-request-1-after-process-restart-2026-10-05.png`](evidence/bc-desktop-request-1-after-process-restart-2026-10-05.png) and
[`evidence/bc-desktop-process-restart-access-logs-2026-10-05.png`](evidence/bc-desktop-process-restart-access-logs-2026-10-05.png).

## What this does and does not close

- Does **not** move `ADR-001` from Proposed to Accepted, and does **not** change `DEC-008`'s
  status from Deferred. The evidence is now recorded for the team to review; changing either
  decision remains a team decision, not this log's to make.
- Does provide new, real evidence toward that decision: the schema-bootstrap approach works and is
  idempotent, `gunicorn` is confirmed installable and licensed appropriately, and the Windows/Unix
  boundary around `gunicorn` is now known rather than assumed.
- The hosted login and request-submission flow was exercised, and request #1 was unavailable
  after a successful Render redeploy. On BC Desktop, all 15 tests passed and a test request
  survived a Flask process restart in local SQLite. These are different environments and
  observations: the BC result does not explain the Render result or establish persistence across
  a Render redeploy. The team still needs to review the combined evidence before deciding DEC-008.
