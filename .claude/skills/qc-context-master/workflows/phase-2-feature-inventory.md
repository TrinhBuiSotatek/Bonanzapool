# Phase 2 - Feature Inventory

Goal: create a feature/use case candidate list for inclusion in `project-context-master.md` Section 4 / Section 6 (system structure + module/feature relationships). This list is also the input that `qc-site-map` will read downstream when mapping screens to features.

> Note: this skill no longer writes a feature-list handoff for `qc-dashboard-sync`. The feature list reaches the dashboard via `qc-site-map` only (which aggregates by feature and writes its own `site-map-handoff.md`).

## Inputs

- `01_input_audit.md`
- `High-level-files`
- `requirement-common-files` when fallback is needed
- existing `project-context-master.md` in Update mode (read previous feature list from Section 4/6)

## Extraction priority

Extract feature candidates in this order:

1. Explicit feature list, WBS, scope table, use case list, story list, or module list from `High-level-files`.
2. Site map or module list from `High-level-files`.
3. `requirement-common-files` or SRS/spec folder if no reliable high-level inventory exists.

## Candidate fields

| Field | Rule |
|---|---|
| `ID` | Prefer official source ID. If missing, use `TMP-001`, `TMP-002`, etc. and mark `Need confirm`. |
| `Site` | Use source site/portal/app. If unknown, use `TBD`. |
| `Module` | Use source module/business area. If unknown, use `TBD`. |
| `Feature/Use case name` | Short name from source title, heading, file name, or folder name. |
| `In scope?` | `Yes` if explicitly current; `Need confirm` if unclear. |
| `Source type` | `official high-level`, `derived from requirement-common-files`, or `existing dashboard`. |
| `Notes` | Include confirmation needs, missing IDs, or source ambiguity. |

## Update mode delta rules

When an existing `project-context-master.md` exists:

1. Preserve the QC Lead-reviewed feature list embedded in the previous output.
2. Mark new candidates as `new`.
3. Mark previously-removed candidates that appear again as `re-add candidate`.
4. Mark previous candidates not found in current sources as `not found in current source`; do not silently remove them — surface as gap for QC Lead review.

## If no candidates can be extracted

Do not invent fake features. Continue the project context workflow, but record a high-priority open question for QC Lead/BA. Downstream (`qc-site-map`) will not be able to map any screen to a feature, and `qc-dashboard-sync` will not receive a feature list — both are acceptable degraded states, but the gap must be visible.

## Checkpoint

Write `process-logging/02_feature_inventory.md` with:

```markdown
# Feature Inventory

## Extraction summary
- source strategy:
- official candidates:
- derived candidates:
- temporary IDs:
- blocked: yes/no

## Feature candidates
| ID | Site | Module | Feature/Use case name | In scope? | Source | Source type | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|

## Feature inventory delta
- new:
- existing unchanged:
- re-add candidates:
- not found in current source:
- need confirmation:

## Gaps for project context
| Gap | Type | Impact | Suggested owner |
|---|---|---|---|
```

Then update `progress.md`:

- `last_phase_done: 2`
- `next_phase: 3`
