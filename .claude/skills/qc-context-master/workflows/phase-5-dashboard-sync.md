# Phase 5 — Site Mapping + Feature List Handoff

> **Invoked by:** `SKILL.md` after Phase 4 (Carry-over) completes.
>
> **Prerequisites loaded into memory:** `04_carryover.md` (snapshot of §10 Open Questions), resolved path-registry logical names, templates.
>
> **Deliverables:**
> - Handoff file at `.claude/skills/qc-dashboard-sync/inbox/feature-list-handoff.md` (consumed by `qc-dashboard-sync`).
> - `qc-dashboard.md` updated via auto-trigger of `qc-dashboard-sync` (NOT written by this workflow directly).
>
> **Checkpoint produced:** `process-logging/05_deltas.md` + `progress.md` updated.
>
> **Worklog Status transitions:** `Running (Phase 5)` → `Phase 5 done`.
>
> **Ownership note:** As of the 2026-05-13 refactor, `qc-context-master` no longer writes the dashboard directly. It produces a feature list and hands off to `qc-dashboard-sync`, which is the sole owner of `qc-dashboard.md`.

---

## Step 0 — Worklog: enter phase

Update agent-work-log row: `Status = Running (Phase 5)`. Add any new Input file paths read in this phase.

## Step 1 — Read / initialize site abbreviation mapping

Read `.claude/skills/qc-context-master/state/site-abbreviations.md`. If missing, create with header:

```
# Site Abbreviations

> Auto-managed by qc-context-master. DO NOT edit manually.

| Full name | Abbreviation | First seen |
|---|---|---|
```

## Step 2 — Detect sites from common files

Scan WBS / Product Brief / Architecture Diagram for site/portal mentions (User, Admin, App, Mobile, Web, Vendor, ...). Normalize: trim + Title-case. For each site:
- Already in mapping → use stored abbreviation.
- New site, name ≤ 4 chars → use as-is, append to mapping.
- New site, name > 4 chars → ask user: `"Site '<full name>' viết tắt thành gì? (gợi ý: <first 4 chars>)"`. Append answer to mapping.

Site values from this mapping populate column 1 (Site) of the dashboard via handoff.

## Step 3 — Extract feature/UC candidates from common files

Extract candidates from WBS / Product Brief / SRS / business-rules. Each candidate is a tuple `(Site, ID, Module, Feature/Use case name, In scope?)`.

- `ID` is taken from the common file's own identifier (UC ID / Feature ID / Story ID — whatever the project uses).
- If a candidate has no explicit ID in source materials, generate one following the detected convention and bump the counter.
- `In scope?` defaults to `Yes` for fresh candidates. If a previous run flagged this ID as `No` / `Removed` and the candidate is still present in the WBS → set to `Yes` (re-add).

Result: `candidates = List<{ Site, ID, Module, Name, InScope }>`.

## Step 4 — Compute deltas vs current dashboard

1. Read current `qc-dashboard.md` if it exists. Build `existingIndex = Map<ID → row>`.
2. For each candidate:
   - ID ∈ existingIndex AND `existingIndex[ID].InScope = Removed` → mark as **re-add** (Status will be `Need confirm` when `qc-dashboard-sync` writes).
   - ID ∈ existingIndex AND `In scope? ≠ Removed` → no change; will skip handoff for this ID (manual edits to Module / Name / Site are preserved by the sync skill).
   - ID ∉ existingIndex → **new add**.
3. For each existing row whose ID is NOT in `candidates`:
   - `In scope? = Yes` → record as **soft-delete candidate** (the sync skill will not auto-Remove; it relies on disk-state). However, write a delta-report line so the user sees that WBS no longer mentions the ID.

> This workflow only **computes** the deltas — it does NOT modify the dashboard.

## Step 5 — Write the handoff file

Create or overwrite `.claude/skills/qc-dashboard-sync/inbox/feature-list-handoff.md`:

```markdown
---
source_skill: qc-context-master
run_id: <this run's run_id>
generated_at: <ISO-8601 datetime>
---

# Feature/UC list handoff

| ID | Site | Module | Feature/Use case name | In scope? |
|---|---|---|---|---|
| <ID> | <Site> | <Module> | <name> | Yes |
| ... | ... | ... | ... | ... |
```

Include only:
- New adds (rows not in existingIndex).
- Re-adds (rows previously `Removed`).

Do NOT include unchanged existing rows — the sync skill preserves them.

## Step 6 — Invoke `qc-dashboard-sync`

Invoke the `qc-dashboard-sync` skill via the Skill tool. The sync skill will:
1. Read the handoff file.
2. Merge it with disk-state observations.
3. Write `qc-dashboard.md`.
4. Delete the handoff file.

Wait for completion. Capture any user-confirmation outputs from the sync skill for the delta report.

## Step 7 — Report deltas to user

After the sync skill returns, output a short block summarizing what changed (this skill's perspective on candidate-level changes; the sync skill already reported its own perspective on disk-state changes):

```
**Feature list handoff (from `qc-context-master`):**
- Mới thêm vào WBS: <N> features (<list IDs>)
- Re-add (Removed → Need confirm): <N> features (<list IDs>)
- Không còn trong WBS (cần user kiểm tra): <N> features (<list IDs>) — `qc-dashboard-sync` không tự xóa; nếu folder cũng đã bị xóa thì sync skill sẽ đề nghị `In scope? = Removed`.
```

If none of the above happened, skip this output.

## Step 8 — Checkpoint write

Per `checkpoint-protocol.md` §4:

1. Write `process-logging/05_deltas.md` capturing the deltas block from Step 7 plus the detected `<ID label>` and current site abbreviations.
2. Update `process-logging/progress.md` → `last_phase_done: 5`, `next_phase: 6.1`.
3. Update agent-work-log row: `Status = Phase 5 done`. Add `.claude/skills/qc-dashboard-sync/inbox/feature-list-handoff.md` (transient) to Input. Add `qc-dashboard.md` to Output (indirectly written via `qc-dashboard-sync`).

## Step 9 — Hand back to SKILL.md

Return control. The next dispatch is `phase-6-extract-interview.md`.
