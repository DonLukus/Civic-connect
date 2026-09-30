# M2 Deployment Proof-of-Concept Log

Evidence for DEC-008 (`docs/decisions/decision-log.csv`, `docs/PED/10-decision-log.md`), gated on
"a small proof of concept covering login, saving data and deploying" on the actual Belgium
Campus platform. This log records what was actually done and observed. It does **not** move
ADR-001 or DEC-008 to Accepted/Decided — that stays a team decision made once this evidence
exists, not something written in here unilaterally.

**Scope, stated up front**: this PoC tests **persistence and deployment**. It does **not** test
**authentication** — FR-001..FR-004 don't exist yet (RSK-16/ADR-007 cover that gap separately).
Nothing below should be read as evidence that the auth half of DEC-008's bar is covered.

## What was built and verified locally

| Item | Status | Evidence |
|---|---|---|
| `gunicorn` added to `requirements.txt` | Done | Version 26.2.0, licence MIT, verified against `pypi.org/pypi/gunicorn/json` — see `docs/decisions/technology-versions.md` |
| `wsgi.py` production entrypoint | Done | Repo root; checked first that `RequestService`/`RequestRepository` do **not** initialise the schema themselves (no `CREATE TABLE`/`executescript` in either file) — confirmed by reading both, not assumed |
| Schema bootstrap on first run | Done, tested | `wsgi.py`'s `bootstrap()` checks for the `requests` table before running `schema.sql`, and uses `INSERT OR IGNORE` for the demo user/category — verified idempotent by importing `wsgi.py` twice against the same file in separate processes and confirming no error and no duplicate rows on the second run |
| Full request flow via `wsgi.app` | Done, tested | `wsgi.app.test_client()`: `GET /requests/new` → 200, `POST /requests` with valid data → 302 to the confirmation page, one row present after |
| Existing test suite | Unaffected | `python -m pytest tests/ -v` → 10/10 passing, unchanged |
| `gunicorn wsgi:app` run locally | **Not possible from this environment** | Installed cleanly via pip, but fails at import: `ModuleNotFoundError: No module named 'fcntl'` — gunicorn needs a Unix-only module. Confirmed by actually installing and importing it in an isolated venv, not assumed. This is expected: gunicorn only needs to run on Render (Linux); it was never going to run natively on this Windows dev machine, and that is not itself evidence about Render |

## What is NOT done — and why, honestly

### 1. The actual Render deployment

**Not done.** This session has no Render account, no Render API key, and no browser access — there
is nothing in this environment that can create a Render Web Service. This is the same category of
gap as the Belgium Campus lab-machine check below: real infrastructure a human has to touch.

**What Masego (or whoever has the Render account) needs to do, exactly:**

1. On [render.com](https://render.com), **New → Web Service**, connect the `DonLukus/Civic-connect`
   repository, branch `main` (or this PR's branch, for a preview first).
2. Runtime: Python 3. Build command: `pip install -r requirements.txt`. Start command:
   `gunicorn wsgi:app`. Instance type: **Free**.
3. **Do not add a Postgres resource for this pass** — the point is specifically to find out
   whether SQLite survives on Render's free tier, not to skip past that question.
4. Deploy, then follow the persistence test in the next section and fill in the result table
   below (or report it back and this file gets updated in a follow-up commit).

### 2. The persistence/idle-timeout observation

**Not done — depends on #1.** Once deployed:

1. Open the live URL's `/requests/new`, submit a real request, note the reference number shown.
2. Wait past Render free-tier's idle timeout (Render spins the instance down after ~15 minutes of
   no traffic), or trigger a manual redeploy from the Render dashboard to force a restart.
3. Reload the app and check whether that request is still there.
4. Record the raw result below — "survived" or "lost", plus how it was checked. Not a guess.

| Field | Result |
|---|---|
| Deployed URL | *(pending — fill in once step 1 above is done)* |
| Request submitted, reference # | *(pending)* |
| How the restart/idle was triggered | *(pending — idle wait or manual redeploy)* |
| Data present after restart? | *(pending)* |
| Conclusion for ADR-001's SQLite-vs-PostgreSQL question | *(pending — this is the actual answer DEC-008 needs)* |

If the data is lost, **that is a valid and useful result** — it is exactly the evidence ADR-001
said was needed to decide between SQLite and a real hosted Postgres instance, not a failure of
this PoC. Report it as found.

### 3. Belgium Campus platform check

**Partly checked on 2026-09-30.** On the Belgium Campus remote desktop, the public repository was
cloned into `C:\Users\BC-STUDENT\PycharmProjects\civic-connect` and opened in PyCharm. The desktop
provided Python 3.14, not the proposed Python 3.11. A fresh project virtual environment was
created. PyCharm installed Flask 3.1.3 and pytest 9.1.1 into that environment, then ran the
repository's `tests/` folder with pytest. Its test runner reported **10 tests passed, 10 total,
600 ms**. This is real evidence that the current test suite runs on that BC desktop.

The clone's commit SHA was not captured, so this result must not be attributed to a later main
commit without a repeat run. `gunicorn` was intentionally not installed or run in this Windows
environment; PyCharm installed the two packages required for the test run, not the entire
`requirements.txt`. Python 3.11, the full dependency install, an interactive login, a live
request submission and a hosted deployment remain **unverified on the BC platform**. The earlier
Windows Python 3.13 result above is a separate data point, not campus evidence.

## What this does and does not close

- Does **not** move `ADR-001` from Proposed to Accepted, and does **not** change `DEC-008`'s
  status from Deferred — both stay exactly as they are until the pending items above have real
  results, and moving them is a team decision, not this log's to make.
- Does provide new, real evidence toward that decision: the schema-bootstrap approach works and is
  idempotent, `gunicorn` is confirmed installable and licensed appropriately, and the Windows/Unix
  boundary around `gunicorn` is now known rather than assumed.
- Leaves the hosted deployment and persistence observation open, along with the login part of
  DEC-008. The campus pytest result narrows the platform risk but does not close it.
