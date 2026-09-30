import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from src.persistence.request_service import RequestService
from src.web.app import create_app


def setup_db(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)

    schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'persistence', 'schema.sql')
    # NOTE: `with sqlite3.connect(...) as conn:` commits/rolls back on exit but does NOT close
    # the connection (stdlib sqlite3 behaviour) - left open, this holds a Windows file lock that
    # a later os.remove() on the db file fails against. Explicit close fixes it throughout this
    # file (same fix applied to tests/test_request_acceptance.py and RequestService).
    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    finally:
        conn.close()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)", ('requester@example.com', generate_password_hash('test-password')))
        conn.execute("INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Utilities', 48, 1)")
        conn.execute("INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Retired category', 48, 0)")
        conn.commit()
    finally:
        conn.close()


# --- RequestService.create_request (FR-005, FR-006), service layer ---

def test_create_request_succeeds_with_valid_data():
    """FR-005: mandatory fields captured; audit row recorded (ADR-001 creation decision)."""
    db_path = 'test_submission.sqlite'
    setup_db(db_path)
    service = RequestService(db_path)

    request_id = service.create_request(
        requester_id=1, category_id=1, title='Broken pipe',
        description='Leak in building', location='Block 4',
    )

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT status, version, assignee_id FROM requests WHERE id = ?", (request_id,)
        ).fetchone()
        assert row == ('New', 0, None), f"Expected new request in status New, got {row}"

        audit = conn.execute(
            "SELECT action_type, previous_status, new_status FROM request_audit WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        assert audit == ('request_submitted', None, 'New'), f"Expected a CREATED-equivalent audit row, got {audit}"

        outbox_count = conn.execute(
            "SELECT COUNT(*) FROM outbox_events WHERE aggregate_id = ?", (request_id,)
        ).fetchone()[0]
        assert outbox_count == 0, "No outbox event on submission - FR-009 doesn't trigger on creation (ADR-001)"
    finally:
        conn.close()

    os.remove(db_path)
    print("[PASS] test_create_request_succeeds_with_valid_data passed")


def test_create_request_rejects_missing_title():
    """FR-005: title is mandatory."""
    db_path = 'test_submission.sqlite'
    setup_db(db_path)
    service = RequestService(db_path)

    try:
        service.create_request(requester_id=1, category_id=1, title='', description='x', location='x')
        assert False, "Expected ValueError for missing title"
    except ValueError as exc:
        assert 'title' in str(exc)

    os.remove(db_path)
    print("[PASS] test_create_request_rejects_missing_title passed")


def test_create_request_rejects_inactive_category():
    """FR-006: category must come from the active controlled list, not just any existing row."""
    db_path = 'test_submission.sqlite'
    setup_db(db_path)
    service = RequestService(db_path)

    try:
        service.create_request(requester_id=1, category_id=2, title='x', description='x', location='x')
        assert False, "Expected ValueError for an inactive category"
    except ValueError as exc:
        assert 'category' in str(exc)

    os.remove(db_path)
    print("[PASS] test_create_request_rejects_inactive_category passed")


def test_create_request_rejects_unknown_category():
    """FR-006: category must exist at all, not just be free text coerced to an id."""
    db_path = 'test_submission.sqlite'
    setup_db(db_path)
    service = RequestService(db_path)

    try:
        service.create_request(requester_id=1, category_id=999, title='x', description='x', location='x')
        assert False, "Expected ValueError for a non-existent category"
    except ValueError as exc:
        assert 'category' in str(exc)

    os.remove(db_path)
    print("[PASS] test_create_request_rejects_unknown_category passed")


# --- The UI path (Flask test client), FR-005/FR-006 end to end ---

def login_client(client):
    assert client.get('/login').status_code == 200
    with client.session_transaction() as sess:
        csrf = sess['_csrf_token']
    response = client.post('/login', data={
        'email': 'requester@example.com', 'password': 'test-password', 'csrf_token': csrf,
    })
    assert response.status_code == 302
    with client.session_transaction() as sess:
        return sess['_csrf_token']

def test_web_submit_request_end_to_end():
    """The traced slice through the actual route: form -> service -> DB -> confirmation page."""
    db_path = 'test_submission_web.sqlite'
    setup_db(db_path)
    app = create_app(db_path, secret_key='test-secret')
    client = app.test_client()

    assert client.get('/requests/new').status_code == 302
    csrf = login_client(client)

    get_response = client.get('/requests/new')
    assert get_response.status_code == 200
    assert b'Submit a service request' in get_response.data

    post_response = client.post('/requests', data={
        'title': 'Streetlight out',
        'description': 'Corner of 5th and Main',
        'category_id': '1',
        'location': 'Corner of 5th and Main',
        'csrf_token': csrf,
    })
    assert post_response.status_code == 302, "Expected a redirect to the confirmation page"

    confirm_response = client.get(post_response.headers['Location'])
    assert confirm_response.status_code == 200
    assert b'Request received' in confirm_response.data

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        assert count == 1
    finally:
        conn.close()

    os.remove(db_path)
    print("[PASS] test_web_submit_request_end_to_end passed")


def test_web_submit_request_rejects_invalid_category():
    """The route surfaces FR-006's validation, not a 500 error, on a bad category."""
    db_path = 'test_submission_web.sqlite'
    setup_db(db_path)
    app = create_app(db_path, secret_key='test-secret')
    client = app.test_client()

    csrf = login_client(client)

    response = client.post('/requests', data={
        'title': 'x', 'description': 'x', 'category_id': '999', 'location': 'x',
        'csrf_token': csrf,
    })
    assert response.status_code == 400
    assert b'category' in response.data

    os.remove(db_path)
    print("[PASS] test_web_submit_request_rejects_invalid_category passed")


def test_unauthenticated_submission_does_not_write():
    db_path = 'test_submission_web.sqlite'
    setup_db(db_path)
    client = create_app(db_path, secret_key='test-secret').test_client()
    response = client.post('/requests', data={
        'title': 'x', 'description': 'x', 'category_id': '1', 'location': 'x',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute('SELECT COUNT(*) FROM requests').fetchone()[0] == 0
    finally:
        conn.close()
    os.remove(db_path)


def test_bad_password_does_not_authenticate():
    db_path = 'test_submission_web.sqlite'
    setup_db(db_path)
    client = create_app(db_path, secret_key='test-secret').test_client()
    client.get('/login')
    with client.session_transaction() as sess:
        csrf = sess['_csrf_token']
    response = client.post('/login', data={
        'email': 'requester@example.com', 'password': 'wrong', 'csrf_token': csrf,
    })
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data
    assert client.get('/requests/new').status_code == 302
    os.remove(db_path)


def test_missing_csrf_does_not_write():
    db_path = 'test_submission_web.sqlite'
    setup_db(db_path)
    client = create_app(db_path, secret_key='test-secret').test_client()
    login_client(client)
    response = client.post('/requests', data={
        'title': 'x', 'description': 'x', 'category_id': '1', 'location': 'x',
    })
    assert response.status_code == 400
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute('SELECT COUNT(*) FROM requests').fetchone()[0] == 0
    finally:
        conn.close()
    os.remove(db_path)


def test_service_rejects_staff_submission():
    db_path = 'test_submission.sqlite'
    setup_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES ('staff@example.com', 'x', 'Staff', 1)")
        staff_id = conn.execute("SELECT id FROM users WHERE email = 'staff@example.com'").fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    try:
        RequestService(db_path).create_request(staff_id, 1, 'x', 'x', 'x')
        assert False, 'Staff should not be allowed to submit as Requester'
    except PermissionError:
        pass
    os.remove(db_path)


if __name__ == '__main__':
    test_create_request_succeeds_with_valid_data()
    test_create_request_rejects_missing_title()
    test_create_request_rejects_inactive_category()
    test_create_request_rejects_unknown_category()
    test_web_submit_request_end_to_end()
    test_web_submit_request_rejects_invalid_category()
    print("All tests passed.")
