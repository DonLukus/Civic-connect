import json
import sqlite3
import uuid

from src.persistence.request_repository import RequestRepository
from src.persistence.lifecycle import LifecycleValidator


class RequestService:
    def __init__(self, db_path: str):
        self.repo = RequestRepository(db_path)
        self.db_path = db_path

    def create_request(
        self,
        requester_id: int,
        category_id: int,
        title: str,
        description: str,
        location: str,
    ):
        """FR-005 / FR-006 - the traced M2 slice (ADR-001).

        Mandatory fields and a controlled, active category are enforced here in the domain
        service, not only in the UI, per FEC-02 (lifecycle/validation must be testable without
        the UI). No outbox row is written on creation: FR-009 triggers notification on accepted,
        rejected, commented or completed, not on submission (ADR-001 correction) - so a
        requester's confirmation here is the synchronous return value, not an async event.

        Returns the new request id on success, or raises ValueError naming the first field that
        failed validation.
        """
        title = (title or "").strip()
        description = (description or "").strip()
        location = (location or "").strip()

        if not title:
            raise ValueError("title is required")
        if not description:
            raise ValueError("description is required")
        if not location:
            raise ValueError("location is required")

        correlation_id = str(uuid.uuid4())

        # NOTE: `with sqlite3.connect(...) as conn:` only wraps the transaction (commit/rollback
        # on exit) - it does NOT close the connection (stdlib sqlite3 behaviour). Left open, this
        # holds a Windows file lock that a later os.remove() on the db file fails against - caught
        # by actually running the traced-slice tests on the target platform, not assumed. Explicit
        # try/finally close fixes it here and in accept_request below.
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")

            category = conn.execute(
                "SELECT id FROM categories WHERE id = ? AND is_active = 1",
                (category_id,),
            ).fetchone()
            if category is None:
                conn.rollback()
                raise ValueError("category must be selected from the active controlled list")

            cursor = conn.execute(
                """
                INSERT INTO requests (
                    requester_id, assignee_id, category_id, title, description, location,
                    status, version
                ) VALUES (?, NULL, ?, ?, ?, ?, 'New', 0)
                """,
                (requester_id, category_id, title, description, location),
            )
            request_id = cursor.lastrowid

            payload = {
                "request_id": request_id,
                "actor_user_id": requester_id,
                "previous_status": None,
                "new_status": "New",
                "correlation_id": correlation_id,
            }

            conn.execute(
                """
                INSERT INTO request_audit (
                    request_id, actor_user_id, action_type, previous_status, new_status,
                    previous_assignee_id, new_assignee_id, correlation_id, payload_json
                ) VALUES (?, ?, 'request_submitted', NULL, 'New', NULL, NULL, ?, ?)
                """,
                (request_id, requester_id, correlation_id, json.dumps(payload)),
            )

            conn.commit()
            return request_id
        finally:
            conn.close()

    def accept_request(self, request_id: int, staff_id: int, expected_version: int) -> bool:
        correlation_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")

            current = conn.execute(
                "SELECT status, assignee_id, version FROM requests WHERE id = ?",
                (request_id,),
            ).fetchone()
            if current is None:
                conn.rollback()
                return False

            previous_status, previous_assignee_id, previous_version = current

            if not LifecycleValidator.can_accept(previous_status, previous_assignee_id) or previous_version != expected_version:
                conn.rollback()
                return False

            rowcount = conn.execute(
                """
                UPDATE requests
                SET assignee_id = ?,
                    status = 'Accepted',
                    version = version + 1,
                    updated_at = CURRENT_TIMESTAMP,
                    accepted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND assignee_id IS NULL
                  AND status = 'New'
                  AND version = ?
                """,
                (staff_id, request_id, expected_version),
            ).rowcount

            if rowcount != 1:
                conn.rollback()
                return False

            payload = {
                "request_id": request_id,
                "actor_user_id": staff_id,
                "previous_status": previous_status,
                "new_status": "Accepted",
                "previous_assignee_id": previous_assignee_id,
                "new_assignee_id": staff_id,
                "correlation_id": correlation_id,
            }

            conn.execute(
                """
                INSERT INTO request_audit (
                    request_id, actor_user_id, action_type, previous_status, new_status,
                    previous_assignee_id, new_assignee_id, correlation_id, payload_json
                ) VALUES (?, ?, 'accept_request', ?, 'Accepted', ?, ?, ?, ?)
                """,
                (
                    request_id,
                    staff_id,
                    previous_status,
                    previous_assignee_id,
                    staff_id,
                    correlation_id,
                    json.dumps(payload),
                ),
            )

            conn.execute(
                """
                INSERT INTO outbox_events (
                    aggregate_type, aggregate_id, event_type, correlation_id, payload_json, state
                ) VALUES ('Request', ?, 'RequestAccepted', ?, ?, 'pending')
                """,
                (request_id, correlation_id, json.dumps(payload)),
            )

            conn.commit()
            return True
        finally:
            conn.close()
