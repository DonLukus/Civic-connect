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

from werkzeug.security import generate_password_hash

from src.web.app import create_app

DB_PATH = os.environ.get("DATABASE_URL", "civicconnect.sqlite")


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

        # PoC account credentials come only from deployment secrets. No fixed password is
        # committed, and an existing user's password is never reset on restart.
        demo_email = os.environ.get("BOOTSTRAP_REQUESTER_EMAIL")
        demo_password = os.environ.get("BOOTSTRAP_REQUESTER_PASSWORD")
        if bool(demo_email) != bool(demo_password):
            raise RuntimeError("Both bootstrap requester settings must be supplied together")
        if demo_email and demo_password:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE lower(email) = ?", (demo_email.lower(),)
            ).fetchone()
            if exists is None:
                conn.execute(
                    "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'Requester', 1)",
                    (demo_email.strip().lower(), generate_password_hash(demo_password)),
                )
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, target_resolution_hours, is_active) "
            "VALUES ('Utilities', 48, 1)"
        )
        conn.commit()
    finally:
        conn.close()


bootstrap(DB_PATH)
app = create_app(DB_PATH)
