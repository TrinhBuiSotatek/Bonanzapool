# Test Scenarios — UC-EXBOT-light-check Execute Periodic Light-Check

> Source: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260722_v5.md
> Generated: 2026-07-22
> Domain/Architecture: AWS Lambda (Scan Worker + Light-Check Worker) + SQS queues + Aurora PostgreSQL + ElastiCache Redis (Pool Slot0 Cache + HL Mark Price Cache). Zero Hyperliquid API calls in light-check (BR-EXBOT-003).
> Changes from v4: (1) lp_value_usd formula updated to `(lpEthAmount × uniPoolPrice) + lpUsdcAmount` per OQ-EXBOT-11 zen confirmed; (2) Pool Slot0 Cache stale threshold updated from >5 min to >120s per OQ-EXBOT-09 zen confirmed (60s refresh interval); (3) funding formula confirmed per OQ-EXBOT-12; (4) added TS_LC_053 for drift_relative trigger (v5-I-01 gap).

## UC-EXBOT-light-check — Execute Periodic Light-Check

---

### Scenario ID: TS_LC_001
**Scenario Title:** Happy path — full scan-to-light-check pipeline, bot needs no rebalance
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 1–13; FR-EXBOT-010, FR-EXBOT-012, FR-EXBOT-013
**Test Type:** Functional
**Description:** Trigger an EventBridge Scheduler tick with one active bot whose drift, range, margin, and stop conditions are all within safe bounds; the entire pipeline (Scan Worker query → enqueue light-check → Light-Check Worker evaluation → idempotency finalize) must complete with zero Hyperliquid API calls, zero queue messages produced, and next_light_check_at advanced by 5 min ± 45 s.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_002
**Scenario Title:** Happy path — drift_threshold fires, hedge-sync enqueued with correct reasons
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9–10; FR-EXBOT-011; AC-LC-07
**Test Type:** Functional
**Description:** Process a light-check for a bot whose `|targetShortEth - lastKnownShortEth| × uniPoolPrice` exceeds drift_threshold (`max($25, lpValueUsd × 3%)`) where `lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount` (principal only, exclude tokensOwed; price = Uniswap pool slot0). The system must enqueue exactly one hedge-sync message with reasons=['drift_threshold'] and the current stateVersion. Zero HL API calls.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_003
**Scenario Title:** Happy path — range_out fires, routed to hedge-sync NOT to a separate lp_rebalancing queue
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; FR-EXBOT-011, FR-EXBOT-015; AC-LC-08
**Test Type:** Functional
**Description:** Process a light-check for a bot with rangeState != 'in' (currentTick outside [tickLower, tickUpper]); the system must include 'range_out' in decision.reason[] and enqueue one hedge-sync message. The Light-Check Worker must NOT set lifecycle_state='lp_rebalancing' and must NOT enqueue any separate lp_rebalancing message — lifecycle transition is the downstream hedge-sync handler's responsibility.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_004
**Scenario Title:** Happy path — multiple reasons fire simultaneously, single hedge-sync with all reasons
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9–10; FR-EXBOT-011; AC-LC-07
**Test Type:** Functional
**Description:** Process a light-check where both drift_threshold and range_boundary_near conditions are true simultaneously; the strategy engine must aggregate all fired triggers into a single decision.reason[] array and enqueue exactly one hedge-sync message (not two separate messages).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_005
**Scenario Title:** range_boundary_near — fires at boundary (nearestFraction = 0.9 exactly)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011; AC-LC-07
**Test Type:** Functional
**Description:** Process a bot where `min(distToLower, distToUpper) / halfRange` equals exactly 0.9 (rangeBoundaryFraction default); the range_boundary_near trigger must fire and be included in decision.reason[]. This verifies the boundary condition of the price-based USD formula.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_006
**Scenario Title:** range_boundary_near — does NOT fire just above boundary (nearestFraction = 0.91)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011
**Test Type:** Functional
**Description:** Process a bot where `min(distToLower, distToUpper) / halfRange` equals 0.91 (just above the 0.9 threshold); range_boundary_near must NOT fire. Verifies the boundary does not bleed into the valid zone.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_007
**Scenario Title:** drift_threshold — fires at exact flat floor ($25) when lpValueUsd × 3% < $25
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011; AC-LC-07
**Test Type:** Functional
**Description:** Process a bot where `lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount` is small enough that `lpValueUsd × 3% < $25` (so the flat $25 floor applies) and the computed deltaErrorUsd equals exactly $25; drift_threshold must fire. Verifies `max($25, lpValueUsd × 3%)` selects the flat floor at the exact boundary value.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_008
**Scenario Title:** drift_threshold — fires at percentage threshold when lpValueUsd × 3% > $25
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011; AC-LC-07
**Test Type:** Functional
**Description:** Process a bot where `lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount` is large enough that `lpValueUsd × 3% > $25` (e.g., lpValueUsd = $1000 → threshold = $30) and deltaErrorUsd equals exactly $30; drift_threshold must fire. Verifies the percentage branch of the `max($25, lpValueUsd × 3%)` formula.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_009
**Scenario Title:** drift_threshold — lpEthAmount = 0 edge case (position fully out of range)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011
**Test Type:** Functional
**Description:** Process a bot where lpEthAmount computes to 0 (position fully out of range, no ETH component); `lpValueUsd = (0 × uniPoolPrice) + lpUsdcAmount = lpUsdcAmount`. If lpUsdcAmount is also near 0, drift_threshold falls back to the $25 flat floor. System must not produce a negative threshold or divide-by-zero error, and must evaluate correctly using the two-component formula.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_010
**Scenario Title:** margin_warning trigger — fires when margin_status = 'warning'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011
**Test Type:** Functional
**Description:** Process a bot with `hedge_legs.margin_status = 'warning'` in Aurora PostgreSQL; the margin_warning reason must be included in decision.reason[] and hedge-sync must be enqueued. Margin status is read from Aurora PostgreSQL only — no HL API fetch occurs.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_011
**Scenario Title:** time_fallback trigger — fires when 4h have elapsed since last adjustment with no other reason
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011
**Test Type:** Functional
**Description:** Process a bot where no drift, range, margin, or funding condition is met, but the time_fallback threshold of 4 hours since the last adjustment is reached; the system must enqueue hedge-sync with reasons=['time_fallback']. Verifies the periodic forced reconcile fires even when all other triggers are silent.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_012
**Scenario Title:** stop trigger detected — markPrice >= stop_price, stop_trigger_crossed_at set and price-near-stop-audit enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; FR-EXBOT-031; AC-LC-12
**Test Type:** Functional
**Description:** Process a bot where HL Mark Price Cache markPriceUsd >= hedge_legs.stop_price and stop_trigger_crossed_at IS NULL; the system must atomically set stop_trigger_crossed_at = now (write-once) and enqueue price-near-stop-audit. Must NOT suppress this action regardless of circuit breaker state. Zero HL API calls.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_013
**Scenario Title:** stop trigger write-once guard — stop_trigger_crossed_at already set, must not overwrite
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A4; BR-EXBOT-005; AC-LC-13
**Test Type:** Functional
**Description:** Process a bot where markPrice >= stop_price but stop_trigger_crossed_at IS NOT NULL (already set by a prior tick); the system must NOT overwrite the existing timestamp, but must still enqueue price-near-stop-audit. BR-EXBOT-005: "stop_trigger_crossed_at is write-once — MUST NOT be overwritten once set."
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_014
**Scenario Title:** SAFE_MODE entry — stop_replacing_started_at overrun > 60s, atomic UPDATE + partial_repair
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; FR-EXBOT-033; AC-LC-15
**Test Type:** Functional
**Description:** Process a bot where stop_replacing_started_at IS NOT NULL and (now − stop_replacing_started_at) > 60s; the Light-Check Worker must execute a single atomic SQL UPDATE setting both `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'`, then enqueue `partial_repair(reason='stop_replacing_overrun')`. The UPDATE must commit to Aurora PostgreSQL before the partial_repair SQS message is enqueued.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_015
**Scenario Title:** SAFE_MODE entry — boundary: overrun exactly at 60s must NOT trigger, 61s must trigger
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; FR-EXBOT-033
**Test Type:** Functional
**Description:** Verify the 60-second overrun threshold boundary: a bot with stop_replacing_started_at set to exactly 60s ago must NOT enter SAFE_MODE; a bot at 61s must trigger the atomic UPDATE and partial_repair enqueue.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_016
**Scenario Title:** Circuit breaker open — hedge-sync suppressed, stop monitoring continues
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A2; FR-EXBOT-011, FR-EXBOT-040; AC-LC-10
**Test Type:** Functional
**Description:** Process a bot with circuit_breakers.state='open' and a rebalance condition (drift_threshold) active; the system must NOT enqueue hedge-sync, but must still evaluate stop trigger (step 11) and SAFE_MODE check (step 12). If markPrice >= stop_price, price-near-stop-audit must still be enqueued.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_017
**Scenario Title:** Circuit breaker half_open — exactly one probe hedge-sync enqueued via atomic claim
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A3; FR-EXBOT-040; AC-LC-11
**Test Type:** Functional
**Description:** Process a bot with circuit_breakers.state='half_open' and a rebalance condition active; the system must atomically claim half_open_probe_used (0→1) and enqueue exactly one probe hedge-sync. No additional hedge-sync messages for the same bot in the same tick.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_018
**Scenario Title:** Pool Slot0 Cache stale (>120s) — tick skipped entirely, no mutation
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A1; FR-EXBOT-093; AC-LC-06
**Test Type:** Functional
**Description:** Process a light-check where the Pool Slot0 Cache (ElastiCache Redis) snapshot age exceeds 120 seconds (2× refresh interval of 60s, zen confirmed per OQ-EXBOT-09); the Light-Check Worker must throw at step 7, skip all trigger evaluation, and produce zero mutations to Aurora PostgreSQL. queue_idempotency.state must remain 'started' (not finalized to 'succeeded').
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_019
**Scenario Title:** Pool Slot0 Cache unreachable — tick skipped entirely, same as stale behavior
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A1; FR-EXBOT-093
**Test Type:** Functional
**Description:** Process a light-check where the Pool Slot0 Cache (ElastiCache Redis) is unreachable (connection error or timeout); the Light-Check Worker must fail-fast at step 7 with the same skip behavior as stale — no trigger evaluation, zero Aurora PostgreSQL mutations.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_020
**Scenario Title:** Pool Slot0 Cache stale boundary — exactly 120s old must trigger skip, 119s must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 7; FR-EXBOT-093
**Test Type:** Functional
**Description:** Verify the 120-second stale threshold (2× 60s refresh interval, OQ-EXBOT-09 closed): a cache snapshot aged exactly 120s must trigger the fail-fast skip; a snapshot aged 119s must be accepted and processing continues normally. This replaces the prior 5-minute threshold.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_021
**Scenario Title:** HL Mark Price Cache stale (>120s) — fallback to eth_price_usd, near-stop band widened to 4%
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; AC-LC-14
**Test Type:** Functional
**Description:** Process a light-check where HL Mark Price Cache updatedAt > 120s ago; the system must log `hl_mark_price_stale` audit event, fall back to `bot_runtime_state.eth_price_usd` for stop trigger evaluation, widen the near-stop band from 2% to 4%, and freeze routine hedge-sync after the stop check for this tick only.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_022
**Scenario Title:** HL Mark Price Cache stale boundary — exactly 120s must trigger stale path, 119s must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11
**Test Type:** Functional
**Description:** Verify the 120-second stale threshold for HL Mark Price Cache: a cache aged exactly 120s must trigger the fallback/band-widening path; a cache aged 119s must use the primary markPriceUsd without fallback.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_023
**Scenario Title:** Bot with lifecycle_state='lp_rebalancing' — skipped by Light-Check Worker, still rescheduled
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2, §3 step 4; FR-EXBOT-011; AC-LC-02
**Test Type:** Functional
**Description:** Process a Scan Worker tick where one bot has lifecycle_state='lp_rebalancing'; Scan Worker must still include that bot in the next_light_check_at batch update (step 4), but Light-Check Worker must skip all rebalance evaluation and enqueuing for that bot (no hedge-sync, no price-near-stop-audit).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_024
**Scenario Title:** Bot with lifecycle_state='lp_closing' — skipped by Light-Check Worker, still rescheduled
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2; FR-EXBOT-011
**Test Type:** Functional
**Description:** Process a light-check for a bot with lifecycle_state='lp_closing'; the Light-Check Worker must skip all evaluation, consistent with the lp_rebalancing behavior. next_light_check_at must still be advanced by Scan Worker at step 4.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_025
**Scenario Title:** Bot with lifecycle_state='hedge_stopped_cooldown' — light-check runs, hedge-sync suppressed
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2 (note); FR-EXBOT-003
**Test Type:** Functional
**Description:** Process a light-check for a bot with lifecycle_state='hedge_stopped_cooldown'; the UC explicitly states these bots are NOT skipped — light-check evaluation runs, but hedge-sync is suppressed downstream. Stop monitoring (step 11) must still execute and price-near-stop-audit must still be enqueued if stop trigger is crossed.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_026
**Scenario Title:** Scan Worker LIMIT 500 — bots beyond 500 eligible deferred to next tick, oldest processed first
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 2; FR-EXBOT-012; AC-LC-16
**Test Type:** Functional
**Description:** With a shard containing 600 bots due for light-check simultaneously, Scan Worker must query `ORDER BY next_light_check_at LIMIT 500`, process the 500 oldest bots first, and defer the remaining 100 to the next EventBridge tick (1 min later). No bots are dropped permanently.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_027
**Scenario Title:** next_light_check_at batch update — single SQL statement covers all eligible bots including skipped
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 4; FR-EXBOT-012; AC-LC-16
**Test Type:** Functional
**Description:** After Scan Worker processes a batch of bots (including some with lifecycle_state='lp_rebalancing'), verify that next_light_check_at is updated for ALL eligible bots in a single UPDATE statement per shard — not per-bot individual writes. Bots that Light-Check Worker later skips must still have their next_light_check_at advanced correctly.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_028
**Scenario Title:** HL API call count = 0 across entire light-check pipeline
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §5; BR-EXBOT-003; AC-LC-01
**Test Type:** Acceptance
**Description:** Execute a full light-check cycle for 10 bots covering all trigger types (drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback, stop trigger); verify that zero Hyperliquid API calls are made by any component in the pipeline. Any HL fetch detected is an architectural violation of BR-EXBOT-003 ("HL API call count MUST be 0 during light-check execution").
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_029
**Scenario Title:** jitter distribution — next_light_check_at set within now+5min ± 45s, deterministic per botId
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 4; FR-EXBOT-012; AC-LC-16
**Test Type:** Functional
**Description:** After a Scan Worker batch update, verify that each bot's new next_light_check_at falls within the range [now+4m15s, now+5m45s]. Jitter must be deterministic per botId (hash-based): the same botId must produce the same jitter offset on repeated calls with the same base timestamp.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_030
**Scenario Title:** Idempotency — duplicate light-check message for same bot in same tick skipped
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; FR-EXBOT-011; AC-LC-05
**Test Type:** Data/State
**Description:** Deliver two light-check SQS messages with the same message_id for the same bot within a single tick (simulating SQS at-least-once redelivery); the second processing attempt must hit a UNIQUE conflict on queue_idempotency INSERT and skip all processing — no duplicate hedge-sync or state mutations.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_031
**Scenario Title:** Idempotency — queue_idempotency.state transitions correctly from 'started' to 'succeeded'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5, 13; FR-EXBOT-011
**Test Type:** Data/State
**Description:** Process a single light-check message end-to-end; verify queue_idempotency row has state='started' after step 5 INSERT and state='succeeded' after step 13 UPDATE. The row must not be missing or stuck in 'started' on successful completion.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_032
**Scenario Title:** Idempotency — expires_at always set to now+1min on INSERT
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; FR-EXBOT-011 AC
**Test Type:** Data/State
**Description:** After a Light-Check Worker INSERT into queue_idempotency, verify expires_at is set to approximately now+1 minute (not NULL). The FR-EXBOT-011 AC requires expires_at to always be populated with TTL=1min. The system must never insert a row with expires_at=NULL. Cleanup of expired rows is handled by the EventBridge hourly cron (covered by TS_LC_048).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_033
**Scenario Title:** Concurrency — two Light-Check Workers process the same bot simultaneously, only one proceeds
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; FR-EXBOT-011
**Test Type:** Data/State
**Description:** Simulate two Lambda invocations processing the same botId concurrently (e.g., near-simultaneous duplicate SQS delivery); only the worker that wins the queue_idempotency UNIQUE INSERT must proceed to evaluation and fan-out. The losing worker must skip cleanly without partial state mutations.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_034
**Scenario Title:** State transition — bot in 'active' lifecycle_state is processed normally
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2; FR-EXBOT-002
**Test Type:** Data/State
**Description:** Verify the valid lifecycle_state for normal light-check processing: a bot with lifecycle_state='active' must pass the precondition check and proceed to full trigger evaluation. This is the baseline valid state.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_035
**Scenario Title:** State transition — SAFE_MODE entry changes both bots.status AND bots.lifecycle_state atomically
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; FR-EXBOT-033; AC-LC-15
**Test Type:** Data/State
**Description:** Trigger SAFE_MODE entry (stop_replacing_started_at overrun >60s); after the atomic UPDATE, both bots.status AND bots.lifecycle_state must equal 'safe_mode' in a single transaction. A subsequent read must see both fields changed — never a state where only one field is updated (partial state is a data integrity violation).
**Test Focus:** State transition

---

### Scenario ID: TS_LC_036
**Scenario Title:** State transition — circuit breaker closed→open is NOT triggered by light-check itself
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; FR-EXBOT-040
**Test Type:** Data/State
**Description:** Process a light-check for a bot with circuit_breakers.state='closed' where hedge-sync is enqueued; verify that Light-Check Worker does not modify circuit_breakers.state. Circuit state transitions are driven by hedge-sync handler failures — not by light-check worker.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_037
**Scenario Title:** State transition — circuit breaker half_open probe already claimed, second attempt denied
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A3; FR-EXBOT-040
**Test Type:** Data/State
**Description:** Process two concurrent light-check workers for the same bot with circuit state='half_open'; only one must succeed in atomically claiming half_open_probe_used (0→1 CAS). The second must not enqueue a second probe hedge-sync. Verifies atomic claim prevents double-probe and the extra message flooding the hedge-sync queue.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_038
**Scenario Title:** Integration — Scan Worker enqueues correct per-bot light-check SQS messages
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 3; FR-EXBOT-010, FR-EXBOT-012
**Test Type:** Integration
**Description:** After a bot-scan SQS message is processed by Scan Worker, verify each eligible botId appears as a separate message in the light-check SQS queue via chunkSendBatch. Message payload must include botId and any required metadata; no batching of multiple bots into one message.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_039
**Scenario Title:** Integration — hedge-sync SQS message payload contains botId, reasons[], and stateVersion
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; FR-EXBOT-011
**Test Type:** Integration
**Description:** When Light-Check Worker enqueues a hedge-sync message, verify the SQS message payload contains at minimum: botId, reasons (non-empty array of RebalanceReason enum values from the closed set: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback), and stateVersion matching Aurora PostgreSQL bot_runtime_state.state_version. Downstream hedge-sync handler depends on stateVersion for stale-message detection.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_040
**Scenario Title:** Integration — price-near-stop-audit SQS message enqueued with correct botId
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; FR-EXBOT-031
**Test Type:** Integration
**Description:** When markPrice >= stop_price, verify the price-near-stop-audit SQS message is enqueued with at minimum the botId. The message must be visible to the stop-audit queue consumer. No hedge-sync message for the same stop trigger must be enqueued in the same pass (stop path and rebalance path are separate fan-outs).
**Test Focus:** Integration

---

### Scenario ID: TS_LC_041
**Scenario Title:** Integration — partial_repair SQS message enqueued AFTER atomic SAFE_MODE UPDATE commits
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; FR-EXBOT-033
**Test Type:** Integration
**Description:** Trigger SAFE_MODE entry; verify the ordering: (1) atomic UPDATE setting `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` must be committed to Aurora PostgreSQL before (2) partial_repair SQS message is enqueued. A consumer reading partial_repair must always observe the bot already in safe_mode state in the database.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_042
**Scenario Title:** Integration — EventBridge Scheduler→bot-scan→light-check E2E pipeline produces correct Aurora PostgreSQL state
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 1–13; FR-EXBOT-010, FR-EXBOT-011, FR-EXBOT-012
**Test Type:** End-to-End
**Description:** Trigger a full EventBridge tick with 3 bots: one needing rebalance (drift_threshold), one needing stop audit (markPrice >= stop_price), and one needing no action. After all workers complete, verify: (1) Aurora PostgreSQL next_light_check_at advanced for all 3; (2) one hedge-sync message in queue for first bot with correct reasons[]; (3) stop_trigger_crossed_at set for second bot + price-near-stop-audit in queue; (4) zero HL API calls across all 3.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_043
**Scenario Title:** E2E — post-downtime catch-up: bots with oldest next_light_check_at processed first across successive ticks
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 2; FR-EXBOT-012; AC-LC-16
**Test Type:** End-to-End
**Description:** Simulate a 30-minute system downtime that caused 1500 bots to accumulate past-due next_light_check_at values. After recovery, verify Scan Worker processes the 500 oldest bots per tick in ascending next_light_check_at order, across 3 successive EventBridge ticks. No bot should be skipped permanently; all 1500 must be processed within 3 minutes post-recovery.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_044
**Scenario Title:** Acceptance — AC-LC-01: 10 bots scanned with all trigger types, HL API weight = 0
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §5; BR-EXBOT-003; AC-LC-01
**Test Type:** Acceptance
**Description:** Run a full light-check cycle covering bots with drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, stop trigger, circuit open, and no-action states. Confirm via AWS CloudWatch or Lambda telemetry that zero HTTP calls to any Hyperliquid endpoint were made during the entire cycle. Any HL fetch detected is an architectural violation of BR-EXBOT-003.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_045
**Scenario Title:** Acceptance — AC-LC-05: idempotency prevents duplicate processing on SQS redelivery
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; FR-EXBOT-011; AC-LC-05
**Test Type:** Acceptance
**Description:** Redeliver a light-check SQS message that was already successfully processed (queue_idempotency.state='succeeded') for the same message_id; the Light-Check Worker must detect the UNIQUE conflict on INSERT, skip processing, and produce no additional Aurora PostgreSQL mutations or SQS messages.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_046
**Scenario Title:** funding_alert fires via fallback path — fundingRate × 8760 < -15% APR when funding_rolling_metrics is empty (v1 scope)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011; AC-LC-09
**Test Type:** Functional
**Description:** Process a light-check when the funding_rolling_metrics table is empty (bnza-market-cron not deployed in v1) and the fallback `fundingRate × 8760` computes to less than -15% APR; the funding_alert reason must be included in decision.reason[] and hedge-sync enqueued. Zero HL API calls — fundingRate must be sourced from Aurora PostgreSQL (cached field), not from a live HL API call. This is the only testable funding_alert path in v1 scope.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_047
**Scenario Title:** funding_alert threshold boundary — exactly -15% APR must fire, -14.99% must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011
**Test Type:** Functional
**Description:** Test the boundary of the funding_alert threshold: when the computed 7d APR (or fallback `fundingRate × 8760`) equals exactly -15.0%, funding_alert must fire; when the value equals -14.99% (just above threshold), funding_alert must NOT fire. Verifies strict less-than semantics of the trigger condition.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_048
**Scenario Title:** queue_idempotency cleanup cron — hourly EventBridge job deletes rows with expires_at < now
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5 note; FR-EXBOT-011 AC
**Test Type:** Functional
**Description:** Verify the hourly EventBridge cron job executes `DELETE FROM queue_idempotency WHERE expires_at < now` and removes expired rows. After the cron runs, rows with expires_at older than current time must be absent; rows with expires_at in the future must be unaffected. This prevents unbounded table growth.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_049
**Scenario Title:** HL Mark Price Cache stale — "freeze routine hedge-sync this tick only" — next tick resumes normally
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11
**Test Type:** Functional
**Description:** Process two successive light-check ticks for the same bot: in tick N, HL Mark Price Cache updatedAt > 120s (stale), causing routine hedge-sync to be frozen after the stop check. In tick N+1, HL Mark Price Cache updatedAt <= 120s (fresh); hedge-sync must resume normally without requiring any manual intervention. Verifies the freeze is scoped to one tick only — not a persistent suppression that carries over.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_050
**Scenario Title:** Circuit breaker state read — system reads from circuit_breakers table (canonical), not a hypothetical hedge_legs field
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 6; FR-EXBOT-011; ERD circuit_breakers table
**Test Type:** Data/State
**Description:** Verify that circuit breaker suppression logic (step 10) is driven by the circuit_breakers.state column from the circuit_breakers table, which is the canonical source per the ERD. Set circuit_breakers.state='open' and confirm hedge-sync is correctly suppressed. This test confirms the correct table is the decision point — not any hypothetical circuit_state field in hedge_legs.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_051
**Scenario Title:** Bot in safe_mode — light-check precondition check must prevent processing
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2; FR-EXBOT-002
**Test Type:** Data/State
**Description:** Process a light-check message for a bot where bots.lifecycle_state='safe_mode' (entered due to prior overrun or hedge failure); the Light-Check Worker must skip all trigger evaluation and produce zero downstream messages. safe_mode is not listed as a valid precondition state in UC §2; bots in safe_mode require partial_repair to exit — light-check must not interfere with recovery. BR-EXBOT-007: "SAFE_MODE is never a terminal state" — the system is expected to recover through the partial_repair path.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_052
**Scenario Title:** Acceptance — AC-LC-08: range_out triggers hedge-sync correctly, light-check does NOT set lifecycle_state='lp_rebalancing'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; US-EXBOT-007 AC-007-1; AC-LC-08
**Test Type:** Acceptance
**Description:** Process a light-check where currentTick is outside [tickLower, tickUpper] (range_out condition); verify: (1) range_out is in decision.reason[] in the hedge-sync message; (2) bots.lifecycle_state in Aurora PostgreSQL remains 'active' — NOT changed to 'lp_rebalancing' by the Light-Check Worker; (3) no separate lp_rebalancing queue message is produced. The lifecycle_state='lp_rebalancing' transition belongs exclusively to the downstream hedge-sync worker (per US-EXBOT-007 AC-007-1 fixed 2026-07-14).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_053
**Scenario Title:** drift_relative trigger — fires when |target - actual| / target > 0.15
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011 (v5-I-01: trigger missing from UC step 9, present in FRD)
**Test Type:** Functional
**Description:** Process a bot where the relative drift ratio `|targetShortEth - actualShortEth| / targetShortEth > 0.15` (15%), even if the absolute dollar value does not exceed the drift_threshold; the drift_relative reason must be included in decision.reason[] and hedge-sync must be enqueued. This verifies the second drift trigger operates independently from drift_threshold. Note: drift_relative condition is confirmed in FRD FR-EXBOT-011 but currently missing from UC step 9 (v5-I-01 — pending BA update).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_054
**Scenario Title:** drift_relative boundary — exactly 0.15 ratio must fire, 0.149 must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011 (v5-I-01)
**Test Type:** Functional
**Description:** Test boundary of the drift_relative threshold: when `|targetShortEth - actualShortEth| / targetShortEth` equals exactly 0.15 (15%), drift_relative must fire; when the ratio equals 0.149 (just below threshold), drift_relative must NOT fire. Verifies strict greater-than semantics per FR-EXBOT-011.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_055
**Scenario Title:** funding_alert primary path — fundingApr7dPct from funding_rolling_metrics < -15% (v1.1+ scope)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; FR-EXBOT-011; AC-LC-09; OQ-EXBOT-12 closed
**Test Type:** Functional
**Description:** Process a light-check when funding_rolling_metrics has a row for the bot and `fundingApr7dPct = (Σ funding_net_usd 7 rows / lp_value_usd) × (365/7) × 100` computes to less than -15%; the funding_alert reason must fire using the primary source. Formula confirmed by zen (OQ-EXBOT-12 closed 2026-07-20). If fewer than 7 rows exist, use `(Σ funding_net_usd n rows / lp_value_usd) × (365/n) × 100` where n < 7. Blocked until bnza-market-cron deploys in v1.1.
**Test Focus:** Happy path

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| funding_alert primary path (bnza-market-cron) | BLOCKED (v1): funding_rolling_metrics table exists in ERD and formula confirmed (OQ-EXBOT-12 closed zen 2026-07-20), but bnza-market-cron worker not deployed in v1 — table empty. Fallback path (fundingRate × 8760) testable in v1 (TS_LC_046, TS_LC_047). Primary path (TS_LC_055) requires v1.1 deployment. | Design fallback path scenarios now (done); defer primary path execution to v1.1 release |
| drift_relative and time_fallback in UC step 9 | PARTIAL (v5-I-01): Both triggers exist in FRD FR-EXBOT-011 but UC step 9 does not list them with explicit threshold values. Scenarios TS_LC_053/054 (drift_relative) and TS_LC_011 (time_fallback) are designed from FRD as source of truth. | BA to update UC step 9 per v5-I-01 to list all 7 RebalanceReason triggers with conditions |
| manual_admin RebalanceReason trigger in light-check | BLOCKED: UC step 9 and FRD FR-EXBOT-011 do not define conditions under which light-check fires manual_admin reason — unclear if light-check can emit this reason at all vs admin-initiated path | BA to clarify whether manual_admin is emittable by light-check worker; if not, document explicitly in UC step 9 |
| recovery_reconcile RebalanceReason trigger in light-check | BLOCKED: UC step 9 and FRD FR-EXBOT-011 do not define conditions under which light-check fires recovery_reconcile reason | BA to clarify whether recovery_reconcile is emittable by light-check worker; add trigger condition to UC step 9 |
| fundingRate fallback source field identity | BLOCKED: UC step 9 does not document which Aurora PostgreSQL field supplies fundingRate for the fallback formula (fundingRate × 8760). If sourced from HL API, this violates BR-EXBOT-003. TS_LC_046 assumes Aurora PostgreSQL source. | BA to confirm exact field name (e.g. bot_runtime_state or hedge_legs field); update TS_LC_046 description if different |
| Load / throughput testing (10,000 bot cycle SLA) | NFR: PERFORMANCE — out of scope for this skill | Defer to performance testing with k6/locust; validate via AWS Lambda concurrent execution + SQS throughput metrics |
| Security testing (SQS message tampering, IAM boundary) | NFR: SECURITY — out of scope for this skill | Defer to security review; validate IAM least-privilege for Lambda → SQS → ElastiCache access |

