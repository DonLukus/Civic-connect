# Performance testing — NFR-001

Owner: Emile. Tests the exact acceptance criterion in
`docs/requirements/non-functional-requirements.csv`, NFR-001: 10 concurrent users, 5 minutes,
against a filtered 500-record request list, 95th-percentile response time ≤ 2.0 seconds on a
warm instance.

## Status

**Local checks done for real; the live-server run has not happened yet.** Updated after review
feedback on PR #80 pointed out that this file and the AI register had drifted apart — here's the
accurate, current split:

**Actually verified, for real, on this machine (Python 3.12.10, installed 2026-10-15 — see
`docs/governance/ai-usage-register.csv` AI-029):**

- The script compiles and imports cleanly.
- Its `p95` calculation is correct against synthetic data.
- Its empty/under-seeded-result guard genuinely rejects a trivial pass (tested directly).
- The row-counting heuristic (`<td>#` occurrences) was checked against `staff_queue.html`'s
  actual rendered output and matches exactly.

**Still not executed, and cannot be yet:** the script's actual HTTP/login path against a live
server. `GET /staff/queue?status=...` does not exist in `src/web/app.py` yet (it's part of what's
being agreed with Don for M3) — there is no route to point this at. This is the one real
remaining gap, not a Python-availability problem.

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
  --status-filter "New" \
  --min-expected-results <the seeded dataset's known row count for that filter> \
  --concurrency 10 \
  --duration-seconds 300
```

`--status-filter` and `--min-expected-results` are both required — there is no "all requests, any
result" default, specifically so an unfiltered or accidentally-empty response can't be mistaken
for NFR-001 evidence. Each of the `--concurrency` simulated users logs in with its own session,
not one session shared across every thread, so this models the requirement's actual wording
("10 concurrent users") rather than 10 threads replaying one person's cookie.

Prints a JSON summary: the parameters actually used, whether the run even qualifies as a real
NFR-001 measurement (concurrency ≥ 10 **and** duration ≥ 300s — a shorter smoke-test run is
clearly labelled as such and never reported as a pass), total/successful requests (a success
requires status 200, real queue-page content, **and** at least `--min-expected-results` rows
actually present — not a login redirect, error page, or suspiciously empty result), the
95th-percentile response time, and the final pass/fail against the 2.0 second target.

## Recording results

Once a real run happens, the result goes in a new file here
(`performance/results/<date>-<environment>.md` or similar) with: tested commit SHA, environment,
dataset size actually used, the full JSON output, and any anomaly observed — same evidence
standard as `docs/decisions/poc-log.md` uses for the DEC-008 PoC. This README gets a pointer added
once that exists.
