# M3 Staging Runbook

**Owner:** Don (DevSecOps/Architecture)  
**Status:** Draft; execute and record actual values before claiming staging readiness.

## 1. Purpose

Provide a repeatable deployment and verification procedure that separates development, test, staging, and production configuration. Staging must use synthetic test data, not real citizen data.

## 2. Configuration rules

- Store secrets in the hosting provider's secret/environment-variable facility; never commit `.env`.
- Generate a unique random `SECRET_KEY` for each environment.
- Set secure session cookies only when the environment is served over HTTPS.
- Configure database connection/storage explicitly and verify persistence across redeploys.
- Do not use production credentials in development, CI, or staging.
- Keep configuration names consistent across environments, while values differ by environment.
- Do not put secrets or personal data in logs, screenshots, or evidence artefacts.

## 3. Pre-deployment checklist

- [ ] Identify the commit SHA and branch being deployed.
- [ ] CI tests pass on that exact commit.
- [ ] Dependency audit, static analysis, and secret scan have completed; findings are reviewed.
- [ ] Required environment variables are present and validated at startup.
- [ ] Database schema initialisation/migration has a documented, repeatable procedure.
- [ ] Staging uses synthetic accounts and records.
- [ ] HTTPS and cookie settings match the actual deployment endpoint.
- [ ] A rollback/redeploy procedure and responsible person are recorded.

## 4. Deployment verification

Record each check with date/time, tester, commit SHA, expected result, actual result, and evidence link.

1. Confirm deployment reports success and the deployed SHA matches the intended commit.
2. Load the login page over HTTPS.
3. Verify valid demo credentials work and invalid credentials fail without revealing which field was incorrect.
4. Verify each role is directed only to authorised pages.
5. Submit a synthetic request as a Requester.
6. Verify the Requester can view their own request but cannot view another account's request.
7. Verify staff can view the queue and filter only by allowed statuses.
8. Attempt to accept one request concurrently as two staff sessions; only one acceptance should succeed.
9. Verify successful acceptance produces one consistent status update, audit record, and outbox event.
10. Verify notification delivery separately from outbox creation.
11. Redeploy/restart and verify the request still exists. If it disappears, record a release blocker.
12. Inspect logs for errors and confirm no credentials or sensitive personal data are exposed.

## 5. Rollback

- Stop promotion if authentication, authorisation, request integrity, or persistence checks fail.
- Restore the last known-good deployment using the hosting provider's documented process.
- Do not run destructive database rollback steps without a verified backup and an approved recovery procedure.
- Record the incident, affected commit, impact, recovery action, and retest evidence.

## 6. Evidence record

| Field | Value |
|---|---|
| Environment URL | Fill in after verification |
| Commit SHA | Fill in from deployment |
| Deployment date/time | Record actual time |
| Tester | Record name |
| Test evidence | Link to CI run and staging results |
| Persistence across redeploy | Pass/Fail/Not tested |
| Known defects | Link issue IDs |
| Decision | Proceed / Block / Retest |

A successful hosting deployment alone is not proof of production readiness.
