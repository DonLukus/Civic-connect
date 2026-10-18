"""FR-004: single-use, expiring password reset links (also used for first-time account setup).

Only a SHA-256 hash of the token is stored, so a copy of the database does not reveal a working
link. A token is valid for a limited time, works once, and requesting a new one cancels the old.
The email carrying the link goes through the same outbox as request notifications.
"""

import hashlib
import json
import secrets
import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime, timedelta

import bcrypt

from src.persistence.migrations import ensure_schema
from src.persistence.user_service import validate_password

RESET_VALID_MINUTES = 60
INVALID_LINK = "This link is invalid or has expired. Request a new one."


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _stamp(delta: timedelta) -> str:
    return (datetime.now(UTC) + delta).strftime("%Y-%m-%d %H:%M:%S")


def create_token(conn, user_id: int, valid_for: timedelta) -> str:
    """Create a token inside the caller's transaction and cancel the user's earlier ones."""
    conn.execute(
        "UPDATE password_resets SET used_at = CURRENT_TIMESTAMP WHERE user_id = ? AND used_at IS NULL",
        (user_id,),
    )
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, _hash(token), _stamp(valid_for)),
    )
    return token


class PasswordResetService:
    def __init__(self, db_path: str, password_cost: int = 12):
        if not 10 <= password_cost <= 16:
            raise ValueError("Password hash cost must be between 10 and 16")
        ensure_schema(db_path)
        self.db_path = db_path
        self.password_cost = password_cost

    def request_reset(self, email: str) -> bool:
        """Queue a reset email if the address belongs to an active account.

        Returns whether one was queued, for tests only: the caller must show the same message
        either way so the form cannot be used to discover which addresses have accounts.
        """
        email = (email or "").strip().lower()
        if not email:
            return False
        with closing(sqlite3.connect(self.db_path, timeout=10)) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT id FROM users WHERE lower(email) = ? AND is_active = 1", (email,)
                ).fetchone()
                if row is None:
                    conn.rollback()
                    return False
                token = create_token(conn, row[0], timedelta(minutes=RESET_VALID_MINUTES))
                correlation_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO outbox_events (aggregate_type, aggregate_id, event_type, "
                    "correlation_id, payload_json, state) VALUES "
                    "('PasswordReset', ?, 'PasswordResetRequested', ?, ?, 'pending')",
                    (row[0], correlation_id, json.dumps({"token": token})),
                )
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                raise

    def is_valid(self, token: str) -> bool:
        with closing(sqlite3.connect(self.db_path, timeout=10)) as conn:
            return self._find(conn, token) is not None

    @staticmethod
    def _find(conn, token):
        if not token:
            return None
        return conn.execute(
            "SELECT p.id, p.user_id FROM password_resets p JOIN users u ON u.id = p.user_id "
            "WHERE p.token_hash = ? AND p.used_at IS NULL AND p.expires_at > ? AND u.is_active = 1",
            (_hash(token), _stamp(timedelta(0))),
        ).fetchone()

    def set_password(self, token: str, new_password: str) -> None:
        """Use the link once to set a new password; raises ValueError for a bad link or password."""
        validate_password(new_password)
        digest = bcrypt.hashpw(new_password.encode("utf-8"),
                               bcrypt.gensalt(rounds=self.password_cost)).decode("ascii")
        with closing(sqlite3.connect(self.db_path, timeout=10)) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                found = self._find(conn, token)
                if found is None:
                    raise ValueError(INVALID_LINK)
                user_id = found[1]
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (digest, user_id))
                conn.execute(
                    "UPDATE password_resets SET used_at = CURRENT_TIMESTAMP "
                    "WHERE user_id = ? AND used_at IS NULL", (user_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
