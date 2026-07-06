# Test Scenarios — UC-EXBOT-pause-resume: Pause and Resume Bot

> Source: `docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260706_v4.md` (v4, 2026-07-06)
> Generated: 2026-07-02
> Updated: 2026-07-06
> Domain/Architecture: API/backend ExBot — **AWS Lambda (ExBot Lambda)** + Hyperliquid + **Aurora PostgreSQL** + Operator Facade `/api/exbot/*`, no UI
> BA Update: 2026-07-04 (ARC Migration: Cloudflare→AWS, D1→Aurora PostgreSQL)

---

## UC-EXBOT-pause-resume — Pause and Resume Bot

### Scenario ID: TS_EXBOT_PAUSE_001
**Scenario Title:** Happy path — Investor pauses active bot; hedge and LP positions preserved
**UC Reference:** UC-EXBOT-pause-resume §3 (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-01; AC-08; BR-EXBOT-002
**Test Type:** Functional
**Description:** Investor sends `POST /api/exbot/pause` with `botId` for a bot with `bots.status='active'` and `bots.lifecycle_state='active'`. The ExBot Lambda (synchronous HTTP handler, no queue) verifies preconditions, sets `bots.status='paused'` with conditional UPDATE (`WHERE status='active'`), persists atomically to Aurora PostgreSQL, and returns API response `{ status: "paused", message: "Bot paused. Hedge and LP are maintained." }` with MSG-SUC-81. After pause, `bots.lifecycle_state` remains `'active'`, `hedge_legs.last_known_hl_short_size` is unchanged, and `positions.token_id` is unchanged. Audit log records "Bot paused by investor".
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_002
**Scenario Title:** Happy path — Investor resumes paused bot; light-check scheduled within 5 minutes
**UC Reference:** UC-EXBOT-pause-resume §4 (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-02; AC-09
**Test Type:** Functional
**Description:** Investor sends `POST /api/exbot/resume` with `botId` for a bot with `bots.status='paused'`. The ExBot Lambda verifies `bots.status='paused'`, restores `bots.status='active'` with conditional UPDATE (`WHERE status='paused'`), confirms `bots.lifecycle_state` unchanged from pre-pause value, sets `bot_runtime_state.next_light_check_at = now + 5min + jitter(−45s, +45s)`, enqueues a `light-check` message, and returns `{ status: "active", message: "Bot resumed. Monitoring will resume shortly." }` with MSG-SUC-82. Audit log records "Bot resumed by investor".
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_003
**Scenario Title:** Pause rejected with E-EXBOT-013 when bot is in safe_mode
**UC Reference:** UC-EXBOT-pause-resume §5 A1 (v2026-07-04)
**Req-ID:** FR-EXBOT-050; AC-03
**Test Type:** Functional
**Description:** Investor sends `POST /api/exbot/pause` for a bot with `bots.status='safe_mode'`. The ExBot Lambda returns HTTP 409 with message: "Bot is in Safe Mode. You can close the bot instead." (verbatim E-EXBOT-013 from message-list.md). No state change occurs in Aurora PostgreSQL.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_EXBOT_PAUSE_004
**Scenario Title:** Pause request is idempotent — bot already paused
**UC Reference:** UC-EXBOT-pause-resume §5 A3 (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-04
**Test Type:** Functional
**Description:** Investor sends `POST /api/exbot/pause` for a bot already with `bots.status='paused'`. The ExBot Lambda returns a success response with message "Bot already paused. No change needed." No Aurora PostgreSQL record is modified. This idempotent behavior is enforced by the conditional UPDATE (`WHERE status='active'`) — the request that finds `status='paused'` does not update anything.
**Test Focus:** Idempotency/Concurrency
**Note:** Q3 resolved — race condition prevented by DB conditional UPDATE (BA response 2026-07-03).

---

### Scenario ID: TS_EXBOT_PAUSE_005
**Scenario Title:** Resume request is idempotent — bot already active
**UC Reference:** UC-EXBOT-pause-resume §5 A2 (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-05
**Test Type:** Functional
**Description:** Investor sends `POST /api/exbot/resume` for a bot already with `bots.status='active'`. The ExBot Lambda returns a success response with message "Bot already active. No change needed." No Aurora PostgreSQL record is modified. This idempotent behavior is enforced by the conditional UPDATE (`WHERE status='paused'`) — the request that finds `status='active'` does not update anything.
**Test Focus:** Idempotency/Concurrency
**Note:** Q3 resolved — race condition prevented by DB conditional UPDATE (BA response 2026-07-03).

---

### Scenario ID: TS_EXBOT_PAUSE_006
**Scenario Title:** Audit log entry is recorded after successful pause
**UC Reference:** UC-EXBOT-pause-resume §7 Postconditions (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-08
**Test Type:** Functional
**Description:** Investor successfully pauses an active bot. The ExBot Lambda records an audit log entry with content "Bot paused by investor" and a timestamp in Aurora PostgreSQL. Audit log contains bot_id, user_wallet_address, timestamp, and action type.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_007
**Scenario Title:** Audit log entry is recorded after successful resume
**UC Reference:** UC-EXBOT-pause-resume §7 Postconditions (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-09
**Test Type:** Functional
**Description:** Investor successfully resumes a paused bot. The ExBot Lambda records an audit log entry with content "Bot resumed by investor" and a timestamp in Aurora PostgreSQL. Audit log contains bot_id, user_wallet_address, timestamp, and action type.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_008
**Scenario Title:** Hedge short position size is unchanged after pause
**UC Reference:** UC-EXBOT-pause-resume §3 step 5 (v2026-07-04)
**Req-ID:** BR-EXBOT-002; AC-10
**Test Type:** Functional
**Description:** Bot has an active HL short position with `hedge_legs.last_known_hl_short_size = X ETH`. Investor pauses the bot. After pause, `hedge_legs.last_known_hl_short_size = X ETH` — exactly the same value. No HL order (close, adjust, or cancel) is submitted to Hyperliquid during the pause operation. Per BR-EXBOT-002: "Pause ≠ Close — only suppresses new mutations, does not liquidate hedge."
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_009
**Scenario Title:** LP NFT token ID is unchanged after pause
**UC Reference:** UC-EXBOT-pause-resume §3 step 6 (v2026-07-04)
**Req-ID:** BR-EXBOT-002; AC-11
**Test Type:** Functional
**Description:** Bot has an active LP NFT with `positions.token_id = N`. Investor pauses the bot. After pause, `positions.token_id = N` — exactly the same value. No vault transaction (redeem, transfer, or approval) is submitted to BnzaExVault during the pause operation. Per BR-EXBOT-002: "Pause ≠ Close — only suppresses new mutations, does not liquidate LP."
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_010
**Scenario Title:** Light-check worker skips entirely for paused bot; no hedge-sync enqueued
**UC Reference:** UC-EXBOT-pause-resume §6 (v2026-07-04)
**Req-ID:** FR-EXBOT-012; AC-06
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. A cron-triggered `light-check` message is delivered to the light-check worker for this bot. The worker evaluates `bots.status='paused'` at the eligibility gate and skips the entire light-check evaluation — does not compute delta, does not evaluate drift/range/funding conditions, does not enqueue a `hedge-sync` message, and does not fetch from Hyperliquid.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_011
**Scenario Title:** Hedge-sync worker does not execute adjustments for paused bot
**UC Reference:** UC-EXBOT-pause-resume §6 (v2026-07-04)
**Req-ID:** FR-EXBOT-005; AC-06
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. A `hedge-sync` message is delivered to the hedge-sync worker (e.g., from a previously enqueued message or event trigger). The worker evaluates `bots.status='paused'` and does not submit any HL order and does not modify `hedge_legs` records. Hedge-sync is suppressed during pause.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_012
**Scenario Title:** Deep-audit continues on 6-hour cadence for paused bot
**UC Reference:** UC-EXBOT-pause-resume §6 (v2026-07-04)
**Req-ID:** FR-EXBOT-016; AC-07
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` under normal conditions (circuit_breakers.state='closed' and margin_status='ok'). The deep-audit cron fires its scheduled run every 6 hours. The deep-audit worker fetches clearinghouseState from HL, verifies short size matches `hedge_legs.last_known_hl_short_size`, updates `hedge_legs.margin_status`, and detects no anomalies. `bots.status='paused'` does not prevent deep-audit from running.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_013
**Scenario Title:** Deep-audit runs on 1-hour high-risk cadence for paused bot when system is in high-risk mode
**UC Reference:** UC-EXBOT-pause-resume §6 (v2026-07-04)
**Req-ID:** FR-EXBOT-016
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` AND (`circuit_breakers.state != 'closed'` OR `margin_status IN ('warning','critical')`). The deep-audit cron fires. The system runs deep-audit at the 1-hour interval instead of the standard 6-hour interval per FR-EXBOT-016. The worker fetches HL state and updates margin status. This applies regardless of `bots.status` — high-risk cadence is independent of pause state.
**Test Focus:** State transition
**Note:** Evidence from FR-EXBOT-016: "In high-risk mode (circuit_breakers.state != 'closed' or margin_status IN ('warning','critical')), the interval reduces to 1 hour."

---

### Scenario ID: TS_EXBOT_PAUSE_014
**Scenario Title:** price-near-stop-audit continues for paused bot — stop monitoring never suppressed
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-014
**Req-ID:** FR-EXBOT-014
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. Even though light-check is skipped for a paused bot, stop monitoring (price-near-stop-audit enqueue) continues "at all times" per FR-EXBOT-014. When ETH mark price is near or above `stop_price`, the system enqueues a `price-near-stop-audit` message. Light-check shall never suppress stop price evaluation or price-near-stop-audit enqueue.
**Test Focus:** State transition
**Note:** Evidence from FR-EXBOT-014: "Stop monitoring shall continue at all times — including when circuit_breakers.state='open'. Light-check shall never suppress stop price evaluation or price-near-stop-audit enqueue."

---

### Scenario ID: TS_EXBOT_PAUSE_015
**Scenario Title:** Bot transitions to safe_mode when deep-audit detects anomaly on paused bot
**UC Reference:** UC-EXBOT-pause-resume §6; states.md (v2026-07-04)
**Req-ID:** FR-EXBOT-050; FR-EXBOT-033
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. Deep-audit runs and detects a SAFE_MODE entry condition (e.g., `stop_trigger_crossed_at` stuck > 30 minutes per FR-EXBOT-033, or `stop_replacing_started_at` stuck > 60 seconds). The system transitions `bots.status` from `'paused'` to `'safe_mode'`. The `bots.lifecycle_state` remains at its pre-pause value (unchanged). Per states.md: `safe_mode` and `paused` are independent coarse-grained states.
**Test Focus:** State transition
**Note:** Evidence from states.md state registry (v2026-07-03): `safe_mode` and `paused` are independent. `bots.status` transitions from `paused` → `safe_mode` while `lifecycle_state` is preserved.

---

### Scenario ID: TS_EXBOT_PAUSE_016
**Scenario Title:** Pause rejected when bot lifecycle_state is hedge_stopped_cooldown or lp_rebalancing
**UC Reference:** UC-EXBOT-pause-resume §2 (v2026-07-04); states.md (v2026-07-03)
**Req-ID:** FR-EXBOT-005
**Test Type:** Functional
**Description:** Bot has `bots.status='active'` but `bots.lifecycle_state` is `'hedge_stopped_cooldown'` (stop fired; hedge-sync suppressed for 4h cooldown) or `'lp_rebalancing'` (LP range rebalance in progress). Investor sends pause request. The ExBot Lambda rejects the request — only `lifecycle_state='active'` is allowed for pause per BA decision (Q7, 2026-07-03). These two states are in the middle of automated processes; pausing would create undefined edge cases (cooldown timer, rebalance in progress). The system returns HTTP 409 with error message.
**Test Focus:** Error/Exception
**Note:** Q7 resolved — BA confirmed (2026-07-03): "Chỉ `lifecycle_state='active'` được phép pause. `hedge_stopped_cooldown` và `lp_rebalancing` không được pause — 2 state này đang trong quá trình xử lý tự động, pause vào giữa tạo edge case không xác định."

---

### Scenario ID: TS_EXBOT_PAUSE_017
**Scenario Title:** Pause rejected when bot lifecycle_state is transitional (preflight, lp_opening, lp_closed, etc.)
**UC Reference:** UC-EXBOT-pause-resume §2 (v2026-07-04); states.md (v2026-07-03)
**Req-ID:** FR-EXBOT-005
**Test Type:** Functional
**Description:** Bot has `bots.status='active'` but `bots.lifecycle_state` is one of the transitional states (`preflight`, `lp_opening`, `lp_opened`, `hedge_pre_open`, `hedge_post_confirmed`, `stop_placing`, `stop_verified`, `lp_closing`, `closed`, or `error`). Investor sends pause request. The ExBot Lambda rejects the request — only `lifecycle_state='active'` is allowed for pause. The system returns HTTP 409 with appropriate error message.
**Test Focus:** Error/Exception
**Note:** Per states.md (v2026-07-03), only the `active` row in the state registry has `bots.status` that can transition to `paused`. All other `lifecycle_state` values either have different `bots.status` values or are transitional/terminal states.

---

### Scenario ID: TS_EXBOT_PAUSE_018
**Scenario Title:** Investor cannot pause another investor's bot — authorization enforcement
**UC Reference:** UC-EXBOT-pause-resume §1 (v2026-07-04); FR-EXBOT-001
**Req-ID:** FR-EXBOT-001
**Test Type:** Functional
**Description:** Investor A (user_wallet_address=WALLET_A) owns an active bot with `bots.status='active'` and `bots.user_wallet_address=WALLET_A`. Investor B (user_wallet_address=WALLET_B) sends a `POST /api/exbot/pause` request specifying Investor A's bot_id. The system enforces one-bot policy per FR-EXBOT-001: each wallet address can only operate on its own bots. The request is rejected with HTTP 403 (wallet mismatch) or HTTP 404 (bot not found for this user).
**Test Focus:** Permission/Role

---

### Scenario ID: TS_EXBOT_PAUSE_019
**Scenario Title:** Investor cannot pause a bot that does not exist
**UC Reference:** UC-EXBOT-pause-resume §2 (v2026-07-04)
**Req-ID:** FR-EXBOT-005
**Test Type:** Functional
**Description:** Investor sends a `POST /api/exbot/pause` request with a non-existent `botId` or a `botId` that exists but belongs to another user. The system returns HTTP 404 — no bot record found for this user. No bot record is created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_EXBOT_PAUSE_020
**Scenario Title:** Concurrent duplicate pause requests are handled safely via conditional UPDATE
**UC Reference:** UC-EXBOT-pause-resume §5 A3 (v2026-07-04)
**Req-ID:** FR-EXBOT-005
**Test Type:** Idempotency/Concurrency
**Description:** Investor sends two simultaneous `POST /api/exbot/pause` requests for the same active bot. The ExBot Lambda (synchronous handler, no queue) processes exactly one state change to `bots.status='paused'` via conditional UPDATE `WHERE status='active'`. The second request finds `bots.status='paused'` and receives the idempotent success response "Bot already paused. No change needed." — no error, no partial state, no race condition in Aurora PostgreSQL. Each request gets a response; only one Aurora PostgreSQL update occurs.
**Test Focus:** Idempotency/Concurrency
**Note:** Q2, Q3 resolved — Pause/resume handled by ExBot Lambda synchronous HTTP handler (not queue consumer). Race condition prevented by DB conditional UPDATE (BA response 2026-07-03).

---

### Scenario ID: TS_EXBOT_PAUSE_021
**Scenario Title:** Concurrent pause and resume requests for the same bot are handled safely
**UC Reference:** UC-EXBOT-pause-resume §5 A2, A3 (v2026-07-04)
**Req-ID:** FR-EXBOT-005
**Test Type:** Idempotency/Concurrency
**Description:** Investor sends a pause request and a resume request for the same bot simultaneously. The ExBot Lambda processes exactly one state change via conditional UPDATE — whichever request runs first wins (`WHERE status='active'` for pause wins if bot was active, `WHERE status='paused'` for resume wins if bot was paused). The losing request receives its idempotent success response ("Bot already paused/active. No change needed."). Final `bots.status` is deterministic (whichever condition matched first), and both operations complete successfully with appropriate responses.
**Test Focus:** Idempotency/Concurrency
**Note:** Q2, Q3 resolved — synchronous handler + DB conditional UPDATE ensures deterministic outcome (BA response 2026-07-03).

---

### Scenario ID: TS_EXBOT_PAUSE_022
**Scenario Title:** Resume reschedules light-check with correct jitter timing
**UC Reference:** UC-EXBOT-pause-resume §4 step 5 (v2026-07-04)
**Req-ID:** FR-EXBOT-013; AC-02
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` with `bot_runtime_state.next_light_check_at` set far in the past (expired schedule). Investor resumes the bot. The ExBot Lambda sets `next_light_check_at = now + 5min + jitter(−45s, +45s)`. The jitter value is verified to be within the range [now + 4m15s, now + 5m45s]. A `light-check` message is enqueued. Same jitter formula applies to resume scheduling as to normal scheduling per FR-EXBOT-013.
**Test Focus:** Happy path
**Note:** Evidence from FR-EXBOT-013: `next_light_check_at = now + 5min + random(−45s, +45s)`. Same jitter pattern for normal and resume scheduling.

---

### Scenario ID: TS_EXBOT_PAUSE_023
**Scenario Title:** Pause does not trigger any Hyperliquid API calls
**UC Reference:** UC-EXBOT-pause-resume §3–4 (v2026-07-04); FR-EXBOT-012
**Req-ID:** BR-EXBOT-003; FR-EXBOT-012
**Test Type:** Integration
**Description:** Investor pauses an active bot. During the pause operation, the ExBot Lambda makes zero calls to the Hyperliquid API. No `hedge_legs` fields are updated from HL. No HL order submission. The pause operation relies solely on Aurora PostgreSQL state. HL read/write is not part of the pause flow.
**Test Focus:** Integration

---

### Scenario ID: TS_EXBOT_PAUSE_024
**Scenario Title:** Resume does not trigger any Hyperliquid API calls
**UC Reference:** UC-EXBOT-pause-resume §4 (v2026-07-04); BR-EXBOT-003
**Req-ID:** BR-EXBOT-003
**Test Type:** Integration
**Description:** Investor resumes a paused bot. During the resume operation, the ExBot Lambda makes zero calls to the Hyperliquid API. No HL position fetch, no order placement, no margin check against HL. The `light-check` message is enqueued, but light-check itself is a separate worker that makes no HL calls per BR-EXBOT-003. Resume only updates Aurora PostgreSQL and enqueues light-check.
**Test Focus:** Integration

---

### Scenario ID: TS_EXBOT_PAUSE_025
**Scenario Title:** Pause/resume operation uses atomic Aurora PostgreSQL write — no partial state on Lambda crash
**UC Reference:** UC-EXBOT-pause-resume §3 step 3, §4 step 3 (v2026-07-04)
**Req-ID:** FR-EXBOT-005
**Test Type:** Data/State
**Description:** Investor sends a pause request. The ExBot Lambda starts the Aurora PostgreSQL conditional UPDATE (`bots.status='paused' WHERE status='active'`) but crashes mid-transaction (e.g., network timeout, Lambda timeout). The Aurora PostgreSQL transaction must be atomic — if the Lambda crashes before commit, Aurora PostgreSQL must remain at the previous consistent state (`bots.status='active'`) with no partial write. No inconsistent `bots.status` value exists in the database.
**Test Focus:** Data/State

---

### Scenario ID: TS_EXBOT_PAUSE_026
**Scenario Title:** Bot transitions to safe_mode when deep-audit detects margin critical on paused bot
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-050; FR-EXBOT-016 (v2026-07-04)
**Req-ID:** FR-EXBOT-050; FR-EXBOT-060
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` and `hedge_legs.margin_status='warning'`. Deep-audit runs and detects `margin_status='critical'` for the second consecutive time. Per FR-EXBOT-050, the system initiates SAFE_MODE. The bot's `bots.status` transitions from `'paused'` to `'safe_mode'`. `bots.lifecycle_state` is preserved at the pre-pause value. `bots.status='safe_mode'` is independent of the paused row in the state registry.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_027
**Scenario Title:** Light-check worker evaluates bots.status as eligibility gate before rebalance logic
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-012 (v2026-07-04)
**Req-ID:** FR-EXBOT-012
**Test Type:** Data/State
**Description:** A bot transitions from `active` to `paused`. The light-check worker receives a `light-check` message. The worker evaluates `bots.status='paused'` at the bot eligibility gate — BEFORE evaluating any rebalance criteria (drift, range, funding, delta). The skip must happen at the gate entry, not after partial evaluation. Verify the worker does not compute drift, does not read market data, and does not enqueue hedge-sync for a paused bot.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_028
**Scenario Title:** Stop trigger crossed > 30min stuck detection triggers SAFE_MODE from paused state
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-033; FR-EXBOT-050 (v2026-07-04)
**Req-ID:** FR-EXBOT-033
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` with `hedge_legs.stop_trigger_crossed_at` set and age > 30 minutes (stuck stop trigger marker). Deep-audit runs on its scheduled cadence (6h or 1h if high-risk) and detects this condition. Per FR-EXBOT-033: stop trigger stuck > 30 minutes initiates SAFE_MODE. The system transitions `bots.status` from `'paused'` to `'safe_mode'`. `bots.lifecycle_state` is preserved. Per states.md: `safe_mode` is a separate state, not a sub-state of `paused`.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_029
**Scenario Title:** Pause operation does not affect rebalance_attempts or lp_operations ledger
**UC Reference:** UC-EXBOT-pause-resume §3–4 (v2026-07-04)
**Req-ID:** FR-EXBOT-005
**Test Type:** Data/State
**Description:** Bot has existing records in `rebalance_attempts` (previous rebalance history) and `lp_operations` (LP mint/burn history). Investor pauses the bot. After pause, all existing records in `rebalance_attempts` and `lp_operations` remain unchanged — no new rows are inserted, no existing rows are modified, no new entries created for the pause action itself.
**Test Focus:** Data/State

---

### Scenario ID: TS_EXBOT_PAUSE_030
**Scenario Title:** Pause/resume API response message verified against MSG-SUC-81/82
**UC Reference:** UC-EXBOT-pause-resume §3 step 7, §4 step 6 (v2026-07-04); message-list.md (v2026-07-03)
**Req-ID:** FR-EXBOT-005
**Test Type:** Acceptance
**Description:** Investor pauses a bot. The API response body contains `message: "Bot paused. Hedge and LP are maintained."` matching MSG-SUC-81 from message-list.md §MSG-EXBOT. Investor resumes a bot. The API response body contains `message: "Bot resumed. Monitoring will resume shortly."` matching MSG-SUC-82. The tester verifies the exact message text from the response body. No placeholder or generic message is returned. Message codes are registered in message-list.md (updated 2026-07-03).
**Test Focus:** Acceptance
**Note:** Q8, Q9 resolved — ExBot scope ends at API response. "Investor receives UI confirmation" belongs to POOL UI (PTL-05), not ExBot. Success messages registered as MSG-SUC-81/82 in message-list.md (BA response 2026-07-03).

---

### Scenario ID: TS_EXBOT_PAUSE_031
**Scenario Title:** ExBot scope verification — no UI elements in pause/resume operations
**UC Reference:** UC-EXBOT-pause-resume §1 (v2026-07-04); spec.md §6
**Req-ID:** FR-EXBOT-005
**Test Type:** Acceptance
**Description:** ExBot is a backend-only module (per spec.md §6: "ExBot is a backend-only module. No UI screens are owned by this module."). The pause/resume operation produces an API response `{ status, message }`. Verify there are no ExBot-owned UI elements, screens, or components. The "Investor receives UI confirmation" step in the UC belongs to POOL UI (PTL-05), not ExBot scope. POOL UI renders the API response data — ExBot does not control how the message is displayed.
**Test Focus:** Acceptance
**Note:** Q8 resolved — ExBot scope confirmed as API-only. Tester verifies ExBot produces correct API response; POOL UI rendering is out of ExBot scope (BA response 2026-07-03).

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Performance testing (pause/resume latency, 10k-bot scan throughput) | NFR — Performance/load testing is out of scope for scenario design | Defer to performance test suite |
| Hyperliquid testnet account provisioning, wallet funding | Environment/infra setup — not a scenario design item | QC Lead / Ops to arrange test accounts |
| POOL UI (PTL-05) message rendering and button labels | Q8 resolved — ExBot scope ends at API response; POOL UI owns rendering | Not in ExBot scope |
| HL testnet environment setup, API keys, RPC endpoints | Dependency on Phase 0 gate (testnet access not yet confirmed) | QC Lead / Ops to arrange |
| Smart contract (BnzaExVault) integration test with real on-chain LP NFT | zen deploys contract; ABI/address not confirmed yet (NV-12) | Wait for Phase 0 gate |
| API endpoint names per environment | Q1 deferred — endpoint names vary by environment | QA to get actual endpoints from test environment config |

---

## Scenario Coverage Summary

| Test Type | Count | Scenarios |
|---|---|---|
| Functional | 18 | TS_EXBOT_PAUSE_001–003, 006–014, 016–019, 022, 026, 028 |
| Idempotency/Concurrency | 3 | TS_EXBOT_PAUSE_004–005, 020–021 |
| Integration | 2 | TS_EXBOT_PAUSE_023–024 |
| Data/State | 4 | TS_EXBOT_PAUSE_015, 025, 027, 029 |
| Acceptance | 3 | TS_EXBOT_PAUSE_030–031, plus MSG-SUC-81/82 verification in TS_EXBOT_PAUSE_001–002 |
| **Total** | **31** | |

---

## Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| v1 | 2026-07-02 | QC Agent | Initial scenarios generated. Q1 deferred; Q2, Q3, Q7, Q8, Q9 flagged as BLOCKED. |
| v1 (updated) | 2026-07-03 | QC Agent | Q2, Q3, Q7, Q8, Q9 resolved by BA (2026-07-03). BLOCKED tags removed. MSG-SUC-81/82 added. Q7 scenarios updated (only `lifecycle_state='active'` allowed for pause). Q8 scope clarified. TS_EXBOT_PAUSE_031 added. |
| **v2** | **2026-07-06** | **QC Agent** | **Updated after BA ARC migration (2026-07-04):** Source updated to audit v4 (2026-07-06). D1→Aurora PostgreSQL, Cloudflare Workers→AWS Lambda (ExBot Lambda), "Status Update Worker"→"ExBot Lambda". Architecture header updated. Q14, Q15 noted (naming consistency — no impact on test scenarios). |

---

*Test Scenarios — UC-EXBOT-pause-resume (Pause and Resume Bot) — 31 scenarios — generated by qc-func-scenario-design-exbot skill*
*Updated: 2026-07-06 (v2) — BA ARC Migration (2026-07-04)*
*BLOCKED tags removed — Q2, Q3, Q7, Q8, Q9 resolved by BA (2026-07-03)*
