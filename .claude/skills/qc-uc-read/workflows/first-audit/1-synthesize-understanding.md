# First Audit · Phase 1 — Synthesize Requirement Understanding

> **Friendly name (for worklog & dashboard):** `Synthesizing Requirement Understanding` (EN) / `Tổng hợp hiểu biết requirement` (VI).
>
> **Inputs:** UC document(s), design images, supporting artefacts (API spec, BPMN, etc.), common reference files.
>
> **Output checkpoint:** `process-logging/<UC-ID>/01_synthesis.md` — contains the 5 synthesis sections + Section 4 inventory with `Delta = 0` coverage verified.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Synthesizing Requirement Understanding` (use the input UC's language — see protocol §3 phase friendly names table). Skip if column missing (graceful degradation).

---

## Step 1: Read all artefacts

- Read the `project-config` file (resolved via `path-registry.md` → `docs/qc-lead/project-config.md`) — **§ 2. Project Context** section to understand the project context.
- Read the common files first — Read `.claude/skills/qc-uc-read/references/input-files-format.md` to understand the input file's structure and to ensure that you understand all the common rules and the project context.

**Common Reference Resolution rule (MANDATORY):** When the source UC references a common-file entry by code/ID/name (e.g., `MSG_E001`, `BR_xxx`, the name of a common function), do NOT leave the bare code in the audit output. Open the corresponding common file, copy the **exact original text** (message wording, full rule statement, function description), and inline that text into the audit section that uses it (Section 6.1.B Business Rules, 6.1.C Error Codes / Toast Messages, Section 3 Preconditions if a common function is reused, etc.). Preserve the original code in parentheses for traceability — e.g., `"New user created successfully." (MSG_E001)`.
This is so test cases written downstream from the audit file have the exact verbatim message/rule text in `Expected Result` without re-opening the common docs.

- Then read each provided UC file or pasted content fully before scoring anything.
- **Site-map cross-check (optional input):** if `qc-site-map` exists, read §5 Screen/Page inventory + §6 Navigation & screen flow + §7 Role/access by screen + §8 Screen ↔ Feature mapping. Hold in working memory: (a) screens mapped to the UC's feature in §8, (b) flows in §6 touching those screens, (c) roles in §7 with access. These feed Phase 2 KA #3/#4/#7 gap detection and the Cross-Artefact Conflict Check. If missing, skip and warn once.

### Input-type routing

| Input type           | Action                                                                                                          |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| PDF provided         | Invoke the `pdf` skill to extract text, tables, images first. Do NOT use the Read tool directly on PDF files.   |
| DOCX provided        | Invoke the `docx` skill to extract text, tables, images first. Do NOT use the Read tool directly on DOCX files. |
| File path provided   | Read the file using the appropriate tools.                                                                      |
| Image file provided  | Use the Read tool — it renders images inline; describe all visible UI elements, labels, states, and flows in detail. |
| Pasted text provided | Treat as a document; parse directly from the prompt.                                                            |

### Supported artefact types

Accept any combination of:

| Type                        | Examples                                           |
| --------------------------- | -------------------------------------------------- |
| Requirements / Use Case doc | UC spec, feature brief, BRD, user story            |
| UI Design / Wireframe       | Figma export, mockup image, screen flow PDF        |
| API Specification           | REST API doc, Swagger/OpenAPI, integration spec    |
| Business Process doc        | Workflow diagram, BPMN, process description       |
| Design document             | Technical design, system design, architecture note |
| Other supporting docs       | Data dictionary, error code list, email templates  |

All file formats are supported: plain text, Markdown, PDF, Word (.docx), images (PNG/JPG).

---

## Step 2: Synthesise a Feature Understanding

After fully comprehending all provided documents and analyzing the design images (including any screen mockups embedded within the specification documents), proceed to synthesize the requirement content according to the following 5 sections:

### 1. UI Object Inventory & Mapping

Extract and catalog all user interface components based on the Design Mockup and map them correspondingly to the Functional Specification document.

**Granularity rule (MANDATORY):** Every atomic UI element gets **its own row** in Section 4. Do NOT collapse multiple inputs/buttons/columns into one row (e.g., do NOT write "Phần I: 9 API fields" — list each field individually). Each row MUST capture:

- **Exact label** as shown on the screen (Vietnamese/English original — no paraphrase)
- **Component type** (Text input / Number input / Dropdown / Date picker / Radio / Checkbox / Textarea / Button / Icon / Table column / Tab / Tooltip / Toast / Popup / etc.)
- **Required flag** (`*` shown in design = Required; absence of `*` = Optional)
- **Default value** (if pre-filled or hint shown)
- **Placeholder text** (exact text inside the input)
- **Enum values** (for Dropdown/Radio/Checkbox — list **all** options exactly as shown, no "(N values)" shorthand)
- **Section / sub-section grouping** (e.g., "Phần I > Nhà đầu tư #1")

Categorize after enumeration, not before:

- **Data Display Structure (Grid/List/Table):** For every table, list **every column** as a separate row (preserve multi-level header hierarchy). Identify pagination limit, default sorting, and Empty state text exactly as designed.
- **Control System (Filters/Search Fields):** Each filter/search field is its own row. Capture initial state, full list of dropdown values, and input constraints.
- **Navigation and Action Components (Buttons/Controls):** Each button/icon is its own row, including action icons inside table rows (Edit/Delete/View/Export/Print/etc.).
- **Other components:** page title, subtitle, hint banner, breadcrumb, tooltip, badge, status chip, empty-state message, loading spinner — each as its own row.

**Self-check before finishing this step:** For each design image, count the visible atomic UI elements. The number of rows in Section 4 mapped to that image must be ≥ that count. Record the count delta in your working notes; if any element is collapsed/grouped, flag and re-expand.

### 2. Object Attributes & Behavior Definition

Determine the state and response of each UI object based on specific system conditions.

**1-to-1 mapping rule (MANDATORY):** Section 5 MUST contain **at least one row for every row in Section 4**. The set of "Object / Component" names in Section 5 must equal or be a superset of the names in Section 4. If a UI element has no special behavior, still list it with `System States = "Enabled (no special behavior)"` and `Behavior = "N/A"` — do NOT omit it. Never group multiple Section-4 components into a single Section-5 row (e.g., do NOT write "SĐT, Email" as one row — split into two).

- **System States:** Define the default state of the object (Enabled, Disabled, Hidden, Read-only) based on variables such as: account privileges (Permissions), input data conditions, or the current data state of the system.
- **Interaction Matrix:** Specify the possible interaction actions and the corresponding system responses for each object. Use platform-appropriate vocabulary based on `project-context-master.md` §1 Product Platform Type — web/desktop: Click, Hover, Drag & Drop, Right-click, keyboard shortcuts; mobile native: Tap, Long-press, Swipe, Pull-to-refresh, Pinch-zoom, Hardware back (Android), Swipe-back-edge (iOS).
- **Object Behavior:** Define how the object reacts when there is a data change or a state change in related objects.

### 3. Functional Logic & Workflow Decomposition

Analyze in detail the business processes of each function available on the feature screen, such as view list, filter, search, create, view detail, edit, delete, export, etc.

- **Workflows:**
  - **Main Flow (Happy Path):** The correct execution flow that produces no errors or exceptions.
  - **Alternative Flows:** Alternative execution paths that lead to a successful outcome.
  - **Exception & Error Flows:** Scenarios involving system errors or invalid data.
- **Business Rules & Validations:** Synthesize the business rules regarding format constraints, value ranges, and mandatory fields.
- **UI/UX Feedback:** Specify system notifications (Toast messages), error codes, and loading states corresponding to each process.

### 4. Functional Integration Analysis

Analyze and evaluate the linkages and influences between the cataloged functions, acting as an integration check between functions.

- **Impact Analysis:** Determine whether a change in state or data within one function directly or indirectly affects other functions.
- **Data Consistency:** Verify the synchronization of data across all related UI components after a function is executed.

### 5. Acceptance Criteria (AC) Synthesis

Establish the final set of measurement and evaluation standards regarding the completeness of the requirement.

- **Establishing Acceptance Criteria (AC):** Categorize and detail the acceptance criteria for each group: Interface (UI), Function, and Integration.

---

## Step 3: UI Coverage Self-Verification (mandatory before exiting Phase 1)

Before exiting Phase 1, do a coverage audit of Section 4 against every design image:

1. For each design image in the input set, count `elements_in_image` — the visible atomic UI elements (every input, dropdown, radio option, checkbox, button, action icon, table column, table row label, tab, tooltip, badge, chip, page title, subtitle, hint banner, empty-state message, toast, popup).
2. Count `rows_in_section_4` — Section 4 rows whose `Source` column references that image.
3. Record a delta table in working notes:

   | Image | elements_in_image | rows_in_section_4 | Delta | Action |
   |-------|-------------------|-------------------|-------|--------|
   | *(filename)* | *(N)* | *(M)* | *(N − M)* | *(if Delta > 0: enumerate the missing elements and add rows; if Delta < 0: review for fabricated elements)* |

4. Loop until `Delta == 0` for every image. Only then proceed to Phase 2.
5. If a design image cannot be opened or rendered, mark Section 4 row `[BLOCKED: <filename> not accessible]` and surface as Blocker — do NOT skip the image silently.

---

## Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §5:

1. **Write checkpoint file** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/01_synthesis.md` with:
   - The 5 synthesis sections (full content)
   - The UI coverage delta table (must show `Delta = 0` for every image)
   - Working notes: detected input language, UC-ID, version of source files read, list of blocked artefacts (if any)
2. **Update `progress.md`** → `last_phase_done: 1`, `next_phase: 2`, `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`.
4. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Synthesizing Requirement Understanding done` (skip if column missing).

---

## Hand-off to Phase 2

Next file: `workflows/first-audit/2-score-and-identify-gaps.md`. It reads `01_synthesis.md` from the checkpoint folder and scores the 10 knowledge areas using the rubric in `references/scoring-rubric.md`.
