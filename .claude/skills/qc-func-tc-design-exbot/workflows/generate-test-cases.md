## Generate Test Cases (Design Workflow)

> **Scope:** This workflow produces ONLY the test case `.md` file(s). Do NOT write a separate summary file in this workflow.
>
> **Checkpoint references:** all phase-boundary write/update steps follow `workflows/checkpoint-protocol.md` §4. Do NOT duplicate those rules here.

---

## Phase 1 — Analysis & Design Brief

### Status update — Start of Phase 1

Per `workflows/checkpoint-protocol.md` §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).

### Step 1: Input Analysis (MANDATORY)

#### 1.1 Read all input files
- `uc-review-report`
- (Optional) `func-test-scenarios`
- Load `.claude/skills/qc-func-tc-design-exbot/references/design-technical/common-logic-technical.md` (the 5 logic phases + blockchain backend add-on).
- Load `.claude/skills/qc-func-tc-design-exbot/references/design-technical/logic-technical.md` (the EXBOT / backend-bot add-on checklists).

#### 1.2 Confirm Logic-only Scope (MANDATORY)

This skill has NO platform variants — there is no web / mobile / desktop split. The feature under test is a backend / API / bot / worker with NO UI.

1. Confirm from `uc-review-report` / `project-context-master.md` that the feature under test is backend / logic-only (no UI screens are owned by this module).
2. If the feature actually has a user interface, STOP and tell the user to use `qc-func-tc-design` (the UI variant) instead.
3. All drafting in this run produces ONE logic test-case track (the on-disk scratch / final md use the literal token `logic` in place of a variant name — there is exactly one).

---

### Step 2: Detailed Drafting (MANDATORY)

Apply the logic test-design technical files to design test cases. The result of this step is the test case content that will be persisted in Step 3.5 (scratch) and written to the deliverable `.md` in Step 4.

#### 2.1 — Apply the 5-Phase Logic Drafting (Common)

Apply ALL 5 logic phases described in `common-logic-technical.md`:
Phase 1 Preconditions & Initial State → Phase 2 Input & Contract Validation → Phase 3 Core Functional Logic → Phase 4 Integration & Data Consistency → Phase 5 Non-Functional (logic-accessible).

If the feature touches a chain / wallet / signer (per the trigger gate in `common-logic-technical.md`), ALSO apply the Blockchain (Chain + Signer) backend add-on ON TOP of the 5 phases.

#### 2.2 — Apply the EXBOT / Backend-Bot Add-on

Apply the relevant checklists from `logic-technical.md` (lifecycle state machine, circuit breaker, margin status, close_operations, queue fan-out, hedge-sync, initialization, reconciliation, SAFE_MODE, precision & idempotency, external & cross-module dependencies, test environment & determinism). They contribute to the same in-memory logic TC list that gets persisted at the end of Phase 1.

**Logic-only step style (MANDATORY — see `SKILL.md` → "Logic-only Step Style"):** every Step is an action + condition with NO UI object (the tester picks the concrete endpoint / call); every Expected Result is an observable system effect (API response / state transition / DB or on-chain state / emitted event / message code), NEVER a visual assertion. For on-chain operations, state BOTH the on-chain and off-chain expected result. Example step: `Deposit ETH to the HL wallet; the deposit amount should be ≥ the minimum deposit amount.`

**Test Case Writing rules (MANDATORY):** 
Apply all the rules in `qc-func-tc-design-exbot/rules/testcase-instruction-rules.md` and `.claude/rules/qc-writting-rules.md`.

- **Test cases example**: read `qc-func-tc-design-exbot/references/Testcase-refer-en.md` and align new TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style). All test-case output is in **English**.

### Step 3: Build the Requirement Traceability Matrix

- Build the `Requirement Traceability Matrix` mapping every Acceptance Criterion of the audited UC to the drafted Test Case IDs.
- Verify 100% coverage. If any AC has no linked TCs, fix the drafting in Step 2 before proceeding.
- The RTM will be embedded in the md prelude (Step 4), not in a separate file. Build ONE RTM for this run (logic-only — single track).

### Step 3.5: Persist Designed TCs to Scratch (MANDATORY — atomic single Write)

This step is the **safety net for 2 auto-recovery**. It locks down the in-memory design before the final md write begins, so that if the final md write is interrupted (multi-part flow, network blip, context flush, etc.), Phase 2's verification gate can detect the mismatch and auto-recover from this scratch — WITHOUT having to re-run the 6-phase drafting.

1. **Compose the full scratch content** in working memory, using the SAME content format as the final deliverable md described in Step 4:
   - The complete required prelude (`# Test Cases — [UC-ID] …`, totals, source filenames, RTM table, etc.).
   - All function / operation sections (`## <Roman>. …`) with their typed subsections — FUNC (`### <Roman>.1. …`), INTG & State (`### <Roman>.2. …`), and NFR-logic (`### <Roman>.3. …`) — and their test case tables.
   - The same heading-level rules as Step 4 (only `#` / `####` in the prelude, `##` for function/operation groups, `###` for FUNC/INTG/NFR sections).
2. **Write to the scratch path** — this skill is logic-only (single track): write the full scratch content to `.claude/skills/qc-func-tc-design-exbot/process-logging/<UC-ID>/02_designed_tcs_logic.md` in **ONE atomic Write call** containing the ENTIRE content. The literal token `logic` stands in for the variant name everywhere Phase 2's per-variant loop expects one; there is exactly one.
   - Do NOT use Edit / multiple appends to build the scratch incrementally — if the scratch's own Write is interrupted, Phase 2 cannot recover. If the volume exceeds a Write's practical limit, that is the signal to fail loudly and ask the user — multi-part scratch is NOT supported.
3. Do NOT delete or modify the scratch file later in this skill run — it is the durable source of truth for Phase 1 and is only removed in `SKILL.md` → Step D cleanup at end-of-run.

After this step completes, the design work of Phase 1 is **durably persisted**. Step 4 below is a re-materialization of the same content at the deliverable path; if Step 4 is interrupted, the scratch is still on disk for Phase 2 auto-recovery.

### Step 4: Write the .md File(s) (MANDATORY)

Re-materialize the scratch content (`02_designed_tcs_logic.md` from Step 3.5) to the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`. Use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume. Each file (single or per-part) is an atomic single Write.

**Deliverable file naming:** follow `rules/naming-convention.md` for `func-test-cases-draft`. Example for UC-EXBOT-001: `UC-EXBOT-001_bot-start_testcases_v1.md`. (Logic-only — there is no variant segment.)

**At the TOP of the md (or top of `part1` if multi-part), include the following required prelude:**

```markdown
# Test Cases — [UC-ID] [feature-name]

**Total test cases:** X (FUNC: a, INTG: b, NFR: c)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** [audited filename + version]
**Source scenarios (if any):** [scenarios filename + version]
**Output language:** English

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | …                   | TC_001, TC_002    | Covered |
| …     | …                   | …                 | …       |

---
```

**Heading-level rules (MANDATORY — they govern what does and does not appear in the xlsx):**
- The prelude MUST use only `#` (h1) and `####` (h4) heading levels — these are skipped by the converter, so the prelude does NOT leak into the xlsx.
- Use `##` (h2) ONLY for function / operation group headers (e.g., `## I. Operation: Bot start preflight`).
- Use `###` (h3) ONLY for FUNC / INTG / NFR section headers (e.g., `### I.1. …` / `### I.2. …` / `### I.3. …`).

After the prelude, write all function/operation sections (FUNC / INTG / NFR) with their test case tables, following the layout and sorting rules in `qc-func-tc-design-exbot/rules/testcase-instruction-rules.md`.

**Do NOT write a separate summary file.** The md (with its prelude) is the only design artifact this workflow produces. Anything noteworthy beyond the prelude (e.g., out-of-scope items, requirement gaps observed during drafting) will be reported on chat by the orchestrator (`SKILL.md` → Step C).

### Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §4.2 (end-of-phase). At this point, two artifacts already exist on disk: the scratch (`02_designed_tcs_logic.md` from Step 3.5) and the final deliverable `.md` file(s) (from Step 4). The remaining work is to publish the `## Phase 1 Summary` block to progress.md (with a single `### Variant: logic` sub-block, so Phase 2's loop runs once), then update worklog.

1. **Compute the Phase 1 summary** by counting TCs in the final md (which equals the scratch — both should match exactly at this moment):
   - Total TCs + FUNC / INTG / NFR split (3 discrete integers).
   - Per-group breakdown: for each `## <Roman>.` operation group in the final md, count TC rows in its `### <Roman>.1.` (FUNC), `### <Roman>.2.` (INTG) and `### <Roman>.3.` (NFR) tables.
   - The output language detected in Phase 1.
   - The scratch path: absolute path to `02_designed_tcs_logic.md`.
   - The final md path(s) written in Step 4 (single file or multi-part list, all absolute paths).
2. **Append a SINGLE `## Phase 1 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. The block contains:
   - A top-level `**Variants in scope:**` line with the single value `logic`.
   - ONE `### Variant: logic` sub-block with the fields computed above (totals, language, scratch path, final md paths, per-group breakdown table). The `FUNC total` and `INTG+NFR total` lines (per the checkpoint schema) carry the logic split: FUNC = Functional logic cases; INTG+NFR = Integration/State + Non-functional logic cases.
   - This is an atomic single Write that overwrites `progress.md` while preserving all existing fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Do NOT touch `last_phase_done` here — it stays at its current value (set when Phase 1 started). Update `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`. Append the final `.md` path(s) to `output` (excluding `process-logging/`).

> **Note:** `last_phase_done: 1` is NOT written here — it gets written at the START of Phase 2, only AFTER Phase 2's Step 0 verification gate passes. This is what guarantees a partial / mismatched md cannot be silently accepted as "Phase 1 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 2

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 1 finishes successfully.
