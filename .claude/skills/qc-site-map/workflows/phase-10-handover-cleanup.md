# Phase 10 - Handover and Cleanup

## Goal

Report completion to the user and clean up internal checkpoints on success.

## Final user summary

Respond in Vietnamese with:

- Mode: Initialization / Update / Skipped.
- `qc-site-map.md`: created / updated / unchanged.
- Sources consolidated: count of files, count with new version since last run.
- Source quality: official / derived / partial.
- Number of screens found.
- Number of features with mapped screens.
- Number of unmapped screens.
- Dashboard handoff:
  - Initialization → `qc-dashboard-sync` auto-invoked. Result: <summary>
  - Update with changes → handoff written, user suggested to run `/qc-dashboard-sync`.
  - Update no change → handoff not written, no downstream action.
- Major gaps/conflicts/assumptions.
- Suggested next action for QC Lead.

## Cleanup rule

Cleanup MUST run when ALL of the following are true:
- `qc-site-map.md` was successfully written (or Update mode finished without changes).
- Phase 9 completed (auto-invoked, suggested, or recorded "no downstream action").
- Final user summary has been produced.

Cleanup action:

1. Delete the entire `.claude/skills/qc-site-map/process-logging/` folder, including `progress.md` and all checkpoint files.
2. Worklog: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`, fill the final summary in `output` (per the protocol).

If cleanup fails (permission error, file lock, etc.), report it as a non-blocking issue. The deliverables are still valid.

## Special case: Skipped runs (Phase 0 preflight `no`)

If Phase 0 stopped due to version preflight `no`:
- Cleanup still runs to remove any stale checkpoints.
- The worklog row records `Status = Skipped (preflight no-change)`.
