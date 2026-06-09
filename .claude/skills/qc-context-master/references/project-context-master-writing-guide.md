# Compact Writing Guide for `project-context-master.md`

This guide is written in English for the skill. The generated `project-context-master.md` must follow the Vietnamese template and should be written in Vietnamese by default.

Goal: generate a compact project-level context file that gives downstream QC Agents enough shared understanding to review specs, design scenarios/test cases, support execution, and verify bugs.

Do not use this file to replace detailed specs, wireframes, API docs, use case details, site maps, feature lists, or `qc-dashboard.md`.

## Core principles

Only include information in `project-context-master.md` if it helps downstream QC Agents understand one or more of these points:

1. What the project is, what type of project it is, and which release/phase it belongs to.
2. Overall scope: in scope, out of scope, dependencies, constraints.
3. Major sites, portals, apps, or modules in the system.
4. Main users, roles, and high-level permissions.
5. Major business flows or relationships between modules.
6. Common rules, data/state models, or integrations used across multiple areas.
7. Platform, environment, device/browser/OS coverage, NFRs, or important constraints.
8. Which high-level file owns which type of information.
9. What project-level context is still missing and may cause downstream Agents to review, design, execute, or verify incorrectly.

If information only applies to one specific function, screen, field, endpoint, or use case, do not include it here. Leave it for function-level/spec-level documents.

## Source rules

`High-level-files` is the primary source folder. It may contain any available project-level BA documents: site map, feature list, WBS, scope docs, Product Brief, high-level BRD/PRD, architecture, tech overview, integration overview, business rules, data model, state diagram, release notes, change logs, NFR, security, compliance, or legal docs.

Not all document types are required. If the folder is missing or empty, stop the skill.

For first-time generation, read available sources in this order:

1. `path-registry.md` and `project-config.md`.
2. `High-level-files`.
3. `requirement-common-files` if needed for feature inventory fallback or high-level confirmation.
4. Existing site map / feature list / `qc-dashboard.md` if available.
5. Change log / release note if available.

For Update mode, read the existing `project-context-master.md` first to preserve QC Lead edits and previously reviewed content. Then read current sources to update, supplement, or mark conflicts.

Detailed specs, wireframes, and API docs may be read only to confirm high-level context or derive feature inventory when official feature inventory is missing. Do not copy detailed content.

## Section writing rules

### Section 1 - How QC Agents should use this file

Briefly explain how each downstream QC Agent or skill should use this project context and which files it should read next. Recommended groups: high-level review / site map / dashboard, function-level spec review, scenario design, test case design, test execution, bug verification. Do not describe the full workflow of each skill.

### Section 2 - Project summary

Include project/product name, domain, project type, main goal, main users, current release/phase, and overall status. Keep the short summary to 3-7 lines.

### Section 3 - Overall scope and testing boundaries

Include project/release-level in-scope areas, out-of-scope or deferred areas, and important assumptions/dependencies/constraints. Do not copy the full feature list. Do not expand scope without source evidence.

### Section 4 - System structure and related high-level files

Include main sites/portals/apps, purpose, major modules, and related high-level files with their responsibilities/status. Do not duplicate the site map, feature list, or `qc-dashboard.md`. Summarize and point downstream Agents to the owning file.

### Section 5 - Users, roles, and high-level permissions

Include main roles/actors, main workflows, high-level permissions/responsibilities, and shared permission rules if any. Do not include field-level, screen-level, or function-specific permission details unless they are common rules across the project.

### Section 6 - Business flows, module relationships, and impact areas

Include major flows that cross multiple modules, dependencies between modules, and data/status/integration relationships that affect impact analysis or regression. Do not write step-by-step use case details. Do not design scenarios in this file.

### Section 7 - Common rules, data/state, and integrations

Include common rules used across multiple functions, important objects/entities/states, and high-impact integrations, APIs, jobs, notifications, reports, imports, or exports. Do not copy API schemas, endpoint lists, or field-level validations.

### Section 8 - Platform, environment, device, and constraints

Include platform type, browser/OS/device/viewport coverage, test environment, integration mode, general test data/account context, and NFR/security/privacy/compliance/legal/audit/accessibility constraints if available. Do not include real passwords, credentials, secrets, or long setup instructions.

### Section 9 - Project-level context readiness

Evaluate each context group using `Ready`, `Partial`, `Missing`, `Conflict`, or `N/A`. Use confidence `High`, `Medium`, or `Low`. Final conclusion should be short: `Du`, `Tam du`, or `Chua du` in Vietnamese output.

### Section 10 - Open questions

Ask only questions that affect project-level context or downstream QC Agent correctness. Prioritize missing/conflicting information about scope, system structure, feature inventory, roles/permissions, business flows, common rules, data/state, integrations, platform/environment, NFR/security/compliance/legal constraints, and document status.

Do not ask field-level or screen-level questions if downstream Agents can resolve them later from detailed specs.

## Missing information classification

Use these categories:

1. `QC-fillable`: QC Lead can manually provide or confirm. Continue, mark `TBD` or `Assumption`, and add an Open Question.
2. `Derivable from detailed requirement docs`: mainly feature/use case inventory from SRS/spec folder. Continue, mark as derived, and require confirmation.
3. `Needs BA/Tech Lead source`: architecture, integration, data model, state lifecycle, NFR, security, compliance, legal. Do not infer. Mark `Missing` or `Partial` and ask the owner.
4. `Blocking`: no high-level files, no writable output path, or no usable project-level context. Stop.

## Deduplication rules

Before writing the final file, check:

1. Is this information already owned by the site map?
2. Is this information already owned by the feature list or `qc-dashboard.md`?
3. Is this information only relevant to one function/screen/field/endpoint?
4. Is the same fact repeated in another section?
5. Does this information actually help QC Agents review, design, execute, or verify better?

If not, remove it or replace it with a reference to the owning file.

## Final checklist

- The output `project-context-master.md` is written in Vietnamese by default.
- The content is compact, project-level, and easy for QC Lead to review.
- Detailed specs, wireframes, and API docs are not copied.
- Site map, feature list, and `qc-dashboard.md` are not duplicated.
- Project summary, scope, and system overview are present.
- High-level roles/permissions are included if found.
- Business flows/module relationships are included if found.
- Common rules/data/state/integrations are included only if they affect multiple areas.
- Platform/environment/NFR context is included if available.
- Project-level readiness is assessed.
- Open questions exist for important TBD/conflict/assumption items.
- No detailed scenarios or test cases are written in this file.
