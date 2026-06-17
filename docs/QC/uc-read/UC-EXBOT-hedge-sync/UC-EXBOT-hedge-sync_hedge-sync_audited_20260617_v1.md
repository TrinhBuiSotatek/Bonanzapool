# UC Readiness Review — UC-EXBOT-hedge-sync
**Functional / Black-box Test Readiness Review**
> Document Title: UC-EXBOT-hedge-sync Readiness Review v1
> Date Created: 2026-06-17
> Author/Agent: qc-uc-read (run-20260617-090000-udemysen)
> Version: v1

---

## Feature Brief

UC-EXBOT-hedge-sync covers the periodic delta-only hedge adjustment flow for an active ExBot. When a `hedge-sync` queue message is received, the Hedge-Sync Worker acquires a distributed lock via `UserLockDO`, checks the message's `stateVersion` against D1 for optimistic concurrency, fetches the actual HL short position, computes the delta (`targetShortEth − actualShortEth`) using BigDecimal only, and submits a delta-only adjustment via `adjustShortDelta`. A full close → open cycle is architecturally forbidden (`BR-EXBOT-004`) except for target=0 or admin-invoked emergency. After the delta order, stop replacement executes via the INV-STOP protected protocol (§19.5, `FR-EXBOT-035`). Post-order reconcile verifies actual HL size, extracts prices, recomputes `stop_trigger_px`, and updates D1. Circuit breaker logic handles HL rejections; partial fills route to a `partial_repair` queue (capped at 3 retries → `bot_safe_close`).

Key invariants: delta-only hedge, BigDecimal only, INV-STOP for stop replacement, `UserLockDO` as single-writer lock, `queue_idempotency` for at-most-once semantics, deterministic `cloid` for HL deduplication.

---

## Readiness Verdict

| Overall Score | Verdict |
|---|---|
| **67.7 / 100** | ❌ **NOT READY** |

**Primary blockers:** NV-3 (INV-STOP §19.5 path unconfirmed), NV-13 (HL minimum order size unconfirmed).

---

## 0. Document Metadata

| UC-ID | Feature Name | Version | Status |
|---|---|---|---|
| UC-EXBOT-hedge-sync | Delta-only Hedge Adjustment + Stop Replace (INV-STOP protocol) | v1 | Draft |

| Author / BA | Approved By | Date Created | Last Updated |
|---|---|---|---|
| @hienduong (BA) | — | 2026-06-12 | 2026-06-17 |

---

## 1. Objective & Scope

### 1.1 Objective

Provide a cost-efficient hedge adjustment mechanism for active ExBots that adjusts only the delta between target and actual HL short position — never performing a full close+open cycle. This minimizes HL rate limit consumption, reduces fee cost, and preserves INV-STOP safety invariant (stop is always protected during resize).

### 1.2 In Scope

- Receiving and processing `hedge-sync` queue messages
- stateVersion optimistic concurrency check before lock acquisition
- `UserLockDO` lease acquire/release lifecycle
- Delta computation: `BigDecimal(targetShortEth).sub(actualShortEth)`
- HL delta-only order submission via `adjustShortDelta(delta, cloid)`
- Deterministic cloid generation (`FR-EXBOT-024`)
- INV-STOP stop replacement protocol (`FR-EXBOT-035`)
- Post-order reconcile: actual size verification, price extraction, `stop_trigger_px` recomputation (`FR-EXBOT-025`)
- `partial_repair` enqueue on partial fill (A4)
- Circuit breaker state management on HL rejection (A3)
- `queue_idempotency` lifecycle (started → succeeded)

### 1.3 Out of Scope

- Full close/open hedge cycle (forbidden in normal hedge-sync per `BR-EXBOT-004`; target=0 case handled by `UC-EXBOT-bot-safe-close`)
- LP rebalance (`partial_repair` class 2 — FR-EXBOT-015 handled by separate flow)
- SAFE_MODE entry on `stop_replacing_started_at` overrun (A5) — handled by light-check + deep-audit UCs
- `bot_safe_close` initiation after 3 partial-repair failures (delegated to `FR-EXBOT-036` / `UC-EXBOT-bot-safe-close`)
- `deep-audit` reconcile flow (6h cadence, separate UC)

---

## 2. Actors & Stakeholders

| Actor | Type | Role & Permissions |
|---|---|---|
| ExBot System Operator (Hedge-Sync Worker) | Primary / System | CF Worker that consumes `hedge-sync` queue messages; executes all steps 1–16; no human interaction |
| Reconcile Worker | System | CF Worker that executes post-order reconcile (steps 11–15); receives `reconcile` queue message |
| UserLockDO | System (CF Durable Object) | Serializes per-user HL mutations; TTL=90s; single writer enforced via lease |
| Hyperliquid (HL) | External System | Target for delta-only position adjustment; source of actual position data |
| Cloudflare D1 | System | Persistent store for bot state, hedge_legs, rebalance_attempts, circuit_breakers, queue_idempotency |

---

## 3. Preconditions & Postconditions

### 3.1 Preconditions

- `hedge-sync` queue message received with `{botId, reasons: RebalanceReason[], stateVersion}`
- Bot `status='active'`, `lifecycle_state='active'` in D1
- `circuit_breakers.state IN ('closed', 'half_open')` — hedge-sync is suppressed when `state='open'`
- *(Inferred — NV gate not listed in UC)* NV-3 (HL stop replacement protocol path) must be confirmed before INV-STOP implementation is finalized
- *(Inferred — NV gate not listed in UC)* NV-13 (HL min order size) must be confirmed before minimum delta threshold is implemented

### 3.2 Postconditions

| After completing... | System State / Postcondition |
|---|---|
| Happy path (Step 16) | `hedge_legs` updated: `stop_price`, `entry_price`, `effective_leverage`, `stop_replacing_started_at=NULL`, `stop_cloid`, `stop_order_id`; `bot_runtime_state.last_known_hl_short_size = reconciled_size`; `rebalance_attempts.status='success'`; `queue_idempotency.state='succeeded'` |
| A1 (lock held) | No HL order submitted; message re-queued with delay; no D1 mutation |
| A2 (stateVersion mismatch) | No HL order submitted; `rebalance_attempts.status='skipped'`; `queue_idempotency.state='succeeded'` |
| A3 (HL rejection) | `rebalance_attempts.status='failed'`; `circuit_breakers.failure_count` incremented (or `state → 'open'` after 3 consecutive); notification enqueued |
| A4 (partial fill) | `partial_repair` message enqueued; D1 records partial state |

---

## 4. API / Queue / State Interface Inventory

> **Note:** UC §2 is ABSENT from `uc-hedge-sync.md`. All entries below are reconstructed from §3 Main Scenario and §5 Postconditions. Auto-cap applied to KA #5 (max 8/15).

**Queue Consumers:**

| # | Queue ID | Trigger Event | Handler Summary | DLQ Policy | Retry Count | Idempotency Key | Priority / SLA |
|---|---|---|---|---|---|---|---|
| 1 | `hedge-sync` queue | Enqueued by light-check scan or system event | Hedge-Sync Worker: stateVersion check → lock → fetch → delta → submit → INV-STOP → release | ⚠️ Not defined in UC | ⚠️ Not defined in UC | `message_id` (in `queue_idempotency`) | Normal |
| 2 | `reconcile` queue | Enqueued by Hedge-Sync Worker after delta order submitted | Reconcile Worker: fetch actual HL position, verify size, extract prices, recompute stop_trigger_px, update D1 | ⚠️ Not defined in UC | ⚠️ Not defined in UC | `{botId, attemptId, hedgeLegId}` | Normal |
| 3 | `partial_repair` queue | Enqueued by Reconcile Worker on partial fill (A4) | Repair Worker: fetch HL, compute remaining delta, resubmit; max 3 attempts → bot_safe_close | ⚠️ Not defined in UC (in spec FR-EXBOT-036) | 3 (spec FR-EXBOT-036) | `message_id` (UNIQUE conflict → skip) | Normal |
| 4 | Notification queue | Enqueued on A3 HL rejection | Investor alert delivery | ⚠️ Not defined in UC | ⚠️ Not defined in UC | ⚠️ Not defined | ⚠️ Not defined |

**Durable Objects:**

| # | DO ID | State Owned | Lease Duration | Expiry Action | Contention Policy |
|---|---|---|---|---|---|
| 5 | `UserLockDO` | Per-user HL mutation lock; `holderToken`, `idempotencyKey` | 90s (TTL); heartbeat() at 30s if work continues (FR-EXBOT-026) | Auto-release after 90s; next worker reconciles before mutation | `acquired=false` returned to caller; worker re-queues with delay |

**HL API Calls:**

| # | HL Method | Direction | Payload | Response | Notes |
|---|---|---|---|---|---|
| 6 | `clearinghouseState` | Worker → HL | `{botId / user}` | Actual short position (size, entry_price, liq_price, eff_leverage) | weight=2; called twice: step 4 (pre-order) + step 11 (reconcile) |
| 7 | `adjustShortDelta(delta, cloid)` | Worker → HL | `delta` (BigDecimal), deterministic `cloid` | Fill confirmation or rejection | Delta-only; cloid = `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` |

**D1 Tables:**

| # | Table | Operation | Fields | Notes |
|---|---|---|---|---|
| 8 | `queue_idempotency` | INSERT (started) + UPDATE (succeeded) | `message_id`, `state` | UNIQUE conflict → skip (idempotency guard) |
| 9 | `bots` / `bot_runtime_state` | READ `state_version`; WRITE `last_known_hl_short_size` | `state_version`, `last_known_hl_short_size` | Read before lock; write after reconcile |
| 10 | `hedge_legs` | WRITE | `stop_price`, `entry_price`, `effective_leverage`, `stop_replacing_started_at`, `stop_cloid`, `stop_order_id`, `stop_size`, `stop_distance_pct` | Written by Reconcile Worker |
| 11 | `rebalance_attempts` | INSERT | `status` (success / failed / skipped), `reason` (CSV) | Status recorded only after reconcile (FR-EXBOT-025) |
| 12 | `circuit_breakers` | WRITE | `failure_count`, `state` | On A3: incrementCircuitBreaker |

---

## 5. System State Model

**Lifecycle State Transitions:**

| From State | Trigger Event | Guard Condition | To State | On Guard Fail |
|---|---|---|---|---|
| `active` | `hedge-sync` message received | `circuit_breakers.state IN ('closed','half_open')` | Remains `active` (no lifecycle state change in happy path) | If `state='open'`: suppress (⚠️ behavior not defined in UC — W4 gap) |
| `active` | `hedge-sync` message received | `stateVersion` in message = D1 `state_version` | Proceeds to lock acquisition | Mismatch → discard (A2), `rebalance_attempts.status='skipped'` |
| Any | `stop_replacing_started_at` stuck >60s detected by light-check | Light-check detects overrun | `safe_mode` | — (A5, handled by separate UC) |

**DO Behavior:**

| DO ID | State Owned | Lease Duration | On Lease Expiry | On Contention |
|---|---|---|---|---|
| `UserLockDO` | Per-user HL mutation lock | 90s; heartbeat() callable at 30s if work continues | Auto-release; next worker reconciles before any new mutation | `acquired=false` → Hedge-Sync Worker re-queues message with delay (A1) |

**Queue Behavior:**

| Queue ID | DLQ After N Retries | Backoff | Idempotency Key | Priority | SLA |
|---|---|---|---|---|---|
| `hedge-sync` | ⚠️ Not defined | ⚠️ Not defined | `message_id` (queue_idempotency UNIQUE) | Normal | ⚠️ Not defined |
| `reconcile` | ⚠️ Not defined | ⚠️ Not defined | `{botId, attemptId, hedgeLegId}` | Normal | ⚠️ Not defined |
| `partial_repair` | 3 retries → `bot_safe_close` (FR-EXBOT-036) | ⚠️ Not defined in UC | `message_id` (UNIQUE) | Normal | ⚠️ Not defined |
| Notification | ⚠️ Not defined | ⚠️ Not defined | ⚠️ Not defined | ⚠️ Not defined | ⚠️ Not defined |

---

## 6. Functional Logic & Workflow Decomposition

### 6.1 Main Success Flow (Delta-Only Hedge Adjustment)

| Step | Actor | Action | FR Ref | Notes |
|---|---|---|---|---|
| 1 | Hedge-Sync Worker | Insert `message_id` into `queue_idempotency` (state=started); UNIQUE conflict → skip | FR-EXBOT-022 | Idempotency guard |
| 2 | Hedge-Sync Worker | Read D1 `bots.state_version`; compare with msg `stateVersion`; mismatch → A2 | FR-EXBOT-027 | Optimistic concurrency check (before lock) |
| 3 | Hedge-Sync Worker | Call `UserLockDO.acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})`; `acquired=false` → A1 | FR-EXBOT-026 | ⚠️ heartbeat() at 30s NOT listed in UC steps — gap W1 |
| 4 | Hedge-Sync Worker | Fetch actual HL position via `clearinghouseState` (weight=2) | FR-EXBOT-021 | Gets actual short size, entry_price, liq_price, eff_leverage |
| 5 | Hedge-Sync Worker | Compute `delta = BigDecimal(targetShortEth).sub(actualShortEth)` | FR-EXBOT-020, FR-EXBOT-021 | BigDecimal only; float FORBIDDEN |
| 6 | Hedge-Sync Worker | Submit `adjustShortDelta(delta, cloid)` to HL; rejection → A3 | FR-EXBOT-020, FR-EXBOT-024 | Delta-only; full close/open FORBIDDEN (BR-EXBOT-004) |
| 7 | Hedge-Sync Worker | Enqueue `reconcile` message: `{botId, attemptId, expectedAbsSize, hedgeLegId}` | FR-EXBOT-025 | Triggers async reconcile flow |
| 8 | Hedge-Sync Worker | Execute stop replacement via INV-STOP protocol (§19.5): set `stop_replacing_started_at` | FR-EXBOT-035 | ⚠️ Path (a) vs (b) unconfirmed — blocked by NV-3 (B1) |
| 9 | Hedge-Sync Worker | Clear `stop_replacing_started_at` in `finally` block | FR-EXBOT-035 | Must clear even on error |
| 10 | Hedge-Sync Worker | `UserLockDO.release(holderToken, idempotencyKey, result)` | FR-EXBOT-026 | In `finally` block |
| 11 | Reconcile Worker | Fetch actual HL position via `clearinghouseState`; verify size = `expectedAbsSize`; mismatch → A4 | FR-EXBOT-025 | Second HL fetch (post-fill) |
| 12 | Reconcile Worker | Extract `entry_price`, `liquidation_price`, `effective_leverage` from response | FR-EXBOT-025 | |
| 13 | Reconcile Worker | Recompute `stop_trigger_px` (BigDecimal): `entry_price × (1 + liq_distance_pct × 0.70)`; record `stop_cloid`, `stop_price`, `stop_size`, `stop_distance_pct` in `hedge_legs` | FR-EXBOT-030 | BigDecimal only |
| 14 | Reconcile Worker | Update `bot_runtime_state.last_known_hl_short_size = reconciled_size` | FR-EXBOT-025 | |
| 15 | Reconcile Worker | Insert `rebalance_attempts` row (status='success') | — | Success recorded AFTER reconcile |
| 16 | Hedge-Sync Worker | Update `queue_idempotency.state='succeeded'` | FR-EXBOT-022 | Terminal idempotency state |

**Business Rules (verbatim):**

| Rule | Verbatim Text (spec.md §8) |
|---|---|
| BR-EXBOT-004 | "Delta-only hedge adjustment is the invariant default. Full close → open in normal hedge-sync is a bug." (P0) |
| BR-EXBOT-010 | "ExBot Worker (`apps/bnza-exbot/`) must not be co-deployed with OPERATOR (`apps/bnza-operator/`). They communicate via CF service binding only." (P0) |

### 6.2 Alternate Flows

| ID | Trigger | Resolution |
|---|---|---|
| A1 (lock held) | Step 3: `UserLockDO.acquired=false` | Re-queue `hedge-sync` message with delay; no HL order; no D1 mutation |
| A2 (stateVersion mismatch) | Step 2: D1 `state_version` ≠ msg `stateVersion` | Discard message; `rebalance_attempts.status='skipped'`; `queue_idempotency.state='succeeded'`; no HL order |
| A3 (HL order rejection) | Step 6: HL rejects `adjustShortDelta` | `rebalance_attempts.status='failed'`; `incrementCircuitBreaker(hedge_leg_id)`; enqueue notification; ⚠️ resulting bot lifecycle state NOT defined (W2) |
| A4 (partial fill) | Step 11: reconciled size ≠ `expectedAbsSize` | Enqueue `partial_repair` message; partial state recorded in D1 |
| A5 (stop_replacing_started_at stuck >60s) | Detected by light-check | Enter SAFE_MODE; handled by separate deep-audit UC |

---

## 7. Functional Integration Analysis

| Trigger / Event | Cross-Operation Impact | Data Consistency Verification |
|---|---|---|
| `adjustShortDelta` submitted (Step 6) | INV-STOP stop replacement (Steps 8-9) must run in same invocation; `stop_replacing_started_at` set before cancel/replace; cleared in `finally` | ⚠️ NV-3 blocker: §19.5 path (a) place-before-cancel vs path (b) cancel-then-place unconfirmed — test cannot be written until confirmed |
| `reconcile` enqueued (Step 7) | Reconcile Worker runs async; `hedge_legs` and `bot_runtime_state` updated after fill confirmed | Two separate HL fetches (weight=2 each): pre-order (step 4) and post-fill (step 11) — total weight=4 per hedge-sync cycle; must not exceed `HLRateLimitDO` 800wt/min budget |
| A3 HL rejection | `circuit_breakers.failure_count` incremented; after 3 consecutive → `state='open'` (FR-EXBOT-040) | ⚠️ UC does not define behavior when hedge-sync arrives during `state='open'` — tester cannot write circuit-open suppression test (W4/W5) |
| A4 partial fill | `partial_repair` enqueued; up to 3 retries using incremented `version` in cloid | After 3 failures: `close_operations` row created → `bot_safe_close` initiated (FR-EXBOT-036, P1) |
| `targetShortEth` derivation | `targetShortEth = lpEthAmount × hedgeRatio (0.70 Phase A)`; `lpEthAmount` depends on `wethIndex` per-chain | NV-12: `wethIndex` for Base+OP unconfirmed (OQ-EXBOT-03) — upstream dependency; hedge-sync itself doesn't call LP contracts but receives `targetShortEth` from upstream |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then |
|---|---|---|---|---|
| AC-01 | Happy path — delta-only adjustment | `hedge-sync` msg with valid stateVersion; `circuit_breakers.state='closed'`; `status='active'` | Worker processes message | Delta-only `adjustShortDelta` submitted; reconcile confirms size; `stop_trigger_px` recomputed; `rebalance_attempts.status='success'`; `stop_replacing_started_at=NULL` |
| AC-02 | stateVersion mismatch | `hedge-sync` msg `stateVersion=5`; D1 `state_version=6` | Worker checks stateVersion before lock | Message discarded; `status='skipped'`; no HL order; `acquired` never called on `UserLockDO` |
| AC-03 | Lock not acquired | Another hedge-sync worker holds `UserLockDO` lease for same user | Worker calls `UserLockDO.acquire` | `acquired=false`; message re-queued with delay; no HL order |
| AC-04 | HL order rejection | Worker submits `adjustShortDelta`; HL returns rejection | HL rejects order | `rebalance_attempts.status='failed'`; `incrementCircuitBreaker` called; notification enqueued; after 3 consecutive failures: `circuit_breakers.state='open'` |
| AC-05 | Cloid determinism | Same `{botId, attemptId, stage, version}` submitted twice | Worker submits delta twice | Same cloid produced; HL deduplicates or 2nd submission skipped after reconcile |
| AC-06 | Reconcile before success | HL fill received | Worker runs post-order reconcile | `rebalance_attempts.status='success'` NOT written before `clearinghouseState` confirms actual size |
| AC-07 | Single-writer lock | Two hedge-sync messages for same user arrive concurrently | Both workers call `UserLockDO.acquire` | Only one proceeds; second gets `acquired=false`; re-queues |
| AC-08 | INV-STOP invariant | Worker resizes delta position | Stop replacement triggered | `stop_replacing_started_at` set before replacement; cleared in `finally`; never NULL during replacement; ⚠️ **BLOCKED: path (a)/(b) unconfirmed — NV-3** |
| AC-09 | Partial fill | Reconcile detects actual size ≠ expected | Reconcile Worker finds mismatch | `partial_repair` message enqueued within same invocation |
| AC-10 | Partial repair cap | `partial_repair` fails 3 times | 3rd failure recorded | `close_operations` row created; `bot_safe_close` initiated (FR-EXBOT-036) |
| AC-11 | Circuit breaker reset | `circuit_breakers.state='half_open'`; probe hedge-sync submitted | Probe succeeds | `state → 'closed'`; `half_open_probe_used` reset |

---

## 9. Non-functional Requirements

| Category | Requirement | Source |
|---|---|---|
| Precision | All delta and stop price computations must use BigDecimal; float/Number FORBIDDEN | FR-EXBOT-020, FR-EXBOT-030 |
| Idempotency | `queue_idempotency` UNIQUE on `message_id`; cloid deterministic per `{botId, attemptId, stage, version}` | FR-EXBOT-022, FR-EXBOT-024 |
| HL Rate Limits | Each hedge-sync cycle consumes weight=4 (2 clearinghouseState calls); must not exceed HLRateLimitDO 800wt/min budget | FR-EXBOT-026 (via DO); spec.md rate limit constraints |
| Concurrency | `UserLockDO` TTL=90s; heartbeat() at 30s; single writer per user at any time | FR-EXBOT-026 |
| SAFE_MODE fence | No hedge-sync mutation allowed when `lifecycle_state='safe_mode'` | FR-EXBOT-050 |
| ⚠️ Latency SLA | No hedge-sync latency SLA defined in UC | — |
| ⚠️ Security | No security NFR for `holderToken` storage/transmission defined in UC | — |

---

## 10. Open Questions & Dependencies

### 10.1 Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | NV-3; OQ-EXBOT-02 | Does HL support place-before-cancel stop replacement (§19.5 path a)? Or must system use cancel-then-place (path b)? | INV-STOP protocol path unconfirmed; stop-replacement AC-08 cannot be written | Open |
| Q2 | H | NV-13; OQ-EXBOT-04 | HL ETH-USD perp minimum order size and dust handling threshold? | Blocks minimum delta threshold for FR-EXBOT-022; sub-minimum delta behavior undefined | Open |
| Q3 | H | uc-hedge-sync.md §3 Step 3 | UC omits heartbeat() call when work exceeds 30s (required by FR-EXBOT-026). Is heartbeat required in hedge-sync? Under what condition is it triggered? | Tester cannot verify lease renewal under slow HL response | Open |
| Q4 | M | uc-hedge-sync.md §4 A3 | What is the resulting bot lifecycle state after HL rejection + circuit breaker increment? Does bot remain 'active'? | AC-04 cannot verify final state without this | Open |
| Q5 | M | uc-hedge-sync.md §3 | What happens when a `hedge-sync` message arrives while `circuit_breakers.state='open'`? Discarded? Dropped to DLQ? | Circuit-open suppression path undefined | Open |
| Q6 | M | uc-hedge-sync.md §3/§4 | DLQ policy for `hedge-sync`, `reconcile`, `partial_repair` queues — retry count, backoff, DLQ destination? | Without DLQ policy, queue-failure test cases are undefined | Open |
| Q7 | L | spec.md §9 vs uc-hedge-sync.md §7 | FR trace mismatch: UC §7 lists FR-022/024/025/026/027/036; spec.md §9 lists FR-020/021/022/024/025/026/027/035. Which is authoritative for this UC? | FR-020/021 (delta-only mandate, position calc) missing from UC trace; FR-036 is P1 | Open |
| Q8 | H | NV-12; OQ-EXBOT-03 | `wethIndex` confirmed values for Base+OP? (NV-12) | `targetShortEth` derives from `lpEthAmount` which depends on correct wethIndex; indirect upstream dependency | Open |

### 10.2 Dependencies

| Dependency | Type | Notes |
|---|---|---|
| NV-3 confirmed (OQ-EXBOT-02) | External verification | INV-STOP §19.5 protocol path (a)/(b) — blocks AC-08 and stop-replacement tests |
| NV-13 confirmed (OQ-EXBOT-04) | External verification | HL min order size — blocks minimum delta threshold test |
| `UC-EXBOT-bot-start` | Upstream UC | Provides bot in `active` state with `hedge_legs` and initial `stop_trigger_px` |
| `UC-EXBOT-light-check` | Trigger source | Light-check evaluates `drift_threshold` and enqueues `hedge-sync` messages |
| `UC-EXBOT-bot-safe-close` | Downstream UC | Invoked after 3 partial-repair failures (FR-EXBOT-036) |

---

## 11. Change Log

| Version | Date | Author | Summary |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read (run-20260617-090000-udemysen) | Initial first-audit review |

---

## Audit Summary

### Score Breakdown

| # | Knowledge Area | Max | Score | Status |
|---|---|---|---|---|
| 1 | Feature Identity | 5 | 5 | ✅ Clear |
| 2 | Objective & Scope | 5 | 3 | ⚠️ Partial |
| 3 | Actors & User Roles | 10 | 10 | ✅ Clear |
| 4 | Preconditions & Postconditions | 10 | 7 | ⚠️ Partial |
| 5 | API/Queue/State Interface Inventory | 15 | 8 | ⚠️ AUTO-CAP (§2 absent) |
| 6 | System State Model | 20 | 12 | ⚠️ Partial |
| 7 | Functional Logic & Workflow | 20 | 15 | ⚠️ Partial |
| 8 | Functional Integration Analysis | 20 | 12 | ⚠️ Partial |
| 9 | Acceptance Criteria | 20 | 13 | ⚠️ Partial |
| 10 | NFRs | 5 | 3 | ⚠️ Partial |
| **TOTAL** | | **130** | **88** | |

**Raw: 88/130 → Final: 67.7/100 → ❌ NOT READY**

### Blockers (must resolve before test design)

| ID | Description |
|---|---|
| B1 | NV-3 (OQ-EXBOT-02): INV-STOP §19.5 path (a) vs (b) unconfirmed — blocks all stop-replacement test cases |
| B2 | NV-13 (OQ-EXBOT-04): HL ETH-USD perp minimum order size unconfirmed — blocks minimum delta threshold validation |

### Strengths

- delta-only mandate and BigDecimal precision requirements are explicit and fully traced to FR-EXBOT-020/021
- cloid determinism (FR-EXBOT-024) enables reliable HL deduplication testing
- UserLockDO concurrency model (FR-EXBOT-026) fully defined: TTL, contention, release-in-finally
- stateVersion optimistic concurrency (FR-EXBOT-027) is a clean, testable guard
- 4 well-formed Gherkin ACs in US-006 provide immediate happy/negative path coverage
- `queue_idempotency` UNIQUE constraint mechanism is explicit

### Testability (clear areas)

- Happy path delta-only adjustment (AC-01): fully testable once environment is ready
- stateVersion mismatch discard (AC-02): testable without NV-3
- Lock contention (AC-03): testable with 2 concurrent workers
- HL rejection + circuit breaker increment (AC-04): testable; final lifecycle state needs BA confirmation (Q4)
- Cloid determinism (AC-05): testable via replay
- Post-order reconcile before success (AC-06): testable
- Partial fill → partial_repair enqueue (AC-09): testable

### Recommendation

**DO NOT begin test design.** Two critical blockers (NV-3, NV-13) prevent stop-replacement and minimum-delta test cases. Additionally, the UC §2 (API/Queue/State Interface) is absent — testers have no official schema reference. Recommend:
1. BA to confirm NV-3 (OQ-EXBOT-02) and NV-13 (OQ-EXBOT-04) as P0 before test design
2. BA to add UC §2 in next revision (heartbeat step, DLQ policies, circuit-open suppression)
3. After NV confirmation: re-audit score is expected to reach 75–80/100 (CONDITIONALLY READY)

### 📋 Unified Gap & Question Report

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | NV-3; OQ-EXBOT-02 | Does HL support place-before-cancel stop replacement (§19.5 path a)? Or cancel-then-place (path b)? | Blocks all stop-replacement AC; INV-STOP path unconfirmed | Open |
| Q2 | H | NV-13; OQ-EXBOT-04 | HL ETH-USD perp minimum order size and dust threshold? | Blocks minimum delta threshold; FR-EXBOT-022 implementation unverifiable | Open |
| Q3 | H | uc-hedge-sync.md §3 Step 3 | Is heartbeat() required in hedge-sync when work exceeds 30s? Under what condition? | Lease renewal path untestable | Open |
| Q4 | M | uc-hedge-sync.md §4 A3 | Bot lifecycle state after HL rejection + circuit breaker increment? | AC-04 cannot verify final state | Open |
| Q5 | M | uc-hedge-sync.md §3 | Behavior when `hedge-sync` arrives while `circuit_breakers.state='open'`? | Circuit-open suppression path undefined | Open |
| Q6 | M | uc-hedge-sync.md §3/§4 | DLQ policy for hedge-sync, reconcile, partial_repair queues? | Queue-failure tests undefined | Open |
| Q7 | L | spec.md §9 vs uc-hedge-sync.md §7 | FR trace mismatch (UC lists FR-036; spec §9 lists FR-020/021/035) — which is authoritative? | Traceability gap | Open |
| Q8 | H | NV-12; OQ-EXBOT-03 | `wethIndex` for Base+OP confirmed? | Upstream dependency for targetShortEth | Open |
