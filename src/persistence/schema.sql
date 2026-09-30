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

CREATE TABLE outbox_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_type TEXT NOT NULL,
    aggregate_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('pending','sent','failed')) DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TEXT
);

CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_assignee ON requests(assignee_id);
CREATE INDEX idx_audit_request ON request_audit(request_id);
CREATE INDEX idx_outbox_state ON outbox_events(state, created_at);
