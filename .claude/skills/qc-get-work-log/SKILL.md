---
name: qc-get-work-log
description: Aggregates per-device JSONL worklog files (docs/qc-lead/agent-work-log.local/worklog_*.jsonl) into the master agent-work-log.md, grouping rows into per-device tables sorted by Start time ascending. Pure append — already-ingested rows are never modified, terminal Legacy section is never touched. Trigger when the user says "tổng hợp work log", "sync work log", "rebuild agent-work-log", "/qc-get-work-log", or after pulling teammates' commits to refresh the master log.
---

# QC Get Work Log — Aggregator Skill

## Purpose

Read all per-device JSONL worklog files and rebuild the **Per-device tables** section of the master `agent-work-log.md`. The Legacy section (frozen pre-2026-05-19 data) is preserved verbatim and never modified.

This is the **sole writer** of the per-device tables in `agent-work-log.md`. No other skill should write into that section.

## Trigger Conditions

- **Manual (primary):** `/qc-get-work-log`, or natural-language phrases like "tổng hợp work log", "sync work log", "rebuild agent-work-log", "gom worklog các máy".
- **After git pull:** typically run by the QC Lead after pulling teammates' per-device JSONL commits.
- **NOT auto-triggered** by any other skill. Aggregation is a Lead-side operation.

## Input Contract

Resolve via `path-registry.md`:

- `worklog-per-device` — folder `docs/qc-lead/agent-work-log.local/`, files matching `worklog_*.jsonl`. Read all files in the folder. Each file is one device's append-log.
- `agent-work-log` — master file `docs/qc-lead/agent-work-log.md`. Used as the dedup source: rows already present in per-device tables are NEVER overwritten (pure append).

## Output Contract

- **`agent-work-log`** — rewrite only the `## Per-device tables` section. Preserve everything above it (title, intro blockquote, `## Legacy ...` section).
- **`worklog-per-device`** — read-only. Never edit, never delete. User manually deletes per-device files when desired.

## Dedup Rule (critical)

The dedup key for "is this run already in the master?" is the composite **`(device, start)`** — NOT `run_id`.

**Why not `run_id`:** users may delete their per-device JSONL file. If they restart with a fresh counter (`run-001`, `run-002` again), `run_id` collisions would falsely mark new runs as "already ingested". Time is monotonic and unique per device.

**Why `(device, start)`:** one device cannot start two runs at exactly the same second. Combined with device-as-filename, this composite is naturally unique across the team.

## Schema

### Per-device JSONL entry (input)

```json
{
  "run_id": "run-20260519-143022-chrisle3",
  "device": "DESKTOP-ABC123",
  "git_user_name": "Joy",
  "git_user_email": "chris.le3@basao.com",
  "branch": "mbfs",
  "commit": "f7d673a",
  "skill": "qc-uc-read",
  "status": "Running (Phase 2)",
  "input": ["docs/BA/UC1/UC1.md"],
  "output": [],
  "issue": null,
  "start": "2026-05-19T14:30:22+07:00",
  "end": null,
  "duration_min": null
}
```

All timestamps are ISO 8601 with offset `+07:00` (UTC+7). The skill MUST NOT convert timezones — it preserves the offset as-written.

### Per-device markdown table (output)

One section per device in `agent-work-log.md`:

```markdown
## DESKTOP-ABC123

| Member | Skill | Status | Input | Output | Issue | Start time | End time | Duration (phút) |
|--------|-------|--------|-------|--------|-------|------------|----------|-----------------|
| Joy    | qc-uc-read | Done | docs/BA/UC1/UC1.md | docs/QC/uc-read/UC1/..._v1.md | - | 2026-05-19 14:30:22 +07 | 2026-05-19 15:30:00 +07 | 60.0 |
```

Column rules:
- **Member** — `git_user_name` from JSONL entry (per-row, since one device may switch user.name over time).
- **Skill / Status** — verbatim from JSONL.
- **Input / Output** — array joined by `<br>`. Empty array → `-`. Exclude any `process-logging/` paths if present.
- **Issue** — string from JSONL, or `-` if null.
- **Start time / End time** — render the ISO 8601 string as `YYYY-MM-DD HH:MM:SS +07` (drop the `T`, replace `+07:00` with `+07`). End time empty for in-progress runs.
- **Duration (phút)** — render as-is (1 decimal). Empty for in-progress runs.

## Workflow

### Phase 1 — Bootstrap log entry

1. Detect device + git context:
   - `device` = `$env:COMPUTERNAME` (Windows) / `hostname` (Unix).
   - `git_user_name` = `git config user.name`.
   - `git_user_email` = `git config user.email`.
   - `branch` = `git rev-parse --abbrev-ref HEAD`.
   - `commit` = `git rev-parse --short HEAD`.
   - `userslug` = lowercase the part of `git_user_email` before `@`, strip non-alphanumeric.
2. Generate `run_id` = `run-<YYYYMMDD>-<HHMMSS>-<userslug>` using local time.
3. Open this device's JSONL file at `docs/qc-lead/agent-work-log.local/worklog_<device>.jsonl` (create if missing).
4. Append a new entry: `status = "Running (Phase 1)"`, `start = <now in +07:00>`, `end = null`, `skill = "qc-get-work-log"`, `input = []`, `output = []`.

> This skill follows the same per-device JSONL logging protocol as every other skill in the kit — it self-logs into its own device's file.

### Phase 2 — Parse master for existing dedup set

1. Read `agent-work-log` (master).
2. Locate the `## Per-device tables` heading. Everything **above** this line (title, intro, Legacy section) is preserved verbatim — never touched.
3. For each `## <device-name>` sub-section below it:
   - Parse the markdown table rows.
   - For each row, extract `(device, start_time_string)` and add to set `ingested`.
   - Also keep the rendered row text intact in memory (keyed by `(device, start)`) — these rows are NEVER regenerated, only carried forward to the new output. This guarantees "already-ingested rows are never modified" even if the source JSONL has since been edited or deleted.
4. Update this skill's JSONL entry: `status = "Phase 2 done"`, append master path to `input`.

### Phase 3 — Scan per-device JSONL files

1. List all files matching `worklog_*.jsonl` in `agent-work-log.local/`.
2. For each file:
   - Append file path to this skill's JSONL `input`.
   - Read line by line. Skip blank lines and malformed JSON (record as issue, do NOT abort).
   - For each valid entry:
     - Compute key `(entry.device, entry.start)`.
     - If key ∈ `ingested` → skip (already in master, including in-progress rows from earlier runs which user is expected to fix by hand if status changed).
     - Else → add to `new_rows` map: `new_rows[entry.device] += [entry]`.
3. Update this skill's JSONL entry: `status = "Phase 3 done"`.

### Phase 4 — Rebuild Per-device tables section

1. Start with the **preserved rows from master** (collected in Phase 2 §3) — these define the existing sections and rows. Group them by device.
2. Merge `new_rows` into the same map (one section per device, sorted alphabetically by device name).
3. For each device:
   - Combine existing rows + new entries.
   - Sort by `start` ascending.
   - Render each entry as a markdown table row (see column rules above).
4. Compose the full `## Per-device tables` section:
   ```markdown
   ## Per-device tables

   > Auto-generated by `qc-get-work-log`. ...

   ### DESKTOP-ABC123

   | Member | Skill | Status | ... |
   | ...    | ...   | ...    | ... |

   ### JOY-MBP

   | Member | ... |
   ```
   Use `### <device>` (h3) for each device under the `## Per-device tables` (h2).
5. Atomic write: assemble `<preserved-prefix>` + `<new Per-device tables section>` and Write to master.

### Phase 5 — Finalize log entry

1. Update this skill's JSONL entry:
   - `status = "Done"`
   - `end = <now in +07:00>`
   - `duration_min = (end - start) / 60`, rounded to 1 decimal
   - `output = ["docs/qc-lead/agent-work-log.md"]`
2. Print a chat summary:
   - N devices found, M new rows ingested, K rows skipped (already present), L malformed lines.
   - List devices and row count delta per device.

## Edge cases

| Situation                                                | Action                                                                                       |
|----------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Master `agent-work-log.md` missing `## Per-device tables` heading | Append a fresh `## Per-device tables` section below existing content. Don't fail.   |
| Master file missing entirely                             | STOP. Ask user to verify path — do not fabricate a new master from scratch.                  |
| JSONL line malformed (parse error)                       | Skip the line, log `<file>:<line-number>` to JSONL `issue` of this skill's run.              |
| JSONL entry missing required fields (`device`, `start`)  | Skip entry, log to `issue`.                                                                  |
| Two entries from same device with identical `start`      | Keep the first encountered (file order). Log to `issue`.                                     |
| Per-device JSONL file exists but is empty                | Skip silently.                                                                                |
| In-progress entry already in master, JSONL shows new status | Skip (pure append). User must hand-edit master if they want the new status reflected.     |
| `Legacy` section accidentally edited                     | Out of scope for this skill — it never touches Legacy. User-owned.                           |

## Boundaries

- **Owns**: `## Per-device tables` section of `agent-work-log.md`. Generates `worklog_<device>.jsonl` for itself (like every other skill).
- **Reads**: all `worklog_*.jsonl` files; master `agent-work-log.md`.
- **Never touches**: Legacy section, intro blockquote, other JSONL files (read-only consumer).
- **Never deletes**: per-device JSONL files. User-managed.
- **Never converts timezones**: preserves `+07:00` offset verbatim.
