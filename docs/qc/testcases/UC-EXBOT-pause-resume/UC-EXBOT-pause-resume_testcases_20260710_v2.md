# Test Cases — UC-EXBOT-pause-resume: Pause and Resume Bot

**Total test cases:** 31 (FUNC: 18, INTG: 9, NFR: 4)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** `docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260706_v4.md` (v4, 2026-07-06)
**Output language:** English

---

## Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Happy path pause — status='paused', hedge/LP preserved | TC_001, TC_002 | Covered |
| AC-02 | Happy path resume — status='active', light-check scheduled within 5min | TC_012, TC_013 | Covered |
| AC-03 | SAFE_MODE rejection — pause rejected with E-EXBOT-013 | TC_002 | Covered |
| AC-04 | Idempotent pause — already paused returns success | TC_003 | Covered |
| AC-05 | Idempotent resume — already active returns success | TC_013 | Covered |
| AC-06 | Light-check suppressed in pause — no hedge-sync enqueued | TC_020, TC_021 | Covered |
| AC-07 | Deep-audit continues during pause | TC_023, TC_024 | Covered |
| AC-08 | Audit log records pause action | TC_007 | Covered |
| AC-09 | Audit log records resume action | TC_017 | Covered |
| AC-10 | Hedge position preserved during pause | TC_008 | Covered |
| AC-11 | LP NFT preserved during pause | TC_009 | Covered |

---

## I. Operation: Bot pause

### I.1. Functional verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_001 | Happy path pause — status changes to 'paused', hedge and LP positions preserved | Bot is `status='active'`, `lifecycle_state='active'`, has open hedge position and LP NFT. | 1. Send `POST /api/exbot/pause` with `botId`. 2. Lambda verifies `status='active'` and `lifecycle_state='active'`. 3. Lambda executes conditional UPDATE: `bots.status='paused' WHERE bot_id=X AND status='active'`. 4. Returns HTTP 200 + MSG-SUC-81. | 1. `bots.status='paused'`. 2. `bots.lifecycle_state='active'` (unchanged). 3. `hedge_legs.last_known_hl_short_size` unchanged. 4. `positions.token_id` unchanged. 5. API returns HTTP 200 with message "Bot paused. Hedge and LP are maintained." (Reference: UC §3, FR-EXBOT-005, BR-EXBOT-002.) | P0 |
| TC_002 | Pause request rejected when bot is in safe_mode | Bot is `status='safe_mode'`. | 1. Send `POST /api/exbot/pause` with `botId`. 2. Lambda queries Aurora: `bots.status='safe_mode'`. 3. Lambda skips UPDATE (blocked). 4. Returns HTTP 409 + E-EXBOT-013. | 1. Request rejected. 2. `bots.status` stays `'safe_mode'` (unchanged). 3. API returns HTTP 409 with "Bot is in Safe Mode. You can close the bot instead." (E-EXBOT-013). 4. No audit log entry for failed pause attempt. (Reference: UC §5 A1, FR-EXBOT-050.) | P0 |
| TC_003 | Idempotent pause — already paused bot returns success | Bot is `status='paused'`. | 1. Send `POST /api/exbot/pause` with `botId`. 2. Lambda queries Aurora: `bots.status='paused'`. 3. Conditional UPDATE finds no match (`WHERE status='active'`). 4. Returns HTTP 200 + "Bot already paused. No change needed." | 1. No state change. 2. `bots.updated_at` unchanged (no actual UPDATE). 3. API returns HTTP 200 with "Bot already paused. No change needed." 4. No new audit log entry. (Reference: UC §5 A3, FR-EXBOT-005.) | P0 |
| TC_004 | Pause blocked when lifecycle_state is not 'active' | Bot has `status='active'` but `lifecycle_state='hedge_stopped_cooldown'` or `'lp_rebalancing'`. | 1. Send `POST /api/exbot/pause` with `botId`. 2. Lambda queries Aurora: `bots.lifecycle_state` is non-active. 3. Lambda skips UPDATE. 4. Returns HTTP 409 with error message. | 1. Request rejected. 2. `bots.status='active'` (unchanged). 3. `bots.lifecycle_state` unchanged. 4. API returns HTTP 409. Only `lifecycle_state='active'` can be paused per BA decision (Q7, 2026-07-03). (Reference: UC §2, states.md.) | P1 |
| TC_005 | Concurrent double pause — race condition prevented by conditional UPDATE | Bot is `status='active'`. Two pause requests sent simultaneously. | 1. Terminal 1: Send `POST /api/exbot/pause`. 2. Terminal 2: Send `POST /api/exbot/pause` at same time. 3. Lambda 1 executes conditional UPDATE → MATCH → updates to `'paused'`. 4. Lambda 2 executes conditional UPDATE → NO MATCH → returns idempotent success. | 1. Exactly 1 state change occurs. 2. Request 1 returns "Bot paused. Hedge and LP are maintained." 3. Request 2 returns "Bot already paused. No change needed." 4. Only 1 audit log entry. 5. No partial state, no race condition. (Reference: UC §5 A3, Q3 resolved.) | P0 |
| TC_006 | API response message matches MSG-SUC-81 exactly | Bot is `status='active'`. | 1. Send `POST /api/exbot/pause` with `botId`. 2. Capture API response body. | 1. Response body contains `message: "Bot paused. Hedge and LP are maintained."` exactly matching MSG-SUC-81. 2. No extra spaces, no typos. (Reference: UC §3 step 7, message-list.md, Q9 resolved.) | P1 |

### I.2. Integration & State verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_007 | Audit log records pause action | Bot is `status='active'`. | 1. Send `POST /api/exbot/pause`. 2. Query `audit_log WHERE bot_id=X ORDER BY created_at DESC LIMIT 1`. | 1. Audit log entry exists with `action='Bot paused by investor'`. 2. `bot_id` and `user_wallet_address` correct. 3. `created_at` timestamp matches pause time. (Reference: UC §7 Postconditions.) | P0 |
| TC_008 | Hedge position size unchanged after pause | Bot has open hedge position with recorded size. | 1. Record `hedge_legs.last_known_hl_short_size`. 2. Send `POST /api/exbot/pause`. 3. Read `hedge_legs.last_known_hl_short_size` again. | 1. Hedge leg size exactly the same before and after pause. 2. No HL order submitted during pause operation. (Reference: UC §3 step 5, BR-EXBOT-002.) | P0 |
| TC_009 | LP NFT token ID unchanged after pause | Bot has LP NFT with recorded token ID. | 1. Record `positions.token_id`. 2. Send `POST /api/exbot/pause`. 3. Read `positions.token_id` again. | 1. LP NFT token ID exactly the same before and after pause. 2. No vault transaction submitted during pause operation. (Reference: UC §3 step 6, BR-EXBOT-002.) | P0 |
| TC_010 | Pause operation makes zero calls to Hyperliquid | Monitor set up to track HL API calls. | 1. Start HL API monitoring. 2. Send `POST /api/exbot/pause`. 3. Check HL API logs for bot's pause timeframe. | 1. Zero HL API calls during pause operation. 2. Pause relies solely on Aurora PostgreSQL state. (Reference: UC §3, BR-EXBOT-003.) | P0 |

### I.3. Non-functional (logic) verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_011 | Aurora PostgreSQL stays consistent when Lambda crashes mid-transaction | Bot is `status='active'`. | 1. Send `POST /api/exbot/pause`. 2. Simulate Lambda crash before transaction commits. 3. Query Aurora PostgreSQL. | 1. Aurora PostgreSQL stays at previous consistent state (`bots.status='active'`). 2. No partial or inconsistent status value left in database. (Reference: Q3 resolved.) | P0 |

---

## II. Operation: Bot resume

### II.1. Functional verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_012 | Happy path resume — status changes to 'active', next_light_check_at scheduled | Bot is `status='paused'`. `lifecycle_state` preserved from before pause. | 1. Send `POST /api/exbot/resume` with `botId`. 2. Lambda verifies `bots.status='paused'`. 3. Lambda executes conditional UPDATE: `bots.status='active' WHERE bot_id=X AND status='paused'`. 4. Lambda sets `next_light_check_at=now+5min+jitter(−45s,+45s)`. 5. Lambda enqueues `light-check` message. 6. Returns HTTP 200 + MSG-SUC-82. | 1. `bots.status='active'`. 2. `bots.lifecycle_state='active'` (unchanged). 3. `next_light_check_at` set to now+4:15 to 5:45. 4. `light-check` message enqueued. 5. API returns HTTP 200 with "Bot resumed. Monitoring will resume shortly." (Reference: UC §4, FR-EXBOT-013.) | P0 |
| TC_013 | Idempotent resume — already active bot returns success | Bot is `status='active'`. | 1. Send `POST /api/exbot/resume` with `botId`. 2. Lambda queries Aurora: `bots.status='active'`. 3. Conditional UPDATE finds no match. 4. Returns HTTP 200 + "Bot already active. No change needed." | 1. No state change. 2. Aurora PostgreSQL not modified. 3. API returns HTTP 200 with "Bot already active. No change needed." (Reference: UC §5 A2, FR-EXBOT-005.) | P0 |
| TC_014 | Resume request rejected when bot does not exist | No bot with specified ID exists in Aurora PostgreSQL. | 1. Send `POST /api/exbot/resume` with non-existent `botId`. 2. Lambda queries Aurora: no row found. 3. Returns HTTP 404. | 1. Request rejected. 2. API returns HTTP 404 with error message indicating bot not found. 3. No audit log entry created. (Reference: UC §2.) | P0 |
| TC_015 | Jitter on next_light_check_at within specified range after resume | Bot is `status='paused'` with expired or unset `next_light_check_at`. | 1. Record current time. 2. Send `POST /api/exbot/resume`. 3. Read `bot_runtime_state.next_light_check_at`. 4. Calculate delta from recorded time. | 1. `next_light_check_at` is at least 4 minutes 15 seconds and at most 5 minutes 45 seconds from recorded time. 2. Jitter within range [−45s, +45s]. (Reference: UC §4 step 5, FR-EXBOT-013.) | P0 |
| TC_016 | Resume operation makes zero calls to Hyperliquid | Monitor set up to track HL API calls. | 1. Start HL API monitoring. 2. Send `POST /api/exbot/resume`. 3. Check HL API logs. | 1. Zero HL API calls during resume operation. 2. Light-check message enqueued (separate worker makes no HL calls per BR-EXBOT-003). (Reference: UC §4, BR-EXBOT-003.) | P0 |

### II.2. Integration & State verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_017 | Audit log records resume action | Bot is `status='paused'`. | 1. Send `POST /api/exbot/resume`. 2. Query `audit_log WHERE bot_id=X ORDER BY created_at DESC LIMIT 1`. | 1. Audit log entry exists with `action='Bot resumed by investor'`. 2. `bot_id` and `user_wallet_address` correct. 3. `created_at` timestamp matches resume time. (Reference: UC §7 Postconditions.) | P0 |
| TC_018 | Resumed bot picked up by next bot-scan cycle | Bot is `status='paused'`. | 1. Send `POST /api/exbot/resume`. 2. Trigger bot-scan cycle. 3. Observe bot inclusion and scheduling. | 1. Resumed bot with `status='active'` included in scan. 2. Bot receives `light-check` message as scheduled. (Reference: UC §4 step 5, flows.md F-01.) | P1 |

### II.3. Non-functional (logic) verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_019 | Aurora PostgreSQL stays consistent when Lambda crashes mid-resume | Bot is `status='paused'`. | 1. Send `POST /api/exbot/resume`. 2. Simulate Lambda crash before transaction commits. 3. Query Aurora PostgreSQL. | 1. Aurora PostgreSQL stays at previous consistent state (`bots.status='paused'`). 2. `next_light_check_at` unchanged. 3. No partial state left in database. (Reference: Q3 resolved.) | P0 |

---

## III. Operation: Suppression behavior during pause

### III.1. Functional verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_020 | Light-check worker skips entirely for paused bot | Bot is `status='paused'`. `light-check` message queued. | 1. Deliver `light-check` message to worker. 2. Worker evaluates `bots.status='paused'` at eligibility gate. 3. Worker skips entire light-check. | 1. Worker skips all processing. 2. No drift, range, or funding evaluation run. 3. No `hedge-sync` message enqueued. 4. Worker returns without error. (Reference: UC §6, FR-EXBOT-012.) | P0 |
| TC_021 | Light-check evaluates status as first eligibility gate | Bot transitions from `active` to `paused` while `light-check` message pending. | 1. Deliver pending `light-check` message to worker. 2. Observe evaluation order. | 1. Worker checks `bots.status='paused'` at gate entry BEFORE any other evaluation. 2. Skip happens at gate, not after partial work. (Reference: FR-EXBOT-012.) | P0 |
| TC_022 | Hedge-sync does not run for paused bot | Bot is `status='paused'`. `hedge-sync` message queued. | 1. Deliver `hedge-sync` message to worker. 2. Worker evaluates `bots.status='paused'`. | 1. Worker does not submit any HL order. 2. No `hedge_legs` records modified. 3. Hedge-sync suppressed for paused bots. (Reference: UC §6.) | P0 |
| TC_023 | Deep-audit continues on 6-hour cadence for paused bots (normal mode) | Bot is `status='paused'`. System in normal mode (`circuit_breakers.state='closed'`). 6 hours passed since last deep-audit. | 1. Let scheduled deep-audit run. 2. Deep-audit worker fetches clearinghouseState from HL, verifies hedge size, updates margin status. | 1. Deep-audit runs normally. 2. `hedge_legs.margin_status` updated. 3. No anomaly detected. 4. `bots.status='paused'` unchanged. (Reference: UC §6, FR-EXBOT-016.) | P0 |
| TC_024 | Deep-audit runs on 1-hour cadence for paused bots (high-risk mode) | Bot is `status='paused'`. System in high-risk mode (`circuit_breakers.state!='closed'` or `margin_status IN ('warning','critical')`). 1 hour passed. | 1. Let scheduled deep-audit run. 2. Deep-audit worker runs at 1-hour interval. | 1. Deep-audit runs at 1-hour interval instead of 6-hour. 2. Worker fetches HL state, updates margin status. 3. High-risk cadence independent of pause state. (Reference: FR-EXBOT-016.) | P0 |
| TC_025 | Stop monitoring (price-near-stop-audit) continues for paused bots | Bot is `status='paused'`. Bot has stop price set. ETH mark price near or above stop price. | 1. Run stop trigger evaluation for paused bot. 2. Observe monitoring behavior. | 1. Stop monitoring continues. 2. `price-near-stop-audit` message enqueued when mark price crosses stop price. 3. Stop monitoring never suppressed. (Reference: FR-EXBOT-014.) | P0 |
| TC_026 | Bot transitions to safe_mode from paused when deep-audit detects stuck stop trigger | Bot is `status='paused'`. `hedge_legs.stop_trigger_crossed_at` set and age > 30 minutes. | 1. Let deep-audit run. 2. Deep-audit detects stuck stop trigger. 3. Observe transition. | 1. `bots.status` changes from `'paused'` to `'safe_mode'`. 2. `bots.lifecycle_state` preserved. (Reference: FR-EXBOT-033, states.md.) | P0 |
| TC_027 | Bot transitions to safe_mode from paused when margin becomes critical twice | Bot is `status='paused'`. Previous deep-audit had `margin_status='warning'`. Current deep-audit detects `margin_status='critical'`. | 1. Run deep-audit → detects `critical`. 2. Run next deep-audit cycle while still paused → detects `critical` again. | 1. `bots.status` changes from `'paused'` to `'safe_mode'`. 2. `bots.lifecycle_state` preserved. (Reference: FR-EXBOT-050, FR-EXBOT-060.) | P0 |
| TC_028 | Pause does not affect rebalance_attempts or lp_operations ledger | Bot has existing records in `rebalance_attempts` and `lp_operations`. | 1. Record current count in both tables. 2. Send `POST /api/exbot/pause`. 3. Read tables again. | 1. No new rows inserted. 2. No existing rows modified. 3. All records unchanged. (Reference: UC §3.) | P1 |

### III.2. Integration & State verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_029 | Bot-scan worker includes resumed bot in next scan | Bot is `status='paused'`. Investor resumes bot, `next_light_check_at` set. | 1. Send `POST /api/exbot/resume`. 2. Trigger bot-scan cron. 3. Observe bot inclusion. | 1. Scan worker selects bot with `status='active'`. 2. `light-check` scheduled. 3. `next_light_check_at` updated. (Reference: flows.md F-01.) | P1 |

### III.3. Non-functional (logic) verification

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_030 | Authorization prevents user from pausing another user's bot | Investor A owns bot with `status='active'`. Investor B authenticated with different wallet. | 1. Investor B sends `POST /api/exbot/pause` for Investor A's bot. 2. Lambda verifies wallet ownership. | 1. Request rejected before Aurora PostgreSQL mutation. 2. API returns HTTP 403 or HTTP 404. 3. No audit log entry for unauthorized attempt. (Reference: FR-EXBOT-001.) | P0 |
| TC_031 | Pause operation latency within SLA | Bot is `status='active'`. Latency measurement tool available. | 1. Record time before sending pause request. 2. Send `POST /api/exbot/pause`. 3. Record time when HTTP response received. | 1. Operation completes within target SLA (fast operation, zero HL API calls, zero vault calls). 2. Expected: <100ms (API latency NFR). (Reference: NFR.) | P2 |

---

## Test Cases Summary

| TC | Title | Priority | Type |
|---|---|---|---|
| TC_001 | Happy path pause | P0 | FUNC |
| TC_002 | Pause rejected in safe_mode | P0 | FUNC |
| TC_003 | Idempotent pause | P0 | FUNC |
| TC_004 | Pause blocked by non-active lifecycle | P1 | FUNC |
| TC_005 | Concurrent double pause | P0 | FUNC |
| TC_006 | API message verification | P1 | FUNC |
| TC_007 | Audit log records pause | P0 | INTG |
| TC_008 | Hedge position preserved | P0 | INTG |
| TC_009 | LP NFT preserved | P0 | INTG |
| TC_010 | Zero HL API calls (pause) | P0 | INTG |
| TC_011 | Aurora consistency on crash | P0 | NFR |
| TC_012 | Happy path resume | P0 | FUNC |
| TC_013 | Idempotent resume | P0 | FUNC |
| TC_014 | Resume rejected - bot not exist | P0 | FUNC |
| TC_015 | Jitter timing | P0 | FUNC |
| TC_016 | Zero HL API calls (resume) | P0 | INTG |
| TC_017 | Audit log records resume | P0 | INTG |
| TC_018 | Bot-scan includes resumed bot | P1 | INTG |
| TC_019 | Aurora consistency on crash (resume) | P0 | NFR |
| TC_020 | Light-check skips for paused bot | P0 | FUNC |
| TC_021 | Light-check eligibility gate | P0 | FUNC |
| TC_022 | Hedge-sync suppressed | P0 | FUNC |
| TC_023 | Deep-audit continues (6h) | P0 | FUNC |
| TC_024 | Deep-audit continues (1h, high-risk) | P0 | FUNC |
| TC_025 | Stop monitoring continues | P0 | FUNC |
| TC_026 | SAFE_MODE transition (stuck stop) | P0 | FUNC |
| TC_027 | SAFE_MODE transition (margin critical) | P0 | FUNC |
| TC_028 | Ledger tables unchanged | P1 | FUNC |
| TC_029 | Bot-scan includes resumed bot | P1 | INTG |
| TC_030 | Authorization check | P0 | NFR |
| TC_031 | Latency within SLA | P2 | NFR |

---

*Test Cases — UC-EXBOT-pause-resume (Pause and Resume Bot) — 31 test cases*
*Updated: 2026-07-10*
