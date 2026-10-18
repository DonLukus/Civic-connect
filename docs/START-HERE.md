# Start here

CivicConnect lets residents report a problem, staff and managers work it through to closure, and
everyone see exactly what happened and when. It is one small Flask application with a SQLite
database. Nothing here needs a build step.

## Find what you need in one step

| I want to... | Open |
|---|---|
| Run it and try it | [README: Quick start](../README.md#local-setup) (two commands for a full demo) |
| Understand how it is built | [ARCHITECTURE.md](ARCHITECTURE.md): one page, three diagrams |
| See which code and test delivers a requirement | [REQUIREMENTS-MAP.md](REQUIREMENTS-MAP.md) |
| Read the original requirements and acceptance criteria | [requirements/](requirements/): `functional-requirements.csv`, `non-functional-requirements.csv`; traceability in `RTM.csv` |
| Know why a technical choice was made | [decisions/](decisions/): `adr/` (architecture), `decision-log.csv` (all decisions), `DEC-019-lifecycle-transition-table.md` (open proposal) |
| See proof that it works | [release/evidence/2026-10-18-m4/](release/evidence/2026-10-18-m4/README.md): load test, live journeys, restart, restore |
| See project status, risks and limits | [PED section 23](PED/23-final-scope-and-project-conclusion.md), [release summary](release/m3-release-evidence-summary.md), [risk register](risk/risk-register.csv) |
| See what changed and when | [history/](history/README.md) (newest entries) and `../PROJECT_HISTORY.md` (earlier archive); `python tools/history.py` prints both |
| Follow the team's rules | [PROJECT_RULES.md](../PROJECT_RULES.md) |

## The code in one glance

```
src/web/app.py           every page and form (routes), sign-in, CSRF, role checks
src/web/templates/       the HTML pages     src/web/static/style.css   the one stylesheet
src/persistence/         everything that touches the database (see ARCHITECTURE.md)
tests/                   what is proven, one file per area
scripts/ performance/    live checks: demo launcher, journeys, load test, backup/restore, layout
docs/                    requirements, decisions, evidence, history (this folder)
```

Three habits keep this folder easy to read: one fact lives in one place and everything else links to
it; every claim names the file or test that proves it; limits are stated next to the claim.
