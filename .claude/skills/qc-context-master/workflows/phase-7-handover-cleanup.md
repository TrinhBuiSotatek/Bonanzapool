# Phase 7 - Handover and Cleanup

Goal: report completion to the user and clean up internal checkpoints on success.

## Inputs

- `05_context_rendered.md`
- `06_sitemap_handoff.md`
- written `project-context-master.md`
- `qc-site-map` invocation result if it was called from Phase 6

## User-facing handover

Respond in Vietnamese with a concise summary:

```text
Hoan tat <Initialization | Update | Skipped> project context.

- project-context-master.md: created / updated / unchanged at <path>
- Sources consolidated: <count> files (<count-with-version> co version, <count-no-version> khong co version)
- Feature candidates: <counts>
- Derived / need confirm: <counts>
- Important missing context: <top items>
- Conflicts: <count or none>
- Next-step:
  - Initialization -> qc-site-map auto-invoked. Ket qua: <summary>
  - Update with changes -> de xuat user chay /qc-site-map
  - Update no change -> khong can chay downstream
- Suggested next action: <action>
```

Do not paste the full `project-context-master.md` into chat unless the user asks.

## Cleanup rule

Cleanup MUST run when ALL of the following are true:
- `project-context-master.md` was successfully written (or Update mode finished without changes).
- Phase 6 completed (either auto-invoked, suggested, or recorded "no downstream action").
- Final user summary has been produced.

Cleanup action:

1. Delete the entire `.claude/skills/qc-context-master/process-logging/` folder, including `progress.md` and all checkpoint files.
2. Worklog: rewrite last entry → `status = "Done"`, `end = now`, `duration_min = computed`, fill the final summary in `output` (per the protocol).

If cleanup fails (permission error, file lock, etc.), report it as a non-blocking issue. The deliverables are still valid.

## Special case: Skipped runs (Phase 0 preflight `no`)

If Phase 0 stopped due to version preflight `no`:
- Cleanup still runs to remove any stale checkpoints that may have been written by a previous interrupted run.
- The worklog row records `Status = Skipped (preflight no-change)`.
