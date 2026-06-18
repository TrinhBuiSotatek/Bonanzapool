---
title: UC Readiness Review — UC-EXBOT-light-check (ExBot SRS-first) — Re-audit HLD-2026-06-18
date: 2026-06-18
author: QC UC Read ExBot Agent
version: v3
last_updated: 2026-06-18
hld_baseline: 2026-06-18
output_language: en
---

# UC Readiness Review: UC-EXBOT-light-check — Execute Periodic Light-Check

**Document title:** UC-EXBOT-light-check Audited Readiness Report (qc-uc-read-exbot) — Re-audit HLD-2026-06-18
**Date created:** 2026-06-18
**Author/Agent:** QC UC Read ExBot Agent
**Version:** v3

> **Re-audit note (v3 — 2026-06-18):**
> This is a re-audit against the HLD-2026-06-18 baseline. Changes since v1:
> - `uc-light-check.md` updated: US-EXBOT-007 and US-EXBOT-008 added to `linked_stories`.
> - `srs/spec.md` updated: FM-XB-08 (park/re-entry dropped), IC-EXBOT-002 (uninvestedBalanceOf removed), US-012 emergency authority updated.
> - `srs/states.md` updated: `cooldown` and `parked` lifecycle states removed from State Registry.
> - `frd.md` updated: FR-EXBOT-002 HLD note added; FR-EXBOT-070/073 updated (no park/re-deploy); `uninvestedBalanceOf` removed from IC.
> - `srs/flows.md` NOT updated (still 2026-06-12): F-05 still contains full park/re-entry loop (new I-017).
> - New US-007 added to scope: LP range rebalance trigger path now in scope for light-check. US-007 references `BnzaExVault.vaultRebalance()` which conflicts with FR-EXBOT-015 (new I-015). UC main flow still does not describe the `range_out → lp_rebalancing` transition (new I-016).
> - **v1 issues I-001 through I-014:** all remain Open (none resolved by HLD-2026-06-18 changes to the files read).
> - Score revised from 61/100 to 52/100 due to new issues I-015, I-016, I-017.

---

## Reference Code Glossary (Bảng mã viết tắt)

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case — ExBot module. Identifies a discrete use case specifying actors, flows, and FR traces for the ExBot backend. | `usecases/index.md` |
| FR-EXBOT-* | Functional Requirement — ExBot. Numbered requirements in `srs/spec.md` (canonical) and `frd.md` (implementation-scoped). Where the two conflict, `srs/spec.md` prevails. | `srs/spec.md`; `frd.md` |
| US-EXBOT-* | User Story — ExBot. Each story has actor, INVEST check, Gherkin ACs, and FR trace. | `userstories/` |
| BR-EXBOT-* | Business Rule — ExBot. Invariants that must hold across all workers and states (e.g., HL weight = 0 in light-check). | `srs/spec.md §4 BR table` |
| OQ-EXBOT-* | Open Question — ExBot. Unresolved design questions that block implementation of specific FRs. | `srs/spec.md §9` |
| IC-EXBOT-* | Integration Constraint — ExBot. Constraints on external dependencies (HL API, BnzaExVault contract, Uniswap pool). | `srs/spec.md §10` |
| NFR-EXBOT-* | Non-Functional Requirement — ExBot. Performance, security, precision, availability constraints. | `srs/spec.md §3` |
| E-EXBOT-* | Error Code — ExBot. Machine-readable error identifiers with HTTP status and message text. | `srs/spec.md §5` |
| F-NN | Flow sequence diagram number in `srs/flows.md`. E.g., F-01 is Queue Fan-Out, F-05 is bot_safe_close + re-entry (stale as of 2026-06-18). | `srs/flows.md` |
| FM-XB-* | Feature Map entry — ExBot. Maps a numbered feature to its SRS/FRD scope. | `02_backbone/backbone.md` |
| HL | Hyperliquid — the perpetuals DEX where ExBot maintains delta-short positions. ExBot calls HL via REST API (info + exchange endpoints). | (industry platform) |
| D1 | Cloudflare D1 — SQLite-based edge database used for all ExBot persistent state. Split into `control_db` (global) and `state_db_shard_*` (per-shard). | (Cloudflare platform) |
| DO / Durable Object | Cloudflare Durable Object — stateful singleton used for `HLRateLimitDO` (rate budget), `UserLockDO` (lease mutex), `MarketDataDO` (pool slot0 cache). | (Cloudflare platform) |
| SAFE_MODE | ExBot lifecycle status. No hedge mutations allowed; only monitoring and recovery actions. Triggered by HL unreachability, reconcile mismatch, margin critical, stuck markers. | `srs/spec.md FR-EXBOT-050` |
| INV-STOP | Protected stop-replacement protocol (§19.5 of SPEC v5.2.6). Prevents a window where no stop exists during cancel-then-place. | `srs/spec.md FR-EXBOT-035` |
| BigDecimal | Arbitrary-precision decimal arithmetic library. All financial computations in ExBot must use BigDecimal; JS `Number()` or `float` for financial values is forbidden. | `srs/spec.md NFR-EXBOT-008` |

---

## Feature Brief

UC-EXBOT-light-check defines the periodic automated scan that runs every 5 minutes (with ±45s jitter) across all active ExBot instances to determine whether a hedge adjustment or stop-price action is needed — without ever calling the Hyperliquid API. The scan is driven by a Cloudflare Cron Worker that fans messages out through a two-stage queue pipeline: `bot-scan → light-check`. The Light-Check Worker evaluates each bot using only D1 hot-state (`bot_runtime_state`, `hedge_legs`) and `MarketDataDO` (Uniswap V3 pool slot0 cache), computing the LP ETH amount via local TickMath + LiquidityAmounts and checking nine rebalance reasons (`RebalanceReason[]`). The worker then routes the outcome: enqueue `hedge-sync` (rebalance needed, circuit not open), enqueue `price-near-stop-audit` (stop trigger or range boundary near), or take no action.

As of HLD-2026-06-18, the UC now also covers the LP range rebalance trigger path (US-EXBOT-007 added to linked_stories): when `range_out` is detected, the system transitions `lifecycle_state` to `lp_rebalancing` and enqueues a rebalance operation. However, this path is absent from UC §3 main flow and §7 FR trace (I-016), and a new cross-source conflict exists between US-007 and FR-EXBOT-015 on the Vault function name (I-015).

Additionally, `srs/flows.md` F-05 was NOT updated on 2026-06-18 and still contains the entire park/re-entry loop that has been dropped from spec.md, states.md, and frd.md (I-017).

**Related artefacts read:** `srs/spec.md` (updated 2026-06-18), `srs/states.md` (updated 2026-06-18), `srs/flows.md` (2026-06-12 -- NOT updated), `srs/erd.md` (2026-06-12), `frd.md` (updated 2026-06-18), `uc-light-check.md` (updated 2026-06-18), `usecases/index.md` (updated 2026-06-18), `us-005.md`, `us-006.md`, `us-007.md`, `us-008.md`.

---

## 0. Document Information

| UC ID | Feature / Use Case Name | Version | Document Status |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check | v3 | Draft |

| Author / BA | Reviewer | Date Created | Last Updated |
|---|---|---|---|
| @hienduong | QC UC Read ExBot Agent | 2026-06-12 | 2026-06-18 |

| Artefact Read | Version / Date | HLD-2026-06-18 Updated? | Role | Notes |
|---|---|---|---|---|
| `usecases/uc-light-check.md` | 2026-06-18 | Yes | UC | Added US-007, US-008 to linked_stories |
| `usecases/index.md` | 2026-06-18 | Yes | UC index | FR trace; linked stories updated |
| `srs/spec.md` | v5.2.6 (2026-06-18) | Yes | SRS — source of truth | FM-XB-08, IC-EXBOT-002, US-012 updated |
| `srs/states.md` | 2026-06-18 | Yes | State diagrams | cooldown/parked removed |
| `srs/flows.md` | 2026-06-12 | **No — stale** | Sequence flows | F-05 still has park/re-entry loop (I-017) |
| `srs/erd.md` | 2026-06-12 | No | ERD | Schema unchanged |
| `frd.md` | 2026-06-18 | Yes | FRD (full) | FR-EXBOT-002 note, FR-EXBOT-070/073 updated |
| `userstories/us-005.md` | 2026-06-12 | No | User Story | light-check without HL calls |
| `userstories/us-006.md` | 2026-06-12 | No | User Story | delta-only hedge-sync |
| `userstories/us-007.md` | 2026-06-12 | No | User Story | LP range rebalance — newly in scope |
| `userstories/us-008.md` | 2026-06-12 | No | User Story | circuit breaker |

---

## 1. Goals and Scope

### 1.1 Business Goal

UC-EXBOT-light-check exists to ensure that the ExBot system detects hedge drift and stop-trigger events within a 5-minute window for up to 10,000 concurrent bots -- without consuming any Hyperliquid API rate limit. This is the primary "heartbeat" that keeps each bot delta-neutral and routes safety events to the appropriate handler. As of HLD-2026-06-18, the UC now also covers the LP range rebalance trigger (US-007): when `rangeState != 'in'` (range_out), the system must transition `lifecycle_state` to `lp_rebalancing` and suppress further light-check evaluation for that bot.

### 1.2 Scope Within This UC

| Item / Function | Description | Source |
|---|---|---|
| Cron to bot-scan queue fan-out | 1-min Cron Worker sends shard windows to `bot-scan`; Scan Worker queries active bots and distributes per-bot messages to `light-check` queue | UC section 3 steps 1-3; SRS F-01 |
| Jitter-based next_light_check_at update | Batch D1 UPDATE (1 stmt/shard) sets `next_light_check_at = now + 5min + jitter(plus or minus 45s)` | UC section 3 step 4; FR-EXBOT-012/013 |
| Idempotency gate | Insert `message_id` into `queue_idempotency` at start; UNIQUE conflict = duplicate skip | UC section 3 step 5; FR-EXBOT-011 |
| D1 + MarketDataDO state read | Read `bot_runtime_state`, `hedge_legs`, `circuit_state`; read `sqrtPriceX96`, `currentTick` from MarketDataDO | UC section 3 steps 6-7 |
| LP ETH amount computation | Local TickMath + LiquidityAmounts (no RPC, no HL) | UC section 3 step 8; FR-EXBOT-021 |
| RebalanceReason[] evaluation | Evaluate 9 canonical reasons from D1 + MarketDataDO only | UC section 3 step 9; FR-EXBOT-023 |
| hedge-sync enqueue | Enqueue when reasons found AND circuit != open | UC section 3 step 10; FR-EXBOT-011 |
| half_open probe enqueue | Allow exactly ONE probe hedge-sync when circuit = half_open | UC section 4 A2 |
| Stop trigger detection + routing | Set `stop_trigger_crossed_at` (guarded); enqueue `price-near-stop-audit` | UC section 3 step 11; FR-EXBOT-032 |
| stop_replacing_started_at overrun detection | Detect overrun > 60s to enqueue partial_repair + SAFE_MODE | FR-EXBOT-033, FR-EXBOT-012; ABSENT from UC |
| Bot skip conditions | Skip if `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'` | UC section 2; FR-EXBOT-012 |
| LP rebalance trigger (NEW -- US-007) | When `range_out` detected: transition to `lp_rebalancing`, enqueue rebalance via `partial_repair` queue | FR-EXBOT-015; US-007 AC-EXBOT-007-1; ABSENT from UC section 3 main flow (I-016) |

### 1.3 Out of Scope / Not Included

| Item | Reason | Test Impact |
|---|---|---|
| Hedge-sync execution logic | Handled by UC-EXBOT-hedge-sync; this UC only enqueues | No test cases for actual HL calls in this UC |
| Price-near-stop-audit worker execution | Downstream consumer, separate UC | Test only that the enqueue occurs with correct payload |
| MarketDataDO refresh logic | FR-EXBOT-093; separate DO lifecycle | Stale-cache scenario is a dependency, not part of this UC |
| Deep-audit secondary stop_replacing detection | FR-EXBOT-033 secondary backstop; covered in deep-audit UC | Only primary detection (5 min) is in scope here |
| `lpValueUsd` exact formula | OQ-EXBOT-11 open; blocks drift_threshold formula | Cannot test drift_threshold fully until resolved |
| 7-day APR aggregation formula | OQ-EXBOT-12 open; blocks funding_alert evaluation | Cannot test funding_alert until resolved |
| range_boundary_near exact threshold | OQ-EXBOT-10 open; tick vs price distance | Cannot test range_boundary_near until resolved |
| LP rebalance worker execution | FR-EXBOT-015 downstream; scope of UC-EXBOT partial-repair | Test only that the `partial_repair` enqueue occurs |

---

## 2. Actors, Roles, and Permissions

| Actor / Role | Type | Role in UC | Permissions / Limits | Source |
|---|---|---|---|---|
| Cron Worker (1-min) | System | Triggers the pipeline by sending shard windows to `bot-scan` queue | No D1 reads; write-only to queue | UC section 1; SRS F-01 |
| Scan Worker | System | Queries D1 for active bots; distributes to `light-check`; batch-updates `next_light_check_at` | D1 read + batch write; queue write | UC section 3 steps 2-4; SRS F-01 |
| Light-Check Worker | Primary | Core evaluation logic; reads D1 + MarketDataDO; routes outcome | D1 read + idempotency write; queue write; NO HL API calls | UC section 3 steps 5-12; BR-EXBOT-003 |
| D1 (state_db_shard) | System | Stores bot lifecycle state, hedge_legs, bot_runtime_state, queue_idempotency | Data store | UC section 1 |
| MarketDataDO | System | Provides shared Uniswap V3 pool slot0 cache (sqrtPriceX96, currentTick) | Read-only from worker perspective; DO manages its own refresh | UC section 1; FR-EXBOT-093 |

---

## 3. Pre- and Post-Conditions

### 3.1 Preconditions

| # | Precondition | Required? | Source |
|---|---|---|---|
| 1 | Bot `status='active'` | Yes | UC section 2 |
| 2 | `next_light_check_at <= now` | Yes | UC section 2 |
| 3 | `lifecycle_state NOT IN ('lp_rebalancing', 'lp_closing')` | Yes | UC section 2; FR-EXBOT-012 |
| 4 | `status != 'paused'` | Yes | UC section 2; FR-EXBOT-012 |
| 5 | `MarketDataDO` cache is available and not stale beyond 2x refresh interval | Implicit | FR-EXBOT-093; OQ-EXBOT-09 (refresh interval TBD) |
| 6 | `queue_idempotency` table accessible in D1 | Yes | FR-EXBOT-011 |

Note: `hedge_stopped_cooldown` state -- light-check runs but hedge-sync is suppressed (SRS states.md: "run (no hedge-sync)"). UC does not mention this state in preconditions (I-005).

### 3.2 Post-Conditions

| Action | Post-state / Data after completion | Source |
|---|---|---|
| Rebalance detected, circuit not open | `hedge-sync` message enqueued with `{botId, reasons, stateVersion}`; `queue_idempotency.state='succeeded'` | UC section 3 step 10, 12 |
| Stop trigger detected | `hedge_legs.stop_trigger_crossed_at` set (if NULL); `price-near-stop-audit` enqueued | UC section 3 step 11; FR-EXBOT-032 |
| Circuit open | No `hedge-sync` enqueued; stop monitoring still runs | UC section 4 A1 |
| Circuit half_open | One probe `hedge-sync` enqueued via atomic `half_open_probe_used` claim | UC section 4 A2 |
| `range_out` detected (NEW -- US-007) | `lifecycle_state` transitions to `lp_rebalancing`; LP rebalance op enqueued via `partial_repair` queue; subsequent light-checks skip this bot | FR-EXBOT-015; US-007 AC-EXBOT-007-1; ABSENT from UC section 3 (I-016) |
| No conditions met | No queue messages; `queue_idempotency.state='succeeded'` | UC section 3 step 12 |
| Duplicate message delivery | Worker exits after UNIQUE conflict on `message_id`; no evaluation runs | UC section 3 step 5 |
| `next_light_check_at` | Updated to `now + 5min + jitter(+-45s)` (batch, 1 stmt/shard) | UC section 3 step 4 |

---

## 4. UI Object List

N/A -- UC-EXBOT-light-check is a backend-only use case running as a Cloudflare Worker pipeline. There is no interactive UI. (Source: SRS section 6: "ExBot is a backend-only module.")

---

## 5. UI Object Behavior

N/A -- same reason as section 4.

---
## 6. Business Logic and Flow Decomposition

### 6.1 Function: Cron to Scan Worker to light-check queue fan-out

#### A. Flow

| Step | Actor | Action / Trigger | System Response (happy path) | Alternate | Exception | Source |
|---|---|---|---|---|---|---|
| 1 | Cron Worker | Fires every 1 minute; calls `chunkSendBatch({shardId, cursor, limit=500, now})` to `bot-scan` queue | `bot-scan` queue receives shard window messages | -- | Cron fire missed: next cron at t+1min | UC section 3 step 1; SRS F-01 |
| 2 | Scan Worker | Receives `bot-scan` message; queries D1: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500` | Returns up to 500 active bots due for check | No bots due: empty result, worker exits | D1 unavailable: worker fails, message redelivered | UC section 3 step 2 |
| 3 | Scan Worker | Sends per-bot messages to `light-check` queue in batches of max 100 (CF limit) | Messages enqueued in chunks of 100 max | -- | Queue full / rate limit: retry per CF queue semantics | UC section 3 step 3; FR-EXBOT-010 |
| 4 | Scan Worker | Batch-updates `next_light_check_at = now + 5min + random(-45s, +45s)` in D1 (1 stmt/shard) | `bots.next_light_check_at` updated for all scanned bots | -- | D1 write fails: next scan will pick these bots up again | UC section 3 step 4; FR-EXBOT-013 |

#### B. Business Rules

| Rule | Constraint | Source |
|---|---|---|
| `chunkSendBatch()` helper | All queue sendBatch calls MUST go through this helper; direct `queue.sendBatch()` forbidden | FR-EXBOT-010 |
| Batch D1 write | `next_light_check_at` written once per shard (not per-bot) | FR-EXBOT-013; NFR-EXBOT-005 |
| Jitter formula | `now + 5min + random(-45s, +45s)` -- prevents clustering at :00/:05 boundaries | FR-EXBOT-013 |

---

### 6.2 Function: Light-Check Worker -- idempotency gate and state read

#### A. Flow

| Step | Actor | Action | System Response (happy path) | Alternate | Exception | Source |
|---|---|---|---|---|---|---|
| 5 | Light-Check Worker | Inserts `{message_id, state='started'}` into `queue_idempotency` | Insert succeeds; worker proceeds | UNIQUE conflict: duplicate delivery, exit immediately | D1 unavailable: worker fails, message redelivered | UC section 3 step 5; FR-EXBOT-011 |
| 6 | Light-Check Worker | Reads D1: `bot_runtime_state`, `lifecycle_state`, `hedge_legs.stop_price`, `margin_status`, `circuit_breakers.state` | Returns current bot state | `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'`: skip | D1 read timeout: worker fails | UC section 3 step 6; FR-EXBOT-012 |
| 7 | Light-Check Worker | Reads `MarketDataDO`: `sqrtPriceX96`, `currentTick` | Returns current pool slot0 data | Cache stale > 2x interval: DO forces refresh + warning log | MarketDataDO unavailable: failure path undefined in UC (I-007) | UC section 3 step 7; FR-EXBOT-093 |

#### B. Business Rules

| Rule | Constraint | Source |
|---|---|---|
| HL weight = 0 | Zero Hyperliquid API calls in any light-check pass. BR-EXBOT-003: "Any HL API call introduced into light-check is an architectural violation." | BR-EXBOT-003; FR-EXBOT-012 |
| Skip conditions | `lifecycle_state IN ('lp_rebalancing','lp_closing')` OR `status='paused'` means skip all evaluation | UC section 2; FR-EXBOT-012 |
| hedge_stopped_cooldown handling | Light-check RUNS but hedge-sync enqueue is suppressed. Stop monitoring continues. UC does not mention this state (I-005). | SRS states.md |

---

### 6.3 Function: Light-Check Worker -- LP ETH amount computation

#### A. Flow

| Step | Actor | Action | System Response | Source |
|---|---|---|---|---|
| 8 | Light-Check Worker | Compute `lpEthAmount` via Uniswap V3 TickMath + LiquidityAmounts using `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick` from D1 + MarketDataDO | Returns `lpEthAmount` in ETH (BigDecimal) | UC section 3 step 8; FR-EXBOT-021 |

#### B. Business Rules

| Rule | Constraint | Source |
|---|---|---|
| AMM formula only | `amount = depositedToken - withdrawnToken + collectedFees` is FORBIDDEN ("carter2099 bug") | FR-EXBOT-021 |
| BigDecimal | All LP amount computations must use BigDecimal; JS float forbidden | FR-EXBOT-021; NFR-EXBOT-008 |
| `wethIndex` source | Read `positions.weth_index` from D1 per chain; NOT hardcoded | FR-EXBOT-021; FR-EXBOT-004 |

---

### 6.4 Function: Light-Check Worker -- RebalanceReason[] evaluation and routing

#### A. RebalanceReason Enum (canonical, 9 values)

| Reason | Evaluation Condition | Data Source | Formula Status | Source |
|---|---|---|---|---|
| `drift_threshold` | `deltaErrorUsd > max($25, lpValueUsd x 3%)` where `deltaErrorUsd = |targetShortEth - actualShortEth| x uniPoolPrice` | D1, MarketDataDO | Partial -- `lpValueUsd` formula unresolved (OQ-EXBOT-11, I-008) | FR-EXBOT-023; SRS spec OQ-EXBOT-11 |
| `drift_relative` | `|target - actual| / target > 0.15` | D1 | Clear | FR-EXBOT-023 |
| `range_out` | `rangeState != 'in'` (derived from `currentTick` vs `tickLower`/`tickUpper`) | D1, MarketDataDO | Clear | FR-EXBOT-023 |
| `range_boundary_near` | Price 90% to range upper/lower -- exact computation method unresolved | D1 + MarketDataDO | Blocked -- OQ-EXBOT-10 (I-004) | SRS spec OQ-EXBOT-10 |
| `margin_warning` | `hedge_legs.margin_status == 'warning'` (read from D1; NO HL fetch) | D1 | Clear | FR-EXBOT-023; FR-EXBOT-060 |
| `funding_alert` | 7d funding APR < -15% | D1 `funding_daily_metrics` | Blocked -- OQ-EXBOT-12 (I-009) | SRS spec OQ-EXBOT-12 |
| `time_fallback` | 4h since last adjustment | D1 (field unspecified, I-006) | Partial | FR-EXBOT-023 |
| `manual_admin` | Admin-triggered | Admin invocation path | Clear (out of scope for this UC) | FR-EXBOT-023 |
| `recovery_reconcile` | Post-SAFE_MODE recovery reconcile | Recovery worker path | Clear (out of scope for this UC) | FR-EXBOT-023 |

Note: `stop_trigger_crossed` is NOT a RebalanceReason. It routes to `price-near-stop-audit`. (Source: FR-EXBOT-023.)

#### B. Routing Logic

| Condition | Action | Source |
|---|---|---|
| `reasons.length > 0` AND `circuit_breakers.state != 'open'` | Enqueue `hedge-sync` with `{botId, reasons, stateVersion}` | UC section 3 step 10 |
| `reasons.length > 0` AND `circuit_breakers.state == 'open'` | Suppress `hedge-sync`; continue to stop check | UC section 4 A1; FR-EXBOT-014 |
| `circuit_breakers.state == 'half_open'` | Atomically claim `half_open_probe_used` (0 to 1); enqueue ONE probe hedge-sync | UC section 4 A2; FR-EXBOT-040 |
| `range_out` detected (NEW -- US-007) | Transition `lifecycle_state` to `lp_rebalancing`; enqueue LP rebalance via `partial_repair` queue | FR-EXBOT-015; US-007 AC-EXBOT-007-1; ABSENT from UC section 3 (I-016) |
| `markPrice >= stop_price` (from `hlMarkPrice` -- source undefined in UC, I-003) | Set `stop_trigger_crossed_at` if NULL (guarded); enqueue `price-near-stop-audit` | UC section 3 step 11; FR-EXBOT-032; BR-EXBOT-005 |
| `stop_trigger_crossed_at` already set (non-NULL) | Do NOT overwrite; still enqueue `price-near-stop-audit` | UC section 4 A3; BR-EXBOT-005 |
| `stop_replacing_started_at IS NOT NULL AND age > 60s` | Enqueue `partial_repair(reason='stop_replacing_overrun')`; trigger SAFE_MODE entry | FR-EXBOT-033; FR-EXBOT-012 -- ABSENT FROM UC (I-001) |
| `range_boundary_near` detected | Enqueue `price-near-stop-audit` per UC section 4 A4 -- routing conflicts with RebalanceReason definition (I-002) | UC section 4 A4; FR-EXBOT-023 |

#### C. Price Source Rules (3-way split -- MUST NOT be interchanged)

| Price | Source | Allowed Use | Forbidden Use | Source |
|---|---|---|---|---|
| `uniPoolPrice` | MarketDataDO `sqrtPriceX96` via TickMath | `deltaErrorUsd` for drift threshold evaluation | Stop trigger detection, margin calculations | FR-EXBOT-012; SRS spec FR-EXBOT-012 note v5.2.6 X-5 |
| `hlMarkPrice` | HL mark price (source unspecified in UC -- see I-003) | Stop trigger detection (`markPrice >= stop_price`) | Drift calculations, margin calculations | FR-EXBOT-012 |
| `hlOraclePrice` | HL oracle price | Margin calculations (`marginRequiredUsd`) | Drift, stop trigger | FR-EXBOT-060 |

#### D. Business Rules

| Rule | Constraint | Source |
|---|---|---|
| BR-EXBOT-003 | "Light-check HL weight = 0. Any HL API call introduced into light-check is an architectural violation." | BR-EXBOT-003 |
| BR-EXBOT-005 | "`stop_trigger_crossed_at` is write-once per stop event (guarded: only set if currently NULL)." | BR-EXBOT-005 |
| Canonical enum | Only 9 canonical `RebalanceReason[]` values allowed; no aliases | FR-EXBOT-023 |

---

### 6.5 Function: LP Range Rebalance Trigger (NEW -- US-EXBOT-007)

This function is now in scope because US-007 was added to `linked_stories` on 2026-06-18.

#### A. Flow

| Step | Actor | Action | System Response | Source |
|---|---|---|---|---|
| LC-R1 | Light-Check Worker | Evaluates `range_out` reason: `currentTick < tickLower OR currentTick >= tickUpper` | `range_out` added to `reasons` array | FR-EXBOT-015; FR-EXBOT-023 |
| LC-R2 | Light-Check Worker | Transitions `bots.lifecycle_state` to `lp_rebalancing`; persists atomically to D1 | `lifecycle_state='lp_rebalancing'`; subsequent light-checks skip this bot | FR-EXBOT-015; US-007 AC-EXBOT-007-1; ABSENT from UC section 3 (I-016) |
| LC-R3 | Light-Check Worker | Enqueues LP rebalance operation via `partial_repair` queue with UNIQUE idempotency key | `partial_repair` message created; `lp_operations` row to be written by repair worker | FR-EXBOT-015; US-007 |
| LC-R4 | Light-Check Worker | Suppresses `hedge-sync` for this bot during `lp_rebalancing` | No hedge-sync message enqueued | US-007 AC-EXBOT-007-4 |

Note: US-007 references `BnzaExVault.vaultRebalance()` and `VaultRebalanced` event. FR-EXBOT-015 describes the rebalance as `BnzaExVault.redeem(tokenId)` (close LP NFT) + compute new tick range + mint new NFT. The function name `vaultRebalance()` and event `VaultRebalanced` do not appear in FR-EXBOT-015 or anywhere in SRS. This is a CROSS_SOURCE_CONFLICT (I-015).

#### B. Business Rules

| Rule | Constraint | Source |
|---|---|---|
| `lp_operations` idempotency | Each LP rebalance attempt must have a UNIQUE idempotency key in `lp_operations` | FR-EXBOT-015; US-007 AC-EXBOT-007-2 |
| Hedge suppressed during lp_rebalancing | No `hedge-sync` messages for bots in `lp_rebalancing` | FR-EXBOT-015; US-007 AC-EXBOT-007-4 |
| Failure path | After 3 consecutive LP rebalance failures, system initiates `bot_safe_close` (FR-EXBOT-072) | FR-EXBOT-015; US-007 AC-EXBOT-007-3 |

---
## 7. Cross-Function Integration and Data Consistency

| Triggering Action | Affected Area | Business Impact | Data Consistency Check | Source |
|---|---|---|---|---|
| Light-check enqueues `hedge-sync` | UC-EXBOT-hedge-sync (downstream) | `stateVersion` in queue message must match `bot_runtime_state.state_version` in D1; stale message is discarded | FR-EXBOT-027: stale stateVersion causes hedge-sync worker to discard and skip HL call | UC section 3 step 10; FR-EXBOT-027 |
| Light-check sets `stop_trigger_crossed_at` | `hedge_legs` table; `price-near-stop-audit` consumer | Field is write-once (guarded); SLA timer begins from first write; deep-audit detects stuck > 30 min to trigger SAFE_MODE | Guarded write ensures only the first detection sets the timestamp | BR-EXBOT-005; FR-EXBOT-032 |
| Scan Worker batch-updates `next_light_check_at` | All bots in shard | 1 stmt/shard; prevents per-bot write overhead; jitter distributes load | Jitter is computed per-bot in memory then written in one batch stmt | FR-EXBOT-013; NFR-EXBOT-005 |
| `stop_replacing_started_at` overrun detected (primary path) | `partial_repair` queue; SAFE_MODE entry | Primary detection within 5 min; deep-audit is secondary backstop (6h/1h interval) | `stop_replacing_started_at` set by hedge-sync, cleared in finally block; light-check reads from D1 | FR-EXBOT-033; FR-EXBOT-035 |
| MarketDataDO cache read | All light-check workers in same CF region | All workers share one DO instance per region; single RPC call per refresh interval | Cache `blockNumber` must monotonically increase; regression triggers forced refresh | FR-EXBOT-093; NFR-EXBOT-001 |
| `queue_idempotency` write | `queue_idempotency` table | Prevents double-processing of same light-check message; UNIQUE on `message_id` | Second delivery exits immediately after UNIQUE constraint conflict | FR-EXBOT-011 |
| `range_out` detected (NEW -- US-007) | `bots.lifecycle_state`; `partial_repair` queue; `lp_operations` ledger | Transition to `lp_rebalancing` must be atomic; repair worker uses `lp_operations.idempotency_key UNIQUE` to prevent double execution | If worker crashes after `lifecycle_state` update but before `partial_repair` enqueue, bot is stuck in `lp_rebalancing` -- recovery not described in UC (I-016) | FR-EXBOT-015; US-007 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then | Source |
|---|---|---|---|---|---|
| AC-01 | Drift detected, circuit closed, hedge-sync enqueued | Active bot where `|targetShortEth - lastKnownShortEth| x uniPoolPrice > $25` AND `circuit_breakers.state='closed'` | Light-check worker processes this bot | `hedge-sync` message enqueued with `{botId, reasons=['drift_threshold'], stateVersion}`; zero HL API calls | UC section 3 steps 9-10; AC-EXBOT-005-1 |
| AC-02 | Stop trigger detected, price-near-stop-audit enqueued (not hedge-sync) | Active bot where `hlMarkPrice >= hedge_legs.stop_price` AND `stop_trigger_crossed_at IS NULL` | Light-check worker processes this bot | `stop_trigger_crossed_at` set to now; `price-near-stop-audit` enqueued; no `hedge-sync` for this trigger | UC section 3 step 11; AC-EXBOT-005-2; BR-EXBOT-005 |
| AC-03 | `stop_trigger_crossed_at` already set -- no overwrite | Active bot where `stop_trigger_crossed_at IS NOT NULL` AND `hlMarkPrice >= stop_price` | Light-check worker processes this bot | `stop_trigger_crossed_at` is NOT overwritten; `price-near-stop-audit` still enqueued | UC section 4 A3; BR-EXBOT-005 |
| AC-04 | Circuit open -- hedge-sync suppressed, stop monitoring continues | Bot with `circuit_breakers.state='open'` | Light-check processes bot | No `hedge-sync` enqueued; if stop criteria met, `price-near-stop-audit` still enqueued | UC section 4 A1; FR-EXBOT-014 |
| AC-05 | Circuit half_open -- exactly one probe hedge-sync | Bot with `circuit_breakers.state='half_open'` AND `half_open_probe_used=0` | Light-check detects rebalance need | `half_open_probe_used` atomically set to 1; exactly one `hedge-sync` enqueued; subsequent light-checks do not enqueue another | UC section 4 A2; FR-EXBOT-040 |
| AC-06 | Bot in lp_rebalancing -- skipped entirely | Bot with `lifecycle_state='lp_rebalancing'` | Light-check worker encounters this bot | No evaluation, no queue messages; worker moves to next bot | UC section 2; AC-EXBOT-005-4 |
| AC-07 | Duplicate message -- idempotency gate | Same `message_id` delivered twice to light-check queue | Second delivery processed | Second worker exits immediately after UNIQUE conflict; no double evaluation | UC section 3 step 5; FR-EXBOT-011 |
| AC-08 | HL API calls = 0 across entire light-check worker | Any active bot processed by light-check | Full evaluation runs | Zero outbound HL API calls; all data from D1 + MarketDataDO | BR-EXBOT-003; NFR-EXBOT-001 |
| AC-09 | `drift_threshold` uses uniPoolPrice, not hlMarkPrice | Active bot near drift threshold | Light-check evaluates `deltaErrorUsd` | `deltaErrorUsd = |targetShortEth - actualShortEth| x uniPoolPrice`; pool slot0 price used | FR-EXBOT-012 (3-way split) |
| AC-10 | `stop_trigger_crossed_at` uses hlMarkPrice, not uniPoolPrice | Active bot near stop price | Light-check evaluates stop trigger | Comparison is `hlMarkPrice >= hedge_legs.stop_price`; pool price NOT used for stop detection | FR-EXBOT-012 (3-way split) |
| AC-11 | stop_replacing_started_at overrun detected, partial_repair + SAFE_MODE triggered | Bot where `stop_replacing_started_at IS NOT NULL AND (now - stop_replacing_started_at) > 60s` | Light-check pass executes | `partial_repair` message enqueued with `reason='stop_replacing_overrun'`; SAFE_MODE entry triggered within 5 min | FR-EXBOT-033; FR-EXBOT-012 -- Inferred from SRS; not in UC section 3: needs confirmation |
| AC-12 | hedge_stopped_cooldown bot -- light-check runs, hedge-sync suppressed | Bot with `lifecycle_state='hedge_stopped_cooldown'` | Light-check processes this bot | Evaluation runs normally; if stop criteria met, `price-near-stop-audit` enqueued; `hedge-sync` NOT enqueued | SRS states.md -- Inferred; UC does not mention this state (I-005) |
| AC-13 | range_out detected, lp_rebalancing transition and partial_repair enqueued (NEW -- US-007) | Active bot where `currentTick < tickLower OR currentTick >= tickUpper` | Light-check worker processes this bot | `bots.lifecycle_state` transitions to `lp_rebalancing`; `partial_repair` message enqueued with LP rebalance op; no `hedge-sync` enqueued for this bot | FR-EXBOT-015; US-007 AC-EXBOT-007-1 -- Inferred; absent from UC section 3 (I-016) |

---

## 9. Non-Functional Requirements

| Group | Requirement | Test Impact | Source |
|---|---|---|---|
| Throughput | System must scan 10,000 bots in a 5-minute window (33.3 bots/sec sustained) | Load test: 10k bots scanned within 5-min window; no queue backlog accumulation | NFR-EXBOT-001 |
| Rate Limit | HL API usage must not exceed 800 weight/min; light-check contribution = 0 | Verify zero HL calls during any light-check pass | NFR-EXBOT-004; BR-EXBOT-003 |
| D1 Write Budget | `next_light_check_at` batch-updated per shard (1 stmt); no unconditional per-bot UPDATE | Test: one D1 write stmt per shard regardless of bot count in that shard | NFR-EXBOT-005 |
| Precision | All hedge, stop, and margin computations use BigDecimal; float forbidden | Test BigDecimal usage for `lpEthAmount`, `deltaErrorUsd`, `targetShortEth` | NFR-EXBOT-008 |
| Idempotency | `queue_idempotency.message_id` UNIQUE prevents double execution | Test: same message delivered twice to second delivery exits immediately | NFR-EXBOT-007 |
| Concurrency | Max 6 simultaneous outbound connections per CF Worker invocation | Not directly testable in unit tests; relevant for integration testing | NFR-EXBOT-011 |
| Availability | MarketDataDO unavailability: worker cannot compute LP amount -- behavior undefined in UC (I-007) | Test: MarketDataDO unavailable causes specific worker behavior | NFR-EXBOT-010 |
| Security | No key material in light-check; no HL agent key decryption in this path | Verify: no `hl_agent_keys` read in light-check code path | NFR-EXBOT-006 |

---
## 10. Gaps, Conflicts, and Open Questions

### 10.1 Issue Register and Questions

Issues I-001 through I-014 carry over from v1 (all remain Open; none resolved by HLD-2026-06-18). Issues I-015 through I-017 are new findings from the v3 re-audit.

| ID | Priority | Issue Type | Source Trace | Finding | Impact on Tester Understanding | Suggested Question or Fix | Status |
|---|---|---|---|---|---|---|---|
| I-001 | High | MISSING_INFO | UC section 3 (no mention); FR-EXBOT-033; FR-EXBOT-012 SRS | The `stop_replacing_started_at` overrun detection path is completely absent from UC section 3 main flow. SRS FR-EXBOT-033 (primary detection, 5 min) and FR-EXBOT-012 (SRS spec body) explicitly require each light-check pass to evaluate `stop_replacing_started_at IS NOT NULL AND age > 60s` and enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE. This is a primary safety guard, not a secondary backstop. | Tester cannot design a test case for the stop_replacing overrun to SAFE_MODE path because the UC does not describe the trigger, the condition check, or the expected system response. | BA/Tech Lead: add step to UC section 3 main flow describing the `stop_replacing_started_at` check. This is a required P0 behavior per FR-EXBOT-033. | Open |
| I-002 | High | MISSING_INFO | UC section 4 A4; FR-EXBOT-023 | A4 says "`range_boundary_near` 90%: Enqueue price-near-stop-audit even before price reaches stop" but FR-EXBOT-023 lists `range_boundary_near` as a `RebalanceReason[]`, which normally routes to `hedge-sync`. A4 implies it routes to `price-near-stop-audit`. These are contradictory. | Tester cannot determine the correct routing for `range_boundary_near`: does it enqueue `hedge-sync`, `price-near-stop-audit`, or both? | BA: clarify whether `range_boundary_near` routes to (a) `hedge-sync`, (b) `price-near-stop-audit` as implied by A4, or (c) both. Fix the UC to be explicit. | Open |
| I-003 | High | MISSING_INFO | UC section 3 step 11; FR-EXBOT-012 SRS 3-way price split | UC step 11 says "If `markPrice >= stop_price`" without specifying the source of `markPrice`. FR-EXBOT-012 SRS states `hlMarkPrice` is "used only for stop trigger detection" and comes from HL mark price. However, the UC describes zero HL API calls (BR-EXBOT-003). How is `hlMarkPrice` obtained without an HL call? The SRS does not clarify whether `hlMarkPrice` is cached in D1 or in a Durable Object. The field `eth_price_usd` in `bot_runtime_state` (ERD) may be the candidate, but this is not stated anywhere in the documents. | Tester cannot write a test case for stop trigger detection because the data source for `markPrice` is undefined. If it requires an HL call, this is a BR-EXBOT-003 violation. If cached, the staleness and update mechanism are undefined. | BA/Tech Lead: specify the source of `hlMarkPrice` used in light-check stop trigger detection. Is it `bot_runtime_state.eth_price_usd`? Is it read from MarketDataDO? Does it come from a prior hedge-sync reconcile result? | Open |
| I-004 | High | MISSING_INFO (OQ-EXBOT-10) | SRS spec section 9 OQ-EXBOT-10; FR-EXBOT-023 | `range_boundary_near` evaluation formula is explicitly unresolved in SRS: "is '90% to upper/lower' measured in tick distance or price distance?" Neither the UC nor FRD provides the formula. | Tester cannot write a test case for `range_boundary_near` detection. Test input (currentTick vs tick range boundary) cannot be defined without the formula. | zen/SOTATEK to resolve OQ-EXBOT-10 and update FR-EXBOT-012 or FRD with the explicit formula. | Open |
| I-005 | High | MISSING_INFO | SRS states.md (State Registry); UC section 2 (preconditions) | `hedge_stopped_cooldown` state: the SRS State Registry explicitly states light-check RUNS for this state ("run (no hedge-sync)"). UC section 2 preconditions and UC section 3 skip logic do not mention this state at all. Testers would assume light-check is skipped (by omission) or be confused about the expected behavior. | Tester designing skip-condition test cases will miss the `hedge_stopped_cooldown` scenario. Stop monitoring behavior during this state (which is required) would not be verified. | BA: add `hedge_stopped_cooldown` to UC section 2 or section 3 with explicit statement: "Light-check runs but hedge-sync enqueue is suppressed for this state; stop monitoring continues." | Open |
| I-006 | Medium | UNCLEAR_INFO | FR-EXBOT-023; frd.md | `time_fallback` reason: condition is "4h since last adjustment." Neither the UC nor FRD specifies which D1 field represents "last adjustment time." Candidates: `bot_runtime_state.last_hl_reconcile_at`, `hedge_legs.updated_at`, or the timestamp of the last `rebalance_attempts` row. The correct field is ambiguous. | Tester cannot set up correct preconditions for `time_fallback` test cases without knowing which timestamp field to set. | BA/Tech Lead: specify the exact D1 field used as "last adjustment time" for the `time_fallback` reason. | Open |
| I-007 | Medium | MISSING_INFO | UC section 3 step 7; FR-EXBOT-093 | UC does not describe the failure path when `MarketDataDO` is unavailable or its cache is stale beyond 2x refresh interval. FR-EXBOT-093 states the DO forces a refresh on staleness, but does not say what the light-check worker should do if the DO is unreachable. | Tester cannot design a test case for MarketDataDO failure mode in the context of light-check. | BA: add exception path to UC section 3 or section 4: what should the light-check worker do if MarketDataDO is unavailable? (Skip bot? Enter SAFE_MODE? Re-queue?) | Open |
| I-008 | Medium | UNCLEAR_INFO (OQ-EXBOT-11) | SRS spec section 9 OQ-EXBOT-11; FR-EXBOT-023 frd | `drift_threshold` formula: `deltaErrorUsd > max($25, lpValueUsd x 3%)`. The formula requires `lpValueUsd` but OQ-EXBOT-11 states: "how is `bot_runtime_state.lp_value_usd` computed and updated?" is unresolved. The candidate formula `(lpEthAmount x uniPoolPrice) + lpUsdcAmount` is not confirmed by zen. | Tester cannot compute the expected `drift_threshold` trigger point. The "$25 floor vs 3% of LP value" threshold crossover test cannot be written. | zen/SOTATEK: resolve OQ-EXBOT-11 and update FR-EXBOT-011 with the confirmed `lpValueUsd` formula. | Open |
| I-009 | Medium | UNCLEAR_INFO (OQ-EXBOT-12) | SRS spec section 9 OQ-EXBOT-12; FR-EXBOT-023 | `funding_alert` reason requires "7d APR < -15%." The aggregation formula from `funding_daily_metrics` is unresolved (OQ-EXBOT-12). The candidate formula (sum of latest 7 rows `funding_net_usd` annualized relative to LP capital) is not confirmed. | Tester cannot set up `funding_daily_metrics` test data to trigger or not trigger `funding_alert` without the confirmed aggregation formula. | zen: resolve OQ-EXBOT-12 and update SRS with the confirmed 7-day APR formula. | Open |
| I-010 | Low | UNCLEAR_INFO | UC section 3 step 10; FR-EXBOT-027 | The UC mentions enqueuing `hedge-sync` with `{botId, reasons, stateVersion}` but does not explicitly state the source of `stateVersion`. FR-EXBOT-027 clarifies it comes from `bot_runtime_state.state_version`. The UC does not trace this. | Minor: tester may not know to verify `stateVersion` field in the enqueued message without reading FR-EXBOT-027 separately. | Suggestion: UC step 10 should add "(stateVersion from bot_runtime_state.state_version)" for traceability. | Open |
| I-011 | Low | SOLUTION_DETAIL_LEAK | UC section 3 step 3 | UC states "Scan Worker sends per-bot messages to light-check queue via `chunkSendBatch`" -- naming the internal helper function is an implementation detail. The business behavior is "send in batches of max 100 per CF limit." | Minor: does not block test design; the business constraint (max 100/batch) is the relevant fact. | Suggestion: rephrase to describe the constraint rather than the helper function name. | Open |
| I-012 | High | CROSS_SOURCE_CONFLICT | `frd.md FR-EXBOT-032` line 283 vs `srs/spec.md FR-EXBOT-033` | `frd.md FR-EXBOT-032` states: "Overrun (>60s) detected by audit to SAFE_MODE." `srs/spec.md FR-EXBOT-033` explicitly states light-check is the primary detector (within 5 min) for `stop_replacing_started_at` overrun; deep-audit is only the secondary backstop (6h/1h cadence). A developer reading only frd.md would implement overrun detection solely in deep-audit (6h lag), leaving the system unprotected for up to 6 hours. Both documents declare "SPEC v5.2.6 prevails" -- srs/spec.md is canonical. Still not resolved in frd.md as of 2026-06-18 update. | Tester writing test cases against frd.md alone would test only a 6-hour detection window, missing the 5-minute primary detection requirement. | BA/Tech Lead: update `frd.md FR-EXBOT-032` to explicitly state that light-check is the primary detector (within 5 min) and deep-audit is only the secondary backstop, matching srs/spec.md FR-EXBOT-033. | Open |
| I-013 | Medium | INTERNAL_INCONSISTENCY | UC section 7 FR Trace; `usecases/index.md` UC row; UC frontmatter `linked_stories` | Three inconsistencies found: (1) UC section 7 FR Trace lists FR-013, 014, 015, 016, 023, 032 but omits FR-012 -- the core "zero HL calls" requirement. `usecases/index.md` correctly lists FR-012. (2) `usecases/index.md` FR trace omits FR-023 (canonical RebalanceReason enum). (3) UC frontmatter `linked_stories` as of 2026-06-18 includes US-EXBOT-005, 006, 007, 008 but `usecases/index.md` lists US-EXBOT-005, 006, 007, 008 (appears updated). UC section 7 FR Trace still does not include FR-015 (LP rebalance) despite US-007 now being linked. | A tester relying on UC section 7 FR trace to scope review would miss FR-012 (HL weight=0 requirement) and FR-015 (LP rebalance). | BA: (1) Add FR-012 to UC section 7 FR Trace. (2) Add FR-023 and FR-015 to both UC section 7 and index. (3) Verify linked_stories is consistent between UC and index. | Open |
| I-014 | Low | MISSING_INFO | `frd.md FR-EXBOT-060`; US-EXBOT-010 AC-1; UC section 3 step 9 | The UC states light-check reads `hedge_legs.margin_status` from D1 and evaluates `margin_warning` as a RebalanceReason. However, the UC does not describe the downstream constraint: when `margin_warning` is included in the `hedge-sync` payload, the hedge-sync worker must block any size-increase adjustments (FR-EXBOT-060: "warning to disable size-increase hedges"). This cross-UC behavioral constraint is not traced in UC section 7. | Tester may write a test case where light-check enqueues hedge-sync with `reason=['margin_warning']` but not verify that the downstream hedge-sync correctly blocks size-increase -- because the UC gives no indication this constraint exists. | Suggestion: UC section 7 FR Trace or section 3 routing table should note that `margin_warning` reason constrains hedge-sync behavior per FR-EXBOT-060. | Open |
| I-015 | High | CROSS_SOURCE_CONFLICT | US-EXBOT-007 AC-EXBOT-007-1 vs FR-EXBOT-015 (SRS spec.md) | US-007 AC-EXBOT-007-1 references `BnzaExVault.vaultRebalance()` and `VaultRebalanced` event. FR-EXBOT-015 (SRS spec, canonical) describes the LP rebalance as: call `BnzaExVault.redeem(tokenId)` to close the existing LP NFT, compute a new tick range, then mint a new LP NFT. The function name `vaultRebalance()` and the event `VaultRebalanced` do not appear in FR-EXBOT-015 or anywhere else in SRS or FRD. Both documents declare "SPEC v5.2.6 prevails" -- srs/spec.md is canonical. | Developer reading US-007 would implement `vaultRebalance()`. Developer reading FR-EXBOT-015 would implement `redeem() + mint`. These are architecturally different: one call vs two calls, different events emitted. Tester writing integration tests against the Vault ABI cannot define the correct call sequence or expected events without resolution. | BA/Tech Lead: reconcile US-007 AC-EXBOT-007-1 with FR-EXBOT-015. Either (a) update US-007 to use `redeem(tokenId)` + mint + emit `VaultMinted`/`VaultRedeemed`, or (b) confirm that `vaultRebalance()` is a new function to be added to BnzaExVault and update FR-EXBOT-015 accordingly. Blocked until zen confirms Vault ABI. | Open |
| I-016 | High | MISSING_INFO | FR-EXBOT-015 (SRS spec); UC section 3 main flow; UC section 7 FR Trace | The LP range rebalance trigger path (`range_out` to `lp_rebalancing` transition + `partial_repair` enqueue) is entirely absent from UC section 3 main flow, UC section 4 alternate flows, and UC section 7 FR Trace. FR-EXBOT-015 is not listed in UC section 7. Despite US-007 being added to `linked_stories` on 2026-06-18, the UC body was not updated to describe: (a) the `range_out` detection step, (b) the `lifecycle_state` transition to `lp_rebalancing`, (c) the `partial_repair` queue enqueue, (d) the hedge suppression rule during `lp_rebalancing`. Additionally, the crash-recovery path (worker crashes after `lifecycle_state` update but before `partial_repair` enqueue) is not described. | A tester reading UC section 3 main flow has no indication that `range_out` should trigger a `lp_rebalancing` transition. All LP rebalance behavior is invisible to the tester, making it impossible to design test cases for this P1 feature. | BA: update UC section 3 main flow to add the `range_out` evaluation step, the `lifecycle_state` transition to `lp_rebalancing`, and the `partial_repair` enqueue. Add FR-015 to UC section 7 FR Trace. Describe the crash-recovery invariant (if worker crashes after transition, repair worker must detect the state and resume). | Open |
| I-017 | Major | CROSS_SOURCE_CONFLICT | `srs/flows.md` F-05 (2026-06-12, NOT updated) vs `srs/spec.md` + `srs/states.md` + `frd.md` (all updated 2026-06-18) | `srs/flows.md` F-05 "bot_safe_close + Automatic Re-Entry" was NOT updated on 2026-06-18. It still contains the entire park/re-entry loop dropped by HLD-2026-06-18: `vaultClose(tokenId, dest=UNINVESTED)`, `FundsParked` event, `lifecycle_state=cooldown (60 min)`, `uninvestedBalanceOf(user, botId)`, `parked` state, and `REENTRY` worker loop. All contradict: `srs/states.md` HLD-2026-06-18 note ("cooldown and parked lifecycle states removed"), `srs/spec.md` FR-EXBOT-070/073 (no park/re-deploy, direct to `closed`), and `frd.md` changelog and FR-EXBOT-002 note. Note: flows.md F-05 is directly relevant to light-check because light-check monitors bots and must correctly handle the `lifecycle_state` transitions after `bot_safe_close`. A `cooldown` or `parked` state visible in flows.md would mislead dev into implementing skip logic for states that no longer exist. | Any developer or tester reading flows.md F-05 gets a contradictory picture of post-`bot_safe_close` lifecycle behavior. Specifically: a developer implementing light-check state-skip logic based on flows.md would add `cooldown` and `parked` to the skip list (non-existent states), wasting code and creating dead logic. A tester creating test data with `lifecycle_state='cooldown'` would be testing behavior that cannot occur. | BA action required: update `flows.md` F-05 to reflect `bot_safe_close to closed` directly (no re-entry worker, no cooldown/parked state, no uninvestedBalanceOf). Also update `frd.md FR-EXBOT-031` if it still references "Section 16.7 cooldown closed loop." | Open |


### 10.2 Dependencies to Monitor

| Dependency | Type | Impact | Owner | Status |
|---|---|---|---|---|
| OQ-EXBOT-10 -- `range_boundary_near` formula | Open Question | Blocks `range_boundary_near` test case design entirely | zen/SOTATEK | Open |
| OQ-EXBOT-11 -- `lpValueUsd` formula | Open Question | Blocks `drift_threshold` formula verification (3% term) | zen/SOTATEK | Open |
| OQ-EXBOT-12 -- 7-day APR aggregation | Open Question | Blocks `funding_alert` test case design entirely | zen | Open |
| OQ-EXBOT-09 -- MarketDataDO cache refresh interval | Open Question | Affects staleness boundary test cases for MarketDataDO | zen/Phase 0 NV-12 | Open |
| IC-EXBOT-003 -- Uniswap V3 pool address + wethIndex (Base + Optimism) | Integration Constraint | Affects LP ETH amount computation tests (correct pool address + wethIndex per chain) | Phase 0 NV-12 | Open |
| FR-EXBOT-033 SAFE_MODE path for stop_replacing_started_at | SRS requirement | Primary safety guard; missing from UC (I-001) | BA / Tech Lead | Open |
| hlMarkPrice source in light-check (I-003) | Architecture / data-flow | Stop trigger detection test case | BA / Tech Lead | Open |
| frd.md FR-EXBOT-032 vs srs FR-EXBOT-033 conflict (I-012) | Cross-source conflict | Dev may implement overrun detection only in deep-audit (6h lag), missing 5-min primary window | BA / Tech Lead | Open |
| BnzaExVault.vaultRebalance() vs redeem()+mint conflict (I-015) | Cross-source conflict (US-007 vs FR-EXBOT-015) | Blocks LP rebalance integration test design; ABI undefined until zen deploys | BA / Tech Lead / zen | Open |
| flows.md F-05 stale park/re-entry loop (I-017) | Cross-source conflict | Dev implementing light-check skip logic may add dead code for non-existent `cooldown`/`parked` states | BA | Open |

---

### 10.3 Audit Summary

#### Scoring Table

| # | Area | Max | Score | Status | Notes |
|---|---|---|---|---|---|
| 1 | Function / Operation and Data Object Inventory | 20 | 12 | Partial | Inventory covers most operations. New gap: LP rebalance trigger path (I-016) entirely absent from UC; flows.md F-05 stale (I-017) adds a cross-source conflict. US-007 addition to linked_stories increases scope without updating UC main flow. |
| 2 | Data Object / State Attributes, Business Rules, Validations | 25 | 12 | Partial | 3-way price split and guarded write (BR-EXBOT-005) documented. Blockers: `hlMarkPrice` source unspecified (I-003), `lpValueUsd` formula OQ-EXBOT-11 (I-008), `funding_alert` formula OQ-EXBOT-12 (I-009), `range_boundary_near` formula blocked (I-004). New: US-007 vs FR-EXBOT-015 conflict (I-015) adds another unresolved Vault call. Auto-cap: Blocker present, max 40% = 10/25. |
| 3 | Functional Logic and Workflow Decomposition | 25 | 10 | Partial | Happy path, circuit open/half_open, duplicate message, stop routing documented. Critical gaps: `stop_replacing_started_at` overrun path absent (I-001 -- Blocker), `range_boundary_near` routing ambiguous (I-002 -- Blocker), `range_out to lp_rebalancing` path absent (I-016 -- High), `hedge_stopped_cooldown` missing (I-005). Auto-cap: Blocker present, max 40% = 10/25. |
| 4 | Functional Integration and Data Consistency | 15 | 10 | Partial | Queue fan-out, stateVersion consistency, MarketDataDO sharing, idempotency covered. Gaps: MarketDataDO failure path undefined (I-007); `margin_warning` cross-UC constraint not traced (I-014); LP rebalance crash-recovery path not described (I-016). |
| 5 | UC / Spec Documentation Quality | 15 | 8 | Partial | Pre-existing issues: I-001 (stop_replacing absent), I-005 (hedge_stopped_cooldown missing), I-002 (range_boundary_near routing conflict), I-003 (markPrice source), I-012 (frd vs srs overrun conflict), I-013 (FR-012/FR-023 omissions). New issues: I-013 further aggravated (FR-015 also missing from UC FR Trace), I-015 (US-007 vs FR-EXBOT-015 Vault function conflict), I-016 (LP rebalance path absent), I-017 (flows.md F-05 stale). |
| **Total** | | **100** | **52** | **Not Ready** | |

#### Blockers (must resolve before test design proceeds)

| # | Issue ID | Finding |
|---|---|---|
| B1 | I-001 | `stop_replacing_started_at` overrun detection path absent from UC -- primary SAFE_MODE guard (FR-EXBOT-033) completely undocumented in UC section 3 |
| B2 | I-003 | `hlMarkPrice` source in light-check undefined -- stop trigger test cases cannot be designed without knowing the data source |
| B3 | I-002 | `range_boundary_near` routing ambiguous (hedge-sync vs price-near-stop-audit) -- UC section 4 A4 directly contradicts the RebalanceReason enum routing rule |
| B4 | I-012 | `frd.md FR-EXBOT-032` says "detected by audit" -- directly contradicts `srs/spec.md FR-EXBOT-033` primary detection (5 min); dev reading frd.md alone would implement wrong detection cadence |
| B5 | I-015 | US-007 AC-EXBOT-007-1 references `BnzaExVault.vaultRebalance()` -- conflicts with FR-EXBOT-015 (`redeem() + mint`); integration test ABI cannot be defined |
| B6 | I-016 | `range_out to lp_rebalancing` transition and `partial_repair` enqueue path entirely absent from UC section 3 main flow and FR Trace -- US-007 linked but UC not updated |

#### Major Issues

| # | Issue ID | Finding |
|---|---|---|
| M1 | I-004 | OQ-EXBOT-10: `range_boundary_near` formula unresolved -- test inputs undefined |
| M2 | I-005 | `hedge_stopped_cooldown` state not described in UC -- creates skip-condition test gap |
| M3 | I-008 | OQ-EXBOT-11: `lpValueUsd` formula unresolved -- `drift_threshold` 3% term unverifiable |
| M4 | I-009 | OQ-EXBOT-12: 7-day APR formula unresolved -- `funding_alert` test cases blocked |
| M5 | I-013 | FR-012 and FR-015 missing from UC section 7 FR Trace; metadata inconsistent across artefacts |
| M6 | I-017 | `srs/flows.md` F-05 stale -- still contains park/re-entry loop dropped by HLD-2026-06-18; CROSS_SOURCE_CONFLICT across spec.md, states.md, frd.md vs flows.md |

#### Recommendation

The UC covers the core light-check pipeline (queue fan-out, idempotency gate, TickMath LP computation, 7 of 9 RebalanceReasons, circuit breaker routing, stop trigger guarded write) with sufficient detail for those paths. However, six areas now block test design:

1. The `stop_replacing_started_at` overrun detection (B1) is a primary P0 safety guard (FR-EXBOT-033) entirely missing from UC section 3. It must be added before test design can proceed.
2. A direct conflict between `frd.md FR-EXBOT-032` ("detected by audit") and `srs/spec.md FR-EXBOT-033` ("light-check is primary detector, within 5 min") (B4) must be resolved in frd.md.
3. The source of `hlMarkPrice` in stop trigger detection (B2/I-003) must be clarified -- architecturally critical given the HL weight = 0 invariant.
4. US-007 was added to `linked_stories` but UC section 3 was not updated: the entire LP rebalance trigger path (`range_out to lp_rebalancing`, `partial_repair` enqueue) is absent (B6/I-016). Additionally, US-007 references `vaultRebalance()` which conflicts with FR-EXBOT-015 `redeem() + mint` (B5/I-015).
5. `srs/flows.md` F-05 was not updated and still shows the dropped park/re-entry loop (I-017), creating a CROSS_SOURCE_CONFLICT with three other documents updated on 2026-06-18.
6. Three OQ-level formulas (OQ-EXBOT-10/11/12) block `range_boundary_near`, `drift_threshold` (3% term), and `funding_alert` test cases.

**Verdict: Not Ready (52/100).** Score declined from 61 (v1) to 52 (v3) due to three new issues: B5 (I-015 US-007 vs FR-EXBOT-015 Vault conflict), B6 (I-016 LP rebalance path absent), and M6 (I-017 flows.md F-05 stale). Test design can proceed for core drift-detection and idempotency paths after B1--B6 are resolved. Formula-dependent test cases (`range_boundary_near`, `drift_threshold` full, `funding_alert`) must wait for OQ resolution.

---

## 11. Change Log

| Version | Date | Updated By | Content |
|---|---|---|---|
| v1 | 2026-06-18 | QC UC Read ExBot Agent | Initial audited report -- qc-uc-read-exbot skill (SRS-first lean variant). 14 issues, 4 Blockers. Score 61/100, Not Ready. |
| v3 | 2026-06-18 | QC UC Read ExBot Agent | Re-audit against HLD-2026-06-18 baseline. UC updated: US-007 and US-008 added to linked_stories. SRS updates: spec.md, states.md updated (park/re-entry dropped, cooldown/parked states removed). flows.md NOT updated (I-017 new). frd.md updated. New issues: I-015 (US-007 vaultRebalance() vs FR-EXBOT-015 redeem()+mint CROSS_SOURCE_CONFLICT), I-016 (range_out to lp_rebalancing path absent from UC main flow MISSING_INFO), I-017 (flows.md F-05 stale CROSS_SOURCE_CONFLICT). v1 issues I-001 through I-014 remain Open. Score revised from 61 to 52. Blockers now 6 (B1-B6). |

---

*UC Readiness Review -- English output per qc-uc-read-exbot skill output contract and qc-writting-rules.md*
