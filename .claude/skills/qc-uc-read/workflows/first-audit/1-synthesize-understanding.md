# First Audit · Phase 1 — Synthesize Requirement Understanding

> **Friendly name (for worklog):** `Synthesizing Requirement Understanding` (EN) / `Tổng hợp hiểu biết requirement` (VI).
>
> **Inputs:** UC document(s), design images, supporting artefacts (API spec, BPMN, etc.), common reference files.
>
> **Output checkpoint:** `process-logging/<UC-ID>/01_synthesis.md` — §A–§E (raw evidence) written at Step 1.7, §F (synthesized 5 sub-sections) appended at Step 2.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).

---

## Step 1 — Read Artefacts and Build Review Context

Before scoring, rewriting, or judging anything, read all provided artefacts and build a lightweight review context.

The purpose of this step is to understand where the UC fits in the overall project and to collect supporting evidence for later reconstruction and Phase 2 cross-checks.

Do **not** score, rewrite, or judge the UC in this step.

---

### 1.1 Route input files before reading

Before reading any artefact, determine the input type and use the correct extraction method.

| Input type              | Action                                                                                                          |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| PDF provided            | Invoke the `pdf` skill to extract text, tables, and images first. Do not read the PDF directly as plain text.   |
| DOCX provided           | Invoke the `docx` skill to extract text, tables, and images first. Do not read the DOCX directly as plain text. |
| File path provided      | Read the file using the appropriate tool based on file type.                                                    |
| Image file provided     | Use visual reading and extract visible UI evidence.                                                             |
| HTML prototype provided | Read prototype source and extract observable UI evidence.                                                       |
| Pasted text provided    | Treat it as a document and parse directly from the prompt.                                                      |

Apply this routing rule to every file used in Step 1, including UC files, context files, site-map files, common files, and design artefacts.

---

### 1.2 Read project-level context

Read the `project-context-master` file, resolved via `path-registry.md`.

Use this file to understand the overall project context, including:

* product / business domain
* target users and user groups
* major modules or feature areas
* key business goals
* global assumptions, constraints, and terminology

Keep only the information needed to understand the UC in the broader project picture.

If the file is missing, skip it and warn the user once.

---

### 1.3 Read site-map / screen-flow context, if available

Read the `qc-site-map` file, resolved via `path-registry.md`, to identify:

* screens related to the UC’s feature
* navigation flows touching those screens
* roles allowed to access those screens
* features mapped to those screens

If the site-map file is missing, skip it and warn the user once.

---

### 1.4 Read common input-format rules

Read:

`.claude/skills/qc-uc-read/references/input-files-format.md`

This file lists the structure of all BA input artefacts and — most importantly — the identifier prefixes used across the project (e.g., `COMMON-*`, `BR-*`, `RULE-*`, `BP-*`, `QA-*`, `MSG_*`, `ERR_*`). Use it for two purposes only:

1. **Reference recognition.** Knowing the full prefix list lets Step 1.5 extract every referenced identifier in the UC without missing any prefix family.
2. **Sub-agent A grounding.** Pass the relevant prefix list and common-file structure into Sub-agent A's prompt at 1.6 so it knows what to scan for and how each common file is organized.

Do not score the UC after reading this file.

---

### 1.5 Read the detailed UC document

Read each provided UC file or pasted UC content fully.

At this step, only capture enough information to identify the review target and support later extraction, including:

* UC ID and UC name
* related feature / module
* actors or roles mentioned
* main sections available in the UC
* referenced screens, rules, messages, APIs, data fields, or external artefacts

Do not list, rewrite, or normalize all UC objects here.

Detailed UC objects, flows, rules, messages, validations, and data fields will be reconstructed in later steps.

---

### 1.6 Parallel sub-agent fan-out

Launch the following independent read-only sub-agents in parallel.

Use a **single message with multiple `Agent` tool calls in the same `<function_calls>` block**.
Do **not** await one sub-agent before invoking the next.

These sub-agents have no data dependency on each other.

Only after all launched sub-agents return, continue to Step 1.7.

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

---

### 1.7 Write Step 1 output to the checkpoint file

Write §A–§E directly to `.claude/skills/qc-uc-read/process-logging/<UC-ID>/01_synthesis.md`. **Always overwrite** if the file exists (first-audit is idempotent on re-run).

Use this exact structure:

````markdown
# Phase 1 Synthesis — <UC-ID>

## Working notes
- UC-ID / name / input language
- Source files with version
- Blocked or missing artefacts (or `none`)
- Generated at <ISO timestamp> by qc-uc-read · first-audit · Phase 1

## §A. Project & site-map context
- A.1 Project context (from Step 1.2) — scoped to this UC
- A.2 Site-map context (from Step 1.3) — related screens, navigation, roles, mapped features

## §B. UC identity & raw reference list (from Step 1.5)
- UC ID / UC name
- Input language
- Source UC file(s)
- Related feature / module
- Artefacts detected for this UC: common files / API / BPMN / design / prototype / site-map
- Notes for downstream extraction: none / <only routing notes>

## §C. Resolved common rules & messages (Sub-agent A — verbatim table, includes NOT_FOUND rows)

## §D. HTML prototype UI evidence (Sub-agent B — verbatim)

## §E. Image design UI evidence (Sub-agent C — verbatim)

## §E2. ASCII screen UI evidence (Sub-agent D — verbatim)
````

For any section whose source did not run or is missing, write `Not applicable — <reason>.` Do not omit the heading.

Leave a trailing `---` after §E so Step 2 can append §F cleanly. Do not write §F here.

---

### 1.8 Step 1 guardrails

During Step 1:

* Do not score the UC.
* Do not rewrite the UC.
* Do not judge whether a gap or conflict is a defect.
* Do not infer missing requirements.
* Do not translate source content unless explicitly requested.
* Do not invent common rules, messages, UI states, or design behavior.
* Warn only once for each missing optional artefact type.
* Use `synthesize`, not `synthesise`, for spelling consistency.

---

## Step 2: Synthesize a Feature Understanding

Append §F to `01_synthesis.md` (file created in Step 1.7). Do not overwrite §A–§E. Do not create a new file.

Follow `qc-writting-rules.md` (MANDATORY). Re-number Section 1–5 below as §F.1–§F.5 in the output.

### §F.1 UI Element Extraction and Cataloging

Extract and catalog all User Interface (UI) elements based on the design data extracted by Sub-agent B and Sub-agent C, and map them to their corresponding descriptions in the use case document.

**Granularity Rules (MANDATORY):** Every single basic UI element MUST have its **own dedicated row**. DO NOT group multiple input fields, buttons, or columns into a single row (e.g., DO NOT write "Part I: 9 API fields" — you must list each field individually). Each row MUST contain:

- **Exact Label:** Exactly as displayed on the screen (Verbatim in Vietnamese/English — do not paraphrase). If there is a discrepancy between the design and the document, prioritize the design label.
- **Component Type:** (e.g., Text Input / Number Input / Dropdown Menu / Date Picker / Radio Button / Checkbox / Text Area / Button / Icon / Table Column / Tab / Tooltip / Alert / Popup / etc.)
- **Mandatory Flag:** (`*` shown in design = Mandatory; no `*` = Optional)
- **Default Value:** (If pre-filled or if a default suggestion is displayed)
- **Placeholder Text:** (The exact background text inside the input field)
- **Enumerated Values:** (For Dropdowns/Radio Buttons/Checkboxes — you must list **all** exact options as displayed; do not use abbreviations like "(N values)")
- **Section / Sub-section Group:** (e.g., "Section I > Investor #1")
- **Discrepancies / Missing Elements:** Note any inconsistencies, mismatches, or missing items between the use case document and the design (images, prototype).

Categorize the elements *after* listing them individually, not before:

- **Data Display Structures (Grid/List/Table):** For each table, list **every column** as a separate row (maintain multi-level header hierarchy if applicable). Identify pagination limits, default sorting, and the exact Empty State text as per the design.
- **Control Systems (Filters/Search Fields):** Each filter/search field MUST be a separate row. Record its initial state, the complete list of dropdown values, and any input constraints.
- **Navigation and Action Elements (Buttons/Controls):** Each button/icon MUST be a separate row, including inline action icons within table rows (Edit/Delete/View/Export/Print/etc.).
- **Other Elements:** Page titles, subtitles, suggestion banners, breadcrumbs, tooltips, badges, status chips, empty state messages, loading indicators — each element MUST be a separate row.

**Self-Verification before completing this step:** For each design image or prototype provided, count the total number of visible UI elements. The number of rows generated in this section that are mapped to that image MUST be greater than or equal to your visual count. Log any numerical discrepancies in your working notes; if any elements were collapsed or grouped in your output, immediately flag them and expand them into individual rows.

### §F.2 Definition of Object Attributes and Behaviors

Determine the state and response of each UI object based on specific system conditions.

**1-to-1 Mapping Rule (MANDATORY):** §F.2 MUST contain **at least one row for every UI element listed in §F.1**. If a UI element has no special behavior, it MUST still be listed with `System State = "Enabled (no special behavior)"` and `Behavior = "N/A"` — DO NOT skip it. Never group multiple elements into a single row (e.g., DO NOT write "Phone, Email" as one row — split them into two separate rows).

**Content Extraction Rule (MANDATORY):** The content of rule codes, validation messages, or error alerts mentioned in the document MUST be replaced with the specific, detailed content already reported by Sub-agent A. If Sub-agent A returns `NOT_FOUND`: keep the original code as written in the UC, append `(NOT_FOUND in common files)`, and do not invent content.

- **System State:** Define the default state of the object (Enabled, Disabled, Hidden, Read-Only) based on variables such as: account privileges (Permissions), input data conditions, or the current data state of the system.
- **Interaction Matrix:** Define the possible interactive actions and their corresponding system responses for each object. Use vocabulary strictly from the use case specification document, such as: Click, Hover, Drag and Drop, Right-click, Keyboard shortcuts. For native mobile apps, use: Tap, Long Press, Swipe, Pull to Refresh, Pinch to Zoom, Hardware Back (Android), Edge Swipe Back (iOS).
- **Object Behavior:** Define exactly how the object reacts to data changes or state changes in other related UI objects.

### §F.3 Functional Logic & Workflow Decomposition

Analyze in detail the business processes of each function available on the feature screen, such as view list, filter, search, create, view detail, edit, delete, export, etc.

- **Workflows:**
  - **Main Flow (Happy Path):** The correct execution flow that produces no errors or exceptions.
  - **Alternative Flows:** Alternative execution paths that lead to a successful outcome.
  - **Exception & Error Flows:** Scenarios involving system errors or invalid data.
- **Business Rules & Validations:** Synthesize the business rules regarding format constraints, value ranges, and mandatory fields.
- **UI/UX Feedback:** Specify system notifications (Toast messages), error codes, and loading states corresponding to each process.

### §F.4 Functional Integration Analysis

Analyze and evaluate the linkages and influences between the cataloged functions, acting as an integration check between functions.

- **Impact Analysis:** Determine whether a change in state or data within one function directly or indirectly affects other functions.
- **Data Consistency:** Verify the synchronization of data across all related UI components after a function is executed.

### §F.5 Acceptance Criteria Candidates for User Confirmation

Purpose:
- Synthesize testable AC candidates from §F.1–§F.4.
- Use these AC candidates as a review aid only.
- Do not treat synthesized AC as source requirement.
- Do not use absence of source AC as a scoring penalty in Phase 2.

Each row must include:
- AC candidate
- Type: UI / Functional / Integration
- Trace: §F.X + source artefact
- Confirmation status: Needs user confirmation
- Source status: Verbatim from UC / Synthesized from understanding

Each AC row should be self-contained per `qc-writting-rules.md` C2 and include the source tag.

---

## Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §4:

1. Verify `01_synthesis.md` contains §A through §F. If §F is missing, Step 2 did not complete — do not proceed.
2. Update `progress.md` → `last_phase_done: 1`, `next_phase: 2`, `updated_at: <now>`.
3. Worklog: rewrite last entry → `status = "Phase 1 done"`.

---

## Hand-off to Phase 2

Next file: `workflows/first-audit/2-score-and-identify-gaps.md`. It reads `01_synthesis.md` from the checkpoint folder and scores the 10 knowledge areas using the rubric in `references/scoring-rubric.md`.



