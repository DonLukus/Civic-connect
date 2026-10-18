### 2026-10-18 - Consolidate verified README corrections from #93 into #92
**Who:** Don, with Claude Code assistance (AI-055) - **Type:** documentation
**What:** On top of PR #92's README: added a Licence section (no licence chosen, no LICENSE file), said plainly that no `.env` file is read, named Utilities as the only seeded category, added the 72-byte bootstrap password limit and the two-command staging demo. PR #93 is superseded by #92 once this is merged.
**Evidence:** Each statement checked against `wsgi.py`, `user_service.py`, `app.py`, `requirements*.txt`; all README links resolve. No code changed.
**Review:** Needs two non-author approvals (Emile's #92 content, Don's additions: Masego and one other member).
