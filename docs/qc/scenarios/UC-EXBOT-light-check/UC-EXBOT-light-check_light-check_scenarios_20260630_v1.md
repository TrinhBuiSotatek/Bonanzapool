# Test Scenarios — UC-EXBOT-light-check Execute Periodic Light-Check

> Source: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260630_v1.md
> Generated: 2026-06-30
> Author: QC Func Scenario Design Exbot Agent
> Version: v1
> Domain/Architecture: Cloudflare Workers (no UI) — Cron -> bot-scan queue -> Scan Worker -> light-check queue -> Light-Check Worker -> downstream queues (hedge-sync, price-near-stop-audit, partial_repair). D1 (SQLite sharded), MarketDataDO (Durable Object). Zero Hyperliquid API calls in this UC (HL weight = 0, BR-EXBOT-003).

---

## UC-EXBOT-light-check — Execute Periodic Light-Check

### Scenario ID: TS_LC_001
**Scenario Title:** Happy path — drift_threshold detected, hedge-sync enqueued, zero HL calls
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 steps 1–13; SRS FR-EXBOT-012; BR-EXBOT-003; AC-EXBOT-005-1; AC-LC-01
**Test Type:** Functional
**Description:** Given an active bot (status='active', lifecycle_state='active', next_light_check_at <= now) whose delta error exceeds drift_threshold — |targetShortEth - lastKnownShortEth| x uniPoolPrice > $25 — when the full pipeline executes (Cron -> Scan Worker -> Light-Check Worker), then the worker evaluates RebalanceReason[] using only D1 state and MarketDataDO (HL API call count = 0), enqueues a hedge-sync message containing {botId, reasons=['drift_threshold'], stateVersion}, sets queue_idempotency.state='succeeded', and updates next_light_check_at = now + 5min + jitter(+/-45s).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_002
**Scenario Title:** Happy path — no reason detected, no message enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 9–10; UC §5; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given an active bot whose RebalanceReason[] evaluates to empty (delta within threshold, range in bounds, margin ok, funding > -15% APR, time_fallback not reached, no stop trigger, no stop replace overrun), when the Light-Check Worker processes the bot, then no message is enqueued to any queue, queue_idempotency.state is set to 'succeeded', and next_light_check_at is updated. The system must not write to hedge_legs or bots.lifecycle_state.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_003
**Scenario Title:** Skip — bot with lifecycle_state='lp_rebalancing' not enqueued for light-check
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §2; SRS FR-EXBOT-012; AC-EXBOT-005-4; AC-LC-03
**Test Type:** Functional
**Description:** Given a bot with status='active' and lifecycle_state='lp_rebalancing' and next_light_check_at <= now, when the Scan Worker queries for eligible bots, then this bot must NOT be included in the light-check queue batch. No light-check message is enqueued and no RebalanceReason evaluation occurs for this bot.
**Test Focus:** Alternative flow — lp_rebalancing bot skipped at Scan Worker query

---

### Scenario ID: TS_LC_004
**Scenario Title:** Skip — bot with lifecycle_state='lp_closing' not enqueued for light-check
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §2; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given a bot with status='active' and lifecycle_state='lp_closing' and next_light_check_at <= now, when the Scan Worker queries for eligible bots, then this bot must NOT be included in the light-check queue batch.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_005
**Scenario Title:** Skip — bot with status='paused' not enqueued for light-check
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §2; SRS FR-EXBOT-003; AC-LC-04
**Test Type:** Functional
**Description:** Given a bot with status='paused' and next_light_check_at <= now, when the Scan Worker queries for eligible bots, then this bot must NOT appear in the light-check queue batch. The status='paused' filter must be applied at the Scan Worker query level (step 2).
**Test Focus:** Alternative flow


---

### Scenario ID: TS_LC_006
**Scenario Title:** hedge_stopped_cooldown — light-check runs normally, hedge-sync suppressed only
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §2 note; SRS states.md; AC-LC-05
**Test Type:** Functional
**Description:** Given lifecycle_state='hedge_stopped_cooldown' and drift reason present, when the Light-Check Worker processes the bot, then the bot is NOT skipped by Scan Worker, RebalanceReason[] is fully evaluated, hedge-sync is NOT enqueued (suppressed for this lifecycle state), and stop monitoring runs normally — if markPrice >= stop_price, price-near-stop-audit is enqueued.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_007
**Scenario Title:** Idempotency — duplicate message (state='started') — worker exits immediately, no mutation
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 5; SRS FR-EXBOT-011; AC-LC-02
**Test Type:** Functional
**Description:** Given message_id already exists in queue_idempotency with state='started', when the same message is redelivered to the Light-Check Worker, then the UNIQUE constraint conflict on message_id causes the worker to exit immediately without evaluating RebalanceReason[], without enqueuing any downstream message, and without mutating any D1 fields.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_008
**Scenario Title:** Idempotency — duplicate message (state='succeeded') — worker exits immediately
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 5; SRS FR-EXBOT-011
**Test Type:** Functional
**Description:** Given message_id already exists in queue_idempotency with state='succeeded', when the same message is redelivered, then the UNIQUE insert conflicts and the worker exits without reprocessing. The prior succeeded outcome is not modified.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_009
**Scenario Title:** Circuit breaker open — hedge-sync suppressed, stop monitoring still active
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §4 A1; SRS FR-EXBOT-014; BR-EXBOT-003; AC-EXBOT-005-3; AC-LC-08
**Test Type:** Functional
**Description:** Given circuit_breakers.state='open' and RebalanceReason[]=[drift_threshold], when the Light-Check Worker processes the bot, then no hedge-sync is enqueued. Stop monitoring still executes: if markPrice >= stop_price, price-near-stop-audit must be enqueued. The bot is not skipped — full light-check logic runs except hedge-sync fan-out.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_010
**Scenario Title:** Circuit breaker half_open, probe unclaimed — exactly one probe hedge-sync enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §4 A2; SRS FR-EXBOT-040; AC-EXBOT-008-2; AC-LC-09
**Test Type:** Data/State
**Description:** Given circuit_breakers.state='half_open' and half_open_probe_used=0 and drift reason present, when the Light-Check Worker processes the bot, then the worker atomically claims half_open_probe_used (0->1) and enqueues exactly one probe hedge-sync. A second concurrent worker finding half_open_probe_used=1 must suppress its own hedge-sync enqueue.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_011
**Scenario Title:** Circuit breaker half_open, probe already claimed — subsequent worker suppresses
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §4 A2; SRS FR-EXBOT-040
**Test Type:** Data/State
**Description:** Given circuit_breakers.state='half_open' and half_open_probe_used=1, when the Light-Check Worker processes the bot, then the worker behaves as if circuit is open: hedge-sync is suppressed and no second claim on half_open_probe_used is attempted.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_012
**Scenario Title:** Stop trigger first detection — stop_trigger_crossed_at set (write-once), price-near-stop-audit enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 11; SRS FR-EXBOT-032; BR-EXBOT-005; AC-LC-06
**Test Type:** Functional
**Description:** Given hedge_legs.stop_trigger_crossed_at IS NULL and markPrice >= hedge_legs.stop_price, when stop trigger detection runs, then stop_trigger_crossed_at is set to current timestamp (write-once guard: only if IS NULL, per BR-EXBOT-005), price-near-stop-audit is enqueued, and hedge-sync is NOT enqueued for this trigger event.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_013
**Scenario Title:** Stop trigger already set — stop_trigger_crossed_at not overwritten, price-near-stop-audit still enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §4 A3; SRS FR-EXBOT-032; BR-EXBOT-005; AC-LC-07; AC-EXBOT-005-2
**Test Type:** Functional
**Description:** Given hedge_legs.stop_trigger_crossed_at IS NOT NULL and markPrice >= stop_price, when stop trigger detection runs, then stop_trigger_crossed_at must NOT be overwritten (BR-EXBOT-005: write-once per stop event), price-near-stop-audit must still be enqueued, and hedge-sync must not be enqueued.
**Test Focus:** Alternative flow


---

### Scenario ID: TS_LC_014
**Scenario Title:** Stop trigger below threshold (BVA: markPrice < stop_price) — no write, no enqueue
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 11; SRS FR-EXBOT-032
**Test Type:** Functional
**Description:** Given hedge_legs.stop_trigger_crossed_at IS NULL and markPrice strictly less than stop_price, when stop trigger detection runs, then stop_trigger_crossed_at remains NULL and no price-near-stop-audit is enqueued.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_015
**Scenario Title:** Stop trigger at exact boundary (BVA: markPrice = stop_price) — condition is met
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 11; SRS FR-EXBOT-032
**Test Type:** Functional
**Description:** Given hedge_legs.stop_trigger_crossed_at IS NULL and markPrice exactly equals stop_price, when stop trigger detection runs, then markPrice >= stop_price is TRUE: stop_trigger_crossed_at is set and price-near-stop-audit is enqueued.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_016
**Scenario Title:** Stop replace overrun detected (age > 60s) — partial_repair enqueued, bot enters safe_mode
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033; AC-LC-12
**Test Type:** Data/State
**Description:** Given hedge_legs.stop_replacing_started_at IS NOT NULL and (now - stop_replacing_started_at) > 60 seconds, when the Light-Check Worker evaluates stop replace overrun at step 12, then partial_repair(reason='stop_replacing_overrun') is enqueued and bots.lifecycle_state is set to 'safe_mode'. Detection occurs within the 5-minute light-check cycle (primary path; deep-audit is only the backstop).
**Test Focus:** State transition

---

### Scenario ID: TS_LC_017
**Scenario Title:** Stop replace overrun at exactly 60s (BVA: limit) — condition is NOT yet met
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Given stop_replacing_started_at IS NOT NULL and age = exactly 60 seconds, when overrun detection runs (condition: age > 60s, strictly greater), then the condition is FALSE: no partial_repair is enqueued and lifecycle_state is not changed.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_018
**Scenario Title:** Stop replace overrun at 61s (BVA: Limit+1) — overrun triggered
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Given stop_replacing_started_at IS NOT NULL and age = 61 seconds, when overrun detection runs, then age > 60s is TRUE: partial_repair(reason='stop_replacing_overrun') is enqueued and lifecycle_state is set to 'safe_mode'.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_019
**Scenario Title:** Stop replacing not in progress (IS NULL) — overrun check produces no action
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Given hedge_legs.stop_replacing_started_at IS NULL, when overrun detection runs, then no partial_repair is enqueued and lifecycle_state is not modified. INV-STOP is not active for this bot.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_020
**Scenario Title:** range_out detected — lifecycle_state transitions to lp_rebalancing, fan-out enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-015; AC-LC-10
**Test Type:** Data/State
**Description:** Given range_out in RebalanceReason[] (currentTick outside [tickLower, tickUpper]), when the Light-Check Worker executes fan-out at step 10, then bots.lifecycle_state is set to 'lp_rebalancing', an lp_rebalancing message is enqueued, and a partial_repair message is enqueued. Subsequent Scan Worker passes must exclude this bot (lifecycle_state='lp_rebalancing' is filtered).
**Test Focus:** State transition

---

### Scenario ID: TS_LC_021
**Scenario Title:** range_boundary_near routes to hedge-sync, not price-near-stop-audit
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §4 A4; AC-LC-11
**Test Type:** Functional
**Description:** Given range_boundary_near in RebalanceReason[] and circuit_state != 'open', when the Light-Check Worker evaluates fan-out, then a hedge-sync message is enqueued (not price-near-stop-audit). range_boundary_near is a rebalance reason routed via hedge-sync — it is not a stop trigger.
**Test Focus:** Alternative flow


---

### Scenario ID: TS_LC_022
**Scenario Title:** drift_threshold formula uses uniPoolPrice from MarketDataDO, NOT hlMarkPrice or hlOraclePrice
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012 (3-way price split v5.2.6 X-5); AC-LC-14
**Test Type:** Functional
**Description:** Given a bot being evaluated for drift_threshold, when deltaErrorUsd is computed as |targetShortEth - lastKnownShortEth| x uniPoolPrice, then uniPoolPrice must be derived from sqrtPriceX96 read via MarketDataDO (the Uniswap V3 pool price) — NOT from any hlMarkPrice or hlOraclePrice source. Using a different price source violates the 3-way price split rule (v5.2.6 X-5).
**Test Focus:** Integration

---

### Scenario ID: TS_LC_023
**Scenario Title:** drift_threshold EP — delta below $25 flat floor, no reason generated
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012; AC-LC-14
**Test Type:** Functional
**Description:** Given a bot where |targetShortEth - lastKnownShortEth| x uniPoolPrice = $24.99 and lpValueUsd x 3% < $25 (so max floor applies), when drift_threshold is evaluated, then deltaErrorUsd ($24.99) is NOT > $25 and drift_threshold must NOT appear in RebalanceReason[].
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_024
**Scenario Title:** drift_threshold EP — delta exactly at $25 flat floor, no reason generated
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given deltaErrorUsd = exactly $25, when drift_threshold is evaluated (condition: deltaErrorUsd > $25, strictly greater), then $25 is NOT > $25 and drift_threshold must NOT appear in RebalanceReason[].
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_025
**Scenario Title:** drift_threshold EP — delta $25.01, above flat floor — reason generated
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given deltaErrorUsd = $25.01 and lpValueUsd x 3% < $25 (flat floor governs), when drift_threshold is evaluated, then $25.01 > $25 is TRUE and drift_threshold must appear in RebalanceReason[].
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_026
**Scenario Title:** drift_relative EP — ratio above 15% threshold — reason generated
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012 (drift_relative: |target - actual| / target > 0.15)
**Test Type:** Functional
**Description:** Given |targetShortEth - lastKnownShortEth| / targetShortEth > 0.15 (e.g. target=1.0 ETH, actual=0.84 ETH => ratio=0.16), when drift_relative is evaluated, then drift_relative must appear in RebalanceReason[].
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_027
**Scenario Title:** drift_relative EP — ratio exactly at 15% — reason NOT generated
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given |target - actual| / target = exactly 0.15, when drift_relative is evaluated (condition: > 0.15, strictly greater), then ratio is NOT > 0.15 and drift_relative must NOT appear in RebalanceReason[].
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_028
**Scenario Title:** time_fallback EP — 4 hours since last adjustment — reason generated
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012 (time_fallback: 4h since last adjustment)
**Test Type:** Functional
**Description:** Given a bot where the elapsed time since last HL reconcile exceeds 4 hours, when time_fallback is evaluated, then time_fallback must appear in RebalanceReason[] and hedge-sync must be enqueued (circuit permitting).
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_029
**Scenario Title:** margin_warning EP — read from D1, not fetched from HL
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-012; FR-EXBOT-060
**Test Type:** Functional
**Description:** Given hedge_legs.margin_status='warning' stored in D1, when margin_warning is evaluated in light-check, then margin_warning must appear in RebalanceReason[] based on the D1 value — no HL API call is made to fetch current margin (HL weight = 0 invariant). margin_status='ok' must NOT produce margin_warning in RebalanceReason[].
**Test Focus:** Integration


---

### Scenario ID: TS_LC_030
**Scenario Title:** lpEthAmount computed via TickMath+LiquidityAmounts, not balance subtraction
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-020; FR-EXBOT-021
**Test Type:** Functional
**Description:** Given a position with known liquidity, tickLower, tickUpper, sqrtPriceX96, currentTick, and wethIndex, when lpEthAmount is computed at step 8, then the result must use the Uniswap V3 AMM formula (TickMath + LiquidityAmounts) — NOT the deprecated depositedToken - withdrawnToken + collectedFees formula (forbidden by FR-EXBOT-020). Computation must use BigDecimal arithmetic (no float/Number).
**Test Focus:** Integration

---

### Scenario ID: TS_LC_031
**Scenario Title:** wethIndex read from D1 positions.weth_index — not hardcoded
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-021; NFR-EXBOT-009
**Test Type:** Functional
**Description:** Given bots on two different chains (Base chainId=8453 and Optimism chainId=10) with different wethIndex values stored in positions.weth_index, when lpEthAmount is computed for each bot, then wethIndex must be read from D1 for each bot's chain context — hardcoding wethIndex to a fixed value must fail the test for the chain where that value is incorrect.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_032
**Scenario Title:** next_light_check_at jitter — batch update 1 statement per shard, result in [now+4m15s, now+5m45s]
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 4; SRS FR-EXBOT-013; NFR-EXBOT-005; AC-LC-13
**Test Type:** Functional
**Description:** Given a Scan Worker pass processing N bots across S shards, when next_light_check_at is batch-updated, then each shard receives exactly 1 UPDATE statement (never per-bot), and next_light_check_at for each eligible bot falls in the range [now + 4m15s, now + 5m45s] (5min +/- 45s jitter). No unconditional per-bot UPDATE is allowed (NFR-EXBOT-005).
**Test Focus:** Integration

---

### Scenario ID: TS_LC_033
**Scenario Title:** next_light_check_at not yet due — bot not included in Scan Worker query (BVA: t < schedule)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 2; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given a bot with status='active' and next_light_check_at = now + 1 second (not yet due), when the Scan Worker runs its query (WHERE next_light_check_at <= now), then this bot must NOT be included in the eligible set and no light-check message is enqueued for it.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_034
**Scenario Title:** next_light_check_at exactly now — bot IS included (BVA: limit)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 2; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given a bot with status='active' and next_light_check_at = exactly now, when the Scan Worker runs (WHERE next_light_check_at <= now), then this bot IS included in the eligible set and a light-check message is enqueued.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_035
**Scenario Title:** MarketDataDO — data read successfully, no RPC call made
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 7; SRS FR-EXBOT-093; BR-EXBOT-003
**Test Type:** Integration
**Description:** Given MarketDataDO has valid sqrtPriceX96 and currentTick data, when the Light-Check Worker reads MarketDataDO at step 7, then sqrtPriceX96 and currentTick are successfully read from the DO cache without any blockchain RPC call. All light-check workers in the CF region share the same DO instance — verifying that multiple concurrent workers read the same DO without conflict.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_036
**Scenario Title:** Multiple reasons in one pass — hedge-sync carries full reasons list with stateVersion
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Given RebalanceReason[]=[drift_threshold, margin_warning, time_fallback] and circuit_state='closed', when fan-out runs at step 10, then exactly one hedge-sync message is enqueued containing {botId, reasons=['drift_threshold','margin_warning','time_fallback'], stateVersion}. Only one hedge-sync per light-check pass — not one per reason.
**Test Focus:** Integration


---

### Scenario ID: TS_LC_037
**Scenario Title:** hedge-sync stateVersion mismatch — downstream hedge-sync worker discards stale message
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-027; §F.4 integration note
**Test Type:** Integration
**Description:** Given a hedge-sync message enqueued by light-check containing stateVersion=N, when the bot's D1 state_version has advanced to N+1 by the time hedge-sync worker processes the message, then the hedge-sync worker must detect the version mismatch and discard the message without applying any hedge mutation. Light-check is responsible for including the correct stateVersion at enqueue time.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_038
**Scenario Title:** range_out + other reasons in same pass — mixed fan-out behavior (I-05 flagged)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-015; Issue I-05
**Test Type:** Functional
**Description:** Given RebalanceReason[]=[range_out, drift_threshold] in the same light-check pass, when fan-out logic runs, then the expected behavior for the non-range_out reasons (drift_threshold) alongside range_out is ambiguous per I-05. This scenario validates the system's actual behavior: whether hedge-sync is also enqueued alongside lp_rebalancing fan-out, or only lp_rebalancing path runs. Expected result: per UC §3 step 10 literal reading, lp_rebalancing + partial_repair are enqueued; other reasons AND circuit != open -> hedge-sync is also enqueued. Confirm with BA before finalizing expected result.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_039
**Scenario Title:** lifecycle_state transitions to lp_rebalancing — future Scan Worker passes skip the bot
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 10; SRS FR-EXBOT-015; §F.4 data consistency
**Test Type:** Data/State
**Description:** Given range_out triggers lp_rebalancing fan-out and bots.lifecycle_state is set to 'lp_rebalancing', when the next Scan Worker cycle runs, then the bot must be excluded from the eligible query (lifecycle_state IN filter at step 2). The D1 write of lifecycle_state='lp_rebalancing' must be visible to the next Scan Worker query.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_040
**Scenario Title:** safe_mode entry from stop overrun — all hedge mutations blocked (FR-EXBOT-050)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 12; SRS FR-EXBOT-050; §F.4 data consistency
**Test Type:** Data/State
**Description:** Given step 12 sets lifecycle_state='safe_mode' due to stop replace overrun, when subsequent operations attempt hedge-sync or LP rebalance for this bot, then all hedge mutation operations must be blocked (FR-EXBOT-050). Only non-mutating operations are allowed: read state, alert user/admin, deep-audit when HL recovers, and light-check (non-HL path).
**Test Focus:** State transition

---

### Scenario ID: TS_LC_041
**Scenario Title:** queue_idempotency finalize — state updated to 'succeeded' at end of successful light-check
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 step 13; SRS FR-EXBOT-011
**Test Type:** Functional
**Description:** Given a successful light-check pass that completes all fan-out logic, when finalize runs at step 13, then the queue_idempotency row for this message_id must have its state updated from 'started' to 'succeeded'. On the next redelivery of the same message, the 'succeeded' state causes an immediate skip.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_042
**Scenario Title:** Acceptance — AC-EXBOT-005-1 full verification (drift detected, hedge-sync, HL=0)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** AC-EXBOT-005-1; US-EXBOT-005
**Test Type:** Acceptance
**Description:** Given an active bot where |targetShortEth - lastKnownShortEth| x uniPoolPrice > $25, when the light-check worker processes this bot end-to-end, then: (a) RebalanceReason[] is evaluated using only D1 + MarketDataDO (HL API call count = 0), (b) hedge-sync is enqueued with reasons=['drift_threshold'] and stateVersion, (c) next_light_check_at is updated to now + 5min + jitter(+/-45s). All three conditions must hold simultaneously.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_043
**Scenario Title:** Acceptance — AC-EXBOT-005-2 stop trigger routing (no hedge-sync for trigger)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** AC-EXBOT-005-2; US-EXBOT-005
**Test Type:** Acceptance
**Description:** Given an active bot where markPriceUsd >= hedge_legs.stop_price, when the light-check worker processes this bot, then: (a) hedge_legs.stop_trigger_crossed_at is set only if currently NULL, (b) price-near-stop-audit is enqueued, (c) hedge-sync is NOT enqueued for this trigger event. All three conditions must hold simultaneously.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_044
**Scenario Title:** Acceptance — AC-EXBOT-005-3 circuit open, stop monitoring still runs
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** AC-EXBOT-005-3; US-EXBOT-005
**Test Type:** Acceptance
**Description:** Given circuit_breakers.state='open', when the light-check worker processes the bot, then: (a) hedge-sync is NOT enqueued, (b) price-near-stop-audit IS enqueued if stop criteria met, (c) the bot continues normally (not skipped). All three must hold simultaneously.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_045
**Scenario Title:** Acceptance — AC-EXBOT-005-4 lp_rebalancing or lp_closing bot skipped entirely
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** AC-EXBOT-005-4; US-EXBOT-005
**Test Type:** Acceptance
**Description:** Given lifecycle_state='lp_rebalancing' (or 'lp_closing'), when the light-check Scan Worker encounters this bot, then the bot is excluded from the light-check queue and no evaluation or enqueuing occurs. The Scan Worker moves to the next bot without error.
**Test Focus:** Alternative flow


---

### Scenario ID: TS_LC_046
**Scenario Title:** State machine — bot in 'active' lifecycle, all light-check paths available
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS states.md; SRS FR-EXBOT-012
**Test Type:** Data/State
**Description:** Given bots.lifecycle_state='active', when the Light-Check Worker processes the bot, then all light-check paths are available: drift evaluation, stop trigger detection, overrun detection, and any fan-out can occur. This is the baseline valid state for full light-check execution.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_047
**Scenario Title:** State machine — invalid transition attempt: light-check mutation while lifecycle_state='safe_mode'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-050; states.md
**Test Type:** Data/State
**Description:** Given bots.lifecycle_state='safe_mode', when the Light-Check Worker processes the bot, then hedge mutation (hedge-sync enqueue, lp_rebalancing transition) must be blocked. The light-check worker may still run the non-HL evaluation path and stop monitoring, but must not attempt any hedge mutation. Attempting to enqueue hedge-sync from safe_mode is an invalid operation.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_048
**Scenario Title:** SAFE_MODE is not terminal — bot in safe_mode can be recovered (NFR-EXBOT-010)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-050; NFR-EXBOT-010
**Test Type:** Data/State
**Description:** Given a bot whose lifecycle_state was set to 'safe_mode' by stop overrun detection, when the recovery path executes (via partial_repair worker and subsequent partial_repair), then the bot's lifecycle_state must be restorable from 'safe_mode' to a valid operational state. SAFE_MODE must not be a terminal state — a recovery path must exist (NFR-EXBOT-010).
**Test Focus:** State transition

---

### Scenario ID: TS_LC_049
**Scenario Title:** stop_trigger_crossed_at set by light-check — deep-audit backstop kicks in if stuck >30 min
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** SRS FR-EXBOT-033; §F.4 stop_trigger_crossed_at dependency
**Test Type:** Integration
**Description:** Given stop_trigger_crossed_at is set by light-check (primary path) and the triggered stop event is not resolved within 30 minutes, when the deep-audit cron job runs (backstop), then deep-audit must detect stop_trigger_crossed_at stuck > 30 min and escalate to SAFE_MODE. Light-check is responsible for the initial write; deep-audit handles overrun detection if light-check misses subsequent evaluation.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_050
**Scenario Title:** E2E — full scan cycle: Cron -> Scan Worker -> Light-Check Worker -> hedge-sync downstream
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC §3 steps 1–13; SRS FR-EXBOT-012; flows.md F-01
**Test Type:** End-to-End
**Description:** Given an active bot eligible for light-check with drift_threshold reason, when the full fan-out pipeline executes from Cron Worker trigger through Scan Worker (query, enqueue, batch-update) through Light-Check Worker (idempotency, D1 read, MarketDataDO read, lpEthAmount compute, reason evaluate, hedge-sync enqueue, finalize), then each stage completes in sequence, the hedge-sync worker receives the message with correct {botId, reasons, stateVersion}, and the entire flow produces zero HL API calls. D1 consistency is verified: queue_idempotency.state='succeeded' and next_light_check_at is in the expected jitter window.
**Test Focus:** Happy path

---

## Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| range_boundary_near exact formula and test data | BLOCKED: OQ-EXBOT-010 open — formula is tick-based vs price-based is unconfirmed. Cannot compute boundary test values. | Resolve via qc-qna (I-02) before designing test cases for this scenario. |
| lpValueUsd formula and drift_threshold percentage floor | BLOCKED: OQ-EXBOT-011 open — (lpEthAmount x uniPoolPrice) + lpUsdcAmount formula unconfirmed by zen. Cannot compute exact drift_threshold percentage branch. | Resolve via qc-qna (I-03) before designing test cases for percentage floor branch. |
| funding_alert (7d APR aggregation) | BLOCKED: OQ-EXBOT-012 open — annualization formula for 7d funding APR is unconfirmed. Cannot compute threshold -15% from raw funding_daily_metrics. | Resolve via qc-qna (I-04) before designing test cases for funding_alert reason. |
| hlMarkPrice staleness policy for stop trigger | BLOCKED: OQ-EXBOT-017 open — source of hlMarkPrice under HL weight=0 constraint is unconfirmed. Staleness policy undefined. Test data for stale-vs-fresh price scenarios cannot be designed. | Resolve via qc-qna (I-01) before expanding TS_LC_012 and TS_LC_013 into atomic test cases. |
| next_light_check_at update for skipped bots (lp_rebalancing) | OPEN: I-08 — unclear if next_light_check_at is updated for bots that Scan Worker skips. Post-recovery scheduling behavior depends on this. | Resolve via qc-qna (I-08) before designing post-recovery scheduling test. |
| SAFE_MODE: which actor updates bots.status vs bots.lifecycle_state | OPEN: I-07 — whether Light-Check Worker or partial_repair worker updates bots.status='safe_mode' is ambiguous. | Resolve via qc-qna (I-07) before finalizing TS_LC_016 expected result for status field. |
| lp_rebalancing queue destination and payload | OPEN: I-06 — UC implies 2 separate messages (lp_rebalancing queue + partial_repair queue) but SRS implies partial_repair queue for both. | Resolve via qc-qna (I-06) before designing TS_LC_020 into atomic test cases. |
| Scan Worker >500 bots per shard handling | OPEN: I-09 — behavior when eligible bots exceed LIMIT 500 per shard is undefined. | Resolve via qc-qna (I-09) before designing volume/overflow test cases. |
| Performance / load: 10,000 bots at 33.3 bots/sec | OUT OF SCOPE: NFR — load/performance testing. | Defer to performance test team. |
| Security beyond functional auth (key management, KMS) | OUT OF SCOPE: ExBot uses AWS KMS for signing; security testing of KMS integration is out of scope for functional scenario design. | Defer to security review. |

