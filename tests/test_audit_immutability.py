"""FR-025 / NFR-006: the audit trail cannot be edited or deleted through the database connection."""

import importlib
import sqlite3

import pytest

from src.persistence.request_service import RequestService
from tests.test_request_submission import setup_db


def _create_one_request(db_path):
    RequestService(db_path).create_request(
        requester_id=1, category_id=1, title="Broken pipe",
        description="Leak in building", location="Block 4",
    )


def _connect(db_path):
    return sqlite3.connect(db_path)


def test_audit_rows_can_be_added(tmp_path):
    db_path = str(tmp_path / "a.sqlite")
    setup_db(db_path)
    _create_one_request(db_path)
    conn = _connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM request_audit").fetchone()[0] == 1
    finally:
        conn.close()


@pytest.mark.parametrize("statement", [
    "UPDATE request_audit SET new_status = 'Closed'",
    "UPDATE request_audit SET actor_user_id = 999",
    "DELETE FROM request_audit",
])
def test_audit_rows_cannot_be_changed_or_deleted(tmp_path, statement):
    db_path = str(tmp_path / "a.sqlite")
    setup_db(db_path)
    _create_one_request(db_path)
    conn = _connect(db_path)
    try:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute(statement)
        row = conn.execute("SELECT new_status, actor_user_id FROM request_audit").fetchone()
        assert row == ("New", 1), "the audit row must be unchanged after the refused statement"
    finally:
        conn.close()


def test_existing_database_gains_protection_on_startup(tmp_path, monkeypatch):
    """A database created before the triggers existed is protected after the next bootstrap."""
    db_path = str(tmp_path / "old.sqlite")
    monkeypatch.setenv("DATABASE_URL", db_path)
    monkeypatch.setenv("SECRET_KEY", "x")
    import wsgi
    importlib.reload(wsgi)

    conn = _connect(db_path)
    try:
        conn.executescript(
            "DROP TRIGGER request_audit_no_update; DROP TRIGGER request_audit_no_delete;"
        )
    finally:
        conn.close()

    wsgi.bootstrap(db_path)

    conn = _connect(db_path)
    try:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        assert {"request_audit_no_update", "request_audit_no_delete"} <= names
    finally:
        conn.close()
