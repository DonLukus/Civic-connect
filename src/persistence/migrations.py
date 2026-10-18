"""Versioned, idempotent schema migrations.

`schema.sql` is the original (M3) schema. Everything added since lives here as numbered migrations so
that a database created at ANY earlier point (a fresh file, the staging database, a deployed copy) is
brought to the current shape the same way. Applied versions are recorded in `schema_migrations`, and
every step also checks what already exists, so running it twice, or on a database built another way,
is harmless. Services call `ensure_schema()` when they are constructed.

To add a change: append a new (version, name, function) to MIGRATIONS. Never edit or reorder an
applied one.
"""

import sqlite3
from contextlib import closing

APPEND_ONLY = "append-only (FR-025, NFR-006)"


def _has_column(conn, table: str, column: str) -> bool:
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def _append_only_triggers(table: str) -> list[str]:
    msg = f"{table} is {APPEND_ONLY}"
    abort = f"BEGIN SELECT RAISE(ABORT, '{msg}'); END"
    return [
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} {abort}",
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} {abort}",
        (
            f"CREATE TRIGGER IF NOT EXISTS {table}_no_replace BEFORE INSERT ON {table} "
            f"WHEN NEW.id IS NOT NULL AND EXISTS (SELECT 1 FROM {table} WHERE id = NEW.id) {abort}"
        ),
    ]


def _m4_workflow(conn) -> None:
    """Resolution/rejection fields, comments, administration audit and password reset tokens."""
    for column in ("resolution_note TEXT", "resolution_by INTEGER", "resolution_at TEXT",
                   "rejection_reason TEXT"):
        if not _has_column(conn, "requests", column.split()[0]):
            conn.execute(f"ALTER TABLE requests ADD COLUMN {column}")
    statements = [
        # FR-010: comment thread, stored with author and timestamp.
        """CREATE TABLE IF NOT EXISTS request_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES requests(id),
            FOREIGN KEY (author_id) REFERENCES users(id)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_comments_request ON request_comments(request_id, id)",
        # FR-001 / FR-024: account creation, role change and (de)activation are audited. The
        # request audit table cannot hold these because it requires a request.
        """CREATE TABLE IF NOT EXISTS admin_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            target_user_id INTEGER,
            previous_value TEXT,
            new_value TEXT,
            changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (actor_user_id) REFERENCES users(id),
            FOREIGN KEY (target_user_id) REFERENCES users(id)
        )""",
        *_append_only_triggers("admin_audit"),
        # FR-004: single-use, expiring reset tokens. Only a hash of the token is stored.
        """CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_requests_category ON requests(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at)",
    ]
    for statement in statements:
        conn.execute(statement)


MIGRATIONS = [
    (1, "m3_baseline", lambda conn: None),  # the schema.sql shape; recorded so the history is complete
    (2, "m4_workflow", _m4_workflow),
]


def ensure_schema(db_path: str) -> None:
    """Apply any migration this database has not had yet. Cheap when already up to date."""
    with closing(sqlite3.connect(db_path, timeout=10)) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
            "applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        pending = [m for m in MIGRATIONS if m[0] not in applied]
        if not pending:
            return
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='requests'"
        ).fetchone() is None:
            return  # no base schema yet; bootstrap applies schema.sql first, then calls us again
        for version, name, fn in pending:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if version not in {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}:
                    fn(conn)
                    conn.execute(
                        "INSERT INTO schema_migrations(version, name) VALUES (?, ?)", (version, name)
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
