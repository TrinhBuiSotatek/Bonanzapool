# Test Scenarios — UC-EXBOT-user-redeem User-Initiated LP-First Redemption

> Source: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260707_v4.md
> Generated: 2026-07-07
> Author: QC Func Scenario Design ExBot Agent
> Version: v2
> Domain/Architecture: AWS Lambda Workers + Aurora PostgreSQL + SQS + Redis Redlock (ElastiCache) + Hyperliquid + BnzaExVault (on-chain) + close_operations state machine
>
> **Delta from v1:** Architecture updated to AWS arc (Aurora PostgreSQL replaces D1; Redis Redlock via ElastiCache replaces UserLockDO). Resolved blockers I-01, I-04, I-05, I-06, I-08, I-11 applied to existing scenarios (TS_004, TS_010, TS_019–021, TS_050). New scenarios TS_045–TS_053 added covering: Redis Redlock in user_redeem flow, hedge_close_pending state, retry exhaustion path, precondition states (paused/safe_mode), reconcile mismatch producing residual_hl_liability, bots.lifecycle_state='error' after A2. Remaining blocked areas carried forward to ⚠️ Out-of-Scope Flags.

---

## UC-EXBOT-user-redeem — User-Initiated LP-First Redemption

---

### Scenario ID: TS_UC-EXBOT-user-redeem_001
**Scenario Title:** Happy path — investor redeems successfully, LP-portion returned on-chain and HL hedge closed within SLA
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 main flow, FR-EXBOT-070, NFR-EXBOT-003, AC-EXBOT-004-1
**Test Type:** End-to-End
**Description:** Trigger the full user_redeem pipeline when a valid investor calls `BnzaExVault.redeem(tokenId)` on-chain with the bot in `active` state. The event watcher detects `RedemptionEvent`, enqueues to `user_redeem` queue (highest priority). Worker processes: acquires Redis Redlock, calls `closeShortReduceOnlyIoc`, cancels stop via `replaceStopProtected(size=0)`, reconcile confirms HL position = 0, HL-portion USDC is transferred to the investor via RedemptionQueue. The system must reach `close_operations.state='done'` and `bots.lifecycle_state='closed'` within the 5-minute SLA window.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_002
**Scenario Title:** LP-portion USDC is returned to investor in the same on-chain transaction as the redeem call
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 1-3, FR-EXBOT-070, BR-EXBOT-006
**Test Type:** Functional
**Description:** Verify that when `BnzaExVault.redeem(tokenId)` is called on-chain, the LP position is liquidated and LP-portion USDC appears at the investor's wallet address in the same transaction — not asynchronously after queue processing. The off-chain Worker's execution must not be a prerequisite for LP-portion delivery.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_003
**Scenario Title:** RedemptionEvent is detected by event watcher and enqueued to user_redeem queue with highest priority
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 4-5, flows.md F-04
**Test Type:** Integration
**Description:** After `BnzaExVault.redeem(tokenId)` emits `RedemptionEvent(botId, redeemTxHash, userAddress)` on-chain, verify the event watcher picks up the event and enqueues a message `{botId, redeemTxHash, userAddress}` to the `user_redeem` SQS queue at highest priority. The message must appear in the queue before any Worker processing begins.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_004
**Scenario Title:** Worker creates close_operations record with initial state='requested' on first message receipt
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7, erd.md, FR-EXBOT-070
**Test Type:** Functional
**Description:** Verify that when the Worker dequeues the `user_redeem` message for the first time, it inserts a row into `close_operations` with `kind='user_redeem'`, `state='requested'`, and a unique `idempotency_key`. The insertion must occur before any HL mutation is attempted. The initial state must be `requested` — not `lp_closed` or `funds_returned`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_005
**Scenario Title:** bots.lifecycle_state transitions from active to lp_closing when close_operations record is created
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7, states.md
**Test Type:** Data/State
**Description:** Verify that immediately after `close_operations` is inserted with `kind='user_redeem'`, `bots.lifecycle_state` transitions from `active` to `lp_closing`. Both writes to Aurora PostgreSQL must be consistent — there must be no window where `close_operations` exists but `lifecycle_state` is still `active`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_006
**Scenario Title:** light-check worker skips the bot entirely while lifecycle_state is lp_closing
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** states.md, UC-EXBOT-user-redeem §3 step 7
**Test Type:** Integration
**Description:** After `close_operations` is created and `bots.lifecycle_state='lp_closing'`, trigger a light-check evaluation for the same bot. Verify the light-check worker does not enqueue any `hedge-sync` message for this bot. Stop monitoring suppression during `lp_closing` must be confirmed.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_007
**Scenario Title:** HL short position is closed via closeShortReduceOnlyIoc (full close, not delta-only)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 9, FR-EXBOT-020 (full-close exception for bot close path), FR-EXBOT-070
**Test Type:** Functional
**Description:** Verify that the Worker calls `closeShortReduceOnlyIoc` with the full short size (not a delta-only partial close) as part of the user_redeem flow. This is the permitted full-close exception per FR-EXBOT-020 when target size = 0 (bot close path). The order must use a deterministic `cloid`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_008
**Scenario Title:** Stop order is cancelled via replaceStopProtected(size=0), not by direct cancel
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 10, FR-EXBOT-032
**Test Type:** Functional
**Description:** Verify that when the Worker cancels the existing stop order on Hyperliquid as part of the close flow, it uses the INV-STOP protocol via `replaceStopProtected(size=0)`. A direct `cancelOrder` call outside this protocol is forbidden. After the call, `hedge_legs.stop_order_id` and `stop_cloid` in Aurora PostgreSQL must be cleared or marked as cancelled.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_009
**Scenario Title:** Post-close reconcile verifies HL position is exactly zero before marking hedge_closed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 11, FR-EXBOT-023
**Test Type:** Functional
**Description:** After `closeShortReduceOnlyIoc` is submitted, verify the Worker fetches `clearinghouseState` from Hyperliquid to confirm the actual short position size = 0. The `close_operations.state` must not advance to `hedge_closed` until reconcile confirms size = 0. No `done` state must be set before this confirmation.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_010
**Scenario Title:** close_operations state machine progresses correctly through the full happy path sequence
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7-15, states.md, erd.md
**Test Type:** Data/State
**Description:** Verify `close_operations.state` transitions through the full expected sequence: `requested` → `lp_closed` → `funds_returned` → `hedge_closed` (after reconcile confirms HL position = 0) → `done` (after HL-portion USDC transfer completes). Each state must be persisted to Aurora PostgreSQL before the next step begins; no state must be skipped. The on-chain guarantee (LP liquidated = `lp_closed`; LP-portion sent = `funds_returned`) is asserted by the Worker from the on-chain event — not by re-verifying on-chain.
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
**Req-ID:** UC-EXBOT-user-redeem §3 step 14-15, states.md
**Test Type:** Data/State
**Description:** Verify that `bots.lifecycle_state` transitions to `closed` and `bots.status` to `closed` only after the HL-portion USDC transfer has been recorded in the RedemptionQueue ledger, and `close_operations.state` is already `done`. Neither field must be set prematurely during any intermediate step.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_013
**Scenario Title:** Admin receives SLA breach alert when hedge close exceeds 5 minutes from event detection
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A1, NFR-EXBOT-003, E-EXBOT-010, AC-EXBOT-004-2
**Test Type:** Functional
**Description:** Trigger a user_redeem flow where the hedge close operation is delayed beyond 5 minutes from the moment `RedemptionEvent` is detected. Verify the system enqueues an admin alert with message E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." The hedge close must continue executing after the alert — the SLA breach must not abort the operation.
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
**Req-ID:** UC-EXBOT-user-redeem §4 A2, BR-EXBOT-006, AC-EXBOT-004-3
**Test Type:** Functional
**Description:** Simulate a scenario where the LP position is already liquidated on-chain (LP-portion USDC delivered to investor) and then the Worker's `closeShortReduceOnlyIoc` call to Hyperliquid fails with an unrecoverable error. Verify that the LP-portion USDC already delivered on-chain is NOT reversed, blocked, or withheld. BR-EXBOT-006: "user_redeem LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user."
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_019
**Scenario Title:** close_operations transitions to residual_hl_liability and bots.lifecycle_state transitions to error when hedge close fails
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2, §5 postconditions A2, erd.md, AC-EXBOT-004-3
**Test Type:** Data/State
**Description:** When `closeShortReduceOnlyIoc` fails after LP-portion has already been returned on-chain, verify: (a) `close_operations.state` transitions to `residual_hl_liability`; (b) `close_operations.residual_amount` is populated with the outstanding HL liability amount as BigDecimal string; (c) `bots.lifecycle_state` transitions to `error`; (d) `bots.status` transitions to `error`. No `done` state must be set in `close_operations`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_020
**Scenario Title:** Admin notification E-EXBOT-024 is enqueued when hedge close fails and residual_hl_liability is set
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2, §5 postconditions A2, E-EXBOT-024
**Test Type:** Functional
**Description:** When `close_operations.state` transitions to `residual_hl_liability`, verify the Worker enqueues an admin notification with message E-EXBOT-024: "User redemption hedge close failed. Manual intervention required." The notification must be enqueued regardless of whether the SLA has been breached. The admin alert is an internal notification requiring manual HL position close.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_021
**Scenario Title:** LP-portion unconditional guarantee holds when HL API is completely unreachable during hedge close
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** BR-EXBOT-006, UC-EXBOT-user-redeem §4 A2
**Test Type:** Functional
**Description:** Simulate the Hyperliquid API being completely unreachable (all HL calls return connection errors) at the time the Worker attempts to close the hedge. Verify that LP-portion USDC already returned on-chain is not affected, and `close_operations.state` transitions to `residual_hl_liability`. BR-EXBOT-006 must be enforced: HL unavailability is an HL problem, not an investor problem.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_022
**Scenario Title:** Duplicate queue message is detected via close_operations idempotency_key UNIQUE constraint
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, erd.md
**Test Type:** Functional
**Description:** Deliver a `user_redeem` queue message for a bot whose `close_operations` record with the same `idempotency_key` already exists (a redelivery scenario). Verify the Worker detects the duplicate via the UNIQUE constraint on `close_operations.idempotency_key`, performs no HL mutation, creates no additional Aurora PostgreSQL records, and exits gracefully without error.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_023
**Scenario Title:** Duplicate queue message is detected via queue_idempotency message_id UNIQUE constraint
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 6, §4 A3, FR-EXBOT-010, erd.md
**Test Type:** Functional
**Description:** Deliver a `user_redeem` SQS message with a `message_id` that already exists in `queue_idempotency` (same message redelivered by SQS). Verify the Worker hits the UNIQUE constraint at the `queue_idempotency` insert step and returns immediately without performing any HL mutation or creating duplicate `close_operations` rows.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_024
**Scenario Title:** Two concurrent deliveries of the same user_redeem message result in exactly one hedge close execution
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, FR-EXBOT-010, erd.md
**Test Type:** Integration
**Description:** Simulate two Workers receiving the same `user_redeem` message simultaneously (concurrent SQS delivery). Verify that exactly one Worker proceeds to execute the hedge close; the other is blocked by either the `queue_idempotency.message_id` UNIQUE constraint or the `close_operations.idempotency_key` UNIQUE constraint. Only one `close_operations` row exists; only one HL `closeShortReduceOnlyIoc` call is made.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_025
**Scenario Title:** Worker returns E-EXBOT-012 when user_redeem is triggered for an already-closed bot
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 6, E-EXBOT-012
**Test Type:** Functional
**Description:** Deliver a `user_redeem` message for a bot that already has `bots.lifecycle_state='closed'`. Verify the Worker detects the closed state early in processing and returns E-EXBOT-012 (HTTP 409): "Bot is already closed. No action needed." No HL mutation, no new `close_operations` row, no state change must occur.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_026
**Scenario Title:** Worker handles gracefully when user_redeem is triggered for a bot already in lp_closing state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** E-EXBOT-012, states.md
**Test Type:** Functional
**Description:** Deliver a second `user_redeem` message for a bot that is already in `lifecycle_state='lp_closing'` (a close operation is already in progress). Verify the Worker recognises the state as "already closing" and either returns E-EXBOT-012 or detects the duplicate via `close_operations.idempotency_key` — in either case, no second HL close is initiated and no duplicate `close_operations` row is created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_027
**Scenario Title:** close_operations record matches the on-chain redeemTxHash from the RedemptionEvent
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 7, erd.md
**Test Type:** Data/State
**Description:** After a successful user_redeem flow, verify that the `close_operations` record's reference to `redeemTxHash` matches the on-chain transaction hash from the `RedemptionEvent`. This confirms off-chain Aurora PostgreSQL state is anchored to the correct on-chain event and not a fabricated or stale value.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_028
**Scenario Title:** No duplicate HL-portion transfer occurs on user_redeem message redelivery after close_operations=done
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, erd.md, FR-EXBOT-010
**Test Type:** Integration
**Description:** Simulate SQS redelivery of a `user_redeem` message after the full pipeline has already completed (`close_operations.state='done'`, HL-portion already sent). Verify the Worker does not re-execute the HL-portion transfer and does not create a second RedemptionQueue entry for the same investor. Total USDC received by the investor from this redeem must equal LP-portion + HL-portion, not LP-portion + 2*HL-portion.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_029
**Scenario Title:** hedge_legs stop fields are cleared after stop is cancelled via replaceStopProtected
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 10, FR-EXBOT-032
**Test Type:** Data/State
**Description:** After `replaceStopProtected(size=0)` successfully cancels the stop order on Hyperliquid, verify that `hedge_legs.stop_order_id` and `hedge_legs.stop_cloid` are cleared or nulled in Aurora PostgreSQL. The database state must reflect that no active stop order exists after the cancel. No stale stop reference must remain.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_030
**Scenario Title:** hedge-sync worker does not interfere with user_redeem while bot is in lp_closing state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** states.md, UC-EXBOT-user-redeem §3 step 7
**Test Type:** Integration
**Description:** While a user_redeem is in progress (`bots.lifecycle_state='lp_closing'`), verify that any concurrent light-check tick does not enqueue a `hedge-sync` message for this bot, and that any `hedge-sync` message already in the queue for this bot is either discarded or returns early due to the `lp_closing` state. No hedge mutation must occur during the close operation.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_031
**Scenario Title:** close_operations idempotency_key prevents double settlement when two separate close signals arrive
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** FR-EXBOT-070, erd.md close_operations.idempotency_key UNIQUE
**Test Type:** Integration
**Description:** Simulate a scenario where two separate triggering signals for the same redeem arrive — for example, an SQS redelivery and a manual retry — both attempting to insert a `close_operations` row with the same `idempotency_key`. Verify only one row is inserted (UNIQUE constraint blocks the second), and only one HL hedge close is executed. No double settlement results.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_032
**Scenario Title:** Worker checks bot is not already closing/closed before attempting any HL mutation
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 6, E-EXBOT-012, states.md
**Test Type:** Functional
**Description:** Verify the Worker checks `bots.lifecycle_state` and `bots.status` early in the processing pipeline — before acquiring any Redis Redlock, before creating `close_operations`, and before calling Hyperliquid — to guard against acting on a bot that has already entered `closing` or `closed` state. If the state is invalid, E-EXBOT-012 (409) must be returned with no side effects.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_033
**Scenario Title:** HL rate limiter is consulted before closeShortReduceOnlyIoc is called
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** FR-EXBOT-070, NFR-EXBOT-004, srs/spec.md FR-EXBOT-090 (HL Rate Limiter via ElastiCache)
**Test Type:** Integration
**Description:** Verify the Worker consults the HL rate limiter (ElastiCache Redis) before calling `closeShortReduceOnlyIoc` on Hyperliquid. If the rate limiter returns allowed=false with a retryAfterMs value, the Worker must not call Hyperliquid immediately; it must respect the retry delay. Given the high priority of `user_redeem` queue, confirm whether the rate limit back-off behavior is the same as other workers or privileged.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_034
**Scenario Title:** Investor who does not own the tokenId cannot trigger user_redeem flow
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §2, §3 precondition (investor holds LP NFT redemption rights)
**Test Type:** Functional
**Description:** Attempt to call `BnzaExVault.redeem(tokenId)` on-chain using a wallet address that does not own the specified `tokenId`. Verify the on-chain transaction is reverted by the BnzaExVault contract. No `RedemptionEvent` is emitted, no SQS message is enqueued, and no off-chain Worker processing occurs.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-user-redeem_035
**Scenario Title:** cloid used for closeShortReduceOnlyIoc is deterministic and idempotent for the same redeem attempt
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 9, srs/spec.md FR-EXBOT-022
**Test Type:** Functional
**Description:** Verify that the `cloid` used when calling `closeShortReduceOnlyIoc` is computed deterministically using FR-EXBOT-022 formula: first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}")). If the Worker retries the same hedge close attempt (same logical operation), the same `cloid` must be produced. A different redeem for a different bot must produce a different `cloid`.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_036
**Scenario Title:** Retry of closeShortReduceOnlyIoc with same cloid does not double-close the HL position
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 9, srs/spec.md FR-EXBOT-022
**Test Type:** Functional
**Description:** Simulate a scenario where `closeShortReduceOnlyIoc` is submitted but the response is ambiguous (timeout or network error). When the Worker retries with the same `cloid`, verify that Hyperliquid recognises the duplicate cloid and does not execute a second close. Reconcile after retry must confirm HL position = 0 with only one close execution.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_037
**Scenario Title:** NFR — HL-portion USDC amount stored in close_operations.usdc_amount uses BigDecimal precision
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** NFR-EXBOT-008, erd.md close_operations.usdc_amount (TEXT BigDecimal)
**Test Type:** Functional
**Description:** After a successful user_redeem, verify that `close_operations.usdc_amount` is stored as a BigDecimal string (TEXT), not as a JavaScript Number or float. No floating-point rounding artefacts must appear in the stored value. Any intermediate computation of the HL-portion amount must use BigDecimal arithmetic throughout.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_038
**Scenario Title:** Acceptance — AC-EXBOT-004-1: full happy path within SLA completes all postconditions
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-EXBOT-004-1, us-004.md, NFR-EXBOT-003
**Test Type:** Acceptance
**Description:** Verify all AC-EXBOT-004-1 postconditions are met end-to-end: LP-portion USDC in investor wallet from the same on-chain tx; `close_operations.state='done'` reached within 5 minutes of event detection; `bots.lifecycle_state='closed'`; HL position = 0 confirmed by reconcile; HL-portion USDC sent via RedemptionQueue. All five conditions must be true simultaneously at completion.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_039
**Scenario Title:** Acceptance — AC-EXBOT-004-2: SLA breach triggers admin alert and hedge close still completes
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-EXBOT-004-2, us-004.md, E-EXBOT-010
**Test Type:** Acceptance
**Description:** Verify AC-EXBOT-004-2 postconditions: after hedge close exceeds 5 minutes, E-EXBOT-010 alert is sent to admin with exact message "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned."; hedge close continues without abort; `close_operations.state` eventually reaches `done`; LP-portion is not reversed.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_040
**Scenario Title:** Acceptance — AC-EXBOT-004-3: hedge close failure leaves LP-portion untouched and sets residual_hl_liability
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** AC-EXBOT-004-3, us-004.md, BR-EXBOT-006
**Test Type:** Acceptance
**Description:** Verify AC-EXBOT-004-3 postconditions when HL close fails: `close_operations.state='residual_hl_liability'`; `close_operations.residual_amount` is populated; `bots.lifecycle_state='error'`; LP-portion USDC already sent on-chain is NOT reversed or blocked; admin notification E-EXBOT-024 is enqueued. BR-EXBOT-006 must hold: the on-chain LP-portion is permanently protected.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_041
**Scenario Title:** Acceptance — duplicate message delivery results in graceful no-op
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A3, erd.md
**Test Type:** Acceptance
**Description:** Verify that when the Worker receives a duplicate `user_redeem` message (same `idempotency_key` or `message_id` already processed), it performs no HL mutation, creates no additional Aurora PostgreSQL rows, and exits without error or state change. The previously completed `close_operations` record remains unchanged.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_042
**Scenario Title:** Acceptance — redeem on already-closed bot returns E-EXBOT-012
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** E-EXBOT-012, UC-EXBOT-user-redeem §3 step 6
**Test Type:** Acceptance
**Description:** Verify that when a `user_redeem` message is processed for a bot with `bots.lifecycle_state='closed'`, the Worker returns E-EXBOT-012 (HTTP 409): "Bot is already closed. No action needed." No HL mutation, no new `close_operations` row, and no state change must occur.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_043
**Scenario Title:** Acceptance — LP-portion guaranteed even when HL is unavailable at hedge close time
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** BR-EXBOT-006, UC-EXBOT-user-redeem §4 A2
**Test Type:** Acceptance
**Description:** Verify that when HL API is unreachable at the time of hedge close, LP-portion USDC already returned on-chain is preserved. `close_operations.state` transitions to `residual_hl_liability`. BR-EXBOT-006 is enforced: HL unavailability must never block or reverse LP repayment.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_044
**Scenario Title:** Acceptance — light-check is fully suppressed while bot is in lp_closing state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** states.md, UC-EXBOT-user-redeem §3 step 7
**Test Type:** Acceptance
**Description:** Verify that while `bots.lifecycle_state='lp_closing'`, the light-check worker evaluates this bot and produces zero `hedge-sync` enqueue events. The bot must remain invisible to hedge-sync scheduling until `lifecycle_state` exits `lp_closing`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_045
**Scenario Title:** Worker acquires Redis Redlock before calling closeShortReduceOnlyIoc on HL
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 8, srs/spec.md FR-EXBOT-092, FR-EXBOT-026
**Test Type:** Functional
**Description:** Verify the Worker calls UserLock.acquire(holderToken, ttlMs=90_000, idempotencyKey) on the Redis Redlock (ElastiCache) before submitting any HL mutation. The lock must be held for the duration of the hedge close sequence (steps 9-11). If acquire() returns acquired=false, the Worker must re-queue the message with a delay per FR-EXBOT-026 and not proceed to HL.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_046
**Scenario Title:** Redis Redlock is released after hedge close sequence completes (happy path)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 8-12, srs/spec.md FR-EXBOT-092
**Test Type:** Functional
**Description:** After the hedge close sequence completes successfully (reconcile confirms HL position = 0, `close_operations.state='hedge_closed'`), verify the Worker calls UserLock.release(holderToken, idempotencyKey?) to release the Redis Redlock. The lock must not remain held after the close sequence finishes. A subsequent attempt to acquire the lock for the same user must succeed.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_047
**Scenario Title:** Redis Redlock contention — user_redeem defers when lock is held by concurrent hedge-sync
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 8, srs/spec.md FR-EXBOT-092, FR-EXBOT-026
**Test Type:** Integration
**Description:** Simulate a scenario where the hedge-sync Worker holds the Redis Redlock for the same user when the user_redeem Worker attempts to acquire it. Verify the user_redeem Worker receives acquired=false from Redlock, re-queues the message with the specified delay, and does not attempt any HL mutation. The hedge close must be attempted only after the lock becomes available on the next delivery.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_048
**Scenario Title:** close_operations passes through hedge_close_pending state before transitioning to hedge_closed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** states.md close_operations table (hedge_close_pending has mark for user_redeem column), UC-EXBOT-user-redeem §3, I-N3 (open)
**Test Type:** Data/State
**Description:** Verify whether `close_operations.state` transitions through `hedge_close_pending` before reaching `hedge_closed` during the user_redeem flow. The states.md close_operations table confirms `hedge_close_pending` is a valid state for user_redeem. The UC main flow steps 7-12 do not explicitly show when this state is entered. Verify the actual transition sequence includes funds_returned to hedge_close_pending to hedge_closed, and identify the trigger for the hedge_close_pending transition. Note: expected result for the exact transition trigger is pending BA resolution of I-N3.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_049
**Scenario Title:** closeShortReduceOnlyIoc retry exhaustion (3 retries) triggers residual_hl_liability path
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 9, §4 A2, E-EXBOT-024
**Test Type:** Functional
**Description:** Simulate Hyperliquid rejecting or timing out `closeShortReduceOnlyIoc` for all 3 retry attempts. Verify: after the 3rd failed attempt the Worker does NOT retry a 4th time; `close_operations.state` transitions to `residual_hl_liability`; `bots.lifecycle_state='error'`; admin notification E-EXBOT-024 is enqueued with message "User redemption hedge close failed. Manual intervention required." LP-portion remains untouched.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_050
**Scenario Title:** closeShortReduceOnlyIoc succeeds on retry 2 (not first attempt)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 9
**Test Type:** Functional
**Description:** Simulate `closeShortReduceOnlyIoc` failing on the first attempt (HL rejects or times out) but succeeding on the second retry. Verify: no `residual_hl_liability` state is set; the hedge close sequence continues normally (reconcile, hedge_closed, HL-portion transfer, done); no admin error notification is sent; `bots.lifecycle_state` transitions to `closed` at completion.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_051
**Scenario Title:** user_redeem is initiated from a bot in paused state (non-active precondition)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 preconditions ("Bot status='active' or paused/safe_mode — user may redeem from any non-closed state"), I-N1 (partially open)
**Test Type:** Functional
**Description:** Trigger BnzaExVault.redeem(tokenId) on-chain when the bot is in `paused` state (not `active`). Verify the Worker accepts the redemption message and processes the full close sequence without rejecting the request due to the non-active state. The `close_operations` record must be created and the flow must complete normally (or reach `residual_hl_liability` if HL close fails).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_052
**Scenario Title:** user_redeem is initiated from a bot in safe_mode state (non-active precondition)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 preconditions ("user may redeem from any non-closed state"), I-N1 (partially open)
**Test Type:** Functional
**Description:** Trigger BnzaExVault.redeem(tokenId) on-chain when the bot is in `safe_mode` state. Verify the Worker accepts the redemption message and does not block the close flow due to safe_mode. The SAFE_MODE constraint (which protects an active LP) does not apply here because the redeem event itself initiates LP liquidation. The close sequence must proceed normally.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_053
**Scenario Title:** Reconcile mismatch (HL position not zero after closeShortReduceOnlyIoc) triggers residual_hl_liability path
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated LP-First Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 11, §4 A2, E-EXBOT-024
**Test Type:** Functional
**Description:** Simulate `closeShortReduceOnlyIoc` returning a success response but the reconcile step (fetch clearinghouseState from HL) showing the actual short position size is not 0 (partial fill or HL-side discrepancy). Verify: the Worker does NOT advance to `hedge_closed`; `close_operations.state` transitions to `residual_hl_liability`; `close_operations.residual_amount` is populated with the remaining liability; `bots.lifecycle_state='error'`; admin notification E-EXBOT-024 is enqueued. SAFE_MODE must NOT be applied — LP already liquidated.
**Test Focus:** Error/Exception

---

## Warning: Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| HL-portion USDC amount calculation formula | BLOCKED: I-02 (High, Open) — UC §3 step 13 does not define: (a) how HL-portion amount is calculated (total from HL position close minus fees/funding or other formula); (b) which component executes the on-chain USDC transfer; (c) whether the tx hash is stored in close_operations.hedge_close_tx. Without this, expected results for scenarios verifying the HL-portion amount cannot be written. | Resolve via BA/Tech Lead: define the formula and source-of-truth for HL-portion amount, the transfer executor, and the tx hash storage field. Then design specific amount-verification scenarios. |
| hedge_close_pending trigger timing in UC main flow | BLOCKED: I-N3 (Medium, Open) — states.md confirms hedge_close_pending is valid for user_redeem (TS_048 captures the state-transition check), but the UC main flow does not document when the transition from funds_returned to hedge_close_pending is triggered. Expected result for the trigger step is incomplete until BA resolves I-N3. | Resolve via BA: confirm the trigger that moves close_operations.state to hedge_close_pending in the user_redeem flow, and update the UC main flow to include this transition. |
| Specific allowed pre-states for user_redeem | BLOCKED: I-N1 (Medium, Open) — UC §2 says "any non-closed state" but states.md does not enumerate all permitted states. Specifically: hedge_stopped_cooldown, lp_rebalancing, error — whether redeem is permitted from these states is unconfirmed. TS_051/TS_052 cover paused/safe_mode which are explicitly named in the UC. | Resolve via BA: enumerate all permitted and blocked pre-states in states.md. Then add EP scenarios per state. |
| Retry strategy detail for closeShortReduceOnlyIoc (in-invocation vs re-queue, backoff delay) | BLOCKED: I-N2 (Low, Open) — retry count = 3 is confirmed (UC step 9), but whether retries are within the same Lambda invocation or re-queue with delay, and whether there is backoff between retries, is unspecified. Affects timing of when residual_hl_liability is reached. | Resolve via BA/Tech Lead: confirm retry execution model and any backoff. Low priority — does not block happy-path or residual_hl_liability path scenarios. |
| FR numbering for Redlock: spec.md FR-EXBOT-092 vs frd.md FR-EXBOT-091 | NOTE: I-N4 (Low, Open) — scenarios reference FR-EXBOT-092 per spec.md convention (consistent with v4 audit report). frd.md uses FR-EXBOT-091 for the same feature. Tester should be aware when cross-referencing both documents. | BA to synchronise FR numbering between spec.md and frd.md. No scenario impact — Redlock behavior is consistent across both sources. |
| Performance / load testing | OUT-OF-SCOPE: throughput, latency benchmarks, load simulation are outside this skill's scope. | Defer to performance test specialist. |
| Security penetration testing | OUT-OF-SCOPE: beyond functional auth (wallet ownership check covered in TS_034). | Defer to security specialist. |
