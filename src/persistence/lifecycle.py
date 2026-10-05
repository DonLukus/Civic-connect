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

from typing import Optional


class LifecycleValidator:
    """Stateless checks for FR-015 status transitions. See module docstring for scope."""

    @staticmethod
    def can_accept(current_status: str, current_assignee_id: Optional[int]) -> bool:
        """FR-014: a request may move New -> Accepted only while unassigned and in New."""
        if current_status is None:
            return False
        return current_status == "New" and current_assignee_id is None

    @staticmethod
    def validate_transition(
        current_status: Optional[str],
        current_assignee_id: Optional[int],
        target_status: str,
        target_assignee_id: Optional[int] = None,
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
