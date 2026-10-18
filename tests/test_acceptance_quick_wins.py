"""Acceptance regressions for FR-006, FR-022, FR-026 and NFR-014."""

import csv
import io
import os
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from src.persistence.request_service import RequestService, SubmissionValidationError
from src.web.app import create_app

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "persistence", "schema.sql")
TEST_SECRET = "acceptance-quick-wins-test-secret"


def setup_db(db_path):
    conn = sqlite3.connect(db_path)
    try:
        with open(SCHEMA_PATH, encoding="utf-8") as schema:
            conn.executescript(schema.read())
        for email, password, role in (
            ("requester@example.com", "requester-pw", "Requester"),
            ("other@example.com", "other-pw", "Requester"),
            ("staff@example.com", "staff-pw", "Staff"),
            ("manager@example.com", "manager-pw", "Manager"),
            ("admin@example.com", "admin-pw", "Administrator"),
        ):
            conn.execute(
                "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                (email, generate_password_hash(password), role),
            )
        conn.execute(
            "INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Roads', 48, 1)"
        )
        conn.execute(
            "INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Water', 24, 1)"
        )
        conn.commit()
    finally:
        conn.close()


def user_id(db_path, email):
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]


def login(client, email, password):
    assert client.get("/login").status_code == 200
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
    response = client.post(
        "/login", data={"email": email, "password": password, "csrf_token": csrf}
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        return session["_csrf_token"]


def request_count(db_path):
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]


@pytest.mark.parametrize(
    ("field", "invalid_value", "message"),
    (
        ("title", "", "title is required."),
        ("description", "", "description is required."),
        ("category_id", "free text", "Select a category from the active controlled list."),
        ("location", "", "location is required."),
    ),
)
def test_submission_rejection_is_field_associated_and_retains_other_values(
    tmp_path, field, invalid_value, message
):
    db_path = str(tmp_path / "field-validation.sqlite")
    setup_db(db_path)
    client = create_app(db_path, secret_key=TEST_SECRET).test_client()
    csrf = login(client, "requester@example.com", "requester-pw")
    values = {
        "title": "Retained title",
        "description": "Retained description",
        "category_id": "1",
        "location": "Retained location",
        "csrf_token": csrf,
    }
    values[field] = invalid_value

    response = client.post("/requests", data=values)

    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert message in html
    assert f'id="{field}-error"' in html
    assert f'aria-describedby="{field}-error"' in html
    retained_fields = {
        "title": "Retained title", "description": "Retained description",
        "location": "Retained location",
    }
    for retained_field, retained in retained_fields.items():
        if retained_field != field:
            assert retained in html
    if field != "category_id":
        assert 'value="1" selected' in html
    assert request_count(db_path) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (("title", 123), ("description", object()), ("location", ["not", "text"])),
)
def test_service_rejects_non_text_submission_values(tmp_path, field, value):
    db_path = str(tmp_path / "type-validation.sqlite")
    setup_db(db_path)
    values = {"title": "Title", "description": "Description", "location": "Location"}
    values[field] = value

    with pytest.raises(SubmissionValidationError) as caught:
        RequestService(db_path).create_request(
            user_id(db_path, "requester@example.com"), 1,
            values["title"], values["description"], values["location"],
        )

    assert caught.value.field == field
    assert request_count(db_path) == 0


@pytest.mark.parametrize(
    ("field", "limit"), (("title", 200), ("description", 5000), ("location", 300))
)
def test_service_enforces_documented_text_boundaries(tmp_path, field, limit):
    db_path = str(tmp_path / "boundary-validation.sqlite")
    setup_db(db_path)
    service = RequestService(db_path)
    requester = user_id(db_path, "requester@example.com")
    values = {"title": "T", "description": "D", "location": "L"}
    values[field] = "x" * (limit + 1)

    with pytest.raises(SubmissionValidationError) as caught:
        service.create_request(
            requester, 1, values["title"], values["description"], values["location"]
        )

    assert caught.value.field == field
    assert str(limit) in str(caught.value)
    assert request_count(db_path) == 0


def test_duplicate_warning_lists_reference_then_allows_confirmation(tmp_path):
    db_path = str(tmp_path / "duplicate.sqlite")
    setup_db(db_path)
    service = RequestService(db_path)
    existing = service.create_request(
        user_id(db_path, "other@example.com"), 1, "Existing road fault", "Existing detail", "Main Street"
    )
    client = create_app(db_path, secret_key=TEST_SECRET).test_client()
    csrf = login(client, "requester@example.com", "requester-pw")
    submission = {
        "title": "Another road fault", "description": "New detail", "category_id": "1",
        "location": " main street ", "csrf_token": csrf,
    }

    warning = client.post("/requests", data=submission)

    assert warning.status_code == 409
    html = warning.get_data(as_text=True)
    assert "Possible duplicate request" in html
    assert f"Request #{existing}" in html
    assert "Confirm submission" in html
    assert "Cancel and view my requests" in html
    assert html.index("Confirm submission") < html.index('for="title"')
    assert "other@example.com" not in html
    assert request_count(db_path) == 1

    submission["confirm_duplicate"] = "yes"
    confirmed = client.post("/requests", data=submission)
    assert confirmed.status_code == 302
    assert "/submitted" in confirmed.headers["Location"]
    assert request_count(db_path) == 2


def test_nonduplicate_submission_does_not_show_warning(tmp_path):
    db_path = str(tmp_path / "nonduplicate.sqlite")
    setup_db(db_path)
    service = RequestService(db_path)
    service.create_request(
        user_id(db_path, "other@example.com"), 1, "Road fault", "Detail", "First Avenue"
    )
    client = create_app(db_path, secret_key=TEST_SECRET).test_client()
    csrf = login(client, "requester@example.com", "requester-pw")

    response = client.post("/requests", data={
        "title": "Water fault", "description": "Detail", "category_id": "2",
        "location": "First Avenue", "csrf_token": csrf,
    })

    assert response.status_code == 302
    assert request_count(db_path) == 2


def test_manager_filtered_csv_matches_displayed_row_values(tmp_path):
    db_path = str(tmp_path / "manager-export.sqlite")
    setup_db(db_path)
    service = RequestService(db_path)
    requester = user_id(db_path, "requester@example.com")
    roads_id = service.create_request(requester, 1, "Road row", "Road detail", "Road location")
    service.create_request(requester, 2, "Water row", "Water detail", "Water location")
    client = create_app(db_path, secret_key=TEST_SECRET).test_client()
    login(client, "manager@example.com", "manager-pw")

    displayed = client.get("/manager/requests?status=New&category_id=1")
    exported = client.get("/manager/requests?status=New&category_id=1&format=csv")

    assert displayed.status_code == 200
    html = displayed.get_data(as_text=True)
    expected_values = [f"#{roads_id}", "Road row", "Roads", "New", "Unassigned"]
    assert "<strong>1</strong> matching request" in html
    assert "Water row" not in html
    for value in expected_values:
        assert value in html

    assert exported.status_code == 200
    assert exported.mimetype == "text/csv"
    assert "attachment; filename=civicconnect-requests.csv" == exported.headers["Content-Disposition"]
    rows = list(csv.DictReader(io.StringIO(exported.get_data(as_text=True))))
    assert len(rows) == 1
    assert list(rows[0]) == ["Reference", "Title", "Category", "Submitted", "Status", "Assignee"]
    assert [rows[0][key] for key in ("Reference", "Title", "Category", "Status", "Assignee")] == expected_values


@pytest.mark.parametrize(
    ("email", "password"),
    (
        ("requester@example.com", "requester-pw"),
        ("staff@example.com", "staff-pw"),
        ("admin@example.com", "admin-pw"),
    ),
)
def test_manager_export_route_rejects_other_roles(tmp_path, email, password):
    db_path = str(tmp_path / "manager-role.sqlite")
    setup_db(db_path)
    client = create_app(db_path, secret_key=TEST_SECRET).test_client()
    login(client, email, password)
    assert client.get("/manager/requests").status_code == 403


@pytest.mark.parametrize(
    "query", ("status=Unknown", "category_id=free-text", "format=json")
)
def test_manager_export_rejects_invalid_filters_and_format(tmp_path, query):
    db_path = str(tmp_path / "manager-invalid.sqlite")
    setup_db(db_path)
    client = create_app(db_path, secret_key=TEST_SECRET).test_client()
    login(client, "manager@example.com", "manager-pw")
    assert client.get(f"/manager/requests?{query}").status_code == 400
