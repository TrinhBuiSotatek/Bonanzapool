---
name: qc-site-map
description: generates and updates qc-site-map.md and qc-data-map.md for agentic QC workflows. Use when the user asks to initialize or update a screen-first QC site map, build a data-entity-first QC data map, map screens to features, analyze navigation, role access, data/API/integration/state touchpoints, data lifecycle, CRUD permissions, regression impact, or sync site-map feature coverage into qc-dashboard. Reads project-context-master.md as a hard baseline and preserves the top-down chain qc-context-master to qc-site-map/qc-data-map to qc-dashboard-sync. Supports Initialization, Update, and Confirm-Orphans mode for dashboard orphan reconciliation.
---

# QC Site Map

## Purpose

Generate and maintain two complementary QC context files:

1. `qc-site-map.md` — screen-first site map for sites, portals, apps, modules, screens, navigation, role access, screen-feature mapping, touchpoints, gaps, and regression anchors.
2. `qc-data-map.md` — data-entity-first map for entities, relationships, lifecycle, CRUD permissions, feature-entity coverage, CR impact, and data-driven regression scope.

These files help downstream QC agents review specs, design function/integration/system/regression scenarios, design test cases, support execution, and verify bugs with screen-level and data-level project understanding.

`qc-site-map.md` and `qc-data-map.md` must not replace detailed specs, wireframes, API docs, DB schemas, `project-context-master.md`, or `qc-dashboard.md`. They add screen and data structure layers on top of the project context.

Generated outputs should be written in Vietnamese by default so QC Lead can review and edit them easily.

---

## Output ownership

| File | Owner | This skill may do |
|---|---|---|
| `qc-site-map.md` | `qc-site-map` | Create and update directly as the screen-first QC site map. |
| `qc-data-map.md` | `qc-site-map` | Create and update directly as the data-entity-first QC data map. |
| `project-context-master.md` | `qc-context-master` | Read as required baseline. Do not rewrite. |
| `qc-dashboard.md` | `qc-dashboard-sync` | Do not write directly. Send feature-level site-map handoff only. |
| Spec / wireframe / API docs / DB schema / ERD | BA / BE / Tech Lead | Read as evidence only. Do not rewrite. |
| Scenario / test case files | Downstream QC skills | Do not create here. |

`qc-site-map.md` is the QC source for screen structure, navigation, and screen-to-feature mapping.

`qc-data-map.md` is the QC source for data entity inventory, lifecycle, CRUD permission, feature-entity coverage, and data-driven CR/regression impact.

`qc-dashboard.md` tracks QC workflow status at feature/spec level, not screen level or entity level. Do not create one dashboard row per screen. Do not create data-level dashboard rows unless `qc-dashboard-sync` explicitly supports a future data-map handoff contract.

---

## Modes

Determine the mode from on-disk state, then ask the user only when multiple modes are applicable.

| Mode | Determination signal | One-line behavior |
|---|---|---|
| **Initialization** | `qc-site-map.md` does not exist or is empty | Create `qc-site-map.md` and `qc-data-map.md` from `project-context-master.md` and available sources. Auto-invoke `qc-dashboard-sync` after writing site-map handoff. |
| **Update** | `qc-site-map.md` exists with real content | Run version preflight against `Sources consolidated`; refresh changed site-map/data-map content; suggest or ask to run `qc-dashboard-sync` only if site-map handoff changed. |
| **Confirm-Orphans (Mode 3)** | `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` exists with at least one data row and `qc-site-map.md` exists | Reconcile orphan UC folders from dashboard bottom-up into existing site-map aliases or new features, rewrite handoff, delete/rewrite orphan inbox, and auto-invoke `qc-dashboard-sync`. |

### Mode selection algorithm

1. Resolve paths from `path-registry.md` whenever possible.
2. Compute:
   - `siteMapExists` = resolved `qc-site-map.md` exists with non-empty content and at least one markdown header.
   - `dataMapExists` = resolved `qc-data-map.md` exists with non-empty content and at least one markdown header.
   - `orphanInboxExists` = `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` exists and parses to at least one non-empty orphan row.
3. Apply:

| siteMapExists | orphanInboxExists | Action |
|:-:|:-:|---|
| No | Any | Mode = Initialization. Orphans cannot be reconciled yet; leave the orphan inbox untouched. |
| Yes | No | Mode = Update. If `qc-data-map.md` is missing, create it as part of Update. |
| Yes | Yes | Prompt the user to pick Mode 2, Mode 3, or both. Default = Mode 3. |

Prompt in Vietnamese:

```text
📋 Phat hien 2 trang thai dong thoi:
- qc-site-map.md ton tai (mode Update kha dung)
- .claude/skills/qc-site-map/inbox/dashboard-orphans.md ton tai (<N> orphan UC tu qc-dashboard-sync bottom-up)

Ban muon chay mode nao?
1. `mode 3` (mac dinh) — Confirm orphans: reconcile <N> orphan UC voi site-map hien tai, update handoff, trigger dashboard-sync.
2. `mode 2` — Update site map/data map tu source files, KHONG dong cham toi orphans.
3. `both` — Chay mode 2 truoc roi mode 3.
```

For `both`, run the Update workflow first, suppress Update's dashboard-sync invocation, then immediately run Mode 3. Mode 3's dashboard-sync invocation fires once at the end.

---

## Hard prerequisite

`project-context-master.md` MUST exist with real content. This skill is step 2 in the top-down chain and refuses to run if step 1 has not produced its output.

If `project-context-master.md` is missing or unreadable, STOP and instruct the user in Vietnamese:

```text
Khong tim thay project-context-master.md. Hay chay /qc-context-master truoc khi chay /qc-site-map.
```

---

## Required inputs

Resolve paths from `path-registry.md` whenever possible.

Required:

- `project-config.md`
- `path-registry.md`
- `project-context-master.md`
- `templates/qc-site-map-template.vi.md`
- `templates/qc-data-map-template.vi.md`
- `references/qc-site-map-writing-guide.md`
- `references/qc-data-map-writing-guide.md`

Required in Update mode when available:

- existing `qc-site-map.md`
- existing `qc-data-map.md`
- existing `qc-dashboard.md`

Optional evidence sources:

- high-level BA files;
- official sitemap / menu / navigation documents;
- feature list / use-case list / backbone file;
- wireframe index / screen list;
- user journey / user flow documents;
- role / permission matrix;
- SRS / spec / wireframe folders for fallback derivation;
- API specs / DB schema / ERD / data dictionary;
- FRD per module;
- data classification / retention / audit policy;
- release notes / change logs / CR impact-assessment files.

Stop if `project-context-master.md` is missing. Continue as Partial if official screen/data sources are missing but enough module/feature context exists to create skeleton outputs.

---

## Core workflow

### Initialization / Update

1. Follow `workflows/workflow-0-run-control.md` to resolve paths, resume safely, determine mode, verify prerequisites, run version preflight, and audit source files.
2. Follow `workflows/workflow-1-build-site-map.md` to build or update the screen-first site-map model.
3. Follow `workflows/workflow-2-build-data-map.md` to build or update the data-entity-first data-map model.
4. Follow `workflows/workflow-3-commit-handoff-cleanup.md` to render staged outputs, compare semantic changes, commit files safely, write `site-map-handoff.md`, invoke/suggest `qc-dashboard-sync` when appropriate, and clean checkpoints.

Each workflow must write a checkpoint before moving to the next workflow.

### Confirm-Orphans Mode

When Mode 3 is selected, jump directly to `workflows/mode-3-confirm-orphans.md`.

Mode 3 does not rebuild source inventory, screen inventory, navigation, or data map. Its only job is to reconcile dashboard orphan folders against the existing `qc-site-map.md`, update folder aliases, rewrite `site-map-handoff.md`, clean the orphan inbox, and invoke `qc-dashboard-sync`.

---

## Screen-first rule for `qc-site-map.md`

Build `qc-site-map.md` from this hierarchy:

```text
System / Site / Portal
  -> Area / Module
    -> Screen / Page
      -> Sub-screen / Tab / Modal / Action
```

Then map each screen to:

- related feature/spec;
- role/access;
- navigation flow;
- data/API/integration/state touchpoints;
- regression/impact notes.

Do not start from feature-first structure. Feature list belongs to `project-context-master.md` and dashboard. `qc-site-map.md` contributes the screen/navigation layer.

---

## Data-entity-first rule for `qc-data-map.md`

Build `qc-data-map.md` from this hierarchy:

```text
Data entity
  -> relationship / dependency / cascade
  -> lifecycle / CRUD / side-effect / sync
  -> state transition when complex
  -> CRUD role permission and field-level restriction
  -> feature-entity coverage and regression impact
```

Do not turn `qc-data-map.md` into a full data dictionary. Include only fields, relationships, lifecycle details, permission rules, and touchpoints that affect QC analysis, test design, CR impact, or regression scope.

---

## Dashboard relationship

This skill is the SOLE upstream source of the feature list used by `qc-dashboard-sync` in top-down mode. The feature list flows:

```text
project-context-master.md -> qc-site-map.md -> site-map-handoff.md -> qc-dashboard-sync
```

When handing off to `qc-dashboard-sync`, aggregate by feature/use case.

Send per feature row:

- mapped screens;
- folder alias(es) — comma-separated list of folder-name IDs that map to this feature;
- `In scope?` — authoritative scope value (`Yes` / `No` / `Need confirm`);
- site-map status (`Mapped` / `Partial` / `Missing` / `Conflict` / `Need confirm`);
- site-map gaps;
- role/access/navigation issues that affect this feature;
- regression/impact notes if relevant.

Do not create one dashboard row per screen. If a screen cannot be mapped to any feature, report it as an unmapped screen in handoff notes but do not create a dashboard feature row unless QC Lead confirms it represents a real feature/spec.

`qc-data-map.md` currently has no automatic dashboard handoff. Report data-map readiness, entity gaps, and hotspot findings in the final summary only, unless `qc-dashboard-sync` has an explicit future contract for data-map handoff.

Invocation mode:

- Initialization -> auto-invoke `qc-dashboard-sync` after writing `site-map-handoff.md`.
- Update with site-map semantic change -> suggest or ask the user whether to run `qc-dashboard-sync`.
- Update with only data-map change -> no dashboard sync by default.
- Update with no semantic change -> no downstream action.
- Mode 3 -> always auto-invoke `qc-dashboard-sync` after writing updated handoff and deleting/rewriting orphan inbox.

---

## Inbox files this skill consumes

| File | Producer | Consumer | Lifecycle |
|---|---|---|---|
| `.claude/skills/qc-site-map/inbox/dashboard-orphans.md` | `qc-dashboard-sync` | This skill Mode 3 | Mode 3 deletes the file after all orphans are reconciled, or rewrites it with skipped-only rows. |

## Inbox files this skill writes

| File | Consumer | Lifecycle |
|---|---|---|
| `.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md` | `qc-dashboard-sync` | This skill is sole writer. Do not let `qc-dashboard-sync` delete it; it remains available for manual dashboard re-sync. |

---

## Stop conditions

Stop and ask the user only when:

1. `project-context-master.md` is missing or unreadable.
2. `path-registry.md` cannot resolve where to write `qc-site-map.md` or `qc-data-map.md`.
3. There is no usable project/module/feature/screen/data context at all.
4. Initialization mode cannot find or invoke `qc-dashboard-sync` after writing the required site-map handoff.
5. A required existing file path changed in a way that may overwrite user work.
6. A conflict blocks safe writing of `qc-site-map.md` or `qc-data-map.md`.
7. Version preflight returned no detected changes and the user answered `no`.

Otherwise, continue with available information, mark gaps, and report what needs confirmation.

---

## Final response

Return a concise Vietnamese summary:

- Mode: Initialization / Update / Skipped / Mode 3.
- `qc-site-map.md`: created / updated / unchanged.
- `qc-data-map.md`: created / updated / unchanged.
- Sources consolidated: count of files, count with new version since last run.
- Site-map source quality: official / derived / partial.
- Screen count and mapped feature count.
- Data-map source quality: confirmed / derived / partial.
- Entity count, relationship count, CRUD-role coverage status, and feature-entity coverage status.
- Dashboard handoff status:
  - Initialization -> `qc-dashboard-sync` auto-invoked.
  - Update with site-map change -> handoff written, user suggested/asked to run `/qc-dashboard-sync`.
  - Update with only data-map change -> no dashboard action.
  - Update no change -> handoff not written, no downstream action.
  - Mode 3 -> `qc-dashboard-sync` auto-invoked.
- Major gaps/conflicts/assumptions.
- Suggested next action for QC Lead.

Do not paste full generated files into chat unless the user asks.
