"""Small authenticated M2 request-submission slice (FR-002, FR-005, FR-006)."""

import hmac
import os
import secrets
import sqlite3

import bcrypt
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from src.persistence import lifecycle
from src.persistence.request_service import RequestService, VersionConflict
from src.persistence.user_service import DuplicateEmailError, UserService

# Which transitions need a written explanation (FR-016, FR-018, FR-015 reopen), for the action form.
NOTE_LABELS = {"Resolved": "resolution note", "Rejected": "reason", "reopen": "reason"}


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
    password_cost = int(os.environ.get("PASSWORD_HASH_COST", "12"))
    if not 10 <= password_cost <= 16:
        raise RuntimeError("PASSWORD_HASH_COST must be between 10 and 16")
    users = UserService(db_path, password_cost)

    def hash_password(password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("password must be no longer than 72 UTF-8 bytes")
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(rounds=password_cost)
        ).decode("ascii")

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
        if request.endpoint in ("login", "register", "static"):
            return None
        user_id = session.get("user_id")
        g.current_user = query_one(
            "SELECT id, role, email FROM users WHERE id = ? AND is_active = 1", (user_id,)
        ) if isinstance(user_id, int) else None
        if g.current_user is None:
            # Keep an anonymous login form's CSRF token. Browsers request /favicon.ico
            # after /login, and that unauthenticated request must not clear the form session.
            if user_id is not None:
                session.clear()
            return redirect(url_for("login"))

    @app.context_processor
    def inject_current_user():
        # Makes current_user available to every template (base.html's nav
        # depends on it) without touching every individual render_template
        # call. g.current_user is (id, role, email) when signed in, per
        # require_login() above.
        user = g.get("current_user")
        if user is None:
            return {"current_user": None}
        return {
            "current_user": {"id": user[0], "role": user[1], "email": user[2]},
            "csrf_token": csrf_token(),
        }

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            if not valid_csrf():
                abort(400)
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = query_one(
                "SELECT id, password_hash, role FROM users WHERE lower(email) = ? AND is_active = 1",
                (email,),
            )
            password_matches = False
            if user and len(password.encode("utf-8")) <= 72:
                if user[1].startswith("$2"):
                    try:
                        password_matches = bcrypt.checkpw(
                            password.encode("utf-8"), user[1].encode("ascii")
                        )
                    except (ValueError, TypeError):
                        password_matches = False
                else:
                    password_matches = check_password_hash(user[1], password)
                    if password_matches:
                        conn = sqlite3.connect(db_path)
                        try:
                            conn.execute(
                                "UPDATE users SET password_hash = ? WHERE id = ?",
                                (hash_password(password), user[0]),
                            )
                            conn.commit()
                        finally:
                            conn.close()
            if password_matches:
                session.clear()
                session["user_id"] = user[0]
                csrf_token()
                if user[2] == "Requester":
                    return redirect(url_for("new_request_form"))
                if user[2] == "Staff":
                    return redirect(url_for("staff_queue"))
                return redirect(url_for("role_landing"))
            error = "Invalid email or password"
        return render_template("login.html", error=error, csrf_token=csrf_token())

    @app.route("/register", methods=["GET", "POST"])
    def register():
        error, email, status = None, "", 200
        if request.method == "POST":
            if not valid_csrf():
                abort(400)
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            if password != request.form.get("confirm_password", ""):
                error, status = "Passwords do not match.", 400
            else:
                try:
                    users.register_requester(email, password)
                except DuplicateEmailError as exc:
                    error, status = str(exc), 409
                except ValueError as exc:
                    error, status = str(exc), 400
                else:
                    session.clear()
                    flash("Your account is ready. Sign in to submit a request.", "success")
                    return redirect(url_for("login"))
        return render_template("register.html", error=error, email=email,
                               csrf_token=csrf_token()), status

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

    @app.route("/", methods=["GET"])
    def home():
        if g.current_user[1] == "Requester":
            return redirect(url_for("request_list"))
        if g.current_user[1] == "Staff":
            return redirect(url_for("staff_queue"))
        return redirect(url_for("role_landing"))

    @app.route("/landing", methods=["GET"])
    def role_landing():
        if g.current_user[1] not in ("Manager", "Administrator"):
            abort(403)
        return render_template("role_landing.html", role=g.current_user[1])

    @app.route("/requests", methods=["GET"])
    def request_list():
        if g.current_user[1] != "Requester":
            abort(403)
        status = request.args.get("status") or None
        try:
            requests = service.list_requester_requests(g.current_user[0], status=status)
        except ValueError as exc:
            return str(exc), 400
        return render_template(
            "requester_requests.html", requests=requests, statuses=service.STATUSES,
            selected_status=status,
        )

    @app.route("/staff/queue", methods=["GET"])
    def staff_queue():
        if g.current_user[1] != "Staff":
            abort(403)
        status = request.args.get("status") or None
        try:
            requests = service.list_staff_queue(g.current_user[0], status=status)
        except ValueError as exc:
            return str(exc), 400
        return render_template(
            "staff_queue.html", requests=requests, statuses=service.STATUSES,
            selected_status=status,
        )

    def available_transitions(detail):
        """Statuses the signed-in user may move this request to (drives the action form)."""
        role = g.current_user[1]
        found = []
        for target in lifecycle.STATUSES:
            try:
                lifecycle.check_transition(
                    role, detail["assignee_id"] == g.current_user[0], detail["status"], target)
            except (PermissionError, ValueError):
                continue
            found.append(target)
        return found

    def detail_page(request_id: int, error=None, status_code=200, form=None):
        try:
            detail = service.get_request_detail(g.current_user[0], request_id)
        except LookupError:
            abort(404)
        except PermissionError:
            abort(403)
        role = g.current_user[1]
        staff = service.list_active_staff() if role == "Manager" else []
        can_comment = detail["assignee_id"] is not None and (
            role == "Manager"
            or (role == "Requester")
            or (role == "Staff" and detail["assignee_id"] == g.current_user[0]))
        return render_template(
            "request_detail.html", request=detail, csrf_token=csrf_token(),
            can_accept=(role == "Staff" and detail["status"] == "New"
                        and detail["assignee_id"] is None),
            transitions=available_transitions(detail), staff_options=staff,
            can_comment=can_comment, notes_required=NOTE_LABELS, error=error,
            form=form or {},
        ), status_code

    def workflow_error(request_id: int, exc: Exception, form):
        """Map a workflow failure to an HTTP status and re-show the request with the reason."""
        if isinstance(exc, LookupError):
            abort(404)
        if isinstance(exc, PermissionError):
            abort(403)
        if isinstance(exc, VersionConflict):
            return detail_page(request_id, error=str(exc), status_code=409, form=form)
        return detail_page(request_id, error=str(exc), status_code=400, form=form)

    def expected_version_or_400():
        try:
            value = int(request.form.get("expected_version", ""))
        except ValueError:
            abort(400)
        if value < 0:
            abort(400)
        return value

    @app.route("/requests/<int:request_id>", methods=["GET"])
    def request_detail(request_id: int):
        return detail_page(request_id)

    @app.route("/requests/<int:request_id>/status", methods=["POST"])
    def change_request_status(request_id: int):
        if not valid_csrf():
            abort(400)
        if g.current_user[1] not in ("Staff", "Manager"):
            abort(403)
        version = expected_version_or_400()
        try:
            service.change_status(
                request_id, g.current_user[0], request.form.get("target_status", ""),
                version, request.form.get("note", ""))
        except (LookupError, PermissionError, ValueError, VersionConflict) as exc:
            return workflow_error(request_id, exc, request.form)
        flash("Status updated.", "success")
        return redirect(url_for("request_detail", request_id=request_id))

    @app.route("/requests/<int:request_id>/assign", methods=["POST"])
    def assign_request(request_id: int):
        if not valid_csrf():
            abort(400)
        if g.current_user[1] != "Manager":
            abort(403)
        version = expected_version_or_400()
        try:
            service.assign_request(
                request_id, g.current_user[0], int(request.form.get("assignee_id", "0") or 0),
                version)
        except (LookupError, PermissionError, ValueError, VersionConflict) as exc:
            return workflow_error(request_id, exc, request.form)
        flash("Assignment saved.", "success")
        return redirect(url_for("request_detail", request_id=request_id))

    @app.route("/requests/<int:request_id>/comments", methods=["POST"])
    def add_request_comment(request_id: int):
        if not valid_csrf():
            abort(400)
        try:
            service.add_comment(request_id, g.current_user[0], request.form.get("body", ""))
        except (LookupError, PermissionError, ValueError) as exc:
            return workflow_error(request_id, exc, request.form)
        flash("Comment added.", "success")
        return redirect(url_for("request_detail", request_id=request_id))

    @app.route("/staff/requests/<int:request_id>/accept", methods=["POST"])
    def accept_request(request_id: int):
        if g.current_user[1] != "Staff":
            abort(403)
        if not valid_csrf():
            abort(400)
        try:
            expected_version = int(request.form.get("expected_version", ""))
        except ValueError:
            return "expected_version must be an integer", 400
        if expected_version < 0:
            return "expected_version must be non-negative", 400
        if not service.accept_request(request_id, g.current_user[0], expected_version):
            return "Request cannot be accepted in its current state", 409
        return redirect(url_for("request_detail", request_id=request_id))

    @app.route("/notifications", methods=["GET"])
    def notifications():
        if g.current_user[1] != "Requester":
            abort(403)
        items = service.list_notifications(g.current_user[0])
        return render_template("notifications.html", notifications=items)

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app("civicconnect.sqlite").run(debug=False)
