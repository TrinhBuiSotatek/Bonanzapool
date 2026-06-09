# Phase 6 - Mapping and Access

## Goal

Map screens to features, roles, touchpoints, and regression anchors.

## Tasks

1. Map each screen to related feature/spec where possible.
2. Summarize feature-level site map coverage for dashboard.
3. Map role/access by screen.
4. Identify data/API/integration/state touchpoints.
5. Identify regression and impact anchors.

## Feature-level dashboard aggregation

For dashboard handoff, aggregate by feature:

| Feature ID | Feature name | Mapped screens | Site map status | Gap / Note |
| ---------- | ------------ | -------------- | --------------- | ---------- |

Site map status values:

- `Mapped`
- `Partial`
- `Missing`
- `Conflict`
- `Need confirm`

## Rules

- Do not create dashboard rows per screen or module.
- Smallest mapping unit is Feature/UC. Module is grouping context only — never a mapping target.
- Do not create feature IDs or user-case IDs unless confirmed by project source. Use existing feature IDs or use-case ID from project context or source docs.
- If screen cannot map to a feature, list it under unmapped screens.
- If feature has no screen mapping, mark `Missing` or `Partial`.

## Output checkpoint

Write:

```text
process-logging/qc-site-map/06_mapping_access.md
```
