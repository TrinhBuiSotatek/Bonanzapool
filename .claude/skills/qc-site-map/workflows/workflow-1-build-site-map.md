# Workflow 1 — Build or Update QC Site Map

## Goal

Build the screen-first `qc-site-map.md` working model from project context and screen/navigation sources.

This workflow consolidates the old Phases 2–7. It produces an internal model/checkpoint only. Do not write the final `qc-site-map.md` here; Workflow 3 renders and commits.

---

## Required reads

- `project-context-master.md`
- `templates/qc-site-map-template.vi.md`
- `references/qc-site-map-writing-guide.md`
- existing `qc-site-map.md` in Update mode
- `sources_to_consolidate` entries from Workflow 0 with `intended_output = site-map` or `both`

---

## Steps

### 1.1 Read project context baseline

Extract only baseline facts needed for screen/navigation/access/mapping work:

- project/product name;
- platform type;
- sites / portals / apps;
- modules / areas;
- feature/use-case list or feature candidates;
- roles / actors;
- major business flows;
- data objects / states;
- integrations / APIs / jobs / reports / notifications;
- NFR/security/compliance constraints that affect screens or access;
- existing gaps/open questions relevant to site map.

Do not rewrite project context. Do not copy long sections. Mark unclear baseline items as `Need confirm`.

### 1.2 Preserve reviewed content in Update mode

If existing `qc-site-map.md` exists, parse and preserve when still valid:

- stable `SCR-xxx` screen IDs;
- QC Lead notes and reviewed assumptions;
- existing `Folder alias(es)` values;
- `Folder alias map` section;
- manually confirmed `In scope?` values;
- manually confirmed screen-feature mappings;
- gap IDs if still applicable.

Mark deprecated, changed, or not-found items clearly. Do not silently delete reviewed content.

### 1.3 Classify source confidence

Use:

- `Official` for approved BA sitemap/navigation/wireframe index.
- `BA-provided` for high-level BA docs not clearly approved.
- `Derived from SRS/spec` for screens inferred from detailed requirement files.
- `Derived from project context` for skeleton items based on modules/features only.
- `Need confirm` for plausible but weakly supported items.
- `Conflict` when sources disagree.

Prefer official sitemap/wireframe/navigation sources for screen structure. Use SRS/spec fallback only when official source is missing or incomplete. Do not use `qc-dashboard.md` as source truth.

### 1.4 Build screen inventory

Extract screen candidates from:

1. Official sitemap/menu/navigation docs.
2. Wireframe index or screen list.
3. High-level product docs.
4. SRS/spec file names and headings.
5. Feature list from `project-context-master.md` only as skeleton fallback.

For each screen candidate, record:

| Field | Description |
|---|---|
| Screen ID | Stable temporary ID such as `SCR-001`. Preserve existing IDs in Update mode. |
| Site / Portal | Site, portal, app, or product area. |
| Area / Module | Module or business area. |
| Screen / Page | User-facing or admin-facing screen/page/modal/tab/report name. |
| Type | Page / Modal / Tab / Dashboard / Form / Report / Entry point. |
| Platform | Web / Mobile / Admin / API / TBD. |
| Source | Source file or derivation basis. |
| Status | Confirmed / Derived / Need confirm / Conflict. |

Rules:

- Do not invent screens without evidence.
- If a feature implies a screen but there is no screen evidence, add a gap instead of creating a confirmed screen.
- Use `Need confirm` for skeleton screen candidates.
- Preserve existing screen IDs in Update mode if they remain valid.

### 1.5 Build screen-first tree and navigation flows

Build:

1. Site / Portal / App tree.
2. Area / Module branches.
3. Screen / Page nodes.
4. Sub-screen / Tab / Modal / Action nodes if known.
5. Important user flows and cross-module navigation.

Rules:

- Keep the tree concise and screen-first.
- Do not write scenario/test-case steps.
- Do not design new UX or navigation.
- Mark missing navigation as `TBD` or `Need confirm`.

### 1.6 Map screens to features and access

Map each screen to related feature/use-case/spec when possible.

Smallest mapping unit is Feature/UC. Module is grouping context only and never a mapping target.

For every screen, identify:

- primary feature/use case;
- supporting/shared features if applicable;
- role/access by screen/action;
- data/API/integration/state touchpoints;
- regression/impact anchor flag;
- unmapped reason if no feature mapping exists.

Do not create dashboard rows per screen or module. Do not create Feature IDs/UC IDs unless confirmed by project source. Use existing feature/use-case IDs from project context or source docs. If screen cannot map to a feature, list it under unmapped screens.

### 1.7 Build feature-level dashboard coverage

Aggregate by feature/use case:

| Feature ID | Feature name | Site / Portal | Module | Mapped screens | Folder alias(es) | In scope? | Site map status | Gap / Note |
|---|---|---|---|---|---|---|---|---|

Rules:

- Preserve `Folder alias(es)` from previous site-map or Mode 3.
- Preserve user-confirmed `In scope?` where available.
- Default `In scope? = Yes` for `Mapped` / `Partial` when the feature is clearly in scope.
- Use `Need confirm` for `Missing`, `Conflict`, unclear scope, or new unconfirmed features.
- If feature has no screen mapping, mark `Missing` or `Partial`.

### 1.8 Identify gaps, conflicts, assumptions, and readiness

Gap types:

- `Missing`: expected screen/navigation/access/mapping source not found.
- `Conflict`: sources disagree.
- `Assumption`: inferred item needs confirmation.
- `Unclear`: source exists but is ambiguous.

Assess readiness areas:

- screen inventory;
- navigation flow;
- role/access by screen;
- screen-feature mapping;
- data/API/integration/state touchpoints;
- regression/impact usage;
- dashboard feature-level handoff;
- data-map baseline usability.

Status values:

- `Ready`
- `Partial`
- `Blocked`
- `N/A` when applicable.

### 1.9 Output checkpoint

Write:

```text
.claude/skills/qc-site-map/process-logging/01_site_map_model.md
```

Include:

- baseline summary;
- source classification;
- screen inventory draft;
- screen-first tree draft;
- navigation flow draft;
- role/access draft;
- screen-feature mapping draft;
- feature-level dashboard coverage draft;
- data/API/integration/state touchpoint summary;
- regression/impact anchors;
- gaps/conflicts/assumptions;
- readiness assessment;
- preserved alias/scope/reviewed-content summary;
- next workflow.

Update `progress.md`:

```md
- last_workflow_done: 1
- next_workflow: 2
- status: Running
```
