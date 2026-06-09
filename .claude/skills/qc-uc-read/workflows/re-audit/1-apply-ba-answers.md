# Re-Audit · Phase 1 — Apply BA Answers

> **Friendly name (for worklog & dashboard):** `Applying BA Answers` (EN) / `Áp dụng câu trả lời BA` (VI).
>
> **Inputs:** Previous `uc-review-report v[N].md` + `question-backlog` file (with answered questions).
>
> **Output checkpoint:** `process-logging/<UC-ID>/01_applied-answers.md` — updated 5 synthesis sections after BA answers integrated + image re-scan delta verified.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names (previous audited file + question-backlog) to `input`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Applying BA Answers` (skip if column missing).

---

## Step 1: Ingest Current State & Answers

1. Locate the highest version of the audited file (`uc-review-report v[N].md`) in the output folder.
2. Locate and read the `question-backlog` file — `Answered Questions` section and `Deferred Questions` section.

---

## Step 2: Apply Answers & Resolve Gaps

1. Analyze the BA's answers in the backlog.
2. Incorporate the clarified business rules, logic, and UI behavior into the 5 synthesis sections (Object Attributes, Workflows, etc.) of the previous audited file.

   **Common Reference Resolution rule (MANDATORY):** When the source UC references a common-file entry by code/ID/name (e.g., `MSG_E001`, `BR_xxx`, the name of a common function), do NOT leave the bare code in the audit output. Open the corresponding common file, copy the **exact original text** (message wording, full rule statement, function description), and inline that text into the audit section that uses it (Section 6.1.B Business Rules, 6.1.C Error Codes / Toast Messages, Section 3 Preconditions if a common function is reused, etc.). Preserve the original code in parentheses for traceability — e.g., `"New user created successfully." (MSG_E001)`.
   This is so test cases written downstream from the audit file have the exact verbatim message/rule text in `Expected Result` without re-opening the common docs.

3. **Re-scan all design images (mandatory).** Do NOT trust v[N-1]'s Section 4/5 to be complete. Open every design image listed in the input set and re-extract atomic UI elements per the granularity rule (1 component = 1 row, with label/type/required/default/placeholder/enum values). For every element missing from v[N-1]'s Section 4 or 5, add it to v[N+1]. Re-scan covers `*.png`, `*.jpg`, design exports, and screen mockups embedded in `.docx`/`.pdf`.

   When re-extracting Section 5 Object Attributes Interaction Matrix entries, use platform-appropriate vocabulary based on `project-context-master.md` §1 Product Platform Type — same rule as `workflows/first-audit/1-synthesize-understanding.md` Step 2.2 (web/desktop: Click, Hover, Drag & Drop, Right-click, keyboard shortcuts; mobile native: Tap, Long-press, Swipe, Pull-to-refresh, Pinch-zoom, Hardware back, Swipe-back-edge).

4. **Coverage delta check.** For each design image, record `elements_in_image` vs `rows_in_section_4` in working notes:

   | Image | elements_in_image | rows_in_section_4 | Delta | Action |
   |-------|-------------------|-------------------|-------|--------|
   | *(filename)* | *(N)* | *(M)* | *(N − M)* | *(if Delta > 0: enumerate the missing elements and add rows; if Delta < 0: review for fabricated elements)* |

   If a delta is found, expand and document; do NOT advance to Phase 2 until delta = 0 for every image.

---

## Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §5:

1. **Write checkpoint file** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/01_applied-answers.md` with:
   - Updated 5 synthesis sections (full content, with BA answers integrated and image re-scan applied)
   - UI coverage delta table (must show `Delta = 0` for every image)
   - List of questions that have been resolved by BA answers (with their IDs)
   - List of new conflicts or gaps surfaced by BA answers (for handling in Phase 2)
   - Working notes: UC-ID, version of previous audited file read (`v[N]`), version that will be written next (`v[N+1]`)
2. **Update `progress.md`** → `last_phase_done: 1`, `next_phase: 2`, `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`.
4. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Applying BA Answers done` (skip if column missing).

---

## Hand-off to Phase 2

Next file: `workflows/re-audit/2-recalculate-and-update-backlog.md`. It reads `01_applied-answers.md` and re-scores all 10 knowledge areas using the rubric in `references/scoring-rubric.md`, then updates the `question-backlog` file.
