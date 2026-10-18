-- CivicConnect M2 persistence schema prototype
-- SQLite-compatible DDL

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    target_resolution_hours INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL,
    assignee_id INTEGER,
    category_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('New','Accepted','In Progress','On Hold','Resolved','Closed','Rejected')),
    version INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accepted_at TEXT,
    FOREIGN KEY (requester_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE request_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    actor_user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    previous_assignee_id INTEGER,
    new_assignee_id INTEGER,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    correlation_id TEXT NOT NULL,
    payload_json TEXT,
    FOREIGN KEY (request_id) REFERENCES requests(id),
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
);

-- FR-025 / NFR-006: audit rows can be added but never changed or removed, even by a bug or
-- a hand-written query run through the application's connection.
CREATE TRIGGER IF NOT EXISTS request_audit_no_update
BEFORE UPDATE ON request_audit
BEGIN
    SELECT RAISE(ABORT, 'request_audit is append-only (FR-025, NFR-006)');
END;

CREATE TRIGGER IF NOT EXISTS request_audit_no_delete
BEFORE DELETE ON request_audit
BEGIN
    SELECT RAISE(ABORT, 'request_audit is append-only (FR-025, NFR-006)');
END;

-- INSERT OR REPLACE / REPLACE delete the old row without firing the delete trigger (SQLite only
-- fires it with PRAGMA recursive_triggers, which is off by default), so reusing an existing id
-- is refused up front.
CREATE TRIGGER IF NOT EXISTS request_audit_no_replace
BEFORE INSERT ON request_audit
WHEN NEW.id IS NOT NULL AND EXISTS (SELECT 1 FROM request_audit WHERE id = NEW.id)
BEGIN
    SELECT RAISE(ABORT, 'request_audit is append-only (FR-025, NFR-006)');
END;

CREATE TABLE outbox_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_type TEXT NOT NULL,
    aggregate_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('pending','sending','sent','failed')) DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TEXT
);

CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_assignee ON requests(assignee_id);
CREATE INDEX idx_audit_request ON request_audit(request_id);
CREATE INDEX idx_outbox_state ON outbox_events(state, created_at);

CREATE TABLE request_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outbox_event_id INTEGER NOT NULL UNIQUE,
    request_id INTEGER NOT NULL,
    requester_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TEXT,
    FOREIGN KEY (request_id) REFERENCES requests(id),
    FOREIGN KEY (requester_id) REFERENCES users(id)
);

CREATE INDEX idx_request_notifications_requester
    ON request_notifications(requester_id, created_at);
