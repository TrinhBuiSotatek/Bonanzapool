# Test Scenarios -- UC-EXBOT-bot-start Start ExBot

> Source: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260630_v1.md
> Generated: 2026-06-30
> Domain/Architecture: Cloudflare Workers (ExBot Worker) + AWS KMS (Signing Lambda) + Hyperliquid perp API + BnzaExVault on-chain contract + Cloudflare D1 (control_db + state_db_shard) + Queue (bot-start, key-provision) + Durable Objects (UserLockDO, HLRateLimitDO)

---

## UC-EXBOT-bot-start -- Start ExBot (system-triggered after on-chain deposit)

---

### Scenario ID: TS_UC-EXBOT-bot-start_001
**Scenario Title:** Happy path -- full bot start from key-provision to active state
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-004, FR-EXBOT-020, FR-EXBOT-025, FR-EXBOT-030, FR-EXBOT-031
**Test Type:** End-to-End
**Description:** Trigger the full bot-start flow for a user who has no existing active ExBot, sufficient HL isolated margin (>= required x 2.0), an active agent key (key_status='active'), confirmed builder fee (5bps), and LP mint simulation passing. The system must progress through all 9 lifecycle states in sequence (preflight -> lp_opening -> lp_opened -> hedge_pre_open -> hedge_post_confirmed -> stop_placing -> stop_verified -> active) without skipping any state, and after reaching 'active': bots.lifecycle_state='active', positions.custodian='vault' with tokenId populated, hedge_legs.stop_price and stop_cloid populated, and no plaintext key material in D1 hl_agent_keys.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_002
**Scenario Title:** One-bot policy -- reject second bot start when user already has active ExBot
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, UC-EXBOT-bot-start §F.3.2 A1
**Test Type:** Functional
**Description:** Trigger a bot-start queue message for a user who already has a bot with lifecycle_state='active' (status='active') in bot_registry. The system must reject the request with E-EXBOT-001 ("You already have an active ExBot. Close or wait for the existing bot to finish.") and must not create any new bot record in D1. Verify bot_registry count for the user remains 1.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_003
**Scenario Title:** One-bot policy -- reject when existing bot is paused (not just active)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001
**Test Type:** Functional
**Description:** Trigger a bot-start queue message for a user who has a bot with status='paused'. Per BR-EXBOT-001, status IN ('active','paused','closing','safe_mode','error') all count toward the 1-bot limit. The system must reject with E-EXBOT-001 and must not create a new bot record. Verify separately for each status value in the set: 'paused', 'closing', 'safe_mode', 'error'.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_004
**Scenario Title:** One-bot policy -- allow start when existing bot is closed
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001
**Test Type:** Functional
**Description:** Trigger a bot-start queue message for a user who has a prior bot with status='closed' only. The one-bot check query (status IN ('active','paused','closing','safe_mode','error')) must return count=0, allowing the start to proceed through preflight. Verify the bot record is created and the flow continues to LP mint.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_005
**Scenario Title:** Preflight -- HL margin exactly at required boundary (2.0x)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-061, UC-EXBOT-bot-start §F.3.2 A2
**Test Type:** Functional
**Description:** Trigger bot-start for a user whose HL isolated margin balance equals exactly required margin x 2.0 (boundary case: Limit). The margin check must pass (>= 2.0x), and the flow must proceed to the next preflight step. Verify no E-EXBOT-002 is returned.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_006
**Scenario Title:** Preflight -- HL margin one unit below required boundary (2.0x - epsilon)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-061
**Test Type:** Functional
**Description:** Trigger bot-start for a user whose HL isolated margin balance is marginally below the required margin x 2.0 threshold (e.g., marginBalance = $699.99, required with 2.0x buffer = $700). The system must block with E-EXBOT-002 ("Required HL margin: $700 (with 100% buffer). Current: $699.99. Please deposit $0.01 to HL."), showing the exact shortfall amount. No bot record is created.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_007
**Scenario Title:** Preflight -- HL margin significantly insufficient (US-EXBOT-001 AC-3 example)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-061
**Test Type:** Acceptance
**Description:** Trigger bot-start for a user with HL margin balance $300 where required margin (including 2.0x buffer) is $700. The system must block with E-EXBOT-002 showing current=$300, required=$700, shortfall=$400. No bot record is created in D1.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_008
**Scenario Title:** Preflight -- agent key not provisioned (no active row in hl_agent_keys)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-080, E-EXBOT-017
**Test Type:** Functional
**Description:** Trigger bot-start for a user who has no row with key_status='active' in hl_agent_keys (key provisioning has not completed). The key_status check (preflight step 3) must block with E-EXBOT-017 ("Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup."). No bot record is created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_009
**Scenario Title:** Preflight -- agent key exists but status is revoked (not active)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-080, BR-EXBOT-012
**Test Type:** Functional
**Description:** Trigger bot-start for a user who has a row in hl_agent_keys but key_status='revoked' (not 'active'). The key_status check must treat this equivalently to no active key -- block with E-EXBOT-017. Verify separately for key_status='superseded'. No bot record is created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_010
**Scenario Title:** Preflight -- builder fee (5bps) not confirmed on HL
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, UC-EXBOT-bot-start §F.3.2 A5
**Test Type:** Functional
**Description:** Trigger bot-start for a user where the builder fee (5bps) check (preflight step 4) determines the fee has not been confirmed on HL. The system must block with E-EXBOT-005 ("HL builder fee (5bps) approval required before starting ExBot."). No bot record is created.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_011
**Scenario Title:** Preflight -- LP mint simulation fails (low pool liquidity)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, UC-EXBOT-bot-start §F.3.2 A6
**Test Type:** Functional
**Description:** Trigger bot-start where the LP mint simulation (preflight step 5) fails due to slippage outside tolerance or insufficient pool liquidity. The system must block with E-EXBOT-006 ("LP mint simulation failed. Check pool liquidity or adjust deposit amount."). No bot record is created in D1.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_012
**Scenario Title:** Preflight sequence ordering -- verify checks run in strict order (step 1 fails, steps 2-5 not executed)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, FR-EXBOT-002
**Test Type:** Functional
**Description:** Trigger bot-start for a user who both (a) already has an active ExBot and (b) has insufficient HL margin. Verify that the system returns E-EXBOT-001 (one-bot check -- step 1 fails), and does NOT call the HL margin check API. This confirms preflight runs in sequence and short-circuits on first failure without consuming additional HL API weight.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_013
**Scenario Title:** Preflight decision table -- margin fail + key not active (step 2 fails before step 3)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-061
**Test Type:** Functional
**Description:** Trigger bot-start for a user with insufficient HL margin AND key_status not 'active'. Because preflight runs in sequence, the system must block at step 2 with E-EXBOT-002 (margin check) and not reach step 3 (key_status check). This validates the combinatoric: fail-at-earlier-step hides later failures.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_014
**Scenario Title:** Bot record creation -- D1 INSERT is atomic and lifecycle_state='preflight' is written before any on-chain call
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, UC-EXBOT-bot-start §F.2 OP-13
**Test Type:** Data/State
**Description:** After all 5 preflight checks pass, trigger the bot record creation (OP-13). Query D1 before the vaultMint transaction is sent on-chain and verify bots.lifecycle_state='preflight' is already set. Confirm there is no window where the on-chain call is made while D1 has no corresponding bot record.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_015
**Scenario Title:** State transition -- lifecycle_state advances idle -> preflight -> lp_opening -> lp_opened (LP phase)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-003, FR-EXBOT-004
**Test Type:** Data/State
**Description:** Observe the D1 bots.lifecycle_state value after each step: (1) after preflight pass and before vaultMint: 'preflight'; (2) after vaultMint call initiated and before VaultMinted event: 'lp_opening'; (3) after VaultMinted event received and positions updated: 'lp_opened'. Verify each state is written before the next step begins and no state is skipped.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_016
**Scenario Title:** State transition -- lifecycle_state advances hedge_pre_open -> hedge_post_confirmed -> stop_placing -> stop_verified -> active (hedge phase)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-020, FR-EXBOT-025, FR-EXBOT-030, FR-EXBOT-031
**Test Type:** Data/State
**Description:** Observe D1 bots.lifecycle_state after each hedge step: (1) after openShortIoc sent and before reconcile: 'hedge_pre_open'; (2) after reconcile confirmed: 'hedge_post_confirmed'; (3) after stop order sent and before HL confirms: 'stop_placing'; (4) after stop confirmed: 'stop_verified'; (5) final D1 write: 'active'. Verify the transitions occur in this exact sequence with no out-of-order or skipped states.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_017
**Scenario Title:** Invalid state transition attempt -- bot-start message received while bot already in 'active' state (duplicate trigger)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, FR-EXBOT-011
**Test Type:** Data/State
**Description:** Deliver a bot-start queue message for a user whose bot has already reached lifecycle_state='active'. The queue_idempotency UNIQUE constraint on message_id must cause the worker to skip processing (UNIQUE conflict -- return immediately). Verify bots.lifecycle_state remains 'active' unchanged and no duplicate bot record is created. This is a different scenario from TS_001 -- it specifically tests the idempotency guard, not one-bot policy.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_018
**Scenario Title:** LP mint -- VaultMinted event fields are correctly stored in D1 positions
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-004, UC-EXBOT-bot-start §F.2 OP-16
**Test Type:** Data/State
**Description:** After a successful vaultMint call and VaultMinted(user, botId, tokenId, liquidity) event receipt, verify D1 positions row has: tokenId matching on-chain event, tickLower and tickUpper matching the position range, custodian='vault', and wethIndex matching the correct value for the chain (0 or 1 -- not hardcoded, per-chain per FR-EXBOT-004). Verify that a mismatch between event tokenId and D1 positions.token_id would be detectable.
**Test Focus:** On-chain<->off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_019
**Scenario Title:** LP mint fail -- A4: bot enters error state when vaultMint on-chain call fails
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-004, UC-EXBOT-bot-start §F.3.2 A4
**Test Type:** Functional
**Description:** Simulate a vaultMint on-chain failure (e.g., Solidity revert, gas estimation failure, or on-chain exception). The system must set bots.lifecycle_state='error'. Verify that D1 positions does NOT contain a tokenId from a partially executed mint, and that the bot does not proceed to the hedge open step. (Note: the mechanism for 'return funds' in this scenario is tracked in open issue I-05 and is out of scope for this scenario's expected-result assertion.)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_020
**Scenario Title:** HL short open -- Signing Lambda signs payload and submits IOC order to HL
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-020, FR-EXBOT-080, SRS F-03
**Test Type:** Integration
**Description:** After lifecycle_state='lp_opened', the system sends a short IOC order via Signing Lambda. Verify: (1) the KMS Sign operation is invoked using the user's agent key (not master key); (2) the signed payload is sent to HL; (3) the cloid is deterministic per the formula keccak256("bnza:{botId}:{attemptId}:{stage}:{version}") first-128-bits-hex; (4) the order type is IOC short ETH-USD; (5) lifecycle_state transitions to 'hedge_pre_open' before confirmation.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_021
**Scenario Title:** Hedge open -- targetShortEth calculation uses BigDecimal (not JS float)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-020, FR-EXBOT-021, NFR-EXBOT-008
**Test Type:** Functional
**Description:** After LP mint, the system computes targetShortEth = lpEthAmount x hedgeRatio (0.70). Verify that the computation uses BigDecimal arithmetic throughout -- no intermediate Number() / parseFloat() conversion. A test with lpEthAmount = 1.0000000000000001 ETH and hedgeRatio = 0.70 must produce an exact 15+ digit precision result (0.7000000000000001, not 0.7 via float truncation). Verify hedge_legs stores BigDecimal-format strings, not JS number literals.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_022
**Scenario Title:** Reconcile -- actual HL position size matches expected after IOC fill
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-025, UC-EXBOT-bot-start §F.2 OP-20
**Test Type:** Integration
**Description:** After openShortIoc completes, the system fetches clearinghouseState from HL and compares actual position size to expected targetShortEth. When actual matches expected (within tolerance), verify D1 hedge_legs is updated with entry_price, liquidation_price, effective_leverage (all as BigDecimal strings), and lifecycle_state advances to 'hedge_post_confirmed'. Verify the reconcile API call uses weight=2 per SRS F-03.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_023
**Scenario Title:** Reconcile mismatch -- A11: actual position deviates beyond threshold, enqueue partial_repair
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-025, UC-EXBOT-bot-start §F.3.2 A11
**Test Type:** Functional
**Description:** Simulate a reconcile result where actual HL position size deviates beyond the (currently unspecified) threshold from targetShortEth. The system must enqueue a 'partial_repair' job and alert the operator. Verify lifecycle_state does NOT advance to 'hedge_post_confirmed' while mismatch persists, and that E-EXBOT-011 ("Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation.") is raised internally. (Blocked: threshold value is unspecified -- I-02; this scenario tests the branching behavior, not exact boundary values.)
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_024
**Scenario Title:** Stop price calculation -- stop_trigger_px uses BigDecimal with stopSafetyFactor=0.70
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-030, NFR-EXBOT-008
**Test Type:** Functional
**Description:** After hedge_post_confirmed, the system computes stop_trigger_px = entry_price x (1 + liq_distance_pct x 0.70). With entry_price=2000, liq_price=1600 (liq_distance_pct = (1600-2000)/2000 = -0.20), stopSafetyFactor=0.70: stop_trigger_px = 2000 x (1 + (-0.20) x 0.70) = 2000 x 0.86 = 1720. Verify: (1) stop_trigger_px stored in hedge_legs as BigDecimal string "1720"; (2) stop_trigger_px < entry_price; (3) stop_trigger_px > liq_price (safety margin preserved); (4) no intermediate float conversion used.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_025
**Scenario Title:** Stop price fallback -- use 1/effective_leverage when liquidationPx is absent from HL response
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-030
**Test Type:** Functional
**Description:** Simulate a reconcile response from HL where liquidationPx is null or absent. The system must fall back to computing liq_distance_pct = 1/effective_leverage (per FR-EXBOT-030 fallback rule). Verify stop_trigger_px is still computed correctly using the fallback, stored as BigDecimal, and that lifecycle_state transitions from 'hedge_post_confirmed' to 'stop_placing' without error.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_026
**Scenario Title:** Stop placement -- reduce-only stop market order is placed via Signing Lambda
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-031, SRS F-03
**Test Type:** Integration
**Description:** After stop_trigger_px is computed, the system sends placeReduceOnlyStopMarket(stopTriggerPx, size, cloid) via Signing Lambda. Verify: (1) the stop order is reduce-only (not a new position); (2) the cloid is deterministic per FR-EXBOT-024 formula; (3) the signed payload uses the agent key via KMS; (4) after HL confirms the stop, D1 hedge_legs.stop_cloid and stop_price are populated; (5) lifecycle_state transitions from 'stop_placing' to 'stop_verified'.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_027
**Scenario Title:** Stop placement fail -- A8: error state when HL rejects stop order, short position remains open
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-031, UC-EXBOT-bot-start §F.3.2 A8
**Test Type:** Functional
**Description:** Simulate HL rejecting the stop market order after the short position is already open. The system must set lifecycle_state='error' and emit E-EXBOT-009 ("Failed to place native stop on Hyperliquid. Bot cannot activate without a stop."). Verify: (1) the HL short position remains open (not automatically closed by this flow); (2) an operator alert is raised; (3) lifecycle_state is 'error', not 'active'. (Note: the recovery flow for this state -- manual stop placement, bot_safe_close trigger, or auto-retry -- is tracked in I-06 and is out of scope for this scenario's expected-result assertion.)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_028
**Scenario Title:** HL unreachable at hedge open -- A7: error state when HL API down during openShortIoc
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-020, UC-EXBOT-bot-start §F.3.2 A7
**Test Type:** Functional
**Description:** Simulate HL API being unreachable (timeout or connection error) at the moment ExBot Worker sends the openShortIoc request (step 7). The system must set lifecycle_state='error' and return E-EXBOT-008 ("Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."). Verify no partial LP or hedge state is left in an inconsistent condition -- LP NFT remains in vault but no hedge_legs row is created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_029
**Scenario Title:** HL rejects IOC order -- A10: error state when HL rejects short IOC for business reason
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-020, UC-EXBOT-bot-start §F.3.2 A10
**Test Type:** Functional
**Description:** Simulate HL accepting the API call but rejecting the IOC order for a business reason (e.g., order size below HL minimum, insufficient perp margin on HL side, or account restriction). The system must set lifecycle_state='error' and capture the HL rejection reason in the bot record or log. Verify this scenario is distinct from A7 (API unreachable): the HL API call succeeds but the order is rejected.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_030
**Scenario Title:** Key provision -- queue_idempotency prevents duplicate key provisioning for same deposit
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, FR-EXBOT-011
**Test Type:** Data/State
**Description:** Deliver the same key-provision queue message twice (same message_id, simulating queue redelivery). The second delivery must hit the UNIQUE constraint on queue_idempotency.message_id and skip re-execution. Verify D1 hl_agent_keys has exactly one row for the user (no duplicate active rows), confirming BR-EXBOT-012 (only one active row per user at any time) is upheld.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_031
**Scenario Title:** Key provision -- only one hl_agent_keys row with key_status='active' per user (BR-EXBOT-012)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, BR-EXBOT-012
**Test Type:** Data/State
**Description:** After key provisioning completes, query D1 control_db hl_agent_keys for the user. Verify exactly one row has key_status='active'. Verify there is no concurrent window where zero rows or two rows have key_status='active'. This enforces BR-EXBOT-012 at the database level (UNIQUE constraint on the active state).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_032
**Scenario Title:** Key security -- D1 hl_agent_keys contains no plaintext private key material
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-080, NFR-EXBOT-006
**Test Type:** Functional
**Description:** After key provisioning and bot start, query all columns of D1 hl_agent_keys for the user. Verify: (1) no column contains a private key in hex, PEM, or base64 format; (2) hl_user_address and agent_address contain only public addresses; (3) KMS key ARN (if stored) does not leak key material. This corresponds to AC-11.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_033
**Scenario Title:** Key security -- ExBot Worker is not directly accessible from public internet
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** BR-EXBOT-010, NFR-EXBOT-006
**Test Type:** Functional
**Description:** Attempt to send a direct HTTP request to the ExBot Worker endpoint (bypassing the OPERATOR service binding). The request must be rejected with 403 or equivalent. Verify that ExBot Worker only accepts requests via Cloudflare service binding from OPERATOR (not via public HTTP).
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-bot-start_034
**Scenario Title:** Idempotency -- duplicate bot-start message is skipped, no second bot record created
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-011, NFR-EXBOT-007
**Test Type:** Functional
**Description:** Deliver the same bot-start queue message twice (same message_id). The second delivery must trigger a UNIQUE conflict on queue_idempotency.message_id and return immediately without creating a second bot record or re-executing any preflight checks. Verify bot_registry count remains 1 for the user. This corresponds to AC-14.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_035
**Scenario Title:** Idempotency -- same cloid resubmitted to HL does not create duplicate order
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-024, FR-EXBOT-020
**Test Type:** Integration
**Description:** If ExBot Worker retries the openShortIoc request (e.g., due to a transient error after the first attempt succeeded on HL's side), the same deterministic cloid is computed and resubmitted. Verify that HL treats the duplicate cloid as idempotent (does not open a second short position). Verify D1 hedge_legs shows one hedge entry, not two.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_036
**Scenario Title:** Idempotency -- same stop cloid resubmitted does not create duplicate stop order
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-024, FR-EXBOT-031
**Test Type:** Integration
**Description:** If ExBot Worker retries the placeReduceOnlyStopMarket request using the same deterministic cloid, verify HL deduplicates the request (no second stop order placed). Verify D1 hedge_legs.stop_cloid is set only once and reflects the single stop order.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_037
**Scenario Title:** Concurrent bot-start -- two deposits for same user arrive simultaneously (race condition)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-011, FR-EXBOT-001
**Test Type:** Data/State
**Description:** Simulate two bot-start queue messages for the same user arriving and being processed near-simultaneously (e.g., two deposits or a race between key-provision worker and a duplicate message). The queue_idempotency UNIQUE constraint or the one-bot policy check must ensure only one bot proceeds. Verify: (1) exactly one bot record is created in D1; (2) the second message is either rejected by idempotency or by one-bot policy; (3) no data corruption or duplicate active rows result.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_038
**Scenario Title:** HL rate limit -- verify preflight margin check (weight=2) is counted against 800 wt/min budget
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-091, NFR-EXBOT-004
**Test Type:** Integration
**Description:** Monitor HLRateLimitDO weight consumption during a bot-start flow. Verify that the HL margin check call (preflight step 2) consumes weight=2 from the 800 wt/min budget. Verify the reconcile call also consumes weight correctly. If the HL rate limit is already at 800 wt/min when bot-start is triggered, verify the worker either waits (retryAfterMs from HLRateLimitDO) or handles the rate limit gracefully without crashing.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_039
**Scenario Title:** UserLockDO -- lock is acquired before any HL operation and released after completion
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** SRS §7.2 UserLockDO (project-context-master)
**Test Type:** Integration
**Description:** Verify that ExBot Worker acquires the UserLockDO lock (TTL 90s) before initiating any HL API call in the bot-start flow. Verify the lock is released after the flow completes (success or error). Verify that a second concurrent worker attempting to acquire the same user's lock is blocked while the first holds it.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_040
**Scenario Title:** On-chain trigger -- Chain Indexer deposit event correctly enqueues key-provision job
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** SRS F-03, FR-EXBOT-080
**Test Type:** Integration
**Description:** Simulate an on-chain USDC deposit to BnzaExVault by a user. Verify that Chain Indexer (Fargate) detects the deposit event, creates a key-provision queue message with the correct userId, depositAmount, and txHash, and enqueues it into the key-provision queue. Verify the message schema matches the expected format per SRS F-03.
**Test Focus:** On-chain<->off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_041
**Scenario Title:** On-chain / off-chain consistency -- VaultMinted event tokenId matches D1 positions.token_id
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-004, EV-01 VaultMinted
**Test Type:** Data/State
**Description:** After a successful vaultMint call emitting VaultMinted(user, botId, tokenId, liquidity) on-chain, verify that D1 positions.token_id exactly matches the tokenId from the on-chain event. Verify positions.custodian='vault'. Verify that if the tokenId from the event differs from a previously cached or estimated value, D1 is updated with the authoritative on-chain value, not the estimate.
**Test Focus:** On-chain<->off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_042
**Scenario Title:** Key-provision agent key immutability -- existing active row cannot be overwritten (BR-EXBOT-013)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** BR-EXBOT-013, FR-EXBOT-080
**Test Type:** Data/State
**Description:** After key provisioning creates an hl_agent_keys row with key_status='active', attempt to update or overwrite that row directly (simulating a bug or replay attack). Verify that BR-EXBOT-013 (agent key rows are immutable after write) is enforced -- the row must not be modified. Verify that revocation or superseding is non-destructive (creates new row or updates status, does not delete the original row).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_043
**Scenario Title:** Downstream integration -- bot reaching 'active' triggers light-check and deep-audit scheduling
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-012, FR-EXBOT-016, UC-EXBOT-bot-start §F.4
**Test Type:** Integration
**Description:** After lifecycle_state='active' is written to D1, verify: (1) bots.next_light_check_at is set to a future timestamp (enabling the light-check cron to start scanning this bot); (2) bots.next_deep_audit_at is set approximately 6 hours from activation time; (3) status API GET /api/exbot/status returns {status: 'active', botId, ...} correctly for this user.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_044
**Scenario Title:** Acceptance -- happy path end-to-end (US-EXBOT-001 AC-1 verification)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-004, FR-EXBOT-020, FR-EXBOT-030, FR-EXBOT-031, US-EXBOT-001 AC-1
**Test Type:** Acceptance
**Description:** Run the full bot-start flow for a user who: has no existing active ExBot, HL margin >= required x 2.0, key_status='active' (provisioned after on-chain deposit), builder fee confirmed, LP mint simulation passes. Verify all AC-1 criteria: lifecycle_state progresses through all 9 states in sequence and reaches 'active'; POOL UI (via status API) reports bot status as 'Active' with LP range and hedge size visible; hedge_legs.stop_price is populated; positions.custodian='vault'.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_045
**Scenario Title:** Acceptance -- one-bot policy (US-EXBOT-001 AC-2 verification)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-001, US-EXBOT-001 AC-2
**Test Type:** Acceptance
**Description:** With a user who already has one active ExBot, simulate a new deposit that triggers the bot-start flow. Verify the system rejects with E-EXBOT-001 ("You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one."), and no new bot record is created.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_046
**Scenario Title:** Acceptance -- insufficient HL margin (US-EXBOT-001 AC-3 verification)
**UC Reference:** UC-EXBOT-bot-start
**Req-ID:** FR-EXBOT-002, FR-EXBOT-061, US-EXBOT-001 AC-3
**Test Type:** Acceptance
**Description:** For a user with HL margin $300 and required margin (with 2.0x buffer) of $700, the bot-start flow must block at preflight step 2 with E-EXBOT-002: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit an additional $400 to HL." No bot record is created.
**Test Focus:** Error/Exception

---


---

## Blocked Scenarios (partial -- cannot design without BA/Tech Lead input)

The following test intents are identified from the UC but BLOCKED pending resolution of open issues. They are listed here so they are not lost.

| Intent ID | Blocked By | Test Intent | Resolve Via |
|---|---|---|---|
| BLOCKED-01 | I-02 (reconcile threshold undefined) | Boundary test for reconcile mismatch -- exactly at threshold, just below, just above | Resolve I-02 via qc-qna then re-audit |
| BLOCKED-02 | I-05 (A4 return funds mechanism unknown) | Postcondition verification after LP mint fail -- is USDC returned on-chain automatically or does ExBot Worker take action? | Resolve I-05 via qc-qna |
| BLOCKED-03 | I-06 (A8 recovery flow unknown) | Verify operator alert message content and recovery flow when stop placement fails (bot in error with open short) | Resolve I-06 via qc-qna |
| BLOCKED-04 | I-04 / OQ-EXBOT-03 (wethIndex per chain unconfirmed) | Verify wethIndex=0 for Base (USDC/WETH 0.3%) and wethIndex=1 for OP (or vice versa) -- exact chain-specific values needed | Resolve OQ-EXBOT-03 via qc-qna |
| BLOCKED-05 | I-07 / OQ-EXBOT-05 (builder fee check mechanism unknown) | Independent test for preflight builder fee check -- which HL API endpoint, which weight consumed | Resolve OQ-EXBOT-05 |

---

## Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Performance / latency of bot-start flow | NFR: PERFORMANCE -- bot-check latency <100ms is stated in NFR-EXBOT-001 but load/latency testing is out of scope for functional QC | Defer to performance/load testing specialist |
| Security penetration testing (KMS IAM role boundary testing) | NFR: SECURITY -- functional auth tested in TS_033; full IAM boundary / pen test is security specialist domain | Defer to security testing specialist |
| BnzaExVault Solidity contract internal logic | OOS: zen develops and deploys; SOTATEK integrates against ABI -- integration test via ABI (TS_018, TS_019) is covered; internal contract logic is OOS | Wait for ABI finalization (OQ-EXBOT-08) before enabling integration scenarios |
| wethIndex per-chain dual-chain LP test | BLOCKED: OQ-EXBOT-03 (pool address + wethIndex for Base and Optimism unconfirmed) -- see BLOCKED-04 above | Resolve via qc-qna |
| HL API weight budget exhaustion behavior during bot-start (full load) | Integration scenario TS_038 covers single-bot weight; full load / budget exhaustion across multiple concurrent bots is load/perf scope | Defer to load testing |

