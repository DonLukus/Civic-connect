# Project Engineering Document

One evolving record across all four milestones (Master Project Brief section 6). Not four reports.

| Version | Milestone | Adds |
|---|---|---|
| v1.0 | M1 | Problem, stakeholders, scope, requirements, constraints, risk, process, governance, baseline |
| v2.0 | M2 | Architecture, design, technology, data, UI, APIs, ADRs, trade-offs |
| v3.0 | M3 | Change impact, construction, CI, testing, quality, security, release readiness |
| v4.0 | M4 | Final success evaluation, deployment evidence, stakeholder validation, decision consequences |

Sections are authored as separate Markdown files here so that changes are reviewable as diffs
(DEC-002), then compiled to `exports/`. Baselined content is never silently overwritten — changes go
through `docs/change/change-request-template.md`.


## M3 review export

Current review index: `22-m3-construction-verification-release.md`; existing M1/M2 section sources remain authoritative. Regenerate from repository root with `python -m pip install -r requirements-docs.txt` then `python tools/build_m3_review_pdf.py`. The builder writes `exports/PED_v3.0-review.pdf` and ignored local page previews. The review export must be regenerated with actual final release identity and approvals before it is called the signed M3 baseline.
