# NFR-001 filtered queue performance check

Target: p95 <=2.0 seconds, 10 concurrent users, five minutes, a 500-record dataset, warm instance. Login and warm-up precede timing. Cold-start, browser rendering, uptime and 5,000-record capacity are separate claims.

Use the isolated [staging runbook](../docs/deployment/m3-staging.md) and `python -m scripts.m3_verify_live load --seconds 300` after preparing a fresh 500-record fixture. Ten distinct Staff accounts are generated privately in the ignored local configuration. The harness confirms the exact returned request IDs and selected status; login redirects or empty/incorrect results cannot count as successes.

`load_test_staff_queue.py` uses standard-library urllib with independent cookie jars and concurrent threads. p95 uses nearest-rank `ceil(0.95*n)-1`. Its original CLI remains available, but the isolated harness avoids putting a password in command-line arguments. A short smoke run is labelled as insufficient for NFR-001.

16 October result: 8,503 successful responses, zero failures, p95 0.422s. The [release summary](../docs/release/m3-release-evidence-summary.md) indexes aggregate evidence, environment, source identity and limitations. Final candidate review and CI remain pending.
