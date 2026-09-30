import sqlite3
import uuid
from typing import Optional


class RequestRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def accept_request_if_available(self, request_id: int, staff_id: int, expected_version: int) -> bool:
        sql = """
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
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql, (staff_id, request_id, expected_version))
            return cursor.rowcount == 1

    def insert_audit_row(
        self,
        request_id: int,
        actor_user_id: int,
        action_type: str,
        previous_status: Optional[str],
        new_status: str,
        previous_assignee_id: Optional[int],
        new_assignee_id: Optional[int],
        correlation_id: str,
        payload_json: str,
    ) -> None:
        sql = """
            INSERT INTO request_audit (
                request_id, actor_user_id, action_type, previous_status, new_status,
                previous_assignee_id, new_assignee_id, correlation_id, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                sql,
                (
                    request_id,
                    actor_user_id,
                    action_type,
                    previous_status,
                    new_status,
                    previous_assignee_id,
                    new_assignee_id,
                    correlation_id,
                    payload_json,
                ),
            )

    def insert_outbox_event(
        self,
        aggregate_type: str,
        aggregate_id: int,
        event_type: str,
        payload_json: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        correlation_id = correlation_id or str(uuid.uuid4())
        sql = """
            INSERT INTO outbox_events (
                aggregate_type, aggregate_id, event_type, correlation_id, payload_json, state
            ) VALUES (?, ?, ?, ?, ?, 'pending')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, (aggregate_type, aggregate_id, event_type, correlation_id, payload_json))
