# Phase 9 - Atomic Commit + Dashboard Handoff

## Goal

Atomically commit the staged `qc-site-map.md` from Phase 8, write the feature-level handoff for `qc-dashboard-sync`, and decide whether to auto-invoke (Initialization) or only suggest to the user (Update with changes). Update-with-no-change exits without touching either the output file or the handoff.

> **Mode 3 (Confirm-Orphans) does NOT run this Phase 9.** Mode 3 has its own atomic-commit + handoff-write step at the end of `workflows/mode-3-confirm-orphans.md`. The schema below is shared, but the lifecycle rules differ (Mode 3 always rewrites the handoff and always auto-invokes dashboard-sync).

## Input

- Staging file: `process-logging/qc-site-map/.staging-qc-site-map.md` (from Phase 8)
- Existing real file (Update mode only): `qc-site-map.md` at the path resolved from `path-registry.md`

## Handoff path

```text
.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md
```

This file is the SOLE upstream feature list source for `qc-dashboard-sync` in top-down mode.

## Handoff lifecycle ownership

`qc-site-map` is the sole writer and sole deleter of this file. The lifecycle rule is:

- Before writing a new handoff, **always delete the existing `site-map-handoff.md`** if present (atomic overwrite, even though markdown). This ensures any stale handoff from a cancelled prior run is removed.
- `qc-dashboard-sync` MUST NOT delete this file. It only reads and consumes the content. The file persists on disk between runs so manual re-runs of `/qc-dashboard-sync` work without forcing the user to re-run the whole top-down chain.

## Handoff format

```md
---
source_skill: qc-site-map
handoff_type: site-map-feature-coverage
mode: initialization | update | mode-3-confirm-orphans
generated_at: <ISO-8601 datetime>
---

# Site Map Handoff for Dashboard

## Feature-level site map coverage

| Feature ID | Feature name | Site / Portal | Module | Mapped screen(s) | Folder alias(es) | In scope? | Site map status | Notes |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  | Yes / No / Need confirm | Mapped / Partial / Missing / Conflict / Need confirm |  |

## Feature-level gaps

| Feature ID | Feature name | Gap | Impact to QC | Owner | Priority |
|---|---|---|---|---|---|
|  |  | No mapped screen / unclear navigation / role access missing / source conflict |  | QC Lead / BA / Tech Lead | High / Medium / Low |

## Unmapped screens

| Screen ID | Screen / Page | Why unmapped | Suggested action |
|---|---|---|---|
|  |  |  |  |

## Dashboard update recommendation

| Feature ID | Recommended dashboard note/status | Reason |
|---|---|---|
|  | Site map: Ready / Partial / Missing / Conflict |  |
```

### Column definitions (Feature-level site map coverage)

- **Feature ID** — canonical Feature/Use case ID as known by `qc-site-map.md`. This is the value that goes into `qc-dashboard.md` column 2 `<ID label>`.
- **Module** - Grouping context only — never the row identity.
- **Folder alias(es)** — comma-separated list of folder-name IDs that map to this feature.
  - EMPTY (blank cell, e.g., `—`) when the folder on disk uses the same ID as `Feature ID`. This is the default for features defined directly by site-map sources.
  - NON-EMPTY only after Mode 3 has reconciled a folder whose on-disk name differs from the canonical ID. Example: `UC1_TrangChuDashboard` is a folder alias for canonical `UC-1`; in that case this cell holds `UC1_TrangChuDashboard` (the literal folder-name ID as it appears on disk).
  - The dashboard uses this column to fill its column 3 `Folder ID`. When multiple aliases exist for the same feature (rare), each alias gets its own dashboard row (sharing the same canonical Feature ID in column 2 but distinct Folder IDs in column 3) — this is handled by `qc-dashboard-sync`'s reconcile logic, not here.
- **In scope?** — authoritative scoping decision. `Yes` / `No` / `Need confirm`. This is the value that goes into `qc-dashboard.md` column 6.
  - For Initialization/Update modes: default `Yes` for features with `Site map status ∈ {Mapped, Partial}`, `Need confirm` for `Missing | Conflict | Need confirm`. The QC Lead can edit `qc-site-map.md` directly to override.
  - For Mode 3 Case 3 (new orphan-derived features): `Need confirm` initially; if Mode 3 collects enough info from the user to confidently scope it, may be set to `Yes`.
- **Site map status** — Mapped / Partial / Missing / Conflict / Need confirm. Diagnostic only — `qc-dashboard-sync` reads it for the Phase 0.5 gap surface but does NOT write it to any dashboard cell.

## Content comparison rule

When comparing the staging file against the existing real file, normalize both first:

1. Strip the `Ngày đọc cuối` (last column) values from every row of the `Sources consolidated` table (Section 2). The date naturally changes every run and is not a semantic change.
2. Compare the normalized byte content of the two files.

`contentChanged = (normalize(staging) != normalize(existing))`

## Behavior by mode

### Initialization mode

Trigger condition: the real `qc-site-map.md` did NOT exist at the resolved path before this run (no existing file to compare against).

1. **Commit staging → real:** atomically rename the staging file to the resolved `qc-site-map.md` path. (If rename fails because rename across filesystems is not supported by the host, fall back to copy-then-delete; ensure the final state has the real file present and staging deleted.)
2. If `site-map-handoff.md` already exists at the inbox path, DELETE it.
3. Write the new handoff file with `mode: initialization`. Most `Folder alias(es)` cells will be EMPTY at first run.
4. INVOKE `qc-dashboard-sync` via the Skill tool.
5. Capture the result returned by `qc-dashboard-sync` for the worklog.

### Update mode

Trigger condition: the real `qc-site-map.md` existed at the resolved path before this run.

1. Run the content comparison (see "Content comparison rule" above) between staging and existing real file. Set `contentChanged = true/false`.

2. **If `contentChanged == false` (no semantic change):**
   - DELETE the staging file (no real file touched, no mtime churn).
   - Do NOT delete or rewrite the existing real `qc-site-map.md` — it stays exactly as it was.
   - Do NOT delete or write `site-map-handoff.md`.
   - Do NOT suggest a downstream call.
   - Record `no content change, no downstream suggestion` in the checkpoint.

3. **If `contentChanged == true` (semantic change detected):**
   - DELETE the existing real `qc-site-map.md`.
   - Atomically rename the staging file to the resolved `qc-site-map.md` path.
   - If `site-map-handoff.md` already exists at the inbox path, DELETE it. Write the new handoff file with `mode: update`. **Preserve any existing `Folder alias(es)` values** that the prior site-map already recorded (parse the prior real `qc-site-map.md`'s Folder-alias section if present, carry forward unchanged aliases).
   - **If `auto-chain-mode-3 = true` (from Phase 0 user choosing `both`)** → do NOT invoke dashboard-sync, do NOT prompt. Instead, exit Phase 9 cleanly and signal Phase 10 to chain into Mode 3 right after cleanup. The handoff written here will be overwritten again by Mode 3 with reconciled aliases before dashboard-sync runs.
   - Otherwise (standalone Update run):
     - Append a suggestion to the final user response:

       ```text
       qc-site-map.md vua duoc cap nhat. De cap nhat dashboard:
       1. Chay /qc-dashboard-sync de re-sync feature list va trang thai 6 artifact.

       Ban co muon chay /qc-dashboard-sync ngay bay gio khong? [yes/no]
       ```

     - User answer `yes` → invoke `qc-dashboard-sync` immediately.
     - User answer `no` → finish without invoking. The suggestion remains in the final user summary.

## Safety rules

- If Phase 9 is interrupted between "DELETE existing real" and "rename staging → real", the staging file is still on disk and the run can be resumed from a checkpoint to retry the rename. The Phase 9 checkpoint records the state transition.
- The staging file is always cleaned up at the end of Phase 9 — either by rename (success) or by explicit delete (no-change case).
- If the staging file is missing when Phase 9 starts (e.g., resume after Phase 8 was interrupted), STOP and ask the user to re-run from Phase 8.

## Hard rules

- Do not send one row per screen as dashboard rows. Aggregate by feature/spec.
- If no feature-level mapping exists, still write the handoff (empty table is acceptable) but mark dashboard update as blocked/partial in the recommendation table.
- This phase MUST NOT write `qc-dashboard.md` directly.
- The `In scope?` column is REQUIRED for every feature row. Never write a blank value — use `Need confirm` if scope is uncertain.

## Output checkpoint

Write:

```text
process-logging/qc-site-map/09_dashboard_handoff.md
```

Include:

- mode: initialization | update
- content changed (update mode only): yes/no
- real file committed: yes/no
- staging file cleaned up: yes/no
- handoff written: yes/no
- folder-alias entries preserved from prior handoff (count): <N>
- action: auto-invoked | suggested | chained-to-mode-3 | none
- qc-dashboard-sync invocation result: <summary if invoked, else N/A>
