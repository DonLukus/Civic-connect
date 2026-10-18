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
from email import message_from_string
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
    form = {"csrf_token": csrf, "title": "M3 live system check",
            "description": "Synthetic end-to-end verification", "location": "Test area", "category_id": category}
    url, receipt = citizen.post("/requests", form)
    if "may already be reported" in receipt:
        # FR-026: the fixture already holds open requests in this category and place, so the
        # Requester is asked to confirm. Confirming is the behaviour under test here.
        url, receipt = citizen.post("/requests", {**form, "confirm_duplicate": "1"})
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
        "credential_storage": f"All {len(hashes)} staged accounts bcrypt cost >=10, inspected without disclosing hashes/passwords",
        "limits": "Live HTTP system tests, not browser automation. Email transported to local STARTTLS sink, not an external inbox. Audit inserts checked, not DBA-proof immutability.",
    })


def _option_value(page, label):
    """Value of the <option> whose visible text is `label` (e.g. a staff member's email)."""
    match = re.search(r'<option value="(\d+)"[^>]*>\s*' + re.escape(label) + r"\s*</option>", page)
    assert match, f"No option labelled {label!r} on the page"
    return match.group(1)


def _decoded_mail_to(mailbox, recipient):
    """Decoded text bodies of every captured email to `recipient` (undoes quoted-printable wrapping)."""
    if not mailbox.exists():
        return ""
    bodies = []
    for line in mailbox.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if recipient in record["recipients"]:
            message = message_from_string(record["message"])
            bodies.append(message.get_payload(decode=True).decode("utf-8", errors="replace"))
    return "\n".join(bodies)


def _wait_for(check, what, seconds=30):
    limit = time.monotonic() + seconds
    while not check():
        if time.monotonic() > limit:
            raise AssertionError(f"Not observed within {seconds} seconds: {what}")
        time.sleep(0.25)


def workflow():
    """The M4 functional journey over real HTTP: submit, assign, work, comment, resolve, close,
    notifications, administration, dashboard, CSV export, password reset and deactivation."""
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    accounts = config["accounts"]
    pick = {role: next(a for a in accounts if a["role"] == role) for role in
            ("Requester", "Staff", "Manager", "Administrator")}
    mailbox = LOCAL / "mailbox.jsonl"
    mail = lambda: mailbox.read_text(encoding="utf-8") if mailbox.exists() else ""
    title = f"M4 workflow check {int(time.time())}"
    citizen, worker, manager, admin = BrowserHTTP(), BrowserHTTP(), BrowserHTTP(), BrowserHTTP()
    steps = []

    # 1. Requester submits (confirming the duplicate prompt, which the fixture triggers).
    _, page = citizen.login(pick["Requester"])
    form = {"csrf_token": token(page), "title": title, "description": "Synthetic workflow verification",
            "location": "Test area", "category_id": re.search(r'<option value="(\d+)"', page).group(1)}
    url, receipt = citizen.post("/requests", form)
    if "may already be reported" in receipt:
        url, receipt = citizen.post("/requests", {**form, "confirm_duplicate": "1"})
    request_id = int(re.search(r"/requests/(\d+)/submitted", url).group(1))
    steps.append("Requester submitted (duplicate prompt confirmed)")

    # 2. Manager finds it by keyword, assigns it to a Staff member (New -> Accepted).
    manager.login(pick["Manager"])
    _, listing = manager.get("/manager/requests?q=" + urllib.parse.quote(title))
    assert f"/requests/{request_id}" in listing
    _, detail = manager.get(f"/requests/{request_id}")
    version = re.search(r'name="expected_version" value="(\d+)"', detail).group(1)
    staff_id = _option_value(detail, pick["Staff"]["email"])
    _, detail = manager.post(f"/requests/{request_id}/assign", {
        "csrf_token": token(detail), "expected_version": version, "assignee_id": staff_id})
    assert "Accepted" in detail
    steps.append("Manager assigned it to Staff (Accepted)")

    # 3. Staff work it: In Progress, comment, a refused Resolved without a note, then Resolved with one.
    worker.login(pick["Staff"])

    def staff_status(target, note=""):
        _, page = worker.get(f"/requests/{request_id}")
        data = {"csrf_token": token(page), "target_status": target, "note": note,
                "expected_version": re.search(r'name="expected_version" value="(\d+)"', page).group(1)}
        try:
            return worker.post(f"/requests/{request_id}/status", data)[1]
        except urllib.error.HTTPError as error:
            return error

    assert "In Progress" in staff_status("In Progress")
    _, page = worker.get(f"/requests/{request_id}")
    _, page = worker.post(f"/requests/{request_id}/comments", {"csrf_token": token(page), "body": "Crew booked for Friday"})
    assert "Crew booked for Friday" in page
    refused = staff_status("Resolved", "")
    assert getattr(refused, "code", None) == 400, "Resolving without a note must be refused"
    assert "Resolved" in staff_status("Resolved", "Replaced the valve")
    steps.append("Staff: In Progress, comment, Resolved refused without a note, Resolved with a note")

    # 4. Staff cannot close; the Manager can.
    refused = staff_status("Closed")
    assert getattr(refused, "code", None) == 403, "Staff must not be able to close"
    _, page = manager.get(f"/requests/{request_id}")
    _, page = manager.post(f"/requests/{request_id}/status", {
        "csrf_token": token(page), "target_status": "Closed", "note": "",
        "expected_version": re.search(r'name="expected_version" value="(\d+)"', page).group(1)})
    assert "Closed" in page
    steps.append("Staff refused (403) closing; Manager closed")

    # 5. Requester sees the outcome, comments back; notifications arrive in-app and by email.
    _, page = citizen.get(f"/requests/{request_id}")
    assert "Replaced the valve" in page and "Closed" in page and "Crew booked for Friday" in page
    _wait_for(lambda: all(text in citizen.get("/notifications")[1] for text in ("resolved", "comment was added")),
              "in-app notifications for resolved and comment")
    _wait_for(lambda: "Replaced the valve" in mail() and "Crew booked for Friday" in mail(),
              "emails carrying the resolution note and the comment")
    steps.append("Requester saw note, status and comment; in-app and email notifications observed")

    with sqlite3.connect(config["env"]["DATABASE_URL"]) as db:
        audit = db.execute("SELECT action_type, previous_status, new_status FROM request_audit "
                           "WHERE request_id=? ORDER BY id", (request_id,)).fetchall()
        comments = db.execute("SELECT count(*) FROM request_comments WHERE request_id=?", (request_id,)).fetchone()[0]
        total = db.execute("SELECT count(*) FROM requests").fetchone()[0]
    assert [a[2] for a in audit if a[2]] == ["New", "Accepted", "In Progress", "Resolved", "Closed"], audit
    assert comments == 1

    # 6. Manager dashboard and CSV agree with the stored records.
    _, dash = manager.get("/manager/dashboard")
    assert re.search(rf'stat__n">{total}</span><span class="stat__l">Total requests', dash), "dashboard total != stored count"
    _, csv_text = manager.get("/manager/requests.csv?q=" + urllib.parse.quote(title))
    lines = [line for line in csv_text.splitlines() if line]
    assert len(lines) == 2 and lines[1].split(",")[0] == str(request_id)
    steps.append(f"Dashboard total {total} equals stored requests; CSV has header plus 1 row")

    # 7. Administrator: create a Staff account, new category; the person sets a password from the one-time
    #    link, resets it through the emailed link, signs in, and is then deactivated and locked out.
    admin.login(pick["Administrator"])
    _, page = admin.get("/admin/users")
    email = f"m4-staff-{int(time.time())}@example.test"
    _, page = admin.post("/admin/users", {"csrf_token": token(page), "email": email, "role": "Staff"})
    setup = re.search(r"/reset-password/([\w-]+)", page).group(1)
    newbie = BrowserHTTP()
    _, form_page = newbie.get(f"/reset-password/{setup}")
    first = "First-password-123"
    newbie.post(f"/reset-password/{setup}", {"csrf_token": token(form_page), "password": first, "confirm_password": first})
    assert "invalid or has expired" in _get_error(newbie, f"/reset-password/{setup}"), "setup link must be single use"
    _, page = newbie.login({"email": email, "password": first})
    assert "Staff queue" in page
    forgot = BrowserHTTP()
    _, page = forgot.get("/forgot-password")
    _, page = forgot.post("/forgot-password", {"csrf_token": token(page), "email": email})
    assert "we have sent a link" in page
    _wait_for(lambda: "reset-password/" in _decoded_mail_to(mailbox, email), "reset email")
    reset_token = re.search(r"reset-password/([\w-]+)", _decoded_mail_to(mailbox, email)).group(1)
    _, form_page = forgot.get(f"/reset-password/{reset_token}")
    second = "Second-password-456"
    forgot.post(f"/reset-password/{reset_token}", {"csrf_token": token(form_page), "password": second, "confirm_password": second})
    fresh = BrowserHTTP()
    _, page = fresh.login({"email": email, "password": second})
    assert "Staff queue" in page
    _, page = admin.get("/admin/users")
    with sqlite3.connect(config["env"]["DATABASE_URL"]) as db:
        new_id = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
    admin.post(f"/admin/users/{new_id}/active", {"csrf_token": token(page), "active": "0"})
    locked = BrowserHTTP()
    _, page = locked.login({"email": email, "password": second})
    assert "Invalid email or password" in page
    steps.append("Administrator created a Staff account; setup link single use; reset by emailed link; deactivation blocks sign-in")
    _, page = admin.get("/admin/categories")
    name = f"M4 category {int(time.time())}"
    _, page = admin.post("/admin/categories", {"csrf_token": token(page), "name": name, "target_hours": "36"})
    assert name in page
    with sqlite3.connect(config["env"]["DATABASE_URL"]) as db:
        admin_rows = [r[0] for r in db.execute("SELECT action_type FROM admin_audit ORDER BY id")]
    assert {"create_user", "deactivate_user", "create_category"} <= set(admin_rows), admin_rows
    steps.append("Administrator added a category; administration audit rows present")

    save("workflow-journey.json", {
        "pass": True, "request_id": request_id, "steps": steps,
        "request_audit_statuses": [a[2] for a in audit if a[2]],
        "limits": "Live HTTP system test, not browser automation. Email goes to the local STARTTLS sink, not an "
                  "external inbox. Synthetic accounts only.",
    })


def _get_error(client, path):
    """Body of a page (including an error page) without raising on a 4xx."""
    try:
        return client.get(path)[1]
    except urllib.error.HTTPError as error:
        return error.read().decode()


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
    parser.add_argument("action", choices=["load", "journeys", "workflow", "restart"])
    parser.add_argument("--seconds", type=int, default=300)
    args = parser.parse_args()
    if args.action == "load":
        load_test(args.seconds)
    elif args.action == "journeys":
        journeys()
    elif args.action == "workflow":
        workflow()
    else:
        restart_check()
