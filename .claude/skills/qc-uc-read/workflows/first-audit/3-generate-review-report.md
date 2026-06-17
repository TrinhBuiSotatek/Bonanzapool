# First Audit · Phase 3 — Generate Review Report

> **Friendly name (for worklog):** `Generating Review Report` (EN) / `Tạo báo cáo review` (VI).
>
> **Inputs:** `process-logging/<UC-ID>/01_synthesis.md` + `02_scoring.md` (Phase 1 & 2 outputs) + `UC_readiness_review_template_v3.md`
>
> **Output:** `uc-review-report v[N].md` written to the UC's output folder (resolved via `path-registry.md`). This file IS the final deliverable — no separate `03_*.md` checkpoint.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running (Phase 3)"`.

If this run is a **resume from Phase 3**: first load `01_synthesis.md` and `02_scoring.md` into memory per `checkpoint-protocol.md` §4 Resume load table.

---

## Step 1 — Load checkpoint inputs

Open:

1. `process-logging/<UC-ID>/01_synthesis.md`
2. `process-logging/<UC-ID>/02_scoring.md`
3. `.claude/skills/qc-uc-read/templates/UC_readiness_review_template_v3.md`
4. `.claude/skills/qc-uc-read/references/qc-writting-rules.md`, if available

Do **not** reload or re-extract raw UC, design, prototype, API, common-rule, or site-map files by default.

Use checkpoint outputs as follows:

| Checkpoint        | Use in Phase 3                                   |
| ----------------- | ------------------------------------------------ |
| `01_synthesis.md` | Fill the business understanding content in `UC_readiness_review_template_v3.md`.                                                   |
| `02_scoring.md`   | Fill readiness conclusion, scoring result, Section 10 issues/questions, Audit Summary, blockers, major issues, and recommendation. |

If one of there files are missing, stop and warning user.

---

## Step 2: Fill the UC Readiness Review Template

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

**Section 10. Gap, mâu thuẫn và câu hỏi mở:** Use the Issue Register and AC Candidate Review from `02_scoring.md` to fill this section.

Section 10.1 is the canonical gap/question table for the final report.

Do not create another duplicated gap/question table elsewhere.

Rules for Section 10.1:

* Include blocker issues first.
* Include major issues after blockers.
* Include medium/minor issues only when they still require BA/QC Lead/PO/Tech Lead confirmation.
* Merge duplicated or overlapping questions.
* Keep only issues relevant to the reviewed UC.
* Write each row as a clear Vietnamese question or action request.
* If the issue is a conflict, describe exactly which sources conflict.
* If the issue is missing information, describe exactly what is missing and why it affects test design.
* If the issue comes from AC candidates, include it only when the AC requires confirmation, is unsupported, or may exceed the UC scope.
* Default status is `Open`.

Use Section 10.2 for dependencies from Phase 2, including blocked artefacts, unavailable related sources, unresolved upstream decisions, environment dependencies, or integration dependencies.

---

## Step 3: Add the Audit Summary under Section 10

Add the audit summary **inside Section 10**, after Section 10.1 and Section 10.2.

Use this heading:

```md
### 10.3 Audit Summary
```

The Audit Summary must be concise. Do not duplicate the full issue register.

Include only the following subsections:

```md
#### Bảng điểm đánh giá

[Render the scoring table from `02_scoring.md` exactly according to Phase 2 result.]
| Nhóm đánh giá | Điểm | Trạng thái | Nhận xét ngắn | 
|---|---:|---|---| 
| <Scoring area from Phase 2> | <X/Y> | <Status from Phase 2> | <Short rationale from Phase 2, rewritten in Vietnamese> | 
| **Tổng điểm** | **<X/100>** | **<Verdict>** | **<One-sentence readiness summary>** |

#### Blocker cần xử lý

[List only blocker issues from `02_scoring.md`. If none, write `Không có blocker được ghi nhận.`]

#### Vấn đề lớn cần xử lý

[List only major issues from `02_scoring.md`. If none, write `Không có major issue được ghi nhận.`]

#### Khuyến nghị

[One short paragraph based on Phase 2 verdict and blocker/major issue status.]
```

Rules:

* Do not restate scoring area definitions from `scoring-rubric.md`.
* Do not restate status marker definitions from `scoring-rubric.md`.
* Do not include all minor issues in Audit Summary.
* Do not duplicate Section 10.1.
* The score and verdict must match `02_scoring.md`.
* If `02_scoring.md` contains a rubric warning, include it in `#### Bảng điểm đánh giá`.

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

After the `uc-review-report v[N].md` is written successfully, **invoke the `qc-qna` skill via the Skill tool** to transfer all `Open` rows from the report's `### 10.1 Bảng gap và câu hỏi cần xác nhận` table into the project's `question-backlog` file (so the BA can answer them).

- Pass the just-written report path + `<UC-ID>` as input context.
- Wait for `qc-qna` to return. Capture its summary (new question IDs created, file path of the backlog).
- If `qc-qna` reports no Open questions to transfer, skip silently.
- If `qc-qna` fails, do NOT block this skill — surface a warning in chat (`⚠️ qc-qna failed: <reason> — please run /qc-qna manually for <UC-ID>`) and continue to Final Status Update.

This auto-trigger is the documented kit flow: first-audit always produces fresh Open questions; sending them directly to the BA's backlog removes a manual step.

---

## Final Status Update & Cleanup

Per `workflows/checkpoint-protocol.md` §5 and §6:

1. **Worklog**: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`. Add the output file name to `output`. If `qc-qna` wrote to `question-backlog`, also add it to `output`.
2. **Cleanup**: delete the entire `.claude/skills/qc-uc-read/process-logging/<UC-ID>/` folder. Cleanup only happens on successful completion.

---

## Boundaries (reminder)

- You ONLY review and audit, DO NOT edit the input files.
- Every finding MUST cite the specific source section, page, or paragraph.
- Do NOT fabricate or assume requirements that are not in the document.
- When uncertain, explicitly state uncertainty and ask the user — never guess.
- Do NOT opine on implementation approach — leave architecture decisions to the development team.
