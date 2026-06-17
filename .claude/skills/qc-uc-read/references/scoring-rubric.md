# UC Readiness Scoring Rubric

> Shared rubric referenced by both `first-audit` and `re-audit` workflows. Update this file ONCE to change scoring rules everywhere.

## Status Markers

Mark each knowledge area as:

- ✅ **Clear** — explicitly stated and unambiguous (full marks)
- ⚠️ **Partial** — present but vague, incomplete, or only inferred (half marks)
- ❌ **Missing** — absent from all provided artefacts (zero marks)

Additional status markers used throughout the report:

- ✅ **Complete** — explicitly stated and unambiguous
- ⚡ **Partial** — present but vague, incomplete, or only inferred (half marks)
- ⚠️ **Missing** — absent from all provided artefacts (zero marks)
- *(inferred)* — the reviewer inferred information rather than finding it explicitly; these are candidates for confirmation before test design begins

## Knowledge Areas Checklist

Score the **combined artefact set** against these knowledge areas. A tester needs all of these to design complete test cases.

| #   | Knowledge Area                            | Max Pts | Critical? | What to look for                                                                                                                                                                                                                                                                                                                                                                                                       |
| --- | ----------------------------------------- | ------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Feature Identity (title, ID, context)     | 5       | Yes       | Is it clear what this feature is and where it fits in the system?                                                                                                                                                                                                                                                                                                                                                  |
| 2   | Objective & Scope                         | 5       | Yes       | Why does this feature exist? What is in/out of scope?                                                                                                                                                                                                                                                                                                                                                                |
| 3   | Actors & User Roles                       | 10      | Yes       | Who triggers the feature (ACT-* or OPERATOR system)? What roles/permissions are involved?                                                                                                                                                                                                                                                                                                                            |
| 4   | Preconditions & Postconditions            | 10      | Yes       | What must be true before (including NV gate status if applicable)? What is the system state after success and failure?                                                                                                                                                                                                                                                                                               |
| 5   | API / Queue / State Interface Inventory   | 15      | Yes       | Every endpoint, queue consumer, and Durable Object listed as its own row. **Required per row:** ID (API-XB-\* / QUE-XB-\* / DO-XB-\*) or method+path, trigger condition, all request fields (name/type/required/constraint), success response shape, all error codes + messages. **Auto-cap rules:** if any field list is collapsed ("N fields") → max = 8/15; if any endpoint/queue/DO has no schema at all → max = 0/15. |
| 6   | System State Model                        | 20      | Yes       | Covers 3 areas — **1-to-1 rule:** every entry in KA #5 must have ≥ 1 row here. If < 80% of KA #5 entries are covered → max = 10/20. Areas: (a) **Lifecycle state transitions:** trigger event → guard condition (NV gate if applicable) → resulting state; (b) **DO behavior:** lease duration, expiry action, contention rule — one row per DO; (c) **Queue behavior:** DLQ policy, retry count + backoff, idempotency key, priority/SLA — one row per queue. |
| 7   | Functional Logic & Workflow Decomposition | 20      | Yes       | Analyze in detail the business processes of each operation (bot-start, hedge-sync, user-redeem, safe-close, etc.). Cover: main flow (happy path), alternative flows, exception & error flows, business rules referencing BR-\* and FR-EXBOT-\* verbatim.                                                                                                                                                            |
| 8   | Functional Integration Analysis           | 20      | Yes       | Analyze linkages between operations: queue fan-out, DO lease coordination, HL adapter calls, dual-chain interactions (Base/OP). Flag NV-blocked integration points explicitly.                                                                                                                                                                                                                                     |
| 9   | Acceptance Criteria                       | 20      | Yes       | Measurable, verifiable pass/fail statements for each operation and state transition.                                                                                                                                                                                                                                                                                                                                  |
| 10  | Non-functional Requirements               | 5       | No        | Performance (SLA: user_redeem 5 min, HLRateLimitDO 800wt/min), security (no raw key in D1/logs, AES-GCM), reliability (idempotency, DLQ policy).                                                                                                                                                                                                                                                                    |

**Total: 130 points → Normalise to 100 for the final score.**

## Normalization Formula

`Final Score = round((Raw Score / 130) × 100, 1)`

> Example: Raw score 88 / 130 → Final Score = round((88 / 130) × 100, 1) = **67.7 / 100**
> Example: Raw score 95 / 130 → Final Score = round((95 / 130) × 100, 1) = **73.1 / 100**

## Auto-fail Rule

If any Critical knowledge area scores 0, verdict = NOT READY regardless of total score.

- **Critical areas** (rows marked "Yes"): Areas #1–#9. If ANY of these score 0, the verdict is automatically NOT READY regardless of total score.
- **Non-critical areas** (rows marked "No"): Area #10. Scoring 0 here reduces the total but does not trigger auto-fail.

## Readiness Thresholds

| Score   | Verdict                       | Meaning                                                              |
| ------- | ----------------------------- | -------------------------------------------------------------------- |
| 90–100  | ✅ **READY**                  | QA can begin test design immediately                                 |
| 70–89   | ⚠️ **CONDITIONALLY READY**   | QA can start on clear areas; flagged items must be fixed in parallel |
| 0–69    | ❌ **NOT READY**             | Too many gaps; do not begin test design                              |

**Auto-fail:** Any Critical knowledge area scoring 0 → ❌ NOT READY regardless of total.

## Cross-Artefact Conflict Check

After scoring, check for **conflicts between artefacts**:

- Does the UC doc describe a flow that contradicts the API spec or SRS?
- Does the SRS define fields not mentioned in the UC?
- Are endpoint/queue schemas inconsistent across documents?
- Are BR-\* / FR-EXBOT-\* IDs referenced in the UC but absent from common-rules.md or srs/spec.md?
- **Site-map cross-check (if `qc-site-map` exists):** does the UC cover every API/Queue/DO entry mapped to its feature in §5? Do UC's actors/roles match site-map §7? Do UC's flows match §6 Navigation? Any mismatch → Warning + flag in Unified Gap & Question Report.

List all conflicts found — they are automatic Warnings.

## Blocked Artefact Protocol

If a referenced artefact (wireframe, API spec, supporting doc) is **unavailable or inaccessible**:

- Mark the dependent knowledge area(s) as `[BLOCKED: artefact name not accessible]`
- Score those areas as 0
- Since blocked artefacts almost always affect Critical knowledge areas (#1–#9), surface each blocked area as a 🔴 **Blocker** in the report under the "Blockers" section
- Do NOT infer or assume content from unavailable artefacts

## Common Gap Patterns

| Gap Pattern                                                       | Impact on Test Design                                              |
| ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| No preconditions stated                                           | Tester can't set up test data correctly                            |
| Vague actor ("the user" instead of ACT-* or OPERATOR)            | Can't determine which role/permission to test                      |
| Missing field validation rules                                    | Can't write boundary value or negative tests                       |
| No error messages / error codes specified                         | Can't verify error handling behaviour                              |
| Acceptance criteria use "should" / "can"                          | Not verifiable; can't define pass/fail                             |
| API error codes not listed                                        | Can't verify API error handling                                    |
| Flows reference other features without links                      | Can't trace test dependencies                                      |
| NV gate not declared for UCs touching stop system / HL integration | Can't determine if UC is testable (may be blocked at Phase 0)     |
| NV items in Cross-References but status still "Open"             | Preconditions incomplete; stop-related tests are blocked           |
| FR-EXBOT-\* referenced without citing specific section in srs/spec.md | Can't trace requirement → spec; verification incomplete       |
| Phase 0 Gate conditions absent from Preconditions of FM-XB-09 UCs | Tester may start HL integration testing before gate passes        |
| Dual-chain behavior (Base/OP wethIndex) not addressed             | LP calc tests and chain-switch tests are blocked (NV-12)           |
| DO contention policy not stated                                   | Can't design concurrent-call test cases                            |
| Queue idempotency key field not specified                         | Can't verify retry safety or deduplication behaviour               |

## Blocked Artefact Protocol

If a referenced artefact (API spec, SRS section, supporting doc) is **unavailable or inaccessible**:
