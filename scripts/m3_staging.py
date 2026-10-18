"""Isolated, loopback-only M3 staging; never uses developer/Render databases.

Run: python -m scripts.m3_staging prepare
Then: python -m scripts.m3_staging serve
Synthetic credentials and TLS keys stay in ignored .m3-local, not in evidence.
"""

import argparse
import json
import os
import secrets
import sqlite3
import ssl
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".m3-local"
CONFIG = LOCAL / "config.json"


def configure():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    os.environ.update(config["env"])
    return config


def prepare():
    if CONFIG.exists():
        raise SystemExit("Existing staging data preserved. Use serve; do not reseed evidence.")
    LOCAL.mkdir(exist_ok=True)
    accounts = [
        {"email": f"{role.lower()}-{i}@example.test", "role": role,
         "password": secrets.token_urlsafe(24)}
        for role, count in (("Requester", 2), ("Staff", 10), ("Manager", 1), ("Administrator", 1))
        for i in range(count)
    ]
    env = {
        "SECRET_KEY": secrets.token_urlsafe(48),
        "DATABASE_URL": str(LOCAL / "staging.sqlite"),
        "SESSION_COOKIE_SECURE": "false",  # Loopback HTTP only; not a public deployment.
        "PASSWORD_HASH_COST": "12",
        "OUTBOX_WORKER_ENABLED": "false",
        "OUTBOX_WORKER_POLL_SECONDS": "1",
        "APP_BASE_URL": "http://127.0.0.1:5083",
        "EMAIL_SMTP_HOST": "127.0.0.1",
        "EMAIL_SMTP_PORT": "8025",
        "EMAIL_FROM_ADDRESS": "civicconnect@example.test",
    }
    CONFIG.write_text(json.dumps({"env": env, "accounts": accounts}, indent=2), encoding="utf-8")
    configure()
    import bcrypt

    from src.persistence.request_service import RequestService
    from wsgi import bootstrap

    bootstrap(env["DATABASE_URL"])
    with sqlite3.connect(env["DATABASE_URL"]) as db:
        for account in accounts:
            digest = bcrypt.hashpw(account["password"].encode(), bcrypt.gensalt(rounds=12)).decode()
            db.execute("INSERT INTO users(email,password_hash,role) VALUES (?,?,?)",
                       (account["email"], digest, account["role"]))
        requester = db.execute("SELECT id FROM users WHERE email=?", (accounts[0]["email"],)).fetchone()[0]
        category = db.execute("SELECT id FROM categories ORDER BY id LIMIT 1").fetchone()[0]
    service = RequestService(env["DATABASE_URL"])
    ids = [service.create_request(requester, category, f"Load fixture {i + 1}",
                                  "Synthetic M3 performance record", "Test area") for i in range(500)]
    (LOCAL / "performance-fixture.json").write_text(json.dumps({
        "dataset_size": 500, "status_filter": "New", "expected_ids": ids,
    }, indent=2), encoding="utf-8")
    openssl = Path("C:/Program Files/Git/mingw64/bin/openssl.exe")
    executable = str(openssl) if openssl.exists() else "openssl"
    subprocess.run([executable, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                    "-keyout", str(LOCAL / "smtp.key"), "-out", str(LOCAL / "smtp.crt"),
                    "-days", "7", "-subj", "/CN=localhost"], check=True, capture_output=True)
    print("Prepared 500 synthetic requests and 14 accounts. Private data: .m3-local (ignored).")


class CaptureMail:
    async def handle_DATA(self, server, session, envelope):
        if any(not recipient.endswith("@example.test") for recipient in envelope.rcpt_tos):
            return "550 Synthetic example.test recipients only"
        with (LOCAL / "mailbox.jsonl").open("a", encoding="utf-8") as output:
            output.write(json.dumps({"recipients": envelope.rcpt_tos,
                                     "message": envelope.content.decode("utf-8", errors="replace")}) + "\n")
        return "250 Captured locally; no external delivery"


def serve():
    configure()
    from aiosmtpd.controller import Controller
    from waitress import serve as serve_wsgi

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(LOCAL / "smtp.crt", LOCAL / "smtp.key")
    smtp = Controller(CaptureMail(), hostname="127.0.0.1", port=8025,
                      tls_context=context, require_starttls=True)
    smtp.start()
    os.environ["OUTBOX_WORKER_ENABLED"] = "true"
    import wsgi

    print("M3 staging: http://127.0.0.1:5083/login; SMTP captured locally on 8025", flush=True)
    try:
        serve_wsgi(wsgi.app, host="127.0.0.1", port=5083, threads=12)
    finally:
        smtp.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "serve"])
    arguments = parser.parse_args()
    if arguments.action == "prepare":
        prepare()
    else:
        serve()
