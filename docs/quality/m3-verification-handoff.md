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
4. Check RTM's added execution-evidence column and all partial scope claims. FR-012 is filter-only, FR-015 covers New-to-Accepted, FR-001 Administrator provisioning UI is not implemented, and FR-009 covers acceptance/local transport only.
5. Review independently with Don and Emile before approving the final revision. Neither another Don account nor AI execution supplies an additional human review.


## Registration addition - 16 October

User-requested self-registration now supplies 11 additional cases in `test_registration.py`: successful bcrypt-backed Requester creation/login (submitted privileged role ignored), invalid email/password/UTF-8 limits, case-insensitive duplicates, CSRF rejection and confirmation mismatch. FR-001 remains partial because Administrator provisioning/audit are not implemented. Inspect `registration-live.json` and the latest `registration-regression.xml`; the original 39-case result is the earlier integration snapshot. Review the new public route and the proposed 8-character registration minimum before final approval.

## Dated finalisation reconciliation - 18 October 2026

Earlier 18/39/50-case and pending-matrix notes retain their dates. The merged pre-finalisation suite has 60 cases; TST-051/052 now add a nested privacy regression and mid-session deactivation check, producing 62 passing cases on the review branch. DEF-006 was reproduced before correction. Full matrix evidence from #86 is addressed for implemented operations. Use the current RTM M4 QA fields, section 23 and the 18 October verification summary; absent operations and original acceptance obligations are not silently marked complete.
