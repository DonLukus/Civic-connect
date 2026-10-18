"""FR-012, FR-019 to FR-022, FR-026: search/filter/sort, dashboard, breakdown, overdue, CSV, duplicates.

Mixed into RequestService. Reads only. Filters are whitelisted and every value reaches SQL as a bound
parameter; the sort column comes from a fixed map, never from user text.
"""

import csv
import io
import re
import sqlite3
from datetime import date

from src.persistence import lifecycle

MAX_QUERY_LENGTH = 100
MAX_ROWS = 5000  # NFR-013 sizes the system at 5,000 requests

SORTS = {
    "created": "r.created_at",
    "updated": "r.updated_at",
    "status": "r.status",
    "category": "c.name",
    "reference": "r.id",
}
OPEN_SQL = "('" + "','".join(lifecycle.OPEN_STATUSES) + "')"
# FR-021: overdue = still open and older than the category's configured target (hours since submission).
OVERDUE_SQL = (
    f"(r.status IN {OPEN_SQL} AND (julianday('now') - julianday(r.created_at)) * 24 "
    "> c.target_resolution_hours)"
)
CSV_COLUMNS = ["Reference", "Title", "Category", "Submitted", "Status", "Assignee",
               "Last status change", "Overdue"]
# The Manager list as displayed; ?format=csv on /manager/requests exports exactly these columns.
DISPLAYED_CSV_COLUMNS = ["Reference", "Title", "Category", "Submitted", "Status", "Assignee"]


def _date(value, label):
    if not value:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{label} must be a date in the form YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label} is not a real date") from None
    return value


def parse_filters(args) -> dict:
    """Validate query-string filters (a mapping with .get) into a clean dict. Raises ValueError."""
    text = (args.get("q") or "").strip()
    if len(text) > MAX_QUERY_LENGTH:
        raise ValueError(f"Search text must be at most {MAX_QUERY_LENGTH} characters")
    status = args.get("status") or None
    if status is not None and status not in lifecycle.STATUSES:
        raise ValueError("status must be one of the supported request statuses")
    category = args.get("category") or args.get("category_id") or None
    if category is not None:
        if not category.isdigit():
            raise ValueError("category must be a category from the list")
        category = int(category)
    assignee = args.get("assignee") or None
    if assignee is not None and assignee not in ("me", "unassigned", "inactive") and not assignee.isdigit():
        raise ValueError("assignee filter is not valid")
    date_from, date_to = _date(args.get("from"), "From date"), _date(args.get("to"), "To date")
    if date_from and date_to and date_from > date_to:
        raise ValueError("The From date must not be after the To date")
    sort = args.get("sort") or "created"
    if sort not in SORTS:
        raise ValueError("sort must be one of: " + ", ".join(SORTS))
    direction = (args.get("dir") or "").lower() or ("asc" if sort == "reference" else "desc")
    if direction not in ("asc", "desc"):
        raise ValueError("dir must be asc or desc")
    return {"q": text, "status": status, "category": category, "assignee": assignee,
            "from": date_from, "to": date_to, "overdue": args.get("overdue") == "1",
            "sort": sort, "dir": direction}


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ReportingMixin:
    db_path: str

    def _reporting_role(self, conn, actor_id, allowed):
        row = conn.execute("SELECT role FROM users WHERE id = ? AND is_active = 1", (actor_id,)).fetchone()
        if row is None or row["role"] not in allowed:
            raise PermissionError("This role cannot view that list")
        return row["role"]

    # ---- FR-012 / FR-011 / FR-008: one query behind every request list ---------------------

    def search_requests(self, actor_id: int, filters: dict | None = None, limit: int = MAX_ROWS):
        """Requests the actor may see, narrowed by `filters` (intersection) and sorted.

        Requester: own requests. Staff: unassigned plus those assigned to them (FR-011).
        Manager: all requests, including those still assigned to a deactivated user.
        """
        filters = filters or parse_filters({})
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            role = self._reporting_role(conn, actor_id, ("Requester", "Staff", "Manager"))
            where, params = [], []
            if role == "Requester":
                where.append("r.requester_id = ?")
                params.append(actor_id)
            elif role == "Staff":
                where.append("(r.assignee_id IS NULL OR r.assignee_id = ?)")
                params.append(actor_id)

            if filters["q"]:
                if filters["q"].lstrip("#").isdigit():
                    where.append("r.id = ?")
                    params.append(int(filters["q"].lstrip("#")))
                else:
                    like = f"%{_escape_like(filters['q'])}%"
                    where.append("(r.title LIKE ? ESCAPE '\\' OR r.description LIKE ? ESCAPE '\\' "
                                 "OR r.location LIKE ? ESCAPE '\\')")
                    params += [like, like, like]
            if filters["status"]:
                where.append("r.status = ?")
                params.append(filters["status"])
            if filters["category"] is not None:
                where.append("r.category_id = ?")
                params.append(filters["category"])
            assignee = filters["assignee"]
            if assignee == "me":
                where.append("r.assignee_id = ?")
                params.append(actor_id)
            elif assignee == "unassigned":
                where.append("r.assignee_id IS NULL")
            elif assignee == "inactive" and role == "Manager":
                where.append("r.assignee_id IN (SELECT id FROM users WHERE is_active = 0) "  # nosec B608 - only code-defined constants are interpolated; values are bound
                             f"AND r.status IN {OPEN_SQL}")
            elif assignee and assignee.isdigit() and role == "Manager":
                where.append("r.assignee_id = ?")
                params.append(int(assignee))
            if filters["from"]:
                where.append("date(r.created_at) >= ?")
                params.append(filters["from"])
            if filters["to"]:
                where.append("date(r.created_at) <= ?")
                params.append(filters["to"])
            if filters["overdue"]:
                where.append(OVERDUE_SQL)

            order = f"{SORTS[filters['sort']]} {'ASC' if filters['dir'] == 'asc' else 'DESC'}, r.id DESC"
            sql = f"""
                SELECT r.id AS reference, r.title, c.name AS category, r.created_at AS submitted_at,
                       r.status, r.assignee_id,
                       {OVERDUE_SQL} AS overdue,
                       COALESCE((SELECT MAX(a.changed_at) FROM request_audit AS a
                                 WHERE a.request_id = r.id AND a.new_status = r.status),
                                r.created_at) AS last_status_changed_at,
                       CASE WHEN ? = 'Manager' THEN u.email END AS assignee_email,
                       CASE WHEN u.is_active = 0 THEN 1 ELSE 0 END AS assignee_inactive
                FROM requests AS r
                JOIN categories AS c ON c.id = r.category_id
                LEFT JOIN users AS u ON u.id = r.assignee_id
                {('WHERE ' + ' AND '.join(where)) if where else ''}
                ORDER BY {order}
                LIMIT ?
            """  # nosec B608 - only code-defined constants are interpolated; values are bound
            rows = conn.execute(sql, [role, *params, limit]).fetchall()
            return [{**dict(row), "overdue": bool(row["overdue"]),
                     "assignee_inactive": bool(row["assignee_inactive"])} for row in rows]
        finally:
            conn.close()

    # ---- FR-019 / FR-020 / FR-021: management dashboard -----------------------------------

    def dashboard(self, actor_id: int, date_from: str | None = None, date_to: str | None = None) -> dict:
        """Counts for requests submitted in the period; every figure comes straight from stored rows."""
        date_from, date_to = _date(date_from, "From date"), _date(date_to, "To date")
        if date_from and date_to and date_from > date_to:
            raise ValueError("The From date must not be after the To date")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            self._reporting_role(conn, actor_id, ("Manager",))
            where, params = ["1 = 1"], []
            if date_from:
                where.append("date(r.created_at) >= ?")
                params.append(date_from)
            if date_to:
                where.append("date(r.created_at) <= ?")
                params.append(date_to)
            condition = " AND ".join(where)
            base = f"FROM requests r JOIN categories c ON c.id = r.category_id WHERE {condition}"

            by_status = {s: 0 for s in lifecycle.STATUSES}
            for row in conn.execute(f"SELECT r.status AS s, COUNT(*) AS n {base} GROUP BY r.status", params):
                by_status[row["s"]] = row["n"]
            total = sum(by_status.values())
            overdue = conn.execute(f"SELECT COUNT(*) {base} AND {OVERDUE_SQL}", params).fetchone()[0]
            unassigned_open = conn.execute(
                f"SELECT COUNT(*) {base} AND r.assignee_id IS NULL AND r.status IN {OPEN_SQL}", params
            ).fetchone()[0]

            counts = {row["category_id"]: row["n"] for row in conn.execute(
                f"SELECT r.category_id, COUNT(*) AS n {base} GROUP BY r.category_id", params)}
            by_category = [
                {"id": c["id"], "name": c["name"], "active": bool(c["is_active"]),
                 "count": counts.get(c["id"], 0)}
                for c in conn.execute("SELECT id, name, is_active FROM categories ORDER BY name")
                if c["is_active"] or counts.get(c["id"], 0)  # every active category, even at zero
            ]
            by_assignee = [
                {"assignee_id": row["assignee_id"], "email": row["email"] or "Unassigned", "count": row["n"]}
                for row in conn.execute(
                    f"SELECT r.assignee_id, u.email, COUNT(*) AS n FROM requests r "  # nosec B608 - only code-defined constants are interpolated; values are bound
                    f"JOIN categories c ON c.id = r.category_id "
                    f"LEFT JOIN users u ON u.id = r.assignee_id WHERE {condition} "
                    f"GROUP BY r.assignee_id ORDER BY (r.assignee_id IS NULL), u.email", params)
            ]
            return {
                "period": {"from": date_from, "to": date_to},
                "total": total,
                "open": sum(by_status[s] for s in lifecycle.OPEN_STATUSES),
                "in_progress": by_status["In Progress"],
                "overdue": overdue,
                "resolved": by_status["Resolved"],
                "closed": by_status["Closed"],
                "rejected": by_status["Rejected"],
                "unassigned_open": unassigned_open,
                "by_status": by_status,
                "by_category": by_category,
                "by_assignee": by_assignee,
            }
        finally:
            conn.close()

    # ---- FR-026: duplicate prompt -----------------------------------------------------------

    def find_possible_duplicates(self, category_id: int, location: str, limit: int = 5):
        """Open requests in the same category at the same place. Titles are not returned: they
        belong to other people."""
        place = " ".join((location or "").split()).lower()
        if not place:
            return []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute(
                f"""
                SELECT r.id AS reference, c.name AS category, r.status, r.created_at AS submitted_at
                FROM requests r JOIN categories c ON c.id = r.category_id
                WHERE r.category_id = ? AND r.status IN {OPEN_SQL}
                  AND lower(trim(r.location)) = ?
                ORDER BY r.created_at DESC, r.id DESC LIMIT ?
                """,  # nosec B608 - only code-defined constants are interpolated; values are bound
                (category_id, place, limit)).fetchall()]
        finally:
            conn.close()


# ---- FR-022: CSV ---------------------------------------------------------------------------

def _safe_cell(value) -> str:
    """Stop a spreadsheet treating text as a formula (CSV injection) by prefixing a quote."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def requests_to_csv(rows: list[dict], columns: list[str] | None = None) -> str:
    """Header plus exactly one row per request, with the same values the list shows.

    `columns` picks a subset (the Manager page's displayed columns); the default is all of them.
    """
    columns = columns or CSV_COLUMNS
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(columns)
    for r in rows:
        cells = {
            "Reference": r["reference"] if columns is CSV_COLUMNS else f"#{r['reference']}",
            "Title": r["title"], "Category": r["category"], "Submitted": r["submitted_at"],
            "Status": r["status"],
            "Assignee": r.get("assignee_email") or r["assignee_id"] or "Unassigned",
            "Last status change": r["last_status_changed_at"],
            "Overdue": "Yes" if r["overdue"] else "No",
        }
        writer.writerow([_safe_cell(cells[name]) for name in columns])
    return out.getvalue()
