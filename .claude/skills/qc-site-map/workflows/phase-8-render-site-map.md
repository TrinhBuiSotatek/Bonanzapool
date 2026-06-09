# Phase 8 - Render Site Map

## Goal

Merge checkpoints into a fully rendered `qc-site-map.md` content **without overwriting the existing file yet**. Atomic commit happens in Phase 9 only after the content-change comparison.

## Steps

1. Read `templates/qc-site-map-template.vi.md`.
2. Read checkpoints from Phases 1-7.
3. Render a compact Vietnamese `qc-site-map.md` content in memory.
4. **Fill the `Sources consolidated` table (Section 2)** from the source list recorded by Phase 1. One row per file actually read during this run. Columns: `# | File | Version | Loại | Ngày đọc cuối`. `File` is the bare filename (no path). `Version` is `v<N>` from regex `_v(\d+)` or `no-version`. `Loại` classifies the document role. `Ngày đọc cuối` is today's date in `YYYY-MM-DD`.
5. Preserve QC Lead-reviewed content in Update mode when still valid.
6. Mark changed/deprecated/not-found items clearly instead of deleting silently.
7. **Write the rendered content to a staging file (not the real path):**

   ```text
   process-logging/qc-site-map/.staging-qc-site-map.md
   ```

   - In **Initialization mode** (`qc-site-map.md` does not exist yet at the resolved path): the staging file pattern is still followed for consistency, even though there is nothing to compare against. Phase 9 will simply move the staging file to the real path.
   - In **Update mode**: the existing `qc-site-map.md` is left untouched on disk. Phase 9 compares staging vs existing, then atomically commits or discards.
8. Do NOT touch the real `qc-site-map.md` in this phase.

## Rules

- Keep output screen-first.
- Use tables and short notes.
- Do not copy detailed specs or API schemas.
- Do not include test cases or scenarios.

## Output checkpoint

Write:

```text
process-logging/qc-site-map/08_site_map_rendered.md
```

Include:

- staging file path: `process-logging/qc-site-map/.staging-qc-site-map.md`
- staging file written: yes/no
- render summary (sections rendered, source count, screen count)
- any render warnings
- next: Phase 9 will compare staging vs existing real file and commit atomically
