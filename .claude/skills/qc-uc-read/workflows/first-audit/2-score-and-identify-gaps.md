# First Audit · Phase 2 — Score & Identify Gaps

> **Friendly name (for worklog):** `Scoring & Identifying Gaps` (EN) / `Chấm điểm & xác định gap` (VI).
>
> **Input checkpoint:** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/01_synthesis.md`
>
> **Scoring rules:** `.claude/skills/qc-uc-read/references/scoring-rubric.md`
>
> **Output checkpoint:** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/02_scoring.md`
---
## Phase objective

Phase 2 reviews whether the Phase 1 synthesis and the source UC artefacts are clear, complete, consistent, and traceable enough for an Agent / tester to understand the reviewed feature.

Phase 2 scores only these areas:

1. F.1 UI Object Inventory & Source Mapping
2. F.2 Object Attributes, Behavior, Rules, Validations & Messages
3. F.3 Functional Logic & Workflow Decomposition
4. F.4 Functional Integration & Data Consistency
5. UC Documentation Quality Issues

Acceptance Criteria candidates from F.5 are reviewed only as confirmation aids and are not scored.

Do not raise broad product, process, design-system, or architecture issues unless they directly affect this reviewed UC.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` section 2:

1. Worklog: rewrite last entry -> `status = "Running (Phase 2)"`.

If this run resumes directly at Phase 2, first load `01_synthesis.md` into memory per `checkpoint-protocol.md` section 4 Resume load table

--- 

## Step 1 — Load Phase 1 synthesis and rubric

### 1.1 Load Phase 1 output

Open: .claude/skills/qc-uc-read/process-logging/<UC-ID>/01_synthesis.md

Use `01_synthesis.md` as the source of Phase 2 review evidence.

Expected Phase 1 content includes:

- evidence sections from Phase 1 Step 1 (`§A`–`§E`);
- synthesized understanding sections from Phase 1 Step 2 (`§F.1`–`§F.5`).

Use `§F.1`–`§F.4` as the primary content basis for scored areas. Use `§A`–`§E` only as supporting evidence for traceability, source alignment, missing evidence, or conflicts already extracted by Phase 1.

Do not score `§F.5` Acceptance Criteria candidates as a readiness area. Review them only as confirmation items if needed.

If an expected synthesis section is missing or unusable, do not invent content. Record an issue against the affected scoring area using the rules in `scoring-rubric.md`.

### 1.2 Load scoring rubric

Open: .claude/skills/qc-uc-read/references/scoring-rubric.md

Treat `scoring-rubric.md` as the **single source of truth** for:

- scoring areas;
- max points and total score;
- status markers;
- issue types;
- severity levels;
- score guide;
- caps / auto-fail rules;
- readiness thresholds / final verdict rules;
- reporting rules.

### 1.3 Rubric completeness check

Before building issues or scoring, check that `scoring-rubric.md` defines the rubric sections required for this phase.

At minimum, Phase 2 needs the rubric to define:

- scoring areas with max points;
- status markers;
- issue classification rules or issue types;
- severity rules or severity levels;
- score guide / cap rules;
- final verdict rules or readiness thresholds.

If any required rubric section is missing:

1. Warn the user in chat.
2. Add a `RUBRIC_WARNING` entry in `02_scoring.md` under `## Working notes`.
3. Continue only with the parts that can be applied safely from the available rubric.
4. Do not invent replacement definitions inside Phase 2.

If scoring areas or status markers are missing from `scoring-rubric.md`, do not fabricate a scoring table. Write the Issue Register and mark final scoring as `Cannot determine — rubric incomplete`.

---

## Step 2 — Build Issue Register from Phase 1 synthesis

Build the Issue Register before assigning scores.

Use the issue types and severity definitions from `scoring-rubric.md`.

### 2.1 Source basis

Use these sections from `01_synthesis.md`:

- `§F.1` for UI object inventory and source mapping.
- `§F.2` for UI object attributes, states, behavior, rules, validations, and messages.
- `§F.3` for functional logic, workflows, business rules, validations, and UI/UX feedback.
- `§F.4` for functional integration, downstream impact, and data consistency.
- `§A`–`§E` as supporting evidence for source grounding and cross-source alignment.
- `§F.5` only for non-scored AC confirmation notes.

### 2.2 Scope rule

Only create issues that affect the reviewed use case's feature behavior, UI interaction, business rules, validation, state transition, integration behavior, source consistency, Agent/tester understanding, or ability to design reliable test cases.

Ignore broader product concerns unless they directly affect the reviewed use case.

### 2.3 Issue Register format

Write the Issue Register in `02_scoring.md` using this table:

```markdown
## §A. Issue Register

| Issue ID | Type | Severity | Affected scoring area | Source trace from 01_synthesis.md | Finding | Impact on Agent/tester understanding | Suggested question or fix | Status |
|---|---|---|---|---|---|---|---|---|
```

Rules:

- Use `I-001`, `I-002`, ... for issue IDs.
- Keep each issue atomic.
- Do not duplicate the same issue across multiple rows.
- If one issue affects multiple scoring areas, list all affected areas in the same row.
- Use source trace from `01_synthesis.md`.
- If the issue is missing information, use `N/A — missing from Phase 1 synthesis` as the source trace.
- If the issue comes from targeted raw-source verification, include both the `01_synthesis.md` trace and the raw-source verification note.
- For `Type`, `Severity`, and `Status`, use values from `scoring-rubric.md` where defined. If not defined, use plain text and add a `RUBRIC_WARNING`.

---

## Step 3 — Review AC candidates without scoring

Review `§F.5 Acceptance Criteria Candidates for User Confirmation` only as a confirmation aid.

Do not assign points for Acceptance Criteria.

Do not penalize the reviewed UC merely because the source document lacks a formal AC section.

Create AC-related issue rows only when an AC candidate causes a review problem, for example:

- it is not traceable to `§F.1`–`§F.4`;
- it appears broader than the reviewed use case;
- it is too vague to be pass/fail;
- it should be confirmed by BA / QC Lead before being used for test design.

Use AC handling rules from `scoring-rubric.md` if present. If the rubric does not define AC handling, follow this Phase 2 boundary: AC candidates are reviewed for confirmation only and are not scored.

Write the AC review in `02_scoring.md` under:

```markdown
## §B. AC Candidate Review — Not Scored

| AC ID | Source trace | Review note | User confirmation needed | Related issue ID |
|---|---|---|---|---|
```

---

## Step 4 — Score readiness areas from the rubric

Score only the scoring areas defined in `scoring-rubric.md`.

Do not copy the scoring-area definitions from the rubric into this workflow. Do not hardcode the number, names, max points, or criticality of scoring areas here.

When scoring:

1. Read the scoring-area table or scoring-area section from `scoring-rubric.md`.
2. Use the scoring areas exactly as defined there.
3. Use max points exactly as defined there.
4. Use status markers exactly as defined there.
5. Apply score guide, caps, blocked handling, and auto-fail rules exactly as defined there.
6. Use the Issue Register as the main rationale for non-full scores.

If `scoring-rubric.md` does not define scoring areas or status markers, warn the user and do not fabricate them.

### 4.1 Scoring table format

Write the scoring table in `02_scoring.md` under:

```markdown
## §C. Scoring Table

| # | Scoring area | Max | Score | Status | Main evidence from 01_synthesis.md | Related issues | Rationale |
|---|---|---:|---:|---|---|---|---|
```

Rules:

- The rows must match the scoring areas from `scoring-rubric.md`.
- The `Max` values must match `scoring-rubric.md`.
- The `Status` values must use the rubric's status markers.
- Every non-full score must reference at least one issue ID unless the rubric explicitly allows another rationale.
- Do not give a full score to an area with unresolved blocker/major issues if the rubric defines those as score-impacting.
- Do not create an Acceptance Criteria scoring row unless the rubric explicitly defines AC as a scoring area.

---

## Step 5 — Determine final score and verdict from the rubric

Use the final-score and verdict rules defined in `scoring-rubric.md`.

Do not duplicate readiness thresholds or auto-fail rules in this workflow.

If `scoring-rubric.md` defines:

- a total score model, use it;
- a normalization formula, apply

---

## Checkpoint write — End of Phase 2

Per `workflows/checkpoint-protocol.md` §5:

1. Verify `02_scoring.md` contains §A (Issue Register), §B (AC Candidate Review), §C (Scoring Table), and final score/verdict. If any section is missing, do not proceed.
2. Update `progress.md` → `last_phase_done: 2`, `next_phase: 3`, `updated_at: <now>`.
3. Worklog: rewrite last entry → `status = "Phase 2 done"`. Append `02_scoring.md` to `output`.
