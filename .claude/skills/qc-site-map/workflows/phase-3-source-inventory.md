# Phase 3 - Source Inventory

## Goal

Read available sitemap-related sources and classify their confidence.

## Source classification

Use:

- `Official` for approved BA sitemap/navigation/wireframe index.
- `BA-provided` for high-level BA docs not clearly approved.
- `Derived from SRS/spec` for screens inferred from detailed requirement files.
- `Derived from project context` for skeleton items based on modules/features only.
- `Need confirm` for plausible but weakly supported items.

## Rules

- Prefer official sitemap/wireframe/navigation sources for screen structure.
- Use SRS/spec fallback only when official source is missing or incomplete.
- Do not use `qc-dashboard.md` as source truth. Use it only for existing workflow status and tracking context.

## Output checkpoint

Write:

```text
process-logging/qc-site-map/03_source_inventory.md
```

Include source list, source type, confidence, and what each source contributes.
