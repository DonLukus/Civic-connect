"""FR-001, FR-023, FR-024: Administrator functions - accounts, roles and the category list.

Every account or role change is written to `admin_audit` (append-only) in the same transaction.
Only an active Administrator may call these methods; the checks are here, not only in the routes.
"""

import re
import secrets
import sqlite3
from contextlib import closing
from datetime import timedelta

import bcrypt

from src.persistence.migrations import ensure_schema
from src.persistence.password_reset import create_token

ROLES = ("Requester", "Staff", "Manager", "Administrator")
EMAIL_PATTERN = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
INVITE_VALID_HOURS = 72
MAX_CATEGORY_NAME = 80
MAX_TARGET_HOURS = 24 * 365


class AdminService:
    def __init__(self, db_path: str, password_cost: int = 12):
        if not 10 <= password_cost <= 16:
            raise ValueError("Password hash cost must be between 10 and 16")
        ensure_schema(db_path)
        self.db_path = db_path
        self.password_cost = password_cost

    # ---- helpers -------------------------------------------------------------------------

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _require_admin(conn, actor_id):
        row = conn.execute(
            "SELECT role FROM users WHERE id = ? AND is_active = 1", (actor_id,)
        ).fetchone()
        if row is None or row["role"] != "Administrator":
            raise PermissionError("Only an active Administrator may do this")

    @staticmethod
    def _audit(conn, actor_id, action, target_id, previous, new):
        conn.execute(
            "INSERT INTO admin_audit (actor_user_id, action_type, target_user_id, "
            "previous_value, new_value) VALUES (?, ?, ?, ?, ?)",
            (actor_id, action, target_id, previous, new),
        )

    @staticmethod
    def _active_admin_count(conn, excluding=None):
        return conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'Administrator' AND is_active = 1 AND id != ?",
            (excluding if excluding is not None else -1,),
        ).fetchone()[0]

    # ---- users ---------------------------------------------------------------------------

    def list_users(self, actor_id: int):
        with closing(self._connect()) as conn:
            self._require_admin(conn, actor_id)
            return [dict(r) for r in conn.execute(
                """
                SELECT u.id, u.email, u.role, u.is_active, u.created_at,
                       (SELECT COUNT(*) FROM requests r WHERE r.assignee_id = u.id
                        AND r.status IN ('New','Accepted','In Progress','On Hold')) AS open_assigned
                FROM users u ORDER BY u.email
                """).fetchall()]

    def provision_user(self, actor_id: int, email: str, role: str):
        """FR-001: create an active account with exactly one role; returns (user_id, setup_token).

        No password is chosen for the person. The account is created with an unusable random
        hash and a single-use link (valid 72 hours) with which they set their own password.
        """
        email = (email or "").strip().lower()
        if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
            raise ValueError("Enter a valid email address.")
        if role not in ROLES:
            raise ValueError("Choose one of the four roles.")
        unusable = bcrypt.hashpw(secrets.token_urlsafe(32).encode(),
                                 bcrypt.gensalt(rounds=self.password_cost)).decode("ascii")
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
                    raise ValueError("An account with that email already exists.")
                user_id = conn.execute(
                    "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                    (email, unusable, role),
                ).lastrowid
                token = create_token(conn, user_id, timedelta(hours=INVITE_VALID_HOURS))
                self._audit(conn, actor_id, "create_user", user_id, None, role)
                conn.commit()
                return user_id, token
            except Exception:
                conn.rollback()
                raise

    def change_role(self, actor_id: int, user_id: int, new_role: str) -> None:
        if new_role not in ROLES:
            raise ValueError("Choose one of the four roles.")
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                row = conn.execute("SELECT role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
                if row is None:
                    raise LookupError("User not found")
                if row["role"] == new_role:
                    raise ValueError("The user already has that role.")
                if (row["role"] == "Administrator" and row["is_active"]
                        and self._active_admin_count(conn, excluding=user_id) == 0):
                    raise ValueError("At least one active Administrator must remain.")
                conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
                self._audit(conn, actor_id, "change_role", user_id, row["role"], new_role)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def set_active(self, actor_id: int, user_id: int, active: bool) -> None:
        """FR-024: deactivate (cannot sign in, sessions stop working) or reactivate an account.

        Requests assigned to a deactivated user stay assigned and visible to Managers, who can
        reassign them (FR-014).
        """
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                row = conn.execute("SELECT role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
                if row is None:
                    raise LookupError("User not found")
                if bool(row["is_active"]) == bool(active):
                    raise ValueError("The account is already " + ("active." if active else "inactive."))
                if not active:
                    if user_id == actor_id:
                        raise ValueError("You cannot deactivate your own account.")
                    if row["role"] == "Administrator" and self._active_admin_count(conn, excluding=user_id) == 0:
                        raise ValueError("At least one active Administrator must remain.")
                conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if active else 0, user_id))
                self._audit(conn, actor_id, "reactivate_user" if active else "deactivate_user",
                            user_id, "inactive" if active else "active", "active" if active else "inactive")
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def list_admin_audit(self, actor_id: int, limit: int = 50):
        with closing(self._connect()) as conn:
            self._require_admin(conn, actor_id)
            return [dict(r) for r in conn.execute(
                "SELECT a.id, a.actor_user_id, a.action_type, a.target_user_id, a.previous_value, "
                "a.new_value, a.changed_at FROM admin_audit a ORDER BY a.id DESC LIMIT ?", (limit,)
            ).fetchall()]

    # ---- categories (FR-023) -------------------------------------------------------------

    @staticmethod
    def _clean_name(name):
        name = " ".join((name or "").split())
        if not name:
            raise ValueError("A category name is required.")
        if len(name) > MAX_CATEGORY_NAME:
            raise ValueError(f"A category name must be at most {MAX_CATEGORY_NAME} characters.")
        return name

    @staticmethod
    def _clean_target(hours):
        try:
            hours = int(hours)
        except (TypeError, ValueError):
            raise ValueError("The target resolution time must be a whole number of hours.") from None
        if not 1 <= hours <= MAX_TARGET_HOURS:
            raise ValueError(f"The target must be between 1 and {MAX_TARGET_HOURS} hours.")
        return hours

    @staticmethod
    def _name_taken(conn, name, excluding=None):
        return conn.execute(
            "SELECT 1 FROM categories WHERE lower(name) = lower(?) AND id != ?",
            (name, excluding if excluding is not None else -1),
        ).fetchone() is not None

    def list_categories(self, actor_id: int):
        with closing(self._connect()) as conn:
            self._require_admin(conn, actor_id)
            return [dict(r) for r in conn.execute(
                "SELECT c.id, c.name, c.target_resolution_hours, c.is_active, "
                "(SELECT COUNT(*) FROM requests r WHERE r.category_id = c.id) AS request_count "
                "FROM categories c ORDER BY c.is_active DESC, c.name").fetchall()]

    def create_category(self, actor_id: int, name: str, target_hours) -> int:
        name, hours = self._clean_name(name), self._clean_target(target_hours)
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                if self._name_taken(conn, name):
                    raise ValueError("A category with that name already exists.")
                category_id = conn.execute(
                    "INSERT INTO categories (name, target_resolution_hours, is_active) VALUES (?, ?, 1)",
                    (name, hours)).lastrowid
                self._audit(conn, actor_id, "create_category", None, None, f"{name} ({hours}h)")
                conn.commit()
                return category_id
            except Exception:
                conn.rollback()
                raise

    def update_category(self, actor_id: int, category_id: int, name=None, target_hours=None) -> None:
        """Rename and/or change the target time. Existing requests keep the category."""
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                row = conn.execute("SELECT name, target_resolution_hours FROM categories WHERE id = ?",
                                   (category_id,)).fetchone()
                if row is None:
                    raise LookupError("Category not found")
                new_name = self._clean_name(name) if name is not None else row["name"]
                new_hours = self._clean_target(target_hours) if target_hours is not None else row["target_resolution_hours"]
                if self._name_taken(conn, new_name, excluding=category_id):
                    raise ValueError("A category with that name already exists.")
                if (new_name, new_hours) == (row["name"], row["target_resolution_hours"]):
                    raise ValueError("Nothing was changed.")
                conn.execute("UPDATE categories SET name = ?, target_resolution_hours = ? WHERE id = ?",
                             (new_name, new_hours, category_id))
                self._audit(conn, actor_id, "update_category", None,
                            f"{row['name']} ({row['target_resolution_hours']}h)", f"{new_name} ({new_hours}h)")
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def set_category_active(self, actor_id: int, category_id: int, active: bool) -> None:
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                row = conn.execute("SELECT name, is_active FROM categories WHERE id = ?", (category_id,)).fetchone()
                if row is None:
                    raise LookupError("Category not found")
                if bool(row["is_active"]) == bool(active):
                    raise ValueError("The category is already " + ("active." if active else "inactive."))
                conn.execute("UPDATE categories SET is_active = ? WHERE id = ?", (1 if active else 0, category_id))
                self._audit(conn, actor_id, "reactivate_category" if active else "deactivate_category",
                            None, row["name"], row["name"])
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def delete_category(self, actor_id: int, category_id: int) -> None:
        """Delete only a category no request refers to; otherwise refuse (deactivate instead)."""
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._require_admin(conn, actor_id)
                row = conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
                if row is None:
                    raise LookupError("Category not found")
                if conn.execute("SELECT 1 FROM requests WHERE category_id = ?", (category_id,)).fetchone():
                    raise ValueError("Requests use this category, so it cannot be deleted. Deactivate it instead.")
                conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                self._audit(conn, actor_id, "delete_category", None, row["name"], None)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
