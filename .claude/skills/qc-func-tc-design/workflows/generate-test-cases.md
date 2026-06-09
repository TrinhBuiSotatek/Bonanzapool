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
- **If `qc-site-map.md` exists**, read §6/§7/§8/§9/§10 and record per-screen notes in `01_analysis.md`: pre-/post-condition states (§6), role × screen access (§7), screens-in-scope for the feature (§8), data/API/state touchpoints (§9), regression weight (§10). These feed Phase 2 Step 2.2 drafting (Pre-condition/Expected Result fields, permission TCs, integration TCs, state-transition TCs). If missing → skip and warn once.

### Checkpoint write — End of Phase 1

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase):

1. **Write checkpoint file** `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/01_analysis.md` containing:
   - UC summary (1–2 sentences) + source input filename + version.
   - **AC list** extracted from the audited UC (just the AC IDs + one-line summary each).
   - **UI inventory snapshot**: condensed list of screens / sections / atomic UI elements identified, grouped by screen — this is the planning skeleton for the 6-phase drafting in Phase 2.
   - **Planned TC scope**: how many screens × ~estimated TCs per screen (GUI + FUNC rough split).
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

> **Resume note:** For EACH platform variant resolved in Step 2.1 below, probe for `process-logging/<UC-ID>/02_designed_tcs_<variant>.md`. If a variant's scratch already exists (prior run finished that variant's drafting), SKIP Steps 2 + 3 + 3.5 for that variant — its design is already done. Read its scratch and jump directly to Step 4 for that variant. Variants without scratch get fresh drafting from Step 2 onward. Per `SKILL.md` §4 Resume load table.

### Step 2: Detailed Drafting (MANDATORY)

Apply the platform-aware 6-phase rubric to design test cases. The result of this step is the test case content that will be persisted in Step 3.5 (scratch) and written to the deliverable `.md` in Step 4.

#### 2.1 — Resolve Platform Variants (MANDATORY)

1. Read `project-context-master.md` §1 → **Product Platform Type**.
2. Parse the value(s). One or more of: `web-responsive`, `web-static`, `mobile-native`, `mobile-hybrid`, `desktop-native`.
3. **If the field is missing or blank → STOP and ask the user to populate it** (this field is mandatory; the rubric drives TC coverage).
4. For EACH applicable variant, load `qc-func-tc-design/references/design-technical/design-technical-<variant>.md` end-to-end. Hold all loaded rubrics in working memory.
5. Record the resolved variant list as a working note (carries through to Step 3.5 / 4 file naming and prelude).

#### 2.2 — Apply the 6-Phase Drafting Rubric Per Variant

For EACH platform variant loaded in 2.1, apply ALL 6 phases described in its rubric file. The 6 phases are *content categories* (systematic coverage buckets), NOT separate checkpoint boundaries — they all contribute to the same in-memory TC list **per variant** that gets persisted at the end of Phase 2.

> **Multi-platform rule:** If multiple variants apply (e.g., a UC ships on BOTH web-responsive and mobile-native), draft a SEPARATE TC list per variant — to be persisted in a SEPARATE scratch file (Step 3.5) and written to a SEPARATE deliverable `.md` (Step 4). Do NOT merge variants into one file. Each variant gets its own RTM (Step 3) and its own prelude.

**Test Case Writing rules (MANDATORY):** Apply all the rules in `qc-func-tc-design/rules/testcase-instruction-rules.md` (Layout, Sorting, Encoding, etc.) regardless of platform.

- **Test cases example**: read the language-matched reference — `qc-func-tc-design/references/Testcase-refer-vi.md` for Vietnamese test cases, `qc-func-tc-design/references/Testcase-refer-en.md` for English test cases — and align new TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style).

### Step 3: Build the Requirement Traceability Matrix

- Build the `Requirement Traceability Matrix` mapping every Acceptance Criterion of the audited UC to the drafted Test Case IDs.
- Verify 100% coverage. If any AC has no linked TCs, fix the drafting in Step 2 before proceeding.
- The RTM will be embedded in the md prelude (Step 4), not in a separate file.
- **Multi-platform:** Build ONE RTM PER variant. Each variant's RTM lives in its own `.md` file's prelude. Each RTM must independently cover 100% of the audited ACs that are in scope for that variant.

### Step 3.5: Persist Designed TCs to Scratch (MANDATORY — atomic single Write)

This step is the **safety net for Phase 3 auto-recovery**. It locks down the in-memory design before the final md write begins, so that if the final md write is interrupted (multi-part flow, network blip, context flush, etc.), Phase 3's verification gate can detect the mismatch and auto-recover from this scratch — WITHOUT having to re-run the 6-phase drafting.

1. **Compose the full scratch content** in working memory, using the SAME content format as the final deliverable md described in Step 4:
   - The complete required prelude (`# Test Cases — [UC-ID] …`, totals, source filenames, RTM table, etc.).
   - All screen sections (`## <Roman>. …`) with their GUI (`### <Roman>.1. …`) and FUNC (`### <Roman>.2. …`) subsections and test case tables.
   - The same heading-level rules as Step 4 (only `#` / `####` in the prelude, `##` for screens, `###` for GUI/FUNC).
2. **Write to scratch path(s)** — ALWAYS per-variant (no special case for single-variant projects): for EACH platform variant V resolved in Step 2.1, write that variant's full scratch content to `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/02_designed_tcs_<V>.md` in **ONE atomic Write call** containing the ENTIRE content for that variant.
   - For a single-variant project, this means writing ONE file with the project's only variant in its name (e.g., `02_designed_tcs_web-responsive.md`). The "bare" name `02_designed_tcs.md` (without variant suffix) is NEVER used — Phase 3 always probes by variant.
   - For a multi-variant project, write N atomic Write calls, one per variant.
   - Do NOT use Edit / multiple appends to build a scratch incrementally — if a scratch's own Write is interrupted, Phase 3 cannot recover that variant. If a single variant's volume exceeds a Write's practical limit, that is the signal to fail loudly and ask the user — multi-part scratch per variant is NOT supported.
3. Do NOT delete or modify any scratch file later in this skill run — they are durable sources of truth for Phase 2 and are only removed in `SKILL.md` → Step D cleanup at end-of-run.

After this step completes, the design work of Phase 2 is **durably persisted for every variant**. Step 4 below is a re-materialization of the same content at the deliverable path; if Step 4 is interrupted for any variant, that variant's scratch is still on disk for Phase 3 auto-recovery.

### Step 4: Write the .md File(s) (MANDATORY)

For EACH platform variant V resolved in Step 2.1, re-materialize that variant's scratch content (`02_designed_tcs_<V>.md` from Step 3.5) to the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`. Each variant produces its own deliverable file(s); within a variant, use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume. Each file (single or per-part) is an atomic single Write.

**Deliverable file naming:** Insert a `_<variant>` segment between the `testcases` type and the version, per `rules/naming-convention.md`. Example for UC-101 with both web-responsive and mobile-native:
- `UC-101_user-login_testcases_web-responsive_v1.md`
- `UC-101_user-login_testcases_mobile-native_v1.md`

For a single-variant project the same naming applies (just one variant in the name), e.g., `UC-101_user-login_testcases_web-responsive_v1.md`. The "no-variant" filename pattern is NOT used — every deliverable carries its variant in the name so Phase 3's per-variant flow can pair scratch ↔ final md unambiguously.

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

### Checkpoint write — End of Phase 2

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase). At this point, the following artifacts already exist on disk: ONE scratch file per variant (`02_designed_tcs_<V>.md` from Step 3.5) and that variant's final deliverable `.md` file(s) (from Step 4). The remaining work is to publish ONE consolidated `## Phase 2 Summary` block to progress.md covering ALL variants (so Phase 3 can iterate per variant), then update worklog + dashboard.

1. **Compute the per-variant Phase 2 summary** by counting TCs in EACH variant's final md (which equals that variant's scratch — both should match exactly at this moment). For each variant V:
   - Total TCs + GUI / FUNC split (3 discrete integers).
   - Per-screen breakdown: for each `## <Roman>.` screen in V's final md, count TC rows in its `### <Roman>.1.` (GUI) and `### <Roman>.2.` (FUNC) tables.
   - The output language detected in Phase 1.
   - The scratch path: absolute path to `02_designed_tcs_<V>.md`.
   - The final md path(s) for V written in Step 4 (single file or multi-part list, all absolute paths).
2. **Append a SINGLE `## Phase 2 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. The block contains:
   - A top-level `**Variants in scope:**` line listing all variants comma-separated.
   - ONE `### Variant: <V>` sub-block per variant, in the same order. Each sub-block has the per-variant fields computed above (totals, language, scratch path, final md paths, screen breakdown table).
   - This is an atomic single Write that overwrites `progress.md` while preserving all existing fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Do NOT touch `last_phase_done` here — it stays at its current value (set when Phase 2 started). Update `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 2 done"`. Append ALL variants' final `.md` path(s) to `output` (excluding `process-logging/`).
4. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Soạn TC & ghi MD done` (VI) / `TC Drafting & MD Write done` (EN). Skip if column missing.

> **Note:** `last_phase_done: 2` is NOT written here — it gets written at the START of Phase 3, only AFTER Phase 3's Step 0 verification gate passes for ALL variants. This is what guarantees a partial / mismatched md for ANY variant cannot be silently accepted as "Phase 2 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 3

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 2 finishes successfully.
