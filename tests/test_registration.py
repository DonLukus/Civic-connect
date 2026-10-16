"""Registration validation, credential storage and privilege boundaries."""

import re
import sqlite3
from pathlib import Path

import bcrypt
import pytest

from src.persistence.user_service import DuplicateEmailError, UserService
from src.web.app import create_app


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("PASSWORD_HASH_COST", "10")
    path = str(tmp_path / "registration.sqlite")
    with sqlite3.connect(path) as db:
        db.executescript(Path("src/persistence/schema.sql").read_text(encoding="utf-8"))
    return path


def form_token(client, path="/register"):
    page = client.get(path)
    assert page.status_code == 200
    return re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)


def test_register_stores_bcrypt_and_forces_requester_then_login(database):
    client = create_app(database, secret_key="x").test_client()
    password = "p" * 12
    response = client.post("/register", data={"csrf_token": form_token(client),
        "email": "  NEW@EXAMPLE.TEST ", "password": password, "confirm_password": password,
        "role": "Administrator", "is_active": "0"})
    assert response.status_code == 302 and response.location.endswith("/login")
    with sqlite3.connect(database) as db:
        email, digest, role, active = db.execute(
            "SELECT email,password_hash,role,is_active FROM users").fetchone()
    assert (email, role, active) == ("new@example.test", "Requester", 1)
    assert digest.startswith("$2b$10$") and bcrypt.checkpw(password.encode(), digest.encode())
    page = client.get("/login").get_data(as_text=True)
    assert "Your account is ready" in page
    login = client.post("/login", data={"csrf_token": form_token(client, "/login"),
                         "email": email, "password": password}, follow_redirects=True)
    assert login.status_code == 200 and "Submit a service request" in login.get_data(as_text=True)


@pytest.mark.parametrize(("email", "password"), [
    ("invalid", "p" * 12), ("a@b.test", "short"),
    ("a@b.test", " " * 12), ("a@b.test", "p" * 73),
    ("a@b.test", "\u00e9" * 37), ("x" * 255 + "@example.test", "p" * 12),
])
def test_service_rejects_invalid_registration_without_writing(database, email, password):
    with pytest.raises(ValueError):
        UserService(database, 10).register_requester(email, password)
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 0


def test_service_rejects_case_insensitive_duplicate(database):
    service = UserService(database, 10)
    service.register_requester("existing@example.test", "p" * 12)
    with pytest.raises(DuplicateEmailError):
        service.register_requester("EXISTING@example.test", "p" * 12)
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1


@pytest.mark.parametrize("supplied", [None, "wrong"])
def test_registration_rejects_missing_or_wrong_csrf(database, supplied):
    client = create_app(database, secret_key="x").test_client()
    form_token(client)
    data = {"email": "new@example.test", "password": "p" * 12, "confirm_password": "p" * 12}
    if supplied is not None:
        data["csrf_token"] = supplied
    assert client.post("/register", data=data).status_code == 400
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 0


def test_mismatched_confirmation_and_duplicate_response(database):
    client = create_app(database, secret_key="x").test_client()
    data = {"csrf_token": form_token(client), "email": "new@example.test",
            "password": "p" * 12, "confirm_password": "q" * 12}
    response = client.post("/register", data=data)
    assert response.status_code == 400 and "Passwords do not match" in response.get_data(as_text=True)
    data["confirm_password"] = data["password"]
    assert client.post("/register", data=data).status_code == 302
    data["csrf_token"] = form_token(client)
    response = client.post("/register", data=data)
    assert response.status_code == 409
    assert data["password"] not in response.get_data(as_text=True)
