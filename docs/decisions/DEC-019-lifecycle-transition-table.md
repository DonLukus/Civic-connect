# DEC-019 (proposed): request lifecycle transition table

**Status: PROPOSED, not approved.** Implemented in `src/persistence/lifecycle.py` so the functional
requirements FR-014 to FR-018 can be met and demonstrated; it needs the team's decision. It is one
table, so changing it means editing one place and the tests in `tests/test_m4_workflow.py`.

## Why a proposal is needed

FR-015 names seven states and fixes only a few rules. The baselined requirements say, and the code
enforces:

| Rule | Source |
|---|---|
| Accept (Staff) or assign (Manager) moves New to Accepted, notifies the Requester, is audited | FR-014 |
| A Manager reassigning leaves the status unchanged and records the previous and new assignee | FR-014 (CHG-001) |
| A Closed request can change only through a defined reopen path; every permitted change is audited | FR-015 |
| Moving to Resolved needs a resolution note, stored with author and time | FR-016 |
| Only a Manager closes a Resolved request; Staff are refused | FR-017 |
| Rejecting needs a reason, which is stored, and the Requester is notified | FR-018 |

The requirements do **not** say which other moves are allowed, who may make them, or what the reopen
path is. Per `PROJECT_RULES.md` section 3 that is a gap to flag, not to hide. The table below is the
smallest reading that makes the seven states usable.

## The proposed table

| From | May move to | Who |
|---|---|---|
| New | Accepted (accept or assign), Rejected | Accepted: Staff self-accept or Manager assign. Rejected: Manager only |
| Accepted | In Progress, On Hold, Resolved, Rejected | assigned Staff or Manager |
| In Progress | On Hold, Resolved, Rejected | assigned Staff or Manager |
| On Hold | In Progress, Rejected | assigned Staff or Manager |
| Resolved | Closed, In Progress | Closed: Manager only. In Progress (work not finished): assigned Staff or Manager |
| Closed | In Progress (the reopen path) | Manager only, with a reason |
| Rejected | nothing (final) | |

Other rules: Accepted is reachable only through accept or assign. Every change checks a version number,
so a stale page is refused (409) and nothing is written. A change, its audit row and any notification
commit together.

## Questions for the team

1. Is the reopen path (Closed to In Progress, Manager only, reason required) acceptable, or should
   reopening go somewhere else or be allowed for Staff?
2. May Staff reject a New request, or must they accept it first? (Proposed: Manager only.)
3. Is Rejected final, or may a Manager return a rejected request to New? FR-018 says "reject or return"
   but its acceptance criterion defines only Rejected.
4. Should "Resolved to In Progress" exist, or is Resolved always followed by Closed?

Until the team decides, the behaviour above is what the application does and what is tested.
