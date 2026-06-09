# Format of input files

> Reference for the structure of all BA input artifacts that the `qc-uc-read` skill consumes.
> All BA artifacts live under `docs/BA/`. Common (cross-UC) artifacts are in `docs/BA/common/`.
> Per-UC artifacts are in `docs/BA/<UC-ID>/`.

---

## 1. Common artifacts — `docs/BA/common/`

Files in this folder are shared across the whole project and apply to every UC.

### 1.1 `common-rules.md`

- **Type:** Catalogue of cross-cutting rules (`COMMON-xxx`) applied to every UC in the project: input constraints, UI/UX behaviors, data standards, error handling, file upload, security, accessibility, pagination & lists.
- **File name:** `common-rules.md` (single canonical file; no version suffix).
- **Language:** English content; rules must be quoted verbatim from this file when referenced from a UC.

#### Document structure

The document is divided into 3 main parts:

1. **Header block** — `Generated`, `Last Updated`, `Managed by` metadata.
2. **Summary table** — counts of `Active` / `Deprecated` / `Total` rules per category.
3. **Rules by Category** (`## Rules by Category`) — one `###` subsection per category.
4. **Changelog** — append-only log of rule additions/modifications.

#### Rule table format

Inside each `###` category subsection, rules are listed in a table with the following columns:

| Column      | Meaning                                                                 |
| :---------- | :---------------------------------------------------------------------- |
| `ID`        | `COMMON-xxx` (3-digit zero-padded, globally unique across all categories) |
| `Rule`      | The rule statement (verbatim — used directly as a reference in UC docs) |
| `Rationale` | Reason / justification for the rule                                      |
| `Source`    | `Initialized`, `Initialized (modified)`, `User-defined`                  |
| `Status`    | `Active` / `Deprecated`                                                  |

#### Standard categories

`Input Constraints`, `UI/UX Behaviors`, `Data Standards`, `Error Handling`, `File Upload`, `Security & Authentication`, `Accessibility`, `Pagination & Lists`.

#### Reference rule

When a UC quotes a `COMMON-xxx` rule, it MUST match the `Rule` text in this file exactly (any deviation = a UC override and must be flagged in the audit).

---

### 1.2 `business-processes.md`

- **Type:** End-to-end business processes (`BP-xxx`) of the project. Each `BP` is a high-level workflow that spans multiple UCs.
- **File name:** `business-processes.md`.
- **Purpose:** Provides the macro context (objective, actors, activity flow, state lifecycle) that lets each UC be understood as a step inside a larger process.

#### Document structure

1. **Header** — `Generated`, `Source files`, `Traceability Matrix`, `QA Backlog`.
2. **One `## BP-xxx: <Process Name>` section per process.** Each section contains:
   - **Metadata block** — `Objective`, `Actors`, `Source` (section refs in the source SRS), `Related BRs` (list of `BR-xxx`), `Related Rules` (list of `RULE-xxx`).
   - **Activity Flow** — a `mermaid flowchart TD` diagram showing the happy path and decision points.
   - **Activity Detail** — table with columns: `Step | Actor | Description | Rule | Notes`.
   - **(Optional) Status Lifecycle** — a `mermaid stateDiagram-v2` if the process introduces a stateful entity.
   - **(Optional) State Detail** — table with columns: `State | Description | Entry Condition | Exit Condition | Actor`.
3. **Changelog** at the bottom.

#### Cross-reference codes used inside `BP-xxx`

- `BR-xxx` → Business requirement (defined in `requirement-traceability.md`).
- `RULE-xxx` → Business rule (defined in `requirement-traceability.md`).
- `COMMON-xxx` → Common rule (defined in `common-rules.md`).
- `QA-xxx` → Resolved question (from QA Answers / meeting transcript files).

---

### 1.3 `usecase-list.md`

- **Type:** Master index of all use cases in the project, grouped by Business Process.
- **File name:** `usecase-list.md`.
- **Purpose:** Single source of truth for the **list of UCs**, their **scope**, and their **mapping to BR/RULE**. The detailed spec of each UC lives in its own `docs/BA/<UC-ID>/<UC-ID>.md` file.

#### Document structure

1. **Header** — `Generated`, `Source` (links to `business-processes.md`, `requirement-traceability.md`).
2. **Summary table** — counts of UCs per category.
3. **One `## N. <Category Name>` section per BP**, with a quote line `> Source: BP-xxx | Actors: <...>` and a UC table.
4. **Changelog** at the bottom.

#### UC table format

Each category section contains a table with the following columns:

| Column                  | Meaning                                                                  |
| :---------------------- | :----------------------------------------------------------------------- |
| `UC ID`                 | `UC-<MODULE>-<###>` (e.g. `UC-VOB-001`, `UC-PLA-001`, `UC-COC-001`)     |
| `Name`                  | Short imperative name (e.g. "Submit Vendor Registration")                |
| `Description`           | One-paragraph summary of what the UC does                                |
| `Pre-condition`         | What must be true before the UC starts                                   |
| `Post-condition`        | What must be true after the UC succeeds                                  |
| `Trigger`               | Event that starts the UC                                                 |
| `Business Requirements` | List of `BR-xxx` codes                                                   |
| `Business Rules`        | List of `RULE-xxx` and/or `COMMON-xxx` codes                             |

#### UC ID convention

`UC-<MODULE>-<###>` where `<MODULE>` is a 3-letter category code (e.g. `VOB` = Vendor Onboarding, `PLA` = Product Listing & Approval, `COC` = Customer Order & Checkout, `OFS` = Order Fulfillment & Status, `RRF` = Returns & Refunds, `CMS` = Commission & Settlement, `CLY` = Customer Loyalty, `ERP` = ERP Integration). The 3-digit `###` is zero-padded and unique inside the module.

---

### 1.4 `project-context_<YYYYMMDD>_v<N>.md`

- **Type:** Per-engagement synthesis of the rules and stakeholders relevant to **the current scope** of work. It is generated once per engagement and bumped (`v2`, `v3`, …) whenever the source rules in `common-rules.md` / `requirement-traceability.md` change.
- **File name pattern:** `project-context_<YYYYMMDD>_v<N>.md` (date = the date the synthesis was built; `v<N>` increments on rebuild).
- **Versioning:** Immutable — never overwrite; create a new versioned file (`v2`, `v3`, …) when content changes.

#### Document structure

1. **YAML frontmatter** with at minimum:
   - `version` — integer (`1`, `2`, …).
   - `created` — `YYYY-MM-DD`.
   - `created-by` — agent / mode that produced the file (e.g. `qc-member#1 (via get-requirement, mode=first-build)`).
   - `project` — project name + scope of the current engagement.
   - `source-files-ingested` — list of source files with their date + counts (e.g. `docs/BA/common/common-rules.md (2026-04-13, 58 active rules)`).
2. **`# Project Context — v<N>`** title.
3. **Numbered sections** (typical layout — order may vary by engagement, but section coverage must be comprehensive):
   - `## 1. Phạm vi dự án` — project name, primary actors/personas, current engagement scope (which UCs are in/out).
   - `## 2. Common Rules (COMMON-xxx → COMMON-yyy)` — every active common rule, with a column "Áp dụng cho UC nào" listing which UCs in the engagement use it (and any UC-level overrides).
   - `## 3. Business Rules (BR-)` — engagement-relevant BRs only.
   - `## 4. Business Rules (RULE-)` — engagement-relevant RULEs only.
   - `## 5. Stakeholders & Personas` — engagement-specific roles.
   - `## 6. Cross-reference codes — quick lookup` — what `COMMON-xxx`, `BR-xxx`, `RULE-xxx`, `QA-xxx`, `UC-XYZ-xxx` mean and which file defines them.
   - `## 7. Ngôn ngữ & quy ước artifact` — language conventions, REQ-ID / TC-ID format, date format.
   - `## 8. Open assumptions / project-level gaps` — table `ID | Item | Owner` of unresolved items at the project level.
4. **Changelog** at the bottom.

#### Note for `qc-uc-read`

When the most recent `project-context_*_v*.md` is present, the audit MUST treat it as the **authoritative summary** of `COMMON-*`, `BR-*`, `RULE-*` for the current engagement. Only fall back to opening `common-rules.md` / `requirement-traceability.md` when a referenced code is missing from `project-context`.

---

## 2. Per-UC artifact — `docs/BA/<UC-ID>/<UC-ID>.md`

Each UC has its own folder under `docs/BA/`, named exactly with the UC ID (e.g. `docs/BA/UC-VOB-001/`). The folder contains:

- `<UC-ID>.md` — the UC specification (the file `qc-uc-read` audits).
- Screen asset images (PNG) referenced from inside the spec.

### 2.1 File naming

- Spec file: `<UC-ID>.md` (e.g. `UC-VOB-001.md`).
- Screen assets: free-form PNG names (e.g. `image.png`, `individual.png`, `business.png`, `file-uploaded.png`, `image copy.png`, `image copy 2.png`, …) — referenced from the spec via blockquote lines `> Screen asset: docs/BA/<UC-ID>/<filename>.png`.

### 2.2 Document structure

The UC spec MUST contain the following sections, in order:

#### Header block (top of file)

```markdown
# <UC-ID>: <Use Case Name>

> Source: [usecase-list.md](../../usecase-list.md), [common-rules.md](../../common-rules.md), [requirement-traceability.md](../../requirement-traceability.md), [<other source>](../../<other-source>.md)
> Screen Asset: docs/BA/<UC-ID>/<filename>.png
> Screen Assets: (multiple — one bullet per screen state)
> - docs/BA/<UC-ID>/<file1>.png — SC-XXa: <state name>
> - docs/BA/<UC-ID>/<file2>.png — SC-XXb: <state name>
```

#### Section 1 — `## 1. Use Case Description`

A single 2-column table (`| Field | Description |`) with the following rows in order:

| Field                | Required content                                                                                              |
| :------------------- | :------------------------------------------------------------------------------------------------------------ |
| `**ID**`             | UC ID, exactly matching the filename and folder name.                                                          |
| `**Use Case**`       | Use case name (matches `usecase-list.md` Name column).                                                         |
| `**Description**`    | "As a `<actor>`, I want to `<goal>`, so that `<benefit>`." (user-story style).                                 |
| `**Pre-conditions**` | Bulleted list using `<br>` and `-` markers inside the table cell.                                              |
| `**Trigger**`        | One-sentence description of the event that starts the UC.                                                      |
| `**Post-conditions**`| `**On Success:** …` and `**On Failure:** …` (when applicable). Bulleted list with `<br>` separators.           |
| `**Basic Flow**`     | Numbered steps (1, 2, 3 …) separated by `<br>`. Each step references `[COMMON-xxx]`, `[RULE-xxx]`, `[QA-xxx]` inline. |
| `**Alternative Flow**`| Multiple sub-flows, each headed by `**[<Sub-flow Name>]**` followed by numbered steps. `<br><br>` between sub-flows. |
| `**Business Rules**` | Bulleted list of `[BR-xxx]` and `[RULE-xxx]` references with the rule text quoted verbatim and a short context sentence. |

#### Section 2 — `## 2. Screen Description`

One `### Screen SC-<##><letter>: <Screen Name>` subsection per screen state.

Each screen subsection contains:

1. **Asset reference** — `> Screen asset: docs/BA/<UC-ID>/<filename>.png`.
2. **`#### Layout Overview`** — prose describing the visual structure of the screen (header, body, footer, columns, grouping).
3. **Element table** — columns:

| Column        | Meaning                                                                                              |
| :------------ | :--------------------------------------------------------------------------------------------------- |
| `#`           | Sequential number on the screen (1, 2, 3 …).                                                          |
| `Name`        | Element label as shown to the user (in **bold**).                                                    |
| `Type`        | UI control type (`Text Input (single-line)`, `Radio Button Group`, `Wizard / Stepper`, `File Upload (drop zone)`, `Button (Primary CTA)`, `Toast / Snackbar`, `Inline Error Text`, `Static Text / Heading`, etc.). |
| `Description & Behavior` | Two-block content with `**Display Rules:**` and `**Behaviors:**` headings. Each block uses `<br>` line breaks and `-` bullets inside the cell. References cite codes inline as `[COMMON-xxx]`, `[RULE-xxx]`, `[QA-xxx]`. |

#### Section 3 — `## 3. Validation Summary`

Tabular summary of every field with validation rules. Standard columns:

`Field | Required | Format Rule | Max Length | Error Messages`

For UCs with multiple sub-types (e.g. Individual vs Business vendor), provide one sub-table per type with `### <Subtype Name>` subheading.

#### Section 4 — `## 4. Cross-References`

Two-column table `| Reference | Type | Notes |` listing every external code referenced anywhere in the UC. Type values include:

- `Next Step` / `Previous Step` / `Downstream` / `Upstream` for UC-to-UC links.
- `Business Requirement` for `BR-xxx`.
- `Business Rule` for `RULE-xxx`.
- `Common Rule` for `COMMON-xxx`.
- `Resolved QA` for `QA-xxx`.

#### Section 5 — `## 5. Open Questions`

Table `# | Question | Status` of unresolved or recently-resolved questions about the UC. Status values:

- `Open` — pending answer; will be picked up by `qc-qna`.
- `Resolved: <answer> — <source>` — answer + source citation (e.g. `Vendor Onboarding QA Answers.csv [QA-021]`).

#### Section 6 — `## Changelog`

Append-only table `Date | Source | Changes | QA Resolved` recording every revision to the UC spec.

---

### 2.3 Inline reference codes — quick lookup

| Code prefix | Meaning                                | Defined in                                                          |
| :---------- | :------------------------------------- | :------------------------------------------------------------------ |
| `COMMON-xxx`| Cross-project common rule              | `docs/BA/common/common-rules.md`                                     |
| `BR-xxx`    | Business requirement                   | `docs/BA/common/requirement-traceability.md` (Business Requirements) |
| `RULE-xxx`  | Business rule                          | `docs/BA/common/requirement-traceability.md` (Business Rules)        |
| `BP-xxx`    | Business process                       | `docs/BA/common/business-processes.md`                               |
| `UC-<MOD>-xxx` | Use case                            | `docs/BA/<UC-ID>/<UC-ID>.md` (per-UC spec); index in `usecase-list.md` |
| `QA-xxx`    | Resolved BA question                   | QA Answers CSV / meeting transcript files referenced in the UC's Changelog |
| `SC-<##><letter>` | Screen state inside a UC         | The owning UC spec (Section 2)                                       |
| `OQ-N`      | Open question local to a UC            | The owning UC spec (Section 5)                                       |
