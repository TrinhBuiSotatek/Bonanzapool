# Test Scenarios — UC-EXBOT-monitor-status: Monitor Bot Status

---
title: Test Scenarios — UC-EXBOT-monitor-status
date: 2026-06-29
author: qc-func-scenario-design-exbot
version: v2 (English)
---

> Source: docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260618_v1.md
> Generated: 2026-06-29
> Domain/Architecture: Cloudflare Workers (ExBot Worker standalone + Operator Facade) — D1 database, Durable Object (MarketDataDO), CF service binding, no UI
>
> **Note:** This UC was audited with verdict NOT READY (65/100). Skill proceeds at user's request.
> Coverage areas blocked by audit gaps are recorded in the ⚠️ Out-of-Scope Flags section.

---

## Reference Code Glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement for the ExBot module | srs/spec.md |
| BR-EXBOT-* | Business Rule at module level for ExBot | srs/spec.md §4 |
| UC-EXBOT-* | Use Case ID for the ExBot module | usecases/index.md |
| US-EXBOT-* | User Story ID | userstories/index.md |
| AC-EXBOT-* | Acceptance Criteria within a user story | userstories/us-002.md |
| lifecycle_state | Field `bots.lifecycle_state` — 18 canonical values tracking fine-grained bot state | srs/states.md, FR-EXBOT-003 |
| Operator Facade | Public-facing CF Worker that proxies `GET /api/exbot/status` to ExBot Worker via CF service binding + internal token. ExBot Worker is not internet-accessible | srs/spec.md FR-EXBOT-090 |
| MarketDataDO | Durable Object providing a shared cache of Uniswap V3 pool slot0 data (`sqrtPriceX96`, `currentTick`). All light-check workers read from this DO instead of making direct RPC calls | srs/spec.md FR-EXBOT-093 |
| SAFE_MODE | Bot state in which all mutation operations are blocked. Not a terminal state (BR-EXBOT-007) | srs/spec.md FR-EXBOT-050 |
| drift % | Percentage deviation of the actual HL short position size from the target size. Formula: `(|actualShortEth - targetShortEth| / targetShortEth) × 100` | UC §3 step 6, FR-EXBOT-021 |
| rangeState | Current tick position relative to the LP range (in / out-of-range) | UC §3 step 5, FR-EXBOT-012 |
| D1 | Cloudflare D1 — serverless SQLite database | project-context-master.md |
| HL | Hyperliquid — perpetuals trading exchange | project-context-master.md |
| cloid | Client Order ID — deterministic order identifier computed via keccak256 formula | FR-EXBOT-024 |

---

## UC-EXBOT-monitor-status — Monitor Bot Status

### Scenario ID: TS_UC-EXBOT-monitor-status_001
**Scenario Title:** Happy path — retrieve full bot status for an active bot with LP in-range and margin ok
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 Main Flow, FR-EXBOT-090, US-EXBOT-002 AC-002-1
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` via the Operator Facade for a bot with `lifecycle_state='active'`, `status='active'`, LP currently in-range (`tickLower <= currentTick < tickUpper`), and `margin_status='ok'`. The response must contain all fields: `status`, `lifecycle_state`, `tickLower`, `tickUpper`, `currentTick`, `rangeState='in'`, `hedgeSize`, `targetShortEth`, `driftPct`, `marginStatus='ok'`, `lastLightCheckAt` (or `nextLightCheckAt` — pending I-003 clarification). No warning banners should accompany the response.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_002
**Scenario Title:** Happy path — rangeState computed correctly when currentTick is exactly at tickLower boundary
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, FR-EXBOT-012
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when `currentTick == tickLower` (exact lower boundary). Per the rule `tickLower <= currentTick < tickUpper`, this case must return `rangeState='in'`. The response returns `rangeState='in'` with no out-of-range indicator.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_003
**Scenario Title:** Boundary — rangeState='out-of-range' when currentTick == tickUpper (upper boundary)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, FR-EXBOT-012
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when `currentTick == tickUpper` (exactly at the upper bound). Per the half-open interval rule `tickLower <= currentTick < tickUpper`, `currentTick = tickUpper` must return `rangeState='out-of-range'`. Response confirms `rangeState='out-of-range'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_004
**Scenario Title:** Boundary — rangeState='out-of-range' when currentTick == tickLower - 1 (just below lower bound)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, FR-EXBOT-012
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when `currentTick = tickLower - 1` (one tick below the lower bound). Response must return `rangeState='out-of-range'` because `currentTick < tickLower`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_005
**Scenario Title:** rangeState='out-of-range' when currentTick exceeds tickUpper (LP out-of-range above)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, FR-EXBOT-012, US-EXBOT-002 AC-002-1
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when the ETH price has moved above the LP range (`currentTick > tickUpper`). The response returns `rangeState='out-of-range'`; the fields `tickLower`, `tickUpper`, and `currentTick` reflect the actual values.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_006
**Scenario Title:** Alternative flow — bot in SAFE_MODE; response includes safe_mode indicator
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A1, US-EXBOT-002 AC-002-2, FR-EXBOT-050, BR-EXBOT-007
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when the bot has `bots.status='safe_mode'`. The response must include `status='safe_mode'`, `lifecycle_state='safe_mode'`, and a `safe_mode_reason` field (D1 source pending I-009 clarification). All client-side action buttons must be disabled except "Close Bot (emergency)". SAFE_MODE is not a terminal state — the response must not present it as "permanently closed" (BR-EXBOT-007).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_007
**Scenario Title:** Alternative flow — bot in hedge_stopped_cooldown; response includes cooldown indicator
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A2, US-EXBOT-002 AC-002-3, FR-EXBOT-034
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when the bot has `lifecycle_state='hedge_stopped_cooldown'` (stop trigger fired; within the 4-hour cooldown period). The response must include the cooldown end timestamp (D1 field pending I-010 clarification) so the client can calculate "Xh remaining". The response must also indicate that automatic re-hedging will occur after the cooldown.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_008
**Scenario Title:** Negative flow — no active bot for the user; returns HTTP 404
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A4
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` for a user who has no active bot. The response must return HTTP 404 with body containing "No active bot" (or equivalent per spec). No bot data is returned.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_009
**Scenario Title:** Exception flow — Operator Facade unavailable; returns HTTP 503
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A5, FR-EXBOT-090
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when the CF service binding from the Operator Facade to ExBot Worker is unavailable (e.g., ExBot Worker deployment failure or CF region outage). The response must return HTTP 503 with body "Status service temporarily unavailable". The client receives no bot data.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_010
**Scenario Title:** Security — ExBot Worker is not directly accessible from the internet (bypassing Facade)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** FR-EXBOT-090, BR-EXBOT-010
**Test Type:** Functional
**Description:** Send a direct HTTP request to ExBot Worker's endpoint (bypassing the Operator Facade) on any path. The response must return HTTP 403 Forbidden. ExBot Worker only accepts requests via CF service binding with an internal auth token — it must not be reachable from the public internet.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_011
**Scenario Title:** Integration — response data reflects the current D1 values at request time (eventual consistency)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 3, FR-EXBOT-025
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status` immediately after a hedge-sync has updated `bot_runtime_state.last_known_hl_short_size` and `hedge_legs.margin_status`. Verify that response fields `hedgeSize` and `marginStatus` reflect the latest values in D1. Note: D1 in CF Workers has eventual consistency — the response may briefly reflect slightly stale values within a few seconds of the write.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_012
**Scenario Title:** Integration — currentTick is sourced from MarketDataDO, not a direct RPC call
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 4, FR-EXBOT-093, BR-EXBOT-003
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status` and verify that ExBot Worker reads `currentTick` from `MarketDataDO` (the shared Durable Object cache) rather than making a direct RPC call to the Uniswap V3 pool. Logs or metrics must show no outbound on-chain RPC call during the monitor-status request processing. The `currentTick` in the response must match the current value cached in MarketDataDO.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_013
**Scenario Title:** Integration — Operator Facade correctly proxies ExBot Worker response to POOL UI
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 steps 2 and 8, FR-EXBOT-090
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status` via the Operator Facade and verify that: (1) the Facade forwards the request to ExBot Worker via CF service binding with the internal token; (2) the Facade forwards the response back to the caller without modifying, adding, or removing any field from ExBot Worker's JSON response.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_014
**Scenario Title:** Data/State — margin_status='warning' reflected in response with investor banner indicator
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** FR-EXBOT-060, srs/states.md §Margin Status
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` when `hedge_legs.margin_status='warning'` in D1 (i.e., `marginUsage` is between 0.55 and 0.75). The response must return `marginStatus='warning'`. The client UI should render an investor warning banner. Note: `margin_status` is updated only by hedge-sync and deep-audit — not by this UC.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_015
**Scenario Title:** Data/State — margin_status='critical' reflected in response with alert indicator
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** FR-EXBOT-060, FR-EXBOT-050, srs/states.md §Margin Status
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` when `hedge_legs.margin_status='critical'` in D1 (i.e., `marginUsage >= 0.75`). The response must return `marginStatus='critical'`. This is a pre-SAFE_MODE state — two consecutive critical readings trigger SAFE_MODE entry. The response must not be rendered identically to 'ok'.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_016
**Scenario Title:** Data/State — lifecycle_state='lp_rebalancing' returns correct transient state
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** FR-EXBOT-015, srs/states.md §State Registry
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` when the bot has `lifecycle_state='lp_rebalancing'` (LP range rebalance in progress). The response must correctly reflect `lifecycle_state='lp_rebalancing'` and `status='active'`. The UI must not show this bot as "stopped" or "error". This is a transient state — light-check and hedge-sync are suppressed during rebalancing.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_017
**Scenario Title:** Data/State — lifecycle_state='error' is displayed correctly, distinct from SAFE_MODE
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** srs/states.md §State Registry, FR-EXBOT-003
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` when the bot has `lifecycle_state='error'` and `status='error'` (state requiring admin intervention). The response must return `status='error'`, `lifecycle_state='error'`. This state is distinct from SAFE_MODE — there is no auto-recovery path. The UI must clearly differentiate "Error — Admin required" from "Safe Mode — No new actions".
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_018
**Scenario Title:** Data/State — lifecycle_state='closed' returns correct closed state
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** srs/states.md §State Registry, FR-EXBOT-003
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` when the bot has `lifecycle_state='closed'` and `status='closed'`. The response must return `status='closed'`, `lifecycle_state='closed'`. No hedge or LP metrics need to be rendered. This must be clearly distinguished from the HTTP 404 case (no bot record) — a closed bot still exists in D1.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_019
**Scenario Title:** Data/State — rangeState and driftPct computed correctly when LP is in-range but drift is large
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 steps 5–6, FR-EXBOT-021
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` when the LP is in-range but `actualShortEth` deviates significantly from `targetShortEth` (e.g., drift > 3%). The response must return `rangeState='in'` and a `driftPct` value accurately computed by the formula `(|actualShortEth - targetShortEth| / targetShortEth) × 100`. The source of `targetShortEth` requires clarification (I-004 — pending BA/Tech Lead).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_020
**Scenario Title:** Data/State — response is consistent across consecutive calls with no intervening state changes (read idempotency)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** FR-EXBOT-090
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` twice in quick succession (within a few seconds) with no operations changing the bot state between the two calls. Both responses must return identical values for all fields (D1 read-only; MarketDataDO cache unchanged). UC monitor-status is read-only — it must produce no side effects in D1.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_021
**Scenario Title:** Idempotency/Concurrency — concurrent requests do not cause race conditions or inconsistent responses
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** FR-EXBOT-090, FR-EXBOT-093
**Test Type:** Data/State
**Description:** Send multiple concurrent `GET /api/exbot/status` requests for the same bot (e.g., 10 requests within 1 second). Each response must return consistent data from the same D1 snapshot and the same MarketDataDO cache. No deadlocks, abnormal timeouts, or HTTP 500 errors occur. Since this UC is read-only, no locking mechanism is required.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_022
**Scenario Title:** E2E — investor opens the status screen and sees full information for an active bot
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §3 Full Flow, US-EXBOT-002
**Test Type:** End-to-End
**Description:** From an end-to-end perspective: the investor triggers the ExBot status screen (via POOL UI), the request traverses Operator Facade → ExBot Worker → D1 + MarketDataDO, and the JSON response is assembled and returned. Verify the full pipeline: 6 fields read from D1, `currentTick` queried from MarketDataDO, `rangeState` and `driftPct` correctly computed, Facade correctly forwards the response — all within a single request/response cycle.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_023
**Scenario Title:** E2E — investor sees SAFE_MODE state immediately after the bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A1, FR-EXBOT-050, US-EXBOT-002 AC-002-2
**Test Type:** End-to-End
**Description:** The bot has just transitioned to `status='safe_mode'` due to one of the SAFE_MODE trigger conditions (e.g., reconcile mismatch, two consecutive critical margin readings). The investor calls `GET /api/exbot/status` immediately after the transition. The response must reflect the latest `status='safe_mode'` from D1 (not the previous 'active' state due to eventual consistency delay). Verify the pipeline reads the current `bots.status` and `lifecycle_state` at the time of the request.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_024
**Scenario Title:** Acceptance — response JSON contains all mandatory fields as defined in the spec
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §F.1.3, US-EXBOT-002 AC-002-1
**Test Type:** Acceptance
**Description:** Call `GET /api/exbot/status` for an active bot and verify that the response JSON contains all fields defined in §F.1.3 of the audit report: `status`, `lifecycle_state`, `tickLower`, `tickUpper`, `currentTick`, `rangeState`, `hedgeSize` (actualShortEth), `targetShortEth`, `driftPct`, `marginStatus`, and the light-check timestamp field (field name pending I-003 clarification). No field is missing; no field is null without justification.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_025
**Scenario Title:** Acceptance — SAFE_MODE response includes safe_mode indicator and disables action buttons
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** US-EXBOT-002 AC-002-2, FR-EXBOT-050, BR-EXBOT-007
**Test Type:** Acceptance
**Description:** Call `GET /api/exbot/status` for a bot in SAFE_MODE. The response must: (1) contain `status='safe_mode'`; (2) contain `safe_mode_reason` with a value explaining the cause (D1 source pending I-009 clarification); (3) not contain any indicator suggesting "permanently closed" — SAFE_MODE is recoverable (BR-EXBOT-007). The client UI relies on this response to disable all action buttons except "Close Bot (emergency)".
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_026
**Scenario Title:** Acceptance — hedge_stopped_cooldown response contains cooldown end time to compute "Xh remaining"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** US-EXBOT-002 AC-002-3, FR-EXBOT-034
**Test Type:** Acceptance
**Description:** Call `GET /api/exbot/status` when the bot is in `lifecycle_state='hedge_stopped_cooldown'`. The response must contain a cooldown end timestamp (D1 field pending I-010 clarification) precise enough for the client to compute "Xh remaining" within the 4-hour cooldown window. The response must also indicate that automatic re-hedging will be attempted after the cooldown.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_027
**Scenario Title:** Acceptance — standard HTTP 404 with correct message when no active bot exists
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A4
**Test Type:** Acceptance
**Description:** Call `GET /api/exbot/status` for a user who has never created a bot or whose bot is already closed. The response must return exactly HTTP 404 with body containing "No active bot" (or the equivalent per spec). Must not return HTTP 200 with empty data. Must not return HTTP 500.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_028
**Scenario Title:** Acceptance — standard HTTP 503 with correct message when Operator Facade is unavailable
**UC Reference:** UC-EXBOT-monitor-status — Monitor Bot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A5, FR-EXBOT-090
**Test Type:** Acceptance
**Description:** Call `GET /api/exbot/status` when the Operator Facade cannot establish a CF service binding to ExBot Worker. The response must return exactly HTTP 503 with body "Status service temporarily unavailable". Must not return HTTP 200 with empty data. Must not expose a stack trace or internal error details.
**Test Focus:** Error/Exception

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Alternate flow for bot `status='paused'` | BLOCKED: I-006 — UC has no alternate flow for `status='paused'`. SRS FR-EXBOT-005 defines display text "Paused — hedge is maintained, LP is maintained" but neither the UC nor US-002 provides an AC for this state. | BA to add alternate flow A6 for `status='paused'` in UC §4 and add corresponding AC in US-002. Design supplementary scenarios after resolution. |
| Alternate flow for MarketDataDO unavailable | BLOCKED: I-005 — UC §4 has no alternate flow for the case where MarketDataDO is unavailable or its cache is excessively stale. ExBot Worker behavior in this scenario (partial response vs. HTTP 503) is undefined. | BA to add alternate flow A7 for MarketDataDO unavailable. Design supplementary scenarios after resolution. |
| drift % calculation with a confirmed targetShortEth source | BLOCKED: I-004 — The source of `targetShortEth` (reading `bot_runtime_state.target_short_size` from D1 vs. recomputing from `lpEthAmount × hedgeRatio`) is unconfirmed. Scenario TS_019 is drafted from the SRS but the expected value cannot be precisely written. | BA/Tech Lead to confirm the source of `targetShortEth`, update UC §3 step 6 and step 3 accordingly. |
| D1 field for `safe_mode_reason` | BLOCKED: I-009 — The `bots` table in erd.md has no `safe_mode_reason` column. The origin of this field is unknown. Scenarios TS_006 and TS_025 use a placeholder; the actual field value cannot be verified. | BA/Tech Lead to identify which D1 column stores `safe_mode_reason` and update UC §3 step 3. |
| D1 field for cooldown end time | BLOCKED: I-010 — Neither the `bots` nor `hedge_legs` table in erd.md has a column for the cooldown end timestamp. FR-EXBOT-034 defines a 4-hour cooldown but does not specify the D1 field. Scenarios TS_007 and TS_026 use a placeholder. | BA/Tech Lead to identify the D1 field for cooldown end time and update UC §3 step 3. |
| Exact field name in response: `lastLightCheckAt` vs `nextLightCheckAt` | BLOCKED: I-003 — UC §3 step 3 reads `next_light_check_at` (a future-scheduled time) but step 9 displays "Last light-check timestamp" (a past time). These are semantically different fields. | BA to clarify which field is used in the JSON response and update the UC consistently. |
| Remaining 14 lifecycle_states not covered by the 4 states mentioned in the UC | UNCLEAR: I-008 — FR-EXBOT-003 trace in UC §6 implies all 18 lifecycle states must be handled, but the UC only describes 4 (active, safe_mode, hedge_stopped_cooldown, closed). Transitional states such as `lp_opening`, `hedge_pre_open`, `stop_placing`, `stop_verified` need defined behavior. | BA to confirm which lifecycle states UC monitor-status must handle and add the corresponding alternate flows. Scenarios TS_016, TS_017, TS_018 are drafted from SRS but lack UC-level specification. |
| Performance / load testing (10,000 concurrent requests) | NFR: Out of scope for functional test design. Monitor-status is read-only so its blast radius is lower than write UCs, but scale testing falls under the NFR domain. | Delegate to performance testing team. Refer to NFR-EXBOT-001. |
