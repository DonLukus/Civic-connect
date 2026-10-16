"""NFR-001 load test: filtered Staff queue response time.

Exact requirement under test (docs/requirements/non-functional-requirements.csv, NFR-001):
"The 95th percentile server response time for a filtered request list of up to 500 records
shall not exceed 2.0 seconds with 10 concurrent users on a warm instance."
Pass criterion from the same row's acceptance criteria: 10 concurrent users, 5 minutes,
against a 500-record data set, p95 <= 2.0s. Cold-start latency (NFR-002) is explicitly out of
scope for this script and must be measured separately, before this test warms the instance.

Stdlib only (urllib + concurrent.futures) - no new dependency added without team agreement.

Executed evidence is indexed in docs/release/m3-release-evidence-summary.md.
This is an HTTP load generator, not a browser or JavaScript rendering benchmark.

Design notes added after review feedback (see PR #80 discussion):
- `--status-filter` and `--min-expected-results` are both required, not defaulted. An empty
  filter or an empty result set would let a trivial, unfiltered or unseeded response pass
  as if it were real NFR-001 evidence - this script now refuses to call that a pass.
- Each simulated user logs in with its own session (its own cookie jar), rather than one
  session shared across every thread, since NFR-001 says "10 concurrent users", not
  "10 concurrent requests from one session".
- The report states the actual parameters used and whether the run qualifies as a real
  NFR-001 result (concurrency >= 10, duration >= 300s) so a short smoke-test run can never be
  mistaken for the required five-minute measurement.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

NFR_001_TARGET_SECONDS = 2.0
NFR_001_MIN_CONCURRENCY = 10
NFR_001_MIN_DURATION_SECONDS = 300


@dataclass
class RequestResult:
    elapsed_seconds: float
    status_code: int
    looks_like_queue_page: bool
    result_rows_seen: int
    error: str | None = None


@dataclass
class RunSummary:
    results: list[RequestResult] = field(default_factory=list)
    min_expected_results: int = 0

    @property
    def successes(self) -> list[RequestResult]:
        """A success must be a real queue page AND contain at least the
        operator-asserted minimum row count - an empty or under-seeded
        queue must not count as evidence for NFR-001."""
        return [
            r for r in self.results
            if r.error is None
            and r.status_code == 200
            and r.looks_like_queue_page
            and r.result_rows_seen >= self.min_expected_results
        ]

    def p95_seconds(self) -> float | None:
        successes = sorted(r.elapsed_seconds for r in self.successes)
        if not successes:
            return None
        index = max(0, math.ceil(0.95 * len(successes)) - 1)
        return successes[min(index, len(successes) - 1)]


def login(base_url: str, email: str, password: str) -> http.cookiejar.CookieJar:
    """One independent session per call - used once per simulated user, not shared."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    login_page = opener.open(urllib.parse.urljoin(base_url, "/login"), timeout=15)
    html = login_page.read().decode("utf-8", errors="replace")
    token = _extract_csrf_token(html)

    data = urllib.parse.urlencode(
        {"email": email, "password": password, "csrf_token": token}
    ).encode()
    response = opener.open(urllib.parse.urljoin(base_url, "/login"), data=data, timeout=15)
    if response.status != 200 or urllib.parse.urlparse(response.url).path != "/staff/queue":
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


def single_request(base_url: str, status_filter: str, jar: http.cookiejar.CookieJar,
                   expected_ids=None) -> RequestResult:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    query = urllib.parse.urlencode({"status": status_filter})
    url = f"{urllib.parse.urljoin(base_url, '/staff/queue')}?{query}"

    start = time.monotonic()
    try:
        response = opener.open(url, timeout=10)
        body = response.read().decode("utf-8", errors="replace")
        elapsed = time.monotonic() - start
        # Guard against counting a login redirect or error page as a success -
        # a real queue page must contain this template's own caption text.
        looks_like_queue = "Service requests in your queue" in body or "No requests match this filter" in body
        # staff_queue.html renders each result row as `<td>#{{ r.id }}</td>` -
        # count those cells as a proxy for how many rows actually came back,
        # so an unexpectedly empty/thin result can't quietly pass as a success.
        rows = re.findall(r"<tr>\s*<td>#(\d+)</td>(.*?)</tr>", body, re.DOTALL)
        rows_seen = len(rows)
        returned_ids = {int(row_id) for row_id, _ in rows}
        filter_valid = all(
            len(cells := re.findall(r"<td>(.*?)</td>", rest, re.DOTALL)) >= 4
            and cells[3].strip() == status_filter for _, rest in rows
        )
        looks_like_queue = bool(looks_like_queue and filter_valid and
                               (expected_ids is None or returned_ids == set(expected_ids)))
        return RequestResult(
            elapsed_seconds=elapsed, status_code=response.status,
            looks_like_queue_page=looks_like_queue, result_rows_seen=rows_seen,
        )
    except urllib.error.HTTPError as exc:
        elapsed = time.monotonic() - start
        return RequestResult(elapsed_seconds=elapsed, status_code=exc.code, looks_like_queue_page=False, result_rows_seen=0, error=str(exc))
    except Exception as exc:  # noqa: BLE001 - record any failure, don't let one thread crash the run
        elapsed = time.monotonic() - start
        return RequestResult(elapsed_seconds=elapsed, status_code=0, looks_like_queue_page=False, result_rows_seen=0, error=str(exc))


def request_loop(base_url: str, status_filter: str, jar: http.cookiejar.CookieJar, deadline: float,
                 expected_ids=None) -> list[RequestResult]:
    """One already-logged-in simulated user firing requests back-to-back
    until the deadline. Login happens before this is called, not inside
    it - see `run()` - so login/warm-up time never eats into the timed
    measurement window."""
    results = []
    while time.monotonic() < deadline:
        results.append(single_request(base_url, status_filter, jar, expected_ids))
    return results


def run(base_url: str, email: str, password: str, status_filter: str,
        concurrency: int, duration_seconds: int, min_expected_results: int,
        accounts=None, expected_ids=None) -> RunSummary:
    if concurrency < 1 or duration_seconds <= 0 or min_expected_results < 1 or not status_filter.strip():
        raise ValueError("Positive workload, non-empty status and positive result count required")
    summary = RunSummary(min_expected_results=min_expected_results)

    # Warm-up phase: every simulated user logs in first. Deliberately NOT
    # part of the timed window - NFR-001 measures warm-instance response
    # time, not login latency, and starting the clock before everyone is
    # actually logged in would silently shrink each user's real firing time.
    with ThreadPoolExecutor(max_workers=concurrency) as login_pool:
        users = accounts or [{"email": email, "password": password}] * concurrency
        if len(users) != concurrency:
            raise ValueError("Account count must equal concurrency")
        jars = list(login_pool.map(lambda user: login(base_url, user["email"], user["password"]), users))
    for jar in jars:
        check = single_request(base_url, status_filter, jar, expected_ids)
        if not check.looks_like_queue_page or check.result_rows_seen < min_expected_results:
            raise RuntimeError("Warm-up failed: queue/filter/fixture did not match expected results")

    # Timed measurement phase: the clock starts only once every user is
    # ready to fire requests immediately.
    deadline = time.monotonic() + duration_seconds
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(request_loop, base_url, status_filter, jar, deadline, expected_ids) for jar in jars]
        for f in futures:
            summary.results.extend(f.result())

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="e.g. https://civic-connect-bcx2.onrender.com")
    parser.add_argument("--email", required=True, help="Staff test account email - never commit real credentials")
    parser.add_argument("--password", required=True)
    parser.add_argument("--status-filter", required=True,
                         help="Status value to filter the queue by - required, since NFR-001 "
                              "is specifically about a FILTERED list, not an unfiltered dump")
    parser.add_argument("--min-expected-results", type=int, required=True,
                         help="The seeded dataset's known row count for this filter - a response "
                              "with fewer rows than this does not count as NFR-001 evidence")
    parser.add_argument("--concurrency", type=int, default=NFR_001_MIN_CONCURRENCY,
                         help=f"NFR-001: {NFR_001_MIN_CONCURRENCY} concurrent users")
    parser.add_argument("--duration-seconds", type=int, default=NFR_001_MIN_DURATION_SECONDS,
                         help=f"NFR-001: {NFR_001_MIN_DURATION_SECONDS} seconds (5 minutes)")
    args = parser.parse_args()

    # `required=True` only forces the flag to be present - it does not stop
    # someone passing an empty/zero value that would defeat the whole point
    # of requiring it. Reject those explicitly.
    if not args.status_filter.strip():
        parser.error("--status-filter must not be empty - NFR-001 is about a FILTERED list; "
                      "an empty filter tests an unfiltered dump instead")
    if args.min_expected_results < 1:
        parser.error("--min-expected-results must be at least 1 - a zero (or negative) "
                      "expectation can never catch an empty or under-seeded response")

    qualifies = (args.concurrency >= NFR_001_MIN_CONCURRENCY and args.duration_seconds >= NFR_001_MIN_DURATION_SECONDS)
    if not qualifies:
        print(f"WARNING: this run uses concurrency={args.concurrency}, duration={args.duration_seconds}s - "
              f"that does NOT meet NFR-001's {NFR_001_MIN_CONCURRENCY} users / "
              f"{NFR_001_MIN_DURATION_SECONDS}s requirement. Treat this as a smoke test only, "
              f"never as NFR-001 evidence.")

    print(f"Starting load test against {args.base_url} "
          f"({args.concurrency} concurrent users, {args.duration_seconds}s, "
          f"status filter={args.status_filter!r})...")
    summary = run(
        args.base_url, args.email, args.password, args.status_filter,
        args.concurrency, args.duration_seconds, args.min_expected_results,
    )

    total = len(summary.results)
    successful = len(summary.successes)
    p95 = summary.p95_seconds()

    report = {
        "concurrency_used": args.concurrency,
        "duration_seconds_used": args.duration_seconds,
        "status_filter_used": args.status_filter,
        "min_expected_results_required": args.min_expected_results,
        "qualifies_as_nfr001_run": qualifies,
        "total_requests": total,
        "successful_requests": successful,
        "failed_or_underfilled_requests": total - successful,
        "p95_seconds": p95,
        "nfr_target_seconds": NFR_001_TARGET_SECONDS,
        "pass": bool(qualifies and p95 is not None and p95 <= NFR_001_TARGET_SECONDS and successful == total),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
