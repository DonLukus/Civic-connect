import json
import sqlite3
import uuid

from request_repository import RequestRepository


class RequestService:
    def __init__(self, db_path: str):
        self.repo = RequestRepository(db_path)
        self.db_path = db_path

    def accept_request(self, request_id: int, staff_id: int, expected_version: int) -> bool:
        correlation_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")

            current = conn.execute(
                "SELECT status, assignee_id, version FROM requests WHERE id = ?",
                (request_id,),
            ).fetchone()
            if current is None:
                conn.rollback()
                return False

            previous_status, previous_assignee_id, previous_version = current

            if previous_status != "New" or previous_assignee_id is not None or previous_version != expected_version:
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
