# CLAUDE.md

Context for Claude Code when working in this repository. Read this fully before making any change.

## What this project is

CivicConnect: a service request management platform for SEN381 (Software Engineering 381),
a university module at Belgium Campus ITversity. Team of three: Masego, Don, Emile.

The module runs through four milestones. **Milestone 1 (M1) is baselined and complete** as of
2026-09-08. You are most likely being asked to help with M2 (Architecture, Design & Engineering
Decisions) or with polishing M1 evidence before submission — check what the user actually asks
before assuming which.

## Read these two files before anything else

1. **`PROJECT_RULES.md`** — the rules, roles, identifier scheme, AI-use policy, git conventions,
   branch protection settings and definition of done. This governs how you must work in this repo.
2. **`PROJECT_HISTORY.md`** — the dated log of what has actually happened. Read the most recent
   entries to know the current state before proposing anything.

Do not duplicate content from either file in your responses — read them, then act consistently
with them.

## The one rule that overrides normal helpfulness

**M1 content is baselined.** Everything under `docs/requirements/`, `docs/stakeholders/`,
`docs/risk/risk-register.csv`, `docs/decisions/decision-log.csv`, and `docs/PED/` sections 2–10
represents the team's signed-off engineering commitment for Milestone 1.

- Do not silently edit, delete, renumber, or "improve" any baselined identifier (`FR-`, `NFR-`,
  `SH-`, `CF-`, `SCOPE-`, `CN-`, `RSK-`, `AS-`, `DEC-`, `FEC-`, `TR-`, `AI-`).
- If asked to change something baselined, first check whether a change request exists under
  `docs/change/`. If not, tell the user this needs one (template is at
  `docs/change/change-request-template.md`) rather than just making the edit.
- Identifiers are never reused and never renumbered, even if deleted. The next one always
  increments from the highest number that has ever existed for that prefix.

## Two decisions are deliberately not made yet

- **DEC-007** (file attachments) and **DEC-008** (technology stack, architecture, hosting) are
  recorded as *deferred*, not decided. Do not pick a tech stack, scaffold a framework, or start
  writing application code on the assumption of a particular stack unless the user has explicitly
  told you DEC-008 has now been resolved and tells you what was chosen.
- If the user asks you to "just start building" something that depends on DEC-008 (a database
  schema, an API, a UI), say so and ask what was decided, rather than guessing a stack.

## The four right-hand columns of the RTM are meant to be empty

`docs/requirements/RTM.csv` has columns for Design (M2), Issue/PR (M3), Test (M3), and Release (M4)
evidence. These are intentionally blank at M1. Only fill them in as that real evidence is produced
in a later milestone — filling them in early is fabricated evidence and will cost the team marks.

## Every substantive change needs a pull request

Never commit directly to `main` — it is branch-protected and the push will be rejected anyway.
Create a branch (`docs/`, `feat/FR-nnn-`, `fix/`, `chore/` — see `PROJECT_RULES.md` §9), commit
there, and tell the user to open a pull request. You cannot merge it yourself: the repo requires
two human approvals from people other than the author, and self-approval is disabled at the
platform level.

## Commit messages

Format: `type(scope): summary (refs #issue)` — see `PROJECT_RULES.md` §9 for the type list and
examples. Reference the artefact identifier where one applies.

## AI use is logged, not silent

If you generate or materially change requirements, risk entries, decisions, or other controlled
content, tell the user what you produced and what they should verify — they are required to record
it in `docs/governance/ai-usage-register.csv` with the verification actually performed. Do not let
AI-authored content merge without that. If you know you materially contributed to something, say so
explicitly rather than leaving it to be discovered.

## Traceability is checked automatically

`.github/workflows/docs-check.yml` fails the build if:
- an RTM row references a requirement identifier that doesn't exist in `functional-requirements.csv`
  or `non-functional-requirements.csv`
- a requirement exists but isn't traced in the RTM
- a traced row has no acceptance-criteria reference

If you touch requirements or the RTM, mentally run this check yourself before handing back: does
every identifier you referenced actually exist, and does every requirement you added appear in the
RTM row-for-row?

`.github/workflows/secret-scan.yml` blocks common credential patterns and tracked `.env`/key files.
Never commit a real or example credential that could trip this — use placeholder values like
`YOUR_API_KEY_HERE` in any example config you write.

## Folder map

```
docs/PED/                    PED sections as Markdown (source of truth) — compile to Word at baseline
docs/requirements/           FR, NFR, scope baseline, RTM (all CSV)
docs/stakeholders/           Stakeholder and conflict registers (CSV)
docs/risk/                   Risk and assumption registers (CSV)
docs/decisions/              Decision log (CSV) + docs/decisions/adr/ for M2 onward
docs/forward-engineering/    Forward engineering considerations (Markdown)
docs/governance/             Working agreement, AI usage register (CSV)
docs/change/                 Change request template — use before editing baselined content
docs/baseline/               M1 sign-off record
src/, tests/                 Empty by design until M2/M3 — see PED §14 for why
```

## Tone

This is a graded university submission, not a toy project. Precision matters more than speed:
a plausible-sounding requirement with no real source, or a risk with a vague cause, costs marks
directly. When drafting content for the team, prefer being specific and testable over sounding
complete. If you don't have enough information to write something properly, say what's missing
rather than filling the gap with something generic.
