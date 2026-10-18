### 2026-10-17 - DEC-008 recommendation and consolidated ASR table (proposal only)
**Who:** Don, with Claude Code assistance (AI-046) - **Type:** docs, decision proposal
**What:** Added `docs/decisions/DEC-008-recommendation.md`: ASR table, weighted matrices for stack and platform, recommendation and the evidence still required. Corrected the record that the stack is Python/Flask (Node.js was only a scored alternative).
**Evidence:** Matrix totals recomputed by script; test and coverage figures from a local run on `main` 6e99ae6 (60 passed, 83%). No provider free-tier terms were verified, and the doc says so.
**Review:** DEC-008 stays Deferred and ADR-001/007 stay Proposed. Needs two non-author approvals; this is a recommendation, not approval.
