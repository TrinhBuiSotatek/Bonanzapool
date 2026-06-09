# Phase 7 + 8 — Finalize & Handover

> **Invoked by:** `SKILL.md` after Phase 6 (Extract + Interview) completes.
>
> **Prerequisites loaded into memory:** the most recent post-interview draft from `process-logging/` (per `checkpoint-protocol.md` §3 Resume load table).
>
> **Deliverable (user-visible):** `project-context-master.md` written at the path resolved via `path-registry` → `project-context-master`.
>
> **Worklog Status transitions:** `Running (Phase 7)` → `Phase 7 done` → `Running (Phase 8)` → `Done`.
>
> **End-of-skill cleanup:** delete `process-logging/` folder after successful Phase 8 (per `checkpoint-protocol.md` §5).

---

## Phase 7 — Write project-context-master.md

### Step 0 — Worklog: enter phase

Update agent-work-log row: `Status = Running (Phase 7)`.

### Step 1 — Render final document

Compose the final markdown from the in-memory draft (latest checkpoint loaded). Render rules:

1. Use `templates/project-context-template.md` as the structural skeleton. Keep template headers in English; section bodies follow `global-rules.md` output-language rule.
2. Section 10 Open Questions table format: `| ID | Question | Impact | Owner | Status |`. Status ∈ {`Open`, `Resolved`}. IDs continue sequence from `04_carryover.md` — do NOT renumber resolved questions.
3. Preserve original-language labels for non-Vietnamese/English sources with English annotations in parentheses (per `global-rules.md`).
4. Persist the `_[AI-proposed | confidence: NN% | evidence: ...]_` tag verbatim at the end of any section that the user did **not** confirm (skipped or partially answered). Sections that were `accept`-ed, `modify`-ed, supplemented, or fully answered in Q&A MUST NOT carry the tag.

### Step 2 — Write to disk

Write the rendered content to the `project-context-master` path. Overwrite if exists.

### Step 3 — Checkpoint write

1. Update `process-logging/progress.md` → `last_phase_done: 7`, `next_phase: 8`.
2. Update agent-work-log row: `Status = Phase 7 done`. Append `project-context-master.md` to Output column if not already present.

---

## Phase 8 — Handover

### Step 0 — Worklog: enter phase

Update agent-work-log row: `Status = Running (Phase 8)`.

### Step 1 — Compose handover message

Compute summary statistics from the just-written `project-context-master.md` and the `05_deltas.md` checkpoint:

- Sections filled: count §1–§10 that have non-empty bodies.
- User-confirmed: count sections without `[AI-proposed]` tag.
- Still tagged: list of §<N> still bearing `[AI-proposed]`.
- Open / Resolved Question counts in §10.
- Dashboard deltas: new / soft-deleted / re-added counts from `05_deltas.md`.
- Site abbreviations: current list.

Output:

```
✅ **Tổng hợp tri thức dự án hoàn tất.**

**Tóm tắt:**
- `project-context-master.md`: <created / updated> — sections filled: <count>/10 | user-confirmed: <N>/10 | còn tag `[AI-proposed]`: <N> (§<list>) | open questions: <open count> open / <resolved count> resolved
- `qc-dashboard.md`: <created / updated> — +<N> rows mới | soft-delete (→ Removed): <N> | re-add (→ Yes): <N>
- Site abbreviations: <list>

➡️ **Bước tiếp theo gợi ý:** chạy `/qc-dashboard-sync` để đồng bộ trạng thái tài liệu, hoặc `/qc-uc-read` để review use case đầu tiên.
```

### Step 2 — Final worklog update

1. Compute `Duration` = now − started_at, rounded to 1 decimal place (minutes).
2. Update agent-work-log row:
   - `Status = Done`
   - `Duration` = computed value
   - Confirm `Input` contains all common files read (excluding `process-logging/`).
   - Confirm `Output` contains `project-context-master.md` and `qc-dashboard.md` (excluding `process-logging/`).
   - `Issue` = `-` if none, else list of any issues encountered during the run (using `<br>` between items).

### Step 3 — Cleanup checkpoint folder

**Only after Step 2 succeeds**, delete the entire `process-logging/` folder. This is the final action of the skill.

If the cleanup fails (e.g., file lock), log it as an Issue in the worklog row but do NOT mark the skill as failed — the deliverables are already on disk and the worklog already says `Done`.
