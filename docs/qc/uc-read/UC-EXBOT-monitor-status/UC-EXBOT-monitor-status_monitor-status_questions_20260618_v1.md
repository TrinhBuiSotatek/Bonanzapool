---
title: Question Backlog — UC-EXBOT-monitor-status
date: 2026-06-18
author: qc-uc-read-exbot
version: v1
---

# Question Backlog — UC-EXBOT-monitor-status

> Generated: 2026-06-18
> Source: docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260618_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-001 | High | UC §4 A3 vs srs/states.md HLD-2026-06-18; frd.md §2 | UC §4 A3 describes an alternate flow for `lifecycle_state='cooldown' after bot_safe_close` with message "Bot safely closed. USDC parked. Re-entry will be attempted automatically." However, states.md updated 2026-06-18 explicitly removes `cooldown` and `parked` lifecycle states. The UC was not updated. BA: remove A3 from UC §4 and remove the "Cooldown" label from the Status label list at step 9. After bot_safe_close, lifecycle transitions directly to `closed` — no parked/cooldown state exists. | Tester designing test cases for A3 will create test data with `lifecycle_state='cooldown'` — a state that cannot exist after HLD-2026-06-18. Additionally, the "Cooldown" label in step 9 Status list compounds the confusion. | Open |
| I-002 | High | UC §3 step 9 vs srs/states.md HLD-2026-06-18 | UC §3 step 9 lists "Status label (Active/Safe Mode/Cooldown)" as possible display labels. The "Cooldown" label corresponds to `lifecycle_state='cooldown'` which was removed by HLD-2026-06-18. BA: update the Status label list at step 9 to remove "Cooldown" and use only valid post-HLD states. | Tester building test data for the "Cooldown" label will test behavior that cannot occur. | Open |
| I-003 | High | UC §3 step 3 vs step 9; erd.md bots + bot_runtime_state | UC §3 step 3 reads `next_light_check_at` (a future-scheduled timestamp from `bots` table), but step 9 says to display "Last light-check timestamp" (a past timestamp). These are different fields: `bots.next_light_check_at` vs `bot_runtime_state.last_light_check_at`. BA: clarify which field is read and displayed. Update step 3 to name the exact D1 field, and align step 9 label to match (either "Last light-check" reading `last_light_check_at` or "Next light-check" reading `next_light_check_at`). | Tester cannot determine which field to verify in the response — reading `next_light_check_at` but displaying "Last light-check" produces a semantically wrong value. | Open |
| I-004 | High | UC §3 step 6; srs/spec.md FR-EXBOT-021; erd.md bot_runtime_state | UC §3 step 6 computes drift % as `(|actualShortEth - targetShortEth| / targetShortEth) × 100` but does not define the source of `targetShortEth`. SRS FR-EXBOT-021 defines `targetShortEth = lpEthAmount × hedgeRatio` (recomputed each time). erd.md `bot_runtime_state` has a `target_short_size` column. The question: does monitor-status (a) read `target_short_size` from D1 directly, or (b) recompute from current LP amounts? If (a), the field is not in the D1 read list at step 3. BA/Tech Lead: specify the source of `targetShortEth` for drift % computation in this UC. | Tester cannot write a drift % test case without knowing where `targetShortEth` comes from. If from cached D1 value, drift % may differ from a live recalculation. | Open |
| I-005 | High | UC §4; srs/spec.md FR-EXBOT-093 | UC §4 has alternate flow A5 for Operator Facade unavailable (HTTP 503) but has no alternate flow for when MarketDataDO is unavailable or its cache exceeds 2× the refresh interval. FR-EXBOT-093 states the DO auto-refreshes on staleness, but if the DO is completely unreachable during the request, ExBot Worker behavior is undefined: return a partial response (missing currentTick/rangeState), or return HTTP 503? BA: add alternate flow A6 for MarketDataDO unavailable. | Tester cannot design a test case for MarketDataDO failure in the monitor-status context. | Open |
| I-006 | High | UC §4; srs/spec.md FR-EXBOT-005; US-EXBOT-002 | UC §4 has no alternate flow for `status='paused'`. SRS FR-EXBOT-005 defines that the status screen for a paused bot must show "Paused — hedge is maintained, LP is maintained." US-002 also has no AC for the paused state. BA: add an alternate flow for `status='paused'` in UC §4, describing the message and UI behavior; add a corresponding AC to US-002. | Tester cannot design test cases for the paused state because neither the UC nor the US describes it. | Open |
| I-007 | Medium | UC §7 FR Trace; srs/spec.md FR-EXBOT-003 | UC §6 FR Trace includes FR-EXBOT-003 (Bot Lifecycle State Tracking — defines 18 lifecycle states and the initialization sequence). Most of FR-003 is about bot initialization and state transitions, not reading state. If this trace is intentional, the UC §4 should include alternate flows for all 18 lifecycle states (e.g., `lp_rebalancing`, `lp_closing`, `error`). BA: confirm whether FR-003 trace is intentional. If so, add alternate flows for missing lifecycle states. If not, remove FR-003 from the FR Trace. | Tester needs to know whether all 18 lifecycle states are in scope for this UC or only the subset shown. | Open |
| I-008 | Medium | UC §4 A1; erd.md bots; srs/spec.md FR-EXBOT-050 | UC §4 A1 says response includes `safe_mode_reason`, but the `bots` table in erd.md has no `safe_mode_reason` column. The field is not in the D1 read list at step 3. The `bots` table has `health_status` which may serve this purpose, but this is not confirmed. BA/Tech Lead: identify which D1 column stores `safe_mode_reason` (or whether it needs to be added) and update UC §3 step 3 to read that field. | Tester cannot verify that `safe_mode_reason` is returned correctly in the A1 response without knowing the source column. | Open |
| I-009 | Medium | UC §4 A2; erd.md; srs/spec.md FR-EXBOT-034 | UC §4 A2 says response includes "cooldown end timestamp" for UI to compute "Xh remaining." However, the `bots` and `hedge_legs` tables in erd.md have no column for cooldown end time. FR-EXBOT-034 defines cooldown as 4 hours after stop fires but does not specify which D1 column stores the end time. BA/Tech Lead: define the D1 column for cooldown end time (may need a new column, or compute from `hedge_legs.stop_trigger_crossed_at + 4h`) and update UC §3 step 3 to read that field. | Tester cannot verify "Xh remaining" is calculated correctly without knowing which D1 field is the source. | Open |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason for Deferral | Status |
|----|----------|-----|----------|---------------------|--------|
