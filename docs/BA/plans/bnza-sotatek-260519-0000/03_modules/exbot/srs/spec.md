---
type: srs
status: draft
created: 2026-06-12
updated: 2026-07-24
owner: "@hienduong"
module: exbot
lang: en
links:
  - ../frd.md
  - ../../02_backbone/backbone.md
  - ../usecases/index.md
  - ../userstories/index.md
changelog:
  - 2026-07-27 | manual | review fixes: E-EXBOT-017 hl_agent_keys → hl_custodial_wallets; FR-EXBOT-070 body → Change A Operator-executed flow; OQ-BNZAEX-01/02 moved to bnza-ex/srs/spec.md
  - 2026-07-25 | /ba-impact | C-1: FR-026/092/FM-XB-03/FR-060 → Postgres advisory lock; Change B: FR-002/080/BR-012..014 → hl_custodial_wallets; C-6: OQ-16 closed; Change A: §7 UC row user-close
  - 2026-07-24 | /ba-do | Change B: preflight AC + E-EXBOT-002 message "deposit $Z to HL" → "deposit $Z USDC to BNZP"; E-EXBOT-007 "Deposit additional margin" → "Deposit additional USDC to BNZP"
  - 2026-07-24 | manual | add OQ-EXBOT-24: funding_24h_apr_immediate_l1 formula Phase A; OQ-EXBOT-25: notification worker delivery channel
  - 2026-07-24 | manual | add OQ-EXBOT-23: §19.3 stop size vs actual position size gap + §19.5 confirmed-size trust assumption
  - 2026-07-24 | /ba-impact | gap fill from closed OQs: FR-004 pool addrs+config-driven (OQ-03/19); FR-050 hysteresis+worker obligations (OQ-18); FR-060 accountValue note+lock ordering (OQ-01/14); FR-091 lock→weight→call AC (OQ-15); add BR-015 one-address-one-org (OQ-21)
  - 2026-07-24 | manual | fix endpoint path GET /api/exbot/status → GET /api/exbot/status/{botId} in FR-EXBOT-090 prose (sync with frd.md, uc-monitor-status)
  - 2026-07-23 | /ba-absorb | absorb client Q&A batch: OQ-01 need-to-re-verify; OQ-02 need-to-re-verify (path conflict); OQ-03 closed (pool addresses confirmed); OQ-04 need-to-re-verify (dust policy confirmed, min size pending); OQ-05 need-to-re-verify (EIP-712 direction confirmed, testnet pending); OQ-06/07 annotated (config-driven placeholders confirmed); OQ-08 annotated (AWS Secrets Manager noted); OQ-10 need-to-re-verify (tick vs price conflict); OQ-13 need-to-re-verify (delta=0 stop replacement conflict); OQ-14/15 closed; OQ-16/17 need-to-re-verify; added OQ-EXBOT-18..22 + OQ-BACKTEST-01 + OQ-BNZAEX-01..02
  - 2026-07-21 | manual | register E-EXBOT-031: status='paused' UI label for uc-monitor-status A10
  - 2026-07-20 | manual | FR-EXBOT-073: clarify redemption_queued step — principal_amount is placeholder at createRequest; overwritten by hl_withdraw Phase 3 (withdrawable delta); step 6 expanded with full hl_withdraw+hl_fulfill+CCTP chain
  - 2026-07-20 | manual | OQ-EXBOT-009 closed: pool slot0 cache refresh interval = 60s provisional (zen); stale threshold = 120s; UC light-check step 7 + A1 updated
  - 2026-07-20 | manual | OQ-EXBOT-012 closed: funding_alert formula confirmed by zen; add formula to FR-EXBOT-012 AC; note bnza-market-cron fallback
  - 2026-07-20 | manual | OQ-EXBOT-013 closed: delta=0 returns no_op_dust immediately — no stop replacement, no reconcile (confirmed develop branch rebalance.ts + handler-impl.ts)
  - 2026-07-20 | manual | FR-EXBOT-035: chốt INV-STOP place-before-cancel sequence per zen; close OQ-EXBOT-02; update AC
  - 2026-07-20 | manual | FR-EXBOT-025 AC: define exact-fill reconcile threshold (no % tolerance); close OQ-EXBOT-11 with zen confirmed lp_value_usd formula; clarify drift_threshold belongs to light-check only
  - 2026-07-20 | manual | FR-EXBOT-072: fix trigger_reason claim — field not in close_operations DB; reason in SQS payload only (enum: l2_evacuation|parked_escalation|admin), logged to CloudWatch
  - 2026-07-13 | manual | register E-EXBOT-030: GET /status wallet mismatch → 403 (N-002 fix for uc-monitor-status A9)
  - 2026-07-09 | manual | register E-EXBOT-029: status='error' UI display message (uc-monitor-status A7)
  - 2026-07-09 | manual | register E-EXBOT-028: LP mint on-chain tx reverted/timeout at bot-start → lifecycle_state='error'
  - 2026-07-08 | /ba-do | add E-EXBOT-026/027; update KMS provisioning flow steps 4–7; add BR-EXBOT-012 UNIQUE active per user constraint
  - 2026-07-04 | arc-migration | FR-EXBOT-010: sync queue count to 11 (add key-provision), fixing inconsistency with FM-XB-02 backbone label
  - 2026-07-03 | arc-migration | replace Cloudflare primitives with AWS equivalents across all FRs
  - 2026-06-29 | manual | flow change: §1 intro; FM-XB-02/05/06; FR-002/080 KMS; remove FR-081/082/083; BR rewrite; remove E-003/004/014/015/016; add E-017; §6/7/8; FR-090; NFR-006; IC-005; close OQ-16
  - 2026-06-20 | /ba-do | QC audit fixes: OQ-EXBOT-13/14/15/16/17 added to §9
  - 2026-06-18 | /ba-do hld-decisions | FR-070/071/073 update: drop park/re-entry; IC-EXBOT-002 remove uninvestedBalanceOf stub; scope FM-XB-08 update; us-012 emergency authority
  - 2026-06-12 | /ba-impact | §9 add OQ-EXBOT-10/11/12: range_boundary_near formula, lpValueUsd computation, 7d APR aggregation — all pending zen confirm
  - 2026-06-12 | /ba-impact | gap fill v5.2.6: FR-012 add stop_replacing_started_at primary detection + uniPoolPrice 3-way split note; FR-033 add primary light-check detection (≤5min) vs deep-audit secondary backstop
  - 2026-06-12 | /ba-start srs --update | gap fill: added FR-015,016,036,072,073,082,083,091,092,093; section 10 Integration Constraints; fixed UC inventory traces
  - 2026-06-12 | /ba-start srs | initial SRS authored from FRD + use cases + user stories
---

# SRS: BNZA-EXBOT Infrastructure (Module 4)

> **Trace:** FM-XB-01 → FM-XB-08 (Feature Map §5.4)
> **Architecture:** Standalone AWS Lambda service (`apps/bnza-exbot/`) — NOT co-deployed with OPERATOR
> **Entry point:** OPERATOR Facade `/api/exbot/*` → API Gateway + Lambda Authorizer (HMAC) → ExBot Lambda
> **Source truth:** SPEC v5.2.6 (zen-approved). Where this SRS conflicts with SPEC v5.2.6, SPEC prevails.

---

## 1. Introduction

### 1.1 Scope

BNZA-EXBOT is the backend infrastructure for a managed delta-hedged LP Bot. SOTATEK builds infrastructure only — trading strategy logic (PositionCalc, hedge math, stop safety factor tuning) is zen-proprietary. ExBot Lambda runs as a standalone AWS Lambda service, separate from OPERATOR. The OPERATOR acts as a thin public-facing facade that proxies `start/status/close/margin` to ExBot Lambda via API Gateway with HMAC Lambda Authorizer.

This SRS covers FM-XB-01 through FM-XB-08 for Phase A (1–100 bots, Base + Optimism dual-chain).

### 1.2 In Scope

| Feature Map ID | Feature | Priority |
|---|---|---|
| FM-XB-01 | Aurora PostgreSQL Serverless v2 Schema (control_db + state_db_shard) | P0 |
| FM-XB-02 | Queue Topology (11 queues via SQS / Redis BullMQ) | P0 |
| FM-XB-03 | ElastiCache Redis — rate limiter (HLRateLimit), Postgres advisory lock (UserLock), pool slot0 cache (MarketData) | P0 |
| FM-XB-04 | Scheduled Jobs via EventBridge Scheduler (deep-audit, metrics-rollup, stop-integrity scan) | P1 |
| FM-XB-05 | HL Adapter (rate limit, cloid, delta-only, reconcile, agent key signing via KMS Signing Lambda) | P1 |
| FM-XB-06 | Operator Facade API (`/api/exbot/*` — 4 endpoints) | P1 |
| FM-XB-07 | Lifecycle State Machine (18 states) | P0 |
| FM-XB-08 | Close/Redeem Operations (user_redeem + bot_safe_close via RedemptionQueue FIFO — park/redeploy dropped HLD 2026-06-18) | P0 |

### 1.3 Out of Scope

- Trading strategy logic (PositionCalc, hedge math formula, stop safety factor tuning) — zen-proprietary
- BnzaExVault Solidity contract development — zen scope; SOTATEK integrates via ABI
- Phase 0 verification tasks (NV-1 to NV-14) — zen/SOTATEK verification tasks
- Backtest module (separate module)
- POOL UI changes for ExBot tab — POOL module scope
- Phase B+ features (multi-bot per user, Aurora PostgreSQL sharding >1 shard, S3 archive, Analytics Engine)

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

The system shall run six preflight checks in sequence before creating a bot record: (1) one-bot policy check, (2) vault balance check — `BnzaExVault` balance > 0 for this user (block with E-EXBOT-025 if no confirmed deposit), (3) HL isolated margin balance ≥ required margin × 2.0, (4) `hl_custodial_wallets.key_status='active'` (provisioned automatically at deposit time — if not active, block with E-EXBOT-017), (5) builder fee (5bps) confirmed on HL, (6) LP mint simulation passes. Any single failure blocks the start with a specific message identifying the failed check.

**Acceptance criteria:** No vault deposit returns E-EXBOT-025. Insufficient margin returns "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z USDC to BNZP." Key not provisioned (`key_status` not `active`) returns E-EXBOT-017. Each check failure produces a distinct error; no partial bot record is left in Aurora PostgreSQL.

---

### FR-EXBOT-003 — Bot Lifecycle State Tracking
**Trace:** FM-XB-07, US-EXBOT-001
**Priority:** P0

The system shall track bot state using two fields: `bots.status` (coarse-grained: active/paused/closing/closed/safe_mode/error) and `bots.lifecycle_state` (fine-grained: 18 canonical values). The initialization sequence is fixed: idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active. No step may be skipped.

**Acceptance criteria:** A bot that completes initialization has `lifecycle_state='active'` and `status='active'`. Each transition is persisted atomically to Aurora PostgreSQL before proceeding to the next step.

---

### FR-EXBOT-004 — Dual-Chain Support (Base + Optimism)

---

### FR-EXBOT-004 — Dual-Chain Support (Base + Optimism)
**Trace:** FM-XB-07, US-EXBOT-001
**Priority:** P0

The system shall support Base and Optimism from Phase 1. `wethIndex` (0 or 1, indicating whether WETH is token0 or token1 in the pool) shall be verified per chain and stored in `positions.weth_index` at LP open. The hedge leg (HL ETH-USD perpetual short) is chain-independent; dual-chain impact is LP side only.

**Acceptance criteria:** A bot on Base and a bot on Optimism can run simultaneously under different users. `weth_index` is populated correctly for each chain; LP ETH amount calculation uses `weth_index` from Aurora PostgreSQL, not a hardcoded assumption. Confirmed pool addresses (OQ-EXBOT-03): Base USDC/WETH 0.3% = `0x6c561B446416E1A00E8E93E221854d6eA4171372` (WETH = token0, `wethIndex=0`); Optimism USDC/WETH 0.3% = `0xc1738D90E2E26C35784A0d3E3d8A9f795074bcA4` (WETH = token1, `wethIndex=1`). System must still assert token0/token1 ordering on-chain at startup rather than trusting config alone. Pool address, tokens, and HL symbol are config-driven parameters — adding a chain requires a config entry and on-chain verification, not a code change.

---

### FR-EXBOT-005 — Pause / Resume Bot
**Trace:** FM-XB-07, US-EXBOT-003
**Priority:** P1

The system shall support pausing a bot by setting `bots.status='paused'` while leaving `lifecycle_state` at its pre-pause value. The existing HL short and LP NFT shall remain intact during pause. Light-check and hedge-sync shall be suppressed for paused bots. Deep-audit shall continue every 6 hours during pause.

**Acceptance criteria:** Paused bot shows status "Paused — hedge is maintained, LP is maintained" in the Operator API status response. Resume restores `status='active'` and schedules the next light-check within 5 minutes.

---

### FR-EXBOT-010 — Queue Topology (11 Queues via SQS / Redis BullMQ)
**Trace:** FM-XB-02, US-EXBOT-005
**Priority:** P0

The system shall implement exactly 11 queues: `bot-scan`, `light-check`, `hedge-sync`, `reconcile`, `deep-audit`, `price-near-stop-audit`, `partial_repair`, `user_redeem` (highest priority, SLA 5 min), `notification`, `metrics-rollup`, `key-provision`. All queue `sendBatch` calls shall go through the `chunkSendBatch()` helper (max 10 messages per call — SQS hard limit). Direct `queue.sendBatch()` without the helper is forbidden.

**Acceptance criteria:** No producer calls `sendBatch` directly. Batch sizes exceeding 10 are chunked automatically. Dead-letter queue (SQS DLQ, maxReceiveCount=3) receives poison messages from any consumer.

---

### FR-EXBOT-011 — Queue Consumer Idempotency
**Trace:** FM-XB-02, US-EXBOT-006
**Priority:** P0

Every queue consumer shall insert `message_id` with `state='started'` into the `queue_idempotency` table at the start of processing. A UNIQUE constraint conflict on `message_id` indicates duplicate delivery; the consumer shall return immediately without processing. On completion, the consumer updates `state='succeeded'`; on failure, `state='failed'` or `'retryable'`.

**Acceptance criteria:** Redelivering the same queue message twice produces exactly one successful execution. The second delivery exits immediately after the UNIQUE constraint conflict. `queue_idempotency` row is present for every processed message. Lambda SQS consumers shall use `reportBatchItemFailures` response format; failed individual records are returned to SQS for retry while succeeded records are not re-delivered. A scheduled cleanup job (EventBridge cron, every 1 hour) shall execute `DELETE FROM queue_idempotency WHERE expires_at < now` to prevent unbounded table growth.

---

### FR-EXBOT-012 — Light-Check (Zero HL API Calls)
**Trace:** FM-XB-02, US-EXBOT-005
**Priority:** P0

The light-check worker shall evaluate each active bot's rebalance need using only Aurora PostgreSQL `bot_runtime_state`, ElastiCache Redis pool slot0 cache (sqrtPriceX96, currentTick — written by Fargate price poller), and local TickMath computation. No Hyperliquid API calls are permitted in light-check (HL weight = 0). The worker shall evaluate the canonical `RebalanceReason[]` enum and enqueue `hedge-sync` when rebalance is needed and `circuit_breakers.state != 'open'`. Light-check shall be skipped entirely for bots with `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'`.

In addition to rebalance evaluation, each light-check pass shall:
1. Check `stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60s` — if true, enqueue `partial_repair` with `reason='stop_replacing_overrun'` and enter SAFE_MODE (primary detection, ≤5 min; see FR-EXBOT-033).
2. Use `uniPoolPrice` (Uniswap V3 pool slot0 `sqrtPriceX96`, sourced from ElastiCache Redis pool slot0 cache) when computing `deltaErrorUsd` for drift threshold evaluation. `hlMarkPrice` is used only for stop trigger detection (`markPrice >= stop_price`). `hlOraclePrice` is used only for margin calculations. These three price sources must not be interchanged (v5.2.6 X-5 3-way price split).

**Acceptance criteria:** A 10,000-bot light-check cycle does not consume any HL API rate limit weight. Any HL fetch introduced into light-check is an architectural violation flagged by code review. `deltaErrorUsd` computation uses pool slot0 price from ElastiCache Redis, not HL mark or oracle price. 10,000 concurrent light-check workers make at most 1 RPC call per refresh interval (via the Fargate price poller writing to ElastiCache Redis), not 10,000. `funding_alert` fires when `funding_apr_7d_pct < −15%`; primary source = `funding_rolling_metrics.funding_apr_7d_pct` (populated by `bnza-market-cron`); fallback = `fundingRate × 8760` when row absent. Formula (zen confirmed): `funding_apr_7d_pct(%) = ( Σ funding_net_usd latest 7 rows / lp_value_usd ) × (365/7) × 100`; if fewer than 7 rows, annualize over n available days (× 365/n).

---

### FR-EXBOT-013 — Light-Check Jitter
**Trace:** FM-XB-02
**Priority:** P0

`next_light_check_at` shall be set to `now + 5min + random(−45s, +45s)`. The jitter is computed per-bot as a value, but the Aurora PostgreSQL write is batched (1 UPDATE statement per shard, not a per-bot individual write).

**Acceptance criteria:** No Aurora PostgreSQL per-bot write for `next_light_check_at`. Bot scan shows even distribution of check times across the 5-minute window.

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

### FR-EXBOT-016 — Deep-Audit Scheduled Job (EventBridge Scheduler)
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

**Acceptance criteria:** `rebalance_attempts.reason` column contains only canonical values (CSV for multiple). No variant spellings or custom trigger names appear in Aurora PostgreSQL or queue messages.

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

**Acceptance criteria:** `rebalance_attempts.status='success'` is never written before reconcile. `hedge_legs.entry_price` and `stop_price` are populated after every hedge open or resize. Match is defined as exact fill — actual HL position size must equal target size. Any partial fill results in `reconcile_partial` status and triggers the partial_repair flow. No percentage tolerance is applied.

---

### FR-EXBOT-026 — User Lock (Postgres Advisory Lock — Concurrency Control)
**Trace:** FM-XB-03, US-EXBOT-006
**Priority:** P0

Before any Hyperliquid mutation for a given user, the hedge-sync worker shall acquire a Postgres advisory lock (`pg_try_advisory_lock(user_id)`) to prevent concurrent HL mutations for the same user. If the lock cannot be acquired, the worker re-queues the message with a delay. The lock is released in a `finally` block after the HL operation completes. Lock TTL is governed by the Lambda invocation timeout; no explicit heartbeat-extend mechanism is required (unlike Redlock).

**Acceptance criteria:** Two hedge-sync workers for the same user cannot run HL mutations concurrently. A failed lock acquisition re-queues the message; no HL call is made. Lock is always released (finally block) regardless of success or failure.

---

### FR-EXBOT-027 — StateVersion Optimistic Concurrency
**Trace:** FM-XB-05, US-EXBOT-006
**Priority:** P0

Before acquiring the Redis Redlock, the hedge-sync worker shall read `bot_runtime_state.state_version` and compare it with the `stateVersion` in the queue message. A mismatch means the state changed since the message was enqueued; the worker shall discard the message (record `rebalance_attempts.status='skipped'`) without submitting any HL order.

**Acceptance criteria:** A stale hedge-sync message (stateVersion < current Aurora PostgreSQL value) is silently discarded. No HL order is submitted for discarded messages.

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

Stop replacement on hedge resize shall use the INV-STOP protected protocol — place-before-cancel sequence: (1) place new stop, (2) verify new stop active (verifyStopPlaced), (3) cancel old stop only after verification succeeds. This guarantees no 0-stop window at any point. Direct cancel-then-place is forbidden. On new stop placement failure, old stop remains active; partial_repair is enqueued. `stop_replacing_started_at` shall be set at the start of the replacement critical section and cleared in a `finally` block.

**Acceptance criteria:** Stop replacement always follows place-before-cancel sequence — new stop must be verified active before old stop is cancelled. No 0-stop window exists at any point during replacement. `stop_replacing_started_at` is always NULL when no replacement is in progress.

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

The system shall enter SAFE_MODE when any of the following is detected: HL API unreachable for more than 5 minutes; reconcile mismatch (actual size ≠ expected); `margin_status='critical'` twice in a row; `effective_leverage > 4.5`; `liquidation_price` within 5% of current hlMarkPrice; `stop_trigger_crossed_at` stuck > 30 min; `stop_replacing_started_at` stuck > 60s. For margin-based SAFE_MODE (OQ-EXBOT-18): entry threshold = margin ratio < 0.55; exit threshold = margin ratio > 0.75 (hysteresis — system remains in SAFE_MODE until the upper threshold is crossed, not merely when the entry condition clears).

In SAFE_MODE the following are forbidden: cancel stops, open positions, rebalance hedge or LP, change leverage, withdraw margin. The following remain allowed: read state, retry HL connectivity, alert user/admin, light-check (non-HL part), deep-audit when HL recovers.

When light-check evaluates a bot as requiring SAFE_MODE entry, the Worker must: (1) stop opening or expanding positions; (2) keep existing hedge and stop orders intact — never leave the LP unhedged; (3) raise an escalation via the notification queue; (4) promote to full-check to measure actual margin from HL; (5) remain in SAFE_MODE until the upper threshold (> 0.75) is recovered — no automatic re-entry below it.

**Acceptance criteria:** A bot in `safe_mode` rejects any hedge-sync or LP rebalance attempt. Stop monitoring continues. Margin-based SAFE_MODE entry fires when ratio < 0.55; exit requires ratio > 0.75 (not merely ≥ 0.55). Auto-recovery proceeds when HL is responsive + 3 consecutive reconciles succeed + `margin_status='ok'`. If recovery is impossible, `bot_safe_close` is initiated.

---

### FR-EXBOT-060 — Margin Status Thresholds
**Trace:** FM-XB-07, US-EXBOT-010
**Priority:** P0

Margin status is computed as `marginUsage = marginRequiredUsd / marginBalanceUsd` where `marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`. Note: the HL `marginSummary` field equivalent to `marginBalanceUsd` is `accountValue` (OQ-EXBOT-01 confirmed). Thresholds: `ok` when marginUsage < 0.55; `warning` when 0.55 ≤ marginUsage < 0.75; `critical` when marginUsage ≥ 0.75.

Margin status shall be updated only during hedge-sync preflight (HL `marginSummary` fetch) and deep-audit. Light-check reads `hedge_legs.margin_status` from Aurora PostgreSQL only — no HL fetch. The `marginSummary` fetch during hedge-sync preflight must occur inside the lock critical section, after the Postgres advisory lock is acquired (OQ-EXBOT-14).

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

**user_redeem / user_close (Change A — Operator-executed):** User clicks "Close Bot" on BNZP UI → Operator API enqueues `user_close` job (highest priority). Execution order: (1) Operator acquires Postgres advisory lock; (2) closes HL hedge via Agent Signing Lambda + KMS (`closeShortReduceOnlyIoc`, SLA: 5 minutes); (3) calls `BnzaExVault.vaultClose(dest=USER)` on-chain via Master Signing Lambda — LP instantly liquidated, LP-portion USDC transferred to investor; (4) `hl_withdraw` + `hl_fulfill` settle HL-portion USDC to investor. Hedge close failure results in `residual_hl_liability` state; LP-portion repayment is NOT reversed. User does not sign any on-chain transaction — Operator executes all steps using custodial KMS keys.

**bot_safe_close (hedge-first):** Triggered by system conditions (circuit breaker exhausted, margin critical, 3 stops in 7 days, admin force-close). Order: close HL hedge → executeStrategy(RedeemStrategyV1) → RedemptionQueue.createRequest → Operator fulfillRequest pays user FIFO on-chain. No park/redeploy loop (dropped HLD 2026-06-18).

**Acceptance criteria:** Duplicate `close_operations` row attempt (same `idempotency_key`) is rejected by UNIQUE constraint. LP-portion USDC is returned to investor via Operator-executed vaultClose regardless of hedge close outcome. `bot_safe_close` funds are returned to user via RedemptionQueue fulfillRequest (on-chain FIFO). No uninvested_balances or uninvestedBalanceOf API used.

---


---

### FR-EXBOT-072 — bot_safe_close Trigger Conditions
**Trace:** FM-XB-08, US-EXBOT-009
**Priority:** P0

The system shall initiate `bot_safe_close` when any of the following conditions is confirmed: (1) circuit breaker exhausted — `circuit_breakers.state='open'` and `reset_at` has been extended 3 or more times without probe success; (2) margin critical — `margin_status='critical'` twice in a row leading to SAFE_MODE with no auto-recovery path; (3) 3 stops within 7 days — `lifecycle_state='hedge_stopped_cooldown'` is entered for the third time within a 7-day rolling window; (4) partial repair exhausted — `partial_repair` consumer fails 3 consecutive repair attempts for the same trigger event; (5) admin force-close — admin invokes `/api/exbot/close` explicitly. All five trigger paths create a `close_operations` row with `idempotency_key UNIQUE` enforced. Trigger reason is conveyed via the SQS message `reason` field (enum: `l2_evacuation | parked_escalation | admin`) and logged to CloudWatch as `bot_safe_close_requested` audit event — it is not persisted as a DB column in `close_operations`.

**Acceptance criteria:** Each trigger condition creates exactly one `close_operations` row (UNIQUE constraint prevents duplicate). SQS message `reason` field is populated with the correct enum value for each trigger type (verify via CloudWatch `bot_safe_close_requested` event). A duplicate trigger for the same bot (e.g., two concurrent admin close calls) is rejected by the UNIQUE constraint on `idempotency_key`.

---

### FR-EXBOT-073 — bot_safe_close Execution Sequence
**Trace:** FM-XB-08
**Priority:** P0

The `bot_safe_close` execution follows a fixed hedge-first sequence tracked atomically in `close_operations`: (1) `requested` — trigger received, `close_operations` row created; (2) `hedge_close_pending` — close HL short position fully via `closeShortReduceOnlyIoc` (target = 0); cancel stop via `replaceStopProtected(size=0)` — both are actions within this step, not separate states; (3) `hedge_closed` — `close_operations.state` advances to `hedge_closed` only after reconcile confirms HL position size = 0 and stop is cancelled; (4) `lp_closed` — call `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` via ExBot Lambda; BnzaExPositionManager closes LP position, fees routed via LpFeeOps, principal returned; `PositionClosed` event emitted; (5) `redemption_queued` — RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId) enqueued; RequestCreated event emitted; `principal_amount` is subsequently overwritten by `hl_withdraw` Phase 3 as `clearinghouseState.withdrawable (initial − final)` — net of PnL, funding, and trading fees; (6) `done` — `hl_withdraw` worker signs master withdraw3 + polls balance; `hl_fulfill` worker bridges USDC via CCTP if needed then calls fulfillRequest(tokens, amounts); FIFO pop; safeTransferFrom(operator, user, principal_amount) on-chain; RequestFulfilled event emitted; bots.status='closed'. On hedge close failure, the system retries up to 3 times before escalating to admin and holding at `hedge_close_pending`. LP close is not attempted until hedge is confirmed closed.

**Acceptance criteria:** `close_operations` state transitions are sequential — no step is skipped. LP close is never attempted before `hedge_closed`. RedemptionQueue request is enqueued at step 5; user funds are returned on-chain when Operator calls fulfillRequest. A failure at any step holds `close_operations.status` at the failed step — does not silently advance.

---

### FR-EXBOT-080 — Agent Key Provisioning (AWS KMS — Custodial Wallet)
**Trace:** FM-XB-01
**Priority:** P0

On user on-chain deposit, the system automatically provisions a per-user **master key** (HL wallet with deposit/withdraw capability) and **agent key** (trade-only delegated signing key) via AWS KMS:

1. Chain indexer (Fargate) detects on-chain deposit event and enqueues a `key-provision` job
2. Key-provision worker requests KMS to generate per-user master key → KMS returns only the public address
3. Key-provision worker requests KMS to generate per-user agent key → KMS returns only the public address
4. Worker creates `hl_custodial_wallets` row with `key_status='provisioning'` — row persisted before HL call to enable retry recovery
5. Key-provision worker calls HL `approveAgent` API to register `agent_address` as authorized delegate of `hl_user_address` (master key public address)
6. Only after HL confirms registration: worker sets `hl_custodial_wallets.key_status='active'`
7. Bot start is enqueued automatically

**Private keys never leave KMS.** All HL order signing goes through the Signing Lambda; only the Signing Lambda IAM role holds `kms:Sign` permission. No key material appears in app memory, logs, or database rows.

**KMS failure handling:**
- *During key generation (steps 2-3):* Abort provisioning, no row created, enqueue retry (max 3 attempts with exponential backoff). On final failure: E-EXBOT-027 alert sent via `notification` queue; admin must manually re-trigger key-provision job via admin panel. User does NOT need to re-deposit — funds remain in BnzaExVault.
- *During HL approveAgent call (step 5):* Row already exists with `key_status='provisioning'`; retry via key-provision queue (max 3 attempts). On final failure: E-EXBOT-027 alert sent via `notification` queue; admin must manually re-trigger from `provisioning` row via admin panel. User does NOT need to re-deposit.
- *During hedge-sync signing:* Signing Lambda failure aborts the signing operation; hedge-sync worker transitions bot to SAFE_MODE. Admin is alerted. Recovery follows standard SAFE_MODE path.

**Key rotation:** New KMS key pair generated; old agent key row set to `key_status='superseded'`; new row set to `key_status='active'` — atomically in the same transaction. Old key is deregistered from HL via `approveAgent` with revocation call.

**Acceptance criteria:** A DB dump of `hl_custodial_wallets` contains no plaintext private key material. Log audit shows no raw key values. A bot start with `key_status='active'` proceeds to preflight. A bot start when no `active` row exists is blocked with E-EXBOT-017. KMS failure during key generation results in admin notification with no partial key row left active. Signing Lambda is the only IAM principal allowed to call `kms:Sign`.

---

### FR-EXBOT-091 — HL Rate Limiter (ElastiCache Redis)
**Trace:** FM-XB-03
**Priority:** P0

An ElastiCache Redis atomic token bucket implements a sliding-window rate limiter for all outbound Hyperliquid API calls. BNZA operating budget: 800 weight/min (67% of HL's hard limit of 1,200 weight/min). Each HL API call category has a known weight; the caller declares the weight before the call is made. If the declared weight would exceed the remaining budget in the current window, the rate limiter returns `{allowed: false, retryAfterMs}` and the caller re-queues the message with the indicated delay. The weight window resets every 60 seconds. Multiple Lambda invocations share a single ElastiCache Redis cluster endpoint. Rate limit operations are atomic via Lua script to prevent race conditions between concurrent Lambda invocations.

**Acceptance criteria:** Total HL API weight consumed in any 60-second window does not exceed 800. A caller receiving `{allowed: false}` must not proceed with the HL call. Weight accounting covers all 5 HL endpoint categories (clearinghouseState, marginSummary, openOrders, placeOrder, cancelOrder). Rate-limit weight must be consumed after lock acquisition — ordering: lock → weight → call (OQ-EXBOT-15). On a rate-limit hit while holding the lock, the worker must release the lock and retry with backoff; it must not hold the lock through the wait window.

---

### FR-EXBOT-092 — User Lock (Postgres Advisory Lock via Aurora PostgreSQL)
**Trace:** FM-XB-03, FR-EXBOT-026
**Priority:** P0

A Postgres advisory lock (`pg_try_advisory_lock` / `pg_advisory_unlock`) provides a database-native mutex preventing concurrent HL mutations for the same user. The lock key is derived from `user_id` (bigint). Interface: `acquire(userId)` → boolean (immediate, non-blocking); `release(userId)` → void (always in finally block). No TTL-based auto-expiry — the lock is tied to the Aurora PostgreSQL connection lifecycle; Lambda invocation timeout governs maximum lock hold time. The `idempotencyKey` pattern `hedge-sync:{botId}:{stateVersion}` continues to prevent duplicate execution on message redelivery; replay result is cached in `queue_idempotency` table. ElastiCache Redis is retained for rate-limit bucket (FR-EXBOT-091) and pool slot0 cache (FR-EXBOT-093) only — not used for user locking.

**Acceptance criteria:** Two hedge-sync workers for the same user cannot hold the advisory lock simultaneously (database-enforced). Failed `pg_try_advisory_lock` re-queues the message; no HL call is made. Lock is always released in finally block. Replay prevention via `idempotencyKey` in `queue_idempotency` table prevents reprocessing the same stateVersion twice.

---

### FR-EXBOT-093 — Pool Slot0 Cache (ElastiCache Redis)
**Trace:** FM-XB-03
**Priority:** P0

ElastiCache Redis provides a shared cache for Uniswap V3 pool slot0 data (`sqrtPriceX96`, `currentTick`, `blockNumber`). The Fargate HL WS Poller writes to this cache at an interval defined by the Phase 0 NV-12 verification result (OQ-EXBOT-03). All light-check Lambda workers read from this cache instead of making individual RPC calls to the RPC provider. Cache staleness older than 2× the refresh interval is logged as a warning and the Fargate poller initiates a forced refresh.

**Acceptance criteria:** 10,000 concurrent light-check workers make at most 1 RPC call per refresh interval (via the Fargate poller), not 10,000. A stale cache (2× refresh interval) triggers a forced Fargate poller refresh and a warning log entry. The `blockNumber` field in the cache monotonically increases — a cache value with a lower `blockNumber` than a prior read is treated as a cache regression and triggers a re-fetch.

---

### FR-EXBOT-090 — Operator Facade API
**Trace:** FM-XB-06, US-EXBOT-012
**Priority:** P1

The OPERATOR shall expose four endpoints under `/api/exbot/*`, each proxied to ExBot Lambda via API Gateway with HMAC Lambda Authorizer. ExBot Lambda is not internet-accessible. Endpoints: `POST /api/exbot/start`, `GET /api/exbot/status/{botId}`, `POST /api/exbot/close`, `POST /api/exbot/margin`. The OPERATOR does not own any ExBot business logic; it only forwards requests.

**Acceptance criteria:** Direct HTTP requests to ExBot Lambda return 403 (not publicly accessible). All four endpoints are reachable via the Operator Facade. OPERATOR logs show API Gateway calls for each proxied request.

---

## 3. Non-Functional Requirements

| NFR ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-EXBOT-001 | Throughput | System must scan 10,000 bots in a 5-minute window (33.3 bots/sec sustained). | P0 |
| NFR-EXBOT-002 | Latency | One hedge-sync should complete within 30 seconds under normal conditions. | P0 |
| NFR-EXBOT-003 | SLA | `user_redeem` hedge close must complete within 5 minutes of event detection. Overrun triggers admin escalation. | P0 |
| NFR-EXBOT-004 | Rate Limit | HL API usage must not exceed 800 weight/min (67% of the 1,200/min hard limit). | P0 |
| NFR-EXBOT-005 | Aurora PostgreSQL Write Budget | `bot_runtime_state` written only on diff. `next_light_check_at` batch-updated per shard (1 stmt). No unconditional UPDATE per light-check. | P0 |
| NFR-EXBOT-006 | Security | Master key + agent key generated and retained in AWS KMS; private keys never leave KMS; all signing via Signing Lambda (IAM role kms:Sign only); no key material in app memory or logs. Table `hl_custodial_wallets` stores public addresses only. | P0 |
| NFR-EXBOT-007 | Idempotency | `queue_idempotency.message_id` UNIQUE prevents double execution. Cloid deterministic prevents double HL order. | P0 |
| NFR-EXBOT-008 | Precision | All hedge, stop, and margin computations use BigDecimal. Float/number arithmetic forbidden for financial values. | P0 |
| NFR-EXBOT-009 | Multi-Chain | Base + Optimism from Phase 1. `wethIndex` verified per chain at LP open. Not hardcoded. | P0 |
| NFR-EXBOT-010 | Availability | SAFE_MODE and `bot_safe_close` lead to autonomous recovery. Neither is a terminal state. | P0 |
| NFR-EXBOT-011 | Concurrency | Outbound HL API call concurrency is governed by the rate limiter (FR-EXBOT-091, 800 weight/min). No per-invocation connection limit is imposed on AWS Lambda. | P0 |
| NFR-EXBOT-012 | Scalability | Phase A: 1 Aurora PostgreSQL shard. Phase B: 4 shards. Phase C: 16 shards (deferred, requires 10k-equivalent load benchmark). `shard_id = hash(bot_id) % shard_count`. | P0 |

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
| BR-EXBOT-009 | Aurora PostgreSQL schema changes after Phase A deploy: ADD COLUMN only. DROP and RENAME of existing columns are forbidden. | P0 |
| BR-EXBOT-010 | ExBot Lambda (`apps/bnza-exbot/`) must not be co-deployed with OPERATOR (`apps/bnza-operator/`). They communicate via API Gateway + HMAC Lambda Authorizer only. | P0 |
| BR-EXBOT-012 | Only one `hl_custodial_wallets` row per user may have `key_status='active'` at any time. This constraint is enforced at the database level. `provisioning` rows are not subject to this constraint — a user may have one `provisioning` row while no `active` row exists yet. Source: FR-EXBOT-080. | P0 |
| BR-EXBOT-013 | Agent key rows are immutable after write — revocation and rotation are non-destructive. `revoked` and `superseded` rows must never be overwritten or deleted; they are retained for audit purposes. Source: FR-EXBOT-080. | P0 |
| BR-EXBOT-014 | During key rotation, the old `hl_custodial_wallets` row's `key_status='superseded'` and the new row's `key_status='active'` must be committed atomically in the same transaction. There is no window where both rows are `active` or neither is `active`. Source: FR-EXBOT-080. | P0 |
| BR-EXBOT-015 | One wallet address belongs to exactly one organization at any time. Multiple organization memberships for the same address are forbidden. Fee attribution and access control must rely on this single-membership invariant. Source: OQ-EXBOT-21. | P0 |

---

## 5. Error Codes

| Code | Condition | Message | HTTP |
|---|---|---|---|
| E-EXBOT-001 | One-bot policy violation | "You already have an active ExBot. Close or wait for the existing bot to finish." | 409 |
| E-EXBOT-002 | Insufficient HL margin at preflight | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z USDC to BNZP." | 400 |
| E-EXBOT-005 | Builder fee not approved | "HL builder fee (5bps) approval required before starting ExBot." | 400 |
| E-EXBOT-006 | LP mint simulation failed | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | 400 |
| E-EXBOT-007 | HL order rejected (insufficient margin during sync) | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional USDC to BNZP." | 502 |
| E-EXBOT-008 | HL API unreachable | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | 503 |
| E-EXBOT-009 | Stop placement failed | "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | 502 |
| E-EXBOT-010 | user_redeem SLA breached | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | — (internal alert) |
| E-EXBOT-011 | Reconcile mismatch | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | — (internal) |
| E-EXBOT-012 | Close attempted on already-closed bot | "Bot is already closed. No action needed." | 409 |
| E-EXBOT-013 | Pause attempted in SAFE_MODE | "Bot is in Safe Mode. You can close the bot instead." | 409 |
| E-EXBOT-017 | Bot start preflight — no `hl_custodial_wallets` row with `key_status='active'` for this user | "Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete." | 400 |
| E-EXBOT-018 | bot_safe_close hedge close failed after 3 retries — `close_operations.state='residual_hl_liability'` | "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability." | — (internal alert) |
| E-EXBOT-024 | user_redeem hedge close failed after 3 retries or reconcile mismatch — `close_operations.state='residual_hl_liability'` | "User redemption hedge close failed. Manual intervention required." | — (internal admin alert) |
| E-EXBOT-025 | Bot start preflight — no confirmed deposit in `BnzaExVault` for this user | "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." | 400 |
| E-EXBOT-026 | HL rejects IOC order at bot-start hedge open | "Hedge order rejected by Hyperliquid. Bot entered Safe Mode." | — (internal alert) |
| E-EXBOT-027 | Key-provision failed after max 3 retries (KMS or HL approveAgent) | "Key-provision failed for user {wallet_address} after 3 retries. Manual re-trigger required via admin panel." | — (internal alert) |
| E-EXBOT-028 | LP mint on-chain tx reverted or timed out at bot-start — `bots.lifecycle_state='error'`; no funds moved | "Bot startup failed: LP mint transaction did not complete. No funds were moved. Please try again or contact support." | 502 |
| E-EXBOT-029 | `bots.status='error'` — bot requires admin intervention; displayed on status screen | "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close." | 200 |
| E-EXBOT-030 | GET /status — Investor wallet_address does not match bot.user_wallet_address | "Access denied: this bot does not belong to your account." | 403 |
| E-EXBOT-031 | `bots.status='paused'` — bot is paused; displayed on status screen | "Bot Paused. Hedge and LP are maintained. You may still redeem." | 200 |

---

## 6. Screen Inventory

ExBot is a **backend-only module**. No UI screens are owned by this module. The POOL UI (PTL-05) renders ExBot status data returned by the Operator Facade API — those screens are specified in the `bnza-pool` module.

The Operator admin view for ExBot management (force-close, key-provision monitoring) is rendered by PTL-02 (ADMIN) and specified in the `admin/bnza-admin` module.

---

## 7. Use Case Inventory

Full UC specs in `../usecases/`. Each file contains: actors, preconditions, main success scenario, alternate flows, postconditions, and FR mapping.

| UC slug | Description | FR trace |
|---|---|---|
| `uc-bot-start` | Start ExBot: user calls POST /api/exbot/start → preflight (vault balance + margin + key_status + builder fee + LP sim) → LP mint → hedge open → stop place → active. Key-provision (KMS + approveAgent) runs automatically at deposit time (see F-03a). | FR-EXBOT-001–004, 020, 030–031 |
| `uc-light-check` | Periodic scan (zero HL calls) → fan-out to hedge-sync or price-near-stop-audit | FR-EXBOT-012, 013, 014, 015, 016, 032 |
| `uc-hedge-sync` | Delta-only hedge adjustment + INV-STOP protocol + post-order reconcile | FR-EXBOT-020, 021, 022, 024, 025, 026, 027, 035, 036 |
| `uc-user-close` | User-initiated close: user clicks "Close Bot" on BNZP UI → Operator API → user_close Worker → Postgres advisory lock → hedge close (Agent CMK) → vaultClose on-chain (Master CMK) → HL-portion settlement | FR-EXBOT-070 |
| `uc-bot-safe-close` | Hedge-first system close → executeStrategy(RedeemStrategyV1) → RedemptionQueue FIFO payout to user | FR-EXBOT-070, 072, 073 |

---

## 8. User Story Inventory

Full story files in `../userstories/`. 11 active stories across 4 epics (US-011 retired).

| Story ID | Epic | Actor | Description | Priority |
|---|---|---|---|---|
| US-EXBOT-001 | Investor Lifecycle | USDC Investor | Start ExBot (user-initiated via POOL UI; key already provisioned automatically at deposit) | P0 |
| US-EXBOT-002 | Investor Lifecycle | USDC Investor | Monitor active ExBot status | P0 |
| US-EXBOT-003 | Investor Lifecycle | USDC Investor | Pause and resume ExBot | P1 |
| US-EXBOT-004 | Investor Lifecycle | USDC Investor | Close ExBot and redeem funds (user_redeem) | P0 |
| US-EXBOT-005 | System Operations | ExBot System Operator | Light-check without HL calls (10k scale) | P0 |
| US-EXBOT-006 | System Operations | ExBot System Operator | Delta-only hedge-sync + cloid + reconcile | P0 |
| US-EXBOT-007 | System Operations | ExBot System Operator | LP range rebalance + lp_operations recovery | P0 |
| US-EXBOT-008 | Risk & Safety | ExBot System Operator | Circuit breaker open/half_open/close | P0 |
| US-EXBOT-009 | Risk & Safety | ExBot System Operator | bot_safe_close + automatic re-entry closed loop | P0 |
| US-EXBOT-010 | Risk & Safety | ExBot System Operator | Margin warning/critical → SAFE_MODE | P0 |
| US-EXBOT-012 | Admin | ExBot Admin (zen) | Admin force-close + emergencyTransfer (Operator-only when paused, no recipient param, EmergencyRecovery event) | P1 |

---

## 9. Open Questions

| OQ ID | Question | Impact | Status |
|---|---|---|---|
| OQ-EXBOT-01 | NV-1: HL `marginSummary` exact API field names for `marginBalanceUsd` | Blocks FR-EXBOT-060 final implementation | **Closed** — Confirmed by zen: `marginSummary` (and `crossMarginSummary`) contains `accountValue`, `totalMarginUsed`, `totalNtlPos`, `totalRawUsd`. The equivalent of `marginBalanceUsd` is `accountValue`. Numerator/denominator for the margin ratio to be pinned together with SAFE_MODE thresholds at Phase 0. |
| OQ-EXBOT-02 | NV-3: Does HL support place-before-cancel stop replacement? Determines §19.5 path (a) vs (b). | Blocks FR-EXBOT-035 (INV-STOP protocol path) | **Need to re-verify** — Conflict between prior closure and latest zen guidance. Prior closure (spec): "place-before-cancel is required — path (a); no 0-stop window permitted." Latest zen answer: "Principle first: the INV-STOP protocol exists to avoid any window with no stop in place, so path (b) place-then-cancel is preferred — or better, HL's order-modify endpoint if it applies to trigger orders (atomic replacement). Please verify on HL testnet: (1) can two same-direction trigger orders coexist momentarily, (2) does modify work for stops. If neither, fall back to (a) cancel-then-place with minimal gap and immediate retry." Dev to verify on HL testnet and share result before §19.5 is finalized. |
| OQ-EXBOT-03 | NV-12: Pool addresses + `wethIndex` for USDC/WETH 0.3% on Base + Optimism | Blocks FR-EXBOT-004 dual-chain LP open | **Closed** — Confirmed by zen: Base: USDC/WETH 0.3% pool = `0x6c561B446416E1A00E8E93E221854d6eA4171372` (verified in production — appears in rebalance tx logs). WETH (`0x4200…`) < USDC (`0x8335…`) by address ordering → WETH = token0 → `wethIndex = 0`. Optimism: pool = `0xc1738D90E2E26C35784A0d3E3d8A9f795074bcA4` (from production `bot_positions`). USDC (`0x0b2C…`) < WETH (`0x4200…`) → WETH = token1 → `wethIndex = 1`. zen note: "Please still assert token0/token1 on-chain at startup rather than trusting config." |
| OQ-EXBOT-04 | NV-13: HL ETH-USD perp minimum order size / dust handling rules | Blocks FR-EXBOT-022 (minimum delta threshold) | **Need to re-verify** — Dust policy confirmed by zen: if |required delta| < min order size, do not trade — carry the residual delta to the next hedge-sync, where it aggregates with new drift and executes once above the minimum. Never round up to the minimum (that over-hedges). Carried dust counts inside the allocation tolerance band (see OQ-EXBOT-20). Exact min order size value: zen notes "please pull from HL specs/API (external fact)" — Dev to verify against current HL docs/testnet and pin the value before FR-EXBOT-022 implementation. |
| OQ-EXBOT-05 | NV-14: HL builder fee 5bps approval flow — on-chain transaction or API call? | Blocks FR-EXBOT-002 preflight step 4 | **Need to re-verify** — zen's understanding: HL's builder-fee approval is an HL action — an EIP-712-signed request submitted via the API (not an L1 on-chain transaction). zen note: "Please confirm against current HL docs (external spec) and map it into the preflight step; share the final signature UX (how many signatures, when) once verified." Dev to confirm on HL testnet and document the final signature flow before FR-EXBOT-002 preflight step 4 is finalized. |
| OQ-EXBOT-06 | Margin thresholds (0.55/0.75) — finalized via Phase 0 backtest (zen task) | FR-EXBOT-060 values pending | Open — Confirmed by zen: implement with candidates (lower 0.55 / upper 0.75) as config-driven placeholders. zen will confirm or adjust the values at Phase 0 without code changes. |
| OQ-EXBOT-07 | `stopSafetyFactor` Phase B+ value — finalized via Phase 0 backtest (zen task) | FR-EXBOT-030 Phase B value pending | Open — Confirmed by zen: finalized after Phase 0. Keep it config-driven; proceed with the spec placeholder for implementation and testing. |
| OQ-EXBOT-08 | BnzaExVault final ABI — confirmed when zen deploys contract at Phase 0 | IC-EXBOT-002 (integration constraints) | Open — Confirmed by zen: final ABI JSON delivered at Phase 0 deployment, together with Base + Optimism addresses. Addresses to be injected via AWS Secrets Manager (supersedes earlier "CF Secrets Store" wording). Until then, code against the interface defined in the spec; any signature change at deployment will be communicated explicitly. |
| OQ-EXBOT-09 | ElastiCache Redis pool slot0 cache refresh interval — determined by Phase 0 NV-12 RPC verification | Blocks FR-EXBOT-093 TTL configuration | **Closed** — Confirmed by zen: provisional refresh interval = 60s (config-driven). Stale threshold = 2× 60s = 120s, consistent with FR-EXBOT-093 "2× refresh interval" policy. To be finalized after Phase 0 NV-12 RPC cost verification — may tighten if measurements allow. UC step 7 and A1 updated to "> 2× refresh interval (provisional: 120s)". |
| OQ-EXBOT-10 | `range_boundary_near` exact computation: is "90% to upper/lower" measured in tick distance or price distance? Formula needed before implementation. E.g. tick-based: `currentTick >= tickUpper - 0.10 × (tickUpper - tickLower)` vs price-based: `sqrtPrice >= sqrtUpper × 0.90`. Owner: zen/SOTATEK to confirm. | Blocks FR-EXBOT-012 `range_boundary_near` implementation | **Closed** — Confirmed by zen: tick-based. Formula: `currentTick >= tickUpper − 0.10 × (tickUpper − tickLower)` (and mirrored for the lower side: `currentTick <= tickLower + 0.10 × (tickUpper − tickLower)`). Ticks are Uniswap's native log-price representation; integer math is deterministic; all LP-side range logic is tick-based. Note: current code implementation is price-based — Dev to align code to tick-based per this confirmation. |
| OQ-EXBOT-11 | `lpValueUsd` formula: how is `bot_runtime_state.lp_value_usd` computed and updated? Candidate: `(lpEthAmount × uniPoolPrice) + lpUsdcAmount` — but SPEC v5.2.6 does not define it explicitly. Owner: zen to confirm or SOTATEK to propose. | Blocks FR-EXBOT-012 `drift_threshold` (lpValueUsd × 3% term) | **Closed** — Confirmed by zen: `lp_value_usd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount`, principal only (exclude uncollected fees/tokensOwed); price source = Uniswap pool slot0 price (not external oracle). Updated at hedge-sync / full-check. Note: OQ-11 unblocks FR-EXBOT-012 `drift_threshold` for light-check only — does NOT affect A11 bot-start reconcile threshold (which is exact fill, no percentage tolerance). |
| OQ-EXBOT-12 | 7d funding APR aggregation formula: how is `funding_alert` condition (`7d APR < −15%`) computed from `funding_daily_metrics`? Candidate (from SPEC v5.2.6 §7.5): sum of latest 7 rows `funding_net_usd`, annualize relative to LP capital — but exact annualization formula not specified. Owner: zen to confirm. | Blocks FR-EXBOT-012 `funding_alert` implementation | **Closed** — Confirmed by zen: `funding_apr_7d_pct(%) = ( Σ funding_net_usd latest 7 rows / lp_value_usd ) × (365/7) × 100`. Alert fires when < −15%. Denominator = `lp_value_usd` at evaluation time. If fewer than 7 rows exist, annualize over n available days (× 365/n). `lp_value_usd` is the right yardstick — keeps funding APR directly comparable to fee APR (same denominator). `funding_rolling_metrics.funding_apr_7d_pct` populated by `bnza-market-cron` (not yet deployed v1 — fallback: `fundingRate × 8760`). AC-LC-09 unblocked when `bnza-market-cron` deploys. |
| OQ-EXBOT-13 | delta=0 behavior in hedge-sync: if computed delta=0, should the Lambda skip HL order entirely and proceed directly to stop replacement, or abort the sync? Owner: Tech Lead. | Blocks UC-EXBOT-hedge-sync step 5 / A6 | **Closed** — Confirmed by zen: skip the HL order, proceed to stop replacement. delta = 0 only means the position size is correct — the appropriate stop level may still have moved with price. Aborting would create the inverted situation where calm periods (stable delta) leave stops stale. Order placement and stop freshness are independent concerns. Note: current code (`rebalance.ts` line 83-84) returns `no_op_dust` immediately with no stop replacement — Dev to align code to this confirmed behavior. |
| OQ-EXBOT-14 | `marginSummary` fetch ordering in hedge-sync preflight: does the Lambda fetch marginSummary before or after acquiring Redis Redlock? Ordering affects lock TTL design. Owner: Tech Lead. | Blocks FR-EXBOT-060 preflight step ordering | **Closed** — Confirmed by zen: fetch after acquiring `UserLockDO`. Reading before the lock invites a stale-read race (state can change while waiting for the lock), defeating the lock's purpose. All decision inputs must be fetched inside the critical section; size the lock TTL to cover fetch + decide + execute (rate-limit retries excluded — see OQ-EXBOT-15). |
| OQ-EXBOT-15 | HL Rate Limiter (Redis) + User Lock (Redis Redlock) interaction in hedge-sync: should rate-limit weight be consumed before or after lock acquisition? Determines retry behavior on rate-limit hit while lock is held. Owner: Tech Lead. | Blocks FR-EXBOT-091 + hedge-sync flow | **Closed** — Confirmed by zen: consume rate-limit weight after lock acquisition (no lock → no HL call → no wasted weight; ordering: lock → weight → call, consistent with OQ-EXBOT-14). On a rate-limit hit while holding the lock: release the lock and retry with backoff — holding a lock through a wait window stalls other users' cycles. The interrupted cycle simply completes on the next sync (idempotent by design). |
| OQ-EXBOT-16 | Admin reject path for agent key: when admin rejects a pending key, what is the resulting row status — remain `pending`, set to `rejected`, or delete? | Blocks UC-EXBOT-agent-key A4 admin reject enum | **Closed (out of scope)** — Manual agent key flow retired per SOT §C-6. UC-EXBOT-agent-key is retired. Admin reject path no longer applicable — custodial wallet model (Change B) fully manages key lifecycle via KMS; no manual approval flow exists. |
| OQ-EXBOT-17 | `hlMarkPrice` data source in light-check step 11: given the zero-HL-calls invariant (BR-EXBOT-003), what is the authoritative source for mark price used to evaluate stop trigger? Candidate: `bot_runtime_state.eth_price_usd`. Staleness policy needed. Owner: Tech Lead. | Blocks UC-EXBOT-light-check step 11 | **Closed** — Confirmed by zen: primary source = `bot_runtime_state.eth_price_usd` (persisted by the latest hedge-sync/full-check). Staleness policy: record the value's timestamp; if age exceeds the limit (provisional 15 min, config-driven, ≈ a few hedge-sync cycles), do NOT resolve the stop trigger on the stale value — promote to full-check instead. A stale price must fail toward more inspection, never toward "no trigger". Final stale limit to be confirmed at Phase 0. Note: current code uses Redis HlMark price key (Fargate WS Poller) as primary with 120s stale threshold — Dev to align to `eth_price_usd` primary + 15 min threshold per this confirmation. |
| OQ-EXBOT-18 | SAFE_MODE: when does SAFE_MODE occur, and what are the required Worker actions when light-check evaluates the system to SAFE_MODE? | Blocks FR-EXBOT-060 behavior spec; BR-EXBOT SAFE_MODE definition | **Closed** — Confirmed by zen: SAFE_MODE is the defensive state entered when hedge-account margin health crosses the lower threshold (candidate: ratio < 0.55, exit > 0.75 — hysteresis; final values after Phase 0, see OQ-EXBOT-06). When light-check evaluates SAFE_MODE, the Worker must: (1) stop opening/expanding positions; (2) KEEP existing hedge and stop orders — never leave the LP unhedged; (3) raise an escalation; (4) promote to full-check to measure actual margin; (5) remain in SAFE_MODE until the upper threshold is recovered — no automatic re-entry below it. |
| OQ-EXBOT-19 | Trading pair scope: should the execution bot support a wider range of trading pairs beyond ETH/USDC to make the system easier to scale in the future? | FR-EXBOT-004 scope; system configurability | **Closed** — Confirmed by zen: ETH/USDC only for Phase 0–1. However, the pair must be config-driven rather than hardcoded (pool address, tokens, HL symbol as configuration parameters). No generic multi-pair engine now (testing surface explodes), but adding a pair later must be a config entry + verification, not a refactor. |
| OQ-EXBOT-20 | Allocation drift tolerance: how should the system handle transient allocation drift between on-chain (Uni) and off-chain (HL) venues during async rebalance execution windows? | Blocks rebalance flow; FR-EXBOT-022 drift handling | **Closed** — Confirmed by zen: the two venues can never be updated atomically — account for drift by design. Principles: (1) define a tolerance band around the target allocation; within band, do nothing; (2) beyond band, converge toward target on subsequent hedge-sync cycles — no one-shot exactness required; (3) transient drift during an execution window is normal, not an alert; (4) escalate only if the deviation persists across cycles. Concrete band value is a strategy parameter — finalized after Phase 0. |
| OQ-EXBOT-21 | Multi-tenant address membership: should one address be allowed to belong to multiple organizations, or restricted to a single organization? | Blocks BR-EXBOT multi-tenant access control; fee attribution | **Closed** — Confirmed by zen: restrict to a single organization per address — consistent with the route-lock principle across the BNZA ecosystem (a wallet belongs to exactly one route/tenant: Normal, WL, or IB on the LP side; same rule applies here). Multiple memberships would make fee attribution and access control ambiguous. One wallet = one organization. |
| OQ-EXBOT-22 | Fee forwarding timing: should collected organizer fees be forwarded immediately after PnL realization, or held within the contract? | Blocks contract fee flow design; IC-EXBOT-002 | **Closed** — Confirmed by zen: forward organizer fees immediately after PnL realization. The contract must never custody accumulated USDC beyond in-flight amounts. Same minimal-custody principle as the LP-side fee flows. |
| OQ-EXBOT-23 | HL reduce-only stop: behavior when stop size < actual position size at trigger time — HL partially closes the position and leaves the remainder unprotected. §19.3 stop audit currently checks `stop size matches DB` but does not verify stop size against actual HL position size (`clearinghouseState`). If DB is stale (prior reconcile underestimate), audit passes but stop is effectively undersized. Clarify: (1) should §19.3 compare stop size against live `clearinghouseState` position size, not only DB? (2) should §19.5 add a guard to reject a confirmed size that is lower than the DB-recorded position size? | Blocks §19.3 audit correctness / §19.5 confirmed-size trust assumption | **Open** |
| OQ-EXBOT-24 | `funding_24h_apr_immediate_l1` computation in Phase A: Phase A has no `funding_rolling_metrics` table (Phase B+). The spec documents 7d annualized APR as `(sum of funding_net_usd over 7 rows of funding_daily_metrics) / LP_capital_usd × 365 / 7`. For the 24h figure, the assumed formula is: `(funding_net_usd from the latest 1 row of funding_daily_metrics) / LP_capital_usd × 365`. Confirm: (1) is this the correct source row (most recent `funding_daily_metrics` entry)? (2) is the annualization factor 365? (3) is `LP_capital_usd` the denominator, and if so, which snapshot — beginning-of-day or latest? | Blocks FR-EXBOT-012 AC and any funding APR display logic | **Open** |
| OQ-EXBOT-25 | Notification delivery channel: `notification_messages` schema records `purpose: user/admin alert`, `producer: any worker`, `consumer: notification worker`. The spec does not define how the notification worker actually delivers the alert to the end recipient. Current assumption is that the notification worker calls a POOL UI API to set a banner/alert state. Confirm: (1) what is the delivery mechanism — POOL UI API call, SQS fan-out to a separate alerting service, email/SMS gateway, or another channel? (2) is there a defined API contract or endpoint on the POOL UI side that the notification worker must call? (3) are user alerts and admin alerts delivered via the same channel or separate paths? | Blocks notification worker implementation; IC-EXBOT scope for POOL UI integration | **Open** |
| OQ-BACKTEST-01 | Backtesting scope: Hyperliquid only provides the most recent 5,000 candles (≈7 months at 1H). Should the backtest period be limited to HL's available data, or should longer historical backtests be supported via a third-party data source? | Backtest module scope and implementation approach | **Closed** — Confirmed by zen (Proposal §10 OQ#2): Option 1 — limit backtest scope to Hyperliquid's available data (1H × ~7 months). SOTATEK's backtest implementation is for behavioral verification / regression, not strategy research (strategy-parameter validation is done on zen's side), so 7 months of 1H candles with accurate fee/funding math is sufficient. Third-party data integration is out of scope for now — revisit only if a concrete need appears. |

---

## 10. Integration Constraints

| IC ID | External Dependency | Constraint | Blocks |
|---|---|---|---|
| IC-EXBOT-001 | Hyperliquid REST API (info + exchange endpoints) | BNZA budget capped at 800 weight/min. All outbound calls routed through ElastiCache Redis rate limiter (FR-EXBOT-091). Weight table per endpoint category must be maintained in code. HL API schema changes (field renames, endpoint deprecations) require immediate SRS review. | FR-EXBOT-060, 091 |
| IC-EXBOT-002 | BnzaExVault Solidity contract (LP NFT custody, redeem) + RedemptionQueue (FIFO payout) | SOTATEK integrates via ABI only — no contract development. Final ABI confirmed when zen deploys at Phase 0 (OQ-EXBOT-08). Until ABI is confirmed, vault.executeStrategy(RedeemStrategyV1, user, botId, params) and RedemptionQueue.createRequest/fulfillRequest calls are stubbed. uninvestedBalanceOf() is no longer part of the integration surface. Contract address (Base + Optimism) must be injected via AWS Secrets Manager, not hardcoded. | FR-EXBOT-015, 070, 073 |
| IC-EXBOT-003 | Uniswap V3 Pool (Base + Optimism, USDC/WETH 0.3%) | Pool addresses and `wethIndex` confirmed via Phase 0 NV-12 verification (OQ-EXBOT-03). ElastiCache Redis pool slot0 cache (FR-EXBOT-093) must be pointed to the correct pool address per chain. Pool address changes (e.g., pool migration) require coordinated deploy of new Fargate poller configuration. | FR-EXBOT-004, 093 |
| IC-EXBOT-004 | AWS Platform (Lambda, Aurora PostgreSQL Serverless v2, SQS, ElastiCache Redis, Secrets Manager, KMS, ECS Fargate, API Gateway) | ExBot Lambda is deployed on AWS Lambda, not co-deployed with OPERATOR. API Gateway + HMAC Lambda Authorizer is required for all Facade API calls. Aurora PostgreSQL concurrent write limits apply; batch patterns (FR-EXBOT-013) are required by design. AWS regional outages are a SAFE_MODE trigger condition. | All FR-EXBOT-* |
| IC-EXBOT-005 | AWS KMS (per-user master key + agent key custody) | Private keys are generated and retained inside KMS HSM — they never leave KMS. All signing requests go through the Signing Lambda; only the Signing Lambda IAM role holds `kms:Sign` permission. KMS credentials are injected via AWS Secrets Manager (not hardcoded). KMS API rate limits apply — key-provision worker must implement backoff on ThrottlingException. KMS failure during key generation aborts provisioning and enqueues retry (max 3); final failure triggers admin alert. KMS failure during hedge-sync signing transitions bot to SAFE_MODE. Custodial wallet metadata stored in `hl_custodial_wallets` table (public addresses only). | FR-EXBOT-080 |
