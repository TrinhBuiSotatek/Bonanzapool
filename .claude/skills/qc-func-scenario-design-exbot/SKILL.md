---
name: qc-func-scenario-design-exbot
description: Designs test scenarios for LOGIC/API/BACKEND systems with NO UI (bot/worker/service — e.g. Cloudflare Workers + Hyperliquid). Trigger this skill whenever the user says "design test scenarios logic", "build logic scenarios", "thiết kế test scenarios logic", or shares an audited uc-review-report for an API/backend/bot feature and asks to proceed with testing. Also trigger when the user mentions their backend/API requirement is ready and they want to move to QA/test design, even if they don't say "test scenario" explicitly.
---
# Test Scenario Design Skill (Logic-Only)

## Purpose

Transform a finalized UC requirement (ideally reviewed and approved by `qc-uc-read-exbot`) into ready-to-use **test scenarios** grouped by UC, covering Functional / Integration / Data/State / End-to-End / Acceptance testing for **LOGIC/API/BACKEND systems that have NO UI** (bots, workers, services, queue/cron/Durable-Object pipelines, on-chain ↔ off-chain integrations).

Scenarios describe **what** must be verified at a meaningful level of intent (one scenario = one distinct test intent). They are the bridge between an audited requirement and atomic test cases — they are NOT atomic, executable test cases (those belong to `qc-func-tc-design-exbot`).

**Logic-only scope:** there is no user interface. Every scenario is expressed as a LOGIC/ACTION intent — an action plus the condition to verify. Scenarios MUST NOT reference UI objects.

## Trigger Conditions

- **Manual:** "design test scenarios logic", "build logic scenarios", "thiết kế test scenarios logic".
- **Implicit:** the user shares an audited `uc-review-report` for an API/backend/bot feature and asks to "proceed to testing" / "next step" / "move to QA" without naming the artifact.

## Input Contract

Resolve via `path-registry.md`:

- `project-context-master` — read to load the **DOMAIN / ARCHITECTURE** of the system under test: API/backend surface, queue / cron / Durable-Object processing model, supported chains, external integrations (e.g. Hyperliquid, on-chain vault, reconcile pipeline). This informs how logic scenarios are phrased (action + condition against endpoints, queue messages, cron ticks, state transitions, on-chain events) — NOT any UI gesture vocabulary.
- `qc-site-map` (optional) — if present, read §6 flow / dependency paths (pre/post-condition + E2E logic paths), §7 Role/access (permission scenarios), §9 Data/API/Integration/State touchpoints (the primary source for logic scenarios — integration, data-consistency, and state edge cases), §10 Regression anchors (risk emphasis). There are no screens, so there is no Screen ↔ Feature mapping to consume. If missing, skip site-map-derived scenarios and warn once.
- `uc-review-report` — latest version of the audited UC document for `<UC-ID>`.
- `requirement-common-files` — for verbatim business rules, error codes/messages, and common functions referenced by the UC.

## Output Contract

- **`func-test-scenarios`** (`.md`) — primary deliverable, one file per UC (or per UC group), versioned per `naming-convention.md` (same logical name and naming convention as the UI variant, so it integrates with the same pipeline):
  ```
  [UC-ID]_[feature-name]_scenarios_[YYYYMMDD]_v[N].md
  ```
- **`worklog-per-device`** — log every phase boundary per the protocol at `docs/qc-lead/agent-work-log.local/README.md`. Do NOT touch the master `agent-work-log`.

## Workflow (single file, 3 phases)

### Phase 0 — Setup

1. **Identify `<UC-ID>`** from the user invocation or the audited filename. If unclear, ASK the user — do NOT guess.
2. **Worklog:** append new entry to the device's JSONL with `status = "Running (Phase 1)"`, `input = [<uc-review-report path>]`, `start = now` (per the protocol).

### Phase 1 — Analysis & Coverage Matrix

Read fully before writing anything.

1. Read `project-context-master.md` → load the **domain / architecture** of the system under test: which API/backend endpoints exist, the processing model (queue / cron / Durable Object), supported chains, and external integrations. Use this to ground scenario phrasing in concrete logic (endpoints, queue messages, cron ticks, state transitions, on-chain events) — there is NO UI gesture vocabulary to load.
1a. **If `qc-site-map.md` exists**, read §6/§7/§9/§10. Use §9 (Data/API/Integration/State touchpoints) as the primary source to enumerate integration and data-state edge cases (rows for the coverage matrix in Step 4); §6 (flow / dependency paths) to derive pre-/post-condition states for E2E logic scenarios; §7 for role/permission scenarios; §10 to weight risk-based emphasis. If missing → skip and warn once.
2. Read the highest-version `uc-review-report` for `<UC-ID>`. Build a working understanding of:
   - All UC IDs in scope and their names
   - All functions/features within each UC
   - Main flow, alternative flows, exception/error flows
   - Business rules and validations (with verbatim wording from common files)
   - Acceptance criteria (Section 8 of the audited report)
   - Actors / roles / permissions
   - Pre/postconditions
   - API endpoints, state-machine states, and integration touchpoints (queue / cron / Durable Object / external API / on-chain)
3. Read `requirement-common-files` only for any error code / business-rule ID / common-function name cited in the UC — to inline the exact message text into scenario descriptions.
4. **Build a coverage matrix in working memory:** `UC × Test Type × Coverage Area`. Rows = each UC in scope; columns = the coverage areas listed in §"Scenario Coverage Rules". Mark each cell as:
   - `to-cover` — has enough info, will produce one or more scenarios
   - `blocked` — the audited report flagged the underlying KA as ⚠️ Missing / ⚡ Partial; surface in §Out-of-Scope Flags, do NOT fabricate
   - `out-of-scope` — performance / load / security beyond functional auth; surface in §Out-of-Scope Flags
5. If the audited report's Verdict is `NOT READY`, STOP and ask the user whether to proceed (scenarios from a Not-Ready UC will inherit known gaps). Do NOT silently continue.
6. **Worklog:** rewrite last entry → `status = "Phase 1 done"`.

> If a UC ID or function name is not explicitly stated in the document, infer from the feature name and note your inference clearly in the output (e.g., *"UC ID inferred as UC-001 from title 'Bot Initialization Flow'."*).

### Phase 2 — Scenario Drafting

For every `to-cover` cell in the matrix, draft scenarios using the **Scenario Template** below. Apply the **MANDATORY Test Design Techniques** systematically (see §"MANDATORY Test Design Techniques"). Each scenario MUST:

- Have a unique ID `TS_[UC-ID]_NNN` (zero-padded sequence per UC).
- Cite a Req-ID (UC ID + section reference — e.g., `UC-001-FR-003`).
- Map to exactly one Test Type (Functional / Integration / Data/State / End-to-End / Acceptance).
- Carry a Test Focus tag (Happy path / Alternative flow / Error/Exception / Boundary / Permission/Role / State transition / Integration / Idempotency/Concurrency / On-chain↔off-chain consistency).
- Follow the **Logic-only scenario style** (see §"Logic-only scenario style") — action + condition, no UI objects.
- Be **independent in intent** — splitting later into atomic test cases is the next skill's job, but the scenario itself must already represent ONE meaningfully different test intent.

Quality checks before writing the file (§"Quality Checks Before Finalizing"). When done, write the deliverable to the resolved `func-test-scenarios` path with the naming convention above.

### Phase 3 — Finalize

1. **Worklog:** rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`, `output = [<scenarios file path>]`.
2. **Chat report** (no separate summary file):

   ```
   ## ✅ Test Scenario Design Complete

   | Artifact       | File                                  | Count |
   |----------------|---------------------------------------|-------|
   | Test Scenarios | <resolved path>                       | X scenarios across Y UCs |

   ### Coverage breakdown by Test Type
   - Functional: X scenarios
   - Integration: X scenarios
   - Data/State: X scenarios
   - End-to-End: X scenarios
   - Acceptance: X scenarios

   ### Notes
   - Inferred UC IDs / function names: <list or "none">
   - Blocked coverage cells (need BA): <list or "none">
   - Out-of-scope items flagged: <list or "none">
   ```

## Logic-only scenario style

This is a **no-UI** skill. Scenarios and any description text MUST describe **the action plus the condition to verify**, and MUST NOT name UI objects — no buttons, fields, screens, modals, dialogs, taps, or clicks. The tester decides the concrete operation, endpoint, queue message, cron trigger, or on-chain call that realizes the action.

- ✅ Correct (action + condition): *"Deposit ETH to the HL wallet, the deposit amount should be ≥ the minimum deposit amount."*
- ✅ Correct (action + condition): *"Trigger a hedge-sync while the circuit breaker is `open`; the system must suppress the hedge mutation but keep stop monitoring active."*
- ❌ Wrong (UI object): *"Click the **Deposit** button and enter an amount in the **Amount** field."*

Keep scenarios at **intent level** — one action + one condition to verify per scenario. They are still NOT atomic test cases (concrete payloads, exact endpoints, and step-by-step assertions are expanded later by `qc-func-tc-design-exbot`).

## Mindset (adapted from `qc-func-tc-design-exbot` so both skills share one playbook)

- **Risk-Based:** scenarios for core logic transactions (bot start/close, hedge-sync, on-chain redeem, reconcile) get extra coverage (alternative + exception + concurrency flows). Trivial read-only logic stays lean.
- **Shift-Left "What-If" Engine:** for every requirement, ask *"What if the action runs under condition X / Y / Z?"* (e.g., message redelivered, cron overlaps, lock contended, external API times out mid-operation). Each meaningful "what-if" becomes its own scenario.
- **Be Skeptical:** the UC is incomplete by default. If a flow can silently branch (e.g., state changes between read and write, partial close, reconcile mismatch), add an alternative-flow or state-transition scenario.
- **Be Domain-Driven:** Fintech/Crypto backend → emphasize transaction accuracy, state-machine integrity, idempotency, and on-chain ↔ off-chain consistency. Tailor scenario emphasis to the domain/architecture declared in `project-context-master.md`.

## MANDATORY Test Design Techniques

Same set as `qc-func-tc-design-exbot` — applied at the **scenario level** (one technique application typically produces one scenario; the downstream TC-design skill expands that scenario into atomic cases).

1. **Equivalence Partitioning (EP)** — one scenario per valid/invalid partition. Never bundle.
   - Supported chains `[chainA, chainB, chainC]` → one scenario per valid chain + one per representative invalid/unsupported chain. Do NOT collapse "all valid chains" into one scenario.

2. **Boundary Value Analysis (BVA)** — for any numeric/size/threshold constraint, one scenario each at `Limit`, `Limit − 1`, `Limit + 1`.
   - Minimum deposit amount → scenarios for exactly the minimum, just below, just above.
   - `marginUsage` thresholds (e.g., 0.55, 0.75) → scenarios at the boundary and on each side.

3. **Decision Table / Combinatorics** — for multi-condition logic (e.g., re-entry: funding APR > −15% × preflight passes × balance > 0), write matrix scenarios for each meaningful combination. Never test one condition in isolation if it logically interacts with another.

4. **State Transition** *(first-class for this skill)* — for explicit state machines (bot lifecycle, circuit breaker, margin status, close-operation states), write one scenario per **valid** transition plus at least one **representative invalid** transition attempt (e.g., attempting a mutation while in `safe_mode`, or a transition not allowed from the current state).

5. **Use Case Testing** — derive Happy / Alternative / Exception flow scenarios directly from the UC's Main / Alt / Exception sections.

6. **Error Guessing** — apply backend/distributed-systems experience to add scenarios for defect-prone areas not explicitly listed in the UC, e.g.:
   - queue redelivery / duplicate message delivery
   - cron tick overlap (a new tick fires before the previous run finishes)
   - Durable-Object lock contention (two workers race for the same lock)
   - external-API timeout mid-operation (e.g., Hyperliquid request hangs after a partial mutation)
   - reconcile mismatch (off-chain expected size ≠ actual on-chain/HL size)
   - retry with the same idempotency key / `cloid` (must not double-apply)
   - out-of-order events (e.g., a confirmation event arrives before its initiating event)

> Failure to apply these techniques limits scenarios to basic happy paths. Applying them correctly typically scales a logic feature to **20–50 distinct scenarios**.

## Test Scenario Template

```
### Scenario ID: TS_[UC-ID]_[SequenceNo]
**Scenario Title:** [Short, clear description of what is being tested]
**UC Reference:** [UC ID and UC Name]
**Req-ID:** [Requirement ID(s) this scenario traces to — e.g., UC-001-FR-003]
**Test Type:** [Functional | Integration | Data/State | End-to-End | Acceptance]
**Description:** [Action + condition to verify — see Logic-only scenario style. No UI objects.]
**Test Focus:** [Happy path | Alternative flow | Error/Exception | Boundary | Permission/Role | State transition | Integration | Idempotency/Concurrency | On-chain↔off-chain consistency]
```

## Scenario Coverage Rules

For each UC, generate scenarios that cover **all of the following** that apply:

| Coverage Area                                                        | Source in UC                                                              |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Happy path (main flow)                                               | Main Flow section                                                         |
| Each named alternative flow                                          | Alternative Flows section                                                 |
| Each error/exception flow                                            | Exception & Error Flows section                                           |
| Each business rule / validation                                      | Business Rules section                                                    |
| Boundary value cases                                                 | Any input/threshold with min/max/format constraints                      |
| Role/permission variations                                           | Actors & User Roles section                                              |
| State-machine transitions                                            | Lifecycle / circuit-breaker / margin / close-operation states — one scenario per valid transition + a representative invalid transition |
| Integration via queue / cron / Durable Object & external API (logic) | Integration / flow sections                                              |
| On-chain ↔ off-chain consistency                                     | Blockchain / integration sections                                        |
| Idempotency / retry / concurrency                                    | Error-handling sections + known defect-prone areas                       |
| API contract verification (logic contract)                           | API / Integration Behaviour section — verify input → output/effect (NOT HTTP status asserts) |
| Acceptance criteria verification                                     | Acceptance Criteria section (Section 8 of audited)                       |

Do not skip a coverage area just because the UC is brief. If a UC only has a main flow and two business rules, still produce scenarios for each. **Quality over quantity** — each scenario must represent a meaningfully different test intent.

## Output File Structure

```markdown
# Test Scenarios — [UC ID] [Feature Name]

> Source: <uc-review-report v[N] path>
> Generated: <YYYY-MM-DD>
> Domain/Architecture: <API/backend/bot — e.g. Cloudflare Workers + Hyperliquid, queue/cron/Durable-Object>

## [UC ID] — [UC Name]

### Scenario ID: TS_[UC ID]_001
**Scenario Title:** ...
**UC Reference:** ...
**Req-ID:** ...
**Test Type:** ...
**Description:** ...
**Test Focus:** ...

### Scenario ID: TS_[UC ID]_002
...

---

## [Next UC ID] — [Next UC Name]
...

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---------------|--------|--------------------|
| [Description] | [NFR: PERFORMANCE / SECURITY / LOAD / BLOCKED by audited gap] | Defer to specialist / wait for BA answer |
```

## Quality Checks Before Finalizing

Run this checklist before writing the output file:

- [ ] Every UC in the audited report has at least one scenario (or an Out-of-Scope row explaining why not).
- [ ] Every "to-cover" cell in the Phase 1 coverage matrix has at least one scenario.
- [ ] Every scenario has a unique `TS_[UC-ID]_NNN` ID.
- [ ] Every scenario cites a real Req-ID — no orphan scenarios.
- [ ] Every Test Type is assigned from the closed list (Functional / Integration / Data/State / End-to-End / Acceptance).
- [ ] Every state machine in scope has one scenario per valid transition plus at least one representative invalid-transition attempt.
- [ ] Boundary scenarios exist for every numeric/size/threshold constraint mentioned in the UC.
- [ ] EP partitions are split, not bundled.
- [ ] Multi-condition logic has at least one combinatoric (decision-table) scenario.
- [ ] Idempotency/retry/concurrency scenarios exist for any mutation that can be redelivered, retried, or run concurrently.
- [ ] Every scenario follows the Logic-only scenario style — action + condition, NO UI objects (no buttons/fields/screens/modals/clicks/taps).
- [ ] All test data uses realistic values (no abstract placeholders like "valid input").
- [ ] Verbatim message text from `requirement-common-files` is inlined into scenarios that reference error codes / business-rule IDs (so the downstream TC skill has the exact text without re-opening common docs).

## Out-of-Scope Handling

When a scenario area is identified as **performance**, **security beyond functional auth**, or **load** testing:

1. Do NOT generate scenarios for it.
2. Add a row to the `## ⚠️ Out-of-Scope Flags` table at the end of the scenarios file with reason and recommended action.

When a scenario area is **blocked** by a known audited gap (⚠️ Missing or ⚡ Partial KA):

1. Do NOT fabricate scenarios from inferred content.
2. Add a row to `## ⚠️ Out-of-Scope Flags` with reason `BLOCKED: <KA name> — needs BA answer` and recommended action `Resolve via qc-qna + re-audit before designing`.

## Boundaries

- This skill ONLY designs test scenarios. Atomic, executable test cases are `qc-func-tc-design-exbot`'s responsibility.
- This skill ONLY covers Functional / Integration / Data/State / E2E / Acceptance. Performance / load / security beyond functional auth are out of scope — flag, do not generate.
- This is a **logic-only / no-UI** skill: scenarios describe action + condition and MUST NOT reference UI objects. The tester selects the concrete operation/endpoint.
- Do NOT edit input files (`uc-review-report`, common files, project-context-master).
- Every scenario MUST trace to a UC via `TS_[UC-ID]_NNN` — no orphan scenarios.
- Output language follows source-input language per `global-rules.md` (Vietnamese audited UC → Vietnamese scenarios; English audited UC → English scenarios).
- This skill produces ONE file per UC (or per UC group when the audited report bundles them). It does NOT shard scenarios across multiple files.
