# Re-Audit · Phase 3 — Generate Updated Report v[N+1]

> **Friendly name (for worklog & dashboard):** `Generating Updated Report v[N+1]` (EN) / `Tạo báo cáo cập nhật v[N+1]` (VI).
>
> **Inputs:** `process-logging/<UC-ID>/01_applied-answers.md` + `02_recalculated.md` + previous `uc-review-report v[N].md`.
>
> **Output:** `uc-review-report v[N+1].md` written to the UC's output folder. This file IS the final deliverable — no separate `03_*.md` checkpoint.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running (Phase 3)"`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Generating Updated Report v[N+1]` (skip if column missing).

If this run is a **resume from Phase 3**: first load `01_applied-answers.md`, `02_recalculated.md`, and the previous `uc-review-report v[N].md` per `checkpoint-protocol.md` §4 Resume load table.

---

## Step 1: Generate the Updated Audited Document

Build the new audited document by **combining**:

1. The updated 5 synthesis sections from `01_applied-answers.md` (template Sections 0–7, mapped per Phase 3 mapping table in first-audit).
2. The updated Acceptance Criteria (template Section 8) — regenerate Given/When/Then statements based on the new BA answers and clarified flows.
3. The updated Non-functional Requirements (template Section 9).
4. The updated **Audit Summary** at the end (use the table format from `workflows/first-audit/3-generate-review-report.md` Step 2 — `Audit Summary Table` — with the new scores from `02_recalculated.md`).

**Section mapping** (knowledge area → template section): same as first-audit Phase 3 — see `workflows/first-audit/3-generate-review-report.md` Step 1 mapping table.

**Status markers** (defined in `references/scoring-rubric.md`):
- ✅ **Complete** — explicitly stated and unambiguous
- ⚡ **Partial** — present but vague, incomplete, or only inferred (half marks)
- ⚠️ **Missing** — absent from all provided artefacts (zero marks)
- *(inferred)* — the reviewer inferred information rather than finding it explicitly

---

## Step 2: Update the Unified Gap & Question Report

Reflect the resolved and new questions in the **Unified Gap & Question Report** table inside the new audited document:

- Move resolved questions to `Resolved` status with a brief note of what answer resolved them.
- Add new questions (from Phase 2 Step 5) with status `Open`.
- Preserve question IDs across versions (Q1, Q2, …). New questions continue from `max(ID) + 1` of the previous version.
- **Platform-specific gaps (mandatory inclusion):** Scan the Phase 2 KA evidence for any entries prefixed with `Platform-specific gap (<variant>):` (added per rubric § "Platform-Aware Gap Detection"). Each remaining gap MUST appear as a row here with `Open` status; previously-flagged platform gaps that are now resolved by BA answers MUST be moved to `Resolved` with the answer source noted. This keeps `qc-qna` in sync.

Table schema (same as first-audit Phase 3):

| ID            | Priority                  | Ref                                       | Question                          | Why It Matters                          | Status |
| ------------- | ------------------------- | ----------------------------------------- | --------------------------------- | --------------------------------------- | ------ |
| *(e.g., Q1)*  | *(High / Medium / Low)*   | *(Exact excerpt from requirement)*        | *(Main content to clarify or fix)* | *(Why this is an issue)*                | *(Open / Resolved)* |

---

## Step 3: Add a Changelog at the Bottom

Append a **Changelog** section at the very bottom of the new audited document summarizing what changed from v[N] to v[N+1]:

```markdown
## Changelog — v[N] → v[N+1]

### BA Answers Integrated
- Q1: <one-line summary of answer and which section it updated>
- Q3: <one-line summary>

### New Information Surfaced
- <one-line description of new gaps/conflicts found during re-audit>

### Score Change
- v[N]: <old final score>/100 — <old verdict>
- v[N+1]: <new final score>/100 — <new verdict>

### Sections Updated
- Section X: <brief description of what changed>
- Section Y: ...
```

---

## Step 4: Write the Output File

Resolve the output path via `path-registry.md` → `uc-review-report` logical name.

**Versioning rule:** Save as `v[N+1]`. **Never overwrite the `v[N]` version.**

**Naming convention** (per `.claude/rules/naming-convention.md`):
```
[UC-ID]_[feature-name]_audited_[YYYYMMDD]_v[N+1].md
```

Write the combined updated content to the resolved path.

---

## Final Status Update & Cleanup

Per `workflows/checkpoint-protocol.md` §5 and §6:

1. **Worklog**: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`. Add the output file name (`v[N+1]`) to `output`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `<Verdict> v[N+1] (Score <X>/100)` (e.g., `Ready v2 (Score 92.3/100)`, `Conditionally Ready v3 (Score 78.5/100)`). Skip if column missing.
3. **Cleanup**: delete the entire `.claude/skills/qc-uc-read/process-logging/<UC-ID>/` folder. Cleanup only happens on successful completion.

---

## Boundaries (reminder)

- You ONLY review and audit, DO NOT edit the input UC files or the previous audited file.
- Every finding MUST cite the specific source section, page, or paragraph.
- Do NOT fabricate or assume requirements that are not in the document or in the BA's answers.
- When uncertain, explicitly state uncertainty and ask the user — never guess.
- Do NOT opine on implementation approach — leave architecture decisions to the development team.
