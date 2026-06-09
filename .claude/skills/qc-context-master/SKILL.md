---
name: qc-context-master
description: generates and updates compact project-level qc context for agentic qc workflows. Step 1 of the top-down chain qc-context-master -> qc-site-map -> qc-dashboard-sync. Use when the user asks to initialize or update project context, summarize high-level ba documents, or prepare shared project understanding for qc agents. Supports initialization when project-context-master.md does not exist and update when it exists. Produces project-context-master.md only. In Initialization mode auto-invokes qc-site-map after writing. In Update mode suggests the user to run qc-site-map only if changes are detected.
---
# QC Context Master

## Purpose

Generate and maintain `project-context-master.md` as the compact project-level context layer for the QC Agentic workflow.

This context helps downstream QC Agents understand the whole project before they read detailed function-level documents. It supports high-level BA document review, site map / feature list / dashboard alignment, function-level spec review, scenario design at function / integration / regression levels, test case design, test execution support, and bug verification.

`project-context-master.md` must not replace detailed source documents such as specs, wireframes, API docs, use case details, or technical documents from BA / BE / Tech Lead. It should summarize only project-level context needed to orient downstream QC Agents.

The generated `project-context-master.md` follows the Vietnamese template and should be written in Vietnamese by default so the QC Lead can review and edit it easily.

## Modes

Determine mode from the resolved `project-context-master` path in `path-registry.md`.

| Mode           | Condition                                                | Behavior                                                                                                                                      |
| -------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Initialization | `project-context-master.md` does not exist or is empty   | Create new project-level context. After writing, auto-invoke `qc-site-map` to continue the chain.                                             |
| Update         | `project-context-master.md` exists with real content     | Run version preflight against the existing `Sources consolidated` table. Preserve QC Lead-reviewed content, re-read current inputs, update changed context, report gaps/conflicts. If output content changes, suggest the user to run `qc-site-map` next. |

In Update mode, always read the existing `project-context-master.md` before extracting from new inputs.

## Version preflight (Update mode only)

Before re-running the full pipeline, parse the `Sources consolidated` table from the existing `project-context-master.md`. For each source, scan its parent folder for the latest version (`_v<N>` suffix in filename) and compare with the recorded version.

- If at least one source has a new version, a new file, or a deleted file -> proceed with the full pipeline.
- If no version change is detected on any source, ask the user:

```text
Khong phat hien version moi cua cac source files da consolidated lan truoc:
- <file 1>: v<N> (khong doi)
- <file 2>: v<N> (khong doi)
...

Luu y: co che nay chi detect version qua ten file (regex _v<N>).
Neu ban da sua content ma khong tang version, hay tra loi yes de chay lai.

Ban co muon chay lai khong? [yes/no]
```

- User answers `no` -> exit early without changes, log the skip in the worklog.
- User answers `yes` -> continue with the full pipeline.

## Inputs

Resolve paths from `path-registry.md` whenever possible.

Required or expected inputs:

- `High-level-files` folder from BA.
- `requirement-common-files` folder from BA.
- `project-config.md`.
- `path-registry.md`.
- Existing `project-context-master.md` in Update mode.
- `templates/project-context-master-template.vi.md`.
- `references/project-context-master-writing-guide.md`.

This skill does NOT need to read `qc-dashboard.md` — the dashboard is owned by `qc-dashboard-sync` and reached only via `qc-site-map` downstream.

`High-level-files` may contain any available project-level BA documents such as site map, feature list, WBS, project plan, scope document, Product Brief, high-level BRD/PRD, system architecture, tech overview, integration overview, business rules, data model, state diagrams, release notes, change logs, NFR, security, compliance, or legal documents. Not all document types are required. If this folder is missing or empty, stop the skill.

## Outputs

This skill produces:

1. `project-context-master.md` directly. Must include the `Sources consolidated` table in the header listing every source file that was read and used during generation, with detected version.
2. In Initialization mode: auto-invokes `qc-site-map` after writing the output. No handoff file is written.
3. In Update mode: when output content changes, suggests the user to run `qc-site-map` next. No auto-invoke.

This skill MUST NOT write `qc-dashboard.md` directly and MUST NOT write any handoff file for `qc-dashboard-sync`. Feature list flows to dashboard via `qc-site-map` only.

## Workflow overview

Follow these workflow files in order. Each workflow must write its checkpoint before moving to the next workflow.

1. `workflows/phase-0-audit-resume.md` — also runs the version preflight in Update mode.
2. `workflows/phase-1-preflight-input-audit.md` — records each source with its detected version into the source inventory.
3. `workflows/phase-2-feature-inventory.md`
4. `workflows/phase-3-project-context-extract.md`
5. `workflows/phase-4-gap-readiness.md`
6. `workflows/phase-5-render-context.md` — writes the `Sources consolidated` table into the output header.
7. `workflows/phase-6-sitemap-handoff.md` — Initialization: auto-invoke `qc-site-map`. Update: suggest the user to run `qc-site-map` when output changed.
8. `workflows/phase-7-handover-cleanup.md` — on success, deletes the entire `process-logging/` folder.

Also read `workflows/checkpoint-protocol.md` at skill start.

## Required reading before extraction

Before drafting project context, read:

- `templates/project-context-master-template.vi.md`
- `references/project-context-master-writing-guide.md`

Use the template as the output structure. Use the writing guide as the operational rule set for source selection, section writing, deduplication, missing information, assumptions, and conflict handling.

## Missing high-level information policy

When high-level information is incomplete, classify the gap:

1. `QC-fillable`: QC Lead can manually provide or confirm it. Continue, mark `TBD` or `Assumption`, and add an Open Question.
2. `Derivable from detailed requirement docs`: mainly feature/use case inventory can be inferred from SRS/spec folders. Continue, mark source as derived, and require QC Lead confirmation.
3. `Needs BA/Tech Lead source`: architecture, integration behavior, data model, state lifecycle, NFR, security, compliance, or legal constraints. Do not infer or invent. Mark `Missing` or `Partial` and ask the owner.
4. `Blocking`: no high-level files, no writable output path, or no usable project-level context. Stop.

## Feature inventory fallback

Feature/use case inventory is critical for downstream skills: `qc-site-map` (to map screens to features) and indirectly `qc-dashboard.md` (rows are sourced from `qc-site-map` aggregation), plus impact analysis and regression support.

Extract feature candidates in this order:

1. Explicit feature list / WBS / scope table from `High-level-files`.
2. Site map or module list from `High-level-files`.
3. `requirement-common-files` or SRS/spec folder by scanning file names, folder names, headings, UC IDs, feature IDs, or story IDs.

If derived from detailed docs:

- Mark source as `derived from requirement-common-files`.
- Do not treat derived items as official until confirmed.
- Use temporary IDs such as `TMP-001` only when no official ID exists.
- Mark temporary IDs as `Need confirm`.

If no feature candidates can be extracted, write `project-context-master.md` with a clear gap. `qc-site-map` (downstream) will still run on whatever screen evidence is available but will not be able to map screens to features.

## Stop conditions

Stop and ask the user only when:

1. `High-level-files` folder is missing or empty.
2. `path-registry.md` cannot resolve where to write `project-context-master.md`.
3. No usable project-level information can be extracted from any source.
4. In Initialization mode, `qc-site-map` cannot be found or invoked.
5. A required existing file path changed in a way that may overwrite user work.
6. A conflict blocks safe writing of `project-context-master.md`.
7. Version preflight returned no detected changes and the user answered `no`.

Otherwise, continue with available information, mark gaps, and report what needs confirmation.

## Final response

At completion, respond in Vietnamese with:

- Mode: Initialization or Update (or `Skipped` when version preflight returned no change and user declined).
- `project-context-master.md`: created or updated.
- Sources consolidated: count of files read, count of files with new version since last run.
- Feature candidates summary: new, derived, need confirmation, not found in current source.
- Highest-impact missing context.
- Next-step status:
  - Initialization -> `qc-site-map` auto-invoked.
  - Update with changes -> suggest the user to run `qc-site-map` next.
  - Update with no content change -> no downstream action suggested.
- Suggested next action for QC Lead.

Do not paste the full generated file into chat unless the user asks.
