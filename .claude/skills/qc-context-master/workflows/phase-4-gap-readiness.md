# Phase 4 - Gap Classification and Readiness

Goal: synthesize gaps, assumptions, conflicts, readiness, and open questions from previous checkpoints.

## Inputs

- all `03_context_section_*.md` checkpoints
- `02_feature_inventory.md`
- existing Section 10 from `project-context-master.md` in Update mode

## Steps

1. Collect all gaps, assumptions, and conflicts from Section 1-8 checkpoints.
2. Classify each gap:
   - `QC-fillable`
   - `Derivable from detailed requirement docs`
   - `Needs BA/Tech Lead source`
   - `Blocking`
3. Create Section 9 readiness content.
4. Create or update Section 10 open questions.
5. In Update mode, carry forward unresolved open questions unless clearly resolved by current sources.
6. Do not delete resolved questions; mark them `Resolved` if the template/status model supports it.
7. Prioritize questions that affect downstream QC correctness.

## Readiness groups

Assess at least these groups:

- Project goal and scope.
- System/site/module overview.
- Feature/use case inventory.
- Users/roles/permission overview.
- Business flows and module relationships.
- Common rules/data/state/integration.
- Platform/environment/device/NFR.
- Document status tracking.

Use status: `Ready`, `Partial`, `Missing`, `Conflict`, or `N/A`.

Use confidence: `High`, `Medium`, or `Low`.

## Checkpoint

Write `process-logging/04_gap_readiness.md`:

```markdown
# Gap and Readiness

## Gap classification
| Gap | Type | Impact | Owner | Priority | Status |
|---|---|---|---|---|---|

## Readiness draft for Section 9
<markdown content in Vietnamese>

## Open questions draft for Section 10
| ID | Question / needed confirmation | Why important | Impact if unclear | Priority | Owner | Status |
|---|---|---|---|---|---|---|

## Resolved carry-over questions
| ID | Resolution | Source |
|---|---|---|
```

Then update `progress.md`:

- `last_phase_done: 4`
- `next_phase: 5`
