"""FR-001, FR-004, FR-023, FR-024: account provisioning, user and role administration, category
administration and password reset. Real schema.sql database, synthetic data only, bcrypt at the
minimum allowed cost so the suite stays quick."""

import json
import sqlite3
from pathlib import Path

import bcrypt
import pytest

from src.persistence.admin_service import AdminService
from src.persistence.migrations import ensure_schema
from src.persistence.outbox import OutboxProcessor
from src.persistence.password_reset import PasswordResetService
from src.persistence.request_service import RequestService
from src.web.app import create_app

SCHEMA = Path(__file__).resolve().parents[1] / "src" / "persistence" / "schema.sql"
REQ, STAFF, MANAGER, ADMIN = 1, 2, 3, 4
COST = 10
# Synthetic value used only by the reset-route test below; it is not a real credential.
ROUTE_PW = "Route-pass-123"  # gitleaks:allow
ROUTE_OTHER = "Different-pass-456"  # gitleaks:allow
APP_KEY = "test-signing-value"


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "admin.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    for email, role in [("req@example.test", "Requester"), ("staff@example.test", "Staff"),
                        ("manager@example.test", "Manager"), ("admin@example.test", "Administrator")]:
        conn.execute("INSERT INTO users(email,password_hash,role,is_active) VALUES (?,?,?,1)",
                     (email, "x", role))
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES ('Roads',48,1)")
    conn.commit()
    conn.close()
    ensure_schema(path)
    return path


@pytest.fixture
def admin(db):
    return AdminService(db, COST)


@pytest.fixture
def resets(db):
    return PasswordResetService(db, COST)


def q(db, sql, args=()):
    with sqlite3.connect(db) as conn:
        return conn.execute(sql, args).fetchall()


def audit(db):
    return q(db, "SELECT actor_user_id, action_type, target_user_id, previous_value, new_value "
                 "FROM admin_audit ORDER BY id")


# ---------------------------------------------------------------- FR-001 provisioning

def test_admin_creates_an_active_account_with_exactly_that_role_and_audit(admin, db):
    user_id, token = admin.provision_user(ADMIN, "  New.Staff@Example.Test ", "Staff")
    assert q(db, "SELECT email, role, is_active FROM users WHERE id=?", (user_id,)) == [
        ("new.staff@example.test", "Staff", 1)]
    assert audit(db) == [(ADMIN, "create_user", user_id, None, "Staff")]
    assert token


@pytest.mark.parametrize("role", ["Requester", "Staff", "Manager", "Administrator"])
def test_every_role_can_be_provisioned(admin, role):
    assert admin.provision_user(ADMIN, f"new-{role.lower()}@example.test", role)[0]


@pytest.mark.parametrize("email,role,message", [
    ("not-an-email", "Staff", "valid email"),
    ("", "Staff", "valid email"),
    ("x@example.test", "Superuser", "four roles"),
    ("x@example.test", "", "four roles"),
    ("req@example.test", "Staff", "already exists"),
    ("REQ@EXAMPLE.TEST", "Staff", "already exists"),
])
def test_invalid_provisioning_is_refused_without_changes(admin, db, email, role, message):
    users = q(db, "SELECT COUNT(*) FROM users")
    with pytest.raises(ValueError, match=message):
        admin.provision_user(ADMIN, email, role)
    assert q(db, "SELECT COUNT(*) FROM users") == users and audit(db) == []


@pytest.mark.parametrize("actor", [REQ, STAFF, MANAGER, 999])
def test_only_an_administrator_may_administer(admin, db, actor):
    for call in (lambda: admin.provision_user(actor, "a@example.test", "Staff"),
                 lambda: admin.list_users(actor), lambda: admin.change_role(actor, REQ, "Staff"),
                 lambda: admin.set_active(actor, REQ, False), lambda: admin.create_category(actor, "X", 5),
                 lambda: admin.list_categories(actor), lambda: admin.list_admin_audit(actor)):
        with pytest.raises(PermissionError):
            call()
    assert audit(db) == []


def test_a_deactivated_administrator_has_no_admin_rights(admin, db):
    admin.provision_user(ADMIN, "second@example.test", "Administrator")
    new_admin = q(db, "SELECT id FROM users WHERE email='second@example.test'")[0][0]
    admin.set_active(new_admin, ADMIN, False)
    with pytest.raises(PermissionError):
        admin.list_users(ADMIN)


def test_provisioned_person_sets_their_own_password_and_can_sign_in(admin, resets, db):
    _id, token = admin.provision_user(ADMIN, "fresh@example.test", "Staff")
    stored = q(db, "SELECT password_hash FROM users WHERE email='fresh@example.test'")[0][0]
    assert stored.startswith("$2")  # an unusable random bcrypt hash, never a known password
    app = create_app(db, secret_key="k")
    client = app.test_client()
    with client.session_transaction() as s:
        s["_csrf_token"] = "t"
    assert client.post("/login", data={"csrf_token": "t", "email": "fresh@example.test",
                                       "password": "anything-guess"}).status_code == 200
    resets.set_password(token, "My-own-password-1")
    assert client.post("/login", data={"csrf_token": "t", "email": "fresh@example.test",
                                       "password": "My-own-password-1"}).status_code == 302


# ---------------------------------------------------------------- FR-024 users and roles

def test_role_change_is_applied_and_audited(admin, db):
    admin.change_role(ADMIN, STAFF, "Manager")
    assert q(db, "SELECT role FROM users WHERE id=?", (STAFF,)) == [("Manager",)]
    assert audit(db) == [(ADMIN, "change_role", STAFF, "Staff", "Manager")]


def test_role_change_validation(admin, db):
    with pytest.raises(ValueError, match="four roles"):
        admin.change_role(ADMIN, STAFF, "Root")
    with pytest.raises(ValueError, match="already has"):
        admin.change_role(ADMIN, STAFF, "Staff")
    with pytest.raises(LookupError):
        admin.change_role(ADMIN, 999, "Staff")
    assert audit(db) == []


def test_the_last_active_administrator_cannot_be_demoted_or_deactivated(admin, db):
    with pytest.raises(ValueError, match="At least one"):
        admin.change_role(ADMIN, ADMIN, "Manager")
    with pytest.raises(ValueError):
        admin.set_active(ADMIN, ADMIN, False)
    other, _ = admin.provision_user(ADMIN, "other-admin@example.test", "Administrator")
    admin.change_role(other, ADMIN, "Manager")  # allowed now: another active Administrator remains
    assert q(db, "SELECT role FROM users WHERE id=?", (ADMIN,)) == [("Manager",)]


def test_an_administrator_cannot_deactivate_themselves(admin, db):
    other, _ = admin.provision_user(ADMIN, "other-admin@example.test", "Administrator")
    with pytest.raises(ValueError, match="own account"):
        admin.set_active(ADMIN, ADMIN, False)
    assert q(db, "SELECT is_active FROM users WHERE id=?", (ADMIN,)) == [(1,)]
    admin.set_active(ADMIN, other, False)
    assert q(db, "SELECT is_active FROM users WHERE id=?", (other,)) == [(0,)]


def test_deactivation_blocks_sign_in_and_existing_sessions_and_is_audited(admin, resets, db):
    _id, token = admin.provision_user(ADMIN, "leaver@example.test", "Staff")
    resets.set_password(token, "Leaver-pass-123")
    uid = q(db, "SELECT id FROM users WHERE email='leaver@example.test'")[0][0]
    app = create_app(db, secret_key="k")
    client = app.test_client()
    with client.session_transaction() as s:
        s["_csrf_token"] = "t"
        s["user_id"] = uid
    assert client.get("/staff/queue").status_code == 200
    admin.set_active(ADMIN, uid, False)
    assert client.get("/staff/queue").status_code == 302  # session no longer works
    fresh = app.test_client()
    with fresh.session_transaction() as s:
        s["_csrf_token"] = "t"
    page = fresh.post("/login", data={"csrf_token": "t", "email": "leaver@example.test",
                                      "password": "Leaver-pass-123"})
    assert page.status_code == 200 and b"Invalid email or password" in page.data
    assert (ADMIN, "deactivate_user", uid, "active", "inactive") in audit(db)
    admin.set_active(ADMIN, uid, True)
    assert (ADMIN, "reactivate_user", uid, "inactive", "active") in audit(db)
    with pytest.raises(ValueError, match="already active"):
        admin.set_active(ADMIN, uid, True)


def test_deactivated_staff_requests_stay_visible_to_the_manager_for_reassignment(admin, db):
    svc = RequestService(db)
    rid = svc.create_request(REQ, 1, "Pothole", "Deep", "Main Rd")
    svc.assign_request(rid, MANAGER, STAFF, 0)
    assert {u["id"]: u["open_assigned"] for u in admin.list_users(ADMIN)}[STAFF] == 1
    admin.set_active(ADMIN, STAFF, False)
    detail = svc.get_request_detail(MANAGER, rid)
    assert detail["assignee_id"] == STAFF and detail["status"] == "Accepted"
    second, _ = admin.provision_user(ADMIN, "staff2@example.test", "Staff")
    svc.assign_request(rid, MANAGER, second, q(db, "SELECT version FROM requests")[0][0])
    assert q(db, "SELECT assignee_id FROM requests WHERE id=?", (rid,)) == [(second,)]


# ---------------------------------------------------------------- FR-023 categories

def test_category_create_rename_target_and_audit(admin, db):
    cid = admin.create_category(ADMIN, "  Street   Lighting ", "24")
    assert q(db, "SELECT name, target_resolution_hours, is_active FROM categories WHERE id=?", (cid,)) == [
        ("Street Lighting", 24, 1)]
    admin.update_category(ADMIN, cid, name="Lighting")
    admin.update_category(ADMIN, cid, target_hours=72)
    assert q(db, "SELECT name, target_resolution_hours FROM categories WHERE id=?", (cid,)) == [("Lighting", 72)]
    actions = [a[1] for a in audit(db)]
    assert actions == ["create_category", "update_category", "update_category"]


@pytest.mark.parametrize("name,hours,message", [
    ("", 10, "name is required"), ("   ", 10, "name is required"), ("x" * 81, 10, "at most 80"),
    ("Roads", 10, "already exists"), ("roads", 10, "already exists"),
    ("Parks", 0, "between 1"), ("Parks", 8761, "between 1"), ("Parks", "abc", "whole number"),
    ("Parks", "", "whole number"), ("Parks", -5, "between 1"),
])
def test_category_validation(admin, db, name, hours, message):
    count = q(db, "SELECT COUNT(*) FROM categories")
    with pytest.raises(ValueError, match=message):
        admin.create_category(ADMIN, name, hours)
    assert q(db, "SELECT COUNT(*) FROM categories") == count


def test_rename_to_an_existing_name_or_no_change_is_refused(admin, db):
    cid = admin.create_category(ADMIN, "Parks", 10)
    with pytest.raises(ValueError, match="already exists"):
        admin.update_category(ADMIN, cid, name="ROADS")
    with pytest.raises(ValueError, match="Nothing was changed"):
        admin.update_category(ADMIN, cid, name="Parks", target_hours=10)
    with pytest.raises(LookupError):
        admin.update_category(ADMIN, 999, name="Z")


def test_deactivated_category_is_withdrawn_from_submission_but_existing_requests_keep_it(admin, db):
    svc = RequestService(db)
    rid = svc.create_request(REQ, 1, "Pothole", "Deep", "Main Rd")
    admin.set_category_active(ADMIN, 1, False)
    with pytest.raises(ValueError, match="active controlled list"):
        svc.create_request(REQ, 1, "Another", "Deep", "Main Rd")
    detail = svc.get_request_detail(REQ, rid)
    assert detail["category"] == "Roads"
    app = create_app(db, secret_key="k")
    client = app.test_client()
    with client.session_transaction() as s:
        s["user_id"] = REQ
    assert b">Roads<" not in client.get("/requests/new").data
    admin.set_category_active(ADMIN, 1, True)
    assert b">Roads<" in client.get("/requests/new").data


def test_a_category_in_use_cannot_be_deleted_but_an_unused_one_can(admin, db):
    svc = RequestService(db)
    svc.create_request(REQ, 1, "Pothole", "Deep", "Main Rd")
    with pytest.raises(ValueError, match="cannot be deleted"):
        admin.delete_category(ADMIN, 1)
    assert q(db, "SELECT COUNT(*) FROM categories WHERE id=1") == [(1,)]
    cid = admin.create_category(ADMIN, "Parks", 10)
    admin.delete_category(ADMIN, cid)
    assert q(db, "SELECT COUNT(*) FROM categories WHERE id=?", (cid,)) == [(0,)]
    with pytest.raises(LookupError):
        admin.delete_category(ADMIN, cid)


# ---------------------------------------------------------------- FR-004 password reset

def test_reset_request_for_an_active_account_queues_one_email_and_stores_only_a_hash(resets, db):
    assert resets.request_reset(" REQ@example.test ") is True
    token = json.loads(q(db, "SELECT payload_json FROM outbox_events")[0][0])["token"]
    assert q(db, "SELECT event_type, state FROM outbox_events") == [("PasswordResetRequested", "pending")]
    assert token not in json.dumps(q(db, "SELECT * FROM password_resets"))  # only the hash is stored
    assert resets.is_valid(token)


@pytest.mark.parametrize("email", ["nobody@example.test", "", "   "])
def test_unknown_or_blank_email_queues_nothing(resets, db, email):
    assert resets.request_reset(email) is False
    assert q(db, "SELECT COUNT(*) FROM outbox_events") == [(0,)]


def test_inactive_account_gets_no_reset(resets, admin, db):
    admin.set_active(ADMIN, STAFF, False)
    assert resets.request_reset("staff@example.test") is False


def test_a_link_works_once_and_sets_a_bcrypt_password(resets, db):
    resets.request_reset("req@example.test")
    token = json.loads(q(db, "SELECT payload_json FROM outbox_events")[0][0])["token"]
    resets.set_password(token, "Brand-new-pass-1")
    stored = q(db, "SELECT password_hash FROM users WHERE id=?", (REQ,))[0][0]
    assert bcrypt.checkpw(b"Brand-new-pass-1", stored.encode())
    with pytest.raises(ValueError, match="invalid or has expired"):
        resets.set_password(token, "Another-pass-22")  # reuse refused
    assert not resets.is_valid(token)


def test_an_expired_link_is_refused(resets, db):
    resets.request_reset("req@example.test")
    token = json.loads(q(db, "SELECT payload_json FROM outbox_events")[0][0])["token"]
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE password_resets SET expires_at = '2000-01-01 00:00:00'")
    assert not resets.is_valid(token)
    with pytest.raises(ValueError, match="invalid or has expired"):
        resets.set_password(token, "Brand-new-pass-1")
    assert q(db, "SELECT password_hash FROM users WHERE id=?", (REQ,)) == [("x",)]


@pytest.mark.parametrize("token", ["", "not-a-token", "A" * 43])
def test_a_wrong_token_is_refused(resets, token):
    assert not resets.is_valid(token)
    with pytest.raises(ValueError, match="invalid or has expired"):
        resets.set_password(token, "Brand-new-pass-1")


def test_requesting_again_cancels_the_earlier_link(resets, db):
    resets.request_reset("req@example.test")
    resets.request_reset("req@example.test")
    first, second = [json.loads(r[0])["token"] for r in q(db, "SELECT payload_json FROM outbox_events ORDER BY id")]
    assert not resets.is_valid(first) and resets.is_valid(second)


@pytest.mark.parametrize("password", ["short", "        ", "x" * 73])
def test_a_weak_or_oversize_password_is_refused_and_the_link_stays_usable(resets, db, password):
    resets.request_reset("req@example.test")
    token = json.loads(q(db, "SELECT payload_json FROM outbox_events")[0][0])["token"]
    with pytest.raises(ValueError):
        resets.set_password(token, password)
    assert resets.is_valid(token)


def test_reset_email_is_sent_with_the_link_and_the_token_is_then_scrubbed(resets, db, monkeypatch):
    sent = []
    monkeypatch.setattr(OutboxProcessor, "_send_plain_email",
                        classmethod(lambda cls, to, subject, text, cid: sent.append((to, subject, text))))
    monkeypatch.setenv("APP_BASE_URL", "https://civic.example.test/")
    resets.request_reset("req@example.test")
    token = json.loads(q(db, "SELECT payload_json FROM outbox_events")[0][0])["token"]
    assert OutboxProcessor(db).process_pending() == 1
    to, subject, text = sent[0]
    assert to == "req@example.test" and "Set your CivicConnect password" in subject
    assert f"https://civic.example.test/reset-password/{token}" in text and "60 minutes" in text
    assert q(db, "SELECT payload_json, state FROM outbox_events") == [("{}", "sent")]


def test_a_failed_send_keeps_the_event_for_retry(resets, db, monkeypatch):
    monkeypatch.delenv("EMAIL_SMTP_HOST", raising=False)
    resets.request_reset("req@example.test")
    assert OutboxProcessor(db).process_pending() == 0
    state, payload = q(db, "SELECT state, payload_json FROM outbox_events")[0]
    assert state == "pending" and "token" in payload


# ---------------------------------------------------------------- routes

@pytest.fixture
def client_for(db):
    app = create_app(db, secret_key=APP_KEY)

    def make(user_id=None):
        client = app.test_client()
        with client.session_transaction() as s:
            s["_csrf_token"] = "tok"
            if user_id:
                s["user_id"] = user_id
        return client
    return make


def post(client, path, **data):
    return client.post(path, data={"csrf_token": "tok", **data})


@pytest.mark.parametrize("path", ["/admin/users", "/admin/categories"])
@pytest.mark.parametrize("user", [REQ, STAFF, MANAGER])
def test_admin_pages_are_forbidden_to_other_roles_and_need_sign_in(client_for, path, user):
    assert client_for(user).get(path).status_code == 403
    assert client_for().get(path).status_code == 302


def test_admin_posts_are_forbidden_to_other_roles_and_need_csrf(client_for, db):
    for user in (REQ, STAFF, MANAGER):
        c = client_for(user)
        assert post(c, "/admin/users", email="a@example.test", role="Staff").status_code == 403
        assert post(c, f"/admin/users/{REQ}/role", role="Staff").status_code == 403
        assert post(c, f"/admin/users/{REQ}/active", active="0").status_code == 403
        assert post(c, "/admin/categories", name="Z", target_hours="5").status_code == 403
        assert post(c, "/admin/categories/1/delete").status_code == 403
    assert client_for(ADMIN).post("/admin/users", data={"email": "a@example.test", "role": "Staff"}).status_code == 400
    assert q(db, "SELECT COUNT(*) FROM users") == [(4,)]


def test_admin_users_journey_through_the_routes(client_for, db):
    c = client_for(ADMIN)
    page = post(c, "/admin/users", email="newhire@example.test", role="Staff")
    html = page.get_data(as_text=True)
    assert page.status_code == 200 and "/reset-password/" in html and "newhire@example.test" in html
    assert post(c, "/admin/users", email="newhire@example.test", role="Staff").status_code == 400
    uid = q(db, "SELECT id FROM users WHERE email='newhire@example.test'")[0][0]
    assert post(c, f"/admin/users/{uid}/role", role="Manager").status_code == 302
    assert post(c, f"/admin/users/{uid}/role", role="Manager").status_code == 400
    assert post(c, f"/admin/users/{uid}/active", active="0").status_code == 302
    assert post(c, "/admin/users/999/active", active="0").status_code == 404
    listing = c.get("/admin/users").get_data(as_text=True)
    assert "Inactive" in listing and "change_role" in listing and "create_user" in listing


def test_admin_categories_journey_through_the_routes(client_for, db):
    c = client_for(ADMIN)
    assert post(c, "/admin/categories", name="Parks", target_hours="36").status_code == 302
    assert post(c, "/admin/categories", name="Parks", target_hours="36").status_code == 400
    assert post(c, "/admin/categories", name="Trees", target_hours="0").status_code == 400
    cid = q(db, "SELECT id FROM categories WHERE name='Parks'")[0][0]
    assert post(c, f"/admin/categories/{cid}/update", name="Green spaces", target_hours="40").status_code == 302
    assert post(c, f"/admin/categories/{cid}/active", active="0").status_code == 302
    assert post(c, f"/admin/categories/{cid}/delete").status_code == 302
    assert post(c, "/admin/categories/1/delete").status_code == 302  # unused so far
    assert q(db, "SELECT COUNT(*) FROM categories") == [(0,)]
    assert post(c, "/admin/categories/999/delete").status_code == 404


def test_forgot_and_reset_routes(client_for, db):
    anon = client_for()
    known = post(anon, "/forgot-password", email="req@example.test").get_data(as_text=True)
    unknown = post(anon, "/forgot-password", email="ghost@example.test").get_data(as_text=True)
    assert "we have sent a link" in known and "we have sent a link" in unknown  # same answer
    token = json.loads(q(db, "SELECT payload_json FROM outbox_events")[0][0])["token"]
    assert anon.get(f"/reset-password/{token}").status_code == 200
    bad = anon.get("/reset-password/not-a-token")
    assert bad.status_code == 400 and b"Request a new link" in bad.data
    assert post(anon, f"/reset-password/{token}", password=ROUTE_PW,
                confirm_password=ROUTE_OTHER).status_code == 400
    assert post(anon, f"/reset-password/{token}", password="short", confirm_password="short").status_code == 400
    ok = post(anon, f"/reset-password/{token}", password=ROUTE_PW, confirm_password=ROUTE_PW)
    assert ok.status_code == 302 and ok.headers["Location"].endswith("/login")
    assert post(anon, f"/reset-password/{token}", password=ROUTE_PW,
                confirm_password=ROUTE_PW).status_code == 400  # single use
    with anon.session_transaction() as s:  # a successful reset clears the session, as it should
        s["_csrf_token"] = "tok"
    signed_in = post(anon, "/login", email="req@example.test", password=ROUTE_PW)
    assert signed_in.status_code == 302
    assert anon.post("/forgot-password", data={"email": "req@example.test"}).status_code == 400  # CSRF
