# Test Cases — UC-EXBOT-pause-resume: Pause and Resume Bot

**Total test cases:** 31 (FUNC: 18, INTG: 9, NFR: 4)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** `docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260706_v4.md` (v4, 2026-07-06)
**Source scenarios:** `docs/qc/scenarios/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_scenarios_20260706_v2.md` (v2, 2026-07-06)
**Output language:** English

## Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Happy path pause — status='paused', hedge/LP preserved | TC_001, TC_002 | Covered |
| AC-02 | Happy path resume — status='active', light-check scheduled within 5min | TC_003, TC_004 | Covered |
| AC-03 | SAFE_MODE rejection — pause rejected with E-EXBOT-013 | TC_005 | Covered |
| AC-04 | Idempotent pause — already paused returns success | TC_006 | Covered |
| AC-05 | Idempotent resume — already active returns success | TC_007 | Covered |
| AC-06 | Light-check suppressed in pause — no hedge-sync enqueued | TC_008, TC_015 | Covered |
| AC-07 | Deep-audit continues during pause | TC_009, TC_010 | Covered |
| AC-08 | Audit log records pause action | TC_011 | Covered |
| AC-09 | Audit log records resume action | TC_012 | Covered |
| AC-10 | Hedge position preserved during pause | TC_002, TC_013 | Covered |
| AC-11 | LP NFT preserved during pause | TC_002, TC_014 | Covered |

---

## I. Operation: Bot pause

### I.1. Functional verification — Operation: Bot pause

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_001 | Verify the happy-path pause succeeds and preserves hedge and LP positions | The bot is running with status='active' and lifecycle_state='active'. The bot has an open hedge position and an LP NFT. | Send a pause request for the bot. | The status changes to 'paused' in Aurora PostgreSQL. The lifecycle_state stays unchanged. The hedge leg size and LP NFT token ID stay unchanged. The API returns HTTP 200 with the message matching MSG-SUC-81. (Reference: UC §3, FR-EXBOT-005, BR-EXBOT-002.) | P0 |
| TC_002 | Verify the pause request is rejected when the bot is in safe_mode | The bot is in safe_mode (status='safe_mode'). | Send a pause request for the bot in safe_mode. | The request is rejected and the status stays 'safe_mode'. The API returns HTTP 409 with the message "Bot is in Safe Mode. You can close the bot instead." (E-EXBOT-013). (Reference: UC §5 A1, FR-EXBOT-050.) | P0 |
| TC_003 | Verify the pause request is idempotent when the bot is already paused | The bot is already paused (status='paused'). | Send another pause request for the already-paused bot. | The request succeeds with no state change (idempotent). The API returns HTTP 200 with the message "Bot already paused. No change needed." Aurora PostgreSQL is not modified by the second request. (Reference: UC §5 A3, FR-EXBOT-005.) | P0 |
| TC_004 | Verify the pause is blocked when the lifecycle_state is not 'active' | The bot has status='active' but lifecycle_state is 'hedge_stopped_cooldown' or 'lp_rebalancing'. | Send a pause request for the bot with the non-active lifecycle_state. | The request is rejected and the status stays 'active'. The API returns HTTP 409 with an error message. Only lifecycle_state='active' can be paused per BA decision (Q7, 2026-07-03). (Reference: UC §2, states.md.) | P1 |
| TC_005 | Verify the pause does not allow a second concurrent pause to double-update | The bot is running (status='active'). | Send two pause requests at the same time for the same bot. | Exactly one state change occurs. The first request wins and changes status to 'paused'. The second request finds status='paused' and returns the idempotent success message. No error, no partial state, no race condition. (Reference: UC §5 A3, Q3 resolved.) | P0 |
| TC_006 | Verify the API response body contains the correct success message code | The bot is running (status='active'). | Send a pause request and capture the API response body. | The response body contains the message "Bot paused. Hedge and LP are maintained." matching MSG-SUC-81 from message-list.md §MSG-EXBOT. (Reference: UC §3 step 7, message-list.md, Q9 resolved.) | P1 |

### I.2. Integration & State verification — Operation: Bot pause

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_007 | Verify the audit log records the pause action | The bot is running (status='active'). | Send a pause request for the bot. Read the audit log for the latest entry. | The audit log contains an entry with the action "Bot paused by investor", the bot ID, the user ID, and a timestamp matching the pause time. (Reference: UC §7 Postconditions.) | P0 |
| TC_008 | Verify the hedge position size is unchanged after pause | The bot has an open hedge position with a recorded size. | Record the current hedge leg size. Send a pause request. Read the hedge leg size again. | The hedge leg size is exactly the same before and after pause. No HL order is submitted during the pause operation. (Reference: UC §3 step 5, BR-EXBOT-002.) | P0 |
| TC_009 | Verify the LP NFT token ID is unchanged after pause | The bot has an LP NFT with a recorded token ID. | Record the current LP NFT token ID. Send a pause request. Read the token ID again. | The LP NFT token ID is exactly the same before and after pause. No vault transaction is submitted during the pause operation. (Reference: UC §3 step 6, BR-EXBOT-002.) | P0 |
| TC_010 | Verify the pause operation makes zero calls to Hyperliquid | A monitor is set up to track HL API calls. | Send a pause request while tracking HL API calls. | Zero HL API calls are made during the pause operation. The pause relies solely on Aurora PostgreSQL state. (Reference: UC §3, BR-EXBOT-003.) | P0 |

### I.3. Non-functional (logic) verification — Operation: Bot pause

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_011 | Verify Aurora PostgreSQL stays consistent when the Lambda crashes mid-transaction | The bot is running (status='active'). | Send a pause request but simulate a Lambda crash before the transaction commits. | Aurora PostgreSQL stays in the previous consistent state (status='active'). No partial or inconsistent status value is left in the database. (Reference: Q3 resolved.) | P0 |

---

## II. Operation: Bot resume

### II.1. Functional verification — Operation: Bot resume

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_012 | Verify the happy-path resume succeeds and schedules the next light-check | The bot is paused (status='paused'). The lifecycle_state is preserved from before the pause. | Send a resume request for the bot. | The status changes back to 'active' in Aurora PostgreSQL. The lifecycle_state stays unchanged. The next_light_check_at is set to now plus 5 minutes plus random jitter of minus 45 to plus 45 seconds. A light-check message is enqueued. The API returns HTTP 200 with MSG-SUC-82. (Reference: UC §4, FR-EXBOT-013.) | P0 |
| TC_013 | Verify the resume request is idempotent when the bot is already active | The bot is already active (status='active'). | Send a resume request for the already-active bot. | The request succeeds with no state change (idempotent). The API returns HTTP 200 with "Bot already active. No change needed." Aurora PostgreSQL is not modified. (Reference: UC §5 A2, FR-EXBOT-005.) | P0 |
| TC_014 | Verify the resume request is rejected when the bot does not exist | No bot with the specified ID exists in Aurora PostgreSQL. | Send a resume request with a non-existent bot ID. | The request is rejected. The API returns HTTP 404 with an error message indicating the bot was not found. (Reference: UC §2.) | P0 |
| TC_015 | Verify the jitter on next_light_check_at is within the specified range after resume | The bot is paused with an expired or unset next_light_check_at. | Record the current time. Send a resume request. Read the next_light_check_at value. | The next_light_check_at is set to a time that is at least 4 minutes 15 seconds and at most 5 minutes 45 seconds from the recorded time. (Reference: UC §4 step 5, FR-EXBOT-013.) | P0 |
| TC_016 | Verify the resume operation makes zero calls to Hyperliquid | A monitor is set up to track HL API calls. | Send a resume request while tracking HL API calls. | Zero HL API calls are made during the resume operation. The light-check message is enqueued, but light-check itself makes no HL calls per BR-EXBOT-003. (Reference: UC §4, BR-EXBOT-003.) | P0 |

### II.2. Integration & State verification — Operation: Bot resume

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_017 | Verify the audit log records the resume action | The bot is paused (status='paused'). | Send a resume request for the bot. Read the audit log for the latest entry. | The audit log contains an entry with the action "Bot resumed by investor", the bot ID, the user ID, and a timestamp matching the resume time. (Reference: UC §7 Postconditions.) | P0 |
| TC_018 | Verify the resumed bot is picked up by the next bot-scan cycle | The bot is paused. | Send a resume request for the bot. Trigger a bot-scan cycle. | The resumed bot with status='active' is included in the scan and receives a light-check message as scheduled. (Reference: UC §4 step 5, flows.md F-01.) | P1 |

### II.3. Non-functional (logic) verification — Operation: Bot resume

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_019 | Verify Aurora PostgreSQL stays consistent when the Lambda crashes mid-resume | The bot is paused (status='paused'). | Send a resume request but simulate a Lambda crash before the transaction commits. | Aurora PostgreSQL stays in the previous consistent state (status='paused'). No partial or inconsistent status value is left in the database. (Reference: Q3 resolved.) | P0 |

---

## III. Operation: Suppression behavior during pause

### III.1. Functional verification — Operation: Suppression behavior during pause

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_020 | Verify the light-check worker skips entirely for a paused bot | The bot is paused (status='paused'). A light-check message is queued for this bot. | Deliver the light-check message to the worker. | The worker skips the entire light-check. No drift, range, or funding evaluation is run. No hedge-sync message is enqueued. The worker returns without error. (Reference: UC §6, FR-EXBOT-012.) | P0 |
| TC_021 | Verify the light-check worker evaluates status as the first eligibility gate | A bot transitions from active to paused while a light-check message is pending. | Deliver the pending light-check message to the worker. | The worker checks status='paused' at the eligibility gate before any other evaluation. The skip happens at the gate entry, not after partial work. (Reference: FR-EXBOT-012.) | P0 |
| TC_022 | Verify hedge-sync does not run for a paused bot | The bot is paused (status='paused'). A hedge-sync message is queued for this bot. | Deliver the hedge-sync message to the worker. | The worker does not submit any HL order. No hedge_legs records are modified. Hedge-sync is suppressed for paused bots. (Reference: UC §6.) | P0 |
| TC_023 | Verify deep-audit continues on the normal 6-hour cadence for paused bots | The bot is paused. The system is in normal mode. Six hours have passed since the last deep-audit. | Let the scheduled deep-audit run. | Deep-audit fetches the clearinghouse state from HL, verifies the hedge size matches the last known value, and updates the margin status. No anomaly is detected. (Reference: UC §6, FR-EXBOT-016.) | P0 |
| TC_024 | Verify deep-audit runs on the 1-hour high-risk cadence for paused bots when the system is in high-risk mode | The bot is paused. The system is in high-risk mode. One hour has passed since the last deep-audit. | Let the scheduled deep-audit run. | Deep-audit runs at the 1-hour interval instead of the normal 6-hour interval. The worker fetches HL state and updates margin status. (Reference: FR-EXBOT-016.) | P0 |
| TC_025 | Verify stop monitoring (price-near-stop-audit) continues for paused bots | The bot is paused. The bot has a stop price set. The ETH mark price is near or above the stop price. | Run the stop trigger evaluation for the paused bot. | Even though light-check is skipped for paused bots, stop monitoring continues. A price-near-stop-audit message is enqueued when the mark price crosses the stop price. Stop monitoring is never suppressed. (Reference: FR-EXBOT-014.) | P0 |
| TC_026 | Verify the bot transitions to safe_mode from the paused state when deep-audit detects a stuck stop trigger | The bot is paused. The stop_trigger_crossed_at timestamp is set and is older than 30 minutes. | Let deep-audit run and detect the stuck stop trigger. | The status changes from 'paused' to 'safe_mode'. The lifecycle_state stays at its pre-pause value. (Reference: FR-EXBOT-033, states.md.) | P0 |
| TC_027 | Verify the bot transitions to safe_mode from the paused state when margin becomes critical twice | The bot is paused. The margin status was 'warning' in the previous deep-audit. | Run deep-audit and detect margin_status='critical'. Run the next deep-audit cycle while still paused and detect margin_status='critical' again. | The status changes from 'paused' to 'safe_mode'. The lifecycle_state is preserved. (Reference: FR-EXBOT-050, FR-EXBOT-060.) | P0 |
| TC_028 | Verify the pause does not affect the rebalance_attempts or lp_operations ledger | The bot has existing records in rebalance_attempts and lp_operations tables. | Record the current count and values in rebalance_attempts and lp_operations. Send a pause request. Read the tables again. | No new rows are inserted and no existing rows are modified in rebalance_attempts or lp_operations. All records are unchanged. (Reference: UC §3.) | P1 |

### III.2. Integration & State verification — Operation: Suppression behavior during pause

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_029 | Verify the bot-scan worker includes the resumed bot in the next scan | The bot is paused. The investor resumes the bot and the next_light_check_at is set. | Trigger the bot-scan cron. | The scan worker selects the bot with status='active' and schedules a light-check. The next_light_check_at is updated. (Reference: flows.md F-01.) | P1 |

### III.3. Non-functional (logic) verification — Operation: Suppression behavior during pause

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_030 | Verify the authorization prevents a user from pausing another user's bot | Investor A owns a bot with status='active'. Investor B is authenticated with a different wallet address. | Have Investor B send a pause request for Investor A's bot. | The request is rejected before any Aurora PostgreSQL mutation. The API returns HTTP 403 or HTTP 404. No audit log entry is written for the unauthorized attempt. (Reference: FR-EXBOT-001.) | P0 |
| TC_031 | Verify the pause operation latency is within the SLA | The bot is running (status='active'). A latency measurement tool is available. | Record the time before sending a pause request. Send the pause request. Record the time when the HTTP response is received. | The operation completes within the target SLA (a fast operation with zero HL API calls and zero vault calls). (Reference: NFR.) | P2 |

---

*Test Cases — UC-EXBOT-pause-resume (Pause and Resume Bot) — 31 test cases — generated by qc-func-tc-design-exbot skill*
*Re-generated after BA ARC Migration (2026-07-04) — v4, 2026-07-06*
