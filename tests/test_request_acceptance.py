import os
import sqlite3
import threading
import time

from request_service import RequestService


def setup_db(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executescript(open('src/persistence/schema.sql').read())

    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Staff', 1)", ('staff1@example.com', 'hash'))
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Staff', 1)", ('staff2@example.com', 'hash'))
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)", ('requester@example.com', 'hash'))
        conn.execute("INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Utilities', 48, 1)")
        conn.execute(
            "INSERT INTO requests (requester_id, assignee_id, category_id, title, description, location, status, version) VALUES (?, ?, ?, 'Broken pipe', 'Leak in building', 'Block 4', 'New', 0)",
            (3, None, 1),
        )


def test_double_accept_rejected():
    db_path = 'test_requests.sqlite'
    setup_db(db_path)
    service = RequestService(db_path)

    assert service.accept_request(1, 1, 0) is True
    assert service.accept_request(1, 2, 0) is False

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT assignee_id, status, version FROM requests WHERE id = 1").fetchone()
        assert row == (1, 'Accepted', 1)
        audit_count = conn.execute("SELECT COUNT(*) FROM request_audit WHERE request_id = 1").fetchone()[0]
        assert audit_count == 1

    os.remove(db_path)


if __name__ == '__main__':
    test_double_accept_rejected()
    print('ok')
