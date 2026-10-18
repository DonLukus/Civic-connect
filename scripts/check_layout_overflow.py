"""Check that user-entered long text never makes a page scroll sideways (phone and desktop).

Renders the real templates and stylesheet (requester, staff, manager and administrator pages) with a
240-character unbroken title/description, an 80-character category name and a long email, plus a normal title, then measures the document's scrollWidth against its clientWidth in headless
Chrome or Edge at 390 px (phone) and 1100 px (desktop). Exit code 1 on any overflow.

    CHROME=/path/to/chromium-browser   (optional; common install paths are tried)
    python -m scripts.check_layout_overflow

This is an automated layout check on synthetic data. It is not an accessibility audit or a usability test.
"""

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from werkzeug.security import generate_password_hash

from src.persistence.request_service import RequestService
from src.web.app import create_app

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = (390, 1100)
CANDIDATES = (
    os.environ.get("CHROME", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
)


def find_browser():
    for path in CANDIDATES:
        if path and Path(path).exists():
            return path
    raise SystemExit("No Chromium browser found; set the CHROME environment variable.")


def build_pages(work: Path) -> dict:
    db = work / "layout.sqlite"
    conn = sqlite3.connect(db)
    conn.executescript((ROOT / "src/persistence/schema.sql").read_text(encoding="utf-8"))
    digest = generate_password_hash("pw")
    for email, role in (("requester@example.test", "Requester"), ("staff@example.test", "Staff"),
                        ("manager@example.test", "Manager"), ("a" * 70 + "@example.test", "Administrator")):
        conn.execute("INSERT INTO users(email,password_hash,role,is_active) VALUES(?,?,?,1)", (email, digest, role))
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES('Utilities',48,1)")
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES(?,48,1)", ("D" * 80,))
    conn.commit()
    conn.close()
    service = RequestService(str(db))
    service.create_request(1, 1, "Streetlight not working", "Normal description", "Main Rd")
    service.create_request(1, 1, "A" * 240, "B" * 240, "C" * 120)
    css = (ROOT / "src/web/static/style.css").read_text(encoding="utf-8")
    app = create_app(str(db), secret_key="layout-check")
    pages = {}

    def grab(client, name, path):
        html = client.get(path).get_data(as_text=True)
        pages[name] = re.sub(r'<link rel="stylesheet"[^>]*>', "<style>" + css + "</style>", html)

    for user_id, jobs in ((1, (("list", "/requests"), ("detail_normal", "/requests/1"),
                              ("detail_long", "/requests/2"), ("new_form", "/requests/new"))),
                          (2, (("staff_queue", "/staff/queue"),)),
                          (3, (("manager_list", "/manager/requests"), ("dashboard", "/manager/dashboard"))),
                          (4, (("admin_users", "/admin/users"), ("admin_categories", "/admin/categories")))):
        with app.test_client() as client:
            with client.session_transaction() as session:
                session["user_id"] = user_id
            for name, path in jobs:
                grab(client, name, path)
    return pages


def measure(browser: str, work: Path, name: str, html: str, width: int):
    page = work / f"{name}.html"
    page.write_text(html, encoding="utf-8")
    wrapper = work / f"{name}_{width}.html"
    wrapper.write_text(
        f"<html><body><iframe id=f src='{page.name}' width={width} height=900></iframe><script>"
        "document.getElementById('f').onload=function(){var d=this.contentDocument.documentElement;"
        "document.title='W='+d.scrollWidth+';C='+d.clientWidth;};</script></body></html>", encoding="utf-8")
    out = subprocess.run(
        [browser, "--headless", "--disable-gpu", "--no-sandbox", f"--user-data-dir={work / 'profile'}",
         "--allow-file-access-from-files", "--virtual-time-budget=3000", "--dump-dom", wrapper.as_uri()],
        capture_output=True, text=True, timeout=90, check=False).stdout
    found = re.search(r"<title>W=(\d+);C=(\d+)</title>", out)
    return (int(found.group(1)), int(found.group(2))) if found else None


def main() -> int:
    browser = find_browser()
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        pages = build_pages(work)
        for width in WIDTHS:
            for name, html in pages.items():
                size = measure(browser, work, name, html, width)
                ok = size is not None and size[0] <= size[1]
                failures += 0 if ok else 1
                print(f"{'ok  ' if ok else 'FAIL'} {name:14s} @{width:4d}px scrollWidth/clientWidth = {size}")
    print("layout check:", "FAILED" if failures else "passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
