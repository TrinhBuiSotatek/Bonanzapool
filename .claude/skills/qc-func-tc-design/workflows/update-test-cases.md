## Update Test Cases (Design Update Workflow)

> **Scope:** This workflow produces ONLY the updated test case `.md` file. It is fully independent from the `.xlsx` artifact — no script invocation, no xlsx step. Conversion to `.xlsx` (Phase 3) and chat-side reporting (Step C) are orchestrated by `SKILL.md`. Do NOT write a separate summary file in this workflow.
>
> **Trigger conditions:** This workflow is triggered when EITHER of the following occurs:
> 1. **Requirement change**: The audited UC Readiness Report has been updated (new version). Test cases need to be aligned with the changed requirements.
> 2. **User feedback**: The user provides explicit feedback about gaps, errors, or missing coverage in the existing test cases.
>
> **Phase mapping (per `SKILL.md` → "Phase Map"):**
> - **Phase 1 — Analysis & Design Brief** = Steps 1 + 2 below.
> - **Phase 2 — TC Drafting & MD Write** = Steps 3 + 3.5 + 4 below. (Step 3.5 persists the merged updated TC list to scratch BEFORE the deliverable md write — required by Phase 3 auto-recovery.)
> - Phase 3 (MD → XLSX) is handled by `convert-md-to-xlsx.md`, not this file.
>
> **Checkpoint references:** all phase-boundary write/update steps follow `SKILL.md` → "Checkpoint & Resume Protocol" §5. Do NOT duplicate those rules here.

---

## Phase 1 — Analysis & Design Brief

### Status update — Start of Phase 1

Per `SKILL.md` → "Checkpoint & Resume Protocol" §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).
2. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Running — Phân tích & Lập đề cương thiết kế` (VI) / `Running — Analysis & Design Brief` (EN). Skip if column missing (graceful degradation). If the UC has no row yet in the dashboard → invoke `qc-dashboard-sync` BEFORE updating.

### Step 1: Input Analysis (MANDATORY)

#### 1.1 — Load Existing Artifacts

- Identify the highest version of the existing `func-test-cases` file.
- Identify the current `uc-review-report` used to originally generate those test cases.
- Identify the latest version of the `uc-review-report` available now.
- Load all three above. Do NOT generate any output files in this step.

#### 1.2 — Determine the Source of Change

Parse the user's invocation to determine **what triggered this update**:

| Trigger Type | Description |
|---|---|
| **A — Requirement Change** | User says the audited file has a new version. OR the latest audited file version is newer than the one used to generate existing test cases. |
| **B — User Feedback** | User provides explicit feedback about test cases (e.g., "missing cases", "wrong expected result", "need to add X"). |
| **C — Both** | Both requirement change and user feedback are provided simultaneously. |

If the trigger type is ambiguous, ask the user:
> _"Bạn muốn cập nhật test cases vì: (A) Requirement đã thay đổi, (B) Có feedback về test cases hiện tại, hay (C) Cả hai?"_

---

### Step 2: Change Impact Analysis (MANDATORY)

This step replaces the open-ended drafting of generate. The agent MUST focus analysis on **what changed** and **how the change impacts existing test cases**.

#### 2A — If Trigger is Type A (Requirement Change)

Perform a **diff analysis** between the previous and latest audited file:

1. **Identify changed ACs**: List all Acceptance Criteria (ACs) that were added, removed, or modified.
2. **Map ACs to existing TCs**: Using the Requirement Traceability Matrix from the previous version's md prelude, find which test cases are linked to each changed AC.
3. **Classify the impact** for each changed AC:

| Change Type | Impact on Test Cases |
|---|---|
| AC added (new requirement) | → Need to **design new TCs** covering this AC. Apply the same 6-phase logic from `generate-test-cases.md`. |
| AC removed | → **Delete TCs** that exclusively cover this AC. If a TC covers multiple ACs and only one is removed, keep the TC and update its coverage. |
| AC modified (wording, logic, constraint changed) | → **Review and update** linked TCs. Recheck: Expected Result, Pre-conditions, Test Steps for accuracy against the new requirement. |
| AC unchanged | → Existing TCs remain valid. Mark as "No change". |

4. Build an **Impact Table**:

```
| AC ID | Change Type | Linked TC IDs | Action Required |
|-------|-------------|---------------|-----------------|
| AC-03 | Modified    | TC_012, TC_013 | Update Expected Result in TC_012, TC_013 |
| AC-07 | Added       | —              | Design new TCs  |
| AC-10 | Removed     | TC_025         | Delete TC_025   |
```

#### 2B — If Trigger is Type B (User Feedback)

Perform a **feedback classification analysis**:

For each feedback item provided by the user, classify it into one of three categories:

| Feedback Category | Definition | Agent Action |
|---|---|---|
| **Cat 1 — Agent Gap** | The requirement clearly implies this case, but the agent missed it when generating. Example: A validation rule was in the audited file but no TC was created for it. | → Design the missing TC(s). **Also flag this as a skill improvement suggestion** (see Step 2B.3). |
| **Cat 2 — Requirement Gap** | The feedback implies a behavior that is NOT documented in the current audited file. Example: User says "the system should show a warning when X" but X is not in the audited AC list. | → Do NOT design the TC yet. First: **ask the user to confirm and update the audited file** with this new requirement. After confirmation, re-trigger update with the new audited file. |
| **Cat 3 — Factual Correction** | The existing TC has an incorrect expected result, wrong step, or wrong pre-condition — not due to missing requirement, but due to a drafting error. | → Directly fix the existing TC. |

**Step 2B.1 — Analysis output per feedback item:**

For each feedback item, state:
```
Feedback: "[user's feedback text]"
Category: Cat 1 / Cat 2 / Cat 3
Reason: [Explain why you classified it this way, citing the AC ID or noting its absence]
Action: [What the agent will do]
```

**Step 2B.2 — For Cat 2 items:** Ask the user:
> _"Feedback '[summary]' mô tả một hành vi chưa được ghi nhận trong tài liệu requirement (audited file [version]). Để đảm bảo traceability, bạn có thể xác nhận và bổ sung nội dung này vào file audited không? Sau khi cập nhật, tôi sẽ thiết kế test case tương ứng."_

**Step 2B.3 — For Cat 1 items:** After designing the missing TCs, prepare a **Skill Improvement Flag** to surface in the chat report (handed off to `SKILL.md` → Step C). Format:
```
⚠️ SKILL IMPROVEMENT SUGGESTION:
Missing coverage for [type of validation/logic, e.g., "boundary value for max-length field"].
Recommended addition to generate-test-cases.md → Phase 3 (Core Functional Testing):
"[Suggested new rule or checklist item]"
```
Do NOT write this flag into a file — it will be reported on chat.

#### 2C — If Trigger is Type C (Both)

Apply both 2A and 2B analyses sequentially. Consolidate the Impact Table and Feedback Analysis into a unified **Change Analysis Report** held in working memory before proceeding to Phase 2.

### Checkpoint write — End of Phase 1

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase):

1. **Write checkpoint file** `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/01_analysis.md` containing:
   - Trigger Type (A / B / C).
   - **Impact Table** (if Type A or C) — full table from Step 2A.
   - **Feedback Classification** (if Type B or C) — per-feedback rows with Category + Reason + Action.
   - **Cat 1 Skill Improvement Flags** (if any) — verbatim text to surface in Step C.
   - **Cat 2 open requirement gaps** (if any) — items waiting on user confirmation / audited-file update.
   - Previous TC version + path; current `uc-review-report` version used.
   - Detected output language (VI / EN).
   - Target platform variant(s) resolved from `project-context-master.md` §1 (for the variant being updated — see Step 3 multi-platform rule).
2. **Worklog**: rewrite last entry → `status = "Phase 1 done"`.
3. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Phân tích & Lập đề cương thiết kế done` (VI) / `Analysis & Design Brief done` (EN). Skip if column missing.

> **Note:** `last_phase_done: 1` is NOT written here — it gets written at the start of Phase 2 (see "Status update — Start of Phase 2" below). Per §5.1, advancing `last_phase_done` happens only at phase transition.

---

## Phase 2 — TC Drafting & MD Write

### Status update — Start of Phase 2

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.1 (start-of-phase / transition write). This is the moment we advance `last_phase_done` to confirm Phase 1 is done.

1. **Update `progress.md`** → `last_phase_done: 1`, `next_phase: 2`, `workflow: update-test-cases`, `updated_at: <now>`. (Preserve any other existing fields / notes.)
2. **Worklog**: rewrite last entry → `status = "Running (Phase 2)"`.
3. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Running — Soạn TC & ghi MD` (VI) / `Running — TC Drafting & MD Write` (EN). Skip if column missing.

> **Resume note:** Probe `process-logging/<UC-ID>/02_designed_tcs_<V>.md` where `<V>` is the variant being updated (recorded in `01_analysis.md`). If the scratch already exists (a prior run interrupted between Phase 2's scratch persist and md write), SKIP Step 3 below — the merged updated TC list is already done. Read the scratch and jump to Step 4 (Final MD Write). Per `SKILL.md` §4 Resume load table.

### Step 3: Redesign Affected Test Cases (MANDATORY)

Using the same platform-aware 6-phase design logic as `generate-test-cases.md` Step 2 — load `references/design-technical/design-technical-<variant>.md` for each platform variant declared in `project-context-master.md` §1 → "Product Platform Type" — apply it **only to the impacted scope** identified in Phase 1. **If `qc-site-map.md` exists**, also cross-check the impacted screens against §8 Screen ↔ Feature mapping (catch screens silently affected), §9 Data/API touchpoints (catch upstream/downstream integration impact), §10 Regression anchors (raise priority of TCs on anchored flows). If missing → skip and warn once.

- **New TCs**: Design from scratch using the 6-phase logic of the matching variant rubric for the new or changed ACs.
- **Updated TCs**: Rewrite only the affected fields (Steps, Expected Result, Pre-conditions) — keep the TC ID unchanged. Add a note: `[Updated vN — Reason: AC-XX modified]`.
- **Deleted TCs**: Mark as DELETED in the working draft — do NOT renumber remaining TCs to avoid traceability breaks.

**Multi-platform update rule:** When the project has multiple platform variants, this update workflow operates on ONE variant `.md` at a time — the variant whose `func-test-cases` was identified in Step 1.1 as the input. If the requirement change cuts across variants, re-trigger update separately for each affected variant `.md`. Do NOT silently update sibling variant files.

**Test Case Writing rules (MANDATORY for new and updated TCs):** Apply all the rules in `qc-func-tc-design/rules/testcase-instruction-rules.md`.

- **Test cases example**: read the language-matched reference — `qc-func-tc-design/references/Testcase-refer-vi.md` for Vietnamese test cases, `qc-func-tc-design/references/Testcase-refer-en.md` for English test cases — and align new/updated TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style).
- For consistency, updated TCs must match the writing style of unchanged TCs in v[N] (do NOT mix styles).

**Sorting rules:** See `qc-func-tc-design/rules/testcase-instruction-rules.md`
- Layout
- Sorting
- Encoding

**TC ID continuity rule:**
- New TCs must continue from the highest existing TC ID (e.g., if TC_025 was the last, new TCs start at TC_026).
- NEVER reuse a deleted TC's ID.

---

### Step 3.5: Persist Updated TC List to Scratch (MANDATORY — atomic single Write)

This step is the **safety net for Phase 3 auto-recovery** (same rationale as `generate-test-cases.md` Step 3.5). It locks down the merged updated TC list (unchanged + updated + new TCs, minus deleted) BEFORE the final v[N+1] md write begins, so that if the final md write is interrupted, Phase 3's verification gate can detect the mismatch and auto-recover from this scratch — WITHOUT having to re-run the impact analysis + redesign work of Steps 1–3.

1. **Compose the full scratch content** in working memory, using the SAME content format as the final deliverable md described in Step 4 below:
   - The complete required prelude for the new version v[N+1] (`# Test Cases — [UC-ID] [feature-name] (v[N+1])`, totals, delta line `+A new, ~U updated, -D deleted`, source UC previous + current versions, update trigger type, output language, updated RTM).
   - All screen sections (`## <Roman>. …`) with their GUI (`### <Roman>.1. …`) and FUNC (`### <Roman>.2. …`) subsections.
   - ALL test cases in their final form: unchanged TCs kept verbatim, updated TCs with `[UPDATED — Reason: AC-XX modified]` annotation, new TCs with `[NEW — AC-XX]` annotation. Deleted TCs are EXCLUDED from the body (their removal is reflected in the RTM `Removed` status only).
   - The same heading-level rules as Step 4 (only `#` / `####` in the prelude, `##` for screens, `###` for GUI/FUNC).
2. **Write to scratch path** `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/02_designed_tcs_<V>.md` where `<V>` is the platform variant being updated (recorded in `01_analysis.md` at end of Phase 1). Use **ONE atomic Write call** containing the ENTIRE content. Do NOT use Edit / multiple appends to build the scratch incrementally — if the scratch itself is interrupted mid-write, Phase 3 has nothing to recover from. If volume exceeds a single Write's practical limit, fail loudly and ask the user — multi-part scratch is NOT supported.
3. Do NOT delete or modify the scratch later in this skill run — it is the durable source of truth for Phase 2 and is only removed in `SKILL.md` → Step D cleanup at end-of-run.

After this step completes, the merged update work of Phase 2 is **durably persisted** for the variant being updated. Step 4 below is a re-materialization of the same content at the deliverable path (new version v[N+1]); if Step 4 is interrupted, the scratch is still on disk for recovery.

> **Multi-platform note:** Per Step 3's multi-platform rule, this workflow updates ONE variant per run. The scratch holds the full v[N+1] content for THAT variant only. Sibling variant scratches / deliverables are not touched. (Phase 3 still iterates per variant — for an update run, "all variants in scope" = the single variant being updated.)

---

### Step 4: Write the Updated .md File (MANDATORY)

The content source is `02_designed_tcs.md` (just written in Step 3.5) — Step 4 re-materializes the same content at the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`, as a NEW version. Naming follows `rules/naming-convention.md` (immutable versions — increment v[N] → v[N+1], never overwrite). Use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume; each file (single or per-part) is an atomic single Write.

The md must contain ALL test cases — unchanged, updated, and newly added — in their final form. Deleted TCs are excluded from the md body.

**At the TOP of the md (or top of `part1` if multi-part), include the following required prelude:**

```markdown
# Test Cases — [UC-ID] [feature-name] — <variant> (v[N+1])

**Total test cases:** Y (Delta vs v[N]: +A new, ~U updated, -D deleted)
**GUI / FUNC counts:** y_gui / y_func
**Platform variant:** [web-responsive / web-static / mobile-native / mobile-hybrid / desktop-native]
**Source UC (previous version):** [audited_filename_vX]
**Source UC (current version):** [audited_filename_vY]
**Update trigger:** [Type A — Requirement Change / Type B — User Feedback / Type C — Both]
**Output language:** [VI / EN]

#### Updated Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases       | Status          |
|---    |---                  |---                      |---              |
| AC-01 | …                   | TC_001, TC_002          | Covered         |
| AC-07 | …                   | TC_026                  | Covered [NEW]   |
| AC-10 | …                   | —                       | Removed         |

---
```

**Heading-level rules (MANDATORY — they govern what does and does not appear in the xlsx):**
- The prelude MUST use only `#` (h1) and `####` (h4) heading levels — these are skipped by the converter, so the prelude does NOT leak into the xlsx.
- Use `##` (h2) ONLY for screen headers (e.g., `## I. Màn hình: …` / `## I. Screen: …`).
- Use `###` (h3) ONLY for GUI / FUNC section headers (e.g., `### I.1. …` / `### I.2. …`).

**Inline annotations on changed TCs in the body:**
- `[NEW — AC-XX]` next to the title of newly added TCs.
- `[UPDATED — Reason: AC-XX modified]` next to the title of modified TCs.
- Do NOT include deleted TCs in the md body — their removal is reflected in the Updated RTM (`Removed` status).

**Layout / Sorting / Encoding requirements (still apply when redrafting the v[N+1] md — see `qc-func-tc-design/rules/testcase-instruction-rules.md` → "Sheet Layout & Section Headers"):**
- Preserve the existing screen / GUI / FUNC section headers from v[N].
- Place new TCs **inside the correct section block** for their screen and type — GUI new cases below the matching `<RomanNumeral>.1.` header, FUNC new cases below `<RomanNumeral>.2.`. Do NOT append at the end of the md.
- When the latest audited file adds a new screen, insert a new screen header block (next Roman numeral with its `.1` / `.2` sub-headers) at the appropriate position.
- Sorting within a section: GUI before Functional. Within GUI: Screen Initialization → Item Interactions → Common UI cases → UI elements verify. Within FUNC: Happy path → Validation → Error/Exception.
- Encoding (Rules 0a–0d): UTF-8 md, preserve dấu, no `unicodedata.normalize` / `unidecode` / Latin-1.

**Do NOT write a separate summary file.** The md (with its prelude) is the only design artifact this workflow produces. Detailed change tables (deleted / updated / new TCs), Cat 1 skill improvement flags, Cat 2 open requirement gaps, and out-of-scope items will be reported on chat by the orchestrator (`SKILL.md` → Step C).

### Checkpoint write — End of Phase 2

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase). At this point, two artifacts already exist on disk: the scratch `02_designed_tcs_<V>.md` (Step 3.5) and the final updated deliverable `.md` v[N+1] for variant `<V>` (Step 4). The remaining work is to publish the `## Phase 2 Summary` block to progress.md (so Phase 3 can verify the final md), then update worklog + dashboard.

1. **Compute the Phase 2 summary** by counting TCs in the final v[N+1] md (which equals the scratch — both should match exactly at this moment):
   - Total TCs (single integer) + GUI total + FUNC total (each on its own line in the summary, per `SKILL.md` §1 schema).
   - **Delta vs v[N]**: `+<A> new, ~<U> updated, -<D> deleted` (counted from the inline annotations: `[NEW]` for new, `[UPDATED]` for modified; deleted count comes from RTM `Removed` rows). ASCII "Delta", not the Greek glyph.
   - Per-screen breakdown: for each `## <Roman>.` screen, count TC rows in its `### <Roman>.1.` (GUI) and `### <Roman>.2.` (FUNC) tables.
   - The output language detected in Phase 1.
   - The platform variant being updated (`<V>`).
   - The scratch path: absolute path to `02_designed_tcs_<V>.md`.
   - The final v[N+1] md path(s) written in Step 4 (single file or multi-part list, absolute paths).
2. **Append `## Phase 2 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. The block contains:
   - A top-level `**Variants in scope:** <V>` line (always exactly ONE variant for the update workflow).
   - Exactly ONE `### Variant: <V>` sub-block, populated from the fields computed above (totals, language, scratch path, final md paths, screen breakdown table, plus the `**Delta vs v[N]:**` line below the table).
   - Atomic single Write that overwrites `progress.md` while preserving all existing fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Do NOT touch `last_phase_done` here — it stays at its current value (set when Phase 2 started). Update `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 2 done"`. Append the final v[N+1] `.md` path(s) to `output` (excluding `process-logging/`).
4. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Soạn TC & ghi MD done` (VI) / `TC Drafting & MD Write done` (EN). Skip if column missing.

> **Note:** `last_phase_done: 2` is NOT written here — it gets written at the START of Phase 3, only AFTER Phase 3's Step 0 verification gate passes. This is what guarantees a partial / mismatched updated md cannot be silently accepted as "Phase 2 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 3

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 2 finishes successfully.
