# Test Scenarios — UC-EXBOT-light-check Execute Periodic Light-Check

> Source: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260714_v4.md
> Generated: 2026-07-15
> Domain/Architecture: AWS Lambda (Scan Worker + Light-Check Worker) + SQS queues + Aurora PostgreSQL + ElastiCache Redis (Pool Slot0 Cache + HL Mark Price Cache). Zero Hyperliquid API calls in light-check (BR-EXBOT-003).

## UC-EXBOT-light-check — Execute Periodic Light-Check

---

### Scenario ID: TS_LC_001
**Scenario Title:** Happy path — full scan-to-light-check pipeline, bot needs no rebalance
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 1–13; SRS FR-EXBOT-010, FR-EXBOT-012, FR-EXBOT-013
**Test Type:** Functional
**Description:** Trigger an EventBridge Scheduler tick with one active bot whose drift, range, margin, and stop conditions are all within safe bounds; the entire pipeline (Scan Worker query → enqueue light-check → Light-Check Worker evaluation → idempotency finalize) must complete with zero Hyperliquid API calls, zero queue messages produced, and next_light_check_at advanced by 5 min ± 45 s.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_002
**Scenario Title:** Happy path — drift_threshold fires, hedge-sync enqueued with correct reasons
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9–10; SRS FR-EXBOT-012, FR-EXBOT-023; AC-LC-01, AC-LC-10
**Test Type:** Functional
**Description:** Process a light-check for a bot whose |targetShortEth - lastKnownShortEth| × currentPriceUsd exceeds drift_threshold (max($25, lpValueUsd × 3%)); the system must enqueue exactly one hedge-sync message containing reasons=['drift_threshold'] and the current stateVersion, with zero HL API calls.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_003
**Scenario Title:** Happy path — range_out fires, routed to hedge-sync NOT to a separate lp_rebalancing queue
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; SRS FR-EXBOT-012, FR-EXBOT-015; AC-LC-11
**Test Type:** Functional
**Description:** Process a light-check for a bot with rangeState != 'in' (price above upper tick or below lower tick); the system must include 'range_out' in decision.reason[] and enqueue one hedge-sync message. The Light-Check Worker must NOT set lifecycle_state='lp_rebalancing' and must NOT enqueue any separate lp_rebalancing message — lifecycle transition is downstream hedge-sync handler responsibility.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_004
**Scenario Title:** Happy path — multiple reasons fire simultaneously, single hedge-sync with all reasons
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9–10; SRS FR-EXBOT-012; AC-LC-10
**Test Type:** Functional
**Description:** Process a light-check where both drift_threshold and range_boundary_near conditions are true simultaneously; the strategy engine must aggregate all fired triggers into a single decision.reason[] array and enqueue exactly one hedge-sync message (not two separate messages).
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_005
**Scenario Title:** range_boundary_near — fires at boundary (nearestFraction = 0.9 exactly)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; SRS OQ-EXBOT-10 (closed); AC-LC-08
**Test Type:** Functional
**Description:** Process a bot where min(distToLower, distToUpper) / halfRange equals exactly 0.9 (rangeBoundaryFraction default); the range_boundary_near trigger must fire and be included in decision.reason[]. This verifies the boundary condition of the price-based USD formula.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_006
**Scenario Title:** range_boundary_near — does NOT fire just above boundary (nearestFraction = 0.91)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; SRS OQ-EXBOT-10 (closed); AC-LC-08
**Test Type:** Functional
**Description:** Process a bot where min(distToLower, distToUpper) / halfRange equals 0.91 (just above the 0.9 threshold); range_boundary_near must NOT fire. Verifies the boundary does not bleed into valid zone.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_007
**Scenario Title:** drift_threshold — fires at exact threshold boundary ($25 flat threshold)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; AC-LC-07
**Test Type:** Functional
**Description:** Process a bot where lpValueUsd × 3% < $25 (so flat $25 threshold applies) and the computed deltaErrorUsd equals exactly $25; drift_threshold must fire. Verifies the max($25, lpValueUsd × 3%) formula selects the flat floor correctly at the exact boundary.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_008
**Scenario Title:** drift_threshold — fires at percentage threshold (lpValueUsd × 3% > $25)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; AC-LC-07
**Test Type:** Functional
**Description:** Process a bot where lpValueUsd is large enough that lpValueUsd × 3% > $25 (e.g., lpValueUsd = $1000 → threshold = $30) and deltaErrorUsd equals exactly $30; drift_threshold must fire. Verifies the percentage branch of the max($25, lpValueUsd × 3%) formula.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_009
**Scenario Title:** drift_threshold — lpValueUsd = 0 (lpEthAmount = 0 edge case)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; AC-LC-07
**Test Type:** Functional
**Description:** Process a bot where lpEthAmount computes to 0 (e.g., position fully out of range with no ETH component); lpValueUsd = max(0, 0 × currentPriceUsd) = 0, so drift_threshold falls back to $25 flat. System must not produce negative threshold or divide-by-zero error.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_010
**Scenario Title:** margin_warning trigger — fires when margin_status = 'warning'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Process a bot with hedge_legs.margin_status = 'warning' in Aurora PostgreSQL; the margin_warning reason must be included in decision.reason[] and hedge-sync must be enqueued. Margin status is read from Aurora PostgreSQL only — no HL fetch occurs.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_011
**Scenario Title:** time_fallback trigger — fires when no other reason fires but enough time has elapsed
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; SRS FR-EXBOT-023
**Test Type:** Functional
**Description:** Process a bot where no drift, range, margin, or funding condition is met, but time_fallback threshold is reached; the system must enqueue hedge-sync with reasons=['time_fallback']. Verifies periodic forced reconcile fires even when other triggers are silent.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_012
**Scenario Title:** stop trigger detected — markPrice >= stop_price, stop_trigger_crossed_at set and price-near-stop-audit enqueued
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; SRS FR-EXBOT-032; AC-LC-13
**Test Type:** Functional
**Description:** Process a bot where HL Mark Price Cache markPriceUsd >= hedge_legs.stop_price and stop_trigger_crossed_at IS NULL; the system must atomically set stop_trigger_crossed_at = now (write-once) and enqueue price-near-stop-audit. Must NOT suppress this action regardless of circuit breaker state.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_013
**Scenario Title:** stop trigger write-once guard — stop_trigger_crossed_at already set, must not overwrite
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A4; SRS BR-EXBOT-005; AC-LC-13
**Test Type:** Functional
**Description:** Process a bot where markPrice >= stop_price but stop_trigger_crossed_at IS NOT NULL (already set by a prior tick); the system must NOT overwrite the existing timestamp, but must still enqueue price-near-stop-audit. BR-EXBOT-005: stop_trigger_crossed_at is write-once.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_014
**Scenario Title:** SAFE_MODE entry — stop_replacing_started_at overrun > 60s, atomic UPDATE + partial_repair
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; SRS FR-EXBOT-033; AC-LC-15
**Test Type:** Functional
**Description:** Process a bot where stop_replacing_started_at IS NOT NULL and (now - stop_replacing_started_at) > 60s; the Light-Check Worker must execute a single atomic SQL UPDATE setting both bots.status='safe_mode' AND bots.lifecycle_state='safe_mode', then enqueue partial_repair(reason='stop_replacing_overrun'). The UPDATE must complete before the partial_repair message enters the queue.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_015
**Scenario Title:** SAFE_MODE entry — boundary: overrun exactly at 60s must NOT trigger, 61s must trigger
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; SRS FR-EXBOT-033
**Test Type:** Functional
**Description:** Verify the 60-second overrun threshold boundary: a bot with stop_replacing_started_at set to exactly 60s ago must NOT enter SAFE_MODE; a bot at 61s must trigger the atomic UPDATE and partial_repair enqueue.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_016
**Scenario Title:** Circuit breaker open — hedge-sync suppressed, stop monitoring continues
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A2; SRS FR-EXBOT-014; AC-LC-12
**Test Type:** Functional
**Description:** Process a bot with circuit_breakers.state='open' and a rebalance condition (drift_threshold) active; the system must NOT enqueue hedge-sync, but must still evaluate stop trigger (step 11) and SAFE_MODE check (step 12). If markPrice >= stop_price, price-near-stop-audit must still be enqueued.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_017
**Scenario Title:** Circuit breaker half_open — exactly one probe hedge-sync enqueued via atomic claim
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A3; SRS FR-EXBOT-040; AC-LC-16
**Test Type:** Functional
**Description:** Process a bot with circuit_breakers.state='half_open' and a rebalance condition active; the system must atomically claim half_open_probe_used (0→1) and enqueue exactly one probe hedge-sync. No additional hedge-sync messages for the same bot in the same tick.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_018
**Scenario Title:** Pool Slot0 Cache stale (>5 min) — tick skipped entirely, no mutation
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A1; SRS FR-EXBOT-093; AC-LC-03
**Test Type:** Functional
**Description:** Process a light-check where the Pool Slot0 Cache (ElastiCache Redis) updatedAt is more than 5 minutes ago; the Light-Check Worker must throw at step 7, skip all trigger evaluation, and produce zero mutations to Aurora PostgreSQL. queue_idempotency.state must remain 'started' (not finalized).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_019
**Scenario Title:** Pool Slot0 Cache unreachable — tick skipped entirely, same as stale behavior
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A1; SRS FR-EXBOT-093; AC-LC-03
**Test Type:** Functional
**Description:** Process a light-check where the Pool Slot0 Cache (ElastiCache Redis) is unreachable (connection error); the Light-Check Worker must fail-fast at step 7 with the same skip behavior as stale — no trigger evaluation, zero Aurora PostgreSQL mutations.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_LC_020
**Scenario Title:** Pool Slot0 Cache stale boundary — exactly 5 min old must trigger skip, 4m59s must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 7; SRS FR-EXBOT-093
**Test Type:** Functional
**Description:** Verify the 5-minute stale threshold: a cache snapshot aged exactly 5 minutes must trigger the fail-fast skip; a snapshot aged 4 minutes 59 seconds must be accepted and processing continues normally.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_021
**Scenario Title:** HL Mark Price Cache stale (>120s) — fallback to eth_price_usd, near-stop band widened to 4%
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; SRS OQ-EXBOT-17 (closed); AC-LC-14
**Test Type:** Functional
**Description:** Process a light-check where HL Mark Price Cache updatedAt > 120s ago; the system must log hl_mark_price_stale audit event, fall back to bot_runtime_state.eth_price_usd for stop trigger evaluation, widen the near-stop band from 2% to 4%, and freeze routine hedge-sync after the stop check.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_022
**Scenario Title:** HL Mark Price Cache stale boundary — exactly 120s must trigger stale path, 119s must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11
**Test Type:** Functional
**Description:** Verify the 120-second stale threshold for HL Mark Price Cache: a cache aged exactly 120s must trigger the fallback/widen path; a cache aged 119s must use the primary markPriceUsd normally.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_023
**Scenario Title:** Bot with lifecycle_state='lp_rebalancing' — skipped by Light-Check Worker, still rescheduled
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2, §3 step 4; SRS FR-EXBOT-012; AC-LC-02
**Test Type:** Functional
**Description:** Process a Scan Worker tick where one bot has lifecycle_state='lp_rebalancing'; Scan Worker must still include that bot in the next_light_check_at batch update, but Light-Check Worker must skip all rebalance evaluation and enqueuing for that bot (no hedge-sync, no price-near-stop-audit).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_024
**Scenario Title:** Bot with lifecycle_state='lp_closing' — skipped by Light-Check Worker
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2; SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Process a light-check for a bot with lifecycle_state='lp_closing'; the Light-Check Worker must skip all evaluation, consistent with the lp_rebalancing behavior. next_light_check_at must still be advanced by Scan Worker.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_025
**Scenario Title:** Bot with lifecycle_state='hedge_stopped_cooldown' — light-check runs, hedge-sync suppressed
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2 (note); SRS states.md
**Test Type:** Functional
**Description:** Process a light-check for a bot with lifecycle_state='hedge_stopped_cooldown'; the UC explicitly states these bots are NOT skipped — light-check evaluation runs, but hedge-sync is suppressed. Stop monitoring (step 11) must still execute.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_026
**Scenario Title:** Scan Worker LIMIT 500 — bots beyond 500 eligible deferred to next tick, oldest processed first
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 2; SRS FR-EXBOT-012; AC-LC-17
**Test Type:** Functional
**Description:** With a shard containing 600 bots due for light-check simultaneously, Scan Worker must query ORDER BY next_light_check_at LIMIT 500, process the 500 oldest bots first, and defer the remaining 100 to the next EventBridge tick (1 min later). No bots are dropped permanently.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_027
**Scenario Title:** next_light_check_at batch update — single SQL statement covers all eligible bots including skipped
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 4; SRS FR-EXBOT-013; AC-LC-05
**Test Type:** Functional
**Description:** After Scan Worker processes a batch of bots (including some with lifecycle_state='lp_rebalancing'), verify that next_light_check_at is updated for ALL eligible bots in a single UPDATE statement per shard — not per-bot individual writes. Bots that Light-Check Worker later skips must still have their next_light_check_at advanced correctly.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_028
**Scenario Title:** HL API call count = 0 across entire light-check pipeline
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §5; SRS BR-EXBOT-003; AC-LC-04
**Test Type:** Acceptance
**Description:** Execute a full light-check cycle for 10 bots covering all trigger types (drift, range_out, range_boundary_near, margin_warning, stop trigger); verify that zero Hyperliquid API calls are made by any component in the pipeline. Any HL fetch detected is an architectural violation.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_029
**Scenario Title:** jitter distribution — next_light_check_at set within now+5min ± 45s
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 4; SRS FR-EXBOT-013
**Test Type:** Functional
**Description:** After a Scan Worker batch update, verify that each bot's new next_light_check_at falls within the range [now + 4m15s, now + 5m45s]. Jitter must be deterministic per botId (hash-based), not random — same botId must produce same jitter offset on repeated calls.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_030
**Scenario Title:** Idempotency — duplicate light-check message for same bot in same tick skipped
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; SRS FR-EXBOT-011; AC-LC-06
**Test Type:** Data/State
**Description:** Deliver two light-check SQS messages with the same message_id for the same bot within a single tick (simulating SQS at-least-once redelivery); the second processing attempt must hit a UNIQUE conflict on queue_idempotency INSERT and skip all processing — no duplicate hedge-sync or state mutations.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_031
**Scenario Title:** Idempotency — queue_idempotency.state transitions correctly from 'started' to 'succeeded'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5, 13; SRS FR-EXBOT-011
**Test Type:** Data/State
**Description:** Process a single light-check message end-to-end; verify queue_idempotency row has state='started' after step 5 INSERT and state='succeeded' after step 13 UPDATE. The row must not be missing or stuck in 'started' on successful completion.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_032
**Scenario Title:** Idempotency — expires_at always set to now+1min on INSERT
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; SRS FR-EXBOT-011 AC
**Test Type:** Data/State
**Description:** After a Light-Check Worker INSERT into queue_idempotency, verify expires_at is set to approximately now+1 minute (not NULL). This confirms the FR-EXBOT-011 AC behavior: expires_at is always populated with TTL=1min. The system must never insert a row with expires_at=NULL. (Cleanup of expired rows is handled by the EventBridge hourly cron job — covered in TS_LC_048.)
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_033
**Scenario Title:** Concurrency — two Light-Check Workers process the same bot simultaneously, only one proceeds
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; SRS FR-EXBOT-011
**Test Type:** Data/State
**Description:** Simulate two Lambda invocations processing the same botId concurrently (e.g., duplicate SQS message delivery with near-simultaneous timing); only the worker that wins the queue_idempotency UNIQUE INSERT must proceed to evaluation and fan-out. The losing worker must skip cleanly without partial state mutations.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_034
**Scenario Title:** State transition — bot in 'active' lifecycle_state is processed normally
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2; SRS states.md
**Test Type:** Data/State
**Description:** Verify the valid lifecycle_state for normal light-check processing: a bot with lifecycle_state='active' must pass the precondition check and proceed to full trigger evaluation. This is the baseline valid state.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_035
**Scenario Title:** State transition — SAFE_MODE entry changes both bots.status AND bots.lifecycle_state atomically
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; SRS FR-EXBOT-033; AC-LC-15
**Test Type:** Data/State
**Description:** Trigger SAFE_MODE entry (stop_replacing_started_at overrun >60s); after the atomic UPDATE, both bots.status AND bots.lifecycle_state must equal 'safe_mode' in a single transaction. A subsequent read must see both fields changed — never a state where only one is updated.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_036
**Scenario Title:** State transition — circuit breaker closed→open is NOT triggered by light-check itself
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; SRS FR-EXBOT-040
**Test Type:** Data/State
**Description:** Process a light-check for a bot with circuit_breakers.state='closed' where hedge-sync is enqueued; verify that Light-Check Worker does not modify circuit_breakers.state. Circuit state transitions are driven by hedge-sync handler failures — not by light-check.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_037
**Scenario Title:** State transition — circuit breaker half_open probe attempt when probe already claimed
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §4 A3; SRS FR-EXBOT-040
**Test Type:** Data/State
**Description:** Process two concurrent light-check workers for the same bot with circuit state='half_open'; only one must succeed in claiming half_open_probe_used (0→1 atomic CAS). The second must not enqueue a second probe hedge-sync. Verifies atomic claim prevents double-probe.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_LC_038
**Scenario Title:** Integration — Scan Worker enqueues correct per-bot light-check SQS messages
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 3; SRS FR-EXBOT-010, FR-EXBOT-012
**Test Type:** Integration
**Description:** After a bot-scan SQS message is processed by Scan Worker, verify each eligible botId appears as a separate message in the light-check SQS queue via chunkSendBatch. Message payload must include botId and any required metadata; no batching of multiple bots into one message.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_039
**Scenario Title:** Integration — hedge-sync SQS message payload contains botId, reasons[], and stateVersion
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; SRS FR-EXBOT-012
**Test Type:** Integration
**Description:** When Light-Check Worker enqueues a hedge-sync message, verify the SQS message payload contains at minimum: botId, reasons (non-empty array of RebalanceReason enum values), and stateVersion matching Aurora PostgreSQL bot_runtime_state.state_version. Downstream hedge-sync handler depends on these fields for stale-message detection.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_040
**Scenario Title:** Integration — price-near-stop-audit SQS message enqueued with correct botId
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; SRS FR-EXBOT-032
**Test Type:** Integration
**Description:** When markPrice >= stop_price, verify the price-near-stop-audit SQS message is enqueued with at minimum the botId. The message must be visible to the stop-audit queue consumer. No hedge-sync message for the same trigger must be enqueued in the same pass (stop and rebalance are separate fan-out paths).
**Test Focus:** Integration

---

### Scenario ID: TS_LC_041
**Scenario Title:** Integration — partial_repair SQS message enqueued AFTER atomic SAFE_MODE UPDATE commits
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 12; SRS FR-EXBOT-033
**Test Type:** Integration
**Description:** Trigger SAFE_MODE entry; verify the ordering: (1) atomic UPDATE bots.status='safe_mode' AND bots.lifecycle_state='safe_mode' must be committed to Aurora PostgreSQL before (2) partial_repair SQS message is enqueued. A consumer reading partial_repair must always observe the bot already in safe_mode state in the database.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_042
**Scenario Title:** Integration — EventBridge Scheduler→bot-scan→light-check E2E pipeline produces correct Aurora PostgreSQL state
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 1–13; SRS FR-EXBOT-010, FR-EXBOT-012, FR-EXBOT-013
**Test Type:** End-to-End
**Description:** Trigger a full EventBridge tick with 3 bots: one needing rebalance (drift_threshold), one needing stop audit (markPrice >= stop_price), and one needing no action. After all workers complete, verify: (1) Aurora PostgreSQL next_light_check_at advanced for all 3; (2) one hedge-sync message in queue for first bot; (3) stop_trigger_crossed_at set for second bot + price-near-stop-audit in queue; (4) zero HL API calls across all 3.
**Test Focus:** Integration

---

### Scenario ID: TS_LC_043
**Scenario Title:** E2E — post-downtime catch-up: bots with oldest next_light_check_at processed first across successive ticks
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 2; SRS FR-EXBOT-012; AC-LC-17
**Test Type:** End-to-End
**Description:** Simulate a 30-minute system downtime that caused 1500 bots to accumulate past-due next_light_check_at values. After recovery, verify Scan Worker processes the 500 oldest bots per tick, in ascending next_light_check_at order, across 3 successive EventBridge ticks. No bot should be skipped permanently; all 1500 must be processed within 3 minutes post-recovery.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_044
**Scenario Title:** Acceptance — AC-LC-04: 10 bots scanned with all trigger types, HL API weight = 0
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §5; SRS BR-EXBOT-003; AC-LC-04
**Test Type:** Acceptance
**Description:** Run a full light-check cycle covering bots with drift_threshold, range_out, range_boundary_near, margin_warning, stop trigger, circuit open, and no-action states. Confirm via AWS CloudWatch or Lambda telemetry that zero HTTP calls to api.hyperliquid.xyz or any HL endpoint were made during the entire cycle.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_045
**Scenario Title:** Acceptance — AC-LC-06: idempotency prevents duplicate processing on SQS redelivery
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5; SRS FR-EXBOT-011; AC-LC-06
**Test Type:** Acceptance
**Description:** Redeliver a light-check SQS message that was already successfully processed (queue_idempotency.state='succeeded') for the same message_id; the Light-Check Worker must detect the UNIQUE conflict on INSERT, skip processing, and produce no additional Aurora PostgreSQL mutations or SQS messages.
**Test Focus:** Idempotency/Concurrency

---


---

### Scenario ID: TS_LC_046
**Scenario Title:** funding_alert fires via fallback path — fundingRate x 8760 < -15% APR when funding_rolling_metrics is empty (v1 scope)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; SRS FR-EXBOT-023; v4 audit note (v3-I-03 partially resolved)
**Test Type:** Functional
**Description:** Process a light-check for a bot when funding_rolling_metrics table is empty (bnza-market-cron not deployed in v1) and the fallback fundingRate x 8760 computes to less than -15% APR; the funding_alert reason must be included in decision.reason[] and hedge-sync enqueued. This is the only testable path in v1 scope. Zero HL API calls must be confirmed — fundingRate must be sourced from Aurora PostgreSQL (cached), not from a live HL API call.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_047
**Scenario Title:** funding_alert threshold boundary — exactly -15% APR must fire, -14.99% must not
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 9; SRS FR-EXBOT-023
**Test Type:** Functional
**Description:** Test the boundary of the funding_alert threshold: when fundingRate x 8760 equals exactly -15.0% APR (or fundingApr7dPct = -15.0% when primary source available), funding_alert must fire; when the value equals -14.99% (just above the threshold), funding_alert must NOT fire. Verifies strict less-than vs less-than-or-equal-to semantics of the trigger condition.
**Test Focus:** Boundary

---

### Scenario ID: TS_LC_048
**Scenario Title:** queue_idempotency cleanup cron — hourly EventBridge job deletes rows with expires_at < now
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 5 note; SRS FR-EXBOT-011 AC
**Test Type:** Functional
**Description:** Verify the hourly EventBridge cron job (as defined in FR-EXBOT-011 AC) executes DELETE FROM queue_idempotency WHERE expires_at < now and removes expired rows. After the cron runs, rows with expires_at older than the current time must be absent from the table; rows with expires_at in the future must be unaffected. This prevents unbounded table growth over time.
**Test Focus:** Happy path

---

### Scenario ID: TS_LC_049
**Scenario Title:** HL Mark Price Cache stale — "freeze routine hedge-sync this tick only" — next tick resumes normally
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 11; SRS flows.md F-01; v4-N-04
**Test Type:** Functional
**Description:** Process two successive light-check ticks for the same bot: in tick N, HL Mark Price Cache updatedAt > 120s (stale), causing routine hedge-sync to be frozen. In tick N+1, HL Mark Price Cache updatedAt <= 120s (fresh); hedge-sync must resume normally without requiring any manual intervention. Verifies the freeze is scoped to one tick only — not a persistent suppression that carries over.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_LC_050
**Scenario Title:** Circuit breaker state read — system reads from circuit_breakers table (canonical), not hedge_legs.circuit_state field
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 6; SRS erd.md (circuit_breakers table); v4-N-02
**Test Type:** Data/State
**Description:** Verify that circuit breaker suppression logic (step 10) is driven by the circuit_breakers.state column from the circuit_breakers table, which is the canonical source per the ERD — not from a circuit_state field hypothetically in hedge_legs. Set circuit_breakers.state='open' with circuit_state absent from hedge_legs (or inconsistent); confirm hedge-sync is correctly suppressed. This test confirms the correct table is the decision point.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_051
**Scenario Title:** Bot in safe_mode — light-check precondition check must prevent processing (invalid lifecycle_state)
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §2; SRS states.md
**Test Type:** Data/State
**Description:** Process a light-check message for a bot where bots.lifecycle_state='safe_mode' (entered due to prior overrun or hedge failure); the Light-Check Worker must skip all trigger evaluation and produce zero downstream messages. safe_mode is not listed as a valid precondition state in UC §2 and bots in safe_mode require partial_repair to exit — light-check must not interfere.
**Test Focus:** State transition

---

### Scenario ID: TS_LC_052
**Scenario Title:** Acceptance — AC-LC-14: range_out triggers hedge-sync correctly, light-check does NOT set lifecycle_state='lp_rebalancing'
**UC Reference:** UC-EXBOT-light-check — Execute Periodic Light-Check
**Req-ID:** UC-EXBOT-light-check §3 step 10; US-EXBOT-007 AC-007-4; v3-I-02 resolved
**Test Type:** Acceptance
**Description:** Process a light-check where currentTick is outside [tickLower, tickUpper] (range_out condition); verify: (1) range_out is in decision.reason[] in the hedge-sync message; (2) bots.lifecycle_state in Aurora PostgreSQL remains 'active' — NOT changed to 'lp_rebalancing' by the Light-Check Worker; (3) no separate lp_rebalancing queue message is produced. The lifecycle_state='lp_rebalancing' transition belongs exclusively to the downstream hedge-sync worker (per US-EXBOT-007 AC-007-1).
**Test Focus:** Happy path


## Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| funding_alert primary path (bnza-market-cron) | BLOCKED (v1): funding_rolling_metrics table exists in ERD (confirmed 2026-07-14) but bnza-market-cron worker not deployed in v1 — primary fundingApr7dPct source is empty. Fallback path (fundingRate x 8760) IS testable and covered by TS_LC_046, TS_LC_047. OQ-EXBOT-12 (7d APR formula) still Open — primary path test cases will be designed post-v2 deployment. | Design fallback path scenarios now (done); defer primary path to v2 release + qc-qna for OQ-EXBOT-12 |
| Load / throughput testing (10,000 bot cycle SLA) | NFR: PERFORMANCE — out of scope for this skill | Defer to performance testing specialist with k6 / locust; validate via AWS Lambda concurrent execution + SQS throughput metrics |
| Security testing (SQS message tampering, IAM boundary) | NFR: SECURITY — out of scope for this skill | Defer to security review; validate IAM least-privilege for Lambda → SQS → ElastiCache access |
| manual_admin RebalanceReason trigger in light-check | BLOCKED (v4-N-01): UC step 9 does not define conditions under which light-check fires manual_admin reason — unclear if light-check can emit this reason at all | BA to clarify whether manual_admin is emittable by light-check worker; if not, document explicitly in UC step 9 |
| recovery_reconcile RebalanceReason trigger in light-check | BLOCKED (v4-N-01): UC step 9 does not define conditions under which light-check fires recovery_reconcile reason | BA to clarify whether recovery_reconcile is emittable by light-check worker; add trigger condition to UC step 9 |
| fundingRate fallback source identity | BLOCKED (v4-N-03): UC step 9 does not document which Aurora PostgreSQL field supplies fundingRate for the fallback formula (fundingRate x 8760). If sourced from HL API, this violates BR-EXBOT-003. | BA to confirm field name (e.g. bot_runtime_state.last_funding_rate); TS_LC_046 is written assuming Aurora source — update if different |
