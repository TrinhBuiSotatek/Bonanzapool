## Update Test Cases (Design Update Workflow)

> **Scope:** This workflow produces ONLY the updated test case `.md` file. It is fully independent from the `.xlsx` artifact — no script invocation, no xlsx step.
>
> **Purpose:** Update-test-cases after one or more changes occur, without rerunning the full generate-test-cases flow unless necessary.
> 1. **Requirement change:** The audited UC Readiness Report has been updated (new version). Test cases need to be aligned with the changed requirements.
> 2. **User feedback:** The user provides explicit feedback about gaps, errors, or missing coverage in the existing test cases.

> **Logic-only note:** this skill has NO platform variants. The legacy `ADD_VARIANT` machinery (a UI web/mobile/desktop concept) does NOT apply here — there is exactly one logic track named `logic`. Where the workflow text below still says "variant", read it as the single `logic` track. Do NOT prompt the user to pick a platform variant.
>
> **Checkpoint references:** all phase-boundary write/update steps follow `workflows/checkpoint-protocol.md` §4. Do NOT duplicate those rules here.

---

## Phase 1 — Impact Analysis & Re-Design

### Status update — Start of Phase 1

Per `workflows/checkpoint-protocol.md` §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).

### Step 1: Input Analysis (MANDATORY)

#### 1.1 — Type detect

Parse the user's invocation to determine **what triggered this update**:

| Trigger Type | When it applies | Main behavior |
|---|---|---|
| `REQUIREMENT_DELTA` | The audited UC / scenarios changed from the baseline source. | Compare old vs new audited sources, assess impact, then update affected existing TC files. |
| `USER_FEEDBACK_ONLY` | The user asks to adjust existing TCs but audited sources are unchanged or not re-supplied. | Interpret feedback, assess impact on current TC files, then update only approved cases. |
| `MIXED` | Both triggers above apply in the same run (audited UC changed AND the user also has feedback). | Produce one consolidated report covering both. Apply only approved actions. |

> `ADD_VARIANT` does NOT apply to this logic-only skill — there are no platform variants to add. If the user asks for "another variant", clarify whether they mean a requirement change or feedback; there is only the single `logic` track.

If the trigger type is ambiguous, ask the user:
> _"What triggered this test-case update: (A) the spec changed and a new audited version exists, (B) I have feedback on the current test cases, or (C) Mixed — both of the above."_
>
> If the user chooses B, ask the user about the feedback content and the test cases that need updating.
> If the user chooses C, ask the user about all of the changes.

#### 1.2 — Read all required input files

Read the following files before performing any analysis:

- Current / baseline `func-test-cases-draft` `.md` file(s) to be updated.
- Old audited UC file that was used to design the current TC version.
- New audited UC file that should drive the update.
- `project-context-master.md`.
- `.claude/skills/qc-func-tc-design-exbot/references/design-technical/common-logic-technical.md` and `.claude/skills/qc-func-tc-design-exbot/references/design-technical/logic-technical.md`.
- User feedback, if provided in the current prompt or earlier messages for this update run.
- User-requested target platform variant(s), if the trigger is adding test cases for another variant.

Read optional files if present:

- Old `func-test-scenarios` used by the current TC version.
- New / updated `func-test-scenarios`.

#### 1.3 Confirm Logic-only Scope (MANDATORY)

This skill is logic-only and has NO platform variants. There is exactly one track named `logic`.

1. Confirm the feature under test is backend / API / bot (no UI). If it has a UI, STOP and tell the user to use `qc-func-tc-design` (the UI variant).
2. Confirm the current baseline TC `.md` file exists (single track). If it is missing for a `REQUIREMENT_DELTA` / `USER_FEEDBACK_ONLY` run, STOP and ask the user to provide it.
3. Load `qc-func-tc-design-exbot/references/design-technical/common-logic-technical.md` and `qc-func-tc-design-exbot/references/design-technical/logic-technical.md` end-to-end. Hold both rubrics in working memory.
4. Record the scope reason (`UPDATE_EXISTING`) as a working note. (`ADD_VARIANT` does not apply to this logic-only skill.)

#### 1.4 Identify update baseline

For EACH variant V, identify:

- Baseline TC file path(s).
- Baseline TC version from filename and/or prelude.
- Baseline source UC filename and version from prelude.
- Baseline source scenarios filename and version, if any.
- Total TC count and FUNC / INTG / NFR split.
- Existing TC ID list.
- Existing operation-group sections (`## <Roman>. ...`).
- Existing typed section structure (`### <Roman>.1.` FUNC, `### <Roman>.2.` INTG, `### <Roman>.3.` NFR).
- Existing RTM table from the prelude.

> **Source-of-truth rule:** the current `.md` test case file is the baseline source of truth. Existing `.xlsx` files are NOT used as the editing source. For `ADD_VARIANT`, there is no same-variant TC baseline; use the latest approved audited UC as the source of truth and use existing other-variant TC files only as writing-style / coverage references, not as authoritative behavior.

#### 1.5 Resolve update trigger type (MANDATORY)

Resolve one of the trigger types defined at the top of this workflow:

| Condition | Trigger Type |
|---|---|
| Old audited UC differs meaningfully from new audited UC. | `REQUIREMENT_DELTA` |
| User feedback changes existing TC content, but audited sources are unchanged. | `USER_FEEDBACK_ONLY` |
| User requests test cases for a variant without a same-variant baseline TC file. | `ADD_VARIANT` |
| Any combination of the above. | `MIXED` |

Record for each variant:

| Variant | Scope Reason | Baseline TC File | Apply Behavior |
|---|---|---|---|
| `<variant>` | `UPDATE_EXISTING` / `ADD_VARIANT` | path or `N/A` | update existing / draft full new set |

---

### Step 2: Impact Analysis
#### 2.1 Requirement delta analysis

Compare old audited UC vs new audited UC by meaning, not only by text diff.

Classify every meaningful change as one of:

| Change Type | Meaning |
|---|---|
| `ADDED` | New requirement, AC, field, screen, action, validation, state, or flow. |
| `MODIFIED` | Existing requirement changed behavior, validation, data rule, UI behavior, integration, or expected result. |
| `REMOVED` | Existing requirement no longer applies. |
| `CLARIFIED` | Requirement was clarified but the intended behavior is materially unchanged. |
| `RENAMED` | Label, field, screen, action, or status name changed without behavior change. |
| `MOVED` | Function moved to another screen / section / flow location. |
| `NFR_CHANGED` | Security, performance, compatibility, accessibility, logging, or platform rule changed. |
| `AMBIGUOUS` | Difference exists but the required TC update is not clear enough to apply safely. |

For each change, capture:

| Change ID | Type | Old Source | New Source | Old Meaning | New Meaning | Expected TC Impact |
|---|---|---|---|---|---|---|

#### 2.2 User feedback analysis

Treat user feedback as a separate input source. Do NOT silently merge it into the audited delta.

Classify feedback as one of:

| Feedback Type | Meaning | Typical Action |
|---|---|---|
| `ADD_MISSING_CASE` | User says coverage is missing. | Propose ADD. |
| `CORRECT_EXPECTED_RESULT` | Existing expected result is wrong. | Propose UPDATE. |
| `REMOVE_REDUNDANT_CASE` | TC is duplicated or unnecessary. | Propose RETIRE or MERGE. |
| `CHANGE_WORDING` | Text should be clearer, no logic change. | Propose wording-only UPDATE. |
| `CHANGE_PRIORITY` | Priority needs adjustment. | Propose priority UPDATE. |
| `CHANGE_SCOPE` | In-scope / out-of-scope changed. | Re-evaluate RTM and affected cases. |
| `CLARIFICATION` | User clarifies ambiguous behavior. | Use to resolve `AMBIGUOUS` items. |

If user feedback conflicts with the new audited UC, flag it as `CONFLICT` in the report. Do NOT apply conflicting changes without explicit user approval.

#### 2.3 Impact analysis on existing test cases

For EACH variant V, evaluate each existing TC against the requirement delta and user feedback.

Use these impact statuses:

| Impact Status | Meaning | Apply Rule |
|---|---|---|
| `KEEP` | TC remains valid and unchanged. | Preserve as-is. |
| `UPDATE` | TC remains valid but needs edits. | Preserve TC ID; update only impacted fields. |
| `ADD` | New test intent is required. | Create new TC ID. |
| `RETIRE` | TC no longer applies. | Remove from active final TC tables; record in report/change log. |
| `SPLIT` | Existing TC covers multiple intents that now need separate cases. | Keep existing TC ID for the main intent; create new TC ID(s). |
| `MERGE` | Multiple TCs should become one. | Keep the representative TC ID; retire/merge others in report. |
| `REVIEW` | Not safe to apply without decision. | Include in Open Questions; do not apply until resolved. |
| `ADD_VARIANT` | A new platform variant has no baseline TC file. | Draft full TC set for that variant using common + variant technical. |

#### 2.4 TC ID stability policy (MANDATORY)

- Preserve existing TC IDs whenever the test intent remains the same.
- Do NOT renumber all TCs because of added / removed cases.
- New test intent → create a new TC ID after the current maximum ID for that variant.
- `UPDATE` keeps the same TC ID.
- `SPLIT` keeps the original TC ID for the closest original intent and creates new IDs for the split-out intents.
- `MERGE` keeps one representative TC ID and records merged/retired IDs in the report.
- `RETIRE` does not reuse the retired TC ID for a new intent.
- If the user explicitly asks to regenerate IDs, flag this as high-risk before applying.

---

### Step 3: Build Update Impact Report for User Approval (MANDATORY)

Create ONE consolidated approval report covering ALL variants in scope. The report may contain per-variant sections.

#### 3.1 Report path

Write the pending approval report to:

```text
.claude/skills/qc-func-tc-design-exbot/process-logging/<UC-ID>/pending_update_report.md
```

Rules:

- This file is temporary.
- It is the report shown to the user for approval.
- It may be rewritten while the user requests report revisions.
- It MUST be deleted after the approved update has been applied and verified.
- Do NOT modify deliverable TC `.md` files while this report is pending.

#### 3.2 Report content format

Use this report structure:

```markdown
# Test Case Update Impact Report — [UC-ID]

**Status:** Waiting for user approval
**Report revision:** R1
**Trigger type:** [REQUIREMENT_DELTA / USER_FEEDBACK_ONLY / MIXED]
**Track in scope:** logic
**Audited source (old):** [filename + version]
**Audited source (new):** [filename + version]
**Current TC source:** [filename(s) + version]
**User feedback source:** [prompt / file / none]

#### Summary

| Item | Count |
|---|---:|
| Requirements added | N |
| Requirements modified | N |
| Requirements removed | N |
| Requirements clarified | N |
| Requirements still ambiguous / need confirmation | N |
| Existing TCs kept | N |
| Existing TCs to update | N |
| New TCs proposed | N |
| TCs proposed to retire | N |
| TCs proposed to split | N |
| TCs proposed to merge | N |
| Items needing user review / confirmation | N |

#### Requirement Delta

| Change ID | Change type | Old meaning | New meaning | Source | Expected TC impact |
|---|---|---|---|---|---|

#### User Feedback Interpretation

| Feedback ID | Feedback | Interpretation | TC impact | Handling status |
|---|---|---|---|---|

#### Test Case Impact Matrix

| TC ID | Current title | Impact Status | Reason | Proposed action |
|---|---|---|---|---|

#### Proposed New Test Cases

| Proposed TC ID | Title | Source of change | TC type | Priority | Note |
|---|---|---|---|---|---|

#### Test Cases Proposed for Retire / Merge

| TC ID | Title | Reason | Replacement / Merge target |
|---|---|---|---|

#### Open Questions / Items to Confirm

| Item | Source | Why confirmation is needed | Decision required from user |
|---|---|---|---|

#### Approval Instructions

You can respond in one of the following ways:

- `Approve update report` to apply exactly as described in this report.
- Send additional feedback if the report needs revision before it is applied.
- `Cancel` to stop the workflow; the plan stays in the process-logging folder so you can resume later.
```

#### 3.3 Report quality gate

Before sending the report to the user:

- Every meaningful audited delta must appear in `Requirement Delta`.
- Every user feedback item must appear in `User Feedback Interpretation`.
- Every existing TC must appear in one impact status unless the report explicitly scopes it out.
- No `CONFLICT` item can be silently hidden.
- No `REVIEW` item can be applied later unless it is resolved by user approval or user feedback.

---

### Checkpoint write — Mid-Phase Approval Pending

This is the first checkpoint for the update phase.

Per `workflows/checkpoint-protocol.md` §4:

1. Write / rewrite `pending_update_report.md` in ONE atomic Write containing the entire report content.
2. Send the report to the user in chat and explicitly wait for approval or revision feedback.
3. Update `progress.md` with an approval-pending block while preserving existing fields:
   - `workflow: update-test-cases`
   - `next_phase: 1`
   - `updated_at: <now>`
   - Add / replace a `## Phase 1 Approval Pending` block containing:
     - `**Pending report path:** <absolute path to pending_update_report.md>`
     - `**Report revision:** R<n>`
     - `**Trigger type:** ...`
     - `**Variants in scope:** ...`
     - `**Current status:** Waiting for user approval`
     - Summary counts by impact status.
4. **Worklog**: rewrite last entry → `status = "Waiting for user approval (Phase 1 update report)"`.
5. Do NOT write final updated TC `.md` file(s).
6. Do NOT write full updated TC scratch yet.
7. Do NOT trigger `convert-md-to-xlsx.md`.
8. Do NOT advance `last_phase_done`.

At this point the update phase is intentionally paused.

---

### Step 4: User Approval & Report Revision Loop (MANDATORY)

The workflow resumes only when the user responds.

#### 4.1 If the user provides feedback before approval

1. Read the current `pending_update_report.md` from `process-logging/<UC-ID>/`.
2. Interpret the new feedback as additional feedback input.
3. Revise the report in working memory.
4. Increment report revision: `R1` → `R2` → `R3` ...
5. Rewrite the SAME `pending_update_report.md` path in ONE atomic Write containing the entire revised report.
6. Update the approval-pending block in `progress.md` to point to the same report path and the new revision.
7. Send the revised report to the user again.
8. Remain in approval-pending state.

Rules:

- User feedback may change impact status, proposed TC changes, priority, wording, or open questions.
- Do NOT apply any update while the report is still pending.
- Do NOT create final `.md` files while the report is still pending.
- Do NOT create `.xlsx` output while the report is still pending.

#### 4.2 If the user approves the report

Accept approval only when the user explicitly says to approve/apply the pending report, for example:

- `Approve update report`
- `Apply this update`
- Equivalent explicit approval in the user's language

After approval:

1. Read the latest `pending_update_report.md` from `process-logging/<UC-ID>/`.
2. Treat that latest report revision as the approved update plan.
3. Continue to Step 5.

#### 4.3 If the user asks to cancel

1. Do not modify deliverable TC files.
2. Delete the temporary `pending_update_report.md` from `process-logging/<UC-ID>/`.
3. Update `progress.md` to remove the approval-pending block or mark it as cancelled.
4. Rewrite worklog last entry → `status = "Cancelled by user before applying update"`.
5. Stop.

---

### Step 5: Apply Approved Update Plan (MANDATORY)

After user approval, apply the approved update plan to the TC baseline.

#### 5.1 Apply update actions per variant

For EACH platform variant V:

- `KEEP`: preserve TC unchanged.
- `UPDATE`: preserve TC ID and update only approved fields.
- `ADD`: create new TC ID(s) after the current maximum ID for V.
- `RETIRE`: remove from active final TC tables; record in update metadata/change log if the final prelude includes one.
- `SPLIT`: preserve original TC ID for the closest original intent; add new IDs for split-out cases.
- `MERGE`: preserve the representative TC ID; do not reuse retired/merged IDs.
- `REVIEW`: do not apply unless the approved report resolves it.
- `ADD_VARIANT`: draft a full new TC set for that variant using the same writing rules as `generate-test-cases.md`; do not require a same-variant baseline TC file; use existing other-variant TC files only as style / coverage references.

Apply all rules in:

- `qc-func-tc-design-exbot/rules/testcase-instruction-rules.md`
- `.claude/rules/qc-writting-rules.md`
- Test case style reference: `Testcase-refer-en.md`
- `common-logic-technical.md` (5 logic phases + blockchain backend add-on)
- `logic-technical.md` (EXBOT / backend-bot add-on checklists)

#### 5.2 Update the Requirement Traceability Matrix

For EACH variant V:

- Rebuild the RTM against the new audited UC.
- For `ADD_VARIANT`, build a brand-new RTM for the requested variant and independently cover 100% of audited ACs in scope for that variant.
- Ensure every in-scope Acceptance Criterion has linked active TC IDs.
- Removed ACs must not remain mapped to active TCs unless still valid through another AC.
- Added ACs must be covered by existing or newly added active TCs.
- If coverage is incomplete, fix the updated TC content before proceeding.

#### 5.3: Persist Full updated TCs to Scratch (MANDATORY — atomic single Write)

This step is the **safety net for Phase 2 auto-recovery**. It locks down the in-memory design before the final md write begins, so that if the final md write is interrupted (multi-part flow, network blip, context flush, etc.), Phase 2's verification gate can detect the mismatch and auto-recover from this scratch — WITHOUT having to re-run the 6-phase drafting.

1. **Compose the full scratch content** in working memory, using the SAME content format as the final deliverable md described in Step 6:
   - The complete required prelude (`# Test Cases — [UC-ID] …`, totals, source filenames, RTM table, etc.).
   - All operation-group sections (`## <Roman>. …`) with their typed subsections — FUNC (`### <Roman>.1. …`), INTG (`### <Roman>.2. …`), NFR (`### <Roman>.3. …`) — and test case tables.
   - The same heading-level rules as Step 6 (only `#` / `####` in the prelude, `##` for operation groups, `###` for FUNC/INTG/NFR).
2. **Write to the scratch path** — logic-only (single track): write the full scratch content to `.claude/skills/qc-func-tc-design-exbot/process-logging/<UC-ID>/02_designed_tcs_logic.md` in **ONE atomic Write call** containing the ENTIRE content. The literal token `logic` stands in for the variant name; there is exactly one.
   - Do NOT use Edit / multiple appends to build the scratch incrementally — if the scratch's own Write is interrupted, Phase 2 cannot recover. If the volume exceeds a Write's practical limit, fail loudly and ask the user — multi-part scratch is NOT supported.
3. Do NOT delete or modify any scratch file later in this skill run — they are durable sources of truth for Phase 1 and are only removed in `SKILL.md` → Step D cleanup at end-of-run.

After this step completes, the update work of Phase 1 is **durably persisted**. Step 6 below is a re-materialization of the same content at the deliverable path; if Step 6 is interrupted, the scratch is still on disk for Phase 2 auto-recovery.

### Step 6: Write the .md File(s) (MANDATORY)

Re-materialize the scratch content (`02_designed_tcs_logic.md` from Step 5.3) to the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`. Use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume. Each file (single or per-part) is an atomic single Write.

**Deliverable file naming:** follow `rules/naming-convention.md` for `func-test-cases-draft` (logic-only — no variant segment). Example: `UC-EXBOT-001_bot-start_testcases_v2.md`.

**At the TOP of the md (or top of `part1` if multi-part), include the following required prelude:**
**Versioning rule:**
- `UPDATE_EXISTING` variants → bump version to `v[N+1]` of the baseline; keep the `Delta vs v[N]` line.
- `ADD_VARIANT` variants → use `v1`; omit the `Delta vs v[N]` line and replace `Total test cases: Y (Delta ...)` with just `Total test cases: Y`.

```markdown
# Test Cases — [UC-ID] [feature-name] (v[N+1])

**Total test cases:** Y (Delta vs v[N]: +A new, ~U updated, -D deleted)
**Scope:** Logic-only (backend / API / bot — no UI)
**Update trigger:** [REQUIREMENT_DELTA / USER_FEEDBACK_ONLY]
**Source UC:** [audited filename + version]
**Source scenarios (if any):** [scenarios filename + version]
**Output language:** English

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | …                   | TC_001, TC_002    | Covered |
| …     | …                   | …                 | Covered [NEW] |
| …     | …                   | …                 | Covered [UPDATE] |
| …     | …                   | …                 | Removed |

---
```

**Heading-level rules (MANDATORY — they govern what does and does not appear in the xlsx):**
- The prelude MUST use only `#` (h1) and `####` (h4) heading levels — these are skipped by the converter, so the prelude does NOT leak into the xlsx.
- Use `##` (h2) ONLY for operation-group headers (e.g., `## I. Operation: Bot start preflight`).
- Use `###` (h3) ONLY for FUNC / INTG / NFR section headers (e.g., `### I.1. …` / `### I.2. …` / `### I.3. …`).

**Layout / Sorting / Encoding requirements (apply when (re)drafting the md — see `qc-func-tc-design-exbot/rules/testcase-instruction-rules.md` → "Sheet Layout & Section Headers"):**
- Preserve the existing operation-group / FUNC / INTG / NFR section headers from the baseline TC file.
- Place new TCs **inside the correct section block** for their operation group and type — FUNC new cases below the matching `<RomanNumeral>.1.` header, INTG below `<RomanNumeral>.2.`, NFR below `<RomanNumeral>.3.`. Do NOT append at the end of the md.
- When the new audited UC adds a new operation, insert a new operation-group header block (next Roman numeral with its `.1` / `.2` / `.3` sub-headers) at the appropriate position.
- Sorting within a group: FUNC → INTG/State → NFR-logic. Within FUNC: Happy path → input/contract validation → core logic & decision tables → error/exception. Within INTG: cross-service/queue/external-API → reconciliation → idempotency/concurrency. Within NFR: security → reliability/resilience → performance/throughput → auditability.
- Encoding: UTF-8 md; do not transliterate technical identifiers.

**Inline annotations on changed TCs in the body:**
- `[NEW — AC-XX]` next to the title of newly added TCs.
- `[UPDATED — Reason: AC-XX modified]` next to the title of modified TCs.
- Do NOT include retired/deleted TCs in the md body — their removal is reflected in the Updated RTM (`Removed` status).

**Do NOT write a separate summary file.** The md (with its prelude) is the only design artifact this workflow produces. Anything noteworthy beyond the prelude (e.g., out-of-scope items, requirement gaps observed during drafting) will be reported on chat by the orchestrator (`SKILL.md` → Step C).

---

### Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §4.2 (end-of-phase). At this point, two artifacts already exist on disk: the scratch `02_designed_tcs_logic.md` (Step 5.3) and the final updated deliverable `.md` v[N+1] (Step 6). The remaining work is to publish the `## Phase 1 Summary` block to progress.md (so Phase 2 can verify the final md), then update worklog.

1. **Compute the Phase 1 summary** by counting TCs in the final v[N+1] md (which equals the scratch — both should match exactly at this moment):
   - Total TCs (single integer) + the FUNC / INTG / NFR split (carried on the `FUNC total` / `INTG+NFR total` schema lines).
   - **Delta vs v[N]**: `+<A> new, ~<U> updated, -<D> deleted` (counted from the inline annotations: `[NEW]` for new, `[UPDATED]` for modified; deleted count comes from RTM `Removed` rows). ASCII "Delta", not the Greek glyph.
   - Per-group breakdown: for each `## <Roman>.` operation group, count TC rows in its `### <Roman>.1.` (FUNC), `### <Roman>.2.` (INTG) and `### <Roman>.3.` (NFR) tables.
   - The output language detected in Phase 1.
   - The track being updated (`logic`).
   - The scratch path: absolute path to `02_designed_tcs_logic.md`.
   - The final v[N+1] md path(s) written in Step 6 (single file or multi-part list, absolute paths).
2. **Append `## Phase 1 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. The block contains:
   - A top-level **Variants in scope:** line with the single value `logic`.
   - Exactly ONE `### Variant: logic` sub-block, populated from the fields computed above (totals, language, scratch path, final md paths, per-group breakdown table, plus the `**Delta vs v[N]:**` line below the table).
   - Atomic single Write that overwrites `progress.md` while preserving all existing fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Do NOT touch `last_phase_done` here — it stays at its current value (set when Phase 1 started). Update `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`. Append the final v[N+1] `.md` path(s) to `output` (excluding `process-logging/`).

> **Note:** `last_phase_done: 1` is NOT written here — it gets written at the START of Phase 2, only AFTER Phase 2's Step 0 verification gate passes. This is what guarantees a partial / mismatched updated md cannot be silently accepted as "Phase 1 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 2

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 1 finishes successfully.
