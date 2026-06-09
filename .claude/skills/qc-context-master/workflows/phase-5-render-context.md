# Phase 5 - Render and Write Project Context

Goal: merge section checkpoints and write `project-context-master.md`.

## Inputs

- `templates/project-context-master-template.vi.md`
- all `03_context_section_*.md`
- `04_gap_readiness.md`
- existing `project-context-master.md` in Update mode

## Render rules

1. Use the Vietnamese template as the structure.
2. Keep section headers from the template.
3. Write body content in Vietnamese by default.
4. **Render the `Sources consolidated` table** at the top of the output, filling it from the `Documents found` table in `01_input_audit.md`. One row per file actually read during this run. Columns: `# | File | Version | Loại | Ngày đọc cuối`. `File` is the bare filename (no path). `Version` is `v<N>` from regex `_v(\d+)` or `no-version`. `Loại` is the document group classified in Phase 1. `Ngày đọc cuối` is today's date in `YYYY-MM-DD`.
5. Merge Sections 1-8 from section checkpoints.
6. Merge Section 9 and Section 10 from `04_gap_readiness.md`.
7. In Update mode, preserve QC Lead-reviewed content when still valid.
8. Clearly mark `TBD`, `Assumption`, and `Conflict`.
9. Do not include detailed scenarios, test cases, endpoint schemas, field validations, or long source excerpts.

## Write rules — staging file pattern (atomic commit)

This phase renders the file but does NOT touch the real `project-context-master.md` yet. Atomic commit happens in Phase 6 after the content-change comparison.

1. Resolve the output path through `path-registry.md` logical name `project-context-master`. If the path cannot be resolved, stop and ask the user.
2. **Write the rendered content to a staging file (not the real path):**

   ```text
   process-logging/.staging-project-context-master.md
   ```

   - In **Initialization mode** (`project-context-master.md` does not exist yet at the resolved path): the staging file pattern is still followed for consistency. Phase 6 will simply move the staging file to the real path.
   - In **Update mode**: the existing `project-context-master.md` is left untouched on disk. Phase 6 compares staging vs existing, then atomically commits or discards.
3. Do NOT touch the real `project-context-master.md` in this phase.

## Checkpoint

Write `process-logging/05_context_rendered.md`:

```markdown
# Context Rendered

- staging file path: process-logging/.staging-project-context-master.md
- staging written: yes/no
- target output path: <resolved project-context-master.md path>
- mode:
- sections rendered:
- unresolved TBD count:
- assumptions count:
- conflicts count:
- open questions count:
- next: Phase 6 will compare staging vs existing real file and commit atomically

## Final rendered content
<copy of rendered markdown or path to staging file>
```

Then update `progress.md`:

- `last_phase_done: 5`
- `next_phase: 6`
