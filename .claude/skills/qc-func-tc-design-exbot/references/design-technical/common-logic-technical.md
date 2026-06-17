# Common Logic Technical Guideline for Test Case Design (No UI)

## Purpose

This guideline defines the common technical checklist for designing **LOGIC-only** test cases for backend / API / bot / worker / service systems that have **NO user interface**.

Use this file as the baseline checklist for every operation, function, queue handler, cron job, state machine, or business rule before applying the backend-bot add-on (`logic-technical.md`) and, when a chain / wallet / signer is involved, the Blockchain (Chain + Signer) backend add-on at the bottom of this file.

There are NO platform variants here (no web / mobile / desktop). Every test case is logic-only: each Step is an action + a condition to verify (the tester chooses the concrete endpoint / call), and every Expected Result is an observable system effect — an API / RPC response, a state-machine transition, a DB or on-chain state value, an emitted event, or a returned message / error code — NEVER a visual assertion.

## How to use

For each operation / function under test:

1. Identify the operation / function under test (e.g. `bot start preflight`, `hedge-sync`, `user_redeem`, `reconcile`). Name it by its logical / technical name, not a screen.
2. Apply all 5 logic phases in this file (Phase 1 → Phase 5).
3. Add the EXBOT / backend-bot add-on from `logic-technical.md` (lifecycle, circuit breaker, margin, close_operations, queue fan-out, hedge-sync, init, reconcile, SAFE_MODE, precision & idempotency, external dependencies, environment).
4. Check whether this operation is chain / wallet / signer-dependent (see the trigger gate in the "Blockchain (Chain + Signer) Add-on" section below). If YES, apply that add-on ON TOP of the 5 phases and the bot add-on. If NO, skip it entirely — do not generate signer / chain cases for a pure off-chain operation.
5. Add business rules, role / permission matrix (operation-level RBAC), data matrix, and environment matrix as needed.
6. Convert the checklist into concrete logic test cases with clear preconditions, steps (action + condition), and expected results (observable effect).

## Recommended test case fields

| Field | Description |
|---|---|
| Test Case ID | Unique ID, follow Rule 2 — Content Logic - `testcase-instruction-rules` (`TC_XXX`) |
| Phase | Phase 1 to Phase 5 (logic phases) |
| Function / Operation | The operation, function, queue handler, cron, or state-machine under test |
| Test Objective | What the test case validates |
| Preconditions | Role / state (actor + permission, entity / state-machine state), system / data state (DB rows, flags, fixtures), environment (testnet / mock RPC / seeded balances) |
| Test Data | Inputs, fixtures, mocked external responses, boundary values (decimals, wei↔token units, BigDecimal limits), idempotency keys / nonces / cloids. Describe boundaries in WORDS, not literals — see the Example field below |
| Steps | Logic actions — each a single action + condition to verify (NO UI object) |
| Expected Result | Observable effect: API / RPC response, state transition, DB or on-chain state, emitted event, or returned message / error code |
| Example (optional) | A concrete number / value shown ONLY to help the reader picture the case, written as an `(Example: …)` note at the END of the relevant cell (Pre-condition / Step / Expected). The case MUST stay executable if the example is removed. Keep all literal amounts / balances / thresholds HERE, never in the body — see `testcase-instruction-rules` Rule 6 |
| Priority | P0 / P1 / P2 |
| Test Type | Functional / Integration / State / Non-functional |
| Notes | Assumptions, constraints, out-of-scope items, open questions |

> **Writing style (mandatory):** every cell must read as a plain sentence a junior QC understands at a glance. Lead with the meaning, put identifiers / statuses / fields in parentheses as evidence (not as the sentence), use simple everyday QA words, and keep concrete numbers in the `(Example: …)` note only. Full rules + before/after examples: `rules/testcase-instruction-rules.md` → "Readability rules" (Rule 4 meaning-first, Rule 5 plain vocabulary, Rule 6 numbers-in-example).

---

# 5-Phase Logic Test Design Framework

## Phase 1: Preconditions & Initial State

Validate the system state that must hold BEFORE the operation runs.

### Entity / record existence
- Required entity / record exists (e.g. bot, position, hedge leg, agent key row).
- Required entity / record is absent — empty / no-data logic path (e.g. start with no prior bot; reconcile with no open position).
- Referential integrity preconditions (1-bot:1-position, 1-bot:1-hedge_leg invariants) hold or are deliberately violated to test the guard.

### State-machine initial state
- The state machine starts in the documented initial state (e.g. `idle`, `closed` circuit, `ok` margin).
- An operation attempted from a non-permitted initial state is rejected (cover at least one representative invalid start state).

### Auth / permission preconditions
- The required actor / role is present (operation-level RBAC: OPERATOR system actor, Admin, internal service token).
- The caller lacks the required permission / token → rejected before any side effect.
- The request reaches the worker only through the allowed path (e.g. internal service binding, not public internet).

### Config / feature flags
- Required config is present and valid (e.g. contract address injected from secrets store, chain id, thresholds).
- A feature flag / phase gate that disables the operation is honored (operation no-ops or rejects).

### Environment & deterministic fixtures
- Run on testnet / forked node / mock RPC with seeded balances and known nonces for deterministic results.
- Mocked external responses (HL, RPC, contract) are wired before the operation runs.

### Idempotency keys / nonces pre-state
- The idempotency key / nonce / cloid for this operation is in its expected pre-state (e.g. no prior `queue_idempotency` row, `state_version` matches the message).

---

## Phase 2: Input & Contract Validation (logic, not HTTP-assert)

Validate that the operation accepts valid inputs and rejects invalid ones at the logic level.

### Required inputs
- Each required input present → accepted; each required input missing → rejected with the correct reason.

### Type / format
- Wrong type / malformed format rejected (e.g. non-numeric amount, malformed address, bad enum value).

### Range / length / precision
- Boundary values for every numeric constraint: min−1, min, min+1, max−1, max, max+1.
- Decimal / unit precision: wei↔token units, BigDecimal scale, basis-point normalization (e.g. `normalizeTargetRatioBps("0.70")` → 7000n). No float rounding loss.

### Enum / state validity
- Only canonical enum values accepted (e.g. canonical `RebalanceReason[]` values); variant spellings / aliases rejected.

### Cross-field
- Cross-field rules enforced (e.g. delta sign vs target direction; target ratio vs leverage; expires_at vs now).

### Signed-request validity (where relevant)
- Signed-request validity at the logic level: HMAC-SHA256 internal signature, SIWE message, or HL agent-key signature verified; tampered / replayed / expired signatures rejected. Signer address ≠ expected address rejected.

### Idempotency-key / nonce / cloid validity
- Idempotency key / nonce / cloid present and well-formed; duplicate or stale key handled per the reject path (see Phase 3 duplicate handling).

### Reject paths
- Every rejection returns the correct message / error code and leaves NO partial side effect (no half-created record, no submitted order).

---

## Phase 3: Core Functional Logic

Validate the business logic and functional outcome of the operation.

### Happy path
- The standard successful flow with valid inputs produces the correct end state, the correct persisted values, and the correct emitted events / responses.

### Business-rule decision tables
- Map condition combinations to expected outcomes for every multi-condition rule (e.g. margin status × circuit state × requested action; close kind × failure condition × resulting state).

### Calculations
- Verify every financial / quantitative computation with BigDecimal: fees, hedge delta, PnL, leverage, stop trigger price, margin usage, drift thresholds. Cover boundary inputs of each formula.

### State transitions
- Cover EVERY valid transition of the state machine (one case per edge).
- Cover representative INVALID transition attempts (operation requested from a state where it is not allowed → blocked, no side effect).

### Exception / error handling
- External dependency failure, validation error, conflict / optimistic-lock error, timeout, malformed / partial response → the operation fails safely with the correct error code and no inconsistent state.

### Duplicate / idempotency
- Double-submit, message redelivery, retry with the same idempotency key / nonce / cloid → exactly ONE effect (no double order, no double settlement, no duplicate record). The second attempt exits cleanly (e.g. UNIQUE-conflict short-circuit).

### Batch / bulk via queue
- Batch produced via the queue helper (chunked to the platform max); partial success reported clearly; failed items carry a reason and a recovery path (dead-letter / repair queue).

### Concurrency & locking
- Lock contention (e.g. Durable-Object lease held by another worker) → the second worker re-queues with delay, does not run the mutation.
- Optimistic concurrency: a stale `stateVersion` (message version < current DB version) → the operation aborts / skips without any external mutation.

---

## Phase 4: Integration & Data Consistency

Validate how the operation interacts with other services, queues, crons, durable objects, external APIs, and data stores.

### Cross-service calls
- Calls across services (e.g. OPERATOR facade → ExBot worker, Admin config, external indexer) succeed on the happy path and fail safely on dependency error / unauthorized.

### Queue fan-out
- Cron → scan → worker fan-out produces the correct messages; backlog / redelivery / dead-letter behavior is correct; no message is processed twice (idempotency ledger).

### Cron scheduling / overlap / jitter
- Scheduled jobs fire at the correct cadence; overlapping runs do not double-process; jitter / next-run scheduling is applied and batched as designed.

### Durable-Object coordination
- DO lease / cache coordination behaves correctly across concurrent worker invocations (single shared instance, lease TTL auto-release, cache refresh / staleness handling).

### External API
- External API (e.g. Hyperliquid) success, failure, timeout, rate-limit (budget exceeded → back-off / re-queue), and partial-fill paths are all covered.

### Reconciliation
- After every mutation, reconcile expected vs actual external state; a mismatch is detected and routed correctly (alert / SAFE_MODE / repair). Success is recorded ONLY after reconcile confirms.

### Event watchers
- Missed event (watcher offline), duplicate event, and out-of-order event are all recovered to the correct state (manual / scheduled re-scan, idempotent application).

### Data sync (on-chain ↔ off-chain, multi-store)
- DB tables stay consistent with each other and with on-chain truth. The source-of-truth rule is honored where the spec names it (e.g. on-chain balance is canonical for a capital check). Indexer / RPC lag and optimistic-update revert are handled per spec — never a silent wrong value.

---

## Phase 5: Non-Functional (logic-accessible)

Validate the quality attributes observable through logic / backend interfaces. (Pure UI / visual / accessibility checks are out of scope for this skill.)

### Security
- Auth layers enforced at the operation level (internal token, RBAC, signed requests).
- Request signing verified; tampered / replayed requests rejected.
- Secret / key handling: secrets and raw keys are NEVER logged, returned, or leaked in error messages; envelope-encryption (DEK wrap / unwrap) handled correctly and plaintext is function-scoped and destroyed after use.
- A D1 / DB dump contains only encrypted blobs for sensitive material.

### Reliability / resilience
- Circuit breaker open / half-open / closed behavior; SAFE_MODE entry / monitor-only / auto-recovery; margin-status escalation; failover and graceful degradation on dependency outage. No safety path is a terminal dead-end (auto-recovery or safe-close).

### Performance / throughput
- Queue throughput / scan-cycle scale target (e.g. N bots within a time window); batch-size limits; per-operation latency SLA; rate-limit budget not exceeded.

### Auditability / logging
- Every sensitive / state-changing action writes an audit record with actor, action, timestamp, target, and result.
- Audit / log records contain NO PII and NO secrets.
- Error logs are useful for diagnosis without leaking sensitive values.

### Data persistence / migration / versioning
- Persisted state survives restart / redelivery; write-on-change budget respected; schema-evolution rules honored (e.g. ADD COLUMN only, no DROP / RENAME after deploy); versioned ledgers (idempotency keys) prevent replay.

---

## Blockchain (Chain + Signer) Add-on — Backend / Bot Context

### Trigger gate — apply this add-on ONLY when at least one is true

Apply this add-on to the operation under test if ANY of the following holds:

- the operation signs and submits an on-chain transaction or a signed exchange request using a server-held signer / agent key; OR
- the operation reads on-chain state (balance, allowance, position, contract view call, event log); OR
- the operation depends on data that must stay consistent with on-chain truth; OR
- the operation manages a signer / agent-key lifecycle (approval, expiry, rotation, revocation).

If NONE of these holds, SKIP this entire add-on. Do not invent signer, gas, or network cases for a purely off-chain operation.

### How to apply (when triggered)

1. Keep applying the 5 logic phases and the bot add-on as usual — this add-on does NOT replace them.
2. Add the 3 extra test case fields below to every chain-dependent case.
3. Walk the areas in order and generate cases for each that applies:
   A. Signer / Agent-key Lifecycle & Identity (backend, no human popup)
   B. On-chain Transactions (lifecycle, pre-flight, idempotency)
   C. Network & Chain
   D. On-chain ↔ Off-chain Consistency
   Plus the two cross-cutting sections (Security & determinism).
4. Scope filter — generate a case only when the trigger for that sub-area is present:
   - No signing in this operation → skip A3 (request signing).
   - Read-only operation (no tx) → skip Area B's submission cases, keep A / C / D as relevant.
5. Mandatory rule: every on-chain operation states BOTH the on-chain expected result AND the off-chain (DB / ledger / backend) expected result. On-chain-only assertions are incomplete.
6. Out of scope — do NOT generate: smart-contract unit / property tests, gas optimization, on-chain security audit, or key-management cryptography internals. Flag them as out-of-scope (owned by dev / audit).

### Extra test case fields for chain-dependent operations

| Field | Description |
|---|---|
| Signer / Contract Precondition | Which signer / agent key (approved? expired? rotated?), which contract + injected address, internal-token gate |
| Chain / Balance Precondition | Expected network (mainnet / testnet + chainId), signer's on-chain balance(s) relevant to the operation |
| On-chain Expected Result | What MUST be true on-chain (tx status, event emitted, state / balance change, position size) |
| Off-chain Expected Result | What the DB / ledger / backend MUST reflect after the on-chain result (row state, idempotency ledger, last-known values) |

> Rule: every on-chain test case MUST state BOTH the on-chain expected result AND the off-chain (DB / ledger / backend) expected result. A case that only checks the chain is incomplete.

#### Area A — Signer / Agent-key Lifecycle & Identity (server-side, no human popup)

> This is the backend equivalent of interactive wallet-UI flows. There is NO connect popup, NO reject-in-wallet popup, NO WalletConnect QR, and NO account-switch UI event. Signing is performed server-side with a stored, approved agent key. The UI-only sub-areas of the original wallet add-on (connect / disconnect dialog, reject-in-wallet, QR pairing, account-switch UI events) apply ONLY if a user-facing wallet flow exists — which is out of scope for a pure backend module.

A1. Agent-key state
- Key with `approved` status and not expired → accepted at preflight.
- Key `pending` / `revoked` / expired → rejected with the correct error code; no order submitted.
- Key rotation: a new approved key supersedes the old one atomically; the old row is retained for audit (no destructive delete).
- Mismatch: signer / agent address ≠ the user's registered address → rejected.

A2. Server-side signing
- The operation signs with the function-scoped decrypted key; the plaintext key / DEK never appears in logs.
- A decryption failure (e.g. the key was revoked mid-flight) fails safely and routes to SAFE_MODE without exposing key material.

A3. Request signing (authentication)
- The signed exchange request / message carries the correct domain, address, and nonce; replayed / expired nonce rejected by the counterparty / verifier.

#### Area B — On-chain Transactions

B1. Pre-flight checks
- Insufficient native / margin balance → operation blocked with a clear reason BEFORE submission.
- Required allowance / approval present (or the approve step runs first) where applicable.
- Amount precision: decimals handled correctly (wei↔token units), no rounding loss; a "max" computation leaves enough native balance for fees where required.
- Would-revert detection (simulation) surfaces the failure BEFORE sending, not after.

B2. Transaction lifecycle (state-transition testing)

Treat the tx as a state machine and cover each transition:

    idle -> submitted -> pending -> confirmed
                       \-> failed / reverted
                       \-> dropped / replaced

- Submitted → pending: the off-chain record reflects "pending" with the tx hash; the operation is not double-submitted.
- Confirmed after the required confirmations → success state persisted + downstream effect applied.
- Reverted on-chain → the off-chain record reflects failure; no optimistic success left dangling.
- Dropped / replaced → the operation reconciles and resubmits idempotently (same deterministic id), never blindly.
- Reorg: a previously "confirmed" tx is rolled back → the off-chain state reverts correctly on the next reconcile.

B3. Idempotency & duplicates
- Double-submit / message redelivery does NOT broadcast two transactions (deterministic cloid / idempotency key).
- Retry after timeout reuses the same deterministic id and reconciles actual state before any resubmit.

#### Area C — Network & Chain
- Wrong / unexpected chainId → the operation is gated; testnet vs mainnet guard enforced.
- The contract address used is the injected, expected address per chain (not hard-coded, not swapped).
- RPC down / slow / rate-limited → error + bounded retry / back-off; no infinite wait.
- Multi-chain: the same logical entity on different chains keeps independent state (no cross-bleed; correct `wethIndex` / token ordering per chain).

#### Area D — On-chain ↔ Off-chain Consistency

The hardest defects live here: the backend / DB disagreeing with the chain.

- Indexer / watcher lag after a confirmed tx → spec'd behavior (polling, "syncing" marker, scheduled reconcile), never a silent stale value.
- Optimistic off-chain update then on-chain failure → the off-chain state reverts to the true state.
- Source-of-truth rule: where the spec names on-chain as canonical (e.g. an on-chain balance read for a capital check), the off-chain value is reconciled to it, not trusted blindly.
- Missed event (watcher offline) → a manual / scheduled re-scan recovers the correct state.
- Read-after-write: re-reading state immediately after a tx returns consistent data or a clearly-labelled pending state.

#### Cross-cutting — Security (chain-specific, extends the Phase 5 Security checks)
- The master private key is NEVER stored; only the delegated agent key (envelope-encrypted) is stored.
- The parameters actually signed MATCH the parameters the operation intends (amount / contract / size).
- Contract / spender addresses are the expected, verified ones.
- No raw key, raw DEK, or signed-payload secret appears in any log or error message.

#### Cross-cutting — Test environment & determinism
- Prefer testnet / forked node / mocked RPC and counterparty (HL) responses for deterministic runs.
- Use seeded accounts with known balances and known nonces; use deterministic cloids / idempotency keys.
- Flag any case whose result depends on live mainnet conditions (gas price, congestion, real funding) as non-deterministic and isolate it from the regression suite.

---

# Output principle

A good logic test suite should not simply list operations. It should combine:

```text
Common 5 logic phases
+ Backend-bot add-on (logic-technical.md)
+ Business rules
+ Data matrix
+ Environment matrix
+ Clear, observable expected results (both on-chain AND off-chain where applicable)
```
