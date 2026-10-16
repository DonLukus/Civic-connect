# CivicConnect M3 release evidence summary

Owner: Emile. Prepared 16 October 2026 with Codex execution assistance. **Release status: NOT READY for final baseline or public production release.** The scoped local demonstration candidate has passing evidence; required independent reviews, decisions and final commit verification remain open.

## Status update - 17 October 2026

The opening paragraph and the dated measurements below describe the 16 October review candidate. Since then, PR #85 merged the supervised M3 slice at `c7e92de8f818b66ca1ecc0faf88b0987c4b17b40`, after Don and Masego approved PR head `e76b96e74515e5cc813c6fba4cd1805362e5c020`. The role-matrix additions brought the automated suite to 60 cases; the recorded 39/50-case runs remain historical evidence, not failed or relabelled runs. Don and Masego recorded CHG-002 decisions, and PR #88 added DEC-013 through DEC-018. The earlier statements that those implementation reviews and register reconciliation are pending are superseded by this update.

The corrected full PED export preserves M1/M2 and continues through section 22; it requires its own normal review. Public production remains NOT READY. Durable hosted storage, external email, dormant hashes, outbox recovery, migration rollback and other stated operational limits remain open. This update does not rerun or extend the earlier load/recovery evidence, accept ADR-001/007, resolve DEC-008, or treat an approved demo slice as the whole product baseline.

## Candidate identity

Integration branch: `m3/emile-release-verification`. Local source assembled from:

| Source | Exact source revision |
|---|---|
| main (PR #79 included) | 87deed2 ? full SHA in source-manifest.json |
| UI/performance PR #80 | e375f0cd5a5218913a42ae9fea1a79c78035254d |
| Import fixes and audit workflow PR #81 | 0f20cdf3814741fb257aba1e2981b08993d6f05b |
| Backend PR #82 | 101f4e7dbf977834b3145e2d2ec5dcbbbb30af0b |
| Auth context PR #83 | ba3ae95986527cd688ed4edfc6d5bf562c1e8171 |
| Backend tests/integration PR #84 | 546effea827113a6956e4900961d26e985ecc40a |

Additional candidate changes: shared logout CSRF fix, visible audit actor fix, lint cleanup, isolated staging/recovery/live HTTP harnesses, hardened load-result validation and release documentation. This working tree is not identical to any one source SHA. The source manifest identifies file hashes; after committing, record the actual candidate SHA and confirm the manifest. Do not present origin/main alone as the tested revision.

## Measured evidence

All paths below are relative to `docs/release/evidence/2026-10-16/`.

| Check | Observed result | Evidence and boundary |
|---|---|---|
| Automated suite (registration revision) | 50 passed in 75.07 seconds | registration-regression.xml; original 39-case snapshot remains in pytest.xml |
| Audit actor regression follow-up | 16 backend cases passed after adding the rendered-actor assertion | verification-checks.json; closes candidate DEF-005 regression check |
| Ruff | Clean after corrections | verification-checks.json; src, tests, wsgi.py, scripts, performance |
| Bandit | No medium/high findings in source scan | bandit.json; automated scanner scope only |
| Dependency audit | No known findings in pinned application requirements at check time | dependency-audit.json; advisory coverage is incomplete by nature |
| NFR-001 load | 8,503/8,503 successful, zero failures; p95 0.422s <=2.0s | performance.json; 10 distinct authenticated Staff accounts, exactly 500 New records, 300s warm-instance measurement |
| Requester live HTTP journey | Login ? submit #501 ? receipt ? own list/detail; another requester denied; shared logout succeeds | live-system-journeys.json; real HTTP/Waitress, not Flask test client |
| Staff live HTTP journey | Login ? filtered queue ? detail ? accept ? requester sees Accepted, in-app notification and locally captured SMTP email | live-system-journeys.json; notification observed in 1.141s; external inbox untested |
| Local process restart | Accepted request #501 remains retrievable | process-restart.json; same SQLite file, different server process |
| Backup and separate restore | SQLite integrity check OK; 502 requests, 504 audit rows, 2 outbox rows preserved | backup-restore.json; one online backup/restore drill, no daily schedule/retention claim |
| Browser walkthrough | Requester submitted #502, found own detail; Staff filtered queue and accepted; audit actor displays after correction | browser-request-form.png, browser-receipt.png; acceptance observed through browser controls; remaining requester browser revisit not captured after browser connection ended |
| Credential storage | All 14 staged accounts use bcrypt cost >=10 | live-system-journeys.json; does not prove all historical accounts migrated |

The performance report's initial phrase ?transfer/rendering? means server template generation and response transfer. No browser rendering timing was measured. Login/warm-up precede the timed load window. The report is an aggregate, not a retained per-request latency dataset. No CPU/memory profile, cold-start, availability-window or 5,000-record capacity result was collected.

## Traceability and test boundaries

`docs/requirements/RTM.csv` now links candidate execution evidence in an added M3 evidence column while preserving existing Trace IDs, requirements, priorities and baseline statuses. `docs/quality/m3-verification-handoff.md` extends Masego's dated kickoff inventory; it does not rewrite what was true on 15 October. Named pytest cases are identifiable now; Masego should assign inventory IDs before final baseline.

Flask test-client cases remain labelled in-process functional/integration coverage. Two executable live HTTP system journeys provide a separate system boundary. Browser operation supplies additional visual evidence, with no claim that a checked-in Playwright/Selenium suite exists. A passing system journey is not counted again as an additional unit test.

## Residual risks and release conditions

| Concern | Consequence | Owner / required disposition |
|---|---|---|
| Independent reviews and CI pending | Local results do not establish the final protected branch or reviewed release | Don and Masego review the exact final diff; two different non-author people approve; rerun required CI on the committed candidate |
| Scope includes deferred Must requirements | A successful slice is narrower than the whole product baseline | Team confirms CHG-002 proposal and explicitly records exclusions; no requirement is marked fulfilled by a scope cut |
| DEC-008 and ADR-001/007 status | Implementation is ahead of formal acceptance | Don reconciles the six proposed decision rows with all three students; preserve Deferred/Proposed until evidenced agreement |
| Durable hosted data | Render free local SQLite can disappear on restart/redeploy/spindown | Team selects durable storage before hosted release; local restart evidence cannot close this |
| Legacy hashes | Successful logins upgrade legacy hashes; dormant accounts may remain scrypt | Don chooses a reset/migration policy; Masego inspects actual release data before closing NFR-003 globally |
| In-process outbox | Crash after claim can strand sending rows; retry after mail send can duplicate email | Don records a recovery/idempotency approach; local delivery success does not prove exactly once |
| External email and certificate trust | Local sink is not an external-delivery/security validation | Test intended SMTP provider and TLS trust on the selected host; free Render restricts SMTP ports |
| Full role matrix | Representative denials do not prove every restricted operation for every role | Masego completes/reviews the role x operation matrix and negative outcomes |
| Rollback and data migration | Code rollback can be incompatible with the migrated database | Don reviews migration and compatible rollback/forward repair; backup drill alone is insufficient |
| Availability/capacity and accessibility | No sustained public uptime, 5,000-record capacity or full accessibility assessment | Retain as unverified requirements/risks; do not claim production readiness |

## Immediate review sequence

1. Emile checks this summary and the generated PED v3 review PDF against the evidence; the authenticated GitHub commit records authorship, not personal baseline acceptance.
2. Don reviews backend/migration/outbox and the decision proposals; Masego reviews UI journeys, test categories, privacy/role coverage and RTM.
3. Both record what they actually checked and approve only the exact revision they reviewed.
4. Run required GitHub checks; merge through the protected PR workflow. Emile records the final release SHA/tag and regenerates the PED export with actual approvals and any agreed residual risk acceptance.

No student approval or signature has been added by this work.

## Requested registration addition - 16 October 2026

Public `/register` creates Requester accounts only; email/password validation, bcrypt, confirmation and CSRF are enforced. Case-insensitive duplicates are rejected under a write transaction. All 11 registration tests and the full 50-case suite passed; `registration-live.json` confirms creation/login over real HTTP with bcrypt cost 12 and a submitted Administrator role ignored. This implements the self-registration part of FR-001; Administrator provisioning/audit remain incomplete. Email verification and signup rate limiting are not implemented. `registration-source-manifest.json` identifies this revision; earlier performance/restart/backup reports predate it and have not been rerun or relabelled. New team review and CI are required after this addition.
