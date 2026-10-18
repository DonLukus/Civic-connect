"""FR-010, FR-014 to FR-018: the request workflow (status changes, assignment, comments).

Mixed into RequestService. Every method is one transaction: the change, its audit row and any
notification (outbox) row commit together or not at all, and a stale page is refused by the
optimistic version check.
"""

import json
import sqlite3
import uuid

from src.persistence import lifecycle

MAX_COMMENT_LENGTH = 2000
MAX_NOTE_LENGTH = 2000


class VersionConflict(Exception):
    """The request changed since the caller loaded it (optimistic lock)."""


class WorkflowMixin:
    db_path: str

    @staticmethod
    def _audit(conn, request_id, actor_id, action, prev_status, new_status, prev_assignee,
               new_assignee, correlation_id, payload):
        conn.execute(
            """
            INSERT INTO request_audit (
                request_id, actor_user_id, action_type, previous_status, new_status,
                previous_assignee_id, new_assignee_id, correlation_id, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (request_id, actor_id, action, prev_status, new_status, prev_assignee,
             new_assignee, correlation_id, json.dumps(payload)),
        )

    @staticmethod
    def _outbox(conn, request_id, event_type, correlation_id, payload):
        conn.execute(
            """
            INSERT INTO outbox_events (
                aggregate_type, aggregate_id, event_type, correlation_id, payload_json, state
            ) VALUES ('Request', ?, ?, ?, ?, 'pending')
            """,
            (request_id, event_type, correlation_id, json.dumps(payload)),
        )

    @staticmethod
    def _active_role(conn, user_id):
        row = conn.execute(
            "SELECT role FROM users WHERE id = ? AND is_active = 1", (user_id,)
        ).fetchone()
        if row is None:
            raise PermissionError("An active user is required")
        return row[0]

    def change_status(self, request_id: int, actor_id: int, target_status: str,
                      expected_version: int, note: str | None = None) -> None:
        """FR-015/016/017/018: move a request along the transition table.

        Raises LookupError (no such request / not visible), PermissionError (role), ValueError
        (illegal transition or missing note/reason) or VersionConflict (stale page).
        """
        note = (note or "").strip()
        if len(note) > MAX_NOTE_LENGTH:
            raise ValueError(f"The text must be at most {MAX_NOTE_LENGTH} characters")
        correlation_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            conn.execute("BEGIN IMMEDIATE")
            role = self._active_role(conn, actor_id)
            current = conn.execute(
                "SELECT status, assignee_id, version FROM requests WHERE id = ?", (request_id,)
            ).fetchone()
            if current is None:
                raise LookupError("Request not found")
            status, assignee_id, version = current
            if role == "Staff" and assignee_id not in (None, actor_id):
                raise LookupError("Request not found")
            lifecycle.check_transition(role, assignee_id == actor_id, status, target_status)
            needed = lifecycle.required_note(status, target_status)
            if needed and not note:
                raise ValueError(f"A {needed} is required")
            if version != expected_version:
                raise VersionConflict("The request changed; reload and try again")

            sets = ["status = ?", "version = version + 1", "updated_at = CURRENT_TIMESTAMP"]
            args = [target_status]
            event = None
            if target_status == "Resolved":
                sets += ["resolution_note = ?", "resolution_by = ?",
                         "resolution_at = CURRENT_TIMESTAMP"]
                args += [note, actor_id]
                event = ("RequestResolved", {"note": note})
            elif target_status == "Rejected":
                sets.append("rejection_reason = ?")
                args.append(note)
                event = ("RequestRejected", {"reason": note})
            changed = conn.execute(
                f"UPDATE requests SET {', '.join(sets)} WHERE id = ? AND version = ?",
                (*args, request_id, expected_version),
            ).rowcount
            if changed != 1:
                raise VersionConflict("The request changed; reload and try again")

            payload = {"request_id": request_id, "actor_user_id": actor_id,
                       "previous_status": status, "new_status": target_status,
                       "note": note or None, "correlation_id": correlation_id}
            self._audit(conn, request_id, actor_id, "change_status", status, target_status,
                        assignee_id, assignee_id, correlation_id, payload)
            if event:
                self._outbox(conn, request_id, event[0], correlation_id, {**payload, **event[1]})
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def assign_request(self, request_id: int, actor_id: int, assignee_id: int,
                       expected_version: int) -> None:
        """FR-014: a Manager assigns (New to Accepted) or reassigns (status unchanged)."""
        correlation_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            conn.execute("BEGIN IMMEDIATE")
            if self._active_role(conn, actor_id) != "Manager":
                raise PermissionError("Only a Manager may assign or reassign a request")
            target = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (assignee_id,)
            ).fetchone()
            if target is None or target[0] != "Staff":
                raise ValueError("The assignee must be an active Staff user")
            current = conn.execute(
                "SELECT status, assignee_id, version FROM requests WHERE id = ?", (request_id,)
            ).fetchone()
            if current is None:
                raise LookupError("Request not found")
            status, previous_assignee, version = current
            if version != expected_version:
                raise VersionConflict("The request changed; reload and try again")
            if previous_assignee == assignee_id:
                raise ValueError("That user is already the assignee")

            if previous_assignee is None:
                if status != "New":
                    raise ValueError(f"A {status} request cannot be newly assigned")
                is_assign, new_status, action = True, "Accepted", "assign_request"
                extra = ", status = 'Accepted', accepted_at = CURRENT_TIMESTAMP"
            else:
                if status in ("Closed", "Rejected"):
                    raise ValueError(f"A {status} request cannot be reassigned")
                is_assign, new_status, action = False, None, "reassign_request"
                extra = ""
            changed = conn.execute(
                "UPDATE requests SET assignee_id = ?, version = version + 1, "
                f"updated_at = CURRENT_TIMESTAMP{extra} WHERE id = ? AND version = ?",
                (assignee_id, request_id, expected_version),
            ).rowcount
            if changed != 1:
                raise VersionConflict("The request changed; reload and try again")

            prev_status = status if is_assign else None
            payload = {"request_id": request_id, "actor_user_id": actor_id,
                       "previous_status": prev_status, "new_status": new_status,
                       "previous_assignee_id": previous_assignee, "new_assignee_id": assignee_id,
                       "correlation_id": correlation_id}
            # A pure reassignment is not a status change, so its status columns stay NULL.
            self._audit(conn, request_id, actor_id, action, prev_status, new_status,
                        previous_assignee, assignee_id, correlation_id, payload)
            if is_assign:
                self._outbox(conn, request_id, "RequestAccepted", correlation_id, payload)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_comment(self, request_id: int, author_id: int, body: str) -> int:
        """FR-010: the Requester, the assigned Staff user or a Manager comments on an assigned request."""
        body = (body or "").strip()
        if not body:
            raise ValueError("A comment cannot be empty")
        if len(body) > MAX_COMMENT_LENGTH:
            raise ValueError(f"A comment must be at most {MAX_COMMENT_LENGTH} characters")
        correlation_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            conn.execute("BEGIN IMMEDIATE")
            role = self._active_role(conn, author_id)
            row = conn.execute(
                "SELECT requester_id, assignee_id FROM requests WHERE id = ?", (request_id,)
            ).fetchone()
            if row is None:
                raise LookupError("Request not found")
            requester_id, assignee_id = row
            allowed = (
                (role == "Requester" and requester_id == author_id)
                or (role == "Staff" and assignee_id == author_id)
                or role == "Manager"
            )
            if not allowed:
                raise LookupError("Request not found")
            if assignee_id is None:
                raise ValueError("Comments open once a staff member is assigned")
            comment_id = conn.execute(
                "INSERT INTO request_comments (request_id, author_id, body) VALUES (?, ?, ?)",
                (request_id, author_id, body),
            ).lastrowid
            if author_id != requester_id:  # FR-009: tell the Requester about the other side's comment
                self._outbox(conn, request_id, "CommentAdded", correlation_id,
                             {"request_id": request_id, "comment_id": comment_id,
                              "actor_user_id": author_id, "comment": body,
                              "correlation_id": correlation_id})
            conn.commit()
            return comment_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
