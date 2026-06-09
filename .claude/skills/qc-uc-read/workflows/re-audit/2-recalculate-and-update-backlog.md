# Re-Audit · Phase 2 — Recalculate Score & Update Backlog

> **Friendly name (for worklog & dashboard):** `Recalculating Score & Updating Backlog` (EN) / `Tính lại điểm & cập nhật backlog` (VI).
>
> **Inputs:** `process-logging/<UC-ID>/01_applied-answers.md` (Phase 1 output) + `question-backlog` file.
>
> **Output checkpoint:** `process-logging/<UC-ID>/02_recalculated.md` — updated scoring table + backlog status changes.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running (Phase 2)"`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Recalculating Score & Updating Backlog` (skip if column missing).

If this run is a **resume from a prior checkpoint** (entered directly at Phase 2): first load `01_applied-answers.md` and the previous `uc-review-report v[N].md` per `checkpoint-protocol.md` §4 Resume load table.

---

## Step 1: Recalculate the Readiness Score

Apply `.claude/skills/qc-uc-read/references/scoring-rubric.md` to the updated synthesis from `01_applied-answers.md`:

- Re-score each of the 10 knowledge areas based on the newly introduced information (BA answers + image re-scan).
- Apply auto-cap rules for UI Inventory (#5) and Object Attributes (#6).
- **Apply Platform-Aware Gap Detection** (per rubric § "Platform-Aware Gap Detection") — re-read `project-context-master.md` §1 → "Product Platform Type" and re-check whether BA answers have closed any prior platform-specific gaps in KA #6 / #7 / #8 / #10. Some BA answers may have surfaced NEW platform gaps too (e.g., the BA confirmed a permission flow but the resulting flow now reveals a missing offline behavior). Mark any remaining/new platform-specific gap inline in the KA's evidence with the prefix `Platform-specific gap (<variant>):` so Phase 3 lifts it into the **Unified Gap & Question Report** table.
- Apply normalization: `Final Score = round((Raw Score / 130) × 100, 1)`.
- Apply auto-fail rule: if any Critical KA = 0 → verdict = NOT READY.
- Determine new verdict: READY (≥90) / CONDITIONALLY READY (70–89) / NOT READY (<70).

---

## Step 2: Cross-Artefact Conflict Check (re-run)

Per `references/scoring-rubric.md` "Cross-Artefact Conflict Check" section, re-check for conflicts. Some conflicts may have been resolved by BA answers; new ones may have surfaced.

List all current conflicts — they are automatic Warnings.

---

## Step 3: Blocked Artefact Protocol (re-run)

Per `references/scoring-rubric.md` "Blocked Artefact Protocol" section:

If any referenced artefact is still **unavailable or inaccessible**:

- Mark the dependent knowledge area(s) as `[BLOCKED: artefact name not accessible]`
- Score those areas as 0
- Surface each blocked area as a 🔴 **Blocker**
- Do NOT infer or assume content from unavailable artefacts

---

## Step 4: Handle Existing Questions

For each question in the `question-backlog`:

1. Check if the BA provided a satisfactory answer.
2. If **answered satisfactorily**: change status from `Open` to `Resolved`. Move the row to the **"Answered Questions"** section table of the backlog file.
3. If **answer is unclear / partial**: keep status `Open` and add a follow-up note explaining what's still missing.

---

## Step 5: Handle New Questions

If the re-audit reveals **new** conflicts or missing information arising from the BA's answers:

1. Identify each new gap as a new question.
2. **Immediately call the `qc-qna` skill** to append these new questions to the **"Open Questions"** table of the backlog file.

> Note: `qc-qna` skill is responsible for backlog updates. Do NOT directly edit the "Open Questions" table here — delegate to `qc-qna`.

---

## Checkpoint write — End of Phase 2

Per `workflows/checkpoint-protocol.md` §5:

1. **Write checkpoint file** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/02_recalculated.md` with:
   - Updated scoring table (all 10 KA with new raw score, status, evidence)
   - New Raw total, Final Score, Verdict
   - Updated conflict list (from Step 2)
   - Updated blocker list (from Step 3)
   - List of resolved question IDs (from Step 4)
   - List of new question IDs created via `qc-qna` (from Step 5)
2. **Update `progress.md`** → `last_phase_done: 2`, `next_phase: 3`, `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 2 done"`. Add `question-backlog` to `output` (since it was modified).
4. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Recalculating Score & Updating Backlog done` (skip if column missing).

---

## Hand-off to Phase 3

Next file: `workflows/re-audit/3-generate-updated-report.md`. It reads `01_applied-answers.md` + `02_recalculated.md` + the previous `uc-review-report v[N].md`, generates the new `v[N+1]` with changelog, and writes it to the output folder.
