# Project Rules

The constant reference for this project. Any team member or AI assistant should be able to read this
file and understand the rules, roles, scope and workflow without further explanation.

Read alongside `PROJECT_HISTORY.md` (what has happened) and the PED (what is true about the project).

---

## 1. Roles

| Member | Workstream | Owns |
|---|---|---|
| Masego | A | Problem, stakeholders, scope, constraints, assumptions, decision log |
| Don | B | Requirements, acceptance criteria, RTM, forward engineering, **repository setup and governance** |
| Emile | C | Risk, team working agreement, AI control, document control, PED assembly, baseline |

Ownership means drafting responsibility. It does **not** limit accountability: every member is
accountable for the whole project and may be examined on any artefact.

## 2. Standard operating procedure

Every substantive contribution follows this sequence, without exception.

1. **Check the rules.** This file and the PED govern. If a request contradicts them, raise it before acting.
2. **Plan before implementing.** State the goal, why it matters to the project, and the steps — before producing anything.
3. **Work on a branch.** Never commit directly to `main`.
4. **Open a pull request.** Describe what changed, why, which identifiers are affected, and the RTM impact.
5. **Get two approvals** from members other than the author.
6. **Update the affected registers and the RTM** in the same change.
7. **Add a `PROJECT_HISTORY.md` entry.**

## 3. Decision rules

- **Do not invent.** If information is missing, say so and ask. An explicit knowledge gap is acceptable; a plausible guess is not.
- **Ambiguity stops work.** If a request is unclear, contradicts the scope, or breaks a rule, ask before proceeding.
- **Propose better alternatives.** If there is a simpler approach that meets the requirement and industry practice, propose it before executing the requested one.
- **Simplicity wins.** Use the simplest approach that is accurate and relevant.
- **No redundancy.** One fact lives in one place. Everything else references it.
- **Defer honestly.** A decision without sufficient evidence is recorded as deferred, with the evidence required stated. It is never guessed and recorded as decided.

## 4. Scope discipline

The scope baseline in `docs/requirements/scope-baseline.csv` is **baselined**. After baseline it
changes only through a change request with impact analysis (`docs/change/change-request-template.md`).

Every additional feature creates obligations to specify, design, secure, implement, test, document,
deploy and maintain it. A smaller controlled solution scores better than a larger unfinished one.
**Additional features do not automatically attract additional marks.**

## 5. Identifier scheme (DEC-003)

`SH-nn` stakeholder · `CF-nn` conflict · `SCOPE-I/O/D-nn` scope · `CN-nn` constraint ·
`FR-nnn` / `NFR-nnn` requirement · `AC-nnn` / `AC-Nnnn` acceptance criterion · `TR-nnn` trace ·
`RSK-nn` risk · `AS-nn` assumption · `DEC-nnn` decision · `FEC-nn` forward consideration ·
`AI-nnn` AI usage · `CHG-nnn` change request · `TST-nnn` test · `DEF-nnn` defect

Identifiers are **never reused and never renumbered** after baseline.

## 6. AI use

AI is a permitted engineering assistant. It is not an author and it does not carry accountability.

- Material AI contributions are recorded in `docs/governance/ai-usage-register.csv` with the verification actually performed.
- Every pull request declares whether AI assisted.
- AI-generated content passes the same branch, review and approval controls as human content.
- Never expose credentials, confidential material or personal data to an external AI system.
- You must be able to explain, defend and modify anything AI helped you produce.
- **"AI generated it" is never an acceptable engineering defence.**

### Giving an AI assistant a task

Provide three things and it will behave consistently regardless of model or member:

1. This file — the rules.
2. `PROJECT_HISTORY.md` — the current state.
3. The specific issue — what is required now.

Then apply step 2 of the SOP: the assistant states the goal, the relevance and the plan **before** producing anything.

## 7. Quality bar

- Every requirement has an ID, a source, a priority and acceptance criteria.
- Every quality claim has a number and a method. The words *fast*, *secure*, *scalable* and *user-friendly* are banned without one.
- Every risk has a specific cause, an owner, and a contingency that differs from its mitigation.
- Every decision records its alternatives, rationale, trade-offs and downstream consequence.
- Every claim presented to an assessor is traceable to a controlled artefact.

## 8. What good looks like

If another engineer — or another AI — opened this repository with no prompt, they should be able to
work out the project rules, roles, scope, current state and workflow without asking anyone.
If they cannot, the documentation has failed regardless of how complete it looks.

---

## 9. Git conventions

**Branches** — `docs/<area>`, `feat/FR-nnn-<desc>`, `fix/<issue>-<desc>`, `chore/<desc>`

**Commits** — `type(scope): summary (refs #issue)` where type is `docs`, `feat`, `fix`, `chore`,
`test` or `refactor`. Reference the artefact identifier where one applies.

```
docs(requirements): add FR-011..FR-018 staff queue requirements (refs #12)
docs(risk): raise RSK-04 impact to 3 after review (refs #19)
```

Commit as you work. Repository history is assessed — bulk uploads before a milestone do not
demonstrate a controlled process and may receive no credit.

## 10. Branch protection on `main`

Owned by Don.

| Setting | Value |
|---|---|
| Require a pull request before merging | On |
| Required approvals | 2 |
| Dismiss stale approvals on new commits | On |
| Require conversation resolution | On |
| Do not allow bypassing the above | On |
| Block force pushes and deletions | On |
| Secret scanning + push protection | On |

**Verify, do not just claim.** Try a direct push to `main` and try to approve your own pull request.
Both must be refused. Keep that evidence.

> Branch protection is unavailable on some GitHub plans for private repositories. If the settings
> are greyed out: make the repository public (there are no secrets in it — that is what NFR-005
> guarantees), or claim GitHub Pro free through the Student Developer Pack. Confirm which applies
> before relying on the control in a presentation.

## 11. Reviewing

Approval must reflect meaningful review; rubber-stamping may receive no credit. "LGTM" on a
substantive change is not review.

Check every time: **traceability** (does every identifier exist?), **testability** (could someone
else verify this?), **consistency** (does it contradict anything baselined?), **specificity** (would
it survive "how do you know?"), **scope** (does it quietly add scope?), **AI declaration**,
**defensibility** (could the author explain it to an assessor?).

A useful comment says what you checked, one specific finding, and your decision. Three sentences.

## 12. Definition of done

- [ ] On a branch, pull request opened with the template completed including the AI declaration
- [ ] Two approvals from members other than the author; every conversation resolved
- [ ] Identifiers follow the scheme; every referenced identifier exists
- [ ] RTM and affected registers updated
- [ ] `PROJECT_HISTORY.md` entry added
- [ ] From M3: linked to a requirement, tests passing, static analysis clean, no secret committed
