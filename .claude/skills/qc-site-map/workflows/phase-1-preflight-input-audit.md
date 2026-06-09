# Phase 1 - Preflight Input Audit

## Goal

Resolve paths, detect mode, and audit available inputs.

## Required checks

1. Read `path-registry.md`.
2. Resolve path for `qc-site-map.md`.
3. Resolve path for `project-context-master.md`.
4. Resolve optional paths for `qc-dashboard.md`, high-level files, SRS/spec folder, wireframe folder, and role matrix.
5. **HARD PREREQUISITE:** if `project-context-master.md` is missing or unreadable → STOP with the Vietnamese message: `Khong tim thay project-context-master.md. Hay chay /qc-context-master truoc khi chay /qc-site-map.` Do not proceed to any later phase.
6. Determine mode:
   - missing/empty `qc-site-map.md` -> Initialization;
   - existing non-empty `qc-site-map.md` -> Update.
7. For EACH file that this skill will actually read (project-context-master.md, plus every file discovered in the source folders below), extract its version via regex `_v(\d+)` on the filename (capture group 1). If no match → version = `no-version`. Record `{ file_name, version, document_group }` — this is the source list that Phase 8 will render into the `Sources consolidated` table of the output.

## Source type detection

Detect whether available sources include:

- official site map;
- menu/navigation docs;
- feature list;
- wireframe index / screen list;
- user flow / journey;
- role / permission matrix;
- SRS / spec fallback folder;
- release notes / change logs.

## Output checkpoint

Write:

```text
process-logging/qc-site-map/01_input_audit.md
```

Include:

- mode;
- resolved paths;
- source folders/files found;
- missing source groups;
- stop blockers;
- next phase.
