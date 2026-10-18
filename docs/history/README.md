# Project history entries

One Markdown file per significant change, named `YYYY-MM-DD-short-slug.md` (for example
`2026-10-19-add-password-reset.md`). Entries merged before this folder existed stay in
[PROJECT_HISTORY.md](../../PROJECT_HISTORY.md), which is now a frozen archive.

**Why a file per entry.** The old single file was edited by every pull request at the same line, so
git reported a conflict on nearly every merge. Separate files cannot conflict, in the GitHub merge button
or anywhere else, and need no special git configuration.

**Format** (same as before):

```markdown
### YYYY-MM-DD - Short title
**Who:** Name, with <tool> assistance (AI-nnn) - **Type:** docs | code | test | CI | decision
**What:** What changed and why, with the identifiers affected.
**Evidence:** What was actually run or checked, and its limits.
**Review:** Who must approve; what is not claimed.
```

Read the running record, newest first: `python tools/history.py` (or `--list` for names only).
If two entries share a date, add a distinguishing slug; never rename an entry after it merges.
