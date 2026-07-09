# Test Cases — UC-EXBOT-deep-audit Periodic Deep Audit and Backstop SAFE_MODE Detection

**Total test cases:** 35 (FUNC: 21, INTG: 12, NFR: 2)
**Scope:** Logic-only (backend / API / bot — no UI)
**Phase:** Phase A (v1) — stub verification only; all functional tests deferred to v1.1
**Update trigger:** REQUIREMENT_DELTA
**Source UC:** `docs/qc/uc-read/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_audited_20260709_v3.md` (v3, re-audit 2026-07-09)
**Source scenarios:** `docs/qc/scenarios/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_scenarios_20260709_v3.md` (31 scenarios)
**Output language:** English

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-DA-01 | Happy path — audit completes without issues | TC_001, TC_002, TC_003, TC_004, TC_015 | v1.1 |
| AC-DA-02 | Mismatch detection → SAFE_MODE | TC_005, TC_006, TC_007 | v1.1 |
| AC-DA-03 | stop_trigger_crossed_at stuck > 30min → SAFE_MODE | TC_008, TC_009, TC_010, TC_011 | v1.1 |
| AC-DA-04 | stop_replacing_started_at stuck > 60s → SAFE_MODE | TC_012, TC_013, TC_014 | v1.1 |
| AC-DA-05 | HL unreachable → graceful degradation | TC_016, TC_017, TC_018, TC_019 | v1.1 |
| AC-DA-06 | Paused bot still audited | TC_020, TC_021, TC_022 | v1.1 |
| AC-DA-07 | High-risk cadence switching | TC_023, TC_024, TC_025, TC_026 | v1.1 |
| AC-DA-08 | Idempotency prevents duplicate | TC_027, TC_028 | v1.1 |
| AC-DA-09 | `last_known_hl_short_size` always synced | TC_033, TC_034 | v1.1 |
| AC-DA-10 | Phase A test deferred — v1 deep-audit is stub | TC_035, TC_036 | Phase A (v1) |

---

## I. Operation: Periodic Deep Audit (deep-audit)

### I.1. Functional verification — Operation: Periodic Deep Audit (deep-audit)

> **Phase:** All test cases in this section are **v1.1** (Phase A deferred).
> **Note:** v1 deep-audit is a stub (`observeDeepAudit()` does not call HL API). Phase A tests verify stub behavior only (see TC_035, TC_036).

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority | Phase |
|---|---|---|---|---|---|---|
| TC_001 | Verify the deep-audit happy path completes without triggering SAFE_MODE | 1. The bot is in `active` status with no hedge size mismatch. 2. No stuck markers are set (`stop_trigger_crossed_at` and `stop_replacing_started_at` are both NULL). 3. Hyperliquid API is reachable and returns valid clearinghouseState and marginSummary. | 1. Bot-scan triggers (`rate: 1 minute`) and queries `bots WHERE status='active' AND next_deep_audit_at <= now`. 2. Bot-scan fans out per-bot SQS message. 3. Deep-audit Lambda processes 1 `botId` per invocation. 4. Worker reads bot state from Aurora PostgreSQL, calls HL clearinghouseState via HL Rate Limiter (weight=2), verifies short size matches `last_known_hl_short_size`, checks stuck markers, fetches marginSummary, updates `last_audit_at` and `next_deep_audit_at=now+6h`. | 1. Audit completes successfully: `hedge_legs.margin_status` updated from HL, `hedge_legs.last_audit_at` set to current timestamp, `bots.next_deep_audit_at` set to `now+6h`, and `queue_idempotency` row inserted with `state='succeeded'`. No SAFE_MODE entry. (Reference: AC-DA-01, FR-EXBOT-016.) | P0 | v1.1 |
| TC_002 | Verify `last_audit_at` is updated after every successful deep-audit cycle | 1. The bot is in `active` status. 2. A previous deep-audit has set `hedge_legs.last_audit_at` to a known timestamp. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot. 2. After Lambda completes, read `hedge_legs.last_audit_at` value. | 1. `hedge_legs.last_audit_at` is updated to the current timestamp (later than the previous value). (Reference: FR-EXBOT-016, UC Step 7.) | P0 | v1.1 |
| TC_003 | Verify margin status is updated from HL marginSummary after deep-audit | 1. The bot is in `active` status with an existing `hedge_legs.margin_status` value. 2. HL marginSummary returns a different margin status than the current Aurora PostgreSQL value. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot. 2. After Lambda completes, read `hedge_legs.margin_status` value. | 1. `hedge_legs.margin_status` is updated to match the fresh HL marginSummary data. (Reference: FR-EXBOT-016, FR-EXBOT-060, UC Step 6.) | P1 | v1.1 |
| TC_004 | Verify deep-audit processes only bots with status IN ('active','paused') | 1. Aurora PostgreSQL contains bots with various statuses including `active`, `paused`, `closed`, and `error`. | 1. Bot-scan queries `bots WHERE status IN ('active','paused') AND next_deep_audit_at <= now`. 2. Observe which bots are read and processed. | 1. Only bots with `bots.status IN ('active','paused')` are read and processed. Bots with `closed`, `error`, `idle`, or other statuses are excluded. `bots.next_deep_audit_at` filter is applied by bot-scan. (Reference: UC §2 Preconditions, FR-EXBOT-016, states.md row 71.) | P0 | v1.1 |
| TC_005 | Verify reconcile mismatch triggers SAFE_MODE entry | 1. The bot is in `active` status. 2. HL clearinghouseState returns an actual short size that differs from `hedge_legs.last_known_hl_short_size`. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot with mismatch (actual ≠ last_known). | 1. Bot enters `safe_mode`. Worker **always updates** `last_known_hl_short_size = actual HL size` and `last_hl_reconcile_at = now` **before** triggering SAFE_MODE (bất kể match hay mismatch). Mismatch is recorded with size delta. Admin notification E-EXBOT-011 enqueued. (Reference: AC-DA-02, FR-EXBOT-050, E-EXBOT-011.) | P0 | v1.1 |
| TC_006 | Verify reconcile mismatch records the size delta correctly when actual is greater | 1. The bot is in `active` status. 2. The actual HL short size is greater than `hedge_legs.last_known_hl_short_size`. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot with positive delta (actual > expected). | 1. Aurora PostgreSQL mismatch record stores the positive delta (actual minus expected). `last_known_hl_short_size` is updated to actual. SAFE_MODE is triggered. (Reference: FR-EXBOT-050, UC A3.) | P1 | v1.1 |
| TC_007 | Verify reconcile mismatch records the size delta correctly when actual is less | 1. The bot is in `active` status. 2. The actual HL short size is less than `hedge_legs.last_known_hl_short_size`. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot with negative delta (actual < expected). | 1. Aurora PostgreSQL mismatch record stores the negative delta (actual minus expected). `last_known_hl_short_size` is updated to actual. SAFE_MODE is triggered. (Reference: FR-EXBOT-050, UC A3.) | P1 | v1.1 |
| TC_008 | Verify stop_trigger_crossed_at stuck for more than 30 minutes triggers SAFE_MODE | 1. The bot is in `active` status. 2. `hedge_legs.stop_trigger_crossed_at` is set to a timestamp older than 30 minutes ago. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when `stop_trigger_crossed_at` age > 30 min. | 1. Bot enters `safe_mode`. Admin escalation E-EXBOT-019 enqueued: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." (Reference: AC-DA-03, FR-EXBOT-033, FR-EXBOT-050, E-EXBOT-019.) | P0 | v1.1 |
| TC_009 | Verify stuck detection boundary — age exactly 30 minutes does NOT trigger SAFE_MODE | 1. The bot is in `active` status. 2. `hedge_legs.stop_trigger_crossed_at` is set to exactly 30 minutes ago. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when elapsed time = exactly 30 min. | 1. Stuck condition evaluates to false (elapsed time is not greater than 30 minutes). No SAFE_MODE entry. Audit proceeds to next check. (Reference: FR-EXBOT-033, UC Step 4 boundary.) | P0 | v1.1 |
| TC_010 | Verify stuck detection boundary — age exactly 31 minutes triggers SAFE_MODE | 1. The bot is in `active` status. 2. `hedge_legs.stop_trigger_crossed_at` is set to exactly 31 minutes ago. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when elapsed time > 30 min. | 1. Stuck condition evaluates to true (31 min > 30 min). SAFE_MODE triggered with E-EXBOT-019. (Reference: FR-EXBOT-033, UC Step 4 boundary.) | P0 | v1.1 |
| TC_011 | Verify stop_trigger_crossed_at being NULL skips the stuck check | 1. The bot is in `active` status. 2. `hedge_legs.stop_trigger_crossed_at` is NULL. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when `stop_trigger_crossed_at` is NULL. | 1. Stuck condition evaluates to false (NULL fails "IS NOT NULL" check). Worker proceeds to Step 5 without triggering SAFE_MODE. (Reference: BR-EXBOT-005, UC Step 4.) | P0 | v1.1 |
| TC_012 | Verify stop_replacing_started_at stuck for more than 60 seconds triggers SAFE_MODE | 1. The bot is in `active` status. 2. `hedge_legs.stop_replacing_started_at` is set to a timestamp older than 60 seconds ago. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when `stop_replacing_started_at` age > 60s. | 1. Bot enters `safe_mode`. Admin escalation E-EXBOT-020 enqueued: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required." (Reference: AC-DA-04, FR-EXBOT-033, FR-EXBOT-050, E-EXBOT-020.) | P0 | v1.1 |
| TC_013 | Verify stuck detection boundary — age exactly 60 seconds does NOT trigger SAFE_MODE | 1. The bot is in `active` status. 2. `hedge_legs.stop_replacing_started_at` is set to exactly 60 seconds ago. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when elapsed time = exactly 60s. | 1. Stuck condition evaluates to false (elapsed time is not greater than 60 seconds). No SAFE_MODE entry. Audit proceeds to Step 6. (Reference: FR-EXBOT-033, UC Step 5 boundary.) | P0 | v1.1 |
| TC_014 | Verify stop_replacing_started_at being NULL skips the stuck check | 1. The bot is in `active` status. 2. `hedge_legs.stop_replacing_started_at` is NULL. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot when `stop_replacing_started_at` is NULL. | 1. Stuck condition evaluates to false (NULL fails "IS NOT NULL" check). Worker proceeds to Step 6 without triggering SAFE_MODE. (Reference: BR-EXBOT-005, UC Step 5.) | P0 | v1.1 |
| TC_015 | Verify deep-audit with zero active or paused bots completes without error | 1. Aurora PostgreSQL contains no bots with `status IN ('active','paused')` or no bots with `next_deep_audit_at <= now`. | 1. Bot-scan queries and receives empty result set. No SQS fan-out. | 1. Bot-scan cycle completes successfully. No SQS messages fan-out. No HL calls, no Aurora PostgreSQL writes for bot records, no notifications. `queue_idempotency` row may still be inserted for the cycle. (Reference: UC §2 Preconditions.) | P1 | v1.1 |

### I.2. Integration & State verification — Operation: Periodic Deep Audit (deep-audit)

> **Phase:** All test cases in this section are **v1.1** unless marked as Phase A (v1).

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority | Phase |
|---|---|---|---|---|---|---|
| TC_016 | Verify HL API unreachable causes graceful degradation without crashing the worker | 1. The bot is in `active` status. 2. HL Rate Limiter returns `{allowed: false}` or HL API returns a 5xx error. | 1. Bot-scan → fan-out SQS → deep-audit Lambda attempts HL call. 2. HL Rate Limiter denies request. | 1. Steps 2, 3, 4, 6, 7 (HL-dependent) are skipped. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`** (not EventBridge self-switch). Notification E-EXBOT-008 "Hyperliquid API unreachable" enqueued. Retry-pending state recorded. Bot stays in current state. (Reference: AC-DA-05, UC A1, E-EXBOT-008.) | P0 | v1.1 |
| TC_017 | Verify deep-audit calls HL clearinghouseState with weight=2 via HL Rate Limiter | 1. The bot is in `active` status. 2. HL Rate Limiter has available weight budget (remaining >= 2). | 1. Bot-scan → fan-out SQS → deep-audit Lambda calls HL via Rate Limiter. | 1. Worker calls HL clearinghouseState with declared weight=2 through HL Rate Limiter. BR-EXBOT-003 (HL weight=0) does NOT apply — this is the documented exception. **Deep-audit v1.1 does not use Redis Redlock** (no hedge mutation). (Reference: FR-EXBOT-091, UC Step 2.) | P0 | v1.1 |
| TC_018 | Verify HL Rate Limiter returning false causes deep-audit to re-queue without proceeding | 1. The bot is in `active` status. 2. HL Rate Limiter has insufficient weight budget and returns `{allowed: false, retryAfterMs}`. | 1. Bot-scan → fan-out SQS → deep-audit Lambda call denied by Rate Limiter. | 1. Worker does NOT proceed with HL call. Message re-queued with delay. No partial state written. (Reference: FR-EXBOT-091.) | P1 | v1.1 |
| TC_019 | Verify partial HL failure — clearinghouseState succeeds but marginSummary fails | 1. The bot is in `active` status. 2. HL clearinghouseState succeeds; HL marginSummary fails with 5xx. | 1. Bot-scan → fan-out SQS → deep-audit Lambda: Step 2 succeeds, Step 6 fails. | 1. Steps 2 and 3 complete normally (including **always syncing `last_known_hl_short_size`**). Step 6 (marginSummary) skipped. Steps 7 and 8 still complete. `hedge_legs.margin_status` retains previous value. (Reference: UC Steps 2, 6, A1.) | P1 | v1.1 |
| TC_020 | Verify paused bot is fully audited including stuck marker detection | 1. The bot has `bots.status='paused'`. 2. No stuck markers are set. 3. HL API is reachable. | 1. Bot-scan includes paused bots in query `WHERE status IN ('active','paused')`. 2. Fan-out SQS → deep-audit Lambda processes paused bot. | 1. All detection paths (Steps 3–7) execute normally: clearinghouseState reconciliation, stuck marker checks, marginSummary fetch, `last_audit_at` update. **Pause does NOT skip deep-audit.** (Reference: AC-DA-06, FR-EXBOT-005, UC A2.) | P0 | v1.1 |
| TC_021 | Verify paused bot with stuck stop_trigger_crossed_at transitions paused to safe_mode | 1. The bot has `bots.status='paused'` and `hedge_legs.stop_trigger_crossed_at` is set and aged > 30 min. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes paused bot with stuck marker. | 1. Bot transitions from `paused` to `safe_mode`. Admin escalation E-EXBOT-019 enqueued. (Reference: FR-EXBOT-005, FR-EXBOT-033, FR-EXBOT-050, states.md row 71.) | P0 | v1.1 |
| TC_022 | Verify both stuck markers set simultaneously — first condition triggers SAFE_MODE | 1. The bot is in `active` status. 2. Both `stop_trigger_crossed_at` (aged >30 min) and `stop_replacing_started_at` (aged >60s) are set simultaneously. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot with both stuck conditions true. | 1. Step 4 evaluates first — `stop_trigger_crossed_at` stuck is true. SAFE_MODE triggered and E-EXBOT-019 enqueued. Step 5 is not reached. Only E-EXBOT-019 sent (first-triggered wins). (Reference: FR-EXBOT-033, FR-EXBOT-050, UC Steps 4–5 + A4.) | P1 | v1.1 |
| TC_023 | Verify circuit_breaker open triggers high-risk cadence switching to 1 hour | 1. `circuit_breakers.state='open'`. 2. The bot is in `active` status. | 1. Bot-scan → fan-out SQS → deep-audit Lambda detects `circuit_breakers.state='open'`. | 1. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`** (not EventBridge self-switch). Bot-scan queries `WHERE status='active' AND next_deep_audit_at <= now` every 1 min. Subsequent audits at 1h cadence until `circuit_breakers.state='closed'`. (Reference: AC-DA-07, FR-EXBOT-040, UC §2 Preconditions.) | P0 | v1.1 |
| TC_024 | Verify margin_status='warning' triggers high-risk cadence switching to 1 hour | 1. The bot has `hedge_legs.margin_status='warning'`. 2. The bot is in `active` status. | 1. Bot-scan → fan-out SQS → deep-audit Lambda detects `margin_status='warning'`. | 1. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**. If Step 6 updates `margin_status` from warning to ok, cadence may revert. (Reference: AC-DA-07, FR-EXBOT-060, UC §2 Preconditions.) | P1 | v1.1 |
| TC_025 | Verify margin_status='critical' triggers high-risk cadence switching to 1 hour | 1. The bot has `hedge_legs.margin_status='critical'`. 2. The bot is in `active` status. | 1. Bot-scan → fan-out SQS → deep-audit Lambda detects `margin_status='critical'`. | 1. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**. (Reference: AC-DA-07, FR-EXBOT-060, UC §2 Preconditions.) | P1 | v1.1 |
| TC_026 | Verify normal 6-hour cadence is maintained when all conditions are nominal | 1. `circuit_breakers.state='closed'` and `hedge_legs.margin_status='ok'`. 2. No stuck markers. 3. Bot is `active`. | 1. Bot-scan → fan-out SQS → deep-audit Lambda processes bot under nominal conditions. | 1. No cadence switching. **Lambda updates `bots.next_deep_audit_at` to `now + 6h`**. Bot-scan picks up due bots at 1-min interval. (Reference: FR-EXBOT-016, UC §2 Preconditions.) | P0 | v1.1 |
| TC_027 | Verify queue idempotency — duplicate message delivery is rejected | 1. A deep-audit message with specific `message_id` has already been processed successfully (`queue_idempotency` row with `state='succeeded'`). | 1. Re-deliver the same `message_id` in a new SQS delivery. | 1. Worker attempts to insert `queue_idempotency` with `state='started'` and hits UNIQUE constraint conflict on `message_id`. Worker returns immediately without re-processing. First delivery's `state='succeeded'` row remains intact. (Reference: AC-DA-08, FR-EXBOT-011.) | P0 | v1.1 |
| TC_028 | Verify idempotency state progression — started to succeeded on first processing | 1. A new deep-audit message with unique `message_id` is received. | 1. Process the new deep-audit message through to completion. 2. Read `queue_idempotency` row state. | 1. Worker inserts `queue_idempotency` with `state='started'` at beginning. After completion, row updated to `state='succeeded'`. (Reference: FR-EXBOT-011, UC Step 8.) | P0 | v1.1 |
| TC_029 | Verify deep-audit reads from correct Aurora PostgreSQL — bot state joined correctly | 1. The bot is in `active` status with valid records in `bots`, `hedge_legs`, and `circuit_breakers` tables. | 1. Bot-scan → fan-out SQS → deep-audit Lambda reads bot state for 1 `botId`. | 1. Worker correctly joins `hedge_legs` to `bots` on `bot_id`. Reads `bots.status`, `bots.lifecycle_state`, `hedge_legs`, `circuit_breakers.state`, `margin_status`. All fields present and valid. **Shard iteration handled by bot-scan layer, not deep-audit Lambda.** (Reference: FR-EXBOT-016, NFR-EXBOT-012, UC Step 1.) | P1 | v1.1 |
| TC_033 | Verify reconciliation mismatch — `last_known_hl_short_size` always synced before SAFE_MODE entry | 1. The bot is in `active` status. 2. HL clearinghouseState returns actual short size ≠ `hedge_legs.last_known_hl_short_size`. | 1. Bot-scan → fan-out SQS → deep-audit Lambda detects mismatch. 2. Immediately after mismatch detection but before SAFE_MODE entry, read `last_known_hl_short_size`. 3. After SAFE_MODE entry, read `last_known_hl_short_size` again. | 1. Worker **ALWAYS updates** `bot_runtime_state.last_known_hl_short_size = actual HL size` and `last_hl_reconcile_at = now` **bất kể match hay mismatch** — before triggering SAFE_MODE. Subsequent deep-audit will NOT re-detect the same mismatch because field is already synced. **This prevents potential loop.** (Reference: AC-DA-09, FR-EXBOT-016, FR-EXBOT-050, Q-DA-07 resolved 2026-07-09.) | P0 | v1.1 |
| TC_034 | Verify subsequent deep-audit after mismatch does not re-detect same mismatch | 1. The bot entered SAFE_MODE due to reconcile mismatch. 2. `last_known_hl_short_size` has been synced to actual HL size. | 1. Run a second deep-audit cycle after SAFE_MODE entry. 2. Observe whether mismatch is re-detected. | 1. Second deep-audit does NOT re-detect mismatch because `last_known_hl_short_size` already equals actual HL size. No additional SAFE_MODE trigger from reconciliation. **Loop prevention confirmed.** (Reference: AC-DA-09, Q-DA-07 resolved 2026-07-09.) | P1 | v1.1 |
| TC_032 | Verify HL Rate Limiter budget enforcement — weight exceeds remaining budget | 1. The bot is in `active` status. 2. HL Rate Limiter has insufficient budget for weight=2 request. | 1. Bot-scan → fan-out SQS → deep-audit Lambda call denied by Rate Limiter (`{allowed: false, retryAfterMs}`). | 1. Worker follows A1 path: Steps 2, 3, 4, 6, 7 skipped. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**. E-EXBOT-008 "Hyperliquid API unreachable" enqueued. **Deep-audit v1.1 does not use Redis Redlock — OQ-EXBOT-15 ordering not applicable.** (Reference: AC-DA-09, FR-EXBOT-091, Q-DA-06 resolved 2026-07-09.) | P1 | v1.1 |

### I.3. Non-functional (logic) verification — Operation: Periodic Deep Audit (deep-audit)

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority | Phase |
|---|---|---|---|---|---|---|
| TC_030 | Verify timestamp comparison for stuck detection uses precise arithmetic | 1. The bot is in `active` status. 2. `hedge_legs.stop_trigger_crossed_at` is set to exact boundary timestamps. | 1. Trigger deep-audit and verify stuck condition evaluation for boundaries (exactly 30 min, exactly 31 min, exactly 60s, exactly 61s). | 1. Timestamp arithmetic uses precise integer or BigDecimal comparison (not floating-point). Boundary cases evaluated correctly without rounding errors. (Reference: NFR-EXBOT-008, FR-EXBOT-033.) | P1 | v1.1 |
| TC_031 | Verify deep-audit does not initiate bot_safe_close — SAFE_MODE is the extent of its role | 1. The bot is in `active` status with a reconcile mismatch. | 1. Bot-scan → fan-out SQS → deep-audit Lambda triggers SAFE_MODE entry. | 1. Deep-audit triggers SAFE_MODE entry and enqueues admin notification. Worker does NOT initiate `bot_safe_close` — handled by SAFE_MODE recovery logic per FR-EXBOT-050 and FR-EXBOT-072. `close_operations` table not affected by deep-audit alone. (Reference: UC §1.3 Out of Scope, FR-EXBOT-050, FR-EXBOT-072.) | P1 | v1.1 |

### I.4. Phase A (v1) — Stub Verification

> **Phase:** Phase A (v1)
> **Note:** v1 deep-audit is a stub. `observeDeepAudit()` does NOT call HL API, does NOT verify hedge size, does NOT check stuck markers, does NOT fetch marginSummary. All functional tests are deferred to v1.1.

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority | Phase |
|---|---|---|---|---|---|---|
| TC_035 | Verify v1 deep-audit stub — observeDeepAudit() does not call HL API | 1. Bot-scan triggers and fans out SQS message. 2. v1 deep-audit Lambda is invoked. | 1. Trigger deep-audit Lambda via SQS in v1 environment. 2. Monitor HL API calls or logs. | 1. `observeDeepAudit()` in v1 is a stub — **no HL API calls are made**. No clearinghouseState, no marginSummary, no HL Rate Limiter calls. Worker completes without deep-audit logic. **Phase A deep-audit tests deferred to v1.1.** (Reference: AC-DA-10, BA confirmed 2026-07-09.) | P0 | Phase A (v1) |
| TC_036 | Verify v1 deep-audit queue is wired but safe_mode_tier column not yet in schema | 1. Deep-audit queue is deployed. 2. `safe_mode_tier` column does NOT exist in Aurora PostgreSQL schema. | 1. Bot-scan fans out SQS message to deep-audit queue. 2. Observe Lambda invocation and schema behavior. | 1. Queue receives SQS messages from bot-scan. Worker attempts to process but `safe_mode_tier` column missing — schema error or graceful skip. **No SAFE_MODE triggers in v1.** Periodic 6h cadence via `next_deep_audit_at` also not wired in v1. **v1.1 will wire both paths.** (Reference: AC-DA-10, BA confirmed 2026-07-09.) | P1 | Phase A (v1) |

---

## Coverage Breakdown

| Test Type | Phase A (v1) | v1.1 | Total |
|---|---|---|---|
| Functional | 0 | 15 | 15 |
| Integration | 0 | 14 | 14 |
| NFR (Logic) | 0 | 2 | 2 |
| Stub Verification | 2 | 0 | 2 |
| **Total** | **2** | **31** | **33** |

### Coverage by Acceptance Criteria

| AC # | Covered By | Phase |
|---|---|---|
| AC-DA-01 | TC_001, TC_002, TC_003, TC_004, TC_015 | v1.1 |
| AC-DA-02 | TC_005, TC_006, TC_007 | v1.1 |
| AC-DA-03 | TC_008, TC_009, TC_010, TC_011 | v1.1 |
| AC-DA-04 | TC_012, TC_013, TC_014 | v1.1 |
| AC-DA-05 | TC_016, TC_017, TC_018, TC_019 | v1.1 |
| AC-DA-06 | TC_020, TC_021, TC_022 | v1.1 |
| AC-DA-07 | TC_023, TC_024, TC_025, TC_026 | v1.1 |
| AC-DA-08 | TC_027, TC_028 | v1.1 |
| AC-DA-09 | TC_033, TC_034 | v1.1 |
| AC-DA-10 | TC_035, TC_036 | Phase A (v1) |

---

## Change Log

| Version | Date | Description |
|---|---|---|
| v1 | 2026-07-02 | Initial test cases for UC-EXBOT-deep-audit |
| v2 | 2026-07-06 | Updated after BA arc-migration (2026-07-04): Cloudflare → AWS naming. Added TC_032, TC_033 for new open questions. |
| v3 | 2026-07-09 | Updated after BA responses (2026-07-04): All open questions resolved (Q-DA-03, Q-DA-04, Q-DA-06, Q-DA-07). Added TC_034 (loop prevention), TC_035, TC_036 (v1 stub verification). Added Phase column. All functional tests deferred to v1.1. |

---

*Test Cases — UC-EXBOT-deep-audit v3 (2026-07-09)*
