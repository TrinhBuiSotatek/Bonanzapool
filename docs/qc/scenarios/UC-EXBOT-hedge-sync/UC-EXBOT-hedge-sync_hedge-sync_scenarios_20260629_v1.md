# Test Scenarios — UC-EXBOT-hedge-sync Execute Delta-Only Hedge Adjustment

> Source: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260626_v2.md
> Generated: 2026-06-29
> Domain/Architecture: Cloudflare Workers + D1 + Queues + Durable Objects; Hyperliquid (HL) external API; logic-only (no UI)

---

## UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment

### Scenario ID: TS_UC-EXBOT-hedge-sync_001
**Scenario Title:** Happy path — delta computed, adjustShortDelta sent, reconcile enqueued, status success
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027; FR-EXBOT-035; NFR-EXBOT-007
**Test Type:** Functional
**Description:** A `hedge-sync` queue message with a stateVersion matching D1 `bot_runtime_state.state_version` is delivered to the Hedge-Sync Worker. The queue idempotency guard passes (no prior `started` entry for this `message_id`). The UserLockDO acquires the mutex. The worker fetches the actual HL short position, computes delta via BigDecimal (actual size ≠ expected size), sends `adjustShortDelta` with the computed delta and a deterministic `cloid`, enqueues a `reconcile` message, runs the full INV-STOP protocol (cancel existing stop → place new stop, clear `stop_replacing_started_at` in `finally`), and releases the lock. `rebalance_attempts.status` must be set to `'success'` only after the reconcile worker confirms the position matches `expectedAbsSize`.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-hedge-sync_002
**Scenario Title:** stateVersion mismatch — message discarded, rebalance_attempts status skipped, no HL order
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A2; FR-EXBOT-027
**Test Type:** Functional
**Description:** A `hedge-sync` message arrives with a `stateVersion` that does NOT match D1 `bot_runtime_state.state_version`. The Hedge-Sync Worker must discard the message immediately, set `rebalance_attempts.status = 'skipped'`, and issue no HL order. No lock acquisition, no delta computation, and no INV-STOP interaction must occur.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_003
**Scenario Title:** stateVersion exact match — guard passes and processing continues
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027
**Test Type:** Boundary
**Description:** A `hedge-sync` message with a `stateVersion` equal to the D1 `bot_runtime_state.state_version` (exact boundary match) is delivered. The stateVersion guard must pass and the worker must proceed to lock acquisition without treating this as a mismatch.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_004
**Scenario Title:** stateVersion strictly less than D1 version — message discarded (stale delivery)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A2; FR-EXBOT-027
**Test Type:** Boundary
**Description:** A `hedge-sync` message with a `stateVersion` one below the current D1 `bot_runtime_state.state_version` is delivered (BVA: limit − 1). The guard must treat this as a mismatch and discard the message, setting `rebalance_attempts.status = 'skipped'`. No HL order must be issued.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_005
**Scenario Title:** UserLockDO lock not acquired — message re-queued with delay, no hedge mutation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A1; FR-EXBOT-027
**Test Type:** Functional
**Description:** When the Hedge-Sync Worker calls `UserLockDO.acquire(holderToken, ttl=90s, idempotencyKey='hedge-sync:{botId}:{stateVersion}')` and the DO returns `acquired=false` (another holder owns the lock), the worker must re-queue the `hedge-sync` message with a backoff delay and exit without performing any delta computation, HL order, or INV-STOP step.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_006
**Scenario Title:** Long-running hedge step (>30s) — lock heartbeat sent to prevent TTL expiry
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027 (UserLockDO TTL contract)
**Test Type:** Integration
**Description:** When HL API processing within a locked hedge-sync run extends beyond 30 seconds, the worker must send a heartbeat to the UserLockDO to extend the TTL and prevent automatic lock release mid-operation. The lock must remain held until the worker explicitly releases it at the end of the run.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_007
**Scenario Title:** UserLockDO TTL auto-release after 90s without heartbeat — lock freed for next worker
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027 (UserLockDO TTL=90s)
**Test Type:** Data/State
**Description:** If a Hedge-Sync Worker holding the UserLockDO lock stops sending heartbeats (e.g., due to a crash or hang), the DO must automatically release the lock after 90 seconds (TTL expiry). A subsequent `hedge-sync` message for the same bot must be able to acquire the lock and proceed normally without requiring manual intervention.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_008
**Scenario Title:** HL rejects delta order (insufficient margin) — E-EXBOT-007, circuit breaker failure incremented
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A3; FR-EXBOT-027; E-EXBOT-007
**Test Type:** Functional
**Description:** Hyperliquid rejects the `adjustShortDelta` order with an insufficient-margin error. The system must store error message E-EXBOT-007 ("Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin.") against the bot, increment the circuit breaker `failure_count`, and set `rebalance_attempts.status = 'failed'`. No retry of the HL call must occur within the same worker invocation.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_009
**Scenario Title:** HL API unreachable — E-EXBOT-008 stored, circuit breaker failure incremented
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Exception flows; FR-EXBOT-027; E-EXBOT-008
**Test Type:** Functional
**Description:** The Hyperliquid API is unreachable when the worker attempts to send `adjustShortDelta`. The system must store error message E-EXBOT-008 ("Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."), increment the circuit breaker `failure_count`, and set `rebalance_attempts.status = 'failed'`. The bot must transition to SAFE_MODE if the circuit breaker threshold is reached.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_010
**Scenario Title:** Circuit breaker opens after 3 consecutive HL failures in 24h rolling window
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Circuit breaker; FR-EXBOT-027
**Test Type:** Data/State
**Description:** Three consecutive HL order rejections or unreachability events accumulate within a rolling 24-hour window, bringing `failure_count` from 0 to 3. The circuit breaker must transition from `closed` to `open`, set `reset_at = now + 1h`, and prevent any further HL mutation calls until the reset time elapses. The state transition must be atomic.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_011
**Scenario Title:** Circuit breaker at failure_count=2 — circuit remains closed, HL call proceeds
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Circuit breaker; FR-EXBOT-027
**Test Type:** Boundary
**Description:** After exactly 2 consecutive failures in the 24-hour rolling window (BVA: limit − 1 = 2), the circuit breaker must remain `closed`. The next `hedge-sync` attempt must be allowed to call HL normally without being blocked. The circuit must NOT open until `failure_count` reaches 3.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_012
**Scenario Title:** Circuit breaker open — hedge suppressed, stop monitoring continues (AC-05)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A4 / AC-05; FR-EXBOT-027
**Test Type:** Functional
**Description:** When the circuit breaker state is `open` and a new `hedge-sync` message arrives, the worker must suppress the delta hedge mutation and must NOT call `adjustShortDelta`. Stop monitoring (INV-STOP protocol) must remain active and must not be skipped. The `rebalance_attempts.status` must reflect that the hedge was blocked by the open circuit.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_013
**Scenario Title:** Circuit breaker half_open — exactly one probe allowed (atomic half_open_probe_used 0→1)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Circuit breaker; FR-EXBOT-027
**Test Type:** Data/State
**Description:** When the circuit breaker transitions to `half_open` after `reset_at` elapses, only one probe attempt is permitted. The `half_open_probe_used` flag must be atomically incremented from 0 to 1 before the probe HL call proceeds. If two concurrent workers both read `half_open_probe_used=0`, only the one that successfully claims it atomically must send the probe; the other must be blocked.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_014
**Scenario Title:** half_open probe success — circuit transitions to closed, failure_count reset to 0 (AC-06)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Circuit breaker / AC-06; FR-EXBOT-027
**Test Type:** Data/State
**Description:** When the circuit breaker is `half_open` and the single probe HL call succeeds, the circuit must transition to `closed`, `failure_count` must be reset to 0, and `reset_at` must be cleared. Subsequent `hedge-sync` runs must be allowed to send HL orders without restriction.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_015
**Scenario Title:** half_open probe failure — circuit transitions back to open with new reset_at (AC-07)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Circuit breaker / AC-07; FR-EXBOT-027
**Test Type:** Data/State
**Description:** When the circuit breaker is `half_open` and the single probe HL call fails, the circuit must transition back to `open`, and `reset_at` must be set to `now + 1h`. The `half_open_probe_used` flag must be reset so the next probe cycle can begin. Subsequent `hedge-sync` runs must be blocked again until `reset_at` elapses.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_016
**Scenario Title:** half_open second probe attempt blocked — half_open_probe_used already 1
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Circuit breaker; FR-EXBOT-027
**Test Type:** Idempotency/Concurrency
**Description:** When a second concurrent worker attempts to send a probe while the circuit breaker is `half_open` and `half_open_probe_used=1` (first probe already claimed), the second worker must be blocked from sending any HL order. It must not treat the blocked state as a new failure or modify the circuit breaker state.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_017
**Scenario Title:** delta=0 — no HL order sent, INV-STOP continues, rebalance_attempts status TBD (AC-09)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A6 / AC-09; FR-EXBOT-027
**Test Type:** Functional
**Description:** When the worker fetches the actual HL position and computes delta = 0 (actual size exactly equals expected size), no `adjustShortDelta` call must be sent to HL (delta-only invariant preserved). The INV-STOP protocol must still execute in full. The `rebalance_attempts.status` assignment for delta=0 is an open issue (I-01); the scenario must verify the behavior and flag the assertion as pending BA confirmation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_018
**Scenario Title:** delta positive (short position too small) — adjustShortDelta with positive delta sent
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; BR-EXBOT-004; FR-EXBOT-027
**Test Type:** Functional
**Description:** When the computed delta is positive (actual HL short position is smaller than expected), the worker must send `adjustShortDelta` with the positive delta value only — it must NOT close the full position and re-open it. The order size must match the computed delta exactly (BigDecimal precision required per NFR-EXBOT-008).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_019
**Scenario Title:** delta negative (short position too large) — adjustShortDelta with negative delta sent
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; BR-EXBOT-004; FR-EXBOT-027
**Test Type:** Functional
**Description:** When the computed delta is negative (actual HL short position is larger than expected), the worker must send `adjustShortDelta` with the negative delta value only. A full close → re-open sequence must NOT occur. BigDecimal must be used for the delta computation (NFR-EXBOT-008).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_020
**Scenario Title:** Full close then re-open in normal hedge-sync — hard violation of delta-only invariant (BR-EXBOT-004)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** BR-EXBOT-004; FR-EXBOT-027
**Test Type:** Functional
**Description:** Under no circumstances during a normal hedge-sync execution (circuit closed, no emergency close) must the worker issue a full position close followed by a new open. Any code path that results in this behavior is a hard violation of BR-EXBOT-004. The system must send only the delta adjustment in all normal scenarios.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_021
**Scenario Title:** BigDecimal delta computation — Number() arithmetic is a violation (NFR-EXBOT-008)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** NFR-EXBOT-008; FR-EXBOT-027
**Test Type:** Functional
**Description:** All hedge delta computations must use BigDecimal arithmetic only. Any code path that uses JavaScript `Number()` arithmetic for delta, stop price, or margin calculations violates NFR-EXBOT-008. The system must produce the correct BigDecimal result for a delta computation involving fractional values that would lose precision under IEEE 754 floating point (e.g., sizes that differ in the sub-cent range).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_022
**Scenario Title:** stop_trigger_px computed via BigDecimal formula — entry_price × (1 + liq_distance_pct × 0.70)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §INV-STOP; FR-EXBOT-035; NFR-EXBOT-008
**Test Type:** Functional
**Description:** During the INV-STOP protocol, the stop trigger price must be computed as `entry_price × (1 + liq_distance_pct × stopSafetyFactor)` where `liq_distance_pct = (liq_price − entry_price) / entry_price` and `stopSafetyFactor = 0.70` (Phase A). BigDecimal must be used. The resulting `stop_trigger_px` must be placed as the new stop order on HL and stored in the DB.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_023
**Scenario Title:** INV-STOP protocol — stop_replacing_started_at set before critical section, cleared in finally
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** FR-EXBOT-035; UC-EXBOT-hedge-sync §Main Flow
**Test Type:** Functional
**Description:** Before entering the INV-STOP critical section (cancel existing stop → place new stop), the worker must set `stop_replacing_started_at` to the current timestamp. After the critical section completes (success or failure), `stop_replacing_started_at` must be cleared to NULL in the `finally` block. The field must not remain set after the run exits.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_024
**Scenario Title:** stop_replacing_started_at stuck >60s — light-check detects and triggers SAFE_MODE (A5 / FR-EXBOT-035)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A5; FR-EXBOT-035
**Test Type:** Integration
**Description:** If `stop_replacing_started_at` remains set for more than 60 seconds without being cleared (e.g., the worker crashed after setting it but before the `finally` block executed), the primary light-check must detect the stuck state and trigger SAFE_MODE for the bot. The scenario must verify that SAFE_MODE is entered and that no new hedge or stop operations are attempted until the bot is manually recovered.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_025
**Scenario Title:** cloid determinism — same botId+attemptId+stage+version always produces same cloid
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027 (cloid spec)
**Test Type:** Data/State
**Description:** The client order ID (`cloid`) must be deterministically computed as `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Given the same `botId`, `attemptId`, `stage`, and `version` inputs, the computed `cloid` must always be identical. Two independent computations with the same inputs must produce the same hex string.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_026
**Scenario Title:** cloid on retry with same payload — do NOT resubmit blindly; reconcile first
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027 (cloid retry contract)
**Test Type:** Idempotency/Concurrency
**Description:** When a worker retries after a failed `adjustShortDelta` attempt using the same `botId+attemptId+stage+version` payload (producing the same `cloid`), it must NOT blindly resubmit the HL order. Instead, it must check the reconcile state first to determine whether the original order was partially or fully filled before deciding whether to retry. Blind resubmission with the same `cloid` must be treated as a violation.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_027
**Scenario Title:** cloid version incremented on payload change — new cloid generated for new attempt
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027 (cloid spec)
**Test Type:** Functional
**Description:** When a retry uses an incremented `version` component in the cloid payload (changed attempt context), the resulting `cloid` must be different from the previous attempt's `cloid`. The new `cloid` must be stored and used for the new HL order. The determinism invariant must hold: same new payload → same new cloid.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_028
**Scenario Title:** Duplicate queue message delivery — idempotency guard exits without duplicate HL order (AC-10)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Idempotency / AC-10; NFR-EXBOT-007
**Test Type:** Idempotency/Concurrency
**Description:** A `hedge-sync` queue message is delivered twice (duplicate delivery due to at-least-once queue semantics). On the second delivery, the `queue_idempotency` table must already contain a row with `message_id` matching the incoming message and `state = 'started'` or `'succeeded'`. The worker must detect the conflict on insert and exit immediately without performing any HL call, lock acquisition, or delta computation. `rebalance_attempts` must not gain a duplicate row.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_029
**Scenario Title:** Concurrent hedge-sync workers race for same bot lock — only one proceeds, other re-queues
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027 (UserLockDO mutex)
**Test Type:** Idempotency/Concurrency
**Description:** Two Hedge-Sync Worker instances for the same bot are triggered concurrently (e.g., from two queue retries). Both attempt to acquire the UserLockDO mutex. Only the first to atomically set the lock must proceed to HL operations. The second must receive `acquired=false` and must re-queue with delay. No double-hedge mutation must occur.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_030
**Scenario Title:** Partial fill detected by reconcile worker — partial_repair enqueued, status = partial
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A4 / AC-08; FR-EXBOT-027
**Test Type:** Integration
**Description:** After `adjustShortDelta` is sent, the reconcile worker fetches the actual HL position and finds that the size does NOT equal `expectedAbsSize` (partial fill). The reconcile worker must enqueue a `partial_repair` message and set `rebalance_attempts.status = 'partial'`. The E-EXBOT-011 error message ("Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation.") must be stored internally.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_031
**Scenario Title:** 3 consecutive partial_repair failures — bot_safe_close triggered
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §A4 / AC-08; FR-EXBOT-027
**Test Type:** Data/State
**Description:** After a partial fill, three consecutive `partial_repair` attempts all fail to bring the actual HL position to `expectedAbsSize`. On the third failure, the system must trigger `bot_safe_close` to safely close the bot position. The bot must transition to SAFE_MODE. No further repair attempts must be made automatically.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_032
**Scenario Title:** reconcile confirms full fill — rebalance_attempts status set to success, stop updated
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027
**Test Type:** Integration
**Description:** After `adjustShortDelta` is sent, the reconcile worker fetches the actual HL position and confirms it matches `expectedAbsSize`. The `rebalance_attempts.status` must be set to `'success'` at this point (NOT before reconcile confirms). The `hedge_legs` record must be updated to reflect the new position. `stop_replacing_started_at` must be NULL.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_033
**Scenario Title:** rebalance_attempts status never set to success before reconcile confirmation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027
**Test Type:** Data/State
**Description:** After `adjustShortDelta` is sent but before the reconcile worker has confirmed the actual HL position, `rebalance_attempts.status` must remain at `'started'` or an intermediate state — it must NOT be `'success'`. Premature success marking before reconcile confirmation is a violation.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_034
**Scenario Title:** queue_idempotency message_id UNIQUE constraint — insert conflict exits immediately
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Idempotency; NFR-EXBOT-007
**Test Type:** Data/State
**Description:** The `queue_idempotency` table enforces a UNIQUE constraint on `message_id`. When the worker attempts to insert a row for an already-processed `message_id`, the DB must return a conflict error. The worker must catch this, treat it as a duplicate delivery, and exit immediately. The `state` column lifecycle must transition from `started` to `succeeded` or `failed` — never skip to `succeeded` without the intermediate write.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_035
**Scenario Title:** agent key decrypt failure mid-hedge-sync — bot enters SAFE_MODE (partially blocked I-06)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Exception flows; I-06 (Open — agent key decrypt step missing from UC main flow)
**Test Type:** Functional
**Description:** If the agent key decryption step fails during hedge-sync processing (e.g., KMS unavailable, key corrupted), the worker must not proceed to HL calls with an invalid or missing key. The bot must enter SAFE_MODE. This scenario is partially blocked by open issue I-06 (the decrypt step is absent from the UC main flow); the scenario must be re-validated after BA confirms the correct flow position for the decrypt step.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_036
**Scenario Title:** HL API unreachable for >5 minutes — bot enters SAFE_MODE, E-EXBOT-008 persisted
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Exception flows; E-EXBOT-008; FR-EXBOT-027
**Test Type:** End-to-End
**Description:** When Hyperliquid remains unreachable across multiple retry attempts spanning more than 5 minutes, the bot must transition to SAFE_MODE and persist E-EXBOT-008 ("Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."). The circuit breaker must have opened. No further hedge mutations must be attempted in SAFE_MODE. The bot must remain in SAFE_MODE until manually recovered or HL connectivity is restored per the defined recovery protocol.
**Test Focus:** End-to-End

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_037
**Scenario Title:** hedge_legs and rebalance_attempts updated atomically after reconcile — no partial DB state
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Main Flow; FR-EXBOT-027
**Test Type:** Data/State
**Description:** After the reconcile worker confirms the HL position matches `expectedAbsSize`, the updates to `hedge_legs` and `rebalance_attempts.status = 'success'` must be written atomically. If the D1 write fails mid-transaction, neither table must reflect a partial update. The system must be able to retry and produce a consistent final state.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_038
**Scenario Title:** Full E2E flow — hedge-sync delivered to SAFE_MODE after 3 circuit failures
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §Full flow; FR-EXBOT-027; FR-EXBOT-035
**Test Type:** End-to-End
**Description:** Starting from a `closed` circuit breaker and a running bot, deliver 3 consecutive `hedge-sync` messages that each result in HL rejection. After the 3rd failure, verify the circuit transitions to `open`, a 4th message is suppressed (hedge mutation blocked), and if the open state persists beyond the configured window without recovery, the bot enters SAFE_MODE. Stop monitoring must remain active throughout the sequence.
**Test Focus:** End-to-End

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_039
**Scenario Title:** AC-01 acceptance — hedge-sync completes end-to-end within 30s NFR (NFR-EXBOT-002)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-01; NFR-EXBOT-002
**Test Type:** Acceptance
**Description:** A single `hedge-sync` message on the happy path (lock acquired, delta computed, `adjustShortDelta` sent, reconcile enqueued, INV-STOP completed, lock released) must complete within 30 seconds end-to-end as required by NFR-EXBOT-002. The `rebalance_attempts` timestamp difference between `started_at` and `completed_at` must be ≤ 30s.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_040
**Scenario Title:** AC-02 acceptance — stateVersion mismatch results in skipped status with no HL side-effect
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-02; FR-EXBOT-027
**Test Type:** Acceptance
**Description:** A `hedge-sync` message with a mismatched `stateVersion` must result in `rebalance_attempts.status = 'skipped'` and zero HL API calls. This acceptance criterion verifies both the DB state and the absence of any external side-effect on the Hyperliquid account.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_041
**Scenario Title:** AC-03 acceptance — lock not acquired results in re-queue, no hedge mutation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-03; FR-EXBOT-027 (UserLockDO)
**Test Type:** Acceptance
**Description:** When the UserLockDO returns `acquired=false`, the message must be re-queued with a delay and no HL mutation must occur. The `rebalance_attempts` table must not record a `'failed'` or `'success'` row for this attempt — only a re-queue event. This verifies AC-03.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_042
**Scenario Title:** AC-04 acceptance — HL order rejection increments failure_count, returns correct error
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-04; FR-EXBOT-027; E-EXBOT-007
**Test Type:** Acceptance
**Description:** When HL rejects the delta order (any reason), the circuit breaker `failure_count` must be incremented, `rebalance_attempts.status = 'failed'`, and the appropriate error message (E-EXBOT-007 for margin rejection or E-EXBOT-008 for unreachability) must be stored. This verifies AC-04.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_043
**Scenario Title:** AC-05 acceptance — open circuit blocks hedge, stop monitoring persists
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-05; FR-EXBOT-027; FR-EXBOT-035
**Test Type:** Acceptance
**Description:** With the circuit breaker in `open` state, a `hedge-sync` message must result in the hedge mutation being suppressed while stop monitoring continues to execute. No `adjustShortDelta` call must reach HL. This verifies AC-05.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_044
**Scenario Title:** AC-06 acceptance — half_open probe success closes circuit and resets failure_count
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-06; FR-EXBOT-027
**Test Type:** Acceptance
**Description:** A successful probe in `half_open` state must close the circuit and reset `failure_count = 0`. The next `hedge-sync` message after recovery must be allowed to call HL without restriction. This verifies AC-06.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_045
**Scenario Title:** AC-07 acceptance — half_open probe failure re-opens circuit with new reset_at
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-07; FR-EXBOT-027
**Test Type:** Acceptance
**Description:** A failed probe in `half_open` state must return the circuit to `open` and set `reset_at = now + 1h`. The `half_open_probe_used` flag must be cleared for the next probe cycle. This verifies AC-07.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_046
**Scenario Title:** AC-08 acceptance — partial fill triggers partial_repair, 3 failures trigger bot_safe_close
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-08; FR-EXBOT-027; E-EXBOT-011
**Test Type:** Acceptance
**Description:** A partial fill detected by the reconcile worker must trigger `partial_repair` and set `status = 'partial'`. After three consecutive `partial_repair` failures, `bot_safe_close` must be triggered and the bot must enter SAFE_MODE. E-EXBOT-011 ("Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation.") must be stored internally. This verifies AC-08.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_047
**Scenario Title:** AC-09 acceptance — delta=0 sends no HL order, INV-STOP still executes
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-09; FR-EXBOT-035
**Test Type:** Acceptance
**Description:** When delta = 0, no HL `adjustShortDelta` call must be made. The INV-STOP protocol must still execute. The `rebalance_attempts.status` for the delta=0 case is under open issue I-01 (TBD); this acceptance scenario must verify the no-HL-call behavior and mark the status assertion as pending BA confirmation.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_048
**Scenario Title:** AC-10 acceptance — duplicate message exits immediately, no double hedge mutation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** AC-10; NFR-EXBOT-007
**Test Type:** Acceptance
**Description:** A duplicate `hedge-sync` message delivery must be detected via the `queue_idempotency` `message_id` UNIQUE constraint and the worker must exit immediately with no HL call and no new `rebalance_attempts` row. The existing idempotency row must remain unchanged. This verifies AC-10.
**Test Focus:** Acceptance

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| `rebalance_attempts.status` assignment when delta=0 | BLOCKED: I-01 — Open issue; BA has not confirmed whether the status should be `'success'`, `'skipped'`, or a new value when delta=0. Scenarios 017 and 047 cover the no-HL-call behavior but leave the status assertion as TBD. | Resolve I-01 via qc-qna + re-audit before writing the final status assertion in TCs. |
| marginSummary preflight check | BLOCKED: I-04 (OQ-EXBOT-014 deferred) — the marginSummary preflight step behavior is not finalized in the UC. No scenarios can be reliably written for margin-preflight edge cases. | Wait for BA to resolve OQ-EXBOT-014, then re-audit and add scenarios. |
| HLRateLimitDO + UserLockDO interaction under rate-limit saturation | BLOCKED: I-05 (OQ-EXBOT-015 deferred) — the interaction between HLRateLimitDO and the hedge-sync lock acquisition sequence under rate-limit conditions is not specified. NFR-EXBOT-004 (≤800 weight/min budget) correctness cannot be fully verified without this. | Wait for BA to resolve OQ-EXBOT-015. Add integration scenarios after confirmation. |
| agent key decrypt step exact flow position | BLOCKED: I-06 — Open; the UC main flow does not include the agent key decrypt step. Scenario 035 covers the failure path partially but exact pre-conditions depend on the resolved flow. | BA must confirm decrypt step position in main flow, then re-audit and finalize scenario 035. |
| HL rate-limit weight budget (NFR-EXBOT-004) | BLOCKED/OUT-OF-SCOPE: verifying that ≤800 weight/min is observed requires load or performance tooling outside functional test scope. | Defer to performance testing track. |
| Performance / throughput (30s NFR-EXBOT-002 under load) | OUT-OF-SCOPE: load-testing beyond a single-invocation timing check. | Defer to performance testing track. |
| Security penetration / cryptographic key extraction | OUT-OF-SCOPE: beyond functional auth scope. | Defer to security testing specialist. |
