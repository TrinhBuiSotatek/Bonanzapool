# Re-Audit

> **Friendly name (for worklog & dashboard):** `Identify the source of change and apply` (EN) / `Phân tích thông tin mới, câu trả lời, áp dụng thay đổi` (VI).
>
> **Purpose:** Re-audit a previously audited use case after one or more changes occur, without rerunning the full first-audit flow unless necessary.
>
> Re-audit is used when:
> * source documents have been updated after a previous audit;
> * BA / QC Lead / PO / Tech Lead answered open questions;
> * user feedback indicates the previous report or Agent understanding needs correction;
> * a mix of document updates, feedback, and question answers must be reconciled;
> * the user asks to refresh readiness after changes.
>
> **Output:** `uc-review-report v[N+1].md` written to the UC's output folder.

---

## Inputs

### Required baseline input

* Latest `uc-review-report v[N].md` for the UC.

### Optional but recommended inputs

* `question-backlog` entries for the UC.
* New BA / QC Lead / PO / Tech Lead answers.
* Updated source artefact(s), if documents changed.
* Diff or change notes, if available.
* User feedback about the previous report.
* `.claude/skills/qc-uc-read/references/scoring-rubric.md`.
* `.claude/skills/qc-uc-read/templates/UC_readiness_review_template_v3.md`.
* `.claude/skills/qc-uc-read/references/qc-writting-rules.md`.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running"`. Append input file names (previous audited file + question-backlog) to `input`.

---

## Step 0 — Ask user to identify change source

Analyze the user prompt to see if it contains information about which source has been changed. If so, skip step 0; otherwise, proceed to step 0.

Ask the user:

```text
Để chạy re-audit đúng phạm vi, bạn cho mình biết thay đổi lần này đến từ nguồn nào?

1. BA đã trả lời open question trong question-backlog
2. Tài liệu đặc tả / API / common rule đã thay đổi
3. Design / prototype đã thay đổi
4. Bạn feedback về report cũ hoặc cách Agent hiểu nghiệp vụ
5. Có nhiều loại thay đổi cùng lúc

Bạn vui lòng cung cấp thêm:
- report audited version đang dùng làm baseline
- nguồn thay đổi cụ thể: Q-ID, file, section, màn hình, hoặc feedback text
```

---

## Step 1 — Select input scope

Use the selected mode only to decide what must be read.

| Mode                      | When to use                                                                     | Input to read                                                                            |
| ------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `question-backlog answer` | BA / QC / PO answered open questions                                            | Latest audited report + `question-backlog` rows for this UC / Q-ID                       |
| `document update`         | UC spec, API, common rule, message, BPMN, or other requirement artefact changed | Latest audited report + changed document or all documents                                    |
| `design update`           | Design image, wireframe, or prototype changed                                   | Latest audited report + design/prototype screen(s)                               |
| `user feedback`           | User says report or Agent understanding is wrong/incomplete                     | Latest audited report + feedback text only, unless feedback requires source verification |
| `mixed update`            | More than one source changed                                                    | Latest audited report + each changed input above                                         |

Do not read all raw artefacts by default.

Read only the source related to the change.

---

## Step 2 — Load baseline audited report

Always load the latest audited report for the UC.

Use it as the baseline for comparison.

Read these sections carefully:

* Feature Brief
* Section 4 — UI object and mapping
* Section 5 — Object attributes and behavior
* Section 6 — Workflow / business logic
* Section 7 — Integration impact
* Section 8 — Acceptance Criteria
* Section 10.1 — Gap / question table
* Section 10.3 — Audit Summary
* Section 11 — Change log

---

## Step 3 — Read changed input

Read changed input according to the selected mode.

### 3.1 Question-backlog answer

Open `question-backlog`.

Find rows for the current UC and relevant Q-ID(s).

Extract:

* question ID;
* original question;
* answer;
* answer owner;
* answer date/status;
* whether the answer says source document was updated.

### 3.2 Document update

Read the updated document or changed section.

If the user provides a diff, use the diff.

If no diff is provided:

1. Use the baseline audited report as the old understanding.
2. Read the updated source section.
3. Compare updated source content against the related section in the audited report.
4. Identify what is deleted, modified, or added.

Do not require reading the previous raw source version unless it is available and needed. The previous audited report is the comparison baseline.

### 3.3 Design update

3.3.1. Read the changed design/prototype screen(s)/ascii file.
Launch the following independent read-only sub-agents in parallel.

Use a **single message with multiple `Agent` tool calls in the same `<function_calls>` block**.
Do **not** await one sub-agent before invoking the next.

These sub-agents have no data dependency on each other.

Only after all launched sub-agents return, continue to section 3.3.2.

#### Sub-agent A — Resolve common rules and messages

Run this sub-agent if `requirement-common-files` exists.

If common files are missing, skip this sub-agent and warn the user once.

Call the `Agent` tool with:

* `subagent_type: "Explore"`
* `description: "Resolve common rules and messages for <UC-ID>"`
* `prompt`:

```text
You are a read-only lookup agent. Do not infer, rewrite, translate, or summarize. Extract only verbatim evidence.

1. Read the detailed UC file at:
   <absolute path to the requirement file for UC-ID>

2. Extract every referenced identifier or named reference, including:
   - error codes, for example E001, E123, ERR_*
   - message IDs, for example MSG_*
   - business rule IDs, for example BR-*, BR001, RULE_*
   - notification names
   - email / SMS / push template names
   - validation message names
   - Vietnamese or English message names written in quotation marks
   - any common rule, common message, or shared configuration reference

3. Search all files under:
   <absolute path to requirement-common-files>

4. When multiple versions of the same common file exist, use the latest file by version suffix, for example:
   - error-codes_v3.md is newer than error-codes_v2.md
   - business-rules_v10.md is newer than business-rules_v9.md

5. For each UC mention, return a Markdown table in exactly this format:

| UC mention | Common file | Section | Verbatim content |
|---|---|---|---|
| E001 | error-codes_v3.md | §2.1 | "Tài khoản không tồn tại" |

6. If a mention cannot be found, write `NOT_FOUND` in the "Common file" column.

7. Do not invent missing content.
8. Do not translate.
9. Do not explain.
10. Keep the report under 400 lines. If the result is too long, prioritize mentions that appear in the UC’s main flow, alternate flows, validation rules, and exception flows.
```

---

#### Sub-agent B — Extract UI evidence from HTML prototype

Run this sub-agent if HTML prototype files are provided.

Call the `Agent` tool with:

* `subagent_type: "Explore"`
* `description: "Extract UI evidence from prototype for <UC-ID>"`
* `prompt`:

```text
You are a UI evidence extraction agent. Do not evaluate quality. Do not infer hidden requirements. Extract only observable UI evidence.

1. Read the detailed UC file at:
   <absolute path to the requirement file for UC-ID>

2. Identify screens, dialogs, forms, and UI states mentioned by the UC.

3. Inspect the HTML prototype files at:
   <absolute path to prototype files>

4. For each relevant screen or state, extract:
   - screen/page name
   - source file or route
   - visible UI text
   - buttons and actions
   - input fields
   - placeholder text
   - tooltip or helper text
   - inline validation messages
   - error, warning, success, or notification messages
   - empty, loading, disabled, readonly, or selected states
   - modal / popup / confirmation dialog content
   - navigation actions
   - table columns, cards, badges, statuses, or displayed data

5. Return the result as Markdown:

## Prototype UI Evidence for <UC-ID>

### Screen: <screen/page name>
- Source: <file or route>
- Related UC section(s): <section names if identifiable>

| UI element type | Label / text | State | Notes |
|---|---|---|---|

## Prototype Coverage Notes

| UC reference | Prototype evidence | Status |
|---|---|---|
| <UC screen/field/action> | <matching prototype source> | FOUND / NOT_FOUND / UNCLEAR |

6. Do not judge whether FOUND or NOT_FOUND is a defect.
7. Do not suggest improvements.
8. Do not translate UI text.
9. Do not invent states that are not present.
10. Keep the report under 500 lines.
```

---

#### Sub-agent C — Extract UI evidence from image designs

Run this sub-agent if image design files are provided, such as PNG, JPG, JPEG, or screenshots.

Call the `Agent` tool with:

* `subagent_type: "Explore"`
* `description: "Extract UI evidence from image designs for <UC-ID>"`
* `prompt`:

```text
You are a UI evidence extraction agent. Analyze the provided design images visually. Do not evaluate quality. Do not infer hidden requirements. Extract only visible UI evidence.

1. Read the detailed UC file at:
   <absolute path to the requirement file for UC-ID>

2. Identify screens, dialogs, forms, and UI states mentioned by the UC.

3. Read the image design files at:
   <absolute path to image design files>

4. For each relevant image, extract:
   - image file name
   - screen/page name
   - visible UI text
   - buttons and actions
   - input fields
   - placeholder text
   - tooltip or helper text
   - inline validation messages
   - error, warning, success, or notification messages
   - empty, disabled, readonly, selected, or loading states
   - modal / popup / confirmation dialog content
   - navigation actions
   - table columns, cards, badges, statuses, or displayed data
   - visible flow indicators such as breadcrumbs, tabs, steppers, or arrows

5. Return the result as Markdown:

## Image UI Evidence for <UC-ID>

### Image: <file name>
- Related screen: <screen/page name>
- Related UC section(s): <section names if identifiable>

| UI element type | Visible text / label | State | Notes |
|---|---|---|---|

## Image Coverage Notes

| UC reference | Image evidence | Status |
|---|---|---|
| <UC screen/field/action> | <matching image/file> | FOUND / NOT_FOUND / UNCLEAR |

6. Do not judge whether FOUND or NOT_FOUND is a defect.
7. Do not suggest improvements.
8. Do not translate UI text.
9. Do not invent invisible content.
10. If text is unclear or unreadable, write `UNCLEAR_TEXT`.
11. Keep the report under 500 lines.
```

---

#### Sub-agent D — Extract UI evidence from ASCII screen files

Run this sub-agent if ASCII screen files are provided (per `references/input-files-format.md` §2.5 — files under `03_modules/<portal>/[<role>/]ascii-screen/<screen-slug>.md`).

Call the `Agent` tool with:

* `subagent_type: "Explore"`
* `description: "Extract UI evidence from ASCII screens for <UC-ID>"`
* `prompt`:

```text
You are a UI evidence extraction agent for ASCII-screen-style design files. Do not evaluate quality. Do not infer hidden requirements. Extract only observable evidence from ASCII layout blocks, element-section tables, quick-reference lines, and markers present in the file.

1. Read the detailed UC file at:
   <absolute path to the requirement file for UC-ID>

2. Identify screens referenced by the UC. Resolve each screen via, in priority order:
   - the UC frontmatter `linked_screens` array;
   - the `Screens:` bullet inside the UC `## Trace` section;
   - the `ascii-screen/index.md` mapping (rich `Linked Use Cases` column OR shared `FM-*` code).
   Each resolved slug points to a file at `03_modules/<portal>/[<role>/]ascii-screen/<screen-slug>.md`.

3. For each linked ASCII screen file, read all of:
   - frontmatter (`type`, `status`, `tags`, `changelog`);
   - quick-reference block (3 bold lines: Route, Nav label, Module);
   - `## Markers` section (the project's 📋 Spec vs ⚡ Dev-built convention);
   - `## Layout Overview` — the fenced ASCII layout block plus any per-tab / per-state sub-sections such as `### <Tab Name>`;
   - every `## <Element Group>` section (e.g. Stat Cards, Table, Buttons, Form) and its inline table;
   - `## Data Sources` (API endpoints or stores the screen reads);
   - `## Notes` (build-state caveats, current limitations, future-work flags).

4. Atomic extraction rules:
   - Treat every row in an element-group table as ONE UI element. Do not collapse rows.
   - For the ASCII layout block, extract every distinct visible element: button labels inside `[ ... ]`, input regions `_____`, badges `( ... )`, tabs, status chips, panel titles, table column headers, breadcrumbs, icons, tooltips. Each is a separate row, even if it also appears in an element-group table — flag the duplicate in the Notes column.
   - For multi-tab screens, prefix every element extracted from `### <Tab Name>` with the tab name in the Section group column.
   - Preserve the marker (`📋 Spec`, `⚡ Dev-built`, or `unknown` if neither is shown) per row.
   - Preserve labels verbatim, including Vietnamese diacritics, English, Korean, Japanese, or Chinese. Do not translate.
   - If the file's `status` is `draft` OR the layout sub-section contains "wireframe TBD", still extract everything visible but add the flag `WIREFRAME_DRAFT` in the Notes column for the affected rows.
   - If an ASCII drawing cannot be unambiguously resolved to an element type, write `UNCLEAR_ASCII` in the Element type column instead of guessing.

5. Return the result as Markdown:

## ASCII Screen UI Evidence for <UC-ID>

### Screen: <screen slug>
- Source: <relative path from plan root>
- Route: <value from quick-reference block, or NOT_FOUND>
- Nav label: <value, or NOT_FOUND>
- Module: <value, or NOT_FOUND>
- Related UC section(s): <UC section names that mention this screen, if identifiable>
- Markers convention: <verbatim short summary from `## Markers`, or NOT_FOUND>

#### Layout-block elements
| Element type | Label / text | Section group | Marker | State / variant | Notes |
|---|---|---|---|---|---|

#### Element-section rows
| Element type | Label / text | Section group | Marker | State / variant | Source row |
|---|---|---|---|---|---|

#### Data Sources
| Endpoint / Store | Purpose | Marker |
|---|---|---|

#### Notes
- <verbatim bullet from `## Notes`, one per row>

## ASCII Coverage Notes

| UC reference | ASCII evidence | Status |
|---|---|---|
| <UC screen / field / action> | <matching screen + element group> | FOUND / NOT_FOUND / UNCLEAR |

6. Do not judge whether FOUND or NOT_FOUND is a defect.
7. Do not suggest improvements.
8. Do not translate labels.
9. Do not invent elements that are not present in the ASCII block, element-section tables, quick-reference lines, or `## Notes`.
10. Do not infer behavior. Behavior synthesis happens later in Phase 1 Step 2.
11. Keep the report under 600 lines. If too long, prioritize screens that match the UC's `linked_screens` and the element groups referenced by the UC's Main Flow, Alternate Flows, and Error / Exception Flows.
```

---

#### Design artefact handling rules

* If HTML prototype, image design, and ASCII screen files are all provided, run Sub-agent B, C, and D in parallel.
* If only one or two of the three are provided, run only the matching sub-agents.
* If other design artefact is provided (not HTML prototype, image design, or ASCII screen files) the main Agent HAVE TO handle those as design files.
* If no design, prototype, or ASCII screen artefact is provided, skip design extraction and warn the user once.
* Do not treat missing optional artefacts as a blocker.
* For projects where ASCII screen is the canonical UI source (e.g., the project has an `ascii-screen/` folder but no HTML prototype or image artefacts), Sub-agent D output is the primary UI evidence used by §F.1 in Step 2 — do not penalize §F.1 for the absence of HTML or image evidence in that case.

3.3.2. Compare with Section 4 and Section 5 of the audited report.

Identify UI changes:

* added UI object;
* removed UI object;
* changed label;
* changed component type;
* changed mandatory marker;
* changed default value / placeholder / enum;
* changed state / behavior / validation / message;
* changed navigation or action.

### 3.4 User feedback

Read the feedback text.

Decide whether it affects:

* wording only;
* Agent understanding;
* workflow logic;
* UI behavior;
* AC;
* score/readiness.

Only open source artefacts if the feedback says the Agent misread a specific source or if verification is required.

---

## Step 4 — Compare and classify changes

Create a compact change table.

```md
## Re-audit Change Summary

| Change ID | Source | Affected audited section | Change type | Old content | New content | Impact on AC? | Impact on score? |
|---|---|---|---|---|---|---|---|
| CH-01 | question-backlog Q1 / updated UC section / design screen / feedback | Section X | Added / Modified / Deleted | <old audited content> | <new content> | Yes / No | Yes / No |
```

Change type:

| Type        | Meaning                                                                     |
| ----------- | --------------------------------------------------------------------------- |
| `Added`     | New requirement, UI object, behavior, rule, flow, issue, or AC is added.    |
| `Modified`  | Existing audited content changed.                                           |
| `Deleted`   | Existing audited content is no longer valid or removed from updated source. |
| `No change` | Input does not affect audited content.                                      |

---

## Step 5 — Update affected report sections

Update only affected sections in the audited report.

Do not regenerate unchanged sections.

Rules:

* If a Q&A answer is not yet reflected in source document, mark it as stakeholder answer and keep a dependency note.
* If updated source contradicts the previous report, update the report and record the change in Section 10.1 or Change Summary.
* If design changed, update Section 4 and Section 5.
* If workflow changed, update Section 6.
* If integration changed, update Section 7.
* If issue status changed, update Section 10.1.
* Always update Section 11 Change log.

---

## Step 6 — Update Acceptance Criteria

AC update is mandatory in every re-audit.

Compare old Section 8 AC with the new information.

Report AC changes explicitly:

```md
## AC Change Summary

| AC ID | Change type | Old AC content | New AC content | Reason / source |
|---|---|---|---|---|
| AC-01 | Added / Modified / Deleted / Unchanged | <old AC> | <new AC> | <Q-ID / source section / design screen / feedback> |
```

Rules:

* If a requirement is added, add or update AC.
* If behavior changes, modify related AC.
* If a requirement is removed, delete or mark related AC as no longer applicable.
* If answer only clarifies existing behavior, update AC wording for testability.
* If AC is based on stakeholder answer but source is not updated, mark `Suy luận / xác nhận từ phản hồi, cần cập nhật vào source`.

---

## Step 7 — Re-score affected areas

Use `scoring-rubric.md` as the single source of truth.

Do not copy scoring definitions into this workflow.

Re-score only affected scoring areas.

Keep unaffected scores from the previous audited report.

```md
## Re-audit Scoring Summary

| Scoring area | Previous score | New score | Reason |
|---|---:|---:|---|
| <area> | X/Y | X/Y | <short reason> |

| Previous total | New total | Previous verdict | New verdict |
|---:|---:|---|---|
| X/100 | X/100 | <verdict> | <verdict> |
```

---

## Step 8 — Update Section 10

Update Section 10.1 based on the comparison result.

* Close resolved questions.
* Mark answered questions as `Answered` if source is not updated yet.
* Mark questions as `Resolved` only when the report has enough stable information.
* Add new questions for new gaps/conflicts.
* Keep unresolved issues open.

Update Section 10.3 Audit Summary with:

* scoring table;
* blocker issues;
* major issues;
* recommendation.

Do not transfer questions from Audit Summary.

Section 10.1 remains the canonical source for question backlog sync.

---

## Step 9 — Write new audited report version

Create a new report:

```text
[UC-ID]_[feature-name]_audited_[YYYYMMDD]_v[N+1].md
```

Do not overwrite the previous report.

Append Section 11 Change log:

```md
| v<N+1> | <YYYY-MM-DD> | QC UC Read Agent | Re-audit: updated based on <question-backlog / document update / design update / feedback>. Changed sections: <list>. AC changes: added <n>, modified <n>, deleted <n>. |
```

---

## Step 10 — Sync question backlog

After writing the new report, sync only Section 10.1 changes:

* add new open questions;
* update statuses for existing questions;
* attach stakeholder answers when available;
* do not duplicate existing Q-IDs;
* do not sync from Audit Summary.

---

## Boundaries

* Re-audit uses the current audited report as the old baseline.
* Re-audit does not run first-audit again.
* Modes only define what input to read.
* Always compare changed input against current audited content.
* Always report what was added, modified, and deleted.
* Always report AC changes explicitly.
* Do not read all raw artefacts unless the user provides them as changed input.
* Do not treat question-backlog answers as source documentation unless the answer says the source was updated.
* Do not overwrite previous audited reports.

---
## Final Status Update & Cleanup

Per `workflows/checkpoint-protocol.md` §5 and §6:

1. **Worklog**: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`. Add `uc-review-report v[N+1].md` to `output`. If Step 10 updated the question-backlog, also add it to `output`.
2. **Cleanup**: delete the entire `.claude/skills/qc-uc-read/process-logging/<UC-ID>/` folder. Cleanup only happens on successful completion.