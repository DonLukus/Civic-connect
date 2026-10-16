# 22. M3 construction, verification and release review

**CivicConnect - PED v3.0, merged 16-17 October 2026.** Prepared by Emile with AI assistance recorded in AI-036 and AI-038/042. Continues the existing M1/M2 PED sources; no historical signature or baseline status is changed.

## 22.1 Candidate and construction

**Merged into `main` at commit `c7e92de8f818b66ca1ecc0faf88b0987c4b17b40` via PR #85**, after Don and Masego approved PR head `e76b96e74515e5cc813c6fba4cd1805362e5c020`. The merge commit and the reviewed PR head are distinct identifiers. PR #85 folded together the backend routes, route tests, UI templates and dependency-check changes originally opened as PRs #80-84, plus PR #86 (the full role x operation authorisation matrix across all four roles, and the RTM scope-wording corrections both Don and Emile made after independent AI-assisted review). PRs #80, #82, #83 and #84 were closed as superseded once their content was verified present on `main` - not merged separately, to avoid duplicate/conflicting code. PR #81 (dependency-audit workflow) was independent of this chain and merged separately. Source revisions and file hashes are indexed in `docs/release/evidence/2026-10-16/source-manifest.json`. The registration addition is identified separately by `registration-source-manifest.json`.

Implemented slice: public Requester registration, login, submission, own list/detail/status; Staff login, queue/status filter/detail/acceptance; acceptance notification through in-app and SMTP; Manager/Administrator login with a safe landing page. `docs/deployment/m3-interface-agreement.md` records actual routes, forms, roles and error behaviour. `CHG-002` records the release-slice exclusions and impact; Don and Masego recorded acceptance for the supervised M3 evaluation. Baselined priorities and excluded obligations remain unchanged.

Two integration defects were corrected: missing CSRF tokens in shared logout forms on list/landing pages (DEF-004), and a mismatched audit-actor field in the detail template (DEF-005). Both have regression checks.

## 22.2 Architecture and configuration conformance

The candidate follows layered server-rendered Flask, service-level rules, SQLite persistence, transactional state/audit/outbox changes and an in-process notification worker. ADR-002/003/004/006 remain Accepted in the source; ADR-001/007 remain Proposed. DEC-008 remains Deferred. **The six Issue #65 decisions are now logged in `docs/decisions/decision-log.csv` as DEC-013 through DEC-018** (§10.4), reconciled directly against each ADR's actual current status - Deferred for DEC-013/018 (ADR-001/007, still Proposed), Decided for DEC-014/015/016/017 (ADR-002/003/004/006, Accepted). Logging them does not itself move ADR-001 or ADR-007 to Accepted; that is a separate, still-open team decision. Issue #65 is closed - the gap it raised (ADRs existing without a corresponding register entry) is fixed, not the underlying architecture/auth placement decisions themselves.

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

**Public production release: NOT READY.** Don and Masego reviewed and approved the supervised M3 evaluation slice before PR #85 merged. Their CHG-002 decisions and the decision-register reconciliation are recorded; those completed steps are no longer pending. This corrected full PED export requires its own review and final documentation identifier. No new production-readiness classification, signature or M2 baseline acceptance is inferred. See the dated update in the release summary for the remaining conditions and owners.

Unresolved claims include durable hosted storage, external SMTP/TLS, dormant legacy-hash disposition, inactive-user/session edge cases beyond the documented role matrix, stuck/duplicate outbox recovery, reversible schema/code rollback, sustained availability, cold-start, capacity and accessibility. A local backup drill does not prove daily backup scheduling or retention. Local restart success does not close the M2 Render redeploy failure.

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
| Decisions/scope requiring review | docs/release/team-decision-review.md; docs/decisions/decision-log.csv (DEC-013..018); CHG-002 |
| AI accountability and progressive history | docs/governance/ai-usage-register.csv; PROJECT_HISTORY.md; final PR/commit |

Each student should be able to demonstrate: FR-014/AC-014 -> service version guard -> acceptance regression -> live journey #501 -> audit/outbox/notification evidence -> residual outbox recovery risk -> release condition. Emile should also explain NFR-001's dataset, concurrency, warm-up, duration, p95 method and local-only limits.

## 22.7 Final review actions - status as of 17 October 2026

1. ~~Emile inspects the candidate~~ - Reviews and test executions are recorded in PRs #85/#86, with AI assistance declared in the register.
2. ~~Don reviews backend, migration, outbox and decisions~~ - His AI-assisted reviews identified and corrected test-count, coverage, test-layer and scope-status claims. The operational limitations remain recorded.
3. ~~Masego records her CHG-002 decision/date~~ - Her acceptance is recorded under her account in PR #86, separately from Don's decision.
4. ~~Resolve the unconfigured Copilot review requirement~~ - The recorded resolution removed `copilot_code_review` from `main-protection-basic-02`; it did not rely on a merge bypass.
5. ~~Obtain two non-author approvals~~ - Don and Masego approved PR #85 head `e76b96e74515e5cc813c6fba4cd1805362e5c020`. The recorded seven CI checks passed.
6. ~~Merge the implementation~~ - PR #85 merged at `c7e92de8f818b66ca1ecc0faf88b0987c4b17b40`. PR #81 merged separately; PRs #80/82/83/84 closed as superseded after content checks.
7. ~~Log the six Issue #65 decisions~~ - DEC-013..018 appear in `decision-log.csv` and PED section 10.4; Issue #65 is closed.

**Still genuinely open, not closed by any of the above:** ADR-001 and ADR-007 remain Proposed - merging to `main` logs the decisions, it does not accept them. Durable hosted storage, external SMTP/TLS, dormant legacy password hashes, sustained availability, capacity and accessibility all remain unverified - see `docs/release/m3-release-evidence-summary.md`'s residual-risk table. This milestone's evaluation slice is complete and merged; a production release is a separate, later decision.

Sources checked 16 October 2026: https://flask.palletsprojects.com/en/stable/testing/ and https://render.com/docs/free. Repository artefacts above supply implementation and execution evidence.
