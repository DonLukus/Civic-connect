"""
CivicConnect — M2 traced slice: "Citizen submits a service request" (ADR-001, FR-005, FR-006).

Server-rendered, single-process frontend (ADR-001 frontend recommendation A) calling directly
into RequestService - no separate API layer yet, consistent with the single-deployable-unit
conclusion in PED §5.1.

Known limitation, stated rather than hidden (PED §15.1 style): FR-001..FR-004 (authentication)
are not built yet. DEC-006 requires authenticated submission only, so this stands in a fixed
demo requester until real auth exists - REQUESTER_ID below is that stand-in, not a design
decision. Do not read this as "login is done".
"""

import sqlite3

from flask import Flask, redirect, render_template, request, url_for

from src.persistence.request_service import RequestService

REQUESTER_ID = 1  # stand-in for authenticated session user until FR-001..FR-004 exist


def create_app(db_path: str) -> Flask:
    app = Flask(__name__)
    service = RequestService(db_path)

    def active_categories():
        # Explicit close - `with sqlite3.connect(...)` commits/rolls back but never closes
        # (stdlib behaviour); a long-running app calling this per-request would otherwise leak
        # a connection on every page view.
        conn = sqlite3.connect(db_path)
        try:
            return conn.execute(
                "SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name"
            ).fetchall()
        finally:
            conn.close()

    @app.route("/requests/new", methods=["GET"])
    def new_request_form():
        return render_template("new_request.html", categories=active_categories(), error=None, values={})

    @app.route("/requests", methods=["POST"])
    def submit_request():
        form = request.form
        try:
            request_id = service.create_request(
                requester_id=REQUESTER_ID,
                category_id=int(form.get("category_id", 0) or 0),
                title=form.get("title", ""),
                description=form.get("description", ""),
                location=form.get("location", ""),
            )
        except ValueError as exc:
            return render_template(
                "new_request.html",
                categories=active_categories(),
                error=str(exc),
                values=form,
            ), 400

        return redirect(url_for("request_submitted", request_id=request_id))

    @app.route("/requests/<int:request_id>/submitted", methods=["GET"])
    def request_submitted(request_id: int):
        return render_template("confirmation.html", request_id=request_id)

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app("civicconnect.sqlite").run(debug=True)
