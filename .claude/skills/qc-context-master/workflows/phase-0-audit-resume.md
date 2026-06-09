# Phase 0 - Audit, Resume, and Version Preflight

Goal: determine whether this is a fresh run or a resumed run, and in Update mode run the version preflight to short-circuit when no source change is detected.

## Steps

1. Read `workflows/checkpoint-protocol.md`.
2. Check `.claude/skills/qc-context-master/process-logging/progress.md`.
3. If no progress file exists, continue as a fresh run.
4. If progress exists, read `run_id`, `mode`, `last_phase_done`, and `next_phase`.
5. Ask the user whether to continue from `next_phase` or restart.
6. If the user chooses restart, delete the `process-logging/` folder and continue to step 8.
7. If the user chooses continue, load checkpoint files based on the resume load table and continue from `next_phase`.
8. **Version preflight (Update mode only — when the resolved `project-context-master.md` already exists with real content):**
   1. Read the existing `project-context-master.md`.
   2. Parse the `Sources consolidated` table at the top of the file. Build `prevSources = [{ file, version }]`.
   3. For each entry in `prevSources`, resolve its parent folder (from `path-registry.md` logical names — typically inside `High-level-files`) and scan for the highest version of files with the same base name (regex `_v(\d+)` on filename; if missing, treat as `v1`).
   4. Classify per source:
      - `same` — current version equals recorded version.
      - `upgraded` — current version higher than recorded.
      - `new-file` — found another file in the same folder family that was not in `prevSources` (treat the appearance of a brand-new source as a real change).
      - `deleted` — file no longer exists.
   5. If at least one source has status `upgraded` / `new-file` / `deleted` → proceed to Phase 1 with the full pipeline.
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

   7. User answer `no` → JUMP TO Phase 7 cleanup (do NOT exit immediately). Phase 7 will: (a) delete the entire `process-logging/` folder to clear any stale checkpoints from previous partial runs, (b) write the worklog row with `Status = Skipped (preflight no-change)`, (c) print the Vietnamese summary `Mode: Skipped`. Do NOT delete the existing `project-context-master.md` output (the file stays valid).
   8. User answer `yes` → proceed to Phase 1.

## Output

No checkpoint is required for a fresh run in Phase 0. If resuming, update `progress.md` with the new run ID and continue. If Phase 0 stopped due to preflight `no`, append the skip event into the worklog only — do not create checkpoint files.

## User-facing message on resume

Use Vietnamese:

```text
Phat hien checkpoint tu run truoc:
- Run ID: <run_id>
- Da hoan thanh: Phase <last_phase_done>
- Phase tiep theo: <next_phase>

Ban muon:
1. Continue - tiep tuc tu phase tiep theo
2. Restart - chay lai tu dau va xoa checkpoint cu
```
