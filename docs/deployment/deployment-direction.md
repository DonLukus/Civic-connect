# Deployment Direction (M2 draft)

> Status: Proposed, same as ADR-001 — this names a direction to verify, not a finished decision.
> Owner: Masego. Gated on the DEC-008 proof-of-concept.

## Where it runs

One free-tier host running the single deployable unit from ADR-001 (backend + server-rendered
frontend in one process). CN-03 rules out anything requiring an always-on paid instance; CN-07
means no candidate host is confirmed to work from the Belgium Campus desktop platform yet — that
confirmation is the outstanding PoC action, not assumed here.

## Configuration and secrets

Configuration is environment variables only (`.env.example` names them; never a value). No
secret is ever committed — `.gitignore` already excludes `.env`, key/cert files and
`appsettings.*.json`, and `secret-scan.yml` enforces it on every PR (NFR-005). The host's own
secret/config store (not a file in the repo) holds the real values in any deployed environment.

## Where state and persistence live

The relational database from ADR-002 (versioned request table, immutable audit table, outbox
table) is the single source of truth. No state is held in the application process itself — the
app tier is stateless (PED §17.5), so the deployable unit can restart or cold-start (CN-03)
without losing anything beyond in-flight requests, which the outbox retry logic already accounts
for (ADR-004).

## Networking

A single public HTTP(S) endpoint for the app. The outbox worker (ADR-002/ADR-004) runs as a
background loop inside the same process for M2 rather than a separate service, consistent with
the single-deployable-unit conclusion in PED §5.1 — a separate worker process is another thing
that idles out under CN-03 for no evidenced benefit yet. See **ADR-006** for the full outbox
decision and its amendment reconciling this direction, including the claim-on-send requirement
(a conditional update from pending to sending) that keeps this in-process loop safe if more than
one app instance is ever active at once.

## Deferred decisions and the evidence still needed

| Deferred | Evidence needed |
|---|---|
| Exact hosting provider (SQLite acceptable vs PostgreSQL required) | Deploy the traced slice and observe whether the file-based store survives an idle/redeploy cycle (this is the concrete test of ADR-001's claim that SQLite fails NFR-011 in production) |
| Belgium Campus platform compatibility | Run the stack on the actual desktop platform per CN-07 / brief §25 — not yet attempted |
| Outbox worker scheduling under a host that sleeps | Measure whether a background loop survives the host's idle-shutdown behaviour, or whether it needs an external trigger (e.g. a scheduled ping). Tied to ADR-006's fallback condition: if the DEC-008 PoC shows the loop does not survive host sleep, fall back to an external trigger or a separate process, as ADR-006's amendment already anticipates |
| TLS / HTTPS termination | Depends on which host is chosen; most free tiers provide it, needs confirming per candidate |

This file is updated once the DEC-008 proof-of-concept produces that evidence — see ADR-001.
