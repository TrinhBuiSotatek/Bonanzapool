---
title: Test Scenarios -- UC-EXBOT-hedge-sync (Execute Delta-Only Hedge Adjustment)
date_created: 2026-07-24
author: QC Func Scenario Design ExBot Agent
version: v5
source_audit: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260724_v5.md
prior_scenarios: docs/qc/scenarios/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_scenarios_20260715_v4.md
---

# Test Scenarios -- UC-EXBOT-hedge-sync (Execute Delta-Only Hedge Adjustment)

> Source: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260724_v5.md
> Generated: 2026-07-24
> Domain/Architecture: AWS Lambda (Hedge-Sync Worker + Reconcile Worker) + Redis Redlock (ElastiCache) + Aurora PostgreSQL + SQS FIFO + Hyperliquid external API. No UI -- all test operations are logic/queue/API.
> Verdict of source audit: READY 94/100
> Changes from v4: Q1/Q7 resolved (no_op_dust delta=0 path fully specified); Q2 resolved (INV-STOP place-before-cancel confirmed); Q6 resolved (lpValueUsd formula + drift_threshold). Scenarios TS_025--TS_032 are new for v5.

---

## UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment

### Scenario ID: TS_EXBOT-hedge-sync_001
**Scenario Title:** Happy path -- full 16-step delta adjustment completes successfully
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 1-16; FR-EXBOT-020/021/022/024/025/035/092; AC-01
**Test Type:** Functional
**Description:** Enqueue a hedge-sync message for an active bot whose stateVersion matches DB, circuit is closed, and User Lock is available; the delta between targetShortEth and actualShortEth is non-zero. Verify the Worker completes all 16 steps: idempotency insert, stateVersion check, circuit recheck, lock acquire, clearinghouseState fetch, delta compute, adjustShortDelta submit, reconcile enqueue, INV-STOP stop replacement (place->verify->cancel), lock release, reconcile worker verifies exact fill, hedge_legs updated, rebalance_attempts.status='success', queue_idempotency.state='succeeded'.
**Test Focus:** Happy path

### Scenario ID: TS_EXBOT-hedge-sync_002
**Scenario Title:** Duplicate message delivery -- idempotency guard prevents second execution
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 1; FR-EXBOT-011; AC-16
**Test Type:** Functional
**Description:** Deliver the same hedge-sync message (same message_id) twice to the queue. Verify the second delivery hits a UNIQUE constraint conflict on queue_idempotency.message_id and returns immediately -- no HL order submitted, no rebalance_attempts row inserted, no lock acquired on second delivery.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_EXBOT-hedge-sync_003
**Scenario Title:** stateVersion mismatch -- message discarded without HL interaction
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 2, §4 A2; FR-EXBOT-027; AC-02
**Test Type:** Functional
**Description:** Enqueue a hedge-sync message with stateVersion=5; set DB bots.state_version=6 before the Worker reads it. Verify the Worker discards the message after the stateVersion check -- rebalance_attempts.status='skipped', reason=original RebalanceReason[], no HL call made, no User Lock acquired.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_004
**Scenario Title:** Circuit recheck at execution time -- circuit transitions open between enqueue and execute
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 2; FR-EXBOT-040; AC-17
**Test Type:** Functional
**Description:** Enqueue a hedge-sync message while circuit_breakers.state='closed'; before the Worker processes it, set circuit_breakers.state='open'. Verify the Worker rechecks circuit state at step 2, discards with status='skipped', and does not acquire the lock or submit any HL order.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_005
**Scenario Title:** User Lock not acquired -- message re-queued without HL mutation
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 3, §4 A1; FR-EXBOT-092; AC-03
**Test Type:** Functional
**Description:** Simulate a concurrent worker already holding the User Lock for the same botId. Verify the current Worker receives acquired=false, re-queues the message with delay, and makes no HL order call and no DB mutation to hedge_legs.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_006
**Scenario Title:** delta=0 (abs < 0.000001) -- no_op_dust short-circuit, no downstream effects
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 5, §4 A6; spec.md OQ-EXBOT-013 Closed; AC-12
**Test Type:** Functional
**Description:** Enqueue a hedge-sync message for a bot where targetShortEth and actualShortEth differ by less than 0.000001 ETH. Verify Worker returns {status: 'no_op_dust'} immediately after delta computation -- no HL adjustShortDelta call, no reconcile message enqueued, no INV-STOP stop replacement, entry_price/liq_price/stop_trigger_px all unchanged in DB, queue_idempotency.state='succeeded'.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_007
**Scenario Title:** BVA: delta exactly at no_op_dust boundary (abs = 0.000001)
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 5; spec.md OQ-EXBOT-013 Closed; AC-12
**Test Type:** Functional
**Description:** Configure targetShortEth - actualShortEth = exactly 0.000001 ETH (the boundary). Verify this is NOT treated as no_op_dust -- the Worker proceeds to submit adjustShortDelta (not short-circuit). One unit below (0.0000009) must trigger no_op_dust.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_008
**Scenario Title:** BVA: delta just below no_op_dust boundary (abs = 0.0000009)
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 5; spec.md OQ-EXBOT-013 Closed; AC-12
**Test Type:** Functional
**Description:** Configure targetShortEth - actualShortEth = 0.0000009 ETH (just below the 0.000001 threshold). Verify Worker returns no_op_dust immediately, with no HL order and no downstream effects. This confirms the exclusive boundary (<, not <=).
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_009
**Scenario Title:** BigDecimal precision -- fractional ETH delta with many decimal places
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-021; NFR-EXBOT-008; spec.md §6 BigDecimal invariant
**Test Type:** Functional
**Description:** Submit a hedge-sync for a bot with targetShortEth = 0.123456789012345 ETH and actualShortEth = 0.100000000000001 ETH. Verify delta is computed exactly as 0.023456789012344 ETH using BigDecimal arithmetic (no float rounding), and the same exact value is submitted in the adjustShortDelta payload. Confirm no float/Number conversion occurs in any intermediate computation.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_010
**Scenario Title:** HL adjustShortDelta rejected (insufficient margin) -- circuit breaker incremented
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §4 A3; FR-EXBOT-040; AC-04; E-EXBOT-007
**Test Type:** Functional
**Description:** Simulate HL API returning a rejection for adjustShortDelta due to insufficient margin. Verify: rebalance_attempts.status='failed', incrementCircuitBreaker called (failure_count increments by 1), notification enqueued with message E-EXBOT-007 "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin.", User Lock released.
**Test Focus:** Error/Exception

### Scenario ID: TS_EXBOT-hedge-sync_011
**Scenario Title:** HL API unreachable during clearinghouseState fetch -- bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 4; FR-EXBOT-050; E-EXBOT-008
**Test Type:** Functional
**Description:** Simulate HL API returning a network timeout during the clearinghouseState fetch (step 4, after lock is acquired). Verify bot enters SAFE_MODE (bots.lifecycle_state='safe_mode'), notification enqueued with E-EXBOT-008 "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically.", User Lock released in finally block.
**Test Focus:** Error/Exception

### Scenario ID: TS_EXBOT-hedge-sync_012
**Scenario Title:** INV-STOP happy path -- place-before-cancel, no 0-stop window
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 8-9; FR-EXBOT-035; spec.md OQ-EXBOT-002 Closed; AC-10
**Test Type:** Functional
**Description:** After a successful delta adjustment and reconcile, trigger INV-STOP stop replacement. Verify the sequence is strictly: (1) Place new stop order on HL, (2) verifyStopPlaced confirms new stop active, (3) Cancel old stop only after step 2 succeeds. Verify there is no point in time where zero stop orders are active, stop_replacing_started_at is set at start and cleared (NULL) in finally after completion.
**Test Focus:** Happy path

### Scenario ID: TS_EXBOT-hedge-sync_013
**Scenario Title:** INV-STOP place failure -- old stop remains active, partial_repair enqueued
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 8-9; FR-EXBOT-035; spec.md OQ-EXBOT-002 Closed; AC-11
**Test Type:** Functional
**Description:** Simulate the Place new stop call failing (HL rejects the new stop order). Verify: old stop order remains active on HL (not cancelled), partial_repair message enqueued with appropriate reason, Worker does NOT enter SAFE_MODE at this step (SAFE_MODE is only via stop_replacing_started_at overrun or circuit open), stop_replacing_started_at left non-NULL for partial_repair to handle.
**Test Focus:** Error/Exception

### Scenario ID: TS_EXBOT-hedge-sync_014
**Scenario Title:** stop_replacing_started_at overrun > 60s -- SAFE_MODE entry detected by light-check
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §4 A5; FR-EXBOT-033; flows.md F-01 step 12; AC-14
**Test Type:** Functional
**Description:** Simulate stop_replacing_started_at set to a timestamp 61+ seconds before now (overrun). When the light-check worker evaluates the bot (primary detection path, runs <=5 min), verify: bot transitions to bots.lifecycle_state='safe_mode', partial_repair enqueued with reason='stop_replacing_overrun'. Confirm the deep-audit also detects this as a backstop.
**Test Focus:** Error/Exception

### Scenario ID: TS_EXBOT-hedge-sync_015
**Scenario Title:** Partial fill -- reconcile_partial detected, partial_repair enqueued, circuit NOT incremented
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §4 A4; FR-EXBOT-036; spec.md FR-EXBOT-025 AC; AC-09
**Test Type:** Functional
**Description:** Simulate HL partially filling the adjustShortDelta order (actual fill size < requested delta). In the Reconcile Worker step, actual HL position size != expectedAbsSize (exact-fill check, no % tolerance). Verify: rebalance_attempts.status='reconcile_partial', partial_repair message enqueued, incrementCircuitBreaker is NOT called (partial fill does not count as failure), rebalance_attempts.status is not 'failed'.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_016
**Scenario Title:** 3 consecutive HL rejections -- circuit breaker opens
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §6 circuit breaker; FR-EXBOT-040; US-EXBOT-008 AC-1; AC-05
**Test Type:** Data/State
**Description:** Simulate 3 consecutive HL order rejections for the same hedge_leg_id within a 24h rolling window (no intervening success). After the 3rd failure, verify: circuit_breakers.state transitions from 'closed' to 'open', reset_at = now + 1h, subsequent light-check does NOT enqueue a new hedge-sync for this bot while circuit='open'.
**Test Focus:** State transition

### Scenario ID: TS_EXBOT-hedge-sync_017
**Scenario Title:** Circuit transitions to half_open after reset_at -- exactly 1 probe enqueued
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-040; US-EXBOT-008 AC-2; AC-06
**Test Type:** Data/State
**Description:** Set circuit_breakers.state='open', reset_at in the past (elapsed). When light-check evaluates the bot, verify exactly 1 probe hedge-sync message is enqueued (half_open_probe_used=1, atomic -- concurrent light-checks must not produce 2 probes). circuit_breakers.state transitions to 'half_open' during probe evaluation.
**Test Focus:** State transition

### Scenario ID: TS_EXBOT-hedge-sync_018
**Scenario Title:** Probe succeeds -- circuit closes, failure_count reset
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-040; US-EXBOT-008 AC-3; AC-07
**Test Type:** Data/State
**Description:** With circuit='half_open', execute a probe hedge-sync that completes successfully. Verify: circuit_breakers.state transitions to 'closed', failure_count=0, half_open_probe_used reset to 0, normal light-check resumes enqueueing hedge-sync for this bot.
**Test Focus:** State transition

### Scenario ID: TS_EXBOT-hedge-sync_019
**Scenario Title:** Probe fails -- circuit re-opens, admin notified
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-040; US-EXBOT-008 AC-4; AC-08
**Test Type:** Data/State
**Description:** With circuit='half_open', execute a probe hedge-sync that fails (HL rejection). Verify: circuit_breakers.state transitions back to 'open', reset_at=now+1h, admin notification enqueued with message "Circuit re-opened after failed probe for bot {id}".
**Test Focus:** State transition

### Scenario ID: TS_EXBOT-hedge-sync_020
**Scenario Title:** margin_status='warning' -- size-increase operations disabled during hedge-sync
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 4; FR-EXBOT-060; BR-EXBOT-003; AC-13
**Test Type:** Functional
**Description:** Set HL marginSummary to produce marginUsage >= 0.55 (warning threshold). After the Worker fetches marginSummary post-lock-acquire (step 4), verify hedge_legs.margin_status updated to 'warning' and any hedge operation that would increase position size is blocked per BR-EXBOT-003. margin_status in DB reflects the value from this hedge-sync execution.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_021
**Scenario Title:** BVA: marginUsage exactly at 0.55 -- transitions ok to warning
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-060; spec.md margin thresholds
**Test Type:** Data/State
**Description:** Set HL marginSummary to produce marginUsage = exactly 0.55. Verify hedge_legs.margin_status transitions from 'ok' to 'warning'. At 0.5499 (just below) must remain 'ok'; at 0.55 must become 'warning'.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_022
**Scenario Title:** BVA: marginUsage exactly at 0.75 -- transitions warning to critical
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-060; spec.md margin thresholds
**Test Type:** Data/State
**Description:** Set HL marginSummary to produce marginUsage = exactly 0.75. Verify hedge_legs.margin_status transitions from 'warning' to 'critical'. At 0.7499 must remain 'warning'; at 0.75 must become 'critical'. Two consecutive 'critical' readings trigger SAFE_MODE per BR-EXBOT-003.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_023
**Scenario Title:** margin_status='critical' two consecutive readings -- SAFE_MODE entry
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-060; BR-EXBOT-003
**Test Type:** Data/State
**Description:** Simulate two consecutive hedge-sync executions both returning marginUsage >= 0.75 (critical). Verify that on the second critical reading, the bot enters safe_mode (bots.lifecycle_state='safe_mode'), consistent with BR-EXBOT-003. A single critical reading alone must NOT trigger SAFE_MODE.
**Test Focus:** State transition

### Scenario ID: TS_EXBOT-hedge-sync_024
**Scenario Title:** drift_threshold boundary -- deltaErrorUsd exactly at max($25, lpValueUsd * 3%)
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** spec.md FR-EXBOT-025 AC; OQ-EXBOT-011 Closed; AC-15
**Test Type:** Functional
**Description:** For a bot with lpValueUsd = $1000, compute drift_threshold = max($25, $1000 * 3%) = $30. Test: deltaErrorUsd = $30.01 (just above threshold) -- hedge-sync must be enqueued. deltaErrorUsd = $30.00 (exactly at boundary) -- verify behavior per exclusive/inclusive boundary definition. deltaErrorUsd = $29.99 (just below) -- hedge-sync must NOT be enqueued.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_025
**Scenario Title:** drift_threshold uses $25 floor when lpValueUsd * 3% < $25
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** spec.md FR-EXBOT-025 AC; OQ-EXBOT-011 Closed; AC-15
**Test Type:** Functional
**Description:** For a bot with lpValueUsd = $500 (3% = $15 < $25 floor), verify drift_threshold = $25 (floor applies). deltaErrorUsd = $25.01 triggers hedge-sync enqueue; deltaErrorUsd = $24.99 does not.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_026
**Scenario Title:** lpValueUsd formula uses principal only -- tokensOwed excluded
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** spec.md OQ-EXBOT-011 Closed; AC-15
**Test Type:** Functional
**Description:** Configure a bot with lpEthAmount=0.5, uniPoolPrice=2000 USDC/ETH (from Uniswap pool slot0), lpUsdcAmount=500 USDC, and tokensOwed_ETH=0.01 / tokensOwed_USDC=10. Verify lpValueUsd = (0.5 * 2000) + 500 = $1500 -- tokensOwed values excluded entirely from the formula. drift_threshold is computed from $1500.
**Test Focus:** Boundary

### Scenario ID: TS_EXBOT-hedge-sync_027
**Scenario Title:** User Lock heartbeat extend -- hedge-sync work exceeds 30s
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 3; FR-EXBOT-092; AC-13
**Test Type:** Integration
**Description:** Simulate a hedge-sync execution where the HL clearinghouseState fetch + adjustShortDelta takes > 30s but < 90s (TTL). Verify the Worker calls extend(holderToken, ttlMs) on the User Lock before the TTL=90s expires, maintaining lock ownership throughout. Confirm lock is released in the finally block after completion.
**Test Focus:** Integration

### Scenario ID: TS_EXBOT-hedge-sync_028
**Scenario Title:** User Lock TTL expires mid-execution -- next worker acquires and reconciles
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-092; NFR-EXBOT-010
**Test Type:** Integration
**Description:** Simulate Worker 1 holding the User Lock and the lock TTL=90s expiring (no extend called) while Worker 1 is still in HL call. Worker 2 subsequently acquires the lock. Verify: Worker 2 does not duplicate the HL mutation (checks existing rebalance_attempts or reconcile state), hedge_legs eventually reaches a consistent state reflecting the actual HL position.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_EXBOT-hedge-sync_029
**Scenario Title:** Deterministic cloid -- retry with same attemptId produces same cloid, HL deduplicates
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-024; NFR-EXBOT-007; spec.md cloid invariant
**Test Type:** Integration
**Description:** Trigger a hedge-sync for botId=B1, attemptId=A1, stage='hedge'. Compute expected cloid = first128BitsHex(keccak256("bnza:B1:A1:hedge:1")). Submit a retry with identical parameters. Verify: the cloid is identical on both attempts, HL either deduplicates (returns existing fill status) or the reconcile worker detects the duplicate and does not double-apply the position change.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_EXBOT-hedge-sync_030
**Scenario Title:** Two Workers race for same User Lock -- exactly one proceeds, one re-queues
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-092; AC-03
**Test Type:** Integration
**Description:** Simulate two hedge-sync Workers for the same botId attempting to acquire the User Lock simultaneously. Verify exactly one Worker receives acquired=true and proceeds, while the other receives acquired=false and re-queues the message with delay. Confirm no duplicate HL orders result from the concurrent acquisition attempt.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_EXBOT-hedge-sync_031
**Scenario Title:** stateVersion check before circuit recheck -- ordering verified
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 2; flows.md F-02; N4-03 carry-forward
**Test Type:** Functional
**Description:** Enqueue a message with stateVersion mismatch AND circuit_breakers.state='open'. Verify the Worker discards via the stateVersion check first (status='skipped', reason reflects stateVersion discard) and does NOT proceed to circuit recheck. This confirms the ordering: stateVersion check precedes circuit recheck per flows.md F-02.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_032
**Scenario Title:** marginSummary fetch after lock acquire -- margin_status updated before hedge mutation
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 4; FR-EXBOT-060; Q3 Answered 2026-07-14; AC-13
**Test Type:** Integration
**Description:** Verify that within a single hedge-sync execution, the marginSummary fetch happens AFTER lock acquire and BEFORE any HL mutation (adjustShortDelta). The margin_status written to hedge_legs reflects the state observed under the lock (not a pre-lock stale read). Confirm this by observing DB writes ordering: lock acquired -> margin_status updated -> adjustShortDelta submitted.
**Test Focus:** Integration

### Scenario ID: TS_EXBOT-hedge-sync_033
**Scenario Title:** Reconcile verify exact fill -- actual matches expected, hedge_legs updated
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 11-15; FR-EXBOT-025; AC-01
**Test Type:** Integration
**Description:** After adjustShortDelta is confirmed by HL, the Reconcile Worker fetches the actual HL position. Verify: actual position size = expectedAbsSize (exact, no % tolerance), entry_price/liq_price/effective_leverage extracted from clearinghouseState, stop_trigger_px recomputed with BigDecimal, hedge_legs updated with all new values, bot_runtime_state.last_known_hl_short_size updated, rebalance_attempts.status='success'.
**Test Focus:** Integration

### Scenario ID: TS_EXBOT-hedge-sync_034
**Scenario Title:** Reconcile mismatch -- actual != expected (exact-fill violation), reconcile_partial triggered
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §4 A4; FR-EXBOT-025/036; AC-09
**Test Type:** Integration
**Description:** Simulate Reconcile Worker fetching an actual HL position size that differs from expectedAbsSize by any non-zero amount (even 0.000001 ETH). Verify: rebalance_attempts.status='reconcile_partial', partial_repair message enqueued with remaining delta, incrementCircuitBreaker NOT called. The system does not accept a "close enough" match.
**Test Focus:** Integration

### Scenario ID: TS_EXBOT-hedge-sync_035
**Scenario Title:** rebalance_attempts row exists for every execution outcome
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-025; uc-hedge-sync.md postconditions; spec.md §5 audit logging
**Test Type:** Integration
**Description:** Execute hedge-sync for each of the following outcomes: success, skipped (stateVersion), skipped (circuit open), failed (HL rejection), reconcile_partial. Verify a rebalance_attempts row exists in the DB for every outcome with the correct status value. No execution must complete without a corresponding audit row.
**Test Focus:** Integration

### Scenario ID: TS_EXBOT-hedge-sync_036
**Scenario Title:** queue_idempotency.state transitions started -> succeeded through full flow
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 1, step 16; FR-EXBOT-011
**Test Type:** Data/State
**Description:** Execute a full happy-path hedge-sync. Verify queue_idempotency row state machine: INSERT with state='started' at step 1, UPDATE to state='succeeded' at step 16 after reconcile completes. Confirm no intermediate state leaves the row in 'started' permanently.
**Test Focus:** State transition

### Scenario ID: TS_EXBOT-hedge-sync_037
**Scenario Title:** delta-only invariant -- adjustShortDelta never sends full-close followed by full-reopen
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-022; BR-EXBOT-004
**Test Type:** Functional
**Description:** For any non-zero delta value, verify the HL payload submitted is an adjustShortDelta (signed delta amount) -- not a sequence of close-all + open-new. Monitor the HL API call log and confirm a single delta order is submitted, not two orders (close then open). This tests the BR-EXBOT-004 invariant.
**Test Focus:** Happy path

### Scenario ID: TS_EXBOT-hedge-sync_038
**Scenario Title:** User Lock holderToken mismatch on release -- no-op, lock not released by wrong holder
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-092; spec.md Lua script ownership check
**Test Type:** Integration
**Description:** Attempt to release the User Lock with a holderToken that does not match the token that acquired the lock (simulating a scenario where TTL expired and another worker took over). Verify the release is a no-op (Lua script ownership check prevents invalid release), and the current lock holder is not affected.
**Test Focus:** Integration

### Scenario ID: TS_EXBOT-hedge-sync_039
**Scenario Title:** E2E drift cycle -- light-check detects drift, hedge-sync adjusts, reconcile confirms
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FLOW-002; FR-EXBOT-025; FR-EXBOT-035; AC-01
**Test Type:** End-to-End
**Description:** Simulate a full drift-to-resolved cycle: (1) LP position drifts such that deltaErrorUsd > drift_threshold, (2) light-check enqueues hedge-sync, (3) hedge-sync Worker executes delta adjustment, (4) Reconcile Worker confirms exact fill, (5) INV-STOP replaces stop, (6) hedge_legs.stop_price/entry_price updated, (7) next light-check finds deltaErrorUsd <= threshold and does NOT enqueue again. Verify end-state: hedge_legs consistent with actual HL position, stop active, rebalance_attempts.status='success'.
**Test Focus:** Happy path

### Scenario ID: TS_EXBOT-hedge-sync_040
**Scenario Title:** E2E partial fill cycle -- partial fill triggers repair, repair reconciles to full target
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** FLOW-002; FR-EXBOT-036; UC A4
**Test Type:** End-to-End
**Description:** Simulate a hedge-sync where HL partially fills the delta. Reconcile Worker detects partial fill. partial_repair Worker fetches remaining delta, submits a new adjustShortDelta with a new cloid, Reconcile Worker confirms full fill. Verify end-state: hedge_legs matches full target size, rebalance_attempts has one 'reconcile_partial' row and one 'success' row (from repair), no SAFE_MODE entry.
**Test Focus:** Alternative flow

### Scenario ID: TS_EXBOT-hedge-sync_041
**Scenario Title:** Acceptance verification -- AC-01 through AC-17 boundary completeness check
**UC Reference:** UC-EXBOT-hedge-sync -- Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §8; US-EXBOT-006 AC-1..4; US-EXBOT-008 AC-1..4
**Test Type:** Acceptance
**Description:** Execute a structured test run covering each AC from §8 of the v5 audit report (AC-01 through AC-17). Verify each acceptance criterion produces the documented expected result. Pay particular attention to AC-12 (no_op_dust), AC-10/AC-11 (INV-STOP sequence), AC-14 (overrun SAFE_MODE), and AC-15 (drift_threshold formula) -- these are newly testable in v5. Report per-AC pass/fail.
**Test Focus:** Happy path

---

## Appendix: Coverage Matrix Summary

| Coverage Area | Scenarios | Status |
|---|---|---|
| Happy path (main 16-step flow) | TS_001, TS_037 | Covered |
| Alt flow A1 (lock not acquired) | TS_005 | Covered |
| Alt flow A2 (stateVersion mismatch) | TS_003 | Covered |
| Alt flow A3 (HL rejection + circuit) | TS_010, TS_016 | Covered |
| Alt flow A4 (partial fill) | TS_015, TS_034, TS_040 | Covered |
| Alt flow A5 (stop overrun SAFE_MODE) | TS_014 | Covered |
| Alt flow A6 (no_op_dust delta=0) | TS_006 | Covered |
| Circuit breaker state machine (4 valid transitions) | TS_016, TS_017, TS_018, TS_019 | Covered |
| Circuit invalid transition (enqueue while open) | TS_004 | Covered |
| INV-STOP happy path | TS_012 | Covered |
| INV-STOP place failure | TS_013 | Covered |
| stateVersion ordering vs circuit check | TS_031 | Covered |
| marginSummary post-lock ordering | TS_032 | Covered |
| margin_status transitions (ok/warning/critical) | TS_020, TS_021, TS_022, TS_023 | Covered |
| BVA: no_op_dust boundary (3 points) | TS_007, TS_008 | Covered |
| BVA: drift_threshold (3 points + floor) | TS_024, TS_025, TS_026 | Covered |
| BigDecimal precision | TS_009 | Covered |
| Idempotency: duplicate delivery | TS_002 | Covered |
| Idempotency: deterministic cloid | TS_029 | Covered |
| Concurrency: lock contention | TS_030 | Covered |
| Lock TTL expiry | TS_028 | Covered |
| Lock heartbeat extend | TS_027 | Covered |
| Lock holderToken mismatch | TS_038 | Covered |
| Reconcile: exact fill + hedge_legs update | TS_033 | Covered |
| Reconcile: partial mismatch | TS_034 | Covered |
| rebalance_attempts audit row all outcomes | TS_035 | Covered |
| queue_idempotency state machine | TS_036 | Covered |
| delta-only invariant | TS_037 | Covered |
| E2E drift cycle | TS_039 | Covered |
| E2E partial fill repair cycle | TS_040 | Covered |
| Acceptance criteria sweep (AC-01..17) | TS_041 | Covered |
| Performance / load testing | N/A | Out-of-scope |
| Key material exposure (NFR-EXBOT-006) | N/A | Out-of-scope |

---

## Warning: Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Performance: hedge-sync <= 30s SLA (NFR-EXBOT-002) | NFR: PERFORMANCE -- load testing is out of scope for functional scenario design | Defer to performance test phase; verify SLA via monitoring (CloudWatch) in integration tests |
| Throughput: 800 wt/min rate limit under concurrent bots (NFR-EXBOT-004) | NFR: LOAD -- requires multi-bot concurrent load | Defer to load testing phase |
| Private key material not in logs/DB/memory (NFR-EXBOT-006) | NFR: SECURITY -- requires security audit tooling and log inspection frameworks | Defer to security review; KMS audit trail verification outside functional test scope |
| Rate-limit weight consumed before or after lock (Q4 Deferred, OQ-EXBOT-015) | BLOCKED: OQ-EXBOT-015 open -- rate-limit vs lock ordering not yet confirmed | Resolve via BA/Tech Lead; add scenario when OQ-EXBOT-015 is closed |

