# Test Cases — UC-EXBOT-pause-resume: Pause and Resume Bot (v2)

**Total test cases:** 42 (Delta vs v1: +0 new, ~10 updated, -0 deleted)
**Scope:** Logic-only (backend / API / bot — no UI)
**Update trigger:** REQUIREMENT_DELTA
**Source UC:** `docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260630_v1.md` (v3, 2026-07-03)
**Source scenarios:** `docs/qc/scenarios/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_scenarios_20260702_v1.md`
**Output language:** English

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project |
|---|---|
| UC | Use Case — tài liệu mô tả luồng nghiệp vụ pause/resume |
| FR-EXBOT-* | Functional Requirement trong SRS spec.md |
| BR-EXBOT-* | Business Rule trong SRS |
| MSG-SUC-* | Success message codes for API response |
| AC | Acceptance Criteria — tiêu chí nghiệp vụ cần đạt |
| E-EXBOT-* | Error code khi reject/exception |
| D1 | Cloudflare D1 database — off-chain state store |
| HL | Hyperliquid — on-chain perpetual exchange |
| SAFE_MODE | Trạng thái bot bất thường nghiêm trọng |

---

## Test Case Summary

| Test Type | Count |
|---|---|
| Functional (FUNC) | 28 |
| Integration (INTG) | 6 |
| Non-Functional (NFR) | 8 |
| **Total** | **42** |

---

## Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Happy path pause | TC_008 | Covered |
| AC-02 | Happy path resume | TC_009, TC_037 | Covered |
| AC-03 | SAFE_MODE rejection | TC_010 | Covered |
| AC-04 | Idempotent pause | TC_011 | Covered |
| AC-05 | Idempotent resume | TC_012 | Covered |
| AC-06 | Light-check suppressed | TC_020, TC_040 | Covered |
| AC-07 | Deep-audit continues | TC_022, TC_023 | Covered |
| AC-08 | Audit log pause | TC_015 | Covered |
| AC-09 | Audit log resume | TC_016 | Covered |
| AC-10 | Hedge position preserved | TC_008, TC_017 | Covered |
| AC-11 | LP NFT preserved | TC_009, TC_019 | Covered |

---

## I. Preconditions & Initial State

### I.1. Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|-------|-------|----------------|-----------|----------------|----------|
| TC_001 | Pause Bot — Precondition: Bot exists with active status | Investor (user_id=U1) is authenticated; Bot exists in D1 with `bots.status='active'` and `bots.lifecycle_state='active'`; Bot is NOT in safe_mode; Test environment: HL testnet | 1. Investor U1 sends `POST /api/exbot/pause` with `{ "botId": "bot_001" }`; 2. System queries D1 to verify bot exists with `bots.status='active'` and `bots.lifecycle_state='active'` | API accepts the request (HTTP 200); D1 record exists with `bots.status='active'` before pause completes; Response includes `status: "paused"` | High |
| TC_002 | Resume Bot — Precondition: Bot exists with paused status | Investor (user_id=U1) is authenticated; Bot exists in D1 with `bots.status='paused'`; `bots.lifecycle_state` is preserved from pre-pause value | 1. Investor U1 sends `POST /api/exbot/resume` with `{ "botId": "bot_001" }`; 2. System queries D1 to verify bot exists with `bots.status='paused'` | API accepts the request (HTTP 200); D1 record exists with `bots.status='paused'` before resume; Response includes `status: "active"` | High |
| TC_003 | Authorization — Investor cannot pause another investor's bot | Investor U1 owns a bot with `bots.status='active'`, `bots.user_id='U1'`; Investor U2 is authenticated | 1. Investor U2 sends `POST /api/exbot/pause` with `{ "botId": "bot_u1_001" }` | API returns HTTP 403 Forbidden OR HTTP 404 (bot not found for this user); No state change occurs in D1; Error message indicates unauthorized action | High |

---

## II. Input & Contract Validation

### II.1. Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|-------|-------|----------------|-----------|----------------|----------|
| TC_004 | Pause Bot — Input validation: missing botId | Investor is authenticated | 1. Investor sends `POST /api/exbot/pause` with missing botId (body: {}) | API returns HTTP 400 Bad Request; Error message indicates botId is required | High |
| TC_005 | Resume Bot — Input validation: missing botId | Investor is authenticated | 1. Investor sends `POST /api/exbot/resume` with missing botId (body: {}) | API returns HTTP 400 Bad Request; Error message indicates botId is required | High |
| TC_006 | Pause Bot — Input validation: malformed botId | Investor is authenticated | 1. Investor sends `POST /api/exbot/pause` with malformed botId: "invalid-bot-id-format!!!" | API returns HTTP 400 Bad Request; Error message indicates invalid botId format | Medium |
| TC_007 | Resume Bot — Input validation: malformed botId | Investor is authenticated | 1. Investor sends `POST /api/exbot/resume` with malformed botId: "invalid-bot-id-format!!!" | API returns HTTP 400 Bad Request; Error message indicates invalid botId format | Medium |

---

## III. Core Functional Logic

### III.1. Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|-------|-------|----------------|-----------|----------------|----------|
| TC_008 | Pause Bot — Happy path: successful state transition | Bot with `bots.status='active'` and `bots.lifecycle_state='active'`; Bot has hedge short position: `hedge_legs.last_known_hl_short_size = X ETH`; Bot has LP NFT: `positions.token_id = N` | 1. Investor sends `POST /api/exbot/pause` with valid botId; 2. System updates D1: `bots.status='paused'` with conditional UPDATE (`WHERE status='active'`); 3. System reads `hedge_legs.last_known_hl_short_size` (should be X); 4. System reads `positions.token_id` (should be N) | HTTP 200: `{ status: "paused", message: "Bot paused. Hedge and LP are maintained." }` (MSG-SUC-81); D1: `bots.status='paused'`; D1: `bots.lifecycle_state` remains 'active' (unchanged); D1: `hedge_legs.last_known_hl_short_size = X` (unchanged); D1: `positions.token_id = N` (unchanged) | High |
| TC_009 | Resume Bot — Happy path: successful state transition and light-check scheduling | Bot with `bots.status='paused'`; `bots.lifecycle_state` preserved from pre-pause value; `bot_runtime_state.next_light_check_at` is expired or unset | 1. Investor sends `POST /api/exbot/resume` with valid botId; 2. System updates D1: `bots.status='active'` with conditional UPDATE (`WHERE status='paused'`); 3. System sets `bot_runtime_state.next_light_check_at`; 4. System enqueues light-check message | HTTP 200: `{ status: "active", message: "Bot resumed. Monitoring will resume shortly." }` (MSG-SUC-82); D1: `bots.status='active'`; D1: `bots.lifecycle_state` unchanged (preserved); D1: `next_light_check_at = now + 5min + jitter(-45s, +45s)`; Light-check message enqueued to queue | High |
| TC_010 | Pause Bot — SAFE_MODE rejection | Bot with `bots.status='safe_mode'` | 1. Investor sends `POST /api/exbot/pause` with bot in safe_mode | HTTP 409 Conflict; Error message: "Bot is in Safe Mode. You can close the bot instead." (E-EXBOT-013); D1: `bots.status` remains 'safe_mode' (no change) | High |
| TC_011 | Pause Bot — Idempotent behavior when already paused | Bot with `bots.status='paused'` | 1. Investor sends `POST /api/exbot/pause` for already-paused bot | HTTP 200 (idempotent success); Response: "Bot already paused. No change needed."; D1: `bots.status` remains 'paused'; Conditional UPDATE (`WHERE status='active'`) returns 0 rows affected — idempotent exit | High |
| TC_012 | Resume Bot — Idempotent behavior when already active | Bot with `bots.status='active'` | 1. Investor sends `POST /api/exbot/resume` for already-active bot | HTTP 200 (idempotent success); Response: "Bot already active. No change needed."; D1: `bots.status` remains 'active'; Conditional UPDATE (`WHERE status='paused'`) returns 0 rows affected — idempotent exit | High |
| TC_013 | Pause Bot — Rejected from hedge_stopped_cooldown or lp_rebalancing lifecycle_state [UPDATED — Reason: Q7 resolved, only `lifecycle_state='active'` allowed for pause] | Bot with `bots.status='active'` and `bots.lifecycle_state='hedge_stopped_cooldown'` OR `bots.lifecycle_state='lp_rebalancing'` | 1. Investor sends `POST /api/exbot/pause` for bot in non-active lifecycle_state | HTTP 409 Conflict; D1: `bots.status` remains 'active' (no change); Message: "Bot is not in a state that supports pause." (or equivalent); Reason: Only `lifecycle_state='active'` is allowed for pause per BA decision (2026-07-03). These states are mid-process (cooldown timer, rebalance in progress) — pausing would create undefined edge cases. | Medium |
| TC_014 | Pause Bot — Rejected from transitional lifecycle_state | Bot with `bots.status='active'` and `bots.lifecycle_state IN ('preflight', 'lp_opening', 'hedge_pre_open', 'stop_placing', 'lp_closing', 'closed', 'error')` | 1. Investor sends `POST /api/exbot/pause` for bot in transitional state | HTTP 409 Conflict; D1: `bots.status` remains 'active' (no change); Message: "Bot is not in a state that supports pause."; Only `lifecycle_state='active'` can transition to `paused` per states.md state registry | Medium |
| TC_035 | Pause Bot — Bot does not exist | No bot with the specified botId exists in D1 | 1. Investor sends `POST /api/exbot/pause` with non-existent botId: "non_existent_bot_999" | HTTP 404 Not Found; No bot record created; Error message indicates bot not found | High |
| TC_036 | Resume Bot — Bot does not exist | No bot with the specified botId exists in D1 | 1. Investor sends `POST /api/exbot/resume` with non-existent botId: "non_existent_bot_999" | HTTP 404 Not Found; Error message indicates bot not found | High |

---

## IV. Integration & Data Consistency

### IV.1. Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|-------|-------|----------------|-----------|----------------|----------|
| TC_015 | Pause Bot — Audit log recording | Bot with `bots.status='active'`; Audit log table exists in D1 | 1. Investor sends `POST /api/exbot/pause` for active bot; 2. System queries audit log table for latest entry | Audit log entry exists with: action = "Bot paused by investor", bot_id = the paused bot's ID, user_id = investor, timestamp = recorded at pause time | High |
| TC_016 | Resume Bot — Audit log recording | Bot with `bots.status='paused'`; Audit log table exists in D1 | 1. Investor sends `POST /api/exbot/resume` for paused bot; 2. System queries audit log table for latest entry | Audit log entry exists with: action = "Bot resumed by investor", bot_id = the resumed bot's ID, user_id = investor, timestamp = recorded at resume time | High |
| TC_020 | Light-check Worker — Skips entirely for paused bot [UPDATED — Reason: Q2 resolved, ExBot Worker handles as synchronous handler] | Bot with `bots.status='paused'`; Light-check message delivered to worker | 1. Cron triggers bot-scan, generates light-check message for paused bot; 2. Light-check worker receives message; 3. Worker evaluates `bots.status='paused'` at eligibility gate | Worker skips entire light-check evaluation; No delta computation; No drift/range/funding evaluation; No hedge-sync message enqueued; Worker returns without error (graceful skip); Worker architecture: ExBot Worker handles pause/resume as synchronous HTTP POST handler (no queue consumer) per Q2 resolved | High |
| TC_021 | Hedge-sync Worker — No execution for paused bot | Bot with `bots.status='paused'`; Hedge-sync message delivered to worker | 1. Hedge-sync worker receives message for paused bot; 2. Worker evaluates `bots.status='paused'` | Worker does NOT submit any HL order; Worker does NOT modify `hedge_legs` records; Worker skips silently or returns early | High |
| TC_022 | Deep-audit — Continues on 6-hour cadence for paused bot (normal) | Bot with `bots.status='paused'`; System in normal mode: `circuit_breakers.state='closed'`, `margin_status='ok'`; 6 hours since last deep-audit | 1. Deep-audit cron fires scheduled run; 2. Deep-audit worker fetches clearinghouseState from HL; 3. Worker verifies short size matches `hedge_legs.last_known_hl_short_size`; 4. Worker updates `hedge_legs.margin_status` | Deep-audit executes normally; D1: `hedge_legs.margin_status` updated from fresh HL margin data; No anomaly detected → no SAFE_MODE entry | High |
| TC_023 | Deep-audit — Runs on 1-hour cadence for paused bot (high-risk) | Bot with `bots.status='paused'`; System in high-risk mode: `circuit_breakers.state='open'` OR `margin_status='warning'` OR `margin_status='critical'`; 1 hour since last deep-audit | 1. Deep-audit cron fires (high-risk cadence); 2. Deep-audit worker runs for paused bot | Deep-audit executes at 1-hour interval (not 6-hour); Worker fetches HL state; Worker updates margin status | High |
| TC_024 | Price-near-stop-audit — Continues for paused bot | Bot with `bots.status='paused'`; Bot has stop price: `hedge_legs.stop_price = S`; ETH mark price near or above stop price | 1. Light-check pass evaluates stop trigger detection for paused bot; 2. System checks: is mark price >= stop price? | Even though light-check is skipped for paused bot, stop monitoring continues; If mark price >= stop price: system enqueues `price-near-stop-audit` message; Reference: FR-EXBOT-014 | High |
| TC_025 | SAFE_MODE Entry — From paused state (stop trigger stuck) | Bot with `bots.status='paused'`; `hedge_legs.stop_trigger_crossed_at` is set and age > 30 minutes | 1. Deep-audit runs for paused bot; 2. Worker detects `stop_trigger_crossed_at` stuck > 30 min | D1: `bots.status` transitions from 'paused' to 'safe_mode'; D1: `bots.lifecycle_state` remains at pre-pause value (unchanged); Reference: FR-EXBOT-033 | High |
| TC_026 | SAFE_MODE Entry — From paused state (margin critical) | Bot with `bots.status='paused'`; `hedge_legs.margin_status='warning'` (first consecutive) | 1. Deep-audit runs for paused bot; 2. Worker detects `margin_status='critical'` for first time; 3. Next deep-audit run (still paused); 4. Worker detects `margin_status='critical'` for second consecutive time | D1: `bots.status` transitions from 'paused' to 'safe_mode'; D1: `bots.lifecycle_state` preserved; Reference: FR-EXBOT-050, FR-EXBOT-060 | High |
| TC_037 | Resume — Correct jitter timing for next_light_check_at | Bot with `bots.status='paused'`; `bot_runtime_state.next_light_check_at` is expired or unset | 1. Record current time (T0); 2. Investor sends `POST /api/exbot/resume`; 3. Query `bot_runtime_state.next_light_check_at` | `next_light_check_at` is within range: [T0 + 4m15s, T0 + 5m45s]; Formula: `now + 5min + jitter(-45s, +45s)`; Light-check message enqueued to queue | High |
| TC_038 | API Response — Pause success message verified against MSG-SUC-81 [UPDATED — Reason: Q9 resolved, MSG-SUC-81 registered] | Bot with `bots.status='active'` | 1. Investor sends `POST /api/exbot/pause`; 2. Verify response body message | HTTP 200; Response body contains: `message: "Bot paused. Hedge and LP are maintained."` matching MSG-SUC-81 from message-list.md §MSG-EXBOT (verbatim); Q9 resolved: Success messages registered as MSG-SUC-81/82 in message-list.md (2026-07-03) | Medium |
| TC_039 | API Response — Resume success message verified against MSG-SUC-82 [UPDATED — Reason: Q9 resolved, MSG-SUC-82 registered] | Bot with `bots.status='paused'` | 1. Investor sends `POST /api/exbot/resume`; 2. Verify response body message | HTTP 200; Response body contains: `message: "Bot resumed. Monitoring will resume shortly."` matching MSG-SUC-82 from message-list.md §MSG-EXBOT (verbatim); Q9 resolved: Success messages registered as MSG-SUC-81/82 in message-list.md (2026-07-03) | Medium |
| TC_040 | Worker Architecture — Light-check uses bots.status as skip gate | Bot transitioning from 'active' to 'paused'; Light-check message pending | 1. Bot status changes to 'paused'; 2. Light-check message delivered to worker; 3. Worker evaluates `bots.status='paused'` at eligibility gate | Worker evaluates `bots.status='paused'` BEFORE evaluating rebalance criteria; Worker does NOT evaluate drift, range, or funding conditions; Skip happens at the bot eligibility gate (first check); Q2 resolved: ExBot Worker handles pause/resume as synchronous HTTP POST handler | High |
| TC_042 | Integration — Bot-scan worker picks up resumed bot | Bot with `bots.status='paused'`; Investor resumes the bot; `next_light_check_at` is set | 1. Bot-scan cron triggers; 2. Scan worker selects bots for light-check scheduling; 3. Worker processes resumed bot | Worker includes bot with `bots.status='active'` in scan; Bot receives light-check message as scheduled; `next_light_check_at` updated to next interval | Medium |

### IV.2. Integration

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|-------|-------|----------------|-----------|----------------|----------|
| TC_017 | Pause Bot — Hedge position preservation (no HL API calls) | Bot with active HL short position: `hedge_legs.last_known_hl_short_size = X ETH`; HL API monitor/logger enabled | 1. Monitor HL API calls before pause; 2. Investor sends `POST /api/exbot/pause`; 3. Monitor HL API calls during pause operation; 4. Verify HL position size in D1 | During pause operation: 0 HL API calls; D1: `hedge_legs.last_known_hl_short_size = X` (unchanged); On-chain: HL short position size unchanged | High |
| TC_018 | Resume Bot — No HL API calls | Bot with `bots.status='paused'`; HL API monitor/logger enabled | 1. Monitor HL API calls before resume; 2. Investor sends `POST /api/exbot/resume`; 3. Monitor HL API calls during resume operation | During resume operation: 0 HL API calls; Light-check message enqueued (but light-check itself makes no HL calls per BR-EXBOT-003) | High |
| TC_019 | Pause Bot — LP NFT preservation (no vault API calls) | Bot with LP NFT: `positions.token_id = N`; Vault API monitor/logger enabled | 1. Monitor vault API calls before pause; 2. Investor sends `POST /api/exbot/pause`; 3. Verify vault state | During pause operation: 0 vault API calls; D1: `positions.token_id = N` (unchanged); On-chain: LP NFT ownership unchanged | High |

---

## V. Non-Functional (Logic-Accessible)

### V.3. Non-Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|-------|-------|----------------|-----------|----------------|----------|
| TC_027 | Security — Authorization enforcement at API layer | Investor U1 owns bot with `bots.status='active'`; Investor U2 is authenticated (different user) | 1. U2 attempts `POST /api/exbot/pause` with U1's botId; 2. System evaluates authorization | Request rejected before any D1 mutation; HTTP 403 or 404 returned; No audit log entry written for cross-user attempt; No state change in D1 | High |
| TC_028 | Reliability — Atomic D1 write for pause operation [UPDATED — Reason: Q2 resolved, synchronous handler architecture confirmed] | Bot with `bots.status='active'` | 1. Investor sends `POST /api/exbot/pause`; 2. Worker starts updating D1 (`bots.status='paused'`) with conditional UPDATE; 3. Simulate worker crash mid-transaction | D1 remains at previous consistent state (`bots.status='active'`); No partial write; No inconsistent `bots.status` value; Q2 resolved: ExBot Worker is synchronous handler — atomicity enforced via DB transaction or equivalent | High |
| TC_029 | Idempotency — Concurrent duplicate pause requests [UPDATED — Reason: Q2, Q3 resolved, DB conditional UPDATE mechanism confirmed] | Bot with `bots.status='active'`; Investor sends two simultaneous pause requests | 1. Investor sends pause request #1; 2. Investor sends pause request #2 (simultaneously); 3. System processes both requests | Exactly ONE state change to `bots.status='paused'`; Request #1: success (HTTP 200); Request #2: idempotent success "Bot already paused. No change needed."; No error, no partial state, no race condition in D1; Q2, Q3 resolved: ExBot Worker synchronous handler + DB conditional UPDATE ensures deterministic outcome | High |
| TC_030 | Idempotency — Concurrent pause and resume requests [UPDATED — Reason: Q2, Q3 resolved, DB conditional UPDATE mechanism confirmed] | Bot with `bots.status='active'`; Investor sends pause and resume simultaneously | 1. Investor sends pause request; 2. Investor sends resume request (simultaneously); 3. System serializes operations | Final `bots.status` is either 'active' or 'paused' (valid end states); No error occurs; Audit log entries recorded for each operation; Q2, Q3 resolved: whichever conditional UPDATE matches first wins — deterministic outcome | High |
| TC_031 | Data Persistence — Pause does not affect rebalance_attempts | Bot with existing records in `rebalance_attempts` table; Bot has `bots.status='active'` | 1. Query `rebalance_attempts` for this bot (record count and values); 2. Investor sends `POST /api/exbot/pause`; 3. Query `rebalance_attempts` again | No new rows inserted in `rebalance_attempts`; No existing rows modified; All records unchanged | Medium |
| TC_032 | Data Persistence — Pause does not affect lp_operations | Bot with existing records in `lp_operations` table; Bot has `bots.status='active'` | 1. Query `lp_operations` for this bot (record count and values); 2. Investor sends `POST /api/exbot/pause`; 3. Query `lp_operations` again | No new rows inserted in `lp_operations`; No existing rows modified; All records unchanged | Medium |
| TC_033 | Auditability — No PII in logs | Investor account with PII data (email, name) | 1. Investor sends `POST /api/exbot/pause`; 2. Check system logs for this request | Logs contain: bot_id, action, timestamp, HTTP status; Logs DO NOT contain: investor email, investor name, or other PII; Error logs are useful for diagnosis without leaking sensitive values | Medium |
| TC_034 | Performance — Pause/resume operation latency | Bot with `bots.status='active'`; Test environment configured | 1. Measure time before sending pause request; 2. Investor sends `POST /api/exbot/pause`; 3. Measure time when HTTP response received | Operation completes quickly (no HL API calls, no vault calls); Latency is within acceptable SLA (target: < 2 seconds); Reference: NFR | Medium |
| TC_041 | Concurrency — Message redelivery idempotency [UPDATED — Reason: Q2, Q3 resolved, no queue consumer for pause/resume] | Bot with `bots.status='active'`; System configured for message redelivery scenario | 1. Investor sends `POST /api/exbot/pause`; 2. Same request arrives again (duplicate); 3. System processes second delivery | Exactly one effect on D1; Second delivery exits cleanly via conditional UPDATE (`WHERE status='active'`) returning 0 rows; No duplicate audit log entries; Q2, Q3 resolved: pause/resume handled by ExBot Worker synchronous handler (not queue consumer) — idempotency via DB conditional UPDATE | High |

---

## VI. Out-of-Scope Flags

| Item | Reason | Recommended Action |
|---|---|---|
| Performance testing (pause/resume latency at scale) | NFR — Load testing is out of scope | Defer to performance test suite |
| Hyperliquid testnet account provisioning | Environment/infra setup | QC Lead / Ops to arrange |
| POOL UI (PTL-05) message rendering | Q8 resolved — ExBot scope ends at API response; POOL UI owns rendering | Not in ExBot scope |
| Smart contract (BnzaExVault) integration with real LP NFT | ABI/address not confirmed yet (OQ-EXBOT-08) | Wait for Phase 0 gate |
| API endpoint names per environment | Q1 deferred — endpoint names vary by environment | QA to get actual endpoints from test environment config |

---

## Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| v1 | 2026-07-02 | QC Agent | Initial test cases generated. Q1 deferred; Q2, Q3, Q7, Q8, Q9 flagged as BLOCKED. |
| v2 | 2026-07-03 | QC Agent | Q2, Q3, Q7, Q8, Q9 resolved by BA (2026-07-03). BLOCKED notes removed. MSG-SUC-81/82 added. Q7 scenarios updated: only `lifecycle_state='active'` allowed for pause. TC_013 updated to REJECTED for non-active states. TC_041 updated: no queue consumer for pause/resume. TC IDs renamed: TC_PAUSE_XXX → TC_XXX. |

---

*Test Cases — UC-EXBOT-pause-resume (Pause and Resume Bot) — 42 test cases — updated by qc-func-tc-design-exbot skill (2026-07-03)*
*BLOCKED notes removed — Q2, Q3, Q7, Q8, Q9 resolved by BA (2026-07-03)*
