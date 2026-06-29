# Test Scenarios — UC-EXBOT-user-redeem (User-Initiated Redemption LP-First)

> **Document title:** Test Scenarios — UC-EXBOT-user-redeem
> **Date created:** 2026-06-29
> **Author / Agent:** qc-func-scenario-design-exbot (Trinh.Bui / MTS-978)
> **Version:** v1
>
> Source: `docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260619_v1.md`
> Generated: 2026-06-29
> Domain/Architecture: Cloudflare Workers + D1 + Hyperliquid API; no UI — all operations triggered by on-chain `RedemptionEvent`, processed by `user_redeem` queue worker; Durable Objects (`UserLockDO`, `HLRateLimitDO`); on-chain `BnzaExVault.redeem()` LP-first close.
>
> **NOTE:** UC-EXBOT-user-redeem has verdict NOT READY (61/100) due to Blocker I-01 (close_operations atomicity undefined) and Blocker I-04 (FR-EXBOT-071 does not exist), plus Major issues I-02, I-03, I-05, I-06, I-07, I-10. Per user direction, scenarios for blocked areas are included with `[TBD — pending BA answer: <issue ref>]` in the Description field so that BA can fill in expected results once the gaps are resolved.

---

## Reference code glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| BR-EXBOT-006 | Business Rule — LP-portion USDC repayment is unconditional. In this project, the on-chain `BnzaExVault.redeem()` call transfers LP-USDC to the investor in the same transaction; hedge close failure on HL must NEVER block or reverse this payment. | `common-rules.md` |
| E-EXBOT-010 | Error/alert message: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." Internal admin alert; triggered when hedge has not closed within 5 minutes of `RedemptionEvent` detection. | `message-list.md` |
| NFR-EXBOT-003 | Non-functional requirement — SLA of 5 minutes for hedge close, measured from event detection. | `srs/spec.md` |
| FR-EXBOT-070 | Functional requirement — full user_redeem worker flow including idempotency, close_operations lifecycle, HL close, and LP-portion guarantee. | `srs/spec.md` |
| close_operations | D1 table tracking the state of each close operation. `state` ENUM: `requested` → `lp_closed` → `funds_returned` → `hedge_close_pending` → `hedge_closed` → `done` | `residual_hl_liability`. | `srs/erd.md`; `srs/states.md` |
| UserLockDO | Durable Object lock per user; TTL=90s. Must be acquired before any Hyperliquid (HL) API mutation to prevent concurrent HL operations on the same account. | `srs/spec.md` |
| HLRateLimitDO | Durable Object rate limiter for HL API calls. Returns `{allowed: boolean, retryAfterMs}`. | `srs/spec.md` FR-EXBOT-091 |
| INV-STOP §19.5 | Protocol for cancelling the investor's stop-loss order via `replaceStopProtected(size=0)`. `stop_replacing_started_at` must be cleared in the `finally` block. | `srs/spec.md §19.5` |
| residual_hl_liability | Terminal failure state in `close_operations`. Set when hedge close fails after max retries. Admin must be notified with bot_id, hedge size, and USD value. LP-portion is never reversed. | `srs/states.md`; UC §A2 |
| LP | Liquidity Provider — Uniswap V3 position wrapped as a bot. In this UC, the LP position is liquidated on-chain first by `BnzaExVault.redeem()` before hedge close happens off-chain. | Industry term |
| HL | Hyperliquid — external perpetuals exchange used to hold the hedge short position. HL operations are done off-chain by the worker after on-chain LP liquidation. | Industry term |
| cloid | Client Order ID — deterministic ID for HL orders; ensures idempotent re-submission of the same close order. | `srs/spec.md` |

---

## UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)

### Scenario ID: TS_UC-EXBOT-UREDEEM_001
**Scenario Title:** Happy path — investor calls BnzaExVault.redeem(), LP liquidated and LP-portion USDC returned in same transaction
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 steps 1-3; SRS FR-EXBOT-070; BR-EXBOT-006
**Test Type:** Functional
**Description:** An investor calls `BnzaExVault.redeem(tokenId)` on-chain for a bot in `bots.status='active'`. The contract executes `decreaseLiquidity` 100% + `collect` + swap to USDC. The LP-portion USDC must be transferred to the investor's wallet in the same on-chain transaction. A `RedemptionEvent(botId, redeemTxHash, userAddress)` must be emitted.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_002
**Scenario Title:** Happy path — RedemptionEvent detected and enqueued into user_redeem with highest priority
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 steps 4-5; SRS NFR-EXBOT-003
**Test Type:** Functional
**Description:** After `BnzaExVault.redeem()` is confirmed on-chain, the Redeem Event Watcher detects the `RedemptionEvent`. A message must be enqueued into the `user_redeem` queue at the highest priority. The SLA 5-minute timer starts from this detection moment.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_003
**Scenario Title:** Happy path — queue_idempotency insert succeeds and worker continues processing
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 6; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** When the `user_redeem` worker receives a message with a new `message_id`, it inserts a row into `queue_idempotency` with `state='started'`. The insert succeeds (no UNIQUE conflict). The worker proceeds to close_operations creation.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_004
**Scenario Title:** Happy path — close_operations row created with kind=user_redeem, state=lp_closed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 7; SRS FR-EXBOT-070; srs/erd.md
**Test Type:** Functional
**Description:** After the idempotency check passes, the worker creates a row in `close_operations` with `kind='user_redeem'`, a unique `idempotency_key`, and initial `state='lp_closed'`. The row must be created in D1. `[TBD — pending BA answer: I-01 — confirm whether lp_closed and funds_returned are two separate updates or one D1 transaction, and the resume strategy if worker crashes between them]`
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_005
**Scenario Title:** Happy path — UserLockDO lease acquired before any HL operation
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 8; SRS UserLockDO spec
**Test Type:** Functional
**Description:** Before the worker calls any Hyperliquid API, it must acquire the `UserLockDO` lease for the user (TTL=90s). The lease must be granted. Only after lease acquisition does the worker proceed to `closeShortReduceOnlyIoc`.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_006
**Scenario Title:** Happy path — HL hedge full close executes with deterministic cloid
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** With `UserLockDO` lease held, the worker calls `closeShortReduceOnlyIoc` on Hyperliquid with a deterministic cloid computed from the bot_id and operation context. HL accepts the close order. `close_operations.hedge_close_tx` is recorded.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_007
**Scenario Title:** Happy path — INV-STOP cancelled via replaceStopProtected(size=0), stop_replacing_started_at cleared in finally
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 10; SRS §19.5
**Test Type:** Functional
**Description:** After the HL close order is sent, the worker calls `replaceStopProtected` with `size=0` to cancel the investor's stop-loss order per INV-STOP §19.5. The stop is cancelled successfully. Regardless of success or failure of this step, `hedge_legs.stop_replacing_started_at` must be cleared in the `finally` block (never left non-null after the operation).
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_008
**Scenario Title:** Happy path — close_operations state advances to hedge_close_pending after HL close sent
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 10; srs/states.md
**Test Type:** Data/State
**Description:** After the HL close order is sent and INV-STOP is handled, the worker updates `close_operations.state` to `hedge_close_pending`. The state transition must occur; the row must not remain at `funds_returned`.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-UREDEEM_009
**Scenario Title:** Happy path — reconcile confirms HL position size = 0
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 11; SRS FR-EXBOT-070
**Test Type:** Integration
**Description:** After the close order is confirmed, the worker queries the HL position for the bot. The returned `positions.size` must equal 0. `close_operations.state` advances to `hedge_closed`. The reconcile confirmation must be stored (D1 state update).
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-UREDEEM_010
**Scenario Title:** Happy path — HL-portion USDC transferred to investor, close_operations advances to done
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 steps 13-14; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** After `close_operations.state='hedge_closed'`, the worker sends the HL-portion USDC to the investor and records the transfer in the RedemptionQueue ledger. `close_operations.state` must advance to `done`. `bots.lifecycle_state` must be updated to `closed`. `[TBD — pending BA answer: I-07 — confirm the HL-portion transfer mechanism: which contract function, whether fulfillRequest is used]`
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_011
**Scenario Title:** Happy path — queue_idempotency marked succeeded after full close
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 15; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** After `close_operations.state='done'` and `bots.lifecycle_state='closed'`, the worker updates `queue_idempotency.state` to `'succeeded'` for this `message_id`. No further processing occurs for this message.
**Test Focus:** Happy path


---

### Scenario ID: TS_UC-EXBOT-UREDEEM_012
**Scenario Title:** A1 — SLA breach: hedge not closed within 5 minutes of event detection, admin alert E-EXBOT-010 sent
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §A1; SRS NFR-EXBOT-003; E-EXBOT-010
**Test Type:** Functional
**Description:** When 5 minutes elapse from the moment the Redeem Event Watcher detects the `RedemptionEvent` and the hedge has not been fully closed, the system must send admin alert E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." The LP-portion USDC already sent to the investor must NOT be reversed or blocked. The `close_operations.state` remains at its current value at the time of the alert.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-UREDEEM_013
**Scenario Title:** A1 — SLA timer measured from event detection, not from on-chain tx confirmation
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §A1; SRS NFR-EXBOT-003; UC §F.4 Watcher lag note
**Test Type:** Functional
**Description:** When the Redeem Event Watcher detects the `RedemptionEvent` with a delay (the tx was confirmed earlier on-chain but the Watcher detects it later), the 5-minute SLA timer must start from the Watcher detection time — not from the on-chain block timestamp. This means a delayed Watcher still provides a 5-minute window from detection, not a reduced window. SLA compliance must be measured accordingly.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-UREDEEM_014
**Scenario Title:** A2 — HL hedge close fails after max retries, residual_hl_liability recorded with bot_id, hedge size, USD value
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §A2; BR-EXBOT-006; US-004 AC-004-3
**Test Type:** Functional
**Description:** When the HL `closeShortReduceOnlyIoc` call fails after all retry attempts, the worker must set `close_operations.state='residual_hl_liability'`. An admin alert must be sent containing the `bot_id`, the open hedge size, and the USD value of the residual position. The LP-portion USDC already transferred to the investor must NOT be reversed.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_015
**Scenario Title:** A2 — BR-EXBOT-006: LP-portion USDC is never reversed regardless of hedge close outcome
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** BR-EXBOT-006; UC §A2; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** Under any hedge close failure scenario (HL API unreachable, partial fill, max retries exceeded, or any exception), verify that the LP-portion USDC that was returned to the investor during `BnzaExVault.redeem()` is not reversed, blocked, or recalled. The on-chain LP payout is unconditional.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_016
**Scenario Title:** A2 — lifecycle_state value when close_operations.state=residual_hl_liability
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §A2; srs/states.md; UC §5 Postconditions
**Test Type:** Data/State
**Description:** When `close_operations.state='residual_hl_liability'` is set after hedge close failure, verify the `bots.lifecycle_state` value. `[TBD — pending BA answer: I-02 — is lifecycle_state='closed' or 'lp_closing' when residual_hl_liability is reached? Must be confirmed before writing expected result.]`
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-UREDEEM_017
**Scenario Title:** A3 — duplicate message_id triggers queue_idempotency UNIQUE conflict, worker returns immediately
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §A3; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** When the `user_redeem` worker receives a message whose `message_id` already exists in `queue_idempotency` (any state), the insert raises a UNIQUE conflict. The worker must return immediately without creating a second `close_operations` row, without mutating any HL position, and without changing any bot state. The existing `queue_idempotency` row must be unchanged.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_018
**Scenario Title:** A3 — duplicate message with same message_id while close_operations is in-progress does not create second row
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §A3; SRS FR-EXBOT-070; erd.md
**Test Type:** Idempotency/Concurrency
**Description:** A second copy of the same redemption message arrives while the first worker is still processing (e.g., `close_operations.state='hedge_close_pending'`). Because `queue_idempotency.state='started'` for this `message_id`, the second worker encounters a UNIQUE conflict on insert and returns immediately. Only one `close_operations` row must exist for this `bot_id` with `kind='user_redeem'`.
**Test Focus:** Idempotency/Concurrency


---

### Scenario ID: TS_UC-EXBOT-UREDEEM_019
**Scenario Title:** State transition — close_operations progresses through full state chain: lp_closed > funds_returned > hedge_close_pending > hedge_closed > done
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3; srs/states.md; SRS FR-EXBOT-073 AC
**Test Type:** Data/State
**Description:** Execute a full happy-path close. At each step, verify that `close_operations.state` advances in order: `lp_closed` → `funds_returned` → `hedge_close_pending` → `hedge_closed` → `done`. No state must be skipped. The sequence must be monotonically forward — no backward transitions. `[TBD — pending BA answer: I-01 — confirm atomicity between lp_closed and funds_returned before writing step-by-step expected results]`
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-UREDEEM_020
**Scenario Title:** State transition — bots.lifecycle_state transitions active > lp_closing > closed during user_redeem
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3; srs/states.md §lifecycle
**Test Type:** Data/State
**Description:** During a full user_redeem close, verify that `bots.lifecycle_state` transitions from the pre-redeem state (`active` or `paused` or `safe_mode`) to `lp_closing` (when close starts) and then to `closed` (after `close_operations.state='done'`). `[TBD — pending BA answer: I-03 — which step in the worker sets lifecycle_state='lp_closing'? Must be confirmed before writing expected result for this transition]`
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-UREDEEM_021
**Scenario Title:** State transition — close_operations cannot skip from lp_closed directly to hedge_close_pending
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** srs/states.md; SRS FR-EXBOT-073 AC
**Test Type:** Data/State
**Description:** Verify that the close_operations state machine does not allow the transition `lp_closed` → `hedge_close_pending` (skipping `funds_returned`). If the worker attempts to set `hedge_close_pending` without first setting `funds_returned`, this should be rejected or never happen by the worker logic. The state must always pass through `funds_returned`.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-UREDEEM_022
**Scenario Title:** State transition — close_operations cannot be created twice for the same bot_id with kind=user_redeem
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 7; srs/erd.md; SRS FR-EXBOT-070
**Test Type:** Data/State
**Description:** When a `close_operations` row with `kind='user_redeem'` already exists for a given `bot_id` (any state including `done`), a second attempt to create another row with the same `idempotency_key` must fail due to the UNIQUE constraint on `close_operations.idempotency_key`. The second worker must not create a duplicate settlement row.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_023
**Scenario Title:** State transition — queue_idempotency transitions started > succeeded after full close
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 steps 6, 15
**Test Type:** Data/State
**Description:** Verify that `queue_idempotency.state` starts as `'started'` when the worker first processes the message and is updated to `'succeeded'` after `close_operations.state='done'` and `bots.lifecycle_state='closed'` are both set. No intermediate state update should be missing.
**Test Focus:** State transition


---

### Scenario ID: TS_UC-EXBOT-UREDEEM_024
**Scenario Title:** UserLockDO — lease contention: another worker holds the lock, current worker must wait or timeout
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 8; srs/F.2 UserLockDO; SRS UserLockDO spec
**Test Type:** Integration
**Description:** When the `user_redeem` worker attempts to acquire the `UserLockDO` lease for the user and another operation is currently holding the lease, the worker must either wait for the lease to become available or fail gracefully. The worker must NOT proceed to any HL API call without successfully holding the lease.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_025
**Scenario Title:** UserLockDO — lease TTL expires mid-flow; stop_replacing_started_at must still be cleared in finally
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 8; SRS §19.5; SRS UserLockDO spec
**Test Type:** Integration
**Description:** If the `UserLockDO` lease TTL (90s) expires while the worker is mid-operation (e.g., during a slow HL response), verify that the `finally` block for INV-STOP §19.5 still clears `hedge_legs.stop_replacing_started_at`. The lease expiry must not cause `stop_replacing_started_at` to remain non-null after the operation ends.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-UREDEEM_026
**Scenario Title:** INV-STOP — stop_replacing_started_at is cleared even when replaceStopProtected fails
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 10; SRS §19.5
**Test Type:** Functional
**Description:** When `replaceStopProtected(size=0)` throws an exception (HL API error, network timeout), the `finally` block must still execute and clear `hedge_legs.stop_replacing_started_at`. After the failure, the field must be null. The stop-loss order may remain active on HL (escalation may be needed), but the `stop_replacing_started_at` field must not be left in a non-null state.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_027
**Scenario Title:** HL API unreachable — worker retries closeShortReduceOnlyIoc, then proceeds to residual_hl_liability after max retries
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 9; UC §A2; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** When `closeShortReduceOnlyIoc` fails due to HL API being unreachable, the worker retries. After max retries are exhausted, the worker must set `close_operations.state='residual_hl_liability'`, send an admin alert with `bot_id`, hedge size, and USD value, and NOT reverse the LP-portion already returned to the investor.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_028
**Scenario Title:** HL reconcile mismatch — HL position size not zero after close, worker retries then escalates
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 11; UC §A2; SRS FR-EXBOT-070
**Test Type:** Integration
**Description:** After the close order is sent, the reconcile step queries HL and finds `positions.size != 0` (partial fill or close not applied yet). The worker must retry the reconcile. After max retries with a non-zero size, the worker must treat this as a hedge close failure and transition to `residual_hl_liability` with admin alert.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_029
**Scenario Title:** HLRateLimitDO — rate limit check behavior before closeShortReduceOnlyIoc
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** SRS FR-EXBOT-091; UC §F.2 HLRateLimitDO
**Test Type:** Integration
**Description:** Before calling `closeShortReduceOnlyIoc`, the worker must check `HLRateLimitDO`. If `allowed=false`, the worker must not send the HL close order. `[TBD — pending BA answer: I-05 — when HLRateLimitDO returns allowed=false while UserLockDO is held, does the worker release the lock before re-queuing? What is the re-queue delay strategy?]`
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-UREDEEM_030
**Scenario Title:** Agent key failure — key revoked or expired when worker needs to sign HL close order
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-080; SRS FR-EXBOT-082
**Test Type:** Functional
**Description:** When the `user_redeem` worker attempts to decrypt the HL agent key for signing the `closeShortReduceOnlyIoc` order and the key is revoked or expired (AES-GCM decrypt fails or `hl_agent_keys.approval_status!='approved'`), verify the worker behavior. `[TBD — pending BA answer: I-06 — does agent key failure in user_redeem flow trigger SAFE_MODE, residual_hl_liability, or a different error path? This is a P0 flow and must be confirmed.]`
**Test Focus:** Error/Exception


---

### Scenario ID: TS_UC-EXBOT-UREDEEM_031
**Scenario Title:** Partial fill — closeShortReduceOnlyIoc partially fills, reconcile finds size != 0
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 9-11; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** When `closeShortReduceOnlyIoc` is only partially filled (HL fills a portion of the short position but not all), the reconcile step finds `positions.size > 0`. `[TBD — pending BA answer: I-10 — when partial fill occurs, does the worker re-submit a new close order for the remaining size, or does it count as a hedge close failure and proceed to residual_hl_liability? Retry limits?]`
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_032
**Scenario Title:** Precondition — redeem rejected when bot.status='closed'
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §2 Precondition 1; SRS FR-EXBOT-070
**Test Type:** Functional
**Description:** When an investor attempts to call `BnzaExVault.redeem(tokenId)` for a bot already in `bots.status='closed'`, the on-chain transaction should revert or the off-chain system should detect and reject the duplicate redemption attempt. No new `close_operations` row should be created.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-UREDEEM_033
**Scenario Title:** Precondition — only the NFT owner can call BnzaExVault.redeem()
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §2 Precondition 2; UC §2 Actors
**Test Type:** Functional
**Description:** Verify that calling `BnzaExVault.redeem(tokenId)` from a wallet address that does not hold the LP NFT (tokenId not owned by caller) causes the on-chain transaction to revert. The contract must enforce ownership at the token level.
**Test Focus:** Permission/Role

### Scenario ID: TS_UC-EXBOT-UREDEEM_034
**Scenario Title:** On-chain/off-chain consistency — LP-portion confirmed on-chain, hedge close async off-chain, both amounts recorded correctly
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.4; SRS FR-EXBOT-070; BR-EXBOT-006
**Test Type:** Integration
**Description:** After a full close, verify: (1) the LP-portion USDC transferred on-chain during `BnzaExVault.redeem()` matches the `close_operations.lp_close_tx` record; (2) the HL-portion USDC transferred off-chain matches `close_operations.usdc_amount`; (3) the sum of both portions equals the expected total bot value. The on-chain LP amount is the source of truth.
**Test Focus:** On-chain/off-chain consistency

### Scenario ID: TS_UC-EXBOT-UREDEEM_035
**Scenario Title:** On-chain/off-chain consistency — LP-portion already paid before hedge close starts; off-chain state correctly reflects this
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** BR-EXBOT-006; UC §3 steps 2-7; SRS FR-EXBOT-070
**Test Type:** Integration
**Description:** Verify that `close_operations.state='funds_returned'` is set (off-chain acknowledgment of LP-portion being returned) before any HL hedge close operation begins. The off-chain state must accurately reflect the on-chain reality: LP USDC is already with the investor before HL operations start.
**Test Focus:** On-chain/off-chain consistency

### Scenario ID: TS_UC-EXBOT-UREDEEM_036
**Scenario Title:** BigDecimal — usdc_amount and residual_amount stored and computed using BigDecimal arithmetic
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** SRS BigDecimal mandate; UC §F.2; srs/erd.md
**Test Type:** Functional
**Description:** When the worker computes and stores `close_operations.usdc_amount` (HL-portion to send) and `close_operations.residual_amount` (in case of residual_hl_liability), all arithmetic must use BigDecimal precision — no floating-point JavaScript Number arithmetic. Store test values with sufficient decimal precision (e.g., 1,000,000.123456 USDC) and verify no precision loss in D1.
**Test Focus:** Boundary


---

### Scenario ID: TS_UC-EXBOT-UREDEEM_037
**Scenario Title:** Idempotency — deterministic cloid prevents double-submission of the same HL close order
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 9; SRS FR-EXBOT-070
**Test Type:** Idempotency/Concurrency
**Description:** When `closeShortReduceOnlyIoc` is retried with the same deterministic cloid (e.g., after a timeout with no confirmed fill response), HL must treat it as the same order (idempotent re-submission). The worker must not double-close a position. Verify that HL position size is 0 (closed) after retry, not a negative or impossible value.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_038
**Scenario Title:** Idempotency — worker crash and restart at hedge_close_pending resumes correctly without re-liquidating LP
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3; SRS FR-EXBOT-073; UC §F.4
**Test Type:** Data/State
**Description:** Simulate a worker crash when `close_operations.state='hedge_close_pending'`. On restart (message redelivered from queue), the new worker must detect the existing `close_operations` row at `hedge_close_pending` and continue from that step — it must NOT re-create the row, re-liquidate LP, or re-send LP-portion. The LP is already returned; only the hedge close must be retried.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_039
**Scenario Title:** Idempotency — worker crash at lp_closed state, resume strategy
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 7; srs/states.md; I-01
**Test Type:** Data/State
**Description:** Simulate a worker crash when `close_operations.state='lp_closed'` (before `funds_returned`). On restart, verify resume behavior. `[TBD — pending BA answer: I-01 — confirm whether worker re-sets funds_returned state or re-verifies on-chain LP payout. The resume strategy is undefined without BA clarification on atomicity.]`
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_040
**Scenario Title:** Concurrency — two redemption events for the same bot_id race to create close_operations row
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 step 7; srs/erd.md; SRS FR-EXBOT-070
**Test Type:** Idempotency/Concurrency
**Description:** In a race condition where two workers receive the same redemption message concurrently (e.g., two Cloudflare Worker instances), both attempt to insert a `close_operations` row with the same `idempotency_key`. The UNIQUE constraint on `close_operations.idempotency_key` must allow only one insert to succeed. The losing worker must handle the conflict gracefully (not crash) and exit without double-closing.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_041
**Scenario Title:** End-to-end — full user_redeem flow from on-chain redeem call to bot.lifecycle_state=closed within SLA
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §3 (all steps); SRS FR-EXBOT-070; NFR-EXBOT-003; BR-EXBOT-006
**Test Type:** End-to-End
**Description:** Execute the complete user_redeem flow end-to-end: investor calls `BnzaExVault.redeem(tokenId)` → LP liquidated → `RedemptionEvent` detected → message queued → worker processes → LP-portion confirmed on-chain → HL hedge closed → INV-STOP cancelled → reconcile size=0 → HL-portion USDC sent → `bots.lifecycle_state='closed'`. Verify: (1) total time from event detection to `lifecycle_state='closed'` is under 5 minutes; (2) all `close_operations` states are recorded; (3) both USDC portions are accounted for; (4) no duplicate rows in `queue_idempotency` or `close_operations`.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_042
**Scenario Title:** End-to-end — full flow starting from bot in bots.status=paused
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §2 Precondition 1; UC §3; srs/states.md
**Test Type:** End-to-End
**Description:** Execute the complete user_redeem flow for a bot currently in `bots.status='paused'` (not `active`). Verify that the redeem is processed identically to the `active` case: LP liquidated on-chain, hedge closed off-chain, `lifecycle_state='closed'` at the end.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-UREDEEM_043
**Scenario Title:** End-to-end — full flow starting from bot in bots.status=safe_mode
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §2 Precondition 1; UC §3; srs/states.md
**Test Type:** End-to-End
**Description:** Execute the complete user_redeem flow for a bot currently in `bots.status='safe_mode'`. Verify that user_redeem is not blocked by safe_mode (unlike hedge-sync which is blocked by circuit breaker). The redeem must proceed to LP liquidation and hedge close. `bots.lifecycle_state='closed'` at the end.
**Test Focus:** Alternative flow


---

### Scenario ID: TS_UC-EXBOT-UREDEEM_044
**Scenario Title:** Acceptance — AC-C1: LP-portion USDC delivered to investor in same on-chain transaction as redeem
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.5 AC-C1; UC §3 step 3; BR-EXBOT-006; SRS FR-EXBOT-070
**Test Type:** Acceptance
**Description:** Verify AC-C1: after a successful `BnzaExVault.redeem(tokenId)`, inspect the on-chain transaction logs. The LP-portion USDC transfer to the investor's wallet address must appear in the same transaction as the `redeem()` call (not a separate transaction). The `redeemTxHash` in the `RedemptionEvent` must match the transaction that contains the USDC transfer.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_045
**Scenario Title:** Acceptance — AC-C2: duplicate message_id returns immediately without creating second close_operations row
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.5 AC-C2; UC §A3
**Test Type:** Acceptance
**Description:** Verify AC-C2: deliver the same redemption message (same `message_id`) to the `user_redeem` worker twice. After both deliveries, query D1: exactly one `close_operations` row must exist for this `bot_id` with `kind='user_redeem'`. Exactly one `queue_idempotency` row must exist for this `message_id`. No state corruption.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-UREDEEM_046
**Scenario Title:** Acceptance — AC-C4: hedge close failure produces residual_hl_liability with admin alert, LP not reversed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.5 AC-C4; UC §A2; BR-EXBOT-006; US-004 AC-004-3
**Test Type:** Acceptance
**Description:** Verify AC-C4: force HL hedge close to fail (all retries exhausted). Verify: (1) `close_operations.state='residual_hl_liability'`; (2) admin alert sent containing `bot_id`, open hedge size in USDC, and USD value of residual; (3) the LP-portion USDC already sent to the investor is not reversed, not blocked, and not recalled.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-UREDEEM_047
**Scenario Title:** Acceptance — AC-C5: SLA breach triggers E-EXBOT-010 admin alert, LP-portion not reversed
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.5 AC-C5; UC §A1; SRS NFR-EXBOT-003; E-EXBOT-010
**Test Type:** Acceptance
**Description:** Verify AC-C5: simulate a hedge close that takes longer than 5 minutes from `RedemptionEvent` detection. At the 5-minute mark, the system must send admin alert with the exact message E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." The LP-portion USDC already sent to the investor must remain in the investor's wallet — not reversed.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-UREDEEM_048
**Scenario Title:** Acceptance — AC-C6: stop_replacing_started_at cleared in finally block
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.5 AC-C6; SRS §19.5
**Test Type:** Acceptance
**Description:** Verify AC-C6 (inferred, pending BA confirmation): after the INV-STOP cancel operation (`replaceStopProtected(size=0)`) completes — whether successfully or with an exception — query D1 for `hedge_legs.stop_replacing_started_at`. The value must be null. Test both success and exception paths.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-UREDEEM_049
**Scenario Title:** Acceptance — AC-C3: close_operations states advance sequentially, no step skipped
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §F.5 AC-C3; srs/states.md; SRS FR-EXBOT-073 AC
**Test Type:** Acceptance
**Description:** After a full happy-path close, query D1 for the `close_operations` row. Verify the state progression timestamp ordering: `lp_closed` < `funds_returned` < `hedge_close_pending` < `hedge_closed` < `done`. No state must be missing from the record. `[TBD — pending BA answer: I-01 — atomicity between lp_closed and funds_returned must be confirmed to determine whether a single timestamp or two separate timestamps are expected]`
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-UREDEEM_050
**Scenario Title:** Integration — user_redeem and bot_safe_close coexist; a bot in lp_closing cannot be re-enqueued into both queues simultaneously
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)
**Req-ID:** UC §1.3 scope; UC §2 Precondition 3; srs/states.md
**Test Type:** Integration
**Description:** Verify that once a bot has `bots.lifecycle_state='lp_closing'` (entered user_redeem close path), the `bot_safe_close` flow cannot also initiate a close on the same bot. The precondition check must block any system-initiated close attempt on a bot already in the `lp_closing` state.
**Test Focus:** Integration


---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| `close_operations.state` crash recovery between `lp_closed` and `funds_returned` (TS_039) | BLOCKED: I-01 — atomicity of `lp_closed` → `funds_returned` transition not defined. BA/Tech Lead must confirm: single D1 transaction or two separate updates? Resume strategy when worker crashes between them? | Resolve via BA Q&A; re-audit UC §3 step 7 and states.md before writing expected result. |
| `bots.lifecycle_state` value when `close_operations.state='residual_hl_liability'` (TS_016) | BLOCKED: I-02 — states.md and UC §A2/§5 do not define `lifecycle_state` in this terminal failure path. | Resolve via BA Q&A; add explicit lifecycle_state definition for residual_hl_liability path in states.md. |
| `bots.lifecycle_state='lp_closing'` transition timing (TS_020) | BLOCKED: I-03 — UC does not describe which step in the user_redeem worker sets `lifecycle_state='lp_closing'`. States.md documents the transition but not the trigger point in the worker. | BA/Tech Lead to confirm which specific step sets `lp_closing`. |
| FR-EXBOT-071 traceability | BLOCKED: I-04 — UC §7 FR Trace cites FR-EXBOT-071 which does not exist in spec.md (spec jumps from FR-EXBOT-070 to FR-EXBOT-072) or in FRD. Traceability is broken for any scenario that would need to trace to FR-EXBOT-071. | BA to confirm if FR-EXBOT-071 is a typo or a missing requirement. Remove or add to spec.md and FRD. |
| `HLRateLimitDO` behavior in user_redeem context (TS_029) | BLOCKED: I-05 — UC does not describe whether worker releases `UserLockDO` before re-queuing when `HLRateLimitDO` denies. Re-queue delay strategy not defined for user_redeem P0 flow. | BA/Tech Lead to confirm lock release and re-queue behavior when rate limited mid-operation. |
| Agent key decryption failure path in user_redeem (TS_030) | BLOCKED: I-06 — UC does not describe what happens if the HL agent key is revoked, expired, or AES-GCM decrypt fails when the P0 user_redeem worker needs to sign an order. Behavior is undefined (SAFE_MODE? residual_hl_liability? different error?) | BA/Tech Lead to define agent key failure path explicitly for user_redeem. This is a security-critical P0 path. |
| HL-portion USDC transfer mechanism (TS_010) | BLOCKED: I-07 — UC §3 step 13 references "RedemptionQueue ledger" but SRS FR-EXBOT-070 states user_redeem does not use `RedemptionQueue.createRequest/fulfillRequest` (that is bot_safe_close). The exact mechanism for sending HL-portion USDC to the investor is not defined. | BA/Tech Lead to clarify: which contract function or off-chain mechanism sends HL-portion USDC? Resolve contradiction between UC §3 step 13 and SRS FR-EXBOT-070. |
| Partial fill handling for `closeShortReduceOnlyIoc` (TS_031) | BLOCKED: I-10 — UC does not define behavior when the close order is only partially filled. Whether to re-submit for remainder or count as failure is unspecified. | BA/Tech Lead to define partial fill handling: re-submit with remaining size or treat as A2 hedge close failure? |
| Performance / load testing of user_redeem queue throughput | NFR: PERFORMANCE / LOAD — testing queue throughput and concurrency limits under load is out of scope for functional scenario design. | Defer to performance/load testing specialist with SLA targets from NFR-EXBOT-003. |
| On-chain smart contract security (reentrancy, front-running) | NFR: SECURITY — smart contract security audit is out of scope for SOTATEK (per IC-EXBOT-002, ABI is provided by zen; contract internals are zen's responsibility). | Defer to zen's smart contract security audit. Verify ABI matches expected events. |
| RedemptionEvent Watcher replay attack / event authenticity | NFR: SECURITY — no description in UC of how the Watcher verifies event authenticity or prevents replay attacks. Out of scope for functional test design. | BA to document event authenticity validation (block confirmations, deduplication window). Then include in integration scenarios. |

