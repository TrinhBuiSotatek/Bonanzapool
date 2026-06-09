---
name: qc-dashboard-sync
description: Owner of qc-dashboard.md. Step 3 of the top-down chain qc-context-master -> qc-site-map -> qc-dashboard-sync. Tracks the on-disk reality of UC artifact folders; does NOT decide In scope?. Operates in TWO modes. (1) Top-down — triggered by /qc-dashboard-sync or auto-invoked by qc-site-map. Requires project-context-master.md AND site-map-handoff.md to exist as upstream evidence. Surfaces the gap report already produced by qc-site-map (no duplicate conflict-check), then syncs the feature list from site-map-handoff into qc-dashboard.md and scans the existence/version of 6 artifact types (Specs, WF, Audited, Scenario, TC md, TC xlsx) into a single Files stt column. (2) Bottom-up — auto-invoked by per-UC skills (qc-uc-read, qc-func-scenario-design, qc-func-tc-design) for a single UC ID. Adds a row with In scope? = Need confirm AND appends an entry to .claude/skills/qc-site-map/inbox/dashboard-orphans.md so qc-site-map Mode 3 can later reconcile it. Does NOT prompt the user for In scope? decisions. Does NOT write the process-state columns UC review stt, Scenario design stt, TC design stt — those are owned by the respective review/design skills.
---

# QC Dashboard Sync Skill

## Two operating modes

This skill operates in two modes that are mutually exclusive within a single run:

| Mode | Triggered by | Scope | Gap review | Prerequisite |
|---|---|---|---|---|
| **Top-down** | `/qc-dashboard-sync` (manual) OR auto-invoked by `qc-site-map` | Full feature list + 6-artifact scan for every UC | YES — surfaces site-map's gap tables (Feature-level gaps, Unmapped screens, Dashboard recommendation) and asks user proceed/cancel | `project-context-master.md` AND `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md` must both exist |
| **Bottom-up** | Auto-invoked by per-UC skills (`qc-uc-read`, `qc-func-scenario-design`, `qc-func-tc-design`) with a specific UC ID | Single UC: add row with `Need confirm` + run the 6-artifact scan for that UC only + append entry to `dashboard-orphans.md` inbox of `qc-site-map` (so Mode 3 can reconcile later) | NO | None — runs even if upstream context is missing |

The caller indicates the mode implicitly:
- No UC ID passed → top-down.
- A UC ID passed (`uc_id=<ID>`) → bottom-up for that single ID.

## Scope decision boundary

This skill does NOT decide `In scope?` business value. Its sole responsibilities:

- In top-down: copy `In scope?` from the site-map handoff (which is the authoritative source of feature scoping).
- In bottom-up: set `In scope? = Need confirm` for newly added rows, and forward the orphan UC ID to `qc-site-map` (via `dashboard-orphans.md`) so Mode 3 can either map it to an existing feature or add it as a new feature; the next top-down sync will then carry the correct scope value back.

No interactive `In scope?` prompts are emitted from this skill. The user can manually edit any row's `In scope?` cell at any time.

## Trigger Conditions

- **Manual top-down:** `/qc-dashboard-sync`, "sync dashboard", "đồng bộ dashboard", "update dashboard status".
- **Auto-trigger top-down from `qc-site-map`** — at the end of its Phase 9, after writing `site-map-handoff.md`, in Initialization mode (or Update mode when the user accepts the prompt).
- **Auto-trigger bottom-up from per-UC skills** (`qc-uc-read`, `qc-func-scenario-design`, `qc-func-tc-design`) — when the skill operates on a UC ID that is NOT yet a row in the dashboard, it MUST invoke this skill in bottom-up mode BEFORE proceeding so the dashboard always reflects on-disk reality.

`qc-context-master` no longer triggers this skill. The dashboard receives its feature list exclusively via `qc-site-map`'s `site-map-handoff.md`.

## Top-down prerequisites

In top-down mode this skill requires BOTH upstream artifacts to exist:

1. `project-context-master.md` resolved via `path-registry.md`.
2. `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md` written by `qc-site-map`.

If either is missing → STOP with the Vietnamese message:

```text
Khong du dieu kien chay top-down sync:
- project-context-master.md: <found | MISSING>
- site-map-handoff.md (tu qc-site-map): <found | MISSING>

Hay chay chuoi theo thu tu: /qc-context-master -> /qc-site-map -> /qc-dashboard-sync.
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
  | <ID extracted from folder name> | requirement-files: <path>; uc-review-report: <path>; ... | Specs: V1<br>WF: Missing<br>... | <ISO-8601 datetime> |
  ```

### Template

- `templates/qc-dashboard-template.md` — used to bootstrap the dashboard when it does not exist.

## Schema (11 columns)

| # | Column | Owner | Type |
|---|---|---|---|
| 1 | `Site` | `qc-dashboard-sync` | metadata |
| 2 | `<ID label>` | `qc-dashboard-sync` | metadata — **canonical** ID from site-map (or folder ID until reconciled) |
| 3 | `Folder ID` | `qc-dashboard-sync` | metadata — ID/name as extracted from on-disk folder (used to match disk scan → row) |
| 4 | `Module` | `qc-dashboard-sync` | metadata |
| 5 | `Feature/Use case name` | `qc-dashboard-sync` | metadata |
| 6 | `In scope?` | `qc-dashboard-sync` | metadata — copied from site-map handoff (top-down) or set to `Need confirm` (bottom-up) |
| 7 | `Files stt` | `qc-dashboard-sync` | **file existence** (consolidated 6 file types) |
| 8 | `UC review stt` | `qc-uc-read` | process state — preserved verbatim |
| 9 | `Scenario design stt` | `qc-func-scenario-design` | process state — preserved verbatim |
| 10 | `TC design stt` | `qc-func-tc-design` | process state — preserved verbatim |
| 11 | `Execute stt` | — (pending) | placeholder — preserved verbatim |

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

- **`qc-dashboard`** — this skill is the **sole owner of the file** (creates + structures it). Writes columns **1, 2, 3, 4, 5, 6, 7**. Preserves columns **8, 9, 10, 11** verbatim.
- **`dashboard-orphans.md`** — at `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`. Written (append + dedupe by Folder ID) every time bottom-up adds a brand-new row. Sole consumer + deleter is `qc-site-map` Mode 3.
- Console report: new rows, Files-stt updates, orphans appended, summary.
- `worklog-per-device` — log every phase boundary per the protocol at `docs/qc-lead/agent-work-log.local/README.md`. Do NOT touch the master `agent-work-log`.

## `Files stt` cell format

Single-cell, 6 lines joined by `<br>`. One line per artifact type, in this fixed order:

```
Specs: V<N> | Missing
WF: V<N> | Missing
Audited: V<N> | Missing
Scenario: V<N> | Missing
TC md: V<N> | Missing
TC xlsx: V<N> | Missing
```

Rendered example (one cell):
```
Specs: V2<br>WF: V1<br>Audited: Missing<br>Scenario: V1<br>TC md: V2<br>TC xlsx: Missing
```

Use literal string `Missing` when the file is absent. Use `V<N>` (capital V) where `<N>` is the highest version detected.

## Workflow

The workflow below is the **top-down workflow** (Phases 0 → 0.5 → 0.6 → 1 → 2 → 3 → 4 → 5 → 6). For bottom-up, see the dedicated section after Phase 6.

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
   - If the dashboard file EXISTS: parse it now (header → `existingLabel`; data rows → `featureIndex` keyed by canonical ID in column 2; notes block captured verbatim). Run schema validation:
     - **11 columns in canonical order** (column 3 = `Folder ID` present): parse `Folder ID` from column 3 into each `featureIndex` entry. Proceed normally.
     - **10 columns (legacy schema without `Folder ID`)**: AUTO-MIGRATE in-memory before continuing. Safe to auto-fill because the legacy schema only existed before Mode 3 existed, so every row was top-down with `column 2 = folder name on disk` (no alias divergence yet possible). Migration steps:
       1. Insert a new `Folder ID` column at position 3 in the header (between `<ID label>` and `Module`).
       2. For every data row, insert a new cell at position 3 with value = column 2's value (self-reference). All existing column-3-onward cells shift one position right; no data is lost.
       3. Append a migration note to the in-memory ghi-chú block (to be written in Phase 5):
          ```text
          > **<YYYY-MM-DD> — Schema migration v10→v11**: cot `Folder ID` da duoc them tu dong, gia tri = cot `<ID label>` (self-reference). Mode 3 cua qc-site-map se update gia tri khi reconcile orphan voi alias mapping khac.
          ```
       4. Print a single info line on console: `Da auto-migrate dashboard tu 10 cot sang 11 cot (them Folder ID = self-reference cho <N> row).`
       5. Continue Phase 0 with the migrated in-memory state. The actual file write happens in Phase 5.
     - **Other mismatches** (wrong column count, wrong header order, missing required column): STOP and report. Do NOT auto-fix beyond the v10→v11 case.
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

2. **Exclude + extract Folder ID from each sub-folder name.** Different sources may name the same UC differently — e.g., BA uses compound names like `UC1_TrangChuDashboard`, `UC258_UC259_ThongBaoHeThong`, while QC uses bare IDs like `UC1`, `UC258_UC259`. The skill MUST extract a `Folder ID` from each folder name and use it as the link to the dashboard row (column 3). For each sub-folder name `<folderName>`:
   - **Exclude** the folder if it satisfies ANY of:
     - Equals the basename (or any path segment) of the `requirement-common-files` resolved path.
     - Starts with `Common`, `Shared`, `_template`, `Old`, `Archive`, `_`, `.` (case-insensitive).
   - **Extract Folder ID prefix** — apply the regex derived from the `<ID label>` to the START of `<folderName>` and take **capture group 1**. The regex is greedy on the ID portion and stops at the first segment that is not an ID continuation (i.e., the first segment that starts with a non-digit / non-`UC`-prefixed letter):
     - Default (`Use Case ID`): `^(UC\d+(?:[-_](?:UC)?\d+)*)`
       - Examples: `UC1_TrangChuDashboard` → `UC1` · `UC42-44_QuanLyDatLich` → `UC42-44` · `UC53_63-65_PhanAnhKienNghi` → `UC53_63-65` · `UC258_UC259_ThongBaoHeThong` → `UC258_UC259` · `UC56-57_66_68_TinTuc` → `UC56-57_66_68` · `UC1` → `UC1`.
     - Feature ID: `^(F(?:EAT)?[\-_]?\d+(?:[-_]\d+)*)`
     - Story ID: `^(S(?:TORY)?[\-_]?\d+(?:[-_]\d+)*)`
     - Otherwise: ask the user during Phase 0 to confirm a Folder-ID extraction regex (must contain exactly one capture group); store as one-shot for this run.
   - If the regex does NOT match → the folder may still be a valid UC with a non-ID-pattern name (e.g., `TrangChuDashboard`). In that case fall back to `Folder ID = <folderName>` verbatim and continue. Do NOT silently skip — these folders are exactly the orphans that `qc-site-map` Mode 3 needs to reconcile.
   - Record the mapping in `sourceFolderMap[<sourceArtifact>][<folderID>] = <full folder path>`. `<sourceArtifact>` is one of `requirement-files | uc-review-report | func-test-scenarios | func-test-cases-draft | func-test-cases`. The same `<folderID>` may legitimately resolve to different folder paths across sources (e.g., `requirement-files/UC1_TrangChuDashboard/` and `uc-review-report/UC1/` both map to Folder ID `UC1`).
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
- Detection of "doc disappeared" (Files stt previously had `V<N>`, now `Missing`) is informational only — surfaced in the Phase 6 report. It does NOT auto-change `In scope?`. The folder still exists; the user decides whether the feature is truly removed.
- "Folder fully removed" (canonicalID was in existingFeatures with a Folder ID but no folder matches it now) is the **EXISTING-NO-FOLDER** bucket above. Same rule: surface in report, do not auto-change scope.

Update worklog: `Status = Phase 2 done`.

### Phase 3 — `Files stt` Computation + Transition Detection

For each row, run all 6 sub-scans against its `Folder ID` (column 3). Each sub-scan looks inside the folder path recorded for that Folder ID in `sourceFolderMap[<sourceArtifact>][<folderID>]` (from Phase 1). If no folder path was recorded for that source (the source has no folder matching the Folder ID — e.g., BA has `UC1_TrangChuDashboard` but QC never created `UC1/` in `func-test-scenarios`) → that sub-scan returns `Missing` without attempting to read disk. Otherwise the sub-scan returns `V<max-N>` or `Missing` based on file contents of the recorded folder.

| Item | Source artifact (folder via `sourceFolderMap`) | Match | Version detection |
|---|---|---|---|
| `Specs` | `requirement-files` | `.md`, `.docx`, `.pdf` — EXCLUDE files with `_extracted_` in name; EXCLUDE image extensions | `_v<N>` (case-insensitive) in filename; absent → treat as v1 |
| `WF` | `requirement-files` | `.png`, `.jpg`, `.jpeg`, `.fig`, `.figma`, `.svg`, `.gif`, `.webp`, `.xd` | Same |
| `Audited` | `uc-review-report` | filename contains `_audited_` AND ends `.md` | Same |
| `Scenario` | `func-test-scenarios` | filename contains `_scenarios_` | Same |
| `TC md` | `func-test-cases-draft` | filename matches `_testcases_*.md` (covers both `_testcases_draft.md` and `_testcases_*_v<N>.md`) | Same |
| `TC xlsx` | `func-test-cases` | filename matches `_testcases_*_v<N>.xlsx` | Same |

Compose `newFilesStt` string in the fixed order, joined by `<br>`:
```
Specs: <V or Missing><br>WF: <V or Missing><br>Audited: <V or Missing><br>Scenario: <V or Missing><br>TC md: <V or Missing><br>TC xlsx: <V or Missing>
```

**Transition detection** — parse the row's previous `Files stt` cell (split on `<br>`, split each line on `:` to get type → value). Compare per-item to the new value:
- Any item that was `V<N>` and is now `Missing` → record in `docDisappearedReport` for the Phase 6 summary (informational only — no `In scope?` change).
- Upgrades (`Missing` → `V<N>`) and version bumps (`V1` → `V2`) → applied silently.

Update worklog: `Status = Phase 3 done`.

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

### Phase 5 — Write Dashboard

1. Re-render the markdown table:
   - For every row, write columns **1, 2, 3, 4, 5, 6, 7** with the values computed above.
     - Column 2 `<ID label>` = canonical Feature ID.
     - Column 3 `Folder ID` = folder-name ID linking the row to disk. NEVER blank — for top-down rows without an alias, equals column 2.
     - Column 6 `In scope?` = copied from handoff (top-down) or `Need confirm` (ORPHAN-FOLDER bucket) or preserved (EXISTING-NO-FOLDER bucket).
   - **Columns 8 (`UC review stt`), 9 (`Scenario design stt`), 10 (`TC design stt`), 11 (`Execute stt`) are preserved verbatim** from `featureIndex[ID]` (blank for new rows).
   - Preserve the header row, **applying label migration if `labelMigrationNeeded` was set in Phase 0.6 case B**: replace `<existingLabel>` with `<expectedLabel>` in column 2 of the header. Otherwise keep the header verbatim.
   - Row order: existing rows in their original order, then new rows (sorted by Site alphabetical, then by canonical ID).
2. Preserve the ghi-chú/notes block below the table verbatim (do not rewrite from template). **If a label migration note was prepared in Phase 0.6 case B, append it to the END of the ghi-chú block as a new bullet line** — do not overwrite existing notes.
3. Write back to the `qc-dashboard` path. **In-place edit** (per path-registry's versioning exception for meta-config files).

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
   - Rows with `Files stt` upgrades (Missing → V<N> hoặc bump version): <N>  (<list IDs>)
   - Rows with `Files stt` regressions (V<N> → Missing): <N>  (<list IDs + items)

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

Triggered by per-UC skills (`qc-uc-read`, `qc-func-scenario-design`, `qc-func-tc-design`) when they encounter a UC ID that is not yet a row in `qc-dashboard.md`. The caller passes `uc_id=<ID>` where `<ID>` is the folder-ID-style identifier (per-UC skills derive it from the folder they are operating on).

### Bottom-up steps

1. Generate `run_id` and append worklog row `Status = Running (bottom-up, uc_id=<ID>)`.
2. Resolve `qc-dashboard` path. If the file does not exist → create it from `templates/qc-dashboard-template.md` with `<ID label> = Use Case ID` (default) so the per-UC skill can proceed; do NOT prompt for the label here (top-down handles the prompt; in bottom-up the default is safe).
3. Parse the existing dashboard (header + `featureIndex` keyed by column 2 + `folderIDIndex` keyed by column 3). Schema validation: if mismatch → STOP and report.
4. **Single-UC scope check (matches by Folder ID, not canonical ID):**
   - If `<ID>` matches an existing `Folder ID` (column 3 of any row) → exit early. Report `<ID> da co trong dashboard (Folder ID khop), khong can add`. The per-UC skill should use the matched row's canonical ID (column 2) for any downstream lookups.
   - Else if `<ID>` matches an existing `<ID label>` (column 2) but the row's `Folder ID` (column 3) is different → exit early with the same message. Per-UC skill uses the row's canonical ID.
   - Otherwise → continue.
5. Run the 6-artifact sub-scans for `<ID>` only (same logic as top-down Phase 3 but limited to a single ID; resolve folder paths inside `requirement-files/<ID>/`, `uc-review-report/<ID>/`, etc., applying the same ID-extraction regex on sub-folder names — if no folder matches the regex, fall back to a literal-name match `<ID>` exactly).
6. Add a new row to `featureIndex`:
   - Column 2 `<ID label>` → `<ID>` (folder-derived; will be replaced with canonical ID once `qc-site-map` Mode 3 reconciles).
   - Column 3 `Folder ID` → `<ID>` (same as column 2 until reconciliation).
   - `Site / Module / Feature/Use case name` → leave BLANK (no upstream context to fill them).
   - `In scope?` → `Need confirm`.
   - `Files stt` → composed from step 5.
   - Process-state columns (8-11) → blank.
7. **Optional upstream alignment check:**
   - If `project-context-master.md` exists, read its feature list. If `<ID>` is NOT present → set `outOfContext = true`.
   - If `site-map-handoff.md` exists in dashboard inbox, read it. If `<ID>` is NOT present (neither as Feature ID nor as a Folder alias) → set `outOfHandoff = true`.
8. Write the dashboard back (in-place).
9. **Write to site-map orphan inbox.** Resolve `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`. Apply append+dedupe semantics (same as top-down Phase 4):
   - File missing → create from schema in "Bottom-up output handoff".
   - File present + entry for `<ID>` already there → update only `Detected at` to current ISO timestamp.
   - File present + entry for `<ID>` missing → append a new row with `<ID>` + its `Folder paths (per source)` + the just-computed `Files stt` + current timestamp.
10. Emit the user message:

    ```text
    ✅ Da them row moi cho <ID> vao qc-dashboard.md (In scope? = Need confirm, Folder ID = <ID>).
    ✅ Da ghi <ID> vao .claude/skills/qc-site-map/inbox/dashboard-orphans.md cho qc-site-map Mode 3 reconcile.

    ⚠️ <ID> chua co trong tai lieu upstream:
    - project-context-master.md: <CO | KHONG CO | KHONG TIM THAY FILE>
    - site-map-handoff.md: <CO | KHONG CO | KHONG TIM THAY FILE>

    De reconcile orphan thanh canonical feature, hay chay /qc-site-map va chon Mode 3 (confirm orphans from dashboard).
    ```

    Suppress the warning paragraph (only show the two success lines) when both upstream files already contain `<ID>` — in that case the orphan inbox write is still safe (Mode 3 will detect the alias mapping and dedupe quickly).

11. Worklog: `Status = Done (bottom-up)`. Append `qc-dashboard.md` and `dashboard-orphans.md` as the Output.

### Bottom-up boundaries

- Bottom-up does NOT delete or consume `site-map-handoff.md`.
- Bottom-up does NOT delete `dashboard-orphans.md` — it only appends/dedupes.
- Bottom-up does NOT run the site-map gap review (Phase 0.5 is top-down only).
- Bottom-up does NOT prompt the user during the run (per-UC skills run within a larger flow; an extra prompt would derail them); the warning is emitted as text only. The per-UC skill itself emits its own pre-run warning (see "Per-UC skill precheck contract" below).
- Bottom-up may create the dashboard file from template if missing, with the default ID label.

## Boundaries

- **OWNER** of `qc-dashboard.md`. Creates the file from template on first run; updates in-place on subsequent runs.
- Writes columns **1, 2, 3, 4, 5, 6, 7**.
- **NEVER writes** columns 8 (`UC review stt`), 9 (`Scenario design stt`), 10 (`TC design stt`), 11 (`Execute stt`). Always preserved verbatim.
- **No soft-delete via `Removed`.** This skill does NOT auto-set `In scope? = Removed`. The `Removed` value remains a legal user-edit value, but the skill itself never writes it. Rows whose folder is gone keep their `In scope?` unchanged; their `Files stt` reflects all-Missing.
- **No interactive prompts** in either mode. All decisions are auto-applied per Phase 2 bucket rules. The only interactive prompt in the entire skill is the Phase 0.5 gap-review proceed/cancel (top-down only) and the Phase 0.6 ID-label confirmation when bootstrapping.
- The skill does NOT invent values for Site / Module / Feature name — in top-down mode they come from the site-map handoff; in bottom-up they remain BLANK.
- Folders matching the exclusion rules (Common, Shared, _template, …) are NEVER added as rows. Folders whose name does not match the ID regex but is otherwise valid (e.g., `TrangChuDashboard`) ARE added — they are exactly the orphans that Mode 3 reconciles.
- Schema mismatch → STOP and report. Do NOT auto-fix.
- Site-map handoff file (`site-map-handoff.md`) is consumed (read only). This skill does NOT delete it — `qc-site-map` overwrites it on its next run.
- Dashboard orphans file (`dashboard-orphans.md`) is written (append + dedupe). This skill does NOT delete it — `qc-site-map` Mode 3 owns deletion.

## Cross-skill contract

- **`qc-context-master`** — Step 1 of the top-down chain. Writes `project-context-master.md` only. NEVER writes any handoff file for this skill. NEVER invokes this skill directly. In Initialization mode it invokes `qc-site-map`; in Update mode it suggests the user to run `qc-site-map`.

- **`qc-site-map`** — Step 2 of the top-down chain. Writes `qc-site-map.md` + `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md`. In Initialization mode + after Mode 3 completes it invokes this skill directly. In Update mode it suggests the user to run `/qc-dashboard-sync`. The handoff file it writes is the SOLE upstream feature list source for top-down sync. The `Folder alias(es)` column inside the handoff is the SOLE source of truth for column 3 `Folder ID` of any non-trivial alias (top-down rows whose folder name differs from the canonical Feature ID).

- **`qc-uc-read`** — before reviewing a UC, MUST check whether the UC's Folder ID matches column 3 of any row in `qc-dashboard.md`. If absent, MUST invoke this skill in BOTTOM-UP mode (pass `uc_id=<folder-derived-ID>`). After running, `qc-uc-read` writes its own column 8 (`UC review stt`). Per-UC skills must also surface a user-facing warning when they trigger bottom-up OR when the UC row's Folder ID is still listed in `dashboard-orphans.md` (see "Per-UC skill precheck contract" below).

- **`qc-func-scenario-design`** — same bottom-up precheck contract. Writes column 9 (`Scenario design stt`).

- **`qc-func-tc-design`** — same bottom-up precheck contract. Writes column 10 (`TC design stt`).

Other skills (e.g., a future `qc-execute` skill) follow the same bottom-up precheck pattern and own column 11 (`Execute stt`) when they exist.

### Per-UC skill precheck contract

Per-UC skills (`qc-uc-read`, `qc-func-scenario-design`, `qc-func-tc-design`) MUST run this precheck BEFORE their main workflow:

1. Resolve `qc-dashboard.md` path. If the file does not exist → invoke this skill in bottom-up mode and continue.
2. Parse the dashboard. Build a `folderIDIndex` from column 3 values.
3. Derive the UC's folder ID (the actual on-disk folder name handled by the per-UC skill — typically `<UC-ID>` passed by user, but may be a non-pattern name).
4. **Case A — UC NOT in dashboard:** The UC has no row at all. Before triggering bottom-up, emit the following Vietnamese warning + prompt:

   ```text
   ⚠️ UC `<ID>` chua co trong qc-dashboard.md va se duoc them moi (Folder ID = <ID>, In scope? = Need confirm).
   Day la dau hieu UC nay chua duoc reconcile voi site-map.

   Ban muon:
   1. `site-map first` — Dung lai. Chay /qc-site-map (chon Mode 3) truoc de reconcile orphans, roi quay lai chay <ten skill nay>.
   2. `continue` — Tiep tuc. Bottom-up se add row + ghi vao dashboard-orphans.md; ban co the chay /qc-site-map Mode 3 sau de reconcile.
   ```

   - User answers `site-map first` → STOP the per-UC skill. Do NOT trigger bottom-up. Print a one-line hint to run `/qc-site-map`.
   - User answers `continue` → invoke `qc-dashboard-sync` bottom-up with `uc_id=<ID>`, then proceed.

5. **Case B — UC IS in dashboard but its Folder ID is still listed in `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`:** The row exists from a prior bottom-up run, but `qc-site-map` Mode 3 has not yet reconciled it. Emit the same two-choice Vietnamese warning but adapted:

   ```text
   ⚠️ UC `<ID>` da co trong qc-dashboard.md nhung VAN dang nam trong dashboard-orphans.md (qc-site-map Mode 3 chua reconcile).
   Ket qua cua <ten skill nay> co the bi rename/realign khi Mode 3 chay sau.

   Ban muon:
   1. `site-map first` — Dung lai. Chay /qc-site-map (chon Mode 3) truoc de reconcile, roi quay lai chay <ten skill nay>.
   2. `continue` — Tiep tuc. Output se duoc tracking duoi Folder ID hien tai; co the can rename sau khi Mode 3 chay.
   ```

   - User answers `site-map first` → STOP.
   - User answers `continue` → proceed (no bottom-up trigger needed — row already exists).

6. **Case C — UC IS in dashboard AND not in the orphan inbox:** proceed normally, no warning, no prompt. This is the happy path (the UC has been reconciled by Mode 3, or was always a clean top-down row).
