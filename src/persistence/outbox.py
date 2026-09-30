import sqlite3


class OutboxProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def process_pending(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, event_type, payload_json, attempts FROM outbox_events WHERE state = 'pending' ORDER BY created_at",
            ).fetchall()

            for row_id, event_type, payload_json, attempts in rows:
                try:
                    # Placeholder for actual email/in-app transport.
                    # In production this would call the notification provider.
                    _ = (event_type, payload_json)
                    conn.execute(
                        "UPDATE outbox_events SET state = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (row_id,),
                    )
                except Exception as exc:  # pragma: no cover
                    conn.execute(
                        "UPDATE outbox_events SET state = 'failed', attempts = attempts + 1, last_error = ? WHERE id = ?",
                        (str(exc), row_id),
                    )
