# Test Scenarios — UC-EXBOT-user-redeem User-Initiated LP-First Redemption

> Source: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260701_v1.md
> Generated: 2026-07-01
> Domain/Architecture: Cloudflare Workers + Hyperliquid + BnzaExVault (on-chain) + D1 (state_db) + queue/Durable-Object pipeline
> Note: UC verdict is Not Ready (67/100). Scenarios for blocked areas (I-01, I-02, I-03, I-04, I-05, I-06, I-08) are flagged in ⚠️ Out-of-Scope Flags below. All other areas proceed.

---

## UC-EXBOT-user-redeem — User-Initiated LP-First Redemption

---

### Scenario ID: TS_UC-EXBOT-user-redeem_001
**Scenario Title:** Happy path — investor redeems successfully, LP-portion returned on-chain and HL hedge closed within SLA
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 main flow, FR-EXBOT-070(A), NFR-EXBOT-003, AC-01
**Test Type:** End-to-End
**Description:** Trigger the full user_redeem pipeline when a valid investor calls `BnzaExVault.redeem(tokenId)` on-chain with the bot in `active` state; the event watcher detects `RedemptionEvent`, enqueues to `user_redeem` queue, Worker processes the message within 5 minutes, closes the HL short via `closeShortReduceOnlyIoc`, cancels the stop via `replaceStopProtected(size=0)`, reconcile confirms HL position = 0, and HL-portion USDC is transferred to the investor via RedemptionQueue. The system must reach `close_operations.state='done'` and `bots.lifecycle_state='closed'` within the 5-minute SLA window.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_002
**Scenario Title:** LP-portion USDC is returned to investor in the same on-chain transaction as the redeem call
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 1-2, FR-EXBOT-070(A), BR-EXBOT-006
**Test Type:** Functional
**Description:** Verify that when `BnzaExVault.redeem(tokenId)` is called on-chain, the LP position is liquidated and LP-portion USDC appears at the investor's wallet address in the same transaction — not asynchronously after queue processing. The off-chain Worker's execution must not be a prerequisite for LP-portion delivery.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_003
**Scenario Title:** RedemptionEvent is detected by event watcher and enqueued to user_redeem queue with highest priority
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 3-4, flows.md F-04
**Test Type:** Integration
**Description:** After `BnzaExVault.redeem(tokenId)` emits `RedemptionEvent(botId, redeemTxHash, userAddress)` on-chain, verify the event watcher picks up the event and enqueues a message `{botId, redeemTxHash, userAddress}` to the `user_redeem` queue (highest priority). The message must appear in the queue before any Worker processing begins.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_004
**Scenario Title:** Worker creates close_operations record on first message receipt
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7, erd.md, FR-EXBOT-070
**Test Type:** Functional
**Description:** Verify that when the Worker dequeues the `user_redeem` message for the first time, it inserts a row into `close_operations` with `kind='user_redeem'` and a unique `idempotency_key`. The insertion must occur before any HL mutation is attempted.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_005
**Scenario Title:** bots.lifecycle_state transitions from active to lp_closing when close_operations record is created
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7, states.md, §F.2 item 2
**Test Type:** Data/State
**Description:** Verify that immediately after `close_operations` is inserted with `kind='user_redeem'`, `bots.lifecycle_state` transitions from `active` to `lp_closing`. Both writes must be consistent — there must be no window where `close_operations` exists but `lifecycle_state` is still `active`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_006
**Scenario Title:** light-check worker skips the bot entirely while lifecycle_state is lp_closing
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** states.md, AC-07, §F.4
**Test Type:** Integration
**Description:** After `close_operations` is created and `bots.lifecycle_state='lp_closing'`, trigger a light-check evaluation for the same bot. Verify the light-check worker does not enqueue any `hedge-sync` message for this bot. Stop monitoring suppression during `lp_closing` must be confirmed.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_007
**Scenario Title:** HL short position is closed via closeShortReduceOnlyIoc (full close, not delta-only)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 8, FR-EXBOT-020 exception #1, FR-EXBOT-070
**Test Type:** Functional
**Description:** Verify that the Worker calls `closeShortReduceOnlyIoc` with the full short size (not a delta-only partial close) as part of the user_redeem flow. This is the explicitly permitted full-close exception per FR-EXBOT-020 when target size = 0 (bot close path). The order must use a deterministic cloid.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_008
**Scenario Title:** Stop order is cancelled via replaceStopProtected(size=0), not by direct cancel
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 10, FR-EXBOT-032, AC-F5-07
**Test Type:** Functional
**Description:** Verify that when the Worker cancels the existing stop order on Hyperliquid as part of the close flow, it uses the INV-STOP protocol via `replaceStopProtected(size=0)`. A direct `cancelOrder` call outside this protocol is forbidden. After the call, `hedge_legs.stop_order_id` and `stop_cloid` must be cleared or marked as cancelled.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_009
**Scenario Title:** Post-close reconcile verifies HL position is exactly zero before marking hedge_closed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 11, flows.md F-04, FR-EXBOT-023
**Test Type:** Functional
**Description:** After `closeShortReduceOnlyIoc` is submitted, verify the Worker fetches `clearinghouseState` from Hyperliquid to confirm the actual short position size = 0. The `close_operations.state` must not advance to `hedge_closed` until reconcile confirms size = 0. No `done` state must be set before this confirmation.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_010
**Scenario Title:** close_operations state machine progresses correctly through the full happy path sequence
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7-15, states.md, erd.md, §F.2 item 1
**Test Type:** Data/State
**Description:** Verify the `close_operations.state` field transitions through the expected sequence during a successful user_redeem: from initial creation state → `hedge_closed` (after reconcile confirms HL position = 0) → `done` (after HL-portion USDC transfer completes). Each state must be persisted to D1 before the next step begins; no state must be skipped.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_011
**Scenario Title:** HL-portion USDC is transferred to investor via RedemptionQueue after hedge close is confirmed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 12-13, erd.md close_operations.usdc_amount
**Test Type:** Functional
**Description:** Verify that after reconcile confirms the HL short position is closed (size = 0), the Worker initiates transfer of the HL-portion USDC to the investor via the RedemptionQueue ledger. The transfer must not occur before reconcile confirms the close. `close_operations.usdc_amount` must be populated with the transferred amount.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_012
**Scenario Title:** Bot reaches lifecycle_state=closed and close_operations=done only after HL-portion transfer completes
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 14-15, states.md, §F.2 item 2
**Test Type:** Data/State
**Description:** Verify that `bots.lifecycle_state` transitions to `closed` and `bots.status` to `closed` only after the HL-portion USDC transfer has been recorded in the RedemptionQueue ledger, and `close_operations.state` is already `done`. Neither field must be set prematurely during any intermediate step.
**Test Focus:** State transition


---

### Scenario ID: TS_UC-EXBOT-user-redeem_013
**Scenario Title:** Admin receives SLA breach alert when hedge close exceeds 5 minutes from event detection
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A1, NFR-EXBOT-003, E-EXBOT-010, AC-02
**Test Type:** Functional
**Description:** Trigger a user_redeem flow where the hedge close operation is artificially delayed beyond 5 minutes from the moment `RedemptionEvent` is detected. Verify the system enqueues an admin alert with message E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." The hedge close must continue executing after the alert — the SLA breach must not abort the operation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_014
**Scenario Title:** Hedge close continues and completes after SLA breach alert is sent
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A1, NFR-EXBOT-003
**Test Type:** Functional
**Description:** After the SLA breach alert (E-EXBOT-010) is sent, verify the Worker does not abort or reset the hedge close attempt. The HL position close, stop cancel, reconcile, and HL-portion transfer must all complete normally. `close_operations.state` must eventually reach `done`. The SLA alert is a notification-only event with no control flow side effects.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_015
**Scenario Title:** SLA alert is sent exactly once, not repeatedly, during a single delayed hedge close
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A1, E-EXBOT-010
**Test Type:** Functional
**Description:** When hedge close takes longer than 5 minutes, verify that E-EXBOT-010 admin alert is enqueued exactly once per redeem operation — not sent again if the Worker continues to be delayed (e.g., multiple retry loops within the same operation). The notification queue must not accumulate duplicate SLA alerts for the same `close_operations` record.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_016
**Scenario Title:** Boundary — hedge close completing at exactly 5 minutes does not trigger SLA alert
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** NFR-EXBOT-003, UC-EXBOT-user-redeem §4 A1
**Test Type:** Functional
**Description:** Simulate a hedge close that completes at exactly the 5-minute mark from event detection (boundary value at the SLA threshold). Verify no E-EXBOT-010 alert is sent. The alert must only be triggered when the elapsed time strictly exceeds 5 minutes, not at exactly 5 minutes (or confirm which side of the boundary triggers the alert if the requirement defines ≥ vs >).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-user-redeem_017
**Scenario Title:** Boundary — hedge close completing 1 second past 5 minutes triggers SLA alert
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** NFR-EXBOT-003, E-EXBOT-010
**Test Type:** Functional
**Description:** Simulate a hedge close that completes at 5 minutes + 1 second from event detection (one unit past the SLA boundary). Verify E-EXBOT-010 alert is sent. This confirms the boundary is at 300 seconds and not at 301 seconds.
**Test Focus:** Boundary


---

### Scenario ID: TS_UC-EXBOT-user-redeem_018
**Scenario Title:** LP-portion is not reversed when hedge close fails after LP liquidation
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2, BR-EXBOT-006, AC-03
**Test Type:** Functional
**Description:** Simulate a scenario where the LP position is already liquidated on-chain (LP-portion USDC delivered to investor) and then the Worker's `closeShortReduceOnlyIoc` call to Hyperliquid fails with an unrecoverable error. Verify that the LP-portion USDC already delivered on-chain is NOT reversed, blocked, or withheld. BR-EXBOT-006: "user_redeem LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user."
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_019
**Scenario Title:** close_operations transitions to residual_hl_liability when hedge close fails after LP returned
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2, erd.md, AC-03
**Test Type:** Data/State
**Description:** When `closeShortReduceOnlyIoc` fails after LP-portion has already been returned on-chain, verify `close_operations.state` transitions to `residual_hl_liability`. The `close_operations.residual_amount` field must be populated with the outstanding HL liability amount (BigDecimal string). No `done` state must be set.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_020
**Scenario Title:** Admin notification is enqueued when hedge close fails and residual_hl_liability is set
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2, §F.2 item 8
**Test Type:** Functional
**Description:** When `close_operations.state` transitions to `residual_hl_liability`, verify the Worker enqueues an admin notification containing the outstanding liability amount from `close_operations.residual_amount`. The notification must be enqueued regardless of whether the SLA has been breached. (Note: exact message content pending I-05 BA confirmation — expected result for notification body is left blank until resolved.)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_021
**Scenario Title:** LP-portion unconditional guarantee holds when HL API is completely unreachable during hedge close
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** BR-EXBOT-006, AC-06, UC-EXBOT-user-redeem §4 A2
**Test Type:** Functional
**Description:** Simulate the Hyperliquid API being completely unreachable (all HL calls return connection errors) at the time the Worker attempts to close the hedge. Verify that LP-portion USDC already returned on-chain is not affected, and `close_operations.state` transitions to `residual_hl_liability`. BR-EXBOT-006 must be enforced: HL unavailability is an HL problem, not an investor problem.
**Test Focus:** Error/Exception


---

### Scenario ID: TS_UC-EXBOT-user-redeem_022
**Scenario Title:** Duplicate queue message is detected via close_operations idempotency_key UNIQUE constraint
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, erd.md, AC-04
**Test Type:** Functional
**Description:** Deliver a `user_redeem` queue message for a bot whose `close_operations` record with the same `idempotency_key` already exists (a redelivery scenario). Verify the Worker detects the duplicate via the UNIQUE constraint on `close_operations.idempotency_key`, performs no HL mutation, creates no additional D1 records, and exits gracefully without error.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_023
**Scenario Title:** Duplicate queue message is detected via queue_idempotency message_id UNIQUE constraint
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, FR-EXBOT-010, erd.md
**Test Type:** Functional
**Description:** Deliver a `user_redeem` queue message with a `message_id` that already exists in `queue_idempotency` (same message redelivered by the queue infrastructure). Verify the Worker hits the UNIQUE constraint at the `queue_idempotency` insert step and returns immediately without performing any HL mutation or creating duplicate `close_operations` rows.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_024
**Scenario Title:** Two concurrent deliveries of the same user_redeem message result in exactly one hedge close execution
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, FR-EXBOT-010, erd.md
**Test Type:** Integration
**Description:** Simulate two Workers receiving the same `user_redeem` message simultaneously (concurrent delivery). Verify that exactly one Worker proceeds to execute the hedge close; the other is blocked by either the `queue_idempotency.message_id` UNIQUE constraint or the `close_operations.idempotency_key` UNIQUE constraint. Only one `close_operations` row exists; only one HL `closeShortReduceOnlyIoc` call is made.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_025
**Scenario Title:** Worker returns E-EXBOT-012 when user_redeem is triggered for an already-closed bot
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 6, E-EXBOT-012, AC-05
**Test Type:** Functional
**Description:** Deliver a `user_redeem` message for a bot that already has `bots.lifecycle_state='closed'`. Verify the Worker detects the closed state early in processing and returns E-EXBOT-012 (HTTP 409): "Bot is already closed. No action needed." No HL mutation, no new `close_operations` row, no state change must occur.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_026
**Scenario Title:** Worker returns E-EXBOT-012 when user_redeem is triggered for a bot already in lp_closing state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** E-EXBOT-012, states.md
**Test Type:** Functional
**Description:** Deliver a second `user_redeem` message for a bot that is already in `lifecycle_state='lp_closing'` (a close operation is already in progress). Verify the Worker recognizes the state as "already closing" and either returns E-EXBOT-012 or detects the duplicate via `close_operations.idempotency_key` — in either case, no second HL close is initiated.
**Test Focus:** Error/Exception


---

### Scenario ID: TS_UC-EXBOT-user-redeem_027
**Scenario Title:** close_operations record matches the on-chain redeemTxHash from the RedemptionEvent
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7, §F.4, erd.md
**Test Type:** Data/State
**Description:** After a successful user_redeem flow, verify that the `close_operations` record's reference to `redeemTxHash` matches the on-chain transaction hash from the `RedemptionEvent`. This confirms off-chain state is anchored to the correct on-chain event and not a fabricated or stale value.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_028
**Scenario Title:** No duplicate HL-portion transfer occurs on user_redeem message redelivery after close_operations=done
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, erd.md, FR-EXBOT-010
**Test Type:** Integration
**Description:** Simulate queue redelivery of a `user_redeem` message after the full pipeline has already completed (`close_operations.state='done'`, HL-portion already sent). Verify the Worker does not re-execute the HL-portion transfer and does not create a second RedemptionQueue entry for the same investor. Total USDC received by the investor from this redeem must equal LP-portion + HL-portion, not LP-portion + 2×HL-portion.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_029
**Scenario Title:** hedge_legs stop fields are cleared after stop is cancelled via replaceStopProtected
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 10, FR-EXBOT-032, §F.1 item 5
**Test Type:** Data/State
**Description:** After `replaceStopProtected(size=0)` successfully cancels the stop order on Hyperliquid, verify that `hedge_legs.stop_order_id` and `hedge_legs.stop_cloid` are cleared or nulled in D1. The D1 state must reflect that no active stop order exists after the cancel. No stale stop reference must remain.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_030
**Scenario Title:** hedge-sync worker does not interfere with user_redeem while bot is in lp_closing state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** states.md, §F.4, §7.1 rule "Delta-only hedge"
**Test Type:** Integration
**Description:** While a user_redeem is in progress (`bots.lifecycle_state='lp_closing'`), verify that any concurrent light-check tick does not enqueue a `hedge-sync` message for this bot, and that any `hedge-sync` message already in the queue for this bot is either discarded or returns early due to the `lp_closing` state. No hedge mutation must occur during the close operation.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_031
**Scenario Title:** close_operations idempotency_key prevents double settlement when two separate close signals arrive
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** FR-EXBOT-070, erd.md close_operations.idempotency_key UNIQUE, §F.2 item 1
**Test Type:** Integration
**Description:** Simulate a scenario where two separate triggering signals for the same redeem arrive — for example, a queue redelivery and a manual retry — both attempting to insert a `close_operations` row with the same `idempotency_key`. Verify only one row is inserted (UNIQUE constraint blocks the second), and only one HL hedge close is executed. No double settlement results.
**Test Focus:** Idempotency/Concurrency


---

### Scenario ID: TS_UC-EXBOT-user-redeem_032
**Scenario Title:** Worker checks bot is not already closing/closed before attempting any HL mutation
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 6, E-EXBOT-012, states.md
**Test Type:** Functional
**Description:** Verify the Worker checks `bots.lifecycle_state` and `bots.status` early in the processing pipeline — before acquiring any lock, before creating `close_operations`, and before calling Hyperliquid — to guard against acting on a bot that has already entered `closing` or `closed` state. If the state is invalid, E-EXBOT-012 (409) must be returned with no side effects.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_033
**Scenario Title:** HL rate limiter is consulted before closeShortReduceOnlyIoc is called
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** FR-EXBOT-070, NFR-EXBOT-004, §7.3 HLRateLimitDO
**Test Type:** Integration
**Description:** Verify the Worker consults `HLRateLimitDO` before calling `closeShortReduceOnlyIoc` on Hyperliquid. If `HLRateLimitDO` returns `{allowed: false, retryAfterMs: N}`, the Worker must not call Hyperliquid immediately; it must respect the retry delay. Given the high priority of `user_redeem` queue, confirm whether the rate limit back-off behavior is the same as other workers or privileged.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_034
**Scenario Title:** Investor who does not own the tokenId cannot trigger user_redeem flow
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §2, §3.1 precondition 3
**Test Type:** Functional
**Description:** Attempt to call `BnzaExVault.redeem(tokenId)` on-chain using a wallet address that does not own the specified `tokenId`. Verify the on-chain transaction is reverted by the BnzaExVault contract. No `RedemptionEvent` is emitted, no queue message is enqueued, and no off-chain Worker processing occurs.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-user-redeem_035
**Scenario Title:** cloid used for closeShortReduceOnlyIoc is deterministic and idempotent for the same redeem attempt
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 8, §7.1 "cloid deterministic", FR-EXBOT-022
**Test Type:** Functional
**Description:** Verify that the `cloid` used when calling `closeShortReduceOnlyIoc` is computed deterministically from fixed inputs (e.g., `botId`, operation type, attempt context). If the Worker retries the same hedge close attempt (same logical operation), the same `cloid` must be produced. A different redeem for a different bot must produce a different `cloid`.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_036
**Scenario Title:** Retry of closeShortReduceOnlyIoc with same cloid does not double-close the HL position
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 8, §7.1 "cloid deterministic"
**Test Type:** Functional
**Description:** Simulate a scenario where `closeShortReduceOnlyIoc` is submitted but the response is ambiguous (timeout or network error). When the Worker retries with the same `cloid`, verify that Hyperliquid recognises the duplicate cloid and does not execute a second close. Reconcile after retry must confirm HL position = 0 with only one close execution.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_037
**Scenario Title:** NFR — HL-portion USDC amount stored in close_operations.usdc_amount uses BigDecimal precision
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** NFR-EXBOT-008, erd.md close_operations.usdc_amount (TEXT BigDecimal), §9 NFR
**Test Type:** Functional
**Description:** After a successful user_redeem, verify that `close_operations.usdc_amount` is stored as a BigDecimal string (TEXT), not as a JavaScript Number or float. No floating-point rounding artefacts must appear in the stored value. Any intermediate computation of the HL-portion amount must use BigDecimal arithmetic throughout.
**Test Focus:** On-chain↔off-chain consistency


---

### Scenario ID: TS_UC-EXBOT-user-redeem_038
**Scenario Title:** Acceptance — AC-01: full happy path within SLA completes all postconditions
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-01, us-004.md AC-004-1, NFR-EXBOT-003
**Test Type:** Acceptance
**Description:** Verify all AC-01 postconditions are met end-to-end: LP-portion USDC in investor wallet from the same on-chain tx; `close_operations.state='done'` reached within ≤ 5 minutes of event detection; `bots.lifecycle_state='closed'`; HL position = 0 confirmed by reconcile; HL-portion USDC sent via RedemptionQueue. All five conditions must be true simultaneously at completion.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_039
**Scenario Title:** Acceptance — AC-02: SLA breach triggers admin alert and hedge close still completes
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-02, us-004.md AC-004-2, E-EXBOT-010
**Test Type:** Acceptance
**Description:** Verify AC-02 postconditions: after hedge close exceeds 5 minutes, E-EXBOT-010 alert is sent to admin with exact message "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned."; hedge close continues without abort; `close_operations.state` eventually reaches `done`; LP-portion is not reversed.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_040
**Scenario Title:** Acceptance — AC-03: hedge close failure leaves LP-portion untouched and sets residual_hl_liability
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-03, us-004.md AC-004-3, BR-EXBOT-006
**Test Type:** Acceptance
**Description:** Verify AC-03 postconditions when HL close fails: `close_operations.state='residual_hl_liability'`; `close_operations.residual_amount` is populated; LP-portion USDC already sent on-chain is NOT reversed or blocked; admin notification is enqueued. BR-EXBOT-006 must hold: the on-chain LP-portion is permanently protected.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_041
**Scenario Title:** Acceptance — AC-04: duplicate message delivery results in graceful no-op
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-04, UC-EXBOT-user-redeem §4 A3
**Test Type:** Acceptance
**Description:** Verify AC-04: when the Worker receives a duplicate `user_redeem` message (same `idempotency_key` or `message_id` already processed), it performs no HL mutation, creates no additional D1 rows, and exits without error or state change. The previously completed `close_operations` record remains unchanged.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_042
**Scenario Title:** Acceptance — AC-05: redeem on already-closed bot returns E-EXBOT-012
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-05, E-EXBOT-012
**Test Type:** Acceptance
**Description:** Verify AC-05: when a `user_redeem` message is processed for a bot with `bots.lifecycle_state='closed'`, the Worker returns E-EXBOT-012 (HTTP 409): "Bot is already closed. No action needed." No HL mutation, no new `close_operations` row, and no state change must occur.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_043
**Scenario Title:** Acceptance — AC-06: LP-portion guaranteed even when HL is unavailable at hedge close time
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-06 (inferred), BR-EXBOT-006
**Test Type:** Acceptance
**Description:** Verify AC-06 (inferred): when HL API is unreachable at the time of hedge close, LP-portion USDC already returned on-chain is preserved. `close_operations.state` transitions to `residual_hl_liability`. BR-EXBOT-006 is enforced: HL unavailability must never block or reverse LP repayment.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_044
**Scenario Title:** Acceptance — AC-07: light-check is fully suppressed while bot is in lp_closing state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-07 (inferred), states.md
**Test Type:** Acceptance
**Description:** Verify AC-07 (inferred): while `bots.lifecycle_state='lp_closing'`, the light-check worker evaluates this bot and produces zero `hedge-sync` enqueue events. The bot must remain invisible to hedge-sync scheduling until `lifecycle_state` exits `lp_closing`.
**Test Focus:** State transition


---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| HL-portion USDC amount calculation formula | BLOCKED: I-02 — UC không định nghĩa công thức tính HL-portion (tổng từ HL close position minus fees/funding hay khác). Không thể viết expected result số tiền cụ thể. | Resolve qua BA: cần công thức hoặc source of truth cho HL-portion amount trước khi thiết kế TC verify số tiền. |
| UserLockDO behavior in user_redeem flow | BLOCKED: I-03 — UC và flows.md F-04 không document UserLockDO cho user_redeem (khác với hedge-sync). Race condition behavior khi concurrent hedge-sync + user_redeem chưa rõ. | Resolve qua BA/Tech Lead: xác nhận UserLockDO có được dùng trong user_redeem không, và behavior khi lock contention xảy ra. |
| close_operations initial state on record creation | BLOCKED: I-04 — UC step 7 dùng notation "lp_closed→funds_returned" (ambiguous); states.md liệt kê full state machine khác. Initial state khi Worker tạo record chưa được chốt. | Resolve qua BA: xác nhận initial state là 'lp_closed', 'funds_returned', hay 'requested'. Sau đó update TS_004/TS_010. |
| Admin notification content for residual_hl_liability | BLOCKED: I-05 — message code và nội dung notification khi A2 xảy ra chưa được định nghĩa trong message-list.md. TS_020 được thiết kế nhưng expected result cho notification body bị để trống. | Resolve qua BA: định nghĩa message code (E-EXBOT-?) và nội dung notification cho A2 flow. |
| bots.lifecycle_state after residual_hl_liability | BLOCKED: I-06 — UC §5 không mô tả postcondition cho A2. states.md không có 'residual_hl_liability' trong bots.lifecycle_state enum. Không biết bot ở state nào sau A2. | Resolve qua BA: xác nhận bots.lifecycle_state và bots.status sau khi A2 path hoàn tất. |
| Reconcile failure behavior in user_redeem context | BLOCKED: I-08 — khi reconcile thấy HL position ≠ 0 sau closeShortReduceOnlyIoc, behavior không được document. Trong hedge-sync thì → SAFE_MODE, nhưng user_redeem context (LP đã thanh lý) có áp dụng cùng rule không? | Resolve qua BA: xác nhận behavior khi reconcile mismatch trong user_redeem path (SAFE_MODE? residual_hl_liability? retry?). |
| FR-EXBOT-071 requirement traceability | BLOCKED: I-01 (Blocker) — FR-EXBOT-071 được cite trong UC FR Trace nhưng không tồn tại trong frd.md hay spec.md. Coverage bị thiếu hoặc FR Trace sai. | Resolve qua BA: xác nhận FR-EXBOT-071 là lỗi đánh máy hay FR bị thiếu. Nếu FR thực sự cần tạo, bổ sung scenarios sau khi FR được định nghĩa. |
| Event watcher missed-event recovery | BLOCKED: UC §3 step 3 mention event watcher có thể miss event nhưng không mô tả retry/recovery mechanism. | Resolve qua BA/Tech Lead: xác nhận có fallback mechanism nào không (polling, re-scan). |
| Performance / load testing | OUT-OF-SCOPE: throughput, latency benchmarks, load simulation nằm ngoài phạm vi skill này. | Defer to performance test specialist. |
| Security penetration testing | OUT-OF-SCOPE: beyond functional auth (wallet ownership check covered in TS_034). | Defer to security specialist. |

