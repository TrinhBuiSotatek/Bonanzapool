---
type: srs
status: draft
created: 2026-06-12
updated: 2026-06-20
owner: "@hienduong"
module: exbot
lang: en
links:
  - ../frd.md
  - ../../02_backbone/backbone.md
  - ../usecases/index.md
  - ../userstories/index.md
changelog:
  - 2026-06-20 | /ba-do | QC audit fixes: OQ-EXBOT-13/14/15/16/17 added to §9
  - 2026-06-18 | /ba-do hld-decisions | FR-070/071/073 update: drop park/re-entry; IC-EXBOT-002 remove uninvestedBalanceOf stub; scope FM-XB-08 update; us-012 emergency authority
  - 2026-06-12 | /ba-impact | §9 add OQ-EXBOT-10/11/12: range_boundary_near formula, lpValueUsd computation, 7d APR aggregation — all pending zen confirm
  - 2026-06-12 | /ba-impact | gap fill v5.2.6: FR-012 add stop_replacing_started_at primary detection + uniPoolPrice 3-way split note; FR-033 add primary light-check detection (≤5min) vs deep-audit secondary backstop
  - 2026-06-12 | /ba-start srs --update | gap fill: added FR-015,016,036,072,073,082,083,091,092,093; section 10 Integration Constraints; fixed UC inventory traces
  - 2026-06-12 | /ba-start srs | initial SRS authored from FRD + use cases + user stories
---

# SRS: BNZA-EXBOT Infrastructure (Module 4)

> **Trace:** FM-XB-01 → FM-XB-08 (Feature Map §5.4)
> **Architecture:** Standalone Cloudflare Worker (`apps/bnza-exbot/`) — NOT co-deployed with OPERATOR
> **Entry point:** OPERATOR Facade `/api/exbot/*` → CF service binding → ExBot Worker (internal token)
> **Source truth:** SPEC v5.2.6 (zen-approved). Where this SRS conflicts with SPEC v5.2.6, SPEC prevails.

---

## 1. Introduction

### 1.1 Scope

BNZA-EXBOT is the backend infrastructure for a managed delta-hedged LP Bot. SOTATEK builds infrastructure only — trading strategy logic (PositionCalc, hedge math, stop safety factor tuning) is zen-proprietary. ExBot Worker runs as a standalone Cloudflare Worker, separate from OPERATOR. The OPERATOR acts as a thin public-facing facade that proxies `start/status/close/agent-key/margin` to ExBot via CF service binding.

This SRS covers FM-XB-01 through FM-XB-08 for Phase A (1–100 bots, Base + Optimism dual-chain).

### 1.2 In Scope

| Feature Map ID | Feature | Priority |
|---|---|---|
| FM-XB-01 | D1 Schema (control_db + state_db_shard) | P0 |
| FM-XB-02 | Queue Topology (10 queues) | P0 |
| FM-XB-03 | Durable Objects (HLRateLimitDO, UserLockDO, MarketDataDO) | P0 |
| FM-XB-04 | Cron Jobs (deep-audit, metrics-rollup, stop-integrity scan) | P1 |
| FM-XB-05 | HL Adapter (rate limit, cloid, delta-only, reconcile, agent key decrypt) | P1 |
| FM-XB-06 | Operator Facade API (`/api/exbot/*` — 5 endpoints) | P1 |
| FM-XB-07 | Lifecycle State Machine (18 states) | P0 |
| FM-XB-08 | Close/Redeem Operations (user_redeem + bot_safe_close via RedemptionQueue FIFO — park/redeploy dropped HLD 2026-06-18) | P0 |

### 1.3 Out of Scope

- Trading strategy logic (PositionCalc, hedge math formula, stop safety factor tuning) — zen-proprietary
- BnzaExVault Solidity contract development — zen scope; SOTATEK integrates via ABI
- Phase 0 verification tasks (NV-1 to NV-14) — zen/SOTATEK verification tasks
- Backtest module (separate module)
- POOL UI changes for ExBot tab — POOL module scope
- Phase B+ features (multi-bot per user, D1 sharding >1 shard, R2 archive, Analytics Engine)

### 1.4 Related Artifacts

| Artifact | Path |
|---|---|
| FRD | `../frd.md` |
| Use Cases | `../usecases/index.md` |
| User Stories | `../userstories/index.md` |
| System Flows | `srs/flows.md` |
| State Diagrams | `srs/states.md` |
| ERD | `srs/erd.md` |

---

## 2. Functional Requirements

### FR-EXBOT-001 — One-Bot-Per-User Policy (Phase A)
**Trace:** FM-XB-07, UC-EXBOT-bot-start, US-EXBOT-001
**Priority:** P0

The system shall enforce a maximum of one active ExBot per user in Phase A. Before creating a new bot, the system shall query `bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')`. If the count is greater than zero, the start request shall be rejected immediately with a specific error message.

**Acceptance criteria:** Start request with an existing active bot returns error "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." No bot record is created on rejection.

---

### FR-EXBOT-002 — Bot Start Preflight Checks
**Trace:** FM-XB-07, UC-EXBOT-bot-start, US-EXBOT-001
**Priority:** P0

The system shall run five preflight checks in sequence before creating a bot record: (1) one-bot policy check, (2) HL isolated margin balance ≥ required margin × 2.0, (3) HL agent key `approval_status='approved'` and `expires_at` not reached, (4) builder fee (5bps) confirmed on HL, (5) LP mint simulation passes. Any single failure blocks the start with a specific message identifying the failed check.

**Acceptance criteria:** Insufficient margin returns "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." Agent key pending returns message directing user to complete key approval. Each check failure produces a distinct error; no partial bot record is left in D1.

---

### FR-EXBOT-003 — Bot Lifecycle State Tracking
**Trace:** FM-XB-07, US-EXBOT-001
**Priority:** P0

The system shall track bot state using two fields: `bots.status` (coarse-grained: active/paused/closing/closed/safe_mode/error) and `bots.lifecycle_state` (fine-grained: 18 canonical values). The initialization sequence is fixed: idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active. No step may be skipped.

**Acceptance criteria:** A bot that completes initialization has `lifecycle_state='active'` and `status='active'`. Each transition is persisted atomically to D1 before proceeding to the next step.

---

### FR-EXBOT-004 — Dual-Chain Support (Base + Optimism)
**Trace:** FM-XB-07, US-EXBOT-001
**Priority:** P0

The system shall support Base and Optimism from Phase 1. `wethIndex` (0 or 1, indicating whether WETH is token0 or token1 in the pool) shall be verified per chain and stored in `positions.weth_index` at LP open. The hedge leg (HL ETH-USD perpetual short) is chain-independent; dual-chain impact is LP side only.

**Acceptance criteria:** A bot on Base and a bot on Optimism can run simultaneously under different users. `weth_index` is populated correctly for each chain; LP ETH amount calculation uses `weth_index` from D1, not a hardcoded assumption.

---

### FR-EXBOT-005 — Pause / Resume Bot
**Trace:** FM-XB-07, US-EXBOT-003
**Priority:** P1

The system shall support pausing a bot by setting `bots.status='paused'` while leaving `lifecycle_state` at its pre-pause value. The existing HL short and LP NFT shall remain intact during pause. Light-check and hedge-sync shall be suppressed for paused bots. Deep-audit shall continue every 6 hours during pause.

**Acceptance criteria:** Paused bot shows status "Paused — hedge is maintained, LP is maintained" in the Operator API status response. Resume restores `status='active'` and schedules the next light-check within 5 minutes.

---

### FR-EXBOT-010 — Queue Topology (10 Queues)
**Trace:** FM-XB-02, US-EXBOT-005
**Priority:** P0

The system shall implement exactly 10 queues: `bot-scan`, `light-check`, `hedge-sync`, `reconcile`, `deep-audit`, `price-near-stop-audit`, `partial_repair`, `user_redeem` (highest priority, SLA 5 min), `notification`, `metrics-rollup`. All queue `sendBatch` calls shall go through the `chunkSendBatch()` helper (max 100 messages per call). Direct `queue.sendBatch()` without the helper is forbidden.

**Acceptance criteria:** No producer calls `sendBatch` directly. Batch sizes exceeding 100 are chunked automatically. Dead-letter queue receives poison messages from any consumer.

---

### FR-EXBOT-011 — Queue Consumer Idempotency
**Trace:** FM-XB-02, US-EXBOT-006
**Priority:** P0

Every queue consumer shall insert `message_id` with `state='started'` into the `queue_idempotency` table at the start of processing. A UNIQUE constraint conflict on `message_id` indicates duplicate delivery; the consumer shall return immediately without processing. On completion, the consumer updates `state='succeeded'`; on failure, `state='failed'` or `'retryable'`.

**Acceptance criteria:** Redelivering the same queue message twice produces exactly one successful execution. The second delivery exits immediately after the UNIQUE constraint conflict. `queue_idempotency` row is present for every processed message.

---

### FR-EXBOT-012 — Light-Check (Zero HL API Calls)
**Trace:** FM-XB-02, US-EXBOT-005
**Priority:** P0

The light-check worker shall evaluate each active bot's rebalance need using only D1 `bot_runtime_state`, `MarketDataDO` (sqrtPriceX96, currentTick), and local TickMath computation. No Hyperliquid API calls are permitted in light-check (HL weight = 0). The worker shall evaluate the canonical `RebalanceReason[]` enum and enqueue `hedge-sync` when rebalance is needed and `circuit_breakers.state != 'open'`. Light-check shall be skipped entirely for bots with `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'`.

In addition to rebalance evaluation, each light-check pass shall:
1. Check `stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60s` — if true, enqueue `partial_repair` with `reason='stop_replacing_overrun'` and enter SAFE_MODE (primary detection, ≤5 min; see FR-EXBOT-033).
2. Use `uniPoolPrice` (Uniswap V3 pool slot0 `sqrtPriceX96`, sourced from `MarketDataDO`) when computing `deltaErrorUsd` for drift threshold evaluation. `hlMarkPrice` is used only for stop trigger detection (`markPrice >= stop_price`). `hlOraclePrice` is used only for margin calculations. These three price sources must not be interchanged (v5.2.6 X-5 3-way price split).

**Acceptance criteria:** A 10,000-bot light-check cycle does not consume any HL API rate limit weight. Any HL fetch introduced into light-check is an architectural violation flagged by code review. `deltaErrorUsd` computation uses pool slot0 price, not HL mark or oracle price.

---

### FR-EXBOT-013 — Light-Check Jitter
**Trace:** FM-XB-02
**Priority:** P0

`next_light_check_at` shall be set to `now + 5min + random(−45s, +45s)`. The jitter is computed per-bot as a value, but the D1 write is batched (1 UPDATE statement per shard, not a per-bot individual write).

**Acceptance criteria:** No D1 per-bot write for `next_light_check_at`. Bot scan shows even distribution of check times across the 5-minute window.

---

### FR-EXBOT-014 — Stop Monitoring Always Active
**Trace:** FM-XB-02, US-EXBOT-008
**Priority:** P0

Stop monitoring (`price-near-stop-audit` enqueue) shall continue at all times — including when `circuit_breakers.state='open'`. Light-check shall suppress `hedge-sync` when circuit is open, but shall never suppress stop price evaluation or `price-near-stop-audit` enqueue.

**Acceptance criteria:** With circuit breaker open, a bot whose `markPrice >= stop_price` still receives a `price-near-stop-audit` message. No `hedge-sync` message is enqueued for that bot.

---

### FR-EXBOT-015 — LP Range Rebalance
**Trace:** FM-XB-07, US-EXBOT-007
**Priority:** P1

When light-check detects `rangeState != 'in'` (range_out condition), the system shall transition `bots.lifecycle_state` to `lp_rebalancing` and enqueue an LP rebalance operation via the `partial_repair` queue. During `lp_rebalancing`, light-check and hedge-sync are suppressed entirely. The rebalance worker shall close the existing LP NFT via `BnzaExVault.redeem(tokenId)`, compute a new tick range, and mint a new LP NFT. All LP operations are tracked in the `lp_operations` ledger with UNIQUE idempotency keys. On success, `lifecycle_state` returns to `active`. On failure after 3 consecutive retries, the system initiates `bot_safe_close` (FR-EXBOT-072).

**Acceptance criteria:** A bot in `lp_rebalancing` produces no `hedge-sync` messages. The `lp_operations` row for each rebalance attempt has a UNIQUE idempotency key. A successful rebalance leaves `lifecycle_state='active'` with an updated `positions` row. Three consecutive LP rebalance failures create a `close_operations` row for `bot_safe_close`.

---

### FR-EXBOT-016 — Deep-Audit Cron
**Trace:** FM-XB-04, US-EXBOT-005
**Priority:** P1

The system shall run a full HL state reconcile for every active and paused bot every 6 hours via the `deep-audit` queue. In high-risk mode (when `circuit_breakers.state != 'closed'` or `margin_status IN ('warning','critical')`), the interval reduces to 1 hour. The deep-audit worker shall: (1) fetch `clearinghouseState` from HL, (2) verify actual short size matches `hedge_legs.last_known_hl_short_size`, (3) detect `stop_trigger_crossed_at` stuck for more than 30 minutes and initiate SAFE_MODE, (4) detect `stop_replacing_started_at` stuck for more than 60 seconds and initiate SAFE_MODE, (5) update `hedge_legs.margin_status` from fresh HL `marginSummary`. Deep-audit continues for paused bots at the 6-hour cadence.

**Acceptance criteria:** `stop_trigger_crossed_at` stuck detection in deep-audit triggers SAFE_MODE entry within one audit cycle. A paused bot is not excluded from deep-audit scheduling. Margin status updated by deep-audit reflects HL `marginSummary` fetched in the same cycle.

---

### FR-EXBOT-020 — LP Position Amount Calculation
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

Hedge size shall be computed from the Uniswap V3 AMM formula using `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, and `currentTick` via TickMath and LiquidityAmounts. Using `depositedToken − withdrawnToken + collectedFees` to approximate LP amount is forbidden.

**Acceptance criteria:** Unit tests cover: in-range, below-lower, above-upper, WETH as token0, WETH as token1, negative tick, zero liquidity, boundary ticks (currentTick == tickLower, currentTick == tickUpper − 1).

---

### FR-EXBOT-021 — Hedge Target Computation (BigDecimal)
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

`targetShortEth = lpEthAmount × hedgeRatio`. All computations shall use BigDecimal; float/number arithmetic is forbidden for any financial value. `target_ratio_bps` normalization shall go through `normalizeTargetRatioBps()` which converts the TEXT ratio (e.g., "0.70") to a bigint in basis points (7000n).

**Acceptance criteria:** `normalizeTargetRatioBps("0.70")` returns 7000n. `Number("0.73") * 10000` is not present in the codebase.

---

### FR-EXBOT-022 — Delta-Only Hedge Adjustment
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

Delta-only adjustment is the default for all hedge-sync operations. Full close → full open is forbidden in normal hedge-sync. The worker shall compute `delta = targetShortEth − actualShortEth` and submit only that delta via `adjustShortDelta`. Full close/open is permitted only for: target size = 0 (bot close path), emergency reset (admin-invoked), or manual reset (Phase B+).

**Acceptance criteria:** A hedge-sync triggered by `drift_threshold` submits only an `adjustShortDelta` call, not a close followed by a new open. Reconcile after the adjustment confirms the new size matches target within tolerance.

---

### FR-EXBOT-023 — Canonical RebalanceReason Enum
**Trace:** FM-XB-05, US-EXBOT-005
**Priority:** P0

Rebalance triggers shall use only the canonical `RebalanceReason[]` enum values: `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile`. No aliases or alternate naming are permitted. `stop_trigger_crossed` is not a `RebalanceReason`; it routes to `price-near-stop-audit`.

**Acceptance criteria:** `rebalance_attempts.reason` column contains only canonical values (CSV for multiple). No variant spellings or custom trigger names appear in D1 or queue messages.

---

### FR-EXBOT-024 — Deterministic Cloid
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

Client order IDs shall be deterministic: `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. The same retry uses the same cloid. A changed payload increments `version`. On duplicate cloid detection, the worker shall reconcile actual HL state before any retry — never blindly resubmit.

**Acceptance criteria:** Submitting the same hedge-sync twice (same `attemptId + stage + version`) produces the same cloid. HL deduplicates or the second submission is detected and skipped after reconcile.

---

### FR-EXBOT-025 — Post-Order Reconcile
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

After every hedge mutation, the worker shall fetch the actual HL position via `clearinghouseState`, verify the size matches expected, extract `entry_price`, `liquidation_price`, and `effective_leverage`, save these to `hedge_legs`, recompute `stop_trigger_px`, and update `bot_runtime_state.last_known_hl_short_size`. Success is recorded in `rebalance_attempts` only after reconcile confirms the actual state.

**Acceptance criteria:** `rebalance_attempts.status='success'` is never written before reconcile. `hedge_legs.entry_price` and `stop_price` are populated after every hedge open or resize.

---

### FR-EXBOT-026 — UserLockDO Lease (Concurrency Control)
**Trace:** FM-XB-03, US-EXBOT-006
**Priority:** P0

Before any Hyperliquid mutation for a given user, the hedge-sync worker shall acquire a lease from `UserLockDO` (TTL=90s, caller-generated `holderToken` UUID). The work runs in the caller, not the DO. If `acquired=false`, the worker re-queues the message with a delay. If work exceeds 30 seconds, the worker extends the lease via `heartbeat()`. The lease is released in a `finally` block.

**Acceptance criteria:** Two hedge-sync workers for the same user cannot run HL mutations concurrently. A lease that expires auto-releases after 90s; the next worker acquires and reconciles before any new mutation.

---

### FR-EXBOT-027 — StateVersion Optimistic Concurrency
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

Before acquiring the `UserLockDO` lease, the hedge-sync worker shall read `bot_runtime_state.state_version` and compare it with the `stateVersion` in the queue message. A mismatch means the state changed since the message was enqueued; the worker shall discard the message (record `rebalance_attempts.status='skipped'`) without submitting any HL order.

**Acceptance criteria:** A stale hedge-sync message (stateVersion < current D1 value) is silently discarded. No HL order is submitted for discarded messages.

---

### FR-EXBOT-030 — Stop Trigger Price Computation
**Trace:** FM-XB-07, US-EXBOT-006
**Priority:** P0

`stop_trigger_px` shall be computed using BigDecimal only. Formula: `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`. `liq_distance_pct = (liquidation_price − entry_price) / entry_price` when HL `liquidationPx` is available; fallback to `1 / effective_leverage` only when unavailable. Phase A `stopSafetyFactor = 0.70`.

**Acceptance criteria:** Stop price calculation uses BigDecimal throughout; no intermediate `Number()` conversion. For a 3x isolated margin position, stop fires before the liquidation price with at least 30% distance buffer.

---

### FR-EXBOT-031 — Stop Placement After Hedge Open
**Trace:** FM-XB-07
**Priority:** P0

After hedge open reconcile, the system shall immediately place a reduce-only stop market on HL with the computed `stop_trigger_px`. The worker shall record `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size`, and `stop_distance_pct` in `hedge_legs`. The bot shall not transition to `stop_verified` until stop placement is confirmed.

**Acceptance criteria:** `hedge_legs.stop_price` is always populated when `lifecycle_state='active'`. A bot without a confirmed stop cannot reach `active` state.

---

### FR-EXBOT-032 — Stop Trigger Detection and Routing
**Trace:** FM-XB-07, US-EXBOT-008
**Priority:** P0

When light-check detects `markPrice >= stop_price`, the worker shall set `hedge_legs.stop_trigger_crossed_at` only if it is currently NULL (guarded write — prevents overwrite on repeated light-checks). It shall enqueue a `price-near-stop-audit` message. It shall NOT enqueue a `hedge-sync` message for this trigger.

**Acceptance criteria:** `stop_trigger_crossed_at` is set exactly once per stop event regardless of how many subsequent light-checks run before the audit resolves it. Stop-audit SLA tracking begins from the first setting of this timestamp.

---

### FR-EXBOT-033 — SAFE_MODE on Stuck Stop Marker
**Trace:** FM-XB-07
**Priority:** P0

If `stop_trigger_crossed_at` is set and more than 30 minutes have elapsed without the stop-audit resolving it, the system shall enter SAFE_MODE.

For `stop_replacing_started_at` overrun, two detection layers exist (v5.2.6 W-5):
- **Primary — light-check (≤5 min):** Each light-check pass shall evaluate `hedge_legs.stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60s`. When true, light-check shall enqueue a `partial_repair` message with `reason='stop_replacing_overrun'` and trigger SAFE_MODE entry. This is the fast path, firing within one 5-minute light-check window.
- **Secondary — deep-audit (backstop):** If the light-check primary detection is missed (e.g. worker abnormal exit before the check runs), the deep-audit shall detect the same condition and trigger SAFE_MODE. Deep-audit cadence is 6 hours normal / 1 hour high-risk.

**Acceptance criteria:** A bot whose `stop_replacing_started_at` is set and older than 60 seconds enters SAFE_MODE within the next light-check cycle (≤5 minutes), not waiting for the next deep-audit. A bot whose stop-audit stalls (`stop_trigger_crossed_at` stuck > 30 min) enters SAFE_MODE within the next deep-audit cycle (at most 6 hours, or 1 hour in high-risk mode).

---

### FR-EXBOT-034 — Stop Cooldown After Stop Fires
**Trace:** FM-XB-07, US-EXBOT-009
**Priority:** P0

After a stop fires and is confirmed, `lifecycle_state` shall transition to `hedge_stopped_cooldown` for 4 hours. During cooldown, hedge-sync is suppressed. After cooldown, the system shall attempt automatic re-hedge. If 3 stops occur within 7 days, the system shall initiate `bot_safe_close` and enter the §16.7 automatic re-entry closed loop.

**Acceptance criteria:** A bot in `hedge_stopped_cooldown` does not enqueue hedge-sync. The re-hedge attempt after 4 hours runs automatically. After 3 stops in 7 days, `close_operations` row is created for `bot_safe_close`.

---

### FR-EXBOT-035 — INV-STOP Protocol for Stop Replacement
**Trace:** FM-XB-07
**Priority:** P0

Stop replacement on hedge resize shall use the INV-STOP protected protocol (§19.5 of SPEC v5.2.6). Direct cancel-then-place without protection is forbidden. `stop_replacing_started_at` shall be set at the start of the replacement critical section and cleared in a `finally` block.

**Acceptance criteria:** No hedge-sync implementation calls `cancelStop` then `placeStop` directly without the protected protocol. `stop_replacing_started_at` is always NULL when no replacement is in progress.

---

### FR-EXBOT-036 — Partial Repair Queue
**Trace:** FM-XB-02, US-EXBOT-006
**Priority:** P1

The `partial_repair` queue handles recovery for two failure classes: (1) hedge-sync partial fill — where a delta order was partially executed and actual size diverges from target; (2) LP rebalance failure (FR-EXBOT-015). The partial-repair worker shall: fetch the actual HL position, compute the remaining delta, and resubmit the delta via `adjustShortDelta` with a new attempt-specific cloid. Repair attempts are capped at 3 per trigger event; after 3 failures the worker initiates `bot_safe_close` (FR-EXBOT-072). Each repair attempt inserts a `queue_idempotency` row with `state='started'` before any HL call; a UNIQUE conflict on `message_id` exits silently.

**Acceptance criteria:** A hedge-sync partial fill that leaves `|actual - target| > drift_threshold` results in a `partial_repair` message within the same worker invocation. Repair retries use distinct cloids (incremented `version`). After 3 failed repair attempts, `close_operations` row is created for `bot_safe_close`. No partial-repair message is processed twice for the same `message_id`.

---

### FR-EXBOT-040 — Circuit Breaker State Machine
**Trace:** FM-XB-07, US-EXBOT-008
**Priority:** P0

The circuit breaker canonical source is `circuit_breakers.state` column (not dynamic computation from history). Transitions: `closed →(3 consecutive failures within 24h)→ open (reset_at = now + 1h)` → `open (reset_at reached) → half_open` → `half_open (probe success) → closed` / `half_open (probe fails) → open (reset_at = now + 1h)`. During `half_open`, exactly one probe hedge-sync is allowed (atomic `half_open_probe_used` 0→1 claim). Circuit resets to `closed` only on success; partial and failed results do not reset.

**Acceptance criteria:** After 3 consecutive hedge-sync failures, `circuit_breakers.state='open'`. After `reset_at` elapses, state transitions to `half_open`. A successful probe transitions to `closed`; a failed probe re-opens with a new `reset_at`.

---

### FR-EXBOT-050 — SAFE_MODE Entry Conditions
**Trace:** FM-XB-07, US-EXBOT-010
**Priority:** P0

The system shall enter SAFE_MODE when any of the following is detected: HL API unreachable for more than 5 minutes; reconcile mismatch (actual size ≠ expected); `margin_status='critical'` twice in a row; `effective_leverage > 4.5`; `liquidation_price` within 5% of current hlMarkPrice; `stop_trigger_crossed_at` stuck > 30 min; `stop_replacing_started_at` stuck > 60s.

In SAFE_MODE the following are forbidden: cancel stops, open positions, rebalance hedge or LP, change leverage, withdraw margin. The following remain allowed: read state, retry HL connectivity, alert user/admin, light-check (non-HL part), deep-audit when HL recovers.

**Acceptance criteria:** A bot in `safe_mode` rejects any hedge-sync or LP rebalance attempt. Stop monitoring continues. Auto-recovery proceeds when HL is responsive + 3 consecutive reconciles succeed + `margin_status='ok'`. If recovery is impossible, `bot_safe_close` is initiated.

---

### FR-EXBOT-060 — Margin Status Thresholds
**Trace:** FM-XB-07, US-EXBOT-010
**Priority:** P0

Margin status is computed as `marginUsage = marginRequiredUsd / marginBalanceUsd` where `marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`. Thresholds: `ok` when marginUsage < 0.55; `warning` when 0.55 ≤ marginUsage < 0.75; `critical` when marginUsage ≥ 0.75.

Margin status shall be updated only during hedge-sync preflight (HL `marginSummary` fetch) and deep-audit. Light-check reads `hedge_legs.margin_status` from D1 only — no HL fetch.

**Acceptance criteria:** `warning` state disables size-increase hedge adjustments and sends investor a UI banner notification. `critical` state (twice in a row) triggers SAFE_MODE and alerts admin. Margin update never occurs during light-check; HL weight in light-check remains 0.

> **Note:** Thresholds (0.55/0.75) are subject to Phase 0 backtest finalization (OQ-EXBOT-06, zen task).

---

### FR-EXBOT-061 — Preflight Margin Check
**Trace:** FM-XB-07, US-EXBOT-001
**Priority:** P0

At bot start preflight, the system shall verify that the user's HL isolated margin balance ≥ `(lpEthAmount × hedgeRatio × hlOraclePrice / leverage) × 2.0`. If insufficient, start is blocked with the required deposit amount displayed.

**Acceptance criteria:** A user with exactly the minimum required margin (no buffer) is blocked. A user with 2.0× the required margin passes. The displayed shortfall is accurate to the nearest dollar.

---

### FR-EXBOT-070 — Two Close Systems (user_redeem + bot_safe_close)
**Trace:** FM-XB-08, US-EXBOT-004, US-EXBOT-009
**Priority:** P0

Two separate close systems exist, both tracked in the `close_operations` ledger with `idempotency_key UNIQUE` to prevent double settlement.

**user_redeem (LP-first):** The on-chain `BnzaExVault.redeem(tokenId)` transaction instantly liquidates the LP and returns the LP-portion USDC to the investor in the same transaction (on-chain guarantee). The worker then closes the HL hedge independently (SLA: 5 minutes from event detection). Hedge close failure results in `residual_hl_liability` state; it never blocks the LP-portion repayment.

**bot_safe_close (hedge-first):** Triggered by system conditions (circuit breaker exhausted, margin critical, 3 stops in 7 days, admin force-close). Order: close HL hedge → executeStrategy(RedeemStrategyV1) → RedemptionQueue.createRequest → Operator fulfillRequest pays user FIFO on-chain. No park/redeploy loop (dropped HLD 2026-06-18).

**Acceptance criteria:** Duplicate `close_operations` row attempt (same `idempotency_key`) is rejected by UNIQUE constraint. LP-portion USDC is returned to investor in the redeem tx regardless of hedge close outcome. `bot_safe_close` funds are returned to user via RedemptionQueue fulfillRequest (on-chain FIFO). No uninvested_balances or uninvestedBalanceOf API used.

---


---

### FR-EXBOT-072 — bot_safe_close Trigger Conditions
**Trace:** FM-XB-08, US-EXBOT-009
**Priority:** P0

The system shall initiate `bot_safe_close` when any of the following conditions is confirmed: (1) circuit breaker exhausted — `circuit_breakers.state='open'` and `reset_at` has been extended 3 or more times without probe success; (2) margin critical — `margin_status='critical'` twice in a row leading to SAFE_MODE with no auto-recovery path; (3) 3 stops within 7 days — `lifecycle_state='hedge_stopped_cooldown'` is entered for the third time within a 7-day rolling window; (4) partial repair exhausted — `partial_repair` consumer fails 3 consecutive repair attempts for the same trigger event; (5) admin force-close — admin invokes `/api/exbot/close` explicitly. All five trigger paths create a `close_operations` row with `trigger_reason` populated and `idempotency_key UNIQUE` enforced.

**Acceptance criteria:** Each trigger condition creates exactly one `close_operations` row (UNIQUE constraint prevents duplicate). `trigger_reason` is populated for all 5 trigger types. A duplicate trigger for the same bot (e.g., two concurrent admin close calls) is rejected by the UNIQUE constraint on `idempotency_key`.

---

### FR-EXBOT-073 — bot_safe_close Execution Sequence
**Trace:** FM-XB-08
**Priority:** P0

The `bot_safe_close` execution follows a fixed hedge-first sequence tracked atomically in `close_operations`: (1) `requested` — trigger received, `close_operations` row created; (2) `hedge_close_pending` — close HL short position fully (target = 0); (3) `hedge_closed` — HL position confirmed closed, stop cancelled; (4) `lp_closed` — call `BnzaExVault.redeem(tokenId)` on-chain, LP NFT burned; (5) `redemption_queued` — RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId) enqueued; RequestCreated event emitted; (6) `done` — Operator calls fulfillRequest(tokens, amounts); FIFO pop; safeTransferFrom(operator, user, amount) on-chain; RequestFulfilled event emitted; bots.status='closed'. On hedge close failure, the system retries up to 3 times before escalating to admin and holding at `hedge_close_pending`. LP close is not attempted until hedge is confirmed closed.

**Acceptance criteria:** `close_operations` state transitions are sequential — no step is skipped. LP close is never attempted before `hedge_closed`. RedemptionQueue request is enqueued at step 5; user funds are returned on-chain when Operator calls fulfillRequest. A failure at any step holds `close_operations.status` at the failed step — does not silently advance.

---

### FR-EXBOT-080 — HL Agent Key Secure Storage
**Trace:** FM-XB-01, US-EXBOT-011
**Priority:** P0

The system shall never store the user's master private key. Only the approved HL agent key (a delegated signing key) is stored, using AES-256-GCM envelope encryption: the key is encrypted with a per-row DEK; the DEK is wrapped with the Master Key (Cloudflare Secrets Store). Stored fields: `encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`.

During decryption (at hedge-sync time), the plain DEK and plain agent key are function-scoped and destroyed immediately after the signing operation. No log entry shall contain the raw key or raw DEK.

**Cloudflare Secrets Store failure handling:**
- *At key submission (wrap DEK):* If Cloudflare Secrets Store is unavailable when wrapping the DEK, the system shall abort the submission and return HTTP 503: "Service temporarily unavailable. Please try again later." No row is inserted into `hl_agent_keys`. The investor may retry after the service recovers.
- *At hedge-sync (unwrap DEK):* If Cloudflare Secrets Store is unavailable when unwrapping the DEK, the hedge-sync worker shall log the error (without exposing key material), abort the signing operation, and transition the bot to SAFE_MODE. Admin is alerted. Recovery follows the standard SAFE_MODE path.

**Acceptance criteria:** A D1 dump of `hl_agent_keys` contains only encrypted blobs — no plaintext key is recoverable without the Master Key. Log audit shows no raw key values. Key rotation inserts a new row (new DEK + wrap); the old row transitions to `status='revoked'`. A submit attempt when Secrets Store is unavailable returns HTTP 503 with no row inserted. A hedge-sync that fails to unwrap DEK due to Secrets Store unavailability enters SAFE_MODE without exposing key material in logs.

---

### FR-EXBOT-081 — Agent Key Approval Flow
**Trace:** FM-XB-01, FM-XB-06, US-EXBOT-011
**Priority:** P0

Newly submitted agent keys have `approval_status='pending'`. The admin approves via the admin dashboard, which calls the Operator Facade `/api/exbot/agent-key` endpoint. Keys with `approval_status='pending'` or `approval_status='revoked'` shall be rejected at preflight. Keys where `expires_at < now` shall be rejected at preflight with a message directing the user to submit a new key.

**Submit constraint:** An investor may only submit a new agent key when their current key has `approval_status='expired'` or `approval_status='revoked'`. Submission while a key is `pending` returns E-EXBOT-014. Submission while a key is `approved` returns E-EXBOT-015.

**Approval audit:** When admin approves a key, ExBot Worker sets `approved_at=now` and `approved_by=<admin_user_id>` on the row. This provides a full audit trail of which admin performed the approval.

**Approval expiry check:** Before committing an approval, ExBot Worker shall validate that `expires_at >= now`. If the key has already expired at the time of admin approval, the approval is rejected with E-EXBOT-016: "This agent key has already expired and cannot be approved. Please ask the investor to submit a new key." The row remains `approval_status='pending'` unchanged.

**Approval SLA:** No SLA is defined for the `pending → approved` transition. Key approval is a manual admin action with no time constraint. There is no system-enforced timeout or escalation for pending keys awaiting approval.

**Acceptance criteria:** A bot start with a pending or expired agent key is blocked with a specific message. A bot start with an approved, non-expired key passes the agent key check. A submit attempt while a `pending` key exists is rejected with E-EXBOT-014. A submit attempt while an `approved` key exists is rejected with E-EXBOT-015. An approved key row always has both `approved_at` and `approved_by` populated. An approve attempt on a key where `expires_at < now` is rejected with E-EXBOT-016 and the row remains `pending`.

---

### FR-EXBOT-082 — Agent Key Revocation
**Trace:** FM-XB-01
**Priority:** P0

Key revocation shall be non-destructive. When a key is revoked (by user request or admin action), the existing `hl_agent_keys` row transitions `approval_status='revoked'` and `revoked_at = now`. A new key submission inserts a new row with a fresh per-row DEK and wrap — the old row is never overwritten or deleted. Only one key per user may have `approval_status='approved'` at any time; the system enforces this at the database level. After revocation, any in-flight hedge-sync that attempts to decrypt the old key shall receive a decryption failure, log the error, and enter SAFE_MODE.

**Acceptance criteria:** `hl_agent_keys` table never has two `approved` rows for the same user. A hedge-sync that decrypts a `revoked` key fails safely and enters SAFE_MODE without exposing key material in logs. Revoked rows remain in D1 for audit purposes — `DELETE` of revoked rows is forbidden.

---

### FR-EXBOT-083 — Agent Key Expiry Handling
**Trace:** FM-XB-01, FM-XB-06
**Priority:** P0

**Background:** Hyperliquid does not assign an expiry date when an agent key is created — HL agent keys are valid indefinitely on the HL protocol level until explicitly deregistered. The `expires_at` field is therefore set by the ExBot system at application level to enforce periodic key rotation as a security best practice.

**Expiry assignment rule:** When an investor submits an agent key, ExBot Worker shall automatically set `expires_at = submitted_at + 90 days`. The investor does not supply `expires_at` in the POST payload — it is always system-computed. No configuration override is exposed to the user.

The system shall proactively check `hl_agent_keys.expires_at` during deep-audit. If `expires_at - now <= 7 days`, a notification is sent to the user via the `notification` queue with message "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." At bot start preflight, `expires_at < now` blocks start with E-EXBOT-004. The re-submission flow: user submits a new key → new `hl_agent_keys` row with `approval_status='pending'` → admin approves → old approved row transitions to `status='superseded'` → new row becomes `approved`. During the window between submission and admin approval, the existing approved key remains active (unless it has expired).

**Note:** `expires_at` is only evaluated at bot start preflight and during deep-audit. A key expiring while a bot is already running does not interrupt ongoing hedge-sync operations — the bot continues until it stops or enters SAFE_MODE, at which point the preflight check applies on the next start attempt.

**Acceptance criteria:** A submitted agent key always has `expires_at = submitted_at + 90 days` set by the system — no user-supplied value is accepted. A user with a key expiring in 5 days receives a notification within the next deep-audit cycle. Bot start with an expired key is blocked with E-EXBOT-004. New key submission does not revoke the existing key until admin approves the replacement. `status='superseded'` is set on the old row atomically with `status='approved'` on the new row.

---

### FR-EXBOT-091 — HLRateLimitDO
**Trace:** FM-XB-03
**Priority:** P0

`HLRateLimitDO` implements a sliding-window rate limiter for all outbound Hyperliquid API calls. BNZA operating budget: 800 weight/min (67% of HL's hard limit of 1,200 weight/min). Each HL API call category has a known weight; the caller declares the weight before the call is made. If the declared weight would exceed the remaining budget in the current window, the DO returns `{allowed: false, retryAfterMs}` and the caller re-queues the message with the indicated delay. The weight window resets every 60 seconds. Multiple CF Worker invocations share a single DO instance per geographic region.

**Acceptance criteria:** Total HL API weight consumed in any 60-second window does not exceed 800. A caller receiving `{allowed: false}` must not proceed with the HL call. Weight accounting covers all 5 HL endpoint categories (clearinghouseState, marginSummary, openOrders, placeOrder, cancelOrder).

---

### FR-EXBOT-092 — UserLockDO (Lease-Based Concurrency)
**Trace:** FM-XB-03, FR-EXBOT-026
**Priority:** P0

`UserLockDO` provides a lease-based mutex preventing concurrent HL mutations for the same user. Interface: `acquire(holderToken, ttlMs=90_000, idempotencyKey?)` → `{acquired: boolean, leaseId?}`; `heartbeat(holderToken, ttlMs)` → extends lease if still held by caller; `release(holderToken, idempotencyKey?, result?)` → releases and optionally caches result for replay. The work runs in the caller (CF Worker), not inside the DO. A `holderToken` mismatch on `release` or `heartbeat` is a no-op. TTL expiry auto-releases the lease. The `idempotencyKey` pattern `hedge-sync:{botId}:{stateVersion}` prevents duplicate execution on message redelivery.

**Acceptance criteria:** Two hedge-sync workers for the same user cannot hold the lease simultaneously. A lease that expires at 90s auto-releases; the next worker acquires and reconciles before submitting any HL order. `heartbeat` called by the correct holder extends the TTL; called by any other token is a no-op. Result caching via `idempotencyKey` prevents reprocessing the same stateVersion twice.

---

### FR-EXBOT-093 — MarketDataDO (Pool Slot0 Cache)
**Trace:** FM-XB-03
**Priority:** P0

`MarketDataDO` provides a shared cache for Uniswap V3 pool slot0 data (`sqrtPriceX96`, `currentTick`, `blockNumber`). All light-check workers read from this DO instead of making individual RPC calls to the RPC provider. The DO refreshes its cache at an interval defined by the Phase 0 NV-12 verification result (OQ-EXBOT-03). A single DO instance serves all light-check workers within a CF region. Cache staleness older than 2× the refresh interval is logged as a warning and the DO initiates a forced refresh.

**Acceptance criteria:** 10,000 concurrent light-check workers in one region make at most 1 RPC call per refresh interval (via the DO), not 10,000. A stale cache (2× refresh interval) triggers a forced DO refresh and a warning log entry. The `blockNumber` field in the cache monotonically increases — a DO that returns a lower `blockNumber` than a prior read is treated as a cache regression and re-fetches.

---

### FR-EXBOT-090 — Operator Facade API
**Trace:** FM-XB-06, US-EXBOT-012
**Priority:** P1

The OPERATOR shall expose five endpoints under `/api/exbot/*`, each proxied to ExBot Worker via CF service binding with internal token authentication. ExBot Worker is not internet-accessible. Endpoints: `POST /api/exbot/start`, `GET /api/exbot/status`, `POST /api/exbot/close`, `POST|GET /api/exbot/agent-key`, `POST /api/exbot/margin`. The OPERATOR does not own any ExBot business logic; it only forwards requests.

**Acceptance criteria:** Direct HTTP requests to ExBot Worker return 403 (not publicly accessible). All five endpoints are reachable via the Operator Facade. OPERATOR logs show service binding calls for each proxied request.

---

## 3. Non-Functional Requirements

| NFR ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-EXBOT-001 | Throughput | System must scan 10,000 bots in a 5-minute window (33.3 bots/sec sustained). | P0 |
| NFR-EXBOT-002 | Latency | One hedge-sync should complete within 30 seconds under normal conditions. | P0 |
| NFR-EXBOT-003 | SLA | `user_redeem` hedge close must complete within 5 minutes of event detection. Overrun triggers admin escalation. | P0 |
| NFR-EXBOT-004 | Rate Limit | HL API usage must not exceed 800 weight/min (67% of the 1,200/min hard limit). | P0 |
| NFR-EXBOT-005 | D1 Write Budget | `bot_runtime_state` written only on diff. `next_light_check_at` batch-updated per shard (1 stmt). No unconditional UPDATE per light-check. | P0 |
| NFR-EXBOT-006 | Security | Master private key never stored. Agent key AES-256-GCM envelope. Plain key function-scope only, never logged. | P0 |
| NFR-EXBOT-007 | Idempotency | `queue_idempotency.message_id` UNIQUE prevents double execution. Cloid deterministic prevents double HL order. | P0 |
| NFR-EXBOT-008 | Precision | All hedge, stop, and margin computations use BigDecimal. Float/number arithmetic forbidden for financial values. | P0 |
| NFR-EXBOT-009 | Multi-Chain | Base + Optimism from Phase 1. `wethIndex` verified per chain at LP open. Not hardcoded. | P0 |
| NFR-EXBOT-010 | Availability | SAFE_MODE and `bot_safe_close` lead to autonomous recovery. Neither is a terminal state. | P0 |
| NFR-EXBOT-011 | Concurrency | Max 6 simultaneous outbound connections per CF Worker invocation. Parallel HL fetches within 1 invocation ≤ 6. | P0 |
| NFR-EXBOT-012 | Scalability | Phase A: 1 D1 shard. Phase B: 4 shards. Phase C: 16 shards (deferred, requires 10k-equivalent load benchmark). `shard_id = hash(bot_id) % shard_count`. | P0 |

---

## 4. Business Rules

| BR ID | Rule | Priority |
|---|---|---|
| BR-EXBOT-001 | Phase A: 1 user = 1 active ExBot. `status IN ('active','paused','closing','safe_mode','error')` all count toward the limit. | P0 |
| BR-EXBOT-002 | PAUSED ≠ CLOSED. Pause keeps hedge and LP intact; only new mutations are stopped. Close liquidates everything. UI must use distinct labels. | P0 |
| BR-EXBOT-003 | Light-check HL weight = 0. Any HL API call introduced into light-check is an architectural violation. | P0 |
| BR-EXBOT-004 | Delta-only hedge adjustment is the invariant default. Full close → open in normal hedge-sync is a bug. | P0 |
| BR-EXBOT-005 | `stop_trigger_crossed_at` is write-once per stop event (guarded: only set if currently NULL). This prevents the 30-min SAFE_MODE detection from being defeated by repeated light-check overwrites. | P0 |
| BR-EXBOT-006 | `user_redeem` LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user. | P0 |
| BR-EXBOT-007 | SAFE_MODE is never a terminal state. Every SAFE_MODE path must lead to auto-recovery or `bot_safe_close` → §16.7 re-entry closed loop. | P0 |
| BR-EXBOT-008 | "BnzaExVault/Vault" (LP NFT custody Solidity contract) is unrelated to "vaultAddress/subaccount" (HL subaccount identifier) despite naming similarity. These must never be conflated in code or documents. | P0 |
| BR-EXBOT-009 | D1 schema changes after Phase A deploy: ADD COLUMN only. DROP and RENAME of existing columns are forbidden. | P0 |
| BR-EXBOT-010 | ExBot Worker (`apps/bnza-exbot/`) must not be co-deployed with OPERATOR (`apps/bnza-operator/`). They communicate via CF service binding only. | P0 |
| BR-EXBOT-011 | Agent key storage is envelope-encrypted only. The plain agent key and plain DEK must never be persisted to D1, logs, or any external store. Plain values are function-scoped during decryption and destroyed immediately after use. Source: FR-EXBOT-080. | P0 |
| BR-EXBOT-012 | Only one `hl_agent_keys` row per user may have `approval_status='approved'` at any time. This constraint is enforced at the database level. Source: FR-EXBOT-082. | P0 |
| BR-EXBOT-013 | Agent key rows are immutable after write — revocation and rotation are non-destructive. `revoked` and `superseded` rows must never be overwritten or deleted; they are retained for audit purposes. Source: FR-EXBOT-082. | P0 |
| BR-EXBOT-014 | During key rotation, the old row's `status='superseded'` and the new row's `status='approved'` must be committed atomically in the same transaction. There is no window where both rows are `approved` or neither is `approved`. Source: FR-EXBOT-083. | P0 |

---

## 5. Error Codes

| Code | Condition | Message | HTTP |
|---|---|---|---|
| E-EXBOT-001 | One-bot policy violation | "You already have an active ExBot. Close or wait for the existing bot to finish." | 409 |
| E-EXBOT-002 | Insufficient HL margin at preflight | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | 400 |
| E-EXBOT-003 | Agent key status is pending | "Agent key is awaiting approval. Please complete the approval process before starting." | 400 |
| E-EXBOT-004 | Agent key expired | "Your HL agent key has expired. Please submit a new one." | 400 |
| E-EXBOT-005 | Builder fee not approved | "HL builder fee (5bps) approval required before starting ExBot." | 400 |
| E-EXBOT-006 | LP mint simulation failed | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | 400 |
| E-EXBOT-007 | HL order rejected (insufficient margin during sync) | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." | 502 |
| E-EXBOT-008 | HL API unreachable | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | 503 |
| E-EXBOT-009 | Stop placement failed | "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | 502 |
| E-EXBOT-010 | user_redeem SLA breached | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | — (internal alert) |
| E-EXBOT-011 | Reconcile mismatch | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | — (internal) |
| E-EXBOT-012 | Close attempted on already-closed bot | "Bot is already closed. No action needed." | 409 |
| E-EXBOT-013 | Pause attempted in SAFE_MODE | "Bot is in Safe Mode. You can close the bot instead." | 409 |
| E-EXBOT-014 | Submit agent key while existing key is pending | "Your agent key is awaiting admin approval. You cannot submit a new key until the current one is reviewed." | 409 |
| E-EXBOT-015 | Submit agent key while existing key is approved | "You already have an active agent key. You can only submit a new key after your current key has expired." | 409 |
| E-EXBOT-016 | Approve agent key that has already expired | "This agent key has already expired and cannot be approved. Please ask the investor to submit a new key." | 409 |

---

## 6. Screen Inventory

ExBot is a **backend-only module**. No UI screens are owned by this module. The POOL UI (PTL-05) renders ExBot status data returned by the Operator Facade API — those screens are specified in the `bnza-pool` module.

The Operator admin view for ExBot management (force-close, agent-key approval) is rendered by PTL-02 (ADMIN) and specified in the `admin/bnza-admin` module.

---

## 7. Use Case Inventory

Full UC specs in `../usecases/`. Each file contains: actors, preconditions, main success scenario, alternate flows, postconditions, and FR mapping.

| UC slug | Description | FR trace |
|---|---|---|
| `uc-bot-start` | Start ExBot: preflight → LP mint → hedge open → stop place → active | FR-EXBOT-001–004, 020, 030–031 |
| `uc-light-check` | Periodic scan (zero HL calls) → fan-out to hedge-sync or price-near-stop-audit | FR-EXBOT-012, 013, 014, 015, 016, 032 |
| `uc-hedge-sync` | Delta-only hedge adjustment + INV-STOP protocol + post-order reconcile | FR-EXBOT-020, 021, 022, 024, 025, 026, 027, 035 |
| `uc-user-redeem` | LP-first instant redemption + HL hedge close SLA 5 min | FR-EXBOT-070, 071 |
| `uc-bot-safe-close` | Hedge-first system close → executeStrategy(RedeemStrategyV1) → RedemptionQueue FIFO payout to user | FR-EXBOT-070, 072, 073 |
| `uc-agent-key` | AES-GCM envelope encryption for HL agent key + admin approval flow | FR-EXBOT-080, 081, 082, 083 |

---

## 8. User Story Inventory

Full story files in `../userstories/`. 12 stories across 4 epics.

| Story ID | Epic | Actor | Description | Priority |
|---|---|---|---|---|
| US-EXBOT-001 | Investor Lifecycle | USDC Investor | Start ExBot (preflight + one-bot policy) | P0 |
| US-EXBOT-002 | Investor Lifecycle | USDC Investor | Monitor active ExBot status | P0 |
| US-EXBOT-003 | Investor Lifecycle | USDC Investor | Pause and resume ExBot | P1 |
| US-EXBOT-004 | Investor Lifecycle | USDC Investor | Close ExBot and redeem funds (user_redeem) | P0 |
| US-EXBOT-005 | System Operations | ExBot System Operator | Light-check without HL calls (10k scale) | P0 |
| US-EXBOT-006 | System Operations | ExBot System Operator | Delta-only hedge-sync + cloid + reconcile | P0 |
| US-EXBOT-007 | System Operations | ExBot System Operator | LP range rebalance + lp_operations recovery | P0 |
| US-EXBOT-008 | Risk & Safety | ExBot System Operator | Circuit breaker open/half_open/close | P0 |
| US-EXBOT-009 | Risk & Safety | ExBot System Operator | bot_safe_close + automatic re-entry closed loop | P0 |
| US-EXBOT-010 | Risk & Safety | ExBot System Operator | Margin warning/critical → SAFE_MODE | P0 |
| US-EXBOT-011 | Agent Key & Admin | USDC Investor | Submit + encrypt HL agent key (AES-GCM) | P0 |
| US-EXBOT-012 | Agent Key & Admin | ExBot Admin (zen) | Admin force-close + emergencyTransfer (Operator-only when paused, no recipient param, EmergencyRecovery event) | P1 |

---

## 9. Open Questions

| OQ ID | Question | Impact | Status |
|---|---|---|---|
| OQ-EXBOT-01 | NV-1: HL `marginSummary` exact API field names for `marginBalanceUsd` | Blocks FR-EXBOT-060 final implementation | Open |
| OQ-EXBOT-02 | NV-3: Does HL support place-before-cancel stop replacement? Determines §19.5 path (a) vs (b). | Blocks FR-EXBOT-035 (INV-STOP protocol path) | Open |
| OQ-EXBOT-03 | NV-12: Pool addresses + `wethIndex` for USDC/WETH 0.3% on Base + Optimism | Blocks FR-EXBOT-004 dual-chain LP open | Open |
| OQ-EXBOT-04 | NV-13: HL ETH-USD perp minimum order size / dust handling rules | Blocks FR-EXBOT-022 (minimum delta threshold) | Open |
| OQ-EXBOT-05 | NV-14: HL builder fee 5bps approval flow — on-chain transaction or API call? | Blocks FR-EXBOT-002 preflight step 4 | Open |
| OQ-EXBOT-06 | Margin thresholds (0.55/0.75) — finalized via Phase 0 backtest (zen task) | FR-EXBOT-060 values pending | Open |
| OQ-EXBOT-07 | `stopSafetyFactor` Phase B+ value — finalized via Phase 0 backtest (zen task) | FR-EXBOT-030 Phase B value pending | Open |
| OQ-EXBOT-08 | BnzaExVault final ABI — confirmed when zen deploys contract at Phase 0 | IC-EXBOT-002 (integration constraints) | Open |
| OQ-EXBOT-09 | MarketDataDO cache refresh interval — determined by Phase 0 NV-12 RPC verification | Blocks FR-EXBOT-093 TTL configuration | Open |
| OQ-EXBOT-10 | `range_boundary_near` exact computation: is "90% to upper/lower" measured in tick distance or price distance? Formula needed before implementation. E.g. tick-based: `currentTick >= tickUpper - 0.10 × (tickUpper - tickLower)` vs price-based: `sqrtPrice >= sqrtUpper × 0.90`. Owner: zen/SOTATEK to confirm. | Blocks FR-EXBOT-012 `range_boundary_near` implementation | Open |
| OQ-EXBOT-11 | `lpValueUsd` formula: how is `bot_runtime_state.lp_value_usd` computed and updated? Candidate: `(lpEthAmount × uniPoolPrice) + lpUsdcAmount` — but SPEC v5.2.6 does not define it explicitly. Owner: zen to confirm or SOTATEK to propose. | Blocks FR-EXBOT-012 `drift_threshold` (lpValueUsd × 3% term) | Open |
| OQ-EXBOT-12 | 7d funding APR aggregation formula: how is `funding_alert` condition (`7d APR < −15%`) computed from `funding_daily_metrics`? Candidate (from SPEC v5.2.6 §7.5): sum of latest 7 rows `funding_net_usd`, annualize relative to LP capital — but exact annualization formula not specified. Owner: zen to confirm. | Blocks FR-EXBOT-012 `funding_alert` implementation | Open |
| OQ-EXBOT-13 | delta=0 behavior in hedge-sync: if computed delta=0, should the Worker skip HL order entirely and proceed directly to stop replacement, or abort the sync? Owner: Tech Lead. | Blocks UC-EXBOT-hedge-sync step 5 / A6 | Open |
| OQ-EXBOT-14 | `marginSummary` fetch ordering in hedge-sync preflight: does the Worker fetch marginSummary before or after acquiring UserLockDO? Ordering affects lock TTL design. Owner: Tech Lead. | Blocks FR-EXBOT-060 preflight step ordering | Open |
| OQ-EXBOT-15 | HLRateLimitDO + UserLockDO interaction in hedge-sync: should rate-limit weight be consumed before or after lock acquisition? Determines retry behavior on rate-limit hit while lock is held. Owner: Tech Lead. | Blocks FR-EXBOT-091 + hedge-sync flow | Open |
| OQ-EXBOT-16 | Admin reject path for agent key: when admin rejects a pending key, what is the resulting row status — remain `pending`, set to `rejected`, or delete? Options: A) `approval_status='rejected'` keep row for audit trail; B) delete row, investor must resubmit; C) `approval_status='rejected'`, allow resubmit without new row. Owner: BA + zen (scope decision). | Blocks UC-EXBOT-agent-key A4 admin reject enum | Open |
| OQ-EXBOT-17 | `hlMarkPrice` data source in light-check step 11: given the zero-HL-calls invariant (BR-EXBOT-003), what is the authoritative source for mark price used to evaluate stop trigger? Candidate: `bot_runtime_state.eth_price_usd`. Staleness policy needed. Owner: Tech Lead. | Blocks UC-EXBOT-light-check step 11 | Open |

---

## 10. Integration Constraints

| IC ID | External Dependency | Constraint | Blocks |
|---|---|---|---|
| IC-EXBOT-001 | Hyperliquid REST API (info + exchange endpoints) | BNZA budget capped at 800 weight/min. All outbound calls routed through HLRateLimitDO (FR-EXBOT-091). Weight table per endpoint category must be maintained in code. HL API schema changes (field renames, endpoint deprecations) require immediate SRS review. | FR-EXBOT-060, 091 |
| IC-EXBOT-002 | BnzaExVault Solidity contract (LP NFT custody, redeem) + RedemptionQueue (FIFO payout) | SOTATEK integrates via ABI only — no contract development. Final ABI confirmed when zen deploys at Phase 0 (OQ-EXBOT-08). Until ABI is confirmed, vault.executeStrategy(RedeemStrategyV1, user, botId, params) and RedemptionQueue.createRequest/fulfillRequest calls are stubbed. uninvestedBalanceOf() is no longer part of the integration surface. Contract address (Base + Optimism) must be injected via Cloudflare Secrets Store, not hardcoded. | FR-EXBOT-015, 070, 073 |
| IC-EXBOT-003 | Uniswap V3 Pool (Base + Optimism, USDC/WETH 0.3%) | Pool addresses and `wethIndex` confirmed via Phase 0 NV-12 verification (OQ-EXBOT-03). `MarketDataDO` (FR-EXBOT-093) must be pointed to the correct pool address per chain. Pool address changes (e.g., pool migration) require coordinated deploy of new DO configuration. | FR-EXBOT-004, 093 |
| IC-EXBOT-004 | Cloudflare Platform (Workers, D1, Queues, Durable Objects, Secrets Store) | ExBot Worker is deployed exclusively as a Cloudflare Worker. Service binding to OPERATOR is required for all Facade API calls. Max 6 simultaneous outbound connections per Worker invocation (NFR-EXBOT-011). D1 concurrent write limits apply; batch patterns (FR-EXBOT-013) are required by design. Cloudflare platform outages are a SAFE_MODE trigger condition. | All FR-EXBOT-* |
