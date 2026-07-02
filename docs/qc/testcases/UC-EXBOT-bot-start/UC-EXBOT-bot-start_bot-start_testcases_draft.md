# Test Cases — UC-EXBOT-bot-start Start ExBot

**Total test cases:** 46 (FUNC: 33, INTG: 8, NFR: 5)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** UC-EXBOT-bot-start_bot-start_audited_20260630_v1.md
**Source scenarios (if any):** UC-EXBOT-bot-start_bot-start_scenarios_20260702_v2.md
**Output language:** English
**Version:** v4 | **Delta (v3 → v4):** +0 new, ~2 updated (TC_028, TC_029), -0 deleted | **Update trigger:** REQUIREMENT_DELTA (scenarios v2 — I-11 flagged on TS_028/TS_029)

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Happy path — all 9 lifecycle states in sequence, hedge + stop populated | TC_001, TC_002, TC_022, TC_023, TC_030, TC_037, TC_039, TC_040 | Covered |
| AC-02 | One-bot policy blocks start, no new record | TC_008, TC_009 | Covered |
| AC-03 | Margin insufficient — exact shortfall in message | TC_012, TC_013 | Covered |
| AC-04 | Agent key not active blocks start with E-EXBOT-017 | TC_015 | Covered |
| AC-05 | Builder fee not confirmed blocks start with E-EXBOT-005 | TC_016 | Covered |
| AC-06 | LP mint simulation fail blocks start with E-EXBOT-006 | TC_018 | Covered |
| AC-07 | HL unreachable during hedge open — lifecycle=error | TC_028 | Covered (I-11 OPEN: destination state ambiguous — `error` per UC §4 A7 vs `safe_mode` per states.md; pending BA confirmation) |
| AC-08 | Stop placement fails — safe_mode + auto-recovery per FR-EXBOT-050 (I-06 resolved) | TC_038 | Covered |
| AC-09 | HL IOC order rejected — lifecycle=error, HL reason captured | TC_029 | Covered (I-11 OPEN: destination state ambiguous — `error` per UC §4 A10 vs `safe_mode` per states.md; pending BA confirmation) |
| AC-10 | Reconcile mismatch — partial_repair enqueued + operator alert | TC_031 | Covered |
| AC-11 | Private key never in hl_agent_keys or logs after provisioning | TC_007, TC_045 | Covered |
| AC-12 | weth_index per chain stored from config (pending OQ-EXBOT-03) | TC_025 | Covered (blocked on OQ-EXBOT-03) |
| AC-13 | stop_price < liquidation_price with ≥30% buffer, BigDecimal | TC_035, TC_040 | Covered |
| AC-14 | Idempotency — redelivered bot-start message creates exactly one bot | TC_043 | Covered |

---

## I. Operation: Key Provision (chain indexer → KMS → HL approveAgent)

### I.1. Functional verification — Operation: Key Provision

#### TC_001

- **Title:** Verify key-provision creates master key and agent key in KMS with only public addresses stored
- **Pre-condition:**
  1. A new on-chain deposit event has been detected by Chain Indexer for a user with no existing `hl_agent_keys` row.
  2. AWS KMS is available and responsive.
- **Step:**
  1. Process the `key-provision` queue message for the user; verify both KMS `GenerateKeyPair` calls complete successfully.
- **Expected Result:**
  1. KMS returns two public addresses (`hl_user_address` for master key, `agent_address` for agent key). A row is inserted into `hl_agent_keys` containing only public addresses and metadata — no private key material is present in any DB field, response payload, or application log. (Reference: FR-EXBOT-080, NFR-EXBOT-006.)
- **Priority:** P0

#### TC_002

- **Title:** Verify key_status is set to active only after HL approveAgent confirms the agent registration
- **Pre-condition:**
  1. KMS has generated both key pairs successfully.
  2. HL `approveAgent` call is in progress (pending HL confirmation).
- **Step:**
  1. Check `hl_agent_keys.key_status` before HL confirmation arrives; then let HL confirm `approveAgent` and check again.
- **Expected Result:**
  1. Before HL confirmation: `key_status` is not `active` (remains `provisioning` or absent). After HL confirms: `key_status='active'` is written atomically to D1 and a `bot-start` job is enqueued. (Reference: FR-EXBOT-080, SRS F-03.)
- **Priority:** P0

#### TC_003

- **Title:** Verify KMS failure during key generation retries up to the limit and sends an admin alert after final failure
- **Pre-condition:**
  1. KMS is mocked to return `ThrottlingException` (or equivalent error) on every `GenerateKeyPair` call.
- **Step:**
  1. Trigger key-provision processing; count the number of KMS retry attempts before the worker gives up.
- **Expected Result:**
  1. The worker retries up to the configured maximum (not fewer, not more). After the final failure: no `hl_agent_keys` row with `key_status='active'` is created; an admin alert is triggered; no `bot-start` job is enqueued. (Example: max retries = 3.) (Reference: FR-EXBOT-080, IC-EXBOT-005.)
- **Priority:** P0

#### TC_004

- **Title:** Verify HL approveAgent failure keeps key_status as not active and triggers retry
- **Pre-condition:**
  1. KMS has generated both key pairs; `hl_user_address` and `agent_address` are available.
  2. HL `approveAgent` is mocked to return an error.
- **Step:**
  1. Let Key-Provision Worker call HL `approveAgent` while it is set to fail; then check the DB row and the queue.
- **Expected Result:**
  1. `hl_agent_keys.key_status` stays at `provisioning` (not changed to `active`); the worker re-enqueues a retry via the `key-provision` queue; no `bot-start` job is enqueued until `key_status='active'` is confirmed. An admin alert is sent when the SLA wait time is exceeded. (Reference: FR-EXBOT-080.)
- **Priority:** P0


#### TC_005

- **Title:** Verify duplicate key-provision queue message does not provision a second key pair
- **Pre-condition:**
  1. A `key-provision` message has already been processed once and `key_status='active'` is set.
  2. The same message is redelivered (Cloudflare Queue at-least-once semantics).
- **Step:**
  1. Deliver the same `key-provision` message a second time with the same `message_id`.
- **Expected Result:**
  1. The second delivery encounters a UNIQUE constraint conflict on `queue_idempotency.message_id` and exits immediately without calling KMS again; only one `hl_agent_keys` row with `key_status='active'` exists; no duplicate `bot-start` job is enqueued. (Reference: FR-EXBOT-011, BR-EXBOT-012.)
- **Priority:** P0

### I.2. Integration & State verification — Operation: Key Provision

#### TC_006

- **Title:** Verify only one active agent key row exists per user at any time
- **Pre-condition:**
  1. A user already has one `hl_agent_keys` row with `key_status='active'`.
- **Step:**
  1. Attempt to insert a second `hl_agent_keys` row with `key_status='active'` for the same user (simulating a race condition or misconfigured re-provisioning).
- **Expected Result:**
  1. The DB-level constraint rejects the second insert (BR-EXBOT-012: only one `active` row per user at any time); the existing active row remains intact; no new row with `active` status is committed. (Reference: BR-EXBOT-012, FR-EXBOT-080.)
- **Priority:** P0

### I.3. Non-functional (logic) verification — Operation: Key Provision

#### TC_007

- **Title:** Verify private key material never appears in DB, logs, or response payloads after key provisioning
- **Pre-condition:**
  1. Key-provision flow has completed successfully; `hl_agent_keys.key_status='active'`.
- **Step:**
  1. Dump the `hl_agent_keys` table from D1; search application logs for the time window of the provisioning run; inspect any API response bodies from Key-Provision Worker.
- **Expected Result:**
  1. No hex-encoded or base64-encoded 256-bit/512-bit private key pattern appears in any D1 field, log line, or response payload. Only `hl_user_address`, `agent_address`, and metadata (status, timestamps) are stored in plaintext. Private keys remain exclusively in AWS KMS HSM. (Reference: FR-EXBOT-080, NFR-EXBOT-006.)
- **Priority:** P0

---

## II. Operation: Bot Start Preflight

### II.1. Functional verification — Operation: Bot Start Preflight

#### TC_008

- **Title:** Verify the one-bot policy rejects a second start when the user already has a running bot
- **Pre-condition:**
  1. The user already has an ExBot with `status='active'` in `bot_registry`.
- **Step:**
  1. Process a `bot-start` job for the same user while the existing bot is still active.
- **Expected Result:**
  1. The start is rejected with `E-EXBOT-001` ("You already have an active ExBot. Close or wait for the existing bot to finish.", HTTP 409). No new row is added to `bot_registry` or `bots`. `bot_registry` count for the user remains 1. (Reference: FR-EXBOT-001, BR-EXBOT-001.)
- **Priority:** P0

#### TC_009

- **Title:** Verify the one-bot policy counts paused, closing, safe_mode, and error statuses toward the limit
- **Pre-condition:**
  1. The user has one existing bot — this test is run four times with the bot set to each disqualifying status in turn: `paused`, `closing`, `safe_mode`, `error`.
- **Step:**
  1. Process a `bot-start` job for the user each time the existing bot is in one of the four statuses above.
- **Expected Result:**
  1. In each of the four cases the start is rejected with `E-EXBOT-001` (HTTP 409) and no new bot record is created. All four statuses count toward the one-bot limit per BR-EXBOT-001. (Reference: FR-EXBOT-001, BR-EXBOT-001.)
- **Priority:** P0

#### TC_010

- **Title:** Verify a new start is allowed when the user's only existing bot has a closed status
- **Pre-condition:**
  1. The user has one existing bot with `status='closed'`.
- **Step:**
  1. Process a `bot-start` job for the user.
- **Expected Result:**
  1. Preflight step 1 passes (the count of disqualifying statuses = 0); the flow proceeds to preflight step 2 (margin check). A `closed` bot does not block a new start per BR-EXBOT-001. (Reference: FR-EXBOT-001, BR-EXBOT-001.)
- **Priority:** P0

#### TC_011

- **Title:** Verify the margin check passes at exactly the minimum required margin including the 2.0x buffer
- **Pre-condition:**
  1. The one-bot policy check passes.
  2. The user's HL isolated margin balance equals exactly the required margin multiplied by 2.0 (right at the threshold, no extra). (Example: required base ≈ 350; balance ≈ 700, which is exactly 2.0×.)
- **Step:**
  1. Process the `bot-start` preflight with the user's HL margin set to exactly the 2.0× threshold.
- **Expected Result:**
  1. Preflight step 2 passes and the flow proceeds to step 3. The formula uses `hlOraclePrice` (not HL mark price or Uniswap pool price) per FR-EXBOT-061. (Reference: FR-EXBOT-002, FR-EXBOT-061.)
- **Priority:** P0

#### TC_012

- **Title:** Verify the margin check fails when the user's balance is just below the 2.0x threshold
- **Pre-condition:**
  1. The one-bot policy check passes.
  2. The user's HL margin is just below the required margin multiplied by 2.0. (Example: required 2.0× ≈ 700; balance ≈ 699.)
- **Step:**
  1. Process the `bot-start` preflight with the user's margin set just below the minimum threshold.
- **Expected Result:**
  1. Preflight step 2 fails with `E-EXBOT-002` (HTTP 400). The message includes the required amount, current amount, and exact shortfall. No bot record is created in D1. (Reference: FR-EXBOT-002, FR-EXBOT-061.)
- **Priority:** P0

#### TC_013

- **Title:** Verify the margin error message shows the exact shortfall without rounding down
- **Pre-condition:**
  1. The one-bot policy check passes.
  2. The user's HL margin is below the required 2.0× threshold by an amount that is not a round number. (Example: balance ≈ 300, required ≈ 700 → shortfall ≈ 400.)
- **Step:**
  1. Process the `bot-start` preflight with the gap between current and required margin being a non-round amount.
- **Expected Result:**
  1. The start is blocked (`E-EXBOT-002`, HTTP 400). The message shows the exact amount the user still needs to deposit — the shortfall is not rounded down to a coarser unit, so depositing exactly that amount would be sufficient. (Example: if shortfall = 400.75, the message shows 400.75, not 400.) (Reference: FR-EXBOT-061 AC.)
- **Priority:** P0

#### TC_014

- **Title:** Verify the preflight is blocked when HL is unreachable during the margin check step
- **Pre-condition:**
  1. The one-bot policy check passes.
  2. HL API (mocked) is set to time out or return an error when `marginSummary` is requested.
- **Step:**
  1. Process the `bot-start` preflight while HL is unreachable during step 2 (margin check).
- **Expected Result:**
  1. The start fails immediately with `E-EXBOT-008`; no bot record is created; the preflight does not proceed to step 3. (Per I-03 confirmed answer: HL timeout at preflight = immediate fail, no retry loop.) (Reference: UC §3 step 3, E-EXBOT-008.)
- **Priority:** P0

#### TC_015

- **Title:** Verify the start is blocked when the agent key is not yet provisioned
- **Pre-condition:**
  1. One-bot policy and margin checks pass.
  2. The user has no `hl_agent_keys` row with `key_status='active'` (key-provision has not yet completed).
- **Step:**
  1. Process the `bot-start` preflight while the agent key is absent or not active.
- **Expected Result:**
  1. Preflight step 3 fails with `E-EXBOT-017` ("Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup.", HTTP 400). No bot record is created. (Reference: FR-EXBOT-002 step 3, E-EXBOT-017.)
- **Priority:** P0

#### TC_016

- **Title:** Verify the start is blocked when builder fee (5bps) has not been confirmed on HL
- **Pre-condition:**
  1. One-bot policy, margin, and key status checks pass.
  2. Builder fee (5bps) has not been confirmed on HL for this user.
- **Step:**
  1. Process the `bot-start` preflight at step 4 while builder fee is not confirmed.
- **Expected Result:**
  1. Preflight step 4 fails with `E-EXBOT-005` ("HL builder fee (5bps) approval required before starting ExBot.", HTTP 400). No bot record is created. (Note: the exact HL endpoint for the fee check is pending OQ-EXBOT-05 — this TC verifies the gate behavior.) (Reference: FR-EXBOT-002 step 4, E-EXBOT-005.)
- **Priority:** P0

#### TC_017

- **Title:** Verify a previously confirmed builder fee from a prior session still passes the check at start
- **Pre-condition:**
  1. One-bot policy, margin, and key status checks pass.
  2. Builder fee was confirmed in a previous session (not the current start attempt).
- **Step:**
  1. Process the `bot-start` preflight at step 4 using a pre-confirmed builder fee.
- **Expected Result:**
  1. Preflight step 4 passes — the system accepts the previously confirmed builder fee without requiring a new on-chain or API confirmation per start attempt. The flow proceeds to step 5 (LP mint simulation). (Per I-10 confirmed answer: builder fee check is a one-time check at start.) (Reference: FR-EXBOT-002 step 4.)
- **Priority:** P1

#### TC_018

- **Title:** Verify LP mint simulation failure blocks the start without making any on-chain call
- **Pre-condition:**
  1. All preflight steps 1–4 pass.
  2. LP mint simulation (mocked) is set to fail (e.g., pool liquidity too low or slippage exceeds tolerance).
- **Step:**
  1. Process the `bot-start` preflight at step 5 while LP mint simulation is set to fail.
- **Expected Result:**
  1. Preflight step 5 fails with `E-EXBOT-006` ("LP mint simulation failed. Check pool liquidity or adjust deposit amount.", HTTP 400). No bot record is created; no on-chain `vaultMint` call is made (no gas consumed). (Reference: FR-EXBOT-002 step 5, E-EXBOT-006.)
- **Priority:** P0

#### TC_019

- **Title:** Verify no partial bot record is left after any one of the five preflight steps fails
- **Pre-condition:**
  1. This test is run five times — once for each preflight step — with each step configured to fail while all prior steps pass.
- **Step:**
  1. Fail preflight at step 1; query D1 for new bot records. Repeat for steps 2, 3, 4, and 5.
- **Expected Result:**
  1. After each preflight failure, `bot_registry` and `bots` contain zero new rows for the user. The bot record is only created AFTER all 5 preflight checks pass (FR-EXBOT-002 AC). No partial record under any failure scenario. (Reference: FR-EXBOT-002, FR-EXBOT-003.)
- **Priority:** P0

### II.2. Integration & State verification — Operation: Bot Start Preflight

#### TC_020

- **Title:** Verify the HL rate-limit weight is consumed at step 2 even when a later preflight step fails
- **Pre-condition:**
  1. The `HLRateLimitDO` sliding-window state is accessible and shows current consumed weight.
  2. Preflight step 2 (margin check, weight = 2) is configured to succeed; step 3 (key_status check) is configured to fail.
- **Step:**
  1. Process the `bot-start` preflight so that step 2 runs and step 3 fails immediately after.
- **Expected Result:**
  1. `HLRateLimitDO` shows that weight = 2 was declared and consumed at step 2; this weight is not reversed by the subsequent step 3 failure. The rate-limit budget reflects the actual HL call made. (Reference: FR-EXBOT-091, NFR-EXBOT-004.)
- **Priority:** P1

### II.3. Non-functional (logic) verification — Operation: Bot Start Preflight

#### TC_021

- **Title:** Verify the ExBot Worker returns 403 when accessed directly without the CF service binding
- **Pre-condition:**
  1. No CF service binding is used; the caller sends a direct HTTP request to ExBot Worker's URL without an internal token.
- **Step:**
  1. Send a direct HTTP POST to ExBot Worker's worker URL bypassing the OPERATOR Facade.
- **Expected Result:**
  1. ExBot Worker returns HTTP 403 and does not process the request. All bot-start operations must only be accessible via the OPERATOR Facade at `POST /api/exbot/start` via CF service binding with internal token. (Reference: FR-EXBOT-090, BR-EXBOT-010.)
- **Priority:** P0


---

## III. Operation: LP Mint & Hedge Open (vaultMint → reconcile)

### III.1. Functional verification — Operation: LP Mint & Hedge Open

#### TC_022

- **Title:** Verify the bot record is created with lifecycle_state=preflight after all preflight checks pass
- **Pre-condition:**
  1. All 5 preflight checks have passed for the user.
- **Step:**
  1. Check D1 `bots` table immediately after all preflight pass and before `vaultMint` is called on-chain.
- **Expected Result:**
  1. A bot record exists in D1 with `lifecycle_state='preflight'` written in a single atomic INSERT. No `vaultMint` on-chain call has been made yet. (Reference: FR-EXBOT-003, UC §3 step 4.)
- **Priority:** P0

#### TC_023

- **Title:** Verify LP mint produces a VaultMinted event and D1 positions row is updated with tokenId and lifecycle_state=lp_opened
- **Pre-condition:**
  1. Bot record exists with `lifecycle_state='preflight'`.
  2. BnzaExVault is available (testnet or mocked ABI) and `vaultMint` is set to succeed.
- **Step:**
  1. ExBot Worker calls `BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` on-chain; wait for confirmation.
- **Expected Result:**
  1. On-chain: `VaultMinted(user, botId, tokenId, liquidity)` event is emitted by BnzaExVault.
  2. Off-chain: `positions.token_id` is populated with the `tokenId` from the event; `positions.custodian='vault'`; `positions.tick_lower`, `positions.tick_upper` are stored; `bots.lifecycle_state='lp_opened'`. (Reference: FR-EXBOT-004, UC §3 step 5–6.)
- **Priority:** P0

#### TC_024

- **Title:** Verify on-chain vaultMint failure transitions the bot to the error state
- **Pre-condition:**
  1. Bot record exists with `lifecycle_state='preflight'`.
  2. `BnzaExVault.vaultMint` is mocked to revert (e.g., slippage exceeded or insufficient allowance).
- **Step:**
  1. ExBot Worker calls `vaultMint` while it is set to fail.
- **Expected Result:**
  1. On-chain: the vault transaction reverts; no LP NFT is minted; no `VaultMinted` event is emitted.
  2. Off-chain: `bots.lifecycle_state` transitions to `error`; no `positions.token_id` is written. (Note: the "return funds" mechanism is pending OQ-EXBOT-08 — this TC verifies the state transition only; fund recovery postcondition is blocked.) (Reference: UC §4 A4, FR-EXBOT-003.)
- **Priority:** P0

#### TC_025

- **Title:** Verify weth_index is stored from per-chain config and not hardcoded after LP mint on Base chain
- **Pre-condition:**
  1. Bot is starting on Base chain (chainId = 8453).
  2. `VaultMinted` event has been received.
- **Step:**
  1. Check `positions.weth_index` value after the LP mint completes on Base chain.
- **Expected Result:**
  1. On-chain: `VaultMinted` is emitted with the correct `tokenId`.
  2. Off-chain: `positions.weth_index` is populated with the value from the per-chain verified config for the USDC/WETH 0.3% pool on Base — not a hardcoded constant. The `lpEthAmount` calculation uses this stored `weth_index`. (Note: exact expected value is pending OQ-EXBOT-03 resolution.) (Reference: FR-EXBOT-004, NFR-EXBOT-009.)
- **Priority:** P1

#### TC_026

- **Title:** Verify targetShortEth is computed using BigDecimal arithmetic without intermediate JS float conversion
- **Pre-condition:**
  1. Bot is in `lp_opened` state; `positions.weth_index` is populated.
  2. `lpEthAmount` and `hedgeRatio` are available as BigDecimal strings.
- **Step:**
  1. Trigger hedge computation; inspect the intermediate and final values used in `targetShortEth = lpEthAmount × hedgeRatio`.
- **Expected Result:**
  1. No intermediate `Number()` conversion is used for `lpEthAmount` or `hedgeRatio`. The result stored in D1 is a TEXT string (not a JSON number). `normalizeTargetRatioBps("0.70")` returns 7000n — not 6999n or 7001n due to float rounding. (Reference: FR-EXBOT-021, NFR-EXBOT-008.)
- **Priority:** P0

#### TC_027

- **Title:** Verify Signing Lambda uses KMS agent key to sign the short IOC order and the signed order is sent to HL
- **Pre-condition:**
  1. `targetShortEth` has been computed; the bot is in `hedge_pre_open` state.
  2. Signing Lambda and KMS are available (testnet or mocked).
- **Step:**
  1. ExBot Worker sends the signing request to Signing Lambda; verify the IAM principal that calls `kms:Sign` and the order payload sent to HL.
- **Expected Result:**
  1. Signing Lambda calls KMS `kms:Sign` using the agent key (not the master key). The signed IOC order is sent to HL. Signing Lambda is the only IAM principal that calls `kms:Sign`. No private key material appears in any signed payload, log, or ExBot Worker memory. (Reference: FR-EXBOT-080, NFR-EXBOT-006, SRS F-03.)
- **Priority:** P0

#### TC_028

- **Title:** Verify HL unreachable during hedge open transitions the bot to error state with the correct error code
- **Pre-condition:**
  1. Bot is in `lp_opened` state; LP NFT has been minted and `VaultMinted` received.
  2. HL API (mocked) is set to be unreachable when the short IOC order is submitted.
- **Step:**
  1. Let ExBot Worker attempt to send the short IOC order while HL is unreachable.
- **Expected Result:**
  1. On-chain: LP NFT remains held by BnzaExVault (LP was already minted; `custodian='vault'` unchanged).
  2. Off-chain: `E-EXBOT-008` is surfaced; no stop order is placed; the LP NFT remains held by BnzaExVault (`custodian='vault'` unchanged). `bots.lifecycle_state` transitions away from `hedge_pre_open` — the destination state is `error` per UC §4 A7 but `safe_mode` per `srs/states.md` (`hedge_pre_open → safe_mode`); this conflict is tracked as **I-11 (open blocker, pending BA confirmation)**. Until I-11 is resolved, this TC verifies the failure gate and the LP-open-without-hedge condition; the specific destination state (`error` vs `safe_mode`) must be re-confirmed once I-11 is answered. (Reference: UC §4 A7, E-EXBOT-008.)
- **Priority:** P0

#### TC_029

- **Title:** Verify HL IOC order rejection transitions the bot to error state with the rejection reason captured
- **Pre-condition:**
  1. Bot is in `lp_opened` state; the signed IOC order has been sent to HL.
  2. HL (mocked) accepts the signed request but rejects the IOC order (e.g., margin insufficient at order time, self-trade, or parameter error).
- **Step:**
  1. Let HL process the signed IOC order while rejecting it.
- **Expected Result:**
  1. On-chain: no short position is opened on HL.
  2. Off-chain: the HL rejection reason is captured; no short position exists on HL after the failure. `bots.lifecycle_state` transitions away from `hedge_pre_open` — the destination state is `error` per UC §4 A10 but `safe_mode` per `srs/states.md` (`hedge_pre_open → safe_mode`); this conflict is tracked as **I-11 (open blocker, pending BA confirmation)**. Until I-11 is resolved, this TC verifies that the order is rejected and no hedge position is left; the specific destination state must be re-confirmed once I-11 is answered. (Reference: UC §4 A10.)
- **Priority:** P0

#### TC_030

- **Title:** Verify post-hedge reconcile updates hedge_legs and transitions lifecycle to hedge_post_confirmed
- **Pre-condition:**
  1. The short IOC order has been submitted; the bot is in `hedge_pre_open` state.
  2. HL `clearinghouseState` (mocked) returns an actual short size that matches the expected size.
- **Step:**
  1. ExBot Worker fetches `clearinghouseState` from HL; verify the reconcile result and D1 update.
- **Expected Result:**
  1. Actual short size matches expected; `hedge_legs.entry_price`, `hedge_legs.liquidation_price`, and `hedge_legs.effective_leverage` are populated as BigDecimal TEXT strings; `hedge_legs.last_known_hl_short_size` is updated; `bots.lifecycle_state` transitions to `hedge_post_confirmed`. No `rebalance_attempts.status='success'` is written before reconcile confirms the state. (Reference: FR-EXBOT-025, UC §3 step 8–9.)
- **Priority:** P0

#### TC_031

- **Title:** Verify reconcile mismatch beyond threshold enqueues partial_repair and sends an operator alert
- **Pre-condition:**
  1. The short IOC order has been submitted; the bot is in `hedge_pre_open` state.
  2. HL `clearinghouseState` (mocked) returns an actual short size that deviates from the expected size beyond the configured `drift_threshold`.
- **Step:**
  1. Run the post-hedge reconcile with the mocked mismatch above the threshold.
- **Expected Result:**
  1. A `partial_repair` message is enqueued; an operator alert is triggered with `E-EXBOT-011`; the bot does not proceed to stop placement. (Note: exact `drift_threshold` value is pending I-02 / OQ-EXBOT-11 resolution — this TC verifies the branch behavior when the threshold is exceeded.) (Reference: UC §4 A11, FR-EXBOT-025, E-EXBOT-011.)
- **Priority:** P0

### III.2. Integration & State verification — Operation: LP Mint & Hedge Open

#### TC_032

- **Title:** Verify the tokenId stored in positions matches the on-chain LP NFT held by BnzaExVault
- **Pre-condition:**
  1. Bot-start has completed and `bots.lifecycle_state='active'`.
- **Step:**
  1. Query on-chain BnzaExVault for the LP NFT held for this user; compare with `positions.token_id` in D1.
- **Expected Result:**
  1. On-chain: the NFT with the recorded `tokenId` is held by BnzaExVault, not by the user's wallet.
  2. Off-chain: `positions.token_id` in D1 matches the `tokenId` from the `VaultMinted` event; `positions.custodian='vault'`. This consistency is required for future `user_redeem` and `bot_safe_close` flows. (Reference: FR-EXBOT-004, FR-EXBOT-070.)
- **Priority:** P0

#### TC_033

- **Title:** Verify the deterministic cloid for the short IOC order prevents duplicate order submission on retry
- **Pre-condition:**
  1. A `bot-start` IOC order attempt has already been made for this bot; `botId`, `attemptId`, `stage`, and `version` are known.
- **Step:**
  1. Submit the same bot-start attempt a second time with the same `{botId, attemptId, stage, version}` combination.
- **Expected Result:**
  1. The second submission produces the same cloid as the first (`first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`). If HL deduplicates by cloid, the second submission is detected and skipped after reconcile without placing a duplicate order. (Reference: FR-EXBOT-024.)
- **Priority:** P0

### III.3. Non-functional (logic) verification — Operation: LP Mint & Hedge Open

#### TC_034

- **Title:** Verify the Signing Lambda is the only IAM principal allowed to call kms:Sign during hedge open
- **Pre-condition:**
  1. The bot is in `lp_opened` state and ExBot Worker is about to send a signing request.
  2. IAM audit logging is enabled for KMS.
- **Step:**
  1. Trigger the hedge open; inspect AWS CloudTrail or equivalent logs for `kms:Sign` calls made during the operation.
- **Expected Result:**
  1. Only Signing Lambda's IAM role appears as the caller for `kms:Sign` during this operation. No other IAM principal (including ExBot Worker) makes a `kms:Sign` call. This verifies the principle of least privilege for the signing path. (Reference: FR-EXBOT-080, NFR-EXBOT-006, SRS F-03.)
- **Priority:** P0


---

## IV. Operation: Stop Placement & Bot Activation

### IV.1. Functional verification — Operation: Stop Placement & Bot Activation

#### TC_035

- **Title:** Verify stop_trigger_px is computed using BigDecimal with stopSafetyFactor=0.70 and stored as a TEXT string
- **Pre-condition:**
  1. Bot is in `hedge_post_confirmed` state; `hedge_legs.entry_price` and `hedge_legs.liquidation_price` are populated.
- **Step:**
  1. ExBot Worker computes `stop_trigger_px`; inspect the computation path and the final value stored in D1.
- **Expected Result:**
  1. `stop_trigger_px = entry_price × (1 + ((liquidation_price − entry_price) / entry_price) × 0.70)` is computed entirely in BigDecimal with no intermediate `Number()` conversion. The result is stored as a TEXT BigDecimal string in `hedge_legs.stop_price`. For a position with isolated leverage, `stop_price` is less than `liquidation_price` with at least 30% buffer. (Reference: FR-EXBOT-030, NFR-EXBOT-008.)
- **Priority:** P0

#### TC_036

- **Title:** Verify stop price computation falls back to the 1/effective_leverage formula when liquidationPx is unavailable
- **Pre-condition:**
  1. Bot is in `hedge_post_confirmed` state.
  2. HL `clearinghouseState` returned a null or absent `liquidationPx` field.
- **Step:**
  1. ExBot Worker computes `stop_trigger_px` using the fallback formula.
- **Expected Result:**
  1. `stop_trigger_px = entry_price × (1 + (1 / effective_leverage) × 0.70)` is computed using BigDecimal. The BigDecimal constraint still applies to the fallback. The result is stored as a TEXT string in D1. (Reference: FR-EXBOT-030.)
- **Priority:** P1

#### TC_037

- **Title:** Verify reduce-only stop market placement confirms on HL and lifecycle transitions to stop_verified then active
- **Pre-condition:**
  1. Bot is in `stop_placing` state; `stop_trigger_px` has been computed and stored.
  2. HL (mocked) is set to accept and confirm the stop market order.
- **Step:**
  1. ExBot Worker sends `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)` via Signing Lambda; wait for confirmation.
- **Expected Result:**
  1. On-chain: HL confirms the reduce-only stop market order.
  2. Off-chain: `hedge_legs.stop_cloid` and `hedge_legs.stop_price` are written to D1; `bots.lifecycle_state` transitions first to `stop_verified` then immediately to `active`; `bots.status='active'`. The bot cannot reach `active` without a confirmed stop — the INV-STOP invariant is satisfied from initialization. (Reference: FR-EXBOT-031, UC §3 step 10–11.)
- **Priority:** P0

#### TC_038

- **Title:** Verify stop placement failure prevents the bot from reaching active and triggers an operator alert
- **Pre-condition:**
  1. Bot is in `stop_placing` state; the short IOC was already filled on HL.
  2. HL (mocked) is set to reject or not confirm the reduce-only stop market order.
- **Step:**
  1. Let ExBot Worker attempt `placeReduceOnlyStopMarket` while HL is set to fail.
- **Expected Result:**
  1. On-chain: the HL short position remains open but no stop order is placed.
  2. Off-chain: `E-EXBOT-009` ("Failed to place native stop on Hyperliquid. Bot cannot activate without a stop.") is surfaced; an operator alert is sent; the bot does NOT reach `lifecycle_state='active'`; `bots.lifecycle_state` transitions to `safe_mode` (per states.md `stop_placing → safe_mode`; I-06 resolved 2026-07-02). Auto-recovery per FR-EXBOT-050 begins: system retries when HL is responsive + 3 consecutive reconciles succeed; if irrecoverable → `bot_safe_close` is triggered. (Reference: UC §4 A8, FR-EXBOT-031, FR-EXBOT-050, E-EXBOT-009.)
- **Priority:** P0

#### TC_039

- **Title:** Verify the full bot-start sequence traverses all 9 lifecycle states in strict order with no state skipped
- **Pre-condition:**
  1. All preconditions for a full happy-path bot-start are met: no existing active bot, sufficient HL margin, agent key active, builder fee confirmed, LP mint simulation passes, BnzaExVault and HL are available.
- **Step:**
  1. Trigger the full bot-start flow from `bot-start` queue message to `active` state; observe D1 `bots.lifecycle_state` after each step completes.
- **Expected Result:**
  1. The sequence observed in D1 is exactly: `preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` — with no state skipped, no state repeated, and each transition persisted atomically before the next step begins. Final state: `bots.lifecycle_state='active'`, `bots.status='active'`, `positions.custodian='vault'`, `positions.token_id` populated, `hedge_legs.stop_price` and `stop_cloid` populated as non-null BigDecimal TEXT strings. (Reference: FR-EXBOT-003, AC-01.)
- **Priority:** P0

#### TC_040

- **Title:** Verify stop_price is less than liquidation_price and maintains at least a 30% safety buffer
- **Pre-condition:**
  1. Bot-start has completed; bot is in `active` state.
  2. The hedge position was opened with a known isolated leverage setting. (Example: isolated leverage ≈ 3×.)
- **Step:**
  1. Read `hedge_legs.stop_price`, `hedge_legs.liquidation_price`, and `hedge_legs.entry_price` from D1; compute the actual buffer percentage.
- **Expected Result:**
  1. `hedge_legs.stop_price` (BigDecimal) < `hedge_legs.liquidation_price`. The distance from `stop_price` to `liquidation_price`, expressed as a percentage of the entry-to-liquidation range, is at least 30% (confirming `stopSafetyFactor=0.70` is applied: stop fires at 70% of the distance to liquidation). (Reference: FR-EXBOT-030, AC-13.)
- **Priority:** P0

### IV.2. Integration & State verification — Operation: Stop Placement & Bot Activation

#### TC_041

- **Title:** Verify light-check and deep-audit are scheduled in D1 after the bot reaches active state
- **Pre-condition:**
  1. Bot-start has just completed; `bots.lifecycle_state='active'`.
- **Step:**
  1. Read `bots.next_light_check_at` and `bots.next_deep_audit_at` from D1 immediately after the bot reaches `active`.
- **Expected Result:**
  1. `bots.next_light_check_at` is set to a time within 5 minutes plus jitter (−45s to +45s) from now. A deep-audit is scheduled within the next 6 hours (`bots.next_deep_audit_at` is in the future and within the 6h window). The cross-UC dependencies (UC-EXBOT-light-check, UC-EXBOT-deep-audit) are activated by the `active` lifecycle transition. (Reference: FR-EXBOT-012, FR-EXBOT-016, FR-EXBOT-013.)
- **Priority:** P1

#### TC_042

- **Title:** Verify the status API returns active state and hedge summary after the bot reaches active
- **Pre-condition:**
  1. Bot is in `active` state with `hedge_legs` and `positions` rows populated.
- **Step:**
  1. Call `GET /api/exbot/status` via the OPERATOR Facade after the bot reaches `active`.
- **Expected Result:**
  1. The response includes `status='active'`, `botId`, and hedge/LP summary fields. The response does not expose any private key material. The OPERATOR logs show the request was proxied via CF service binding to ExBot Worker. (Reference: FR-EXBOT-090, FR-EXBOT-003, UC §3 step 12.)
- **Priority:** P1

#### TC_043

- **Title:** Verify the bot-start queue message is processed exactly once even when redelivered
- **Pre-condition:**
  1. A `bot-start` queue message has been delivered and processing has started (or completed) once.
- **Step:**
  1. Deliver the same `bot-start` message a second time with the same `message_id`.
- **Expected Result:**
  1. The second delivery encounters a UNIQUE constraint conflict on `queue_idempotency.message_id` and exits immediately; only one bot record exists in D1 for the user; no duplicate HL orders are submitted; no duplicate `positions` or `hedge_legs` rows are created. (Reference: FR-EXBOT-011, NFR-EXBOT-007, AC-14.)
- **Priority:** P0

#### TC_044

- **Title:** Verify two simultaneous bot-start messages for the same user result in exactly one bot being created
- **Pre-condition:**
  1. No existing bot for the user (policy check would pass for the first).
  2. Two concurrent `bot-start` queue messages for the same user are pending (simulating two on-chain deposit events processed at the same time).
- **Step:**
  1. Deliver both `bot-start` messages to two separate worker instances at the same time.
- **Expected Result:**
  1. Exactly one bot record is created in D1. The second worker either hits the `queue_idempotency` UNIQUE constraint or hits the one-bot policy check after the first bot is created — in either case no duplicate bot is created and no duplicate HL orders are placed. (Reference: FR-EXBOT-001, FR-EXBOT-011, BR-EXBOT-001.)
- **Priority:** P0

### IV.3. Non-functional (logic) verification — Operation: Stop Placement & Bot Activation

#### TC_045

- **Title:** Verify the agent key is never written to logs while it is decrypted for signing during bot start
- **Pre-condition:**
  1. The user's agent key is active (`key_status='active'` in `hl_agent_keys`).
  2. Log capture is enabled for the worker execution.
- **Step:**
  1. Run the bot-start so the agent key is decrypted for signing (for `openShortIoc` and `placeReduceOnlyStopMarket`); then read the worker logs and any error output.
- **Expected Result:**
  1. No private key material appears anywhere in the logs or error output. The agent private key is generated and retained exclusively in AWS KMS — it never leaves the HSM, is never passed to ExBot Worker or Signing Lambda's memory as plaintext, and is never written to D1. A dump of `hl_agent_keys` shows only public addresses and metadata. (Reference: FR-EXBOT-080, NFR-EXBOT-006, AC-11.)
- **Priority:** P0

#### TC_046

- **Title:** Verify all financial values in D1 after bot activation are stored as BigDecimal TEXT strings, not numeric types
- **Pre-condition:**
  1. Bot-start has completed; bot is in `active` state.
- **Step:**
  1. Read the D1 schema and row values for `hedge_legs.entry_price`, `hedge_legs.liquidation_price`, `hedge_legs.effective_leverage`, `hedge_legs.stop_price`, `positions.token_id`.
- **Expected Result:**
  1. All financial amount fields (`entry_price`, `liquidation_price`, `effective_leverage`, `stop_price`) are stored as TEXT columns containing BigDecimal string values — not stored as REAL or INTEGER SQLite types. No JSON number literals (e.g., `0.7` instead of `"0.7"`) exist for any financial field. (Reference: NFR-EXBOT-008, ERD invariant.)
- **Priority:** P0

