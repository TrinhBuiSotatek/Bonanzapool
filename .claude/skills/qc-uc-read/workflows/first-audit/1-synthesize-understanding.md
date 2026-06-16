# First Audit · Phase 1 — Synthesize Requirement Understanding

> **Friendly name (for worklog & dashboard):** `Synthesizing Requirement Understanding` (EN) / `Tổng hợp hiểu biết requirement` (VI).
>
> **Inputs:** UC document(s), design images, supporting artefacts (API spec, BPMN, etc.), common reference files.
>
> **Output checkpoint:** `process-logging/<UC-ID>/01_synthesis.md` — contains the 5 synthesis sections + Section 4 inventory with `Delta = 0` coverage verified.

---

## Status update — Start

Per `workflows/checkpoint-protocol.md` §2 (write-before-work rule):

1. **Worklog**: rewrite last entry → `status = "Running (Phase 1)"`. Append input file names to `input` (excluding `process-logging/`).
2. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Running — Synthesizing Requirement Understanding` (use the input UC's language — see protocol §3 phase friendly names table). Skip if column missing (graceful degradation).

---

## Step 1: Read all artefacts

- Read the `project-config` file (resolved via `path-registry.md` → `docs/qc-lead/project-config.md`) — **§ 2. Project Context** section to understand the project context.
- Read the common files first — Read `.claude/skills/qc-uc-read/references/input-files-format.md` to understand the input file's structure and to ensure that you understand all the common rules and the project context.

**Common Reference Resolution rule (MANDATORY):** When the source UC references a common-file entry by code/ID/name (e.g., `MSG_E001`, `BR_xxx`, the name of a common function), do NOT leave the bare code in the audit output. Open the corresponding common file, copy the **exact original text** (message wording, full rule statement, function description), and inline that text into the audit section that uses it (Section 6.1.B Business Rules, 6.1.C Error Codes / Toast Messages, Section 3 Preconditions if a common function is reused, etc.). Preserve the original code in parentheses for traceability — e.g., `"New user created successfully." (MSG_E001)`.
This is so test cases written downstream from the audit file have the exact verbatim message/rule text in `Expected Result` without re-opening the common docs.

- Then read each provided UC file or pasted content fully before scoring anything.
- **Site-map cross-check (optional input):** if `qc-site-map` exists, read §5 Screen/Page inventory + §6 Navigation & screen flow + §7 Role/access by screen + §8 Screen ↔ Feature mapping. Hold in working memory: (a) screens mapped to the UC's feature in §8, (b) flows in §6 touching those screens, (c) roles in §7 with access. These feed Phase 2 KA #3/#4/#7 gap detection and the Cross-Artefact Conflict Check. If missing, skip and warn once.

### Input-type routing

| Input type           | Action                                                                                                          |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| PDF provided         | Invoke the `pdf` skill to extract text, tables, images first. Do NOT use the Read tool directly on PDF files.   |
| DOCX provided        | Invoke the `docx` skill to extract text, tables, images first. Do NOT use the Read tool directly on DOCX files. |
| File path provided   | Read the file using the appropriate tools.                                                                      |
| Pasted text provided | Treat as a document; parse directly from the prompt.                                                            |

### Supported artefact types

Accept any combination of:

| Type                        | Examples                                           |
| --------------------------- | -------------------------------------------------- |
| Requirements / Use Case doc | UC spec, feature brief, BRD, user story            |
| API Specification           | REST API doc, Swagger/OpenAPI, integration spec    |
| Business Process doc        | Workflow diagram, BPMN, process description       |
| Design document             | Technical design, system design, architecture note |
| Other supporting docs       | Data dictionary, error code list, SRS spec         |

All file formats are supported: plain text, Markdown, PDF, Word (.docx).

---

## Step 2: Synthesise a Feature Understanding

After fully comprehending all provided documents, proceed to synthesize the requirement content according to the following 5 sections:

### 1. API / Queue / State Interface Inventory

Extract and catalog every endpoint, queue consumer, and Durable Object from the UC spec §2 (API/Queue/State Interface section) and any referenced SRS sections.

**Granularity rule (MANDATORY):** Every endpoint, queue, and DO gets **its own row**. Do NOT collapse multiple fields into one row (e.g., do NOT write "5 request fields" — list each individually). Each row MUST capture:

- **ID** — API-XB-\* / QUE-XB-\* / DO-XB-\* (from site-map or SRS), or method + path for REST endpoints
- **Trigger condition** — what event or caller initiates this endpoint/queue/DO
- **Request fields** — name, type, required/optional, constraint (one sub-row per field)
- **Success response shape** — fields returned on success
- **Error codes + messages** — exact list of all error codes and their message text
- **For Queue:** DLQ policy, retry count, backoff interval, idempotency key field, priority/SLA if stated
- **For DO:** state owned, lease duration, expiry action, contention policy

**Self-check before finishing this step:** Count total entries (endpoints + queues + DOs) declared in the UC spec §2 header and body. The number of rows in this inventory must equal that count exactly. If any entry is missing, add it with `[BLOCKED: no schema provided]`.

### 2. System State Model

Define the state and behavior of each entry in Section 1 based on system conditions.

**1-to-1 mapping rule (MANDATORY):** This section MUST contain **at least one row for every entry in Section 1**. If an entry has no special behavior beyond what is in its schema, still list it with a note — do NOT omit it.

- **Lifecycle state transitions (for FM-XB-07 and any UC touching bot lifecycle):** For each state, define: trigger event → guard condition (include NV gate status if applicable) → resulting state. Flag transitions guarded by unresolved NV items as ⚠️ Partial.
- **DO behavior:** For each DO from Section 1: lease duration, expiry action (what happens when lease expires), contention rule (what happens when two callers race for the same DO).
- **Queue behavior:** For each queue from Section 1: DLQ policy (max retries, backoff), idempotency key field, priority relative to other queues, SLA (if stated). Flag queue behaviors where NV gate applies.

Do NOT use UI vocabulary. Use: Trigger / Guard / State-in / State-out / Error-handling.

### 3. Functional Logic & Workflow Decomposition

Analyze in detail the business processes of each operation in the feature (bot-start, light-check, hedge-sync, user-redeem, safe-close, agent-key, etc.).

- **Workflows:**
  - **Main Flow (Happy Path):** The correct execution sequence with no errors.
  - **Alternative Flows:** Alternative paths leading to a successful outcome.
  - **Exception & Error Flows:** Scenarios involving system errors, NV-blocked paths, or invalid inputs.
- **Business Rules & Validations:** Resolve every BR-\* and FR-EXBOT-\* reference to its exact verbatim text from `common-rules.md` / `srs/spec.md` (per Common Reference Resolution rule). Keep the code in parentheses for traceability.
- **System feedback:** Error codes returned, queue enqueue confirmations, D1 state changes, DO lease acquisitions.

### 4. Functional Integration Analysis

Analyze linkages and influences between operations in this feature.

- **Impact Analysis:** Determine whether a state change or data mutation in one operation directly or indirectly affects other operations (e.g., bot-start enqueues to hedge-sync queue; user-redeem acquires UserLockDO lease).
- **Cross-chain consistency:** For dual-chain operations (Base/OP), verify that wethIndex usage and pool address handling are addressed per NV-12 status.
- **DO lease coordination:** Check for scenarios where two operations could race for the same DO and verify contention policy is stated.

### 5. Acceptance Criteria (AC) Synthesis

Establish the final set of measurement and evaluation standards for the requirement.

- **AC per operation:** Categorize and detail acceptance criteria for each operation: state transition correctness, error handling, SLA compliance (where applicable), idempotency guarantees.
- NV-gated ACs must be flagged explicitly: mark them as `[BLOCKED: NV-N pending]` so they are not included in Phase A1 test scope until the NV gate passes.

---

## Step 3: Interface Coverage Self-Verification (mandatory before exiting Phase 1)

Before exiting Phase 1, verify that Section 1 (API/Queue/State Interface Inventory) is complete:

1. Count `entries_in_spec` — total endpoints + queue consumers + DOs declared in the UC spec §2 header and body.
2. Count `rows_in_section_1` — rows written in the inventory above.
3. Record:

   | UC | entries_in_spec | rows_in_section_1 | Delta | Action |
   |---|---|---|---|---|
   | *(UC-ID)* | *(N)* | *(M)* | *(N − M)* | *(if Delta > 0: add missing entries as [BLOCKED: no schema]; if Delta < 0: review for fabricated entries)* |

4. Loop until `Delta == 0`. Only then proceed to Phase 2.

---

## Checkpoint write — End of Phase 1

Per `workflows/checkpoint-protocol.md` §5:

1. **Write checkpoint file** `.claude/skills/qc-uc-read/process-logging/<UC-ID>/01_synthesis.md` with:
   - The 5 synthesis sections (full content)
   - The interface coverage delta table (must show `Delta = 0`)
   - Working notes: detected input language, UC-ID, version of source files read, list of blocked artefacts (if any)
2. **Update `progress.md`** → `last_phase_done: 1`, `next_phase: 2`, `updated_at: <now>`.
3. **Worklog**: rewrite last entry → `status = "Phase 1 done"`.
4. **qc-dashboard.md**: update the UC's `UC review stt` cell → `Synthesizing Requirement Understanding done` (skip if column missing).

---

## Hand-off to Phase 2

Next file: `workflows/first-audit/2-score-and-identify-gaps.md`. It reads `01_synthesis.md` from the checkpoint folder and scores the 10 knowledge areas using the rubric in `references/scoring-rubric.md`.
