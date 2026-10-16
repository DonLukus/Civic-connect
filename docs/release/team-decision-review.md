# M3 decisions for team review — 16 October 2026

Prepared for Emile, Don and Masego. These are recommendations, not recorded votes.

| Topic | Recommended disposition | Evidence and remaining decision |
|---|---|---|
| Test boundary | Keep Flask test-client cases labelled in-process functional/integration tests. Add the two live HTTP system journeys in `scripts/m3_verify_live.py`; retain browser walkthrough evidence separately. | Flask's test client does not run a server. The team must confirm the evidence mix against the brief, rather than rename tests to meet a quota. |
| M3 staging | Use isolated Windows/Waitress/SQLite staging for the scoped demonstration, with synthetic users and a local SMTP sink. | Reproducible setup in `docs/deployment/m3-staging.md`. This demonstrates controlled simulated staging, not public uptime or external email delivery. |
| Render and DEC-008 | Keep DEC-008 Deferred; exclude ephemeral local SQLite from any durable hosted release. | Render documents loss of local files on free-service restart/redeploy/spindown. This is consistent with the M2 observation, but the historical instance configuration was not independently recovered. Not redeploying does not prevent idle shutdown. |
| Production database | Compare persistent storage/managed PostgreSQL before public release; do not claim PostgreSQL selected or implemented. | Local restart evidence cannot close the hosted persistence requirement. Any paid option needs an explicit cost/constraint decision. |
| PR #83/#84 | Review actual backend/static/context changes and tests with both non-author students before integration. | The integrated candidate includes these changes plus a logout-CSRF regression fix; earlier approvals do not automatically cover new changes. |
| Scope | Retain the user-reported journey scope: authenticated submission, own list/detail, Staff status filter and acceptance, acceptance notification. | Manager/Admin login and safe landing exist; their operational features remain deferred. FR-012 is status-filter-only; FR-015 is New→Accepted-only. Must-priority exclusions must stay explicit in the change/scope record, not be marked fulfilled. |
| Credential storage | Treat bcrypt verification as candidate evidence only until final reviewed code and account migration policy are accepted. | Fresh staging accounts are inspected by the live harness. Legacy hashes upgrade only on successful login; dormant legacy accounts require reset/migration disposition. |
| Issue #65 | Review `docs/decisions/issue-65-draft-rows.csv` against the ADRs, then append agreed rows to the canonical log. | Six draft rows; no new approval inferred. Accepted ADRs map to Decided; Proposed ADRs remain Deferred in the log until accepted. DEC-008 is not closed. |
| Review identity | Count independent people, not GitHub accounts. Don uses one account for future reviews. | Don's alternate account is not an independent reviewer of his own work. Existing approval provenance must remain accurate. |
| Review comments | Name the behaviour/files checked and any remaining limits in each approval. | Do not paste a review claim until the reviewer actually performs it. |

## Suggested review order

1. Don and Masego review backend behaviour and Emile's integration diff; reproduce the tests.
2. Confirm scope, staged environment and test boundaries; record actual decisions and dates.
3. Don reconciles the six decision rows and ADR statuses; Masego validates test classification and RTM coverage.
4. Emile freezes the reviewed commit, reruns evidence as necessary and regenerates PED v3 PDF.
5. Both non-author reviewers approve the final revision. Merge only when required checks pass.

## Source corrections for Issue #65

The long comment is background, not authoritative implementation evidence. Its outbox is not event sourcing; an outbox does not guarantee exactly-once email delivery; a single deployable unit can still idle; and PostgreSQL has not been selected merely because a diagram names it. ADR-001 and ADR-007 still say Proposed in the source reviewed here.

Sources checked 16 October 2026: [Flask testing](https://flask.palletsprojects.com/en/stable/testing/), [Render free-service limits](https://render.com/docs/free), repository ADRs and source. The SMTP sink validates local transport and message capture only.
