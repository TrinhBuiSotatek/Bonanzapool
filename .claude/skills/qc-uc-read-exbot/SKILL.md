---
name: qc-uc-read-exbot
description: Reviews ONE ExBot use case (no-UI bot tested through the Back-End and observed through the Admin site) for test-design readiness, using an SRS-first method — first read the whole srs/ folder to understand how the bot works (states, formulas, variables), then cross-check that baseline against the use case + its linked user stories to find conflicts, missing, wrong, or ambiguous information. Produces one audited report per UC with a 0–100 readiness score, using its own bundled template and scoring rubric. Use when the user says `review uc exbot`, `đọc uc exbot`, `audit exbot uc`, or `cross-check uc exbot`.
---

# ExBot UC Readiness Review Skill — SRS-first cross-check (lean)

> Lean, single-flow variant for the **ExBot** module. Scope: ExBot is tested only through the Back-End and observed through the Admin site — there is **no interactive UI**.
>
> This skill is deliberately stripped of the checkpoint/resume machinery and the parallel sub-agent fan-out. Its method puts the **srs/ baseline as the source of truth** and makes the **cross-check** the core activity. One run reviews one UC.

## Method (the user's workflow, encoded)

1. Read all of `srs/` first to understand how the bot works — states, formulas, variables, triggers — and form a holistic picture of ExBot.
2. Read the use case, the user provided the UC in the prompt.
3. Read every document related to that UC (the UC file, its linked user stories, frd, common rules, messages) using the index files for tracking.
4. **Cross-check** the `srs/` baseline against the UC + user stories to surface contradictions, missing items, wrong items, and ambiguity that would block test design.
5. Write the audited report with a readiness score.

## Input Contract (resolve every path via `.claude/config/path-registry.md`)

- `references/input-files-format.md` (in this skill) — structure of ExBot inputs, index files, and `BR-*` / `E-*` / `FR-EXBOT-*` prefixes.
- `requirement-files`
- `requirement-common-files`
- `project-context-master` (optional, if present).
- Always read the **highest `v[N]`** of any versioned file.

## Output Contract (resolve via `path-registry.md`)

- `uc-review-report` → `docs/qc/uc-read/<UC-ID>/<UC-ID>_<feature>_audited_<YYYYMMDD>_v<N>.md`.
- Naming per `.claude/rules/naming-convention.md`. **Never overwrite**: if `v[N]` exists, write `v[N+1]`.
- Optional: transfer Open questions to `question-backlog` via `qc-qna` (Step 5).

## Shared references

- **Scoring rubric** (areas, max points, status markers, issue types, severity, caps, verdict): `references/scoring-rubric.md`. Single source of truth for scoring.
- **Report template**: `templates/UC_readiness_review_template_v3.md`.
- **Writing rules** (MANDATORY): `.claude/rules/qc-writting-rules.md` — output is **English**.

## Worklog (MANDATORY — global-rules)

Log to the device JSONL under `worklog-per-device`; schema and the cross-platform safe-edit commands are in `docs/qc-lead/agent-work-log.local/README.md`. Lean lifecycle: **append** `status = "Running (Phase 1)"` at start; **rewrite** the last line to `status = "Done"`, `end = now`, `duration_min` computed, with the report path in `output` at the end. Exclude scratch from `input`/`output`.

---

## Workflow

### Step 0 — Identify the UC

Determine `<UC-ID>` from the user's prompt or the UC file name (e.g. `UC-EXBOT-bot-start`). Read `usecases/index.md` to confirm the UC exists, its `Linked Stories`, and `FR Trace`. Append the worklog start entry.

If the UC is ambiguous or not in the index, stop and ask the user.

### Step 1 — Build the ExBot baseline from `srs/` (source of truth)

Read **all** of `srs/spec.md`, `srs/states.md`, `srs/flows.md`, `srs/erd.md`, plus
`frd.md`. Build a compact mental model — do not score yet, do not write a file.
Capture, for the feature this UC touches:

- lifecycle states + transitions and their triggers (the full enum sets);
- formulas, variables, thresholds, and parameters;
- operations and their triggers (request / queue / cron / on-chain event);
- data objects + fields + types + on-chain↔off-chain source-of-truth side;
- emitted events and resolved error / success messages (`E-*`).

Routing: PDF → `pdf` skill; DOCX → `docx` skill; diagrams → read visually.
If an srs file is missing, warn once and continue.

### Step 2 — Scope and read the UC + its user stories

1. Read the UC file fully.
2. Resolve and read every **linked US** (from `usecases/index.md` `Linked Stories`
   or the UC frontmatter `linked_stories`), plus `userstories/index.md`.
3. Resolve every cited `BR-*` / `E-*` to verbatim text from `common-rules.md` /
   `message-list.md`. If a code is not found, keep it as written and append
   `(NOT_FOUND in common files)` — never invent content.
4. Verify `FR-EXBOT-*` cited by the UC exist in `frd.md`.

### Step 3 — Synthesize UC understanding (template sections + §F.1–§F.5)

Write the business understanding directly into the report draft, following
`templates/UC_readiness_review_template_v3.md` and `qc-writting-rules.md`. Produce,
atomically (one item per row — never group operations, fields, or states):

- **§F.1 Inventory** — functions/operations, triggers, inputs/outputs, data
  objects + fields + types, full enum/state sets, emitted events, messages, mapped
  to source (srs / frd / state diagram / erd).
- **§F.2** — per item: states, preconditions, validations, business rules,
  dependencies, resolved messages. At least one row per §F.1 item.
- **§F.3** — per major function: happy / alternate / exception path, trigger,
  input, output, actor/permission, system response (API response / state change /
  emitted event / message).
- **§F.4** — cross-function / queue / cron / external-API / on-chain↔off-chain
  effects and data consistency after create / update / close / reconcile / rebalance.
- **§F.5** — AC candidates (not scored; mark `Suy luận cần xác nhận` when inferred).

### Step 4 — Cross-check, build Issue Register, and score

This is the core step. Compare the **srs/ baseline (Step 1)** against the **UC + US
(Step 2–3)** and record every discrepancy in an Issue Register, then score with
`references/scoring-rubric.md`.

Cross-check directions (raise an issue per finding):

- **srs vs UC**: does the UC describe states / transitions / formulas / variables /
  messages that match `srs/`? (`CROSS_SOURCE_CONFLICT`, `MISSING_INFO`)
- **srs vs US**: do the user stories' AC match the bot behavior in `srs/`?
- **UC vs US**: are flows, rules, and AC consistent between them?
  (`INTERNAL_INCONSISTENCY`)
- **Completeness**: is anything in `srs/` (a state, an error path, a formula input)
  absent from the UC so a tester could not design a test? (`MISSING_INFO`)
- **Clarity / testability**: vague wording without a concrete rule
  (`AMBIGUOUS_WORDING`, `UNCLEAR_INFO`); over-specified implementation detail
  (`SOLUTION_DETAIL_LEAK`); behavior asserted without source trace
  (`UNTRACEABLE_SYNTHESIS`).
- **Blocked**: a required artefact is missing/inaccessible (`BLOCKED_EVIDENCE`).

Use the exact issue types, severities, status markers, scoring areas, max points,
caps, auto-fail, and final verdict from `references/scoring-rubric.md` — do not
redefine them here. Apply the blockchain checklist (§6b) only when the UC touches a
wallet / signing / transaction / on-chain data; ExBot UCs usually do.

Issue Register columns: `Issue ID | Type | Severity | Affected area | Source trace |
Finding | Impact on tester understanding | Suggested question or fix | Status`.

### Step 5 — Write the report (and hand off Open questions)

1. Fill the template completely (no empty sections — use `N/A` + reason if needed),
   in Vietnamese per `qc-writting-rules.md`.
2. Put the Issue Register / questions into **§10.1**, dependencies into **§10.2**,
   and the **§10.3 Audit Summary** with the scoring table, blockers, major issues,
   and a one-paragraph recommendation. Score and verdict must match Step 4.
3. Resolve the output path via `path-registry.md` → `uc-review-report`; write
   `v[N+1]` (never overwrite).
4. Invoke `qc-qna` to push every `Open` row from §10.1 into `question-backlog`. If
   none, skip; if `qc-qna` fails, warn and continue (non-blocking).
5. Rewrite the worklog last line to `Done` with the report path in `output`.

---

## Boundaries

- Review and audit only — never edit the input files.
- Every finding MUST cite the specific source section (srs / frd / UC / US / common file).
- Do NOT fabricate or assume requirements not in the documents.
- When uncertain, state the uncertainty and ask the user — never guess.
- Do NOT opine on implementation approach; leave architecture to the dev team.
- No UI in scope — never look for or penalize missing screens / wireframes.
