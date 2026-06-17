# Checkpoint Protocol

Use checkpoints to make long `qc-site-map` runs resumable.

Canonical checkpoint folder:

```text
.claude/skills/qc-site-map/process-logging/
```

If an old run used `process-logging/qc-site-map/`, read it for resume compatibility, then migrate or continue under the canonical folder.

This folder is internal scratch space. It is not a user deliverable.

---

## Required files

```text
.claude/skills/qc-site-map/process-logging/progress.md
.claude/skills/qc-site-map/process-logging/00_run_control.md
.claude/skills/qc-site-map/process-logging/01_site_map_model.md
.claude/skills/qc-site-map/process-logging/02_data_map_model.md
.claude/skills/qc-site-map/process-logging/03_commit_handoff_cleanup.md
```

Mode 3 may also write:

```text
.claude/skills/qc-site-map/process-logging/mode_3_confirm_orphans.md
```

---

## Resume rule

At the start of every run:

1. Look for `progress.md` in the canonical checkpoint folder, then in the legacy folder.
2. If found, read `run_id`, `mode`, `last_workflow_done`, `next_workflow`, and `status`.
3. Resume from `next_workflow` if checkpoint files are present and consistent.
4. If checkpoints are inconsistent, report the inconsistency and resume from the last safe workflow.
5. Do not re-prompt mode on resume. Preserve the mode recorded by the interrupted run.

---

## Checkpoint contract

Every checkpoint must include:

- run id or timestamp;
- mode: Initialization / Update / Mode3-ConfirmOrphans / Skipped;
- workflow name;
- inputs used;
- output produced;
- changed/unmodified state where relevant;
- gaps/conflicts/assumptions found;
- next workflow.

Every workflow must write its checkpoint before moving to the next workflow.

---

## Cleanup rule

Do not delete checkpoint folders mid-run.

Cleanup is allowed only after:

- `qc-site-map.md` was written successfully or confirmed unchanged;
- `qc-data-map.md` was written successfully, confirmed unchanged, or explicitly skipped with a reason;
- dashboard handoff was written, preserved, or explicitly skipped with a reason;
- final handover summary was produced.
