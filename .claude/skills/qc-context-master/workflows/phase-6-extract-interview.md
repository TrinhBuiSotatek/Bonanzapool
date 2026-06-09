# Phase 6 — Extract, Propose, and Interview

> **Invoked by:** `SKILL.md` after Phase 5 (Dashboard sync) completes.
>
> **Heaviest phase in the skill** — reads all common files, drafts 10 sections, and runs 3 interactive interview passes. Most likely place for context-limit interruption. Per-section checkpointing is mandatory.
>
> **Prerequisites loaded into memory:** `04_carryover.md`, `05_deltas.md`, all path-registry resolutions.
>
> **Checkpoints produced:**
> - `06_1_draft.md` (after extraction)
> - `06_3a_after_passA.md` (after Pass A)
> - `06_3b_passB_§<N>.md` (after EACH section in Pass B)
> - `06_3c_passC_§<N>.md` (after EACH section in Pass C)
>
> **Worklog Status transitions:**
> `Running (Phase 6.1)` → `Phase 6.1 done` → `Running (Phase 6.3.A)` → `Phase 6.3.A done` → `Running (Phase 6.3.B §<N>)` → `Phase 6.3.B done` → `Running (Phase 6.3.C §<N>)` → `Phase 6.3.C done`.

---

## Phase 6.1 — Extract, draft, score confidence

> **All-or-nothing step.** Phase 6.1 must run to completion in one shot — sections cross-reference each other during confidence scoring. Cannot be checkpointed mid-flight.

### Step 0 — Worklog: enter phase

Update agent-work-log row: `Status = Running (Phase 6.1)`. Add common files read to Input column.

### Step 1 — Extraction priority per section

For each section, follow this priority: `High-level-files` → `requirement-common-files` → `project-config.md` → ask user (defer to interview passes).

| § | Section | Primary source | Required? |
|---|---|---|---|
| 1 | Project Identity (project name, ID, product name, release version, project type, domain) | project-config.md §1 + common files | ✅ |
| 2 | Business Goal (goal, problem/pain point, success criteria) | Product Brief, WBS | ✅ |
| 3 | Scope Summary (in scope, out of scope, assumptions, dependencies) | WBS, Product Brief, common rules | ✅ |
| 4 | Users and Roles (table: role, description, permissions, workflows) | Architecture, common files, project-config.md §5 | ✅ |
| 5 | System Overview (architecture summary; embed Sites table from mapping; link to qc-dashboard) | Architecture, Tech Stack | ✅ |
| 6 | Requirement Sources (table: PRD/BRD, wireframe, API spec, business rules, change log) | path-registry.md + ask user | ✅ |
| 7 | Quality Context (critical flows, high-risk areas, NFR notes, known constraints) | common files | ✅ |
| 8 | Environment Context (platform coverage, test environments) | project-config.md §4 + common files | ✅ |
| 9 | QC Process Notes (test levels, entry/exit criteria, defect workflow, reporting) | common files | ✅ |
| 10 | Open Questions | populated dynamically from gaps in §1–§9 + carry-over from `04_carryover.md` | — |

For Section 5 specifically:
- Embed the `Sites` sub-table from the site-abbreviations mapping (`Full name | Abbreviation`).
- End with a line linking to the qc-dashboard file using the resolved path.

### Step 2 — Confidence scoring per section

After drafting each §1–§9:

1. Score `confidence` based on coverage of required sub-items:
   - **High (≥70%)** — most sub-items backed by explicit source references.
   - **Medium (40–69%)** — partial source coverage; some sub-items inferred from context.
   - **Low (1–39%)** — mostly inferred from indirect signals; minimal source backing.
   - **Empty (0%)** — no source data found.
2. Collect `evidence`: list of `<file> §<section/line>` references that back the draft. Empty sections have no evidence.
3. Append the tag at the END of the section's content (before the next `##` header):
   ```
   _[AI-proposed | confidence: NN% | evidence: <file §x.y>, <file §a.b>]_
   ```
   Empty sections use `evidence: —`.

This tag is the source of truth for which sections go into which interview pass and which remain pending review.

### Step 3 — Checkpoint write

1. Write `process-logging/06_1_draft.md` containing the full 10-section draft (with confidence tags).
2. Update `process-logging/progress.md` → `last_phase_done: 6.1`, `next_phase: 6.3.A`.
3. Update agent-work-log row: `Status = Phase 6.1 done`.

Proceed to Phase 6.3.

---

## Phase 6.3 — Multi-pass interview

Run THREE passes in order. Each pass MUST offer a `skip` option; skipping never blocks the skill.

Section 10 (Open Questions) is **populated as a byproduct** of the passes (high-level gaps recorded there). Do NOT interview §10 directly.

### Pass A — High-confidence review (sections with confidence ≥70%)

#### Step A.0 — Worklog

Update Status → `Running (Phase 6.3.A)`.

#### Step A.1 — Show consolidated table

```
**Pass A — Đề xuất confidence cao (xác nhận nhanh):**

| § | Section | Tóm tắt đề xuất (1 dòng) | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Project Identity | <summary> | 90% | project-config §1; Product Brief §2 |
| 5 | System Overview | <summary> | 85% | Architecture diagram §3; Tech Stack §2 |

👉 Trả lời:
- `accept all` — chấp nhận toàn bộ.
- `modify §<N>: <nội dung sửa>` — sửa từng mục (lặp lại cho nhiều mục).
- `skip §<N>` — bỏ qua mục đó (giữ tag `[AI-proposed]`; đẩy high-level question vào §10).
- `skip all` — bỏ qua toàn bộ pass.
```

#### Step A.2 — Apply user response

Merge user feedback into the in-memory draft per the **Tag lifecycle** table (below).

#### Step A.3 — Checkpoint write

1. Write `process-logging/06_3a_after_passA.md` containing the post-Pass-A draft.
2. Update `progress.md` → `last_phase_done: 6.3.A`, `next_phase: 6.3.B`.
3. Update agent-work-log row: `Status = Phase 6.3.A done`.

### Pass B — Medium + Low confidence refinement (sections 1–69%)

Iterate per affected section. **Each section gets its own checkpoint.**

For section §N:

#### Step B.N.0 — Worklog

Update Status → `Running (Phase 6.3.B §<N>)`.

#### Step B.N.1 — Show section block

```
**Pass B — §<N> <Section name>** (confidence: NN%)

*Đề xuất hiện tại:*
> <content draft, 3–8 dòng>

*Evidence:* <refs>
*Còn thiếu:* <bullet list các sub-items chưa có nguồn>

👉 Trả lời:
- `<nội dung bổ sung>` — Agent merge vào draft và remove tag.
- `accept` — giữ draft hiện tại (giữ tag `[AI-proposed]`).
- `skip` — bỏ qua (giữ tag; đẩy gap thành high-level question vào §10).
```

#### Step B.N.2 — Apply user response

Merge per tag lifecycle.

#### Step B.N.3 — Checkpoint write

1. Write `process-logging/06_3b_passB_§<N>.md` containing the draft snapshot after this section's update.
2. Update `progress.md` → `last_phase_done: 6.3.B:§<N>`, `next_phase: 6.3.B:§<next>` (or `6.3.C` if this was the last Pass B section).
3. Update agent-work-log row: `Status = Running (Phase 6.3.B §<next>)` if more sections remain, else `Phase 6.3.B done`.

Move to next Pass B section. Repeat until none remain.

### Pass C — Direct Q&A for empty sections (confidence = 0%)

Iterate per empty section. **Each section gets its own checkpoint.**

For section §N:

#### Step C.N.0 — Worklog

Update Status → `Running (Phase 6.3.C §<N>)`.

#### Step C.N.1 — Show Q&A block

Ask 2–4 TARGETED questions (không hỏi chung chung):

```
**Pass C — §<N> <Section name>** (chưa có dữ liệu từ common files)

Để hoàn thiện mục này, cần biết:
1. <câu hỏi cụ thể 1>
2. <câu hỏi cụ thể 2>
3. <câu hỏi cụ thể 3>

👉 Trả lời:
- Trả lời từng câu (đánh số) — Agent compose nội dung section từ answers và remove tag.
- Trả lời một phần — Agent fill phần có; phần còn lại đẩy vào §10.
- `skip` — bỏ qua mục này (placeholder `_<Pending — see Q-XXX>_`; high-level question vào §10).
```

#### Step C.N.2 — Apply user response

Compose section from answers per tag lifecycle.

#### Step C.N.3 — Checkpoint write

1. Write `process-logging/06_3c_passC_§<N>.md` containing the draft snapshot after this section's Q&A.
2. Update `progress.md` → `last_phase_done: 6.3.C:§<N>`, `next_phase: 6.3.C:§<next>` (or `7` if this was the last Pass C section).
3. Update agent-work-log row: `Status = Running (Phase 6.3.C §<next>)` if more sections remain, else `Phase 6.3.C done`.

Move to next Pass C section. Repeat until none remain.

---

## Tag lifecycle (applies to ALL passes)

| User action | Tag handling |
|---|---|
| `accept` toàn bộ / từng mục | **Remove** tag — content trở thành user-owned. |
| `modify §<N>: ...` (Pass A) | **Remove** tag — content user-owned sau khi merge. |
| Bổ sung nội dung (Pass B) | **Remove** tag — content user-owned sau khi merge. |
| Trả lời Q&A (Pass C) | **Remove** tag — content được compose từ answers. |
| Trả lời một phần (Pass C) | **Keep** tag với confidence cập nhật + evidence bao gồm "user input <date>"; phần còn thiếu đẩy vào §10. |
| `skip` (mọi pass) | **Keep** tag nguyên trạng — signal pending review cho run sau. |

Trong run kế tiếp (update mode), section nào còn tag `[AI-proposed]` sẽ được re-evaluate (re-score, có thể lên Pass A/B/C lại tùy confidence mới).

---

## Open Questions §10 — scope rule

Section 10 chỉ chứa câu hỏi **high-level / tổng quan** để track, KHÔNG phải mọi gap chi tiết. Detail gaps được resolve in-flow ở Pass B/C.

Ví dụ câu hỏi đủ điều kiện vào §10:
- "Stakeholder nào sẽ review/ký duyệt §<N> sau khi Agent đề xuất?"
- "Roadmap sau v1.0 đã có chưa? (ảnh hưởng scope và §2 Business Goal)"
- "Defect SLA và severity thresholds chưa được định nghĩa — cần input từ ai?"
- "Có thêm role/persona nào ngoài danh sách hiện tại không? (kéo theo cập nhật §4)"

KHÔNG đưa vào §10:
- "Permission cụ thể của role Vendor là gì?" (→ Pass B/C resolve trực tiếp).
- "Field `email` có bắt buộc không?" (→ thuộc UC detail, ngoài scope project-context).

All 10 sections are required; unresolvable info is acceptable as `[AI-proposed]` tag still present + high-level Q in §10 — do NOT block the skill.

Question IDs continue the sequence from `04_carryover.md`. Resolved questions retain their IDs and move to status `Resolved` (do NOT renumber, do NOT delete).

---

## Hand back to SKILL.md

After Pass C's last section, return control. The next dispatch is `phase-7-8-finalize.md`.
