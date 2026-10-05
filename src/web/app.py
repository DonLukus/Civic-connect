"""Small authenticated M2 request-submission slice (FR-002, FR-005, FR-006)."""

import hmac
import os
import secrets
import sqlite3

from flask import Flask, abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from src.persistence.request_service import RequestService


def create_app(db_path: str, secret_key: str | None = None) -> Flask:
    secret_key = secret_key or os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be configured before starting CivicConnect")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    )
    service = RequestService(db_path)

    def query_one(sql: str, parameters=()):
        conn = sqlite3.connect(db_path)
        try:
            return conn.execute(sql, parameters).fetchone()
        finally:
            conn.close()

    def active_categories():
        conn = sqlite3.connect(db_path)
        try:
            return conn.execute(
                "SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name"
            ).fetchall()
        finally:
            conn.close()

    def csrf_token():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_urlsafe(32)
        return session["_csrf_token"]

    def valid_csrf():
        supplied = request.form.get("csrf_token", "")
        return bool(supplied) and hmac.compare_digest(supplied, session.get("_csrf_token", ""))

    @app.before_request
    def require_login():
        if request.endpoint == "login":
            return None
        user_id = session.get("user_id")
        g.current_user = query_one(
            "SELECT id, role FROM users WHERE id = ? AND is_active = 1", (user_id,)
        ) if isinstance(user_id, int) else None
        if g.current_user is None:
            session.clear() if user_id is not None else None
            return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            if not valid_csrf():
                abort(400)
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = query_one(
                "SELECT id, password_hash FROM users WHERE lower(email) = ? AND is_active = 1",
                (email,),
            )
            if user and check_password_hash(user[1], password):
                session.clear()
                session["user_id"] = user[0]
                csrf_token()
                return redirect(url_for("new_request_form"))
            error = "Invalid email or password"
        return render_template("login.html", error=error, csrf_token=csrf_token())

    @app.route("/logout", methods=["POST"])
    def logout():
        if not valid_csrf():
            abort(400)
        session.clear()
        return redirect(url_for("login"))

    @app.route("/requests/new", methods=["GET"])
    def new_request_form():
        if g.current_user[1] != "Requester":
            abort(403)
        return render_template(
            "new_request.html", categories=active_categories(), error=None, values={},
            csrf_token=csrf_token(),
        )

    @app.route("/requests", methods=["POST"])
    def submit_request():
        if not valid_csrf():
            abort(400)
        if g.current_user[1] != "Requester":
            abort(403)
        form = request.form
        try:
            request_id = service.create_request(
                requester_id=g.current_user[0],
                category_id=int(form.get("category_id", 0) or 0),
                title=form.get("title", ""),
                description=form.get("description", ""),
                location=form.get("location", ""),
            )
        except ValueError as exc:
            return render_template(
                "new_request.html", categories=active_categories(), error=str(exc),
                values=form, csrf_token=csrf_token(),
            ), 400

        return redirect(url_for("request_submitted", request_id=request_id))

    @app.route("/requests/<int:request_id>/submitted", methods=["GET"])
    def request_submitted(request_id: int):
        if g.current_user[1] != "Requester":
            abort(403)
        owner = query_one("SELECT requester_id FROM requests WHERE id = ?", (request_id,))
        if owner is None or owner[0] != g.current_user[0]:
            abort(404)
        return render_template("confirmation.html", request_id=request_id)

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app("civicconnect.sqlite").run(debug=False)
