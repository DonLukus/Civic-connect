import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from src.persistence.request_service import RequestService


def setup_db(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)

    schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'persistence', 'schema.sql')
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())

    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Staff', 1)", ('staff1@example.com', 'hash'))
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Staff', 1)", ('staff2@example.com', 'hash'))
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)", ('requester@example.com', 'hash'))
        conn.execute("INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Utilities', 48, 1)")
        conn.execute(
            "INSERT INTO requests (requester_id, assignee_id, category_id, title, description, location, status, version) VALUES (?, ?, ?, 'Broken pipe', 'Leak in building', 'Block 4', 'New', 0)",
            (3, None, 1),
        )
        conn.commit()


def test_double_accept_rejected():
    """Test that the optimistic update prevents duplicate acceptance (FR-014 correctness rule)."""
    db_path = 'test_requests.sqlite'
    setup_db(db_path)
    service = RequestService(db_path)

    # First staff member accepts; should succeed
    assert service.accept_request(1, 1, 0) is True, "First acceptance should succeed"
    
    # Second staff member tries to accept with same version; should fail
    assert service.accept_request(1, 2, 0) is False, "Second acceptance should be rejected (concurrency guard)"

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT assignee_id, status, version FROM requests WHERE id = 1").fetchone()
        assert row == (1, 'Accepted', 1), f"Expected (1, 'Accepted', 1), got {row}"
        audit_count = conn.execute("SELECT COUNT(*) FROM request_audit WHERE request_id = 1").fetchone()[0]
        assert audit_count == 1, f"Expected 1 audit row, got {audit_count}"

    os.remove(db_path)
    print("✓ test_double_accept_rejected passed")


if __name__ == '__main__':
    test_double_accept_rejected()
    print("All tests passed.")
