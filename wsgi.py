"""
Production WSGI entrypoint for the M2 deployment proof-of-concept (DEC-008 evidence).

Checked before writing this: neither RequestService nor RequestRepository initialises the
database schema (no CREATE TABLE / executescript call in either file) - schema.sql is applied
only by the test files' own setup_db() and by the README's manual bootstrap snippet. A fresh
deploy target has neither, so this module does it once, idempotently, before serving any request.

Idempotent because schema.sql's CREATE TABLE statements have no IF NOT EXISTS - this checks for
the 'requests' table first rather than assuming a fresh file, so it is safe across process
restarts on a persistent file - which is exactly the thing this PoC is trying to find out whether
Render's free tier actually gives us.
"""

import os
import sqlite3
import threading

import bcrypt

from src.persistence.outbox import OutboxProcessor
from src.web.app import create_app

DB_PATH = os.environ.get("DATABASE_URL", "civicconnect.sqlite")
_outbox_thread = None


def _migrate_m3_schema(conn: sqlite3.Connection) -> None:
    outbox = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='outbox_events'"
    ).fetchone()
    if outbox and "sending" not in outbox[0]:
        conn.executescript(
            """
            CREATE TABLE outbox_events_m3 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aggregate_type TEXT NOT NULL,
                aggregate_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('pending','sending','sent','failed')) DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT
            );
            INSERT INTO outbox_events_m3
                SELECT id, aggregate_type, aggregate_id, event_type, correlation_id,
                       payload_json, state, attempts, last_error, created_at, sent_at
                FROM outbox_events;
            DROP TABLE outbox_events;
            ALTER TABLE outbox_events_m3 RENAME TO outbox_events;
            """
        )
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_outbox_state ON outbox_events(state, created_at);
        CREATE TABLE IF NOT EXISTS request_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outbox_event_id INTEGER NOT NULL UNIQUE,
            request_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT,
            FOREIGN KEY (request_id) REFERENCES requests(id),
            FOREIGN KEY (requester_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_request_notifications_requester
            ON request_notifications(requester_id, created_at);

        -- Databases created before this change get the same append-only protection.
        CREATE TRIGGER IF NOT EXISTS request_audit_no_update
        BEFORE UPDATE ON request_audit
        BEGIN
            SELECT RAISE(ABORT, 'request_audit is append-only (FR-025, NFR-006)');
        END;

        CREATE TRIGGER IF NOT EXISTS request_audit_no_delete
        BEFORE DELETE ON request_audit
        BEGIN
            SELECT RAISE(ABORT, 'request_audit is append-only (FR-025, NFR-006)');
        END;
        """
    )


def _start_outbox_worker(db_path: str) -> None:
    global _outbox_thread
    if os.environ.get("OUTBOX_WORKER_ENABLED", "false").lower() != "true":
        return
    if not os.environ.get("EMAIL_SMTP_HOST") or not os.environ.get("EMAIL_FROM_ADDRESS"):
        raise RuntimeError("SMTP host and sender must be configured when the outbox worker is enabled")
    poll_seconds = int(os.environ.get("OUTBOX_WORKER_POLL_SECONDS", "60"))
    if poll_seconds < 1:
        raise RuntimeError("OUTBOX_WORKER_POLL_SECONDS must be positive")
    processor = OutboxProcessor(db_path)
    _outbox_thread = threading.Thread(
        target=processor.run, args=(poll_seconds,), name="civicconnect-outbox", daemon=True
    )
    _outbox_thread.start()


def bootstrap(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        has_schema = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='requests'"
        ).fetchone()
        if has_schema is None:
            schema_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "src", "persistence", "schema.sql"
            )
            with open(schema_path, "r") as f:
                conn.executescript(f.read())
            conn.commit()

        _migrate_m3_schema(conn)

        password_cost = int(os.environ.get("PASSWORD_HASH_COST", "12"))
        if not 10 <= password_cost <= 16:
            raise RuntimeError("PASSWORD_HASH_COST must be between 10 and 16")
        accounts = (
            ("Requester", "BOOTSTRAP_REQUESTER_EMAIL", "BOOTSTRAP_REQUESTER_PASSWORD"),
            ("Staff", "BOOTSTRAP_STAFF_EMAIL", "BOOTSTRAP_STAFF_PASSWORD"),
            ("Manager", "BOOTSTRAP_MANAGER_EMAIL", "BOOTSTRAP_MANAGER_PASSWORD"),
            ("Administrator", "BOOTSTRAP_ADMIN_EMAIL", "BOOTSTRAP_ADMIN_PASSWORD"),
        )
        for role, email_name, password_name in accounts:
            demo_email = os.environ.get(email_name)
            demo_password = os.environ.get(password_name)
            if bool(demo_email) != bool(demo_password):
                raise RuntimeError(f"Both {email_name} and {password_name} must be supplied together")
            if not demo_email:
                continue
            if len(demo_password.encode("utf-8")) > 72:
                raise RuntimeError(f"{password_name} exceeds bcrypt's 72-byte limit")
            exists = conn.execute(
                "SELECT role FROM users WHERE lower(email) = ?", (demo_email.strip().lower(),)
            ).fetchone()
            if exists is None:
                conn.execute(
                    "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                    (
                        demo_email.strip().lower(),
                        bcrypt.hashpw(
                            demo_password.encode("utf-8"), bcrypt.gensalt(rounds=password_cost)
                        ).decode("ascii"),
                        role,
                    ),
                )
            elif exists[0] != role:
                raise RuntimeError(f"{email_name} is already provisioned with a different role")
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, target_resolution_hours, is_active) "
            "VALUES ('Utilities', 48, 1)"
        )
        conn.commit()
    finally:
        conn.close()


bootstrap(DB_PATH)
app = create_app(DB_PATH)
_start_outbox_worker(DB_PATH)
