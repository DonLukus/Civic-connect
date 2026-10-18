"""Verify an online SQLite backup and a separate restore without altering staging."""

import json
import sqlite3

from scripts.m3_staging import CONFIG, LOCAL
from scripts.m3_verify_live import save

# Everything the application stores. Tables added by later migrations are included when present.
TABLES = ("users", "categories", "requests", "request_audit", "outbox_events", "request_notifications",
          "request_comments", "admin_audit", "password_resets", "schema_migrations")


def run():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    reference = json.loads((LOCAL / "restart-reference.json").read_text())
    backup_path, restored_path = LOCAL / "backup.sqlite", LOCAL / "restored.sqlite"
    with sqlite3.connect(config["env"]["DATABASE_URL"]) as source:
        present = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        tables = [table for table in TABLES if table in present]
        source_counts = [source.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables]
        with sqlite3.connect(backup_path) as backup:
            source.backup(backup)
    with sqlite3.connect(backup_path) as backup, sqlite3.connect(restored_path) as restored:
        backup.backup(restored)
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        restored_counts = [restored.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                           for table in tables]
        assert source_counts == restored_counts
        assert restored.execute("SELECT status FROM requests WHERE id=?",
                                (reference["request_id"],)).fetchone()[0] == "Accepted"
    save("backup-restore.json", {"pass": True, "tables": tables,
         "source_and_restored_counts": dict(zip(tables, source_counts, strict=True)), "request_id": reference["request_id"],
         "method": "SQLite online Connection.backup to backup file, then separate restored database; integrity_check and counts",
         "limits": "One local recovery drill. No daily schedule, retention, cloud recovery or schema/code rollback claim."})


if __name__ == "__main__":
    run()
