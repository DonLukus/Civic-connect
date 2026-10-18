"""FR-007, FR-009, FR-010, FR-013 to FR-018, FR-025: the request workflow.

Service-level and route-level cases on a real schema.sql database, synthetic data only. Users are
inserted directly (no password hashing) so the cases stay fast; routes are driven with a session.
"""

import json
import sqlite3
from pathlib import Path

import pytest

from src.persistence.migrations import ensure_schema
from src.persistence.outbox import OutboxProcessor
from src.persistence.request_service import RequestService, VersionConflict
from src.web.app import create_app

SCHEMA = Path(__file__).resolve().parents[1] / "src" / "persistence" / "schema.sql"
APP_KEY = "test-signing-value"
REQ_A, REQ_B, STAFF_1, STAFF_2, MANAGER, ADMIN = 1, 2, 3, 4, 5, 6


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "m4.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    users = [("req-a@example.test", "Requester"), ("req-b@example.test", "Requester"),
             ("staff-1@example.test", "Staff"), ("staff-2@example.test", "Staff"),
             ("manager@example.test", "Manager"), ("admin@example.test", "Administrator")]
    for email, role in users:
        conn.execute("INSERT INTO users(email,password_hash,role,is_active) VALUES (?,?,?,1)",
                     (email, "x", role))
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES ('Roads',48,1)")
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def svc(db):
    return RequestService(db)


def make_request(svc, requester=REQ_A):
    return svc.create_request(requester, 1, "Pothole", "Deep pothole", "Main Rd")


def version(db, request_id):
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT version FROM requests WHERE id=?", (request_id,)).fetchone()[0]


def row(db, sql, args=()):
    with sqlite3.connect(db) as conn:
        return conn.execute(sql, args).fetchall()


def accepted_request(svc, db, assignee=STAFF_1):
    rid = make_request(svc)
    svc.assign_request(rid, MANAGER, assignee, version(db, rid))
    return rid


# ---------------------------------------------------------------- FR-014 assign / reassign

def test_manager_assigns_new_request_which_becomes_accepted_and_notifies(svc, db):
    rid = make_request(svc)
    svc.assign_request(rid, MANAGER, STAFF_1, version(db, rid))
    status, assignee = row(db, "SELECT status, assignee_id FROM requests WHERE id=?", (rid,))[0]
    assert (status, assignee) == ("Accepted", STAFF_1)
    audit = row(db, "SELECT action_type, previous_status, new_status, previous_assignee_id, "
                    "new_assignee_id, actor_user_id FROM request_audit WHERE request_id=? ORDER BY id", (rid,))
    assert audit[-1] == ("assign_request", "New", "Accepted", None, STAFF_1, MANAGER)
    assert row(db, "SELECT event_type, state FROM outbox_events WHERE aggregate_id=?", (rid,)) == [
        ("RequestAccepted", "pending")]


def test_reassign_changes_only_the_assignee_and_records_both(svc, db):
    rid = accepted_request(svc, db, STAFF_1)
    svc.change_status(rid, STAFF_1, "In Progress", version(db, rid))
    svc.assign_request(rid, MANAGER, STAFF_2, version(db, rid))
    status, assignee = row(db, "SELECT status, assignee_id FROM requests WHERE id=?", (rid,))[0]
    assert (status, assignee) == ("In Progress", STAFF_2)
    last = row(db, "SELECT action_type, previous_status, new_status, previous_assignee_id, new_assignee_id "
                   "FROM request_audit WHERE request_id=? ORDER BY id DESC LIMIT 1", (rid,))[0]
    assert last == ("reassign_request", None, None, STAFF_1, STAFF_2)
    # a reassignment is not a notification trigger and does not count as a status change
    assert row(db, "SELECT COUNT(*) FROM outbox_events WHERE aggregate_id=?", (rid,)) == [(1,)]
    detail = svc.get_request_detail(MANAGER, rid)
    assert detail["last_status_changed_at"]  # still the In Progress change, not the reassignment


@pytest.mark.parametrize("actor", [STAFF_1, REQ_A, ADMIN])
def test_only_a_manager_may_assign(svc, db, actor):
    rid = make_request(svc)
    with pytest.raises(PermissionError):
        svc.assign_request(rid, actor, STAFF_1, version(db, rid))
    assert row(db, "SELECT status, assignee_id FROM requests WHERE id=?", (rid,)) == [("New", None)]


def test_assignment_rules(svc, db):
    rid = make_request(svc)
    v = version(db, rid)
    with pytest.raises(ValueError, match="active Staff"):
        svc.assign_request(rid, MANAGER, REQ_B, v)
    with pytest.raises(LookupError):
        svc.assign_request(999, MANAGER, STAFF_1, 0)
    with pytest.raises(VersionConflict):
        svc.assign_request(rid, MANAGER, STAFF_1, v + 5)
    svc.assign_request(rid, MANAGER, STAFF_1, v)
    with pytest.raises(ValueError, match="already the assignee"):
        svc.assign_request(rid, MANAGER, STAFF_1, version(db, rid))


def test_inactive_staff_cannot_be_assigned(svc, db):
    rid = make_request(svc)
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE users SET is_active=0 WHERE id=?", (STAFF_2,))
    with pytest.raises(ValueError, match="active Staff"):
        svc.assign_request(rid, MANAGER, STAFF_2, version(db, rid))


# ---------------------------------------------------------------- FR-015..FR-018 lifecycle

def test_full_journey_records_every_change_in_order(svc, db):
    rid = make_request(svc)
    svc.assign_request(rid, MANAGER, STAFF_1, version(db, rid))
    svc.change_status(rid, STAFF_1, "In Progress", version(db, rid))
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "Filled and sealed")
    svc.change_status(rid, MANAGER, "Closed", version(db, rid))
    audit = row(db, "SELECT action_type, previous_status, new_status, actor_user_id FROM request_audit "
                    "WHERE request_id=? ORDER BY id", (rid,))
    assert audit == [("request_submitted", None, "New", REQ_A),
                     ("assign_request", "New", "Accepted", MANAGER),
                     ("change_status", "Accepted", "In Progress", STAFF_1),
                     ("change_status", "In Progress", "Resolved", STAFF_1),
                     ("change_status", "Resolved", "Closed", MANAGER)]
    detail = svc.get_request_detail(REQ_A, rid)
    assert detail["status"] == "Closed" and detail["resolution_note"] == "Filled and sealed"
    assert len(detail["history"]) == 5


def test_resolving_needs_a_note_and_stores_it_with_author_and_time(svc, db):
    rid = accepted_request(svc, db)
    for note in (None, "", "   "):
        with pytest.raises(ValueError, match="resolution note"):
            svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), note)
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("Accepted",)]
    assert row(db, "SELECT COUNT(*) FROM request_audit WHERE request_id=?", (rid,)) == [(2,)]
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "  Replaced the valve  ")
    note, by, at = row(db, "SELECT resolution_note, resolution_by, resolution_at FROM requests WHERE id=?", (rid,))[0]
    assert (note, by) == ("Replaced the valve", STAFF_1) and at
    assert ("RequestResolved",) in row(db, "SELECT event_type FROM outbox_events WHERE aggregate_id=?", (rid,))


def test_rejecting_needs_a_reason_stores_it_and_notifies(svc, db):
    rid = accepted_request(svc, db)
    with pytest.raises(ValueError, match="reason"):
        svc.change_status(rid, STAFF_1, "Rejected", version(db, rid), "")
    svc.change_status(rid, STAFF_1, "Rejected", version(db, rid), "Not a council road")
    assert row(db, "SELECT status, rejection_reason FROM requests WHERE id=?", (rid,)) == [
        ("Rejected", "Not a council road")]
    event = row(db, "SELECT payload_json FROM outbox_events WHERE event_type='RequestRejected'")[0][0]
    assert json.loads(event)["reason"] == "Not a council road"


def test_a_manager_may_reject_a_new_unassigned_request_but_staff_may_not(svc, db):
    rid = make_request(svc)
    with pytest.raises(PermissionError):
        svc.change_status(rid, STAFF_1, "Rejected", version(db, rid), "no")
    svc.change_status(rid, MANAGER, "Rejected", version(db, rid), "Duplicate of #7")
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("Rejected",)]


def test_staff_cannot_close_and_a_manager_can(svc, db):
    rid = accepted_request(svc, db)
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "done")
    with pytest.raises(PermissionError):
        svc.change_status(rid, STAFF_1, "Closed", version(db, rid))
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("Resolved",)]
    svc.change_status(rid, MANAGER, "Closed", version(db, rid))
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("Closed",)]


@pytest.mark.parametrize("target", ["New", "Accepted", "Resolved", "Closed", "Rejected", "On Hold"])
def test_closed_only_allows_the_reopen_path(svc, db, target):
    rid = accepted_request(svc, db)
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "done")
    svc.change_status(rid, MANAGER, "Closed", version(db, rid))
    before = row(db, "SELECT status, version FROM requests WHERE id=?", (rid,))
    with pytest.raises(ValueError):
        svc.change_status(rid, MANAGER, target, version(db, rid), "because")
    assert row(db, "SELECT status, version FROM requests WHERE id=?", (rid,)) == before


def test_reopen_is_manager_only_needs_a_reason_and_is_audited(svc, db):
    rid = accepted_request(svc, db)
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "done")
    svc.change_status(rid, MANAGER, "Closed", version(db, rid))
    with pytest.raises(PermissionError):
        svc.change_status(rid, STAFF_1, "In Progress", version(db, rid), "reopen")
    with pytest.raises(ValueError, match="reason"):
        svc.change_status(rid, MANAGER, "In Progress", version(db, rid), "")
    svc.change_status(rid, MANAGER, "In Progress", version(db, rid), "Leak returned")
    assert row(db, "SELECT previous_status, new_status FROM request_audit WHERE request_id=? "
                   "ORDER BY id DESC LIMIT 1", (rid,)) == [("Closed", "In Progress")]


def test_rejected_is_final(svc, db):
    rid = accepted_request(svc, db)
    svc.change_status(rid, STAFF_1, "Rejected", version(db, rid), "no")
    for target in ("In Progress", "Resolved", "Closed", "Accepted", "New"):
        with pytest.raises(ValueError):
            svc.change_status(rid, MANAGER, target, version(db, rid), "x")


def test_accepted_cannot_be_set_through_a_status_change(svc, db):
    rid = make_request(svc)
    with pytest.raises(ValueError):
        svc.change_status(rid, MANAGER, "Accepted", version(db, rid))


def test_staff_cannot_change_a_request_assigned_to_someone_else_or_unassigned(svc, db):
    rid = accepted_request(svc, db, STAFF_1)
    with pytest.raises(LookupError):
        svc.change_status(rid, STAFF_2, "In Progress", version(db, rid))
    new = make_request(svc)
    with pytest.raises(PermissionError):
        svc.change_status(new, STAFF_2, "Rejected", version(db, new), "x")
    for actor in (REQ_A, ADMIN):
        with pytest.raises(PermissionError):
            svc.change_status(rid, actor, "In Progress", version(db, rid))
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("Accepted",)]


def test_stale_version_is_refused_without_changes(svc, db):
    rid = accepted_request(svc, db)
    stale = version(db, rid)
    svc.change_status(rid, STAFF_1, "In Progress", stale)
    with pytest.raises(VersionConflict):
        svc.change_status(rid, STAFF_1, "On Hold", stale)
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("In Progress",)]


def test_failed_change_leaves_no_audit_or_outbox_rows(svc, db):
    rid = accepted_request(svc, db)
    audit = row(db, "SELECT COUNT(*) FROM request_audit")[0][0]
    outbox = row(db, "SELECT COUNT(*) FROM outbox_events")[0][0]
    with pytest.raises(ValueError):
        svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "")
    assert row(db, "SELECT COUNT(*) FROM request_audit")[0][0] == audit
    assert row(db, "SELECT COUNT(*) FROM outbox_events")[0][0] == outbox


def test_note_length_is_bounded(svc, db):
    rid = accepted_request(svc, db)
    with pytest.raises(ValueError, match="at most"):
        svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "x" * 2001)


# ---------------------------------------------------------------- FR-010 comments

def test_requester_and_assigned_staff_comment_and_both_see_the_thread(svc, db):
    rid = accepted_request(svc, db)
    svc.add_comment(rid, STAFF_1, "Crew booked for Friday")
    svc.add_comment(rid, REQ_A, "Thank you")
    for viewer in (REQ_A, STAFF_1, MANAGER, ADMIN):
        thread = svc.get_request_detail(viewer, rid)["comments"]
        assert [(c["author_role"], c["body"]) for c in thread] == [
            ("Staff", "Crew booked for Friday"), ("Requester", "Thank you")]
        assert all(c["created_at"] and c["author_id"] for c in thread)
        assert "@" not in json.dumps(thread)  # no email address in the thread itself


def test_requester_view_hides_the_assignee_contact_details(svc, db):
    rid = accepted_request(svc, db)
    assert "assignee_email" not in svc.get_request_detail(REQ_A, rid)
    assert svc.get_request_detail(MANAGER, rid)["assignee_email"] == "staff-1@example.test"


def test_comments_open_only_when_assigned(svc, db):
    rid = make_request(svc)
    with pytest.raises(ValueError, match="assigned"):
        svc.add_comment(rid, REQ_A, "hello?")


@pytest.mark.parametrize("author", [REQ_B, STAFF_2])
def test_outsiders_cannot_comment(svc, db, author):
    rid = accepted_request(svc, db)
    with pytest.raises(LookupError):
        svc.add_comment(rid, author, "hi")
    assert row(db, "SELECT COUNT(*) FROM request_comments") == [(0,)]


def test_comment_validation(svc, db):
    rid = accepted_request(svc, db)
    for body in ("", "   ", None):
        with pytest.raises(ValueError):
            svc.add_comment(rid, REQ_A, body)
    with pytest.raises(ValueError, match="at most"):
        svc.add_comment(rid, REQ_A, "x" * 2001)


def test_comment_from_staff_notifies_the_requester_but_the_requesters_own_does_not(svc, db):
    rid = accepted_request(svc, db)
    before = row(db, "SELECT COUNT(*) FROM outbox_events")[0][0]
    svc.add_comment(rid, REQ_A, "my own comment")
    assert row(db, "SELECT COUNT(*) FROM outbox_events")[0][0] == before
    svc.add_comment(rid, STAFF_1, "We are on it")
    assert row(db, "SELECT event_type FROM outbox_events ORDER BY id DESC LIMIT 1") == [("CommentAdded",)]


def test_comments_are_not_status_or_assignment_audit_entries(svc, db):
    rid = accepted_request(svc, db)
    before = row(db, "SELECT COUNT(*) FROM request_audit WHERE request_id=?", (rid,))[0][0]
    svc.add_comment(rid, STAFF_1, "note")
    assert row(db, "SELECT COUNT(*) FROM request_audit WHERE request_id=?", (rid,))[0][0] == before


# ---------------------------------------------------------------- FR-009 notifications

@pytest.fixture
def mail_sink(monkeypatch):
    sent = []
    monkeypatch.setattr(OutboxProcessor, "_send_email",
                        staticmethod(lambda to, rid, text, cid, suffix="updated": sent.append((to, rid, text, suffix))))
    return sent


def test_every_fr009_trigger_creates_an_in_app_notification_and_an_email(svc, db, mail_sink):
    rid = make_request(svc)
    svc.assign_request(rid, MANAGER, STAFF_1, version(db, rid))                  # Accepted
    svc.add_comment(rid, STAFF_1, "Crew booked")                                 # comment
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "Patched")     # Resolved
    other = make_request(svc)
    svc.change_status(other, MANAGER, "Rejected", version(db, other), "Out of scope")  # Rejected
    assert OutboxProcessor(db).process_pending() == 4
    messages = [m for (m,) in row(db, "SELECT message FROM request_notifications ORDER BY id")]
    assert messages == [
        f"Request #{rid} has been accepted. Current status: Resolved.",
        f"A comment was added to request #{rid}: Crew booked",
        f"Request #{rid} has been resolved. Resolution note: Patched",
        f"Request #{other} has been rejected. Reason: Out of scope",
    ]
    assert [(to, suffix) for to, _r, _t, suffix in mail_sink] == [
        ("req-a@example.test", "accepted"), ("req-a@example.test", "has a new comment"),
        ("req-a@example.test", "resolved"), ("req-a@example.test", "rejected")]
    assert "Out of scope" in mail_sink[-1][2]


def test_notifications_reach_only_the_owning_requester(svc, db, mail_sink):
    rid = make_request(svc, REQ_B)
    svc.assign_request(rid, MANAGER, STAFF_1, version(db, rid))
    OutboxProcessor(db).process_pending()
    assert svc.list_notifications(REQ_A) == []
    assert len(svc.list_notifications(REQ_B)) == 1


# ---------------------------------------------------------------- migrations

def test_migrations_upgrade_an_m3_database_and_are_repeatable(tmp_path):
    path = str(tmp_path / "old.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.close()
    cols = lambda c, t: {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
    with sqlite3.connect(path) as c:
        assert "resolution_note" not in cols(c, "requests")
    ensure_schema(path)
    ensure_schema(path)  # idempotent
    with sqlite3.connect(path) as c:
        assert {"resolution_note", "resolution_by", "resolution_at", "rejection_reason"} <= cols(c, "requests")
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"request_comments", "admin_audit", "password_resets", "schema_migrations"} <= tables
        assert [r[0] for r in c.execute("SELECT version FROM schema_migrations ORDER BY version")] == [1, 2]


def test_migration_keeps_existing_requests_and_audit(tmp_path):
    path = str(tmp_path / "old.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("INSERT INTO users(email,password_hash,role) VALUES ('a@example.test','x','Requester')")
    conn.execute("INSERT INTO categories(name,target_resolution_hours) VALUES ('Roads',48)")
    conn.commit()
    conn.close()
    old = RequestService.__new__(RequestService)  # build the data without migrating first
    old.db_path = path
    from src.persistence.request_repository import RequestRepository
    old.repo = RequestRepository(path)
    rid = RequestService.create_request(old, 1, 1, "Old", "Made before the upgrade", "Here")
    ensure_schema(path)
    detail = RequestService(path).get_request_detail(1, rid)
    assert detail["title"] == "Old" and detail["resolution_note"] is None and detail["comments"] == []
    assert len(detail["history"]) == 1


def test_admin_audit_is_append_only(db):
    ensure_schema(db)
    with sqlite3.connect(db) as c:
        c.execute("INSERT INTO admin_audit(actor_user_id, action_type) VALUES (?, 'x')", (ADMIN,))
        for sql in ("UPDATE admin_audit SET action_type='y'", "DELETE FROM admin_audit",
                    "INSERT OR REPLACE INTO admin_audit(id, actor_user_id, action_type) VALUES (1, 1, 'z')"):
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                c.execute(sql)


# ---------------------------------------------------------------- routes

@pytest.fixture
def client_for(db):
    app = create_app(db, secret_key=APP_KEY)

    def make(user_id):
        client = app.test_client()
        with client.session_transaction() as s:
            s["user_id"] = user_id
            s["_csrf_token"] = "tok"
        return client
    return make


def post(client, path, **data):
    return client.post(path, data={"csrf_token": "tok", **data})


def test_detail_page_offers_the_right_actions_to_each_role(svc, db, client_for):
    rid = accepted_request(svc, db)
    staff = client_for(STAFF_1).get(f"/requests/{rid}").get_data(as_text=True)
    assert "Update status" in staff and "Reassign" not in staff and "Post comment" in staff
    manager = client_for(MANAGER).get(f"/requests/{rid}").get_data(as_text=True)
    assert "Reassign" in manager and "Update status" in manager
    requester = client_for(REQ_A).get(f"/requests/{rid}").get_data(as_text=True)
    assert "Update status" not in requester and "Reassign" not in requester and "Post comment" in requester
    assert "staff-1@example.test" not in requester
    unassigned = make_request(svc)
    assert "Comments open once a staff member is assigned" in client_for(REQ_A).get(
        f"/requests/{unassigned}").get_data(as_text=True)


def test_route_status_change_resolve_close_journey(svc, db, client_for):
    rid = accepted_request(svc, db)
    staff, manager = client_for(STAFF_1), client_for(MANAGER)
    r = post(staff, f"/requests/{rid}/status", target_status="Resolved", expected_version=version(db, rid), note="")
    assert r.status_code == 400 and "resolution note is required" in r.get_data(as_text=True)
    r = post(staff, f"/requests/{rid}/status", target_status="Resolved", expected_version=version(db, rid), note="Fixed")
    assert r.status_code == 302
    r = post(staff, f"/requests/{rid}/status", target_status="Closed", expected_version=version(db, rid))
    assert r.status_code == 403
    r = post(manager, f"/requests/{rid}/status", target_status="Closed", expected_version=version(db, rid))
    assert r.status_code == 302
    page = client_for(REQ_A).get(f"/requests/{rid}").get_data(as_text=True)
    assert "Fixed" in page and "Closed" in page


def test_route_authorization_and_csrf(svc, db, client_for):
    rid = accepted_request(svc, db)
    v = version(db, rid)
    assert post(client_for(REQ_A), f"/requests/{rid}/status", target_status="Resolved",
                expected_version=v, note="x").status_code == 403
    assert post(client_for(ADMIN), f"/requests/{rid}/status", target_status="Resolved",
                expected_version=v, note="x").status_code == 403
    assert post(client_for(STAFF_1), f"/requests/{rid}/assign", assignee_id=STAFF_2,
                expected_version=v).status_code == 403
    assert post(client_for(STAFF_2), f"/requests/{rid}/status", target_status="In Progress",
                expected_version=v).status_code == 404
    bad = client_for(STAFF_1).post(f"/requests/{rid}/status", data={"target_status": "In Progress",
                                                                    "expected_version": v})
    assert bad.status_code == 400
    assert row(db, "SELECT status FROM requests WHERE id=?", (rid,)) == [("Accepted",)]


def test_route_stale_page_gets_409_and_bad_version_400(svc, db, client_for):
    rid = accepted_request(svc, db)
    stale = version(db, rid)
    assert post(client_for(STAFF_1), f"/requests/{rid}/status", target_status="In Progress",
                expected_version=stale).status_code == 302
    assert post(client_for(STAFF_1), f"/requests/{rid}/status", target_status="On Hold",
                expected_version=stale).status_code == 409
    assert post(client_for(STAFF_1), f"/requests/{rid}/status", target_status="On Hold",
                expected_version="abc").status_code == 400


def test_route_assign_and_reassign(svc, db, client_for):
    rid = make_request(svc)
    manager = client_for(MANAGER)
    assert post(manager, f"/requests/{rid}/assign", assignee_id=STAFF_1,
                expected_version=version(db, rid)).status_code == 302
    assert post(manager, f"/requests/{rid}/assign", assignee_id=STAFF_2,
                expected_version=version(db, rid)).status_code == 302
    assert row(db, "SELECT status, assignee_id FROM requests WHERE id=?", (rid,)) == [("Accepted", STAFF_2)]
    assert post(manager, f"/requests/{rid}/assign", assignee_id=REQ_B,
                expected_version=version(db, rid)).status_code == 400


def test_route_comments(svc, db, client_for):
    rid = accepted_request(svc, db)
    assert post(client_for(STAFF_1), f"/requests/{rid}/comments", body="On it").status_code == 302
    assert post(client_for(REQ_A), f"/requests/{rid}/comments", body="Thanks").status_code == 302
    assert post(client_for(REQ_A), f"/requests/{rid}/comments", body="").status_code == 400
    assert post(client_for(REQ_B), f"/requests/{rid}/comments", body="spy").status_code == 404
    page = client_for(REQ_A).get(f"/requests/{rid}").get_data(as_text=True)
    assert "On it" in page and "Thanks" in page and "spy" not in page
