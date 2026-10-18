### 2026-10-18 - CI coverage report and gate (NFR-009); full verification of main
**Who:** Don, with Claude Code assistance (AI-058) - **Type:** CI, verification
**What:** `quality.yml` now runs pytest with `pytest-cov`, prints per-file missing lines and fails below 70% of `src/`. Re-verified `main` (af2f545): 60 tests pass, 83% coverage (`request_service.py` 91%, `user_service.py` 90%, `app.py` 91%, `outbox.py` 64%), Ruff clean, Bandit no medium/high findings, `pip-audit` no known vulnerabilities.
**Evidence:** Local run on Python 3.14.3 (CI uses 3.11, not yet observed with this change). The gate was shown to fail when coverage is low. This does not make the check required to merge; that is a ruleset setting (see the governance record).
**Review:** Needs two non-author approvals; `.github/` is owned by Don in CODEOWNERS.
