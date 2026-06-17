# Workflow 3 — Render, Atomic Commit, Handoff, and Cleanup

## Goal

Render staged outputs, compare with existing files, commit safely, write dashboard handoff, invoke/suggest downstream sync, and clean internal checkpoints.

This workflow consolidates the old Phases 8–10.

---

## Inputs

- `00_run_control.md`
- `01_site_map_model.md` unless mode is Skipped
- `02_data_map_model.md` unless data map is explicitly skipped
- `templates/qc-site-map-template.vi.md`
- `templates/qc-data-map-template.vi.md`
- existing `qc-site-map.md` in Update mode
- existing `qc-data-map.md` in Update mode
- site-map handoff path:

```text
.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md
```

---

## Steps

### 3.1 Handle Skipped mode

If Workflow 0 set `mode = Skipped` because version preflight found no changes and user answered `no`:

1. Do not render staged outputs.
2. Do not touch existing `qc-site-map.md` or `qc-data-map.md`.
3. Do not delete or rewrite `site-map-handoff.md`.
4. Write checkpoint with `status = Skipped (preflight no-change)`.
5. Run cleanup of process logging folder after final response.

If `auto-chain-mode-3 = true`, do not treat Update skip as final; chain into Mode 3 after cleanup as requested by the user.

### 3.2 Render staged files

Render in memory first, then write staging files:

```text
.claude/skills/qc-site-map/process-logging/.staging-qc-site-map.md
.claude/skills/qc-site-map/process-logging/.staging-qc-data-map.md
```

Render `qc-site-map.md` from:

- `templates/qc-site-map-template.vi.md`;
- `01_site_map_model.md`;
- preserved reviewed content from existing site map;
- preserved `Folder alias(es)` and `Folder alias map`.

Render `qc-data-map.md` from:

- `templates/qc-data-map-template.vi.md`;
- `02_data_map_model.md`;
- preserved reviewed content from existing data map.

Do not touch the real output files during rendering.

### 3.3 Fill `Sources consolidated`

For each output, fill `Sources consolidated` with one row per file actually read for that output.

Columns:

```text
# | File | Version | Loại | Ngày đọc cuối
```

Rules:

- `File` is bare filename, no path.
- `Version` is `v<N>` from regex `_v(\d+)` or `no-version`.
- `Loại` classifies the document role.
- `Ngày đọc cuối` is today's date in `YYYY-MM-DD`.

### 3.4 Normalize for content comparison

When comparing staged vs existing output, normalize both first:

1. Strip `Ngày đọc cuối` values from every row of all `Sources consolidated` tables.
2. Normalize generated timestamp fields if present.
3. Normalize trailing whitespace.

Compute independently:

```text
siteMapChanged = normalize(staged_site_map) != normalize(existing_site_map)
dataMapChanged = normalize(staged_data_map) != normalize(existing_data_map)
```

In Initialization mode, missing file means changed.

### 3.5 Commit outputs safely

For each changed file:

1. Keep staged file intact until the real output is ready to replace.
2. If no existing file, atomically rename/copy staging to target path.
3. If existing file changed semantically:
   - preserve a safe backup only if project convention requires it;
   - replace target via atomic rename if possible;
   - if rename across filesystems fails, copy-then-verify-then-delete staging.
4. If not changed:
   - delete staging file;
   - do not touch the real file and do not churn mtime.

Never silently delete QC Lead-reviewed content. If a source item disappeared, mark it deprecated/not-found in the rendered content unless the user explicitly requests removal.

### 3.6 Write site-map handoff

Only write `site-map-handoff.md` when:

- Initialization mode; or
- Update mode and `siteMapChanged = true`; or
- `auto-chain-mode-3 = true` and Update produced a refreshed handoff for Mode 3 to overwrite later.

Do not write handoff when only `qc-data-map.md` changed.

Before writing a new handoff, delete the existing `site-map-handoff.md` if present. This prevents stale handoff from a cancelled prior run.

Handoff schema:

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

## Feature-level gaps

| Feature ID | Feature name | Gap | Impact to QC | Owner | Priority |
|---|---|---|---|---|---|

## Unmapped screens

| Screen ID | Screen / Page | Why unmapped | Suggested action |
|---|---|---|---|

## Dashboard update recommendation

| Feature ID | Recommended dashboard note/status | Reason |
|---|---|---|
```

Rules:

- Aggregate by feature/use case only.
- Never create one row per screen or module.
- `Feature ID` is the canonical Feature/Use Case ID.
- `Folder alias(es)` is blank/`—` when folder ID equals canonical feature ID.
- `Folder alias(es)` is non-empty only for Mode 3 or preserved alias mappings.
- `In scope?` is required for every row; use `Need confirm` if uncertain.
- Do not write `qc-dashboard.md` directly.

### 3.7 Data-map dashboard boundary

Do not write a data-map handoff in this version.

Do not invoke `qc-dashboard-sync` only because `qc-data-map.md` changed.

Report data-map readiness, entity gaps, CR impact notes, and hotspot findings in the final response for QC Lead.

### 3.8 Downstream action

Apply:

| Mode/result | Action |
|---|---|
| Initialization | Auto-invoke `qc-dashboard-sync` after writing site-map handoff. |
| Update + `siteMapChanged = true` + `auto-chain-mode-3 = false` | Suggest or ask user whether to run `/qc-dashboard-sync`. |
| Update + `siteMapChanged = true` + `auto-chain-mode-3 = true` | Do not invoke dashboard-sync; chain to Mode 3 after cleanup. |
| Update + `siteMapChanged = false` + `dataMapChanged = true` | No dashboard action. |
| Update + no semantic changes | No dashboard action. |
| Skipped | No dashboard action unless auto-chain Mode 3 was requested. |

Suggested prompt in Vietnamese for standalone Update with site-map change:

```text
qc-site-map.md vua duoc cap nhat. De cap nhat dashboard:
1. Chay /qc-dashboard-sync de re-sync feature list va trang thai 6 artifact.

Ban co muon chay /qc-dashboard-sync ngay bay gio khong? [yes/no]
```

If user answers `yes`, invoke `qc-dashboard-sync`. If `no`, finish; handoff remains available for manual re-run.

### 3.9 Output checkpoint

Write:

```text
.claude/skills/qc-site-map/process-logging/03_commit_handoff_cleanup.md
```

Include:

- mode;
- siteMapChanged yes/no;
- dataMapChanged yes/no;
- real `qc-site-map.md` committed yes/no/unchanged;
- real `qc-data-map.md` committed yes/no/unchanged;
- staging files cleaned up yes/no;
- handoff written yes/no;
- folder-alias entries preserved count;
- action: auto-invoked / suggested / asked-and-invoked / asked-and-skipped / chained-to-mode-3 / none;
- `qc-dashboard-sync` invocation result summary if invoked;
- cleanup result.

Update `progress.md`:

```md
- last_workflow_done: 3
- next_workflow: cleanup-or-mode-3
- status: Done / Skipped / ChainToMode3
```

### 3.10 Final summary and cleanup

Respond in Vietnamese with:

- Mode: Initialization / Update / Skipped.
- `qc-site-map.md`: created / updated / unchanged.
- `qc-data-map.md`: created / updated / unchanged.
- Sources consolidated: count of files, count with new version since last run.
- Site-map source quality: official / derived / partial.
- Number of screens found.
- Number of features with mapped screens.
- Number of unmapped screens.
- Data-map source quality: confirmed / derived / partial.
- Number of entities found.
- Number of relationships found.
- CRUD-role coverage: Ready / Partial / Blocked.
- Feature-entity coverage: Ready / Partial / Blocked.
- Dashboard handoff:
  - Initialization -> `qc-dashboard-sync` auto-invoked. Result: <summary>.
  - Update with site-map changes -> handoff written, user suggested/asked to run `/qc-dashboard-sync`.
  - Update with only data-map changes -> no dashboard action.
  - Update no change -> handoff not written, no downstream action.
- Major gaps/conflicts/assumptions.
- Suggested next action for QC Lead.

Cleanup rule:

Delete the entire `.claude/skills/qc-site-map/process-logging/` folder only after:

- final outputs are committed or confirmed unchanged;
- handoff decision is completed;
- final user summary is produced.

If cleanup fails, report it as non-blocking. Deliverables remain valid.

If `auto-chain-mode-3 = true`, run `workflows/mode-3-confirm-orphans.md` after cleanup and do not print a misleading final Update-only summary.
