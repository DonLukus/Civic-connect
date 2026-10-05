from src.persistence.lifecycle import LifecycleValidator


def test_can_accept_when_new_and_unassigned():
    """FR-014/FR-015: New + unassigned is the only combination that may become Accepted."""
    assert LifecycleValidator.can_accept("New", None) is True
    assert LifecycleValidator.validate_transition("New", None, "Accepted", 7) is True
    print("[PASS] test_can_accept_when_new_and_unassigned")


def test_cannot_accept_when_already_assigned():
    assert LifecycleValidator.can_accept("New", 1) is False
    assert LifecycleValidator.validate_transition("New", 1, "Accepted", 7) is False
    print("[PASS] test_cannot_accept_when_already_assigned")


def test_cannot_accept_when_not_new():
    for status in ("Accepted", "In Progress", "On Hold", "Resolved", "Closed", "Rejected"):
        assert LifecycleValidator.can_accept(status, None) is False, f"{status} should not accept"
        assert LifecycleValidator.validate_transition(status, None, "Accepted", 7) is False
    print("[PASS] test_cannot_accept_when_not_new")


if __name__ == "__main__":
    test_can_accept_when_new_and_unassigned()
    test_cannot_accept_when_already_assigned()
    test_cannot_accept_when_not_new()
    print("All tests passed.")
