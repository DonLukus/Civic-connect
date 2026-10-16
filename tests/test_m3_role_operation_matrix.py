"""M3 verification: role x operation authorisation matrix, exercised through the actual
HTTP routes (not the service layer directly).

Why this file exists: every route-level authorisation check up to this point was either
untested, or tested at the RequestService layer only (e.g. test_request_detail_owner_can_view_
non_owner_cannot calls service.get_request_detail directly). A service-layer pass does not
prove the route actually calls the service, with the right actor id, before rendering - a
wiring mistake in app.py would not be caught by a service-only test. NFR-004 ("100% of
role-restricted operations reject unauthorised access") cannot be claimed from service tests
alone; this file closes that by hitting every route as every role that should be rejected,
through the real Flask test client.

Administrator is included here for the first time outside the shared-navigation logout test
(tests/test_m3_logout.py, which only exercises GET /landing positively for that role) - no
prior test checked that Administrator is blocked from any Requester/Staff-only route.
"""

import os
import re
import sqlite3

from werkzeug.security import generate_password_hash

from src.persistence.request_service import RequestService
from src.web.app import create_app

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "persistence", "schema.sql")


def setup_db(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
    finally:
        conn.close()

    conn = sqlite3.connect(db_path)
    try:
        for email, role, pw in [
            ("requester-a@example.com", "Requester", "pw-a"),
            ("requester-b@example.com", "Requester", "pw-b"),
            ("staff-1@example.com", "Staff", "pw-s1"),
            ("staff-2@example.com", "Staff", "pw-s2"),
            ("manager@example.com", "Manager", "pw-m"),
            ("admin@example.com", "Administrator", "pw-admin"),
        ]:
            conn.execute(
                "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                (email, generate_password_hash(pw), role),
            )
        conn.execute("INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Roads', 48, 1)")
        conn.commit()
    finally:
        conn.close()


def user_id(db_path: str, email: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]
    finally:
        conn.close()


def login(client, email: str, password: str) -> str:
    """Logs in and returns the session's CSRF token for use in subsequent POSTs."""
    page = client.get("/login").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    response = client.post("/login", data={"email": email, "password": password, "csrf_token": token})
    assert response.status_code == 302, f"login failed for {email}"
    with client.session_transaction() as sess:
        return sess["_csrf_token"]


CREDENTIALS = {
    "Requester": ("requester-a@example.com", "pw-a"),
    "Requester-B": ("requester-b@example.com", "pw-b"),
    "Staff": ("staff-1@example.com", "pw-s1"),
    "Staff-2": ("staff-2@example.com", "pw-s2"),
    "Manager": ("manager@example.com", "pw-m"),
    "Administrator": ("admin@example.com", "pw-admin"),
}


def _client(db_path):
    return create_app(db_path, secret_key="test-secret").test_client()


# ---------------------------------------------------------------------------
# Requester-only operations: GET /requests/new, POST /requests, GET /notifications,
# GET /requests (own list) must reject Staff, Manager and Administrator.
# ---------------------------------------------------------------------------

def test_new_request_form_blocks_non_requester():
    db_path = "test_matrix_new_form.sqlite"
    setup_db(db_path)
    for role in ("Staff", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get("/requests/new")
        assert response.status_code == 403, f"{role} must not reach the request-submission form"
    os.remove(db_path)


def test_submit_request_blocks_non_requester_at_route():
    """Route-level complement to test_service_rejects_staff_request_creation (TST-015),
    which only calls the service directly."""
    db_path = "test_matrix_submit.sqlite"
    setup_db(db_path)
    for role in ("Staff", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        token = login(client, email, pw)
        response = client.post(
            "/requests",
            data={"category_id": "1", "title": "x", "description": "y", "location": "z", "csrf_token": token},
        )
        assert response.status_code == 403, f"{role} must not be able to submit a request through the route"
    os.remove(db_path)


def test_request_submitted_blocks_non_requester_and_non_owner_roles():
    db_path = "test_matrix_submitted.sqlite"
    setup_db(db_path)
    a = user_id(db_path, "requester-a@example.com")
    req_id = RequestService(db_path).create_request(a, 1, "A private matter", "desc", "loc")

    for role in ("Staff", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get(f"/requests/{req_id}/submitted")
        assert response.status_code == 403, f"{role} must not reach a Requester's own confirmation page"
    os.remove(db_path)


def test_request_list_blocks_staff_manager_administrator():
    db_path = "test_matrix_list.sqlite"
    setup_db(db_path)
    for role in ("Staff", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get("/requests")
        assert response.status_code == 403, f"{role} must not reach the Requester's own-request list"
    os.remove(db_path)


def test_notifications_blocks_staff_manager_administrator():
    db_path = "test_matrix_notifications.sqlite"
    setup_db(db_path)
    for role in ("Staff", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get("/notifications")
        assert response.status_code == 403, f"{role} must not reach a Requester's notifications"
    os.remove(db_path)


# ---------------------------------------------------------------------------
# Staff-only operations: GET /staff/queue, POST /staff/requests/<id>/accept must reject
# Requester, Manager and Administrator.
# ---------------------------------------------------------------------------

def test_staff_queue_blocks_requester_manager_administrator():
    db_path = "test_matrix_queue.sqlite"
    setup_db(db_path)
    for role in ("Requester", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get("/staff/queue")
        assert response.status_code == 403, f"{role} must not reach the Staff queue"
    os.remove(db_path)


def test_accept_request_blocks_requester_manager_administrator():
    db_path = "test_matrix_accept.sqlite"
    setup_db(db_path)
    a = user_id(db_path, "requester-a@example.com")
    req_id = RequestService(db_path).create_request(a, 1, "Pothole", "desc", "loc")

    for role in ("Requester", "Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        token = login(client, email, pw)
        response = client.post(
            f"/staff/requests/{req_id}/accept",
            data={"csrf_token": token, "expected_version": "0"},
        )
        assert response.status_code == 403, f"{role} must not be able to accept a request"

    # Confirm the request is genuinely untouched by any of the three rejected attempts above.
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT status, assignee_id, version FROM requests WHERE id = ?", (req_id,)).fetchone()
        assert row == ("New", None, 0), "a rejected accept attempt must not mutate the request"
    finally:
        conn.close()
    os.remove(db_path)


# ---------------------------------------------------------------------------
# Manager/Administrator-only: GET /landing must reject Requester and Staff, and must be
# reachable by both Manager and Administrator (not just Manager, as prior tests checked).
# ---------------------------------------------------------------------------

def test_landing_blocks_requester_and_staff_allows_manager_and_administrator():
    db_path = "test_matrix_landing.sqlite"
    setup_db(db_path)
    for role in ("Requester", "Staff"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get("/landing")
        assert response.status_code == 403, f"{role} must not reach the Manager/Administrator landing page"

    for role in ("Manager", "Administrator"):
        client = _client(db_path)
        email, pw = CREDENTIALS[role]
        login(client, email, pw)
        response = client.get("/landing")
        assert response.status_code == 200, f"{role} must be able to reach the landing page"
    os.remove(db_path)


# ---------------------------------------------------------------------------
# GET /requests/<id> (request_detail): this is the one route every role can legitimately
# reach, but visibility differs per role/ownership/assignment. Previously tested only at the
# RequestService layer (test_request_detail_owner_can_view_non_owner_cannot, etc.) - never
# through the HTTP route, so a route-wiring bug (wrong actor id, missing error mapping) would
# not have been caught.
# ---------------------------------------------------------------------------

def test_request_detail_route_enforces_role_and_ownership():
    db_path = "test_matrix_detail_route.sqlite"
    setup_db(db_path)
    a = user_id(db_path, "requester-a@example.com")
    s1 = user_id(db_path, "staff-1@example.com")
    req_id = RequestService(db_path).create_request(a, 1, "Pothole", "desc", "loc")

    # Owning Requester: 200.
    client = _client(db_path)
    login(client, *CREDENTIALS["Requester"])
    assert client.get(f"/requests/{req_id}").status_code == 200

    # Non-owning Requester: 404, not 403 - must not confirm the request's existence.
    client = _client(db_path)
    login(client, *CREDENTIALS["Requester-B"])
    assert client.get(f"/requests/{req_id}").status_code == 404

    # Unassigned Staff: 200 (any Staff may view an unassigned request).
    client = _client(db_path)
    login(client, *CREDENTIALS["Staff"])
    assert client.get(f"/requests/{req_id}").status_code == 200

    # Accept with staff-1, then staff-2 (unassigned to it) must get 404.
    RequestService(db_path).accept_request(req_id, s1, 0)
    client = _client(db_path)
    login(client, *CREDENTIALS["Staff-2"])
    assert client.get(f"/requests/{req_id}").status_code == 404, (
        "a Staff member not assigned to an already-accepted request must get 404 through the route"
    )

    # Manager and Administrator: 200 regardless of assignment (oversight access).
    for role in ("Manager", "Administrator"):
        client = _client(db_path)
        login(client, *CREDENTIALS[role])
        response = client.get(f"/requests/{req_id}")
        assert response.status_code == 200, f"{role} must be able to view any request's detail"
    os.remove(db_path)


# ---------------------------------------------------------------------------
# GET / (home): redirect target must match the signed-in role, for all four roles - not
# previously tested at all.
# ---------------------------------------------------------------------------

def test_home_redirects_by_role():
    db_path = "test_matrix_home.sqlite"
    setup_db(db_path)
    expected = {
        "Requester": "/requests",
        "Staff": "/staff/queue",
        "Manager": "/landing",
        "Administrator": "/landing",
    }
    for role, target in expected.items():
        client = _client(db_path)
        login(client, *CREDENTIALS[role])
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].endswith(target), (
            f"{role} must be redirected to {target}, got {response.headers['Location']}"
        )
    os.remove(db_path)


if __name__ == "__main__":
    import sys

    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
