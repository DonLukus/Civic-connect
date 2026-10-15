"""NFR-001 load test: filtered Staff queue response time.

Exact requirement under test (docs/requirements/non-functional-requirements.csv, NFR-001):
"The 95th percentile server response time for a filtered request list of up to 500 records
shall not exceed 2.0 seconds with 10 concurrent users on a warm instance."
Pass criterion from the same row's acceptance criteria: 10 concurrent users, 5 minutes,
against a 500-record data set, p95 <= 2.0s. Cold-start latency (NFR-002) is explicitly out of
scope for this script and must be measured separately, before this test warms the instance.

Stdlib only (urllib + concurrent.futures) - no new dependency added without team agreement.

This script is a design/tooling deliverable. It has NOT been executed against a live server as
part of this change - see performance/README.md for exactly what is still needed before a real
result exists, and docs/governance/ai-usage-register.csv for how this was verified.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field


@dataclass
class RequestResult:
    elapsed_seconds: float
    status_code: int
    looks_like_queue_page: bool
    error: str | None = None


@dataclass
class RunSummary:
    results: list[RequestResult] = field(default_factory=list)

    @property
    def successes(self) -> list[RequestResult]:
        return [r for r in self.results if r.error is None and r.status_code == 200 and r.looks_like_queue_page]

    def p95_seconds(self) -> float | None:
        successes = sorted(r.elapsed_seconds for r in self.successes)
        if not successes:
            return None
        index = max(0, int(round(0.95 * len(successes))) - 1)
        return successes[min(index, len(successes) - 1)]


def login_and_get_cookie_jar(base_url: str, email: str, password: str) -> http.cookiejar.CookieJar:
    """Signs in once so every worker thread reuses an authenticated session,
    matching NFR-001's own wording ("server response time"), not login time."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    login_page = opener.open(urllib.parse.urljoin(base_url, "/login"))
    html = login_page.read().decode("utf-8", errors="replace")
    token = _extract_csrf_token(html)

    data = urllib.parse.urlencode(
        {"email": email, "password": password, "csrf_token": token}
    ).encode()
    response = opener.open(urllib.parse.urljoin(base_url, "/login"), data=data)
    if response.status not in (200, 302):
        raise RuntimeError(f"Login failed with status {response.status}")
    return jar


def _extract_csrf_token(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.find(marker)
    if start == -1:
        raise RuntimeError("Could not find csrf_token in login page - page shape may have changed")
    start += len(marker)
    end = html.find('"', start)
    return html[start:end]


def single_request(base_url: str, status_filter: str, jar: http.cookiejar.CookieJar) -> RequestResult:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    query = urllib.parse.urlencode({"status": status_filter}) if status_filter else ""
    url = urllib.parse.urljoin(base_url, "/staff/queue")
    if query:
        url = f"{url}?{query}"

    start = time.monotonic()
    try:
        response = opener.open(url, timeout=10)
        body = response.read().decode("utf-8", errors="replace")
        elapsed = time.monotonic() - start
        # Guard against counting a login redirect or error page as a success -
        # a real queue page must contain this template's own caption text.
        looks_like_queue = "Service requests in your queue" in body or "No requests match this filter" in body
        return RequestResult(elapsed_seconds=elapsed, status_code=response.status, looks_like_queue_page=looks_like_queue)
    except urllib.error.HTTPError as exc:
        elapsed = time.monotonic() - start
        return RequestResult(elapsed_seconds=elapsed, status_code=exc.code, looks_like_queue_page=False, error=str(exc))
    except Exception as exc:  # noqa: BLE001 - record any failure, don't let one thread crash the run
        elapsed = time.monotonic() - start
        return RequestResult(elapsed_seconds=elapsed, status_code=0, looks_like_queue_page=False, error=str(exc))


def run(base_url: str, email: str, password: str, status_filter: str, concurrency: int, duration_seconds: int) -> RunSummary:
    """Keeps exactly `concurrency` requests in flight until `duration_seconds`
    elapses, then drains whatever is still running. Matches NFR-001's
    "10 concurrent users over 5 minutes" wording rather than firing a batch
    and waiting."""
    jar = login_and_get_cookie_jar(base_url, email, password)
    summary = RunSummary()
    deadline = time.monotonic() + duration_seconds

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        in_flight: set = set()
        while time.monotonic() < deadline or in_flight:
            while len(in_flight) < concurrency and time.monotonic() < deadline:
                in_flight.add(pool.submit(single_request, base_url, status_filter, jar))
            done = {f for f in in_flight if f.done()}
            for f in done:
                summary.results.append(f.result())
            in_flight -= done
            if not done:
                time.sleep(0.02)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="e.g. https://civic-connect-bcx2.onrender.com")
    parser.add_argument("--email", required=True, help="Staff test account email - never commit real credentials")
    parser.add_argument("--password", required=True)
    parser.add_argument("--status-filter", default="", help="Status value to filter the queue by (empty = all)")
    parser.add_argument("--concurrency", type=int, default=10, help="NFR-001: 10 concurrent users")
    parser.add_argument("--duration-seconds", type=int, default=300, help="NFR-001: 5 minutes")
    args = parser.parse_args()

    print(f"Starting NFR-001 load test against {args.base_url} "
          f"({args.concurrency} concurrent users, {args.duration_seconds}s)...")
    summary = run(
        args.base_url, args.email, args.password, args.status_filter,
        args.concurrency, args.duration_seconds,
    )

    total = len(summary.results)
    successful = len(summary.successes)
    p95 = summary.p95_seconds()

    report = {
        "total_requests": total,
        "successful_requests": successful,
        "failed_or_unexpected_requests": total - successful,
        "p95_seconds": p95,
        "pass": (p95 is not None and p95 <= 2.0 and successful == total),
        "nfr_target_seconds": 2.0,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
