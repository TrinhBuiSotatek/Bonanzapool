# First Audit · Phase 2 — Score & Identify Gaps

> **Friendly name (for worklog & dashboard):** `Scoring & Identifying Gaps` (EN) / `Chấm điểm & xác định gap` (VI).
>
> **Input:** `process-logging/<UC-ID>/01_synthesis.md` (Phase 1 output) + all source artefacts (re-readable from disk if needed).
>
> **Output checkpoint:** `process-logging/<UC-ID>/02_scoring.md` — scoring table + cross-artefact conflicts + blocker list.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2:

1. **Worklog**: rewrite last entry → `status = "Running (Phase 2)"`.
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Scoring & Identifying Gaps` (skip if column missing).

If this run is a **resume from a prior checkpoint** (entered directly at Phase 2): first load `01_synthesis.md` into memory per `checkpoint-protocol.md` §4 Resume load table.

---

## Step 1: Score the 10 Knowledge Areas

Open and apply `.claude/skills/qc-uc-read/references/scoring-rubric.md`. The rubric file defines:

- The 10 knowledge areas (Feature Identity, Objective & Scope, Actors & Roles, Preconditions/Postconditions, UI Inventory, Object Attributes, Functional Logic, Functional Integration, Acceptance Criteria, NFR)
- Max points (5/5/10/10/15/20/20/20/20/5 → 130 total)
- Auto-cap rules for UI Inventory (#5) and Object Attributes (#6)
- Status markers (✅ Clear / ⚠️ Partial / ❌ Missing)
- Normalization formula (`(Raw / 130) × 100`)
- Auto-fail rule (any Critical KA = 0 → NOT READY)
- Readiness thresholds (≥90 READY, 70–89 CONDITIONALLY READY, <70 NOT READY)
- **Platform-Aware Gap Detection** — sharpens what counts as Partial/Missing in KA #6, #7, #8, #10 based on `project-context-master.md` §1 Product Platform Type (does NOT add a new KA or change scoring).

**Before scoring**, read `project-context-master.md` §1 → "Product Platform Type" and load the matching row(s) from the rubric's "Platform-Aware Gap Detection" table into working memory. Apply those expectations when scoring KA #6 / #7 / #8 / #10. Mark any platform-specific gap inline in the KA's evidence with the prefix `Platform-specific gap (<variant>):` so Phase 3 lifts it as a row in the **Unified Gap & Question Report** table (the canonical Q-table that `qc-qna` reads — NOT template §10.1, which is the BA's UC-local Open Questions section).

**Score each KA** based on the synthesis in `01_synthesis.md` cross-referenced against the source artefacts. For each KA, record:

- Raw score (e.g., `12/15`)
- Status marker (✅ / ⚠️ / ❌)
- Evidence: specific reference to source section / page / paragraph
- For Partial / Missing: a one-line explanation of what's lacking

---

## Step 2: Cross-Artefact Conflict Check

Per `references/scoring-rubric.md` "Cross-Artefact Conflict Check" section, check for conflicts between artefacts:

- Does the UC doc describe a flow that contradicts the wireframe?
- Does the API spec define fields not mentioned in requirements?
- Are there UI elements in the design with no corresponding business rule?
- Are labels/field names inconsistent across documents?

List all conflicts found — they are automatic Warnings.

---

## Step 3: Blocked Artefact Protocol

Per `references/scoring-rubric.md` "Blocked Artefact Protocol" section:

If any referenced artefact (wireframe, API spec, supporting doc) is **unavailable or inaccessible**:

- Mark the dependent knowledge area(s) as `[BLOCKED: artefact name not accessible]`
- Score those areas as 0
- Since blocked artefacts almost always affect Critical knowledge areas (#1–#9), surface each blocked area as a 🔴 **Blocker**
- Do NOT infer or assume content from unavailable artefacts

---

## Step 4: Compute Final Score & Verdict

1. Sum the raw scores from the 10 KA → `Raw Score`.
2. Apply normalization: `Final Score = round((Raw Score / 130) × 100, 1)`.
3. Apply auto-fail rule: if any Critical KA scored 0 → verdict = `NOT READY` (regardless of Final Score).
4. Otherwise apply readiness threshold:
   - 90–100 → `READY` (✅)
   - 70–89 → `CONDITIONALLY READY` (⚠️)
   - 0–69 → `NOT READY` (❌)

---

## Checkpoint write — End of Phase 2

Per `workflows/checkpoint-protocol.md` §5:

1. **Write checkpoint file** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/02_scoring.md` with:
   - Scoring table (all 10 KA with raw score, status, evidence, gap notes)
   - Raw total, normalized Final Score, Verdict
   - Conflict list (from Step 2)
   - Blocker list (from Step 3)
2. **Update `progress.md`** → `last_phase_done: 2`, `next_phase: 3`, `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 2 done"`.
4. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Scoring & Identifying Gaps done` (skip if column missing).

---

## Hand-off to Phase 3

Next file: `workflows/first-audit/3-generate-review-report.md`. It reads `01_synthesis.md` + `02_scoring.md` from the checkpoint folder, fills the UC Readiness Review Template, and writes the final `uc-review-report v[N].md` to the output folder.
