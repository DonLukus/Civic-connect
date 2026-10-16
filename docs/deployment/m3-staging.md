# M3 isolated staging runbook

Owner: Emile. Candidate verification environment prepared 16 October 2026; team selection and release approval remain pending.

## Environment

Windows, Python 3.12.14, Waitress 3.0.2 on `127.0.0.1:5083`, one SQLite file distinct from development/BC/Render databases, and aiosmtpd 1.4.6 on loopback port 8025 with STARTTLS. Only synthetic `example.test` accounts are used. No external email is sent. This is controlled simulated staging, not an internet deployment.

Install into an isolated virtual environment with `python -m pip install -r requirements-staging.txt`. The staging helper requires OpenSSL (Git for Windows supplies it) to generate its local SMTP certificate.

## Reproduce on a fresh checkout

1. Record `git rev-parse HEAD` and `git status --short`. A dirty tree must include a source manifest; do not label it tested at HEAD alone.
2. Run `python -m scripts.m3_staging prepare` once. It creates 14 synthetic accounts, bcrypt cost 12, and exactly 500 New requests. It refuses to overwrite existing staging data.
3. Run `python -m scripts.m3_staging serve` in one terminal. Wait for the loopback URL.
4. In another terminal run `python -m scripts.m3_verify_live load --seconds 300`. Run this BEFORE journeys so the fixture remains exactly 500 records. Ten distinct Staff accounts, independent sessions and warm-up precede the five-minute measurement.
5. Run `python -m scripts.m3_verify_live journeys`. This submits and accepts a new request and checks requester isolation, status, audit, in-app notification and local SMTP capture.
6. Stop only this server with Ctrl+C, start it again with the same command, then run `python -m scripts.m3_verify_live restart`.
7. Preserve reports under `docs/release/evidence/2026-10-16/` with the candidate source manifest. Later independent runs should use a new evidence directory, not overwrite this run.
8. For a visual walkthrough, use `/login` and the local synthetic credentials in `.m3-local/config.json`. Never commit or screenshot that file. Verify Requester submit/list/detail and Staff filter/detail/accept, then return as Requester to verify status/notification.

## Secret and configuration controls

`.m3-local/` is Git-ignored and contains the generated accounts, session secret, SQLite file, TLS keys and captured synthetic emails. This file-based local launcher loads settings into the server process environment; it is not a production secret vault. `SESSION_COOKIE_SECURE=false` is restricted to loopback HTTP; a public HTTPS deployment requires secure cookies and a stable private signing secret. Do not point the fixture generator at an existing database.

## Persistence and recovery boundaries

A local stop/start preserves the same disk file. This does not prove cloud redeploy persistence. Render's free-service local filesystem is ephemeral across restarts, redeploys and idle shutdowns; free services cannot attach a persistent disk. This matches the M2 symptom, but the historical service configuration was not recovered. DEC-008 remains Deferred. Avoiding a manual redeploy is not a durability solution.

Before any schema-changing deployment, take a SQLite online backup using `Connection.backup`, verify `PRAGMA integrity_check` on the copy and restore into a separate path. Never copy an actively written database file by ordinary file copy. Restore must be exercised before claiming recovery readiness. Code rollback also needs a schema-compatible backup or reviewed forward repair; the current outbox migration is not a tested reversible migration. No production rollback success is claimed.

## Remaining release work

Don and Masego review the candidate and staging choice; Masego confirms test classifications, role matrix and RTM; Emile records the final reviewed SHA and regenerates PED v3. External SMTP, public HTTPS, uptime, cold start, durable hosted storage and 5,000-record capacity are separate unverified claims.

Source: [Render free-service limits](https://render.com/docs/free), checked 16 October 2026.
