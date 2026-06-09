# First Audit · Phase 3 — Generate Review Report

> **Friendly name (for worklog & dashboard):** `Generating Review Report` (EN) / `Tạo báo cáo review` (VI).
>
> **Inputs:** `process-logging/<UC-ID>/01_synthesis.md` + `02_scoring.md` (Phase 1 & 2 outputs).
>
> **Output:** `uc-review-report v[N].md` written to the UC's output folder (resolved via `path-registry.md`). This file IS the final deliverable — no separate `03_*.md` checkpoint.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running (Phase 3)"`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Generating Review Report` (skip if column missing).

If this run is a **resume from Phase 3**: first load `01_synthesis.md` and `02_scoring.md` into memory per `checkpoint-protocol.md` §4 Resume load table.

---

## Step 1: Fill the UC Readiness Review Template

The report is based on the **UC Readiness Review Template** at `.claude/skills/qc-uc-read/templates/UC_readiness_review_template_v3.md`. Open the template file, fill every section based on what was found (or not found) in the provided artefacts.

**Section mapping (knowledge area → template section):**

| KA # | Knowledge Area                          | Template Section |
| ---- | --------------------------------------- | ---------------- |
| 1    | Feature Identity                        | Section 0        |
| 2    | Objective & Scope                       | Section 1        |
| 3    | Actors & User Roles                     | Section 2        |
| 4    | Preconditions & Postconditions          | Section 3        |
| 5    | UI Object Inventory & Mapping           | Section 4        |
| 6    | Object Attributes & Behavior Definition | Section 5        |
| 7    | Functional Logic & Workflow Decomposition | Section 6      |
| 8    | Functional Integration Analysis         | Section 7        |
| 9    | Acceptance Criteria                     | Section 8        |
| 10   | Non-functional Requirements             | Section 9        |

**Section 8 — Acceptance Criteria:** Based on the AC synthesis performed in Phase 1 Step 2 (item 5), populate Section 8 of the template with concrete Given/When/Then acceptance criteria derived from the analyzed workflows, business rules, and UI behaviors. Even if the source document lacks explicit AC, the agent MUST generate them from the synthesized understanding. Score this section based on the source document's AC, but always provide generated AC in the output.

**Status markers used throughout the report** (also defined in `references/scoring-rubric.md`):
- ✅ **Complete** — explicitly stated and unambiguous
- ⚡ **Partial** — present but vague, incomplete, or only inferred (half marks)
- ⚠️ **Missing** — absent from all provided artefacts (zero marks)
- *(inferred)* — the reviewer inferred information rather than finding it explicitly; these are candidates for confirmation before test design begins

---

## Step 2: Add the Audit Summary at the End

Append the **Audit Summary** section at the end of the report, with these subsections:

### Audit Summary Table

> **Note:** Knowledge area numbers map to template sections as follows:
> #1 → Section 0 · #2 → Section 1 · #3 → Section 2 · #4 → Section 3 · #5 → Section 4 · #6 → Section 5 · #7 → Section 6 · #8 → Section 7 · #9 → Section 8 · #10 → Section 9

Use the same Max Pts as in `references/scoring-rubric.md` (totals 130 → normalized to 100):

| #         | Knowledge Area                          | Max Pts | Score | Status      |
| --------- | --------------------------------------- | ------- | ----- | ----------- |
| 1         | Feature Identity                        | 5       | X/5   | ✅ / ⚡ / ⚠️ |
| 2         | Objective & Scope                       | 5       | X/5   | ✅ / ⚡ / ⚠️ |
| 3         | Actors & User Roles                     | 10      | X/10  | ✅ / ⚡ / ⚠️ |
| 4         | Preconditions & Postconditions          | 10      | X/10  | ✅ / ⚡ / ⚠️ |
| 5         | UI Object Inventory & Mapping           | 15      | X/15  | ✅ / ⚡ / ⚠️ |
| 6         | Object Attributes & Behavior Definition | 20      | X/20  | ✅ / ⚡ / ⚠️ |
| 7         | Functional Logic & Workflow Decomposition | 20    | X/20  | ✅ / ⚡ / ⚠️ |
| 8         | Functional Integration Analysis         | 20      | X/20  | ✅ / ⚡ / ⚠️ |
| 9         | Acceptance Criteria                     | 20      | X/20  | ✅ / ⚡ / ⚠️ |
| 10        | Non-functional Requirements             | 5       | X/5   | ✅ / ⚡ / ⚠️ |
| **Total** |                                         | **130** |       | **XX/130 → XX/100** |

### Unified Gap & Question Report

Synthesize all gaps, missing info, warnings, conflicts, and open questions from all analyzed sections into a single comprehensive table for the BA to review. Ensure there is no duplicated content.

**Mandatory inclusion — Platform-specific gaps:** Scan the Phase 2 KA evidence for any entries prefixed with `Platform-specific gap (<variant>):` (added per rubric § "Platform-Aware Gap Detection"). Each such marked gap MUST appear as its own row in this table, with `Ref` citing the KA + the source section, `Question` stating what platform-specific behavior the BA needs to clarify, and `Why It Matters` explaining the impact on test design for that platform variant. This is what makes the gap visible to `qc-qna` for auto-transfer to the question-backlog.

| ID            | Priority                  | Ref                                       | Question                          | Why It Matters                          | Status |
| ------------- | ------------------------- | ----------------------------------------- | --------------------------------- | --------------------------------------- | ------ |
| *(e.g., Q1)*  | *(High / Medium / Low)*   | *(Exact excerpt from requirement. Skip if Missing)* | *(Main content to clarify or fix)* | *(Why this is an issue, impact on testability)* | *(Open)* |

- **ID**: ID of the question (e.g., Q1, Q2)
- **Priority**:
  - **High**: Blockers (critical knowledge areas scoring 0, missing critical info).
  - **Medium**: Warnings, Cross-artefact conflicts, Partial/Vague details.
  - **Low**: Suggestions for improvement, minor open questions.
- **Ref**: Exact excerpt from the requirement that led to this question. If the issue is something completely missing, write "N/A (Missing)".
- **Question**: Clearly state what needs to be answered, provided, or corrected by the BA. Make sure to include the description of the issue as currently found.
- **Why It Matters**: Explain the specific reason for raising this question (e.g., impact on test design, potential bugs, data inconsistency).
- **Status**: Default to "Open".

### 🟢 What's Good

Briefly acknowledge what is well-documented. Give the author credit for what is ✅ Complete.

### 🧪 Testability Outlook

**What CAN be tested now:**

- [Test areas with enough information to start]

**What CANNOT be tested yet (blocked by gaps):**

- [Test areas blocked by ⚠️ Missing or ⚡ Partial sections]

**Suggested test focus areas** *(once gaps are resolved)*:

- Happy path: [based on Section 5. Object Attributes & Behavior Definition]
- Alternative scenarios: [based on Section 5. Object Attributes & Behavior Definition]
- Boundary & validation tests: [based on Section 5. Object Attributes & Behavior Definition]
- Error & exception scenarios: [based on Section 5. Object Attributes & Behavior Definition]
- UI-specific checks: [based on Section 5. Object Attributes & Behavior Definition, if design/wireframe was provided]

### 📌 Summary & Recommendation

One paragraph: overall state of the artefact set, key actions required, and a clear recommendation — hold until fixed / fix specific items and proceed / proceed now.

---

## Step 3: Write the Output File

Resolve the output path via `path-registry.md` → `uc-review-report` logical name.

**Versioning rule:** Check the output directory for existing versions. If `v[N]` exists, increment the version to `v[N+1]`. **Never overwrite existing files.**

**Naming convention** (per `.claude/rules/naming-convention.md`):
```
[UC-ID]_[feature-name]_audited_[YYYYMMDD]_v[N].md
```

Write the completed report to the resolved path.

---

## Step 4: Transfer Open Questions to Question Backlog (auto-trigger `qc-qna`)

After the `uc-review-report v[N].md` is written successfully, **invoke the `qc-qna` skill via the Skill tool** to transfer all `Open` rows from the report's `### 📋 Unified Gap & Question Report` table into the project's `question-backlog` file (so the BA can answer them).

- Pass the just-written report path + `<UC-ID>` as input context.
- Wait for `qc-qna` to return. Capture its summary (new question IDs created, file path of the backlog).
- If `qc-qna` reports no Open questions to transfer, skip silently.
- If `qc-qna` fails, do NOT block this skill — surface a warning in chat (`⚠️ qc-qna failed: <reason> — please run /qc-qna manually for <UC-ID>`) and continue to Final Status Update.

This auto-trigger is the documented kit flow: first-audit always produces fresh Open questions; sending them directly to the BA's backlog removes a manual step.

---

## Final Status Update & Cleanup

Per `workflows/checkpoint-protocol.md` §5 and §6:

1. **Worklog**: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`. Add the output file name to `output`. If `qc-qna` wrote to `question-backlog`, also add it to `output`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `<Verdict> v[N] (Score <X>/100)` (e.g., `Conditionally Ready v1 (Score 73.1/100)`). Skip if column missing.
3. **Cleanup**: delete the entire `.claude/skills/qc-uc-read/process-logging/<UC-ID>/` folder. Cleanup only happens on successful completion.

---

## Boundaries (reminder)

- You ONLY review and audit, DO NOT edit the input files.
- Every finding MUST cite the specific source section, page, or paragraph.
- Do NOT fabricate or assume requirements that are not in the document.
- When uncertain, explicitly state uncertainty and ask the user — never guess.
- Do NOT opine on implementation approach — leave architecture decisions to the development team.
