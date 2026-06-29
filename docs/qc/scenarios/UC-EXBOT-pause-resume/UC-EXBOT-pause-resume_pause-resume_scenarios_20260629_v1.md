---
title: "Test Scenarios — UC-EXBOT-pause-resume: Pause and Resume Bot"
date: 2026-06-29
author: qc-func-scenario-design-exbot
version: v1
---

# Test Scenarios — UC-EXBOT-pause-resume: Pause and Resume Bot

> Source: docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260618_v1.md (v1, 2026-06-18)
> Generated: 2026-06-29
> Domain/Architecture: Cloudflare Workers (ExBot Worker) + Cloudflare D1 (SQLite off-chain state) + Cloudflare Queues (light-check, deep-audit). No UI — tested through Operator Facade API (`POST /api/exbot/pause`, `POST /api/exbot/resume`).

---

## UC-EXBOT-pause-resume — Pause and Resume Bot

---

### Scenario ID: TS_UC-EXBOT-pause-resume_001
**Scenario Title:** Pause a bot that is in `status='active'` — happy path
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3, FR-EXBOT-005, AC-01
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` with a valid `botId` belonging to the authenticated investor, where the bot has `status='active'` and is not in `safe_mode`. The system must set `bots.status='paused'` in D1, leave `bots.lifecycle_state` unchanged, and return `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-pause-resume_002
**Scenario Title:** Pause a bot — verify HL short position is not modified
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3 step 5, FR-EXBOT-005, AC-08
**Test Type:** Data/State
**Description:** After successfully pausing a bot that had an open HL short at size X, verify that `hedge_legs.last_known_hl_short_size` still equals X and that no new HL order was submitted during the pause operation (no HL API mutation should occur).
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_003
**Scenario Title:** Pause a bot — verify LP NFT is not modified
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3 step 6, FR-EXBOT-005
**Test Type:** Data/State
**Description:** After successfully pausing a bot, verify that the `positions.token_id` stored in D1 remains unchanged and that no BnzaExVault operation was triggered. The LP NFT must be intact and held in the vault exactly as before the pause.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_004
**Scenario Title:** Pause a bot — verify `lifecycle_state` is not changed
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3 step 4, FR-EXBOT-005, AC-01
**Test Type:** Data/State
**Description:** After pausing a bot that had `lifecycle_state='active'`, verify that `bots.lifecycle_state` is still `'active'` in D1. The pause operation must only modify `bots.status`; it must not write to `lifecycle_state`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-pause-resume_005
**Scenario Title:** Pause rejected when bot is in `status='safe_mode'`
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 A1, E-EXBOT-013, AC-03
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` for a bot with `bots.status='safe_mode'`. The system must return HTTP 409 with message "Bot is in Safe Mode. You can close the bot instead." No change to `bots.status` or any other D1 field must occur.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_006
**Scenario Title:** Pause is idempotent — bot already paused
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 A3, AC-04
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` for a bot that already has `bots.status='paused'`. The system must return a success response with message "Bot already paused. No change needed." without modifying any D1 field and without triggering any downstream queue message.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_007
**Scenario Title:** Resume a bot that is in `status='paused'` — happy path
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §4, FR-EXBOT-005, AC-02
**Test Type:** Functional
**Description:** Send `POST /api/exbot/resume` with a valid `botId` belonging to the investor, where the bot has `bots.status='paused'`. The system must set `bots.status='active'` in D1, leave `bots.lifecycle_state` unchanged, set `bots.next_light_check_at` to `now + 5 min ± 45 s`, enqueue a `light-check` message, and return `{ status: "active", message: "Bot resumed. Monitoring resumed." }`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-pause-resume_008
**Scenario Title:** Resume — verify `next_light_check_at` is scheduled within correct window
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §4 step 5, FR-EXBOT-005, FR-EXBOT-013, AC-02
**Test Type:** Data/State
**Description:** After a successful resume, read `bots.next_light_check_at` from D1 and verify that its value falls within the window `[now + 4m15s, now + 5m45s]` (i.e. `5 min ± 45 s` relative to the resume timestamp). Values outside this window indicate a jitter implementation error.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-pause-resume_009
**Scenario Title:** Resume — verify `light-check` message is enqueued after resume
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §4 step 5, FR-EXBOT-005, FR-EXBOT-010, AC-02
**Test Type:** Integration
**Description:** After a successful resume, verify that exactly one `light-check` queue message has been enqueued for the resumed bot. The message must follow the queue contract defined in FR-EXBOT-010 and be consumable by the light-check worker without format error.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-pause-resume_010
**Scenario Title:** Resume — `lifecycle_state` must remain unchanged after resume
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §4 step 4, FR-EXBOT-005
**Test Type:** Data/State
**Description:** Before pausing the bot, record the value of `bots.lifecycle_state`. After resuming, verify that `bots.lifecycle_state` still equals that pre-pause value. Neither the pause nor the resume operation must write to `lifecycle_state`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-pause-resume_011
**Scenario Title:** Resume is idempotent — bot already active
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 A2, AC-05
**Test Type:** Functional
**Description:** Send `POST /api/exbot/resume` for a bot that already has `bots.status='active'`. The system must return a success response with message "Bot already active. No change needed." without modifying any D1 field and without enqueuing a `light-check` message.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_012
**Scenario Title:** Light-check is skipped while bot is paused
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §6, FR-EXBOT-012, AC-07
**Test Type:** Integration
**Description:** While a bot is in `bots.status='paused'`, simulate a `bot-scan` cron tick that would normally enqueue a `light-check` message. Verify that the paused bot is excluded from the `light-check` queue — no `light-check` message is produced for the paused bot in that cycle.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-pause-resume_013
**Scenario Title:** Hedge-sync is not triggered while bot is paused
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §6, FR-EXBOT-012
**Test Type:** Integration
**Description:** While a bot is in `bots.status='paused'`, simulate conditions that would normally trigger a `hedge-sync` message (e.g., drift threshold exceeded according to D1 state). Verify that no `hedge-sync` message is produced — because light-check itself is skipped for paused bots, the hedge-sync fan-out cannot occur.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-pause-resume_014
**Scenario Title:** Deep-audit continues every 6 hours while bot is paused
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §6, FR-EXBOT-016, AC-06
**Test Type:** Integration
**Description:** While a bot is in `bots.status='paused'`, trigger a `deep-audit` cron cycle. Verify that the paused bot appears in the `deep-audit` queue and that the deep-audit worker processes it (fetches `clearinghouseState` from HL, updates `hedge_legs.margin_status`, checks for stuck stop markers). The bot must NOT be excluded from deep-audit based solely on its paused status.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-pause-resume_015
**Scenario Title:** SAFE_MODE detection via deep-audit continues while bot is paused
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §6, FR-EXBOT-016, FR-EXBOT-050
**Test Type:** Integration
**Description:** While a bot is `paused`, deep-audit detects a condition that would normally trigger SAFE_MODE (e.g., `stop_trigger_crossed_at` stuck for more than 30 minutes). Verify that SAFE_MODE entry is not blocked by the `paused` status — the bot transitions to `bots.status='safe_mode'` as expected.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-pause-resume_016
**Scenario Title:** Pause → Resume round-trip — full state consistency check
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3, UC §4, FR-EXBOT-005, AC-01, AC-02
**Test Type:** End-to-End
**Description:** Execute the complete pause → resume cycle: (1) record the bot's initial D1 state (`status`, `lifecycle_state`, `next_light_check_at`, `hedge_legs.last_known_hl_short_size`, `positions.token_id`); (2) call `POST /api/exbot/pause`; (3) verify paused state; (4) call `POST /api/exbot/resume`; (5) verify `status='active'`, `lifecycle_state` unchanged, `next_light_check_at` updated, `light-check` enqueued, HL short size unchanged, LP NFT unchanged.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-pause-resume_017
**Scenario Title:** Acceptance criteria AC-01 — verify exact pause response body shape and HTTP 200 (response contract only)
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** AC-01, FR-EXBOT-005
**Test Type:** Acceptance
**Description:** Send `POST /api/exbot/pause` for a bot with `status='active'`. Verify that the HTTP response status is exactly 200 and the response body JSON contains exactly the two fields `status: "paused"` and `message: "Paused — hedge is maintained, LP is maintained"` — with no extraneous fields and no variation in casing or wording. This scenario verifies the API response contract only; D1 state changes (`bots.status`, `lifecycle_state`) are covered by TS_UC-EXBOT-pause-resume_001 and TS_UC-EXBOT-pause-resume_004.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-pause-resume_018
**Scenario Title:** Acceptance criteria AC-02 — verify exact resume response body shape and HTTP 200 (response contract only)
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** AC-02, FR-EXBOT-005
**Test Type:** Acceptance
**Description:** Send `POST /api/exbot/resume` for a bot with `status='paused'`. Verify that the HTTP response status is exactly 200 and the response body JSON contains exactly the two fields `status: "active"` and `message: "Bot resumed. Monitoring resumed."` — with no extraneous fields and no variation in casing or wording. This scenario verifies the API response contract only; D1 state changes (`bots.status`, `next_light_check_at`) and queue enqueue behavior are covered by TS_UC-EXBOT-pause-resume_007, TS_UC-EXBOT-pause-resume_008, and TS_UC-EXBOT-pause-resume_009.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-pause-resume_019
**Scenario Title:** Acceptance criteria AC-03 — pause rejected in SAFE_MODE produces no queue side effects
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** AC-03, E-EXBOT-013
**Test Type:** Acceptance
**Description:** With a bot in `bots.status='safe_mode'`, send `POST /api/exbot/pause`. Verify that no queue messages were enqueued on any Cloudflare Queue (light-check, hedge-sync, bot-scan, or deep-audit) as a side effect of the rejected request — the rejection must be fully side-effect-free. HTTP 409 and the verbatim error message are covered by TS_UC-EXBOT-pause-resume_005; this scenario focuses exclusively on the absence of queue side effects upon rejection.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_020
**Scenario Title:** Pause rejected for a bot that is in `status='closing'`
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 (I-005 — missing alternate flow), FR-EXBOT-003
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` for a bot with `bots.status='closing'`. The system must reject the request (no D1 state change). The expected HTTP status and error message are pending BA confirmation (I-005 in audited report). This scenario is in scope for coverage but the expected result must be confirmed before marking as passed.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_021
**Scenario Title:** Pause rejected for a bot that is in `status='error'`
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 (I-005 — missing alternate flow)
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` for a bot with `bots.status='error'`. The system must reject the request (no D1 state change). The expected HTTP status and error message are pending BA confirmation (I-005 in audited report).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_022
**Scenario Title:** Resume rejected for a bot that is in `status='closing'`
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 (I-005 — missing alternate flow)
**Test Type:** Functional
**Description:** Send `POST /api/exbot/resume` for a bot with `bots.status='closing'`. The system must reject the request. Expected HTTP status and error message pending BA (I-005).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_023
**Scenario Title:** Resume rejected for a bot that is in `status='safe_mode'`
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 (I-005 — missing alternate flow), FR-EXBOT-050
**Test Type:** Functional
**Description:** Send `POST /api/exbot/resume` for a bot with `bots.status='safe_mode'`. The system must reject the resume because a bot in `safe_mode` cannot be manually resumed — it auto-recovers only via the deep-audit cycle (3 reconciles + margin ok). Expected HTTP status and error message pending BA (I-005).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_024
**Scenario Title:** Authorization — pause a bot that does not belong to the requesting investor
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §2, UC §3 step 1 (I-004 — missing alternate flow)
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` using Investor A's credentials but with a `botId` that belongs to Investor B. The system must reject the request (authorization failure — IDOR protection). Expected HTTP status and error message are pending BA confirmation (I-004 in audited report).
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-pause-resume_025
**Scenario Title:** Authorization — resume a bot that does not belong to the requesting investor
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §2, UC §4 step 1 (I-004 — missing alternate flow)
**Test Type:** Functional
**Description:** Send `POST /api/exbot/resume` using Investor A's credentials but with a `botId` belonging to Investor B. The system must reject the request. Expected HTTP status and error message pending BA (I-004).
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-pause-resume_026
**Scenario Title:** Pause with a non-existent `botId`
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3 step 1 (I-004 — missing alternate flow)
**Test Type:** Functional
**Description:** Send `POST /api/exbot/pause` with a `botId` that does not exist in D1. The system must return a 4xx error indicating the bot was not found or is not accessible. Expected HTTP status and error message pending BA (I-004).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-pause-resume_027
**Scenario Title:** Concurrent pause requests for the same bot — race condition
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3 step 3 ("atomic write"), BR-EXBOT-002 (implied)
**Test Type:** Data/State
**Description:** Send two simultaneous `POST /api/exbot/pause` requests for the same bot (both arriving while `status='active'`). The D1 atomic write must ensure that exactly one request transitions the bot to `paused` and the other returns the idempotent response "Bot already paused. No change needed." No race condition should result in duplicate writes or inconsistent state.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_028
**Scenario Title:** Concurrent pause and resume requests — last-write-wins check
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §3 step 3, UC §4 step 3
**Test Type:** Data/State
**Description:** Send a `POST /api/exbot/pause` and a `POST /api/exbot/resume` concurrently for the same bot. Verify that the final `bots.status` in D1 is deterministic and consistent with one of the two operations winning atomically. No intermediate or corrupt state should be written.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_029
**Scenario Title:** `next_light_check_at` boundary — jitter exactly at lower bound (`now + 4m15s`)
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §4 step 5, FR-EXBOT-013
**Test Type:** Data/State
**Description:** After resume, verify that `bots.next_light_check_at` is never set earlier than `now + 4m15s`. Values below this lower bound indicate a jitter implementation defect (`random(-45s)` yielding a value outside the allowed range).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-pause-resume_030
**Scenario Title:** `next_light_check_at` boundary — jitter exactly at upper bound (`now + 5m45s`)
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §4 step 5, FR-EXBOT-013
**Test Type:** Data/State
**Description:** After resume, verify that `bots.next_light_check_at` is never set later than `now + 5m45s`. Values above this upper bound indicate a jitter implementation defect (`random(+45s)` exceeding the allowed range).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-pause-resume_031
**Scenario Title:** `next_light_check_at` is NOT updated on resume when already-active (idempotent resume)
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §5 A2, AC-05
**Test Type:** Data/State
**Description:** Record `bots.next_light_check_at` for an `active` bot. Then call `POST /api/exbot/resume` (idempotent — bot already active). Verify that `bots.next_light_check_at` is NOT modified and no `light-check` message is enqueued. The idempotent resume must produce zero side effects.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-pause-resume_032
**Scenario Title:** BR-EXBOT-002 — Pause does not trigger LP liquidation or hedge closure
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** BR-EXBOT-002, FR-EXBOT-005
**Test Type:** Functional
**Description:** Perform a pause operation. Confirm that the system does not initiate any LP close via BnzaExVault and does not send any HL order to reduce or close the short position. This verifies BR-EXBOT-002: "Pause keeps hedge and LP intact; only new mutations are stopped."
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-pause-resume_033
**Scenario Title:** Bot in `lifecycle_state='hedge_stopped_cooldown'` with `status='active'` — pause behavior
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** I-001 (open question — lifecycle_state precondition conflict), FR-EXBOT-003
**Test Type:** Functional
**Description:** A bot can have `bots.status='active'` but `bots.lifecycle_state='hedge_stopped_cooldown'` (stop fired but 4h cooldown has not elapsed). Send `POST /api/exbot/pause` for such a bot. Based on FR-EXBOT-005 (which has no `lifecycle_state` constraint), the system should accept the pause. The expected behavior is pending BA confirmation (I-001 in audited report). This scenario verifies the conflict between UC §2 (`lifecycle_state='active'` required) and SRS FR-EXBOT-005 (no such constraint).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-pause-resume_034
**Scenario Title:** Bot in `lifecycle_state='lp_rebalancing'` — pause behavior
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** I-001 (open), FR-EXBOT-003, FR-EXBOT-015
**Test Type:** Functional
**Description:** A bot can be `status='active'` and `lifecycle_state='lp_rebalancing'` (during range rebalance). Send `POST /api/exbot/pause`. Based on UC §2 requiring `lifecycle_state='active'`, this pause should be rejected. However, FR-EXBOT-005 has no such constraint. Expected result pending BA (I-001).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-pause-resume_035
**Scenario Title:** Deep-audit in high-risk mode continues at 1-hour interval while paused
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §6, FR-EXBOT-016
**Test Type:** Integration
**Description:** While a bot is `paused` and `circuit_breakers.state='open'` (high-risk mode), verify that deep-audit is scheduled at the 1-hour cadence rather than 6-hour cadence. The paused status must not override the high-risk interval shortening defined in FR-EXBOT-016.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-pause-resume_036
**Scenario Title:** End-to-end flow: Pause → deep-audit detects margin warning → Resume → light-check fires
**UC Reference:** UC-EXBOT-pause-resume — Pause and Resume Bot
**Req-ID:** UC §6, FR-EXBOT-005, FR-EXBOT-016, AC-06
**Test Type:** End-to-End
**Description:** (1) Pause a bot. (2) While paused, simulate a deep-audit cycle that updates `hedge_legs.margin_status='warning'` (because HL margin deteriorated). (3) Verify margin status updated in D1 and investor notification sent. (4) Resume the bot. (5) Verify `light-check` is enqueued and, once the light-check worker processes it, hedge-sync is evaluated (not suppressed) because the bot is now `active`.
**Test Focus:** Integration

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Pause/resume performance (SLA for D1 write latency) | NFR: PERFORMANCE — no SLA defined in the UC or SRS for pause/resume operations | Defer to performance testing track if SLA is added in future |
| Security testing beyond functional authorization (e.g., JWT bypass, brute-force) | NFR: SECURITY — out of scope for functional scenario design | Defer to security audit/penetration testing |
| Audit log verification (who paused the bot, timestamp, actor) | BLOCKED: I-003 — no D1 audit log table defined in ERD; no FR in SRS for pause/resume audit logging. Tester cannot verify this postcondition. | Resolve via qc-qna (I-003) + re-audit before adding audit-log scenarios |
| Pause/resume when `botId` is invalid or not owned (exact HTTP status and message) | BLOCKED: I-004 — alternate flow for unauthorized `botId` is missing from UC §3/§4. Expected response is unknown. | Resolve via qc-qna (I-004) + re-audit before finalizing TS_024/025/026 expected results |
| Pause/resume when `status='closing'` or `status='error'` | BLOCKED: I-005 — alternate flows for these statuses are not documented. Expected behavior is unknown. | Resolve via qc-qna (I-005) + re-audit before finalizing TS_020/021/022/023 expected results |
| Pause behavior when `lifecycle_state != 'active'` (e.g., `hedge_stopped_cooldown`, `lp_rebalancing`) | BLOCKED: I-001 — conflict between UC §2 precondition and SRS FR-EXBOT-005; BA must clarify | Resolve via qc-qna (I-001) + re-audit before finalizing TS_033/034 expected results |
| Stop monitoring (`price-near-stop-audit`) behavior during pause | BLOCKED: I-008 — UC §6 does not specify whether stop monitoring continues when `status='paused'`. FR-EXBOT-014 says stop monitoring is always active, but UC §6 omits this case. | Resolve via qc-qna (I-008) + re-audit; FR-EXBOT-014 strongly suggests it should continue |
| Expected message for SAFE_MODE pause rejection (`already in Safe Mode` vs. `in Safe Mode`) | BLOCKED: I-009 — US-EXBOT-003 AC-003-4 and E-EXBOT-013 in spec.md have different message texts. Must be resolved before writing test assertion. | Resolve via qc-qna (I-009); use spec.md verbatim as baseline for TS_019 until confirmed |
