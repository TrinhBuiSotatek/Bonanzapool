# Test Scenarios — UC-EXBOT-bot-safe-close System-Initiated Safe Close

> **Source:** UC-EXBOT-bot-safe-close_bot-safe-close_audited_20260709_v4.md
> **Generated:** 2026-07-02
> **Updated:** 2026-07-09 (v4: **Q4 RESOLVED (BA 2026-07-04)**, Q9 still pending)
> **Domain/Architecture:** ExBot Lambda + Hyperliquid + BnzaExVault (on-chain) + RedemptionQueue (on-chain) + Redis Redlock via ElastiCache (User Lock). No UI — logic-only / backend pipeline.

---

## UC-EXBOT-bot-safe-close — System-Initiated Safe Close

### Scenario ID: TS_UC-EXBOT-bot-safe-close_001
**Scenario Title:** Happy path — bot_safe_close completes successfully when all conditions are met
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073, FR-EXBOT-070, US-EXBOT-009 AC-009-1, SRS states.md
**Test Type:** End-to-End
**Description:** Given a bot with `bots.status IN ('active', 'safe_mode')` and a valid trigger condition met (circuit breaker exhausted, margin critical irrecoverable, 3 stops in 7 days, partial_repair exhausted, or admin force-close), when ExBot Lambda initiates bot_safe_close, then HL short is fully closed (size=0 confirmed via reconcile), LP position is closed via `vault.executeStrategy(RedeemStrategyV1, user, botId, params)`, `RedemptionQueue.createRequest` enqueues HL portion payout, Operator calls `fulfillRequest` FIFO on-chain, `bots.status='closed'`, `bots.lifecycle_state='closed'`, and investor is notified: "Bot safely closed. Funds have been returned to your wallet."
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_002
**Scenario Title:** Happy path — close_operations state machine progresses sequentially through all valid states
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073, SRS states.md close_operations
**Test Type:** Data/State
**Description:** Given a bot_safe_close trigger is accepted, when ExBot Lambda executes the close flow, then `close_operations.state` must progress sequentially through all valid states in order: `requested` → `hedge_close_pending` → `hedge_closed` → `lp_closed` → `redemption_queued` → `done` — no state may be skipped or reached out of order.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_003
**Scenario Title:** Happy path — bots.lifecycle_state transitions from active/safe_mode to lp_closing, then to closed
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** SRS states.md, FR-EXBOT-015, UC §3 Q6 update
**Test Type:** Data/State
**Description:** Given bot_safe_close is triggered, when ExBot Lambda starts operation, then `bots.lifecycle_state` transitions to `lp_closing` immediately and `bots.status` transitions to `closing` simultaneously — these states persist until `fulfillRequest` completes, then both transition to `closed`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_004
**Scenario Title:** Trigger rejected when bots.status is already 'closed'
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-072, SRS erd.md, Q3 update
**Test Type:** Functional
**Description:** Given a bot with `bots.status='closed'`, when a new bot_safe_close trigger arrives from any of the 5 trigger sources, then the system must reject the trigger and return E-EXBOT-012: "Bot {id} is already closed. No action needed." — no new close_operations row must be created.
**Expected Result Note:** ✅ **Q4 RESOLVED (2026-07-09):** "Close Worker" là label cho ExBot Lambda — architecture component, không phải actor. 5 trigger conditions từ workers/admin đã được xác nhận. Actor list convention giữ nguyên. Trigger rejection behavior (UNIQUE constraint) không phụ thuộc vào Q4 answer.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_005
**Scenario Title:** Trigger rejected when bots.status is already 'closing' (idempotency)
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-072, FR-EXBOT-070, Q3 update
**Test Type:** Functional
**Description:** Given a bot with an active close_operations row (bot_safe_close in progress, `bots.status='closing'`), when a duplicate bot_safe_close trigger arrives for the same bot, then the system must reject the duplicate via UNIQUE constraint on `close_operations.idempotency_key` — exactly one close_operations row must exist, no double settlement.
**Expected Result Note:** ✅ **Q4 RESOLVED (2026-07-09):** "Close Worker" là label cho ExBot Lambda — architecture component. 5 trigger conditions từ workers/admin đã được xác nhận. UNIQUE constraint idempotency không phụ thuộc vào Q4 answer.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_006
**Scenario Title:** Hedge close failure — HL order fails after 3 retries, LP not touched, residual_hl_liability recorded
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** UC A1, FR-EXBOT-073, US-EXBOT-009 AC-009-2, message-list.md E-EXBOT-018, Q5/Q11 update
**Test Type:** Functional
**Description:** Given bot_safe_close is triggered and hedge close begins, when `closeShortReduceOnlyIoc` fails after 3 retries, then `close_operations.state` must be set to `residual_hl_liability`, `bots.status` and `bots.lifecycle_state` must both be set to `safe_mode`, LP position must NOT be closed, and admin notification E-EXBOT-018 must be sent: "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability."
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_007
**Scenario Title:** LP close revert — retry 3 times then escalate to admin
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** UC A2, FR-EXBOT-073
**Test Type:** Functional
**Description:** Given hedge has been successfully closed (`hedge_legs.last_known_hl_short_size=0`), when `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` call reverts, then the system must retry up to 3 times, and after the 3rd failure must escalate to admin and hold at `close_operations.state='lp_closed'` pending manual resolution.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_008
**Scenario Title:** fulfillRequest not yet called — request stays enqueued, bots.status remains 'closing'
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** UC A3, US-EXBOT-009 AC-009-4
**Test Type:** Functional
**Description:** Given `close_operations.state='redemption_queued'` and `RedemptionQueue.createRequest` has been called, when Operator has not yet called `fulfillRequest`, then the request must stay enqueued in the FIFO queue and must not be lost, `bots.status` must remain `closing`, and user funds must remain safe on-chain.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_009
**Scenario Title:** fulfillRequest fails — request stays enqueued, Operator retries
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-070, UC A3
**Test Type:** Functional
**Description:** Given `close_operations.state='redemption_queued'` and `fulfillRequest` is called, when `fulfillRequest` fails, then the request must stay enqueued in the FIFO queue (not dropped or lost), and Operator must be able to retry the fulfillRequest call.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_010
**Scenario Title:** 3rd trigger within 7 days — close executes normally with admin notification
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** UC A4, US-EXBOT-009 AC-009-3
**Test Type:** Functional
**Description:** Given a bot that already has 2 bot_safe_close events triggered within the last 7 days (rolling window), when the 3rd trigger condition is met, then the close flow must execute normally without blocking, and admin notification must be sent concurrently (not instead of the close).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_011
**Scenario Title:** Delta computation uses BigDecimal for full hedge close
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-021, FR-EXBOT-022, NFR-EXBOT-008
**Test Type:** Functional
**Description:** Given a bot with an existing HL short position (actualShortEth > 0), when ExBot Lambda computes delta for full hedge close, then the computation must use BigDecimal (not float/Number) with formula `delta = 0 - actualShortEth` — precision loss from floating-point arithmetic must be avoided.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_012
**Scenario Title:** Stop cancel via INV-STOP protocol — not direct cancel-then-place
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-035, FR-EXBOT-073, Q8 update
**Test Type:** Functional
**Description:** Given bot_safe_close requires stopping the reduce-only protective stop, when the stop is cancelled, then the cancellation must use the INV-STOP protocol (§19.5) via `replaceStopProtected(size=0)` — direct cancel-then-place is an architectural violation and must not be used.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_013
**Scenario Title:** Reconcile confirms HL size = 0 and stop cancelled before advancing to hedge_closed
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-025, FR-EXBOT-073, Q8 update
**Test Type:** Functional
**Description:** Given hedge close order has been submitted, when ExBot Lambda reconciles by fetching clearinghouseState, then `close_operations.state` must only advance to `hedge_closed` if BOTH conditions are confirmed: (1) HL short size = 0 AND (2) stop has been cancelled. If either condition is not met, the state must not advance.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_014
**Scenario Title:** LP close via vault.executeStrategy emits PositionClosed event, fees routed via LpFeeOps
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073, Q1 update
**Test Type:** Integration
**Description:** Given hedge is confirmed closed (`hedge_closed`), when ExBot Lambda calls `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` to close LP position, then BnzaExPositionManager must process the strategy, earned fees must be routed via LpFeeOps (op fee + perf fee), principal must be returned in pair currency, and PositionClosed event must be emitted. ExBot Lambda must only advance `close_operations.state` to `lp_closed` after PositionClosed event is received.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_015
**Scenario Title:** RedemptionQueue.createRequest enqueues HL portion payout, state advances to redemption_queued
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073, UC step 8-9
**Test Type:** Integration
**Description:** Given LP is confirmed closed (`lp_closed`), when ExBot Lambda calls `RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId)`, then the request must be enqueued on-chain, RequestCreated event must be emitted, and `close_operations.state` must advance to `redemption_queued`.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_016
**Scenario Title:** RedemptionQueue fulfillRequest pops FIFO — oldest request served first
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-070
**Test Type:** Integration
**Description:** Given multiple redemption requests exist in the queue from different bots, when Operator calls `RedemptionQueue.fulfillRequest(tokens, amounts)`, then the system must pop requests in FIFO order (oldest first) — out-of-order fulfillment creates user fund loss risk and must not occur.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_017
**Scenario Title:** RequestFulfilled event received — close_operations.state advances to done, bots.status='closed'
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073, UC step 11
**Test Type:** Data/State
**Description:** Given `close_operations.state='redemption_queued'` and Operator has called `fulfillRequest`, when `RequestFulfilled` event is received on-chain, then `close_operations.state` must advance to `done` and `bots.status` must transition to `closed`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_018
**Scenario Title:** Admin force-close via POST /api/exbot/close initiates full bot_safe_close flow
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** US-EXBOT-012, FR-EXBOT-090, Q2 update
**Test Type:** Functional
**Description:** Given an admin (zen) calls POST /api/exbot/close with a valid botId and reason, when the request is forwarded via OperatorFacade through API Gateway + HMAC Lambda Authorizer to ExBot Lambda, then bot_safe_close must be initiated: `bots.status='closing'`, hedge → LP → RedemptionQueue flow executes, and investor is notified: "Your ExBot was administratively closed. USDC is available for withdrawal."
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_019
**Scenario Title:** Admin force-close on SAFE_MODE bot proceeds with existing hedge state
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** US-EXBOT-012 AC-012-2
**Test Type:** Functional
**Description:** Given an admin initiates force-close on a bot with `bots.status='safe_mode'`, when the system processes the close, then it must proceed with bot_safe_close using the existing hedge state. If hedge cannot close due to irrecoverable state, `residual_hl_liability` must be recorded and admin notified of outstanding liability.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_020
**Scenario Title:** Admin force-close on already-closed bot returns E-EXBOT-012, no close_operations row created
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** US-EXBOT-012 AC-012-4, message-list.md E-EXBOT-012
**Test Type:** Functional
**Description:** Given a bot with `lifecycle_state='closed'`, when an admin attempts to Force-close it via POST /api/exbot/close, then the system must return E-EXBOT-012: "Bot {id} is already closed. No action needed." and no close_operations row must be created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_021
**Scenario Title:** Emergency transfer transfers funds to user's own address only, no recipient parameter
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** US-EXBOT-012 AC-012-3, FRD §2 ACT-M
**Test Type:** Functional
**Description:** Given BnzaExVault contract is paused and Operator calls `emergencyTransfer(user, botId)`, when the emergency transfer executes, then user's USDC and LP NFTs must be transferred to the user's own address (no recipient parameter exists) and EmergencyRecovery event must be emitted on-chain. Multi-sig is NOT required for this operation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_022
**Scenario Title:** bots.status='closed' is only set after fulfillRequest completes — not earlier
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073, UC §5
**Test Type:** Data/State
**Description:** Given bot_safe_close is in progress, when any intermediate step completes (e.g., hedge closed, LP closed, request enqueued) but fulfillRequest has not yet been called, then `bots.status` must remain `closing` — it must not be set to `closed` prematurely. Premature state transition creates misleading user-facing status.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_023
**Scenario Title:** Force-close reason is logged in close_operations for audit trail
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** US-EXBOT-012 Notes, FR-EXBOT-090
**Test Type:** Functional
**Description:** Given an admin initiates force-close with a reason, when the close_operations row is created, then `close_operations.trigger_reason` must be populated with the admin-provided reason, ensuring a traceable audit trail.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_024
**Scenario Title:** bot_safe_close succeeds even when circuit_breakers.state='open'
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-040, FR-EXBOT-073
**Test Type:** Functional
**Description:** Given a bot with `circuit_breakers.state='open'` (circuit breaker is open), when bot_safe_close is triggered, then the close operation must succeed — circuit breaker suppresses hedge-sync but does NOT block close operation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_025
**Scenario Title:** Duplicate trigger via redelivery is rejected (idempotency)
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-070, SRS erd.md, **Q4 RESOLVED (2026-07-09)**
**Test Type:** Idempotency/Concurrency
**Description:** Given bot_safe_close trigger is delivered and processed, when the same trigger is redelivered (e.g., consumer ack failure, worker crash before ack), then the system must reject the duplicate via UNIQUE constraint on `close_operations.idempotency_key` — the operation must not be double-applied.
**Expected Result Note:** ✅ **Q4 RESOLVED (2026-07-09):** "Close Worker" là ExBot Lambda (architecture component). 5 trigger conditions đã được xác nhận trong UC. UNIQUE constraint idempotency không phụ thuộc vào Q4 answer.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_026
**Scenario Title:** HL API unreachable during hedge close — bot enters SAFE_MODE with E-EXBOT-008
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** message-list.md E-EXBOT-008
**Test Type:** Error/Exception
**Description:** Given bot_safe_close is processing hedge close, when HL API becomes unreachable during `closeShortReduceOnlyIoc` call, then bot must enter SAFE_MODE and E-EXBOT-008: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." must be triggered.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_027
**Scenario Title:** Reconcile mismatch after hedge close — bot enters SAFE_MODE with E-EXBOT-011
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** message-list.md E-EXBOT-011, FR-EXBOT-025
**Test Type:** Error/Exception
**Description:** Given `closeShortReduceOnlyIoc` has been submitted, when reconcile (fetch clearinghouseState) detects that actual HL short size ≠ 0, then bot must enter SAFE_MODE and E-EXBOT-011: "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." must be triggered.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_028
**Scenario Title:** bots.lifecycle_state='safe_mode' when entering safe_mode (both status and lifecycle_state match)
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** SRS states.md, Q11 update
**Test Type:** Data/State
**Description:** Given a bot enters SAFE_MODE (via any trigger: hedge fail, reconcile mismatch, HL unreachable), when the safe_mode state is applied, then both `bots.status` and `bots.lifecycle_state` must be set to `'safe_mode'` with the same value — they must not diverge.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_029
**Scenario Title:** Each of 5 trigger conditions creates close_operations with correct trigger_reason populated
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-072, FR-EXBOT-073, **Q9 CẦN CONFIRM TỪ BA**, **Q4 RESOLVED (2026-07-09)**
**Test Type:** Boundary
**Description:** Given a valid bot (not closed/closing) and each of the 5 trigger conditions is met individually: (1) circuit breaker exhausted, (2) margin critical irrecoverable, (3) 3 stops in 7 days, (4) partial_repair exhausted, (5) admin force-close, when trigger fires in each case, then a close_operations row must be created with `kind='bot_safe_close'` and `trigger_reason` populated matching the specific trigger type — enabling traceable audit trail.
**Expected Result Note:** ⚠️ **Q9 CẦN CONFIRM TỪ BA** — format cụ thể của `trigger_reason` enum values chưa được định nghĩa. BA cần xác nhận: `circuit_breaker_exhausted`, `margin_critical`, `3_stops_7d`, `partial_repair_exhausted`, `admin_force_close`. ✅ **Q4 RESOLVED** — "Close Worker" là ExBot Lambda (architecture component). 5 trigger conditions đến từ: deep-audit worker, hedge-sync worker, partial_repair worker, light-check/hedge-stopped, HOẶC admin API (`POST /api/exbot/close`). Không có dedicated `bot_safe_close` queue trong 11 queues (FR-EXBOT-010).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_030
**Scenario Title:** Investor receives notification after fulfillRequest completes
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** UC step 12, US-EXBOT-009 AC-009-1
**Test Type:** Acceptance
**Description:** Given bot_safe_close completes successfully (fulfillRequest has been called and RequestFulfilled event received), when the system sends investor notification, then the investor must receive the message: "Bot safely closed. Funds have been returned to your wallet."
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_031
**Scenario Title:** Investor receives admin-force-close notification with correct message
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** US-EXBOT-012 AC-012-1
**Test Type:** Acceptance
**Description:** Given an admin force-close completes successfully (fulfillRequest has been called), when the system sends investor notification, then the investor must receive the message: "Your ExBot was administratively closed. USDC is available for withdrawal." — this is distinct from the happy-path close message.
**Test Focus:** Acceptance

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_032
**Scenario Title:** HL agent key with key_status='active' is required for hedge close signing
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-080
**Test Type:** Boundary
**Description:** Given bot_safe_close is triggered and requires HL signing for `closeShortReduceOnlyIoc`, when the signing operation is attempted, then HL agent key must have `key_status='active'` — the operation must fail if the key is not active.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_033
**Scenario Title:** Light-check is suppressed during bot_safe_close
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-015, SRS states.md
**Test Type:** Functional
**Description:** Given bot_safe_close is in progress (`bots.status='closing'`, `bots.lifecycle_state='lp_closing'`), when light-check queue worker runs, then light-check must be suppressed for this bot — no hedge fetch or margin check via HL API must occur during close operation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_034
**Scenario Title:** LP close must not be attempted before hedge_closed is confirmed
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-073
**Test Type:** State transition
**Description:** Given bot_safe_close is in progress but hedge has not yet been confirmed closed, when LP close operation (`vault.executeStrategy`) is attempted prematurely, then the system must prevent LP close — LP close must only proceed after `hedge_closed` is confirmed. This hedge-first invariant must be enforced.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-safe-close_035
**Scenario Title:** cloid deterministic — same cloid resubmission does not create duplicate HL orders
**UC Reference:** UC-EXBOT-bot-safe-close
**Req-ID:** FR-EXBOT-024, FR-EXBOT-073
**Test Type:** Idempotency/Concurrency
**Description:** Given `closeShortReduceOnlyIoc` is submitted with deterministic cloid (keccak256("bnza:{botId}:{attemptId}:{stage}:{version}")), when the same order is resubmitted with the same cloid, then HL must deduplicate — exactly one HL order must be created, no double-apply of the close.
**Test Focus:** Idempotency/Concurrency

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| `idempotency_key` và `trigger_reason` format (**Q9 — CẦN CONFIRM TỪ BA**) | FR-EXBOT-072 nói "idempotency_key UNIQUE enforced" và "trigger_reason populated" nhưng không định nghĩa format/value cụ thể. BA cần bổ sung: (1) format của `idempotency_key` (ví dụ: `{botId}:{kind}:{trigger_timestamp}`), (2) enum values của `trigger_reason` (`circuit_breaker_exhausted`, `margin_critical`, `3_stops_7d`, `partial_repair_exhausted`, `admin_force_close`). | **Chờ Q9 answer từ BA** |
| BnzaExVault Solidity contract internal logic | zen develops; SOTATEK integrates via ABI | Integration tests depend on ABI confirmation (OQ-EXBOT-08) |
| RedemptionQueue contract internal logic (fulfillRequest ABI) | zen develops; SOTATEK integrates via ABI | Integration tests depend on ABI confirmation (OQ-EXBOT-08) |
| SPEC §19.5 INV-STOP protocol implementation details | Pending HL confirmation on stop placement behavior (OQ-EXBOT-02) | Wait for OQ-EXBOT-02 answer |
| HL API field names for marginSummary | Pending HL API docs confirmation (OQ-EXBOT-01) | Integration tests depend on API confirmation |
| Multi-bot per user support (Phase B+) | Phase A supports only 1 bot per user | N/A for Phase A |
| Performance / load testing (NFR-EXBOT-003: 5-minute SLA) | Performance testing out of scope for functional scenario design | Defer to performance testing phase |
| Security: private key never leaves KMS, Signing Lambda only | Security audit beyond functional testing scope | Defer to security audit |
| EmergencyTransfer contract-level enforcement (no recipient param) | Cannot be tested via integration — requires contract audit | Defer to contract security review |

---

✅ **Q4 RESOLVED (2026-07-09):** "Close Worker" trong UC §1 là label cho ExBot Lambda — architecture component, không phải actor độc lập. 5 trigger conditions đã được xác nhận trong UC §1/FR-EXBOT-072. Actor list convention giữ nguyên.

---

## Coverage Breakdown by Test Type

| Test Type | Count |
|---|---:|
| Happy path | 7 (TS_001, TS_002, TS_003, TS_012, TS_018, TS_023, TS_030, TS_031) |
| Alternative flow | 6 (TS_008, TS_010, TS_019, TS_021, TS_024, TS_033) |
| Error/Exception | 6 (TS_004, TS_006, TS_007, TS_009, TS_026, TS_027) |
| State transition | 7 (TS_002, TS_003, TS_013, TS_017, TS_022, TS_028, TS_034) |
| Integration | 3 (TS_014, TS_015, TS_016) |
| Idempotency/Concurrency | 3 (TS_005, TS_025, TS_035) |
| Boundary | 3 (TS_011, TS_029, TS_032) |
| Acceptance | 2 (TS_030, TS_031) |
| **Total** | **35** |

---

*Generated by qc-func-scenario-design-exbot skill — logic-only, no UI*
