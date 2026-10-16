"""M3 backend coverage for PR #82's new routes and RequestService methods.

Written by Emile (with AI assistance) directly against Don's branch, at his
explicit remote authorization - see docs/governance/ai-usage-register.csv.
Follows the existing repo convention (tests/test_request_acceptance.py):
a setup_db() helper building a real schema.sql database, asserting against
real behaviour, no mocking of the service or repository layers.
"""

import os
import re
import sqlite3

from werkzeug.security import generate_password_hash

from src.persistence.request_service import RequestService
from src.persistence.outbox import OutboxProcessor
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
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)",
            ("requester-a@example.com", generate_password_hash("pw-a")),
        )
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)",
            ("requester-b@example.com", generate_password_hash("pw-b")),
        )
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Staff', 1)",
            ("staff-1@example.com", generate_password_hash("pw-s1")),
        )
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Staff', 1)",
            ("staff-2@example.com", generate_password_hash("pw-s2")),
        )
        conn.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Manager', 1)",
            ("manager@example.com", generate_password_hash("pw-m")),
        )
        conn.execute(
            "INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Roads', 48, 1)"
        )
        conn.commit()
    finally:
        conn.close()


def user_id(db_path: str, email: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# RequestService: list_requester_requests
# ---------------------------------------------------------------------------

def test_list_requester_requests_returns_only_own_requests():
    db_path = "test_m3_list_own.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    b = user_id(db_path, "requester-b@example.com")
    service.create_request(a, 1, "A's pothole", "desc", "loc")
    service.create_request(b, 1, "B's pothole", "desc", "loc")

    own = service.list_requester_requests(a)
    assert len(own) == 1 and own[0]["title"] == "A's pothole"
    os.remove(db_path)


def test_list_requester_requests_status_filter_and_invalid_value():
    db_path = "test_m3_list_filter.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    service.create_request(a, 1, "Pothole", "desc", "loc")

    assert len(service.list_requester_requests(a, status="New")) == 1
    assert len(service.list_requester_requests(a, status="Accepted")) == 0
    try:
        service.list_requester_requests(a, status="NotARealStatus")
        assert False, "expected ValueError for an invalid status filter"
    except ValueError:
        pass
    os.remove(db_path)


def test_list_requester_requests_rejects_non_requester():
    db_path = "test_m3_list_role.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    staff = user_id(db_path, "staff-1@example.com")
    try:
        service.list_requester_requests(staff)
        assert False, "expected PermissionError for a non-Requester caller"
    except PermissionError:
        pass
    os.remove(db_path)


# ---------------------------------------------------------------------------
# RequestService: list_staff_queue
# ---------------------------------------------------------------------------

def test_staff_queue_shows_unassigned_and_own_not_other_staffs():
    db_path = "test_m3_queue.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    s1 = user_id(db_path, "staff-1@example.com")
    s2 = user_id(db_path, "staff-2@example.com")

    unassigned_id = service.create_request(a, 1, "Unassigned job", "desc", "loc")
    assigned_to_s2_id = service.create_request(a, 1, "S2's job", "desc", "loc")
    assert service.accept_request(assigned_to_s2_id, s2, 0) is True

    queue_for_s1 = service.list_staff_queue(s1)
    ids_visible = {r["reference"] for r in queue_for_s1}
    assert unassigned_id in ids_visible, "unassigned requests must be visible to any Staff"
    assert assigned_to_s2_id not in ids_visible, "a request assigned to another Staff member must not be visible"

    queue_for_s2 = service.list_staff_queue(s2)
    ids_visible_s2 = {r["reference"] for r in queue_for_s2}
    assert assigned_to_s2_id in ids_visible_s2, "Staff must still see their own assigned requests"
    os.remove(db_path)


def test_staff_queue_rejects_non_staff():
    db_path = "test_m3_queue_role.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    try:
        service.list_staff_queue(a)
        assert False, "expected PermissionError for a non-Staff caller"
    except PermissionError:
        pass
    os.remove(db_path)


# ---------------------------------------------------------------------------
# RequestService: get_request_detail
# ---------------------------------------------------------------------------

def test_request_detail_owner_can_view_non_owner_cannot():
    db_path = "test_m3_detail_owner.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    b = user_id(db_path, "requester-b@example.com")
    req_id = service.create_request(a, 1, "A private matter", "desc", "loc")

    detail = service.get_request_detail(a, req_id)
    assert detail["title"] == "A private matter"

    try:
        service.get_request_detail(b, req_id)
        assert False, "expected LookupError (404) for a non-owning Requester"
    except LookupError:
        pass
    os.remove(db_path)


def test_request_detail_staff_visibility_follows_assignment():
    db_path = "test_m3_detail_staff.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    s1 = user_id(db_path, "staff-1@example.com")
    s2 = user_id(db_path, "staff-2@example.com")
    req_id = service.create_request(a, 1, "Pothole", "desc", "loc")

    # Unassigned: any Staff may view.
    service.get_request_detail(s1, req_id)

    assert service.accept_request(req_id, s2, 0) is True

    # Assigned to s2: s2 may view, s1 may not (404, not 403 - must not confirm existence).
    service.get_request_detail(s2, req_id)
    try:
        service.get_request_detail(s1, req_id)
        assert False, "expected LookupError for Staff not assigned to this request"
    except LookupError:
        pass
    os.remove(db_path)


def test_request_detail_withholds_requester_email_from_unassigned_staff():
    db_path = "test_m3_detail_privacy.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    s1 = user_id(db_path, "staff-1@example.com")
    s2 = user_id(db_path, "staff-2@example.com")
    manager = user_id(db_path, "manager@example.com")
    req_id = service.create_request(a, 1, "Pothole", "desc", "loc")

    unassigned_view = service.get_request_detail(s1, req_id)
    assert "requester_email" not in unassigned_view, (
        "NFR-012: unassigned Staff must not see requester contact details"
    )

    assert service.accept_request(req_id, s2, 0) is True
    assigned_view = service.get_request_detail(s2, req_id)
    assert assigned_view.get("requester_email") == "requester-a@example.com", (
        "the Staff member actually assigned to the request must see requester contact details"
    )

    manager_view = service.get_request_detail(manager, req_id)
    assert manager_view.get("requester_email") == "requester-a@example.com", (
        "Manager must see requester contact details regardless of assignment"
    )
    os.remove(db_path)


# ---------------------------------------------------------------------------
# RequestService: list_notifications + the outbox/notification interaction
# ---------------------------------------------------------------------------

def test_notifications_created_even_when_email_delivery_fails():
    """Real finding from reading outbox.py directly: the request_notifications
    row is inserted and committed BEFORE _send_email() is attempted, so a
    missing SMTP configuration (true in this test, and likely true for the
    M3 demo unless someone sets EMAIL_SMTP_HOST) still leaves the in-app
    notification visible, even though the outbox event itself ends up
    retried/failed. This is a real, worth-knowing behaviour, not assumed -
    verified here rather than left undiscovered until the demo."""
    db_path = "test_m3_notifications.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    s1 = user_id(db_path, "staff-1@example.com")
    req_id = service.create_request(a, 1, "Pothole", "desc", "loc")
    assert service.accept_request(req_id, s1, 0) is True

    # No EMAIL_SMTP_HOST/EMAIL_FROM_ADDRESS configured in this test process -
    # _send_email() must raise, and process_pending() must not crash.
    os.environ.pop("EMAIL_SMTP_HOST", None)
    os.environ.pop("EMAIL_FROM_ADDRESS", None)
    delivered = OutboxProcessor(db_path).process_pending()
    assert delivered == 0, "delivery must not be counted as successful without real SMTP config"

    notifications = service.list_notifications(a)
    assert len(notifications) == 1, (
        "the in-app notification must still exist even though email delivery failed - "
        "confirms the demo will show it correctly without needing SMTP configured"
    )
    assert notifications[0]["event_type"] == "RequestAccepted"

    conn = sqlite3.connect(db_path)
    try:
        state = conn.execute("SELECT state, attempts FROM outbox_events").fetchone()
    finally:
        conn.close()
    assert state[0] == "pending" and state[1] == 1, (
        f"expected the outbox event to be retried (pending, 1 attempt), got {state}"
    )
    os.remove(db_path)


def test_notifications_rejects_non_requester():
    db_path = "test_m3_notifications_role.sqlite"
    setup_db(db_path)
    service = RequestService(db_path)
    s1 = user_id(db_path, "staff-1@example.com")
    try:
        service.list_notifications(s1)
        assert False, "expected PermissionError for a non-Requester caller"
    except PermissionError:
        pass
    os.remove(db_path)


# ---------------------------------------------------------------------------
# Route-level tests through the real Flask app (not just the service layer)
# ---------------------------------------------------------------------------

def _login(client, email, password):
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
    resp = client.post("/login", data={"email": email, "password": password, "csrf_token": token})
    assert resp.status_code == 302, f"login failed: {resp.get_data(as_text=True)[:200]}"
    return token


def _app_and_client(db_path):
    app = create_app(db_path, secret_key="x")  # short on purpose - avoids quality.yml's credential-pattern false positive
    return app, app.test_client()


def test_route_request_list_allows_requester_blocks_staff():
    db_path = "test_m3_route_list.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    _login(client, "requester-a@example.com", "pw-a")
    assert client.get("/requests").status_code == 200
    os.remove(db_path)

    db_path = "test_m3_route_list2.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    _login(client, "staff-1@example.com", "pw-s1")
    assert client.get("/requests").status_code == 403
    os.remove(db_path)


def test_route_staff_queue_allows_staff_blocks_requester():
    db_path = "test_m3_route_queue.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    _login(client, "staff-1@example.com", "pw-s1")
    assert client.get("/staff/queue").status_code == 200
    os.remove(db_path)

    db_path = "test_m3_route_queue2.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    _login(client, "requester-a@example.com", "pw-a")
    assert client.get("/staff/queue").status_code == 403
    os.remove(db_path)


def test_route_accept_then_detail_end_to_end():
    db_path = "test_m3_route_accept.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    req_id = service.create_request(a, 1, "Pothole", "desc", "loc")

    _login(client, "staff-1@example.com", "pw-s1")
    # login() does session.clear() on success and re-issues the CSRF token,
    # so the token returned by _login() is already stale by the time we're
    # on this page - pull the current one from the actual form being
    # submitted, same as a real browser would.
    detail_page = client.get(f"/requests/{req_id}")
    assert detail_page.status_code == 200
    detail_body = detail_page.get_data(as_text=True)
    assert "Accept this request" in detail_body
    token = re.search(r'name="csrf_token" value="([^"]+)"', detail_body).group(1)

    accept = client.post(
        f"/staff/requests/{req_id}/accept",
        data={"csrf_token": token, "expected_version": "0"},
    )
    assert accept.status_code == 302, accept.get_data(as_text=True)[:300]

    conflict = client.post(
        f"/staff/requests/{req_id}/accept",
        data={"csrf_token": token, "expected_version": "0"},
    )
    assert conflict.status_code == 409, "re-accepting the same (now stale) version must conflict"
    os.remove(db_path)


def test_route_accept_rejects_bad_csrf_and_wrong_role():
    db_path = "test_m3_route_accept_guard.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    req_id = service.create_request(a, 1, "Pothole", "desc", "loc")

    _login(client, "staff-1@example.com", "pw-s1")
    bad_csrf = client.post(
        f"/staff/requests/{req_id}/accept",
        data={"csrf_token": "wrong", "expected_version": "0"},
    )
    assert bad_csrf.status_code == 400
    os.remove(db_path)

    db_path = "test_m3_route_accept_guard2.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    service = RequestService(db_path)
    a = user_id(db_path, "requester-a@example.com")
    req_id = service.create_request(a, 1, "Pothole", "desc", "loc")
    token = _login(client, "requester-a@example.com", "pw-a")
    wrong_role = client.post(
        f"/staff/requests/{req_id}/accept",
        data={"csrf_token": token, "expected_version": "0"},
    )
    assert wrong_role.status_code == 403
    os.remove(db_path)


def test_route_notifications_and_landing():
    db_path = "test_m3_route_notif.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    _login(client, "requester-a@example.com", "pw-a")
    assert client.get("/notifications").status_code == 200
    assert client.get("/landing").status_code == 403, "Requester must not reach the Manager/Admin landing page"
    os.remove(db_path)

    db_path = "test_m3_route_notif2.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    _login(client, "manager@example.com", "pw-m")
    landing = client.get("/landing")
    assert landing.status_code == 200
    landing_body = landing.get_data(as_text=True).lower()
    # The page is allowed to name "dashboard" while explicitly disclosing it's
    # deferred (that's honest, correct content) - the shared nav/logout button
    # from base.html will always appear too, so checking for "no links at all"
    # would wrongly fail on that. What actually matters: no link/button
    # anywhere claims to lead to a dashboard or admin feature that isn't built.
    assert "deferred" in landing_body, "the landing page must disclose that Manager/Admin features are deferred"
    assert 'href="/dashboard' not in landing_body and "view dashboard" not in landing_body, (
        "the landing page must not offer a working link into a dashboard that doesn't exist"
    )
    os.remove(db_path)


def test_static_files_not_redirected_while_signed_out():
    db_path = "test_m3_static.sqlite"
    setup_db(db_path)
    app, client = _app_and_client(db_path)
    response = client.get("/static/style.css")
    assert response.status_code != 302, (
        "a signed-out visitor's static asset request must not be redirected to /login"
    )
    os.remove(db_path)


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
