# M3 verification update for Masego

16 October 2026 integration candidate. The original `test-inventory.md` is a dated kickoff snapshot: its 18-test/no-new-routes observations remain historical, not the current candidate count.

- Existing main: 18 pytest cases. PR #84 contributes 16 named cases covering service and route integration. Shared-navigation logout regression contributes 5 role/page combinations. Combined suite: **39 passed**; these are not 39 browser tests.
- Existing unit/component and black-box minimums remain covered. Equivalence partitioning (valid/invalid categories, ownership/role partitions) and state transitions (valid acceptance, stale/illegal acceptance) are identifiable techniques. Avoid counting negative/security testing as a separate formal black-box technique on its own.
- `scripts/m3_verify_live.py journeys` supplies two sequential live HTTP system journeys. They assert Requester creation/visibility/isolation and Staff filtering/acceptance/requester notification. SMTP uses a local STARTTLS sink. Browser walkthrough of #502 is supplementary; no persistent browser automation suite is claimed.
- Load scenario is separate: 10 distinct Staff users, 500 matching New records, 300 seconds, no errors, p95 0.422s. Record NFR-001 as local-candidate evidence only.
- `tests/test_m3_logout.py` checks real login, rendered token, successful logout and denied subsequent access on five page/role combinations. `test_route_accept_then_detail_end_to_end` now also asserts a rendered audit actor. These cover DEF-004/005.

## Review still needed

1. Reproduce the exact candidate revision; confirm 39 collected and passed, plus the two live HTTP journeys. Assign stable inventory IDs to the new named cases without changing TST-001?018.
2. Complete a role x operation table for Requester, Staff, Manager and Administrator, including own/other records, direct service calls, missing CSRF and stale acceptance. Mark gaps rather than infer full NFR-004 compliance.
3. Verify bcrypt cost and legacy migration disposition; the 14 fresh staged accounts are evidence for fresh data only.
4. Check RTM's added execution-evidence column and all partial scope claims. FR-012 is filter-only, FR-015 covers New-to-Accepted, FR-001 provisioning UI is not implemented, and FR-009 covers acceptance/local transport only.
5. Review independently with Don and Emile before approving the final revision. Neither another Don account nor AI execution supplies an additional human review.
