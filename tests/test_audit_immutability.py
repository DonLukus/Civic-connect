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


_COLUMNS = "(id, request_id, actor_user_id, action_type, new_status, correlation_id)"
_VALUES = "VALUES (1, 1, 1, 'rewritten', 'Closed', 'x')"
REPLACE_STATEMENTS = [
    f"INSERT OR REPLACE INTO request_audit {_COLUMNS} {_VALUES}",
    f"REPLACE INTO request_audit {_COLUMNS} {_VALUES}",
]


def _original_row(db_path):
    """Read the audit row through a brand-new connection, as the application would."""
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT id, action_type, new_status FROM request_audit WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()


@pytest.mark.parametrize("statement", REPLACE_STATEMENTS)
@pytest.mark.parametrize("recursive_triggers", [False, True])
def test_replace_cannot_overwrite_an_existing_audit_row(tmp_path, statement, recursive_triggers):
    """INSERT OR REPLACE deletes the old row without firing the DELETE trigger unless
    recursive_triggers is on, so a separate guard must refuse reuse of an existing id."""
    db_path = str(tmp_path / "a.sqlite")
    setup_db(db_path)
    _create_one_request(db_path)
    before = _original_row(db_path)
    assert before == (1, "request_submitted", "New")

    conn = _connect(db_path)  # fresh connection, default pragmas: how the app connects
    try:
        if recursive_triggers:
            conn.execute("PRAGMA recursive_triggers = ON")
        else:
            assert conn.execute("PRAGMA recursive_triggers").fetchone()[0] == 0
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute(statement)
    finally:
        conn.close()

    assert _original_row(db_path) == before


def test_new_audit_rows_still_insert_after_replace_guard(tmp_path):
    db_path = str(tmp_path / "a.sqlite")
    setup_db(db_path)
    _create_one_request(db_path)
    _create_one_request(db_path)  # a second genuine audit entry through the real service
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO request_audit (id, request_id, actor_user_id, action_type, correlation_id) "
            "VALUES (500, 1, 1, 'explicit_new_id', 'c')"
        )
        conn.commit()
        assert [r[0] for r in conn.execute("SELECT id FROM request_audit ORDER BY id")] == [1, 2, 500]
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
            "DROP TRIGGER request_audit_no_update; DROP TRIGGER request_audit_no_delete; "
            "DROP TRIGGER request_audit_no_replace;"
        )
    finally:
        conn.close()

    wsgi.bootstrap(db_path)

    conn = _connect(db_path)
    try:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        assert {
            "request_audit_no_update", "request_audit_no_delete", "request_audit_no_replace",
        } <= names
    finally:
        conn.close()

    # The guard is live on the migrated database, not just present in sqlite_master.
    conn = _connect(db_path)
    try:
        conn.execute("INSERT INTO users (email, password_hash, role) VALUES ('u@example.test', 'h', 'Requester')")
        conn.execute("INSERT INTO requests (requester_id, category_id, title, description, location, status) "
                     "VALUES (1, 1, 't', 'd', 'l', 'New')")
        conn.execute("INSERT INTO request_audit (request_id, actor_user_id, action_type, new_status, correlation_id) "
                     "VALUES (1, 1, 'request_submitted', 'New', 'c')")
        conn.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute(REPLACE_STATEMENTS[0])
    finally:
        conn.close()
