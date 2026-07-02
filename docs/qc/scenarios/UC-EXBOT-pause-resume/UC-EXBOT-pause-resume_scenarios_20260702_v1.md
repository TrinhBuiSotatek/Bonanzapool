# Test Scenarios — UC-EXBOT-pause-resume: Pause and Resume Bot

> Source: `docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260630_v1.md`
> Generated: 2026-07-02
> Domain/Architecture: API/backend ExBot — Cloudflare Workers + Hyperliquid + D1 + Operator Facade `/api/exbot/*`, no UI

---

## UC-EXBOT-pause-resume — Pause and Resume Bot

### Scenario ID: TS_EXBOT_PAUSE_001
**Scenario Title:** Happy path — Investor pauses active bot; hedge and LP positions preserved
**UC Reference:** UC-EXBOT-pause-resume §3
**Req-ID:** FR-EXBOT-005; AC-01; AC-08; BR-EXBOT-002
**Test Type:** Functional
**Description:** Investor sends pause request for a bot with `bots.status='active'` and `bots.lifecycle_state='active'`. The system sets `bots.status='paused'`, persists atomically to D1, and returns API response `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }`. After pause, `bots.lifecycle_state` remains `'active'`, `hedge_legs.last_known_hl_short_size` is unchanged, and `positions.token_id` is unchanged.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_002
**Scenario Title:** Happy path — Investor resumes paused bot; light-check scheduled within 5 minutes
**UC Reference:** UC-EXBOT-pause-resume §4
**Req-ID:** FR-EXBOT-005; AC-02; AC-09
**Test Type:** Functional
**Description:** Investor sends resume request for a bot with `bots.status='paused'`. The system restores `bots.status='active'`, confirms `bots.lifecycle_state` unchanged, sets `bot_runtime_state.next_light_check_at = now + 5min + jitter(−45s, +45s)`, enqueues a `light-check` message, and returns `{ status: "active", message: "Bot resumed. Monitoring resumed." }`. Audit log records "Bot resumed by investor".
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_003
**Scenario Title:** Pause rejected with E-EXBOT-013 when bot is in safe_mode
**UC Reference:** UC-EXBOT-pause-resume §5 A1
**Req-ID:** FR-EXBOT-050; AC-03
**Test Type:** Functional
**Description:** Investor sends pause request for a bot with `bots.status='safe_mode'`. The system returns HTTP 409 with message: "Bot is in Safe Mode. You can close the bot instead." (verbatim E-EXBOT-013). No state change occurs in D1.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_EXBOT_PAUSE_004
**Scenario Title:** Pause request is idempotent — bot already paused
**UC Reference:** UC-EXBOT-pause-resume §5 A3
**Req-ID:** FR-EXBOT-005; AC-04
**Test Type:** Functional
**Description:** Investor sends pause request for a bot already with `bots.status='paused'`. The system returns a success response with message "Bot already paused. No change needed." No D1 record is modified.
**Test Focus:** Idempotency/Concurrency
**⏸ BLOCKED:** Q3 — Idempotency mechanism for pause/resume has not been defined in the UC. Tester must confirm the idempotency key and implementation with Tech Lead before finalizing this scenario's expected result structure.

---

### Scenario ID: TS_EXBOT_PAUSE_005
**Scenario Title:** Resume request is idempotent — bot already active
**UC Reference:** UC-EXBOT-pause-resume §5 A2
**Req-ID:** FR-EXBOT-005; AC-05
**Test Type:** Functional
**Description:** Investor sends resume request for a bot already with `bots.status='active'`. The system returns a success response with message "Bot already active. No change needed." No D1 record is modified.
**Test Focus:** Idempotency/Concurrency
**⏸ BLOCKED:** Q3 — Same as TS_EXBOT_PAUSE_004.

---

### Scenario ID: TS_EXBOT_PAUSE_006
**Scenario Title:** Audit log entry is recorded after successful pause
**UC Reference:** UC-EXBOT-pause-resume §7 Postconditions
**Req-ID:** FR-EXBOT-005; AC-08
**Test Type:** Functional
**Description:** Investor successfully pauses an active bot. The system records an audit log entry with content "Bot paused by investor" and a timestamp in D1.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_007
**Scenario Title:** Audit log entry is recorded after successful resume
**UC Reference:** UC-EXBOT-pause-resume §7 Postconditions
**Req-ID:** FR-EXBOT-005; AC-09
**Test Type:** Functional
**Description:** Investor successfully resumes a paused bot. The system records an audit log entry with content "Bot resumed by investor" and a timestamp in D1.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_008
**Scenario Title:** Hedge short position size is unchanged after pause
**UC Reference:** UC-EXBOT-pause-resume §3 step 5
**Req-ID:** BR-EXBOT-002; AC-10
**Test Type:** Functional
**Description:** Bot has an active HL short position with `hedge_legs.last_known_hl_short_size = X ETH`. Investor pauses the bot. After pause, `hedge_legs.last_known_hl_short_size = X ETH` — exactly the same value. No HL order (close, adjust, or cancel) is submitted to Hyperliquid during the pause operation.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_009
**Scenario Title:** LP NFT token ID is unchanged after pause
**UC Reference:** UC-EXBOT-pause-resume §3 step 6
**Req-ID:** BR-EXBOT-002; AC-11
**Test Type:** Functional
**Description:** Bot has an active LP NFT with `positions.token_id = N`. Investor pauses the bot. After pause, `positions.token_id = N` — exactly the same value. No vault transaction (redeem, transfer, or approval) is submitted to BnzaExVault during the pause operation.
**Test Focus:** Happy path

---

### Scenario ID: TS_EXBOT_PAUSE_010
**Scenario Title:** Light-check worker skips entirely for paused bot; no hedge-sync enqueued
**UC Reference:** UC-EXBOT-pause-resume §6
**Req-ID:** FR-EXBOT-012; AC-06
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. A cron-triggered `light-check` message is delivered to the light-check worker for this bot. The worker skips the entire light-check evaluation — does not compute delta, does not evaluate drift/range/funding conditions, and does not enqueue a `hedge-sync` message.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_011
**Scenario Title:** Hedge-sync worker does not execute adjustments for paused bot
**UC Reference:** UC-EXBOT-pause-resume §6
**Req-ID:** FR-EXBOT-005; AC-06
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. A `hedge-sync` message is delivered to the hedge-sync worker (e.g., from a previously enqueued message). The worker does not submit any HL order and does not modify `hedge_legs` records.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_012
**Scenario Title:** Deep-audit continues on 6-hour cadence for paused bot
**UC Reference:** UC-EXBOT-pause-resume §6
**Req-ID:** FR-EXBOT-016; AC-07
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` under normal conditions (circuit_breakers.state='closed' and margin_status='ok'). The deep-audit cron fires its scheduled run. The deep-audit worker fetches clearinghouseState from HL, verifies short size matches `hedge_legs.last_known_hl_short_size`, updates `hedge_legs.margin_status`, and detects no anomalies.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_013
**Scenario Title:** Deep-audit runs on 1-hour high-risk cadence for paused bot when system is in high-risk mode
**UC Reference:** UC-EXBOT-pause-resume §6
**Req-ID:** FR-EXBOT-016
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` AND `circuit_breakers.state != 'closed'` (circuit breaker is open). The deep-audit cron fires. The system runs deep-audit at the 1-hour interval instead of the standard 6-hour interval. The worker fetches HL state and updates margin status.
**Test Focus:** State transition
**Note:** Evidence from FR-EXBOT-016: "In high-risk mode (circuit_breakers.state != 'closed' or margin_status IN ('warning','critical')), the interval reduces to 1 hour."

---

### Scenario ID: TS_EXBOT_PAUSE_014
**Scenario Title:** price-near-stop-audit continues for paused bot — stop monitoring never suppressed
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-014
**Req-ID:** FR-EXBOT-014
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. A light-check pass evaluates stop trigger detection for this bot. Even though light-check is skipped for a paused bot, stop monitoring (price-near-stop-audit enqueue) continues "at all times" per FR-EXBOT-014. The system enqueues a `price-near-stop-audit` message if the ETH mark price is near or above `stop_price`.
**Test Focus:** State transition
**Note:** Evidence from FR-EXBOT-014: "Stop monitoring shall continue at all times — including when circuit_breakers.state='open'. Light-check shall never suppress stop price evaluation or price-near-stop-audit enqueue."

---

### Scenario ID: TS_EXBOT_PAUSE_015
**Scenario Title:** Bot transitions to safe_mode when deep-audit detects anomaly on paused bot
**UC Reference:** UC-EXBOT-pause-resume §6; states.md state registry
**Req-ID:** FR-EXBOT-050; FR-EXBOT-033
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'`. Deep-audit runs and detects a SAFE_MODE entry condition (e.g., `stop_trigger_crossed_at` stuck > 30 minutes). The system transitions `bots.status` from `'paused'` to `'safe_mode'`. The `bots.lifecycle_state` remains at its pre-pause value (unchanged). The `stop_trigger_crossed_at` stuck detection initiates SAFE_MODE per FR-EXBOT-033.
**Test Focus:** State transition
**Note:** Evidence from states.md state registry: `safe_mode` and `paused` are independent coarse-grained states. `bots.status` transitions from `paused` to `safe_mode` while `lifecycle_state` is preserved.

---

### Scenario ID: TS_EXBOT_PAUSE_016
**Scenario Title:** Pause not allowed when bot is in closed or transitional lifecycle_state
**UC Reference:** UC-EXBOT-pause-resume §2; states.md state registry
**Req-ID:** FR-EXBOT-005; FR-EXBOT-003
**Test Type:** Functional
**Description:** Investor sends pause request for a bot with `bots.status='active'` but `bots.lifecycle_state` is one of the transitional states (`preflight`, `lp_opening`, `lp_opened`, `hedge_pre_open`, `hedge_post_confirmed`, `stop_placing`, `stop_verified`, `lp_closing`, `closed`, or `error`). The system returns HTTP 409 with message "Bot is not in a state that supports pause." (or equivalent — exact message not defined in UC; tester to use the actual error message returned).
**Test Focus:** Error/Exception
**⏸ BLOCKED:** Q7 — UC §2 only mentions `lifecycle_state='active'` as the pause precondition. The UC does not explicitly state whether transitional states are rejected. BA to confirm: is `lifecycle_state='active'` the ONLY valid state for pause, or do all non-terminal runtime states support pause?

---

### Scenario ID: TS_EXBOT_PAUSE_017
**Scenario Title:** Pause allowed when bot lifecycle_state is hedge_stopped_cooldown or lp_rebalancing
**UC Reference:** states.md state registry; UC §2
**Req-ID:** FR-EXBOT-003; FR-EXBOT-005
**Test Type:** Functional
**Description:** Bot has `bots.status='active'` and `bots.lifecycle_state='hedge_stopped_cooldown'` (or `'lp_rebalancing'`). Investor sends pause request. The system sets `bots.status='paused'` and preserves `bots.lifecycle_state` at its current value. This scenario verifies that pause does not require `lifecycle_state='active'` exclusively.
**Test Focus:** State transition
**⏸ BLOCKED:** Q7 — states.md state registry row `(pre-pause value) | paused` suggests all lifecycle_state values can be paused, but UC §2 only names `active`. BA to confirm: is pause allowed from `hedge_stopped_cooldown` and `lp_rebalancing` states?

---

### Scenario ID: TS_EXBOT_PAUSE_018
**Scenario Title:** Investor cannot pause another investor's bot
**UC Reference:** UC-EXBOT-pause-resume §1; FR-EXBOT-001
**Req-ID:** FR-EXBOT-001
**Test Type:** Functional
**Description:** Investor A (user_id=U1) owns an active bot with `bots.status='active'`. Investor B (user_id=U2) sends a pause request specifying Investor A's bot_id. The system rejects the request with HTTP 403 or 404 (bot not found for this user) — Investor B has no authorization to pause Investor A's bot.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_EXBOT_PAUSE_019
**Scenario Title:** Investor cannot pause a bot that does not exist
**UC Reference:** UC-EXBOT-pause-resume §2
**Req-ID:** FR-EXBOT-005
**Test Type:** Functional
**Description:** Investor sends a pause request with a non-existent `botId`. The system returns HTTP 404 with an appropriate error message — no bot record is created.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_EXBOT_PAUSE_020
**Scenario Title:** Concurrent duplicate pause requests are handled safely
**UC Reference:** UC-EXBOT-pause-resume §5 A3
**Req-ID:** FR-EXBOT-011; UC §3 step 3 (atomic persistence)
**Test Type:** Idempotency/Concurrency
**Description:** Investor sends two simultaneous pause requests for the same active bot. The system processes exactly one state change to `bots.status='paused'`. The second request receives the idempotent success response "Bot already paused. No change needed." — no error, no partial state, no race condition in D1.
**Test Focus:** Idempotency/Concurrency
**⏸ BLOCKED:** Q2 — Worker architecture (synchronous handler vs queue consumer) is not defined. Q3 — Idempotency mechanism is not defined. Tester must confirm both with Tech Lead before finalizing this scenario.

---

### Scenario ID: TS_EXBOT_PAUSE_021
**Scenario Title:** Concurrent pause and resume requests for the same bot are handled safely
**UC Reference:** UC-EXBOT-pause-resume §5 A2, A3
**Req-ID:** FR-EXBOT-011
**Test Type:** Idempotency/Concurrency
**Description:** Investor sends a pause request and a resume request for the same bot simultaneously. The system serializes the two operations correctly — either order is acceptable as long as the final `bots.status` is one of the two valid end states (`active` or `paused`) and no error occurs. Audit log entries are recorded for each operation.
**Test Focus:** Idempotency/Concurrency
**⏸ BLOCKED:** Q2 and Q3 — Same as TS_EXBOT_PAUSE_020.

---

### Scenario ID: TS_EXBOT_PAUSE_022
**Scenario Title:** Resume reschedules light-check with correct jitter timing
**UC Reference:** UC-EXBOT-pause-resume §4 step 5
**Req-ID:** FR-EXBOT-013; AC-02
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` with `bot_runtime_state.next_light_check_at` set far in the past (expired schedule). Investor resumes the bot. The system sets `next_light_check_at = now + 5min + jitter(−45s, +45s)`. The jitter value is within the range [now + 4m15s, now + 5m45s]. A `light-check` message is enqueued.
**Test Focus:** Happy path
**Note:** Evidence from FR-EXBOT-013: `next_light_check_at = now + 5min + random(−45s, +45s)`. Same jitter formula applies to resume scheduling as to normal scheduling.

---

### Scenario ID: TS_EXBOT_PAUSE_023
**Scenario Title:** Pause does not trigger any Hyperliquid API calls
**UC Reference:** UC-EXBOT-pause-resume §3–4; FR-EXBOT-012
**Req-ID:** BR-EXBOT-003; FR-EXBOT-012
**Test Type:** Integration
**Description:** Investor pauses an active bot. During the pause operation, the system makes zero calls to the Hyperliquid API. No `hedge_legs` fields are updated from HL. The pause operation relies solely on D1 state.
**Test Focus:** Integration
**Note:** ExBot is a backend-only module. The API response content is verified as the system output, not as a UI rendering. Confirmation message text comes from the API response.

---

### Scenario ID: TS_EXBOT_PAUSE_024
**Scenario Title:** Resume does not trigger any Hyperliquid API calls
**UC Reference:** UC-EXBOT-pause-resume §4
**Req-ID:** BR-EXBOT-003
**Test Type:** Integration
**Description:** Investor resumes a paused bot. During the resume operation, the system makes zero calls to the Hyperliquid API. No HL position fetch, no order placement, no margin check against HL. The light-check message is enqueued, but light-check itself is a separate worker that makes no HL calls per BR-EXBOT-003.
**Test Focus:** Integration

---

### Scenario ID: TS_EXBOT_PAUSE_025
**Scenario Title:** Pause/resume operation uses atomic D1 write — no partial state on worker crash
**UC Reference:** UC-EXBOT-pause-resume §3 step 3, §4 step 3
**Req-ID:** FR-EXBOT-005
**Test Type:** Data/State
**Description:** Investor sends a pause request. The worker starts updating D1 (`bots.status='paused'`) but crashes mid-transaction. The system must ensure D1 remains at the previous consistent state (`bots.status='active'`) — no partial write, no inconsistent `bots.status` value.
**Test Focus:** Data/State
**⏸ BLOCKED:** Q2 — Worker architecture determines how atomicity is enforced (database transaction vs application-level lock). Tech Lead to confirm.

---

### Scenario ID: TS_EXBOT_PAUSE_026
**Scenario Title:** Bot in safe_mode transitions to safe_mode when deep-audit detects margin critical on paused bot
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-050; FR-EXBOT-016
**Req-ID:** FR-EXBOT-050; FR-EXBOT-060
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` and `hedge_legs.margin_status='warning'`. Deep-audit runs and detects `margin_status='critical'` for the second consecutive time. Per FR-EXBOT-050, the system initiates SAFE_MODE. The bot's `bots.status` transitions from `'paused'` to `'safe_mode'`. `bots.lifecycle_state` is preserved.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_027
**Scenario Title:** light-check worker check uses bots.status='paused' as skip gate
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-012
**Req-ID:** FR-EXBOT-012
**Test Type:** Data/State
**Description:** A bot is transitioning from `active` to `paused`. Verify that the light-check worker evaluates `bots.status='paused'` as a skip condition BEFORE evaluating any rebalance criteria (drift, range, funding). The worker must not evaluate rebalance logic for a paused bot — skip must happen at the bot eligibility gate.
**Test Focus:** State transition

---

### Scenario ID: TS_EXBOT_PAUSE_028
**Scenario Title:** Safe_mode entry condition stop_trigger_crossed_at stuck > 30min triggers SAFE_MODE from paused state
**UC Reference:** UC-EXBOT-pause-resume §6; FR-EXBOT-033; FR-EXBOT-050
**Req-ID:** FR-EXBOT-033
**Test Type:** Functional
**Description:** Bot has `bots.status='paused'` with `hedge_legs.stop_trigger_crossed_at` set and age > 30 minutes (stuck stop trigger). Deep-audit runs and detects this condition. The system transitions `bots.status` from `'paused'` to `'safe_mode'` per FR-EXBOT-033.
**Test Focus:** State transition
**Note:** Evidence from states.md state registry: SAFE_MODE is a separate coarse-grained state. `bots.lifecycle_state` is preserved at the pre-pause value.

---

### Scenario ID: TS_EXBOT_PAUSE_029
**Scenario Title:** Pause operation does not affect rebalance_attempts or lp_operations ledger
**UC Reference:** UC-EXBOT-pause-resume §3–4; erd.md
**Req-ID:** FR-EXBOT-005
**Test Type:** Data/State
**Description:** Bot has existing records in `rebalance_attempts` and `lp_operations`. Investor pauses the bot. After pause, all existing records in `rebalance_attempts` and `lp_operations` remain unchanged — no new rows are inserted, no existing rows are modified.
**Test Focus:** Data/State

---

### Scenario ID: TS_EXBOT_PAUSE_030
**Scenario Title:** Pause/resume API response message is verified verbatim from response body
**UC Reference:** UC-EXBOT-pause-resume §3 step 7, §4 step 6
**Req-ID:** FR-EXBOT-005
**Test Type:** Acceptance
**Description:** Investor pauses a bot. The API response body contains `message: "Paused — hedge is maintained, LP is maintained"`. The tester verifies this exact message text (or the exact Vietnamese localization if the system uses locale-specific messages). No placeholder or generic message is returned.
**Test Focus:** Acceptance
**⏸ BLOCKED:** Q8 — ExBot is backend-only per spec.md §6. The "investor receives UI confirmation" in the UC is the POOL UI (PTL-05) rendering the API response, not an ExBot UI element. BA to confirm: does ExBot scope include verifying the API response message text, or does POOL UI own the message display?
**Note:** No message code (E-code or MSG-code) exists for this success message in message-list.md. Tester verifies text content directly from the response body.

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Performance testing (pause/resume latency, 10k-bot scan throughput) | NFR — Performance/load testing is out of scope for scenario design | Defer to performance test suite |
| Hyperliquid testnet account provisioning, wallet funding | Environment/infra setup — not a scenario design item | QC Lead / Ops to arrange test accounts |
| POOL UI (PTL-05) message rendering | Q8 — ExBot is backend-only; POOL UI is out of ExBot scope | BA to confirm whether API response message verification is ExBot scope or POOL UI scope |
| UI button labels / screen copy ("Pause Bot (hedge is maintained)") | Q8 — BR-EXBOT-002 states UI must use distinct labels for pause vs close; but ExBot module does not own UI screens | BA to confirm UI scope boundary |
| HL testnet environment setup, API keys, RPC endpoints | Dependency on Phase 0 gate (testnet access not yet confirmed) | QC Lead / Ops to arrange |
| Smart contract (BnzaExVault) integration test with real on-chain LP NFT | zen deploys contract; ABI/address not confirmed yet (NV-12) | Wait for Phase 0 gate |
| Worker architecture (synchronous handler vs queue consumer) | Q2 — blocked pending Tech Lead confirmation | Resolve via qc-qna before finalizing concurrency scenarios |
| Idempotency mechanism (key format, storage) | Q3 — blocked pending Tech Lead confirmation | Resolve via qc-qna before finalizing idempotency scenarios |
| Valid lifecycle_state values for pause/resume | Q7 — blocked pending BA confirmation | Resolve via qc-qna before finalizing state transition scenarios for hedge_stopped_cooldown and lp_rebalancing |
| Message codes for success responses | Q9 — blocked pending BA confirmation | Resolve via qc-qna before finalizing acceptance scenarios for API response text |

---

*Test Scenarios — UC-EXBOT-pause-resume (Pause and Resume Bot) — 30 scenarios — generated by qc-func-scenario-design-exbot skill (2026-07-02)*
