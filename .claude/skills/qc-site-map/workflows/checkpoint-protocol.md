# Checkpoint Protocol

Use checkpoints to make long `qc-site-map` runs resumable.

All checkpoints live under:

```text
process-logging/qc-site-map/
```

This folder is internal scratch space. It is not a user deliverable.

## Required files

```text
process-logging/qc-site-map/progress.md
process-logging/qc-site-map/01_input_audit.md
process-logging/qc-site-map/02_context_baseline.md
process-logging/qc-site-map/03_source_inventory.md
process-logging/qc-site-map/04_screen_inventory.md
process-logging/qc-site-map/05_navigation_map.md
process-logging/qc-site-map/06_mapping_access.md
process-logging/qc-site-map/07_gap_readiness.md
process-logging/qc-site-map/08_site_map_rendered.md
process-logging/qc-site-map/09_dashboard_handoff.md
process-logging/qc-site-map/10_handover.md
```

## Resume rule

At the start of every run:

1. Look for `process-logging/qc-site-map/progress.md`.
2. If it exists, read `last_phase_done`, `next_phase`, and `mode`.
3. Resume from `next_phase` if checkpoint files are present and consistent.
4. If checkpoints are inconsistent, report the inconsistency and resume from the last safe phase.

## Checkpoint contract

Every phase checkpoint must include:

- run id or timestamp;
- mode: Initialization / Update;
- phase name;
- inputs used;
- output produced;
- gaps/conflicts/assumptions found;
- next phase.

Each phase must write its checkpoint before moving to the next phase.

## Cleanup rule

Do not delete `process-logging/qc-site-map/` mid-run.

Cleanup is allowed only after:

- `qc-site-map.md` was written successfully;
- dashboard handoff was written or explicitly skipped with a reason;
- final handover summary was produced.
