"""
M3 verification: requester isolation (FR-008 / NFR-012 boundary at the one route that exists).

Scope note: FR-008 ("view own request history") has no list route yet in src/web/app.py - only
the single-request confirmation page (request_submitted) exists, and it already enforces
ownership. This test exercises that enforcement directly rather than waiting for the list route,
which is Don's/Emile's build - see docs/quality/test-inventory.md Gap 2.
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

from src.persistence.request_service import RequestService
from src.web.app import create_app

TEST_SESSION_KEY = 'test-secret'  # deliberately non-secret fixture


def setup_db(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)

    schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'persistence', 'schema.sql')
    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    finally:
        conn.close()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)",
            ('requester-a@example.com', generate_password_hash('pw-a')),
        )
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)",
            ('requester-b@example.com', generate_password_hash('pw-b')),
        )
        conn.execute("INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Utilities', 48, 1)")
        conn.commit()
    finally:
        conn.close()


def login_as(client, email, password):
    assert client.get('/login').status_code == 200
    with client.session_transaction() as sess:
        csrf = sess['_csrf_token']
    response = client.post('/login', data={'email': email, 'password': password, 'csrf_token': csrf})
    assert response.status_code == 302


def test_requester_cannot_open_another_requesters_confirmation_page():
    """FR-008 / NFR-012: requester A's request must 404, not display, for requester B."""
    db_path = 'test_isolation.sqlite'
    setup_db(db_path)

    conn = sqlite3.connect(db_path)
    requester_a_id = conn.execute(
        "SELECT id FROM users WHERE email = 'requester-a@example.com'"
    ).fetchone()[0]
    conn.close()

    request_id = RequestService(db_path).create_request(
        requester_id=requester_a_id, category_id=1,
        title='A private matter', description='desc', location='loc',
    )

    app = create_app(db_path, secret_key=TEST_SESSION_KEY)
    client = app.test_client()
    login_as(client, 'requester-b@example.com', 'pw-b')

    response = client.get(f'/requests/{request_id}/submitted')
    assert response.status_code == 404, (
        "requester B must not be able to open requester A's confirmation page"
    )

    os.remove(db_path)
    print("[PASS] test_requester_cannot_open_another_requesters_confirmation_page")


def test_owning_requester_can_open_own_confirmation_page():
    """Control case: the same route must still work for the actual owner."""
    db_path = 'test_isolation.sqlite'
    setup_db(db_path)

    conn = sqlite3.connect(db_path)
    requester_a_id = conn.execute(
        "SELECT id FROM users WHERE email = 'requester-a@example.com'"
    ).fetchone()[0]
    conn.close()

    request_id = RequestService(db_path).create_request(
        requester_id=requester_a_id, category_id=1,
        title='A private matter', description='desc', location='loc',
    )

    app = create_app(db_path, secret_key=TEST_SESSION_KEY)
    client = app.test_client()
    login_as(client, 'requester-a@example.com', 'pw-a')

    response = client.get(f'/requests/{request_id}/submitted')
    assert response.status_code == 200, "the owning requester must still be able to open their own page"

    os.remove(db_path)
    print("[PASS] test_owning_requester_can_open_own_confirmation_page")


if __name__ == '__main__':
    test_requester_cannot_open_another_requesters_confirmation_page()
    test_owning_requester_can_open_own_confirmation_page()
    print("All tests passed.")
