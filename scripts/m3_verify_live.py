"""Live HTTP system journeys and load evidence against isolated M3 staging.

No Flask test client, no external email; SMTP is captured by m3_staging locally.
Run load before journeys so its dataset is exactly 500 records.
"""

import argparse
import http.cookiejar
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from scripts.m3_staging import CONFIG, LOCAL

BASE = "http://127.0.0.1:5083"
EVIDENCE = Path("docs/release/evidence/2026-10-16")


class BrowserHTTP:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(self, path):
        with self.opener.open(BASE + path, timeout=20) as response:
            return response.url, response.read().decode()

    def post(self, path, data):
        with self.opener.open(BASE + path, urllib.parse.urlencode(data).encode(), timeout=20) as response:
            return response.url, response.read().decode()

    def login(self, account):
        _, page = self.get("/login")
        return self.post("/login", {"email": account["email"], "password": account["password"],
                                    "csrf_token": token(page)})


def token(page):
    match = re.search(r'name="csrf_token" value="([^"]+)"', page)
    assert match, "A rendered state-changing form has no usable CSRF token"
    return match.group(1)


def save(name, report):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    report["observed_at_utc"] = datetime.now(UTC).isoformat()
    report["environment"] = "Windows local simulated staging; Waitress, loopback HTTP, SQLite; local SMTP STARTTLS sink"
    (EVIDENCE / name).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


def load_test(seconds):
    from performance.load_test_staff_queue import run
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    fixture = json.loads((LOCAL / "performance-fixture.json").read_text())
    accounts = [a for a in config["accounts"] if a["role"] == "Staff"]
    with sqlite3.connect(config["env"]["DATABASE_URL"]) as db:
        dataset_size = db.execute("SELECT count(*) FROM requests").fetchone()[0]
        ids = [r[0] for r in db.execute("SELECT id FROM requests WHERE status='New' ORDER BY id")]
    assert dataset_size == 500 and ids == fixture["expected_ids"], "Fixture changed; do not claim 500-record evidence"
    started = time.monotonic()
    summary = run(BASE, "", "", "New", 10, seconds, 500, accounts=accounts, expected_ids=ids)
    total, successes = len(summary.results), len(summary.successes)
    p95 = summary.p95_seconds()
    save("performance.json" if seconds >= 300 else "performance-smoke.json", {
        "scenario": "NFR-001 filtered Staff queue", "distinct_staff_accounts": len(accounts),
        "dataset_size": dataset_size, "expected_filtered_rows": 500, "status_filter": "New",
        "duration_seconds": seconds, "total_wall_seconds_including_login": time.monotonic() - started,
        "total_requests": total, "successful_requests": successes, "failed_requests": total - successes,
        "p95_seconds_nearest_rank": p95, "target_seconds": 2.0,
        "qualifies_as_nfr001_run": seconds >= 300,
        "pass": bool(seconds >= 300 and total > 0 and successes == total and p95 <= 2),
        "limits": "Client-observed HTTP elapsed time includes server template generation and transfer, but not browser rendering; local machine only; no production-scale or uptime claim.",
    })


def journeys():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    accounts = config["accounts"]
    requester = next(a for a in accounts if a["role"] == "Requester")
    other = [a for a in accounts if a["role"] == "Requester"][1]
    staff = next(a for a in accounts if a["role"] == "Staff")
    citizen, worker = BrowserHTTP(), BrowserHTTP()
    _, page = citizen.login(requester)
    assert "Submit a service request" in page
    csrf = token(page)
    category = re.search(r'<option value="(\d+)"', page).group(1)
    url, receipt = citizen.post("/requests", {"csrf_token": csrf, "title": "M3 live system check",
        "description": "Synthetic end-to-end verification", "location": "Test area", "category_id": category})
    request_id = int(re.search(r"/requests/(\d+)/submitted", url).group(1))
    assert f"#{request_id}" in receipt
    _, page = citizen.get("/requests")
    assert f"/requests/{request_id}" in page
    # Regression: the shared logout form works from list pages too.
    _, page = citizen.post("/logout", {"csrf_token": token(page)})
    assert "Sign in" in page
    citizen.login(requester)
    stranger = BrowserHTTP()
    stranger.login(other)
    try:
        stranger.get(f"/requests/{request_id}")
        raise AssertionError("Another requester saw the record")
    except urllib.error.HTTPError as error:
        assert error.code == 404

    worker.login(staff)
    _, page = worker.get("/staff/queue?status=New")
    assert f"/requests/{request_id}" in page
    _, detail = worker.get(f"/requests/{request_id}")
    assert requester["email"] not in detail
    version = re.search(r'name="expected_version" value="(\d+)"', detail).group(1)
    accepted_at = time.monotonic()
    _, detail = worker.post(f"/staff/requests/{request_id}/accept",
                           {"csrf_token": token(detail), "expected_version": version})
    assert "Accepted" in detail
    limit = time.monotonic() + 30
    while True:
        _, notifications = citizen.get("/notifications")
        mailbox = LOCAL / "mailbox.jsonl"
        mail = mailbox.read_text(encoding="utf-8") if mailbox.exists() else ""
        if f"#{request_id}" in notifications and f"#{request_id}" in mail:
            break
        if time.monotonic() > limit:
            raise AssertionError("In-app and SMTP-captured notification not both observed within 30 seconds")
        time.sleep(0.25)
    _, detail = citizen.get(f"/requests/{request_id}")
    assert "Accepted" in detail
    with sqlite3.connect(config["env"]["DATABASE_URL"]) as db:
        audit_count = db.execute("SELECT count(*) FROM request_audit WHERE request_id=?", (request_id,)).fetchone()[0]
        assert audit_count == 2
        hashes = [row[0] for row in db.execute("SELECT password_hash FROM users")]
        assert all(h.startswith("$2b$") and int(h.split("$")[2]) >= 10 for h in hashes)
    (LOCAL / "restart-reference.json").write_text(json.dumps({"request_id": request_id}), encoding="utf-8")
    save("live-system-journeys.json", {
        "pass": True, "request_id": request_id,
        "journey_1": "Requester real HTTP login -> submit -> receipt -> list -> logout -> login -> own detail; other requester refused",
        "journey_2": "Staff real HTTP login -> status-filtered queue -> detail -> accept -> requester status + in-app + local SMTP-captured email",
        "notification_seconds": time.monotonic() - accepted_at, "audit_rows": audit_count,
        "credential_storage": "All 14 staged accounts bcrypt cost >=10, inspected without disclosing hashes/passwords",
        "limits": "Live HTTP system tests, not browser automation. Email transported to local STARTTLS sink, not an external inbox. Audit inserts checked, not DBA-proof immutability.",
    })


def restart_check():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    reference = json.loads((LOCAL / "restart-reference.json").read_text())
    client = BrowserHTTP()
    client.login(next(a for a in config["accounts"] if a["role"] == "Requester"))
    _, page = client.get(f"/requests/{reference['request_id']}")
    assert "Accepted" in page and f"#{reference['request_id']}" in page
    save("process-restart.json", {"pass": True, **reference,
        "claim": "Previously accepted request retrievable after local staging process stop/start using same SQLite file",
        "limits": "Does not verify Render redeploy persistence or code/schema rollback."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["load", "journeys", "restart"])
    parser.add_argument("--seconds", type=int, default=300)
    args = parser.parse_args()
    if args.action == "load":
        load_test(args.seconds)
    elif args.action == "journeys":
        journeys()
    else:
        restart_check()
