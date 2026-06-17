## Update Test Cases (Design Update Workflow)

> **Scope:** This workflow produces ONLY the updated test case `.md` file. It is fully independent from the `.xlsx` artifact — no script invocation, no xlsx step.
>
> **Purpose:** Update-test-cases after one or more changes occur, without rerunning the full generate-test-cases flow unless necessary.
> 1. **Requirement change:** The audited UC Readiness Report has been updated (new version). Test cases need to be aligned with the changed requirements.
> 2. **New variant:** The user request test cases for another variant.
> 3. **User feedback:** The user provides explicit feedback about gaps, errors, or missing coverage in the existing test cases.
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
| `ADD_VARIANT` | The user asks to write test cases for an additional platform variant that does not have a current TC `.md` baseline. | Draft a full new TC set for the requested variant using the latest approved audited UC, common technical, and that variant's technical rubric. Existing variant TC files are reference-only unless also impacted by another trigger. |
| `MIXED` | More than one trigger applies in the same run, e.g. audited UC changed and user also asks to add `mobile-native`. | Produce one consolidated report covering both changed existing variants and newly added variants. Apply only approved actions. |

**Variant expansion rule:** When the trigger type is `ADD_VARIANT`, the newly requested variant(s) may not have existing TC files yet. This is valid because those variants are being created for the first time. However, any existing variant that is also being updated in the same run MUST still have its current TC markdown file available as the update baseline.
**Explicit user request rule:** if the user explicitly names a target variant (for example, "write mobile-native test cases too"), include that variant in scope even if it is not yet present in the current TC baseline. If it is absent from `project-context-master.md` → Product Platform Type, record this discrepancy in the report and proceed as a user-requested variant override unless the target variant is unsupported.

If the trigger type is ambiguous, ask the user:
> _"Bạn muốn cập nhật test cases vì: (A) Tài liệu đặc tả đã thay đổi và đã có audited version mới, (B) Tôi có feedback về test cases hiện tại, (C) Viết test cases cho Platform type khác, hay (D) Mix - có nhiều mục thay đổi"_
>
> If the user choose B, ask the user about the feedback content and the test cases that need updating.
> If the user choose C, ask the user about the new variant.
> If the user choose D, ask the user about all of the changed.

#### 1.2 — Read all required input files

Read the following files before performing any analysis:

- Current / baseline `func-test-cases-draft` `.md` file(s) to be updated.
- Old audited UC file that was used to design the current TC version.
- New audited UC file that should drive the update.
- `project-context-master.md`.
- `.claude/skills/qc-func-tc-design/references/design-technical/common-technical.md`.
- User feedback, if provided in the current prompt or earlier messages for this update run.
- User-requested target platform variant(s), if the trigger is adding test cases for another variant.

Read optional files if present:

- Old `func-test-scenarios` used by the current TC version.
- New / updated `func-test-scenarios`.

#### 1.3 Resolve Platform Variants (MANDATORY)

1. Read `project-context-master.md` §1 → **Product Platform Type**.
2. Parse the value(s). One or more of: `web-responsive`, `web-static`, `mobile-native`, `mobile-hybrid`, `desktop-native`.
3. Parse user-requested target variant(s), if explicitly provided in the prompt.
4. Cross-check the resolved project-context variants against the current TC file prelude(s) → `**Platform variant:**`.
5. Build the update scope as:
   - Existing variants that have current TC `.md` baselines and are impacted by audited delta or user feedback.
   - PLUS user-requested target variants that do not yet have current TC `.md` baselines (`ADD_VARIANT`).
   - PLUS variants newly added by the new audited UC / project context (`ADD_VARIANT`).
6. If `Product Platform Type` is missing or blank:
   - If the user explicitly requested a supported target variant, proceed only for that requested variant and record `Product Platform Type missing; using explicit user-requested variant override` in the report.
   - Otherwise STOP and ask the user to populate it.
7. If a resolved variant has no current TC `.md` file:
   - If the variant is explicitly requested by the user OR newly added by the new audited UC / project context, mark that variant as `ADD_VARIANT`; it is valid for this variant to have no baseline TC file.
   - Otherwise STOP and ask the user to provide the missing current TC `.md` file.
8. If the user requests an unsupported variant value, STOP and ask the user to choose one of: `web-responsive`, `web-static`, `mobile-native`, `mobile-hybrid`, `desktop-native`.
9. For EACH applicable variant, load `qc-func-tc-design/references/design-technical/<variant>-technical.md` end-to-end. Hold common + variant rubrics in working memory.
10. Record the resolved variant list and the per-variant scope reason (`UPDATE_EXISTING` or `ADD_VARIANT`) as a working note.

#### 1.4 Identify update baseline

For EACH variant V, identify:

- Baseline TC file path(s).
- Baseline TC version from filename and/or prelude.
- Baseline source UC filename and version from prelude.
- Baseline source scenarios filename and version, if any.
- Total TC count and GUI / FUNC split.
- Existing TC ID list.
- Existing screen sections (`## <Roman>. ...`).
- Existing GUI/FUNC section structure (`### <Roman>.1. ...`, `### <Roman>.2. ...`).
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
| `ADD_VARIANT_REQUEST` | User asks to write TCs for another platform variant. | Mark requested variant as `ADD_VARIANT`; propose full new TC set for that variant. |
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
.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/pending_update_report.md
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
# Báo cáo ảnh hưởng cập nhật Test Cases — [UC-ID]

**Trạng thái:** Chờ user phê duyệt  
**Phiên bản report:** R1  
**Trigger type:** [REQUIREMENT_DELTA / USER_FEEDBACK_ONLY / ADD_VARIANT / MIXED]  
**Variant trong scope:** [web-responsive, mobile-native, ...]  
**Variant được yêu cầu bổ sung:** [không có / mobile-native / ...]  
**Audited source cũ:** [tên file + version]  
**Audited source mới:** [tên file + version]  
**Nguồn TC hiện tại:** [tên file(s) + version]  
**Nguồn feedback của user:** [prompt / file / không có]

#### Tóm tắt

| Hạng mục | Số lượng |
|---|---:|
| Requirement được thêm mới | N |
| Requirement bị thay đổi | N |
| Requirement bị loại bỏ | N |
| Requirement được làm rõ | N |
| Requirement còn mơ hồ / cần xác nhận | N |
| Variant mới được yêu cầu bổ sung | N |
| Bộ TC đầy đủ cho variant mới được đề xuất | N |
| TC hiện tại giữ nguyên | N |
| TC hiện tại cần cập nhật | N |
| TC mới được đề xuất | N |
| TC được đề xuất retire | N |
| TC được đề xuất tách nhỏ | N |
| TC được đề xuất gộp | N |
| Hạng mục cần user review / xác nhận | N |

#### Thay đổi Requirement

| Change ID | Loại thay đổi | Ý nghĩa cũ | Ý nghĩa mới | Nguồn | Ảnh hưởng dự kiến tới TC |
|---|---|---|---|---|---|

#### Diễn giải Feedback của User

| Feedback ID | Feedback | Diễn giải | Ảnh hưởng tới TC | Trạng thái xử lý |
|---|---|---|---|---|

#### Mở rộng phạm vi Variant

Chỉ dùng section này khi `Trigger type` là `ADD_VARIANT` hoặc `MIXED`.

| Variant được yêu cầu | Nguồn yêu cầu | Đã có baseline TC hiện tại? | Technical rubric áp dụng | Output đề xuất | Ghi chú |
|---|---|---|---|---|---|
| `<variant>` | user prompt / project context / audited UC | Có / Không | `<variant>-technical.md` | Tạo mới full TC `.md` | ... |

#### Tóm tắt ảnh hưởng theo Variant

| Variant | Giữ nguyên | Cập nhật | Thêm mới | Retire | Tách nhỏ | Gộp | Cần review |
|---|---:|---:|---:|---:|---:|---:|---:|

#### Ma trận ảnh hưởng Test Case — <variant>

| TC ID | Tiêu đề hiện tại | Impact Status | Lý do ảnh hưởng | Hành động đề xuất |
|---|---|---|---|---|

#### Test Cases mới được đề xuất — <variant>

| Proposed TC ID | Tiêu đề | Nguồn thay đổi | Loại TC | Priority | Ghi chú |
|---|---|---|---|---|---|

#### Test Cases đề xuất Retire / Merge — <variant>

| TC ID | Tiêu đề | Lý do | TC thay thế / Merge target |
|---|---|---|---|

#### Câu hỏi mở / Điểm cần xác nhận

| Hạng mục | Nguồn | Lý do cần xác nhận | Quyết định cần user đưa ra |
|---|---|---|---|

#### Hướng dẫn phê duyệt

User có thể phản hồi theo một trong các cách sau:

- `Duyệt report` hoặc `Approve update report` để áp dụng đúng theo report này.
- Gửi thêm feedback nếu cần chỉnh report trước khi áp dụng.
- Cancel để dừng workflow, plan sẽ vẫn lưu ở folder process-logging để bạn có thể tiếp tục lại sau.
```

#### 3.3 Report quality gate

Before sending the report to the user:

- Every meaningful audited delta must appear in `Requirement Delta`.
- Every user feedback item must appear in `User Feedback Interpretation`.
- Every existing TC must appear in one impact status unless the report explicitly scopes it out.
- Every requested new variant must appear in `Variant Coverage Expansion` with proposed output and rubric.
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
- `Duyệt report`
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

- `qc-func-tc-design/rules/testcase-instruction-rules.md`
- `.claude/rules/qc-writting-rules.md`
- Language-matched test case reference: `Testcase-refer-vi.md` or `Testcase-refer-en.md`
- `common-technical.md`
- Variant-specific technical rubric for V

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
   - All screen sections (`## <Roman>. …`) with their GUI (`### <Roman>.1. …`) and FUNC (`### <Roman>.2. …`) subsections and test case tables.
   - The same heading-level rules as Step 6 (only `#` / `####` in the prelude, `##` for screens, `###` for GUI/FUNC).
2. **Write to scratch path(s)** — ALWAYS per-variant (no special case for single-variant projects): for EACH platform variant V, write that variant's full scratch content to `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/02_designed_tcs_<V>.md` in **ONE atomic Write call** containing the ENTIRE content for that variant.
   - For a single-variant project, this means writing ONE file with the project's only variant in its name (e.g., `02_designed_tcs_web-responsive.md`). The "bare" name `02_designed_tcs.md` (without variant suffix) is NEVER used — Phase 2 always probes by variant.
   - For a multi-variant project, write N atomic Write calls, one per variant.
   - Do NOT use Edit / multiple appends to build a scratch incrementally — if a scratch's own Write is interrupted, Phase 2 cannot recover that variant. If a single variant's volume exceeds a Write's practical limit, that is the signal to fail loudly and ask the user — multi-part scratch per variant is NOT supported.
3. Do NOT delete or modify any scratch file later in this skill run — they are durable sources of truth for Phase 1 and are only removed in `SKILL.md` → Step D cleanup at end-of-run.

After this step completes, the update work of Phase 1 is **durably persisted for every variant**. Step 6 below is a re-materialization of the same content at the deliverable path; if Step 6 is interrupted for any variant, that variant's scratch is still on disk for Phase 2 auto-recovery.

### Step 6: Write the .md File(s) (MANDATORY)

For EACH platform variant V resolved in Step 1.3, re-materialize that variant's scratch content (`02_designed_tcs_<V>.md` from Step 5.3) to the **deliverable path** defined in `path-registry.md` for `func-test-cases-draft`. Each variant produces its own deliverable file(s); within a variant, use a single file or multi-part files (`*_part1.md`, `*_part2.md`, …) depending on volume. Each file (single or per-part) is an atomic single Write.

**Deliverable file naming:** Insert a `_<variant>` segment between the `testcases` type and the version, per `rules/naming-convention.md`. Example for UC-101 with both web-responsive and mobile-native:
- `UC-101_user-login_testcases_web-responsive_v1.md`
- `UC-101_user-login_testcases_mobile-native_v1.md`

For a single-variant project the same naming applies (just one variant in the name), e.g., `UC-101_user-login_testcases_web-responsive_v1.md`. The "no-variant" filename pattern is NOT used — every deliverable carries its variant in the name so Phase 2's per-variant flow can pair scratch ↔ final md unambiguously.

**At the TOP of the md (or top of `part1` if multi-part), include the following required prelude:**
**Versioning rule:**
- `UPDATE_EXISTING` variants → bump version to `v[N+1]` of the baseline; keep the `Delta vs v[N]` line.
- `ADD_VARIANT` variants → use `v1`; omit the `Delta vs v[N]` line and replace `Total test cases: Y (Delta ...)` with just `Total test cases: Y`.

```markdown
# Test Cases — [UC-ID] [feature-name] [— <variant> if multi-platform] (v[N+1])

**Total test cases:** Y (Delta vs v[N]: +A new, ~U updated, -D deleted)
**Platform variant:** [web-responsive / web-static / mobile-native / mobile-hybrid / desktop-native]
**Update trigger:** [REQUIREMENT_DELTA / USER_FEEDBACK_ONLY / ADD_VARIANT / MIXED]
**Source UC:** [audited filename + version]
**Source scenarios (if any):** [scenarios filename + version]
**Output language:** [VI / EN]

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
- Use `##` (h2) ONLY for screen headers (e.g., `## I. Màn hình: …` / `## I. Screen: …`).
- Use `###` (h3) ONLY for GUI / FUNC section headers (e.g., `### I.1. …` / `### I.2. …`).

**Layout / Sorting / Encoding requirements (apply when (re)drafting the md — see `qc-func-tc-design/rules/testcase-instruction-rules.md` → "Sheet Layout & Section Headers"):**
- Preserve the existing screen / GUI / FUNC section headers from the baseline TC file (for `UPDATE_EXISTING` variants).
- Place new TCs **inside the correct section block** for their screen and type — GUI new cases below the matching `<RomanNumeral>.1.` header, FUNC new cases below `<RomanNumeral>.2.`. Do NOT append at the end of the md.
- When the new audited UC adds a new screen, insert a new screen header block (next Roman numeral with its `.1` / `.2` sub-headers) at the appropriate position.
- Sorting within a section: GUI before Functional. Within GUI: Screen Initialization → Item Interactions → Common UI cases → UI elements verify. Within FUNC: Happy path → Validation → Error/Exception.
- Encoding (Rules 0a–0d): UTF-8 md, preserve dấu, no `unicodedata.normalize` / `unidecode` / Latin-1.

**Inline annotations on changed TCs in the body:**
- `[NEW — AC-XX]` next to the title of newly added TCs.
- `[UPDATED — Reason: AC-XX modified]` next to the title of modified TCs.
- Do NOT include retired/deleted TCs in the md body — their removal is reflected in the Updated RTM (`Removed` status).

**Do NOT write a separate summary file.** The md (with its prelude) is the only design artifact this workflow produces. Anything noteworthy beyond the prelude (e.g., out-of-scope items, requirement gaps observed during drafting) will be reported on chat by the orchestrator (`SKILL.md` → Step C).

---

### Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §4.2 (end-of-phase). At this point, two artifacts already exist on disk: the scratch `02_designed_tcs_<V>.md` (Step 5.3) and the final updated deliverable `.md` v[N+1] for variant `<V>` (Step 6). The remaining work is to publish the `## Phase 1 Summary` block to progress.md (so Phase 2 can verify the final md), then update worklog.

1. **Compute the Phase 1 summary** by counting TCs in the final v[N+1] md (which equals the scratch — both should match exactly at this moment):
   - Total TCs (single integer) + GUI total + FUNC total (each on its own line in the summary, per `SKILL.md` §1 schema).
   - **Delta vs v[N]**: `+<A> new, ~<U> updated, -<D> deleted` (counted from the inline annotations: `[NEW]` for new, `[UPDATED]` for modified; deleted count comes from RTM `Removed` rows). ASCII "Delta", not the Greek glyph.
   - Per-screen breakdown: for each `## <Roman>.` screen, count TC rows in its `### <Roman>.1.` (GUI) and `### <Roman>.2.` (FUNC) tables.
   - The output language detected in Phase 1.
   - The platform variants being updated (`<V>`).
   - The scratch path: absolute path to `02_designed_tcs_<V>.md`.
   - The final v[N+1] md path(s) written in Step 6 (single file or multi-part list, absolute paths).
2. **Append `## Phase 1 Summary` block to `progress.md`** using the exact schema from `SKILL.md` → §1 `progress.md` format. The block contains:
   - A top-level **Variants in scope:** line listing all variants comma-separated.
   - Exactly ONE `### Variant: <V>` sub-block per variant, populated from the fields computed above (totals, language, scratch path, final md paths, screen breakdown table, plus the `**Delta vs v[N]:**` line below the table).
   - Atomic single Write that overwrites `progress.md` while preserving all existing fields (run_id, uc_id, workflow, started_at, last_phase_done, next_phase, updated_at, ## Notes). Do NOT touch `last_phase_done` here — it stays at its current value (set when Phase 1 started). Update `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`. Append the final v[N+1] `.md` path(s) to `output` (excluding `process-logging/`).

> **Note:** `last_phase_done: 1` is NOT written here — it gets written at the START of Phase 2, only AFTER Phase 2's Step 0 verification gate passes. This is what guarantees a partial / mismatched updated md cannot be silently accepted as "Phase 1 done" on resume. See `convert-md-to-xlsx.md` → Step 0.

---

## Hand-off to Phase 2

Next file: `workflows/convert-md-to-xlsx.md`. The orchestrator (`SKILL.md` → Step B) auto-triggers it after Phase 1 finishes successfully.
