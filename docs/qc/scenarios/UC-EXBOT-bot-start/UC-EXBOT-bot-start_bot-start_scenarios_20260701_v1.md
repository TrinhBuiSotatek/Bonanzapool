# Test Scenarios — UC-EXBOT-bot-start Start ExBot

> Source: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260630_v1.md
> QnA: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_questions_20260701_v1.md
> Generated: 2026-07-01
> Domain/Architecture: Cloudflare Workers (ExBot Worker + Key-Provision Worker) + AWS KMS (Signing Lambda) + Hyperliquid perp API + BnzaExVault on-chain (Base + Optimism) + Cloudflare D1 (control_db + state_db_shard) + Queues (key-provision, bot-start) + Durable Objects (HLRateLimitDO)

---

## UC-EXBOT-bot-start — Start ExBot (system-triggered after on-chain deposit)

---

### Scenario ID: TS_UC-EXBOT-bot-start_001
**Scenario Title:** Happy path — full bot-start from key-provision to active state
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-004, FR-EXBOT-020, FR-EXBOT-025, FR-EXBOT-030, FR-EXBOT-031, FR-EXBOT-080
**Test Type:** End-to-End
**Description:** Trigger the full bot-start flow for a user who has no existing active ExBot, sufficient HL isolated margin (>= required × 2.0), a confirmed `hl_agent_keys.key_status='active'` row, confirmed builder fee (5bps), and passing LP mint simulation. The system must progress through all 9 lifecycle states in sequence (preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active) with no state skipped, each transition persisted atomically to D1. After reaching `active`: `bots.lifecycle_state='active'`, `bots.status='active'`, `positions.custodian='vault'` with tokenId populated, `hedge_legs.stop_price` and `stop_cloid` populated (BigDecimal strings), and no plaintext private key material in `hl_agent_keys`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_002
**Scenario Title:** Key-provision — KMS generates master key and agent key, private keys never leave HSM
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, NFR-EXBOT-006
**Test Type:** Functional
**Description:** Trigger key-provision flow after an on-chain deposit event. The Key-Provision Worker must call KMS `GenerateKeyPair` twice (master key, then agent key). Verify: (1) KMS returns only the public addresses (`hl_user_address`, `agent_address`) — no private key material appears in the worker response, D1 rows, or application logs; (2) `hl_agent_keys` row is written with `key_status='active'`, `hl_user_address`, and `agent_address` populated; (3) no raw private key value is visible in any log stream.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_003
**Scenario Title:** Key-provision — HL approveAgent registration succeeds before key_status set to active
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080
**Test Type:** Functional
**Description:** After KMS generates both keys, the Key-Provision Worker calls HL `approveAgent(hl_user_address, agent_address)`. Verify that `hl_agent_keys.key_status` is only set to `'active'` AFTER HL confirms the agent registration — not before. If HL confirmation is pending, `key_status` must remain `'provisioning'` and no `bot-start` job is enqueued yet.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_004
**Scenario Title:** Key-provision — KMS failure during key generation triggers retry and admin alert after 3 attempts
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, IC-EXBOT-005
**Test Type:** Functional
**Description:** Simulate KMS `ThrottlingException` (or equivalent failure) during `GenerateKeyPair`. The Key-Provision Worker must retry up to 3 times with exponential backoff. After the 3rd failure, an admin alert must be sent. Verify: (1) no partial `hl_agent_keys` row is created with `key_status='active'`; (2) admin notification is triggered; (3) no `bot-start` job is enqueued.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_005
**Scenario Title:** Key-provision — HL approveAgent failure leaves key_status as provisioning and triggers retry
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080
**Test Type:** Functional
**Description:** Simulate HL `approveAgent` call failure after both KMS key pairs are generated. Verify: (1) `hl_agent_keys.key_status` remains `'provisioning'` (not set to `'active'`); (2) the Key-Provision Worker re-enqueues a retry via the key-provision queue; (3) an admin alert is sent when SLA is breached; (4) no `bot-start` job is enqueued until `key_status='active'` is confirmed.
**Test Focus:** Error/Exception


---

### Scenario ID: TS_UC-EXBOT-bot-start_006
**Scenario Title:** Key-provision — duplicate queue message does not provision a second key pair
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-011, FR-EXBOT-080, BR-EXBOT-012
**Test Type:** Functional
**Description:** Deliver the same `key-provision` queue message twice (simulating Cloudflare Queue at-least-once redelivery). Verify: (1) the second delivery encounters a UNIQUE constraint conflict on `queue_idempotency.message_id` and exits immediately without calling KMS again; (2) only one `hl_agent_keys` row with `key_status='active'` exists for the user; (3) no second `bot-start` job is enqueued.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_007
**Scenario Title:** Key-provision — only one active agent key row per user enforced at DB level
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** BR-EXBOT-012, FR-EXBOT-080
**Test Type:** Data/State
**Description:** Attempt to insert a second `hl_agent_keys` row with `key_status='active'` for the same user while an existing `active` row already exists (simulating a race or misconfigured re-provisioning). Verify that the DB-level constraint (BR-EXBOT-012: only one `active` row per user at any time) rejects the second insert, and the existing active row remains intact.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_008
**Scenario Title:** Preflight step 1 — one-bot policy blocks start when user already has active ExBot
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001
**Test Type:** Functional
**Description:** Trigger a `bot-start` queue message for a user who already has a bot with `status='active'` in `bot_registry`. Verify: (1) E-EXBOT-001 ("You already have an active ExBot. Close or wait for the existing bot to finish.") is returned; (2) no new bot record is created in D1; (3) `bot_registry` count for the user remains 1.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_009
**Scenario Title:** Preflight step 1 — one-bot policy counts paused, closing, safe_mode, and error statuses
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001
**Test Type:** Functional
**Description:** Execute 4 separate scenarios: trigger a `bot-start` job when the user has an existing bot with `status='paused'`; then `status='closing'`; then `status='safe_mode'`; then `status='error'`. In every case verify E-EXBOT-001 is returned and no new bot record is created. All four statuses count toward the one-bot limit per BR-EXBOT-001.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_010
**Scenario Title:** Preflight step 1 — start allowed when user's only existing bot has status='closed'
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001
**Test Type:** Functional
**Description:** Trigger a `bot-start` job for a user who has one existing bot with `status='closed'`. Verify that preflight step 1 passes (the query count for disqualifying statuses = 0) and the flow proceeds to preflight step 2. A `closed` bot must not block a new start.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_011
**Scenario Title:** Preflight step 2 — margin check passes at exactly 2.0× required margin (boundary)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-061, FR-EXBOT-002
**Test Type:** Functional
**Description:** Set the user's HL isolated margin balance to exactly `(lpEthAmount × hedgeRatio × hlOraclePrice / leverage) × 2.0`. Verify preflight step 2 passes and the flow proceeds to step 3. The formula must use `hlOraclePrice` specifically (not HL mark price or Uniswap pool price).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_012
**Scenario Title:** Preflight step 2 — margin check fails at 2.0× required minus $1 (insufficient)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-061, FR-EXBOT-002
**Test Type:** Functional
**Description:** Set the user's HL isolated margin balance to `(required × 2.0) − $1`. Verify: (1) E-EXBOT-002 is returned with the correct required amount, current amount, and shortfall ($1); (2) no bot record is created; (3) preflight stops at step 2.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_013
**Scenario Title:** Preflight step 2 — HL API unreachable returns E-EXBOT-008 and blocks start without creating bot record
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, E-EXBOT-008
**Test Type:** Functional
**Description:** Simulate HL API being unreachable when ExBot Worker fetches `marginSummary` during preflight step 2. Verify: (1) start request fails immediately with E-EXBOT-008 ("Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."); (2) no bot record is created in D1; (3) preflight does not proceed to step 3. (Confirmed behavior from I-03 answer: preflight HL timeout = immediate fail, no retry loop.)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_014
**Scenario Title:** Preflight step 2 — HL rate-limit weight consumed even when a later preflight step fails
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-091
**Test Type:** Integration
**Description:** Execute a bot-start flow where preflight step 2 (margin check, weight=2) succeeds but preflight step 3 (key_status check) fails. Verify via `HLRateLimitDO` sliding-window state that weight=2 was declared and consumed at step 2 and is not reversed by the step 3 failure. This is per FR-EXBOT-091: weight is accounted before the HL call and consumed regardless of downstream outcome.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_015
**Scenario Title:** Preflight step 3 — key not provisioned blocks start with E-EXBOT-017
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-080, E-EXBOT-017
**Test Type:** Functional
**Description:** Trigger a `bot-start` job for a user who has no `hl_agent_keys` row with `key_status='active'` (e.g., the key-provision flow has not yet completed). Verify: (1) E-EXBOT-017 ("Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup.") is returned; (2) no bot record is created; (3) preflight stops at step 3 without reaching step 4.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_016
**Scenario Title:** Preflight step 4 — builder fee not confirmed blocks start with E-EXBOT-005
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, E-EXBOT-005
**Test Type:** Functional
**Description:** Trigger a `bot-start` job where preflight steps 1-3 all pass but builder fee (5bps) has not been confirmed on HL. Verify: (1) E-EXBOT-005 ("HL builder fee (5bps) approval required before starting ExBot.") is returned; (2) no bot record is created; (3) preflight stops at step 4 without reaching step 5. Note: the exact HL endpoint for the fee check is pending OQ-EXBOT-05 — this scenario verifies the gate behavior, not the endpoint implementation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_017
**Scenario Title:** Preflight step 4 — builder fee check is one-time at start; confirmed fee from prior session passes
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, E-EXBOT-005
**Test Type:** Functional
**Description:** Trigger a bot-start for a user whose builder fee was confirmed in a prior session (not the current start attempt). Verify preflight step 4 passes — the system accepts a previously-confirmed builder fee, not requiring a new on-chain or API confirmation per start attempt. (Confirmed by I-10 answer: builder fee check is a one-time check at start, not a re-confirmation flow.)
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_018
**Scenario Title:** Preflight step 5 — LP mint simulation failure blocks start with E-EXBOT-006
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, E-EXBOT-006
**Test Type:** Functional
**Description:** Trigger a `bot-start` job where all preflight steps 1-4 pass but the LP mint simulation fails (e.g., pool liquidity too low for the deposit amount). Verify: (1) E-EXBOT-006 ("LP mint simulation failed. Check pool liquidity or adjust deposit amount.") is returned; (2) no bot record is created in D1; (3) no on-chain vault call is made (simulation only, no gas consumed).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_019
**Scenario Title:** Preflight failure — no partial bot record left in D1 after any preflight step fails
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-003
**Test Type:** Functional
**Description:** For each of the 5 preflight steps individually (steps 1-5), trigger a failure at that step. After each failure, query D1 `bot_registry` and verify zero new records exist for the user. The bot record must only be created AFTER all 5 preflight checks pass (UC §3 step 4). No partial records under any failure scenario.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_020
**Scenario Title:** Bot record creation — lifecycle_state='preflight' written atomically after all preflight pass
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003
**Test Type:** Data/State
**Description:** After all 5 preflight checks pass, verify that a bot record is created in D1 with `lifecycle_state='preflight'` and `status` set to the appropriate coarse-grained value, in a single atomic operation. The record must be present in D1 before any `vaultMint` on-chain call is made. Query D1 between preflight completion and vault call to confirm.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_021
**Scenario Title:** LP mint — lifecycle progresses from lp_opening to lp_opened after VaultMinted event
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, FR-EXBOT-004
**Test Type:** Data/State
**Description:** After the bot record is created with `lifecycle_state='preflight'`, ExBot Worker calls `BnzaExVault.vaultMint(...)`. When the `VaultMinted(user, botId, tokenId, liquidity)` on-chain event is received, verify: (1) `positions.token_id` is populated with the correct `tokenId` from the event; (2) `positions.custodian='vault'`; (3) `positions.tick_lower`, `positions.tick_upper` are stored; (4) `bots.lifecycle_state='lp_opened'`.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_022
**Scenario Title:** LP mint — on-chain vaultMint failure transitions bot to error state (A4)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, UC §4 A4
**Test Type:** Functional
**Description:** Simulate `BnzaExVault.vaultMint(...)` on-chain failure (e.g., revert due to slippage exceeding tolerance or insufficient allowance). Verify: (1) `bots.lifecycle_state` transitions to `'error'`; (2) no LP NFT tokenId is written to `positions`; (3) the bot record reflects the error state. Note: the "return funds" mechanism for A4 is pending OQ-EXBOT-08 (ABI not confirmed) — this scenario verifies the state transition only; the on-chain fund recovery postcondition is in the Out-of-Scope Flags.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_023
**Scenario Title:** LP mint — weth_index stored correctly in positions after VaultMinted on Base chain
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-004, NFR-EXBOT-009
**Test Type:** Data/State
**Description:** Complete LP mint on Base chain (chainId=8453). After `VaultMinted` event, verify `positions.weth_index` is populated with the correct value (0 or 1) for the USDC/WETH 0.3% pool on Base — not a hardcoded constant but read from the per-chain verified config. The LP ETH amount calculation must use this stored `weth_index`. Note: exact value pending OQ-EXBOT-03 resolution; this scenario verifies that the field is populated from config, not hardcoded 0.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_024
**Scenario Title:** LP mint — weth_index stored correctly in positions after VaultMinted on Optimism chain
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-004, NFR-EXBOT-009
**Test Type:** Data/State
**Description:** Complete LP mint on Optimism chain (chainId=10). After `VaultMinted` event, verify `positions.weth_index` is populated with the correct value for the USDC/WETH 0.3% pool on Optimism — independently from the Base chain value. If both chains have the same WETH ordering the values may match, but the source must be per-chain config, not a hardcoded assumption. Note: pending OQ-EXBOT-03 resolution.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_025
**Scenario Title:** Hedge open — targetShortEth computed with BigDecimal, not JS float
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-021, NFR-EXBOT-008
**Test Type:** Functional
**Description:** After `lp_opened` state, trigger hedge computation. Verify that `targetShortEth = lpEthAmount × 0.70` is computed using BigDecimal arithmetic. Specifically: (1) no intermediate `Number()` conversion is used for `lpEthAmount` or `hedgeRatio`; (2) the result stored in D1 is a TEXT string (not a JSON number); (3) `normalizeTargetRatioBps("0.70")` returns 7000n (not 6999n or 7001n due to float rounding).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_026
**Scenario Title:** Hedge open — Signing Lambda signs short IOC via KMS agent key and sends to HL
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, NFR-EXBOT-006
**Test Type:** Integration
**Description:** After `targetShortEth` is computed, ExBot Worker sends the signing request to Signing Lambda. Verify: (1) Signing Lambda calls KMS `kms:Sign` using the agent key (not the master key); (2) the signed IOC order is sent to HL; (3) the Signing Lambda is the only IAM principal that calls `kms:Sign`; (4) no private key material appears in the signed payload or in ExBot Worker memory/logs.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_027
**Scenario Title:** Hedge open — deterministic cloid used for short IOC order
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-024
**Test Type:** Functional
**Description:** Verify the cloid for the bot-start short IOC order is computed as `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Submitting the same bot-start attempt (same `botId`, `attemptId`, `stage`, `version`) twice must produce the same cloid. If HL deduplicates, the second submission must be detected and skipped after reconcile without placing a duplicate order.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_028
**Scenario Title:** Hedge open — HL API unreachable during short IOC transitions lifecycle to error state (A7)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** UC §4 A7, E-EXBOT-008
**Test Type:** Functional
**Description:** Simulate HL API being unreachable when ExBot Worker sends the short IOC order (after `lp_opened`). Verify: (1) `bots.lifecycle_state` transitions to `'error'`; (2) E-EXBOT-008 is surfaced; (3) the LP NFT is still held by BnzaExVault (the LP was already minted — bot enters error with LP open but no hedge). No stop is placed in this state.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_029
**Scenario Title:** Hedge open — HL IOC order rejected by exchange transitions lifecycle to error state (A10)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** UC §4 A10
**Test Type:** Functional
**Description:** Simulate HL accepting the signed request but rejecting the IOC order itself (e.g., margin insufficient at order time, self-trade, or order parameter error). Verify: (1) `bots.lifecycle_state` transitions to `'error'`; (2) HL rejection reason is captured; (3) no hedge position exists on HL after the failure.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_030
**Scenario Title:** Post-hedge reconcile — actual HL position confirmed, hedge_legs updated, lifecycle advances to hedge_post_confirmed
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-025
**Test Type:** Data/State
**Description:** After the short IOC order is placed, ExBot Worker fetches `clearinghouseState` from HL to reconcile. Verify: (1) actual short size matches expected; (2) `hedge_legs.entry_price`, `hedge_legs.liquidation_price`, and `hedge_legs.effective_leverage` are populated with BigDecimal strings; (3) `hedge_legs.last_known_hl_short_size` is updated; (4) `bots.lifecycle_state` transitions to `'hedge_post_confirmed'`; (5) no `rebalance_attempts.status='success'` is written before reconcile confirms the state.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_031
**Scenario Title:** Post-hedge reconcile — mismatch beyond threshold enqueues partial_repair and alerts operator (A11)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-025, UC §4 A11, E-EXBOT-011
**Test Type:** Functional
**Description:** Simulate the reconcile step returning an actual HL short size that deviates from the expected size beyond the configured `drift_threshold`. Verify: (1) a `partial_repair` message is enqueued; (2) an operator alert is triggered with E-EXBOT-011 (internal: "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation."); (3) the bot does not proceed to stop placement. Note: exact `drift_threshold` value is pending I-02 / OQ-EXBOT-11 resolution — this scenario verifies the branch logic when threshold is exceeded.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_032
**Scenario Title:** Stop price computation — BigDecimal formula using liquidation_price with stopSafetyFactor=0.70
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-030, NFR-EXBOT-008
**Test Type:** Functional
**Description:** After `hedge_post_confirmed`, compute `stop_trigger_px` using the formula: `stop_trigger_px = entry_price × (1 + ((liquidation_price − entry_price) / entry_price) × 0.70)`. Verify: (1) all arithmetic uses BigDecimal with no intermediate `Number()` conversion; (2) for a 3× isolated margin position, `stop_trigger_px < liquidation_price` with at least 30% distance buffer; (3) the computed value is stored as a TEXT BigDecimal string in `hedge_legs.stop_price`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_033
**Scenario Title:** Stop price computation — fallback to 1/effective_leverage when liquidationPx unavailable
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-030
**Test Type:** Functional
**Description:** Simulate `clearinghouseState` returning a null or absent `liquidationPx` field. Verify that the stop price falls back to: `stop_trigger_px = entry_price × (1 + (1 / effective_leverage) × 0.70)` — the documented fallback formula. The BigDecimal constraint still applies to the fallback computation.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_034
**Scenario Title:** Stop placement — reduce-only stop market placed and confirmed; lifecycle advances to stop_verified then active
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-031, FR-EXBOT-003
**Test Type:** Data/State
**Description:** After `stop_trigger_px` is computed, ExBot Worker places a reduce-only stop market via Signing Lambda. Verify: (1) the stop is placed with the correct trigger price and size; (2) HL confirms the stop order; (3) `hedge_legs.stop_cloid` and `hedge_legs.stop_price` are written; (4) `bots.lifecycle_state` transitions to `'stop_verified'` then immediately to `'active'`; (5) the bot cannot reach `active` state without a confirmed stop — the INV-STOP invariant is satisfied from initialization.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_035
**Scenario Title:** Stop placement failure — lifecycle transitions per states.md (stop_placing → safe_mode) and E-EXBOT-009 is surfaced (A8 — pending BA confirm on state)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-031, UC §4 A8, E-EXBOT-009
**Test Type:** Functional
**Description:** Simulate HL rejecting or failing to confirm the reduce-only stop market after the short IOC was already filled. Verify: (1) E-EXBOT-009 ("Failed to place native stop on Hyperliquid. Bot cannot activate without a stop.") is triggered; (2) an operator alert is sent; (3) the bot does NOT reach `lifecycle_state='active'`; (4) the HL short position remains open. Note: UC §4 A8 states `lifecycle_state='error'` but `srs/states.md` state diagram shows `stop_placing → safe_mode` — the destination state (error vs safe_mode) must be confirmed with BA (I-06 open). This scenario verifies the failure gate and alert; expected destination state is flagged as ambiguous.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_036
**Scenario Title:** Lifecycle state machine — all 9 initialization states transition in strict sequence
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003
**Test Type:** Data/State
**Description:** Execute a full happy-path bot-start and observe D1 `bots.lifecycle_state` at each step. Verify the sequence is exactly: `preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` — with no state skipped, no state repeated, and each transition persisted atomically before the next step begins. Any state arriving out of order or missing is a defect.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_037
**Scenario Title:** Lifecycle state machine — no bot record created if preflight fails (idle does not become preflight on failure)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-003
**Test Type:** Data/State
**Description:** Fail preflight at step 1 (one-bot policy). Verify `bots.lifecycle_state` for the user does not have a new `'preflight'` row. The bot remains in the conceptual `idle` pre-state — meaning no record is created. The constraint: bot record creation only happens after ALL 5 preflight checks pass.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_038
**Scenario Title:** Lifecycle state machine — hedge_pre_open to safe_mode transition when HL short fails
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, srs/states.md
**Test Type:** Data/State
**Description:** Simulate HL short IOC failure during the `hedge_pre_open` → `hedge_post_confirmed` transition (A7 or A10). According to `srs/states.md`, the valid transitions from `hedge_pre_open` are: → `hedge_post_confirmed` (success) or → `safe_mode` (HL order fails). Verify that on IOC failure, the lifecycle state transitions to `safe_mode` (per states.md) — not to `error`. Contrast with UC §4 A7/A10 which records `error` — the states.md is the authoritative state machine.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_039
**Scenario Title:** Bot-start queue idempotency — duplicate bot-start message delivery does not create a second bot
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-011, NFR-EXBOT-007
**Test Type:** Functional
**Description:** Deliver the same `bot-start` queue message twice (redelivery scenario). Verify: (1) the second delivery encounters a UNIQUE constraint conflict on `queue_idempotency.message_id` and exits immediately; (2) only one bot record exists in D1 for the user; (3) no duplicate HL orders are submitted; (4) no duplicate `positions` or `hedge_legs` rows are created.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_040
**Scenario Title:** Concurrent bot-start messages for same user — only one bot is created
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, FR-EXBOT-011, BR-EXBOT-001
**Test Type:** Functional
**Description:** Send two simultaneous `bot-start` queue messages for the same user (simulating a race condition — e.g., two on-chain deposit events processed concurrently). Verify that the one-bot policy check (FR-EXBOT-001) combined with `queue_idempotency` ensures only one bot record is created. The second worker must either hit the idempotency UNIQUE constraint or hit the one-bot policy check after the first bot is created.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_041
**Scenario Title:** Security — hl_agent_keys row contains no plaintext private key after provisioning
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, NFR-EXBOT-006
**Test Type:** Functional
**Description:** After key-provision completes and bot-start runs, dump the `hl_agent_keys` table from D1. Verify: (1) all rows contain only public addresses (`hl_user_address`, `agent_address`) and metadata; (2) no field contains a hex-encoded or base64-encoded 256-bit/512-bit private key pattern; (3) application logs searched for the time window of provisioning show no raw key values. Private keys must remain exclusively within AWS KMS HSM.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_042
**Scenario Title:** Security — direct HTTP request to ExBot Worker returns 403 (not publicly accessible)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-090, BR-EXBOT-010
**Test Type:** Functional
**Description:** Send a direct HTTP POST request to ExBot Worker's URL (bypassing the OPERATOR Facade / CF service binding). Verify the Worker returns 403 and does not process the request. All bot-start operations must only be accessible via the OPERATOR Facade at `POST /api/exbot/start`, which proxies via CF service binding with internal token authentication.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-bot-start_043
**Scenario Title:** Integration — after bot reaches active, light-check and deep-audit are scheduled
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, FR-EXBOT-012, FR-EXBOT-016
**Test Type:** Integration
**Description:** After `bots.lifecycle_state='active'` is set, verify: (1) `bots.next_light_check_at` is set to `now + 5min + jitter(−45s, +45s)` per FR-EXBOT-013; (2) the bot will be picked up by the next light-check cron scan; (3) a deep-audit is scheduled within the next 6 hours. The cross-UC dependencies (UC-EXBOT-light-check, UC-EXBOT-deep-audit) are activated by the `active` lifecycle transition.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_044
**Scenario Title:** Integration — after bot reaches active, status API returns active state
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-090, FR-EXBOT-003
**Test Type:** Integration
**Description:** After `bots.lifecycle_state='active'`, call `GET /api/exbot/status` via the OPERATOR Facade. Verify: (1) the response includes `status='active'`, `botId`, and hedge/LP summary fields; (2) the response does not expose any key material; (3) the OPERATOR logs show the request was proxied via CF service binding to ExBot Worker.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_045
**Scenario Title:** Integration — tokenId stored in positions matches the on-chain LP NFT held by BnzaExVault
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-004, FR-EXBOT-070
**Test Type:** Integration
**Description:** After bot-start completes, query on-chain BnzaExVault for the LP NFT held for the user. Verify `positions.token_id` in D1 matches the actual `tokenId` from the `VaultMinted` event and that the NFT is currently held by BnzaExVault (`custodian='vault'`). This consistency is critical for future `user_redeem` and `bot_safe_close` flows that call `BnzaExVault.redeem(tokenId)`.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_046
**Scenario Title:** Acceptance — full initialization results in bot with stop_price < liquidation_price and >= 30% buffer
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-030, AC-13
**Test Type:** Acceptance
**Description:** Complete a full bot-start with a known 3× isolated margin position on HL. After `active` state: verify `hedge_legs.stop_price` (BigDecimal) is less than `hedge_legs.liquidation_price`, with a distance of at least 30% of the entry-to-liquidation range (stopSafetyFactor=0.70 means stop fires at 70% of the distance to liquidation). This confirms the stop safety buffer is correctly enforced.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_047
**Scenario Title:** Acceptance — margin error displays exact required and shortfall amounts
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-061, AC-03
**Test Type:** Acceptance
**Description:** Trigger a bot-start where `marginBalance=$300` and required (×2.0) =$700. Verify E-EXBOT-002 message contains: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit $400 to HL." The shortfall must be accurate to the nearest dollar (not approximated).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_048
**Scenario Title:** Acceptance — no bot record created on any single preflight failure
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-003, AC-02/03/04/05/06
**Test Type:** Acceptance
**Description:** For each of the 5 preflight failure scenarios (one-bot policy, margin insufficient, key not provisioned, builder fee missing, simulation fail), verify that zero bot records exist in D1 for the user after the failure. The creation of any partial bot record is a defect per FR-EXBOT-002.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_049
**Scenario Title:** Acceptance — redelivered bot-start message produces exactly one successful execution
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-011, AC-14, NFR-EXBOT-007
**Test Type:** Acceptance
**Description:** Deliver the same `bot-start` queue message twice (queue retry simulation). Verify: (1) exactly one bot record is created; (2) exactly one set of `positions` and `hedge_legs` rows is written; (3) exactly one HL short position is opened; (4) the second delivery exits immediately after `queue_idempotency` UNIQUE conflict with no D1 writes and no HL calls. This is the canonical idempotency acceptance criterion.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_050
**Scenario Title:** Acceptance — all 9 lifecycle states transition in order and bot reaches active with hedge and stop confirmed
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, AC-01
**Test Type:** Acceptance
**Description:** Execute a full bot-start happy path and record the sequence of `bots.lifecycle_state` values observed in D1. The sequence must be exactly: `preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`. Final state: `bots.status='active'`, `hedge_legs.stop_price` populated (non-null BigDecimal string), `positions.token_id` populated, `positions.custodian='vault'`. Any deviation in state sequence or missing final field is a defect.
**Test Focus:** Happy path

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| A4 postcondition — on-chain fund return mechanism after LP mint failure | BLOCKED: BnzaExVault ABI not confirmed (OQ-EXBOT-08 Open; IC-EXBOT-002). Cannot determine if revert is automatic or requires explicit ExBot Worker action. I-05 Deferred. | Resolve OQ-EXBOT-08 → confirm ABI → add specific postcondition check to scenario TS_022 |
| Reconcile mismatch boundary test — exact drift_threshold value | BLOCKED: `drift_threshold` value not defined in FR-EXBOT-025 or UC §4 A11. I-02 Open; OQ-EXBOT-11 (lpValueUsd × 3% candidate) not yet confirmed by zen. | Resolve I-02 / OQ-EXBOT-11 → add boundary scenarios at threshold, threshold−1, threshold+1 |
| Preflight builder fee check — exact HL endpoint and weight | BLOCKED: OQ-EXBOT-05 (NV-14) Open — builder fee approval mechanism (on-chain tx vs API call) not confirmed. I-07 Deferred. | Resolve OQ-EXBOT-05 → add endpoint-specific integration scenario for step 4 |
| A8 expected destination state — error vs safe_mode ambiguity | OPEN ISSUE I-06: UC §4 A8 records `error` but srs/states.md shows `stop_placing → safe_mode`. Recovery flow also undefined. Scenario TS_035 tests the failure gate but flags the destination state as ambiguous. | BA/zen to confirm states.md is authoritative → update TS_035 expected state; add recovery-flow scenario if safe_mode path |
| weth_index exact values per chain (Base 8453 / OP 10) | BLOCKED: OQ-EXBOT-03 (NV-12) Open — pool addresses and WETH token ordering for USDC/WETH 0.3% not confirmed. Scenarios TS_023/TS_024 verify the field is populated from config but cannot assert specific values. I-04 Deferred. | Resolve OQ-EXBOT-03 → update TS_023/TS_024 with concrete expected values |
| Performance / load test — 10,000 bots concurrently | NFR: PERFORMANCE / LOAD — FR-EXBOT-011 / NFR-EXBOT-001. Out of scope for functional QC. | Defer to load-test specialist using k6 or equivalent |
| Security depth test — KMS IAM boundary, Signing Lambda privilege escalation | NFR: SECURITY beyond functional auth check. Functional scenario TS_041/TS_042 cover observable surface; deep IAM pen-testing is out of scope. | Defer to cloud security specialist |
