---
name: qc-qna
description: Transfers Open questions from a UC review report's "Unified Gap & Question Report" table into the project's Question Backlog file for the BA to answer. Auto-triggered by qc-uc-read at end of first-audit Phase 3 and mid-flow during re-audit Phase 2 Step 5. Also user-invokable via /qc-qna <UC-ID> or phrases like "transfer questions", "chuyển câu hỏi cho BA".
---
# QC Q&A — Question Transfer Skill

## Purpose

Extract unresolved questions identified during UC review (the `### 📋 Unified Gap & Question Report` table inside the audited file) and transfer them into a dedicated **Question Backlog** file so Business Analysts (BAs) can track, answer, and confirm the missing information.

This skill is the **sole writer** of `question-backlog` files. Other skills (including `qc-uc-read`) MUST delegate backlog edits here.

## Trigger Conditions

- **Auto-trigger (end of run):** `qc-uc-read` first-audit Phase 3 invokes this skill immediately after writing `uc-review-report v[N].md`.
- **Auto-trigger (mid-flow):** `qc-uc-read` re-audit Phase 2 Step 5 invokes this skill to append newly-surfaced questions to the Open Questions section.
- **Manual:** `/qc-qna <UC-ID>`, or natural-language phrases such as "transfer questions for UC-X", "chuyển câu hỏi cho BA", "update question backlog".

## Input Contract

Resolve via `path-registry.md`:

- `uc-review-report` — the audited UC file. The caller may pass an explicit file path (auto-trigger mode); otherwise locate the **highest-version** audited file for `<UC-ID>` in the resolved folder.
- `question-backlog` — existing backlog file for `<UC-ID>` (highest version, if any).
- Template: `.claude/skills/qc-qna/templates/question-backlog_template.md` — clone source when no backlog exists yet.

## Output Contract

- **`question-backlog`** — created from template if missing (written into the same folder as the audited file); updated in-place if exists. Versioning follows `naming-convention.md`.
- **`worklog-per-device`** — log every phase boundary per the protocol at `docs/qc-lead/agent-work-log.local/README.md`. Do NOT touch the master `agent-work-log`.

## Workflow

### Phase 0 — Setup

1. Extract `<UC-ID>` from caller args / user prompt / audited filename. If multiple UCs share the audited file (group review), resolve `<UC-ID>` to the canonical group ID used in the dashboard.
2. Worklog: append new entry to the device's JSONL with `status = "Running (Phase 1)"`, `input = [<audited file path>]`, `start = now` (per the protocol).
3. Resolve the audited file:
   - If the caller passed an explicit path → use it.
   - Otherwise → locate the highest-version `uc-review-report` for `<UC-ID>` in the resolved folder.

### Phase 1 — Read Audited File

1. Open the audited file. Locate the section heading `Unified Gap & Question Report`.
2. Parse the table beneath it. Extract every row where `Status = Open` into an in-memory list of question objects:
   ```
   { ID, Priority, Ref, Question, "Why It Matters" }
   ```
3. If no `Open` rows exist, jump directly to Phase 4 with summary "No open questions to transfer."

### Phase 2 — Reconcile with Existing Backlog

1. Check for an existing `question-backlog` file (highest version) for `<UC-ID>`.
2. **If the backlog does NOT exist:**

   - Read the master template `.claude/skills/qc-qna/templates/question-backlog_template.md`.
   - Create a new file in the same folder as the audited file. Name per `naming-convention.md`:
     ```
     [UC-ID]_[feature-name]_questions_[YYYYMMDD]_v1.md
     ```
   - Populate the header (UC-ID, created date from current date, author from `userEmail` context if available, version `v1`).
3. **If the backlog EXISTS:**

   - Read its three sections: `## Open Questions`, `## Answered Questions`, `## Deferred Questions`.
   - For each ID in the audited Open list:
     - ID already in `Answered Questions` or has `Status = Resolved` in `Open Questions` → **SKIP and WARN** the user:
       *"⚠️ Q`<ID>` đã được BA trả lời nhưng audited report mới vẫn để Open. UC này cần re-audit qua `/qc-uc-read` để đồng bộ trạng thái."*
     - ID already in `Open Questions` with `Status = Open` → SKIP (already pending — no-op).
     - ID is NEW (not in any section of the backlog) → APPEND to `## Open Questions` table.
   - For each ID currently in backlog `Open Questions` whose ID is NOT in the audited Open list → **leave alone**. The BA may still answer them; `qc-uc-read` re-audit Phase 2 will reconcile resolved questions.

> ID Handling: keep the original IDs from the audited report (e.g., `Q1`, `Q2`) verbatim. They are stable across UC versions. Do NOT renumber.

### Phase 3 — Write

1. If new rows are being appended, remove any placeholder line `_(No open questions — all resolved.)_` from the `Open Questions` section.
2. Insert the new rows into the `## Open Questions` table, preserving column order:
   ```
   | ID | Priority | Ref | Question | Why It Matters | Status |
   ```

   New rows have `Status = Open` by default.
3. Write the backlog file.
   - **First-time create:** new file with version `v1`.
   - **Update existing:** in-place edit of the highest-version file (the backlog is a living document — does NOT bump version on every append).

### Phase 4 — Return

1. Worklog: rewrite last entry → `status = "Done"`, `output = [<backlog file path>]`, `end = now`, `duration_min = computed` (per the protocol).
2. Return a short summary to the caller (caller may be `qc-uc-read` or the user):
   ```
   ✅ Question transfer complete.
   - Backlog file: <path>
   - New questions appended: N (Q<id>, Q<id>, ...)
   - Already-pending (skipped): M
   - Conflicts (audited Open vs backlog Answered): K  →  ⚠️ recommend re-audit
   ```

   If `N = 0`, output a one-line note instead: *"No new questions to transfer — backlog already reflects audited report."*

## Boundaries

- This skill is the **sole writer** of `question-backlog` files. Other skills (incl. `qc-uc-read`) MUST delegate backlog edits here — they do not edit the Open Questions table directly.
- This skill does NOT modify the audited file (`uc-review-report`).
- This skill does NOT mark questions `Resolved` — that is `qc-uc-read` re-audit Phase 2's job (after the BA fills in answers).
- This skill does NOT create new question IDs — it only transfers IDs that already exist in the audited Unified Gap & Question Report table.
- If the audited file has no `Open` rows, exit silently with a one-line note. Do NOT touch the backlog file in that case.
- Output language follows source-input language per `global-rules.md`. Question text and Why-It-Matters content are copied **verbatim** from the audited report (no paraphrasing, no translation).
