# Test Cases — UC-EXBOT-hedge-sync Execute Delta-Only Hedge Adjustment

**Total test cases:** 57 (FUNC: 37, INTG: 16, NFR: 4)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** UC-EXBOT-hedge-sync_hedge-sync_audited_20260630_v1.md
**Source scenarios:** UC-EXBOT-hedge-sync_hedge-sync_scenarios_20260701_v1.md
**Output language:** English

## Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Happy path — delta adjustment + reconcile end-to-end | TC_013, TC_034, TC_035, TC_036 | Covered |
| AC-02 | stateVersion mismatch — discard, no HL order | TC_004, TC_010 | Covered |
| AC-03 | Lock held — re-queue, no HL order | TC_006, TC_011 | Covered |
| AC-04 | HL order rejection — circuit increment | TC_019, TC_043 | Covered |
| AC-05 | Circuit opens after 3 consecutive failures | TC_043, TC_044 | Covered |
| AC-06 | Circuit transitions to half_open at reset_at | TC_046 | Covered |
| AC-07 | Half_open probe success — circuit closes | TC_047 | Covered |
| AC-08 | Half_open probe failure — circuit reopens | TC_048 | Covered |
| AC-09 (inferred) | Half_open probe: exactly 1 allowed | TC_049 | Covered |
| AC-10 (inferred) | Partial fill → partial_repair enqueued | TC_037 | Covered |
| AC-11 (inferred) | delta=0 — no HL order, proceed to stop replacement | TC_015 | Covered (pending OQ-EXBOT-013) |
| AC-12 (inferred) | KMS signing failure → SAFE_MODE | TC_023 | Covered |

---

## I. Operation: Hedge-sync preflight (idempotency, stateVersion, lock)

### I.1. Functional verification — Operation: Hedge-sync preflight (idempotency, stateVersion, lock)

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_001 | Verify a new hedge-sync message is accepted when its message_id has not been seen before | 1. Bot running (`bots.status='active'`, `lifecycle_state='active'`).\n2. `queue_idempotency` has no row for the incoming `message_id`. | 1. Deliver a `hedge-sync` message whose `message_id` does not exist in `queue_idempotency`. | 1. A new row is inserted in `queue_idempotency` with `state='started'`; worker proceeds past the dedup check to the stateVersion check. No early exit. (Ref: FR-EXBOT-011.) | P0 |
| TC_002 | Verify delivering the same hedge-sync message twice causes the second delivery to exit immediately | 1. A `hedge-sync` message was already processed; its `message_id` exists in `queue_idempotency`. | 1. Deliver the exact same `hedge-sync` message a second time with the same `message_id`. | 1. Second delivery hits UNIQUE constraint conflict on `queue_idempotency.message_id` and returns immediately. No HL order placed, no new `rebalance_attempts` row created. Existing row unchanged. (Ref: FR-EXBOT-011, NFR-EXBOT-007.) | P0 |
| TC_003 | Verify the worker proceeds when the message stateVersion matches the current bot state | 1. Bot running.\n2. `bot_runtime_state.state_version` in D1 matches `stateVersion` in the incoming message. | 1. Deliver a `hedge-sync` message whose `stateVersion` equals current `bot_runtime_state.state_version`. | 1. stateVersion check passes; worker proceeds to acquire `UserLockDO`. No discard or skip. (Ref: FR-EXBOT-027.) | P0 |
| TC_004 | Verify a stale hedge-sync message is discarded without sending any HL order | 1. Bot running.\n2. Queued `hedge-sync` message has `stateVersion` lower than current `bot_runtime_state.state_version`. | 1. Deliver the out-of-date `hedge-sync` message. | 1. Worker discards the message, records `rebalance_attempts.status='skipped'`, sends no order to Hyperliquid. No lock acquired. (Ref: FR-EXBOT-027, AC-02.) | P0 |
| TC_005 | Verify the worker acquires the user lock and proceeds when the lock is free | 1. Bot running; stateVersion and idempotency checks pass.\n2. No other worker holds the `UserLockDO` lease for this user. | 1. Process the `hedge-sync` message when the lock is available. | 1. `UserLockDO.acquire(holderToken, ttl=90s, idempotencyKey='hedge-sync:{botId}:{stateVersion}')` returns `acquired=true`; worker proceeds to fetch actual HL position. (Ref: FR-EXBOT-026, FR-EXBOT-092.) | P0 |
| TC_006 | Verify the worker re-queues with a delay and takes no action when the lock is held by another worker | 1. Bot running; stateVersion and idempotency checks pass.\n2. Another worker holds the `UserLockDO` lease. | 1. Process the `hedge-sync` message while lock is held by another worker. | 1. `UserLockDO.acquire` returns `acquired=false` with `currentHolderExpiresAt`; worker re-queues with a delay and exits. No HL order placed. No `rebalance_attempts` row for this attempt. (Ref: FR-EXBOT-026, AC-03.) | P0 |
| TC_007 | Verify a size-increase delta adjustment is blocked when the margin is in warning state | 1. Bot running with lock acquired.\n2. `hedge_legs.margin_status='warning'` in D1.\n3. Computed delta is positive (size increase). | 1. Process the `hedge-sync` message when margin is warning and delta is positive. | 1. Worker blocks the size-increase order; only reduce-only adjustments allowed. Attempt recorded as blocked/skipped with margin reason. No size-increase order sent to Hyperliquid. (Ref: FR-EXBOT-060, FR-EXBOT-021.) | P1 |
| TC_008 | Verify both increase and reduce adjustments are allowed when the margin is in OK state | 1. Bot running with lock acquired.\n2. `hedge_legs.margin_status='ok'` in D1. | 1. Process a `hedge-sync` message with a positive delta (size increase) when margin status is OK. | 1. Size-increase delta order is not blocked by margin check; worker proceeds to call `adjustShortDelta`. (Ref: FR-EXBOT-060.) | P1 |

### I.2. Integration & State verification — Operation: Hedge-sync preflight (idempotency, stateVersion, lock)

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_009 | Verify that two concurrent deliveries of the same message result in exactly one execution | 1. Bot running.\n2. Two workers receive the same `hedge-sync` message (same `message_id`) at the same time. | 1. Deliver the same `hedge-sync` message to two workers simultaneously. | 1. UNIQUE constraint on `queue_idempotency.message_id` ensures exactly one worker proceeds; the other gets conflict and exits. Only one HL order placed and one `rebalance_attempts` row exists. (Ref: FR-EXBOT-011.) | P0 |
| TC_010 | Verify the exact stateVersion boundary — a message matching the current version proceeds; one lower is discarded | 1. Bot running with known current `bot_runtime_state.state_version`. | 1. Deliver a `hedge-sync` message with `stateVersion` equal to current D1 value (exact match).\n2. Deliver a second message with `stateVersion` one less than current. | 1. Step 1: message proceeds.\n2. Step 2: message discarded (`rebalance_attempts.status='skipped'`), no HL order. Lower-than-current means discard. (Ref: FR-EXBOT-027, AC-02.) | P0 |
| TC_011 | Verify the UserLockDO lease auto-releases if the worker holds it longer than the TTL without heartbeat | 1. Worker acquired `UserLockDO` lease (TTL=90s).\n2. Worker does not call `heartbeat()` before TTL expires. | 1. Let TTL expire without heartbeat.\n2. Second worker tries to acquire the lock. | 1. After TTL expiry, lease auto-released; second worker acquires it (`acquired=true`).\n2. Second worker reconciles actual HL state before any new order. (Ref: FR-EXBOT-026, FR-EXBOT-092.) | P1 |
| TC_012 | Verify the UserLockDO returns a cached result for the same idempotency key within the same state version | 1. Worker already processed hedge-sync for `{botId, stateVersion}` and released lock.\n2. Same `idempotencyKey='hedge-sync:{botId}:{stateVersion}'` as prior run. | 1. Second worker attempts to acquire the lock with the same `idempotencyKey`. | 1. DO returns cached result from previous run without re-running mutation; second worker does not re-submit HL order. (Ref: FR-EXBOT-026, FR-EXBOT-092.) | P1 |

---

## II. Operation: Hedge-sync delta computation and HL order

### II.1. Functional verification — Operation: Hedge-sync delta computation and HL order

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_013 | Verify hedge-sync only sends the difference when the short position needs to increase | 1. Bot running with lock acquired.\n2. Target short size is larger than actual short size (positive delta, at or above drift threshold). | 1. Process `hedge-sync` message with a positive computed delta. | 1. Only one `adjustShortDelta(delta, cloid)` call with the positive difference — bot does NOT close full position and reopen. Reconcile confirms new actual size matches target. `rebalance_attempts.status='success'` written only after reconcile confirms. (Ref: FR-EXBOT-022, BR-EXBOT-004, AC-01.) | P0 |
| TC_014 | Verify hedge-sync sends a reduce-only adjustment when the short position needs to decrease | 1. Bot running with lock acquired.\n2. Target short size is smaller than actual (negative delta, reduce-only). | 1. Process `hedge-sync` message with a negative computed delta. | 1. `adjustShortDelta` called with negative delta (reduce-only); order reduces short by exact difference. Reconcile confirms new size. `rebalance_attempts.status='success'` recorded. (Ref: FR-EXBOT-022, FR-EXBOT-025.) | P0 |
| TC_015 | Verify no HL order is placed when the computed delta is zero | 1. Bot running with lock acquired.\n2. Target short size equals actual short size (delta=0 after BigDecimal computation). | 1. Process `hedge-sync` message when delta computes to zero. | 1. No `adjustShortDelta` call made. Worker proceeds to stop replacement step (INV-STOP protocol). `rebalance_attempts` row written with `reason='delta_zero'`. `queue_idempotency.state='succeeded'`. (Note: exact behavior pending OQ-EXBOT-013; update when Q1 resolved.) (Ref: FR-EXBOT-022, UC §A6.) | P1 |
| TC_016 | Verify the target ratio normalizer converts a decimal string to the correct BigInt basis points | 1. Hedge ratio stored as decimal string (e.g., `"0.70"`) in bot config. | 1. Call `normalizeTargetRatioBps("0.70")` during delta computation. | 1. Returns `7000n` (BigInt), not `7000` (Number) or `6999.9999…` from float rounding. No `Number()` intermediate used. (Ref: FR-EXBOT-021, NFR-EXBOT-008.) | P0 |
| TC_017 | Verify the delta calculation uses BigDecimal throughout with no float arithmetic | 1. Bot running with `targetShortEth` and `actualShortEth` stored as TEXT BigDecimal strings in D1. | 1. Compute `delta = targetShortEth - actualShortEth` using the delta computation function. | 1. Result is a BigDecimal value with full precision. No `Number()` cast or JS float arithmetic at any step. (Ref: NFR-EXBOT-008, FR-EXBOT-021.) | P0 |
| TC_018 | Verify the order id for the same attempt is always the same regardless of how many times it is computed | 1. Specific set of `{botId, attemptId, stage, version}` inputs known. | 1. Compute `cloid` for the same `{botId, attemptId, stage, version}` twice in separate calls. | 1. Both calls return the same `cloid` value (`first128BitsHex(keccak256('bnza:{botId}:{attemptId}:{stage}:{version}'))`). Changing any input field produces a different `cloid`. (Ref: FR-EXBOT-024.) | P0 |
| TC_019 | Verify an HL order rejection increments the circuit breaker failure count and returns the correct error | 1. Bot running with lock acquired, positive delta computed.\n2. Hyperliquid (mocked) rejects the `adjustShortDelta` call (insufficient margin). | 1. Process `hedge-sync` when HL rejects the order. | 1. `rebalance_attempts.status='failed'` recorded. `incrementCircuitBreaker` called once. Error `E-EXBOT-007` returned. Lock released in `finally` block. (Ref: FR-EXBOT-040, E-EXBOT-007, AC-04.) | P0 |
| TC_020 | Verify the delta is computed and the order is placed correctly at the exact drift threshold boundary | 1. Bot running with lock acquired.\n2. Difference between target and actual short size is exactly at the drift threshold. | 1. Process `hedge-sync` when delta is at exact drift threshold. | 1. Order placed for the exact threshold amount (not rounded down, not skipped). Reconcile confirms new actual size matches expected. (Ref: FR-EXBOT-022, OQ-EXBOT-004 — threshold value pending.) | P1 |

### II.2. Integration & State verification — Operation: Hedge-sync delta computation and HL order

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_021 | Verify the worker checks with the HL rate limiter before calling Hyperliquid, and waits when told to | 1. Bot running with lock acquired. | 1. Process `hedge-sync` when `HLRateLimitDO` returns `{allowed: true}` (normal case).\n2. In separate test: process when `HLRateLimitDO` returns `{allowed: false, retryAfterMs: <delay>}`. | 1. Step 1: worker calls Hyperliquid normally.\n2. Step 2: worker does NOT call Hyperliquid; re-queues with specified delay and exits. (Ref: FR-EXBOT-091, NFR-EXBOT-004.) | P0 |
| TC_022 | Verify the bot enters safe mode when Hyperliquid is unreachable for longer than the grace period | 1. Bot running with lock acquired.\n2. Hyperliquid (mocked) returns connection errors for all calls. | 1. Process `hedge-sync` when HL has been unreachable past the grace period. | 1. Bot enters safe mode (`lifecycle_state='safe_mode'`, `bots.status='safe_mode'`). Error `E-EXBOT-008` logged. No HL order placed. (Grace period ≈ 5 minutes.) (Ref: FR-EXBOT-050, E-EXBOT-008.) | P0 |
| TC_023 | Verify the bot enters safe mode when the signing service fails to sign the HL order | 1. Bot running with lock acquired, delta ready to send.\n2. KMS Signing Lambda set to fail during signing step. | 1. Process `hedge-sync` when signing service returns error. | 1. No HL order submitted. Bot enters safe mode (`lifecycle_state='safe_mode'`). Admin notified. No raw key material in any log. (Ref: FR-EXBOT-080, AC-12.) | P0 |
| TC_024 | Verify a duplicate cloid is detected and reconciled before any retry, not blindly resubmitted | 1. A `hedge-sync` attempt already sent an order with specific `cloid`; outcome unknown (timeout or partial response). | 1. Retry the same `hedge-sync` attempt (same `{botId, attemptId, stage, version}`), producing the same `cloid`. | 1. Worker detects duplicate `cloid`, fetches actual HL position to reconcile, proceeds based on confirmed actual state — does NOT blindly submit a second order with same `cloid`. (Ref: FR-EXBOT-024.) | P0 |

### II.3. Non-functional (logic) verification — Operation: Hedge-sync delta computation and HL order

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_025 | Verify the stop trigger price is computed with full BigDecimal precision at large decimal values | 1. `entry_price`, `liq_price`, and `stopSafetyFactor` available as BigDecimal strings. | 1. Compute `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)` using the stop-price function. | 1. Result has full decimal precision — no intermediate `Number()` cast, no rounding loss. Formula output matches expected BigDecimal value. (Ref: NFR-EXBOT-008, FR-EXBOT-030.) | P0 |
| TC_026 | Verify hedge-sync does not open more than six outbound connections in a single worker invocation | 1. Bot running; full hedge-sync cycle about to execute (HL fetch, order, reconcile, DO calls). | 1. Monitor outbound connection count during one full hedge-sync invocation. | 1. Total simultaneous outbound connections from worker is at most 6. (Ref: NFR-EXBOT-011.) | P2 |

---

## III. Operation: INV-STOP protocol (stop replacement)

### III.1. Functional verification — Operation: INV-STOP protocol (stop replacement)

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_027 | Verify stop_replacing_started_at is set in D1 before the critical stop-replacement section begins | 1. Bot running; hedge adjustment completed (or delta=0, proceeding directly to stop replacement).\n2. `hedge_legs.stop_replacing_started_at` is NULL. | 1. Begin the INV-STOP protocol to replace the stop on Hyperliquid. | 1. Before any cancel or place call to HL, `hedge_legs.stop_replacing_started_at` is written to the current timestamp in D1. Field is not NULL during the critical section. (Ref: FR-EXBOT-035.) | P0 |
| TC_028 | Verify stop_replacing_started_at is cleared after the stop replacement succeeds | 1. INV-STOP protocol in progress; `stop_replacing_started_at` is set.\n2. Both cancel and place HL calls succeed. | 1. Complete the INV-STOP stop-replacement sequence successfully. | 1. After stop is placed and confirmed, `hedge_legs.stop_replacing_started_at` set to NULL in `finally` block. Field must be NULL regardless of whether hedge-sync overall succeeds. (Ref: FR-EXBOT-035.) | P0 |
| TC_029 | Verify stop_replacing_started_at is cleared even when stop replacement fails midway | 1. INV-STOP protocol in progress; `stop_replacing_started_at` is set.\n2. HL cancel or place call fails (mocked to return error). | 1. Let INV-STOP stop-replacement sequence fail at the HL call step. | 1. Even though stop-replacement failed, `hedge_legs.stop_replacing_started_at` cleared to NULL in `finally` block. No half-completed state left. (Ref: FR-EXBOT-035.) | P0 |
| TC_030 | Verify the new stop is placed with the correct trigger price and as reduce-only | 1. INV-STOP protocol has cancelled old stop and is ready to place new one.\n2. New `stop_trigger_px` computed from latest `entry_price`, `liq_price`, and `stopSafetyFactor`. | 1. Execute `placeReduceOnlyStopMarket` call as part of INV-STOP. | 1. New stop placed on HL as reduce-only stop-market order with BigDecimal `stop_trigger_px`. New `stop_cloid` and `stop_price` written to `hedge_legs`. (Ref: FR-EXBOT-035, FR-EXBOT-030.) | P0 |
| TC_031 | Verify the bot enters safe mode when stop_replacing_started_at is stuck for too long | 1. Previous hedge-sync run set `hedge_legs.stop_replacing_started_at` but crashed before clearing it.\n2. Field has remained set longer than the stuck threshold. | 1. Light-check worker runs while `stop_replacing_started_at` is stuck beyond the threshold. | 1. Light-check detects stuck flag and triggers bot to enter safe mode (`lifecycle_state='safe_mode'`). (Threshold ≈ 60 seconds.) (Ref: FR-EXBOT-033, FR-EXBOT-035.) | P0 |

### III.2. Integration & State verification — Operation: INV-STOP protocol (stop replacement)

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_032 | Verify that stop replacement always uses the INV-STOP protocol and not a direct cancel-then-place sequence | 1. Hedge-sync run needs to replace stop after delta adjustment. | 1. Observe exact sequence of HL calls made during stop-replacement step. | 1. Stop replacement follows protected INV-STOP sequence (FR-EXBOT-035 / SPEC §19.5). Direct `cancelStop` followed immediately by `placeStop` outside protected protocol is forbidden. `stop_replacing_started_at` set before any HL call. (Note: exact sequence — place-before-cancel or cancel-before-place — pending OQ-EXBOT-002.) (Ref: FR-EXBOT-035, Q2/OQ-EXBOT-002.) | P0 |
| TC_033 | Verify the new stop trigger price is recomputed from the latest entry and liquidation prices after reconcile | 1. Reconcile step has returned latest `entry_price`, `liq_price`, and `effective_leverage` from HL. | 1. Compute new `stop_trigger_px` as part of INV-STOP stop-placement step. | 1. `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)` computed with BigDecimal, where `liq_distance_pct = (liq_price - entry_price) / entry_price` using HL-provided `liq_price` (fallback: `1/effective_leverage` only when `liq_price` absent). No float intermediate. (Ref: FR-EXBOT-030, NFR-EXBOT-008.) | P0 |

---

## IV. Operation: Reconcile and D1 update

### IV.1. Functional verification — Operation: Reconcile and D1 update

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_034 | Verify that a successful reconcile updates all hedge leg fields and marks the attempt as succeeded | 1. Hedge-sync delta order submitted; reconcile worker fetched actual HL position.\n2. Actual short size matches expected size within tolerance. | 1. Let reconcile worker run and confirm position matches expected size. | 1. `hedge_legs` updated with new `entry_price`, `liq_price`, `effective_leverage`, `stop_price`, `stop_cloid`. `bot_runtime_state.last_known_hl_short_size` set to reconciled size. `rebalance_attempts` row inserted with `status='success'`. `queue_idempotency.state='succeeded'`. (Ref: FR-EXBOT-025, AC-01.) | P0 |
| TC_035 | Verify the attempt is only marked successful after reconcile confirms the position, not before | 1. Hedge-sync delta order has been placed.\n2. Reconcile step has not yet run. | 1. Check `rebalance_attempts` state immediately after order is placed (before reconcile confirms). | 1. No `rebalance_attempts` row with `status='success'` exists before reconcile confirms. Success row written only after actual HL position verified. (Ref: FR-EXBOT-025.) | P0 |
| TC_036 | Verify the bot's last known HL short size is updated to the value confirmed by reconcile | 1. Reconcile completed successfully and confirmed a new short size. | 1. Read `bot_runtime_state.last_known_hl_short_size` after successful reconcile. | 1. Value equals reconciled actual short size from HL `clearinghouseState` response — not the expected size, not a locally computed value. (Ref: FR-EXBOT-025.) | P0 |
| TC_037 | Verify a partial fill detection causes a repair message to be queued and the attempt is marked partial | 1. Reconcile worker fetched actual HL position.\n2. Actual short size differs from expected by more than drift threshold (partial fill). | 1. Let reconcile worker detect a partial fill mismatch. | 1. `partial_repair` message enqueued with `{botId, attemptId, reason='partial_fill'}`. `rebalance_attempts.status='partial'` recorded. No `success` row written. (Ref: FR-EXBOT-036, AC-10.) | P0 |
| TC_038 | Verify three consecutive partial repair failures trigger a bot safe close | 1. `partial_repair` queue has processed and failed for the same bot three consecutive times. | 1. Let the third partial repair attempt fail. | 1. `close_operations` row created with `trigger_reason='partial_repair_exhausted'`; UNIQUE constraint prevents double-creation. Bot transitions to close flow (`lifecycle_state='lp_closing'` or similar). (Ref: FR-EXBOT-036, FR-EXBOT-072.) | P0 |
| TC_039 | Verify the reconcile handles a zero actual position without crashing or writing incorrect state | 1. Reconcile worker fetched actual HL position and found it is zero (unexpected). | 1. Run reconcile step when HL position returns size=0. | 1. Mismatch between expected non-zero size and zero actual size detected. `partial_repair` message enqueued or bot enters safe recovery path. `rebalance_attempts.status` set to non-success value. No success row written. (Ref: FR-EXBOT-025, FR-EXBOT-036.) | P1 |

### IV.2. Integration & State verification — Operation: Reconcile and D1 update

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_040 | Verify all hedge leg fields are written atomically in a single D1 operation after reconcile | 1. Successful reconcile has returned new position data from HL. | 1. Observe D1 write for `hedge_legs` after successful reconcile. | 1. All fields (`entry_price`, `liq_price`, `effective_leverage`, `stop_price`, `stop_cloid`) written in a single D1 update — not separate individual writes. No partial update state visible. (Ref: FR-EXBOT-025, ERD.) | P0 |
| TC_041 | Verify queue_idempotency state is updated to succeeded only after the full pipeline finishes | 1. Hedge-sync message fully processed through pipeline (preflight, order, reconcile, D1 update). | 1. Check `queue_idempotency.state` at the very end of the pipeline. | 1. `queue_idempotency.state='succeeded'` written only after all D1 updates (`hedge_legs`, `bot_runtime_state`, `rebalance_attempts`) completed. Not set prematurely. (Ref: FR-EXBOT-011.) | P0 |
| TC_042 | Verify the bot state version is incremented after a successful rebalance, causing any older messages to be discarded | 1. Hedge-sync completed successfully; `bot_runtime_state.state_version` incremented.\n2. Older `hedge-sync` message with previous `stateVersion` still in queue. | 1. Deliver the older message after the state version has incremented. | 1. Older message discarded (stateVersion mismatch), no HL order placed. D1 state version reflects only the latest completed rebalance. (Ref: FR-EXBOT-027.) | P0 |


---

## V. Operation: Circuit breaker management

### V.1. Functional verification — Operation: Circuit breaker management

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_043 | Verify the circuit breaker opens after three consecutive HL order failures within 24 hours | 1. Circuit breaker closed (`circuit_breakers.state='closed'`).\n2. Two previous failures already recorded within last 24 hours (`failure_count=2`). | 1. Process a `hedge-sync` message that fails at HL order step (third failure in 24h window). | 1. `circuit_breakers.state` changes from `closed` to `open`, `reset_at = now + 1h`. Light-check no longer enqueues `hedge-sync` for this bot. Stop monitoring continues. (Ref: FR-EXBOT-040, AC-05.) | P0 |
| TC_044 | Verify the circuit does not open when failures are not consecutive within the rolling 24h window | 1. Circuit breaker closed.\n2. Two previous failures in 24h window, but a success occurred between them (resetting consecutive count). | 1. Process a `hedge-sync` message that fails. | 1. `circuit_breakers.state` stays `closed`; `failure_count` increments but does not reach open threshold because intervening success broke the consecutive run. (Ref: FR-EXBOT-040, AC-05.) | P1 |
| TC_045 | Verify stop monitoring continues when the circuit is open but hedge-sync is suppressed | 1. Circuit breaker open (`circuit_breakers.state='open'`).\n2. Bot's mark price is at or above stop price (stop-crossing condition). | 1. Run light-check for this bot while circuit is open. | 1. Light-check does NOT enqueue `hedge-sync` message (suppressed by open circuit). Light-check DOES enqueue `price-near-stop-audit` because stop monitoring is never suppressed. (Ref: FR-EXBOT-012, FR-EXBOT-014.) | P0 |
| TC_046 | Verify the circuit transitions to half_open when the reset timer expires | 1. Circuit breaker open (`circuit_breakers.state='open'`).\n2. `reset_at` time reached.\n3. `half_open_probe_used=0`. | 1. Run light-check after `reset_at` has passed. | 1. Exactly one `hedge-sync` probe message enqueued; `half_open_probe_used` set to 1; circuit transitions to `half_open`. No more than one probe allowed. (Ref: FR-EXBOT-040, AC-06.) | P0 |
| TC_047 | Verify a successful half_open probe closes the circuit and resets the failure count | 1. Circuit breaker in `half_open` state.\n2. One probe `hedge-sync` message in flight. | 1. Process probe hedge-sync message and let it succeed (HL order succeeds, reconcile confirms). | 1. `circuit_breakers.state` changes from `half_open` to `closed`, `failure_count=0`. Normal hedge-sync resumes at next light-check cycle. (Ref: FR-EXBOT-040, AC-07.) | P0 |
| TC_048 | Verify a failed half_open probe reopens the circuit with a new reset timer | 1. Circuit breaker in `half_open` state.\n2. One probe `hedge-sync` message in flight. | 1. Process probe hedge-sync message and let it fail (HL order fails). | 1. `circuit_breakers.state` changes from `half_open` back to `open`, `reset_at` extended by 1 hour. Admin notification sent. (Ref: FR-EXBOT-040, AC-08.) | P0 |

### V.2. Integration & State verification — Operation: Circuit breaker management

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_049 | Verify a second probe attempt while in half_open is blocked atomically | 1. Circuit breaker in `half_open` state; one probe already claimed (`half_open_probe_used=1`). | 1. Attempt to enqueue a second `hedge-sync` probe for the same bot. | 1. Second probe blocked because `half_open_probe_used` is already 1. Atomic 0→1 claim ensures exactly one probe. (Ref: FR-EXBOT-040.) | P0 |
| TC_050 | Verify the circuit breaker state change is visible to light-check at the next tick without cache delay | 1. Hedge-sync failure just opened circuit breaker (`state='open'`). | 1. Run the next light-check tick for the same bot immediately after circuit opens. | 1. Light-check reads updated `circuit_breakers.state='open'` from D1 and does not enqueue new `hedge-sync`. State change not served from stale cache. (Ref: FR-EXBOT-012, FR-EXBOT-040.) | P0 |
| TC_051 | Verify the failure count is not double-incremented when the same failed message is redelivered | 1. A `hedge-sync` message processed and failed, incrementing `failure_count` once. | 1. Redeliver the same failed `hedge-sync` message (same `message_id`). | 1. Redelivery caught by idempotency check (`queue_idempotency` UNIQUE conflict) before `incrementCircuitBreaker` called; `failure_count` not incremented a second time. (Ref: FR-EXBOT-011, FR-EXBOT-040.) | P0 |


---

## VI. Operation: SAFE_MODE entry and recovery from hedge-sync

### VI.1. Functional verification — Operation: SAFE_MODE entry and recovery from hedge-sync

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_052 | Verify the bot enters safe mode when Hyperliquid remains unreachable past the grace period | 1. Bot running (`lifecycle_state='active'`).\n2. Hyperliquid unreachable (all HL API calls fail) for longer than grace period. | 1. Attempt hedge-sync while HL remains unreachable past the grace period. | 1. `lifecycle_state` changes to `safe_mode`, `bots.status='safe_mode'`. Error `E-EXBOT-008` recorded. Lock released in `finally`. (Grace period ≈ 5 minutes.) (Ref: FR-EXBOT-050, E-EXBOT-008.) | P0 |
| TC_053 | Verify the bot enters safe mode when the reconcile detects a size mismatch it cannot explain | 1. Bot running.\n2. Hedge-sync order submitted; reconcile finds actual HL position does not match expected by more than allowed tolerance. | 1. Let reconcile worker detect an unexplained size mismatch after an order. | 1. `lifecycle_state` changes to `safe_mode`. Error `E-EXBOT-011` recorded. Mismatch routed to repair or admin alert path. (Ref: FR-EXBOT-050, E-EXBOT-011.) | P0 |
| TC_054 | Verify the bot enters safe mode after two consecutive critical margin readings | 1. Bot running.\n2. Margin status updated to `critical` by previous hedge-sync preflight. | 1. Run second hedge-sync preflight that again fetches a critical margin reading. | 1. After second consecutive `critical` margin reading, bot enters safe mode (`lifecycle_state='safe_mode'`). Investor and admin alerts sent. (Ref: FR-EXBOT-050, FR-EXBOT-060.) | P0 |
| TC_055 | Verify all mutations are blocked when the bot is in safe mode | 1. Bot in safe mode (`lifecycle_state='safe_mode'`). | 1. Attempt each while bot is in safe mode: (a) place hedge order, (b) cancel stop, (c) rebalance hedge, (d) increase leverage. | 1. All mutation attempts (a)–(d) rejected with no side effect. Read operations and retry connectivity checks are allowed. (Ref: FR-EXBOT-050, BR-EXBOT-007.) | P0 |

### VI.2. Integration & State verification — Operation: SAFE_MODE entry and recovery from hedge-sync

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_056 | Verify the bot exits safe mode automatically when recovery conditions are met | 1. Bot in safe mode.\n2. HL becomes reachable again.\n3. Three consecutive reconcile attempts succeed with `margin_status` OK. | 1. Let auto-recovery check run three times, all successful. | 1. After third consecutive successful reconcile with OK margin, bot transitions from `safe_mode` to `active` (`lifecycle_state='active'`). (Ref: FR-EXBOT-050, BR-EXBOT-007.) | P0 |
| TC_057 | Verify safe mode is never a dead end — it always leads to recovery or safe close | 1. Bot in safe mode. | 1. Verify the possible paths out of `safe_mode` as documented. | 1. Safe mode must exit via: (a) auto-recovery to `active` when HL back and 3 consecutive reconciles succeed with OK margin, or (b) `bot_safe_close` when recovery impossible. No path leaves bot in `safe_mode` permanently. (Ref: BR-EXBOT-007, FR-EXBOT-050.) | P0 |
