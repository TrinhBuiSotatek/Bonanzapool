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
- Load `.claude/skills/qc-func-tc-design/references/design-technical/common-technical.md`

#### 1.2 Resolve Platform Variants (MANDATORY)

1. Read `project-context-master.md` §1 → **Product Platform Type**.
2. Parse the value(s). One or more of: `web-responsive`, `web-static`, `mobile-native`, `mobile-hybrid`, `desktop-native`.
3. **If the field is missing or blank → STOP and ask the user to populate it** (this field is mandatory; the rubric drives TC coverage).
4. For EACH applicable variant, load `qc-func-tc-design/references/design-technical/<variant>-technical.md` end-to-end. Hold all loaded rubrics in working memory.
5. Record the resolved variant list as a working note.

---

### Step 2: Detailed Drafting (MANDATORY)

Apply the design technical to design test cases. The result of this step is the test case content that will be persisted in Step 3.5 (scratch) and written to the deliverable `.md` in Step 4.

#### 2.1 — Apply the 6-Phase Drafting Common

Apply ALL 6 phases described in the `common-technical.md` file.

#### 2.2 — Apply the 6-Phase Drafting per variant

For EACH platform variant loaded in §1.2, apply end-to-end of the corresponding technical file.

They all contribute to the same in-memory TC list **per variant** that gets persisted at the end of phase 1.

> **Multi-platform rule:** If multiple variants apply (e.g., a UC ships on BOTH web-responsive and mobile-native), draft a SEPARATE TC list per variant, including both common and per variant — to be persisted in a SEPARATE scratch file (Step 3.5) and written to a SEPARATE deliverable `.md` (Step 4). Do NOT merge variants into one file. Each variant gets its own RTM (Step 3) and its own prelude.

**Test Case Writing rules (MANDATORY):** 
Apply all the rules in `qc-func-tc-design/rules/testcase-instruction-rules.md` and `.claude/rules/qc-writting-rules.md`.

- **Test cases example**: read the language-matched reference — `qc-func-tc-design/references/Testcase-refer-vi.md` for Vietnamese test cases, `qc-func-tc-design/references/Testcase-refer-en.md` for English test cases — and align new TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style).

### Step 3: Build the Requirement Traceability Matrix

- Build the `Requirement Traceability Matrix` mapping every Acceptance Criterion of the audited UC to the drafted Test Case IDs.
- Verify 100% coverage. If any AC has no linked TCs, fix the drafting in Step 2 before proceeding.
- The RTM will be embedded in the md prelude (Step 4), not in a separate file.
- **Multi-platform:** Build ONE RTM PER variant. Each variant's RTM lives in its own `.md` file's prelude. Each RTM must independently cover 100% of the audited ACs that are in scope for that variant.

### Step 3.5: Persist Designed TCs to Scratch (MANDATORY — atomic single Write)

This step is the **safety net for 2 auto-recovery**. It locks down the in-memory design before the final md write begins, so that if the final md write is interrupted (multi-part flow, network blip, context flush, etc.), Phase 2's verification gate can detect the mismatch and auto-recover from this scratch — WITHOUT having to re-run the 6-phase drafting.

1. **Compose the full scratch content** in working memory, using the SAME content format as the final deliverable md described in Step 4:
   - The complete required prelude (`# Test Cases — [UC-ID] …`, totals, source filenames, RTM table, etc.).
   - All screen sections (`## <Roman>. …`) with their GUI (`### <Roman>.1. …`) and FUNC (`### <Roman>.2. …`) subsections and test case tables.
   - The same heading-level rules as Step 4 (only `#` / `####` in the prelude, `##` for screens, `###` for GUI/FUNC).
2. **Write to scratch path(s)** — ALWAYS per-variant (no special case for single-variant projects): for EACH platform variant V resolved in Step 2.1, write that variant's full scratch content to `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/02_designed_tcs_<V>.md` in **ONE atomic Write call** containing the ENTIRE content for that variant.
   - For a single-variant project, this means writing ONE file with the project's only variant in its name (e.g., `02_designed_tcs_web-responsive.md`). The "bare" name `02_designed_tcs.md` (without variant suffix) is NEVER used — Phase 2 always probes by variant.
   - For a multi-variant project, write N atomic Write calls, one per variant.
   - Do NOT use Edit / multiple appends to build a scratch incrementally — if a scratch's own Write is interrupted, Phase 2 cannot recover that variant. If a single variant's volume exceeds a Write's practical limit, that is the signal to fail loudly and ask the user — multi-part scratch per variant is NOT supported.
3. Do NOT delete or modify any scratch file later in this skill run — they are durable sources of truth for Phase 1 and are only removed in `SKILL.md` → Step D cleanup at end-of-run.

After this step completes, the design work of Phase 1 is **durably persisted for every variant**. Step 4 below is a re-materialization of the same content at the deliverable path; if Step 4 is interrupted for any variant, that variant's scratch is still on disk for Phase 2 auto-recovery.

### Step 4: Write the .md File(s) (MANDATORY)

For EACH platform variant V resolved in Step 1.2, re-materialize that variant's scratch content (`02_designed_tcs_<V>.md` from Step 3.5) to the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`. Each variant produces its own deliverable file(s); within a variant, use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume. Each file (single or per-part) is an atomic single Write.

**Deliverable file naming:** Insert a `_<variant>` segment between the `testcases` type and the version, per `rules/naming-convention.md`. Example for UC-101 with both web-responsive and mobile-native:
- `UC-101_user-login_testcases_web-responsive_v1.md`
- `UC-101_user-login_testcases_mobile-native_v1.md`

For a single-variant project the same naming applies (just one variant in the name), e.g., `UC-101_user-login_testcases_web-responsive_v1.md`. The "no-variant" filename pattern is NOT used — every deliverable carries its variant in the name so Phase 2's per-variant flow can pair scratch ↔ final md unambiguously.

**At the TOP of the md (or top of `part1` if multi-part), include the following required prelude:**

```markdown
# Test Cases — [UC-ID] [feature-name] [— <variant> if multi-platform]

**Total test cases:** X (GUI: Y, FUNC: Z)
**Platform variant:** [web-responsive / web-static / mobile-native / mobile-hybrid / desktop-native]
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
- The prelude MUST use only `#` (h1) and `####` (h4) heading levels — these are skipped by the converter, so the prelude does NOT leak into the xlsx.
- Use `##` (h2) ONLY for screen headers (e.g., `## I. Màn hình: …` / `## I. Screen: …`).
- Use `###` (h3) ONLY for GUI / FUNC section headers (e.g., `### I.1. …` / `### I.2. …`).

After the prelude, write all screen / GUI / FUNC sections with their test case tables, following the layout and sorting rules in `qc-func-tc-design/rules/testcase-instruction-rules.md`.

**Do NOT write a separate summary file.** The md (with its prelude) is the only design artifact this workflow produces. Anything noteworthy beyond the prelude (e.g., out-of-scope items, requirement gaps observed during drafting) will be reported on chat by the orchestrator (`SKILL.md` → Step C).

### Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §4.2 (end-of-phase). At this point, the following artifacts already exist on disk: ONE scratch file per variant (`02_designed_tcs_<V>.md` from Step 3.5) and that variant's final deliverable `.md` file(s) (from Step 4). The remaining work is to publish ONE consolidated `## Phase 1 Summary` block to progress.md covering ALL variants (so Phase 2 can iterate per variant), then update worklog.

1. **Compute the per-variant Phase 1 summary** by counting TCs in EACH variant's final md (which equals that variant's scratch — both should match exactly at this moment). For each variant V:
   - Total TCs + GUI / FUNC split (3 discrete integers).
   - Per-screen breakdown: for each `## <Roman>.` screen in V's final md, count TC rows in its `### <Roman>.1.` (GUI) and `### <Roman>.2.` (FUNC) tables.
   - The output language detected in Phase 1.
   - The scratch path: absolute path to `02_designed_tcs_<V>.md`.
   - The final md path(s) for V written in Step 4 (single file or multi-part list, all absolute paths).
2. **Append a SINGLE `## Phase 1 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. The block contains:
   - A top-level `**Variants in scope:**` line listing all variants comma-separated.
   - ONE `### Variant: <V>` sub-block per variant, in the same order. Each sub-block has the per-variant fields computed above (totals, language, scratch path, final md paths, screen breakdown table).
   - This is an atomic single Write that overwrites `progress.md` while preserving all existing fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Do NOT touch `last_phase_done` here — it stays at its current value (set when Phase 1 started). Update `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`. Append ALL variants' final `.md` path(s) to `output` (excluding `process-logging/`).

> **Note:** `last_phase_done: 1` is NOT written here — it gets written at the START of Phase 2, only AFTER Phase 2's Step 0 verification gate passes for ALL variants. This is what guarantees a partial / mismatched md for ANY variant cannot be silently accepted as "Phase 1 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 2

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 1 finishes successfully.
