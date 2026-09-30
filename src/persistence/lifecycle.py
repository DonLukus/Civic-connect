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
        return current_status == "New" and current_assignee_id is None
