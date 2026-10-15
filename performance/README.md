# Performance testing — NFR-001

Owner: Emile. Tests the exact acceptance criterion in
`docs/requirements/non-functional-requirements.csv`, NFR-001: 10 concurrent users, 5 minutes,
against a filtered 500-record request list, 95th-percentile response time ≤ 2.0 seconds on a
warm instance.

## Status

**Design and tooling only — not yet executed.** This could not be run as part of the change that
added it, for two concrete reasons, neither hidden:

1. No working Python interpreter exists on the machine this was written on (checked directly —
   `python`/`python3`/`py` all resolve to the Microsoft Store install stub, not a real
   interpreter). The script has been read through manually for syntax and logic correctness, but
   that is not the same as actually running it.
2. The script targets `GET /staff/queue?status=...` — a route that does not exist in `src/web/app.py`
   yet (it's part of what's being agreed with Don for M3). This cannot produce a real result until
   that route is live.

## What's needed before a real result exists

1. Don's `/staff/queue` route merged and live on the target environment (staging or Render).
2. A seeded dataset of up to 500 requests in that environment — Masego/Don to confirm how this
   gets seeded (a fixture script, not hand-entered data).
3. A dedicated Staff test account — credentials passed via `--email`/`--password` at run time,
   **never committed to the repo**.
4. Run on a *warm* instance specifically — hit the environment once first and let that warm-up
   request complete before starting the timed run, since NFR-001 explicitly excludes cold-start
   latency (that's NFR-002's concern, measured separately).

## Running it, once the above is ready

```
python performance/load_test_staff_queue.py \
  --base-url https://<staging-or-render-host> \
  --email <staff-test-account-email> \
  --password <staff-test-account-password> \
  --status-filter "" \
  --concurrency 10 \
  --duration-seconds 300
```

Prints a JSON summary: total requests, successful requests (status 200 **and** the response body
actually contains the queue page's own content — a login redirect or error page counted as a
"successful" request would make this test meaningless), the 95th-percentile response time, and a
pass/fail against the 2.0 second target.

## Recording results

Once a real run happens, the result goes in a new file here
(`performance/results/<date>-<environment>.md` or similar) with: tested commit SHA, environment,
dataset size actually used, the full JSON output, and any anomaly observed — same evidence
standard as `docs/decisions/poc-log.md` uses for the DEC-008 PoC. This README gets a pointer added
once that exists.
