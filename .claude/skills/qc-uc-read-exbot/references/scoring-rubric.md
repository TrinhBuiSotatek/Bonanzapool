# UC Readiness Scoring Rubric

> Rubric for `qc-uc-read-exbot` (logic / no-UI ExBot UC readiness review).
>
> This simplified rubric scores only the content quality of Phase 1 synthesis sections F.1-F.4 and one additional area for UC documentation issues.
>
> Acceptance Criteria candidates are not scored.

---

## 1. Core policy

Score only the feature / use case currently under review.

Do not penalize broad product, process, or architecture issues unless they directly affect this UC's behavior, operation / API logic, data rules, validation, state transition, integration, or Agent / tester understanding.

Phase 2 must build an Issue Register first. The scoring table is a short summary of the Issue Register, not a long report.

---

## 2. Acceptance Criteria policy

Acceptance Criteria candidates are **not** a scoring area.

Phase 1 may still synthesize AC candidates to help the user confirm Agent understanding.

Phase 2 may review AC candidates only as a non-scored confirmation aid:

- Are they traceable to source evidence or Phase 1 synthesis?
- Are they within the reviewed UC scope?
- Are they observable and pass/fail testable?
- Do they need user confirmation?

If an AC candidate is unsupported, too broad, or outside scope, record it as a UC documentation / synthesis quality issue only when it affects Agent understanding.

---

## 3. Status markers

| Status | Meaning |
|---|---|
| ✅ Clear | Complete, consistent, traceable, and unambiguous enough for Agent / tester understanding. |
| ⚠️ Partial | Present but incomplete, vague, inconsistent, partly inferred, or only partially traceable. |
| ❌ Missing | Absent from accessible artefacts. |
| 🚫 Blocked | Required or referenced artefact is unavailable or inaccessible, so the area cannot be verified. |

---

## 4. Severity levels

| Severity | Meaning |
|---|---|
| Blocker | Prevents reliable understanding of a critical feature behavior, or a required artefact is inaccessible. |
| Major | Creates meaningful ambiguity, conflict, missing logic, or traceability risk for test design. |
| Minor | Local issue that should be fixed but does not block understanding of the main behavior. |
| Note | Confirmation item or out-of-scope observation. Usually no score impact. |

---

## 5. Issue types

Use only these issue types unless this rubric is updated.

| Issue type | Use when |
|---|---|
| `MISSING_INFO` | Required functional information is absent from Phase 1 synthesis or source evidence. |
| `UNCLEAR_INFO` | Information exists but is vague, incomplete, or not specific enough for test design. |
| `CROSS_SOURCE_CONFLICT` | Phase 1 evidence shows contradiction between UC, FRD / SRS, API contract, state diagram / ERD, flow diagram, common rule/message, or project context. |
| `INTERNAL_INCONSISTENCY` | Terms, labels, statuses, rules, or flow behavior are inconsistent within the same source or synthesis section. |
| `AMBIGUOUS_WORDING` | Source wording is too broad or subjective, such as "valid", "appropriate", "quickly", "as needed", without a concrete rule. |
| `DESIGN_DETAIL_LEAK` | UC text specifies visual design details such as color, pixel, layout, spacing, font, or exact placement without functional/test relevance. **Rarely applicable here** — this is a logic / no-UI feature, so visual-design leaks are uncommon. |
| `SOLUTION_DETAIL_LEAK` | UC text over-specifies implementation details not needed to understand business behavior. **This is the common leak type for a logic / backend UC** (e.g. over-specified algorithm internals, infra/queue mechanics not needed to understand behavior). |
| `UNTRACEABLE_SYNTHESIS` | Phase 1 synthesis states behavior or rules without source trace or inferred marker. |
| `SYNTHESIS_SOURCE_MISMATCH` | Targeted verification shows Phase 1 synthesis does not match the original source. |
| `BLOCKED_EVIDENCE` | A required source or evidence section is marked missing, blocked, or inaccessible. |
| `AC_CONFIRMATION_NEEDED` | §F.5 AC candidate is useful but requires BA/QC Lead confirmation. This is not scored directly. |
| `OUT_OF_SCOPE` | The issue is not directly relevant to the reviewed use case. Do not include in scoring. |

---

## 6. Scoring areas

Total score: **100 points**.

No normalization is required.

| # | Scoring Area | Max | Critical? | What to evaluate |
|---:|---|---|---:|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | Yes | Functions, API operations / endpoints (logic, not HTTP-assert), triggers (request / queue / cron / event), inputs, outputs, data objects / fields, enum / valid-value sets, lifecycle states, emitted events, and error / success messages are listed **atomically** (one per row) and mapped to source (FRD / SRS / API contract / state diagram / ERD). |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | Yes | Each data object / function has system / lifecycle states and transitions, preconditions, validations, business rules, dependencies, and resolved error / success messages where applicable. |
| 3 | Functional Logic & Workflow Decomposition | 25 | Yes | Each major function has clear happy path, alternative path, exception path, trigger, input, output, actor / permission behavior, and system response (API response / state change / emitted event / message). |
| 4 | Functional Integration & Data Consistency | 15 | Yes | Cross-service, cross-function, queue, cron, Durable Object, external-API, and on-chain↔off-chain effects, plus data synchronization, are clear after create / update / close / reconcile / rebalance or related operations. |
| 5 | UC / Spec Documentation Quality Issues | 15 | Yes | UC / spec is clear, consistent, scoped, and reviewable. Penalize ambiguity, internal inconsistency, source conflict, solution-detail leak, untraceable synthesis, and wording that prevents Agent / tester understanding. |

## 6b. Blockchain UC readiness checklist (conditional)

Apply this checklist ONLY when the UC is blockchain-dependent — i.e.
`project-context-master.md` §1 declares a chain/wallet domain, OR the UC involves
connecting a wallet, signing, sending a transaction, or displaying on-chain data.
If the UC is purely off-chain, SKIP this checklist entirely.

This checklist does NOT add a scoring area. When an item below is missing or vague
for a blockchain UC, raise a `MISSING_INFO` / `UNCLEAR_INFO` issue under the mapped
existing area, so it affects that area's score normally.

| # | The UC should define... | Maps to area | If absent/vague |
|---|---|---|---|
| B1 | Wallet / agent-key states & messages: HL agent key approved / expired / revoked, signer rejected, key rotation (e.g. `setBotWlMaster`) | Area 2 | MISSING_INFO / UNCLEAR_INFO |
| B2 | Signing behavior: what is signed, reject-signature path, expiry/replay handling (if auth uses SIWE or similar) | Area 2/3 | MISSING_INFO |
| B3 | Required network/chain: expected chainId, testnet vs mainnet, wrong-chain and switch-chain behavior | Area 2/3 | MISSING_INFO |
| B4 | Transaction lifecycle: submitted → pending → confirmed / failed-reverted / dropped-replaced, and the bot / system state (lifecycle_state, emitted event) per stage (e.g. `lp_opening` → `lp_opened` on `VaultMinted`) | Area 3 | MISSING_INFO (often Blocker) |
| B5 | Pre-flight rules: insufficient gas/native token, token allowance/approve step, amount precision (decimals) | Area 3 | MISSING_INFO / UNCLEAR_INFO |
| B6 | Mid-flow events: agent-key change, circuit-breaker open, or margin → critical during a hedge-sync / close operation | Area 3 | UNCLEAR_INFO |
| B7 | On-chain ↔ off-chain consistency: which side is source of truth (e.g. on-chain `uninvestedBalanceOf` is canonical), event-watcher / reconcile lag behavior, optimistic-update revert rule | Area 4 | MISSING_INFO |
| B8 | Error/success messages for the above, resolved verbatim from requirement-common-files | Area 2 | UNCLEAR_INFO |
| B9 | Security expectations: no key/seed handling, approval/spender disclosure, signed-data matches displayed data | Area 5 | MISSING_INFO |

Out of scope for this checklist (do NOT penalize the UC for omitting): smart-contract
internal logic, gas optimization, on-chain audit concerns. These belong to dev/audit.

---

## 7. Score guide

Use the score guide below for each area.

| Score band | Meaning |
|---|---|
| 90-100% of max | Clear: only minor or no issues. |
| 60-89% of max | Partial: usable, but has missing details, ambiguity, or unresolved questions. |
| 1-59% of max | Weak: significant missing logic, conflicts, or unclear behavior. |
| 0 | Missing or blocked. Cannot be reliably reviewed. |

---

## 8. Auto-cap rules

Apply these caps after identifying issues.

| Condition | Cap |
|---|---|
| Any required / referenced artefact is inaccessible and the affected area cannot be verified. | Affected area = 0 and status = Blocked. |
| A blocker prevents understanding of a critical function. | Affected area max 40% of its max score. Final verdict = Not Ready. |
| F.1 groups multiple atomic functions / operations / data objects / states into one row, or omits operations / fields present in the provided FRD / API contract / state-diagram evidence. | Area 1 max 12/20. If API / spec evidence is referenced but unusable, Area 1 = 0. |
| Project's canonical source is the API contract / SRS / state diagram (no separate design artefact exists), and F.1 maps operations / fields / states atomically to that evidence. | No cap — the API contract / SRS / state diagram is treated as the canonical source. |
| F.2 does not cover at least 80% of F.1 elements. | Area 2 max 15/25. |
| F.3 covers happy path only and omits important alternative / exception paths. | Area 3 max 18/25. |
| F.4 is generic and does not identify concrete data, function, service, or on-chain↔off-chain impacts. | Area 4 max 7/15. |
| UC has unresolved contradiction across sources that changes expected behavior. | Area 5 max 8/15 and affected content area max 70% of max. |
| UC has repeated ambiguous wording for rules / validation / states. | Area 5 max 8/15 and affected content area max 80% of max. |
| UC over-specifies implementation / solution details as requirements without business meaning (the no-UI equivalent of a design-detail leak — usually a SOLUTION_DETAIL_LEAK). | Area 5 max 10/15. |
| Phase 1 adds behavior not traceable to source and does not mark it as inferred. | Area 5 max 9/15. |
| No formal AC section exists in UC. | No score impact. |

---

## 9. Blocked artefact handling

Do not treat a missing optional artefact as a blocker.

A blocker exists only when an artefact is required by the workflow or referenced by the UC / project context / path registry, but is unavailable or inaccessible.

When blocked:

1. Record `BLOCKED_ARTEFACT` in the Issue Register.
2. Set the dependent scoring area to 0 only if the area cannot be verified without that artefact.
3. Do not infer missing content from unavailable artefacts.

---

## 10. Final verdict

| Score | Verdict | Meaning |
|---:|---|---|
| 90-100 | Ready | Agent / tester can proceed with high confidence. |
| 70-89 | Conditionally Ready | Usable for clear areas; issues must be fixed or confirmed in parallel. |
| 0-69 | Not Ready | Too many gaps, conflicts, or unclear requirements. Do not proceed without clarification. |

Auto-fail: if any critical scoring area is 0, or any Blocker remains unresolved, verdict = Not Ready regardless of total score.