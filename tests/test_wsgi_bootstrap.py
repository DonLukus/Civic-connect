"""Verify the deployable WSGI entrypoint, not just the app factory."""

import importlib
import sqlite3


def test_wsgi_login_save_and_repeat_bootstrap(tmp_path, monkeypatch):
    db_path = tmp_path / "civicconnect.sqlite"
    monkeypatch.setenv("DATABASE_URL", str(db_path))
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BOOTSTRAP_REQUESTER_EMAIL", "poc@example.test")
    monkeypatch.setenv("BOOTSTRAP_REQUESTER_PASSWORD", "pw")

    import wsgi
    importlib.reload(wsgi)
    client = wsgi.app.test_client()

    assert client.get("/requests/new").status_code == 302
    assert client.get("/login").status_code == 200
    with client.session_transaction() as sess:
        csrf = sess["_csrf_token"]
    assert client.post("/login", data={
        "email": "poc@example.test", "password": "pw", "csrf_token": csrf,
    }).status_code == 302
    with client.session_transaction() as sess:
        csrf = sess["_csrf_token"]
    assert client.get("/requests/new").status_code == 200
    response = client.post("/requests", data={
        "title": "Broken light", "description": "Outside library", "location": "Campus",
        "category_id": "1", "csrf_token": csrf,
    })
    assert response.status_code == 302

    wsgi.bootstrap(str(db_path))
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 1
    finally:
        conn.close()
