# Test Cases — UC-EXBOT-bot-start Start ExBot

**Document Title:** Test Cases — UC-EXBOT-bot-start Start ExBot (v6)
**Date Created:** 2026-07-08
**Author / Agent:** qc-func-tc-design-exbot
**Version:** v6

---

**Total test cases:** 48 (FUNC: 35, INTG: 8, NFR: 5)
**Scope:** Logic-only (backend / API / bot — no UI)
**Update trigger:** REQUIREMENT_DELTA (UC updated 2026-07-07: vault balance preflight added as step 2; E-EXBOT-017 message updated; IS-03 flagged)
**Source UC:** UC-EXBOT-bot-start_bot-start_audited_20260707_v4.md
**Source scenarios (if any):** UC-EXBOT-bot-start_bot-start_scenarios_20260707_v4.md
**Output language:** English

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Happy path — all 9 lifecycle states in sequence, hedge + stop populated | TC_001, TC_002, TC_022, TC_023, TC_030, TC_037, TC_039, TC_040 | Covered |
| AC-02 | One-bot policy blocks start, no new record | TC_008, TC_009 | Covered |
| AC-03 | Vault balance = 0 — E-EXBOT-025 blocks start | TC_047, TC_048 | Covered [NEW] |
| AC-04 | Margin insufficient — exact shortfall in message | TC_012, TC_013 | Covered |
| AC-05 | Key not provisioned — E-EXBOT-017 blocks start | TC_015 | Covered [UPDATE] |
| AC-06 | Stop fail — safe_mode + auto-recovery per FR-EXBOT-050 | TC_038 | Covered |
| AC-07 | Reconcile mismatch — partial_repair enqueued + operator alert | TC_031 | Covered |
| AC-08 | KMS key — private key never in DB or logs after provisioning | TC_007, TC_045 | Covered |
| AC-09 | HL IOC reject — destination state (IS-01 open) | TC_029 | Covered (IS-01 OPEN: `error` per UC A10 vs `safe_mode` per states.md; pending BA confirmation) |
| AC-10 | weth_index per chain stored from config (pending OQ-EXBOT-03) | TC_025 | Covered (blocked OQ-EXBOT-03) |
| AC-11 | stop_trigger_px BigDecimal, stop less than liq with 30% buffer | TC_035, TC_040 | Covered |

---

## I. Operation: Key Provision (chain indexer to KMS to HL approveAgent)

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

#### TC_002 [UPDATED — Reason: IS-03 annotation added]

- **Title:** Verify key_status is set to active only after HL approveAgent confirms the agent registration
- **Pre-condition:**
  1. KMS has generated both key pairs successfully.
  2. HL `approveAgent` call is in progress (pending HL confirmation).
- **Step:**
  1. Check `hl_agent_keys.key_status` before HL confirmation arrives; then let HL confirm `approveAgent` and check again.
- **Expected Result:**
  1. Before HL confirmation: `key_status` is not `active`. After HL confirms: `key_status='active'` is written atomically to Aurora PostgreSQL and a `bot-start` job is enqueued. (Note: `spec.md` FR-EXBOT-080 mentions `key_status='provisioning'` as a transient state in the failure path, but `states.md` only defines three states — `active`, `superseded`, `revoked` — with no `provisioning`. This conflict is tracked as IS-03 (Minor, open); the exact transient value before `active` is pending BA confirmation.) (Reference: FR-EXBOT-080, SRS F-03a.)
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

#### TC_004 [UPDATED — Reason: IS-03 annotation added]

- **Title:** Verify HL approveAgent failure keeps key_status as not active and triggers retry
- **Pre-condition:**
  1. KMS has generated both key pairs; `hl_user_address` and `agent_address` are available.
  2. HL `approveAgent` is mocked to return an error.
- **Step:**
  1. Let Key-Provision Worker call HL `approveAgent` while it is set to fail; then check the DB row and the queue.
- **Expected Result:**
  1. `hl_agent_keys.key_status` does not become `active`; the worker re-enqueues a retry via the `key-provision` queue; no `bot-start` job is enqueued until `key_status='active'` is confirmed. An admin alert is sent when the SLA wait time is exceeded. (Note: `spec.md` FR-EXBOT-080 refers to `key_status='provisioning'` in this failure path, but `states.md` does not list `provisioning` as a valid state — tracked as IS-03 (Minor, open); verify the actual stored value against whichever source BA confirms.) (Reference: FR-EXBOT-080.)
- **Priority:** P0

#### TC_005

- **Title:** Verify duplicate key-provision queue message does not provision a second key pair
- **Pre-condition:**
  1. A `key-provision` message has already been processed once and `key_status='active'` is set.
  2. The same message is redelivered (SQS at-least-once semantics).
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
  1. Dump the `hl_agent_keys` table from Aurora PostgreSQL; search application logs for the time window of the provisioning run; inspect any API response bodies from Key-Provision Worker.
- **Expected Result:**
  1. No hex-encoded or base64-encoded 256-bit/512-bit private key pattern appears in any Aurora PostgreSQL field, log line, or response payload. Only `hl_user_address`, `agent_address`, and metadata (status, timestamps) are stored in plaintext. Private keys remain exclusively in AWS KMS HSM. (Reference: FR-EXBOT-080, NFR-EXBOT-006.)
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
  1. Preflight step 1 passes (the count of disqualifying statuses = 0); the flow proceeds to preflight step 2 (vault balance check). A `closed` bot does not block a new start per BR-EXBOT-001. (Reference: FR-EXBOT-001, BR-EXBOT-001.)
- **Priority:** P0

#### TC_047 [NEW — AC-03]

- **Title:** Verify the start is blocked when the user has no confirmed on-chain deposit in the vault
- **Pre-condition:**
  1. Preflight step 1 (one-bot policy) passes — the user has no active bot.
  2. The user's `BnzaExVault` on-chain balance is zero (no deposit has been confirmed on-chain for this user).
- **Step:**
  1. Process the `bot-start` preflight for the user while the vault balance is zero.
- **Expected Result:**
  1. Preflight step 2 fails with `E-EXBOT-025` ("No confirmed deposit found. Please complete an on-chain deposit before starting the bot.", HTTP 400). No bot record is created in Aurora PostgreSQL. The flow does not proceed to step 3 (margin check). (Reference: FR-EXBOT-002 step 2, E-EXBOT-025.)
- **Priority:** P0

#### TC_048 [NEW — AC-03]

- **Title:** Verify the vault balance check passes and the flow proceeds to the margin check when a deposit is confirmed
- **Pre-condition:**
  1. Preflight step 1 passes.
  2. The user has a confirmed on-chain deposit: `BnzaExVault` balance is greater than zero.
- **Step:**
  1. Process the `bot-start` preflight with a non-zero vault balance.
- **Expected Result:**
  1. Preflight step 2 passes; the flow proceeds to step 3 (HL margin check). No error is returned for this step. (Reference: FR-EXBOT-002 step 2.)
- **Priority:** P0

#### TC_011 [UPDATED — Reason: margin is now step 3 of 6]

- **Title:** Verify the margin check passes at exactly the minimum required margin including the 2.0x buffer
- **Pre-condition:**
  1. Preflight steps 1 and 2 (one-bot policy, vault balance) pass.
  2. The user's HL isolated margin balance equals exactly the required margin multiplied by 2.0 (right at the threshold, no extra). (Example: required base approx 350; balance approx 700, which is exactly 2.0x.)
- **Step:**
  1. Process the `bot-start` preflight with the user's HL margin set to exactly the 2.0x threshold.
- **Expected Result:**
  1. Preflight step 3 passes and the flow proceeds to step 4. The formula uses `hlOraclePrice` (not HL mark price or Uniswap pool price) per FR-EXBOT-061. (Reference: FR-EXBOT-002 step 3, FR-EXBOT-061.)
- **Priority:** P0

#### TC_012 [UPDATED — Reason: margin is now step 3 of 6]

- **Title:** Verify the margin check fails when the user's balance is just below the 2.0x threshold
- **Pre-condition:**
  1. Preflight steps 1 and 2 pass.
  2. The user's HL margin is just below the required margin multiplied by 2.0. (Example: required 2.0x approx 700; balance approx 699.)
- **Step:**
  1. Process the `bot-start` preflight with the user's margin set just below the minimum threshold.
- **Expected Result:**
  1. Preflight step 3 fails with `E-EXBOT-002` (HTTP 400). The message includes the required amount, current amount, and exact shortfall. No bot record is created in Aurora PostgreSQL. (Reference: FR-EXBOT-002 step 3, FR-EXBOT-061.)
- **Priority:** P0

#### TC_013

- **Title:** Verify the margin error message shows the exact shortfall without rounding down
- **Pre-condition:**
  1. Preflight steps 1 and 2 pass.
  2. The user's HL margin is below the required 2.0x threshold by an amount that is not a round number. (Example: balance approx 300, required approx 700 — shortfall approx 400.)
- **Step:**
  1. Process the `bot-start` preflight with the gap between current and required margin being a non-round amount.
- **Expected Result:**
  1. The start is blocked (`E-EXBOT-002`, HTTP 400). The message shows the exact amount the user still needs to deposit — the shortfall is not rounded down to a coarser unit, so depositing exactly that amount would be sufficient. (Example: if shortfall = 400.75, the message shows 400.75, not 400.) (Reference: FR-EXBOT-061 AC.)
- **Priority:** P0

#### TC_014

- **Title:** Verify the preflight is blocked when HL is unreachable during the margin check step
- **Pre-condition:**
  1. Preflight steps 1 and 2 pass.
  2. HL API (mocked) is set to time out or return an error when `marginSummary` is requested.
- **Step:**
  1. Process the `bot-start` preflight while HL is unreachable during step 3 (margin check).
- **Expected Result:**
  1. The start fails immediately with `E-EXBOT-008`; no bot record is created; the preflight does not proceed to step 4. (Per I-03 confirmed answer: HL timeout at preflight = immediate fail, no retry loop.) (Reference: UC step 3, E-EXBOT-008.)
- **Priority:** P0

#### TC_015 [UPDATED — Reason: E-EXBOT-017 message text changed in v4; step 4 of 6]

- **Title:** Verify the start is blocked when the agent key is not yet provisioned
- **Pre-condition:**
  1. Preflight steps 1, 2, and 3 (one-bot policy, vault balance, margin) pass.
  2. The user has no `hl_agent_keys` row with `key_status='active'` (key-provision has not yet completed).
- **Step:**
  1. Process the `bot-start` preflight while the agent key is absent or not active.
- **Expected Result:**
  1. Preflight step 4 fails with `E-EXBOT-017` ("Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete.", HTTP 400). No bot record is created. (Reference: FR-EXBOT-002 step 4, E-EXBOT-017.)
- **Priority:** P0

#### TC_016 [UPDATED — Reason: builder fee is now step 5 of 6]

- **Title:** Verify the start is blocked when builder fee (5bps) has not been confirmed on HL
- **Pre-condition:**
  1. Preflight steps 1, 2, 3, and 4 pass.
  2. Builder fee (5bps) has not been confirmed on HL for this user.
- **Step:**
  1. Process the `bot-start` preflight at step 5 while builder fee is not confirmed.
- **Expected Result:**
  1. Preflight step 5 fails with `E-EXBOT-005` ("HL builder fee (5bps) approval required before starting ExBot.", HTTP 400). No bot record is created. (Note: the exact HL endpoint for the fee check is pending OQ-EXBOT-05 — this TC verifies the gate behavior.) (Reference: FR-EXBOT-002 step 5, E-EXBOT-005.)
- **Priority:** P0

#### TC_017 [UPDATED — Reason: builder fee is now step 5 of 6]

- **Title:** Verify a previously confirmed builder fee from a prior session still passes the check at start
- **Pre-condition:**
  1. Preflight steps 1, 2, 3, and 4 pass.
  2. Builder fee was confirmed in a previous session (not the current start attempt).
- **Step:**
  1. Process the `bot-start` preflight at step 5 using a pre-confirmed builder fee.
- **Expected Result:**
  1. Preflight step 5 passes — the system accepts the previously confirmed builder fee without requiring a new on-chain or API confirmation per start attempt. The flow proceeds to step 6 (LP mint simulation). (Per I-10 confirmed answer: builder fee check is a one-time check at start.) (Reference: FR-EXBOT-002 step 5.)
- **Priority:** P1

#### TC_018 [UPDATED — Reason: LP mint simulation is now step 6 of 6]

- **Title:** Verify LP mint simulation failure blocks the start without making any on-chain call
- **Pre-condition:**
  1. All preflight steps 1 through 5 pass.
  2. LP mint simulation (mocked) is set to fail (e.g., pool liquidity too low or slippage exceeds tolerance).
- **Step:**
  1. Process the `bot-start` preflight at step 6 while LP mint simulation is set to fail.
- **Expected Result:**
  1. Preflight step 6 fails with `E-EXBOT-006` ("LP mint simulation failed. Check pool liquidity or adjust deposit amount.", HTTP 400). No bot record is created; no on-chain `vaultMint` call is made (no gas consumed). (Reference: FR-EXBOT-002 step 6, E-EXBOT-006.)
- **Priority:** P0

#### TC_019 [UPDATED — Reason: 6 preflight steps; vault balance step 2 added]

- **Title:** Verify no partial bot record is left after any one of the six preflight steps fails
- **Pre-condition:**
  1. This test is run six times — once for each preflight step — with each step configured to fail while all prior steps pass.
- **Step:**
  1. Fail preflight at step 1 (one-bot policy); query Aurora PostgreSQL for new bot records. Repeat for steps 2 (vault balance), 3 (margin), 4 (key_status), 5 (builder fee), and 6 (LP simulation).
- **Expected Result:**
  1. After each preflight failure, `bot_registry` and `bots` contain zero new rows for the user. The bot record is only created AFTER all 6 preflight checks pass (FR-EXBOT-002 AC). No partial record exists under any failure scenario. (Reference: FR-EXBOT-002, FR-EXBOT-003.)
- **Priority:** P0

#### TC_020 [UPDATED — Reason: margin is now step 3 of 6; vault balance step 2 passes]

- **Title:** Verify the HL rate-limit weight is consumed at step 3 even when a later preflight step fails
- **Pre-condition:**
  1. Preflight steps 1 and 2 (one-bot policy, vault balance) pass.
  2. The margin check at step 3 succeeds (HL API is called and responds successfully).
  3. The key_status check at step 4 is configured to fail.
- **Step:**
  1. Process the `bot-start` preflight; allow step 3 to complete against HL successfully, then observe failure at step 4.
- **Expected Result:**
  1. One HL `marginSummary` API call is made (rate-limit weight consumed) at step 3; the flow then fails at step 4 with `E-EXBOT-017`. The consumed HL rate-limit weight is NOT reversed. No bot record is created. (Reference: FR-EXBOT-002 step 3, FR-EXBOT-061.)
- **Priority:** P1

#### TC_021

- **Title:** Verify the ExBot Lambda returns 403 when accessed directly without going through API Gateway
- **Pre-condition:**
  1. An attempt is made to call the ExBot Lambda ARN directly, bypassing API Gateway (e.g., via AWS SDK invoke or a crafted direct invocation without the API Gateway event wrapper).
- **Step:**
  1. Send a direct invocation to the ExBot Lambda endpoint that does not include the expected API Gateway headers/context.
- **Expected Result:**
  1. The Lambda returns HTTP 403 (or an authorization error equivalent). No `bot-start` processing is triggered. This verifies that the Lambda is not publicly accessible except through API Gateway. (Reference: NFR-EXBOT-003.)
- **Priority:** P0

### II.2. Integration & State verification — Operation: Bot Start Preflight

_No additional integration TCs beyond TC_020 — the preflight integration points are fully covered by the functional TCs above which assert both API call behavior and DB state._

---

## III. Operation: LP Mint & Hedge Open

### III.1. Functional verification — Operation: LP Mint & Hedge Open

#### TC_022

- **Title:** Verify the bot record is created with lifecycle_state=preflight after all six preflight checks pass
- **Pre-condition:**
  1. All six preflight checks pass successfully.
- **Step:**
  1. Process the `bot-start` job through all preflight steps; query `bots` table immediately after the last preflight step passes.
- **Expected Result:**
  1. A new row is created in `bots` and `bot_registry` with `lifecycle_state='preflight'`. The record is created only after ALL 6 preflight checks pass — not before. (Reference: FR-EXBOT-002, FR-EXBOT-003.)
- **Priority:** P0

#### TC_023

- **Title:** Verify LP mint produces a VaultMinted event and the positions row is updated with tokenId and tick ranges
- **Pre-condition:**
  1. Bot is in `lifecycle_state='preflight'`; all preflight checks have passed.
  2. Uniswap V3 pool and BnzaExVault are responsive.
- **Step:**
  1. Process the LP opening phase — trigger `vaultMint` on-chain; wait for the transaction to be confirmed on-chain.
- **Expected Result:**
  1. A `VaultMinted` event is emitted on-chain. The `positions` row in Aurora PostgreSQL is updated with the correct `tokenId`, `tickLower`, `tickUpper`, and liquidity amounts. `lifecycle_state` transitions from `preflight` to `lp_opening`, then to `lp_opened` after confirmation. (Reference: FR-EXBOT-010, FR-EXBOT-003.)
- **Priority:** P0

#### TC_024

- **Title:** Verify on-chain vaultMint failure transitions the bot to the error state
- **Pre-condition:**
  1. Bot is in `lifecycle_state='preflight'`.
  2. On-chain `vaultMint` call is mocked to revert (e.g., insufficient liquidity, slippage exceeded on-chain).
- **Step:**
  1. Process the LP opening phase with `vaultMint` set to revert; wait for the failure to propagate.
- **Expected Result:**
  1. `lifecycle_state` transitions to `error` (not left in `lp_opening`). An operator alert is sent. No partial LP position is recorded in `positions`. (Reference: FR-EXBOT-010, FR-EXBOT-003.)
- **Priority:** P0

#### TC_025

- **Title:** Verify weth_index is stored from per-chain config and not hardcoded after LP mint on Base chain
- **Pre-condition:**
  1. Bot is executing LP mint on Base chain.
  2. Per-chain config has a `weth_index` value defined for Base.
- **Step:**
  1. Process LP mint on Base chain; inspect the stored `weth_index` value in Aurora PostgreSQL after the LP position is confirmed.
- **Expected Result:**
  1. The stored `weth_index` matches the value from the per-chain config (not a hardcoded constant). If the config value is updated and the test is re-run, the stored value reflects the new config. (Reference: OQ-EXBOT-03 pending; TC blocked by open question but written for when it is resolved.)
- **Priority:** P1

#### TC_026

- **Title:** Verify targetShortEth is computed using BigDecimal arithmetic and matches the expected formula output
- **Pre-condition:**
  1. LP position has been confirmed on-chain; `lp_opened` state is reached.
  2. Known inputs: `lp_eth_value`, `hedge_ratio`, `basis_adjustment` — all in BigDecimal-compatible format.
- **Step:**
  1. Trigger hedge-open phase; capture the `targetShortEth` value sent to Signing Lambda.
- **Expected Result:**
  1. `targetShortEth` equals `lp_eth_value × hedge_ratio × basis_adjustment` computed with BigDecimal (no floating-point rounding). Example: if lp_eth_value = 1.123456789012345678 ETH, the value is preserved without truncation. No `Number()` or `parseFloat()` is used in the computation path. (Reference: FR-EXBOT-061, AC-11.)
- **Priority:** P0

#### TC_027

- **Title:** Verify Signing Lambda uses the KMS agent key to sign the short IOC order before submitting to HL
- **Pre-condition:**
  1. Bot is in `hedge_pre_open` state; `targetShortEth` is computed.
  2. Signing Lambda has IAM role with `kms:Sign` permission for the agent key.
- **Step:**
  1. Allow the hedge-open phase to proceed; intercept the KMS `Sign` call and the subsequent HL order submission.
- **Expected Result:**
  1. The KMS `Sign` API is called with the agent key ARN before the HL order is submitted. The HL order payload carries the signature produced by KMS. The private key material never leaves KMS HSM — only the signature is returned. (Reference: FR-EXBOT-080, NFR-EXBOT-006.)
- **Priority:** P0

#### TC_028 [IS-01 OPEN BLOCKER: destination state unclear — UC A7 says `error`, states.md says `safe_mode`]

- **Title:** Verify HL unreachable during hedge open transitions the bot to the correct error state
- **Pre-condition:**
  1. Bot is in `hedge_pre_open` state.
  2. HL API (mocked) is set to time out or return 5xx when the IOC order is submitted.
- **Step:**
  1. Allow the hedge-open phase to attempt HL order submission while HL is unreachable.
- **Expected Result:**
  1. The bot transitions out of `hedge_pre_open` to a terminal error state. (IS-01 OPEN: UC §4 A7 states the destination is `error`, but `states.md` defines `hedge_pre_open → safe_mode` for this failure. The correct destination state is unresolved — pending BA confirmation. This TC verifies a failure transition occurs and no bot is left stuck in `hedge_pre_open`; the exact state assertion must be updated once IS-01 is resolved.) (Reference: FR-EXBOT-003, IS-01.)
- **Priority:** P0

#### TC_029 [IS-01 OPEN BLOCKER: destination state unclear — UC A10 says `error`, states.md says `safe_mode`]

- **Title:** Verify HL IOC order rejection transitions the bot to the correct error state
- **Pre-condition:**
  1. Bot is in `hedge_pre_open` state.
  2. HL API (mocked) is set to return an IOC rejection response (order rejected, not filled).
- **Step:**
  1. Allow the hedge-open phase to submit the IOC order; receive the HL rejection response.
- **Expected Result:**
  1. The bot transitions out of `hedge_pre_open` to a terminal error state. (IS-01 OPEN: UC §4 A10 states the destination is `error`, but `states.md` defines `hedge_pre_open → safe_mode` for IOC rejection. The correct destination state is unresolved — pending BA confirmation. This TC verifies a failure transition occurs; the exact state assertion must be updated once IS-01 is resolved.) (Reference: FR-EXBOT-003, IS-01, AC-09.)
- **Priority:** P0

#### TC_030

- **Title:** Verify post-hedge reconcile updates hedge_legs and transitions lifecycle to hedge_post_confirmed
- **Pre-condition:**
  1. Bot is in `hedge_pre_open` state; HL IOC order has been submitted successfully.
- **Step:**
  1. Simulate HL confirming the IOC order fill; trigger the post-hedge reconcile step.
- **Expected Result:**
  1. `hedge_legs` row in Aurora PostgreSQL is updated with the confirmed fill size, entry price, and HL order ID. `lifecycle_state` transitions from `hedge_pre_open` to `hedge_post_confirmed`. (Reference: FR-EXBOT-003, FR-EXBOT-062, AC-01.)
- **Priority:** P0

#### TC_031

- **Title:** Verify reconcile mismatch beyond the tolerance threshold enqueues a partial_repair job and sends an operator alert
- **Pre-condition:**
  1. Post-hedge reconcile runs; the confirmed fill size from HL deviates from `targetShortEth` by more than the defined tolerance threshold.
- **Step:**
  1. Mock HL to report a confirmed fill size that exceeds the mismatch tolerance (e.g., fill = 0.5 ETH when target = 1.0 ETH).
- **Expected Result:**
  1. A `partial_repair` job is enqueued in SQS; an operator alert is sent with the mismatch details (expected vs. actual size). `lifecycle_state` is NOT advanced to `hedge_post_confirmed` until reconciliation is resolved. (Reference: FR-EXBOT-062, AC-07.)
- **Priority:** P0

#### TC_032

- **Title:** Verify the tokenId stored in positions matches the on-chain LP NFT held by BnzaExVault
- **Pre-condition:**
  1. LP mint has completed; `lp_opened` state reached; `positions.tokenId` is stored in Aurora PostgreSQL.
- **Step:**
  1. Query the on-chain `BnzaExVault` to get the LP NFT token ID it holds; compare to `positions.tokenId` in Aurora PostgreSQL.
- **Expected Result:**
  1. `positions.tokenId` in Aurora PostgreSQL exactly matches the LP NFT token ID held by `BnzaExVault` on-chain. No mismatch is allowed. (Reference: FR-EXBOT-010, AC-01.)
- **Priority:** P0

### III.2. Integration & State verification — Operation: LP Mint & Hedge Open

#### TC_033

- **Title:** Verify the deterministic cloid for the short IOC order prevents duplicate order submission on retry
- **Pre-condition:**
  1. A `bot-start` job for bot ID `botId=1001` with `attemptId=1` is processed; the hedge IOC order submission fails transiently after the order is sent but before confirmation is received.
  2. The same job is retried with identical `botId` and `attemptId`.
- **Step:**
  1. On retry, allow the hedge-open phase to recompute the cloid and attempt to resubmit the IOC order to HL.
- **Expected Result:**
  1. The recomputed cloid equals `first128BitsHex(keccak256("bnza:1001:1:hedge:v1"))` — identical to the first attempt. HL deduplicates on cloid and does NOT open a second position. The reconcile step detects the existing fill and advances to `hedge_post_confirmed` without double-sending. (Reference: FR-EXBOT-011, FR-EXBOT-062.)
- **Priority:** P0

#### TC_034

- **Title:** Verify the Signing Lambda is the only IAM principal allowed to call kms:Sign during hedge open
- **Pre-condition:**
  1. IAM policies are in place; hedge-open phase is in progress.
- **Step:**
  1. Attempt to call `kms:Sign` on the agent key ARN from a principal other than the Signing Lambda IAM role (e.g., the ExBot Lambda role, a developer IAM user, or the Key-Provision Worker role).
- **Expected Result:**
  1. All calls to `kms:Sign` from non-Signing-Lambda principals are rejected by IAM with `AccessDeniedException`. Only the Signing Lambda IAM role succeeds. The agent key cannot be used for signing from any other context. (Reference: NFR-EXBOT-006, FR-EXBOT-080.)
- **Priority:** P0

---

## IV. Operation: Stop Placement & Bot Activation

### IV.1. Functional verification — Operation: Stop Placement & Bot Activation

#### TC_035

- **Title:** Verify stop_trigger_px is computed using BigDecimal with stopSafetyFactor=0.70
- **Pre-condition:**
  1. Bot has reached `hedge_post_confirmed`; `entry_price` and `liq_distance_pct` are known.
- **Step:**
  1. Trigger stop placement; capture the `stop_trigger_px` value sent to HL.
- **Expected Result:**
  1. `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)` — computed with BigDecimal (no floating-point rounding). Example: if entry_price = 3500.123456789 and liq_distance_pct = 0.10, stop_trigger_px = 3500.123456789 × (1 + 0.07) = 3745.132098... — precision is preserved. (Reference: FR-EXBOT-050, AC-11.)
- **Priority:** P0

#### TC_036

- **Title:** Verify stop price computation falls back to the 1/effective_leverage formula when liq_distance_pct is unavailable
- **Pre-condition:**
  1. Bot has reached `hedge_post_confirmed`; `liq_distance_pct` is not available (e.g., HL did not return a liquidation distance in the position response).
- **Step:**
  1. Trigger stop placement while `liq_distance_pct` is absent; observe the fallback formula used.
- **Expected Result:**
  1. `liq_distance_pct` falls back to `1 / effective_leverage`; `stop_trigger_px` is then computed as `entry_price × (1 + (1/effective_leverage) × 0.70)`. The fallback is used only when the primary value is unavailable — not as the default. (Reference: FR-EXBOT-050.)
- **Priority:** P0

#### TC_037

- **Title:** Verify reduce-only stop market placement confirms on HL and lifecycle transitions to stop_verified then active
- **Pre-condition:**
  1. Bot is in `hedge_post_confirmed` state; `stop_trigger_px` has been computed.
- **Step:**
  1. Allow stop placement to submit the reduce-only stop market order to HL; wait for HL to confirm the order.
- **Expected Result:**
  1. HL confirms the stop market order; `lifecycle_state` transitions from `hedge_post_confirmed` to `stop_placing`, then to `stop_verified`, then to `active` — in that strict order. No state is skipped. `bot_registry.status` is set to `active`. Monitoring jobs (light-check, deep-audit) are scheduled. (Reference: FR-EXBOT-050, FR-EXBOT-003, AC-01.)
- **Priority:** P0

#### TC_038

- **Title:** Verify stop placement failure prevents the bot from reaching active and triggers an operator alert
- **Pre-condition:**
  1. Bot is in `stop_placing` state; HL is mocked to reject or not respond to the stop market order.
- **Step:**
  1. Allow stop placement to fail (HL rejects or times out); observe the resulting lifecycle state.
- **Expected Result:**
  1. `lifecycle_state` does NOT advance to `active`. The bot transitions to `safe_mode` (per INV-STOP invariant: a bot cannot be active without a confirmed stop). An operator alert is sent with the failure reason. Light-check and deep-audit are NOT scheduled. (Reference: FR-EXBOT-050, INV-STOP, AC-06.)
- **Priority:** P0

#### TC_039

- **Title:** Verify the full bot-start sequence traverses all 9 lifecycle states in strict order
- **Pre-condition:**
  1. All external dependencies (KMS, HL, Uniswap V3, Aurora PostgreSQL, SQS) are available and responding normally.
  2. All preflight conditions pass (no active bot, vault balance > 0, margin ≥ 2.0x required, key active, builder fee confirmed, LP sim passes).
- **Step:**
  1. Process a complete `bot-start` job from initial queue message to final `active` state; record each `lifecycle_state` value at each transition point.
- **Expected Result:**
  1. The `lifecycle_state` sequence is exactly: `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`. All 9 states appear in that order; no state is skipped or repeated. (Reference: FR-EXBOT-003, AC-01.)
- **Priority:** P0

#### TC_040

- **Title:** Verify stop_price is less than liquidation_price and maintains at least a 30% safety buffer
- **Pre-condition:**
  1. Bot is in `stop_placing` state; `liquidation_price` and `stop_trigger_px` are both computed.
- **Step:**
  1. Compare `stop_trigger_px` to `liquidation_price` after stop placement completes; verify the safety margin.
- **Expected Result:**
  1. `stop_trigger_px < liquidation_price`. The distance between `stop_trigger_px` and `liquidation_price` is at least 30% of `liq_distance_pct` (stopSafetyFactor = 0.70 means the stop uses only 70% of the liquidation distance, leaving a 30% buffer). Computed with BigDecimal. (Reference: FR-EXBOT-050, AC-11.)
- **Priority:** P0

#### TC_041

- **Title:** Verify light-check and deep-audit monitoring are scheduled after the bot reaches active state
- **Pre-condition:**
  1. Bot has reached `lifecycle_state='active'`.
- **Step:**
  1. Query the scheduling system (e.g., SQS or cron registry) immediately after `active` state is set.
- **Expected Result:**
  1. A light-check job is scheduled per the configured interval (e.g., every N minutes). A deep-audit job is scheduled per its configured interval. Neither job is scheduled before `active` is reached. (Reference: FR-EXBOT-003.)
- **Priority:** P0

#### TC_042

- **Title:** Verify the status API returns active state and hedge summary after the bot reaches active
- **Pre-condition:**
  1. Bot has reached `lifecycle_state='active'`; `hedge_legs` and `positions` rows are fully populated.
- **Step:**
  1. Call the bot status API endpoint for the active bot.
- **Expected Result:**
  1. The API response includes `lifecycle_state='active'`, the LP position summary (tokenId, tick ranges, liquidity), and the hedge summary (short size, entry price, stop price). HTTP 200. No sensitive key material appears in the response. (Reference: FR-EXBOT-003, NFR-EXBOT-006.)
- **Priority:** P0

### IV.2. Integration & State verification — Operation: Stop Placement & Bot Activation

#### TC_043

- **Title:** Verify the bot-start queue message is processed exactly once even when redelivered by SQS
- **Pre-condition:**
  1. A `bot-start` SQS message for a given user is delivered and processed successfully to `active` state.
  2. SQS redelivers the same message (same `message_id`) due to at-least-once delivery semantics.
- **Step:**
  1. Deliver the same `bot-start` message a second time after the bot is already `active`.
- **Expected Result:**
  1. The second delivery hits the UNIQUE constraint on `queue_idempotency.message_id` and exits immediately. No second bot record is created. The existing `active` bot is not affected. (Reference: FR-EXBOT-011, BR-EXBOT-001.)
- **Priority:** P0

#### TC_044

- **Title:** Verify two simultaneous bot-start messages for the same user result in exactly one bot being created
- **Pre-condition:**
  1. Two `bot-start` messages for the same user with different `message_id` values are delivered concurrently to ExBot Lambda.
- **Step:**
  1. Allow both messages to be processed simultaneously; race them through the one-bot policy check.
- **Expected Result:**
  1. The DB-level insert or lock ensures exactly one bot record is created. The second concurrent attempt hits the one-bot policy (`E-EXBOT-001`) or a DB uniqueness constraint and is rejected. No duplicate bot is created. (Reference: FR-EXBOT-001, BR-EXBOT-001.)
- **Priority:** P0

### IV.3. Non-functional (logic) verification — Operation: Stop Placement & Bot Activation

#### TC_045

- **Title:** Verify the agent key is never written to logs while it is decrypted for signing during bot start
- **Pre-condition:**
  1. Bot-start is in the hedge-open phase; Signing Lambda is decrypting the agent key for signing.
- **Step:**
  1. Capture all application logs, CloudWatch logs, and structured logging output during the Signing Lambda execution window.
- **Expected Result:**
  1. No hex-encoded or base64-encoded private key material appears in any log output, error message, or trace during the signing window. Only the agent address (public) and signing metadata are logged. (Reference: NFR-EXBOT-006, AC-08.)
- **Priority:** P0

#### TC_046

- **Title:** Verify all financial values in Aurora PostgreSQL after bot activation are stored as BigDecimal TEXT strings
- **Pre-condition:**
  1. Bot has reached `lifecycle_state='active'`; all financial fields are written: entry_price, stop_trigger_px, targetShortEth, liquidity amounts, tick ranges.
- **Step:**
  1. Query the relevant Aurora PostgreSQL columns (entry_price, stop_trigger_px, lp_liquidity, etc.) and inspect the stored data type and value format.
- **Expected Result:**
  1. All financial columns are stored as TEXT or NUMERIC with full precision — no floating-point IEEE 754 approximation. Example: entry_price stored as "3500.123456789012345678" (not 3500.1234567890124). No `Number()`, `parseFloat()`, or JavaScript float representation appears in any stored value. (Reference: FR-EXBOT-061, AC-11.)
- **Priority:** P0
