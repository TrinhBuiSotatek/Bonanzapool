---
name: qc-func-scenario-design
description: Designs test scenarios from a finalized, reviewed UC (Use Case) requirement document. Trigger this skill whenever the user says "design test scenarios", "build test scenarios", or provides a uc-review-report output and asks to proceed with testing. Also trigger when the user mentions their requirement is ready and they want to move to QA/test design, even if they don't say "test scenario" explicitly.
---
# Test Scenario Design Skill

## Purpose

Transform a finalized UC requirement (ideally reviewed and approved by `qc-uc-read`) into ready-to-use **test scenarios** grouped by UC, covering Functional / Integration / UI / End-to-End / Acceptance testing for web applications and APIs.

Scenarios describe **what** must be verified at a meaningful level of intent (one scenario = one distinct test intent). They are the bridge between an audited requirement and atomic test cases — they are NOT atomic, executable test cases (those belong to `qc-func-tc-design`).

## Trigger Conditions

- **Manual:** "design test scenarios", "build test scenarios", "thiết kế test scenarios".
- **Implicit:** the user shares an audited `uc-review-report` and asks to "proceed to testing" / "next step" / "move to QA" without naming the artifact.

## Input Contract

Resolve via `path-registry.md`:

- `project-context-master` — read §1 **Product Platform Type** (informs UI/E2E scenario phrasing — Tap vs Click, Swipe vs Hover, Hardware back vs browser back, etc.).
- `qc-site-map` (optional) — if present, read §6 Navigation (pre/post-condition + E2E paths), §7 Role/access (permission scenarios), §8 Screen ↔ Feature mapping (screens touched by this UC's feature → coverage matrix), §9 Data/API/Integration/State touchpoints (integration + state edge cases), §10 Regression anchors (risk emphasis). If missing, skip site-map-derived scenarios and warn once.
- `uc-review-report` — latest version of the audited UC document for `<UC-ID>`.
- `requirement-common-files` — for verbatim business rules, error codes/messages, and common functions referenced by the UC.

## Output Contract

- **`func-test-scenarios`** (`.md`) — primary deliverable, one file per UC (or per UC group), versioned per `naming-convention.md`:
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

1. Read `project-context-master.md` §1 → Product Platform Type. Load the matching interaction vocabulary (web/desktop: Click/Hover/Right-click; mobile native: Tap/Long-press/Swipe/Pinch/Hardware-back).
1a. **If `qc-site-map.md` exists**, read §6/§7/§8/§9/§10. Use §8 to enumerate screens touched by this UC's feature (rows for the coverage matrix in Step 4); §6 to derive pre-/post-condition states for E2E scenarios; §7 for role/permission scenarios; §9 for integration + data-state edge cases; §10 to weight risk-based emphasis. If missing → skip and warn once.
2. Read the highest-version `uc-review-report` for `<UC-ID>`. Build a working understanding of:
   - All UC IDs in scope and their names
   - All functions/features within each UC
   - Main flow, alternative flows, exception/error flows
   - Business rules and validations (with verbatim wording from common files)
   - Acceptance criteria (Section 8 of the audited report)
   - Actors / roles / permissions
   - Pre/postconditions
   - API endpoints + UI states (if applicable)
3. Read `requirement-common-files` only for any error code / business-rule ID / common-function name cited in the UC — to inline the exact message text into scenario descriptions.
4. **Build a coverage matrix in working memory:** `UC × Test Type × Coverage Area`. Rows = each UC in scope; columns = the 9 coverage areas listed in §"Scenario Coverage Rules". Mark each cell as:
   - `to-cover` — has enough info, will produce one or more scenarios
   - `blocked` — the audited report flagged the underlying KA as ⚠️ Missing / ⚡ Partial; surface in §Out-of-Scope Flags, do NOT fabricate
   - `out-of-scope` — performance / load / security beyond functional auth; surface in §Out-of-Scope Flags
5. If the audited report's Verdict is `NOT READY`, STOP and ask the user whether to proceed (scenarios from a Not-Ready UC will inherit known gaps). Do NOT silently continue.
6. **Worklog:** rewrite last entry → `status = "Phase 1 done"`.

> If a UC ID or function name is not explicitly stated in the document, infer from the feature name and note your inference clearly in the output (e.g., *"UC ID inferred as UC-001 from title 'User Login Feature'."*).

### Phase 2 — Scenario Drafting

For every `to-cover` cell in the matrix, draft scenarios using the **Scenario Template** below. Apply the **MANDATORY Test Design Techniques** systematically (see §"MANDATORY Test Design Techniques"). Each scenario MUST:

- Have a unique ID `TS_[UC-ID]_NNN` (zero-padded sequence per UC).
- Cite a Req-ID (UC ID + section reference — e.g., `UC-001-FR-003`).
- Map to exactly one Test Type (Functional / Integration / UI / End-to-End / Acceptance).
- Carry a Test Focus tag (Happy path / Alternative flow / Error/Exception / Boundary / Permission/Role / UI State / API contract).
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
   - UI: X scenarios
   - End-to-End: X scenarios
   - Acceptance: X scenarios

   ### Notes
   - Inferred UC IDs / function names: <list or "none">
   - Blocked coverage cells (need BA): <list or "none">
   - Out-of-scope items flagged: <list or "none">
   ```

## Mindset (adapted from `qc-func-tc-design` so both skills share one playbook)

- **Risk-Based:** scenarios for core transactions (login, payment, data submit) get extra coverage (alternative + exception flows). Trivial UI scenarios stay lean.
- **Shift-Left "What-If" Engine:** for every requirement, ask *"What if user does X / Y / Z?"*. Each meaningful "what-if" becomes its own scenario.
- **Be Skeptical:** the UC is incomplete by default. If a flow can silently branch (e.g., session expiry mid-action), add an alternative-flow scenario.
- **Be Domain-Driven:** Fintech/Crypto → emphasize security & transaction accuracy. Cooking/Social → emphasize UX & data sync. Tailor scenario emphasis to the domain declared in `project-context-master.md` §1.

## MANDATORY Test Design Techniques

Same set as `qc-func-tc-design` — applied at the **scenario level** (one technique application typically produces one scenario; the downstream TC-design skill expands that scenario into atomic cases).

1. **Equivalence Partitioning (EP)** — one scenario per valid/invalid partition. Never bundle.
   - Allowed file types `.png .jpg .svg` → one scenario per valid extension + one per representative invalid extension. Do NOT collapse "all valid extensions" into one scenario.

2. **Boundary Value Analysis (BVA)** — for any numeric/length/size constraint, one scenario each at `Limit`, `Limit − 1`, `Limit + 1`.
   - 255-char max → scenarios for 1, 255, 256 chars.
   - 1MB max → scenarios for 1.00MB exactly, 1.01MB.

3. **Decision Table / Combinatorics** — for multi-filter, multi-condition, or multi-variable forms, write matrix scenarios.
   - `Filter A valid × Filter B valid`, `A valid × B invalid`, `A invalid × B valid`, … Never test a filter in isolation if it logically interacts with another.

4. **State Transition** — for UI/data with explicit states (Draft → Published → Archived), one scenario per valid transition + at least one invalid-transition attempt.

5. **Use Case Testing** — derive Happy / Alternative / Exception flow scenarios directly from the UC's Main / Alt / Exception sections.

6. **Error Guessing** — apply domain experience to add scenarios for defect-prone areas not explicitly listed in the UC (concurrent edit, race condition, network drop mid-submit, double-click on action button, paste with surrounding whitespace, etc.).

> Failure to apply these techniques limits scenarios to basic happy paths. Applying them correctly typically scales a CRUD feature to **20–50 distinct scenarios**.

## Test Scenario Template

```
### Scenario ID: TS_[UC-ID]_[SequenceNo]
**Scenario Title:** [Short, clear description of what is being tested]
**UC Reference:** [UC ID and UC Name]
**Req-ID:** [Requirement ID(s) this scenario traces to — e.g., UC-001-FR-003]
**Test Type:** [Functional | Integration | UI | End-to-End | Acceptance]
**Description:** [One or two sentences describing the scenario — what condition or flow is being verified]
**Test Focus:** [Happy path | Alternative flow | Error/Exception | Boundary | Permission/Role | UI State | API contract]
```

## Scenario Coverage Rules

For each UC, generate scenarios that cover **all of the following** that apply:

| Coverage Area                    | Source in UC                                        |
| -------------------------------- | --------------------------------------------------- |
| Happy path (main flow)           | Main Flow section                                   |
| Each named alternative flow      | Alternative Flows section                           |
| Each error/exception flow        | Exception & Error Flows section                     |
| Each business rule / validation  | Business Rules section                              |
| Boundary value cases             | Any field with min/max/format constraints           |
| Role/permission variations       | Actors & User Roles section                         |
| UI state transitions             | UI/UX Behaviour section (if applicable)             |
| API contract verification        | API / Integration Behaviour section (if applicable) |
| Acceptance criteria verification | Acceptance Criteria section (Section 8 of audited)  |

Do not skip a coverage area just because the UC is brief. If a UC only has a main flow and two business rules, still produce scenarios for each. **Quality over quantity** — each scenario must represent a meaningfully different test intent.

## Output File Structure

```markdown
# Test Scenarios — [UC ID] [Feature Name]

> Source: <uc-review-report v[N] path>
> Generated: <YYYY-MM-DD>
> Platform: <web-responsive | mobile-native | ...>

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
- [ ] Every Test Type is assigned from the closed list (Functional / Integration / UI / End-to-End / Acceptance).
- [ ] Boundary scenarios exist for every numeric/length/size field mentioned in the UC.
- [ ] EP partitions are split, not bundled.
- [ ] Multi-filter / multi-condition features have at least one combinatoric scenario.
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

- This skill ONLY designs test scenarios. Atomic, executable test cases are `qc-func-tc-design`'s responsibility.
- This skill ONLY covers Functional / Integration / UI / E2E / Acceptance. Performance / load / security beyond functional auth are out of scope — flag, do not generate.
- Do NOT edit input files (`uc-review-report`, common files, project-context-master).
- Every scenario MUST trace to a UC via `TS_[UC-ID]_NNN` — no orphan scenarios.
- Output language follows source-input language per `global-rules.md` (Vietnamese audited UC → Vietnamese scenarios; English audited UC → English scenarios).
- This skill produces ONE file per UC (or per UC group when the audited report bundles them). It does NOT shard scenarios across multiple files.
