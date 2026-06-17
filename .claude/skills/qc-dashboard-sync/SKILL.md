---
name: qc-dashboard-sync
description: SOLE writer of qc-dashboard.md (all columns including stt). Step 3 of the top-down chain qc-context-master -> qc-site-map -> qc-dashboard-sync. This skill checks that subfolder for in-progress detection, and sparse-parses output files (audited reports, ui-elements files) for done-state — only when the on-disk version is NEWER than the cached version already in the dashboard cell (token-efficient). Operates in TWO modes, (1) Top-down — auto-invoked by qc-site-map. Requires project-context-master.md AND site-map-handoff.md. Syncs feature list + scans disk for 6 artifact types into Files stt + populates stt columns via in-progress check + sparse done-state derivation. (2) Bottom-up — manual invoke by user. Auto-sorts rows per a single-line `Sorting:` directive above the table (auto-generated on first write, user-editable thereafter).
---

# QC Dashboard Sync Skill

## Two operating modes

This skill operates in two modes that are mutually exclusive within a single run. **Both modes are triggered manually by the user** — per-UC skills no longer auto-invoke this skill.

| Mode | Triggered by | Scope | Gap review | Prerequisite |
|---|---|---|---|---|
| **Top-down** | auto-invoked by `qc-site-map` (Initialization + after Mode 3) | Full feature list + 6-artifact disk scan + in-progress check + sparse done-state parse for every UC | YES — surfaces site-map's gap tables (Feature-level gaps, Unmapped screens, Dashboard recommendation) and asks user proceed/cancel | `project-context-master.md` AND `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md` must both exist |
| **Bottom-up** | User runs `/qc-dashboard-sync` manually | Per UC: add rows with `Need confirm` if missing + 6-artifact disk scan + in-progress check + sparse done-state parse for that UC only + append to `dashboard-orphans.md` inbox of `qc-site-map` if folder not in site-map | NO | None — runs even if upstream context is missing |

The caller indicates the mode implicitly:
- Auto-invoked by qc-site-map → top-down
- Manual trigger by user → bottom-up for all ID that have new version or not existed in the current dashboard.

## Scope decision boundary

This skill does NOT decide `In scope?` business value. Its sole responsibilities:

- In top-down: copy `In scope?` from the site-map handoff (which is the authoritative source of feature scoping).
- In bottom-up: set `In scope? = Need confirm` for newly added rows, and forward the orphan UC ID to `qc-site-map` (via `dashboard-orphans.md`) so Mode 3 can either map it to an existing feature or add it as a new feature; the next top-down sync will then carry the correct scope value back.

No interactive `In scope?` prompts are emitted from this skill. The user can manually edit any row's `In scope?` cell at any time.

## Trigger Conditions

- **Manual bottom-up:** `/qc-dashboard-sync` — user manual invoke.
- **Auto-trigger top-down from `qc-site-map`** — at the end of its Phase 9, after writing `site-map-handoff.md`, in Initialization mode (or Update mode when the user accepts the prompt) and after Mode 3 reconciliation.

`qc-context-master` does not trigger this skill. The dashboard receives its feature list exclusively via `qc-site-map`'s `site-map-handoff.md`, and its stt columns via the in-progress check + sparse done-state derivation performed by this skill.

## Top-down prerequisites

In top-down mode this skill requires BOTH upstream artifacts to exist:

1. `project-context-master.md` resolved via `path-registry.md`.
2. `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md` written by `qc-site-map`.

If either is missing → STOP with the Vietnamese message:

```text
Không đủ điều kiện chạy top-down sync:
- project-context-master.md: <found | MISSING>
- site-map-handoff.md (tu qc-site-map): <found | MISSING>

Hãy chạy lại chuỗi theo thứ tự: /qc-context-master -> /qc-site-map -> /qc-dashboard-sync.
```

Do not fall through to bottom-up mode automatically — bottom-up is triggered only by per-UC skills with an explicit UC ID.

## Inputs

Resolve via `path-registry.md`:

| Logical name | Role | Used for |
|---|---|---|
| `qc-dashboard` | Dashboard markdown file. Created from template if missing. | Read/write target. |
| `project-context-master` | Project baseline. | **Top-down mode only** — existence check only (evidence that the chain ran in order: qc-context-master → qc-site-map → here). Content is NOT parsed for a competing feature list; the canonical feature list comes from `site-map-handoff.md`. |
| `requirement-files` | Parent folder; per-`<ID>` sub-folders. | Specs + WF scans. |
| `uc-review-report` | Parent folder; per-`<ID>` sub-folders. | Audited scan. |
| `func-test-scenarios` | Parent folder; per-`<ID>` sub-folders. | Scenario scan. |
| `func-test-cases-draft` | Parent folder; per-`<ID>` sub-folders. | TC md scan. |
| `func-test-cases` | Parent folder; per-`<ID>` sub-folders. | TC xlsx scan. |
| `requirement-common-files` | — | **Exclusion path** during orphan scan (its folder is not a UC). |

### Process-logging inputs (per-UC subfolder — existing checkpoint files)

The 4 per-UC skills already maintain checkpoint files in **per-UC subfolders** for their own resume-from-interruption logic. This skill does NOT require any new file or schema — it reuses the existing checkpoints purely as an **in-progress indicator**:

| Path pattern | Owner skill | Indicates |
|---|---|---|
| `.claude/skills/qc-uc-read/process-logging/<UC-ID>/progress.md` | `qc-uc-read` | A run is in-progress for that UC → `UC review stt` cell = current `status:` line |
| `.claude/skills/qc-func-scenario-design/process-logging/<UC-ID>/progress.md` | `qc-func-scenario-design` | In-progress → `Scenario design stt` cell = current `status:` line |
| `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/progress.md` | `qc-func-tc-design` | In-progress → `TC design stt` cell = current `status:` line |
| `.claude/skills/qc-ui-extract/process-logging/<UC-ID>/progress.md` | `qc-ui-extract` | In-progress → `UI extract stt` cell = current `status:` line |

**File existence semantics:** Each owner skill deletes its `<UC-ID>/` subfolder upon successful Phase 3 cleanup (per its `checkpoint-protocol.md` §5). So the file existing = the UC has an active or interrupted run; the file absent = either the UC has never been processed by that skill OR the skill finished successfully and cleaned up.

This skill does NOT modify these files. It only reads them for in-progress detection.

### Done-state derivation (when per-UC progress.md is absent)

When a per-UC subfolder progress.md does NOT exist, the UC is either never-started or fully-done. To distinguish + populate the cell without exhausting tokens by parsing every output file each run, this skill uses a **sparse-parse** strategy:

| stt column | Done-state source | Sparse-parse condition |
|---|---|---|
| `UC review stt` | The audited UC review report file (`<uc-review-report>/<Folder ID>/*_audited_*_v<N>.md`) — extract verdict + score from the "Tổng điểm" row of the scoring table | Only parse when `Audited: V<N>` from current Files stt scan is GREATER than `v<M>` parsed from the existing cell value. If versions match → keep cell verbatim (no parse). If no Audited file → cell BLANK. |
| `Scenario design stt` | The Files stt `Scenario: V<N>` value directly — no file parse | Always derive from Files stt (no content parse). Format: `v<N> generated`. If no Scenario file → cell BLANK. |
| `TC design stt` | The Files stt `TC xlsx: V<N>` value directly — no file parse | Always derive from Files stt. Format: `v<N> generated`. If TC xlsx missing but TC md exists → `v<N> draft`. If neither → cell BLANK. The historical `v<N> updated` value distinction (generate vs update workflow) is NO LONGER tracked — user can edit manually if desired. |
| `UI extract stt` | The UI extract output folder (`docs/qc/ui-elements/<Folder ID>/*_v<N>.md`) — count distinct page files; parse one of them for `audited_version` reference | Only parse when the latest ui-elements version (from filename) is GREATER than `v<M>` parsed from the existing cell value. Format: `v<N> (audited v<M>) [<Kp]` where K = page count (omit `[Kp]` if K=1). If folder missing → cell BLANK. |

**Cache extraction regex for existing cell values:**

- `UC review stt`: existing pattern `(?:Ready|Conditionally Ready|Not Ready)\s+v(\d+)\s*\(Score` → capture group 1 = cached audited version. If cell doesn't match → treat as cached version 0 (forces re-parse).
- `Scenario design stt` / `TC design stt`: `^v(\d+)\s+(generated|updated|draft)` → cached version. No "sparse" optimization needed since the source is Files stt (no file parse).
- `UI extract stt`: `^v(\d+)\s+\(audited` → cached ui-extract version.

**Audited file parse contract** (only used for `UC review stt` re-parse):

The scoring summary row in the audited report follows the pattern:

```
| **Tổng điểm** | **<score>/100** | **<verdict>** | <reason> |
```

where `<verdict>` ∈ {`Ready`, `Conditionally Ready`, `Not Ready`} and `<score>` is a number (integer or 1-decimal). Regex: `\|\s*\*+Tổng điểm\*+\s*\|\s*\*+(\d+(?:\.\d+)?)/100\*+\s*\|\s*\*+(Ready|Conditionally Ready|Not Ready)\*+\s*\|`.

Implementation hint: use `grep -n "Tổng điểm" <audited file>` to locate the line, then read just that line + the next column-value row via `head`/targeted Read — DO NOT load the whole report into context.

Composed cell value: `<verdict> v<auditedVersion> (Score <score>/100)` — matches existing dashboard format.

### Top-down handoff input (from `qc-site-map`)

- **Handoff file** at `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md`. REQUIRED in top-down mode. Schema (written by `qc-site-map` Phase 9):

  ```markdown
  ---
  source_skill: qc-site-map
  handoff_type: site-map-feature-coverage
  mode: initialization | update
  generated_at: <ISO-8601 datetime>
  ---

  # Site Map Handoff for Dashboard

  ## Feature-level site map coverage
  | Feature ID | Feature name | Site / Portal | Module | Mapped screen(s) | Folder alias(es) | In scope? | Site map status | Notes |
  ...

  ## Feature-level gaps
  ## Unmapped screens
  ## Dashboard update recommendation
  ```

  - `Feature ID` = canonical ID in site-map (will be written to dashboard column 2 `<ID label>`).
  - `Folder alias(es)` = comma-separated list of folder-name IDs (as they appear on disk) that map to this feature. EMPTY means the folder ID equals the Feature ID (default case for top-down rows). NON-EMPTY means `qc-site-map` Mode 3 has reconciled a prior orphan and confirmed the folder belongs to this feature; the dashboard updates row(s) with matching `Folder ID` cell to the canonical Feature ID while keeping `Folder ID` as the alias.
  - `In scope?` = `Yes` / `No` / `Need confirm` — authoritative scope value decided upstream (by `qc-site-map` Mode 3 user prompts or by site-map content alone). Dashboard copies this value verbatim into column 6.
  - `Site map status` = `Mapped | Partial | Missing | Conflict | Need confirm` — diagnostic from site-map; surfaced to user in Phase 0.5 but NOT written to any dashboard cell.

  This skill READS the file but does NOT delete it. Lifecycle is owned by `qc-site-map` (which overwrites it on its next run). Only the `Feature-level site map coverage` table provides the canonical feature list — the other tables (`Feature-level gaps`, `Unmapped screens`, `Dashboard update recommendation`) are surfaced to the user in Phase 0.5.

### Bottom-up input (from per-UC skills)

- Single `uc_id` parameter (e.g., `UC-100`). No handoff file. Pure disk scan of that specific UC's folders.
- Bottom-up extracts the **folder ID** from the on-disk folder name (regex; see Phase 1) and uses it for BOTH dashboard column 2 `<ID label>` and column 3 `Folder ID` until `qc-site-map` Mode 3 reconciles a canonical ID for it.

### Bottom-up output handoff (to `qc-site-map`)

- **Orphan list file** at `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`. Written (created if missing, appended if exists) every time bottom-up adds a brand-new row.
- Lifecycle: this skill is the sole **writer**; `qc-site-map` Mode 3 is the sole **deleter** (it consumes and removes the file after reconciliation). Append-and-dedupe semantics: if an entry with the same `Folder ID` already exists, do NOT add a duplicate row — update `Detected at` to the latest ISO timestamp instead.
- Schema:

  ```markdown
  ---
  source_skill: qc-dashboard-sync
  handoff_type: dashboard-orphan-uc-list
  generated_at: <ISO-8601 datetime>
  ---

  # Dashboard Orphan UC List for Site Map

  > Per row: a UC folder detected on disk via bottom-up that is NOT in the latest site-map handoff. `qc-site-map` Mode 3 must review each entry and either map it to an existing feature (Case 1/2) or add it as a new feature (Case 3).

  | Folder ID | Folder paths (per source) | Files stt | Detected at |
  |---|---|---|---|
  | <ID extracted from folder name> | requirement-files: <path>; uc-review-report: <path>; ... | Specs: V1<br>Scenario: V1 (or `No files yet`) | <ISO-8601 datetime> |
  ```

### Template

- `templates/qc-dashboard-template.md` — used to bootstrap the dashboard when it does not exist.

## Schema (10 baseline columns + optional self-injected columns)

### Baseline (10 columns — always present)

`qc-dashboard-sync` is the SOLE writer of all 10 baseline columns. The data SOURCE for each column appears in the "Source" sub-column. stt columns use a 2-step source: in-progress check (per-UC subfolder progress.md existence) → done-state derivation (output file sparse parse OR Files stt mapping).

| # | Column | Writer | Data source |
|---|---|---|---|
| 1 | `Site` | `qc-dashboard-sync` | site-map handoff (top-down) / blank (bottom-up) |
| 2 | `<ID label>` | `qc-dashboard-sync` | site-map handoff canonical ID / folder ID (bottom-up unreconciled) |
| 3 | `Folder ID` | `qc-dashboard-sync` | on-disk folder name extraction |
| 4 | `Module` | `qc-dashboard-sync` | site-map handoff (top-down) / blank (bottom-up) |
| 5 | `Feature/Use case name` | `qc-dashboard-sync` | site-map handoff (top-down) / blank (bottom-up) |
| 6 | `In scope?` | `qc-dashboard-sync` | site-map handoff verbatim (top-down) / `Need confirm` (bottom-up new row) |
| 7 | `Files stt` | `qc-dashboard-sync` | disk scan (6 artifact types) |
| 8 | `UC review stt` | `qc-dashboard-sync` | (in-progress) `qc-uc-read/process-logging/<UC-ID>/progress.md` status / (done) sparse parse of latest audited file |
| 9 | `Scenario design stt` | `qc-dashboard-sync` | (in-progress) `qc-func-scenario-design/process-logging/<UC-ID>/progress.md` status / (done) derived from Files stt `Scenario: V<N>` |
| 10 | `TC design stt` | `qc-dashboard-sync` | (in-progress) `qc-func-tc-design/process-logging/<UC-ID>/progress.md` status / (done) derived from Files stt `TC xlsx`/`TC md` version |

### Optional columns

| Order if present | Column | Writer | Data source |
|---|---|---|---|
| 11 | `UI extract stt` | `qc-dashboard-sync` | (in-progress) `qc-ui-extract/process-logging/<UC-ID>/progress.md` status / (done) sparse parse of latest ui-elements file at `docs/qc/ui-elements/<UC-ID>/` |
| 12 (or 11 if no UI extract) | `Execute stt` | future `qc-execute` skill (placeholder) | (not yet implemented) |

`UI extract stt` is auto-injected by this skill in Phase 5 if `docs/qc/ui-elements/` contains at least one `<UC-ID>/` subfolder with extracted files AND the column is missing from the dashboard header. `Execute stt` remains a manual user-injection placeholder until the future `qc-execute` skill exists.

Valid column counts: **10** (baseline), **11** (with `UI extract stt` only, or `Execute stt` only), **12** (both). `qc-dashboard-sync` accepts any of these.

### `Folder ID` column semantics

The `Folder ID` is the link between the dashboard row and the on-disk folder name. It is REQUIRED for every row.

| Row origin | Column 2 `<ID label>` | Column 3 `Folder ID` |
|---|---|---|
| Top-down, normal | Canonical Feature ID from handoff | Same as column 2 (the folder on disk uses the canonical ID) |
| Top-down, reconciled alias | Canonical Feature ID from handoff | Original folder-extracted ID (the alias) — taken from handoff's `Folder alias(es)` column |
| Bottom-up, freshly added | Folder-extracted ID (same as Folder ID, until reconciled) | Folder-extracted ID |
| Bottom-up, later reconciled by Mode 3 (Case 1/2) | Canonical Feature ID from updated handoff | Folder-extracted ID (kept verbatim) |
| Bottom-up, later reconciled by Mode 3 (Case 3 = new feature) | New canonical Feature ID minted by site-map | Folder-extracted ID (kept verbatim, may equal canonical) |

Disk scan in Phase 1 always matches a folder back to a row via `Folder ID` — never via `<ID label>`. Two rows MUST NOT share the same `Folder ID`.

## Outputs

- **`qc-dashboard`** — this skill is the **SOLE writer of every column** (creates + structures + maintains the file). Writes columns **1, 2, 3, 4, 5, 6, 7** from site-map handoff + disk scan, and columns **8, 9, 10, 11** via in-progress check (per-UC subfolder progress.md) + sparse done-state derivation (output file parse or Files stt mapping). Preserves `Execute stt` (col 12) verbatim from user edits (no current owner skill writes it).
- **`Sorting:` directive line** — single line above the table header. Auto-generated on first write; respected verbatim on subsequent runs (user edits preserved unless the level no longer applies — see "Sort order directive").
- **`dashboard-orphans.md`** — at `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`. Written (append + dedupe by Folder ID) every time top-down detects an orphan folder OR bottom-up adds a brand-new row. Sole consumer + deleter is `qc-site-map` Mode 3.
- Console report: new rows, Files-stt updates, stt updates, orphans appended, sort decision, summary.
- `worklog-per-device` — log every phase boundary per the protocol at `docs/qc-lead/agent-work-log.local/README.md`. Do NOT touch the master `agent-work-log`.

## `Files stt` cell format

Single-cell. Lists only the artifact types that were FOUND on disk; absent types are OMITTED (no `Missing` line). Lines are joined by `<br>` and appear in this fixed order (skipping any absent type):

```
Specs: V<N>
WF: V<N>
Audited: V<N>
Scenario: V<N>
TC md: V<N>
TC xlsx: V<N>
```

Rendered examples:
- Some files found:
  ```
  Specs: V2<br>WF: V1<br>Scenario: V1<br>TC md: V2
  ```
- No files found at all (after scan):
  ```
  No files yet
  ```

Use `V<N>` (capital V) where `<N>` is the highest version detected. When the scan finds NO artifact across all 6 types, write the literal string `No files yet` as the sole cell content.

## Process-log parse contract

Per-UC subfolder progress.md format is OWNED by each owner skill (see their respective `workflows/checkpoint-protocol.md` files). This skill ONLY reads `status:` line — best-effort — and does NOT require any schema change from the owner skill.

### Parse algorithm (in-progress detection)

For each row + each per-UC skill, with `<UC-ID>` = the row's `Folder ID`:

1. Check if `.claude/skills/<skill>/process-logging/<UC-ID>/progress.md` exists.
2. If NO → fall through to done-state derivation (see "Done-state derivation" section above).
3. If YES → read the file (small, single-state overwrite per checkpoint protocol). Extract the `status:` line via regex `^[-*]?\s*status\s*:\s*(.+)$` (case-insensitive). If found → cell value = the captured raw status string verbatim (e.g., `Running — Phase 3`, `Phase 3 done`).
4. If progress.md exists but has no `status:` line → cell value = `Running (status không xác định)` and emit a warning in the Phase 6 report.

### Best-effort tolerance

- Free-form markdown bullets, frontmatter, or comments are all tolerated. The skill only cares about the `status:` key.
- If parsing fails entirely → cell value = `Running (parse failed)` and emit a warning.
- This skill NEVER writes to any per-UC subfolder progress.md. The owner skill remains the sole writer.

## Sort order directive

Above the dashboard header table, this skill writes (and respects on re-run) a single-line directive:

```
Sorting: <value1> >> <value2> >> <value3>
```

### Purpose

Controls row order. The user can edit the directive at any time; subsequent runs honor the edited order.

### Auto-generation logic (Phase 5)

1. Compute `distinctSites = set of column 1 values` and `distinctModules = set of column 4 values` across all rows.
2. **Pick the sort level:**
   - If `len(distinctSites) > 1` → sort level = `Site` (column 1).
   - Else if `len(distinctModules) > 1` → sort level = `Module` (column 4).
   - Else → no `Sorting:` line written (single-module case; rows default to ascending by canonical ID).
3. **Compose values:** alphabetical ascending of the distinct values at the chosen level. This is the default ordering on first generation.
4. Write `Sorting: v1 >> v2 >> v3` immediately above the table header (separated from the surrounding markdown by a blank line on each side).

### Re-run logic (Phase 5)

1. Parse the existing dashboard. Look for `^Sorting:\s*(.+)$` anywhere above the table header line.
2. If found, split the value list by `>>` (trim each token). Call this `userSortList`.
3. Determine which column `userSortList` refers to by majority-match:
   - Count how many tokens of `userSortList` are members of `distinctSites`. Call this `siteMatches`.
   - Count how many tokens are members of `distinctModules`. Call this `moduleMatches`.
   - The level with the larger match count wins; ties go to `Site` (higher level).
4. **Determine if regeneration is needed:**
   - If the picked level disagrees with the auto-generation logic above (e.g., user wrote module names but auto would pick `Site` since `distinctSites > 1`) → respect the user's level. The user can intentionally sort by Module within a multi-portal project.
   - If `userSortList` is missing some values that exist on disk → append the missing values alphabetically at the end of `userSortList`, then rewrite the `Sorting:` line. Print a notice.
   - If `userSortList` contains values no longer on disk → drop them. Print a notice.
   - If `userSortList` matches NEITHER `distinctSites` nor `distinctModules` (zero matches) → log a warning and fall back to auto-generation; overwrite the `Sorting:` line.
5. **Apply sort:**
   - Group rows by their value at the chosen sort level, in the order given by `userSortList`. Rows whose level-value is not in `userSortList` (after step 4 append) go last in alphabetical order.
   - Within each group, sort by the next-lower level alphabetically (e.g., if sort level is `Site`, sub-sort by `Module` ascending; then by canonical ID ascending).
   - Levels below the sort level are NEVER written into the directive — they always default to ascending by canonical ID.

### Single-module / single-portal case

When neither Site nor Module has more than 1 distinct value, the `Sorting:` line is NOT written. The skill removes any pre-existing `Sorting:` line in that case (with a notice) and sorts rows by canonical ID ascending.

## Workflow

The workflow below is the **top-down workflow** (Phases 0 → 0.5 → 0.6 → 1 → 2 → 3a → 3b → 4 → 5 → 6). For bottom-up, see the dedicated section after Phase 6.

### Phase 0 — Mode detection, prerequisites & input parse

This phase is purely read-only. No dashboard file is created or modified here; that happens in Phase 0.6 after the user reviews the gap report.

1. Generate a new `run_id` per the worklog protocol. Worklog: append new entry to the device's JSONL with `status = "Running (Phase 0)"`, `input`/`output` empty, `start = now`.
2. **Mode detection:**
   - Caller passed `uc_id=<ID>` → switch to bottom-up workflow (see section "Bottom-up workflow"). Skip the rest of Phase 0 in this top-down workflow.
   - Otherwise → top-down.
3. **Top-down prerequisite check:**
   - Resolve `project-context-master` path from `path-registry.md`. Verify the file EXISTS with real content. (Content is not parsed here — its presence is only required as evidence that the top-down chain ran in order. The canonical feature list comes from the site-map handoff.)
   - Verify `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md` exists.
   - If either is missing → STOP with the Vietnamese message defined in "Top-down prerequisites" above. Do not fall through to bottom-up.
4. **Parse the site-map handoff file.**
   - Parse the `Feature-level site map coverage` table into `handoffList = Map<FeatureID → { Site, Module, Name, MappedScreens, FolderAliases[], InScope, SiteMapStatus, Notes }>`. The `Feature ID` column maps to FeatureID; `Feature name` to Name; `Site / Portal` to Site; `Module` to Module; `Folder alias(es)` parsed as a comma-separated list (empty list if blank); `In scope?` to InScope (copied verbatim — values `Yes`, `No`, `Need confirm`); `Site map status` to SiteMapStatus (diagnostic; surfaced in Phase 0.5 but NOT written to a dashboard cell).
   - Build `aliasIndex = Map<FolderID → FeatureID>` from the `FolderAliases` lists — for each (FeatureID, alias) pair, record `aliasIndex[alias] = FeatureID`. If a FeatureID has no aliases declared, treat the FeatureID itself as its own folder ID (i.e., `aliasIndex[FeatureID] = FeatureID`). If the same alias appears under two different FeatureIDs → STOP with a Vietnamese error message (`Loi: folder alias <X> duoc khai bao trung lap o site-map-handoff cho ca hai feature <A> va <B>. Vui long sua qc-site-map.md hoac chay lai qc-site-map Mode 3.`).
   - Parse the `Feature-level gaps`, `Unmapped screens`, and `Dashboard update recommendation` tables — keep them as `siteMapGaps`, `unmappedScreens`, `dashboardRecommendations` for Phase 0.5.
5. Resolve `qc-dashboard` path from `path-registry.md`. **Do NOT create or write the file yet.**
   - If the dashboard file EXISTS: parse it now (header → `existingLabel`; data rows → `featureIndex` keyed by canonical ID in column 2; notes block captured verbatim). Detect the schema variant and apply auto-migration when needed:

     | Detected schema | Action |
     |---|---|
     | **Baseline 10 cols** (`Site | <ID> | Folder ID | Module | Name | In scope? | Files stt | UC review stt | Scenario design stt | TC design stt`) | Proceed normally. Existing stt cells (cols 8/9/10) are KEPT (cached values needed for sparse-parse comparisons in Phase 3b); they will be OVERWRITTEN in Phase 5 only when the corresponding source has a newer version. |
     | **11 cols** = baseline + (`UI extract stt` OR `Execute stt`) after `TC design stt` | Proceed normally. `UI extract stt` cached value kept for sparse-parse; `Execute stt` is preserved VERBATIM into `featureIndex[ID].executeStt`. |
     | **12 cols** = baseline + both `UI extract stt` and `Execute stt` (in that order) after `TC design stt` | Proceed normally. `UI extract stt` cached for sparse-parse; `Execute stt` preserved verbatim. |
     | **Legacy v10** (10 cols WITHOUT `Folder ID`, header `Site | <ID> | Module | …`) | AUTO-MIGRATE: insert `Folder ID` at position 3 = column 2 self-reference; shift rest right. |
     | **Legacy v11-old** (header contains `Specs stt`, `WF stt`, `Test scenario stt`, `Test cases stt` as separate columns — typical pre-consolidation shape: `Site | <ID> | Module | Name | In scope? | Specs stt | WF stt | Test scenario stt | Test cases stt | [UI extract stt] | [Execute stt]`) | AUTO-MIGRATE per "Legacy v11-old → new" steps below. |
     | **Other** (wrong header order, unknown column names, can't classify) | STOP and report. Do NOT auto-fix. |

     **Legacy v10 → new** migration steps (in-memory):
     1. Insert `Folder ID` column at position 3 in the header.
     2. For every data row, insert cell at position 3 = column 2's value (self-reference).
     3. Append migration note:
        ```text
        > **<YYYY-MM-DD> — Schema migration v10→new**: cot `Folder ID` da duoc them tu dong, gia tri = cot `<ID label>` (self-reference). Mode 3 cua qc-site-map se update gia tri khi reconcile orphan voi alias mapping khac.
        ```
     4. Print: `Da auto-migrate dashboard: them Folder ID = self-reference cho <N> row.`

     **Legacy v11-old → new** migration steps (in-memory, purely STRUCTURAL — values of the 4 file cols are DROPPED, not transformed, because the new `Files stt` format requires a fresh disk scan):
     1. Header transformation:
        - Insert `Folder ID` at position 3.
        - Replace the 4 cols (`Specs stt`, `WF stt`, `Test scenario stt`, `Test cases stt`) with a single `Files stt` column at position 7.
        - Insert `UC review stt`, `Scenario design stt`, `TC design stt` at positions 8, 9, 10.
        - Preserve `UI extract stt` if present (becomes col 11 optional).
        - Preserve `Execute stt` if present (becomes col 11 if no UI extract, or col 12).
     2. For every data row:
        - Insert col 3 = col 2 (self-reference).
        - Set col 7 `Files stt` = EMPTY (force next sync to populate via fresh scan).
        - Set cols 8, 9, 10 = EMPTY (no prior process-state values existed).
        - Carry over `UI extract stt` value if column existed.
        - Carry over `Execute stt` value if column existed.
     3. Append migration note:
        ```text
        > **<YYYY-MM-DD> — Schema migration v11-old→new**: hop nhat 4 cot (`Specs stt`, `WF stt`, `Test scenario stt`, `Test cases stt`) thanh `Files stt` (cell trong, se duoc populate bang next sync); them `Folder ID`, `UC review stt`, `Scenario design stt`, `TC design stt`. Cac cot stt (8/9/10/11 neu co `UI extract stt`) se duoc populate tu in-progress check + sparse done-state derivation o Phase 3b. Cot `Execute stt` neu co duoc giu lai verbatim. Gia tri 4 cot file cu duoc DROP (khong transform) vi format moi yeu cau scan lai.
        ```
     4. Print: `Da auto-migrate dashboard tu v11-old sang schema moi (<N> row, <K> cot optional duoc giu).`
     5. Continue Phase 0 with the migrated in-memory state. The actual file write happens in Phase 5.

   - If the dashboard file does NOT exist: skip parsing. `featureIndex` is empty. The `<ID label>` will be determined in Phase 0.6 from the handoff and a user prompt.

   Build `folderIDIndex = Map<FolderID → FeatureID>` from `featureIndex` (column 3 → column 2) so Phase 1 can match observed folders back to existing rows even when the on-disk folder uses an alias.
6. **Detect ID label mismatch** (only when dashboard already exists):
   - Compute `handoffDominantPrefix` by scanning the `Feature ID` column of `handoffList` — pick the most common prefix among `UC`, `F`, `FEAT`, `STORY`, `S`. Map it to `expectedLabel` (`UC` → `Use Case ID`, `F`/`FEAT` → `Feature ID`, `S`/`STORY` → `Story ID`).
   - Compare `existingLabel` against `expectedLabel`.
   - If they differ → set `labelMigrationNeeded = true` and remember `(existingLabel, expectedLabel)` for Phase 0.6 + Phase 5.
   - Rationale: top-down is the canonical source. If the dashboard was originally bootstrapped by bottom-up with default `Use Case ID` but the handoff uses `F-` IDs, the top-down label wins.

Update worklog: `Status = Phase 0 done`.

### Phase 0.5 — Site-map gap review (top-down only)

`qc-site-map` already performs the upstream consistency analysis (site-map content vs `project-context-master.md`) when it builds its handoff. The gap report and unmapped screens are surfaced verbatim from the handoff — this skill does NOT redo the comparison.

1. Read the three secondary tables captured in Phase 0 step 4: `siteMapGaps`, `unmappedScreens`, `dashboardRecommendations`.
2. If ALL three are empty → skip the prompt, jump to Phase 0.6.
3. Otherwise, present a consolidated report and ask the user to proceed or cancel:

   ```text
   📋 Bao cao tu site-map-handoff.md (do qc-site-map tao):

   **Feature-level gaps (<N> mục):**
   | Feature ID | Feature name | Gap | Impact to QC | Owner | Priority |
   |---|---|---|---|---|---|
   | ... | ... | No mapped screen / unclear navigation / role access missing / source conflict | ... | QC Lead / BA / Tech Lead | High / Medium / Low |

   **Unmapped screens (<N> mục):** (screens chưa map được vào feature nào — sẽ KHÔNG tạo dashboard row)
   | Screen ID | Screen / Page | Why unmapped | Suggested action |
   |---|---|---|---|
   | ... | ... | ... | ... |

   **Dashboard update recommendation (<N> mục):**
   | Feature ID | Recommended note/status | Reason |
   |---|---|---|
   | ... | Site map: Ready / Partial / Missing / Conflict | ... |

   👉 Lua chon:
   - `proceed` — chay sync voi du lieu hien tai. Cac gap nay duoc bao luu trong site-map-handoff.md va qc-site-map.md de QC Lead theo doi rieng; dashboard.md chi giu feature list va Files stt.
   - `cancel` — dung sync. Xem xet sua tai lieu upstream (chay /qc-context-master hoac /qc-site-map) roi chay lai /qc-dashboard-sync.
   ```

4. User answers `cancel` → STOP. Worklog: `Status = Cancelled (Phase 0.5 gap review)`. **No dashboard file was created or modified in Phase 0**, so nothing to roll back.
5. User answers `proceed` → continue to Phase 0.6. The dashboard schema does NOT have a Notes column; gap data is informational at this prompt only.

Update worklog: `Status = Phase 0.5 done`.

### Phase 0.6 — Bootstrap or relabel dashboard

Only executed AFTER Phase 0.5 user proceeds. Splitting this out of Phase 0 ensures a cancelled run never leaves an empty dashboard on disk.

Two sub-cases:

**A. Dashboard MISSING — bootstrap:**

1. Read `templates/qc-dashboard-template.md`.
2. Determine the `<ID label>`: use `expectedLabel` derived from handoff dominant prefix (computed in Phase 0 step 6). Confirm with the user: `"Ten cot dinh danh trong dashboard nen la gi? (mac dinh: <expectedLabel>. Goi y khac: Use Case ID / Feature ID / Story ID)"`. Accept user's override.
3. Replace placeholder `{{ID_LABEL}}` in the template (header + notes section) with the chosen label.
4. Write the populated template to the resolved `qc-dashboard` path. The body table is empty at this point.
5. Re-parse the freshly written dashboard so `featureIndex` is initialized (empty map) and `<ID label>` is captured verbatim for write-back. Run schema validation.

**B. Dashboard EXISTS with `labelMigrationNeeded == true` — relabel:**

1. Do NOT prompt the user. Top-down is canonical: silently migrate.
2. In-memory only (the actual write happens in Phase 5):
   - Set `<ID label>` to `expectedLabel`.
   - Append a migration note to be inserted into the ghi-chú block in Phase 5:

     ```text
     > **<YYYY-MM-DD> — ID label migration**: dashboard duoc re-label tu `<existingLabel>` sang `<expectedLabel>` do site-map-handoff dung prefix `<handoffDominantPrefix>` lam canonical. Cac row pre-existing co ID o dang cu duoc giu nguyen (khong auto-rename). Neu can map sang ID prefix moi, QC Lead vui long doi chieu manual voi qc-site-map.md hoac project-context-master.md. Co the ghi tracking note dang `(orig: <old-ID>)` ngay sau cot `Feature/Use case name` cua row tuong ung.
     ```
3. `featureIndex` (parsed in Phase 0 step 5) is kept as-is; existing rows retain their original ID values in column 2. Phase 1 disk scan + Phase 2 reconcile will still pick up new handoff rows correctly using the handoff's own IDs.

**C. Dashboard EXISTS with `labelMigrationNeeded == false`:** skip Phase 0.6 entirely.

Update worklog: `Status = Phase 0.6 done`.

### Phase 1 — Disk Scan (collect observed IDs)

1. Resolve the parent folders (portion before `<UC-ID>`) of these 5 path-registry logical names — these are the on-disk sources for orphan detection:
   - `requirement-files` (covers Specs + WF)
   - `uc-review-report` (covers Audited)
   - `func-test-scenarios` (covers Scenario)
   - `func-test-cases-draft` (covers TC md)
   - `func-test-cases` (covers TC xlsx; skip if same parent as `func-test-cases-draft`)
   For each existing parent folder, list immediate sub-folder names.

2. **Exclude + extract Folder ID from each sub-folder name** using a regex list built dynamically from the project's actual ID patterns. Different sources may name the same UC differently — e.g., BA uses compound names like `UC-CLY-005_LoyaltyRules` or `UC1_TrangChuDashboard`, while QC uses bare IDs like `UC-CLY-005` or `UC1`. A single dự án may use multiple ID formats simultaneously (e.g., `UC-CLY-005` for new modules + legacy `F-100`). The skill MUST extract a `Folder ID` and use it as the link to the dashboard row (column 3).

   **Step 2a — Build `regexList` (dynamic pattern detection):**
   - Source IDs for pattern detection:
     - Top-down: all `Feature ID` values from `handoffList` (Phase 0 step 4) PLUS all column 2 values from existing `featureIndex`.
     - Bottom-up: the single `uc_id` passed by caller.
   - For each source ID, compute its **shape signature**:
     - Split the ID by `-` and `_` into tokens.
     - Classify each token as `L` (all-letters), `N` (all-digits), or `M` (mixed — rare; treat as `L`).
     - Signature = tokens joined by their original separator (vd: `UC-CLY-005` → `L-L-N`; `UC1` → `LN` (no separator merges adjacent classes); `F-100` → `L-N`; `UC258_UC259` → `LN_LN`).
   - Group source IDs by signature; for each distinct signature, build ONE regex with **capture group 1** = the canonical ID portion:
     - `L`, `M` tokens → `[A-Z]+` (case-insensitive match).
     - `N` tokens → `\d+`.
     - Separators preserved verbatim (`-` or `_`).
     - Optional trailing continuation segments (to handle compound disk names like `UC1_61_TrangChu`): append `(?:[-_]\d+)*` ONLY when the LAST token is `N`. Don't append for IDs that end with letters.
     - Examples produced: `L-L-N` → `^([A-Z]+-[A-Z]+-\d+(?:[-_]\d+)*)`; `L-N` → `^([A-Z]+-\d+(?:[-_]\d+)*)`; `LN` → `^([A-Z]+\d+(?:[-_]\d+)*)`; `LN_LN` → `^([A-Z]+\d+_[A-Z]+\d+(?:[-_]\d+)*)`.
   - Sort `regexList` by **specificity descending** (longer signatures first, more separators first) so a compound-prefix regex matches before its shorter superset.
   - If `regexList` is empty (no source IDs at all — bootstrap edge case): fall back to a single permissive regex `^([A-Z]+[-_]?\d+(?:[-_]\d+)*)`. Continue with whole-name fallback for non-matches.

   **Step 2b — For each sub-folder name `<folderName>`:**
   - **Exclude** the folder if it satisfies ANY of:
     - Equals the basename (or any path segment) of the `requirement-common-files` resolved path.
     - Starts with `Common`, `Shared`, `_template`, `Old`, `Archive`, `_`, `.` (case-insensitive).
   - **Extract Folder ID** — try each regex in `regexList` order (first match wins); take capture group 1.
   - If NO regex matches → fall back to `Folder ID = <folderName>` verbatim. Do NOT silently skip — these folders are exactly the orphans that `qc-site-map` Mode 3 needs to reconcile.
   - Record the mapping in `sourceFolderMap[<sourceArtifact>][<folderID>] = <full folder path>`. `<sourceArtifact>` is one of `requirement-files | uc-review-report | func-test-scenarios | func-test-cases-draft | func-test-cases`. The same `<folderID>` may legitimately resolve to different folder paths across sources (e.g., `requirement-files/UC-CLY-005_LoyaltyRules/` and `uc-review-report/UC-CLY-005/` both map to Folder ID `UC-CLY-005`).
   - If two folders within the SAME source extract to the same Folder ID → warn in the run report and pick the first encountered (lexicographic order); user must resolve manually.

3. Build `observedFolderIDs = Set<FolderID>` deduplicated as the union of `<folderID>` keys across all 5 source maps.

4. **Resolve Folder ID → canonical Feature ID** for each observed folder, using this lookup chain (first match wins):
   - `aliasIndex[folderID]` (from handoff `Folder alias(es)`)
   - `folderIDIndex[folderID]` (from existing dashboard rows' column 3)
   - handoff `FeatureID == folderID` (direct match — top-down's default top-down case where Folder ID equals Feature ID)
   - existing dashboard `featureIndex[folderID]` (legacy direct match)
   - **No match → orphan**: this folder is not yet linked to any canonical ID. Treat its canonical ID as the Folder ID itself (`canonicalID := folderID`) and mark this row for inclusion in the bottom-up-style orphan handoff (see Phase 4).

   Persist the mapping as `folderToFeature = Map<FolderID → CanonicalFeatureID>` and the inverse `featureToFolder = Map<CanonicalFeatureID → FolderID>` (one folder per feature in the current scan; if a feature has multiple aliases on disk, only one folder is scanned this run — additional aliases stay in handoff but produce no disk scan).

Update worklog: `Status = Phase 1 done`.

### Phase 2 — Reconcile Buckets

The reconciliation operates over THREE sets:
- `existingFeatures = featureIndex.keys()` (canonical Feature IDs in current dashboard)
- `handoffFeatures = handoffList.keys()` (canonical Feature IDs in fresh handoff)
- `observedFolderIDs` (folder IDs seen on disk in Phase 1)

For each `observedFolderID`, `folderToFeature[observedFolderID]` is the canonical Feature ID it resolves to (Phase 1 Step 4). The reconciliation classifies every `(canonicalID, folderID?)` pair into one of the buckets below. **There are NO user confirmation prompts in this skill** — every bucket auto-applies its action.

| Bucket | Condition | Action |
|---|---|---|
| **MATCH-WITH-FOLDER** | canonicalID ∈ (handoffFeatures ∪ existingFeatures) AND ∃ folderID with `folderToFeature[folderID] = canonicalID`. | Update row (creating it if only in handoff). Column 3 `Folder ID` = the matched folderID. Run Phase 3 disk scan over that folderID's paths → write `Files stt`. Copy `In scope?` from handoff if present, else preserve existing value. |
| **HANDOFF-ONLY** | canonicalID ∈ handoffFeatures AND no observed folder maps to it. | Create row from handoff values. Column 3 `Folder ID` = first alias in handoff `Folder alias(es)`; if none, default to canonicalID. `Files stt` = all 6 lines `Missing`. `In scope?` from handoff. |
| **EXISTING-NO-FOLDER** | canonicalID ∈ existingFeatures AND canonicalID ∉ handoffFeatures AND no observed folder maps to it. | Preserve row as-is. Run Phase 3 over that row's existing Folder ID (column 3) — typically all `Missing`. Files stt updated. **In scope? NOT auto-changed**; user can manually edit if the feature is truly gone. Surface row in Phase 6 report under "Features no longer in handoff" so user is aware. |
| **ORPHAN-FOLDER** | folderID ∈ observedFolderIDs AND `folderToFeature[folderID] = folderID` (= no canonical match found). | Create row with column 2 `<ID label>` = folderID, column 3 `Folder ID` = folderID, `In scope? = Need confirm`. Run Phase 3 disk scan → write `Files stt`. **Add folderID to `orphanQueue`** for Phase 4 export to `dashboard-orphans.md`. |

Notes:
- A folder that appeared on disk for a feature whose `In scope?` was previously `No` is still scanned — Files stt always reflects disk reality regardless of scope. The user keeps full control of `In scope?` via manual edit.
- "Folder fully removed" (canonicalID was in existingFeatures with a Folder ID but no folder matches it now) is the **EXISTING-NO-FOLDER** bucket above. Surface in report, do not auto-change scope.

Update worklog: `Status = Phase 2 done`.

### Phase 3a — `Files stt` Computation (disk scan)

For each row, run all 6 sub-scans against its `Folder ID` (column 3). Each sub-scan looks inside the folder path recorded for that Folder ID in `sourceFolderMap[<sourceArtifact>][<folderID>]` (from Phase 1). If no folder path was recorded for that source (the source has no folder matching the Folder ID — e.g., BA has `UC1_TrangChuDashboard` but QC never created `UC1/` in `func-test-scenarios`) → that sub-scan returns no result (artifact absent) without attempting to read disk. Otherwise the sub-scan returns `V<max-N>` when matching files are found, or no result when none.

| Item | Source artifact (folder via `sourceFolderMap`) | Match | Version detection |
|---|---|---|---|
| `Specs` | `requirement-files` | `.md`, `.docx`, `.pdf` — EXCLUDE files with `_extracted_` in name; EXCLUDE image extensions | `_v<N>` (case-insensitive) in filename; absent → treat as v1 |
| `WF` | `requirement-files` | `.png`, `.jpg`, `.jpeg`, `.fig`, `.figma`, `.svg`, `.gif`, `.webp`, `.xd` | Same |
| `Audited` | `uc-review-report` | filename contains `_audited_` AND ends `.md` | Same |
| `Scenario` | `func-test-scenarios` | filename contains `_scenarios_` | Same |
| `TC md` | `func-test-cases-draft` | filename matches `_testcases_*.md` (covers both `_testcases_draft.md` and `_testcases_*_v<N>.md`) | Same |
| `TC xlsx` | `func-test-cases` | filename matches `_testcases_*_v<N>.xlsx` | Same |

Compose `newFilesStt`:
- Walk the 6 artifact types in the fixed order (Specs, WF, Audited, Scenario, TC md, TC xlsx) and keep only the ones whose sub-scan returned `V<N>`.
- Format each kept item as `<Type>: V<N>` and join with `<br>`.
- If NO item is found across all 6 types → set the cell to the literal string `No files yet`.

Do NOT compare against the previous `Files stt` value; this skill no longer tracks transitions (upgrades/regressions). The new cell always reflects current disk reality verbatim.

Update worklog: `Status = Phase 3a done`.

### Phase 3b — stt columns Computation (in-progress check + sparse done-state derivation)

This phase populates columns 8 (`UC review stt`), 9 (`Scenario design stt`), 10 (`TC design stt`), and 11 (`UI extract stt` if present or auto-injectable). The strategy minimizes token cost by parsing audited reports only when their version is newer than the cached value already in the cell.

For every dashboard row (`<UC-ID>` = the row's `Folder ID`), and for each of the 4 stt columns:

#### Step 1 — In-progress check

Check whether `.claude/skills/<owner-skill>/process-logging/<UC-ID>/progress.md` exists (`<owner-skill>` per the "Process-logging inputs" table). If yes → read it, extract `status:` line per the "Process-log parse contract" parse algorithm, and set the cell to the raw status string. SKIP step 2 for this column.

#### Step 2 — Done-state derivation (only when in-progress file is absent)

Apply the per-column rule from the "Done-state derivation" table:

- **`UC review stt`:**
  1. From the row's Files stt, extract `currentAuditedVer` (digit after `Audited: V`). If no Audited line → cell BLANK; skip.
  2. From the row's existing cell value, extract `cachedAuditedVer` via regex `(?:Ready|Conditionally Ready|Not Ready)\s+v(\d+)\s*\(Score`. If no match → `cachedAuditedVer = 0`.
  3. If `currentAuditedVer <= cachedAuditedVer` → keep cell verbatim (NO PARSE — token saving).
  4. Else → locate the highest-version audited file at `<uc-review-report>/<UC-ID>/*_audited_*_v<currentAuditedVer>.md`. Use `grep -n "Tổng điểm"` to find the scoring line, then targeted-read 1 line. Extract `score` + `verdict` via the regex in "Done-state derivation" → audited file parse contract. Compose new cell value `<verdict> v<currentAuditedVer> (Score <score>/100)`.
  5. If grep fails (no scoring row found in file) → emit warning + keep cell verbatim.

- **`Scenario design stt`:**
  1. From the row's Files stt, extract `scenarioVer` (digit after `Scenario: V`). If no Scenario line → cell BLANK.
  2. Else → cell = `v<scenarioVer> generated` (no file parse).

- **`TC design stt`:**
  1. From the row's Files stt, extract `tcXlsxVer` and `tcMdVer`.
  2. If `tcXlsxVer` present → cell = `v<tcXlsxVer> generated`.
  3. Else if `tcMdVer` present → cell = `v<tcMdVer> draft`.
  4. Else → cell BLANK.

- **`UI extract stt`** (only if column exists OR Step 3 auto-injection triggers):
  1. Scan `<ui-elements>/<UC-ID>/` (resolve `ui-elements` from `path-registry`). List files matching `*_v<N>.md`. If folder absent or empty → cell BLANK; skip.
  2. Compute `currentUiVer = max(N across files)`, `pageCount = count of distinct page-name in files at version currentUiVer`.
  3. From the row's existing cell, extract `cachedUiVer` via `^v(\d+)\s+\(audited`. If no match → `cachedUiVer = 0`.
  4. If `currentUiVer <= cachedUiVer` → keep cell verbatim (no parse).
  5. Else → open ONE file from the highest-version set; grep for a reference to the audited version (pattern `audited[_\s-]*v(\d+)` in the file's header/frontmatter). Extract `auditedRefVer`. If not found → fallback to current Files stt's `Audited: V<N>` value.
  6. Compose cell value: `v<currentUiVer> (audited v<auditedRefVer>)`. Append ` [<pageCount>p]` only when `pageCount > 1`.

#### Step 3 — `UI extract stt` auto-injection check

If the dashboard header does NOT yet have a `UI extract stt` column AND `<ui-elements>/` parent folder has at least one `<UC-ID>/` subfolder with extracted files → mark `injectUIExtractColumn = true`. Phase 5 inserts the column at position 11 (before `Execute stt` if present, else at the end).

#### Step 4 — Store results

Store the computed values in `stttCells[<rowID>][<columnName>] = formattedValue`. Phase 5 writes them into the rendered table.

**Idempotency note:** Phase 3b reads at most: (a) the per-UC subfolder progress.md files (small, fast) and (b) one grep + targeted read per UC that has a NEWER audited or ui-elements version than its cached cell. Steady-state (no new audited reports since last sync) → ZERO file reads.

Update worklog: `Status = Phase 3b done`.

### Phase 4 — Export orphan handoff (no user prompt)

This skill is non-interactive after Phase 0.5. Phase 4 performs ONE write outside of `qc-dashboard.md`: it exports the `orphanQueue` (from Phase 2's `ORPHAN-FOLDER` bucket) to the inbox of `qc-site-map`.

1. If `orphanQueue` is empty → skip the file write and continue to Phase 5.
2. Otherwise, resolve the output path `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`.
3. **Append + dedupe semantics:**
   - If the file does NOT exist → create it from the schema in "Bottom-up output handoff" above. Write each orphan as one row.
   - If the file EXISTS → parse its existing table. For each Folder ID in `orphanQueue`:
     - If the Folder ID already has a row → update only the `Detected at` cell to the current ISO timestamp; do NOT duplicate.
     - Else → append a new row.
   - Preserve frontmatter; update `generated_at` to the latest run timestamp.
4. Record `orphanQueue` count for the Phase 6 report.

Update worklog: `Status = Phase 4 done`.

### Phase 5 — Compose sort + write Dashboard

This skill is the SOLE writer of every column in the dashboard. Phase 5 composes the final row order via the `Sorting:` directive, writes all cells (including stt columns from Phase 3b), and persists to disk.

#### Step 1 — Optional column injection check

- If Phase 3b set `injectUIExtractColumn = true` → insert a `UI extract stt` column at position 11 (before `Execute stt` if it already exists, else at the end). Pre-existing rows get blank values until Phase 3b later finds entries for them.
- Otherwise preserve the header as-is.

#### Step 2 — Compute sort order

Apply the algorithm in "Sort order directive" section above:

1. Compute `distinctSites` and `distinctModules`.
2. Read any pre-existing `Sorting:` line from the in-memory parsed dashboard.
3. Decide the sort level + the `userSortList` per the re-run logic. If no pre-existing line OR re-run logic triggers fresh generation → auto-generate alphabetical ascending of the chosen level.
4. Record the final `sortLevel` (`Site` | `Module` | `None`) and `sortList`.
5. If `sortLevel == None` (single-portal single-module case) and a pre-existing `Sorting:` line is present → mark it for removal with a notice in Phase 6 output.

#### Step 3 — Apply sort to rows

1. Group rows by their value at `sortLevel`:
   - For each group in the order given by `sortList`, append the group's rows.
   - Append any rows whose level-value is not in `sortList` last, alphabetical ascending.
2. Within each group, sort by the next-lower level alphabetically (`Site` → sub-sort by `Module` ascending; then by canonical ID ascending). If `sortLevel == Module`, sub-sort by canonical ID ascending. If `sortLevel == None`, sort all rows by canonical ID ascending.

#### Step 4 — Render the table

For every row, write ALL columns:

- Columns **1, 2, 3, 4, 5, 6, 7** with the values computed in Phases 0–3a (per the bucket rules in Phase 2 and the disk scan in Phase 3a).
  - Column 2 `<ID label>` = canonical Feature ID.
  - Column 3 `Folder ID` = folder-name ID linking the row to disk. NEVER blank — for top-down rows without an alias, equals column 2.
  - Column 6 `In scope?` = copied from handoff (top-down) or `Need confirm` (ORPHAN-FOLDER bucket) or preserved (EXISTING-NO-FOLDER bucket).
- Columns **8, 9, 10** with the values from Phase 3b's `stttCells` map. If no value was computed → BLANK.
- Optional columns (`UI extract stt`, `Execute stt`):
  - `UI extract stt` (column 11) → value from Phase 3b. BLANK if no entry.
  - `Execute stt` — preserved VERBATIM from the parsed dashboard if present (no current owner skill writes it; the user may have written it manually).
- Preserve the header row, applying label migration if `labelMigrationNeeded` was set in Phase 0.6 case B.

#### Step 5 — Write `Sorting:` directive

- If `sortLevel != None` → write the line `Sorting: <v1> >> <v2> >> ...` immediately above the table header. Place it on its own line with one blank line on each side.
- If `sortLevel == None` AND a pre-existing `Sorting:` line was present → remove it.
- If `sortLevel == None` AND no pre-existing line → write nothing.

#### Step 6 — Preserve notes block + write file

- Preserve the ghi-chú/notes block below the table verbatim (do not rewrite from template). If a label migration note or v10/v11-old migration note was prepared earlier, append it to the END of the ghi-chú block as a new bullet — do not overwrite existing notes.
- Write back to the `qc-dashboard` path. In-place edit.

Update worklog: `Status = Phase 5 done`. Add `qc-dashboard.md` to the Output column. If `orphanQueue` was non-empty in Phase 4, also append `dashboard-orphans.md` to the Output column.

### Phase 6 — Cleanup & Handover

1. **Do NOT delete `site-map-handoff.md`.** Lifecycle ownership rule: `qc-site-map` is the sole writer and deleter (it overwrites the file at the start of its own Phase 9). Leaving the file in place means the user can manually re-run `/qc-dashboard-sync` after editing artifacts on disk, without being forced to re-run the entire top-down chain.
2. **Do NOT delete `dashboard-orphans.md`.** Lifecycle ownership rule: `qc-site-map` Mode 3 is the sole deleter (it removes the file after reconciling every entry). Top-down may have appended new entries this run; those persist until Mode 3 runs.
3. Output the summary:
   ```
   ✅ **Dashboard sync hoàn tất.**

   **Thay đổi:**
   - New rows added (top-down handoff):           <N>  (<list canonical IDs>)
   - Orphan folders appended to site-map inbox:   <N>  (<list Folder IDs>)
   - Features in dashboard không còn trong handoff (cần user review): <N>  (<list canonical IDs>)
   - stt cells updated (in-progress hoặc sparse-parse done): <N>  (<list "col:UC-ID" entries, max 10 then "... và <K> mục khác">)
   - Audited file re-parses (token cost):          <N>  (<list "UC-ID v<old>→v<new>" entries>)
   - `UI extract stt` column auto-injected:        <Yes | No>

   **Sort order:**
   - Sort level:    <Site | Module | None — single module>
   - Sorting line:  <`Sorting: ...` written | removed | unchanged | auto-generated>

   Dashboard tại: `<resolved path>`
   Orphan inbox: `<inbox path>` (<orphanQueue count> entries this run; total <total dedup count> trong file)
   ```
4. **Next-step reminder.**
   - If `orphanQueue` count > 0:
     ```
     📋 **Cần chạy tiếp:** Có <N> folder UC không khớp site-map đã được ghi vào `dashboard-orphans.md`. Hãy chạy `/qc-site-map` (chọn Mode 3 khi được hỏi) để reconcile các orphan này thành mapped feature hoặc feature mới.
     ```
   - If any new row has blank Site/Module/Name OR any row at `Need confirm`:
     ```
     📋 **Cần user xử lý manual:**
     - <N> row mới có cột Site / Module / Feature name TRỐNG — vui lòng cập nhật trực tiếp trong dashboard.
     - <N> row đang ở `Need confirm` — sẽ tự resolve sau khi `qc-site-map` Mode 3 chạy, hoặc bạn có thể edit thủ công thành Yes / No.
     ```
5. Update worklog: `Status = Done`. Fill Duration.

## Bottom-up workflow

Triggered ONLY by the user running `/qc-dashboard-sync <UC-ID>` manually. Per-UC skills do not auto-invoke this skill anymore — they only maintain their existing per-UC subfolder progress.md for resume; the user runs `/qc-dashboard-sync <UC-ID>` to refresh the dashboard row.

### Bottom-up steps

1. Generate `run_id` and append worklog row `Status = Running (bottom-up, uc_id=<ID>)`.
2. Resolve `qc-dashboard` path. If the file does not exist → create it from `templates/qc-dashboard-template.md` with `<ID label> = Use Case ID` (default). Do NOT prompt for the label here (top-down handles the prompt; in bottom-up the default is safe).
3. Parse the existing dashboard (header + `featureIndex` keyed by column 2 + `folderIDIndex` keyed by column 3). Schema validation + auto-migration: same as top-down Phase 0 step 5. If mismatch and not auto-migratable → STOP and report.
4. **Single-UC scope check (matches by Folder ID, not canonical ID):**
   - If `<ID>` matches an existing `Folder ID` (column 3 of any row) → SKIP "add new row" step but PROCEED with stt + Files stt refresh for that matched row. Print `<ID> da co trong dashboard (Folder ID khop), se refresh Files stt va stt columns`.
   - Else if `<ID>` matches an existing `<ID label>` (column 2) but the row's `Folder ID` (column 3) is different → same as above (the row exists; refresh only).
   - Otherwise → mark `addNewRow = true` and continue.
5. Run the 6-artifact disk sub-scans for `<ID>` only. Build a single-entry `regexList` from `<ID>` itself using the same shape-signature algorithm as top-down Phase 1 step 2a (so compound disk names like `<ID>_SomeSuffix` will match back to `<ID>`). Resolve folder paths inside `requirement-files/<...>`, `uc-review-report/<...>`, etc., scanning sub-folders and extracting Folder IDs via the regex; if no folder matches, fall back to a literal-name match `<ID>` exactly. Compose `Files stt` per "Files stt cell format" section.
6. **stt computation for `<ID>` only.** Apply the exact same algorithm as top-down Phase 3b, scoped to this single UC:
   - **In-progress check:** for each of the 4 per-UC skills, check whether `.claude/skills/<skill>/process-logging/<ID>/progress.md` exists. If yes → cell = `status:` line read verbatim.
   - **Done-state derivation** (only when in-progress file is absent): per the "Done-state derivation" table — sparse-parse audited file for `UC review stt` (only when `Audited: V<N>` from step 5 is greater than the cached cell version of the existing row, if any); derive from Files stt for `Scenario design stt` and `TC design stt`; sparse-parse latest ui-elements file for `UI extract stt`.
   - If `docs/qc/ui-elements/<ID>/` has at least one extracted file AND the dashboard does NOT yet have a `UI extract stt` column → mark `injectUIExtractColumn = true`.
7. **If `addNewRow == true`:** add a new row to `featureIndex`:
   - Column 2 `<ID label>` → `<ID>` (folder-derived; will be replaced with canonical ID once `qc-site-map` Mode 3 reconciles).
   - Column 3 `Folder ID` → `<ID>` (same as column 2 until reconciliation).
   - `Site / Module / Feature/Use case name` → BLANK (no upstream context to fill them).
   - `In scope?` → `Need confirm`.
   - `Files stt` → from step 5.
   - Columns 8, 9, 10, 11 → from step 6 (may be blank).

   **Otherwise (row exists):** update only `Files stt` (col 7) + stt cells (cols 8, 9, 10, 11) on the matched row. Do NOT touch `Site / Module / Feature/Use case name / In scope?` — those are owned by top-down and should not be overwritten by a bottom-up refresh.

8. **Optional upstream alignment check:**
   - If `project-context-master.md` exists, read its feature list. If `<ID>` is NOT present → set `outOfContext = true`.
   - If `site-map-handoff.md` exists in dashboard inbox, read it. If `<ID>` is NOT present (neither as Feature ID nor as a Folder alias) → set `outOfHandoff = true`.
9. **Sort + write dashboard.** Apply the same Phase 5 sort logic as top-down (Step 2 + Step 3 + Step 5). For a single-UC bottom-up that adds a row, the sort level may have changed (e.g., the new row introduces a new Site/Module) — re-evaluate and update the `Sorting:` line if needed. Then write the dashboard back (in-place).
10. **Write to site-map orphan inbox** (only if `addNewRow == true`). Resolve `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`. Apply append+dedupe semantics (same as top-down Phase 4):
    - File missing → create from schema in "Bottom-up output handoff".
    - File present + entry for `<ID>` already there → update only `Detected at` to current ISO timestamp.
    - File present + entry for `<ID>` missing → append a new row with `<ID>` + its `Folder paths (per source)` + the just-computed `Files stt` + current timestamp.

    If `addNewRow == false` → SKIP this step. The row already exists; no need to orphan-track again.

11. Emit the user message:

    ```text
    ✅ <message tuy theo trang thai>:
       - <addNewRow==true>:   Da them row moi cho <ID> vao qc-dashboard.md (In scope? = Need confirm, Folder ID = <ID>).
       - <addNewRow==false>:  Da refresh Files stt + stt columns cho row <ID> trong qc-dashboard.md.

    📊 stt columns sau scan process-log:
       - UC review stt:       <value | (blank — chua co progress.md entry)>
       - Scenario design stt: <value | (blank)>
       - TC design stt:       <value | (blank)>
       - UI extract stt:      <value | (blank | column chua duoc inject)>

    <only when addNewRow==true:>
    ✅ Da ghi <ID> vao .claude/skills/qc-site-map/inbox/dashboard-orphans.md cho qc-site-map Mode 3 reconcile.

    ⚠️ <ID> chua co trong tai lieu upstream:
    - project-context-master.md: <CO | KHONG CO | KHONG TIM THAY FILE>
    - site-map-handoff.md: <CO | KHONG CO | KHONG TIM THAY FILE>

    De reconcile orphan thanh canonical feature, hay chay /qc-site-map va chon Mode 3 (confirm orphans from dashboard).
    ```

    Suppress the upstream-warning paragraph when both `outOfContext` and `outOfHandoff` are false.

12. Worklog: `Status = Done (bottom-up)`. Append `qc-dashboard.md` (always) and `dashboard-orphans.md` (only if appended) as the Output.

### Bottom-up boundaries

- Bottom-up does NOT delete or consume `site-map-handoff.md`.
- Bottom-up does NOT delete `dashboard-orphans.md` — it only appends/dedupes.
- Bottom-up does NOT run the site-map gap review (Phase 0.5 is top-down only).
- Bottom-up does NOT prompt the user during the run — it is a one-shot manual invocation; warnings are emitted as text only.
- Bottom-up may create the dashboard file from template if missing, with the default ID label.
- Bottom-up DOES re-evaluate + rewrite the `Sorting:` line if the row added changed the sort level (e.g., introduces a new portal in a previously single-portal dashboard).

## Boundaries

- **SOLE writer** of `qc-dashboard.md`. Creates the file from template on first run; updates in-place on subsequent runs. NO other skill is allowed to open this file for writing.
- Writes ALL columns: **1, 2, 3, 4, 5, 6, 7** from disk scan + handoff; **8, 9, 10, 11** via in-progress check + sparse done-state derivation per Phase 3b. Preserves `Execute stt` (col 12) verbatim — no current owner skill writes it.
- Writes the `Sorting:` directive line above the header. Respects user edits to the line on subsequent runs.
- **No soft-delete via `Removed`.** This skill does NOT auto-set `In scope? = Removed`. The `Removed` value remains a legal user-edit value, but the skill itself never writes it. Rows whose folder is gone keep their `In scope?` unchanged; their `Files stt` reflects `No files yet` (or a partial list of remaining artifacts).
- **No interactive prompts** in either mode except: Phase 0.5 gap-review proceed/cancel (top-down only) and Phase 0.6 ID-label confirmation when bootstrapping (top-down only).
- The skill does NOT invent values for Site / Module / Feature name — in top-down mode they come from the site-map handoff; in bottom-up they remain BLANK on newly added rows, and are PRESERVED on existing rows during a refresh.
- Folders matching the exclusion rules (Common, Shared, _template, …) are NEVER added as rows. Folders whose name does not match the ID regex but is otherwise valid (e.g., `TrangChuDashboard`) ARE added — they are exactly the orphans that Mode 3 reconciles.
- Schema mismatch → STOP and report. Do NOT auto-fix (except the explicit auto-migrations in Phase 0 step 5).
- Site-map handoff file (`site-map-handoff.md`) is consumed (read only). This skill does NOT delete it — `qc-site-map` overwrites it on its next run.
- Dashboard orphans file (`dashboard-orphans.md`) is written (append + dedupe). This skill does NOT delete it — `qc-site-map` Mode 3 owns deletion.
- Per-UC subfolder progress.md files (`<skill>/process-logging/<UC-ID>/progress.md`) are consumed (read only) — this skill NEVER writes to them. Output files (audited reports under `<uc-review-report>/<UC-ID>/`, ui-elements under `docs/qc/ui-elements/<UC-ID>/`) are also read-only; this skill only does sparse-parse for verdict/score/version extraction.

## Cross-skill contract

- **`qc-context-master`** — Step 1 of the top-down chain. Writes `project-context-master.md` only. NEVER writes any handoff file for this skill. NEVER invokes this skill directly. In Initialization mode it invokes `qc-site-map`; in Update mode it suggests the user to run `qc-site-map`.

- **`qc-site-map`** — Step 2 of the top-down chain. Writes `qc-site-map.md` + `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md`. In Initialization mode + after Mode 3 completes it invokes this skill directly (top-down mode). In Update mode it suggests the user to run `/qc-dashboard-sync`. The handoff file it writes is the SOLE upstream feature list source for top-down sync. The `Folder alias(es)` column inside the handoff is the SOLE source of truth for column 3 `Folder ID` of any non-trivial alias (top-down rows whose folder name differs from the canonical Feature ID).

- **`qc-uc-read`** — MUST NOT open `qc-dashboard.md` for read or write. Continues to use its EXISTING per-UC subfolder `process-logging/<UC-ID>/progress.md` (per its `workflows/checkpoint-protocol.md`) for resume-from-interruption — no schema change required. This skill (qc-dashboard-sync) reads that file for in-progress detection and parses the latest audited file (sparse) for done-state verdict + score.

- **`qc-func-scenario-design`** — same contract. Existing per-UC subfolder progress.md is unchanged. Done-state value derived from the Scenario file version in Files stt — no file content parse.

- **`qc-func-tc-design`** — same contract. Existing per-UC subfolder progress.md is unchanged. Done-state value derived from the TC xlsx/md file version in Files stt — no file content parse. The historical `v<N> updated` vs `v<N> generated` distinction is lost; user can edit manually if desired.

- **`qc-ui-extract`** — same contract. Existing per-UC subfolder progress.md is unchanged. Done-state value derived from the latest ui-elements file (sparse parse of one file at the highest version to read `audited_version` reference + count pages).

**User responsibility:** the dashboard-write code currently embedded in each per-UC skill workflow (e.g., `qc-uc-read/workflows/re-audit/re-audit.md:42`, `qc-func-scenario-design/SKILL.md:75/99/118`, `qc-func-tc-design/workflows/convert-md-to-xlsx.md:72/148`, `qc-ui-extract/SKILL.md:130-141`) needs to be REMOVED manually by the user. This skill does NOT depend on those writes — but as long as they exist, two writers may race on the dashboard file. The user has elected to remove those writes by hand without modifying the per-UC SKILL.md or workflow files via automation.

Other skills (e.g., a future `qc-execute` skill) should follow the same contract: maintain their own per-UC subfolder progress.md for resume + produce a versioned output file that this skill can scan for done-state.

### Why no precheck contract anymore

Previous versions required per-UC skills to run a "Case A/B/C precheck" against the dashboard and auto-invoke bottom-up on Case A. That contract is REMOVED because:

- Per-UC skills should no longer open the dashboard at all, so they cannot perform a precheck against it.
- Concurrent runs of multiple per-UC skills no longer race on the dashboard file (once the user has removed the embedded dashboard-write code).
- The user is now responsible for running `/qc-dashboard-sync <UC-ID>` (or full top-down) when they want to see the latest stt in the dashboard.
- If the user wants to be reminded that a UC is not in the dashboard (the old Case A warning) or is still in `dashboard-orphans.md` (the old Case B warning), they can run `/qc-dashboard-sync <UC-ID>` BEFORE starting the per-UC skill — bottom-up will surface those signals in its end-of-run message.
