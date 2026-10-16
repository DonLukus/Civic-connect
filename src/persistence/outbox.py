import logging
import os
import smtplib
import sqlite3
import time
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class OutboxProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def process_pending(self, limit: int = 50) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT id FROM outbox_events WHERE state = 'pending' ORDER BY created_at, id LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            conn.close()

        delivered = 0
        for (row_id,) in rows:
            if not self._claim(row_id):
                continue
            try:
                self._deliver(row_id)
                self._set_state(row_id, "sent", None)
                delivered += 1
            except Exception as exc:
                logger.exception("Notification delivery failed for outbox event %s", row_id)
                self._record_failure(row_id, str(exc))
        return delivered

    def _claim(self, row_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            changed = conn.execute(
                "UPDATE outbox_events SET state = 'sending', attempts = attempts + 1 "
                "WHERE id = ? AND state = 'pending'",
                (row_id,),
            ).rowcount
            conn.commit()
            return changed == 1
        finally:
            conn.close()

    def _deliver(self, row_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            event = conn.execute(
                """
                SELECT e.event_type, e.aggregate_id, e.correlation_id, r.requester_id,
                       u.email, r.status
                FROM outbox_events AS e
                JOIN requests AS r ON r.id = e.aggregate_id
                JOIN users AS u ON u.id = r.requester_id
                WHERE e.id = ? AND e.aggregate_type = 'Request'
                """,
                (row_id,),
            ).fetchone()
            if event is None:
                raise ValueError("Outbox event has no matching request and requester")

            event_type, request_id, correlation_id, requester_id, email, status = event
            if event_type != "RequestAccepted":
                raise ValueError(f"Unsupported notification event: {event_type}")
            message = f"Request #{request_id} has been accepted. Current status: {status}."
            conn.execute(
                """
                INSERT OR IGNORE INTO request_notifications (
                    outbox_event_id, request_id, requester_id, event_type, message
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (row_id, request_id, requester_id, event_type, message),
            )
            conn.commit()
        finally:
            conn.close()

        self._send_email(email, request_id, status, correlation_id)

    @staticmethod
    def _send_email(recipient: str, request_id: int, status: str, correlation_id: str) -> None:
        host = os.environ.get("EMAIL_SMTP_HOST")
        sender = os.environ.get("EMAIL_FROM_ADDRESS")
        if not host or not sender:
            raise RuntimeError("EMAIL_SMTP_HOST and EMAIL_FROM_ADDRESS must be configured")
        port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
        message = EmailMessage()
        message["Subject"] = f"CivicConnect request #{request_id} accepted"
        message["From"] = sender
        message["To"] = recipient
        message["X-Correlation-ID"] = correlation_id
        message.set_content(
            f"Your service request #{request_id} has been accepted. Current status: {status}."
        )

        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            username = os.environ.get("EMAIL_SMTP_USERNAME")
            password = os.environ.get("EMAIL_SMTP_PASSWORD")
            if username:
                if not password:
                    raise RuntimeError("EMAIL_SMTP_PASSWORD is required with EMAIL_SMTP_USERNAME")
                smtp.login(username, password)
            smtp.send_message(message)

    def _set_state(self, row_id: int, state: str, error: str | None) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE outbox_events SET state = ?, sent_at = CASE WHEN ? = 'sent' "
                "THEN CURRENT_TIMESTAMP ELSE sent_at END, last_error = ? WHERE id = ?",
                (state, state, error, row_id),
            )
            conn.commit()
        finally:
            conn.close()

    def _record_failure(self, row_id: int, error: str) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT attempts FROM outbox_events WHERE id = ?", (row_id,)
            ).fetchone()
            if row is None:
                return
            state = "failed" if row[0] >= 5 else "pending"
            conn.execute(
                "UPDATE outbox_events SET state = ?, last_error = ? WHERE id = ?",
                (state, error[:1000], row_id),
            )
            conn.commit()
        finally:
            conn.close()

    def run(self, poll_seconds: int, stop_event=None) -> None:
        if poll_seconds < 1:
            raise ValueError("poll_seconds must be positive")
        while stop_event is None or not stop_event.is_set():
            self.process_pending()
            if stop_event is None:
                time.sleep(poll_seconds)
            elif stop_event.wait(poll_seconds):
                break
