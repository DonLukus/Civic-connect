# Repository and Configuration Management

> **PED v1.0 section.** Owner: Don.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

GitHub is an engineering control environment, not file storage. These controls have operated since the start of M1; the evidence is repository history rather than this description of it.

| Control | Configuration | Evidence |
|---|---|---|
| Repository | One controlled team repository for documentation, registers and (from M3) source | Repository settings |
| Protected main | Direct pushes blocked; main is the controlled product state | Branch rule; a refused direct push |
| Pull requests | Required for every substantive change, including documentation | Merged pull request history |
| Approvals | Two, from members other than the author; self-approval refused | Approval records |
| Stale approvals | Dismissed on new commits, so approval refers to what merges | Branch rule |
| Conversation resolution | Required before merge | Resolved threads |
| Administrator bypass | Disabled — applies to every member including the owner | Branch rule |
| Force push / deletion | Blocked, so history cannot be rewritten | Branch rule |
| Secrets | Secret scanning and push protection on; .gitignore covers environment files before any code exists (NFR-005) | Scan results, .gitignore |
| Issues | Substantive work is an issue with an owner, linked to the closing pull request | Issue history |
| Conventions | Branches docs/, feat/FR-nnn-, fix/, chore/. Commits type(scope): summary (refs #issue) | Commit history |

Two approvals matter because a substantive change alters the controlled state every later artefact depends on, and the author is least able to see what they missed — which matters most for AI-generated content, since it is fluent and therefore easy to accept unchecked. The cost is recorded honestly as RSK-04 rather than avoided.
