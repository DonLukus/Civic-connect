import json
import logging
import os
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from typing import ClassVar

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

    # FR-009: the events that notify a Requester, and the wording for each.
    SUBJECTS: ClassVar[dict[str, str]] = {
        "RequestAccepted": "accepted",
        "RequestRejected": "rejected",
        "RequestResolved": "resolved",
        "CommentAdded": "has a new comment",
    }

    @staticmethod
    def build_message(event_type: str, request_id: int, status: str, payload: dict) -> str:
        if event_type == "RequestAccepted":
            return f"Request #{request_id} has been accepted. Current status: {status}."
        if event_type == "RequestRejected":
            return f"Request #{request_id} has been rejected. Reason: {payload.get('reason', '')}"
        if event_type == "RequestResolved":
            return (f"Request #{request_id} has been resolved. "
                    f"Resolution note: {payload.get('note', '')}")
        if event_type == "CommentAdded":
            return f"A comment was added to request #{request_id}: {payload.get('comment', '')}"
        raise ValueError(f"Unsupported notification event: {event_type}")

    def _deliver_password_reset(self, row_id: int) -> None:
        """FR-004: email the one-time reset link, then scrub the token from the stored event."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT u.email, e.payload_json, e.correlation_id FROM outbox_events e "
                "JOIN users u ON u.id = e.aggregate_id "
                "WHERE e.id = ? AND e.aggregate_type = 'PasswordReset'", (row_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise ValueError("Outbox event has no matching account")
        email, raw, correlation_id = row
        token = json.loads(raw or "{}").get("token")
        if not token:
            raise ValueError("This reset event has no token left to send")
        base = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
        text = (f"Use this link to set a new CivicConnect password: {base}/reset-password/{token}\n"
                "It works once and expires in 60 minutes. If you did not ask for it, ignore this email.")
        self._send_plain_email(email, "Set your CivicConnect password", text, correlation_id)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("UPDATE outbox_events SET payload_json = '{}' WHERE id = ?", (row_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _smtp_send(message: EmailMessage) -> None:
        host = os.environ.get("EMAIL_SMTP_HOST")
        if not host or not os.environ.get("EMAIL_FROM_ADDRESS"):
            raise RuntimeError("EMAIL_SMTP_HOST and EMAIL_FROM_ADDRESS must be configured")
        port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            username = os.environ.get("EMAIL_SMTP_USERNAME")
            password = os.environ.get("EMAIL_SMTP_PASSWORD")
            if username:
                if not password:
                    raise RuntimeError("EMAIL_SMTP_PASSWORD is required with EMAIL_SMTP_USERNAME")
                smtp.login(username, password)
            smtp.send_message(message)

    @classmethod
    def _send_plain_email(cls, recipient: str, subject: str, text: str, correlation_id: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = os.environ.get("EMAIL_FROM_ADDRESS", "")
        message["To"] = recipient
        message["X-Correlation-ID"] = correlation_id
        message.set_content(text)
        cls._smtp_send(message)

    def _deliver(self, row_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            kind = conn.execute(
                "SELECT aggregate_type FROM outbox_events WHERE id = ?", (row_id,)).fetchone()
        finally:
            conn.close()
        if kind and kind[0] == "PasswordReset":
            self._deliver_password_reset(row_id)
            return
        conn = sqlite3.connect(self.db_path)
        try:
            event = conn.execute(
                """
                SELECT e.event_type, e.aggregate_id, e.correlation_id, r.requester_id,
                       u.email, r.status, e.payload_json
                FROM outbox_events AS e
                JOIN requests AS r ON r.id = e.aggregate_id
                JOIN users AS u ON u.id = r.requester_id
                WHERE e.id = ? AND e.aggregate_type = 'Request'
                """,
                (row_id,),
            ).fetchone()
            if event is None:
                raise ValueError("Outbox event has no matching request and requester")

            event_type, request_id, correlation_id, requester_id, email, status, raw = event
            message = self.build_message(event_type, request_id, status, json.loads(raw or "{}"))
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

        self._send_email(email, request_id, message, correlation_id,
                         self.SUBJECTS.get(event_type, "updated"))

    @staticmethod
    def _send_email(recipient: str, request_id: int, message_text: str, correlation_id: str,
                    subject_suffix: str = "updated") -> None:
        host = os.environ.get("EMAIL_SMTP_HOST")
        sender = os.environ.get("EMAIL_FROM_ADDRESS")
        if not host or not sender:
            raise RuntimeError("EMAIL_SMTP_HOST and EMAIL_FROM_ADDRESS must be configured")
        port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
        message = EmailMessage()
        message["Subject"] = f"CivicConnect request #{request_id} {subject_suffix}"
        message["From"] = sender
        message["To"] = recipient
        message["X-Correlation-ID"] = correlation_id
        message.set_content(f"{message_text}\n\nReference: #{request_id}")

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
