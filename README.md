#  CivicConnect

> A community service request platform that brings order to chaos.

**Status:** Milestone 2 (Proof-of-Concept) | **Production Ready:** No | **License:** MIT

---

##  What This Does

CivicConnect solves a critical problem: **citizen service requests are scattered across email, phone, WhatsApp, spreadsheets, and paper.** Nobody can track progress, requests get lost or duplicated, and accountability is impossible.

**Our solution:**
-  One shared, controlled record for all requests
-  Permanent audit trail of every change
-  Role-based access control (Requester, Staff, Manager)
-  Real-time status tracking
-  Lightweight and cost-effective to run

**Built for:** Municipal governments, nonprofits, service organizations.

---

##  Project Status

| Aspect | Status |
|--------|--------|
| **Milestone 1** | ✅ Complete |
| **Milestone 2** | 🔄 In Progress (Architecture & Design) |
| **Core Slice** | ✅ Traced (Request Submission + Acceptance) |
| **Login PoC** | ✅ Functional (Single Account) |
| **Admin Panel** | ❌ Not Started |
| **Staff Dashboard** | ❌ Not Started |
| **Reports** | ❌ Not Started |
| **Notifications** | 🔄 Partial (Outbox pattern implemented) |

---

##  Quick Start

### Prerequisites

- **Python 3.11+** (tested on Python 3.14)
- **pip** (Python package manager)
- **Git**

### Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/DonLukus/Civic-connect.git
cd Civic-connect

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values (see below)

# 5. Run locally (development)
flask --app wsgi:app run

# 6. Access the app
# Open http://127.0.0.1:5000/login in your browser
```

### Environment Configuration

Create a `.env` file in the project root (never commit this):

```bash
# Application
FLASK_ENV=development
SECRET_KEY=<generate-a-random-string-here>  # Use: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Database (local dev uses SQLite)
DATABASE_URL=civicconnect.sqlite

# Session Security (set to 'true' only behind HTTPS)
SESSION_COOKIE_SECURE=false

# Authentication
PASSWORD_HASH_ROUNDS=160
BOOTSTRAP_REQUESTER_EMAIL=demo@example.com
BOOTSTRAP_REQUESTER_PASSWORD=<secure-password>

# Email / Notifications (optional for PoC)
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_FROM_ADDRESS=noreply@example.com
OUTBOX_WORKER_POLL_SECONDS=60
```

**🔒 Security Notes:**
- `SECRET_KEY` must be a cryptographically random string—never use a fixed value
- `BOOTSTRAP_REQUESTER_PASSWORD` is hashed with bcrypt; never store plaintext passwords
- `.env` is in `.gitignore`—never commit it
- Use a secret manager (e.g., Render Secrets, AWS Secrets Manager) in production

---

## 📦 Deployment on Render

### Step 1: Prepare for Render

Render uses **Gunicorn** (Linux-only) instead of Flask's dev server. The repo includes `gunicorn` in `requirements.txt`.

### Step 2: Create Render Service

1. Go to **[render.com](https://render.com)** and sign up
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo (`DonLukus/Civic-connect`)
4. Configure:
   - **Name:** `civic-connect`
   - **Environment:** `Python 3.11`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --workers 4 --bind 0.0.0.0:10000 wsgi:app`
   - **Instance Type:** Free tier (or higher for production)

### Step 3: Set Environment Variables in Render

In Render dashboard, go to **Settings** → **Environment** and add:

```
FLASK_ENV=production
SECRET_KEY=<generate-new-random-value>
DATABASE_URL=/var/data/civicconnect.sqlite
SESSION_COOKIE_SECURE=true
PASSWORD_HASH_ROUNDS=160
BOOTSTRAP_REQUESTER_EMAIL=<demo-email>
BOOTSTRAP_REQUESTER_PASSWORD=<demo-password>
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM_ADDRESS=<your-email>
OUTBOX_WORKER_POLL_SECONDS=60
```

### Step 4: Deploy

Push to `main` branch—Render will auto-deploy:

```bash
git add .
git commit -m "chore: Prepare for Render deployment"
git push origin main
```

Monitor deployment in Render dashboard.

### Step 5: Database Persistence

SQLite on Render's free tier is ephemeral. For production:
- **Option A:** Use [Render PostgreSQL](https://render.com/docs/postgres)
- **Option B:** Use [S3](https://aws.amazon.com/s3/) for backups
- **Option C:** Upgrade to [Render Persistent Disk](https://render.com/docs/persistent-disk)

Current configuration uses `civicconnect.sqlite` which will be lost on redeploy. Upgrade for production.

---

## 🧪 Running Tests

All 15 tests pass locally and run on every PR via GitHub Actions.

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_request_submission.py::test_create_request_succeeds_with_valid_data -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

**Test Coverage:**
-  Request creation (FR-005, FR-006)
-  Validation (required fields, category list)
-  End-to-end web flow (login → submit → confirm)
-  Race condition prevention (FR-014: concurrent acceptance)
-  Authentication & CSRF protection
-  Role-based access control
-  Bootstrap & WSGI startup

---

##  Project Structure

```
CivicConnect/
├── src/
│   ├── persistence/          # Database layer
│   │   ├── schema.sql        # SQLite DDL
│   │   ├── request_service.py    # Business logic (create, accept requests)
│   │   ├── request_repository.py # Data access (deprecated—use service)
│   │   ├── lifecycle.py       # Status transition rules
│   │   └── outbox.py          # Notification queue processor
│   │
│   └── web/
│       ├── app.py            # Flask app, routes, auth
│       └── templates/        # HTML templates (login, forms, confirmation)
│
├── tests/                     # Pytest suite (15 tests)
│   ├── test_request_submission.py    # FR-005, FR-006, web flows
│   ├── test_request_acceptance.py    # FR-014, concurrent safety
│   ├── test_lifecycle_validator.py   # FR-015 status rules
│   └── test_wsgi_bootstrap.py        # Startup & schema
│
├── docs/                      # Master project documentation
│   ├── PED/                   # Project Engineering Document
│   ├── decisions/adr/         # Architecture Decision Records
│   ├── requirements/          # Functional & non-functional requirements
│   ├── risk/                  # Risk register
│   └── deployment/            # Deployment guidance
│
├── wsgi.py                    # Production entry point (Render, Gunicorn)
├── requirements.txt           # Python dependencies (pinned versions)
├── .env.example               # Environment template (never commit .env)
├── .gitignore                 # Secrets, build artifacts, caches
└── README.md                  # This file
```

---

##  Security & Secret Key Management

### How Secrets Are Handled

- **`SECRET_KEY`**: Used for Flask session signing. **Must be random and unique per environment.**
- **`PASSWORD_HASH_ROUNDS`**: Iteration count for bcrypt (higher = slower but more secure).
- **Bootstrap credentials**: Hashed with bcrypt—**never stored plaintext.**
- **Audit trail**: Every action is logged with actor ID, timestamp, and previous state.

### Generating a Secure SECRET_KEY

```bash
# In Python:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# In bash:
openssl rand -base64 32
```

### Secrets in Render

1. **Never** put secrets in code or `.env` that's committed
2. Use Render's **Environment** secrets (encrypted at rest)
3. Rotate `SECRET_KEY` periodically
4. Use strong, unique `BOOTSTRAP_REQUESTER_PASSWORD`
5. For production, use a dedicated auth service (Keycloak, Auth0)

### CSRF Protection

- All forms include CSRF tokens (Jinja2 `{{ csrf_token }}`)
- Tokens are session-bound and validated on POST
- CSRF failures return 400 Bad Request

---

##  Performance & Optimization

### Current Bottlenecks

1. **SQLite:** File-based database—safe for testing, not for production scale
   - **Fix:** Migrate to PostgreSQL (free tier on Render)

2. **Connection pooling:** Each request creates a new DB connection
   - **Fix:** Implement connection pool (see `Performance Issues` section of docs)

3. **Category caching:** Categories loaded on every request
   - **Fix:** Cache in memory with TTL or use Redis

4. **No request pagination:** All data fetched at once
   - **Fix:** Implement `LIMIT`/`OFFSET` pagination

### Optimizations in Progress

- ✅ Proper transaction isolation (`BEGIN IMMEDIATE`)
- ✅ Indexes on frequently queried columns (`status`, `assignee_id`, `created_at`)
- ✅ Audit trail stored efficiently in JSON
- 🔄 Outbox pattern for reliable notifications (partial)

---

## 🐛 Known Issues & Limitations

| Issue | Severity | Status | Fix |
|-------|----------|--------|-----|
| SQLite on Render is ephemeral | 🔴 High | Open | Migrate to PostgreSQL |
| No rate limiting on login | 🔴 High | Open | Add Flask-Limiter |
| Database connections not pooled | 🟠 Medium | Open | Add SQLAlchemy pool |
| Only 1 PoC requester account | 🟠 Medium | Open | Build user admin panel |
| Staff dashboard not started | 🟠 Medium | Open | Implement in M3 |
| Notifications manual-triggered | 🟡 Low | Open | Add scheduler (APScheduler) |

---

##  Learn More

| Want to Know | See |
|---|---|
| **Problem statement & scope** | [`docs/PED/`](docs/PED/) |
| **What we promised to build** | [`docs/requirements/`](docs/requirements/) |
| **Why we made technical choices** | [`docs/decisions/adr/`](docs/decisions/adr/) |
| **What could go wrong** | [`docs/risk/risk-register.csv`](docs/risk/risk-register.csv) |
| **How the team works** | [`PROJECT_RULES.md`](PROJECT_RULES.md) |
| **Project history & milestones** | [`PROJECT_HISTORY.md`](PROJECT_HISTORY.md) |

---

##  Technology Stack

| Component | Technology | Version | License |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.11+ | – |
| **Web Framework** | Flask | 3.1.3 | BSD-3-Clause |
| **Database** | SQLite / PostgreSQL | – | Public Domain / PG License |
| **Testing** | Pytest | 9.1.1 | MIT |
| **Password Hashing** | Werkzeug | – | BSD-3-Clause |
| **Production Server** | Gunicorn | 26.2.0 | MIT |

---

##  Contributing

This is a university project with structured governance. See [`PROJECT_RULES.md`](PROJECT_RULES.md) for:
- Branch naming conventions
- Code review requirements (2+ approvals)
- Commit message standards
- Issue triaging workflow

---

## 📄 License

MIT License — See LICENSE file.

---

##  Team

- **Don** (Workstream B): Backend architecture, database, business logic
- **Masego** (Workstream A): Frontend, UI/UX
- **Emile** (Workstream C): Deployment, DevOps, documentation

---

##  Support

For issues, feature requests, or questions:
1. Check [`docs/risk/`](docs/risk/) for known issues
2. Open an issue on GitHub (tag with `bug`, `enhancement`, or `question`)
3. Refer to architecture decisions in [`docs/decisions/adr/`](docs/decisions/adr/)

---

**Last Updated:** 2026-10-01 | **Next Milestone:** M3 (Testing & Release Readiness)
