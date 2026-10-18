# NFR-005 full-history secret scan, 2026-10-18

NFR-005 requires "an automated secret scan on every pull request and a full-history scan", both with zero
findings. This records one independent full-history run and its limits.

| Item | Value |
|---|---|
| Repository state | `origin/main` = `af2f5456a9a940f6c9a020db5cd5fe5e4889219d` (fetched 2026-10-18), plus every remote-tracking branch present in the local clone |
| Tool | gitleaks 8.30.1, official Windows release, SHA-256 checked against the published `gitleaks_8.30.1_checksums.txt` (OK) |
| Command | `gitleaks git --log-opts="--all" --redact -f json -r report.json --no-banner .` |
| Rules | gitleaks default ruleset, no custom config. The repository's `.gitleaksignore` (one exact fingerprint for a public commit SHA in `source-manifest.json`) is read automatically; see the control run below. |
| Scope | 176 commits with changes scanned, about 1.59 MB. 248 commits are reachable from all refs; the difference is merge commits, which carry no diff of their own. |
| Result | **0 findings** (`no leaks found`; report file is an empty JSON list) |

## Control run without the ignore file

The first run above picked up the repository's `.gitleaksignore` automatically. To show it was not hiding
anything, the scan was repeated with the ignore path overridden by an empty file, and again with an empty
directory. Both gave **0 findings** (181 commits, because the PR head refs `refs/remotes/pr/*` for open PRs
#92 to #96 had been fetched by then, which also covers those PR branches). With this gitleaks version the
default rules do not flag the SHA at all, so the ignore entry had no effect on this local result; the CI
action may behave differently, which is why the entry exists.

## Limits (what this does not show)

- It scans the default gitleaks rules only. It cannot recognise a secret with an unusual format, and it
  does not prove that no secret ever existed in a place git history does not cover.
- It scanned a local clone. The control run included open-PR head refs, but not other hidden pull-request refs, deleted branches,
  forks, issue or PR text, Actions logs or uploaded artefacts.
- Findings were run with `--redact`; with zero findings there was nothing to redact.
- Several documents (README, `.env.example`, tests) contain obviously fake credentials such as
  `test-secret`. The default rules did not flag them, and no allowlist was used to hide anything.
- This is one point-in-time run. The continuing control is the `secret-scan` job in
  `.github/workflows/quality.yml` (gitleaks-action over `fetch-depth: 0`) and `secret-scan.yml`, which run on
  every pull request. Their results are visible per commit under the repository's Actions tab; they were
  not exported for this record.

## How to repeat

Download the gitleaks release for your platform, verify its checksum, then from a fresh clone with all
branches fetched run the command above. A non-empty report means rotate the credential first, then purge it
from history; do not paste the finding into an issue or chat.
