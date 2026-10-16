# 22. M3 construction, verification and release review

**CivicConnect - PED v3.0 review candidate, 16 October 2026.** Prepared by Emile with AI assistance recorded in AI-036. Continues the existing M1/M2 PED sources; no historical signature or baseline status is changed. No new student approval is recorded.

## 22.1 Candidate and construction

The integration candidate combines the current main snapshot with the proposed backend, route tests, UI and dependency-check changes in PRs #80-84. Source revisions and file hashes are indexed in `docs/release/evidence/2026-10-16/source-manifest.json`. A final signed release SHA/tag is pending.

Implemented slice: Requester login, submission, own list/detail/status; Staff login, queue/status filter/detail/acceptance; acceptance notification through in-app and SMTP; Manager/Administrator login with a safe landing page. `docs/deployment/m3-interface-agreement.md` records actual routes, forms, roles and error behaviour. `CHG-002` records the proposed release-slice exclusions and impact without rewriting baselined priorities.

Two integration defects were corrected: missing CSRF tokens in shared logout forms on list/landing pages (DEF-004), and a mismatched audit-actor field in the detail template (DEF-005). Both have regression checks.

## 22.2 Architecture and configuration conformance

The candidate follows layered server-rendered Flask, service-level rules, SQLite persistence, transactional state/audit/outbox changes and an in-process notification worker. ADR-002/003/004/006 remain Accepted in the source; ADR-001/007 remain Proposed. DEC-008 remains Deferred. The six Issue #65 register rows are draft proposals awaiting team reconciliation, not accepted decisions.

Staging is a distinct loopback Waitress process with a generated synthetic database, separate credentials and local STARTTLS SMTP sink. Config/secrets and the database stay Git-ignored. This simulates staging and does not establish public HTTPS, availability or production durability. See `docs/deployment/m3-staging.md`.

## 22.3 Verification results

| Evidence | Result | Scope |
|---|---|---|
| pytest automated suite | 39 passed in 80.56s | Unit/component and in-process functional/integration; five parameterised logout combinations included |
| Backend regression follow-up | 16 passed | Includes corrected rendered audit actor assertion |
| Ruff / Bandit / dependency audit | Clean / no medium-high findings / no known application dependency findings | Tool results at check time, not complete security proof |
| Live HTTP system journey 1 | Passed | Requester login, submit #501, receipt, list/detail, logout and cross-requester denial |
| Live HTTP system journey 2 | Passed | Staff filter/detail/accept, requester status, in-app notification and local SMTP capture |
| Browser walkthrough | Request #502 submitted and accepted | Actual browser UI operated; form/receipt screenshots retained; no checked-in browser automation claim |
| NFR-001 five-minute load | 8,503 successful; 0 failures; p95 0.422s | 10 distinct Staff users, 500 filtered records, local warm instance, target <=2s |
| Local process restart | Passed | Accepted #501 retrieved after stop/start of same-file staging |
| Online backup/separate restore | Passed | Integrity check OK; request/audit/outbox counts preserved |

`docs/release/evidence/2026-10-16/` holds execution reports. The five-second smoke run is explicitly insufficient for NFR-001. The subsequent 300-second run supplies the stated measurement. No browser rendering benchmark or production-capacity claim is made.

## 22.4 Traceability and quality controls

`docs/requirements/RTM.csv` adds an execution-evidence column for the implemented slice without promoting baseline statuses. `docs/quality/test-inventory.md` remains the historical kickoff; `docs/quality/m3-verification-handoff.md` records the new boundary and remaining independent checks. Requirements, acceptance criteria, code, named tests, execution reports, DEF-004/005 and release conditions are connected through these artefacts.

GitHub workflows provide automated tests, static analysis, dependency audit and secret-pattern checks. Local results are not GitHub CI results. Current CI and branch-protection enforcement must be checked on the signed final revision. Two separate non-author students must review it; two accounts belonging to one person do not create two reviews.

## 22.5 Residual risk and release decision

**NOT READY for final baseline/public production release.** The scoped local demonstration candidate has passing evidence, while independent reviews, formal scope/decision reconciliation and the final committed revision remain pending. See the full release summary for conditions and owners.

Unresolved claims include durable hosted storage, external SMTP/TLS, dormant legacy-hash disposition, complete role x operation coverage, stuck/duplicate outbox recovery, reversible schema/code rollback, sustained availability, cold-start, capacity and accessibility. A local backup drill does not prove daily backup scheduling or retention. Local restart success does not close the M2 Render redeploy failure.

Render documents that free-service local files disappear on restart/redeploy/spindown, which is consistent with the observed M2 failure. The historical instance configuration was not independently recovered. Avoiding redeploy alone cannot ensure durability. PostgreSQL remains a candidate, not an adopted platform.

## 22.6 Evidence index and individual defence

| Engineering concern | Authoritative artefact |
|---|---|
| M1 business/scope/requirements baseline | PED sections 01-15 and docs/requirements/ registers |
| M2 architecture/data/patterns/integration/baseline | PED sections 16, 17, 19, 20, 21 and docs/decisions/adr/ |
| Current route/UI contract | docs/deployment/m3-interface-agreement.md |
| Controlled staging and recovery | docs/deployment/m3-staging.md; scripts/m3_staging.py; scripts/m3_verify_recovery.py |
| Test classifications and remaining matrix | docs/quality/m3-verification-handoff.md; tests/ |
| Performance scenario and result | performance/load_test_staff_queue.py; performance.json |
| Live journeys and restart evidence | scripts/m3_verify_live.py; live-system-journeys.json; process-restart.json |
| Traceability and defects | docs/requirements/RTM.csv; docs/quality/defect-register.csv |
| Debt and residual risks | docs/quality/technical-debt-register.md; docs/release/m3-release-evidence-summary.md |
| Decisions/scope requiring review | docs/release/team-decision-review.md; docs/decisions/issue-65-draft-rows.csv; CHG-002 |
| AI accountability and progressive history | docs/governance/ai-usage-register.csv; PROJECT_HISTORY.md; final PR/commit |

Each student should be able to demonstrate: FR-014/AC-014 -> service version guard -> acceptance regression -> live journey #501 -> audit/outbox/notification evidence -> residual outbox recovery risk -> release condition. Emile should also explain NFR-001's dataset, concurrency, warm-up, duration, p95 method and local-only limits.

## 22.7 Final review actions

1. Emile inspects this candidate. The authenticated GitHub commit records technical authorship; personal acceptance and final baseline signatures remain separate.
2. Don reviews backend/migration/outbox, existing ADR statuses and the six draft register rows.
3. Masego independently verifies test classification, role/privacy coverage and RTM; both non-author reviewers review the exact integration diff.
4. Record actual scope/decision agreement, resolve findings, pass required CI and merge through the PR process.
5. Record the final SHA/tag, actual approvals and residual-risk acceptance; regenerate the controlled PED v3 PDF. This review export is not the final signed baseline.

Sources checked 16 October 2026: https://flask.palletsprojects.com/en/stable/testing/ and https://render.com/docs/free. Repository artefacts above supply implementation and execution evidence.
