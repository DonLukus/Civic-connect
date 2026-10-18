"""Public account registration; self-registered users are always Requesters."""

import re
import sqlite3
from contextlib import closing

import bcrypt


class DuplicateEmailError(ValueError):
    pass


def validate_password(password: str) -> None:
    """The password rules shared by registration and password reset."""
    if len(password) < 8 or not password.strip():
        raise ValueError("Use a password with at least 8 characters.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be no longer than 72 UTF-8 bytes.")


class UserService:
    def __init__(self, db_path: str, password_cost: int = 12):
        if not 10 <= password_cost <= 16:
            raise ValueError("Password hash cost must be between 10 and 16")
        self.db_path = db_path
        self.password_cost = password_cost

    def register_requester(self, email: str, password: str) -> int:
        email = email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Enter a valid email address.")
        validate_password(password)
        digest = bcrypt.hashpw(password.encode("utf-8"),
                               bcrypt.gensalt(rounds=self.password_cost)).decode("ascii")
        with closing(sqlite3.connect(self.db_path, timeout=10)) as db, db:
            # Serialize the case-insensitive duplicate check and insert. Hashing is
            # deliberately completed before taking the database write lock.
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM users WHERE lower(email)=?", (email,)).fetchone():
                raise DuplicateEmailError("Unable to register this email. Try signing in instead.")
            try:
                cursor = db.execute(
                    "INSERT INTO users(email,password_hash,role,is_active) VALUES (?,?,'Requester',1)",
                    (email, digest),
                )
            except sqlite3.IntegrityError as exc:
                raise DuplicateEmailError("Unable to register this email. Try signing in instead.") from exc
            return cursor.lastrowid
