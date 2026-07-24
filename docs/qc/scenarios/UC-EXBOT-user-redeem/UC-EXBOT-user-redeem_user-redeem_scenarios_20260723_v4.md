# Test Scenarios — UC-EXBOT-user-redeem: User Redeem (LP Liquidation + HL Settlement)

| Field | Value |
|---|---|
| Document title | Test Scenarios — UC-EXBOT-user-redeem User Redeem |
| Date created | 2026-07-23 |
| Author/Agent | qc-func-scenario-design-exbot |
| Version | v4 |

> Source: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260723_v6.md
> Generated: 2026-07-23
> Domain/Architecture: AWS Lambda + Aurora PostgreSQL + Redis Redlock (ElastiCache) + SQS FIFO + Hyperliquid API + BnzaExVault (on-chain Base/Optimism) + RedemptionQueue (on-chain FIFO)

---

## UC-EXBOT-user-redeem — User Redeem (LP Liquidation + HL Settlement)

---

### Scenario ID: TS_UC-EXBOT-user-redeem_001
**Scenario Title:** Full happy path — on-chain redeem triggers complete LP liquidation and HL settlement chain
**UC Reference:** UC-EXBOT-user-redeem — User Redeem
**Req-ID:** UC-EXBOT-user-redeem §3 Main Flow (steps 1–17); AC-001
**Test Type:** End-to-End
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` on-chain; the system processes the full flow: event watcher detects the `RedemptionEvent`, enqueues to the `user_redeem` SQS FIFO queue, the Redeem Worker closes the LP position, returns the LP-portion to the investor, closes the HL short hedge, creates a `redemption_requests` row, submits `hl_withdraw`, selects the reserved-liquidity or CCTP path, and completes `RedemptionQueue.fulfillRequest` on-chain. Verify: `close_operations.state=done`, `redemption_requests.status=fulfilled`, `bots.lifecycle_state=closed`, and the investor receives the HL-portion USDC on-chain.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_002
**Scenario Title:** On-chain RedemptionEvent detected and enqueued to user_redeem SQS FIFO queue
**UC Reference:** UC-EXBOT-user-redeem §3 steps 2–4
**Req-ID:** FR-EXBOT-010; UC-EXBOT-user-redeem §3 step 3
**Test Type:** Integration
**Description:** After `BnzaExVault.redeem(tokenId)` is confirmed on-chain, the event watcher picks up the `RedemptionEvent` and enqueues a message to the `user_redeem` queue. Verify: message is present in the correct SQS FIFO queue with the correct `botId`, `tokenId`, and `redeemTxHash`; no other queue receives the message.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-user-redeem_003
**Scenario Title:** Worker creates close_operations row with state=requested on first message receipt
**UC Reference:** UC-EXBOT-user-redeem §3 step 5; UC-EXBOT-user-redeem §3 step 7
**Req-ID:** FR-EXBOT-073; UC-EXBOT-user-redeem §3 step 5
**Test Type:** Data/State
**Description:** When the Redeem Worker processes a user_redeem queue message for a bot with no existing `close_operations` row for that `redeemTxHash`, it inserts a new row with `state='requested'` and the correct `idempotency_key`. Verify: `close_operations` row exists with `state='requested'`, `idempotency_key = user-redeem:{botId}:{redeemTxHash}`, and `bots.lifecycle_state` has transitioned to `lp_closing`.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_004
**Scenario Title:** close_operations state transitions through full sequence: requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done
**UC Reference:** UC-EXBOT-user-redeem §3 main flow; states.md close_operations
**Req-ID:** FR-EXBOT-073; UC-EXBOT-user-redeem §3 steps 5–16
**Test Type:** Data/State
**Description:** Observe `close_operations.state` at each checkpoint throughout a complete user_redeem execution. Verify each transition is sequential and no state is skipped: `requested` (after INSERT) → `lp_closed` (after LP liquidated on-chain) → `funds_returned` (after LP-portion credited to investor) → `hedge_close_pending` (after Redlock acquired, before HL close call) → `hedge_closed` (after HL position confirmed at 0) → `done` (after `redemption_requests` row created). Verify `done` is set before `hl_withdraw` worker runs.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_005
**Scenario Title:** LP-portion is returned to investor unconditionally before hedge close begins
**UC Reference:** UC-EXBOT-user-redeem §3 steps 5–7; BR-EXBOT-006
**Req-ID:** BR-EXBOT-006; UC-EXBOT-user-redeem §3 step 7
**Test Type:** Functional
**Description:** When the LP NFT is liquidated by `BnzaExVault.redeem()`, the LP-portion USDC is transferred to the investor on-chain as part of the redemption transaction itself — before the hedge close worker runs. Verify: the investor's on-chain USDC balance increases by the LP-portion amount; `close_operations.usdc_amount` (BigDecimal TEXT) matches the amount; this occurs regardless of whether the subsequent hedge close succeeds or fails. (Business Rule BR-EXBOT-006: "LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user.")
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_006
**Scenario Title:** bots.lifecycle_state transitions active → lp_closing → lp_closed → closing → closed through user_redeem
**UC Reference:** UC-EXBOT-user-redeem §3 full flow; states.md bots
**Req-ID:** UC-EXBOT-user-redeem §3; states.md bots lifecycle
**Test Type:** Data/State
**Description:** Trace `bots.lifecycle_state` throughout the user_redeem execution. Verify sequential transitions: `active` (or any valid pre-redeem state) → `lp_closing` (on queue receipt) → `lp_closed` (on LP liquidation) → `closing` (on hedge close start) → `closed` (when `close_operations.state=done`). Verify that `closed` is set at the same time as `done`, before HL settlement completes.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_007
**Scenario Title:** close_operations INSERT (idempotency record) is created BEFORE Redis Redlock is acquired
**UC Reference:** UC-EXBOT-user-redeem §3 step 5; FR-EXBOT-092
**Req-ID:** FR-EXBOT-092; FR-EXBOT-073; UC-EXBOT-user-redeem §3 steps 5–8; AC-014
**Test Type:** Functional
**Description:** When a new user_redeem message is processed, the `close_operations` row with `state='requested'` is inserted into the database before the system attempts to acquire the Redis Redlock. Verify: if the lock cannot be acquired (lock held by another worker), the `close_operations` row already exists and the idempotency key is recorded. On the next delivery attempt, the worker detects the existing row and resumes without double-inserting.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_011
**Scenario Title:** closeShortReduceOnlyIoc closes the full HL short position (target=0)
**UC Reference:** UC-EXBOT-user-redeem §3 step 9; FR-EXBOT-022
**Req-ID:** FR-EXBOT-022; UC-EXBOT-user-redeem §3 step 9
**Test Type:** Functional
**Description:** After acquiring the Redlock, the worker calls `closeShortReduceOnlyIoc` with target size = 0 (full close). Verify: the HL API receives a `reduceOnly` close order for the full short position size; the `cloid` follows the formula `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` (FR-EXBOT-022); a successful fill is confirmed before state advances to `hedge_closed`.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_012
**Scenario Title:** Stop order cancelled via replaceStopProtected(size=0) as part of hedge close
**UC Reference:** UC-EXBOT-user-redeem §3 step 9; AC-003
**Req-ID:** UC-EXBOT-user-redeem §3 step 9; AC-003
**Test Type:** Functional
**Description:** The system calls `replaceStopProtected(size=0)` to cancel the existing stop order as part of the hedge close. Verify: stop order cancelled (HL shows no open stop); `hedge_legs` stop fields cleared in DB; main position close proceeds without interference.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_013
**Scenario Title:** closeShortReduceOnlyIoc retries use deterministic cloid (up to 3 in-invocation retries, no double-close)
**UC Reference:** UC-EXBOT-user-redeem §3 step 9; FR-EXBOT-022
**Req-ID:** FR-EXBOT-022; UC-EXBOT-user-redeem §3 step 9
**Test Type:** Functional
**Description:** When HL rejects the first `closeShortReduceOnlyIoc` call, the worker retries within the same Lambda invocation using the same deterministic `cloid`. Verify: same `cloid` used on all retries; retry count does not exceed 3; no duplicate close order placed on HL.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_014
**Scenario Title:** Reconcile confirms HL position = 0 before transitioning to hedge_closed
**UC Reference:** UC-EXBOT-user-redeem §3 step 11; AC-005
**Req-ID:** AC-005; UC-EXBOT-user-redeem §3 step 11
**Test Type:** Functional
**Description:** After `closeShortReduceOnlyIoc` returns success, the worker calls the reconcile function. Verify: state advances to `hedge_closed` only when reconcile confirms HL position size = 0; state does NOT advance before reconcile.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_015
**Scenario Title:** Reconcile mismatch (HL position ≠ 0 after close) → residual_hl_liability, not SAFE_MODE
**UC Reference:** UC-EXBOT-user-redeem §4 A2; BR-EXBOT-007
**Req-ID:** BR-EXBOT-007; UC-EXBOT-user-redeem §4 A2; AC-006
**Test Type:** Functional
**Description:** When reconcile finds HL position ≠ 0 after close, the worker transitions to A2: `close_operations.state='residual_hl_liability'`, `bots.lifecycle_state='error'`. Verify: SAFE_MODE NOT activated (BR-EXBOT-007); admin receives E-EXBOT-024 ("User redemption hedge close failed. Manual intervention required."); LP-portion already returned NOT reversed.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-user-redeem_016
**Scenario Title:** 3 closeShortReduceOnlyIoc retries exhausted → residual_hl_liability
**UC Reference:** UC-EXBOT-user-redeem §4 A2; UC-EXBOT-user-redeem §3 step 9
**Req-ID:** UC-EXBOT-user-redeem §4 A2; FR-EXBOT-022
**Test Type:** Functional
**Description:** When all 3 in-invocation retries fail (HL rejects or times out), the worker transitions to `residual_hl_liability`. Verify: `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; E-EXBOT-024 sent to admin; LP-portion not affected.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-user-redeem_017
**Scenario Title:** BR-EXBOT-006 — hedge close failure never blocks or reverses LP-portion return
**UC Reference:** UC-EXBOT-user-redeem §4 A2; BR-EXBOT-006
**Req-ID:** BR-EXBOT-006
**Test Type:** Acceptance
**Description:** When hedge close fails (A2 path), the investor's LP-portion USDC that was returned in steps 5–7 remains with the investor. Verify: on-chain LP-portion transfer not reversed; `close_operations.usdc_amount` preserved; no compensating transaction sent. (Verbatim: "LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user.")
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_018
**Scenario Title:** SLA alert E-EXBOT-010 sent when hedge close exceeds 5 minutes from event detection
**UC Reference:** UC-EXBOT-user-redeem §4 A1; NFR-EXBOT-003
**Req-ID:** NFR-EXBOT-003; UC-EXBOT-user-redeem §4 A1; AC-002
**Test Type:** Functional
**Description:** When elapsed time from on-chain `RedemptionEvent` detection to hedge close completion exceeds 5 minutes, the SLA monitor sends E-EXBOT-010 exactly once. Verify: message text matches verbatim "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned."; hedge close continues after alert; LP-portion already returned.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_019
**Scenario Title:** SLA timer starts at event detection, not at worker start
**UC Reference:** UC-EXBOT-user-redeem §4 A1; NFR-EXBOT-003
**Req-ID:** NFR-EXBOT-003
**Test Type:** Functional
**Description:** The 5-minute SLA clock starts from when the event watcher detects the on-chain `RedemptionEvent`. Verify: queue wait time + worker processing time = total elapsed; if queue wait = 4 min + worker = 2 min = 6 min total, SLA is breached and E-EXBOT-010 fires; SLA is not measured from worker pickup alone.
**Test Focus:** Boundary

### Scenario ID: TS_UC-EXBOT-user-redeem_020
**Scenario Title:** SLA boundary — hedge close at exactly 5 minutes (no alert)
**UC Reference:** UC-EXBOT-user-redeem §4 A1; NFR-EXBOT-003
**Req-ID:** NFR-EXBOT-003
**Test Type:** Functional
**Description:** Hedge close completes at exactly the 5-minute mark from event detection. Verify: E-EXBOT-010 NOT triggered; state advances to `hedge_closed` without alert.
**Test Focus:** Boundary

### Scenario ID: TS_UC-EXBOT-user-redeem_021
**Scenario Title:** SLA boundary — hedge close at 5 minutes + 1 second (alert triggered)
**UC Reference:** UC-EXBOT-user-redeem §4 A1; NFR-EXBOT-003
**Req-ID:** NFR-EXBOT-003
**Test Type:** Functional
**Description:** Hedge close completes 1 second past the 5-minute SLA. Verify: E-EXBOT-010 triggered; message matches verbatim text.
**Test Focus:** Boundary

### Scenario ID: TS_UC-EXBOT-user-redeem_022
**Scenario Title:** Cumulative Redlock re-queue delays count toward SLA breach
**UC Reference:** UC-EXBOT-user-redeem §4 A1; FR-EXBOT-092; NFR-EXBOT-003
**Req-ID:** NFR-EXBOT-003; FR-EXBOT-092
**Test Type:** Functional
**Description:** Multiple Redlock re-queue delays cumulatively exceeding 5 minutes from event detection trigger E-EXBOT-010, even if hedge close eventually succeeds. Verify: SLA clock does not reset on each re-delivery.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_023
**Scenario Title:** Duplicate SQS message (same MessageDeduplicationId) discarded via queue_idempotency
**UC Reference:** UC-EXBOT-user-redeem §4 A3; FR-EXBOT-010
**Req-ID:** FR-EXBOT-010; UC-EXBOT-user-redeem §4 A3; AC-004
**Test Type:** Functional
**Description:** When SQS redelivers the same user_redeem message (same `MessageDeduplicationId`), the worker detects the existing `queue_idempotency` record and discards it without reprocessing. Verify: no new `close_operations` row created; no HL API call made; no duplicate transfer to investor.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_024
**Scenario Title:** Duplicate detected via close_operations idempotency_key (different MessageId, same redeemTxHash)
**UC Reference:** UC-EXBOT-user-redeem §3 step 5; FR-EXBOT-073
**Req-ID:** FR-EXBOT-073; UC-EXBOT-user-redeem §3 step 5
**Test Type:** Functional
**Description:** Two SQS messages with different `MessageId` but same `redeemTxHash` reach the worker. Verify: second worker detects existing `close_operations` row via `idempotency_key = user-redeem:{botId}:{redeemTxHash}`; no second hedge close attempted.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_025
**Scenario Title:** redemption_requests row created with status=pending after hedge_closed is confirmed
**UC Reference:** UC-EXBOT-user-redeem §3 step 13 (post-I-02a); AC-009
**Req-ID:** AC-009; flow-withdraw-close-settlement-ba.md §5 step 4
**Test Type:** Data/State
**Description:** After `close_operations.state` transitions to `hedge_closed`, the system creates a new `redemption_requests` row with `status='pending'` and records the `botId`, `tokenId`, and pre-withdraw `clearinghouseState.withdrawable` snapshot. Verify: row is inserted into `redemption_requests` (NOT `close_operations`); `status='pending'`; the two tables remain distinct — `close_operations.usdc_amount` is the LP-portion, `redemption_requests.principal_amount` is the HL-portion.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_026
**Scenario Title:** close_operations.state transitions to done BEFORE hl_withdraw completes (done timing — G-06)
**UC Reference:** UC-EXBOT-user-redeem §3 step 14 (renumbered step 15); AC-016
**Req-ID:** AC-016; flow-withdraw-close-settlement-ba.md §5 step 6 note
**Test Type:** Data/State
**Description:** `close_operations.state='done'` and `bots.lifecycle_state='closed'` are set after `hedge_closed` + `redemption_requests` row created — before `hl_withdraw` and `hl_fulfill` workers complete. Verify: the `done` state is observable before the HL settlement chain finishes; the HL settlement chain runs asynchronously after `done` is set; `done` does NOT mean the investor has received the HL-portion yet.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_027
**Scenario Title:** principal_amount = initial clearinghouseState.withdrawable − final (after HL withdraw settled)
**UC Reference:** UC-EXBOT-user-redeem §3 step 14a; AC-009
**Req-ID:** AC-009; I-02a answer; flow-withdraw-close-settlement-ba.md §5 step 4
**Test Type:** Functional
**Description:** The hl_withdraw worker reads `clearinghouseState.withdrawable` from the HL API before and after the withdraw settles. `principal_amount = initial_withdrawable − final_withdrawable`. This value is net of PnL, funding, and trading fees (HL API computes the balance — no manual breakdown). Verify: `redemption_requests.principal_amount` stored as BigDecimal TEXT equals the delta; value is not a raw `hl_portion_usdc` from bot-open-time; the formula is applied consistently.
**Test Focus:** Functional

### Scenario ID: TS_UC-EXBOT-user-redeem_028
**Scenario Title:** principal_amount stored as BigDecimal TEXT, no floating-point precision loss
**UC Reference:** UC-EXBOT-user-redeem §3 step 14a; AC-009
**Req-ID:** AC-009; I-02a answer; erd.md close_operations
**Test Type:** Data/State
**Description:** `redemption_requests.principal_amount` is stored as TEXT in BigDecimal format, not as a float or numeric type. Verify: the stored value exactly matches the computed delta without rounding; retrieving the value and converting to BigDecimal produces a lossless result; the same BigDecimal precision applies to `close_operations.usdc_amount` (LP-portion).
**Test Focus:** Functional

### Scenario ID: TS_UC-EXBOT-user-redeem_029
**Scenario Title:** HL withdraw submitted to operator Arbitrum wallet; status advances to hl_withdraw_submitted
**UC Reference:** UC-EXBOT-user-redeem §3 step 14a; AC-010 (partial)
**Req-ID:** flow-withdraw-close-settlement-ba.md §5 step 5; flow §8.2 C-06/C-07
**Test Type:** Functional
**Description:** After `redemption_requests` row is created, the hl_withdraw worker submits a USDC withdrawal from HL to the operator Arbitrum wallet. Verify: `redemption_requests.status` transitions from `pending` to `hl_withdraw_submitted`; the HL API receives the withdraw request for the correct amount.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_030
**Scenario Title:** HL withdraw soft-fail — settlement proceeds when operator dest-chain already has sufficient USDC
**UC Reference:** UC-EXBOT-user-redeem §3 step 14a; flow §8.2 C-06/C-07
**Req-ID:** flow-withdraw-close-settlement-ba.md §8.2 C-06/C-07; AC-012
**Test Type:** Functional
**Description:** When the HL withdraw fails (HL API error or timeout), the settlement worker checks whether the operator dest-chain already holds sufficient USDC. If the dest balance ≥ amount owed, the settlement proceeds without waiting for the HL withdraw to succeed. Verify: `redemption_requests.status` can advance past `hl_withdraw_submitted` even with a failed HL withdraw; no error state is set; investor receives the full amount.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_031
**Scenario Title:** Reserved-liquidity path — CCTP skipped when operator dest-chain USDC ≥ amount owed
**UC Reference:** UC-EXBOT-user-redeem §3 step 14b; AC-010
**Req-ID:** AC-010; flow-withdraw-close-settlement-ba.md §11.3; flow §8.3 C-08
**Test Type:** Functional
**Description:** When the HL withdraw settles (or soft-fail condition met) and the operator dest-chain USDC balance ≥ `principal_amount`, the CCTP bridge is skipped entirely. Verify: `redemption_requests.status` transitions directly from `hl_withdraw_submitted` to `ready_to_fulfill` without entering `bridge_pending_attestation`; no CCTP burn transaction is initiated.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_032
**Scenario Title:** CCTP path — burn initiated when operator dest-chain USDC < amount owed
**UC Reference:** UC-EXBOT-user-redeem §3 step 14b; AC-011
**Req-ID:** AC-011; flow-withdraw-close-settlement-ba.md §11.2; flow §8.3 C-09
**Test Type:** Functional
**Description:** When the operator dest-chain USDC < `principal_amount`, the settlement worker initiates a CCTP bridge: burns USDC on Arbitrum and submits to Circle Iris for attestation. Verify: `redemption_requests.status` transitions to `bridge_pending_attestation`; a CCTP burn transaction is confirmed on Arbitrum; the attestation cron polling begins.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_033
**Scenario Title:** CCTP attestation cron polls Circle Iris until attestation ready; status does not advance prematurely
**UC Reference:** UC-EXBOT-user-redeem §3 step 14b; AC-011
**Req-ID:** flow-withdraw-close-settlement-ba.md §11.2; AC-011
**Test Type:** Integration
**Description:** While `redemption_requests.status='bridge_pending_attestation'`, the attestation cron polls Circle Iris periodically. Verify: status remains at `bridge_pending_attestation` until Circle Iris confirms the attestation is ready; the cron does not advance status prematurely on a pending/not-yet-ready attestation response; each cron tick resumes polling correctly.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-user-redeem_034
**Scenario Title:** CCTP in-flight rule — once burn started, mint must complete even if dest balance becomes sufficient mid-bridge
**UC Reference:** UC-EXBOT-user-redeem §3 step 14b; flow §8.3 C-10
**Req-ID:** flow-withdraw-close-settlement-ba.md §8.3 C-10; AC-011
**Test Type:** Functional
**Description:** Once a CCTP burn has been initiated for a settlement, the flow must complete the mint on the dest chain — it cannot be abandoned even if the operator dest-chain balance is subsequently topped up to sufficient levels. Verify: the system does not switch from the CCTP path to the reserved-liquidity path mid-bridge; `bridge_pending_attestation` proceeds to attestation → mint → `ready_to_fulfill`.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_035
**Scenario Title:** CCTP mint on dest chain completes; status advances to ready_to_fulfill
**UC Reference:** UC-EXBOT-user-redeem §3 step 14b; AC-011
**Req-ID:** flow-withdraw-close-settlement-ba.md §11.2 step 3; AC-011
**Test Type:** Functional
**Description:** After Circle Iris attests the CCTP burn and the USDC is minted on the dest chain, the settlement worker advances `redemption_requests.status` to `ready_to_fulfill`. Verify: USDC is minted on the correct dest chain (Base or Optimism); `status='ready_to_fulfill'`; no duplicate minting occurs.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_036
**Scenario Title:** fulfillRequest on-chain succeeds; status advances to fulfilled; investor receives USDC
**UC Reference:** UC-EXBOT-user-redeem §3 step 14c; AC-013
**Req-ID:** AC-013; flow-withdraw-close-settlement-ba.md §11.4; AC-001
**Test Type:** Functional
**Description:** When `redemption_requests.status='ready_to_fulfill'`, the settlement worker calls `RedemptionQueue.fulfillRequest` on-chain. Verify: the on-chain call succeeds; `redemption_requests.status` transitions to `fulfilled`; the investor's on-chain USDC balance increases by `principal_amount`; `fulfillRequest` is emitted as an on-chain event.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_037
**Scenario Title:** fulfillRequest reverts when request is not the RedemptionQueue head; worker retries via SQS
**UC Reference:** UC-EXBOT-user-redeem §3 step 14c; AC-013
**Req-ID:** AC-013; flow-withdraw-close-settlement-ba.md §11.4; flow §8.4 C-13/C-14
**Test Type:** Integration
**Description:** `RedemptionQueue.fulfillRequest` enforces FIFO on-chain: it reverts if the request being fulfilled is not the current queue head. When the on-chain call reverts, the settlement worker re-queues the message via SQS for retry. Verify: the revert does not set a terminal state; the worker retries; there is no off-chain wait branch — only SQS retry; the request is eventually fulfilled when it becomes the queue head.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-user-redeem_038
**Scenario Title:** HL fulfill redelivery is idempotent — no second on-chain payout when status=fulfilled
**UC Reference:** UC-EXBOT-user-redeem §3 step 14c; AC-014
**Req-ID:** AC-014; flow-withdraw-close-settlement-ba.md §12 rule 6; flow §8.4 C-15
**Test Type:** Integration
**Description:** When a settlement worker message is redelivered after `redemption_requests.status='fulfilled'` (already paid), the worker detects the terminal status and skips the `fulfillRequest` call. Verify: no second on-chain USDC transfer to the investor; `status` remains `fulfilled`; no error is raised.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_039
**Scenario Title:** fulfillRequest retry exhaustion → redemption_requests.status transitions to failed (terminal)
**UC Reference:** UC-EXBOT-user-redeem §3 step 14c; AC-015
**Req-ID:** AC-015; flow-withdraw-close-settlement-ba.md §8.4
**Test Type:** Functional
**Description:** When `fulfillRequest` retry limit is exhausted (e.g., FIFO revert continues beyond the retry cap), `redemption_requests.status` transitions to `failed`. Verify: `failed` is a terminal state; the request remains on-chain as a durable claim; ops intervention is required; no further automatic retries occur after `failed`.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-user-redeem_040
**Scenario Title:** redemption_requests status lifecycle — all 6 states reachable and transitions are valid
**UC Reference:** UC-EXBOT-user-redeem §3 steps 14a–14c; flow-withdraw-close-settlement-ba.md §7
**Req-ID:** flow-withdraw-close-settlement-ba.md §7; AC-015
**Test Type:** Data/State
**Description:** Trace the full `redemption_requests.status` lifecycle: `pending → hl_withdraw_submitted → bridge_pending_attestation → ready_to_fulfill → fulfilled` (success path) and `→ failed` (terminal failure). Verify: each transition is forward-only; no backward transition is possible; `fulfilled` and `failed` are both terminal (no further status changes occur after reaching them).
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_041
**Scenario Title:** close_operations.usdc_amount (LP-portion) and redemption_requests.principal_amount (HL-portion) are separate, independent amounts
**UC Reference:** UC-EXBOT-user-redeem §3; AC-009; erd.md
**Req-ID:** AC-009; I-02a answer; erd.md close_operations; flow-withdraw-close-settlement-ba.md §5
**Test Type:** Data/State
**Description:** The LP-portion and HL-portion are tracked in separate database tables and represent distinct amounts. Verify: `close_operations.usdc_amount` stores the LP-portion (from on-chain LP liquidation, via `BnzaExVault.redeem`); `redemption_requests.principal_amount` stores the HL-portion (from `clearinghouseState.withdrawable` delta); neither field is a copy of the other; their sum equals the investor's total redemption proceeds.
**Test Focus:** On-chain↔off-chain consistency

### Scenario ID: TS_UC-EXBOT-user-redeem_042
**Scenario Title:** close_operations.hedge_close_tx field remains null for user_redeem (HL-portion tx not stored here)
**UC Reference:** UC-EXBOT-user-redeem; I-02bc answer; erd.md
**Req-ID:** I-02bc answer; erd.md close_operations
**Test Type:** Data/State
**Description:** The HL-portion transfer transaction hash is NOT stored in `close_operations.hedge_close_tx`. Verify: `close_operations.hedge_close_tx` remains null after the settlement completes; the on-chain `fulfillRequest` transaction hash (if tracked) is stored in `redemption_requests`, not `close_operations`.
**Test Focus:** On-chain↔off-chain consistency

### Scenario ID: TS_UC-EXBOT-user-redeem_043
**Scenario Title:** user_redeem accepted when bot.lifecycle_state = active
**UC Reference:** UC-EXBOT-user-redeem §2 Preconditions; I-N1 answer
**Req-ID:** UC-EXBOT-user-redeem §2; states.md bots
**Test Type:** Functional
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` when the bot's `lifecycle_state='active'`. Verify: the on-chain call succeeds; `RedemptionEvent` emitted; event watcher enqueues the message; full user_redeem flow proceeds.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_044
**Scenario Title:** user_redeem accepted when bot.lifecycle_state = paused
**UC Reference:** UC-EXBOT-user-redeem §2 Preconditions; I-N1 answer
**Req-ID:** UC-EXBOT-user-redeem §2; states.md bots
**Test Type:** Functional
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` when `bots.lifecycle_state='paused'`. Verify: on-chain contract does not block the call (LP NFT still in vault); `RedemptionEvent` emitted; full user_redeem flow proceeds correctly.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_045
**Scenario Title:** user_redeem accepted when bot.lifecycle_state = safe_mode
**UC Reference:** UC-EXBOT-user-redeem §2 Preconditions; I-N1 answer; BR-EXBOT-007
**Req-ID:** UC-EXBOT-user-redeem §2; BR-EXBOT-007
**Test Type:** Functional
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` when `bots.lifecycle_state='safe_mode'`. Verify: on-chain contract allows the call; user_redeem flow proceeds; SAFE_MODE does not block or alter the redeem flow (BR-EXBOT-007: SAFE_MODE never applies in A2 user_redeem once LP is liquidated).
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_046
**Scenario Title:** user_redeem accepted when bot.lifecycle_state = hedge_stopped_cooldown
**UC Reference:** UC-EXBOT-user-redeem §2 Preconditions; I-N1 answer
**Req-ID:** UC-EXBOT-user-redeem §2; states.md bots
**Test Type:** Functional
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` when `bots.lifecycle_state='hedge_stopped_cooldown'`. Verify: LP NFT still in vault; on-chain `redeem()` succeeds; user_redeem flow proceeds normally.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_047
**Scenario Title:** user_redeem accepted when bot.lifecycle_state = error
**UC Reference:** UC-EXBOT-user-redeem §2 Preconditions; I-N1 answer
**Req-ID:** UC-EXBOT-user-redeem §2; states.md bots
**Test Type:** Functional
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` when `bots.lifecycle_state='error'`. Verify: LP NFT still in vault; on-chain `redeem()` succeeds; event watcher enqueues; user_redeem flow proceeds normally.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_048
**Scenario Title:** redeem(oldTokenId) reverts safely when bot is mid-lp_rebalancing
**UC Reference:** UC-EXBOT-user-redeem §2 Preconditions; I-N1 answer
**Req-ID:** UC-EXBOT-user-redeem §2; I-N1 answer
**Test Type:** Functional
**Description:** When `bots.lifecycle_state='lp_rebalancing'`, calling `BnzaExVault.redeem(oldTokenId)` reverts on-chain (old tokenId no longer valid). Verify: the on-chain revert is safe — no `RedemptionEvent` emitted; no queue message enqueued; `redeem(newTokenId)` succeeds after rebalancing completes.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-user-redeem_049
**Scenario Title:** bots.lifecycle_state = closed and close_operations.state = done set simultaneously after settlement chain starts
**UC Reference:** UC-EXBOT-user-redeem §3 step 15 (renumbered); AC-016
**Req-ID:** AC-016; flow-withdraw-close-settlement-ba.md §5 step 6 note; G-06 gap note
**Test Type:** Data/State
**Description:** `bots.lifecycle_state='closed'` and `close_operations.state='done'` are set together — before the async HL settlement chain (hl_withdraw → hl_fulfill) completes. Verify: `closed`/`done` are set immediately after `redemption_requests` creation; a subsequent query on the bot returns `lifecycle_state='closed'` even while `redemption_requests.status` is still `pending` or `hl_withdraw_submitted`.
**Test Focus:** On-chain↔off-chain consistency

### Scenario ID: TS_UC-EXBOT-user-redeem_050
**Scenario Title:** queue_idempotency.state transitions to succeeded after full flow completes
**UC Reference:** UC-EXBOT-user-redeem §3 step 16
**Req-ID:** FR-EXBOT-010; UC-EXBOT-user-redeem §3 step 16
**Test Type:** Data/State
**Description:** After `close_operations.state='done'`, the `queue_idempotency` record for the original SQS message is marked as `succeeded`. Verify: `queue_idempotency.state='succeeded'` is set; the record prevents any future re-delivery of the same message from triggering reprocessing.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-user-redeem_051
**Scenario Title:** AC-001 — Full happy path postconditions all satisfied
**UC Reference:** UC-EXBOT-user-redeem §8 AC-001
**Req-ID:** AC-001
**Test Type:** Acceptance
**Description:** After a complete user_redeem execution on the happy path, verify all postconditions simultaneously: (1) `close_operations.state='done'`; (2) `bots.lifecycle_state='closed'`; (3) `redemption_requests.status='fulfilled'`; (4) investor on-chain USDC balance increased by LP-portion (via BnzaExVault) + HL-portion (via RedemptionQueue); (5) no open HL position remains; (6) `queue_idempotency.state='succeeded'`.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-user-redeem_052
**Scenario Title:** AC-002 — SLA breach alert sent with exact message text
**UC Reference:** UC-EXBOT-user-redeem §8 AC-002
**Req-ID:** AC-002; NFR-EXBOT-003
**Test Type:** Acceptance
**Description:** When the hedge close SLA is breached, verify: E-EXBOT-010 alert contains exactly "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." — no truncation or paraphrase; alert is sent exactly once; alert routing reaches admin.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_053
**Scenario Title:** AC-004 — Duplicate message is a graceful no-op (investor receives funds exactly once)
**UC Reference:** UC-EXBOT-user-redeem §8 AC-004
**Req-ID:** AC-004; FR-EXBOT-010
**Test Type:** Acceptance
**Description:** Verify that any duplicate user_redeem message delivery (whether via SQS deduplication or `close_operations` idempotency) results in the investor receiving their funds exactly once — no duplicate LP-portion or HL-portion transfer occurs.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_054
**Scenario Title:** AC-006 — A2 path: LP-portion retained by investor, bots.lifecycle_state=error
**UC Reference:** UC-EXBOT-user-redeem §8 AC-006
**Req-ID:** AC-006; BR-EXBOT-006
**Test Type:** Acceptance
**Description:** When the A2 failure path is reached (hedge close failed → `residual_hl_liability`), verify: investor's LP-portion is NOT reversed; `bots.lifecycle_state='error'`; `close_operations.state='residual_hl_liability'`; E-EXBOT-024 received by admin.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-user-redeem_055
**Scenario Title:** AC-009 — principal_amount stored correctly in redemption_requests as BigDecimal TEXT delta
**UC Reference:** UC-EXBOT-user-redeem §8 AC-009
**Req-ID:** AC-009; I-02a answer
**Test Type:** Acceptance
**Description:** Verify: `redemption_requests.principal_amount` equals `initial_clearinghouseState.withdrawable − final_clearinghouseState.withdrawable` stored as BigDecimal TEXT; the stored value is lossless; the value is used as the amount for `RedemptionQueue.fulfillRequest`.
**Test Focus:** On-chain↔off-chain consistency

### Scenario ID: TS_UC-EXBOT-user-redeem_056
**Scenario Title:** AC-010 — Reserved-liquidity path skips CCTP and sets status=ready_to_fulfill directly
**UC Reference:** UC-EXBOT-user-redeem §8 AC-010
**Req-ID:** AC-010; flow-withdraw-close-settlement-ba.md §11.3
**Test Type:** Acceptance
**Description:** When the operator dest-chain has sufficient USDC pre-funded, verify: `redemption_requests.status` advances from `hl_withdraw_submitted` to `ready_to_fulfill` without entering `bridge_pending_attestation`; no CCTP burn transaction on Arbitrum; settlement completes faster.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_057
**Scenario Title:** AC-011 — CCTP path: burn Arb → attestation → mint dest → ready_to_fulfill
**UC Reference:** UC-EXBOT-user-redeem §8 AC-011
**Req-ID:** AC-011; flow-withdraw-close-settlement-ba.md §11.2
**Test Type:** Acceptance
**Description:** When CCTP bridge is triggered, verify the full chain: Arb USDC burned → status=`bridge_pending_attestation` → Circle Iris polled → attestation received → USDC minted on dest chain → status=`ready_to_fulfill`; all status transitions are sequential and correct.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-user-redeem_058
**Scenario Title:** AC-012 — HL withdraw soft-fail path: settlement continues when dest already funded
**UC Reference:** UC-EXBOT-user-redeem §8 AC-012
**Req-ID:** AC-012; flow-withdraw-close-settlement-ba.md §8.2 C-06/C-07
**Test Type:** Acceptance
**Description:** When HL withdraw fails but operator dest-chain balance ≥ principal_amount, verify: settlement proceeds without HL withdraw success; `redemption_requests.status` still advances normally; investor receives full HL-portion.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-user-redeem_059
**Scenario Title:** AC-013 — FIFO: fulfillRequest reverts when not queue head; retried via SQS until success
**UC Reference:** UC-EXBOT-user-redeem §8 AC-013
**Req-ID:** AC-013; flow-withdraw-close-settlement-ba.md §11.4
**Test Type:** Acceptance
**Description:** Verify FIFO enforcement: when the on-chain `fulfillRequest` reverts because this request is not the queue head, the worker re-queues via SQS and retries. Verify: no off-chain wait branch exists; revert is gracefully handled; the request eventually succeeds when it becomes the head.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-user-redeem_060
**Scenario Title:** AC-014 — fulfill redelivery idempotent: no double payout when already fulfilled
**UC Reference:** UC-EXBOT-user-redeem §8 AC-014
**Req-ID:** AC-014; flow-withdraw-close-settlement-ba.md §12 rule 6
**Test Type:** Acceptance
**Description:** When a settlement message is redelivered after `status='fulfilled'`, verify: second `fulfillRequest` call is NOT made; investor USDC balance unchanged; status remains `fulfilled`.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-user-redeem_061
**Scenario Title:** AC-015 — fulfill retry limit exhausted → status=failed (terminal, durable on-chain claim)
**UC Reference:** UC-EXBOT-user-redeem §8 AC-015
**Req-ID:** AC-015; flow-withdraw-close-settlement-ba.md §8.4
**Test Type:** Acceptance
**Description:** When fulfill retry limit is exhausted, verify: `redemption_requests.status='failed'`; the on-chain request is preserved as a durable claim; no automatic retries occur; ops notification sent.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-user-redeem_062
**Scenario Title:** AC-016 — close_operations.state=done set BEFORE hl_withdraw/hl_fulfill completes (async settlement)
**UC Reference:** UC-EXBOT-user-redeem §8 AC-016
**Req-ID:** AC-016; flow-withdraw-close-settlement-ba.md §5 step 6 note; G-06
**Test Type:** Acceptance
**Description:** Verify the done-timing contract: `close_operations.state='done'` and `bots.lifecycle_state='closed'` are observable before the HL settlement chain completes. Verify: `done`/`closed` are set after `hedge_closed` + `redemption_requests` creation; querying the bot at this point returns `closed` while `redemption_requests.status` may still be `pending`.
**Test Focus:** On-chain↔off-chain consistency

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Performance / load testing (e.g., sustained queue throughput, Lambda cold-start latency at scale) | NFR: PERFORMANCE / LOAD — out of scope for functional scenario design | Defer to load testing specialist; design dedicated perf scenarios with traffic model |
| Security beyond functional auth (e.g., key rotation, IAM boundary testing, HL agent key exposure audits beyond E-EXBOT log check) | NFR: SECURITY — out of scope beyond TC_047 log-scrub functional check | Defer to security engineer; run OWASP-style review on HL key handling |
| `redemption_requests` ERD schema validation (G-01: table not in srs/erd.md) | BLOCKED: `redemption_requests` table structure not documented in ERD — column names, indexes, constraints unverifiable | Resolve G-01 via `qc-qna`: BA to add `redemption_requests` table to `srs/erd.md` |
| Settlement status lifecycle in states.md (G-02: states.md missing) | BLOCKED: `redemption_requests` status lifecycle not in `srs/states.md` — scenarios designed from `flow-withdraw-close-settlement-ba.md` §7 as surrogate | Resolve G-02 via `qc-qna`: BA to add settlement lifecycle to `srs/states.md` |
| F-04 flow diagram cross-verification (G-03: stale) | BLOCKED: `srs/flows.md` F-04 predates settlement chain introduction — cannot verify scenario steps against flow diagram | Resolve G-03: BA to update F-04 to reflect post-I-02a settlement chain |
| Circle Iris attestation SLA / timeout behavior | UNCLEAR: maximum attestation wait time not defined in flow-withdraw-close-settlement-ba.md — no boundary value for attestation timeout | BA to specify attestation polling timeout and max wait |
