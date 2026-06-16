## Generate Test Cases (Design Workflow)

> **Scope:** This workflow produces ONLY the test case `.md` file(s). It is fully independent from the `.xlsx` artifact — no script invocation, no xlsx step. Conversion to `.xlsx` (Phase 3) and chat-side reporting (Step C) are orchestrated by `SKILL.md`. Do NOT write a separate summary file in this workflow.
>
> **Phase mapping (per `SKILL.md` → "Phase Map"):**
> - **Phase 1 — Analysis & Design Brief** = Step 1 below.
> - **Phase 2 — TC Drafting & MD Write** = Steps 2 + 3 + 3.5 + 4 below. (Step 3.5 persists per-variant scratch BEFORE the deliverable md write — required by Phase 3 auto-recovery.)
> - Phase 3 (MD → XLSX) is handled by `convert-md-to-xlsx.md`, not this file.
>
> **Checkpoint references:** all phase-boundary write/update steps follow `SKILL.md` → "Checkpoint & Resume Protocol" §5. Do NOT duplicate those rules here.

---

## Phase 1 — Analysis & Design Brief

### Status update — Start of Phase 1

Per `SKILL.md` → "Checkpoint & Resume Protocol" §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).
2. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Running — Phân tích & Lập đề cương thiết kế` (use the input UC's language — Vietnamese here; English equivalent: `Running — Analysis & Design Brief`). Skip if column missing (graceful degradation). If the UC has no row yet in the dashboard → invoke `qc-dashboard-sync` BEFORE updating.

### Step 1: Input Analysis (MANDATORY)

- Identify the highest version of all the input files (UC Readiness Report, Scenarios). Always select the highest version number available.
- Read the provided documents and comprehend the use case in preparation for test case design.
- Detect the output language from the source input language (Vietnamese UC → Vietnamese TCs; otherwise English) and record it as a working note.
- **If `qc-site-map.md` exists**, read §5/§6/§7/§9/§10 and record notes in `01_analysis.md`: API/Queue/DO inventory (§5), pre-/post-condition states (§6), role × operation access (§7), data/API/state touchpoints (§9), regression weight (§10). These feed Phase 2 drafting (Pre-condition/Expected Result fields, permission TCs, integration TCs, state-transition TCs). If missing → skip and warn once.

### Checkpoint write — End of Phase 1

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase):

1. **Write checkpoint file** `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/01_analysis.md` containing:
   - UC summary (1–2 sentences) + source input filename + version.
   - **AC list** extracted from the audited UC (just the AC IDs + one-line summary each).
   - **API/Queue/DO inventory snapshot**: condensed list of endpoints, queue consumers, and Durable Objects identified — this is the planning skeleton for the drafting in Phase 2.
   - **Planned TC scope**: how many operations × ~estimated TCs per operation (FUNC rough count).
   - **Detected output language** (VI / EN).
   - Working notes: version of source files read, target md path (resolved from `func-test-cases-draft` in path-registry).
2. **Worklog**: rewrite last entry → `status = "Phase 1 done"`.
3. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Phân tích & Lập đề cương thiết kế done` (skip if column missing).

> **Note:** `last_phase_done: 1` is NOT written here — it gets written at the start of Phase 2 (see "Status update — Start of Phase 2" below). Per §5.1, advancing `last_phase_done` happens only at phase transition.

---

## Phase 2 — TC Drafting & MD Write

### Status update — Start of Phase 2

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.1 (start-of-phase / transition write). This is the moment we advance `last_phase_done` to confirm Phase 1 is done.

1. **Update `progress.md`** → `last_phase_done: 1`, `next_phase: 2`, `updated_at: <now>`. (Preserve any other existing fields / notes.)
2. **Worklog**: rewrite last entry → `status = "Running (Phase 2)"`.
3. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Running — Soạn TC & ghi MD` (VI) / `Running — TC Drafting & MD Write` (EN). Skip if column missing.

> **Resume note:** Probe for `process-logging/<UC-ID>/02_designed_tcs.md`. If scratch already exists (prior run finished drafting), SKIP Steps 2 + 3 + 3.5 — design is already done. Read the scratch and jump directly to Step 4. Per `SKILL.md` §4 Resume load table.

### Step 2: Detailed Drafting (MANDATORY)

Design test cases for the backend-only operations declared in the audited UC (API endpoints, queue consumers, Durable Objects). The result of this step is the test case content persisted in Step 3.5 (scratch) and written to the deliverable `.md` in Step 4.

**Coverage categories (apply systematically, not intuitively):**

1. **Happy Path** — main flow for each operation (POST endpoint success, queue consumer success, DO lease acquired).
2. **Alternative Path** — valid but non-standard flows (optional fields omitted, edge-of-valid inputs).
3. **Exception / Error Flow** — each named error code from the audited UC Section 4 (400/403/409/5xx); NV-blocked paths marked `[BLOCKED: NV-N pending]`.
4. **State Transition Cases** — for each lifecycle transition in the audited UC Section 5: valid trigger, guard pass, guard fail, NV-gated transitions (marked blocked).
5. **DO Behavior Cases** — lease expiry, contention (second caller during active lease), state after expiry action.
6. **Queue Behavior Cases** — retry N (where N = max retries), DLQ trigger, idempotency (same key processed twice), SLA breach scenario.
7. **API Contract Cases** — required field missing, invalid type/format, constraint violation (BVA: at limit / limit−1 / limit+1 for every numeric constraint).
8. **Permission/Role Cases** — each ACT-\* actor that may or may not call the endpoint; unauthorized access → expected error.

**Test Case Writing rules (MANDATORY):** Apply all rules in `qc-func-tc-design/rules/testcase-instruction-rules.md` (Layout, Encoding, etc.).

**Test cases example**: read the language-matched reference (`Testcase-refer-vi.md` for VI / `Testcase-refer-en.md` for EN) and align new TCs to the same structural & writing style.

### Step 3: Build the Requirement Traceability Matrix

- Build the RTM mapping every Acceptance Criterion of the audited UC to the drafted Test Case IDs.
- Verify 100% coverage. If any AC has no linked TCs, fix the drafting in Step 2 before proceeding.
- The RTM is embedded in the md prelude (Step 4), not in a separate file.

### Step 3.5: Persist Designed TCs to Scratch (MANDATORY — atomic single Write)

This step is the **safety net for Phase 3 auto-recovery**. It locks down the in-memory design before the final md write begins.

1. **Compose the full scratch content** in working memory, using the SAME content format as the final deliverable md described in Step 4 (prelude + operation/section headers + TC tables, same heading-level rules).
2. **Write the entire scratch content** to `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/02_designed_tcs.md` in **ONE atomic Write call**.
   - Do NOT use Edit / multiple appends — if interrupted, Phase 3 cannot recover.
3. Do NOT delete or modify the scratch later in this run — it is removed only in `SKILL.md` → Step D cleanup.

After this step, design is durably persisted. Step 4 is a re-materialization at the deliverable path.

### Step 4: Write the .md File(s) (MANDATORY)

Re-materialize the scratch content (`02_designed_tcs.md` from Step 3.5) to the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`. Use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume. Each file is an atomic single Write.

**Deliverable file naming** (per `rules/naming-convention.md`):
- `UC-101_bot-start_testcases_20260616_v1.md`

No `_<variant>` segment — this project is backend-only (PTL-04 EXBOT, no UI variant).

**At the TOP of the md (or top of `part1` if multi-part), include the following required prelude:**

```markdown
# Test Cases — [UC-ID] [feature-name]

**Total test cases:** X (FUNC: Z)
**Platform:** backend-only (PTL-04 EXBOT — no UI)
**Source UC:** [audited filename + version]
**Source scenarios (if any):** [scenarios filename + version]
**Output language:** [VI / EN]

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | …                   | TC_001, TC_002    | Covered |
| …     | …                   | …                 | …       |

---
```

**Heading-level rules (MANDATORY — they govern what does and does not appear in the xlsx):**
- The prelude MUST use only `#` (h1) and `####` (h4) heading levels — these are skipped by the converter.
- Use `##` (h2) ONLY for operation headers (e.g., `## I. Bot Start` / `## II. Hedge Sync`).
- Use `###` (h3) ONLY for FUNC section headers (e.g., `### I.1. Functional verification — Bot Start`).

After the prelude, write all operation / FUNC sections with their test case tables, following the layout and sorting rules in `qc-func-tc-design/rules/testcase-instruction-rules.md`.

**Do NOT write a separate summary file.**

### Checkpoint write — End of Phase 2

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase).

1. **Compute the Phase 2 summary** by counting TCs in the final md (which equals the scratch — both should match exactly at this moment):
   - Total TCs + FUNC count (discrete integers).
   - Per-operation breakdown: for each `## <Roman>.` operation in the final md, count TC rows in its `### <Roman>.1.` FUNC table.
   - The output language detected in Phase 1.
   - The scratch path: absolute path to `02_designed_tcs.md`.
   - The final md path(s) written in Step 4 (single file or multi-part list, all absolute paths).
2. **Append a `## Phase 2 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. Atomic single Write preserving all other progress.md fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Update `updated_at: <now>`. Do NOT touch `last_phase_done` here.
3. **Worklog**: rewrite last entry → `status = "Phase 2 done"`. Append the final `.md` path(s) to `output` (excluding `process-logging/`).
4. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Soạn TC & ghi MD done` (VI) / `TC Drafting & MD Write done` (EN). Skip if column missing.

> **Note:** `last_phase_done: 2` is NOT written here — it gets written at the START of Phase 3, only AFTER Phase 3's Step 0 verification gate passes. This guarantees a partial / mismatched md cannot be silently accepted as "Phase 2 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 3

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 2 finishes successfully.
