# CivicConnect M3 Interface Agreement — Draft for Team Review

**Owner:** Don (Workstream B)  
**Status:** Draft — confirm against the baselined requirements and current templates before treating as an approved contract.  
**Purpose:** Give frontend, backend, and verification work a shared contract.

## Proposed route contract

The route names below are proposals for the M3 integration. They are not evidence that the routes already exist. Before implementation, compare them with the approved requirements, current Flask routes, templates, and team decisions.

| Capability | Method and path | Authorised role | Expected outcome |
|---|---|---|---|
| Sign in | GET/POST `/login` | Public | Render form; validate credentials and CSRF on POST |
| Sign out | POST `/logout` | Authenticated | Clear session after CSRF validation |
| New request form | GET `/requests/new` | Requester | Render active controlled categories |
| Submit request | POST `/requests` | Requester | Validate and create request; redirect to confirmation |
| Own requests | GET `/requests` | Requester | Return only requests owned by current user |
| Own request detail/history | GET `/requests/<id>` | Owning Requester | Return own request and permitted history; avoid existence disclosure |
| Staff queue | GET `/staff/requests` | Staff; Manager only if baseline permits | Filter/sort using allow-listed values |
| Staff request detail | GET `/staff/requests/<id>` | Staff; Manager only if baseline permits | Render authorised details and available actions |
| Accept request | POST `/staff/requests/<id>/accept` | Staff role permitted by baseline | Call domain service with expected version; preserve audit/outbox transaction |
| Manager landing | GET `/manager` | Manager | Safe landing page only; not a claim that dashboard scope is implemented |
| Administrator landing | GET `/admin` | Administrator | Safe landing page only; not a claim that user/category administration is implemented |

## Request submission fields

The current service accepts `requester_id`, `category_id`, `title`, `description`, and `location`. The web form should submit `category_id`, `title`, `description`, `location`, and a CSRF token. The server derives requester identity from the authenticated session, never from a client-supplied user ID.

## Staff queue query contract

- `status` must be checked against the agreed lifecycle values before querying.
- Sort fields and sort directions must use allow-lists; never interpolate arbitrary client values into SQL.
- Add pagination only after agreeing the default page size and acceptance criterion.
- Empty or invalid filters must have documented behaviour.
- Query results must not expose secrets or unrelated requester data.

## Security requirements for every state-changing route

1. Authenticate the session and check the role on the server.
2. Validate CSRF for form-based state changes.
3. Validate all inputs server-side.
4. Call domain/service methods for business rules; do not rely on template visibility.
5. Preserve transactional audit and outbox writes for successful acceptance.
6. Use expected-version/concurrency checks to prevent two staff members accepting the same request.
7. Return a non-disclosing response when a requester tries to access another user's request.

## Template data agreement (provisional)

| Template | Suggested context |
|---|---|
| `login.html` | `error`, `csrf_token` |
| `new_request.html` | `categories`, `error`, `values`, `csrf_token` |
| `request_list.html` | `requests`, `csrf_token` |
| `request_detail.html` | `item`, `csrf_token` |
| `staff_queue.html` | `requests`, `selected_status`, `allowed_statuses`, `csrf_token` |
| `staff_request_detail.html` | `item`, `csrf_token` |

Confirm naming and object shape with the frontend owner before implementation.

## Traceability required before approval

For every route and behaviour, add the exact baselined `FR-nnn`, `NFR-nnn`, `AC-nnn`/`AC-Nnnn`, and `TR-nnn` identifiers. Do not invent identifiers. Link each route to a test ID and state whether the implementation is complete, partial, or deferred.

## Approval checklist

- [ ] Confirm route names against current code and agreed design.
- [ ] Confirm each role against the baseline.
- [ ] Confirm request/detail fields against schema and templates.
- [ ] Add exact requirement and acceptance-criterion IDs.
- [ ] Agree response/error behaviour with frontend and test owners.
- [ ] Record review feedback and update the traceability matrix.
