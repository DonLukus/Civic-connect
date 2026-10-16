# M3 technical debt register

Prepared 16 October 2026 for team review. These are identified limitations, not approved risk acceptances.

| ID | Compromise and consequence | Proposed owner | Exit condition |
|---|---|---|---|
| TD-001 | Outbox `sending` has no lease/recovery; a process crash can strand a message. A crash after mail send before sent-state update can also duplicate external mail. | Don | Add recovery/idempotency policy and failure-injection evidence; keep notification failure separate from request state. |
| TD-002 | In-process worker and one local SQLite file simplify the demo but constrain concurrency, availability and hosted durability. | Don / Emile | Select durable hosting/storage under DEC-008 and verify restart/redeploy/recovery on that environment. |
| TD-003 | Legacy Werkzeug hashes upgrade only after successful login; inactive legacy accounts can remain outside NFR-003's approved algorithms. | Don | Choose reset/migration policy and inspect actual candidate account storage. |
| TD-004 | Bootstrap provisioning stands in for FR-001/023/024 operations; Manager/Admin safe landing is not operational functionality. | Team | Implement required flows or approve an explicit scope disposition while retaining baseline gaps. |
| TD-005 | Live HTTP journeys and browser walkthrough exist, but browser automation, complete role matrix, accessibility audit and cold-start/uptime/capacity evidence remain incomplete. | Masego / Emile | Add/review missing evidence before making the associated claims. |
| TD-006 | Outbox schema migration is not a demonstrated reversible deployment migration. | Don | Test interruption/rollback/forward repair with schema-compatible backup and restore. |

Priorities, owners and target milestone require team confirmation. See release summary for current impact and evidence.
