# Phase 4 - Screen Inventory

## Goal

Create the screen/page inventory.

## Extract screen candidates from

1. Official sitemap/menu/navigation docs.
2. Wireframe index or screen list.
3. High-level product docs.
4. SRS/spec file names and headings.
5. Feature list from `project-context-master.md` only as skeleton fallback.

## Screen candidate fields

| Field | Description |
|---|---|
| Screen ID | Stable temporary ID such as `SCR-001`. |
| Site / Portal | Site, portal, app, or product area. |
| Area / Module | Module or business area. |
| Screen / Page | User-facing or admin-facing screen/page/modal/tab/report name. |
| Type | Page / Modal / Tab / Dashboard / Form / Report / Entry point. |
| Platform | Web / Mobile / Admin / API / TBD. |
| Source | Source file or derivation basis. |
| Status | Confirmed / Derived / Need confirm / Conflict. |

## Rules

- Do not invent screens without evidence.
- If a feature implies a screen but there is no screen evidence, add a gap instead of creating a confirmed screen.
- Use `Need confirm` for skeleton screen candidates.
- Preserve existing screen IDs in Update mode if they are still valid.

## Output checkpoint

Write:

```text
process-logging/qc-site-map/04_screen_inventory.md
```
