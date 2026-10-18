"""
ADR-003's transition-table validator, extracted as a reusable, testable module.

Deliberately partial: FR-015 names the seven states (New, Accepted, In Progress, On Hold,
Resolved, Closed, Rejected) but does not yet specify the full legal-transition table beyond what
FR-014 concretely tests - New -> Accepted via a Staff self-accept or a Manager assignment, guarded
by "not already assigned" (CHG-001). Encoding the rest of the table here would be inventing
business rules nobody has approved (PROJECT_RULES §3). This module formalises only the rule that
is actually specified and tested, as a named, reusable check instead of an inline conditional -
closing the "no extracted implementation" gap noted against ADR-003 without fabricating the rest
of the table. Extend LifecycleValidator as each further transition is actually specified.
"""



class LifecycleValidator:
    """Stateless checks for FR-015 status transitions. See module docstring for scope."""

    @staticmethod
    def can_accept(current_status: str, current_assignee_id: int | None) -> bool:
        """FR-014: a request may move New -> Accepted only while unassigned and in New."""
        if current_status is None:
            return False
        return current_status == "New" and current_assignee_id is None

    @staticmethod
    def validate_transition(
        current_status: str | None,
        current_assignee_id: int | None,
        target_status: str,
        target_assignee_id: int | None = None,
    ) -> bool:
        """Validate only the transition explicitly specified and approved for M2.

        FR-014 defines the only approved M2 state change in the current requirement set:
        a still-New, unassigned request may move to Accepted when a Staff/Manager takes it.
        The rest of FR-015 remains deferred until a requirement is written and reviewed.
        """
        if target_status == "Accepted":
            return (
                current_status == "New"
                and current_assignee_id is None
                and target_assignee_id is not None
            )

        return False


# ---------------------------------------------------------------------------------------------
# FR-015..FR-018: the full transition table.
#
# PROPOSED, NOT YET TEAM-APPROVED (see docs/decisions/DEC-019-lifecycle-transition-table.md).
# The baselined requirements name the seven states and fix only these rules: a Closed request may
# change only through the defined reopen path (FR-015), Resolved needs a note (FR-016), only a
# Manager closes (FR-017), Rejected needs a reason (FR-018), and accept/assign moves New to
# Accepted (FR-014). Everything else below is the smallest sensible reading, kept in this one
# table so the team can change it in one place.
# ---------------------------------------------------------------------------------------------
STATUSES = ("New", "Accepted", "In Progress", "On Hold", "Resolved", "Closed", "Rejected")
OPEN_STATUSES = ("New", "Accepted", "In Progress", "On Hold")
TERMINAL_STATUSES = ("Resolved", "Closed", "Rejected")

TRANSITIONS = {
    "New": {"Accepted", "Rejected"},
    "Accepted": {"In Progress", "On Hold", "Resolved", "Rejected"},
    "In Progress": {"On Hold", "Resolved", "Rejected"},
    "On Hold": {"In Progress", "Rejected"},
    "Resolved": {"Closed", "In Progress"},
    "Closed": {"In Progress"},  # the defined reopen path
    "Rejected": set(),
}

# Transitions only a Manager may make (everything else is open to the assigned Staff user and Manager).
MANAGER_ONLY = {("Resolved", "Closed"), ("Closed", "In Progress"), ("New", "Rejected")}


def check_transition(role: str, is_assignee: bool, current: str, target: str) -> None:
    """Raise PermissionError / ValueError unless this actor may make this change of status."""
    if target not in STATUSES:
        raise ValueError("status must be one of the supported request statuses")
    if target not in TRANSITIONS.get(current, set()) or target == "Accepted":
        raise ValueError(f"A {current} request cannot move to {target}")
    if role == "Manager":
        return
    if (current, target) in MANAGER_ONLY:
        raise PermissionError("Only a Manager may make this change")
    if role == "Staff" and is_assignee:
        return
    raise PermissionError("Only the assigned Staff user or a Manager may change this request's status")


def required_note(current: str, target: str) -> str | None:
    """Name of the mandatory explanation for this change, or None."""
    if target == "Resolved":
        return "resolution note"
    if target == "Rejected":
        return "reason"
    if current == "Closed":
        return "reason"
    return None
