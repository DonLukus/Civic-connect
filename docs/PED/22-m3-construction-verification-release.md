# 22. M3 construction, verification and release review

**CivicConnect - PED v3.0 review candidate, updated 17 October 2026.** Prepared by Emile with AI assistance recorded in AI-036 and AI-038/039. Continues the existing M1/M2 PED sources; no historical signature or baseline status is changed.

## 22.1 Candidate and construction

The integration candidate combines the current main snapshot with the proposed backend, route tests, UI and dependency-check changes in PRs #80-84, plus PR #86 (the full role x operation authorisation matrix across all four roles, and the RTM scope-wording corrections both Don and Emile made after independent AI-assisted review). Source revisions and file hashes are indexed in `docs/release/evidence/2026-10-16/source-manifest.json`. The registration addition is identified separately by `registration-source-manifest.json`. A final signed release SHA/tag is pending.

Implemented slice: public Requester registration, login, submission, own list/detail/status; Staff login, queue/status filter/detail/acceptance; acceptance notification through in-app and SMTP; Manager/Administrator login with a safe landing page. `docs/deployment/m3-interface-agreement.md` records actual routes, forms, roles and error behaviour. `CHG-002` records the proposed release-slice exclusions and impact without rewriting baselined priorities.

Two integration defects were corrected: missing CSRF tokens in shared logout forms on list/landing pages (DEF-004), and a mismatched audit-actor field in the detail template (DEF-005). Both have regression checks.

## 22.2 Architecture and configuration conformance

The candidate follows layered server-rendered Flask, service-level rules, SQLite persistence, transactional state/audit/outbox changes and an in-process notification worker. ADR-002/003/004/006 remain Accepted in the source; ADR-001/007 remain Proposed. DEC-008 remains Deferred. The six Issue #65 register rows are draft proposals awaiting team reconciliation, not accepted decisions.

Staging is a distinct loopback Waitress process with a generated synthetic database, separate credentials and local STARTTLS SMTP sink. Config/secrets and the database stay Git-ignored. This simulates staging and does not establish public HTTPS, availability or production durability. See `docs/deployment/m3-staging.md`.

## 22.3 Verification results

| Evidence | Result | Scope |
|---|---|---|
| pytest automated suite | 60 passed (re-verified fresh in an isolated worktree, not just the commit message) | 39 historical + 11 registration cases (registration-regression.xml) + 10 new role x operation matrix cases (PR #86) |
| Backend regression follow-up | 16 passed | Includes corrected rendered audit actor assertion |
| Role x operation matrix | 10/10 passed, including the previously-missing positive case (assigned Staff viewing their own accepted request) | `tests/test_m3_role_operation_matrix.py`; `docs/quality/role-operation-matrix.md`; closes the coverage gap Don's AI-assisted review found on the first integration commit |
| Ruff / Bandit / dependency audit | Clean / no medium-high findings / no known application dependency findings | Tool results at check time, not complete security proof |
| Live HTTP system journey 1 | Passed | Requester login, submit #501, receipt, list/detail, logout and cross-requester denial |
| Live HTTP system journey 2 | Passed | Staff filter/detail/accept, requester status, in-app notification and local SMTP capture |
| Browser walkthrough | Request #502 submitted and accepted | Actual browser UI operated; form/receipt screenshots retained; no checked-in browser automation claim |
| NFR-001 five-minute load | 8,503 successful; 0 failures; p95 0.422s | 10 distinct Staff users, 500 filtered records, local warm instance, target <=2s |
| Local process restart | Passed | Accepted #501 retrieved after stop/start of same-file staging |
| Online backup/separate restore | Passed | Integrity check OK; request/audit/outbox counts preserved |

`docs/release/evidence/2026-10-16/` holds execution reports. The five-second smoke run is explicitly insufficient for NFR-001. The subsequent 300-second run supplies the stated measurement. The load/restart/backup evidence predates registration and was not rerun. Registration-live.json separately confirms public signup and login; email verification and signup rate limiting remain outstanding. No browser rendering benchmark or production-capacity claim is made.

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

## 22.7 Final review actions - status as of 17 October 2026

1. ~~Emile inspects this candidate~~ - done, repeatedly, across each corrected commit, with real re-execution each time (not just re-reading commit messages).
2. ~~Don reviews backend/migration/outbox, existing ADR statuses and the six draft register rows~~ - done. Don's AI-assisted review of the first integration commit (9d10b11) found real gaps (stale test counts, a coverage overclaim, inaccurate test-layer history, a scope-approval wording overclaim); all were corrected, re-verified, and **Don approved PR #86 against the corrected commit (f060d41)**.
3. Masego independently verified test classification, role/privacy coverage and RTM, and fixed everything Don's review flagged on her side (PR #86, commit 6eebb3c). **Her own CHG-002 decision/date, separate from the technical fix, is the one item still outstanding** - CHG-002 itself names her specifically, and her approving the PR mechanically does not substitute for it, since she is PR #86's author and cannot approve her own PR.
4. PR #86: 2 real non-author approvals in (Don, Emile), both against the final corrected commit, both with documented re-verification. PR #85 (the broader integration candidate) still needs the same from both reviewers once #86 is folded into it.
5. Record the final SHA/tag, actual approvals and residual-risk acceptance; regenerate the controlled PED v3 PDF once #85/#86 are consolidated and merged. This review export is still not the final signed baseline.

Sources checked 16 October 2026: https://flask.palletsprojects.com/en/stable/testing/ and https://render.com/docs/free. Repository artefacts above supply implementation and execution evidence.
