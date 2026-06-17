# Checkpoint & Resume Protocol

> **Scope:** Shared rules referenced by all `qc-uc-read` workflow phase files. Read this once at skill start.
>
> **Purpose:** Make the skill resilient to context-limit / interruption mid-run by:
> (1) persisting per-phase intermediate output to disk, (2) updating the device's worklog JSONL entry at every phase boundary, (3) detecting prior checkpoints on the next run so the user does not redo finished work.

---

## 1. `process-logging/` directory

All checkpoint files live in `.claude/skills/qc-uc-read/process-logging/<UC-ID>/`. Create the folder lazily — when the first checkpoint is written. One subfolder per UC so the skill can run for multiple UCs concurrently without conflict.

### File layout

| File                        | Owner phase           | Content                                                                                       |
| --------------------------- | --------------------- | --------------------------------------------------------------------------------------------- |
| `progress.md`               | All phases            | State machine — current run metadata + last completed phase                                   |
| `01_synthesis.md`           | First audit Phase 1   | 5 synthesis sections + Section 4 inventory with `Delta = 0` coverage verified                 |
| `02_scoring.md`             | First audit Phase 2   | Scoring table (10 KA) + cross-artefact conflicts + blocker list                               |

Phase 3 in both workflows writes the **real deliverable** (`uc-review-report v[N].md`) to the output folder — this IS the final checkpoint. No separate `03_*.md` file needed.

Re-audit runs as a **single uninterrupted flow** with no intermediate checkpoint files. The output `uc-review-report v[N+1].md` IS the checkpoint. If re-audit is interrupted before completion, the next run restarts from Step 0.

### `progress.md` format

Single source of truth for resume. Overwrite on every checkpoint write.

```markdown
# qc-uc-read progress — <UC-ID>

- run_id: run-XXX
- uc_id: UC-XXX
- mode: <first-audit | re-audit>
- started_at: <ISO-8601 datetime>
- last_phase_done: <phase-number>   # 0, 1, 2, 3
- next_phase: <phase-number>
- updated_at: <ISO-8601 datetime>

## Notes
<any per-run scratch data — e.g. detected output language, version of input read, ...>
```

---

## 2. Worklog updates

All worklog updates target the device's JSONL file under `worklog-per-device`. Schema, lifecycle (append-on-start, rewrite-on-phase-boundary, terminal states), `run_id` generation, and write-before-work rule are defined once in `docs/qc-lead/agent-work-log.local/README.md`. Do not duplicate them here.

### Files excluded from `input` / `output` arrays

- Anything under `process-logging/` — internal scratchpad, not a deliverable.
- `progress.md` — internal.
- Templates and references (`.claude/skills/.../templates/*`, `.claude/skills/.../references/*`).

User-visible deliverables that DO go into `output`: `uc-review-report v[N].md`, `question-backlog` (if updated).

---

## 3. Resume detection (runs at Phase 0)

At skill start, after the routing decision is made (first-audit vs re-audit) and `<UC-ID>` is determined:

1. Check `.claude/skills/qc-uc-read/process-logging/<UC-ID>/progress.md`.
   - **Not found** → fresh run. Generate new `run_id` per the worklog protocol. Skip to Phase 1.
   - **Found** → there is a prior incomplete run. Continue to step 2.
2. Read `last_phase_done`, `next_phase`, and `mode`.
3. Ask the user (ONE message, blocking):
   ```
   Phát hiện checkpoint từ run trước cho UC <UC-ID>:
   - Run ID: <run_id>
   - Mode: <first-audit | re-audit>
   - Bắt đầu lúc: <started_at>
   - Đã hoàn thành: Phase <last_phase_done> (<phase friendly name>)

   Bạn muốn:
   1. **Continue** — tiếp tục từ Phase <next_phase>
   2. **Restart** — chạy lại từ đầu (xoá toàn bộ checkpoint cũ)
   ```
4. If user picks **Continue**:
   - Worklog: rewrite the prior entry's `status` → `Resumed by run-<new>` (one-time edit).
   - Worklog: append a new entry for the new run with `status = "Running (Phase <next_phase>)"`.
   - Load required checkpoint files (see "Resume load table" below).
   - Jump to `next_phase` workflow file.
5. If user picks **Restart**:
   - Delete `.claude/skills/qc-uc-read/process-logging/<UC-ID>/` folder entirely.
   - Worklog: rewrite the prior entry's `status` → `Interrupted (last: Phase <last_phase_done>)`.
   - Worklog: append a new entry, start fresh from Phase 1.

### Resume load table

When resuming, load these files INTO MEMORY before executing the next phase:

| Mode          | Resuming at Phase | Files to load from `process-logging/<UC-ID>/`                      |
| ------------- | ----------------- | -------------------------------------------------------------------- |
| first-audit   | 2                 | `01_synthesis.md`                                                    |
| first-audit   | 3                 | `01_synthesis.md`, `02_scoring.md`                                   |

> **Re-audit has no intermediate checkpoints.** If `progress.md` shows `mode: re-audit` with `last_phase_done: 0`, offer only **Restart** — there is no partial state to resume from.

Also re-resolve all `path-registry` logical names — paths may have changed since the last run.

---

## 4. Checkpoint write protocol (used by every phase)

After completing a phase, the workflow MUST execute these 4 steps **in order, atomically as possible**:

1. **Write the checkpoint file** for this phase (markdown, full content as defined per phase workflow). For Phase 3, this step is the actual deliverable write (`uc-review-report v[N].md`).
2. **Update `process-logging/<UC-ID>/progress.md`** — set `last_phase_done`, `next_phase`, `updated_at`.
3. **Update the worklog JSONL entry** — rewrite last entry's `status` to `Phase <N> done`, append any new `input`/`output` files (excluding `process-logging/`).

---

## 5. Cleanup

After the final phase (Phase 3) finishes successfully:

1. Worklog: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`.
2. **Delete the entire `.claude/skills/qc-uc-read/process-logging/<UC-ID>/` folder.** It is scratch — not part of project deliverables.

Cleanup must NOT happen mid-run, even on error. Only on successful Phase 3 completion.

---

## 6. Failure modes

| Symptom                                                  | Recovery                                                                         |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `progress.md` exists but no checkpoint files             | Treat as fresh run; warn user and delete `progress.md`.                          |
| Checkpoint file referenced by `progress.md` missing      | STOP and ask user; do not silently re-derive.                                    |
| Per-device JSONL missing entry for current `run_id`      | Append a new entry; do not fail the skill.                                       |
| Path-registry logical name changed between runs          | Re-resolve from current registry; if path differs, ask user before continuing.   |
