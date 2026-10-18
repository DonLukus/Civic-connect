"""Finalisation regressions for existing privacy/session boundaries; synthetic data only."""

import json
import sqlite3
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from src.persistence.request_service import RequestService
from src.web.app import create_app


@pytest.fixture
def existing_slice(tmp_path):
    path = tmp_path / "final-regression.sqlite"
    with sqlite3.connect(path) as db:
        schema = Path(__file__).resolve().parents[1] / "src/persistence/schema.sql"
        db.executescript(schema.read_text(encoding="utf-8"))
        # Deliberately cheap synthetic legacy fixture; not an application hash policy.
        digest = generate_password_hash("qa", method="pbkdf2:sha256:1")
        for email, role in [("requester@example.test", "Requester"),
                            ("staff@example.test", "Staff"),
                            ("manager@example.test", "Manager")]:
            db.execute("INSERT INTO users(email,password_hash,role,is_active) VALUES(?,?,?,1)",
                       (email, digest, role))
        db.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES('Roads',48,1)")
    service = RequestService(str(path))
    item = service.create_request(1, 1, "Synthetic report", "Synthetic description", "QA location")
    return str(path), service, item


def test_unassigned_staff_history_does_not_disclose_requester_contact(existing_slice):
    """TST-051 / NFR-012: inspect nested service data, not only the rendered template."""
    _path, service, item = existing_slice
    detail = service.get_request_detail(2, item)
    assert "requester@example.test" not in json.dumps(detail)
    assert detail["history"][0]["actor_user_id"] == 1
    # Authorised oversight still receives the separately controlled contact field.
    assert service.get_request_detail(3, item)["requester_email"] == "requester@example.test"


def test_deactivation_invalidates_existing_session_and_direct_service_access(existing_slice):
    """TST-052 / NFR-004/012: an authenticated session is not permanent authorisation."""
    path, service, item = existing_slice
    app = create_app(path, secret_key="x")
    with app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = 1
        assert client.get(f"/requests/{item}").status_code == 200
        with sqlite3.connect(path) as db:
            db.execute("UPDATE users SET is_active=0 WHERE id=1")
        response = client.get(f"/requests/{item}")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")
        assert b"Synthetic description" not in response.data
    with pytest.raises(PermissionError):
        service.get_request_detail(1, item)
