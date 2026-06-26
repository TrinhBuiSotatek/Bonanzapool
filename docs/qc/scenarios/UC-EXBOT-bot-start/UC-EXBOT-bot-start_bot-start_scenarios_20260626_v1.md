# Test Scenarios — UC-EXBOT-bot-start Bot Initialization

> Source: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260617_v1.md
> Generated: 2026-06-26
> Author: qc-func-scenario-design-exbot
> Version: v1
> Domain/Architecture: Cloudflare Workers (ExBot Worker + OPERATOR Facade), Cloudflare D1, Hyperliquid REST API, BnzaExVault Solidity contract, Uniswap V3 on-chain LP. No UI — backend logic only.
>
> **Note on UC readiness:** Audited score 52/100 (Not Ready at audit time). BA responses 2026-06-20 resolved Blockers I-01, I-04, I-08, I-16, I-22. Scenarios are designed against confirmed content; blocked/open areas are excluded and flagged in §Out-of-Scope Flags.

---

## UC-EXBOT-bot-start — Bot Initialization

### Scenario ID: TS_UC-EXBOT-bot-start_001
**Scenario Title:** Happy path — all preflight checks pass, bot reaches active state
**UC Reference:** UC-EXBOT-bot-start — Bot Initialization
**Req-ID:** UC-EXBOT-bot-start §3 Main Flow; SRS FR-EXBOT-001/002/003/021/024/025/030/031
**Test Type:** End-to-End
**Description:** Submit a valid `POST /api/exbot/start` request through OPERATOR Facade for a user who has no existing active/paused/closing/safe_mode/error bot, HL isolated margin ≥ required × 2.0, agent key approved and not expired, builder fee confirmed, and LP mint simulation passes. The system must create a bot record, traverse all 8 lifecycle states (`preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`), populate `positions` and `hedge_legs` rows in D1, and return `{status: "active", botId}`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_002
**Scenario Title:** One-bot policy blocks start when user already has an active bot
**UC Reference:** UC-EXBOT-bot-start §4 A1
**Req-ID:** UC-EXBOT-bot-start §3.3; SRS FR-EXBOT-001; BR-EXBOT-001; E-EXBOT-001
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` for a user who already has one ExBot with `status = 'active'`. The system must reject the request with error E-EXBOT-001 ("You already have an active ExBot. Close or wait for the existing bot to finish.") and must not create any new bot record in `bots` or `bot_registry`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_003
**Scenario Title:** One-bot policy blocks start — user has a bot in `paused` state
**UC Reference:** UC-EXBOT-bot-start §4 A1
**Req-ID:** SRS BR-EXBOT-001; FR-EXBOT-001; E-EXBOT-001
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` for a user whose existing bot has `status = 'paused'`. BR-EXBOT-001 includes `paused` in the blocking set. The system must reject with E-EXBOT-001 and create no new bot record.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_004
**Scenario Title:** One-bot policy blocks start — user has a bot in `closing` state
**UC Reference:** UC-EXBOT-bot-start §4 A1
**Req-ID:** SRS BR-EXBOT-001; FR-EXBOT-001; E-EXBOT-001
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` for a user whose existing bot has `status = 'closing'`. The system must reject with E-EXBOT-001. `closing` is explicitly in the blocked set per BR-EXBOT-001.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_005
**Scenario Title:** One-bot policy blocks start — user has a bot in `safe_mode` state
**UC Reference:** UC-EXBOT-bot-start §4 A1
**Req-ID:** SRS BR-EXBOT-001; FR-EXBOT-001; E-EXBOT-001
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` for a user whose existing bot has `status = 'safe_mode'`. The system must reject with E-EXBOT-001.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_006
**Scenario Title:** One-bot policy blocks start — user has a bot in `error` state
**UC Reference:** UC-EXBOT-bot-start §4 A1
**Req-ID:** SRS BR-EXBOT-001; FR-EXBOT-001; E-EXBOT-001
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` for a user whose existing bot has `status = 'error'`. The system must reject with E-EXBOT-001.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_007
**Scenario Title:** One-bot policy allows start — user's only previous bot is `closed`
**UC Reference:** UC-EXBOT-bot-start §3 Main Flow; §4 A1
**Req-ID:** SRS BR-EXBOT-001; FR-EXBOT-001
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` for a user whose only prior bot record has `status = 'closed'`. BR-EXBOT-001 does not include `closed` in the blocking set. The system must allow the start to proceed past preflight check 1.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_008
**Scenario Title:** Preflight check 2 blocks — HL margin balance exactly at required × 2.0 minus one unit
**UC Reference:** UC-EXBOT-bot-start §4 A2
**Req-ID:** SRS FR-EXBOT-002; FR-EXBOT-061; E-EXBOT-002
**Test Type:** Functional
**Description:** Configure the HL isolated margin balance so that `marginBalanceUsd` is exactly `(marginRequiredUsd × 2.0) - ε` (just below the threshold). The system must reject with E-EXBOT-002, showing the required amount and the shortfall, and must not create a bot record.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_009
**Scenario Title:** Preflight check 2 passes — HL margin balance exactly at required × 2.0
**UC Reference:** UC-EXBOT-bot-start §3.3
**Req-ID:** SRS FR-EXBOT-002; FR-EXBOT-061
**Test Type:** Functional
**Description:** Configure the HL isolated margin balance so that `marginBalanceUsd` is exactly `marginRequiredUsd × 2.0` (at threshold). The system must allow preflight check 2 to pass and proceed to check 3.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_010
**Scenario Title:** Preflight check 2 blocks — HL margin insufficient, error message contains correct computed values
**UC Reference:** UC-EXBOT-bot-start §4 A2
**Req-ID:** SRS FR-EXBOT-061; E-EXBOT-002
**Test Type:** Functional
**Description:** Submit start with a known HL margin balance ($300) and a computable `marginRequiredUsd × 2.0` ($700). The system must return E-EXBOT-002 with the verbatim message format: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit $400 to HL." The computed values must match the actual margin state fetched from HL.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_011
**Scenario Title:** Preflight check 3 blocks — agent key status is `pending`
**UC Reference:** UC-EXBOT-bot-start §4 A3
**Req-ID:** SRS FR-EXBOT-081; FR-EXBOT-083; E-EXBOT-003
**Test Type:** Functional
**Description:** Set `hl_agent_keys.approval_status = 'pending'` for the user. Submit `POST /api/exbot/start`. The system must reject with E-EXBOT-003 verbatim: "Agent key is awaiting approval. Please complete the approval process before starting." No bot record must be created.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_012
**Scenario Title:** Preflight check 3 blocks — agent key is expired (`approved` but `expires_at` in the past)
**UC Reference:** UC-EXBOT-bot-start §4 (A5–A11 added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-083; E-EXBOT-004
**Test Type:** Functional
**Description:** Set `hl_agent_keys.approval_status = 'approved'` and `expires_at = now - 1 second`. Submit start. The system must reject with E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." No bot record created.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_013
**Scenario Title:** Preflight check 3 blocks — agent key status is `revoked`
**UC Reference:** UC-EXBOT-bot-start §2 preconditions; question Q19 (Open)
**Req-ID:** SRS FR-EXBOT-082
**Test Type:** Functional
**Description:** Set `hl_agent_keys.approval_status = 'revoked'` for the user. Submit start. The system must reject the request — the exact error code and message is an open question (Q19), so this scenario verifies that a rejected response is returned and no bot record is created. Document the actual error code returned for BA review.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_014
**Scenario Title:** Preflight check 3 blocks — agent key status is `superseded`
**UC Reference:** UC-EXBOT-bot-start §2; question Q19 (Open)
**Req-ID:** SRS FR-EXBOT-083
**Test Type:** Functional
**Description:** Set `hl_agent_keys.approval_status = 'superseded'` (key rotation in progress; old key superseded, new key pending approval). Per SRS FR-EXBOT-083, "existing approved key remains active until admin approves replacement" — so this scenario verifies whether a `superseded` key still allows start or blocks it. Document actual behavior for BA clarification.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_015
**Scenario Title:** Preflight check 4 blocks — HL builder fee 5bps not confirmed
**UC Reference:** UC-EXBOT-bot-start §4 A5 (added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-002 step 4; E-EXBOT-005; OQ-EXBOT-05 (mechanism TBD)
**Test Type:** Functional
**Description:** Arrange a state where the HL builder fee 5bps approval has not been confirmed for the user. Submit start. The system must reject with E-EXBOT-005: "HL builder fee (5bps) approval required before starting ExBot." No bot record created. The exact mechanism for checking confirmation is pending OQ-EXBOT-05; this scenario validates the blocking behavior regardless of mechanism.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_016
**Scenario Title:** Preflight check 5 blocks — LP mint simulation fails due to slippage
**UC Reference:** UC-EXBOT-bot-start §4 A6 (added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-001 step 5; E-EXBOT-006; Q11 (slippage threshold TBD)
**Test Type:** Functional
**Description:** Arrange conditions where the simulated `BnzaExVault.vaultMint` call fails slippage tolerance (exact threshold pending Q11). Submit start. The system must reject with E-EXBOT-006: "LP mint simulation failed. Check pool liquidity or adjust deposit amount." No bot record created. Preflight check 5 blocks before any on-chain tx is submitted.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_017
**Scenario Title:** LP mint transaction fails on-chain — bot transitions to `error` state
**UC Reference:** UC-EXBOT-bot-start §4 A4
**Req-ID:** SRS states.md `lp_opening → error`
**Test Type:** Functional
**Description:** All preflight checks pass; bot record is inserted with `lifecycle_state = 'preflight'`, transitions to `lp_opening`, then the on-chain `vaultMint` tx reverts. The system must transition the bot to `lifecycle_state = 'error'` and must not leave the bot stuck in `lp_opening`. The `positions` row must not be created. Note: the exact fund-return mechanism after revert is open (Q5) — this scenario verifies the state transition only.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_018
**Scenario Title:** State machine — bot record inserted at `preflight` before any external call
**UC Reference:** UC-EXBOT-bot-start §3.4
**Req-ID:** SRS FR-EXBOT-003; ERD `bots`, `bot_registry`
**Test Type:** Data/State
**Description:** After OPERATOR forwards the request and preflight checks 1–5 all pass, verify that a `bots` record with `lifecycle_state = 'preflight'` and a `bot_registry` record are inserted into D1 before the ExBot Worker submits the `vaultMint` transaction. The `shard_id`, `chain`, and `wallet_address` fields must be populated at this point.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_019
**Scenario Title:** State machine — `lp_opening → lp_opened` on `VaultMinted` event receipt
**UC Reference:** UC-EXBOT-bot-start §3.5–3.6
**Req-ID:** SRS FR-EXBOT-003; states.md `lp_opening → lp_opened`; ERD `positions`
**Test Type:** Data/State
**Description:** After `vaultMint` is submitted, the bot is in `lp_opening`. When the `VaultMinted(user, botId, tokenId, liquidity)` event is confirmed, the system must atomically: (1) insert a `positions` row with `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `liquidity`, `pool_address`, `custodian = 'vault'`; (2) transition `bots.lifecycle_state` to `lp_opened`. Verify both writes occur in the same atomic D1 operation.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_020
**Scenario Title:** State machine — `lp_opened → hedge_pre_open` transition persisted before HL call
**UC Reference:** UC-EXBOT-bot-start §3.7; Q6 (state gap in UC)
**Req-ID:** SRS states.md `lp_opened → hedge_pre_open`; FR-EXBOT-020/021
**Test Type:** Data/State
**Description:** After `lp_opened`, the worker computes `targetShortEth = lpEthAmount × hedgeRatio (Phase A = 0.70)` using TickMath + LiquidityAmounts from confirmed `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick`. The system must persist `lifecycle_state = 'hedge_pre_open'` in D1 before submitting the HL short order. Verify state is written before the HL API is called.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_021
**Scenario Title:** State machine — `hedge_post_confirmed` and `hedge_legs` row after reconcile passes
**UC Reference:** UC-EXBOT-bot-start §3.8–3.9
**Req-ID:** SRS FR-EXBOT-025; states.md `hedge_pre_open → hedge_post_confirmed`; ERD `hedge_legs`
**Test Type:** Data/State
**Description:** After HL `openShortIoc` is submitted and `clearinghouseState` confirms actual short size = target ± tolerance, the system must: (1) insert a `hedge_legs` row with `entry_price`, `liquidation_price`, `effective_leverage`, `isolated_margin_usd`, `hl_asset`, `target_ratio`, `leverage`, `margin_mode` all populated; (2) transition to `lifecycle_state = 'hedge_post_confirmed'`. Verify all required fields are non-null.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_022
**Scenario Title:** State machine — `stop_placing → stop_verified → active` on successful stop placement
**UC Reference:** UC-EXBOT-bot-start §3.10–3.11
**Req-ID:** SRS FR-EXBOT-030/031; states.md `stop_placing → stop_verified → active`
**Test Type:** Data/State
**Description:** After `hedge_post_confirmed`, the worker computes `stop_trigger_px` via BigDecimal using `liq_distance_pct × stopSafetyFactor (Phase A = 0.70)`, transitions to `stop_placing`, submits `placeReduceOnlyStopMarket`, and upon confirmation transitions `stop_verified → active`. Verify: `hedge_legs` is updated with `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size`, `stop_distance_pct`, `stop_last_verified_at`; `bots.lifecycle_state = 'active'`; `bots.status = 'active'`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_023
**Scenario Title:** Post-active init — `bot_runtime_state` and `circuit_breakers` initialized correctly
**UC Reference:** UC-EXBOT-bot-start §3.11; Q20 (post-active init gap)
**Req-ID:** SRS FR-EXBOT-013; FR-EXBOT-040; FR-EXBOT-003
**Test Type:** Data/State
**Description:** After bot reaches `active`, verify: (1) a `bot_runtime_state` row is inserted with `next_light_check_at` set to `now + 5min + jitter (±45s)`, `last_hl_reconcile_at` and `last_known_hl_short_size` populated; (2) a `circuit_breakers` row is initialized with `state = 'closed'`. These post-conditions are required for light-check to pick up the new bot.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_024
**Scenario Title:** HL IOC reject — insufficient margin during hedge open, bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-bot-start §4 A10 (added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-050; E-EXBOT-007; states.md `hedge_pre_open → safe_mode`
**Test Type:** Functional
**Description:** All preflight checks pass; LP minted successfully; HL returns a rejection for `openShortIoc` due to insufficient margin during synchronization. The system must: (1) transition bot to SAFE_MODE; (2) emit E-EXBOT-007 alert: "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin."; (3) not transition to `hedge_post_confirmed`. LP NFT is already minted; rollback behavior is pending UC gap (Q4/Q5).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_025
**Scenario Title:** HL API unreachable during hedge open — bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-bot-start §4 A7 (added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-050; E-EXBOT-008
**Test Type:** Functional
**Description:** All preflight checks pass; LP minted successfully; HL API is unreachable when the worker attempts `openShortIoc`. The system must enter SAFE_MODE and emit E-EXBOT-008: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." Bot must not reach `active`. Per SRS FR-EXBOT-050, HL unreachable > 5 minutes is a SAFE_MODE trigger.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_026
**Scenario Title:** Reconcile mismatch after hedge open — bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-bot-start §4 A11 (added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-025; FR-EXBOT-050; E-EXBOT-011
**Test Type:** Functional
**Description:** HL `openShortIoc` is submitted and acknowledged; however `clearinghouseState` returns an actual short size that differs from `targetShortEth` beyond the allowed tolerance. The system must: (1) enter SAFE_MODE; (2) emit E-EXBOT-011: "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation."; (3) not persist a successful `hedge_legs` row. State must be `safe_mode` not `hedge_post_confirmed`.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_027
**Scenario Title:** Stop placement fails — bot transitions `stop_placing → safe_mode`
**UC Reference:** UC-EXBOT-bot-start §4 A8 (added 2026-06-20)
**Req-ID:** SRS FR-EXBOT-031; E-EXBOT-009; states.md `stop_placing → safe_mode`
**Test Type:** Functional
**Description:** LP minted; hedge open reconciled; worker transitions to `stop_placing` and submits `placeReduceOnlyStopMarket`. HL rejects the stop order. The system must: (1) transition `stop_placing → safe_mode`; (2) emit E-EXBOT-009: "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop."; (3) not transition to `active`. The `stop_cloid` must be recorded even on failure for retry tracing.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_028
**Scenario Title:** Cloid determinism — retrying HL hedge open with same botId and attemptId produces same cloid
**UC Reference:** UC-EXBOT-bot-start §3.7
**Req-ID:** SRS FR-EXBOT-024
**Test Type:** Integration
**Description:** For the same `botId`, `attemptId`, `stage`, and `version`, compute `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` twice. The two resulting cloids must be identical. When the same cloid is submitted to HL a second time, HL must not create a duplicate order (idempotent deduplication). This verifies the retry-safety of the cloid scheme.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_029
**Scenario Title:** Different stage produces different cloid for same botId
**UC Reference:** UC-EXBOT-bot-start §3.7; §3.10
**Req-ID:** SRS FR-EXBOT-024
**Test Type:** Integration
**Description:** For the same `botId` and `attemptId`, compute cloid for `stage = 'hedge_open'` and for `stage = 'stop_place'`. The two cloids must be different. This ensures the hedge-open order and the stop order cannot collide on HL's deduplication table.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_030
**Scenario Title:** BigDecimal precision — `targetShortEth` computed without floating-point loss
**UC Reference:** UC-EXBOT-bot-start §3.7; SRS NFR-EXBOT-008
**Req-ID:** SRS FR-EXBOT-021; NFR-EXBOT-008
**Test Type:** Functional
**Description:** Provide an `lpEthAmount` value that would lose precision under standard JavaScript `Number` arithmetic (e.g., a value with more than 15 significant digits). Verify that `targetShortEth = lpEthAmount × hedgeRatio (Phase A = 0.70)` is computed using BigDecimal and that no `Number()` conversion occurs at any intermediate step. The result stored in `hedge_legs.target_ratio` and used for HL must match the BigDecimal-computed value exactly.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_031
**Scenario Title:** BigDecimal precision — `stop_trigger_px` computed without floating-point loss
**UC Reference:** UC-EXBOT-bot-start §3.10
**Req-ID:** SRS FR-EXBOT-030; NFR-EXBOT-008
**Test Type:** Functional
**Description:** Using a known `entry_price` and `liquidation_price` that would produce precision loss under `Number` arithmetic, verify that the full stop price computation chain (`liq_distance_pct → stop_distance_pct → stop_trigger_px`) uses BigDecimal throughout. The `stop_price` stored in `hedge_legs` must match the expected BigDecimal result with no rounding error from float conversion.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_032
**Scenario Title:** `effective_leverage > 4.5` at reconcile step triggers SAFE_MODE
**UC Reference:** UC-EXBOT-bot-start §3.8; SRS FR-EXBOT-050
**Req-ID:** SRS FR-EXBOT-050; states.md SAFE_MODE triggers
**Test Type:** Functional
**Description:** After hedge open, `clearinghouseState` returns `effective_leverage = 4.51` (just above the 4.5 threshold). Per SRS FR-EXBOT-050, `effective_leverage > 4.5` is a SAFE_MODE trigger. The system must enter SAFE_MODE and must not transition to `hedge_post_confirmed` or proceed to stop placement.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_033
**Scenario Title:** `effective_leverage` exactly at 4.5 does not trigger SAFE_MODE
**UC Reference:** UC-EXBOT-bot-start §3.8; SRS FR-EXBOT-050
**Req-ID:** SRS FR-EXBOT-050
**Test Type:** Functional
**Description:** After hedge open, `clearinghouseState` returns `effective_leverage = 4.5` (at the threshold, not exceeding it). The system must not enter SAFE_MODE and must proceed normally to `hedge_post_confirmed`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_034
**Scenario Title:** HL margin sufficiency — margin buffer exactly at 2.0× with HL oracle price variation
**UC Reference:** UC-EXBOT-bot-start §3.3 preflight check 2
**Req-ID:** SRS FR-EXBOT-061; FR-EXBOT-002
**Test Type:** Functional
**Description:** The margin check formula is `marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`. Verify that a change in `hlOraclePrice` (e.g., ETH price rises between preflight and hedge execution) correctly recomputes `marginRequiredUsd` at the time of check. The check must use the live price fetched from HL `marginSummary`, not a cached value.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_035
**Scenario Title:** Direct HTTP request to ExBot Worker URL returns 403
**UC Reference:** UC-EXBOT-bot-start §3.2; BR-EXBOT-010
**Req-ID:** SRS FR-EXBOT-090; BR-EXBOT-010
**Test Type:** Functional
**Description:** Send a `POST /api/exbot/start` request directly to the ExBot Worker's internet-facing URL, bypassing OPERATOR Facade (i.e., not using the Cloudflare service binding). The ExBot Worker must return HTTP 403 and must not execute any preflight logic or create any bot record. This validates BR-EXBOT-010 enforcement.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-bot-start_036
**Scenario Title:** OPERATOR Facade rejects request with missing or invalid internal token
**UC Reference:** UC-EXBOT-bot-start §3.2
**Req-ID:** SRS FR-EXBOT-090
**Test Type:** Functional
**Description:** Submit `POST /api/exbot/start` to the OPERATOR Facade with a missing, malformed, or expired internal authentication token. The Facade must reject the request before forwarding to ExBot Worker. No ExBot Worker logic must execute.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-bot-start_037
**Scenario Title:** Concurrent double-submit — two simultaneous start requests for the same user
**UC Reference:** UC-EXBOT-bot-start §3; Q14 (idempotency gap — open)
**Req-ID:** SRS BR-EXBOT-001; FR-EXBOT-001; Q14
**Test Type:** Integration
**Description:** Submit two `POST /api/exbot/start` requests concurrently for the same user who has no existing bot. Exactly one bot must be created and reach `active`; the second request must be rejected with E-EXBOT-001 or a lock-based rejection. No duplicate `bot_registry` records must exist for the user after both requests complete. The exact mechanism (UserLockDO, D1 UNIQUE constraint, or Idempotency-Key header) is an open question (Q14); this scenario documents the expected outcome regardless of mechanism.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_038
**Scenario Title:** Agent key decryption — plain key must not appear in any log
**UC Reference:** UC-EXBOT-bot-start §3.7 (HL signing); SRS NFR-EXBOT-006
**Req-ID:** SRS FR-EXBOT-080; NFR-EXBOT-006
**Test Type:** Integration
**Description:** During a successful bot start, the ExBot Worker decrypts the AES-256-GCM envelope to obtain the plain agent key, signs HL orders, and destroys the plain key after use. Verify that no log entry (Worker logs, D1 audit rows, error messages) contains the plain agent key or the raw DEK. Only `wrapped_dek` should appear in storage. Master private key must never be stored.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_039
**Scenario Title:** Agent key decryption fails mid-flow — start must fail safely
**UC Reference:** UC-EXBOT-bot-start §4 A9 (added 2026-06-20); SRS FR-EXBOT-080
**Req-ID:** SRS FR-EXBOT-080; FR-EXBOT-082; E-EXBOT-004
**Test Type:** Functional
**Description:** Arrange a scenario where the agent key decryption fails (e.g., DEK is corrupted or master key is unavailable) at the point the worker needs to sign an HL order. The system must fail the start request with an appropriate error, not expose partial decrypted key material in any error response, and transition the bot to a non-active error state. The exact error code for decryption failure is Q19 (open); document actual behavior.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_040
**Scenario Title:** Integration — new active bot is picked up by light-check cron within 5–6 minutes
**UC Reference:** UC-EXBOT-bot-start §3.11; UC-EXBOT-light-check §2 trigger
**Req-ID:** SRS FR-EXBOT-012; FR-EXBOT-013
**Test Type:** Integration
**Description:** After bot reaches `active` with `next_light_check_at = now + 5min + jitter(±45s)`, verify that the `bot-scan` cron (1-minute interval) picks up the bot in the first scan cycle where `next_light_check_at <= now`. The bot must appear in the light-check queue within the expected window. This cross-UC integration verifies the hand-off from bot-start to light-check.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_041
**Scenario Title:** Integration — `stop_price` populated in `hedge_legs` is used by light-check stop monitor
**UC Reference:** UC-EXBOT-bot-start §3.10–3.11; UC-EXBOT-light-check stop monitoring
**Req-ID:** SRS FR-EXBOT-014; FR-EXBOT-032
**Test Type:** Integration
**Description:** After a successful bot start, verify that `hedge_legs.stop_price` and `hedge_legs.stop_cloid` are persisted correctly and that the light-check stop monitor reads them accurately. The stop monitor must use the BigDecimal-computed `stop_price`, not a float-converted value. A subsequent light-check cycle must be able to compare `markPrice >= stop_price` using the stored value.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_042
**Scenario Title:** Acceptance — happy path response is `{status: "active", botId}` with correct values
**UC Reference:** UC-EXBOT-bot-start §3.12; AC-01
**Req-ID:** SRS FR-EXBOT-003; US-EXBOT-001 AC-EXBOT-001-1
**Test Type:** Acceptance
**Description:** After a full successful start, the OPERATOR Facade must return HTTP 200 with body `{status: "active", botId}` where `botId` matches the newly created bot record. The `status` field must be the string `"active"` exactly. The response must be received by the calling party (POOL UI via OPERATOR) and must not contain any implementation details (no internal state fields, no key material, no D1 row IDs beyond `botId`).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_043
**Scenario Title:** Acceptance — one-bot policy response is E-EXBOT-001 verbatim
**UC Reference:** UC-EXBOT-bot-start §4 A1; AC-02
**Req-ID:** SRS E-EXBOT-001; US-EXBOT-001 AC-EXBOT-001-2
**Test Type:** Acceptance
**Description:** When a user already has an active bot and submits start, the OPERATOR Facade must return HTTP 409 with the verbatim message: "You already have an active ExBot. Close or wait for the existing bot to finish." The status code and message text must both match exactly.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_044
**Scenario Title:** Acceptance — HL margin error returns E-EXBOT-002 with computed values
**UC Reference:** UC-EXBOT-bot-start §4 A2; AC-03
**Req-ID:** SRS E-EXBOT-002; US-EXBOT-001 AC-EXBOT-001-3
**Test Type:** Acceptance
**Description:** When HL margin balance is $300 and required × 2.0 is $700, the system must return HTTP 400 with verbatim: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit $400 to HL." All three dollar values in the message must be computed dynamically from the actual margin state, not hardcoded.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_045
**Scenario Title:** Acceptance — agent key pending returns E-EXBOT-003 verbatim
**UC Reference:** UC-EXBOT-bot-start §4 A3; AC-04
**Req-ID:** SRS E-EXBOT-003; US-EXBOT-001 AC-EXBOT-001-4
**Test Type:** Acceptance
**Description:** When `hl_agent_keys.approval_status = 'pending'`, the system must return HTTP 400 with verbatim: "Agent key is awaiting approval. Please complete the approval process before starting." This is the canonical message from spec.md §5 E-EXBOT-003. Any paraphrase (e.g., "Agent key must be approved first") must not be accepted.
**Test Focus:** Alternative flow

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Dual-chain (Base vs Optimism) LP open with actual pool addresses | BLOCKED: OQ-EXBOT-03 (NV-12) — pool address + `wethIndex` for USDC/WETH 0.3% on Base and Optimism not yet finalized | Wait for zen Phase 0 NV-12; re-run scenarios after pool addresses are confirmed |
| LP mint simulation slippage boundary scenarios (exact basis-point threshold) | BLOCKED: Q11 — slippage tolerance value not defined in UC or SRS | BA/zen to specify the tolerance; add BVA scenarios (at threshold, just above, just below) once known |
| Builder fee 5bps confirmation mechanism | BLOCKED: OQ-EXBOT-05 — on-chain tx vs API call mechanism TBD | BA/zen to resolve; scenario 015 currently tests blocking behavior only, not mechanism |
| `lpEthAmount` pre-mint source formula | BLOCKED: Q7 — formula for computing `lpEthAmount` before LP NFT is minted is not documented | BA + zen (PositionCalc owner) to specify; required before writing integration test for hedge size accuracy |
| `POST /api/exbot/start` request payload (chain selector, tick range, deposit amount) | BLOCKED: Q12 — request body not documented in UC | BA to document payload; scenarios 001/035/037 currently treat payload as a black box |
| Idempotency mechanism for double-submit (UserLockDO vs D1 UNIQUE vs Idempotency-Key) | BLOCKED: Q14 — mechanism not defined in UC or SRS | BA + Dev to confirm; scenario 037 tests expected outcome only |
| `revoked`/`superseded` agent key exact error code and message | BLOCKED: Q19 — behavior for these key states is undefined in UC | BA to add explicit alt flows for revoked/superseded; scenarios 013–014 document observed behavior for BA review |
| Fund-return mechanism after on-chain `vaultMint` revert (ERC-20 rollback vs explicit refund) | BLOCKED: Q5 — "return funds" in UC §4 A4 is undefined | BA + zen to clarify the contract-level refund path; scenario 017 tests state transition only |
| Performance / latency SLA for full bot-start flow | OUT-OF-SCOPE: NFR-EXBOT-002 states hedge-sync < 30s but no SLA defined for full start flow (Q18) | Defer to performance test team; BA to define expected SLA per chain |
| HL API rate-limit budget consumption during start (HLRateLimitDO interaction) | BLOCKED: Q17 — UC does not describe HLRateLimitDO interaction; implementation detail | Dev to confirm DOs used during start; add integration scenario once confirmed |
| `wethIndex` per-chain verification correctness | BLOCKED: OQ-EXBOT-03 — chain-specific pool config not finalized | Unblocks with NV-12; scenario 019 covers `wethIndex` field population but cannot verify correct value until pool config is known |
| Security beyond functional auth (penetration testing, key-material exfiltration beyond log check) | OUT-OF-SCOPE: NFR-EXBOT-006 security testing beyond scenario 038 | Defer to security specialist team |
| GDPR / PII handling for `wallet_address` and `hl_user_address` | OUT-OF-SCOPE: No NFR defined (Q21 / audit gap) | BA to confirm compliance requirement; add scope if applicable |
