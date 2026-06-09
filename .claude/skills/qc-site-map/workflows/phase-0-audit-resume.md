# Phase 0 - Audit, Resume, Mode Detection, and Version Preflight

## Goal

Detect resume state, decide which mode to run (Initialization / Update / Mode 3 Confirm-Orphans), and — in Update mode only — run the version preflight to short-circuit when no source change is detected.

## Steps

1. **Resume detection.** Check `process-logging/qc-site-map/progress.md`.
   - If found, read the last completed phase + next phase + the `mode` field. Branch into the resume path: resume from the next safe phase using the SAME mode that was recorded. Do NOT re-prompt the user for mode selection on resume — preserves user intent across interruption.
   - If no progress file exists, continue to step 2 for fresh-run mode detection.

2. **Mode signals.** Compute two booleans:
   - `siteMapExists` = `qc-site-map.md` exists at the path resolved from `path-registry.md` AND its byte length is > 0 AND it contains at least one section header (`#`).
   - `orphanInboxExists` = `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` exists AND parses to at least ONE data row in its `Dashboard Orphan UC List for Site Map` table (rows with all-empty cells do not count).

3. **Apply the mode decision table:**

   | siteMapExists | orphanInboxExists | Action |
   |:-:|:-:|---|
   | No  | — (any) | `mode = Initialization`. **NOTE:** if `orphanInboxExists` is `Yes` here, append a warning to the Phase 0 checkpoint: *"Orphan inbox exists but site map missing — orphans will NOT be reconciled this run. They remain in inbox for a future Mode 3 run after site map is initialized."* Do NOT delete the inbox file. |
   | Yes | No  | `mode = Update`. Proceed to step 4 (version preflight). |
   | Yes | Yes | Run the Mode-2/3 prompt below to let the user pick the mode. |

4. **Mode-2/3 prompt** (only when both `siteMapExists` and `orphanInboxExists` are true). Read the orphan inbox briefly to count rows for the prompt message:

   ```text
   📋 Phat hien 2 trang thai dong thoi:
   - qc-site-map.md ton tai (mode Update kha dung)
   - .claude/skills/qc-site-map/inbox/dashboard-orphans.md ton tai (<N> orphan UC tu qc-dashboard-sync bottom-up)

   Ban muon chay mode nao?
   1. `mode 3` (mac dinh) — Confirm orphans: reconcile <N> orphan UC voi site-map hien tai (mapping case 1/2/3), update handoff, trigger dashboard-sync.
   2. `mode 2` — Update site map: refresh content tu source files, KHONG dong cham toi orphans (orphans van con cho lan sau).
   3. `both` — Chay mode 2 truoc roi mode 3 (refresh site-map roi reconcile orphans tren site-map moi).
   ```

   Parse the user response (case-insensitive, allow `3` / `mode 3` / `mode3` etc.):
   - `mode 3` (default if input is empty/unrecognized) → `mode = Mode3-ConfirmOrphans`. JUMP to `workflows/mode-3-confirm-orphans.md` — Phases 1-10 of this workflow are SKIPPED entirely.
   - `mode 2` → `mode = Update`. Continue to step 5 (version preflight). Orphan inbox is left untouched.
   - `both` → `mode = Update`. Set `auto-chain-mode-3 = true` in progress.md notes; the chain into Mode 3 fires automatically when Phase 10 cleanup of the Update run is done. The Phase 9 dashboard-sync invocation from the Update run is **suppressed** (only the Mode 3 invocation fires).

5. **Version preflight (Update mode only — when `mode == Update` and the resolved `qc-site-map.md` already exists with real content):**
   1. Read the existing `qc-site-map.md`.
   2. Parse the `Sources consolidated` table (Section 2). Build `prevSources = [{ file, version }]`.
   3. For each entry in `prevSources`, resolve its parent folder (from `path-registry.md` logical names — typically project-context-master, high-level-files, wireframe folder, etc.) and scan for the highest version of files with the same base name (regex `_v(\d+)` on filename; if missing, treat as `no-version`).
   4. Classify per source: `same` / `upgraded` / `new-file` / `deleted` (same definitions as in qc-context-master Phase 0).
   5. If at least one source has status other than `same` → proceed to Phase 1 with the full pipeline.
   6. If ALL sources are `same` → ask the user:

      ```text
      Khong phat hien version moi cua cac source files da consolidated lan truoc:
      - <file 1>: v<N> (khong doi)
      - <file 2>: v<N> (khong doi)
      ...

      Luu y: co che nay chi detect version qua ten file (regex _v<N>).
      Neu ban da sua content ma khong tang version, hay tra loi yes de chay lai.

      Ban co muon chay lai khong? [yes/no]
      ```

   7. User answer `no` → JUMP TO Phase 10 cleanup (do NOT exit immediately). Phase 10 will: (a) delete the entire `process-logging/qc-site-map/` folder to clear any stale checkpoints from previous partial runs, (b) write the worklog row with `Status = Skipped (preflight no-change)`, (c) print the Vietnamese summary `Mode: Skipped`. Do NOT delete the existing `qc-site-map.md` output (the file stays valid). **If `auto-chain-mode-3` was set in step 4, override the skip — proceed directly to Mode 3 since the user explicitly asked for chained `both`.**
   8. User answer `yes` → proceed to Phase 1.

## Output checkpoint

Update or create:

```text
process-logging/qc-site-map/progress.md
```

Minimum content:

```md
# QC Site Map Progress

- run_id:
- mode: Unknown / Initialization / Update / Mode3-ConfirmOrphans / Skipped
- last_phase_done: 0
- next_phase: 1
- status: Running
- auto-chain-mode-3: false / true   # only true when user picked `both`
- notes:
```

If Phase 0 stopped due to preflight `no` AND `auto-chain-mode-3 = false`, set `status: Skipped` and `next_phase: —`.

If `mode = Mode3-ConfirmOrphans`, set `next_phase: mode-3-step-1` (Mode 3 uses its own step numbering, not the 1-10 of the standard workflow).
