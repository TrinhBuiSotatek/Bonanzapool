# Workflow 2 — Build or Update QC Data Map

## Goal

Build or update `qc-data-map.md` as the data-entity-first QC data map, using `project-context-master.md` and the current/staged `qc-site-map.md` as baselines.

This workflow produces an internal model/checkpoint only. Do not write the final `qc-data-map.md` here; Workflow 3 renders and commits.

---

## Required reads

- `project-context-master.md`
- `templates/qc-data-map-template.vi.md`
- `references/qc-data-map-writing-guide.md`
- `01_site_map_model.md` from Workflow 1, or existing `qc-site-map.md` if Workflow 1 was skipped by resume logic
- existing `qc-data-map.md` in Update mode
- `sources_to_consolidate` entries from Workflow 0 with `intended_output = data-map` or `both`

---

## Steps

### 2.1 Establish data-map baseline

Use:

- `project-context-master.md` for project/product, platform, modules, roles, features, flows, integrations, NFR/security/compliance constraints.
- `qc-site-map.md` / `01_site_map_model.md` for screens, feature-screen mapping, navigation, screen data/API/state touchpoints.
- API specs / DB schema / ERD / data dictionary for data ground truth when available.
- FRD/SRS/specs for module-level business rules and data lifecycle evidence.
- CR impact-assessment/release notes for entity/field/lifecycle deltas.

Record source quality:

- `Confirmed` from signed-off DB/API/ERD/spec.
- `Derived` from UC list/backbone/spec headings.
- `Inferred` from wireframes/screens.
- `Need confirm` when evidence is weak.
- `Conflict` when sources disagree.

### 2.2 Preserve reviewed content in Update mode

If existing `qc-data-map.md` exists, preserve when still valid:

- stable Entity IDs (`ENT-...`);
- QC Lead notes;
- confirmed classification values;
- ownership boundary;
- manually confirmed CRUD-role/field permissions;
- CR removal notes;
- gap IDs if still applicable;
- hotspot ratings if still valid.

Do not silently remove old entities. If a CR removes an entity, keep the row with `Removed by CR-XXX (YYYY-MM-DD)`.

### 2.3 Build Data Entity Inventory

Create an entity inventory at pure data-entity level, not module/screen level.

For each entity, record:

| Field | Rule |
|---|---|
| Entity ID | Stable ID such as `ENT-USER-001`, `ENT-ORDER-001`, or project convention. Do not reuse removed IDs. |
| Tên entity | Vietnamese business name and technical table/collection name when available. |
| Mô tả ngắn | 1–2 line business description. |
| Các thuộc tính chính | Only QC-important fields: PK, FK, sensitive fields, business-rule fields, state fields, sync fields. Do not copy full schema. |
| Nơi lưu trữ | DB table, collection, cache, object storage, external system, or `Need confirm`. |
| Classification | Leave blank if project classification scheme is not known; otherwise use project-specific values. |
| Ownership boundary | tenant-scoped / cross-tenant / system-level / user-owned / organization-owned / external-owned. |
| Nguồn | Confirmed / Derived / Inferred + source reference. |

### 2.4 Build Entity Relationship Map

Create both:

- Mermaid `erDiagram` overview;
- detailed relationship table.

For each relationship, record:

- Entity A;
- Entity B;
- relationship type: 1-1 / 1-n / n-n / optional;
- dependency direction;
- cascade rule when A is deleted/archived;
- cascade rule when B is deleted/archived;
- foreign key/link field;
- QC note.

Allowed cascade values:

- `cascade-delete`
- `cascade-soft-delete`
- `set-null`
- `set-default`
- `block`
- `archive-and-keep`
- `custom`
- `Need confirm`

When a relationship is derived weakly, mark it `Need confirm` instead of treating it as confirmed.

### 2.5 Build Data Lifecycle Flow per Entity

For each important entity, describe CRUD + side-effects + external sync.

Include these sections when relevant:

- Create: trigger/source, actor, pre-condition, validation, uniqueness, side-effects, initial state.
- Read: UI/API/export channel, default scope/filter, permission, masking, audit.
- Update: immutable/mutable fields, role-specific update rules, validation, side-effects, external sync, concurrency.
- Delete/Archive: hard/soft/archive/unsupported, actor, pre-condition, cascade, retention, restore, audit, external sync.
- Lock/Deactivate/State change: trigger, behavior after lock, reverse path, audit.

If an operation is unsupported, write `Không hỗ trợ — <reason>`. If unknown, write `Need confirm` and add a gap.

### 2.6 Build State Transition Diagram only when needed

Only create state diagrams for entities with:

- at least 3 states;
- non-linear transition;
- loop/reverse transition;
- terminal state;
- role-dependent transition;
- side-effect-heavy transition.

For each stateful entity, include:

- Mermaid `stateDiagram-v2`;
- valid transition table;
- forbidden transition table for negative test scope.

Do not force state diagrams for simple active/inactive entities.

### 2.7 Build CRUD × Role Matrix at data level

Build a matrix where rows are entities and columns are roles.

Use values:

- `CRUD`, `CRU`, `RU`, `R`, `-`;
- `(*)` for subset-field permission;
- `(†)` for conditional ownership/scope;
- `(‡)` for subset-state permission.

Add per-field permission tables only for entities with sensitive, restricted, masked, role-specific, compliance-relevant, nullable-delete, or CR-impacted fields.

Add anti-pattern negative tests for:

- cross-tenant access;
- unauthorized field update;
- hidden API operation;
- delete/archive with child dependencies;
- sensitive field masking;
- export/report access;
- state-dependent update/delete attempts.

### 2.8 Build Feature × Entity Coverage Matrix

Build UC/Feature × Entity matrix.

Rows: Feature/UC IDs from project context/backbone/dashboard-aligned sources.

Columns: Entity IDs from Section 3.

Cells: C/R/U/D operations; blank or `-` if not touched.

Then produce:

1. Entity-centric gap analysis:
   - Has Create?
   - Has Read?
   - Has Update?
   - Has Delete/Archive?
   - Gap/risk note.

2. Feature-centric hotspot analysis:
   - number of entities touched;
   - number of entities with Update/Delete;
   - hotspot rating High / Medium / Low;
   - reason.

Suggested hotspot rating:

- High: >=4 entities touched, or U/D root entity with cascade >=2 children, or external sync.
- Medium: 2–3 entities touched and at least one U/D.
- Low: 1 entity or read-only.

3. Map to test strategy:
   - integration test from lifecycle side-effects and external sync;
   - system test from high-hotspot features plus navigation path from `qc-site-map.md`;
   - regression scope from changed root entity -> relationship/cascade -> impacted feature rows.

### 2.9 CR impact support

Include the Change Impact Analysis appendix template in `qc-data-map.md` as a reusable reference, but do not append every CR analysis to the main file.

When a CR file is detected and already applied to current sources, reflect the delta in the main sections.

When a user asks for a CR-specific analysis, recommend or create a separate file named:

```text
CR-NNN-qc-impact.md
```

or append a QC-view section to that CR's `impact-assessment.md` if the project convention requires it.

### 2.10 Output checkpoint

Write:

```text
.claude/skills/qc-site-map/process-logging/02_data_map_model.md
```

Include:

- metadata draft;
- sources consolidated draft for data-map;
- entity inventory draft;
- relationship diagram/table draft;
- lifecycle per entity draft;
- state transition draft if any;
- CRUD role matrix draft;
- per-field permission draft if any;
- anti-pattern negative test draft;
- feature-entity coverage matrix draft;
- gap analysis;
- hotspot analysis;
- test strategy mapping;
- CR impact notes;
- data-map readiness assessment;
- changed/preserved/removed entity summary;
- next workflow.

Update `progress.md`:

```md
- last_workflow_done: 2
- next_workflow: 3
- status: Running
```
