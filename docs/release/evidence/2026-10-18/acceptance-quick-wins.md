# M4 acceptance quick wins - review candidate

**Date:** 18 October 2026 SAST

**Owner:** Emile, with Codex execution assistance (AI-059)

**Branch:** `m4/acceptance-quick-wins` from merged `origin/main` at `2524a66`
**Review state:** independent review and merge pending

## Implemented acceptance behaviour

- **FR-006 / AC-006:** the active controlled category remains the only selectable source. Blank, free-text, inactive and unknown category values are rejected. The rendered error is now programmatically tied to `category_id` and other entered values remain present.
- **FR-022 / AC-022:** a Manager-only request list supports status and category filters. CSV generation reuses the same six-value display mapping. The acceptance regression reconciles one filtered display row to one CSV data row plus its header, with the same Reference, Title, Category, Submitted, Status and Assignee values.
- **FR-026 / AC-026:** a submission that matches an open request by active category and case-insensitive trimmed location shows possible-duplicate reference(s), creates no row at the warning step, and offers confirm and cancel actions. Confirmation creates the request. Requester contact information is not included in the warning.
- **NFR-014 / AC-N014:** submission title, description, category and location now have field-associated server errors; non-secret values are retained. Text fields reject non-text service input and enforce declared maximum lengths of 200, 5,000 and 300 characters. This improves the evidence but does not complete NFR-014 across every implemented input.

FR-012 remains **Partially Met**: the new Manager list adds status/category filtering, but the original search, combined category/status/assignee/priority/date filters and requested sorting are not all delivered. There is still no priority field in the data model.

## Automated evidence

`tests/test_acceptance_quick_wins.py` adds 8 stable test functions (TST-058 through TST-065), collected as 19 cases. The focused submission/acceptance run passed 30/30. The first full run found one truthful-content regression: the changed Manager landing page omitted the word `deferred`; the existing test rejected it. The disclosure was restored and the changed landing test plus all 19 new cases passed 20/20. After Emile's walkthrough, duplicate confirm/cancel controls were moved before the retained fields; the duplicate and ordinary submission regressions then passed 2/2.

The final full-suite rerun completed after the landing disclosure correction:

- **Final result after the keyboard-order refinement:** 96 passed in 200.76 seconds on Python 3.12.14.
- **Persistence coverage:** 291/358 lines, 81.28%; the 70% threshold passed.
- **Ruff:** clean for `src` and the new acceptance tests.
- **CI:** all seven checks pass on PR #103 revision `45bcdf6`, including the full test/static-analysis job after replacing the parameter-placeholder f-string that Bandit flagged.
- **Boundary:** local Python/Flask/SQLite evidence. Coverage is persistence-package line coverage, not browser or whole-application coverage. Independent review is pending; this is not hosted availability, external email, team approval or production acceptance.

## Browser layout evidence

A synthetic request with an unbroken 200-character valid title reproduced the earlier mobile-risk condition. At a 390x844 browser viewport after the CSS correction:

| Screen | `innerWidth` | document/body `scrollWidth` | Long-title container client/scroll width | Result |
|---|---:|---:|---:|---|
| Requester list | 390 | 375 / 375 | 341 / 341 | No horizontal document overflow |
| Request detail | 390 | 375 / 375 | 309 / 309 | No horizontal document overflow |

This closes DEF-007 for the measured pages and fixture. It is not a full responsive-device or accessibility certification.

## Human keyboard and usability result

Emile supervised five different human participants and reported the following local moderated results. Participant identities and synthetic credentials are deliberately excluded from the repository.

| Participant | Duration | Completed | Unaided | Screens | Receipt | Problem observed | Qualifies |
|---|---:|---|---|---:|---|---|---|
| P1 Emile | 2:12 | Yes | Yes, reported | 3 | #504 | Duplicate confirmation originally followed retained fields in tab order | Yes |
| P2 | 0:52 | Yes | Yes | 2 | #505 | None observed | Yes |
| P3 | 0:37.29 | Yes | Yes | 2 | #506 | None observed | Yes |
| P4 | 0:33.20 | Yes | Yes | 2 | #507 | None observed | Yes |
| P5 | 1:06.22 | Yes | Yes | 2 | #508 | None observed | Yes |

The task was to submit a Utilities request for a broken streetlight at the participant's assigned synthetic location, starting from the submission page and stopping at the receipt. Emile reported giving no help during the timed attempts. All five completed validly, unaided, within three minutes and no more than three screens. This exceeds AC-N007's threshold of at least 4/5, so NFR-007 is proposed **Met**.

P1 also supplies positive manual evidence for the keyboard-completion part of NFR-008: Emile reported keyboard-only use, visible focus, the duplicate warning and retained values, and supplied warning/receipt screenshots. This does not replace the required automated computed-style accessibility scan, so NFR-008 remains Partially Met. After P1, duplicate confirmation and cancellation were moved before the retained fields in keyboard order; later participants did not encounter a duplicate because each used a distinct location.
