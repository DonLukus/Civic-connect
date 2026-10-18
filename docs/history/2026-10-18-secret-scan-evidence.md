### 2026-10-18 - Independent full-history secret scan recorded (NFR-005)
**Who:** Don, with Claude Code assistance (AI-052) - **Type:** security evidence
**What:** Ran gitleaks 8.30.1 (checksum-verified) over all refs of a clone at `origin/main` af2f545: 176 commits with diffs scanned, 0 findings. Added `docs/security/secret-scan-full-history-2026-10-18.md` with the exact command, scope and limits, and linked it from RTM row TR-018.
**Evidence:** Report file empty; limits stated (default rules only, local clone, no PR refs, forks or logs).
**Review:** Needs two non-author approvals. This does not replace the per-PR CI scans.
