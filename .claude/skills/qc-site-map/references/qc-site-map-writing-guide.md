# Compact Writing Guide for `qc-site-map.md`

This guide is written in English because it is intended to be referenced by `SKILL.md`.

Important: although this guide is in English, the actual `qc-site-map.md` output must follow the Vietnamese template and should be written in Vietnamese by default so the QC Lead can review and edit it easily.

Goal: create a screen-first QC site map that helps downstream QC Agents understand system structure, screens, navigation, role access, feature-to-screen mapping, and regression impact.

Do not use this file to replace `project-context-master.md`, specs, wireframes, API docs, feature lists, or `qc-dashboard.md`.

--- 

## 1. Core principles

Only include information in `qc-site-map.md` if it helps QC Agents understand one or more of the following:

1. Which site / portal / app / module exists.
2. Which screens, pages, tabs, modals, dashboards, reports, or entry points exist.
3. How users navigate between screens.
4. Which roles can access which screens or actions.
5. Which feature/spec each screen supports.
6. Which data, API, integration, state, or common rule touches each screen or flow.
7. Which screens are important regression or impact anchors.
8. Which screen-level context is missing, unclear, derived, or conflicting.

If information belongs only to detailed spec behavior, validation fields, API schema, scenario steps, or test cases, do not include it here.

---

## 2. Source hierarchy

Read `project-context-master.md` first and use it as the baseline for project scope, modules, features, roles, flows, platform, integration, and constraints.

When sources conflict, prefer this hierarchy:

1. Approved BA sitemap / wireframe index / navigation docs.
2. `project-context-master.md` for project-level baseline.
3. High-level BRD / PRD / product docs.
4. Detailed SRS / spec / wireframe docs for evidence.
5. `qc-dashboard.md` only for workflow status and existing tracking, not source truth.

Do not use dashboard rows to override site-map structure unless supported by source evidence or QC Lead confirmation.

---

## 3. Screen-first writing rule

Use screen-first structure:

```text
System / Site / Portal
  -> Area / Module
    -> Screen / Page
      -> Sub-screen / Tab / Modal / Action
```

Then map screens back to features, roles, flows, data, integrations, and regression anchors.

Do not make the output feature-first. Feature list is owned by project context and dashboard. Site map contributes screen/navigation structure.

---

## 4. Derivation rules

When official sitemap or screen list is missing, derive cautiously from:

- module names in `project-context-master.md`;
- feature list/use case list;
- SRS/spec file names and headings;
- wireframe file names;
- user flow documents;
- menu/navigation references in source docs.

Mark derived items clearly:

- `Confirmed`: directly supported by official source.
- `Derived`: inferred from detailed source names/headings or consistent evidence.
- `Need confirm`: plausible but not sufficiently supported.
- `Conflict`: source disagreement.

Do not invent screens without evidence.

---

## 5. Section rules

### Section 1 - Metadata

State mode, readiness, source quality, baseline, and dashboard relationship.

### Section 2 - Source baseline

List only sources actually used. Include confidence and purpose.

### Section 3 - Site / Portal / App overview

Summarize high-level sites or apps. Do not list all screens here.

### Section 4 - Screen-first tree

Show the screen hierarchy as a concise text tree. Use stable labels. Mark unknown branches as `TBD` or `Need confirm`.

### Section 5 - Screen inventory

List screens/pages/modals/tabs/reports/dashboards. Use stable temporary screen IDs such as `SCR-001`. Do not create official product IDs.

### Section 6 - Navigation and screen flow

Capture important screen paths and cross-module flows. Do not write detailed scenario steps.

### Section 7 - Role/access by screen

Capture high-level access and action rights by role. Do not include field-level permission unless it is a common screen-level rule.

### Section 8 - Screen-feature mapping

Every screen with Confirmed/Derived status MUST be mapped to a Feature/UC ID. If not mappable, mark screen as Need confirm and list under unmapped — never fall back to module-level mapping.
Add feature-level/use-case-level coverage summary for dashboard handoff.

### Section 9 - Data/API/integration/state touchpoints

Only include touchpoints that affect screen behavior, integration testing, state transitions, or regression risk.

### Section 10 - Regression/impact anchors

Identify shared screens, core flows, common components, permission screens, integration screens, and data-state screens that should influence regression selection.

### Section 11 - Gaps/conflicts/assumptions

Include only issues that affect QC usefulness of the site map.

### Section 12 - Readiness

Assess whether the site map is usable by downstream QC Agents. Use `Ready`, `Partial`, or `Blocked`.

---

## 6. Dashboard handoff rules

`qc-dashboard.md` tracks feature/use-case, spec workflow status, not screen-level rows.

When handing off to `qc-dashboard-sync`, aggregate by feature/use case:

- Feature ID or use case ID and name.
- Mapped screens.
- Site map status: `Mapped`, `Partial`, `Missing`, `Conflict`, `Need confirm`.
- Role/access/navigation gaps affecting the feature.
- Regression/impact notes.

If a screen cannot be mapped to a feature, report it as an unmapped screen in handoff notes. Do not create a dashboard feature row unless QC Lead confirms that the screen represents a real feature/spec.

---

## 7. Missing, assumption, and conflict handling

### Missing

If important screen/navigation/access/mapping information is missing:

- write `TBD`;
- mark readiness as `Partial` or `Blocked`;
- add an issue in Section 11.

### Assumption

If the Agent must infer something:

- mark it as `Assumption`;
- explain the impact if it is wrong;
- add a confirmation issue if it affects navigation, access, feature mapping, or regression.

### Conflict

If sources conflict:

- do not silently choose one;
- mark the item as `Conflict`;
- summarize the conflict;
- explain the QC impact;
- add an issue for QC Lead / BA / Tech Lead.

---

## 8. Final checklist

Before finalizing, ensure:

- [ ] `qc-site-map.md` is written in Vietnamese by default.
- [ ] The output is screen-first.
- [ ] `project-context-master.md` was read first as baseline.
- [ ] Detailed specs, wireframes, and API docs are not copied.
- [ ] Dashboard rows are not created per screen.
- [ ] Screen inventory has source and status.
- [ ] Screen-feature mapping is included.
- [ ] Role/access by screen is included if found.
- [ ] Navigation flow is included if found.
- [ ] Regression/impact anchors are included.
- [ ] Gaps/conflicts/assumptions are explicit.
- [ ] Dashboard handoff is aggregated by feature or use case, not module or screen.
