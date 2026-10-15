# M3 Performance Test Plan

**Owner:** Don  
**Status:** Plan only; results must be generated against an agreed target and recorded separately.

## Objective

Verify the baselined performance non-functional requirement using repeatable measurements. Do not invent an acceptance threshold: retrieve the exact NFR and its acceptance criterion from the controlled requirements artefacts first.

## Test target

- Requirement ID:
- Acceptance criterion and threshold:
- Endpoint(s):
- Staging URL and commit SHA:
- Runtime/hosting tier:
- Database type and dataset size:
- Test tool/version:
- Tester and date:

## Workload

Use synthetic data only. Record the data-generation script and seed so the run can be reproduced.

- Warm-up period:
- Measurement period:
- Concurrent users/workers:
- Request rate:
- Request mix:
- Filter values and distribution:
- Number of records:
- Cache state:
- Number of repetitions:

## Measurements

Capture at minimum:
- p50, p95, and p99 response latency;
- throughput (requests per second);
- HTTP/application error rate;
- CPU and memory use where hosting telemetry permits;
- database query timing where instrumentation permits.

## Procedure

1. Confirm the acceptance threshold before testing.
2. Confirm the staging commit and dataset.
3. Run a smoke test at low concurrency.
4. Run the agreed load profile for the full measurement window.
5. Repeat the test at least three times unless the approved criterion specifies another method.
6. Save raw output and environment details.
7. Compare results with the exact NFR threshold.
8. Investigate errors and outliers; do not discard inconvenient runs without documenting why.
9. Re-run after a material fix and link both results.

## Result table

| Run | Commit SHA | Concurrency | Dataset size | p95 latency | Throughput | Error rate | Pass/Fail |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | Fill in | | | | | | Not run |
| 2 | Fill in | | | | | | Not run |
| 3 | Fill in | | | | | | Not run |

## Acceptance

Pass only if the recorded measurements satisfy the exact baselined criterion and the error-rate/functional-integrity expectations. If the NFR threshold cannot be located or staging is not stable, report **Blocked / Not tested**, not Pass.
