import json
import sqlite3
import uuid
from typing import ClassVar

from src.persistence.lifecycle import LifecycleValidator
from src.persistence.request_repository import RequestRepository


class SubmissionValidationError(ValueError):
    """A submission validation failure that can be tied to one form control."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


class RequestService:
    STATUSES = ("New", "Accepted", "In Progress", "On Hold", "Resolved", "Closed", "Rejected")
    OPEN_STATUSES = ("New", "Accepted", "In Progress", "On Hold")
    TEXT_LIMITS: ClassVar[dict[str, int]] = {
        "title": 200, "description": 5000, "location": 300,
    }

    def __init__(self, db_path: str):
        self.repo = RequestRepository(db_path)
        self.db_path = db_path

    @classmethod
    def validate_status_filter(cls, status):
        if status is not None and status not in cls.STATUSES:
            raise ValueError("status must be one of the supported request statuses")
        return status

    def list_requester_requests(self, requester_id: int, status=None):
        status = self.validate_status_filter(status)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (requester_id,)
            ).fetchone()
            if actor is None or actor["role"] != "Requester":
                raise PermissionError("Only an active Requester may view this request list")

            sql = """
                  SELECT r.id AS reference, r.title, c.name AS category, r.created_at AS submitted_at,
                      r.status,
                      COALESCE((
                          SELECT MAX(a.changed_at) FROM request_audit AS a
                          WHERE a.request_id = r.id AND a.new_status = r.status
                      ), r.created_at) AS last_status_changed_at
                FROM requests AS r
                JOIN categories AS c ON c.id = r.category_id
                WHERE r.requester_id = ?
            """
            parameters = [requester_id]
            if status is not None:
                sql += " AND r.status = ?"
                parameters.append(status)
            sql += " ORDER BY r.created_at DESC, r.id DESC"
            return [dict(row) for row in conn.execute(sql, parameters).fetchall()]
        finally:
            conn.close()

    def list_staff_queue(self, staff_id: int, status=None):
        status = self.validate_status_filter(status)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (staff_id,)
            ).fetchone()
            if actor is None or actor["role"] != "Staff":
                raise PermissionError("Only an active Staff user may view the staff queue")

            sql = """
                  SELECT r.id AS reference, r.title, c.name AS category, r.created_at AS submitted_at,
                      r.status, r.assignee_id,
                      COALESCE((
                          SELECT MAX(a.changed_at) FROM request_audit AS a
                          WHERE a.request_id = r.id AND a.new_status = r.status
                      ), r.created_at) AS last_status_changed_at
                FROM requests AS r
                JOIN categories AS c ON c.id = r.category_id
                WHERE (r.assignee_id IS NULL OR r.assignee_id = ?)
            """
            parameters = [staff_id]
            if status is not None:
                sql += " AND r.status = ?"
                parameters.append(status)
            sql += " ORDER BY r.created_at ASC, r.id ASC"
            return [dict(row) for row in conn.execute(sql, parameters).fetchall()]
        finally:
            conn.close()

    def list_manager_requests(self, manager_id: int, status=None, category_id=None):
        """Return the Manager's displayed/exported request list using the same filters."""
        status = self.validate_status_filter(status)
        if category_id in (None, ""):
            category_id = None
        elif isinstance(category_id, bool):
            raise ValueError("category must be a valid controlled-list identifier")
        else:
            try:
                category_id = int(category_id)
            except (TypeError, ValueError) as exc:
                raise ValueError("category must be a valid controlled-list identifier") from exc
            if category_id <= 0:
                raise ValueError("category must be a valid controlled-list identifier")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (manager_id,)
            ).fetchone()
            if actor is None or actor["role"] != "Manager":
                raise PermissionError("Only an active Manager may view or export this list")

            sql = """
                SELECT r.id AS reference, r.title, c.name AS category,
                       r.created_at AS submitted_at, r.status,
                       COALESCE(assignee.email, 'Unassigned') AS assignee
                FROM requests AS r
                JOIN categories AS c ON c.id = r.category_id
                LEFT JOIN users AS assignee ON assignee.id = r.assignee_id
                WHERE 1 = 1
            """
            parameters = []
            if status is not None:
                sql += " AND r.status = ?"
                parameters.append(status)
            if category_id is not None:
                sql += " AND r.category_id = ?"
                parameters.append(category_id)
            sql += " ORDER BY r.created_at DESC, r.id DESC"
            return [dict(row) for row in conn.execute(sql, parameters).fetchall()]
        finally:
            conn.close()

    def get_request_detail(self, actor_id: int, request_id: int):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (actor_id,)
            ).fetchone()
            if actor is None:
                raise PermissionError("An active user is required to view request detail")

            row = conn.execute(
                """
                SELECT r.id AS reference, r.requester_id, r.assignee_id, r.category_id,
                       r.title, r.description, r.location, r.status, r.version,
                       r.created_at AS submitted_at, r.updated_at, r.accepted_at,
                       COALESCE((
                           SELECT MAX(a.changed_at) FROM request_audit AS a
                           WHERE a.request_id = r.id AND a.new_status = r.status
                       ), r.created_at) AS last_status_changed_at,
                       c.name AS category, assignee.email AS assignee_email,
                       requester.email AS requester_email
                FROM requests AS r
                JOIN categories AS c ON c.id = r.category_id
                LEFT JOIN users AS assignee ON assignee.id = r.assignee_id
                JOIN users AS requester ON requester.id = r.requester_id
                WHERE r.id = ?
                """,
                (request_id,),
            ).fetchone()
            if row is None:
                raise LookupError("Request not found")

            role = actor["role"]
            if role == "Requester" and row["requester_id"] != actor_id:
                raise LookupError("Request not found")
            if role == "Staff" and row["assignee_id"] not in (None, actor_id):
                raise LookupError("Request not found")
            if role not in ("Requester", "Staff", "Manager", "Administrator"):
                raise PermissionError("This role cannot view request detail")

            detail = dict(row)
            detail.pop("requester_id")
            if not (role in ("Manager", "Administrator") or
                    (role == "Staff" and row["assignee_id"] == actor_id)):
                detail.pop("requester_email")

            detail["history"] = [
                dict(item) for item in conn.execute(
                    """
                    SELECT a.action_type, a.previous_status, a.new_status,
                           a.previous_assignee_id, a.new_assignee_id, a.changed_at,
                           a.actor_user_id
                    FROM request_audit AS a
                    WHERE a.request_id = ?
                    ORDER BY a.changed_at ASC, a.id ASC
                    """,
                    (request_id,),
                ).fetchall()
            ]
            return detail
        finally:
            conn.close()

    def list_notifications(self, requester_id: int):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (requester_id,)
            ).fetchone()
            if actor is None or actor["role"] != "Requester":
                raise PermissionError("Only an active Requester may view notifications")
            return [
                dict(row) for row in conn.execute(
                    """
                    SELECT id, request_id, event_type, message, created_at, read_at
                    FROM request_notifications
                    WHERE requester_id = ?
                    ORDER BY created_at DESC, id DESC
                    """,
                    (requester_id,),
                ).fetchall()
            ]
        finally:
            conn.close()

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
        category_id, title, description, location = self._validate_submission_values(
            category_id, title, description, location
        )

        correlation_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")

            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (requester_id,)
            ).fetchone()
            if actor is None or actor[0] != "Requester":
                conn.rollback()
                raise PermissionError("Only an active Requester may submit a request")

            category = conn.execute(
                "SELECT id FROM categories WHERE id = ? AND is_active = 1",
                (category_id,),
            ).fetchone()
            if category is None:
                conn.rollback()
                raise SubmissionValidationError(
                    "category_id", "Select a category from the active controlled list."
                )

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

    @classmethod
    def _validate_submission_values(cls, category_id, title, description, location):
        values = {}
        labels = {"title": "title", "description": "description", "location": "location"}
        for field, value in (
            ("title", title), ("description", description), ("location", location)
        ):
            if not isinstance(value, str):
                raise SubmissionValidationError(field, f"{labels[field]} must be text.")
            cleaned = value.strip()
            if not cleaned:
                raise SubmissionValidationError(field, f"{labels[field]} is required.")
            if len(cleaned) > cls.TEXT_LIMITS[field]:
                raise SubmissionValidationError(
                    field,
                    f"{labels[field]} must be {cls.TEXT_LIMITS[field]} characters or fewer.",
                )
            values[field] = cleaned

        if isinstance(category_id, bool):
            raise SubmissionValidationError(
                "category_id", "Select a category from the active controlled list."
            )
        try:
            category_id = int(category_id)
        except (TypeError, ValueError) as exc:
            raise SubmissionValidationError(
                "category_id", "Select a category from the active controlled list."
            ) from exc
        if category_id <= 0:
            raise SubmissionValidationError(
                "category_id", "Select a category from the active controlled list."
            )
        return category_id, values["title"], values["description"], values["location"]

    def find_open_duplicates(
        self, requester_id: int, category_id, title, description, location
    ):
        """List safe duplicate references before creation without exposing requester data."""
        category_id, _, _, location = self._validate_submission_values(
            category_id, title, description, location
        )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (requester_id,)
            ).fetchone()
            if actor is None or actor["role"] != "Requester":
                raise PermissionError("Only an active Requester may submit a request")
            category = conn.execute(
                "SELECT id FROM categories WHERE id = ? AND is_active = 1", (category_id,)
            ).fetchone()
            if category is None:
                raise SubmissionValidationError(
                    "category_id", "Select a category from the active controlled list."
                )
            placeholders = ", ".join("?" for _ in self.OPEN_STATUSES)
            rows = conn.execute(
                f"""
                SELECT r.id AS reference, c.name AS category, r.location, r.status
                FROM requests AS r
                JOIN categories AS c ON c.id = r.category_id
                WHERE r.category_id = ?
                  AND lower(trim(r.location)) = lower(?)
                  AND r.status IN ({placeholders})
                ORDER BY r.created_at DESC, r.id DESC
                """,
                (category_id, location, *self.OPEN_STATUSES),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def accept_request(self, request_id: int, staff_id: int, expected_version: int) -> bool:
        correlation_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")

            actor = conn.execute(
                "SELECT role FROM users WHERE id = ? AND is_active = 1", (staff_id,)
            ).fetchone()
            if actor is None or actor[0] != "Staff":
                conn.rollback()
                raise PermissionError("Only active Staff may accept a request")

            current = conn.execute(
                "SELECT status, assignee_id, version FROM requests WHERE id = ?",
                (request_id,),
            ).fetchone()
            if current is None:
                conn.rollback()
                return False

            previous_status, previous_assignee_id, previous_version = current

            transition_valid = LifecycleValidator.validate_transition(
                current_status=previous_status,
                current_assignee_id=previous_assignee_id,
                target_status="Accepted",
                target_assignee_id=staff_id,
            )
            if not transition_valid or previous_version != expected_version:
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
