# Test Scenarios — UC-EXBOT-monitor-status: View Active ExBot Status

> Source: `docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260630_v2.md`
> Generated: 2026-07-02
> Domain/Architecture: Cloudflare Workers (ExBot Worker + Operator Facade) + Cloudflare D1 (control_db + state_db_shard) + Durable Objects (MarketDataDO). Read-only API endpoint: `GET /api/exbot/status`. No UI — all scenarios are logic/API level.
> Author/Agent: `qc-func-scenario-design-exbot`
> Version: v2

---

## UC-EXBOT-monitor-status — View Active ExBot Status

### Scenario ID: TS_UC-EXBOT-monitor-status_001
**Scenario Title:** Active bot — full status response returns all required fields
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 Main Flow, AC-01, SRS FR-EXBOT-090, US-EXBOT-002 AC-EXBOT-002-1
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` for a bot with `lifecycle_state='active'` and `bots.status='active'`, with valid positions, hedge_legs, and bot_runtime_state records in D1. The system must return HTTP 200 with a JSON body that includes: `status`, `lifecycle_state`, `tickLower`, `tickUpper`, current tick from MarketDataDO, `rangeState` ('in' or 'out'), `last_known_hl_short_size`, `target_short_size`, `drift_pct` (computed), `margin_status` ('ok', 'warning', or 'critical'), and a light-check timestamp field.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_002
**Scenario Title:** Active bot on Base chain — rangeState uses Base pool MarketDataDO currentTick
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 4–5, SRS FR-EXBOT-093, project-context-master §3.3 Dual-chain constraint
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status` for a bot deployed on Base (chainId 8453). The ExBot Worker must query `currentTick` from the MarketDataDO slot corresponding to the Base Uniswap V3 pool address, not the Optimism pool address. The returned `rangeState` must reflect the Base pool tick relative to the bot's LP range boundaries.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_003
**Scenario Title:** Active bot on Optimism chain — rangeState uses Optimism pool MarketDataDO currentTick
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 4–5, SRS FR-EXBOT-093, project-context-master §3.3 Dual-chain constraint
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status` for a bot deployed on Optimism (chainId 10). The ExBot Worker must query `currentTick` from the MarketDataDO slot corresponding to the Optimism Uniswap V3 pool address. The returned `rangeState` must reflect the Optimism pool tick.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_004
**Scenario Title:** rangeState = 'in' — currentTick strictly inside LP range
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 5, AC-05, SRS FR-EXBOT-020 AC (boundary convention implied: tickLower ≤ currentTick < tickUpper)
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `currentTick` is strictly between `tickLower` and `tickUpper` (e.g., tickLower=100, currentTick=150, tickUpper=200). The response must contain `rangeState = 'in'`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_005
**Scenario Title:** rangeState = 'in' — currentTick exactly at tickLower (lower boundary inclusive)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 5, SRS FR-EXBOT-020 AC ("boundary ticks: currentTick == tickLower" listed as in-range test case — I-012 partial)
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `currentTick == tickLower` exactly (e.g., both equal 100). Per the boundary convention implied by FR-EXBOT-020 AC (`tickLower <= currentTick < tickUpper`), the tick at the lower boundary is in-range. The response must contain `rangeState = 'in'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_006
**Scenario Title:** rangeState = 'out' — currentTick exactly at tickUpper (upper boundary exclusive)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 5, SRS FR-EXBOT-020 AC ("boundary ticks: currentTick == tickUpper − 1" listed as last in-range tick)
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `currentTick == tickUpper` exactly (e.g., both equal 200). Per the implied convention, tickUpper is exclusive (out-of-range). The response must contain `rangeState = 'out'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_007
**Scenario Title:** rangeState = 'in' — currentTick at tickUpper minus 1 (last in-range tick)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 5, SRS FR-EXBOT-020 AC ("currentTick == tickUpper − 1" is a required BVA test case)
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `currentTick == tickUpper − 1` (e.g., tickUpper=200, currentTick=199). This is the last tick that should be classified as in-range. The response must contain `rangeState = 'in'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_008
**Scenario Title:** rangeState = 'out' — currentTick below tickLower
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 5, AC-06
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `currentTick < tickLower` (e.g., tickLower=100, currentTick=99). The response must contain `rangeState = 'out'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_009
**Scenario Title:** rangeState = 'out' — currentTick above tickUpper
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 5, AC-06
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `currentTick > tickUpper` (e.g., tickUpper=200, currentTick=201). The response must contain `rangeState = 'out'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_010
**Scenario Title:** drift % — typical case with distinct actual and target hedge sizes
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 6, AC-07, SRS NFR-EXBOT-008 (BigDecimal)
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `last_known_hl_short_size = 1.0 ETH` and `target_short_size = 0.9 ETH`. The response must contain `drift_pct ≈ 11.11...%` computed as `(|1.0 − 0.9| / 0.9) × 100`. The computation must use BigDecimal arithmetic (NFR-EXBOT-008) — not JavaScript floating-point — so the value must not exhibit floating-point rounding error (e.g., must not return 11.100000000000001).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_011
**Scenario Title:** drift % — actual equals target (zero drift)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 6, SRS NFR-EXBOT-008
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `last_known_hl_short_size == target_short_size` (e.g., both 1.0 ETH). The response must contain `drift_pct = 0.0` (exactly zero, not a floating-point near-zero). BigDecimal arithmetic required.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_012
**Scenario Title:** drift % — large hedge sizes preserving BigDecimal precision
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 6, SRS NFR-EXBOT-008
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where both hedge sizes are large values with many decimal places (e.g., `last_known_hl_short_size = 9999999.123456789 ETH`, `target_short_size = 9999998.987654321 ETH`). The response `drift_pct` must preserve full decimal precision without truncation or floating-point rounding artifacts, as required by NFR-EXBOT-008.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_013
**Scenario Title:** margin_status = 'ok' — value from D1, no live HL API call
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-060, project-context-master §7.1 (light-check HL weight = 0)
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `hedge_legs.margin_status = 'ok'` in D1 (written by hedge-sync). The response must return `margin_status = 'ok'`. The endpoint reads this value from D1 — it must NOT call the Hyperliquid API to recalculate margin (per light-check HL weight = 0 rule).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_014
**Scenario Title:** margin_status = 'warning' (marginUsage between 0.55 and 0.75)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `hedge_legs.margin_status = 'warning'` in D1. The response must return `margin_status = 'warning'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_015
**Scenario Title:** margin_status = 'critical' (marginUsage above 0.75)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `hedge_legs.margin_status = 'critical'` in D1. The response must return `margin_status = 'critical'`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_016
**Scenario Title:** margin_status boundary at exact marginUsage = 0.55
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `hedge_legs.margin_status` was written when marginUsage was exactly 0.55. Verify whether the stored and returned value is 'ok' or 'warning' — the boundary assignment (inclusive/exclusive at 0.55) must be consistent with FR-EXBOT-060.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_017
**Scenario Title:** margin_status boundary at exact marginUsage = 0.75
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-060
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `hedge_legs.margin_status` was written when marginUsage was exactly 0.75. Verify whether the stored and returned value is 'warning' or 'critical' — consistent with FR-EXBOT-060 boundary rule.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_018
**Scenario Title:** Alternate Flow A1 — safe_mode response includes safe_mode_reason
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §A1, AC-02, US-EXBOT-002 AC-EXBOT-002-2, SRS FR-EXBOT-050
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `bots.status = 'safe_mode'`. The system must return HTTP 200 with `safe_mode_reason` populated. Per BR-EXBOT-007, SAFE_MODE is not a terminal state — the response must not indicate the bot is closed or permanently stopped.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_019
**Scenario Title:** A1 — safe_mode_reason reflects the specific FR-EXBOT-050 entry condition
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §A1, SRS FR-EXBOT-050
**Test Type:** Data/State
**Description:** Call `GET /api/exbot/status` for a bot that entered SAFE_MODE due to a specific FR-EXBOT-050 condition (e.g., HL API unreachable, reconcile mismatch, margin critical). The `safe_mode_reason` in the response must accurately reflect the specific triggering condition stored in D1, not a generic fallback.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_020
**Scenario Title:** Alternate Flow A2 — hedge_stopped_cooldown includes cooldown end timestamp
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §A2, AC-03, US-EXBOT-002 AC-EXBOT-002-3
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` where `bots.lifecycle_state = 'hedge_stopped_cooldown'`. The system must return HTTP 200 with the cooldown end timestamp included in the response body, so that POOL UI can render the remaining cooldown duration.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_021
**Scenario Title:** Alternate Flow A4 — no bot record in D1 returns HTTP 404 (not 500)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §A4, AC-04, SRS NFR-EXBOT-015
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` for an authenticated investor with no bot record in D1. The system must return HTTP 404, not HTTP 500. Per NFR-EXBOT-015, the D1 read path must handle not-found gracefully.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_022
**Scenario Title:** Alternate Flow A5 — Operator Facade unavailable returns HTTP 503
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §A5, AC-08
**Test Type:** Functional
**Description:** Call `GET /api/exbot/status` when the CF service binding from Operator Facade to ExBot Worker is broken or the Facade is unavailable. The system must return HTTP 503 with message "Status service temporarily unavailable".
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_023
**Scenario Title:** D1 reads — all required fields present and non-null for a fully initialized active bot
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-090, ERD tables: bots, positions, hedge_legs, bot_runtime_state
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status` for a fully initialized active bot. Verify the response contains non-null values for: `bots.status`, `bots.lifecycle_state`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status`, `bot_runtime_state.last_known_hl_short_size`. No field may be null when all D1 records exist and have been written by bot-start.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_024
**Scenario Title:** margin_status read from D1, not from live Hyperliquid API call
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, project-context-master §7.1 (light-check HL weight = 0), SRS FR-EXBOT-060
**Test Type:** Data/State
**Description:** With `hedge_legs.margin_status = 'warning'` stored in D1 after a hedge-sync run, call `GET /api/exbot/status`. The response must return `margin_status = 'warning'` from D1, without making a live HL API call. This verifies the read-only status endpoint respects the "light-check HL weight = 0" architectural constraint.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_025
**Scenario Title:** last_known_hl_short_size reflects latest hedge-sync reconcile write
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 3, SRS FR-EXBOT-025, §F.4 integration impact
**Test Type:** Data/State
**Description:** After a hedge-sync reconcile cycle writes an updated `last_known_hl_short_size` to `bot_runtime_state`, call `GET /api/exbot/status`. The response must return the post-reconcile value, confirming the D1 read picks up the latest hedge-sync result and not a stale value.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_026
**Scenario Title:** currentTick sourced from MarketDataDO, not hardcoded or from D1
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 4, SRS FR-EXBOT-093
**Test Type:** Integration
**Description:** Call `GET /api/exbot/status`. Verify that `currentTick` (used for rangeState computation) is retrieved from MarketDataDO via a DO query, not hardcoded or read from D1. The returned `rangeState` must be consistent with the actual cached tick in MarketDataDO at call time.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_027
**Scenario Title:** Idempotency — multiple concurrent GET calls produce no D1 mutations
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** SRS NFR-EXBOT-011
**Test Type:** Data/State
**Description:** Issue multiple concurrent `GET /api/exbot/status` calls for the same bot. All calls must return consistent response payloads. After all calls complete, verify via D1 inspection that zero rows were inserted, updated, or deleted in any table. This is a read-only endpoint — idempotency is guaranteed by design and must be confirmed.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_028
**Scenario Title:** Concurrent status + light-check — MarketDataDO cache not corrupted under load
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §3 step 4, SRS FR-EXBOT-093, §F.4
**Test Type:** Data/State
**Description:** Issue `GET /api/exbot/status` calls while light-check workers are simultaneously reading MarketDataDO for the same pool. Verify: (1) status response returns a valid, non-null `currentTick`; (2) concurrent read access does not cause the DO cache to become corrupt or return an inconsistent tick value.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_029
**Scenario Title:** E2E — bot-start completion to first status call returns all fields populated
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §2 Preconditions, §3 Main Flow, §F.4 (UC-EXBOT-bot-start dependency)
**Test Type:** End-to-End
**Description:** After UC-EXBOT-bot-start completes and the bot reaches `lifecycle_state = 'active'`, immediately call `GET /api/exbot/status`. All response fields (tickLower, tickUpper, last_known_hl_short_size, margin_status, drift_pct, rangeState) must be non-null, confirming bot-start has fully initialized all D1 tables the status endpoint depends on.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_030
**Scenario Title:** E2E — status reflects updated margin_status after hedge-sync deep-audit
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** §F.4 integration, SRS FR-EXBOT-060
**Test Type:** End-to-End
**Description:** Before a hedge-sync deep-audit, `hedge_legs.margin_status = 'ok'`. Trigger a deep-audit that causes marginUsage to exceed the warning threshold, writing `margin_status = 'warning'` to D1. Call `GET /api/exbot/status` after the audit completes. The response must return `margin_status = 'warning'`, confirming the status endpoint reflects the post-audit D1 state.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_031
**Scenario Title:** Acceptance — response does not trigger any D1 writes
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC §5 Postconditions, SRS NFR-EXBOT-011
**Test Type:** Acceptance
**Description:** Call `GET /api/exbot/status` for any valid bot state. After the call, verify via D1 audit or log inspection that zero rows were inserted, updated, or deleted in any D1 table (bots, positions, hedge_legs, bot_runtime_state, queue_idempotency). The endpoint is read-only by design.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_032
**Scenario Title:** Acceptance — all three US-EXBOT-002 acceptance criteria satisfied
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-1, AC-EXBOT-002-2, AC-EXBOT-002-3
**Test Type:** Acceptance
**Description:** Verify the three explicit ACs from US-EXBOT-002: (1) active bot returns lifecycle status and all computed metrics (AC-EXBOT-002-1); (2) bot in safe_mode returns response with `safe_mode_reason` populated (AC-EXBOT-002-2); (3) bot in `hedge_stopped_cooldown` returns cooldown end timestamp (AC-EXBOT-002-3).
**Test Focus:** Happy path

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Alternate Flow A3 (lifecycle_state = 'cooldown') | BLOCKED: I-001 Blocker — `cooldown` state was removed in HLD 2026-06-18. A3 references a deleted state. Cannot design test without a valid target state. | BA must rewrite A3 to describe behavior after `bot_safe_close` when `lifecycle_state = 'closed'` and update the message text per FR-EXBOT-070. Re-audit before designing. |
| Actor / auth path scenarios (valid auth, expired auth, missing auth header) | BLOCKED: I-002 Major + I-011 Minor — actor conflict (Investor vs Admin) and auth mechanism not specified for POOL UI → Facade and Facade → ExBot Worker. | BA confirms actor (I-002); BA/Tech Lead documents auth mechanism (I-011). Re-audit then design auth-path scenarios. |
| Alternate flows for lifecycle states: paused, lp_rebalancing, lp_closing, error, closed | BLOCKED: I-005 Major — UC only covers active, safe_mode, hedge_stopped_cooldown. No alternate flow for the remaining 7 of 15 active states. | BA adds alternate flows per I-005 resolution. Re-audit before designing. |
| JSON response schema contract tests (field names, types, optionality) | BLOCKED: I-006 Major — no JSON schema defined in UC, SRS, or FRD. Field names for derived fields (rangeState, drift_pct) unspecified. | BA/Tech Lead provides full HTTP 200 response schema. Required before API contract test scenarios can be written. |
| drift % source verification — target_short_size D1 read vs. computed from lpEthAmount × hedgeRatio | BLOCKED: I-003 Major — source of targetShortEth unconfirmed. Test cannot verify correct input values. | BA/Tech Lead confirms source (I-003) and defines divide-by-zero handling. Re-audit before designing precision scenarios beyond 010–012. |
| timestamp field verification — next vs. last light-check | BLOCKED: I-004 Major — UC step 3 reads `bots.next_light_check_at` but step 9 labels it "Last light-check". Cannot write timestamp assertion without knowing which field is displayed. | BA clarifies and corrects the timestamp field name in UC (I-004). |
| MarketDataDO unavailable or stale fallback | BLOCKED: I-013 Minor + OQ-EXBOT-09 Open — cache TTL undefined; fallback behavior for stale/unavailable DO not documented. | BA/Tech Lead defines fallback per I-013 resolution before fallback scenarios can be designed. |
| Error code body content for HTTP 404 (A4) and HTTP 503 (A5) | BLOCKED: I-009 + I-010 Minor — no E-EXBOT-* codes registered for these two error responses. Cannot verify error body field values. | BA registers E-EXBOT codes per I-009/I-010 resolution. |
| Performance / load testing (NFR-EXBOT-009: p99 ≤ 500ms) | OUT OF SCOPE — NFR, not functional | Defer to performance testing specialist. |
| Security beyond functional auth (NFR-EXBOT-010: sensitive data not logged at INFO level) | OUT OF SCOPE — NFR/security | Defer to security review. |
