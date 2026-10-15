# CivicConnect M3 Release Evidence Summary

**Owner:** Don  
**Status:** Template — complete only from verified evidence.  
**Release decision:** NOT READY until all mandatory evidence and approvals are recorded.

## 1. Candidate identity

- Candidate version:
- Git commit SHA:
- Pull request:
- Staging URL:
- Verification date/time:
- Evidence owner:

## 2. Quality-gate evidence

| Gate | Evidence link / run ID | Result | Notes / unresolved findings |
|---|---|---|---|
| Automated tests | Fill in | Not verified | Record count and commit SHA |
| Dependency vulnerability audit | Fill in | Not verified | Record tool/version and findings |
| Static analysis | Fill in | Not verified | Record findings and dispositions |
| Secret scanning | Fill in | Not verified | Confirm no exposed secrets |
| Traceability check | Fill in | Not verified | Requirements → tests → results |
| Independent code review | Pull request | Pending | Two non-author approvals required by project rules |

## 3. Functional and security verification

| Area | Required evidence | Result |
|---|---|---|
| Authentication and role access | Positive and negative role tests | Not verified |
| Requester privacy | Own-request access and cross-user denial | Not verified |
| Request submission | Valid and invalid form tests | Not verified |
| Staff queue/filter | Valid filters, invalid filters, role denial | Not verified |
| Concurrent acceptance | Two competing attempts; only one succeeds | Not verified |
| Audit/outbox integrity | State change and related records agree | Not verified |
| Notification delivery | Actual in-app/email delivery evidence | Not verified |
| CSRF | Missing/invalid token is rejected | Not verified |
| Secret handling | Repository scan and environment review | Not verified |

## 4. Performance evidence

- Requirement ID and target:
- Test tool and version:
- Test environment and resource size:
- Dataset size and data-generation method:
- Request mix and concurrency:
- Warm-up and measured duration:
- p50 latency:
- p95 latency:
- p99 latency:
- Throughput:
- Error rate:
- CPU/memory observations:
- Raw report link:
- Result against acceptance threshold:

Do not state that performance passed until the exact baseline threshold and repeatable measurements are attached.

## 5. Deployment and recovery evidence

- [ ] Deployed commit matches candidate SHA.
- [ ] HTTPS and session-cookie configuration verified.
- [ ] Environment variables and secrets reviewed.
- [ ] Database persistence across restart/redeploy verified.
- [ ] Backup and restore/recovery procedure tested where required.
- [ ] Logs reviewed for errors and sensitive data.
- [ ] Rollback path documented.

## 6. Open defects and release blockers

| ID | Severity | Impact | Owner | Mitigation | Evidence required to close |
|---|---|---|---|---|---|
| Fill in | Fill in | Fill in | Fill in | Fill in | Fill in |

## 7. Decision

Select one: **READY**, **READY WITH APPROVED LIMITATIONS**, or **NOT READY**.

Decision rationale:
- Mandatory gates passed:
- Outstanding defects/risks:
- Approved limitations and approver:
- Reviewer names and dates:
- Next action:

A blank field means evidence is missing, not that the check passed.
