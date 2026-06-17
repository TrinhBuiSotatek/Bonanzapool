# Workflow 0 — Run Control, Resume, Mode Detection, and Input Audit

## Goal

Resolve run mode, resume safely, verify prerequisites, detect source versions, and decide which outputs must be generated or updated.

This workflow consolidates the old Phase 0 and Phase 1. Do not run old phase files in new executions.

---

## Steps

### 0.1 Load checkpoint protocol

Read `workflows/checkpoint-protocol.md` for resume and cleanup rules.

Create or reuse a `run_id`.

Use canonical process logging folder:

```text
.claude/skills/qc-site-map/process-logging/
```

If `process-logging/qc-site-map/` exists from an older version, read it only for resume compatibility.

### 0.2 Resume detection

Check `progress.md`.

If found:

- Read `mode`, `last_workflow_done`, `next_workflow`, `status`, and `auto-chain-mode-3`.
- Resume from `next_workflow` if checkpoint files are present and consistent.
- Do not re-prompt the user for mode selection.
- If files are inconsistent, resume from the last safe workflow and record the inconsistency.

If no progress exists, continue as a fresh run.

### 0.3 Resolve paths

Read `path-registry.md` and resolve:

- `project-config.md`
- `project-context-master.md`
- `qc-site-map.md`
- `qc-data-map.md`
- `qc-dashboard.md`
- high-level BA/source folders
- requirement/spec folder
- wireframe folder
- API/DB/ERD/data folder if available
- CR/release note folder if available
- `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`
- `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md`

If a path cannot be resolved but a conventional location exists, use it and record the fallback. If neither exists for required outputs, STOP before writing.

### 0.4 Verify hard prerequisite

`project-context-master.md` MUST exist and contain real content.

If missing or unreadable, STOP with:

```text
Khong tim thay project-context-master.md. Hay chay /qc-context-master truoc khi chay /qc-site-map.
```

Do not continue to site-map or data-map build.

### 0.5 Compute mode signals

Compute:

- `siteMapExists`: resolved `qc-site-map.md` exists, byte length > 0, and has at least one markdown header.
- `dataMapExists`: resolved `qc-data-map.md` exists, byte length > 0, and has at least one markdown header.
- `orphanInboxExists`: `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` exists and parses to at least one non-empty data row in `Dashboard Orphan UC List for Site Map`.

### 0.6 Select mode

Apply:

| siteMapExists | orphanInboxExists | Action |
|:-:|:-:|---|
| No | Any | `mode = Initialization`. If orphan inbox exists, append a warning: orphans remain in inbox and will not be reconciled until site map exists. |
| Yes | No | `mode = Update`. If `dataMapExists = false`, set `data_map_submode = InitializationWithinUpdate`. |
| Yes | Yes | Prompt user to choose Mode 2 / Mode 3 / both. |

Prompt in Vietnamese:

```text
📋 Phat hien 2 trang thai dong thoi:
- qc-site-map.md ton tai (mode Update kha dung)
- .claude/skills/qc-site-map/inbox/dashboard-orphans.md ton tai (<N> orphan UC tu qc-dashboard-sync bottom-up)

Ban muon chay mode nao?
1. `mode 3` (mac dinh) — Confirm orphans: reconcile <N> orphan UC voi site-map hien tai, update handoff, trigger dashboard-sync.
2. `mode 2` — Update site map/data map tu source files, KHONG dong cham toi orphans.
3. `both` — Chay mode 2 truoc roi mode 3.
```

Parse case-insensitively:

- `mode 3`, `3`, empty, or unrecognized -> `mode = Mode3-ConfirmOrphans`; jump to `workflows/mode-3-confirm-orphans.md`.
- `mode 2`, `2`, `update` -> `mode = Update`; leave orphan inbox untouched.
- `both` -> `mode = Update`; set `auto-chain-mode-3 = true`; suppress Update's dashboard-sync invocation because Mode 3 will invoke it.

### 0.7 Version preflight in Update mode

Run only when `mode = Update`.

1. Read existing `qc-site-map.md` and existing `qc-data-map.md` if present.
2. Parse all `Sources consolidated` tables.
3. Build `prevSources = [{ file, version, source_output }]`.
4. For each previous source, scan relevant parent folders for the latest version using regex `_v(\d+)` on filename. If no version suffix, use `no-version`.
5. Also detect new relevant source files in source folders, especially official sitemap/menu/wireframe/API/DB/ERD/FRD/CR files not previously consolidated.
6. Classify per source: `same`, `upgraded`, `new-file`, `deleted`, `content-only-unknown`.
7. If at least one source is not `same`, continue.
8. If all sources are `same`, ask:

```text
Khong phat hien version moi cua cac source files da consolidated lan truoc.

Luu y: co che nay chi detect version qua ten file (regex _v<N>).
Neu ban da sua content ma khong tang version, hay tra loi yes de chay lai.

Ban co muon chay lai khong? [yes/no]
```

- `no` -> set `mode = Skipped`; jump to Workflow 3 cleanup without rendering/committing.
- `yes` -> continue.
- If `auto-chain-mode-3 = true`, do not skip Mode 3; continue or chain as requested.

### 0.8 Source audit

Detect and classify available source groups:

For site map:

- official site map;
- menu/navigation docs;
- feature/use-case list;
- wireframe index/screen list;
- user flow/journey;
- role/permission matrix;
- SRS/spec fallback folder;
- release notes/change logs.

For data map:

- backbone/use-case inventory;
- FRD/SRS per module;
- API spec;
- DB schema / ERD / data dictionary;
- data permission/classification/retention/audit policy;
- CR impact-assessment files.

Record only files that will actually be read into `sources_to_consolidate` with:

```text
file_name, version, document_group, source_quality, intended_output(site-map/data-map/both)
```

### 0.9 Output checkpoint

Write:

```text
.claude/skills/qc-site-map/process-logging/progress.md
.claude/skills/qc-site-map/process-logging/00_run_control.md
```

Minimum `progress.md`:

```md
# QC Site Map Progress

- run_id:
- mode: Initialization / Update / Mode3-ConfirmOrphans / Skipped
- data_map_submode: InitializationWithinUpdate / Update / Skipped / N/A
- last_workflow_done: 0
- next_workflow: 1
- status: Running / Skipped
- auto-chain-mode-3: false / true
- siteMapExists: true / false
- dataMapExists: true / false
- orphanInboxExists: true / false
- notes:
```

Minimum `00_run_control.md`:

- resolved paths;
- mode and data map submode;
- prerequisite result;
- source folders/files found;
- source groups missing;
- source versions and version-change findings;
- stop blockers;
- next workflow.
