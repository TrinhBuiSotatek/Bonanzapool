# Test Cases — UC-EXBOT-deep-audit Periodic Deep Audit

**Total test cases:** 47 (FUNC: 30, INTG: 14, NFR: 3)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** docs/qc/uc-read/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_deep-audit_audited_20260626_v2.md
**Source scenarios (if any):** docs/qc/scenarios/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_deep-audit_scenarios_20260626_v1.md (25 scenarios)
**Output language:** English

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-C1 | Bot status='paused' receives full deep-audit at 6h cadence | TC_008, TC_023 | Covered |
| AC-C2 | Reconcile mismatch triggers SAFE_MODE + E-EXBOT-011 admin alert | TC_002, TC_009 | Covered |
| AC-C3 | effective_leverage > 4.5 triggers SAFE_MODE + admin alert | TC_003 | Covered |
| AC-C4 | liquidation_price within 5% of hlMarkPrice triggers SAFE_MODE | TC_004 | Covered |
| AC-C5 | stop_trigger_crossed_at stuck > 30 min triggers SAFE_MODE | TC_005, TC_025 | Covered |
| AC-C6 | stop_replacing_started_at stuck > 60s triggers SAFE_MODE (secondary) | TC_006 | Covered |
| AC-C7 | Cadence switches to 1h when circuit_breakers.state != 'closed' OR margin_status IN ('warning','critical') | TC_016, TC_017 | Covered |
| AC-C8 | Agent key expiring <= 7d triggers expiry notification | TC_014, TC_027 | Covered |
| AC-C9 | Pending status agent key does NOT trigger notification | TC_015 | Covered |
| AC-C10 | queue_idempotency UNIQUE conflict returns immediately | TC_009 | Covered |
| AC-C11 | margin_status 'warning' sends investor notification | TC_011, TC_018 | Covered |
| AC-C12 | Multiple SAFE_MODE conditions trigger idempotently | TC_019, TC_020 | Covered |

---

## I. Operation: Deep-Audit Cron Trigger & Scope Selection

### I.1. Functional verification — Operation: Deep-Audit Cron Trigger & Scope Selection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_001 | Verify deep-audit fires when next_deep_audit_at is due | The bot is in scope (`status='active'`). The scheduled time has arrived (`bots.next_deep_audit_at <= now`). | 1. Wait for the cron to fire at the scheduled time. 2. Observe whether the deep-audit worker is invoked for this bot. | 1. The deep-audit worker is invoked for the bot and begins processing. (Reference: UC §2; SRS FR-EXBOT-016.) | P1 |
| TC_002 | Verify only active and paused bots are included in deep-audit scope | Multiple bots exist: one with `status='active'`, one with `status='paused'`, and one with `status='error'`. | 1. Trigger the deep-audit cron. 2. Check which bots are picked up for processing. | 1. The bots with `status='active'` and `status='paused'` are included in scope. 2. The bot with `status='error'` is NOT included. (Reference: UC §2 Preconditions; SRS FR-EXBOT-016.) | P1 |
| TC_003 | Verify deep-audit processes bots in normal cadence (6 hours) | The bot is active with no risk conditions. The circuit breaker is closed (`circuit_breakers.state='closed'`). The margin status is healthy (`hedge_legs.margin_status='ok'`). | 1. Complete one deep-audit cycle. 2. Check the next scheduled audit time. | 1. After the audit completes successfully, `bots.next_deep_audit_at` is set to approximately 6 hours from now. (Reference: UC §2; SRS FR-EXBOT-016.) | P1 |

### I.2. Integration & State verification — Operation: Deep-Audit Cron Trigger & Scope Selection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_004 | Verify queue_idempotency prevents duplicate audit execution | A deep-audit message with a specific `message_id` has already been processed successfully. The `queue_idempotency` table has a row with `state='succeeded'` for this `message_id`. | 1. Deliver the same `message_id` again via the queue. | 1. The worker detects the UNIQUE constraint conflict on `message_id` and returns immediately without reprocessing. 2. No duplicate audit is recorded. (Reference: SRS FR-EXBOT-016; AC-C10.) | P0 |
| TC_005 | Verify new message_id creates idempotency row and continues processing | A deep-audit message with a new `message_id` arrives. No existing row in `queue_idempotency` for this `message_id`. | 1. Deliver the deep-audit message with a unique `message_id`. 2. Observe the `queue_idempotency` row creation. | 1. A new row is inserted with `message_id` and `state='started'`. 2. The audit processing continues. (Reference: SRS FR-EXBOT-016.) | P1 |

### I.3. Non-functional (logic) verification — Operation: Deep-Audit Cron Trigger & Scope Selection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_006 | Verify concurrent deep-audit invocations are handled safely | Two deep-audit workers are invoked for the same bot simultaneously. | 1. Deliver two concurrent deep-audit messages for the same bot. | 1. Only one audit completes successfully. 2. The second invocation exits early due to idempotency check or lock contention. (Reference: SRS FR-EXBOT-016.) | P2 |

---

## II. Operation: HL ClearinghouseState Fetch & Rate Limit

### II.1. Functional verification — Operation: HL ClearinghouseState Fetch & Rate Limit

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_007 | Verify clearinghouseState fetch succeeds when HLRateLimitDO allows | The bot is in deep-audit scope (`status IN ('active','paused')`). HLRateLimitDO returns `{allowed: true}` for weight=2. Hyperliquid API is reachable and returns valid clearinghouseState. | 1. Trigger deep-audit and let it reach the clearinghouseState fetch step. 2. Check the fetched data includes actual short size, effective_leverage, and liquidation_price. | 1. The clearinghouseState is fetched successfully. 2. The actual short size, effective_leverage, and liquidation_price are available for subsequent checks. (Reference: UC §3 Step 2; SRS FR-EXBOT-016, FR-EXBOT-091.) | P0 |
| TC_008 | Verify HLRateLimitDO declares weight=2 before clearinghouseState call | The deep-audit worker reaches the clearinghouseState fetch step. | 1. Observe the call made to HLRateLimitDO before fetching clearinghouseState. | 1. The worker declares weight=2 to HLRateLimitDO. 2. The rate limiter's total budget accounting includes this weight. (Reference: SRS FR-EXBOT-091.) | P1 |

### II.2. Integration & State verification — Operation: HL ClearinghouseState Fetch & Rate Limit

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_009 | Verify partial audit when HLRateLimitDO denies clearinghouseState but allows marginSummary | HLRateLimitDO is configured so the first HL call (clearinghouseState) is denied (`{allowed: false}`). The second HL call (marginSummary) is allowed. | 1. Trigger deep-audit and observe the rate-limit behavior. | 1. The clearinghouseState checks (reconcile mismatch, effective_leverage, liquidation_price) are skipped. 2. The marginSummary is fetched and margin_status is updated. 3. The audit completes partially. (Reference: UC §A1; SRS FR-EXBOT-091.) | P1 |
| TC_010 | Verify partial audit when clearinghouseState succeeds but HLRateLimitDO denies marginSummary | HLRateLimitDO allows the first HL call (clearinghouseState). HLRateLimitDO denies the second HL call (marginSummary). | 1. Trigger deep-audit and observe the rate-limit behavior. | 1. The clearinghouseState checks run and complete. 2. The margin_status update is skipped. 3. The audit completes partially. (Reference: UC §A1; SRS FR-EXBOT-091.) | P1 |
| TC_011 | Verify HL API timeout triggers high-risk cadence switch | Hyperliquid API is configured to return a timeout or 5xx error. | 1. Trigger deep-audit when HL API is unreachable. | 1. The HL-dependent steps are skipped. 2. `bots.next_deep_audit_at` is shortened to 1 hour. 3. A "Hyperliquid API unreachable" notification is enqueued. (Reference: UC §A1; SRS FR-EXBOT-016.) | P0 |

---

## III. Operation: Reconcile Mismatch Detection

### III.1. Functional verification — Operation: Reconcile Mismatch Detection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_012 | Verify SAFE_MODE triggers when actual short size differs from last_known_hl_short_size | The bot is active with a hedge leg (`status='active'`, `hedge_legs` exists). `hedge_legs.last_known_hl_short_size` is set to a specific value. The actual short size on Hyperliquid is different from the recorded value. | 1. Trigger deep-audit to fetch the actual clearinghouseState. 2. Compare the actual short size with `last_known_hl_short_size`. | 1. A mismatch is detected. 2. The bot's status changes to `safe_mode` (`bots.status='safe_mode'`). 3. The mismatch is recorded in D1. 4. An admin notification with message E-EXBOT-011 is enqueued. (Reference: UC §A3; SRS FR-EXBOT-050; AC-C2.) | P0 |
| TC_013 | Verify no SAFE_MODE when actual short size matches last_known_hl_short_size | The bot is active with a hedge leg. `hedge_legs.last_known_hl_short_size` matches the actual short size on Hyperliquid. | 1. Trigger deep-audit and observe the reconcile check. | 1. The sizes match. 2. No SAFE_MODE is triggered. 3. Audit continues to the next check. (Reference: UC §3 Step 3; SRS FR-EXBOT-050.) | P1 |

### III.2. Integration & State verification — Operation: Reconcile Mismatch Detection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_014 | Verify source of truth is HL actual for reconcile mismatch detection | A bot has `hedge_legs.last_known_hl_short_size` recorded. The actual on-chain position size differs (due to a partial fill or failed sync). | 1. Trigger deep-audit to reconcile. | 1. The actual on-chain size from HL is treated as the source of truth. 2. If the D1 value differs, SAFE_MODE is triggered with the delta recorded. (Reference: SRS FR-EXBOT-016; §F.4 Integration point.) | P1 |

---

## IV. Operation: effective_leverage & Liquidation Price Checks

### IV.1. Functional verification — Operation: effective_leverage & Liquidation Price Checks

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_015 | Verify SAFE_MODE triggers when effective_leverage exceeds 4.5 | The bot is active. The clearinghouseState returns `effective_leverage` greater than 4.5. | 1. Trigger deep-audit with high effective_leverage. | 1. SAFE_MODE is triggered (`bots.status='safe_mode'`). 2. An admin alert with the effective_leverage value is enqueued. (Reference: FR-EXBOT-050; US-010 AC-010-4; AC-C3.) | P0 |
| TC_016 | Verify no SAFE_MODE when effective_leverage is at or below 4.5 | The bot is active. The clearinghouseState returns `effective_leverage` at or below 4.5. | 1. Trigger deep-audit with normal effective_leverage. | 1. No SAFE_MODE is triggered. 2. Audit continues to the next check. (Reference: FR-EXBOT-050; US-010 AC-4.) | P1 |
| TC_017 | Verify SAFE_MODE triggers when liquidation_price is within 5% of hlMarkPrice | The bot is active. The clearinghouseState shows `liquidation_price` is within 5% of the current `hlMarkPrice`. | 1. Trigger deep-audit with liquidation price near market price. | 1. SAFE_MODE is triggered. (Reference: FR-EXBOT-050; AC-C4.) | P0 |
| TC_018 | Verify no SAFE_MODE when liquidation_price is outside 5% of hlMarkPrice | The bot is active. The clearinghouseState shows `liquidation_price` is safely outside 5% of `hlMarkPrice`. | 1. Trigger deep-audit with safe liquidation distance. | 1. No SAFE_MODE is triggered. 2. Audit continues to the next check. (Reference: FR-EXBOT-050.) | P1 |

### IV.2. Integration & State verification — Operation: effective_leverage & Liquidation Price Checks

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_019 | Verify all three SAFE_MODE conditions are checked independently in same cycle | The bot has multiple risk conditions: reconcile mismatch AND high effective_leverage AND near-liquidation. | 1. Trigger deep-audit with all three conditions true. | 1. All three conditions are checked sequentially. 2. SAFE_MODE is triggered (idempotently) for each condition. 3. The audit continues to remaining checks after each SAFE_MODE entry. (Reference: FR-EXBOT-050; AC-C12.) | P1 |

---

## V. Operation: Stuck Stop Marker Detection

### V.1. Functional verification — Operation: Stuck Stop Marker Detection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_020 | Verify SAFE_MODE triggers when stop_trigger_crossed_at is stuck for more than 30 minutes | The bot has `stop_trigger_crossed_at` set to a timestamp. The elapsed time since `stop_trigger_crossed_at` exceeds 30 minutes. | 1. Trigger deep-audit and observe the stuck marker check. | 1. SAFE_MODE is triggered (`bots.status='safe_mode'`). 2. An admin escalation notification is enqueued with the reason "stop_trigger_crossed_at stuck > 30min" and the timestamp. (Reference: UC §A4; SRS FR-EXBOT-033; BR-EXBOT-005; AC-C5.) | P0 |
| TC_021 | Verify SAFE_MODE triggers when stop_replacing_started_at is stuck for more than 60 seconds (secondary backstop) | The bot has `stop_replacing_started_at` set to a timestamp. The elapsed time since `stop_replacing_started_at` exceeds 60 seconds. | 1. Trigger deep-audit and observe the secondary stuck marker check. | 1. SAFE_MODE is triggered as the secondary backstop. 2. An admin escalation notification is enqueued with the reason "stop_replacing_started_at stuck > 60s". (Reference: UC §A4; SRS FR-EXBOT-033; AC-C6.) | P0 |
| TC_022 | Verify no SAFE_MODE when stop_trigger_crossed_at is not stuck | The bot has `stop_trigger_crossed_at` set to a recent timestamp (within 30 minutes). | 1. Trigger deep-audit and observe the stuck marker check. | 1. No stuck condition is detected. 2. No SAFE_MODE is triggered. 3. Audit continues. (Reference: UC §3 Step 8; SRS FR-EXBOT-033.) | P1 |
| TC_023 | Verify no SAFE_MODE when stop_replacing_started_at is not stuck | The bot has `stop_replacing_started_at` set to a recent timestamp (within 60 seconds). | 1. Trigger deep-audit and observe the secondary stuck marker check. | 1. No stuck condition is detected. 2. No SAFE_MODE is triggered. 3. Audit continues. (Reference: UC §3 Step 9; SRS FR-EXBOT-033.) | P1 |
| TC_024 | Verify stop_trigger_crossed_at write-once guard is respected by deep-audit | The bot has `stop_trigger_crossed_at` already set from a previous light-check pass. | 1. Trigger deep-audit and observe whether deep-audit attempts to overwrite the timestamp. | 1. The timestamp is NOT overwritten by deep-audit (write-once guard, BR-EXBOT-005). 2. Stuck detection uses the original timestamp correctly. (Reference: BR-EXBOT-005; FR-EXBOT-033.) | P1 |
| TC_025 | Verify bot with status='paused' receives full deep-audit including stuck stop marker detection | A bot with `status='paused'` has `stop_trigger_crossed_at` stuck for more than 30 minutes. | 1. Trigger deep-audit for the paused bot. | 1. The stuck marker check runs fully. 2. SAFE_MODE is triggered if the condition is met. (Reference: UC §A2; SRS FR-EXBOT-016; AC-C1.) | P1 |

### V.2. Integration & State verification — Operation: Stuck Stop Marker Detection

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_026 | Verify both stuck checks run in sequence and independently trigger SAFE_MODE | The bot has both `stop_trigger_crossed_at` stuck > 30 min AND `stop_replacing_started_at` stuck > 60s. | 1. Trigger deep-audit and observe both stuck checks. | 1. Both conditions are checked sequentially. 2. SAFE_MODE may be triggered twice but remains idempotent. (Reference: UC §3 Steps 8-9; FR-EXBOT-033.) | P1 |

---

## VI. Operation: HL marginSummary Fetch & Margin Status Update

### VI.1. Functional verification — Operation: HL marginSummary Fetch & Margin Status Update

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_027 | Verify margin_status updates to 'ok' when marginUsage is below 0.55 | The bot is active. The HL marginSummary returns `marginUsage` below 0.55. | 1. Trigger deep-audit to fetch fresh marginSummary. 2. Check the updated `hedge_legs.margin_status`. | 1. `hedge_legs.margin_status` is updated to 'ok'. 2. No notification is sent. (Reference: SRS FR-EXBOT-060.) | P1 |
| TC_028 | Verify margin_status updates to 'warning' and investor notification when marginUsage is between 0.55 and 0.75 | The bot is active. The HL marginSummary returns `marginUsage` between 0.55 and 0.75. | 1. Trigger deep-audit with warning-level margin. | 1. `hedge_legs.margin_status` is updated to 'warning'. 2. A notification is enqueued to the investor: "Margin warning for your ExBot. Consider depositing additional margin to HL." (Reference: SRS FR-EXBOT-060; US-010 AC-010-1; AC-C11.) | P0 |
| TC_029 | Verify margin_status updates to 'critical' on first critical reading without SAFE_MODE | The bot is active with `margin_status='ok'`. The HL marginSummary returns `marginUsage` at or above 0.75 (first critical reading). | 1. Trigger deep-audit with critical margin. | 1. `hedge_legs.margin_status` is updated to 'critical'. 2. No SAFE_MODE is triggered on this first critical reading alone. (Reference: SRS FR-EXBOT-060; US-010 AC-010-2.) | P1 |
| TC_030 | Verify SAFE_MODE triggers on second consecutive critical margin reading | The bot already has `margin_status='critical'` from the previous deep-audit. Current deep-audit reads `marginUsage` at or above 0.75 (second consecutive critical). | 1. Trigger deep-audit with second consecutive critical margin. | 1. SAFE_MODE is triggered. 2. An investor and admin alert is sent: "Bot entered Safe Mode — Margin critical. Please deposit additional margin to HL." (Reference: FR-EXBOT-050; US-010 AC-010-2.) | P0 |
| TC_031 | Verify boundary at marginUsage exactly 0.55 triggers warning status | The bot is active. The HL marginSummary returns `marginUsage` exactly at the boundary (0.55). (Example: marginUsage = 0.550000.) | 1. Trigger deep-audit with marginUsage at exactly 0.55. | 1. `hedge_legs.margin_status` is updated to 'warning'. (Reference: SRS FR-EXBOT-060; OQ-EXBOT-06.) | P2 |
| TC_032 | Verify boundary at marginUsage exactly 0.75 triggers critical status | The bot is active. The HL marginSummary returns `marginUsage` exactly at the boundary (0.75). (Example: marginUsage = 0.750000.) | 1. Trigger deep-audit with marginUsage at exactly 0.75. | 1. `hedge_legs.margin_status` is updated to 'critical'. (Reference: SRS FR-EXBOT-060; OQ-EXBOT-06.) | P2 |

### VI.2. Integration & State verification — Operation: HL marginSummary Fetch & Margin Status Update

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_033 | Verify margin_status update timing respects 6-hour staleness in normal mode | The bot is in normal cadence mode (6 hours between deep-audit). The margin status may become stale between audit cycles. | 1. Verify that margin_status is only updated during deep-audit and hedge-sync (not light-check). | 1. Between deep-audit cycles, margin_status may be stale for up to 6 hours. 2. Light-check does not update margin_status (reads from D1). (Reference: SRS FR-EXBOT-060, FR-EXBOT-016.) | P2 |

---

## VII. Operation: Agent Key Expiry Check

### VII.1. Functional verification — Operation: Agent Key Expiry Check

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_034 | Verify expiry notification triggers when approved agent key expires within 7 days | The bot is active with an approved agent key. The agent key's `expires_at` is within 7 days from now. The key's `approval_status='approved'`. | 1. Trigger deep-audit and observe the agent key expiry check. | 1. An expiry notification is enqueued: "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." (Reference: UC §3 Step 7; SRS FR-EXBOT-083; AC-C8.) | P0 |
| TC_035 | Verify no notification when agent key is pending approval | The bot has an agent key with `approval_status='pending'`. The key's `expires_at` is within 7 days. | 1. Trigger deep-audit and observe the agent key expiry check. | 1. No expiry notification is sent for the pending key. (Reference: SRS FR-EXBOT-083; AC-C9.) | P1 |
| TC_036 | Verify no notification when approved agent key expires beyond 7 days | The bot has an approved agent key. The key's `expires_at` is more than 7 days from now. | 1. Trigger deep-audit and observe the agent key expiry check. | 1. No expiry notification is sent. (Reference: SRS FR-EXBOT-083.) | P1 |

### VII.2. Integration & State verification — Operation: Agent Key Expiry Check

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_037 | Verify only approved keys are checked for expiry | The bot has multiple agent keys: one approved (near expiry), one revoked, one pending. | 1. Trigger deep-audit and observe which keys are checked. | 1. Only the key with `approval_status='approved'` is checked for expiry. 2. Revoked and pending keys are skipped. (Reference: SRS FR-EXBOT-083; §F.4 Integration point.) | P1 |

---

## VIII. Operation: SAFE_MODE Entry & Recovery

### VIII.1. Functional verification — Operation: SAFE_MODE Entry & Recovery

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_038 | Verify multiple SAFE_MODE conditions trigger idempotently in same cycle | Multiple SAFE_MODE conditions are true in the same deep-audit cycle (e.g., reconcile mismatch AND stop_trigger stuck). | 1. Trigger deep-audit with multiple conditions true. | 1. SAFE_MODE is triggered for each condition. 2. The system handles this idempotently (no duplicate state changes). 3. Audit continues to remaining checks. (Reference: SRS FR-EXBOT-050; AC-C12.) | P1 |

### VIII.2. Integration & State verification — Operation: SAFE_MODE Entry & Recovery

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_039 | Verify deep-audit can run when bot is already in safe_mode (HL recovered) | The bot is in `safe_mode` (`bots.status='safe_mode'`). Hyperliquid is now reachable and conditions have resolved. | 1. Trigger deep-audit for the safe_mode bot. | 1. Deep-audit runs and completes successfully. 2. SAFE_MODE is not re-triggered if conditions have resolved. 3. `last_deep_audit_at` is updated. (Reference: SRS FR-EXBOT-050; UC §F.4 Integration point.) | P1 |

### VIII.3. Non-functional (logic) verification — Operation: SAFE_MODE Entry & Recovery

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_040 | Verify deep-audit can run while bot is in safe_mode but hedge-sync and LP operations are blocked | The bot is in `safe_mode`. | 1. Attempt to run deep-audit. 2. Attempt to run hedge-sync or LP rebalance operations. | 1. Deep-audit runs successfully for safe_mode bots. 2. Hedge-sync and LP operations are blocked. (Reference: SRS FR-EXBOT-050.) | P2 |

---

## IX. Operation: Cadence Management

### IX.1. Functional verification — Operation: Cadence Management

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_041 | Verify cadence switches to 1 hour when circuit breaker is open | The bot is active. The circuit breaker transitions to `state != 'closed'` (e.g., 'open'). | 1. Trigger deep-audit and observe the cadence recalculation. | 1. After the audit, `bots.next_deep_audit_at` is set to approximately 1 hour from now. (Reference: UC §2; SRS FR-EXBOT-016; AC-C7.) | P1 |
| TC_042 | Verify cadence switches to 1 hour when margin_status becomes 'warning' | The bot is active with `margin_status='warning'`. | 1. Trigger deep-audit and observe the cadence recalculation. | 1. After the audit, `bots.next_deep_audit_at` is set to approximately 1 hour from now. (Reference: UC §2; SRS FR-EXBOT-016; AC-C7.) | P1 |
| TC_043 | Verify cadence switches to 1 hour when margin_status becomes 'critical' | The bot is active with `margin_status='critical'`. | 1. Trigger deep-audit and observe the cadence recalculation. | 1. After the audit, `bots.next_deep_audit_at` is set to approximately 1 hour from now. (Reference: UC §2; SRS FR-EXBOT-016; AC-C7.) | P1 |

### IX.2. Integration & State verification — Operation: Cadence Management

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_044 | Verify cadence reverts to 6 hours when high-risk condition resolves | The bot was in high-risk mode (circuit open OR margin warning/critical). The condition has now resolved (circuit closed, margin OK). | 1. Trigger deep-audit with no high-risk conditions. | 1. After the audit, `bots.next_deep_audit_at` is set to approximately 6 hours from now (normal cadence restored). (Reference: UC §2; SRS FR-EXBOT-016.) | P2 |

---

## X. Operation: Audit Completion & Timestamp Update

### X.1. Functional verification — Operation: Audit Completion & Timestamp Update

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_045 | Verify last_deep_audit_at is updated after successful audit | The bot is active. Deep-audit completes successfully with no issues detected. | 1. Complete a full deep-audit cycle. 2. Check `bot_runtime_state.last_deep_audit_at`. | 1. `bot_runtime_state.last_deep_audit_at` is set to the current timestamp. 2. `queue_idempotency.state` is updated to 'succeeded'. (Reference: UC §3 Step 8; erd.md.) | P1 |

### X.2. Integration & State verification — Operation: Audit Completion & Timestamp Update

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_046 | Verify audit completion updates all required state after partial audit (HL unreachable) | Deep-audit runs with HL unreachable (A1 path). HL-dependent steps are skipped. | 1. Complete the partial audit. 2. Check which states are updated. | 1. `bot_runtime_state.last_deep_audit_at` is still updated. 2. `queue_idempotency.state` is updated. 3. `bots.next_deep_audit_at` is set to 1 hour (high-risk cadence). 4. Notification about HL unreachable is enqueued. (Reference: UC §A1.) | P1 |

### X.3. Non-functional (logic) verification — Operation: Audit Completion & Timestamp Update

| TC ID | Test Title/Summary of test cases | Pre-conditions | Step | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_047 | Verify every deep-audit cycle produces an audit record for accountability | Deep-audit is triggered. | 1. Complete the audit cycle and check the audit trail. | 1. An audit record is written with the timestamp, bot_id, and result (success/partial/SAFE_MODE). 2. No audit cycle completes without a traceable record. (Reference: NFR-EXBOT-011.) | P2 |

---

## ⚠️ Out-of-Scope Flags

| Area | Reason | Recommended Action |
|---|---|---|
| SAFE_MODE auto-recovery flow | UC scope: only trigger, not recovery | Defer to SAFE_MODE recovery UC |
| bot_safe_close initiation from SAFE_MODE | UC scope: SAFE_MODE is a trigger condition only | Defer to uc-bot-safe-close |
| Margin thresholds 0.55/0.75 finalization | Pending OQ-EXBOT-06 (zen backtest) | Wait for zen to finalize thresholds; boundary TCs (TC_031, TC_032) are structure-ready |
| Performance/scale test (10k bots) | NFR: not functional test scope | Defer to performance team |
| Security audit of AES-256-GCM key encryption | NFR: beyond functional test scope | Defer to security team |
| UI/mobile/desktop testing | EXBOT is backend-only | Not applicable |
