# Test Cases Reference (English) — Logic / Backend (No UI)

> Reference test case document for **English-language LOGIC-only projects** (backend / API / bot / worker — no UI).
> Each test case has 6 fields: **TC ID**, **Test Title/Summary**, **Pre-condition**, **Test Steps**, **Expected Result**, **Priority**.
> These are STYLE examples only (showing TC ID format, title phrasing, precondition / step / expected-result layout). Some IDs are non-contiguous — ignore the gaps and follow the writing style.
>
> Writing style every example below follows (see `rules/testcase-instruction-rules.md`):
> - **Meaning first, identifier in parentheses** (Rule 4): lead with a plain sentence; put the status / field / value in `(...)` as evidence — never let the variable be the sentence.
> - **Plain QA vocabulary** (Rule 5): simple, everyday tester words; no academic / rare terms.
> - **No concrete numbers in the body** (Rule 6): describe the boundary in words; put any number only in an `(Example: …)` note at the end of the cell.
> - Every Step is an action + a condition to verify (the tester picks the concrete endpoint / call — no UI object); every Expected Result is an observable system effect (API/RPC response, state transition, D1 row / on-chain value, emitted event, or message / error code). For on-chain operations, state BOTH the on-chain and off-chain effect.

---

## I. Operation: Bot start (preflight)

### I.1. Functional verification — Operation: Bot start (preflight)

#### TC_001

- **Title:** Verify the one-bot policy blocks a second start while a bot is still running
- **Pre-condition:**
  1. The user already has a running ExBot (`status='active'`).
- **Step:**
  1. Start a new bot for the same user while the first bot is still running.
- **Expected Result:**
  1. The start is rejected and no new bot is created (error code `E-EXBOT-001`, message "You already have an active ExBot. Close or wait for the existing bot to finish.", HTTP 409). No new row is added to `bot_registry` / `bots`. (Reference: FR-EXBOT-001, BR-EXBOT-001.)
- **Priority:** P0

#### TC_002

- **Title:** Verify the start is blocked when the user does not have enough HL margin
- **Pre-condition:**
  1. The one-bot policy check passes for the user.
  2. The user's HL margin is below the required margin including its safety buffer. (Example: the rule asks for the required margin plus a 100% buffer; the user has only about the required margin with no buffer.)
- **Step:**
  1. Start a bot when the user's HL margin is below the required-margin-plus-buffer threshold.
- **Expected Result:**
  1. The start is blocked and no bot is created (error code `E-EXBOT-002`, HTTP 400). The message tells the user how much more to deposit to HL. No partial bot row is left in D1. (Reference: FR-EXBOT-002 step 2, FR-EXBOT-061.)
- **Priority:** P0

#### TC_003

- **Title:** Verify the suggested top-up amount is not rounded down when the balance is too low
- **Pre-condition:**
  1. The one-bot policy passes.
  2. The user's HL margin is below the required margin, and the gap is not a whole round number. (Example: required ≈ 700, current ≈ 350 → the user still needs ≈ 350 more.)
- **Step:**
  1. Start a bot when the user's balance is below the required margin by an amount that is not a round number.
- **Expected Result:**
  1. The start is blocked (`E-EXBOT-002`, HTTP 400) and the message shows the exact amount the user still needs to deposit — the suggested amount is not rounded down to a coarser unit, so depositing exactly that amount is enough to pass. (Reference: FR-EXBOT-061 AC.)
- **Priority:** P0

#### TC_004

- **Title:** Verify the start is blocked when the agent key is still waiting for approval
- **Pre-condition:**
  1. The one-bot policy and margin checks pass.
  2. The user's HL agent key is still waiting for approval (`approval_status='pending'`).
- **Step:**
  1. Start a bot while the agent key is still waiting for approval.
- **Expected Result:**
  1. The start is blocked and no bot is created (error code `E-EXBOT-003`, message "Agent key is awaiting approval...", HTTP 400). (Reference: FR-EXBOT-002 step 3, FR-EXBOT-081.)
- **Priority:** P0

### I.2. Integration & State verification — Operation: Bot start (preflight)

#### TC_010

- **Title:** Verify the bot goes through every start step in order and ends up running
- **Pre-condition:**
  1. All five preflight checks pass for the user.
  2. The Hyperliquid and BnzaExVault responses (mocked) are set to succeed.
- **Step:**
  1. Start a bot and let the whole start process run to the end.
  2. Read the bot's stage (`bots.lifecycle_state`) after each saved step.
- **Expected Result:**
  2. The bot moves through every start step in the fixed order with none skipped, and each step is saved before the next one begins, ending in the running state (`bots.status='active'`). On-chain: the LP is minted (`VaultMinted` is emitted) and the HL short plus a reduce-only stop are placed. Off-chain: the `positions` and `hedge_legs` rows are filled in (e.g. `token_id`, `entry_price`, `stop_price`). (Example order: `idle -> preflight -> lp_opening -> lp_opened -> hedge_pre_open -> hedge_post_confirmed -> stop_placing -> stop_verified -> active`.) (Reference: FR-EXBOT-003, flow F-03.)
- **Priority:** P0

#### TC_011

- **Title:** Verify the bot goes into safe mode when the HL short order fails during start
- **Pre-condition:**
  1. The bot has minted the LP and is about to open the hedge (`lifecycle_state='lp_opened'`).
  2. The HL short order (mocked `openShortIoc`) is set to fail.
- **Step:**
  1. Let the start try to open the HL short while the HL order fails.
- **Expected Result:**
  1. The bot stops opening the hedge and switches to safe mode (`lifecycle_state` goes from `hedge_pre_open` to `safe_mode`, `bots.status='safe_mode'`); no stop is placed and the bot does not become active. (Reference: states.md diagram, FR-EXBOT-050.)
- **Priority:** P0

### I.3. Non-functional (logic) verification — Operation: Bot start (preflight)

#### TC_020

- **Title:** Verify the agent key is never written to the logs while it is being used at start
- **Pre-condition:**
  1. The user's agent key is approved and not expired.
- **Step:**
  1. Run the start so the agent key is decrypted for signing, then read the worker logs and any error output.
- **Expected Result:**
  1. The plain agent key and the plain data-encryption key (DEK) do not appear anywhere in the logs or error output; they are used only inside the function and dropped right after. A dump of the `hl_agent_keys` table shows encrypted values only. (Reference: FR-EXBOT-080, NFR-EXBOT-006.)
- **Priority:** P0

---

## II. Operation: Hedge-sync (delta-only)

### II.1. Functional verification — Operation: Hedge-sync (delta-only)

#### TC_030

- **Title:** Verify hedge-sync only adjusts the difference instead of closing and reopening
- **Pre-condition:**
  1. The bot is running with an open hedge (`status='active'`).
  2. The hedge needs a small rebalance because the target short size and the actual short size differ.
- **Step:**
  1. Process one `hedge-sync` message and watch the calls made to Hyperliquid.
  2. Adjust the hedge by only the difference between the target size and the actual size (a small change right at the rebalance threshold).
- **Expected Result:**
  2. Only one adjust call is sent (using a fixed, repeatable order id / `cloid`) — the bot does NOT close the whole position and open a new one. After the order, a check confirms the new size matches the target within tolerance, and the attempt is marked successful only after that check (`rebalance_attempts.status='success'`). (Reference: FR-EXBOT-022, FR-EXBOT-025, BR-EXBOT-004.)
- **Priority:** P0

### II.2. Integration & State verification — Operation: Hedge-sync (delta-only)

#### TC_040

- **Title:** Verify an out-of-date hedge-sync message is skipped without sending any HL order
- **Pre-condition:**
  1. The bot is running.
  2. A queued `hedge-sync` message is older than the bot's current state (its `stateVersion` is lower than the bot's current `bot_runtime_state.state_version`).
- **Step:**
  1. Deliver the out-of-date `hedge-sync` message.
- **Expected Result:**
  1. The worker stops before taking the lock and marks the attempt as skipped (`rebalance_attempts.status='skipped'`); no order is sent to Hyperliquid. (Reference: FR-EXBOT-027.)
- **Priority:** P0

#### TC_041

- **Title:** Verify delivering the same hedge-sync message twice does not act twice
- **Pre-condition:**
  1. A `hedge-sync` message has already been processed once successfully.
- **Step:**
  1. Deliver the same `hedge-sync` message a second time (same `message_id` and same `idempotencyKey`).
- **Expected Result:**
  1. The second delivery stops immediately because the message id was already seen (UNIQUE conflict on `queue_idempotency.message_id`); the hedge was adjusted exactly once, and there is no duplicate success row. (Reference: FR-EXBOT-011, NFR-EXBOT-007.)
- **Priority:** P0

### II.3. Non-functional (logic) verification — Operation: Hedge-sync (delta-only)

#### TC_050

- **Title:** Verify the circuit breaker opens after three hedge-sync failures in a row
- **Pre-condition:**
  1. The circuit breaker is closed (`circuit_breakers.state='closed'`).
  2. Hyperliquid (mocked) is set so hedge-sync fails three times in a row within a day.
- **Step:**
  1. Make hedge-sync fail three times in a row within the same 24-hour window.
- **Expected Result:**
  1. The circuit breaker opens (`state` goes from `closed` to `open`) and stays open for a cooldown before it will retry. While it is open, new hedge-sync is paused but stop monitoring keeps running (a bot whose price is near its stop still gets checked). (Example: cooldown ≈ 1 hour, `reset_at = now + 1h`.) (Reference: FR-EXBOT-040, FR-EXBOT-014.)
- **Priority:** P0

---

## III. Operation: Close bot (user_redeem)

### III.1. Functional verification — Operation: Close bot (user_redeem)

#### TC_060

- **Title:** Verify a user redeem returns the LP's USDC on-chain in the same transaction
- **Pre-condition:**
  1. The bot is running with an open LP position and an open hedge.
- **Step:**
  1. Redeem the LP on-chain for the user (`BnzaExVault.redeem(tokenId)`).
- **Expected Result:**
  1. On-chain: the LP is closed and the LP's share of USDC is returned to the user in the same redeem transaction, and a redemption event is emitted (`RedemptionEvent(botId, redeemTxHash, userAddress)`). Off-chain: a close record is created and moves forward (`close_operations` `kind=user_redeem`, state `lp_closed -> funds_returned`). (Reference: FR-EXBOT-070, flow F-04.)
- **Priority:** P0

### III.2. Integration & State verification — Operation: Close bot (user_redeem)

#### TC_070

- **Title:** Verify the LP money already returned is not taken back when the hedge close fails
- **Pre-condition:**
  1. A user redeem is in progress and the LP's USDC has already been returned on-chain (`close_operations.state='funds_returned'`).
  2. The HL hedge close (mocked `closeShortReduceOnlyIoc`) is set to fail.
- **Step:**
  1. Run the redeem while the HL hedge close fails.
- **Expected Result:**
  1. The close record is marked as having a leftover hedge debt (`state='residual_hl_liability'`) and an alert with the leftover amount is sent to admin; the LP's USDC that was already returned to the user is NOT taken back. If it runs past the time limit, an admin escalation is raised (`E-EXBOT-010`, "LP funds already returned"). (Reference: BR-EXBOT-006, FR-EXBOT-070, NFR-EXBOT-003.)
- **Priority:** P0

### III.3. Non-functional (logic) verification — Operation: Close bot (user_redeem)

#### TC_080

- **Title:** Verify the redeem hedge close finishes within the time limit
- **Pre-condition:**
  1. A redemption event has been picked up and a `user_redeem` message has been queued at top priority.
- **Step:**
  1. Measure the time from picking up the event to the hedge being closed (`close_operations.state='hedge_closed'`).
- **Expected Result:**
  1. The HL hedge close (close the short, cancel the stop, then confirm the position is empty) finishes within the time limit after the event is picked up; going over the limit raises an admin escalation (`E-EXBOT-010`). (Example: time limit ≈ 5 minutes.) (Reference: NFR-EXBOT-003, FR-EXBOT-070.)
- **Priority:** P0
