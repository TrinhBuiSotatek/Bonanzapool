## Checkpoint & Resume Protocol

> **Scope:** Inline shared rules referenced by every Phase boundary in this skill. Read this once at skill start.
>
> **Purpose:** Make the skill resilient to context-limit / interruption mid-run by (1) persisting per-phase intermediate output to disk, (2) updating the device's worklog JSONL entry at every phase boundary, (3) detecting prior checkpoints on the next run so the user does not redo finished work.
>
> **Phase model:** This skill runs in **two phases**: Phase 1 = analysis + design + scratch + final `.md` (per variant); Phase 2 = `.md` → `.xlsx` conversion (per variant). The earlier 3-phase model is retired — the legacy file prefix `02_` on the scratch is kept for backward compatibility only and no longer implies a phase number.

### 1. `process-logging/` directory

All checkpoint files live in `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/`. Create the folder lazily — when the first checkpoint is written. One subfolder per UC so the skill can run for multiple UCs concurrently without conflict.

#### File layout

| File                                    | Owner phase                                 | Content                                                                                       |
| --------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `progress.md`                           | All phases                                  | State machine — current run metadata + `last_phase_done` + a `## Phase 1 Summary` block appended at end of Phase 1 (contains one `### Variant: <name>` sub-block per platform variant in scope; see `progress.md` format below). Phase 2 reads this block to drive its per-variant verification loop. For `update-test-cases` only: may also contain a `## Phase 1 Approval Pending` block while the workflow is paused for user approval (see §4.3). |
| `02_designed_tcs_<variant>.md`          | Phase 1                                     | **Source of truth for the designed test cases — ONE file per platform variant.** Atomic snapshot of the FULL TC list + RTM for that variant, written BEFORE the variant's deliverable `.md` is written (Step 3.5 of `generate-test-cases.md`, Step 5.3 of `update-test-cases.md`). Phase 2 Step 0 reads this when auto-recovering a partial / mismatched final md (overwrites the same-version final md from the scratch). Same content format as the final deliverable md (prelude + screen/section headers + TC tables). One file per variant in scope, for both generate and update runs. |
| `pending_update_report.md`              | Phase 1 — `update-test-cases` only          | **Temporary approval report** shown to the user before any update is applied (written by Step 3 of `update-test-cases.md`). May be rewritten while the user requests revisions (`R1` → `R2` → ...). MUST be deleted after the approved update has been applied and verified, or when the user cancels. No scratch / final md / xlsx is produced until the user approves. |

Phase 2 produces the **real deliverable** (`.xlsx`) to the output folder — that IS the final checkpoint for Phase 2. No separate process-logging file is written.

#### `progress.md` format

Single source of truth for resume. Overwrite on every checkpoint write.

**Semantic of `last_phase_done`:** This field tracks **completed-and-verified** phases. It is written **at the moment of TRANSITION to the next phase**, NOT at the end of the current phase. This guarantees that whenever resume reads `last_phase_done = N`, the work of Phase N has been confirmed safe (deliverable exists AND any gating check has passed). If interrupt happens at any point inside Phase N before transition to Phase N+1, the field stays at N-1 and resume will safely re-enter Phase N (re-using persisted scratch artifacts where possible — see §3 Resume load table). Phase 2 is the last phase, so its `last_phase_done: 2` is written at end-of-Phase-2 directly (right after the last variant's `.xlsx` is verified).

```markdown
# qc-func-tc-design progress — <UC-ID>

- run_id: run-XXX
- uc_id: UC-XXX
- workflow: <generate-test-cases | update-test-cases>
- started_at: <ISO-8601 datetime>
- last_phase_done: <empty | 1 | 2>   # set at transition to next phase; written directly at end of Phase 2
- next_phase: <1 | 2 | ->
- updated_at: <ISO-8601 datetime>

## Notes
<any per-run scratch data — e.g. detected output language, version of input read, ...>

## Phase 1 Approval Pending
<!-- update-test-cases only. Written by Step 3 of update-test-cases.md when the pending_update_report.md is sent to the user; removed when the user approves (and the update is applied) or cancels. While this block is present, the workflow is paused mid-Phase 1 and last_phase_done stays empty. -->

**Pending report path:** <absolute path to pending_update_report.md>
**Report revision:** R<n>
**Trigger type:** <REQUIREMENT_DELTA | USER_FEEDBACK_ONLY | ADD_VARIANT | MIXED>
**Variants in scope:** <comma-separated list>
**Current status:** Waiting for user approval
**Impact summary:** <KEEP=k, UPDATE=u, ADD=a, RETIRE=r, SPLIT=s, MERGE=m, REVIEW=q>

## Phase 1 Summary
<!-- Written at end of Phase 1, AFTER all variant scratches + all variant final md files are written. Phase 2 reads this block to drive its per-variant verification loop. Contains ONE `### Variant: <name>` sub-block per platform variant in scope. -->

**Variants in scope:** <comma-separated list of variant names, e.g., web-responsive, mobile-native>

### Variant: <variant-name>

**Platform variant:** <variant-name>
**Scope reason:** <UPDATE_EXISTING | ADD_VARIANT>   <!-- update-test-cases only; omit for generate-test-cases -->
**Total test cases designed:** <N>
**GUI total:** <a>
**FUNC total:** <b>
**Output language:** <VI | EN>
**Scratch:** <absolute path>/process-logging/<UC-ID>/02_designed_tcs_<variant-name>.md
**Final MD file(s):** <absolute paths resolved from path-registry — one bullet per file (single-file or multi-part)>
- <absolute path to part1>
- <absolute path to part2 if multi-part>

| Screen | Total | GUI | FUNC |
|---|---|---|---|
| I. <screen name> | <n1> | <a1> | <b1> |
| II. <screen name> | <n2> | <a2> | <b2> |
| ... | ... | ... | ... |

<!-- For update-test-cases with Scope reason = UPDATE_EXISTING, append this line below the table (the new file is v[N+1]; v[N] is the previous version): -->
**Delta vs v[N]:** +<A> new, ~<U> updated, -<D> deleted

<!-- For update-test-cases with Scope reason = ADD_VARIANT, OMIT the Delta line — there is no baseline to diff against; the variant's file is v1. -->

### Variant: <next-variant-name>
<!-- same shape as above; one block per variant -->
...
```

**Notes on the schema:**
- `Total test cases designed`, `GUI total`, `FUNC total` are explicit, separately-parseable fields on their own lines (Phase 2 Step 0 parses each as a discrete integer).
- All file paths in `Scratch` and `Final MD file(s)` are **absolute paths** (resolved from `path-registry.md` at write time). Phase 2 reads these paths verbatim — no relative-path resolution needed.
- The `Delta vs v[N]` line uses ASCII "Delta", NOT the Greek glyph `Δ`. The version reference is `v[N]` (the previous version), because the new file is `v[N+1]`. Same convention as the md prelude in `update-test-cases.md`.
- For both `generate-test-cases` and `update-test-cases` runs, `Variants in scope` lists every platform variant in scope for this run (one or more), and there is one `### Variant: <name>` sub-block per variant in the same order.
- The `Scope reason` line and the `Delta vs v[N]` line are **`update-test-cases`-only**. For `generate-test-cases` runs, omit both.

### 2. Worklog updates

All worklog updates target the device's JSONL file under `worklog-per-device`. Schema, lifecycle (append-on-start, rewrite-on-phase-boundary, terminal states), `run_id` generation, and write-before-work rule are defined once in `docs/qc-lead/agent-work-log.local/README.md`. Do not duplicate them here.

#### Files excluded from `input` / `output` arrays

- Anything under `process-logging/` — internal scratchpad, not a deliverable. This includes `pending_update_report.md`.
- `progress.md` — internal.
- Templates, references, rules, scripts under `.claude/skills/.../`.

User-visible deliverables that DO go into `output`: `func-test-cases-draft` `.md` (Phase 1), `func-test-cases` `.xlsx` (Phase 2).

#### Ordering at a phase transition

When Phase N+1 starts (a transition write — see §4.1), execute the writes in this exact order so that the durable resume state advances atomically before any user-visible status changes:

1. **`progress.md`** — `last_phase_done: N`, `next_phase: N+1`, `updated_at: <now>`. (For Phase 2 entry, this happens INSIDE `convert-md-to-xlsx.md` Step 0 AFTER the verification gate passes.)
2. **Worklog JSONL** — rewrite last entry → `status = "Running (Phase N+1)"`, append any new `input` files.

The same ordering applies at end-of-phase (§4.2), but `progress.md` only receives the artifact-related writes (e.g., `## Phase 1 Summary`); `last_phase_done` is NOT touched there (except for Phase 2, which is the last phase — see §4.2).

### 3. Resume detection (runs at Phase 0)

At skill start, after the workflow decision is made (generate vs update) and `<UC-ID>` is determined:

1. Check `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/progress.md`.
  - **Not found** → fresh run. Generate new `run_id` per the worklog protocol. Skip to Phase 1.
  - **Found** → there is a prior incomplete run. Continue to step 2.
2. Read `last_phase_done`, `next_phase`, `workflow`, and check for the presence of a `## Phase 1 Approval Pending` block.
3. **Special case — Mid-Phase 1 approval pending (update workflow only):** If the `## Phase 1 Approval Pending` block is present AND `pending_update_report.md` exists on disk at the path referenced in the block, the workflow was paused waiting for user response. Re-enter the approval-wait state directly:
  - Worklog: rewrite the prior entry's `status` → `Resumed by run-<new>` (one-time edit).
  - Worklog: append a new entry for the new run with `status = "Waiting for user approval (Phase 1 update report)"`.
  - Re-send the latest report revision to the user on chat and wait for response (approve / feedback / cancel).
  - Do NOT prompt Continue/Restart — the only meaningful action here is to act on the user's response.
4. **Default case:** Ask the user (ONE message, blocking):
  ```
  Phát hiện checkpoint từ run trước cho UC <UC-ID>:
  - Run ID: <run_id>
  - Workflow: <generate-test-cases | update-test-cases>
  - Bắt đầu lúc: <started_at>
  - Đã hoàn thành: Phase <last_phase_done> (<phase friendly name>)

  Bạn muốn:
  1. **Continue** — tiếp tục từ Phase <next_phase>
  2. **Restart** — chạy lại từ đầu (xoá toàn bộ checkpoint cũ)
  ```
5. If user picks **Continue**:
  - Worklog: rewrite the prior entry's `status` → `Resumed by run-<new>` (one-time edit).
  - Worklog: append a new entry for the new run with `status = "Running (Phase <next_phase>)"`.
  - Load required checkpoint files (see "Resume load table" below).
  - If the stored `workflow` differs from the freshly-determined workflow, warn the user and prefer the stored workflow unless they explicitly Restart.
  - Jump to `next_phase` work.
6. If user picks **Restart**:
  - Delete `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/` folder entirely.
  - Worklog: rewrite the prior entry's `status` → `Interrupted (last: Phase <last_phase_done>)`.
  - Worklog: append a new entry, start fresh from Phase 1.

#### Resume load table

When resuming, load these files INTO MEMORY before executing the next phase:

| Resuming at Phase | Files to load |
| --- | --- |
| 1 (fresh) | All input files re-resolved from `path-registry.md` — UC review report, scenarios (optional), `project-context-master.md`, `common-technical.md`, per-variant `<variant>-technical.md`, language-matched `Testcase-refer-*.md`. For `update-test-cases`: also the baseline TC `.md` file(s), the old audited UC (the one used by the baseline), the new audited UC, and any user feedback in the current prompt. |
| 1 (partial — `## Phase 1 Summary` block already exists) | Same inputs as fresh, PLUS for each variant declared in the summary, probe for `02_designed_tcs_<variant>.md` scratch. If a variant's scratch is present, its drafting is already done — re-materialize the final md from scratch only. Variants without scratch get fresh drafting. After all variants are on disk (scratch + final md), rewrite the `## Phase 1 Summary` block. |
| 1 (mid-approval, update workflow only) | Same inputs as fresh, PLUS the latest `pending_update_report.md` (already on disk). Re-send it to the user; wait for response. See §3 step 3. |
| 2 | For EACH variant listed in the `## Phase 1 Summary` block: that variant's final `.md` file(s) at the path(s) recorded in the summary + that variant's `02_designed_tcs_<variant>.md` scratch (required for auto-recovery of that variant). |

Also re-resolve all `path-registry` logical names — paths may have changed since the last run.

### 4. Checkpoint write protocol (used by every phase)

The protocol is split into **three boundaries**: start-of-phase (transition write — §4.1), end-of-phase (deliverable write — §4.2), and the update-workflow-only mid-Phase 1 approval pause (§4.3). The transition/deliverable split exists so `last_phase_done` only advances when the previous phase has actually produced a usable, verified artifact.

#### 4.1 — Start of Phase N (transition write)

Run these steps BEFORE doing any work for Phase N. They mark "Phase N-1 is confirmed done; we're now committing to Phase N":

1. **(Phase 2 only) Run the Phase 1 verification gate** — see `convert-md-to-xlsx.md` → Step 0. For EACH platform variant listed in the `## Phase 1 Summary` block, compare that variant's final md (deliverable) against its summary sub-block (counts + per-screen breakdown). If a variant mismatches → auto-recover from `02_designed_tcs_<variant>.md` scratch (overwrite that variant's final md same-version), re-run verification for that variant. If recovery also fails (scratch missing or scratch-derived md still mismatches) → STOP and report. **Do NOT advance `last_phase_done` until ALL variants pass verification.**
2. **Update `process-logging/<UC-ID>/progress.md`** — set `last_phase_done: <N-1>`, `next_phase: <N>`, `updated_at: <now>`. Preserve the existing `## Phase 1 Summary` block (if any). For start of Phase 1, this is part of Phase 0 init (last_phase_done stays empty, next_phase: 1).
3. **Update the worklog JSONL entry** — rewrite last entry's `status` to `Running (Phase <N>)`, append any new `input` files (excluding `process-logging/`). For Phase 2, no new `input` files are appended (the Phase 1 final md was already recorded in `output` at end of Phase 1).

Order within the transition: `progress.md` → worklog JSONL (see §2 "Ordering at a phase transition").

#### 4.2 — End of Phase N (deliverable write)

Run these steps AFTER finishing the actual work of Phase N. They write the artifacts.

1. **Write the artifact(s) for this phase:**
  - **Phase 1 (per platform variant in scope)**:
    - 1a. `process-logging/<UC-ID>/02_designed_tcs_<variant>.md` — scratch for THAT variant with the FULL designed TC list + RTM (same content format as the final deliverable). Atomic single Write. This is the source of truth for Phase 2 auto-recovery of that variant.
    - 1b. The deliverable `func-test-cases-draft` `.md` file(s) for THAT variant at the output path. May be single-file or multi-part — each part is its own atomic Write.
    - Repeat 1a + 1b for every variant.
  - **Phase 1 (once, AFTER all variants' files in 1a + 1b are on disk)**:
    - 1c. Append the `## Phase 1 Summary` block to `progress.md` — one `### Variant: <name>` sub-block per variant, plus the top-level `**Variants in scope:**` line. Schema per §1 above. Atomic single Write that preserves all other progress.md fields. (This is NOT a `last_phase_done` advance; that happens later in §4.1 of Phase 2.)
  - **Phase 2 (per platform variant in scope)**: that variant's deliverable `.xlsx` at the output path (produced by the converter script).
2. **Update the worklog JSONL entry** — rewrite last entry's `status` to `Phase <N> done`, append any new `output` files (excluding `process-logging/`). For Phase 1 multi-variant, append ALL variants' final md paths. For Phase 2 multi-variant, append ALL variants' xlsx paths.

**`last_phase_done` rules at end-of-phase:**
- **Phase 1**: Do NOT touch `last_phase_done`. It stays at its current value (likely empty) until Phase 2's §4.1 transition advances it to `1` — only AFTER Phase 2's Step 0 verification gate has confirmed Phase 1's artifacts are valid.
- **Phase 2**: Phase 2 is the last phase — there is no Phase 3 to transition into. Write `last_phase_done: 2` and `next_phase: -` directly at the end of Phase 2, right after the last variant's `.xlsx` has passed its self-verification (see `convert-md-to-xlsx.md` → Step 4).

#### 4.3 — Mid-Phase 1 Approval Pending (`update-test-cases` only)

The update workflow has an intentional pause inside Phase 1: after impact analysis (Steps 1–2) the workflow writes a temporary approval report (Step 3), sends it to the user, and waits for a response. The skill must NOT touch deliverable files during this pause.

**Writing the pause checkpoint** (called from Step 3 of `update-test-cases.md`):

1. Write / rewrite `process-logging/<UC-ID>/pending_update_report.md` in ONE atomic Write containing the entire report content.
2. Update `progress.md` while preserving existing fields:
  - `workflow: update-test-cases`
  - `last_phase_done` stays unchanged (typically empty — Phase 1 not done).
  - `next_phase: 1`
  - `updated_at: <now>`
  - Add / replace the `## Phase 1 Approval Pending` block (schema in §1 above).
3. Worklog: rewrite last entry → `status = "Waiting for user approval (Phase 1 update report)"`.
4. Do NOT write `02_designed_tcs_<variant>.md` scratch yet.
5. Do NOT write final TC `.md` file(s) yet.
6. Do NOT trigger `convert-md-to-xlsx.md`.
7. Do NOT advance `last_phase_done`.

**Revision** (user sends feedback before approval):
- Rewrite the SAME `pending_update_report.md` path in ONE atomic Write with new revision marker (`R1` → `R2` → ...).
- Update the `**Report revision:**` field in the `## Phase 1 Approval Pending` block.
- Re-send the revised report on chat. Remain in the approval-wait state.

**Approval** (user explicitly approves):
- Continue Phase 1 from Step 5 of `update-test-cases.md` (Apply Approved Update Plan).
- After Step 6 (Write final md) and the End-of-Phase-1 checkpoint complete successfully, delete `pending_update_report.md` and remove the `## Phase 1 Approval Pending` block from `progress.md`.

**Cancel** (user explicitly cancels):
- Delete `pending_update_report.md`.
- Remove the `## Phase 1 Approval Pending` block from `progress.md`; set `next_phase: -`, `updated_at: <now>`.
- Worklog: rewrite last entry → `status = "Cancelled by user before applying update"`.
- Stop the skill. Do NOT run cleanup (Step D) — the user may choose to start a fresh update later.

### 5. Cleanup

Cleanup happens in **Step D** of the orchestration (after Phase 2 SUCCESS AND chat report sent). See `SKILL.md` → Step D. Cleanup must NOT happen mid-run, even on error.

### 6. Failure modes

| Symptom                                                  | Recovery                                                                         |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `progress.md` not found                                  | Fresh run — generate new `run_id`, start at Phase 1.                             |
| `progress.md` exists but `## Phase 1 Summary` block missing AND no `02_designed_tcs_<variant>.md` scratches on disk | Treat Phase 1 as not started; warn user and offer Continue (re-enter Phase 1 fresh) or Restart (delete the folder). |
| `## Phase 1 Summary` block missing OR `**Variants in scope:**` line missing, BUT one or more `02_designed_tcs_<variant>.md` scratches exist | Treat Phase 1 as incomplete. For each scratch found, derive a per-variant summary from it. Reconstruct `## Phase 1 Summary` from the discovered scratches and write it back to `progress.md`. Then write each variant's final md from its scratch (overwrite same version). Then run Phase 2 Step 0 verification normally. |
| `## Phase 1 Approval Pending` block present AND `pending_update_report.md` exists | Resume into approval-wait state per §3 step 3 — re-send the latest report revision and wait for user response. |
| `## Phase 1 Approval Pending` block present BUT `pending_update_report.md` is missing on disk | STOP. Approval state corrupted (likely the file was manually deleted). Ask the user: (a) Restart the update from Phase 1 (deletes the folder and re-runs impact analysis), or (b) abandon the run (delete the approval block + reset `next_phase: -` and stop). Do NOT silently re-derive the report. |
| Per-device JSONL missing entry for current `run_id`      | Append a new entry; do not fail the skill.                                       |
| Path-registry logical name changed between runs          | Re-resolve from current registry; if path differs, ask user before continuing.   |
| Phase 2 Step 0 verification: a variant's final md TC counts ≠ that variant's `### Variant: <name>` sub-block in `## Phase 1 Summary` | **AUTO-RECOVERY (no user prompt):** Check if `process-logging/<UC-ID>/02_designed_tcs_<variant>.md` scratch exists. If yes → overwrite that variant's final md (same version) with content sourced from the scratch, then re-run Step 0 verification for that variant. If verification passes after recovery → proceed; report on chat that auto-recovery was triggered for variant `<name>` + the delta detected. |
| Phase 2 Step 0 verification: variant's final md mismatched AND `02_designed_tcs_<variant>.md` scratch is missing for that variant | STOP. No source of truth for auto-recovery of this variant. Report on chat that Phase 1 scratch for variant `<name>` never persisted (interrupt happened before Step 3.5 / Step 5.3 for that variant). User must Restart the skill (deletes `process-logging/<UC-ID>/` and re-designs from Phase 1). |
| Phase 2 Step 0 verification fails AGAIN after auto-recovery (scratch-sourced md still mismatches summary) for some variant | STOP. Both scratch and summary may be corrupt for this variant. Report on chat with the observed counts (summary vs scratch-sourced md) for the affected variant. User decides next action (manual inspection / Restart). |
| Phase 2 Step 3 (converter script) or Step 4 (xlsx self-verification) fails (mojibake, script error, missing prerequisites) for some variant | STOP. Do NOT run cleanup. The Phase 1 scratch + final md for that variant are preserved (and so are any already-produced xlsx for earlier variants). The user can re-trigger conversion after fixing the root cause; resume will re-run Phase 2 Step 0 + Steps 1–4 for all variants (idempotent on the variants that already converted, because Step 0 will simply pass). |
