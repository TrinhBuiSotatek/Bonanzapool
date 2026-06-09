# Mode 3 — Confirm Orphans (from dashboard)

## Goal

Reconcile each orphan UC folder reported by `qc-dashboard-sync` (via `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`) against the existing `qc-site-map.md`. For each orphan, decide whether it is:

- **Case 1** — A folder alias of an EXISTING feature in site-map (high-confidence name match). Map the alias and persist it so the dashboard can rename column 2 to the canonical Feature ID while keeping the alias in column 3 `Folder ID`.
- **Case 2** — A POSSIBLE alias of an existing feature (partial name match, not confident enough). Ask the user. If user confirms → behave as Case 1; if user denies → behave as Case 3.
- **Case 3** — A genuinely NEW feature. Append it to site-map at the bottom of the screen tree / feature tables with `Status = Need confirm`. Ask the user follow-up questions about its module + connections; if user provides info, finish the integration. If user provides nothing, leave the new feature at `Need confirm` and continue.

When done, rewrite `qc-site-map.md`, write the handoff with updated `Folder alias(es)`, DELETE the orphan inbox file, and auto-invoke `qc-dashboard-sync`.

## Prerequisites

- `qc-site-map.md` MUST exist with real content (mode determination already gated this).
- `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` MUST exist with at least one orphan row.
- `path-registry.md` resolves successfully for `requirement-files`, `qc-site-map`, and the dashboard inbox.

## Step 1 — Load inputs

1. Generate `run_id` per the worklog protocol. Worklog: append new entry with `status = "Running (Mode 3 - load)"`, `start = now`.
2. Read `qc-site-map.md`. Parse:
   - Feature/UC list (canonical IDs + names + module + screens mapped) → `siteFeatures = Map<canonicalID → { name, module, mappedScreens[], folderAliases[] }>`.
   - Screen inventory + tree → `siteScreens` (for adjacency suggestions in Case 3).
   - Existing Folder-alias map (look for `## Folder alias map` section if previously written; build `existingAliasMap = Map<folderID → canonicalID>`). Empty if section not present.
3. Read `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`. Parse the `Dashboard Orphan UC List for Site Map` table → `orphanList = [{ folderID, folderPaths[], filesStt, detectedAt }]`. If parsing fails (corrupt table) → STOP with a Vietnamese error and ask the user to manually fix the inbox file.
4. Filter out orphans already present in `existingAliasMap` (defensive — they should not be in the inbox, but if they are, treat as already-resolved and remove from the list silently). Record removed count for the run report.

## Step 2 — Per-orphan reconciliation loop

For each `orphan ∈ orphanList`:

### 2.1 Locate source artifacts for the orphan

Resolve folder paths from `orphan.folderPaths`. Of particular interest:

- The folder under `requirement-files/<folderID>/`: search for the highest-version SRS/spec (`.md` / `.docx` / `.pdf`) AND for wireframe files (`.png` / `.jpg` / `.fig` / `.svg` / ...). If found, prefer reading the spec to extract:
  - **Feature/UC name** — explicit title in the SRS, or first H1/H2 heading.
  - **Screen name(s)** — any wireframe filename hints, or screen mentions inside the SRS.
- If `requirement-files` folder is missing for this orphan → set `evidence = "no-spec"`. Mark for Case 3 path (cannot match without evidence).

### 2.2 Compare against site-map

For the extracted `(orphanFeatureName, orphanScreenNames[])`:

1. **Exact-match check (Case 1):**
   - Compare `orphanFeatureName` against each `siteFeatures[X].name` using case-insensitive normalized comparison (strip diacritics, collapse whitespace, remove punctuation). Also compare each `orphanScreenName` against `siteScreens` entries the same way.
   - If exactly ONE feature matches with high confidence (feature-name exact match OR ≥1 screen-name exact match unambiguously inside that feature's `mappedScreens`) → declare **Case 1**, target = `siteFeatures[X]`.
2. **Partial-match check (Case 2):**
   - If 0 exact matches BUT one or more features have ≥40% normalized token overlap with `orphanFeatureName`, OR a screen-name partial-overlap inside one feature → declare **Case 2** with `candidates = [siteFeatures[Y], ...]` ranked by overlap score (highest first, top 3).
3. **No-match (Case 3):**
   - No exact match and no partial match → declare **Case 3**.

### 2.3 Apply per-case action

**Case 1 — confident alias:**

1. Append `orphan.folderID` to `siteFeatures[X].folderAliases`.
2. Record in `aliasUpdates` for later persistence: `(canonicalID = X, addedAlias = orphan.folderID)`.
3. Print a short Vietnamese confirmation line (no prompt) on the console:
   ```text
   ✓ Map: folder `<folderID>` → feature `<X>` (<name>) — exact match.
   ```
4. Move to next orphan.

**Case 2 — possible alias, ask user:**

1. Present the top candidates and ask:
   ```text
   ❓ Folder `<folderID>` (SRS: <feature name từ spec>, screens: <list>) co the la alias cua mot trong cac feature sau khong?

   1. `<canonicalID-1>` — <name-1> (mapped screens: <screens-1>)
   2. `<canonicalID-2>` — <name-2> (mapped screens: <screens-2>)
   3. `<canonicalID-3>` — <name-3> (mapped screens: <screens-3>)
   4. `none` — Khong khop, day la feature moi (chuyen sang Case 3)
   5. `skip` — Bo qua orphan nay lan nay (giu trong inbox cho lan sau)
   ```
2. Parse user response:
   - `1` / `2` / `3` (or the canonicalID text) → treat as Case 1 with `target = siteFeatures[<chosen>]`. Run the Case 1 action.
   - `none` → drop to **Case 3** action below for this orphan.
   - `skip` → record `(folderID, "skipped")` in `skippedOrphans`. Do NOT remove from inbox at end-of-run. Move to next orphan.

**Case 3 — new feature:**

1. Mint a canonical ID for the new feature. Strategy (in order):
   - If `orphan.folderID` already looks like an ID pattern (matches the project's ID regex from Phase 1) → use it verbatim as the canonical ID.
   - Else generate a new ID: pick the next sequence number in the project's prefix (e.g., next `UC-<N>` after current max). If the project's ID label is not `Use Case ID`, use the equivalent prefix.
2. Append a new entry to `siteFeatures[newCanonicalID]` with:
   - `name` = name extracted from SRS (or `orphan.folderID` if no spec was readable).
   - `module` = blank (to be filled by user prompt below).
   - `mappedScreens` = screens extracted from SRS / wireframes (best effort).
   - `folderAliases` = `[orphan.folderID]` (only if folderID differs from newCanonicalID; otherwise empty).
   - Site map status = `Need confirm`.
3. Add this new feature to the BOTTOM of the screen tree / feature tables in the working copy of `qc-site-map.md` (`Section: New features pending confirmation`). Mark with a `<!-- mode-3 added <ISO> -->` HTML comment for traceability.
4. Ask the user follow-up questions (single consolidated prompt):
   ```text
   ❓ Feature moi tu folder `<folderID>` da duoc them vao site-map (ID canonical: `<newCanonicalID>`, ten: `<name>`, screens phat hien: <list>).
   De hoan thien:

   1. Feature/screen nay thuoc Module nao? (vd: User, Admin, Vendor, hoac de trong neu chua biet)
   2. Feature nay lien ket toi cac feature/screen nao da co trong site-map? (vd: navigation tu screen X, share data voi feature Y; de trong neu chua biet)
   3. Role/access nao co the truy cap feature nay? (vd: User dang nhap, Admin; de trong neu chua biet)

   Tra loi tung dong, hoac go `skip` de giu o trang thai `Need confirm` va xu ly sau.
   ```
5. Parse user response:
   - User provides info on any of the 3 questions → integrate into `siteFeatures[newCanonicalID]`:
     - Update module / navigation references / role-access.
     - If user names a Module that does NOT exist → add the module to site-map's module list with a `Need confirm` flag.
     - If user names a navigation target that DOES exist → update both directions (this feature's `pre/post conditions` + the target feature's `regression anchors`).
   - User `skip` (or empty response) → leave the new feature at `Need confirm`; downstream user can edit `qc-site-map.md` manually.
6. Move to next orphan.

### 2.4 Worklog update per orphan

After each orphan is processed, rewrite the worklog last entry's `status` with the running counter:
`status = "Running (Mode 3 - processed <i>/<N> orphans: <case-1-count> Case1, <case-2-count> Case2, <case-3-count> Case3, <skipped-count> skipped)"`.

## Step 3 — Persist site-map changes

1. Generate the updated `qc-site-map.md` in-memory:
   - Apply all `aliasUpdates` to the appropriate sections (typically Section: Feature ↔ Screen mapping + a new `## Folder alias map` section if not already present — that section holds the canonical → aliases mapping for traceability).
   - Apply all new features added in Case 3 to the BOTTOM of the relevant section (Feature tables, screen tree leaf).
   - Update `generated at` / `last modified` metadata at top of `qc-site-map.md`.
2. Write the updated `qc-site-map.md` IN-PLACE (per path-registry exception for fixed-path files). Atomic single Write.

## Step 4 — Write updated handoff

1. Resolve `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md`.
2. If the file exists → DELETE it.
3. Compose the new handoff body with the full feature list from `siteFeatures` (including freshly-added Case 3 features). Schema per `phase-9-dashboard-handoff.md` — `mode: mode-3-confirm-orphans`, `generated_at: <now>`.
   - For each feature with non-empty `folderAliases`, fill the `Folder alias(es)` column with the comma-separated list.
   - For Case 3 features, set `In scope? = Need confirm` unless the user explicitly indicated scope during the follow-up prompt.
   - For Case 1/2-resolved features, copy their existing `In scope?` from the prior site-map content (do NOT downgrade scope just because an alias was added).
4. Write the handoff file.

## Step 5 — Delete orphan inbox

1. Resolve `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`.
2. **If `skippedOrphans` is empty** → DELETE the file outright. All orphans are reconciled.
3. **If `skippedOrphans` is non-empty** → rewrite the file containing ONLY the skipped rows (preserve their original `Detected at` timestamps). This keeps them on the queue for the next Mode 3 run.

## Step 6 — Auto-invoke `qc-dashboard-sync`

1. INVOKE `qc-dashboard-sync` via the Skill tool (no `uc_id` parameter → triggers top-down sync). The handoff written in Step 4 will drive its reconcile + rename rows whose Folder ID matches an alias.
2. Capture the invocation result for the worklog.

## Step 7 — Final report

Worklog: rewrite last entry → `status = "Done (Mode 3)"`, `end = now`, `duration_min = computed`. Print a Vietnamese summary on chat:

```text
✅ Mode 3 (Confirm orphans) hoan tat.

Da xu ly <N> orphan UC:
- Case 1 (exact alias map): <count>  — vd: <folderID-1> → <canonicalID-1>, ...
- Case 2 (user-confirmed alias): <count>
- Case 3 (new feature minted): <count>  — vd: `<newCanonicalID-1>` (<name-1>), ...
- Skipped (giu lai trong inbox): <count>

qc-site-map.md: updated.
site-map-handoff.md: rewritten.
dashboard-orphans.md: <deleted | <count> rows giu lai>.
qc-dashboard-sync: invoked → <summary tu dashboard-sync>.
```

## Boundaries

- Mode 3 does NOT re-run source inventory / screen inventory / navigation pipeline (Phases 1–8 of the standard workflow). It edits the existing site map surgically.
- Mode 3 does NOT prompt the user for `In scope?` on existing features. Only Case 3 new features get a `Need confirm` default + the optional follow-up prompt about module/connections.
- Mode 3 ALWAYS deletes (or rewrites with skipped-only) the orphan inbox at end-of-run. The inbox is not allowed to leak stale entries.
- Mode 3 ALWAYS invokes `qc-dashboard-sync` at the end. There is no `contentChanged` short-circuit (the alias-map changes alone are semantically significant for the dashboard even if the screen tree is unchanged).
- A user `cancel` mid-loop (Ctrl+C / interrupt) means the run is incomplete. The progress.md checkpoint allows resume: next run picks up at the next unprocessed orphan. Re-running detects that some aliases are already in `siteFeatures` and skips them on re-parse of the inbox.
