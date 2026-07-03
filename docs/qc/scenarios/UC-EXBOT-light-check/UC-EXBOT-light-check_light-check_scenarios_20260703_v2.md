# Test Scenarios — UC-EXBOT-light-check Execute Periodic Light-Check

> Source: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260703_v2.md
> Generated: 2026-07-03
> Author: QC Func Scenario Design Exbot Agent
> Version: v2
> Domain/Architecture: Cloudflare Workers (no UI) — Cron Worker (1 min) → bot-scan queue → Scan Worker → light-check queue → Light-Check Worker → [hedge-sync | price-near-stop-audit | partial_repair] queues. State stored in D1 (state_db_shard) + MarketDataDO + HlMarkDO. Zero Hyperliquid API calls (BR-EXBOT-003).

> **v2 changes vs v1:**
> - Corrected TS_LC_008, 009, 010: added `next_light_check_at` update assertion for skipped bots (I-08 confirmed).
> - Corrected TS_LC_015: explicit HlMarkDO as primary source for stop trigger evaluation.
> - Corrected TS_LC_017: assert BOTH `bots.status` AND `bots.lifecycle_state` atomically in 1 UPDATE BEFORE enqueue (I-07 confirmed).
> - Corrected TS_LC_020, 039, 047: `range_out` → light-check enqueues hedge-sync; `lifecycle_state='lp_rebalancing'` is set DOWNSTREAM by hedge-sync handler, NOT by light-check (I-05 confirmed).
> - Corrected TS_LC_046: MarketDataDO stale → fail-fast, tick skipped entirely — NOT a forced refresh (I-12 confirmed).
> - Added TS_LC_061–075: new scenarios for HlMarkDO staleness fallback (I-01), funding_alert BVA (I-04), lpValueUsd=0 edge case (I-03), mixed-reason with range_out (I-05), SAFE_MODE atomic assertion (I-07), next_light_check_at for skipped bots (I-08), MarketDataDO fail-fast (I-12), acceptance scenarios.
> - Out-of-Scope Flags updated: removed 5 previously-blocked flags (OQ-EXBOT-011, OQ-EXBOT-012, OQ-EXBOT-017, I-07, I-08 all resolved). range_boundary_near (I-02) remains blocked.

---

## UC-EXBOT-light-check — Execute Periodic Light-Check

---

### Scenario ID: TS_LC_001
**Scenario Title:** Happy path — active bot with drift_threshold reason triggers hedge-sync, zero HL calls
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 steps 1–13; SRS BR-EXBOT-003; FR-EXBOT-012; AC-EXBOT-005-1
**Test Type:** Functional
**Description:** Deliver a light-check queue message for an active bot whose `|targetShortEth − lastKnownShortEth| × uniPoolPrice > max($25, lpValueUsd × 3%)` (drift_threshold triggered). The Light-Check Worker must evaluate `RebalanceReason[]` using only D1 + MarketDataDO (zero HL API calls), enqueue a hedge-sync message with `{botId, reasons:['drift_threshold'], stateVersion}`, update `queue_idempotency.state='succeeded'`, and leave `next_light_check_at` updated to `now + 5min + jitter(±45s)`. HL API call count must remain 0 throughout.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_002
**Scenario Title:** Happy path — active bot with no rebalance reason, no fan-out, idempotency finalized
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 steps 5, 9, 13; UC §5
**Test Type:** Functional
**Description:** Deliver a light-check message for an active bot whose `RebalanceReason[]` evaluates to empty (no drift, in range, margin ok, funding ok, not time_fallback). The Light-Check Worker must not enqueue any downstream message (no hedge-sync, no price-near-stop-audit, no partial_repair), must update `queue_idempotency.state='succeeded'`, and must not mutate any D1 bot state fields.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_003
**Scenario Title:** Cron fan-out uses chunkSendBatch to bot-scan queue (not direct sendBatch)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 1; SRS FR-EXBOT-010
**Test Type:** Functional
**Description:** Trigger a Cron Worker execution. Verify that all bot-scan queue messages are sent via the `chunkSendBatch()` helper (max 100 messages per call). Direct `queue.sendBatch()` without the helper must not be used at any point in the Cron → bot-scan path.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_004
**Scenario Title:** Scan Worker query filters eligible bots correctly — status active + next_light_check_at <= now
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 2; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Set up a D1 shard with bots in various states: `status='active'` with `next_light_check_at <= now` (eligible), `status='active'` with `next_light_check_at > now` (not yet due), `status='paused'`, `status='closed'`. The Scan Worker query must return only the eligible active bots whose check is due and exclude all others.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_005
**Scenario Title:** next_light_check_at batch-updated as 1 statement per shard with jitter (not per-bot)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 4; SRS FR-EXBOT-013; NFR-EXBOT-005; AC-LC-13
**Test Type:** Functional
**Description:** After the Scan Worker enqueues per-bot light-check messages, verify that `next_light_check_at` is batch-updated with exactly 1 D1 UPDATE statement per shard (not one per bot). The resulting value for each bot must fall in the range `[now + 4m15s, now + 5m45s]` (5 min ± 45s jitter).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_006
**Scenario Title:** Idempotency insert at worker start — new message_id accepted, state set to started
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 5; SRS FR-EXBOT-011
**Test Type:** Functional
**Description:** Deliver a light-check message with a fresh `message_id` not present in `queue_idempotency`. The Light-Check Worker must successfully insert a row with `state='started'` and `expires_at = now + 1min` (not NULL) before processing any bot logic. After completing all fan-out logic, the row must be updated to `state='succeeded'`.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_007
**Scenario Title:** Idempotency — duplicate light-check message for same message_id exits immediately, no mutation
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 5; SRS FR-EXBOT-011; AC-LC-02
**Test Type:** Functional
**Description:** Pre-insert a `queue_idempotency` row with the same `message_id` as the incoming light-check message. The Light-Check Worker must detect the UNIQUE constraint conflict on insert and exit immediately without enqueuing any downstream message, without reading D1 bot state, and without mutating any field.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_008
**Scenario Title:** Skip — bot with lifecycle_state='lp_rebalancing' not enqueued for light-check, but next_light_check_at still updated
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §2; SRS FR-EXBOT-012; AC-LC-03; confirmed code
**Test Type:** Functional
**Description:** Set a bot to `status='active'` and `lifecycle_state='lp_rebalancing'` with `next_light_check_at <= now`. When the Scan Worker runs: (1) this bot must NOT appear in the light-check queue — no light-check message must be enqueued for it; (2) `next_light_check_at` MUST still be batch-updated to `now + 5min + jitter(±45s)` — the bot is rescheduled even though it was skipped.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_009
**Scenario Title:** Skip — bot with lifecycle_state='lp_closing' not enqueued for light-check, but next_light_check_at still updated
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §2; SRS FR-EXBOT-012; confirmed code
**Test Type:** Functional
**Description:** Set a bot to `lifecycle_state='lp_closing'` with `next_light_check_at <= now`. Verify the Scan Worker excludes this bot from the light-check queue entirely, AND `next_light_check_at` is still batch-updated for this bot (not forgotten after recovery).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_010
**Scenario Title:** Skip — bot with status='paused' not enqueued for light-check, but next_light_check_at still updated
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §2; SRS FR-EXBOT-003; AC-LC-04; confirmed code
**Test Type:** Functional
**Description:** Set a bot to `status='paused'` with `next_light_check_at <= now`. Verify the Scan Worker excludes this bot from the light-check queue, AND `next_light_check_at` is still batch-updated for this bot so it can resume on schedule after unpausing.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_011
**Scenario Title:** hedge_stopped_cooldown bot — light-check runs normally but hedge-sync suppressed
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §2 note; SRS states.md; AC-LC-05
**Test Type:** Functional
**Description:** Set a bot to `lifecycle_state='hedge_stopped_cooldown'` (status='active'). Deliver a light-check message. The Light-Check Worker must process the bot normally — evaluate RebalanceReason[], check stop trigger, check stop overrun — but must NOT enqueue hedge-sync even if rebalance reasons are present. Stop monitoring (price-near-stop-audit) must still run.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_012
**Scenario Title:** Circuit breaker open — hedge-sync suppressed but stop monitoring continues
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A1; SRS FR-EXBOT-014; AC-LC-08
**Test Type:** Functional
**Description:** Set `circuit_breakers.state='open'` for a bot that also has `markPrice >= stop_price`. Process the light-check message. Verify: (1) no hedge-sync message is enqueued despite rebalance reasons being present; (2) stop monitoring runs — `stop_trigger_crossed_at` is set (if NULL) and `price-near-stop-audit` is enqueued.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_013
**Scenario Title:** Circuit breaker half_open — exactly one probe hedge-sync enqueued, half_open_probe_used set atomically
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A2; SRS FR-EXBOT-040; AC-LC-09
**Test Type:** Functional
**Description:** Set `circuit_breakers.state='half_open'` and `half_open_probe_used=0` for a bot with rebalance reasons. Process the light-check message. Verify: (1) exactly one hedge-sync probe message is enqueued; (2) `half_open_probe_used` is atomically set to 1 in D1.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_014
**Scenario Title:** Circuit breaker half_open already probed — suppress like open, no second probe
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A2; SRS FR-EXBOT-040
**Test Type:** Functional
**Description:** Set `circuit_breakers.state='half_open'` and `half_open_probe_used=1` (already claimed). Process the light-check message with rebalance reasons. Verify no hedge-sync message is enqueued — the worker treats this identically to circuit open.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_015
**Scenario Title:** Stop trigger detected via HlMarkDO (primary source) with stop_trigger_crossed_at NULL — write-once set + price-near-stop-audit enqueued
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 11; SRS FR-EXBOT-032; BR-EXBOT-005; AC-LC-06; confirmed Tech Lead
**Test Type:** Functional
**Description:** Set `hedge_legs.stop_trigger_crossed_at = NULL` and configure `HlMarkDO.markPriceUsd >= stop_price` (HlMarkDO fresh, stale < 120s). Process the light-check message. Verify: (1) the worker reads `markPriceUsd` from `HlMarkDO` as primary source; (2) `stop_trigger_crossed_at` is written with a non-null timestamp (write-once, BR-EXBOT-005); (3) `price-near-stop-audit` is enqueued; (4) NO hedge-sync is enqueued for the stop trigger itself.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_016
**Scenario Title:** Stop trigger detected with stop_trigger_crossed_at already set — no overwrite, price-near-stop-audit still enqueued
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A3; SRS FR-EXBOT-032; BR-EXBOT-005; AC-LC-07
**Test Type:** Functional
**Description:** Pre-set `hedge_legs.stop_trigger_crossed_at` to a non-null timestamp and configure `markPrice >= stop_price`. Process the light-check message. Verify: (1) the existing `stop_trigger_crossed_at` value is NOT overwritten; (2) `price-near-stop-audit` is still enqueued.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_017
**Scenario Title:** Stop replace overrun > 60s — BOTH bots.status AND bots.lifecycle_state set to safe_mode atomically in 1 UPDATE BEFORE enqueue, then partial_repair enqueued
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033; confirmed code; AC-LC-12
**Test Type:** Functional
**Description:** Set `hedge_legs.stop_replacing_started_at` to a timestamp > 60 seconds in the past (NOT NULL). Process the light-check message. Verify all of the following in order: (1) `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` are set atomically within a single D1 UPDATE statement — tester must assert both fields simultaneously; (2) the atomic UPDATE completes BEFORE `partial_repair` is enqueued; (3) `partial_repair` message is enqueued with `reason='stop_replacing_overrun'`.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_018
**Scenario Title:** Stop replace overrun exactly at 60s boundary — should NOT trigger overrun detection
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Set `stop_replacing_started_at` to exactly 60 seconds ago. Process the light-check message. Verify that the overrun condition `age > 60s` is NOT triggered — no `partial_repair(stop_replacing_overrun)` is enqueued and `lifecycle_state` remains unchanged.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_019
**Scenario Title:** Stop replace overrun at 61s boundary — triggers overrun detection
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Set `stop_replacing_started_at` to exactly 61 seconds ago. Process the light-check message. Verify that the overrun condition `age > 60s` IS triggered — `bots.status='safe_mode'` AND `lifecycle_state='safe_mode'` are set atomically, then `partial_repair(stop_replacing_overrun)` is enqueued.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_020
**Scenario Title:** range_out reason — light-check enqueues single hedge-sync with reasons; lifecycle_state='lp_rebalancing' set DOWNSTREAM by hedge-sync handler
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-015; confirmed code; AC-LC-10
**Test Type:** Functional
**Description:** Set `currentTick` outside `[tickLower, tickUpper]` so that `rangeState != 'in'` (range_out). Process the light-check message. Verify: (1) a single hedge-sync message is enqueued with `reasons:['range_out']`; (2) light-check does NOT set `bots.lifecycle_state='lp_rebalancing'` — that transition is the downstream responsibility of the hedge-sync handler; (3) `partial_repair` queue is NOT used for range_out; (4) the bot is NOT filtered in subsequent Scan Worker cycles until hedge-sync handler sets lifecycle_state.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_021
**Scenario Title:** range_boundary_near reason routed to hedge-sync, not price-near-stop-audit
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A4; AC-LC-11; confirmed code
**Test Type:** Functional
**Description:** Configure a bot whose `nearestFraction = min(distToLower, distToUpper) / halfRange <= 0.9` (range_boundary_near condition met, price-based). Process the light-check message. Verify: (1) `range_boundary_near` is included in `RebalanceReason[]`; (2) a hedge-sync message is enqueued (not price-near-stop-audit); (3) light-check does NOT set `lifecycle_state='lp_rebalancing'` — that is hedge-sync handler responsibility.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_022
**Scenario Title:** drift_relative reason alone triggers hedge-sync
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Set `|targetShortEth − actualShortEth| / targetShortEth > 0.15` (drift_relative threshold exceeded) while `deltaErrorUsd <= max($25, lpValueUsd × 3%)` (drift_threshold not triggered). Process the light-check message. Verify `RebalanceReason[]` contains `drift_relative` and hedge-sync is enqueued with `reasons:['drift_relative']`.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_023
**Scenario Title:** margin_warning reason triggers hedge-sync, zero HL calls
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Set `hedge_legs.margin_status='warning'` in D1 (no HL fetch required). Process the light-check message. Verify `RebalanceReason[]` contains `margin_warning` and hedge-sync is enqueued. HL API call count must remain 0.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_024
**Scenario Title:** time_fallback reason — 4h since last adjustment triggers hedge-sync
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Set `bot_runtime_state.last_hl_reconcile_at` to more than 4 hours in the past with no other rebalance conditions triggered. Process the light-check message. Verify `RebalanceReason[]` contains `time_fallback` and hedge-sync is enqueued.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_025
**Scenario Title:** BVA — drift_threshold at exact $25 floor (not triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012; confirmed code
**Test Type:** Functional
**Description:** Configure a small bot where `lpValueUsd × 3% < $25`. Set `deltaErrorUsd` exactly equal to $25.00. Process the light-check message. Verify the `drift_threshold` condition `deltaErrorUsd > max($25, lpValueUsd × 3%)` is NOT triggered (equal is not greater than), and no drift_threshold reason appears in `RebalanceReason[]`. `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_026
**Scenario Title:** BVA — drift_threshold just above $25 floor ($25.01, small bot, triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012; confirmed code
**Test Type:** Functional
**Description:** Configure a small bot where `lpValueUsd × 3% < $25`. Set `deltaErrorUsd = $25.01`. Process the light-check message. Verify the `drift_threshold` condition IS triggered and `drift_threshold` appears in `RebalanceReason[]`.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_027
**Scenario Title:** BVA — drift_threshold at exactly 3% of lpValueUsd (large bot, not triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012; confirmed code
**Test Type:** Functional
**Description:** Configure a large bot where `lpValueUsd × 3% > $25`. Set `deltaErrorUsd` exactly equal to `lpValueUsd × 3%`. Verify the `drift_threshold` condition is NOT triggered (equal is not greater than), and no drift_threshold reason appears in `RebalanceReason[]`. Formula: `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_028
**Scenario Title:** BVA — drift_threshold just above 3% ceiling (large bot, triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012; confirmed code
**Test Type:** Functional
**Description:** Configure a large bot where `lpValueUsd × 3% > $25`. Set `deltaErrorUsd = lpValueUsd × 3% + $0.01`. Verify the `drift_threshold` condition IS triggered and `drift_threshold` appears in `RebalanceReason[]`.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_029
**Scenario Title:** BVA — drift_relative at exactly 0.15 (not triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Set `|targetShortEth − actualShortEth| / targetShortEth` to exactly 0.15. Verify the `drift_relative` condition is NOT triggered (equal is not greater than).
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_030
**Scenario Title:** BVA — drift_relative just above 0.15 (triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Set `|targetShortEth − actualShortEth| / targetShortEth` to 0.151. Verify `drift_relative` IS triggered and appears in `RebalanceReason[]`.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_031
**Scenario Title:** Decision table — drift_threshold + drift_relative both triggered, single hedge-sync with both reasons
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-023; confirmed code
**Test Type:** Functional
**Description:** Configure a bot where both `drift_threshold` and `drift_relative` conditions are simultaneously true. Process the light-check message. Verify: (1) `RebalanceReason[]` contains both reasons; (2) exactly one hedge-sync message is enqueued with `reasons:['drift_threshold','drift_relative']` (not two separate messages); (3) light-check does NOT set lifecycle_state.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_032
**Scenario Title:** Decision table — drift_threshold + range_boundary_near both triggered, single hedge-sync with both reasons
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9–10; SRS FR-EXBOT-023; confirmed code
**Test Type:** Functional
**Description:** Configure a bot where both `drift_threshold` and `range_boundary_near` are true simultaneously. Verify both reasons are included in a single hedge-sync message payload, not in separate enqueue calls.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_033
**Scenario Title:** Decision table — drift_threshold triggered + circuit open → no hedge-sync enqueued
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A1; SRS FR-EXBOT-014
**Test Type:** Functional
**Description:** Configure a bot with `drift_threshold` triggered AND `circuit_breakers.state='open'`. Process the light-check message. Verify no hedge-sync is enqueued (circuit open suppresses all hedge mutations regardless of reasons).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_034
**Scenario Title:** Decision table — drift_threshold triggered + hedge_stopped_cooldown → no hedge-sync enqueued
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §2 note; SRS states.md
**Test Type:** Functional
**Description:** Configure a bot with `lifecycle_state='hedge_stopped_cooldown'` and `drift_threshold` triggered. Verify no hedge-sync is enqueued — hedge_stopped_cooldown suppresses hedge-sync just like circuit open.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_035
**Scenario Title:** drift_threshold uses uniPoolPrice (sqrtPriceX96 from MarketDataDO), not hlMarkPrice
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-012; AC-LC-14
**Test Type:** Data/State
**Description:** Verify that `deltaErrorUsd` computation for `drift_threshold` uses `uniPoolPrice` derived from `sqrtPriceX96` (MarketDataDO) — not `hlMarkPrice` or `hlOraclePrice`. Inject a scenario where `uniPoolPrice` and a hypothetical `hlMarkPrice` differ significantly; verify the worker uses `uniPoolPrice` (3-way price split invariant v5.2.6 X-5).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_036
**Scenario Title:** lpEthAmount computed via TickMath + LiquidityAmounts (BigDecimal), not deprecated depositedToken formula
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 8; SRS FR-EXBOT-020; FR-EXBOT-021
**Test Type:** Data/State
**Description:** Verify that `lpEthAmount` is computed using Uniswap V3 TickMath + LiquidityAmounts (BigDecimal). Confirm the worker does NOT use `depositedToken − withdrawnToken + collectedFees` (forbidden by FR-EXBOT-020). Also verify `wethIndex` is read from `positions.weth_index` in D1, not hardcoded.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_037
**Scenario Title:** Multi-chain — Base chain bot uses correct wethIndex=0 for lpEthAmount
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 8; SRS FR-EXBOT-021; NFR-EXBOT-009
**Test Type:** Functional
**Description:** Configure a bot on the Base chain with `positions.weth_index=0` (WETH is token0). Verify `lpEthAmount` is computed using token0 as the ETH leg.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_038
**Scenario Title:** Multi-chain — Optimism chain bot uses correct wethIndex=1 for lpEthAmount
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 8; SRS FR-EXBOT-021; NFR-EXBOT-009
**Test Type:** Functional
**Description:** Configure a bot on the Optimism chain with `positions.weth_index=1` (WETH is token1). Verify `lpEthAmount` is computed using token1 as the ETH leg. The result must differ from the Base chain calculation only due to wethIndex — same liquidity, same ticks, different WETH leg assignment.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_039
**Scenario Title:** State transition — active → lp_rebalancing set DOWNSTREAM by hedge-sync handler after range_out enqueue; subsequent Scan Worker skips bot
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-015; AC-LC-10; confirmed code
**Test Type:** Data/State
**Description:** Process a light-check message that triggers `range_out`. Verify: (1) light-check enqueues hedge-sync with `reasons:['range_out']` and does NOT itself set `lifecycle_state='lp_rebalancing'`; (2) after the hedge-sync handler processes the message and sets `lifecycle_state='lp_rebalancing'`, the Scan Worker excludes the bot from the next light-check batch.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_040
**Scenario Title:** State transition — active → safe_mode (BOTH status AND lifecycle_state) on stop_replacing_overrun; all hedge mutations blocked
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033; FR-EXBOT-050; BR-EXBOT-007; confirmed code; AC-LC-12
**Test Type:** Data/State
**Description:** Trigger the stop_replacing_overrun condition (age > 60s). Verify: (1) `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` are both set in a single atomic UPDATE — assert both fields in the same check; (2) any subsequent hedge-sync attempt for this bot is blocked (SAFE_MODE blocks all hedge mutations per FR-EXBOT-050); (3) BR-EXBOT-007: SAFE_MODE is not terminal — a recovery path exists (auto-recovery or bot_safe_close).
**Test Focus:** State transition

---

### Scenario ID: TS_LC_041
**Scenario Title:** State transition — circuit closed → open after 3 consecutive failures, hedge-sync suppressed next cycle
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A1; SRS FR-EXBOT-040; states.md
**Test Type:** Data/State
**Description:** Simulate 3 consecutive hedge-sync failures for a bot within 24h, causing `circuit_breakers.state` to transition from `'closed'` to `'open'`. In the next light-check cycle, verify the circuit open state is detected and hedge-sync is suppressed, while stop monitoring continues.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_042
**Scenario Title:** State transition — circuit open → half_open after reset_at elapsed, probe allowed
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A2; SRS FR-EXBOT-040; states.md
**Test Type:** Data/State
**Description:** Set `circuit_breakers.state='open'` and `reset_at` to a timestamp in the past. When a light-check message is processed, verify `circuit_breakers.state` transitions to `'half_open'` and one probe hedge-sync is enqueued.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_043
**Scenario Title:** State transition — invalid: SAFE_MODE bot receives light-check, no HL mutation allowed
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS FR-EXBOT-050; BR-EXBOT-007
**Test Type:** Data/State
**Description:** Set a bot to `lifecycle_state='safe_mode'`. Deliver a light-check message. Verify: (1) no hedge-sync is enqueued; (2) no HL mutation is attempted; (3) stop monitoring (read-only path) may still run. SAFE_MODE blocks all hedge mutations — this is the representative invalid transition attempt for the safe_mode state.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_044
**Scenario Title:** Integration — hedge-sync message payload includes stateVersion matching D1 state_version at read time
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-027
**Test Type:** Integration
**Description:** Process a light-check message that triggers hedge-sync. Verify the enqueued hedge-sync message contains `{botId, reasons, stateVersion}` where `stateVersion` matches `bot_runtime_state.state_version` at the time of the light-check read (not stale). The hedge-sync worker will discard messages with mismatched stateVersion per SRS FR-EXBOT-027.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_045
**Scenario Title:** Integration — MarketDataDO provides sqrtPriceX96 and currentTick without HL API call
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 7; SRS FR-EXBOT-093; BR-EXBOT-003
**Test Type:** Integration
**Description:** Process a light-check message. Verify that `sqrtPriceX96` and `currentTick` are read from `MarketDataDO` (Cloudflare Durable Object cache) — not from any HL API call or direct on-chain RPC. Confirm HL API call count = 0 after the worker completes.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_046
**Scenario Title:** Integration — MarketDataDO snapshot stale > 5 minutes — worker fails fast and skips tick entirely (no refresh attempted)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 7; SRS FR-EXBOT-093; confirmed code; AC-LC-15
**Test Type:** Integration
**Description:** Simulate a MarketDataDO snapshot whose age > 5 minutes (stale threshold). Process a light-check message. Verify: (1) the worker throws fail-fast at step 7; (2) the tick is skipped completely — no triggers are evaluated; (3) no D1 mutation occurs; (4) `queue_idempotency.state` remains 'started' (cannot advance to 'succeeded'); (5) the worker does NOT attempt a forced cache refresh or wait for DO refresh.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_047
**Scenario Title:** Integration — range_out hedge-sync enqueued; lifecycle_state='lp_rebalancing' NOT set by light-check
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-015; confirmed code
**Test Type:** Integration
**Description:** Trigger `range_out` in a light-check pass. Verify: (1) the hedge-sync message is enqueued; (2) `bots.lifecycle_state` is NOT mutated by Light-Check Worker — it must remain as-is until the hedge-sync handler processes the message; (3) no state inconsistency window exists where lifecycle is changed but no queue message is present.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_048
**Scenario Title:** Idempotency/Concurrency — two light-check workers process same message_id concurrently, only one executes
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 5; SRS FR-EXBOT-011
**Test Type:** Integration
**Description:** Simulate concurrent delivery of the same light-check message to two Light-Check Worker instances simultaneously (message redelivery race). Verify: (1) the UNIQUE constraint on `queue_idempotency.message_id` ensures only one worker proceeds to fan-out logic; (2) the second worker exits on UNIQUE conflict without enqueuing duplicate downstream messages.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_049
**Scenario Title:** Idempotency/Concurrency — half_open probe claim race, only one probe hedge-sync enqueued across two workers
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §4 A2; SRS FR-EXBOT-040
**Test Type:** Integration
**Description:** Simulate two Light-Check Worker instances simultaneously attempting to claim `half_open_probe_used` for the same `circuit_breakers` row (state='half_open', probe_used=0). Verify that the atomic CAS write ensures exactly one probe hedge-sync is enqueued across both workers — the second write must fail the atomic claim.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_050
**Scenario Title:** End-to-end — Cron → bot-scan → Scan → light-check → hedge-sync full fan-out for one active bot
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 steps 1–13; SRS FR-EXBOT-012; BR-EXBOT-003
**Test Type:** End-to-End
**Description:** Run the complete light-check pipeline from Cron Worker trigger through to hedge-sync enqueue for one active bot with `drift_threshold` triggered. Verify the end-to-end sequence: (1) Cron enqueues bot-scan; (2) Scan Worker queries and enqueues light-check per bot; (3) `next_light_check_at` batch-updated; (4) Light-Check Worker processes, evaluates RebalanceReason[], enqueues hedge-sync; (5) idempotency row set to `succeeded`; (6) total HL API calls = 0 throughout.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_051
**Scenario Title:** Acceptance — AC-LC-01: zero HL calls invariant verified
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS BR-EXBOT-003; AC-LC-01; AC-EXBOT-005-1
**Test Type:** Acceptance
**Description:** Run a complete light-check cycle for an active bot with drift_threshold triggered. After the worker completes, verify that the total Hyperliquid API call count for the entire light-check path (Cron → Scan → Light-Check Worker) is exactly 0. Any non-zero count is a P0 violation of BR-EXBOT-003.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_052
**Scenario Title:** Acceptance — AC-LC-13: next_light_check_at jitter range and 1 stmt/shard constraint
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS FR-EXBOT-013; NFR-EXBOT-005; AC-LC-13
**Test Type:** Acceptance
**Description:** After a Scan Worker cycle, read `next_light_check_at` for all bots in the shard. Verify: (1) every value is in the range `[now + 4m15s, now + 5m45s]`; (2) the D1 write was issued as exactly 1 UPDATE statement per shard, not one per bot.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_053
**Scenario Title:** Acceptance — AC-LC-14: drift_threshold uses sqrtPriceX96 (uniPoolPrice), not hlMarkPrice
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS FR-EXBOT-012; AC-LC-14
**Test Type:** Acceptance
**Description:** Verify via observable worker behavior that `deltaErrorUsd` for drift_threshold is derived from `sqrtPriceX96` (MarketDataDO) only. Configure a test where `uniPoolPrice ≠ hlMarkPrice` and confirm the worker's decision matches the `uniPoolPrice`-based calculation.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_054
**Scenario Title:** Acceptance — AC-LC-09: half_open probe atomicity — half_open_probe_used set to 1 in single operation
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS FR-EXBOT-040; AC-LC-09
**Test Type:** Acceptance
**Description:** Set `circuit_breakers.state='half_open'` and `half_open_probe_used=0`. Process a light-check message. After the worker completes, verify: (1) exactly one hedge-sync probe message is in the queue; (2) `half_open_probe_used` is now 1 in D1; (3) the transition was performed atomically (no window where probe_used=0 and hedge-sync is not yet enqueued).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_055
**Scenario Title:** Error guessing — Scan Worker LIMIT 500 reached, remaining bots deferred to next Cron cycle
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 2; confirmed code; AC-LC-18
**Test Type:** Functional
**Description:** Set up a D1 shard with 501+ eligible bots using deterministic jitter (`hash(botId) ±45s`). Trigger one Scan Worker cycle. Verify: (1) exactly 500 bots are enqueued for light-check (LIMIT applied); (2) the 501st+ bots are not processed in this cycle; (3) their `next_light_check_at` values remain eligible for the next Cron tick (1 minute later, oldest first). No bot is permanently lost.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_056
**Scenario Title:** Error guessing — light-check message for non-existent botId, worker handles gracefully
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 6; SRS FR-EXBOT-011
**Test Type:** Functional
**Description:** Deliver a light-check message for a botId that does not exist in D1 (e.g., bot deleted between Scan Worker enqueue and Light-Check Worker processing). Verify the worker does not panic or throw an unhandled exception — it must handle the "bot not found" case gracefully (log and exit, or skip with idempotency finalized).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_057
**Scenario Title:** Error guessing — D1 read failure mid-worker, idempotency row left in started state
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 steps 5–6; SRS FR-EXBOT-011
**Test Type:** Functional
**Description:** Simulate a D1 read failure after `queue_idempotency` insert (state='started') but before bot state is read. Verify: (1) the worker does not update idempotency to 'succeeded'; (2) the message is redelivered by the queue; (3) on redelivery, the idempotency insert detects UNIQUE conflict (state='started' from prior attempt) and determines whether to retry or skip. This tests the handling of partial failures in the idempotency lifecycle.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_058
**Scenario Title:** Error guessing — stop_replacing_started_at IS NULL, overrun check does not fire
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Set `hedge_legs.stop_replacing_started_at = NULL`. Process a light-check message. Verify the overrun detection condition (`IS NOT NULL AND age > 60s`) is not satisfied — no `partial_repair(stop_replacing_overrun)` is enqueued and `lifecycle_state` remains unchanged.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_059
**Scenario Title:** Error guessing — cron tick overlap: new Cron fires while previous Scan Worker still running
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 1; SRS FR-EXBOT-010
**Test Type:** Integration
**Description:** Simulate a Cron Worker firing a second time while the first Scan Worker invocation is still in progress (e.g., slow D1 query). Verify that the bot-scan queue and light-check queue handle duplicate scan messages correctly — idempotency at the light-check level (UNIQUE on message_id) must prevent double-processing of any individual bot.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_060
**Scenario Title:** Error guessing — BigDecimal used throughout (no float arithmetic in drift or LP computations)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS NFR-EXBOT-008
**Test Type:** Data/State
**Description:** Verify that `lpEthAmount`, `deltaErrorUsd`, and `drift_threshold` comparison all use BigDecimal arithmetic — not JavaScript `number` floating point. Use a test case with known precision sensitivity (e.g., `deltaErrorUsd` near the $25 boundary) and confirm the comparison result matches the exact BigDecimal calculation, not a floating-point approximation.
**Test Focus:** Boundary

---

## New Scenarios (v2) — Previously Blocked, Now Resolved

---

### Scenario ID: TS_LC_061
**Scenario Title:** HlMarkDO stale > 120s — fallback to eth_price_usd, near-stop band widened from 2% to 4%, hedge-sync frozen
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 11; confirmed Tech Lead; AC-LC-16
**Test Type:** Functional
**Description:** Configure `HlMarkDO.markPriceUsd` with a last-updated timestamp > 120 seconds ago (stale). Process the light-check message for a bot where stop monitoring runs. Verify: (1) the worker falls back to `bot_runtime_state.eth_price_usd` as the mark price source; (2) the near-stop band is widened from 2% to 4% for stop trigger evaluation; (3) hedge-sync is frozen (not enqueued even if rebalance reasons are present due to HlMarkDO staleness); (4) `price-near-stop-audit` can still be enqueued if stop trigger condition is met with the fallback price.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_062
**Scenario Title:** HlMarkDO stale > 120s — stop trigger still fires with fallback price when markPrice >= stop_price
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 11; confirmed Tech Lead; AC-LC-16
**Test Type:** Functional
**Description:** Configure HlMarkDO stale > 120s (fallback to `eth_price_usd`) and set `eth_price_usd >= stop_price` (stop trigger met with fallback). Verify: (1) `stop_trigger_crossed_at` is set (write-once if NULL); (2) `price-near-stop-audit` is enqueued; (3) hedge-sync remains frozen due to HlMarkDO staleness. Stop monitoring is NOT disabled by HlMarkDO staleness — only the band widens and the price source changes.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_063
**Scenario Title:** BVA — HlMarkDO stale at exactly 120s boundary (not yet stale, normal band 2%)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 11; confirmed Tech Lead
**Test Type:** Functional
**Description:** Configure HlMarkDO.markPriceUsd with last-updated exactly 120 seconds ago. Verify: (1) the worker uses `HlMarkDO.markPriceUsd` as primary source (not fallback); (2) near-stop band remains at 2% (not widened); (3) hedge-sync is NOT frozen due to HlMarkDO staleness. The fallback threshold is strictly > 120s.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_064
**Scenario Title:** BVA — HlMarkDO stale at 121s (just past threshold — fallback active, band widened to 4%)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 11; confirmed Tech Lead
**Test Type:** Functional
**Description:** Configure HlMarkDO.markPriceUsd with last-updated exactly 121 seconds ago. Verify: (1) the worker falls back to `bot_runtime_state.eth_price_usd`; (2) near-stop band is widened to 4%; (3) hedge-sync is frozen.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_065
**Scenario Title:** BVA — funding_alert threshold at exactly -15% (not triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; confirmed code; AC-LC-17
**Test Type:** Functional
**Description:** Set `funding_rolling_metrics.fundingApr7dPct = -15.0` (exact threshold). Process the light-check message. Verify the `funding_alert` condition (`fundingApr7dPct < -15%`) is NOT triggered — equal to -15% does not satisfy strict less-than. `funding_alert` must NOT appear in `RebalanceReason[]`.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_066
**Scenario Title:** BVA — funding_alert threshold at -15.01% (just below threshold, triggered)
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; confirmed code; AC-LC-17
**Test Type:** Functional
**Description:** Set `funding_rolling_metrics.fundingApr7dPct = -15.01`. Verify the `funding_alert` condition IS triggered — `funding_alert` appears in `RebalanceReason[]` and hedge-sync is enqueued.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_067
**Scenario Title:** funding_alert primary source — reads fundingApr7dPct directly from funding_rolling_metrics table
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; confirmed code
**Test Type:** Functional
**Description:** Configure `funding_rolling_metrics.fundingApr7dPct = -20%` (well below -15% threshold). Verify: (1) the worker reads `fundingApr7dPct` directly from `funding_rolling_metrics` (primary path); (2) `funding_alert` is included in `RebalanceReason[]`; (3) hedge-sync is enqueued. HL API call count = 0 (no funding data fetched from HL).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_068
**Scenario Title:** funding_alert fallback — uses fundingRate × 8760 when fundingApr7dPct unavailable
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; confirmed code
**Test Type:** Functional
**Description:** Simulate the absence of `fundingApr7dPct` in `funding_rolling_metrics` (row missing or NULL). Configure `fundingRate` such that `fundingRate × 8760 < -0.15` (annualized per-hour rate triggers threshold). Verify: (1) the worker falls back to the annualization formula; (2) `funding_alert` fires and appears in `RebalanceReason[]`; (3) hedge-sync is enqueued.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_069
**Scenario Title:** lpValueUsd = 0 edge case — drift_threshold floor applies ($25), lpEthAmount = 0
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 9; confirmed code
**Test Type:** Functional
**Description:** Configure a bot with `lpEthAmount = 0` (position fully out of range, both tokens concentrated at boundary). Verify: (1) `lpValueUsd = max(0, 0 × currentPriceUsd) = $0`; (2) `drift_threshold = max($25, $0 × 3%) = $25` (floor applies); (3) subsequent drift_threshold evaluation uses $25 as the threshold — not $0 or negative.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_070
**Scenario Title:** Mixed reasons including range_out + drift_threshold — single hedge-sync with all reasons; lifecycle_state NOT set by light-check
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-023; confirmed code; AC-LC-10
**Test Type:** Functional
**Description:** Configure a bot simultaneously triggering `range_out` (tick outside range) AND `drift_threshold` (delta error above threshold) in the same light-check pass. Verify: (1) engine gathers both reasons into `decision.reason[]`; (2) exactly one hedge-sync message is enqueued with `reasons:['range_out','drift_threshold']`; (3) `bots.lifecycle_state` is NOT mutated by Light-Check Worker — the downstream hedge-sync handler is responsible for setting `lifecycle_state='lp_rebalancing'`.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_071
**Scenario Title:** SAFE_MODE atomic assertion — bots.status and bots.lifecycle_state updated in one D1 statement, not two sequential writes
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033; FR-EXBOT-050; confirmed code
**Test Type:** Data/State
**Description:** Trigger the stop_replacing_overrun condition. Inspect the D1 write sequence. Verify: (1) both `bots.status='safe_mode'` and `bots.lifecycle_state='safe_mode'` are set in a single atomic UPDATE (e.g., `UPDATE bots SET status='safe_mode', lifecycle_state='safe_mode' WHERE id=?`) — NOT in two separate sequential statements; (2) there is no observable window where only one of the two fields is 'safe_mode'; (3) the UPDATE completes before the `partial_repair` queue message is sent.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_072
**Scenario Title:** next_light_check_at update for lp_rebalancing bot — rescheduled at correct interval even when not enqueued
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 4; SRS FR-EXBOT-013; confirmed code
**Test Type:** Data/State
**Description:** Set a bot to `lifecycle_state='lp_rebalancing'` and `next_light_check_at <= now`. Run the Scan Worker. Verify: (1) the bot is NOT enqueued for light-check processing; (2) `next_light_check_at` IS updated to `now + 5min + jitter(±45s)` in the batch UPDATE — the bot does not fall behind schedule during the lp_rebalancing period and will resume light-check after recovery.
**Test Focus:** Data/State

---

### Scenario ID: TS_LC_073
**Scenario Title:** MarketDataDO unreachable (DO timeout) — fail-fast behavior identical to stale data
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** UC §3 step 7; SRS FR-EXBOT-093; confirmed code; AC-LC-15
**Test Type:** Integration
**Description:** Simulate `MarketDataDO` being unreachable (request timeout / DO down). Process a light-check message. Verify: (1) the worker throws fail-fast at step 7 (same behavior as stale data); (2) tick is skipped entirely — no triggers evaluated, no D1 mutation; (3) `queue_idempotency.state` remains 'started'; (4) HL API call count = 0.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_074
**Scenario Title:** Acceptance — AC-LC-12: stop_replacing_overrun SAFE_MODE — bots.status AND lifecycle_state both set, partial_repair enqueued after
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS FR-EXBOT-033; AC-LC-12; confirmed code
**Test Type:** Acceptance
**Description:** Trigger stop_replacing_overrun (age > 60s). Verify the full AC-LC-12 acceptance criteria: (1) `bots.status='safe_mode'` confirmed in D1; (2) `bots.lifecycle_state='safe_mode'` confirmed in the same D1 read; (3) `partial_repair` message with `reason='stop_replacing_overrun'` is present in the partial_repair queue; (4) ordering: D1 mutation precedes queue enqueue (verified by observing no state where queue message exists without both D1 fields set).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_075
**Scenario Title:** Acceptance — AC-LC-15 and AC-LC-16: MarketDataDO stale skips tick; HlMarkDO stale fallbacks but does not skip tick
**UC Reference:** UC-EXBOT-light-check
**Req-ID:** SRS FR-EXBOT-093; AC-LC-15; AC-LC-16; confirmed code; confirmed Tech Lead
**Test Type:** Acceptance
**Description:** Two acceptance verifications confirming different staleness behaviors: (1) MarketDataDO stale > 5 min → entire tick skipped, no evaluation, no D1 write; (2) HlMarkDO stale > 120s → tick NOT skipped — evaluation continues with fallback price + widened band. These two scenarios confirm that only MarketDataDO staleness is a hard skip condition; HlMarkDO staleness triggers degraded mode, not skip.
**Test Focus:** Alternative flow

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| range_boundary_near exact BVA — price values at nearestFraction = 0.9 boundary | BLOCKED: I-02 open — ví dụ trong docs mâu thuẫn với công thức (giá $3,020 và $3,380 được báo là trigger nhưng nằm trong range $3,000–$3,400). Không thể xây dựng test data chính xác cho BVA ranh giới cho đến khi BA clear. TS_LC_021 covers routing intent but not boundary values. | Resolve I-02 (BA to clarify formula vs. example), then add BVA scenarios for nearestFraction = 0.9 (not triggered) and nearestFraction = 0.89 (triggered). |
| Performance / throughput (10k bots / 5-min window) | NFR: LOAD — NFR-EXBOT-001 requires 33.3 bots/sec sustained throughput. Out of scope for functional test scenarios. | Defer to performance/load test suite. |
| Security testing | NFR: SECURITY — beyond functional auth scope. | Defer to security review. |
