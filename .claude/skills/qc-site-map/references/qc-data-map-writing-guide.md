# Compact Writing Guide for `qc-data-map.md`

This guide is written in English because it is intended to be referenced by `SKILL.md`. The actual `qc-data-map.md` output must follow the Vietnamese template and should be written in Vietnamese by default.

Goal: create a data-entity-first QC map that helps downstream QC agents understand entity inventory, relationships, lifecycle, role/field permissions, feature-entity coverage, CR impact, integration risk, and regression scope.

Do not use this file to replace `project-context-master.md`, `qc-site-map.md`, specs, API docs, DB schemas, ERDs, or `qc-dashboard.md`.

---

## 1. Core principles

Only include information in `qc-data-map.md` if it helps QC agents answer at least one of these questions:

1. What important data entities exist?
2. How do entities depend on each other?
3. What creates, reads, updates, deletes, archives, locks, or syncs each entity?
4. Which role can perform which data operation?
5. Which fields require field-level permission, masking, audit, encryption, export, or cross-tenant negative tests?
6. Which features/use cases touch which entities?
7. Which entity or relationship changes create integration, system, or regression impact?
8. Which CRs add/remove/change entities, fields, lifecycle, cascade rules, or external sync?

Do not turn the output into a full data dictionary. List only QC-important fields: primary key, foreign key, sensitive fields, business-rule fields, fields used in state transitions, fields used in integration/sync, and fields changed by CRs.

---

## 2. Source hierarchy

Read `project-context-master.md` and current/staged `qc-site-map.md` first. Use them as project/screen baselines.

When sources conflict, prefer this hierarchy:

1. Signed-off DB schema / ERD / API contract / backend source-of-truth document.
2. Signed-off FRD/SRS/module spec.
3. `project-context-master.md` for scope, roles, features, flows, and constraints.
4. `qc-site-map.md` for screen/feature/touchpoint baseline.
5. Wireframes and UI docs for hints only.
6. `qc-dashboard.md` only for tracking context, not data truth.

When conflict remains, mark `Conflict` and ask QC Lead / BA / Tech Lead. Do not silently override a signed-off source.

---

## 3. Data-entity-first writing rule

Use entity-first structure:

```text
Entity
  -> relationship / dependency / cascade
  -> lifecycle operation C/R/U/D/archive/lock/sync
  -> state machine when complex
  -> CRUD role and field-level permission
  -> feature/use-case coverage
  -> CR/regression impact
```

Do not start from screens. Screens are already handled in `qc-site-map.md`. Use screen references only when identifying where entity operations are triggered or viewed.

---

## 4. Entity inventory rules

For every important entity:

- Assign a stable ID such as `ENT-USER-001`, `ENT-ORDER-001`, or project convention.
- Do not reuse an ID when an entity is removed.
- Include VN name and technical table/collection name when available.
- Include only QC-important fields, not the full schema.
- State storage location if known: database table, cache, object storage, external system, etc.
- Leave classification blank if the project has not defined the classification scheme.
- Record ownership boundary: tenant-scoped, cross-tenant, system-level, user-owned, organization-owned, or external-owned.
- Record source and confidence: Confirmed / Derived / Inferred / Need confirm / Conflict.

When a CR removes an entity, keep the old row with a note such as `Removed by CR-123 (YYYY-MM-DD)`. This prevents regression from ignoring legacy data.

---

## 5. Relationship and cascade rules

Represent relationships in both diagram and parseable table.

For each relationship, capture:

- Entity A and Entity B.
- Relationship type: 1-1, 1-n, n-n, optional.
- Dependency direction.
- Cascade rule when either side is deleted/archived/deactivated.
- Foreign key or linking field when available.
- QC note for required cascade test.

Allowed cascade values include:

- `cascade-delete`
- `cascade-soft-delete`
- `set-null`
- `set-default`
- `block`
- `archive-and-keep`
- `custom`
- `Need confirm`

When a CR changes a relationship, update Section 4 first, then Section 5 lifecycle, then Section 7 permissions, then Section 8 feature coverage.

---

## 6. Lifecycle rules

For each important entity, document operations that matter to QC:

- Create: trigger, actor, pre-condition, validation, uniqueness, side-effects, initial state.
- Read: UI/API/export channel, default scope/filter, permission, masking, audit.
- Update: immutable fields, mutable fields by role, validation, side-effects, sync, concurrency.
- Delete/Archive: type, actor, pre-condition, cascade, retention, restore, audit, external sync.
- Lock/Deactivate/State change: trigger, behavior change, reverse path, audit.

If an operation is not supported, state `Không hỗ trợ` and why. If unknown, state `Need confirm` and record a gap.

Side-effects must name the affected entity/system when possible. Examples: child entity creation, audit log, notification, external API push, TCP/device sync, cache invalidation, background job, report update.

---

## 7. State transition rules

Create state diagrams only for entities with complex lifecycle: at least three states, non-linear transitions, terminal states, or role-dependent transitions.

For each stateful entity:

- Add Mermaid `stateDiagram-v2`.
- Add valid transition table.
- Add forbidden transition table for negative test scope.
- Include trigger/UC, actor, pre-condition, and side-effect.

Do not force state diagrams for simple active/inactive entities; lifecycle section is enough.

---

## 8. CRUD role and field permission rules

Build CRUD × Role matrix at data level. This is different from `qc-site-map.md` screen-level access.

Use markers:

- `CRUD`, `CRU`, `RU`, `R`, `-`.
- `(*)` for subset-field permission.
- `(†)` for conditional ownership/scope.
- `(‡)` for subset-state permission.

Add per-field permission tables only for sensitive, restricted, masked, nullable-delete, role-specific, or compliance-relevant fields.

Always add anti-pattern negative tests for likely misuse, especially:

- cross-tenant read/write;
- unauthorized field update;
- role attempting hidden operation via API;
- delete/archive with dependent child data;
- reading/masking sensitive fields;
- export/report access to sensitive data.

---

## 9. Feature × Entity coverage rules

Build UC × Entity matrix from feature/use-case IDs. A feature/use case is the row. Entity IDs are columns. Matrix cells contain C/R/U/D operations.

Use the matrix three ways:

1. **Column/entity gap analysis**: Does each entity have Create, Read, Update, Delete/Archive coverage or an explicit reason it lacks one?
2. **Row/feature hotspot analysis**: Which feature touches many entities or performs risky Update/Delete/sync?
3. **Regression derivation**: When entity or relationship changes, trace impacted UC rows and cascade-related child entities.

Suggested hotspot rating:

- High: at least 4 entities touched, or U/D on root entity with cascade to at least 2 children, or external sync.
- Medium: 2-3 entities touched with at least one U/D.
- Low: 1 entity or read-only.

---

## 10. CR impact rules

When a Change Request affects data:

1. Update Section 3 entity inventory.
2. Update Section 4 relationships/cascade.
3. Update Section 5 lifecycle.
4. Update Section 6 state diagrams if needed.
5. Update Section 7 CRUD role/field permission.
6. Update Section 8 feature-entity coverage and hotspot analysis.

Do not accumulate every CR analysis inside the main `qc-data-map.md`. Use the appendix template to create a separate file such as `CR-123-qc-impact.md`, or add a QC-view section to the CR's own impact-assessment file.

---

## 11. Dashboard boundary

Do not write `qc-dashboard.md` directly.

Do not create a data-map handoff unless a future `qc-dashboard-sync` contract explicitly defines it. In the current skill, only `site-map-handoff.md` drives dashboard sync.

`qc-data-map.md` findings should appear in the final response as readiness/gap/hotspot summary for QC Lead.

---

## 12. Final checklist

Before finalizing, ensure:

- [ ] `qc-data-map.md` is written in Vietnamese by default.
- [ ] It is entity-first, not screen-first or feature-first.
- [ ] `project-context-master.md` and `qc-site-map.md` were used as baselines.
- [ ] Entity IDs are stable and not reused.
- [ ] Only QC-important fields are listed.
- [ ] Relationships include dependency direction and cascade rules.
- [ ] Lifecycle includes side-effects and external sync when relevant.
- [ ] State transitions include forbidden transitions where relevant.
- [ ] CRUD role matrix is data-level.
- [ ] Field-level permission is captured only when needed.
- [ ] UC × Entity matrix supports gap and hotspot analysis.
- [ ] CR impact guidance is present but CR-by-CR analysis is not accumulated in the main file.
- [ ] Data-map output does not alter dashboard-sync behavior unless explicitly supported.
