# Test Case Update Impact Report — UC-EXBOT-monitor-status

**Status:** Waiting for user approval
**Report revision:** R1
**Trigger type:** REQUIREMENT_DELTA
**Track in scope:** logic
**Audited source (old):** UC-EXBOT-monitor-status_monitor-status_audited_20260715_v5.md
**Audited source (new):** UC-EXBOT-monitor-status_monitor-status_audited_20260722_v6.md
**Current TC source:** UC-EXBOT-monitor-status_monitor-status_testcases_draft.md (v3, 69 TCs — FUNC 43 / INTG 20 / NFR 6)
**User feedback source:** none (pure REQUIREMENT_DELTA — no user feedback supplied for this run)

#### Summary

| Item | Count |
|---|---:|
| Requirements added | 2 |
| Requirements modified | 2 |
| Requirements removed | 0 |
| Requirements clarified | 3 |
| Requirements still ambiguous / need confirmation | 1 |
| Existing TCs kept | 0 |
| Existing TCs to update | 67 |
| New TCs proposed | 4 |
| TCs proposed to retire | 2 |
| TCs proposed to split | 0 |
| TCs proposed to merge | 0 |
| Items needing user review / confirmation | 3 |

#### Requirement Delta

| Change ID | Change type | Old meaning | New meaning | Source | Expected TC impact |
|---|---|---|---|---|---|
| CH-01 | MODIFIED | v5: no `isAdmin` guard existed. Investor with valid HMAC signature could reach the wallet-ownership check (step 3 / A9) and get HTTP 200 (match) or HTTP 403 `E-EXBOT-030` (mismatch). | v6: ExBot Lambda step 2b applies a hard `isAdmin` guard. Any non-Admin caller (Investor — the UC's Primary actor) gets HTTP 403 immediately, before any business logic or Aurora PostgreSQL read runs. Only Admin can exercise the happy path and most alternate flows in v1. | UC §2 Preconditions #8, §6.1.A step 2b; audit v6 V-009 (Major, Open) | Massive — every FUNC/INTG test case that currently reaches business logic must explicitly require actor **Admin** in its preconditions. TC_025 and TC_048 (which assume Investor reaches the ownership check) are directly contradicted and must be retired. New test cases are needed for the guard's own behavior. |
| CH-02 | MODIFIED | v5 endpoint: `GET /api/exbot/status` (no path parameter). | v6 endpoint: `GET /api/exbot/status/{botId}` — `botId` is now a required path parameter. | UC §6.1 header (changelog 2026-07-20); audit v6 V-011 (Minor, Open — `us-002.md` not yet updated to match) | Cosmetic but universal — every existing TC's Test Steps column that calls the endpoint must be reworded to include the `{botId}` path segment. No behavior change by itself. |
| CH-03 | ADDED | v5: no alternate flow existed for `bots.status='paused'`; the only v3 coverage (TC_049) was inferred from `states.md` with no defined response message (V-008 was Open in v5). | v6: formal Alternate Flow A10 — `status='paused'`, `lifecycle_state` unchanged from its pre-pause value, response message `E-EXBOT-031` "Bot Paused. Hedge and LP are maintained. You may still redeem." | UC §4 A10; audit v6 V-008 (Resolved — Answered 2026-07-20) | TC_049 must be updated to assert the `E-EXBOT-031` message explicitly (previously untestable — no message was defined) and to require actor Admin (Investor variant of A10 is blocked by CH-01/V-009). |
| CH-04 | CLARIFIED | v5: `last_reconcile_at`, `last_error_code`, `safe_mode_tier` were Open questions (V-002, V-003, V-007) — unclear whether they ever return a real value in v1; current TCs hedge with "field presence only" / "may need follow-up pass" wording. | v6: BA confirmed all three are v1 gaps — the mapping/column does not exist yet, so they always return `null` in v1 regardless of bot state; real values arrive only in v1.1 (dependency D1). | UC §6.1.D Field Inventory rows 5/6/7; audit v6 V-002, V-003, V-007 (all Resolved — Answered 2026-07-20) | TC_001, TC_034, TC_047, TC_056 (and TC_012/TC_013/TC_018, which currently hedge on `safe_mode_tier`) should have their wording firmed up from "field presence only" / tentative language to a definitive "always `null` in v1" assertion. No new test intent — wording precision only. |
| CH-05 | CLARIFIED | v5: `dry_run` was an Open question (V-004) — no confirmed data source. | v6: BA confirmed `dry_run` is a boolean read from environment variable `EXBOT_DRY_RUN` (not a DB column); when `true`, all Hyperliquid calls are short-circuited. | UC §6.1.D Field Inventory row 8; audit v6 V-004 (Resolved — Answered 2026-07-20) | No existing TC needs correction (all current assertions already treat `dry_run` as a valid non-null Implemented field). Optional: a dedicated test toggling `EXBOT_DRY_RUN` could be added — see Open Questions below. |
| CH-06 | ADDED | v5: no such acceptance criterion existed. | v6: new **AC-ms-01b** — an Investor whose `wallet_address` matches `bot.user_wallet_address` still receives HTTP 403 (blocked by the `isAdmin` guard at step 2b), NOT HTTP 200 as `us-002.md` AC-EXBOT-002-1/2/3 currently describe. | UC §8 AC-ms-01b; audit v6 V-009 (Major, Open — direct conflict with `us-002.md`, unresolved) | New test case required to cover AC-ms-01b directly (wallet-matching Investor still gets 403). This is the direct replacement for TC_048's now-contradicted intent. |
| CH-07 | AMBIGUOUS | v5: the `isAdmin` guard did not exist, so this question did not apply. | v6: the UC defines the guard's 403 behavior but does **not** define a message body or `E-EXBOT-*` code for it — unlike every other 403 in the UC, which all carry a defined error code. | UC §6.1.C Error/messages table; audit v6 V-012 (Minor, Open) | New test case should assert HTTP status code 403 only for the guard rejection — explicitly must NOT hard-code a message-text assertion until BA confirms (V-012). |
| CH-08 | CLARIFIED | v5: `runtime_health_status` vs ERD column `health_status` was an unresolved naming conflict (V-001). | v6: strong indirect technical evidence (ERD changelog 2026-07-20, `runtime-state.ts`, `get-bot-status` handler) confirms the column was renamed to `runtime_health_status` to match the UC — but BA has not yet given a genuine verbal confirmation (the answer file repeats the question verbatim), so it remains formally Open. | UC §6.1.D Field Inventory row 4; audit v6 V-001 (Open — technical evidence sufficient, formal BA confirmation still pending) | No TC change required now — TC_047 already carries this exact caveat and continues to use the UC-stated name `runtime_health_status`. Carried forward as a non-blocking open note. |

#### User Feedback Interpretation

_No user feedback was supplied for this run — trigger type is pure REQUIREMENT_DELTA. This section is intentionally empty._

| Feedback ID | Feedback | Interpretation | TC impact | Handling status |
|---|---|---|---|---|
| — | — | — | — | N/A |

#### Test Case Impact Matrix

| TC ID | Current title | Impact Status | Reason | Proposed action |
|---|---|---|---|---|
| TC_001 | Full status response, 8 Implemented non-null + 11 Pending null | UPDATE | CH-01 (add explicit Admin actor precondition), CH-02 (endpoint `{botId}`), CH-04 (firm up null wording) | Add Admin actor precondition; reword endpoint; firm up v1-gap null wording |
| TC_002 | range_state/current_tick are Pending, null even in-range | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_003 | range_state='out' when Pending fields implemented (currentTick=tick_upper) | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_004 | range_state='in' when Pending fields implemented (tick_upper-1) | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_005 | range_state='out' when Pending fields implemented (below tick_lower) | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_006 | safe_mode response reflects correctly, safe_mode_reason Pending null | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_007 | hedge_stopped_cooldown, cooldown_end_at Pending null | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_008 | No bot record → 404 E-EXBOT-023 | UPDATE | CH-01 (must be Admin to reach the not-found check at all), CH-02 | Add Admin actor precondition; reword endpoint |
| TC_009 | drift_pct BigDecimal + normalizeTargetRatioBps() formula | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_010 | drift_pct exactly zero when actual=target | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_011 | drift_pct precision preserved for large values | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_012 | margin_status='warning' Pending field | UPDATE | CH-01, CH-02, CH-04 (firm up wording) | Add Admin actor precondition; reword endpoint; firm up wording |
| TC_013 | margin_status='critical' Pending field | UPDATE | CH-01, CH-02, CH-04 | Add Admin actor precondition; reword endpoint; firm up wording |
| TC_014 | SAFE_MODE not presented as terminal | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_015 | coarse status='active' while lifecycle_state='hedge_stopped_cooldown' | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_016 | lp_rebalancing transient state reflected | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_017 | HTTP 503 when Facade cannot reach Lambda | UPDATE | CH-02 only — infra-level failure occurs at the Facade↔Lambda hop, before/independent of the guard; actor is irrelevant here | Reword endpoint only |
| TC_018 | margin_status boundary at ok/warning threshold | UPDATE | CH-01, CH-02, CH-04 | Add Admin actor precondition; reword endpoint; firm up wording |
| TC_019 | error state reflected, distinguished from SAFE_MODE | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_020 | closed bot → HTTP 200 (not 404) | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_021 | two back-to-back calls return identical data | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_022 | lp_closing → HTTP 200 + E-EXBOT-021 | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_023 | closed bot → HTTP 200 + E-EXBOT-022 | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_024 | HTTP 401 when X-Wallet-Address header missing | UPDATE | CH-02 only — rejected at Operator Facade before any actor/guard check applies | Reword endpoint only |
| TC_025 | HTTP 403 E-EXBOT-030 when Investor wallet mismatches owner | **RETIRE** | CH-01/V-009 — in v1, an Investor calling this endpoint is rejected by the `isAdmin` guard at step 2b, before the wallet-ownership check (step 3/A9) is ever evaluated. This TC's core intent (verify the E-EXBOT-030 ownership check) can no longer be exercised via an Investor actor. | Retire; replaced by new TC_071 (guard blocks mismatched-wallet Investor with 403, not E-EXBOT-030) |
| TC_026 | Admin can query any bot regardless of ownership | UPDATE | CH-02 only — this TC already correctly uses Admin actor; still valid and now more central since Admin is the only actor that reaches business logic in v1 | Reword endpoint only |
| TC_027 | hedge size/margin_status reflect latest hedge-sync write | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_028 | Facade forwards Lambda response unchanged | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_029 | current_tick read from Pool Slot0 Cache only, no RPC | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_030 | Base-chain bot uses Base pool's cache tick | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_031 | SAFE_MODE transition immediately visible | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_032 | ten concurrent requests return consistent data | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_033 | full pipeline E2E through Facade/Gateway/Lambda/Aurora/Cache | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_034 | first call after bot-start returns 8 Implemented fields populated | UPDATE | CH-01, CH-02, CH-04 | Add Admin actor precondition; reword endpoint; firm up wording |
| TC_035 | exactly 11 Pending fields present as null | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_036 | ExBot Lambda returns 403 when called directly, bypassing API Gateway | UPDATE | CH-02 note only — tests the Lambda function URL directly, not the Facade path-param endpoint; no actor applies (request is rejected before any auth identity is evaluated) | No content change needed beyond version/prelude bump; carried forward as-is |
| TC_037 | HMAC Authorizer rejects missing/invalid signature | UPDATE | CH-02 note only — HMAC check happens before the `isAdmin` guard in the flow; unaffected by CH-01 | Reword endpoint only |
| TC_038 | No sensitive data in response body or Lambda logs | UPDATE | CH-01, CH-02 — needs a successful (Admin) call to inspect a real response body | Add Admin actor precondition; reword endpoint |
| TC_039 | HTTP 401 when Facade forwards invalid HMAC signature | UPDATE | CH-02 note only — HMAC check precedes the guard; unaffected by CH-01 | Reword endpoint only |
| TC_040 | Pool Slot0 Cache unavailable → 200, current_tick/range_state null | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_041 | Pool Slot0 Cache stale snapshot treated as unavailable | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_042 | range_state null, no computation when current_tick null | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_043 | BVA rangeState: tickLower-1 → 'out' | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_044 | margin_status='normal' below 0.55 | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_045 | margin_status='critical' at/above 0.75 | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_046 | HTTP 403 when wallet blocked by Operator Facade | UPDATE | CH-02 only — rejected at Facade block-list check, before any guard/actor logic | Reword endpoint only |
| TC_047 | All 8 Implemented fields always present as keys | UPDATE | CH-01, CH-02, CH-04, CH-08 | Add Admin actor precondition; reword endpoint; firm up V-002/V-003/V-007 wording; keep V-001 caveat as-is |
| TC_048 | Investor can query their own bot — HTTP 200 | **RETIRE** | CH-01/V-009 / CH-06 — directly contradicted: an Investor with a matching wallet now receives HTTP 403 from the `isAdmin` guard, not HTTP 200. | Retire; replaced by new TC_070 (AC-ms-01b: wallet-matching Investor still gets 403) |
| TC_049 | Response reflects paused state — status='paused', lifecycle_state='active' | UPDATE | CH-01, CH-02, CH-03 (A10 now formal, add E-EXBOT-031 message assertion; remove "V-008 open" caveat since it is now Resolved) | Add Admin actor precondition; reword endpoint; add E-EXBOT-031 message assertion; update note to V-008 Resolved |
| TC_050 | Transitional lifecycle_state returns HTTP 200 with exact value | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_051 | Status maps all 18 canonical lifecycle_state values | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_052 | drift_pct null when lp_eth_amount=0 | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_053 | drift_pct null when lp_eth_amount=null | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_054 | drift_pct formula uses normalizeTargetRatioBps() with BigDecimal | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_055 | margin_status='normal' returned (renamed from 'ok') | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_056 | Full JSON response contains exactly 19 fields | UPDATE | CH-01, CH-02, CH-04 | Add Admin actor precondition; reword endpoint; firm up wording |
| TC_057 | bot_id matches bots.id primary key | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_058 | lp_eth_amount/lp_usdc_amount match positions table | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_059 | range_state consistent with currentTick at query time | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_060 | Status call after rebalance reflects post-rebalance data | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_061 | safe_mode not permanent — bot transitions back to active | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_062 | Status call immediately after active→safe_mode returns new state | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_063 | Status call immediately after active→error returns new state | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_064 | Aurora cold-start does not return 200 with empty body | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_065 | HMAC key rotation — new key accepted, old key rejected | UPDATE | CH-02 note only — HMAC check precedes the guard; unaffected by CH-01 | Reword endpoint only |
| TC_066 | Status response latency under normal load | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_067 | Data inconsistency between bots and bot_runtime_state surfaced clearly | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_068 | Five concurrent requests from same wallet, no data mixing | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |
| TC_069 | Three sequential calls with no state change return identical data | UPDATE | CH-01, CH-02 | Add Admin actor precondition; reword endpoint |

#### Proposed New Test Cases

| Proposed TC ID | Title | Source of change | TC type | Priority | Note |
|---|---|---|---|---|---|
| TC_070 | Verify an Investor whose wallet matches the bot owner still receives HTTP 403 due to the isAdmin guard | CH-01 (V-009), CH-06 (AC-ms-01b) | FUNC | P0 | Direct replacement for TC_048's retired intent. Must assert 403, not 200 — this is v1's actual (gap) behavior, not a bug. |
| TC_071 | Verify an Investor whose wallet does NOT match the bot owner receives the same HTTP 403 from the isAdmin guard, indistinguishable from the matching-wallet case | CH-01 (V-009), AC-ms-05 | FUNC | P0 | Direct replacement for TC_025's retired intent. Confirms the guard — not E-EXBOT-030 — is what fires for Investor in v1. |
| TC_072 | Decision table — confirm the isAdmin guard evaluates before the wallet-ownership check across {Admin/other's bot, Admin/own bot, Investor/match, Investor/mismatch} | CH-01 (V-009), AC-ms-05 | FUNC | P0 | Combines TC_070/TC_071/TC_026 into one explicit 4-row decision table proving guard order; does not replace those TCs, adds cross-cutting confirmation. |
| TC_073 | Verify the isAdmin guard's 403 response asserts only the HTTP status code — no message-text assertion until BA confirms the response body | CH-07 (V-012) | FUNC | P1 | Explicitly documents the open gap (V-012) so no tester later hard-codes an unconfirmed message string. |

#### Test Cases Proposed for Retire / Merge

| TC ID | Title | Reason | Replacement / Merge target |
|---|---|---|---|
| TC_025 | Verify HTTP 403 with E-EXBOT-030 when Investor wallet address does not match the bot's owner | Contradicted by CH-01/V-009 — Investor never reaches the ownership check in v1; the check is unreachable, not merely untested. | TC_071 |
| TC_048 | Verify Investor can query their own bot — HTTP 200 | Contradicted by CH-01/V-009 and CH-06/AC-ms-01b — the expected result (200) is factually wrong for v1. | TC_070 |

#### Open Questions / Items to Confirm

| Item | Source | Why confirmation is needed | Decision required from user |
|---|---|---|---|
| Q1 | CH-01 / TC_025, TC_048 | This report proposes **retiring** TC_025 and TC_048 outright (rather than repurposing their IDs) because their expected results are now factually false, not just outdated wording. Retiring removes them from the active TC tables (per `RETIRE` apply rule) and records them only in this report / the final md's RTM as `Removed`. | Confirm retiring (not repurposing) TC_025 and TC_048 is acceptable, or ask to repurpose the IDs instead. |
| Q2 | CH-05 (V-004 Resolved) | `dry_run`'s data source (`EXBOT_DRY_RUN` env var) is now confirmed, but no existing or proposed TC specifically toggles it true/false — current TCs only assert it is present and non-null as part of the 8-field check. | Confirm whether a dedicated `dry_run` true/false test case should be added now, or deferred as out-of-scope for this update. |
| Q3 | V-001 (still formally Open) | BA's answer for `runtime_health_status` vs `health_status` repeats the question verbatim rather than confirming it — strong indirect technical evidence exists (ERD changelog), but no update is proposed to TC_047's existing caveat pending a real BA confirmation. | Confirm no action is needed on TC_047 until V-001 is formally closed by BA (no decision blocks this update either way). |

#### Approval Instructions

You can respond in one of the following ways:

- `Approve update report` to apply exactly as described in this report.
- Send additional feedback if the report needs revision before it is applied.
- `Cancel` to stop the workflow; the plan stays in the process-logging folder so you can resume later.
