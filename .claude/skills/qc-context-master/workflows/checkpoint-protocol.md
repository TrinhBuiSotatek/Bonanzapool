# Checkpoint and Resume Protocol

Scope: shared rules for all `qc-context-master` workflow phases.

Purpose: make the skill resilient to context limit or interruption by persisting phase outputs, updating worklog state, and allowing a later run to continue without redoing completed work.

## Process logging folder

All internal checkpoints live under:

`.claude/skills/qc-context-master/process-logging/`

Create it lazily when the first checkpoint is written.

## Checkpoint files

| File | Owner phase | Purpose |
|---|---|---|
| `progress.md` | Phase 0+ | Single source of truth for resume. |
| `01_input_audit.md` | Phase 1 | Resolved paths, mode, source inventory, missing document groups. |
| `02_feature_inventory.md` | Phase 2 | Feature/use case candidates and inventory delta. |
| `03_context_section_01.md` to `03_context_section_08.md` | Phase 3 | Draft content, sources, gaps, assumptions, and confidence per section. |
| `04_gap_readiness.md` | Phase 4 | Gap classification, readiness section, open questions. |
| `05_context_rendered.md` | Phase 5 | Final rendered context (with `Sources consolidated` table) and write status. |
| `06_sitemap_handoff.md` | Phase 6 | Site map handoff decision: auto-invoked / suggested / none. |
| `07_handover.md` | Phase 7 | Final user-facing summary and cleanup status. |

## `progress.md` format

```markdown
# qc-context-master progress

- run_id: run-XXX
- mode: initialization | update
- started_at: <ISO-8601 datetime>
- last_phase_done: <phase-id>
- next_phase: <phase-id>
- updated_at: <ISO-8601 datetime>

## Notes
<any resume-critical notes>
```

## Phase checkpoint contract

Each phase checkpoint must contain enough information for the next phase to continue without rerunning the previous phase.

At the end of each phase, do these steps in order:

1. Write the checkpoint file.
2. Update `progress.md` with `last_phase_done`, `next_phase`, and `updated_at`.
3. Update the agent worklog row if the project uses one.

If a phase writes a real user-visible deliverable, write the deliverable before its checkpoint.

## Resume detection

At skill start:

1. Check `process-logging/progress.md`.
2. If not found, start a fresh run.
3. If found, report the prior run ID, last completed phase, and next phase.
4. Ask the user whether to continue or restart.
5. If continuing, load the checkpoints required for the next phase.
6. If restarting, delete `process-logging/` and start fresh.

## Resume load table

| Resuming at phase | Load these files |
|---|---|
| Phase 1 | `progress.md` only |
| Phase 2 | `01_input_audit.md` |
| Phase 3 | `01_input_audit.md`, `02_feature_inventory.md` |
| Phase 4 | all `03_context_section_*.md`, plus `02_feature_inventory.md` |
| Phase 5 | all section checkpoints and `04_gap_readiness.md` |
| Phase 6 | `05_context_rendered.md`, `02_feature_inventory.md` |
| Phase 7 | `05_context_rendered.md`, `06_sitemap_handoff.md` if present |

Always re-resolve `path-registry.md` paths after resume because paths may have changed.

## Worklog notes

Worklog: update the device's JSONL entry before entering each phase, per the protocol at `docs/qc-lead/agent-work-log.local/README.md`. Do not include files under `process-logging/` in `input`/`output`.

User-visible deliverables: only `project-context-master.md` is owned by this skill. Downstream files (`qc-site-map.md`, `qc-dashboard.md`) are owned by their respective skills and never written here.

## Cleanup

Delete `process-logging/` after Phase 7 completes successfully (output written + downstream handoff decided). Cleanup runs even on `Skipped` Phase 0 outcomes to clear any stale checkpoints from previous partial runs.
