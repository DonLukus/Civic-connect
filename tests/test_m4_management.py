"""FR-008, FR-011, FR-012, FR-019 to FR-022, FR-026: search/filter/sort, overdue, dashboard,
activity breakdown, CSV export and the duplicate prompt. Real schema.sql database, synthetic data.

Dashboard figures are checked against independently written SQL, not against the code under test.
"""

import csv
import io
import sqlite3
from pathlib import Path

import pytest

from src.persistence.admin_service import AdminService
from src.persistence.reporting import parse_filters, requests_to_csv
from src.persistence.request_service import RequestService
from src.web.app import create_app

SCHEMA = Path(__file__).resolve().parents[1] / "src" / "persistence" / "schema.sql"
APP_KEY = "test-signing-value"
REQ_A, REQ_B, STAFF_1, STAFF_2, MANAGER, ADMIN = 1, 2, 3, 4, 5, 6
ROADS, PARKS, RETIRED = 1, 2, 3


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "mgmt.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    for email, role in [("req-a@example.test", "Requester"), ("req-b@example.test", "Requester"),
                        ("staff-1@example.test", "Staff"), ("staff-2@example.test", "Staff"),
                        ("manager@example.test", "Manager"), ("admin@example.test", "Administrator")]:
        conn.execute("INSERT INTO users(email,password_hash,role,is_active) VALUES (?,?,?,1)",
                     (email, "x", role))
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES ('Roads',48,1)")
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES ('Parks',24,1)")
    conn.execute("INSERT INTO categories(name,target_resolution_hours,is_active) VALUES ('Retired',72,0)")
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def svc(db):
    return RequestService(db)


def q(db, sql, args=()):
    with sqlite3.connect(db) as conn:
        return conn.execute(sql, args).fetchall()


def make(svc, db, title="Pothole", cat=ROADS, requester=REQ_A, location="Main Rd",
         description="Deep hole", created=None):
    rid = svc.create_request(requester, cat, title, description, location)
    if created:
        with sqlite3.connect(db) as conn:
            conn.execute("UPDATE requests SET created_at = ?, updated_at = ? WHERE id = ?", (created, created, rid))
    return rid


def hours_ago(db, rid, hours):
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE requests SET created_at = datetime('now', ?) WHERE id = ?", (f"-{hours} hours", rid))


def version(db, rid):
    return q(db, "SELECT version FROM requests WHERE id = ?", (rid,))[0][0]


def assign(svc, db, rid, staff):
    svc.assign_request(rid, MANAGER, staff, version(db, rid))


def search(svc, actor, **raw):
    return svc.search_requests(actor, parse_filters({k.rstrip("_"): v for k, v in raw.items()}))


def refs(rows):
    return [r["reference"] for r in rows]


@pytest.fixture
def mixed(svc, db):
    """Six requests across two categories, requesters, statuses, dates and assignees."""
    a = make(svc, db, "Pothole on Main", ROADS, REQ_A, "Main Rd", "Deep hole", "2026-10-01 09:00:00")
    b = make(svc, db, "Broken swing", PARKS, REQ_B, "Central Park", "Seat snapped", "2026-10-03 09:00:00")
    c = make(svc, db, "Streetlight out", ROADS, REQ_A, "Oak Ave", "100% dark_night", "2026-10-05 09:00:00")
    d = make(svc, db, "Graffiti", PARKS, REQ_A, "Central Park", "Wall tagged", "2026-10-07 09:00:00")
    e = make(svc, db, "Fallen tree", ROADS, REQ_B, "Elm St", "Blocks road", "2026-10-09 09:00:00")
    f = make(svc, db, "Litter", PARKS, REQ_B, "River Walk", "Bins full", "2026-10-11 09:00:00")
    assign(svc, db, b, STAFF_1)                                   # Accepted, staff 1
    assign(svc, db, c, STAFF_2)
    svc.change_status(c, STAFF_2, "In Progress", version(db, c))  # In Progress, staff 2
    assign(svc, db, d, STAFF_1)
    svc.change_status(d, STAFF_1, "Resolved", version(db, d), "Cleaned")
    svc.change_status(d, MANAGER, "Closed", version(db, d))       # Closed, staff 1
    svc.change_status(e, MANAGER, "Rejected", version(db, e), "Not council land")
    return {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f}


# ---------------------------------------------------------------- FR-012 search / filter / sort

def test_manager_sees_everything_by_default_newest_first(svc, mixed):
    m = mixed
    assert refs(search(svc, MANAGER)) == [m["f"], m["e"], m["d"], m["c"], m["b"], m["a"]]


@pytest.mark.parametrize("filters,expected", [
    ({"status": "New"}, ["a", "f"]),
    ({"status": "Closed"}, ["d"]),
    ({"category": "1"}, ["a", "c", "e"]),
    ({"category": "2"}, ["b", "d", "f"]),
    ({"q": "swing"}, ["b"]),
    ({"q": "central park"}, ["b", "d"]),          # matches location
    ({"q": "tagged"}, ["d"]),                     # matches description
    ({"q": "POTHOLE"}, ["a"]),                    # case-insensitive
    ({"from_": "2026-10-05", "to": "2026-10-09"}, ["c", "d", "e"]),
    ({"from_": "2026-10-11"}, ["f"]),
    ({"to": "2026-10-01"}, ["a"]),
    ({"assignee": "unassigned"}, ["a", "e", "f"]),
])
def test_each_filter_alone(svc, mixed, filters, expected):
    got = set(refs(search(svc, MANAGER, **filters)))
    assert got == {mixed[k] for k in expected}


@pytest.mark.parametrize("filters,expected", [
    ({"status": "New", "category": "2"}, ["f"]),                   # two filters = intersection
    ({"category": "1", "from_": "2026-10-04"}, ["c", "e"]),
    ({"q": "park", "status": "Closed"}, ["d"]),
    ({"category": "2", "assignee": "unassigned", "to": "2026-10-10"}, []),
    ({"status": "Accepted", "category": "2", "q": "swing", "from_": "2026-10-01"}, ["b"]),
])
def test_combining_filters_returns_the_intersection(svc, mixed, filters, expected):
    assert set(refs(search(svc, MANAGER, **filters))) == {mixed[k] for k in expected}


def test_reference_search_with_and_without_hash(svc, mixed):
    target = mixed["c"]
    assert refs(search(svc, MANAGER, q=str(target))) == [target]
    assert refs(search(svc, MANAGER, q=f"#{target}")) == [target]
    assert search(svc, MANAGER, q="9999") == []


def test_search_text_is_literal_so_percent_and_underscore_are_not_wildcards(svc, mixed):
    assert refs(search(svc, MANAGER, q="100%")) == [mixed["c"]]
    assert refs(search(svc, MANAGER, q="dark_night")) == [mixed["c"]]
    assert search(svc, MANAGER, q="dark%night") == []
    assert search(svc, MANAGER, q="d_rk") == []


def test_sql_injection_text_is_just_text(svc, db, mixed):
    count = q(db, "SELECT COUNT(*) FROM requests")
    assert search(svc, MANAGER, q="'; DROP TABLE requests; --") == []
    assert search(svc, MANAGER, q='" OR 1=1 --') == []
    assert q(db, "SELECT COUNT(*) FROM requests") == count


@pytest.mark.parametrize("sort,direction,key", [
    ("created", "asc", lambda r: r["submitted_at"]),
    ("created", "desc", lambda r: r["submitted_at"]),
    ("status", "asc", lambda r: r["status"]),
    ("status", "desc", lambda r: r["status"]),
    ("category", "asc", lambda r: r["category"]),
    ("reference", "asc", lambda r: r["reference"]),
    ("reference", "desc", lambda r: r["reference"]),
])
def test_sorting(svc, mixed, sort, direction, key):
    rows = search(svc, MANAGER, sort=sort, dir=direction)
    values = [key(r) for r in rows]
    assert values == sorted(values, reverse=(direction == "desc"))
    assert len(rows) == 6


@pytest.mark.parametrize("raw,message", [
    ({"status": "Bogus"}, "supported request statuses"),
    ({"category": "abc"}, "category"),
    ({"category": "-1"}, "category"),
    ({"assignee": "x; y"}, "assignee"),
    ({"from": "01/10/2026"}, "YYYY-MM-DD"),
    ({"to": "2026-13-45"}, "not a real date"),
    ({"from": "2026-10-09", "to": "2026-10-01"}, "must not be after"),
    ({"sort": "title; DROP"}, "sort must be"),
    ({"dir": "sideways"}, "asc or desc"),
    ({"q": "x" * 101}, "at most 100"),
])
def test_invalid_filters_are_refused(raw, message):
    with pytest.raises(ValueError, match=message):
        parse_filters(raw)


def test_requester_sees_only_their_own_requests_whatever_the_filters(svc, mixed):
    own = search(svc, REQ_A)
    assert {r["reference"] for r in own} == {mixed[k] for k in "acd"}
    # a filter can never widen what a role may see
    assert set(refs(search(svc, REQ_A, category="2", assignee="unassigned"))) <= {mixed["d"], mixed["a"], mixed["c"]}
    assert mixed["b"] not in refs(search(svc, REQ_A, q="swing"))
    assert all(r["assignee_email"] is None for r in own)  # contact details stay hidden from Requesters


def test_staff_see_unassigned_and_their_own_but_not_other_staffs_work(svc, mixed):
    m = mixed
    staff_1 = set(refs(search(svc, STAFF_1)))
    assert staff_1 == {m["a"], m["b"], m["d"], m["e"], m["f"]}  # unassigned (a, e, f) plus their own (b, d)
    assert m["c"] not in staff_1                                            # staff 2's request
    assert m["c"] not in refs(search(svc, STAFF_1, assignee=str(STAFF_2)))   # a filter cannot reveal it
    assert set(refs(search(svc, STAFF_1, assignee="me"))) == {m["b"], m["d"]}
    assert set(refs(search(svc, STAFF_1, assignee="unassigned"))) == {m["a"], m["e"], m["f"]}


@pytest.mark.parametrize("actor", [ADMIN, 999])
def test_other_roles_cannot_search(svc, actor):
    with pytest.raises(PermissionError):
        svc.search_requests(actor, parse_filters({}))


def test_requester_list_shows_reference_category_date_status_and_is_newest_first(svc, mixed):
    rows = search(svc, REQ_A)
    assert [r["reference"] for r in rows] == sorted((r["reference"] for r in rows), reverse=True)
    assert {"reference", "category", "submitted_at", "status"} <= set(rows[0])


# ---------------------------------------------------------------- FR-021 overdue

def test_overdue_uses_the_categorys_configured_target(svc, db):
    over = make(svc, db, "Over", ROADS)       # Roads target 48h
    under = make(svc, db, "Under", ROADS)
    park = make(svc, db, "Park", PARKS)       # Parks target 24h
    hours_ago(db, over, 49)
    hours_ago(db, under, 47)
    hours_ago(db, park, 25)
    flags = {r["reference"]: r["overdue"] for r in search(svc, MANAGER)}
    assert flags == {over: True, under: False, park: True}
    assert set(refs(search(svc, MANAGER, overdue="1"))) == {over, park}


def test_changing_a_target_changes_what_is_overdue(svc, db):
    rid = make(svc, db, "Pothole", ROADS)
    hours_ago(db, rid, 30)
    assert not search(svc, MANAGER)[0]["overdue"]
    AdminService(db, 10).update_category(ADMIN, ROADS, target_hours=24)
    assert search(svc, MANAGER)[0]["overdue"]


def test_only_open_requests_can_be_overdue(svc, db):
    rid = make(svc, db, "Old", ROADS)
    assign(svc, db, rid, STAFF_1)
    hours_ago(db, rid, 500)
    assert search(svc, MANAGER)[0]["overdue"]
    svc.change_status(rid, STAFF_1, "Resolved", version(db, rid), "Done")
    assert not search(svc, MANAGER)[0]["overdue"]
    svc.change_status(rid, MANAGER, "Closed", version(db, rid))
    assert not search(svc, MANAGER)[0]["overdue"]
    other = make(svc, db, "Rejected one", ROADS)
    hours_ago(db, other, 500)
    svc.change_status(other, MANAGER, "Rejected", version(db, other), "no")
    assert not next(r for r in search(svc, MANAGER) if r["reference"] == other)["overdue"]


def test_on_hold_and_in_progress_still_count_as_open_for_overdue(svc, db):
    rid = make(svc, db, "Held", ROADS)
    assign(svc, db, rid, STAFF_1)
    svc.change_status(rid, STAFF_1, "On Hold", version(db, rid))
    hours_ago(db, rid, 100)
    assert search(svc, MANAGER)[0]["overdue"]


# ---------------------------------------------------------------- FR-019 / FR-020 dashboard

def direct(db, sql, args=()):
    return q(db, sql, args)[0][0]


def test_dashboard_counts_equal_the_stored_records(svc, db, mixed):
    report = svc.dashboard(MANAGER)
    assert report["total"] == direct(db, "SELECT COUNT(*) FROM requests") == 6
    for status in ("New", "Accepted", "In Progress", "On Hold", "Resolved", "Closed", "Rejected"):
        assert report["by_status"][status] == direct(db, "SELECT COUNT(*) FROM requests WHERE status = ?", (status,))
    assert report["open"] == direct(
        db, "SELECT COUNT(*) FROM requests WHERE status IN ('New','Accepted','In Progress','On Hold')")
    assert report["in_progress"] == 1 and report["closed"] == 1 and report["rejected"] == 1
    assert report["resolved"] == 0
    assert report["unassigned_open"] == direct(
        db, "SELECT COUNT(*) FROM requests WHERE assignee_id IS NULL AND status IN ('New','Accepted','In Progress','On Hold')")


def test_category_breakdown_covers_every_active_category_and_sums_to_the_total(svc, db, mixed):
    report = svc.dashboard(MANAGER)
    by_name = {c["name"]: c["count"] for c in report["by_category"]}
    assert by_name == {"Parks": 3, "Roads": 3}
    assert sum(by_name.values()) == report["total"]
    AdminService(db, 10).create_category(ADMIN, "Trees", 10)  # an active category with no requests
    report = svc.dashboard(MANAGER)
    assert {c["name"]: c["count"] for c in report["by_category"]}["Trees"] == 0
    assert sum(c["count"] for c in report["by_category"]) == report["total"]


def test_inactive_category_with_requests_is_still_counted_so_the_sum_reconciles(svc, db):
    make(svc, db, "Old style", ROADS)
    AdminService(db, 10).set_category_active(ADMIN, ROADS, False)
    report = svc.dashboard(MANAGER)
    assert sum(c["count"] for c in report["by_category"]) == report["total"] == 1
    assert [c["name"] for c in report["by_category"] if c["name"] == "Roads"]


def test_period_filter_is_inclusive_and_figures_follow_it(svc, db, mixed):
    report = svc.dashboard(MANAGER, "2026-10-03", "2026-10-07")
    expected = direct(db, "SELECT COUNT(*) FROM requests WHERE date(created_at) BETWEEN '2026-10-03' AND '2026-10-07'")
    assert report["total"] == expected == 3
    assert sum(report["by_status"].values()) == 3
    assert sum(c["count"] for c in report["by_category"]) == 3
    assert svc.dashboard(MANAGER, "2027-01-01", "2027-01-31")["total"] == 0
    empty = svc.dashboard(MANAGER, "2027-01-01", "2027-01-31")
    assert all(v == 0 for v in empty["by_status"].values()) and empty["overdue"] == 0


def test_dashboard_overdue_count_matches_the_flagged_requests(svc, db):
    for hours in (60, 49, 10):
        hours_ago(db, make(svc, db, f"r{hours}", ROADS), hours)
    assert svc.dashboard(MANAGER)["overdue"] == 2 == len(search(svc, MANAGER, overdue="1"))


def test_assignee_breakdown_sums_to_the_total(svc, db, mixed):
    report = svc.dashboard(MANAGER)
    assert sum(a["count"] for a in report["by_assignee"]) == report["total"]
    names = {a["email"]: a["count"] for a in report["by_assignee"]}
    assert names["Unassigned"] == 3 and names["staff-1@example.test"] == 2 and names["staff-2@example.test"] == 1


@pytest.mark.parametrize("actor", [REQ_A, STAFF_1, ADMIN, 999])
def test_only_a_manager_sees_the_dashboard(svc, actor):
    with pytest.raises(PermissionError):
        svc.dashboard(actor)


def test_dashboard_rejects_bad_dates(svc):
    with pytest.raises(ValueError):
        svc.dashboard(MANAGER, "nope", None)
    with pytest.raises(ValueError, match="must not be after"):
        svc.dashboard(MANAGER, "2026-10-09", "2026-10-01")


# ---------------------------------------------------------------- FR-022 CSV

def parse(text):
    return list(csv.reader(io.StringIO(text)))


def test_csv_has_a_header_and_exactly_one_row_per_listed_request(svc, db, mixed):
    rows = search(svc, MANAGER, category="2")
    table = parse(requests_to_csv(rows))
    assert table[0] == ["Reference", "Title", "Category", "Submitted", "Status", "Assignee",
                        "Last status change", "Overdue"]
    assert len(table) - 1 == len(rows) == 3
    for line, row in zip(table[1:], rows, strict=True):
        assert line[0] == str(row["reference"]) and line[1] == row["title"]
        assert line[2] == row["category"] and line[4] == row["status"]


def test_csv_of_an_empty_list_is_just_the_header(svc, db):
    assert len(parse(requests_to_csv([]))) == 1


def test_csv_round_trips_commas_quotes_and_newlines(svc, db):
    make(svc, db, 'He said "stop", twice', ROADS, description="line one\nline two", location="A, B")
    table = parse(requests_to_csv(search(svc, MANAGER)))
    assert table[1][1] == 'He said "stop", twice'


@pytest.mark.parametrize("title", ["=SUM(A1)", "+cmd|' /C calc'!A0", "-2+3", "@HYPERLINK(1)"])
def test_csv_cells_that_look_like_formulas_are_neutralised(svc, db, title):
    make(svc, db, title, ROADS)
    cell = parse(requests_to_csv(search(svc, MANAGER)))[1][1]
    assert cell == "'" + title  # opens as text, not as a formula


# ---------------------------------------------------------------- FR-026 duplicates

def test_possible_duplicates_match_open_requests_in_the_same_category_and_place(svc, db):
    original = make(svc, db, "Pothole", ROADS, location="Main Rd")
    assert [d["reference"] for d in svc.find_possible_duplicates(ROADS, "  main   RD ")] == [original]
    assert svc.find_possible_duplicates(PARKS, "Main Rd") == []        # other category
    assert svc.find_possible_duplicates(ROADS, "Elm St") == []         # other place
    assert svc.find_possible_duplicates(ROADS, "") == []
    assign(svc, db, original, STAFF_1)
    svc.change_status(original, STAFF_1, "Resolved", version(db, original), "Done")
    assert svc.find_possible_duplicates(ROADS, "Main Rd") == []        # no longer open


def test_duplicate_warning_does_not_reveal_other_peoples_titles(svc, db):
    make(svc, db, "Private matter about neighbour", ROADS, REQ_B, "Main Rd")
    found = svc.find_possible_duplicates(ROADS, "Main Rd")
    assert "title" not in found[0] and "Private" not in str(found)


# ---------------------------------------------------------------- routes

@pytest.fixture
def client_for(db):
    app = create_app(db, secret_key=APP_KEY)

    def make_client(user_id):
        client = app.test_client()
        with client.session_transaction() as s:
            s["user_id"] = user_id
            s["_csrf_token"] = "tok"
        return client
    return make_client


def test_manager_pages_and_their_authorization(client_for, mixed):
    for path in ("/manager/requests", "/manager/dashboard", "/manager/requests.csv"):
        assert client_for(MANAGER).get(path).status_code == 200
        for user in (REQ_A, STAFF_1, ADMIN):
            assert client_for(user).get(path).status_code == 403
    assert client_for(REQ_A).get("/staff/queue.csv").status_code == 403
    assert client_for(MANAGER).get("/staff/queue.csv").status_code == 403


def test_route_filters_and_bad_input(client_for, mixed):
    c = client_for(MANAGER)
    page = c.get("/manager/requests?category=2&status=New").get_data(as_text=True)
    assert "Litter" in page and "Pothole on Main" not in page
    assert c.get("/manager/requests?status=Bogus").status_code == 400
    assert c.get("/manager/requests?from=2026-10-09&to=2026-10-01").status_code == 400
    assert c.get("/manager/dashboard?from=bad").status_code == 400
    assert client_for(STAFF_1).get("/staff/queue?sort=evil").status_code == 400
    assert client_for(REQ_A).get("/requests?status=Bogus").status_code == 400


def test_csv_route_matches_the_filtered_list(client_for, mixed):
    c = client_for(MANAGER)
    response = c.get("/manager/requests.csv?category=1")
    assert response.mimetype == "text/csv" and "attachment" in response.headers["Content-Disposition"]
    table = parse(response.get_data(as_text=True))
    assert len(table) == 1 + 3
    assert {r[1] for r in table[1:]} == {"Pothole on Main", "Streetlight out", "Fallen tree"}
    staff_csv = parse(client_for(STAFF_1).get("/staff/queue.csv").get_data(as_text=True))
    assert "Streetlight out" not in {r[1] for r in staff_csv}  # another staff member's request


def test_dashboard_page_shows_the_counted_figures(client_for, mixed):
    html = client_for(MANAGER).get("/manager/dashboard").get_data(as_text=True)
    assert "Total requests" in html and "Overdue" in html and "By category" in html
    assert "Parks" in html and "Roads" in html


def test_overdue_and_reassign_markers_show_in_the_lists(svc, db, client_for):
    rid = make(svc, db, "Stale one", ROADS)
    assign(svc, db, rid, STAFF_1)
    hours_ago(db, rid, 100)
    AdminService(db, 10).set_active(ADMIN, STAFF_1, False)
    html = client_for(MANAGER).get("/manager/requests").get_data(as_text=True)
    assert 'badge--rejected">Overdue' in html and "deactivated" in html
    only = client_for(MANAGER).get("/manager/requests?assignee=inactive").get_data(as_text=True)
    assert "Stale one" in only
    overdue_only = client_for(MANAGER).get("/manager/requests?overdue=1").get_data(as_text=True)
    assert "Stale one" in overdue_only


def submit(client, **form):
    base = {"csrf_token": "tok", "title": "Another pothole", "description": "Same road",
            "category_id": str(ROADS), "location": "Main Rd"}
    return client.post("/requests", data={**base, **form})


def test_duplicate_prompt_flow(svc, db, client_for):
    first = make(svc, db, "Pothole", ROADS, REQ_B, "Main Rd")
    c = client_for(REQ_A)
    warned = submit(c)
    html = warned.get_data(as_text=True)
    assert warned.status_code == 409 and "Possible duplicate request" in html and f"#{first}" in html
    assert "Another pothole" in html  # what they typed is kept
    assert q(db, "SELECT COUNT(*) FROM requests") == [(1,)]                       # nothing created yet
    assert "Pothole</li>" not in html and "Private" not in html                    # no one else's title
    confirmed = submit(c, confirm_duplicate="1")
    assert confirmed.status_code == 302 and q(db, "SELECT COUNT(*) FROM requests") == [(2,)]


def test_no_warning_when_nothing_matches(svc, db, client_for):
    make(svc, db, "Pothole", ROADS, REQ_B, "Elm St")
    assert submit(client_for(REQ_A)).status_code == 302


def test_staff_queue_and_requester_list_offer_the_filter_bar(svc, db, client_for):
    rid = make(svc, db, "Pothole", ROADS)
    page = client_for(STAFF_1).get("/staff/queue").get_data(as_text=True)
    assert 'name="q"' in page and 'name="sort"' in page and "Export CSV" in page and f"#{rid}" in page
    mine = client_for(REQ_A).get("/requests").get_data(as_text=True)
    assert 'name="q"' in mine and "Export CSV" not in mine
