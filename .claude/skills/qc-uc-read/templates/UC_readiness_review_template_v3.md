# UC Readiness Review
**Functional / Black-box Test Readiness Template**

---

> **How to use this template**
>This template defines the minimum information QA testers need to begin test case design.
>Fill out all sections completely before handing off to QA. Do not leave any field blank — if a section truly does not apply, write N/A and explain why.
>
> **Completion status conventions:**
> - ✅ **Complete** = section is fully populated and no longer ambiguous
> - ⚠️ **Partial** = contains content but requires further clarification
> - ❌ **Missing** = absent — BLOCKER, cannot start test design

---

## Feature Brief

*(Summarize the feature based on all read documents. Include: what the feature is, who uses it, how it works, key business rules, and known exceptions.)*

---

## Readiness Verdict

| Overall Score | Verdict |
| ------------- | ------- |
| `XX / 100` | [✅ READY / ⚠️ CONDITIONALLY READY / ❌ NOT READY] |

---

## 0. Document Metadata

| UC-ID | Feature Name | Version | Status |
|-------|-------------|---------|--------|
| *(e.g., UC-12)* | *(e.g., Service Menu List)* | *(e.g., v1.0)* | *(Draft / In Review / Finalized)* |

| Author / BA | Approved By | Date Created | Last Updated |
|-------------|-------------|--------------|--------------|
| *(Name)* | *(Name & Role)* | *(YYYY-MM-DD)* | *(YYYY-MM-DD)* |

---

## 1. Objective & Scope

### 1.1 Objective
*(Describe WHY this feature exists. What business problem does it solve? Who benefits? Write 1–3 concise sentences.)*

### 1.2 In Scope
*(List every function / sub-use-case covered in this UC. Use one line per item or bullet points.)*

### 1.3 Out of Scope
*(Clearly list what is NOT covered in this UC. If nothing is excluded, write "None.")*

---

## 2. Actors & Stakeholders

| Actor | Type | Role & Permissions |
|-------|------|-------------------|
| *(e.g., Admin User)* | *(Primary / System)* | *(Describe what this actor can do in the UC.)* |
*(Add rows as needed)*

---

## 3. Preconditions & Postconditions

### 3.1 Preconditions
*(List every condition that must be true before the flow begins. One condition per line.)*
- *(e.g., The admin has successfully authenticated.)*

### 3.2 Postconditions
| After completing... | System state / Postcondition |
|--------------------|------------------------------|
| *(e.g., Add record)* | *(e.g., New record appears at the top of the list. Success message is displayed.)* |
*(Add rows as needed)*

---

## 4. API / Queue / State Interface Inventory

> **Instructions:** Extract and catalog every endpoint, queue consumer, and Durable Object. **One entry = one row.** Do NOT collapse multiple fields into a single row (e.g., do NOT write "5 request fields" — list each individually).
>
> **Required columns per row:** Entry ID (API-XB-\* / QUE-XB-\* / DO-XB-\* or method+path) · trigger condition · all request fields (name/type/required/constraint) · success response shape · error codes + messages.
>
> **Coverage rule:** The number of rows must equal the count of endpoints + queues + DOs declared in the UC spec §2. If a schema is absent, mark the row `[BLOCKED: no schema provided]`.

**REST Endpoints:**

| # | Entry ID / Path | Trigger Condition | Request Fields (name · type · required · constraint) | Success Response | Error Codes + Messages |
|---|---|---|---|---|---|
| *(e.g., 1)* | *(e.g., POST /api/exbot/start)* | *(e.g., zen calls after preflight pass)* | *(e.g., user_id: string, required, must be active LP)* | *(e.g., { status: "STARTING", bot_id: uuid })* | *(e.g., 400 ALREADY_RUNNING / 403 PREFLIGHT_FAILED)* |

**Queue Consumers:**

| # | Queue ID | Trigger Event | Handler Summary | DLQ Policy | Retry Count | Idempotency Key | Priority / SLA |
|---|---|---|---|---|---|---|---|
| *(e.g., 1)* | *(e.g., QUE-XB-01 bot-scan)* | *(e.g., enqueued by light-check cron)* | *(e.g., scans all bots, enqueues hedge-sync per delta)* | *(e.g., DLQ after 3 retries)* | *(e.g., 3)* | *(e.g., bot_id + epoch_slot)* | *(e.g., Normal)* |

**Durable Objects:**

| # | DO ID | State Owned | Lease Duration | Expiry Action | Contention Policy |
|---|---|---|---|---|---|
| *(e.g., 1)* | *(e.g., DO-XB-02 UserLockDO)* | *(e.g., per-user operation lock)* | *(e.g., 90 seconds)* | *(e.g., release lock, log timeout)* | *(e.g., second caller receives 409 LOCK_HELD)* |

---

## 5. System State Model

> **Instructions:** Define the state and behavior of each entry from Section 4. Every Section 4 entry must have ≥ 1 row here.

**Lifecycle State Transitions** *(for UCs involving bot lifecycle — FM-XB-07)*:

| From State | Trigger Event | Guard Condition | To State | On Guard Fail |
|---|---|---|---|---|
| *(e.g., IDLE)* | *(e.g., POST /start received)* | *(e.g., 5 preflight checks pass; NV-1/NV-3 not required for Phase A1)* | *(e.g., STARTING)* | *(e.g., Return 403 PREFLIGHT_FAILED, state remains IDLE)* |

**DO Behavior** *(one row per DO from Section 4)*:

| DO ID | State Owned | Lease Duration | On Lease Expiry | On Contention |
|---|---|---|---|---|
| *(e.g., DO-XB-02)* | *(e.g., user operation lock)* | *(e.g., 90s)* | *(e.g., release lock, emit timeout metric)* | *(e.g., 409 LOCK_HELD returned to second caller)* |

**Queue Behavior** *(one row per queue from Section 4)*:

| Queue ID | DLQ After N Retries | Backoff | Idempotency Key | Priority vs Others | SLA |
|---|---|---|---|---|---|
| *(e.g., QUE-XB-08 user-redeem)* | *(e.g., 3)* | *(e.g., exponential 1s/2s/4s)* | *(e.g., redeem_request_id)* | *(e.g., Highest — runs before all other queues)* | *(e.g., 5 min LP-first)* |

---

## 6. Functional Logic & Workflow Decomposition

> **Instructions:** Analyze in detail the business processes of each operation in this feature. Duplicate the block below for each major operation (e.g., 6.1 Bot Start, 6.2 Hedge Sync).

### 6.1 Operation Name: *(e.g., Bot Start)*

**A. Workflows**
| Step | Actor | Action | System Response (Happy Path) | Alternative Flows | Exception & Error Flows |
|------|-------|--------|------------------------------|-------------------|-------------------------|
| 1 | *OPERATOR* | *POST /api/exbot/start* | *5 preflight checks run; state → STARTING; bot-scan enqueued to QUE-XB-01* | *N/A* | *Preflight fail: 403 PREFLIGHT_FAILED; state stays IDLE* |

**B. Business Rules & Validations**

> Resolve every BR-\* and FR-EXBOT-\* reference to its exact verbatim text from `common-rules.md` / `srs/spec.md`. Keep the code in parentheses for traceability.

| Field / Param | Required | Format / Constraint | Min / Max | Error Code + Message *(exact text)* |
|----------------|----------|---------------------|-----------|--------------------------------------|
| *(e.g., user_id)* | *Yes* | *UUID v4* | *—* | *400 INVALID_USER / "user_id must be a valid UUID"* |

**C. System Feedback**

* **Queue enqueue confirmations:** *(e.g., On bot-start success: QUE-XB-01 bot-scan enqueued with bot_id + epoch_slot)*
* **D1 state changes:** *(e.g., bots table: status → STARTING, started_at = now)*
* **Error codes returned:** *(e.g., 403 PREFLIGHT_FAILED — "One or more preflight checks failed: [list]")*

---

## 7. Functional Integration Analysis

> **Instructions:** Analyze linkages and influences between operations — queue fan-out, DO lease coordination, HL adapter calls, dual-chain interactions.

| Trigger Operation / Event | Impact Analysis (cross-operation influence) | Data / State Consistency Verification |
|---------------------------|---------------------------------------------|----------------------------------------|
| *(e.g., Bot Start → bot-scan enqueued)* | *(e.g., Triggers light-check scan cycle; UserLockDO lease acquired for 90s preventing concurrent start)* | *(e.g., Verify bots.status = STARTING in D1 before QUE-XB-01 consumer processes the message)* |
| *(e.g., User Redeem → QUE-XB-08 enqueued)* | *(e.g., Highest-priority queue; must complete within 5 min SLA; UserLockDO prevents concurrent redeem)* | *(e.g., Verify close_operations ledger entry created atomically with redeem request)* |
*(Add rows as needed)*

---

## 8. Acceptance Criteria

> **Instructions:** Acceptance criteria must be written in a verifiable pass/fail format, using the Given / When / Then structure. Cover each operation, state transition, error path, and SLA requirement.

| AC # | Scenario | Given *(precondition)* | When *(trigger)* | Then *(expected result)* |
|------|----------|------------------------|------------------|--------------------------|
| AC-01 | *(e.g., Bot Start — Happy Path)* | *(e.g., User has active LP position; all 5 preflight checks pass)* | *(e.g., POST /api/exbot/start called by OPERATOR)* | *(e.g., Response 200 { status: "STARTING" }; bots.status = STARTING in D1; QUE-XB-01 enqueued within 1s)* |
*(Add ACs for every operation, state transition, error path, and SLA...)*

---

## 9. Non-functional Requirements

| Category | Requirement | Source / Reference |
|----------|-------------|-------------------|
| *(Performance)* | *(e.g., user_redeem SLA: LP-first close must complete within 5 min)* | *(e.g., SRS spec.md §user-redeem)* |
| *(Performance)* | *(e.g., HLRateLimitDO: max 800 weight/min sliding window)* | *(e.g., DO-XB-01 spec)* |
| *(Security)* | *(e.g., No raw agent key stored in D1 or logs; AES-GCM envelope encryption required)* | *(e.g., SPEC_v5.2.6_EN.md §21.5)* |
| *(Reliability)* | *(e.g., All queue operations must be idempotent; DLQ policy must be stated)* | *(e.g., SRS spec.md §queue-topology)* |
*(Add categories as needed)*

---

## 10. Open Questions & Dependencies

### 10.1 Open Questions
| # | Question / Issue | Context | Owner | Status |
|---|-----------------|---------|-------|--------|
| Q1 | *(e.g., Is drag-and-drop reordering in scope?)* | *(e.g., Wireframe conflict.)* | *(e.g., PO)* | *(Open)* |

### 10.2 Dependencies
*(List any UC, feature, API, or external system that this UC depends on.)*

---

## 11. Change Log

| Version | Date | Author | Summary of Changes |
|---------|------|--------|--------------------|
| *(e.g., v2.0)* | *(YYYY-MM-DD)* | *(Author name)* | *(e.g., Restructured template to include UI mapping and integration analysis.)* |

---

*UC Readiness Template v3.0 — For QA Test Design*