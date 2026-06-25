---
type: frd
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-18
owner: "@hienduong"
version: 0.1.0
sources:
  - SPEC_v5.2.6_EN.md
  - Google Doc: EXBOT System & Smart Contract Overview (Daniel, June 2026)
  - Google Sheet: BNZA ExBot Feature Tracker
changelog:
  - 2026-06-24 | /ba-do | remove §7 Open Questions — 8 OQs migrated to SRS §9 (OQ-EXBOT-01..08); SRS is source of truth
  - 2026-06-18 | /ba-do hld-decisions | ACT-M removed; bot_safe_close flow updated (drop park/re-entry); lifecycle states cooldown/parked removed; emergencyTransfer authority updated
  - 2026-06-12 | /ba-impact | gap fill v5.2.6 X-5: §4.2 FR-011 add deltaErrorUsd formula + 3-way price split (uniPoolPrice/hlMarkPrice/hlOraclePrice); add stop_replacing_started_at primary detection bullet
  - 2026-06-12 | /ba-start frd | initial draft from SPEC v5.2.6 + Google Doc + Sheet
links:
  - docs/sotatek/ba/plans/bnza-sotatek-260519-0000/01_intake/intake.md
  - docs/sotatek/ba/plans/bnza-sotatek-260519-0000/02_backbone/backbone.md
---

# FRD — BNZA-EXBOT Infrastructure (Module 4)

## 1. Module Overview

| Attribute | Value |
|-----------|-------|
| Module | BNZA-EXBOT Infrastructure |
| Line | Line 2 (independent of Line 1 WL ecosystem) |
| Scope | Backend infrastructure only. Trading strategy logic is zen-proprietary. |
| Architecture | Standalone Cloudflare Worker (`apps/bnza-exbot/`). NOT co-deployed with OPERATOR. |
| Entry point | OPERATOR thin facade at `/api/exbot/*` → service binding → ExBot Worker (internal token auth) |
| Chain support | Base + Optimism from Phase 1 (v5.2.6 Theme E) |
| Phase A limit | 1 active ExBot per user |
| Source of truth | SPEC v5.2.6 (zen-approved). Where this FRD conflicts with SPEC, SPEC prevails. |

---

## 2. Actors

| Actor ID | Actor | Role |
|----------|-------|------|
| ACT-I | Investor (End User) | Deposits USDC, starts/monitors/closes ExBot via POOL UI |
| ACT-O | OPERATOR (System) | Executes strategy via queue workers; calls BnzaExVault and HL |
| ACT-A | Admin (zen) | Manages system config, force-closes, emergency operations |
| ACT-Z | zen | Owns trading algorithm; provides interface specs only |

> **Emergency authority (HLD 2026-06-18):** `emergencyTransfer(user, botId)` is executed by `OPERATOR_ROLE` when contract is paused. No recipient parameter — funds return to user's own address only. Emits `EmergencyRecovery` event. Multi-sig is not required.

---

## 3. System Boundary

**In scope (SOTATEK builds):**
- ExBot Cloudflare Worker (`apps/bnza-exbot/`)
- D1 schema (control_db + state_db_shard)
- Queue topology (10 queues)
- Durable Objects (HLRateLimitDO, UserLockDO, MarketDataDO)
- Hyperliquid Adapter (rate limit, cloid, error parser, delta-only adjust, reconcile)
- Operator Facade API (`/api/exbot/*` endpoints on OPERATOR side)
- Cron workers (bot-scan, deep-audit, metrics-rollup)
- Agent key storage (AES-GCM envelope encryption in D1)

**Out of scope (zen-proprietary):**
- Trading strategy logic (PositionCalc, hedge math formula, stop safety factor tuning)
- BnzaExVault Solidity contract development (zen scope; SOTATEK integrates via ABI)
- Phase 0 verification tasks (NV-1 to NV-14)
- Backtest module (separate Module 5)

---

## 4. Functional Requirements

### 4.1 Bot Lifecycle Management

#### FR-EXBOT-001 — Bot Initialization (PREFLIGHT)
**Priority:** P0

Before starting an ExBot, the system MUST run preflight checks in this order:
1. One-bot policy: `SELECT count(*) FROM bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')` — if result > 0, reject start
2. HL margin sufficiency: expected post-deposit margin balance ≥ `required_margin × preflight_buffer (2.0x)`
   - `required_margin = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`
   - If insufficient: block start, display "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL."
3. HL agent key approval status = `approved` and not expired
4. Builder fee approval confirmed (5bps)
5. LP mint simulation passes (slippage within tolerance)

On any check failure: return specific error, do not create bot record.

#### FR-EXBOT-002 — Bot Lifecycle State Machine
**Priority:** P0

Bot lifecycle is tracked in two fields:
- `bots.status` (coarse): `active | paused | closing | closed | safe_mode | error`
- `bots.lifecycle_state` (fine-grained, canonical): 18 states

**Initialization sequence:**
```
idle → preflight → lp_opening → lp_opened → hedge_pre_open →
hedge_post_confirmed → stop_placing → stop_verified → active
```

**Runtime states (from `active`):**
| State | Description |
|-------|-------------|
| `active` | Normal monitoring, light-check every 5 min |
| `lp_rebalancing` | LP range rebalance in progress; light-check skips |
| `hedge_stopped_cooldown` | Stop fired; hedge-sync suppressed; 4h cooldown |
| `lp_closing` | Close operation in progress |
| `closed` | Fully closed |
| `safe_mode` | No mutations; monitor only |
| `error` | Admin intervention required |

> **Note (HLD 2026-06-18):** `cooldown` and `parked` lifecycle states removed — park/redeploy feature dropped. After bot_safe_close, lifecycle transitions directly to `closed`.

**PAUSED behavior:** `bots.status='paused'` only. `lifecycle_state` keeps pre-pause value. Hedge and LP both maintained. No new mutations.

#### FR-EXBOT-003 — Pause/Resume
**Priority:** P1

- Pause: set `bots.status='paused'`. Do NOT close hedge. Do NOT close LP.
- Resume: restore `bots.status` to pre-pause coarse value.
- Light-check: skip when `status='paused'`.
- Deep-audit: continue every 6h even when paused.
- UI must distinguish: Pause = "hedge maintained" vs Close = "close everything, return USDC".

---

### 4.2 Queue Architecture

#### FR-EXBOT-010 — Queue Topology (10 queues)
**Priority:** P0

| Queue | Purpose | Producer | Consumer |
|-------|---------|---------|---------|
| `bot-scan` | Shard/window scan | Cron (1 min) | scan worker |
| `light-check` | Per-bot check (no HL) | scan worker | light-check worker |
| `hedge-sync` | Delta-only mutation candidate | light-check worker | hedge-sync worker |
| `reconcile` | Post-order reconciliation | hedge-sync worker | reconcile worker |
| `deep-audit` | Full HL state audit | Cron (6h) | deep-audit worker |
| `price-near-stop-audit` | Stop/range boundary priority audit | light-check worker | stop-audit worker |
| `partial_repair` | Partial reconcile / stop replace failure repair | hedge-sync worker | repair worker |
| `user_redeem` | Hedge close for instant redemption (SLA 5 min) | redeem event watcher | redeem worker |
| `notification` | User/admin alerts | any worker | notification worker |
| `metrics-rollup` | Hourly/daily aggregation | Cron (hourly) | rollup worker |

All queue `sendBatch` calls MUST go through `chunkSendBatch()` helper (CF max 100/call). Direct `queue.sendBatch()` is forbidden.

Every consumer MUST insert `message_id` with `state='started'` into `queue_idempotency` at start. UNIQUE conflict = duplicate delivery → return immediately.

#### FR-EXBOT-011 — Light-Check Logic
**Priority:** P0

Light-check MUST NOT touch Hyperliquid (HL weight = 0). Sources:
- D1 hot state (`bot_runtime_state.last_known_hl_short_size`)
- `MarketDataDO` (sqrtPriceX96, currentTick)
- Local TickMath (LP amount calculation)

Evaluate `RebalanceReason[]` (canonical enum, §7.6):
- `drift_threshold`: `deltaErrorUsd > max($25, lpValueUsd × 3%)` where `deltaErrorUsd = |targetShortEth − actualShortEth| × uniPoolPrice`
- `drift_relative`: `|target - actual| / target > 0.15`
- `range_out`: `rangeState != 'in'`
- `range_boundary_near`: price 90% to range upper/lower
- `margin_warning`: `hedge_legs.margin_status == 'warning'` (read from D1, no HL fetch)
- `funding_alert`: 7d funding < −15% APR
- `time_fallback`: 4h since last adjustment

**Price source rules (v5.2.6 X-5 — 3-way split, MUST NOT be interchanged):**
- `uniPoolPrice` — Uniswap V3 pool slot0 `sqrtPriceX96` via `MarketDataDO`: used for LP drift valuation (`deltaErrorUsd`)
- `hlMarkPrice` — HL mark price: used only for stop trigger detection (`markPrice >= stop_price`)
- `hlOraclePrice` — HL oracle price: used only for margin calculations (`marginRequiredUsd`)

Also evaluate per light-check pass:
- `stop_replacing_started_at IS NOT NULL AND age > 60s` → enqueue `partial_repair (reason='stop_replacing_overrun')` + SAFE_MODE (primary detection ≤5 min, see FR-EXBOT-033)

Skip light-check entirely when `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'`.

Stop monitoring (price-near-stop-audit) continues at ALL times including `circuit_breakers.state='open'`.

If `stopTriggerCrossed` detected → enqueue `price-near-stop-audit`, NOT `hedge-sync`.
If `circuit_breakers.state='open'` → suppress `hedge-sync` enqueue (but continue stop monitoring).
If `circuit_breakers.state='half_open'` → allow ONE probe hedge-sync through.

#### FR-EXBOT-012 — Jitter Strategy
**Priority:** P0

```
next_light_check_at = now + 5min + random(−45s, +45s)
```
Prevents bot clustering at :00/:05 boundaries; reduces D1 write spikes.

---

### 4.3 Hedge Execution (Delta-Only)

#### FR-EXBOT-020 — Delta-Only Hedge Adjustment
**Priority:** P0

Full close → full open per hedge-sync is FORBIDDEN. System MUST adjust only `Δ(targetSize − actualSize)`.

Full close/open is ONLY allowed for:
1. `target size = 0` (bot close path)
2. Emergency reset (admin-invoked)
3. Manual reset by user (Phase B+)

`targetShortEth = lpEthAmount × hedgeRatio`

Computation MUST use BigDecimal (never JS float). `target_ratio_bps` normalization via `normalizeTargetRatioBps()`.

#### FR-EXBOT-021 — Position Amount Calculation
**Priority:** P0

Hedge size MUST be based on current Uniswap V3 position amount (AMM formula). FORBIDDEN to use:
```
amount = depositedToken − withdrawnToken + collectedFees  // carter2099 bug — DO NOT USE
```

Correct formula: compute `lpEthAmount` from `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick` using Uniswap V3 TickMath + LiquidityAmounts.

`wethIndex` (0 or 1) per chain MUST be verified and stored at LP open. Base and Optimism may have different token0/token1 ordering.

#### FR-EXBOT-022 — Cloid Idempotency
**Priority:** P0

```
cloid = first128BitsHex(keccak256(`bnza:{botId}:{attemptId}:{stage}:{version}`))
```
- Same retry → same cloid
- Payload changed → increment version
- Duplicate cloid detected → reconcile first, do NOT blindly retry

#### FR-EXBOT-023 — Post-Order Reconcile
**Priority:** P0

After every hedge mutation:
1. Fetch actual HL position (`clearinghouseState`)
2. Verify size matches expected
3. Extract `entry_price`, `liquidation_price`, `effective_leverage`
4. Save to `hedge_legs`
5. Compute and update `stop_trigger_px` (§19.1)
6. Update `bot_runtime_state.last_known_hl_short_size`

Do NOT record success before reconcile confirms actual state.

---

### 4.4 Native Stop Management

#### FR-EXBOT-030 — Stop Placement
**Priority:** P0

On hedge open (size 0 → >0):
1. Open short (IOC)
2. Reconcile actual size, extract `entry_price`, `liquidation_price`, `effective_leverage`
3. Compute `stop_trigger_px`:
   - `liq_distance_pct = (liquidation_price − entry_price) / entry_price` (prefer HL value; fallback: `1 / effective_leverage`)
   - `stop_distance_pct = liq_distance_pct × stopSafetyFactor (0.70 Phase A)`
   - `stop_trigger_px = entry_price × (1 + stop_distance_pct)`
4. Place reduce-only stop market with computed trigger (HL native stop)
5. Verify placed; record `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size` in D1

All stop price computations MUST use BigDecimal (never float).

#### FR-EXBOT-031 — Stop-Trigger Crossed Handling
**Priority:** P0

When `ETH price >= stop_price` detected in light-check:
- Set `hedge_legs.stop_trigger_crossed_at = now` (guarded: do NOT overwrite if already non-NULL)
- Enqueue `price-near-stop-audit` immediately (priority)
- Do NOT route to `hedge-sync`

If `stop_trigger_crossed_at` is stuck > 30 min → enter SAFE_MODE.
If `stop_replacing_started_at` is stuck > 60s → enter SAFE_MODE (catcher for worker crash during stop replacement).

After stop fires (hedge_stopped_cooldown lifecycle):
1. Suppress hedge-sync for 4h
2. After cooldown: automatic re-hedge attempt
3. 3 stops within 7 days → `bot_safe_close` → §16.7 cooldown closed loop

#### FR-EXBOT-032 — Stop Replace (INV-STOP Protocol)
**Priority:** P0

On hedge resize (delta-only adjustment), stop MUST be replaced via protected procedure (§19.5). Direct cancel-then-place without protection is FORBIDDEN (`INV-STOP` invariant).

Stop replacement sets `hedge_legs.stop_replacing_started_at`. Must be cleared in `finally` block. Overrun (>60s) detected by audit → SAFE_MODE.

---

### 4.5 Circuit Breaker

#### FR-EXBOT-040 — Circuit Breaker State Machine
**Priority:** P0

| Transition | Condition |
|-----------|-----------|
| `closed → open` | 3 consecutive failures within 24h; `reset_at = now + 1h` |
| `open → half_open` | `reset_at` reached |
| `half_open → closed` | ONE probe hedge-sync succeeds |
| `half_open → open` | Probe fails; `reset_at` reset to `now + 1h` |

Canonical source: `circuit_breakers.state` column (NOT dynamic computation from history).

During `open`: suppress hedge-sync. Stop monitoring continues.
During `half_open`: allow exactly ONE probe (atomic `half_open_probe_used` 0→1).
Reset ONLY on probe success. Do NOT reset on partial or failed.

---

### 4.6 SAFE_MODE

#### FR-EXBOT-050 — SAFE_MODE Triggers
**Priority:** P0

Enter SAFE_MODE when ANY of:
- HL API unreachable > 5 min
- Reconcile mismatch (actual ≠ expected)
- `margin_status = 'critical'` twice in a row
- `effective_leverage > 4.5`
- `liquidation_price` within 5% of current ETH price (hlMarkPrice)
- `stop_trigger_crossed_at` stuck > 30 min
- `stop_replacing_started_at` stuck > 60s (worker crash catcher)

**Forbidden in SAFE_MODE:** cancel stops, open positions, rebalance hedge/LP, change leverage, withdraw margin.

**Allowed in SAFE_MODE:** read state, retry HL connectivity, alert user/admin, light-check (non-HL part), deep-audit (when HL recovers), priority stop audit.

**Recovery:**
- Auto: HL responsive + 3 successful reconciles + `margin_status` returned to `ok`
- Manual: admin via dashboard
- Terminus (irrecoverable): `bot_safe_close` → §16.7 cooldown closed loop

---

### 4.7 Margin Management

#### FR-EXBOT-060 — Margin Status Thresholds
**Priority:** P0

```
marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage
marginUsage = marginRequiredUsd / marginBalanceUsd

ok:       marginUsage < 0.55
warning:  0.55 ≤ marginUsage < 0.75
critical: marginUsage ≥ 0.75
```

Margin status is updated ONLY at:
1. Just before hedge-sync (fetch HL marginSummary)
2. Deep-audit

Light-check reads `hedge_legs.margin_status` from D1 only (NO HL fetch). Weight = 0.

`warning` → disable size-increase hedges; alert user (POOL UI banner, Phase A only).
`critical` → enter SAFE_MODE; alert admin; guide "deposit additional $Z to HL".

---

### 4.8 Close / Redeem Operations

#### FR-EXBOT-070 — Two Close Systems
**Priority:** P0

**(A) user_redeem (LP-first, user-initiated):**
1. User calls `BnzaExVault.redeem(tokenId)` on-chain → LP liquidated instantly → LP-portion USDC returned to user in same tx
2. Worker detects redeem event → enqueues `user_redeem` (highest priority queue, SLA 5 min from detection)
3. Worker closes HL hedge immediately
4. After hedge close confirmed: send HL-portion USDC to user (tracked in `RedemptionQueue` ledger)
5. On hedge close failure → `residual_hl_liability` state. Do NOT stop LP-portion repayment.

**(B) bot_safe_close (hedge-first, system/operator-initiated):**

Triggers:
- Circuit breaker open + retries exhausted
- Margin critical (SAFE_MODE recovery impossible)
- 3 stops within 7 days
- partial_repair exhausted
- Compliance/admin force close

Order: hedge → LP (via executeStrategy(RedeemStrategyV1)) → RedemptionQueue.createRequest → Operator fulfillRequest pays user FIFO on-chain.

After bot_safe_close completes: bots.status='closed'. User receives notification "Bot safely closed. Funds have been returned to your wallet."

**Both systems tracked in `close_operations` ledger** (`idempotency_key UNIQUE` prevents double settlement).


---

### 4.9 D1 Schema

#### FR-EXBOT-080 — D1 Architecture
**Priority:** P0

Two physically separate databases:

**control_db** (1, global):
| Table | Purpose |
|-------|---------|
| `users` | User profiles + HL account references |
| `bot_registry` | All bots cross-shard; status, chain, bot_type |
| `shard_registry` | Shard-to-DB binding |
| `hl_agent_keys` | Encrypted agent keys (envelope encryption) |

**state_db_shard_xx** (Phase A: 1 shard; Phase B: 4; Phase C: 16 — deferred):
| Table | Purpose |
|-------|---------|
| `bots` | Per-shard bot state + lifecycle_state |
| `positions` | LP position static data + custody info |
| `hedge_legs` | Hedge leg state, stop state, circuit_state, margin_status, scale ladder |
| `bot_runtime_state` | Hot state (current tick, eth price, LP amounts, short size) |
| `circuit_breakers` | Circuit breaker per hedge_leg_id |
| `rebalance_attempts` | Hedge sync attempt audit log |
| `lp_operations` | LP open/rebalance/close idempotency ledger |
| `close_operations` | Close/redeem state machine ledger |
| `queue_idempotency` | Consumer message deduplication ledger |
| `funding_daily_metrics` | Daily funding aggregate (Phase A) |
| `hourly_bot_metrics` | Per-bot hourly metrics |
| `daily_bot_metrics` | Per-bot daily metrics |

Shard key: `shard_id = hash(bot_id) % shard_count`.

D1 write budget rule: write `bot_runtime_state` ONLY on change (no-op detection). Batch `next_light_check_at` updates (1 statement per shard). Forbidden: unconditional UPDATE per light-check.

Schema change rule: ADD COLUMN only. DROP / RENAME of existing columns is FORBIDDEN.

#### FR-EXBOT-081 — Agent Key Storage (AES-GCM Envelope)
**Priority:** P0

Agent key storage in `hl_agent_keys`:
- `encrypted_secret` = agent key, AES-256-GCM, encrypted with a per-row DEK
- `wrapped_dek` = DEK wrapped with Master Key (Cloudflare Secrets Store)
- `secret_iv`, `secret_auth_tag`, `dek_iv` stored as separate BLOB columns

Decryption: unwrap `wrapped_dek` → decrypt `encrypted_secret`. Plain DEK / plain agent key is function-scope only, destroyed immediately after use.

Do NOT use keys with `approval_status='pending'`.

---

### 4.10 Durable Objects

#### FR-EXBOT-090 — HLRateLimitDO
**Priority:** P0

Sliding-window rate limit for HL API calls. BNZA operating budget: 800 weight/min (67% of HL's 1,200/min hard limit). Excess → queue + delay.

#### FR-EXBOT-091 — UserLockDO (Lease-Based)
**Priority:** P0

Lease-based mutex for same-user HL mutations:
- `acquire(holderToken, ttlMs=90_000, idempotencyKey?)` → `{acquired: true/false}`
- `heartbeat(holderToken, ttlMs)` → extend lease if still held
- `release(holderToken, idempotencyKey?, result?)` → release + optional cache result for replay

holderToken mismatch on release = noop. TTL expiry = auto-release. Caller (not DO) runs the work.

`idempotencyKey` pattern: `hedge-sync:{botId}:{stateVersion}`. Prevents duplicate execution of same stateVersion on redelivery.

#### FR-EXBOT-092 — MarketDataDO
**Priority:** P0

Shared cache for pool slot0 (sqrtPriceX96, currentTick, blockNumber). All light-check workers read from this DO instead of individual RPC calls. Cache TTL and refresh cadence: per SPEC NV-12 result.

---

### 4.11 Operator Facade API

#### FR-EXBOT-100 — Operator Facade Endpoints
**Priority:** P1

OPERATOR exposes `/api/exbot/*` which proxies to ExBot Worker via CF service binding + internal token. ExBot Worker is NOT directly accessible from the internet.

| Endpoint | Method | Action | Actor |
|----------|--------|--------|-------|
| `/api/exbot/start` | POST | Start a new ExBot for user | Admin |
| `/api/exbot/status` | GET | Get ExBot status for user | Admin |
| `/api/exbot/close` | POST | Initiate close (bot_safe_close path) | Admin |
| `/api/exbot/agent-key` | POST/GET | Manage HL agent key approval | Admin |
| `/api/exbot/margin` | POST | Adjust margin parameters | Admin |

---

### 4.12 Throughput & Scale

#### FR-EXBOT-110 — 10,000 Bot Scale Design
**Priority:** P0

Target: 10,000 bots / 5-min light-check = 33.3 bots/sec.

Forbidden at scale (light-check must NOT):
- Fetch `clearinghouseState` for all bots every 5 min
- Fetch `openOrders` for all bots every 5 min
- Fetch `userFunding` for all bots every 5 min

D1 sharding: Phase A = 1 shard; Phase B = 4; Phase C = 16 (deferred until Phase B stable + 10k-equivalent load benchmark passes).

CF Workers simultaneous outbound connections: max 6 per invocation. Parallel fetches within 1 invocation must be limited to 6 concurrent.

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-EXBOT-001 | Throughput | 10,000 bots / 5-min scan cycle = 33.3 bots/sec sustained |
| NFR-EXBOT-002 | Latency | 1 hedge-sync normally completes < 30s (queue lag reduction) |
| NFR-EXBOT-003 | SLA | user_redeem hedge close: ≤ 5 min from event detection |
| NFR-EXBOT-004 | Rate limit | HL API: ≤ 800 weight/min (67% of 1,200 hard limit) |
| NFR-EXBOT-005 | D1 write | No unconditional UPDATE per light-check; write-on-change only |
| NFR-EXBOT-006 | Security | No master private key stored; agent key AES-GCM envelope; plain key function-scope only |
| NFR-EXBOT-007 | Idempotency | All queue consumers: idempotency ledger insert at start; UNIQUE conflict = skip |
| NFR-EXBOT-008 | Precision | All hedge/stop/margin computations: BigDecimal only (float/number arithmetic forbidden) |
| NFR-EXBOT-009 | Chain | Dual-chain (Base + Optimism) from Phase 1; wethIndex verified per chain |
| NFR-EXBOT-010 | Availability | SAFE_MODE is NOT a one-way ticket; autonomous recovery via closed loop |

---

## 6. Phase 0 Gate (Blocks Phase A Start)

All 4 conditions must be met before Phase A work begins:

1. zen approves SPEC v5.2.6
2. BnzaExVault deployed; Base + OP addresses, authorizedOperator, multiSig finalized (2 sets)
3. HL agent key encryption method confirmed (NV-3)
4. WL stability gate: 7 consecutive post-launch days with zero SAFE_MODE + no major incident

Before gate clears: SOTATEK prepares D1 schema + Queue skeleton only (no HL integration).

