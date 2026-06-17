# Mode 3 — Confirm Orphans from Dashboard

## Goal

Reconcile each orphan UC folder reported by `qc-dashboard-sync` through:

```text
.claude/skills/qc-site-map/inbox/dashboard-orphans.md
```

against the existing `qc-site-map.md`.

For each orphan, decide whether it is:

- **Case 1** — A folder alias of an existing feature in the site map, with high-confidence name/screen match.
- **Case 2** — A possible alias of an existing feature, requiring user confirmation.
- **Case 3** — A genuinely new feature that must be appended to the site map with `Need confirm` status.

When done, rewrite `qc-site-map.md`, write the updated `site-map-handoff.md`, delete or rewrite the orphan inbox, and auto-invoke `qc-dashboard-sync`.

Mode 3 does not rebuild `qc-data-map.md`.

---

## Prerequisites

- `qc-site-map.md` MUST exist with real content.
- `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` MUST exist with at least one orphan row.
- `path-registry.md` resolves successfully for requirement files, `qc-site-map.md`, and dashboard inbox.
- `qc-dashboard-sync` can be invoked.

If `qc-data-map.md` exists, leave it untouched. If a Case 3 new feature likely introduces a new entity, mention in the final report that `qc-data-map.md` should be updated in the next normal Update run.

---

## Step 1 — Load inputs

1. Generate or reuse `run_id` according to `workflows/checkpoint-protocol.md`.
2. Append a worklog/progress entry with `status = Running (Mode 3 - load)`.
3. Read `qc-site-map.md`.
4. Parse:
   - Feature/UC list: canonical IDs, names, module, mapped screens, `In scope?`, and aliases.
   - Screen inventory and tree.
   - Existing `Folder alias map` section if present.
5. Read `.claude/skills/qc-site-map/inbox/dashboard-orphans.md`.
6. Parse table `Dashboard Orphan UC List for Site Map` into:

```text
orphanList = [{ folderID, folderPaths[], filesStt, detectedAt }]
```

7. If parsing fails, STOP with a Vietnamese error asking the user to manually fix the inbox file.
8. Filter out orphans already present in `existingAliasMap`; record removed count.

Write checkpoint:

```text
.claude/skills/qc-site-map/process-logging/mode_3_confirm_orphans.md
```

---

## Step 2 — Per-orphan reconciliation loop

For each orphan:

### 2.1 Locate source artifacts

Resolve folder paths from `orphan.folderPaths`.

Prefer evidence from:

- `requirement-files/<folderID>/`;
- highest-version SRS/spec (`.md`, `.docx`, `.pdf`) when readable;
- wireframe files (`.png`, `.jpg`, `.fig`, `.svg`, etc.);
- existing feature/use-case naming conventions.

Extract:

- feature/use-case name;
- screen names;
- module hints;
- role/access hints if obvious;
- data/entity hints only as note, not as data-map update.

If no evidence is found, mark `evidence = no-spec` and treat as Case 3 unless user says otherwise.

### 2.2 Compare against site map

Normalize names by:

- case-insensitive comparison;
- stripping diacritics;
- collapsing whitespace;
- removing punctuation;
- comparing key tokens.

Case logic:

1. **Case 1 exact/high-confidence alias**
   - Exactly one feature matches by normalized feature name; or
   - at least one extracted screen name matches unambiguously inside one feature's mapped screens.

2. **Case 2 possible alias**
   - No exact match; and
   - one or more features have at least 40 percent normalized token overlap with orphan feature name; or
   - one screen-name partial overlap points to candidate features.

3. **Case 3 new feature**
   - No exact or useful partial match.

### 2.3 Case 1 — Confident alias

1. Append `orphan.folderID` to the target feature's `folderAliases` if not already present.
2. Record alias update:

```text
canonicalID -> addedAlias
```

3. Print a short Vietnamese confirmation line:

```text
✓ Map: folder `<folderID>` → feature `<canonicalID>` (<name>) — exact match.
```

4. Move to next orphan.

### 2.4 Case 2 — Possible alias, ask user

Present up to top 3 candidates:

```text
❓ Folder `<folderID>` (SRS: <feature name từ spec>, screens: <list>) co the la alias cua mot trong cac feature sau khong?

1. `<canonicalID-1>` — <name-1> (mapped screens: <screens-1>)
2. `<canonicalID-2>` — <name-2> (mapped screens: <screens-2>)
3. `<canonicalID-3>` — <name-3> (mapped screens: <screens-3>)
4. `none` — Khong khop, day la feature moi (chuyen sang Case 3)
5. `skip` — Bo qua orphan nay lan nay (giu trong inbox cho lan sau)
```

Parse response:

- `1` / `2` / `3` / canonical ID -> treat as Case 1 with chosen target.
- `none` -> continue as Case 3.
- `skip` -> record skipped orphan and leave it in inbox for the next Mode 3 run.

### 2.5 Case 3 — New feature

1. Mint canonical ID:
   - If `orphan.folderID` already matches project ID convention, use it as canonical ID.
   - Otherwise generate next sequence in the project's prefix, such as `UC-<N>`.
2. Append a new feature to the site map with:
   - canonical ID;
   - name from spec or folder ID;
   - module = blank / `Need confirm` unless evidence is clear;
   - mapped screens from spec/wireframes if found;
   - `Folder alias(es)` only if folder ID differs from canonical ID;
   - `In scope? = Need confirm` unless user confirms;
   - `Site map status = Need confirm`.
3. Add it under a `New features pending confirmation` note in relevant screen/feature sections.
4. Add trace comment if compatible with project style:

```html
<!-- mode-3 added <ISO-8601 datetime> -->
```

5. Ask one consolidated prompt:

```text
❓ Feature moi tu folder `<folderID>` da duoc them vao site-map (ID canonical: `<newCanonicalID>`, ten: `<name>`, screens phat hien: <list>).
De hoan thien:

1. Feature/screen nay thuoc Module nao? (vd: User, Admin, Vendor, hoac de trong neu chua biet)
2. Feature nay lien ket toi cac feature/screen nao da co trong site-map? (vd: navigation tu screen X, share data voi feature Y; de trong neu chua biet)
3. Role/access nao co the truy cap feature nay? (vd: User dang nhap, Admin; de trong neu chua biet)

Tra loi tung dong, hoac go `skip` de giu o trang thai `Need confirm` va xu ly sau.
```

6. If user provides info, integrate module/navigation/role-access into the site map working copy. If user skips or gives no info, leave the feature as `Need confirm`.

### 2.6 Worklog update per orphan

After each orphan, update progress status:

```text
Running (Mode 3 - processed <i>/<N> orphans: <case1> Case1, <case2> Case2, <case3> Case3, <skipped> skipped)
```

---

## Step 3 — Persist site-map changes

1. Generate updated `qc-site-map.md` in memory.
2. Apply alias updates to:
   - Section 8 Feature-level coverage summary;
   - Section 13 Folder alias map.
3. Apply new Case 3 features to relevant site-map sections with `Need confirm` markers.
4. Preserve existing reviewed content and existing aliases.
5. Update metadata date/mode.
6. Write updated `qc-site-map.md` atomically.

Do not update `qc-data-map.md` in Mode 3. Note any possible data-map follow-up in the final report.

---

## Step 4 — Write updated handoff

Resolve:

```text
.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md
```

If the file exists, delete it before writing the new version.

Compose the full feature list from the updated site map, including Case 3 features.

Use schema from `workflow-3-commit-handoff-cleanup.md` with:

```text
mode: mode-3-confirm-orphans
```

Rules:

- Fill `Folder alias(es)` for every feature with aliases.
- For Case 3 features, set `In scope? = Need confirm` unless user explicitly scoped it.
- For Case 1/2 features, copy existing `In scope?`; do not downgrade scope just because an alias was added.
- Do not write `qc-dashboard.md` directly.

---

## Step 5 — Delete or rewrite orphan inbox

Resolve:

```text
.claude/skills/qc-site-map/inbox/dashboard-orphans.md
```

If no orphans were skipped, delete the file.

If some orphans were skipped, rewrite the file with ONLY skipped rows and preserve original `Detected at` timestamps.

Mode 3 owns this inbox lifecycle and is the only deleter.

---

## Step 6 — Auto-invoke `qc-dashboard-sync`

Invoke `qc-dashboard-sync` without `uc_id` so it runs top-down sync from the updated `site-map-handoff.md`.

Capture invocation result for the worklog/final report.

There is no contentChanged short-circuit in Mode 3. Alias changes are semantically significant for dashboard sync.

---

## Step 7 — Final report

Worklog: rewrite last entry with:

```text
status = Done (Mode 3)
end = now
duration_min = computed
```

Print Vietnamese summary:

```text
✅ Mode 3 (Confirm orphans) hoan tat.

Da xu ly <N> orphan UC:
- Case 1 (exact alias map): <count> — vd: <folderID-1> → <canonicalID-1>, ...
- Case 2 (user-confirmed alias): <count>
- Case 3 (new feature minted): <count> — vd: `<newCanonicalID-1>` (<name-1>), ...
- Skipped (giu lai trong inbox): <count>

qc-site-map.md: updated.
qc-data-map.md: unchanged (Mode 3 khong rebuild data map). <data-map follow-up neu co>
site-map-handoff.md: rewritten.
dashboard-orphans.md: <deleted | <count> rows giu lai>.
qc-dashboard-sync: invoked → <summary tu dashboard-sync>.
```

---

## Boundaries

- Mode 3 does not re-run normal source inventory, screen inventory, navigation, or data-map workflow.
- Mode 3 does not prompt for `In scope?` on existing features.
- Mode 3 only uses Case 3 follow-up prompt for new features.
- Mode 3 always deletes or rewrites orphan inbox at end-of-run.
- Mode 3 always invokes `qc-dashboard-sync` at end-of-run.
- If user cancels mid-loop, leave checkpoint/progress so next run can resume safely.
