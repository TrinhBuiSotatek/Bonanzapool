# Phase 6 - Atomic Commit + Site Map Handoff

Goal: atomically commit the staged `project-context-master.md` from Phase 5, then continue the top-down chain by handing off to `qc-site-map`. Update-with-no-change exits without touching the real output and without suggesting a downstream call.

## Inputs

- Staging file: `process-logging/.staging-project-context-master.md` (from Phase 5)
- Existing real file (Update mode only): `project-context-master.md` at the path resolved from `path-registry.md`
- Resolved path of `qc-site-map.md` from `path-registry.md`

## Content comparison rule

When comparing the staging file against the existing real file, normalize both first:

1. Strip the `Ngày đọc cuối` (last column) values from every row of the `Sources consolidated` table. The date naturally changes every run and is not a semantic change.
2. Compare the normalized byte content of the two files.

`contentChanged = (normalize(staging) != normalize(existing))`

## Behavior by mode

### Initialization mode

Trigger condition: the real `project-context-master.md` did NOT exist at the resolved path before this run.

1. **Commit staging → real:** atomically rename the staging file to the resolved `project-context-master.md` path. (Fallback: copy-then-delete if rename across filesystems fails. Final state must have the real file present and staging deleted.)
2. Check whether `qc-site-map.md` exists at its resolved path.
3. If it does NOT exist → INVOKE `qc-site-map` via the Skill tool. No handoff file is needed; `qc-site-map` reads `project-context-master.md` directly.
4. If `qc-site-map.md` exists already (unusual but possible: a leftover from a previous partial run) → ALSO invoke `qc-site-map` so it runs through its own update flow and aligns with the new project context.
5. Capture the result returned by `qc-site-map` for the worklog.

### Update mode

Trigger condition: the real `project-context-master.md` existed at the resolved path before this run.

1. Run the content comparison (see "Content comparison rule" above) between staging and existing real file. Set `contentChanged = true/false`.

2. **If `contentChanged == false` (no semantic change):**
   - DELETE the staging file (no real file touched, no mtime churn).
   - Do NOT delete or rewrite the existing real `project-context-master.md` — it stays exactly as it was.
   - Do NOT invoke or suggest `qc-site-map`.
   - Record `no content change, no downstream suggestion` in the checkpoint.

3. **If `contentChanged == true` (semantic change detected):**
   - DELETE the existing real `project-context-master.md`.
   - Atomically rename the staging file to the resolved `project-context-master.md` path.
   - Append a suggestion to the final user response:

     ```text
     project-context-master.md vua duoc cap nhat. De cap nhat downstream:
     1. Chay /qc-site-map de re-generate site map theo project context moi.
     2. Sau khi qc-site-map xong, neu duoc de xuat, chay /qc-dashboard-sync.

     Ban co muon chay /qc-site-map ngay bay gio khong? [yes/no]
     ```

   - User answer `yes` → invoke `qc-site-map` immediately.
   - User answer `no` → finish without invoking. The suggestion remains in the final user summary.

## Safety rules

- If Phase 6 is interrupted between "DELETE existing real" and "rename staging → real", the staging file is still on disk and the run can be resumed from a checkpoint to retry the rename. The Phase 6 checkpoint records the state transition.
- The staging file is always cleaned up at the end of Phase 6 — either by rename (success) or by explicit delete (no-change case).
- If the staging file is missing when Phase 6 starts (e.g., resume after Phase 5 was interrupted), STOP and ask the user to re-run from Phase 5.

## Hard rules

- This phase MUST NOT write any handoff file under `.claude/skills/qc-dashboard-sync/inbox/`.
- This phase MUST NOT invoke `qc-dashboard-sync` directly.
- The only downstream skill `qc-context-master` may invoke is `qc-site-map`.

## Checkpoint

Write `process-logging/06_sitemap_handoff.md`:

```markdown
# Sitemap Handoff

- mode: initialization | update
- content changed (update mode only): yes/no
- real file committed: yes/no
- staging file cleaned up: yes/no
- qc-site-map.md path:
- qc-site-map.md existed before this phase: yes/no
- action: auto-invoked | suggested | none
- qc-site-map invocation result: <summary if invoked, else N/A>
```

Then update `progress.md`:

- `last_phase_done: 6`
- `next_phase: 7`
