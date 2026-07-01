# Test Scenarios — UC-EXBOT-monitor-status View Active ExBot Status

> **Document title:** Test Scenarios — View Active ExBot Status
> **Source:** `docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260630_v1.md`
> **Generated:** 2026-06-30
> **Author / Agent:** qc-func-scenario-design-exbot
> **Version:** v1
> **Domain / Architecture:** Cloudflare Workers (backend-only, no UI) — `GET /api/exbot/status` Operator Facade → ExBot Worker → D1 (bots, positions, hedge_legs, bot_runtime_state) + MarketDataDO (Durable Object). Read-only; zero mutations.
> **Audit verdict:** Not Ready (51/100). Proceeding per user explicit invocation. Blocked areas flagged in ⚠️ Out-of-Scope Flags.

---

## UC-EXBOT-monitor-status — View Active ExBot Status

---

### Scenario ID: TS_UC-EXBOT-monitor-status_001
**Scenario Title:** Active bot — full status response with all D1 fields and derived values
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 Main Flow, SRS FR-EXBOT-090, US-EXBOT-002 AC-EXBOT-002-1
**Test Type:** Functional
**Description:** Send `GET /api/exbot/status` for an investor whose bot has `lifecycle_state='active'` and `bots.status='active'`, with all D1 fields populated (valid tickLower/tickUpper, last_known_hl_short_size, target_short_size, margin_status='ok', last_light_check_at timestamp) and MarketDataDO returning a currentTick value. The response should contain status='active', lifecycle_state='active', LP range tick boundaries, computed rangeState, actual and target hedge sizes, drift percentage (non-zero, correctly computed), margin_status='ok', and the light-check timestamp. No D1 write should occur as a side effect.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_002
**Scenario Title:** Status response when bot is in SAFE_MODE — includes safe_mode_reason
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §A1, SRS FR-EXBOT-050, US-EXBOT-002 AC-EXBOT-002-2
**Test Type:** Functional
**Description:** Send `GET /api/exbot/status` for an investor whose bot has `bots.status='safe_mode'` and `lifecycle_state='safe_mode'`. The response should return HTTP 200 with a `safe_mode_reason` field (derived from the reason recorded when the bot entered safe_mode) and a status field reflecting the safe_mode state. Per BR-EXBOT-007, SAFE_MODE is never a terminal state — the response must NOT indicate the bot is permanently closed.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_003
**Scenario Title:** Status response when bot is in hedge_stopped_cooldown — includes cooldown end time
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §A2, SRS FR-EXBOT-003, US-EXBOT-002 AC-EXBOT-002-3
**Test Type:** Functional
**Description:** Send `GET /api/exbot/status` for an investor whose bot has `lifecycle_state='hedge_stopped_cooldown'`. The response should return HTTP 200 including the cooldown end timestamp so the caller can display "Stop Fired — Cooldown (Xh remaining)". The margin_status, LP range, and tick data should still be present in the response if those fields are always returned regardless of lifecycle state.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_004
**Scenario Title:** No active bot — 404 returned when investor has no bot in D1
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §A4, SRS FR-EXBOT-090
**Test Type:** Functional
**Description:** Send `GET /api/exbot/status` for an investor who has never created a bot (no bot record exists in D1 for this investor). The system should return HTTP 404. The response body should indicate there is no active bot. No E-EXBOT error code is currently registered for this case (I-009) — the scenario should verify the response structure that is actually returned.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_005
**Scenario Title:** Operator Facade unavailable — 503 returned
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §A5, SRS FR-EXBOT-090
**Test Type:** Functional
**Description:** Simulate the Operator Facade being unavailable (CF service binding to ExBot Worker is broken or ExBot Worker is not deployed) and send `GET /api/exbot/status`. The response should be HTTP 503. The response message text should be "Status service temporarily unavailable" per UC §A5. No E-EXBOT code is registered for this message (I-010) — verify the actual response body structure.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_006
**Scenario Title:** rangeState='in' — currentTick is strictly inside LP range
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Configure an active bot with tickLower=100, tickUpper=200. Set MarketDataDO to return currentTick=150 (strictly between lower and upper bounds). Send `GET /api/exbot/status`. The response should contain rangeState='in'. This verifies the in-range condition for a tick strictly inside the range.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_007
**Scenario Title:** rangeState='out' — currentTick is below tickLower
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Configure an active bot with tickLower=100, tickUpper=200. Set MarketDataDO to return currentTick=99 (one below tickLower). Send `GET /api/exbot/status`. The response should contain rangeState='out'. This is the boundary below the LP range.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_008
**Scenario Title:** rangeState='out' — currentTick is above tickUpper
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Configure an active bot with tickLower=100, tickUpper=200. Set MarketDataDO to return currentTick=200 (at tickUpper boundary). Send `GET /api/exbot/status`. Whether this is 'in' or 'out' depends on the inclusive/exclusive boundary definition (I-012 — pending BA clarification on whether the upper bound is inclusive or exclusive per Uniswap V3 convention `tickLower <= currentTick < tickUpper`). Verify the returned rangeState is consistent with the actual implemented boundary rule.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_009
**Scenario Title:** rangeState boundary — currentTick equals tickLower exactly
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 5, SRS FR-EXBOT-012
**Test Type:** Functional
**Description:** Configure an active bot with tickLower=100, tickUpper=200. Set MarketDataDO to return currentTick=100 (exactly at tickLower). Send `GET /api/exbot/status`. The expected rangeState depends on the boundary rule (I-012). Per Uniswap V3 standard `tickLower <= currentTick < tickUpper`, this should return rangeState='in'. Verify the implementation matches the canonical boundary rule.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_010
**Scenario Title:** Drift % — nominal case with non-zero actual and target short sizes
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 6, ERD `bot_runtime_state`
**Test Type:** Functional
**Description:** Configure an active bot with `last_known_hl_short_size='1.0'` (BigDecimal stored as TEXT) and `target_short_size='0.9'`. Send `GET /api/exbot/status`. The returned drift percentage should be `|1.0 - 0.9| / 0.9 * 100 ≈ 11.11%`. Verify that the drift calculation uses BigDecimal arithmetic (not JavaScript float) and that the result value is within acceptable precision (e.g., not 11.100000000000001% due to floating-point error per SRS NFR-EXBOT-008).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_011
**Scenario Title:** Drift % — zero drift when actual short size equals target
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 6, ERD `bot_runtime_state`
**Test Type:** Functional
**Description:** Configure an active bot with `last_known_hl_short_size='1.0'` and `target_short_size='1.0'` (perfectly hedged). Send `GET /api/exbot/status`. The returned drift percentage should be exactly 0%. Verify the system does not return a non-zero value due to floating-point rounding.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_012
**Scenario Title:** Drift % — large drift (actual significantly above target)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 6, SRS FR-EXBOT-003
**Test Type:** Functional
**Description:** Configure an active bot with `last_known_hl_short_size='2.0'` and `target_short_size='1.0'` (actual is double the target). Send `GET /api/exbot/status`. The returned drift percentage should be exactly 100%. Verify the formula handles large drift correctly.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_013
**Scenario Title:** margin_status='ok' — reflected correctly in status response
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §F.2, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Configure a bot where `hedge_legs.margin_status='ok'` (marginUsage below 0.55 threshold per SRS FR-EXBOT-060). Send `GET /api/exbot/status`. The response should include margin_status='ok'. This is the normal operating state.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_014
**Scenario Title:** margin_status='warning' — reflected correctly in status response
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §F.2, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Configure a bot where `hedge_legs.margin_status='warning'` (marginUsage between 0.55 and 0.75 per SRS FR-EXBOT-060). Send `GET /api/exbot/status`. The response should include margin_status='warning'. The investor's UI should display a warning indicator based on this value. Verify this is a D1 read (not a live HL API call — the status endpoint must not trigger any HL requests).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_015
**Scenario Title:** margin_status='critical' — reflected correctly in status response
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §F.2, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Configure a bot where `hedge_legs.margin_status='critical'` (marginUsage above 0.75 per SRS FR-EXBOT-060). Send `GET /api/exbot/status`. The response should include margin_status='critical'. Verify this is read from D1 and the endpoint performs no HL API call.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_016
**Scenario Title:** Status on Base chain (chainId=8453) — correct MarketDataDO pool address used
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 4, SRS FR-EXBOT-093, NFR-EXBOT-009
**Test Type:** Integration
**Description:** For an active bot on Base chain (chainId=8453), send `GET /api/exbot/status`. Verify that the ExBot Worker queries the MarketDataDO instance corresponding to the Base Uniswap V3 pool address (not the Optimism pool address). The currentTick returned should be from the Base network pool. This ensures dual-chain correctness per SRS NFR-EXBOT-009.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_017
**Scenario Title:** Status on Optimism chain (chainId=10) — correct MarketDataDO pool address used
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 4, SRS FR-EXBOT-093, NFR-EXBOT-009
**Test Type:** Integration
**Description:** For an active bot on Optimism chain (chainId=10), send `GET /api/exbot/status`. Verify that the ExBot Worker queries the MarketDataDO instance corresponding to the Optimism Uniswap V3 pool address (not the Base pool address). The currentTick must reflect the OP network pool state. This is the second of two EP partitions for the dual-chain requirement.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_018
**Scenario Title:** Status call performs zero Hyperliquid API calls
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §9 (NFR — Rate Limiting), SRS BR-EXBOT-003, SRS FR-EXBOT-093
**Test Type:** Integration
**Description:** For an active bot, send `GET /api/exbot/status` and monitor all outbound calls made by ExBot Worker. Verify that zero calls are made to the Hyperliquid API during status processing. The margin_status must be read from D1 `hedge_legs.margin_status`, not fetched from HL. MarketDataDO is read instead of HL for the current tick. This test enforces the "HL weight = 0 for status" behavior.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_019
**Scenario Title:** margin_status in response reflects D1 value, not live HL state (staleness awareness)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §F.4, SRS FR-EXBOT-060, SRS FR-EXBOT-025
**Test Type:** Data/State
**Description:** Configure a bot where hedge-sync has not run for several hours and `hedge_legs.margin_status` was last written as 'ok' in D1. Simulate a scenario where the actual HL margin would now be 'warning' (but D1 has not been updated). Send `GET /api/exbot/status`. The response should return margin_status='ok' (the D1 value), confirming the status endpoint does not refresh margin data from HL. This verifies the known design: margin_status in status reflects the last hedge-sync write, which may lag reality by up to 6 hours.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_020
**Scenario Title:** last_known_hl_short_size reflects D1 reconcile value, not live HL position
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §F.4, SRS FR-EXBOT-025
**Test Type:** Data/State
**Description:** Configure a bot where the D1 `bot_runtime_state.last_known_hl_short_size='1.5'`, but the actual live HL short position has since changed to 1.6 ETH (not yet reconciled by hedge-sync). Send `GET /api/exbot/status`. The response must return the actual_short_size value of '1.5' (the D1 value), not the live HL value. This confirms the status endpoint displays the last-reconciled value and does not make a live HL query.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_021
**Scenario Title:** rangeState uses MarketDataDO currentTick (shared Durable Object), not a live pool query
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 step 4, SRS FR-EXBOT-093
**Test Type:** Data/State
**Description:** Configure MarketDataDO to have a cached currentTick=150 from the most recent refresh (which may be minutes old). Send `GET /api/exbot/status`. The rangeState computation should use currentTick=150 from the cache, not trigger a fresh on-chain slot0 read. Verify the response's tick value matches what was in the DO cache, not a live query value. This confirms the endpoint uses the shared DO cache as designed, avoiding extra on-chain reads per status call.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_022
**Scenario Title:** Valid auth token — request accepted and processed
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2 Preconditions, SRS FR-EXBOT-090
**Test Type:** Functional
**Description:** Send `GET /api/exbot/status` with a valid investor authentication token (mechanism TBD per I-011 — BA to define auth mechanism). The request should reach ExBot Worker and receive a valid status response (HTTP 200 for active bot or HTTP 404 for no bot). This is the baseline authorization scenario.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_023
**Scenario Title:** Missing auth token — request rejected
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2 Preconditions, SRS FR-EXBOT-090
**Test Type:** Functional
**Description:** Send `GET /api/exbot/status` with no authentication token (or with an expired/invalid token). The Operator Facade should reject the request before forwarding to ExBot Worker. The response should be HTTP 401 or 403. The exact behavior depends on I-011 resolution (auth mechanism not yet defined in UC). Verify no bot data is returned.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_024
**Scenario Title:** Investor A cannot retrieve Investor B's bot status (data isolation)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2 (actor: USDC Investor, read-only), SRS FR-EXBOT-090
**Test Type:** Functional
**Description:** With two investors each having an active bot, send `GET /api/exbot/status` authenticated as Investor A. The response must contain only Investor A's bot data. The response must not contain any data from Investor B's bot. Verify that the ExBot Worker queries the bot record scoped to the authenticated investor's identity.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_025
**Scenario Title:** Status response is consistent with what light-check workers read from D1
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §F.4, SRS FR-EXBOT-003, SRS FR-EXBOT-012
**Test Type:** Data/State
**Description:** After a light-check worker completes and writes `bots.lifecycle_state`, `hedge_legs.margin_status`, and `bot_runtime_state.last_known_hl_short_size` to D1, immediately send `GET /api/exbot/status`. The status response should reflect the same values that the light-check just wrote. This verifies that the status endpoint reads the latest committed D1 state and there is no stale-read issue between the two operations.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_026
**Scenario Title:** Drift % — BigDecimal precision preserved (no floating-point error)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §9 (NFR — Data Precision), SRS NFR-EXBOT-008, SRS FR-EXBOT-021
**Test Type:** Functional
**Description:** Configure `last_known_hl_short_size='0.3'` and `target_short_size='0.1'`. The mathematically correct drift % is `|0.3 - 0.1| / 0.1 * 100 = 200%`. Using JavaScript float arithmetic `0.3 - 0.1` = 0.19999999999999998, which would produce a slightly wrong result. Send `GET /api/exbot/status` and verify the returned drift % is exactly 200%, confirming BigDecimal arithmetic is used per SRS NFR-EXBOT-008.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_027
**Scenario Title:** End-to-end: Investor gets status via POOL UI flow (POOL → Operator Facade → ExBot Worker → D1 + MarketDataDO → Facade → POOL)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 steps 1–9, SRS FR-EXBOT-090
**Test Type:** End-to-End
**Description:** Starting from the POOL UI layer, trigger the `GET /api/exbot/status` call as an authenticated investor with an active bot on Base chain. Trace the full request path: (1) POOL UI sends request to Operator Facade, (2) Facade forwards to ExBot Worker via CF service binding, (3) ExBot Worker reads D1 tables and queries MarketDataDO, (4) Worker computes rangeState and drift %, (5) Worker returns composite JSON, (6) Facade passes response to POOL UI. Verify the final response contains all expected fields with correct values and the full round-trip completes without errors.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_028
**Scenario Title:** Acceptance: Active bot — AC-EXBOT-002-1 verification
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-1
**Test Type:** Acceptance
**Description:** Given a bot with `lifecycle_state='active'` and `bots.status='active'`, when `GET /api/exbot/status` is called by an authenticated investor, then the response must include: status='active', the LP range tick boundaries, current tick from MarketDataDO, rangeState ('in' or 'out'), the actual hedge size, the target hedge size, drift percentage (computed correctly), margin_status (one of ok/warning/critical), and the last light-check timestamp. This directly maps to AC-EXBOT-002-1 from US-EXBOT-002.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_029
**Scenario Title:** Acceptance: SAFE_MODE bot — AC-EXBOT-002-2 verification
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-2, SRS FR-EXBOT-050, common-rules.md BR-EXBOT-007
**Test Type:** Acceptance
**Description:** Given a bot with `bots.status='safe_mode'`, when `GET /api/exbot/status` is called by an authenticated investor, then the response must return HTTP 200 with a `safe_mode_reason` field explaining why the bot entered safe mode. The status must indicate safe_mode. Per BR-EXBOT-007 ("SAFE_MODE is never a terminal state. Every SAFE_MODE path must lead to auto-recovery or bot_safe_close"), the response must not indicate a terminal/closed state. This directly maps to AC-EXBOT-002-2.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_030
**Scenario Title:** Acceptance: hedge_stopped_cooldown bot — AC-EXBOT-002-3 verification
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-3
**Test Type:** Acceptance
**Description:** Given a bot with `lifecycle_state='hedge_stopped_cooldown'`, when `GET /api/exbot/status` is called by an authenticated investor, then the response must include the cooldown end timestamp, allowing the caller to compute "Xh remaining" for display. The response must return HTTP 200 (not a 404 or error). This directly maps to AC-EXBOT-002-3.
**Test Focus:** Alternative flow

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Alternate Flow A3 (`lifecycle_state='cooldown'`) | **BLOCKED: I-001 Blocker** — `cooldown` state was removed in HLD 2026-06-18. UC A3 describes untestable behavior. The system never enters this state. | BA must rewrite A3 to describe `lifecycle_state='closed'` behavior (bot fully closed via bot_safe_close) per SRS FR-EXBOT-070. Re-design scenario after BA fixes A3. |
| Status response for `lifecycle_state='lp_rebalancing'` | **BLOCKED: I-005 Major** — UC has no defined behavior for this state. Whether the endpoint returns 200 with full field set, partial fields, or a different indicator is undefined. | BA to add alternate flow for `lp_rebalancing`. Resolve via qc-qna before designing scenario. |
| Status response for `lifecycle_state='lp_closing'` | **BLOCKED: I-005 Major** — UC has no defined behavior for this state. | BA to add alternate flow for `lp_closing`. |
| Status response for `lifecycle_state='error'` | **BLOCKED: I-005 Major** — UC has no defined behavior for this state (admin intervention required). | BA to add alternate flow for `error` state. |
| Status response for `lifecycle_state='closed'` (bot exists but is closed) | **BLOCKED: I-005 Major** — UC uses 404 for "no active bot" but does not define whether a closed bot returns 404 or a closed-state JSON response. | BA to clarify: closed bot = 404 or HTTP 200 with lifecycle_state='closed'? Resolve I-005. |
| API response field name assertion | **BLOCKED: I-006 Major** — No JSON response schema is defined anywhere (field names, types, null handling, key names for computed fields). Scenarios above describe expected data content but cannot assert exact JSON key names. | BA or Tech Lead to define full HTTP 200 response schema. |
| Authentication mechanism test cases | **BLOCKED: I-011 Minor (partially)** — Auth mechanism (SIWE JWT? API key?) for POOL UI → Facade is not specified. Scenarios 022–024 use generic "auth token" language. Specific expired-token, tampered-token, and wrong-scope scenarios cannot be designed without knowing the auth mechanism. | BA to document auth mechanism. Refine scenarios 022–024 after resolution. |
| Exact rangeState boundary (currentTick == tickUpper) | **BLOCKED: I-012 Minor** — Whether `currentTick == tickUpper` is 'in' or 'out' is not specified. Scenario 008 tests this case but cannot assert the expected value definitively until BA confirms the inclusive/exclusive boundary rule. | BA or Tech Lead to confirm: `rangeState='in'` iff `tickLower <= currentTick AND currentTick < tickUpper` (Uniswap V3 standard). |
| MarketDataDO staleness fallback | **BLOCKED: I-013 Minor** — UC does not define the status endpoint behavior when MarketDataDO is unavailable or cache is stale beyond TTL (forced refresh in progress). | BA or Tech Lead to document: does status return null for currentTick, a stale value, or block until DO refreshes? |
| Actor = Admin path (FRD §4.11 conflict) | **BLOCKED: I-002 Major** — FRD §4.11 FR-EXBOT-100 lists actor as "Admin" but UC/US say "Investor". Admin auth path scenarios cannot be designed until the conflict is resolved. | BA to confirm: can Admin also call this endpoint? If yes, define auth mechanism and whether response differs by role. |
| Drift % when target_short_size = 0 | **BLOCKED: I-003 Major** — Division by zero behavior is undefined in UC. Whether the system returns 0%, null, or an error for a bot where `target_short_size=0` is not specified. | BA or Tech Lead to define: what is the drift % when `target_short_size=0`? |
| Performance / load testing of status endpoint | **OUT-OF-SCOPE** — At 10,000 bots, simultaneous status polling would stress MarketDataDO. This is a load/performance concern, not a functional scenario. | Defer to performance testing team. |
| Security pen-test paths (injection, enumeration) | **OUT-OF-SCOPE** — Security testing beyond functional auth (valid/invalid token) is out of functional QC scope. | Defer to security team. |

---
