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

The full export includes **every numbered source file currently present here**, beginning with `00-document-control.md`, retaining the M1/M2 sections, and continuing through `22-m3-construction-verification-release.md`. It is not a standalone section-22 report. Historical content and signatures retain their original dates and scope. No section 18 source currently exists; the builder preserves that gap rather than inventing or renumbering a section.

Install the documentation dependencies with `python -m pip install -r requirements-docs.txt`, then run:

```text
python tools/build_m3_review_pdf.py --build-date 2026-10-17 --render-dir .m3-local/pdf-review/pages
```

The output is `docs/PED/exports/PED_v3.0-review.pdf`. The builder works from any current directory, includes a linked contents page and bookmarks, renders Markdown strikethrough, and presents registers with six or more columns as labelled records so their fields remain readable. All original rows/fields remain included. Use `--output PATH` for a separate review copy and set `--build-date` to the actual export date.

After writing the PDF, the builder checks for body content from every source section and rejects literal unrendered strikethrough. It writes a source/hash manifest and optional page previews under ignored `.m3-local/`. Inspect those previews and review the exact exported revision before submission. A clean build is not a new team approval, signature, production-readiness claim or proof that a missing source section exists.

## M4 closure continuation

Section 23 contains the final-scope/acceptance analysis, register consequences, deployment recommendation, demonstration/defence preparation and Group U submission block. This is a v4.0 review candidate, not a signed Final submission. Use `python tools/build_m3_review_pdf.py --ped-version 4.0 --build-date 2026-10-18 --render-dir .m3-local/m4-pdf/pages` to produce `exports/PED_v4.0-review.pdf`; preserve all earlier sections and the explicit absent section 18. The existing RTM owns the detailed QA scores; the section-23 table is its generated view.
