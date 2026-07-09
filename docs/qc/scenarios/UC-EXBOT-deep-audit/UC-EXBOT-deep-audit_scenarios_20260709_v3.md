# Test Scenarios — UC-EXBOT-deep-audit Periodic Deep Audit and Backstop SAFE_MODE Detection

> **Source:** `docs/qc/uc-read/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_audited_20260709_v3.md` (v3)
> **Generated:** 2026-07-06
> **Updated:** 2026-07-09 (v3 — after BA responses 2026-07-04)
> **Domain/Architecture:** AWS Lambda EventBridge Scheduler-triggered worker — no UI. Deep-Audit Worker reads Aurora PostgreSQL, calls Hyperliquid API via HL Rate Limiter (ElastiCache Redis) with weight=2 (v1.1), updates Aurora PostgreSQL, and enqueues notifications. **v1 deep-audit is a stub — Phase A tests deferred to v1.1.**

---

## UC-EXBOT-deep-audit — Periodic Deep Audit and Backstop SAFE_MODE Detection

### Scenario ID: TS_EXBOT-deep-audit_001
**Scenario Title:** Deep-audit happy path — audit completes without issues (v1.1)
**UC Reference:** UC-EXBOT-deep-audit §3 Main Success Scenario
**Req-ID:** AC-DA-01; FR-EXBOT-016; FR-EXBOT-091
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** EventBridge Scheduler triggers bot-scan (`rate: 1 minute`) → bot-scan queries `bots WHERE status='active'` → fan-out per-bot SQS message → deep-audit Lambda processes 1 `botId` per invocation. Worker reads bot state from Aurora PostgreSQL, calls HL clearinghouseState via HL Rate Limiter (ElastiCache Redis) (weight=2), verifies short size matches last_known_hl_short_size, checks stuck markers (both NULL or not aged), fetches marginSummary, updates hedge_legs.margin_status, sets last_audit_at=now, sets next_deep_audit_at=now+6h, and inserts queue_idempotency state='succeeded'.
**Test Focus:** Happy path
**Note:** v1 deep-audit is a stub (`observeDeepAudit()` does not call HL). Phase A tests deferred to v1.1.

---

### Scenario ID: TS_EXBOT-deep-audit_002
**Scenario Title:** Reconciliation mismatch detected — bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §3 Step 3 + A3
**Req-ID:** AC-DA-02; FR-EXBOT-016; FR-EXBOT-050; E-EXBOT-011
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker calls HL clearinghouseState via HL Rate Limiter (ElastiCache Redis) and finds actual short size ≠ hedge_legs.last_known_hl_short_size. Worker **always updates** `last_known_hl_short_size = actual HL size` and `last_hl_reconcile_at = now` (bất kể match hay mismatch) — trước khi trigger SAFE_MODE. Worker records the mismatch in Aurora PostgreSQL with the size delta (actual − expected), triggers bot transition to safe_mode, and enqueues admin notification with message E-EXBOT-011: "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." **This behavior confirmed by BA 2026-07-09 — ngăn potential loop in subsequent audits.**
**Test Focus:** Error/Exception — reconciliation failure leading to SAFE_MODE
**Resolved:** Q-DA-07 (2026-07-09): Worker always syncs `last_known_hl_short_size` before triggering SAFE_MODE.

---

### Scenario ID: TS_EXBOT-deep-audit_003
**Scenario Title:** stop_trigger_crossed_at stuck > 30 minutes — bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §3 Step 4 + A4
**Req-ID:** AC-DA-03; FR-EXBOT-033; FR-EXBOT-050; E-EXBOT-019
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_trigger_crossed_at set to a timestamp older than 30 minutes from now. Deep-audit worker evaluates: stop_trigger_crossed_at IS NOT NULL AND (now − stop_trigger_crossed_at) > 30 minutes — condition is true. Worker triggers bot transition to safe_mode and enqueues admin escalation notification with message E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required."
**Test Focus:** Error/Exception — stuck marker triggers SAFE_MODE

---

### Scenario ID: TS_EXBOT-deep-audit_004
**Scenario Title:** stop_trigger_crossed_at NOT stuck — age exactly 30 minutes (boundary)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 4
**Req-ID:** FR-EXBOT-033; BR-EXBOT-005
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_trigger_crossed_at set to exactly 30 minutes ago. Deep-audit worker evaluates: (now − stop_trigger_crossed_at) > 30 minutes. Since the elapsed time equals exactly 30 minutes (not greater than), the stuck condition is false. Worker does NOT trigger SAFE_MODE; audit proceeds to next check.
**Test Focus:** Boundary value — threshold at exactly 30 minutes (not stuck)

---

### Scenario ID: TS_EXBOT-deep-audit_005
**Scenario Title:** stop_trigger_crossed_at stuck at exactly 31 minutes (boundary)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 4
**Req-ID:** FR-EXBOT-033; BR-EXBOT-005
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_trigger_crossed_at set to exactly 31 minutes ago. Deep-audit worker evaluates: (now − stop_trigger_crossed_at) > 30 minutes. Since 31 minutes > 30 minutes, the stuck condition is true. Worker triggers SAFE_MODE and enqueues E-EXBOT-019 notification.
**Test Focus:** Boundary value — threshold at exactly 31 minutes (stuck triggers)

---

### Scenario ID: TS_EXBOT-deep-audit_006
**Scenario Title:** stop_trigger_crossed_at NULL — no stuck detection
**UC Reference:** UC-EXBOT-deep-audit §3 Step 4
**Req-ID:** BR-EXBOT-005
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_trigger_crossed_at = NULL. Deep-audit worker evaluates: stop_trigger_crossed_at IS NOT NULL AND (now − stop_trigger_crossed_at) > 30 minutes. The first condition fails (NULL), so the entire condition is false. Worker proceeds to Step 5 without triggering SAFE_MODE.
**Test Focus:** Alternative flow — no marker set

---

### Scenario ID: TS_EXBOT-deep-audit_007
**Scenario Title:** stop_replacing_started_at stuck > 60 seconds — bot enters SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §3 Step 5 + A4
**Req-ID:** AC-DA-04; FR-EXBOT-033; FR-EXBOT-050; E-EXBOT-020
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_replacing_started_at set to a timestamp older than 60 seconds from now. Deep-audit worker evaluates: stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60 seconds — condition is true. Worker triggers bot transition to safe_mode and enqueues admin escalation notification with message E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required."
**Test Focus:** Error/Exception — stuck marker triggers SAFE_MODE

---

### Scenario ID: TS_EXBOT-deep-audit_008
**Scenario Title:** stop_replacing_started_at NOT stuck — age exactly 60 seconds (boundary)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 5
**Req-ID:** FR-EXBOT-033
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_replacing_started_at set to exactly 60 seconds ago. Deep-audit worker evaluates: (now − stop_replacing_started_at) > 60 seconds. Since the elapsed time equals exactly 60 seconds (not greater than), the stuck condition is false. Worker does NOT trigger SAFE_MODE; audit proceeds to Step 6.
**Test Focus:** Boundary value — threshold at exactly 60 seconds (not stuck)

---

### Scenario ID: TS_EXBOT-deep-audit_009
**Scenario Title:** stop_replacing_started_at stuck at exactly 61 seconds (boundary)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 5
**Req-ID:** FR-EXBOT-033
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_replacing_started_at set to exactly 61 seconds ago. Deep-audit worker evaluates: (now − stop_replacing_started_at) > 60 seconds. Since 61 seconds > 60 seconds, the stuck condition is true. Worker triggers SAFE_MODE and enqueues E-EXBOT-020 notification.
**Test Focus:** Boundary value — threshold at exactly 61 seconds (stuck triggers)

---

### Scenario ID: TS_EXBOT-deep-audit_010
**Scenario Title:** stop_replacing_started_at NULL — no stuck detection
**UC Reference:** UC-EXBOT-deep-audit §3 Step 5
**Req-ID:** FR-EXBOT-033
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.stop_replacing_started_at = NULL. Deep-audit worker evaluates: stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60 seconds. The first condition fails (NULL), so the entire condition is false. Worker proceeds to Step 6 without triggering SAFE_MODE.
**Test Focus:** Alternative flow — no marker set

---

### Scenario ID: TS_EXBOT-deep-audit_011
**Scenario Title:** HL API unreachable — graceful degradation with cadence switch to 1 hour (v1.1)
**UC Reference:** UC-EXBOT-deep-audit §3 A1
**Req-ID:** AC-DA-05; FR-EXBOT-091; E-EXBOT-008
**Test Type:** Integration
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** HL Rate Limiter (ElastiCache Redis) returns {allowed: false} OR HL API returns 5xx when deep-audit worker attempts to call clearinghouseState. Worker skips Steps 2, 3, 4, 6, 7 (HL-dependent steps), **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**, enqueues notification "Hyperliquid API unreachable" with message E-EXBOT-008, and records retry-pending state in Aurora PostgreSQL. Bot remains in its current state.
**Test Focus:** Error/Exception — external dependency failure
**Note:** Cadence switching via Lambda write to `bots.next_deep_audit_at` confirmed by BA 2026-07-09.

---

### Scenario ID: TS_EXBOT-deep-audit_012
**Scenario Title:** HL API partially reachable — marginSummary fails after clearinghouseState succeeds (v1.1)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 2, 6
**Req-ID:** FR-EXBOT-091; FR-EXBOT-016
**Test Type:** Integration
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker successfully calls HL clearinghouseState via HL Rate Limiter (ElastiCache Redis) (Step 2) and completes reconciliation check (Step 3) — **always syncs `last_known_hl_short_size`** before any decision. However, when calling HL marginSummary (Step 6), the API returns 5xx or times out. Worker continues to complete Steps 7 and 8 (update last_audit_at, insert idempotency row). The margin_status field is NOT updated from HL; it retains its previous value.
**Test Focus:** Alternative flow — partial HL failure after reconciliation

---

### Scenario ID: TS_EXBOT-deep-audit_013
**Scenario Title:** Paused bot is fully audited — all detection paths execute including stuck markers
**UC Reference:** UC-EXBOT-deep-audit §3 A2; states.md row 71
**Req-ID:** AC-DA-06; FR-EXBOT-005; FR-EXBOT-033
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has status='paused'. EventBridge Scheduler triggers bot-scan → fan-out per-bot SQS → deep-audit Lambda reads the bot's state. Worker executes all detection paths (Steps 3–7) normally: clearinghouseState reconciliation, stop_trigger_crossed_at stuck check (>30min), stop_replacing_started_at stuck check (>60s), marginSummary fetch, and last_audit_at update. **Pause does NOT skip deep-audit scheduling or any detection path.**
**Test Focus:** Alternative flow — paused bot inclusion

---

### Scenario ID: TS_EXBOT-deep-audit_014
**Scenario Title:** Paused bot with stuck stop_trigger_crossed_at — transitions paused → safe_mode
**UC Reference:** UC-EXBOT-deep-audit §3 A2; states.md row 71
**Req-ID:** FR-EXBOT-005; FR-EXBOT-033; FR-EXBOT-050
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has status='paused' and hedge_legs.stop_trigger_crossed_at is set and aged > 30 minutes. Deep-audit runs for this paused bot, detects the stuck marker, and triggers bot transition from paused status to safe_mode. The bot exits the paused state despite being paused — pause does not exempt the bot from SAFE_MODE entry via stuck marker detection. Admin notification E-EXBOT-019 is enqueued.
**Test Focus:** State transition — paused to safe_mode via stuck marker

---

### Scenario ID: TS_EXBOT-deep-audit_015
**Scenario Title:** High-risk cadence switching — circuit breaker open triggers 1-hour schedule
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions; FR-EXBOT-016
**Req-ID:** AC-DA-07; FR-EXBOT-040
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has circuit_breakers.state='open'. Deep-audit worker detects this condition. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`** (not EventBridge Scheduler self-switch). Bot-scan queries `WHERE status='active' AND next_deep_audit_at <= now` every 1 minute and fans out SQS messages for due bots. Subsequent deep-audit runs for this bot occur every 1 hour until circuit_breakers.state returns to 'closed'.
**Test Focus:** Alternative flow — cadence switching based on circuit breaker state
**Resolved:** Q-DA-04 (2026-07-09): Cadence switching via Lambda write to `bots.next_deep_audit_at`; EventBridge does not self-switch.

---

### Scenario ID: TS_EXBOT-deep-audit_016
**Scenario Title:** High-risk cadence switching — margin_status='warning' triggers 1-hour schedule
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions; FR-EXBOT-016
**Req-ID:** AC-DA-07; FR-EXBOT-060
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.margin_status='warning'. Deep-audit worker detects this condition. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**. Bot-scan picks up due bots every minute. All subsequent deep-audit runs for this bot occur at 1-hour cadence. Note: margin_status update in Step 6 may change the status — if it transitions from warning to ok, cadence may revert. Margin threshold values (0.55/0.75) are subject to Phase 0 backtest finalization (OQ-EXBOT-06).
**Test Focus:** Alternative flow — cadence switching based on margin status
**Open:** OQ-EXBOT-06 — margin threshold values pending Phase 0 backtest

---

### Scenario ID: TS_EXBOT-deep-audit_017
**Scenario Title:** High-risk cadence switching — margin_status='critical' triggers 1-hour schedule
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions; FR-EXBOT-016
**Req-ID:** AC-DA-07; FR-EXBOT-060
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has hedge_legs.margin_status='critical'. Deep-audit worker detects this condition. **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**. Deep-audit processes the bot at high-risk cadence going forward. Note: two consecutive critical margin status values trigger SAFE_MODE per FR-EXBOT-050, but deep-audit only updates margin_status — the consecutive-count logic is handled elsewhere.
**Test Focus:** Alternative flow — cadence switching based on critical margin status

---

### Scenario ID: TS_EXBOT-deep-audit_018
**Scenario Title:** Normal cadence persists — all conditions are nominal (circuit closed, margin ok)
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions
**Req-ID:** FR-EXBOT-016
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has circuit_breakers.state='closed' and hedge_legs.margin_status='ok'. Deep-audit worker verifies both conditions. **Lambda updates `bots.next_deep_audit_at` to `now + 6h`**. Bot-scan picks up due bots every minute. No cadence switching occurs. Deep-audit processes the bot at normal cadence.
**Test Focus:** Happy path — normal cadence maintained

---

### Scenario ID: TS_EXBOT-deep-audit_019
**Scenario Title:** Idempotency — duplicate queue message is rejected by UNIQUE constraint
**UC Reference:** UC-EXBOT-deep-audit §3 Step 8; FR-EXBOT-011
**Req-ID:** AC-DA-08; FR-EXBOT-011
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** The queue delivery system redelivers a message with the same message_id that was already processed successfully. Deep-audit worker attempts to insert queue_idempotency row with state='started'. The UNIQUE constraint on message_id conflicts with the existing row. Worker returns immediately without re-processing. The first delivery's queue_idempotency row with state='succeeded' remains intact.
**Test Focus:** Idempotency/Concurrency — duplicate message delivery

---

### Scenario ID: TS_EXBOT-deep-audit_020
**Scenario Title:** Idempotency — first message processing inserts 'started' then transitions to 'succeeded'
**UC Reference:** UC-EXBOT-deep-audit §3 Step 8; FR-EXBOT-011
**Req-ID:** FR-EXBOT-011
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker receives a new message with a unique message_id. Worker inserts queue_idempotency row with state='started' at the beginning of processing. As the audit completes successfully, worker updates the same row to state='succeeded'. The transition from started → succeeded is recorded in Aurora PostgreSQL for audit trail.
**Test Focus:** Happy path — idempotency state progression

---

### Scenario ID: TS_EXBOT-deep-audit_021
**Scenario Title:** HL Rate Limiter (ElastiCache Redis) integrated — deep-audit calls HL with weight=2 (v1.1)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 2; FR-EXBOT-091
**Req-ID:** AC-DA-09; FR-EXBOT-091; BR-EXBOT-003
**Test Type:** Integration
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker calls HL clearinghouseState via HL Rate Limiter (ElastiCache Redis) with declared weight=2. The rate limiter accepts the weight call since it is within the 800 weight/min budget. Worker proceeds with the HL API call. BR-EXBOT-003 (HL weight=0) does NOT apply to deep-audit — this is the exception confirmed in UC §6 BR. **Deep-audit v1.1 does not use Redis Redlock (no hedge mutation), so OQ-EXBOT-15 ordering question does not apply.**
**Test Focus:** Integration — HL rate limit compliance
**Resolved:** Q-DA-06 (2026-07-09): OQ-EXBOT-15 not applicable to deep-audit v1.1.

---

### Scenario ID: TS_EXBOT-deep-audit_022
**Scenario Title:** Deep-audit skips bots with status='closed' — not in scope
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions; states.md row 68-69
**Req-ID:** FR-EXBOT-016; states.md rows 68-69
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** EventBridge Scheduler triggers bot-scan. Bot-scan queries `bots WHERE status IN ('active', 'paused')` from Aurora PostgreSQL. Bots with status='closed', 'error', 'idle', 'lp_rebalancing', 'lp_closing', or other non-active/paused statuses are NOT included in the query (per states.md registry). The worker processes zero bots in these categories and completes successfully.
**Test Focus:** Happy path — bot scope filtering

---

### Scenario ID: TS_EXBOT-deep-audit_023
**Scenario Title:** Deep-audit processes multiple bots sequentially — hedge_legs.margin_status updated individually
**UC Reference:** UC-EXBOT-deep-audit §3 Step 6
**Req-ID:** FR-EXBOT-016; FR-EXBOT-060
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** EventBridge Scheduler triggers bot-scan → fan-out per-bot SQS → deep-audit Lambda processes bots sequentially (1 bot per Lambda invocation). For each bot, Step 6 fetches HL marginSummary via HL Rate Limiter (ElastiCache Redis) and updates that bot's hedge_legs.margin_status independently. Worker correctly maps each marginSummary response to the correct bot's hedge_legs record. No cross-bot contamination of margin_status values.
**Test Focus:** Alternative flow — batch processing across multiple bots
**Note:** Architecture: bot-scan layer handles shard iteration; deep-audit Lambda processes 1 botId per invocation.

---

### Scenario ID: TS_EXBOT-deep-audit_024
**Scenario Title:** Both stuck markers set simultaneously — stop_trigger_crossed_at and stop_replacing_started_at both stuck
**UC Reference:** UC-EXBOT-deep-audit §3 Steps 4–5 + A4
**Req-ID:** FR-EXBOT-033; FR-EXBOT-050
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** A bot has both hedge_legs.stop_trigger_crossed_at (aged >30min) and hedge_legs.stop_replacing_started_at (aged >60s) set simultaneously. Deep-audit worker evaluates Step 4 first — stop_trigger_crossed_at stuck condition is true. Worker triggers SAFE_MODE entry and enqueues E-EXBOT-019. Step 5 is not reached because SAFE_MODE entry has already occurred. Only E-EXBOT-019 notification is sent (first-triggered condition wins).
**Test Focus:** Alternative flow — multiple stuck conditions at once

---

### Scenario ID: TS_EXBOT-deep-audit_025
**Scenario Title:** SAFE_MODE entry triggered — bot_safe_close is NOT initiated by deep-audit
**UC Reference:** UC-EXBOT-deep-audit §1.3 Out of Scope
**Req-ID:** FR-EXBOT-050; FR-EXBOT-072
**Test Type:** End-to-End
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker triggers SAFE_MODE entry via mismatch, stuck marker, or other condition. Bot transitions to safe_mode. The deep-audit worker does NOT initiate bot_safe_close — this is handled by the SAFE_MODE recovery logic in FR-EXBOT-050 and FR-EXBOT-072. Deep-audit's postcondition is limited to SAFE_MODE entry and notification enqueue.
**Test Focus:** End-to-End — SAFE_MODE entry role boundary

---

### Scenario ID: TS_EXBOT-deep-audit_026
**Scenario Title:** Deep-audit reads from correct Aurora PostgreSQL shard — bot state and hedge_legs joined correctly (v1.1)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 1; erd.md
**Req-ID:** FR-EXBOT-016; NFR-EXBOT-012
**Test Type:** Integration
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Bot-scan queries `bots WHERE status='active' AND next_deep_audit_at <= now` → fan-out per-bot SQS → deep-audit Lambda reads bot state for 1 botId. Worker correctly joins hedge_legs to bots on bot_id and reads circuit_breakers.state from the circuit_breakers table. All fields are present and valid before proceeding to Step 2. **Shard iteration is handled by bot-scan layer, not deep-audit Lambda.**
**Test Focus:** Integration — Aurora PostgreSQL read correctness
**Resolved:** Q-DA-03 (2026-07-09): Architecture confirmed — bot-scan handles shard iteration; deep-audit Lambda processes 1 botId per invocation.

---

### Scenario ID: TS_EXBOT-deep-audit_027
**Scenario Title:** No bot exists with status IN ('active','paused') — deep-audit completes with zero processed
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions
**Req-ID:** FR-EXBOT-016
**Test Type:** Functional
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** EventBridge Scheduler triggers bot-scan but no bot in Aurora PostgreSQL has status='active' or status='paused', or no bots have `next_deep_audit_at <= now`. Bot-scan queries and receives an empty result set. No SQS messages are fan-out. Worker completes the cron cycle without error — no HL calls are made, no Aurora PostgreSQL writes occur, and no notifications are enqueued. The queue_idempotency row is still inserted to mark the audit cycle occurred.
**Test Focus:** Alternative flow — empty bot set

---

### Scenario ID: TS_EXBOT-deep-audit_028
**Scenario Title:** Timestamp comparison precision — uses BigDecimal/time comparison, not float
**UC Reference:** UC-EXBOT-deep-audit §3 Steps 4–5; NFR-EXBOT-008
**Req-ID:** NFR-EXBOT-008; FR-EXBOT-033
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker evaluates stuck marker conditions using precise timestamp arithmetic: (now − stop_trigger_crossed_at) and (now − stop_replacing_started_at). The comparison uses BigDecimal or integer second arithmetic to avoid floating-point precision errors. Boundary cases (exactly 30 min / 60 sec) are evaluated correctly without rounding errors that could cause a false positive or false negative.
**Test Focus:** Boundary — timestamp precision

---

### Scenario ID: TS_EXBOT-deep-audit_029
**Scenario Title:** HL Rate Limiter budget enforcement — weight exceeds remaining budget (v1.1)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 2 + A1; FR-EXBOT-091
**Req-ID:** FR-EXBOT-091; AC-DA-09
**Test Type:** Integration
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker attempts to call HL clearinghouseState via HL Rate Limiter (ElastiCache Redis) with weight=2, but the remaining budget in the current 60-second window is less than 2. Rate Limiter returns {allowed: false, retryAfterMs}. Worker follows A1 path: skips Steps 2, 3, 4, 6, 7, **Lambda updates `bots.next_deep_audit_at` to `now + 1h`**, and enqueues notification E-EXBOT-008 "Hyperliquid API unreachable". **Deep-audit v1.1 does not use Redis Redlock, so OQ-EXBOT-15 ordering is not applicable.**
**Test Focus:** Integration — rate limit exceeded
**Resolved:** Q-DA-06 (2026-07-09): OQ-EXBOT-15 not applicable to deep-audit v1.1.

---

### Scenario ID: TS_EXBOT-deep-audit_030
**Scenario Title:** Reconciliation mismatch — last_known_hl_short_size always synced before SAFE_MODE entry
**UC Reference:** UC-EXBOT-deep-audit §3 Step 3 + A3; FR-EXBOT-016
**Req-ID:** FR-EXBOT-016; FR-EXBOT-050; AC-DA-09
**Test Type:** Data/State
**Test Phase:** v1.1 (deferred from Phase A)
**Description:** Deep-audit worker detects reconciliation mismatch: actual short size on HL ≠ hedge_legs.last_known_hl_short_size. **Worker ALWAYS updates `last_known_hl_short_size = actual HL size` and `last_hl_reconcile_at = now` BEFORE triggering SAFE_MODE** — bất kể match hay mismatch. Worker records mismatch in Aurora PostgreSQL and triggers SAFE_MODE entry. Subsequent deep-audit runs will NOT re-detect the same mismatch because `last_known_hl_short_size` is already synced to actual HL size. **This prevents potential loop.**
**Test Focus:** Data consistency — mismatch state sync prevents loop
**Resolved:** Q-DA-07 (2026-07-09): Worker always syncs `last_known_hl_short_size` before triggering SAFE_MODE.

---

### Scenario ID: TS_EXBOT-deep-audit_031 (NEW)
**Scenario Title:** v1 deep-audit stub — observeDeepAudit() does not call HL API
**UC Reference:** UC-EXBOT-deep-audit §1.1; BA response 2026-07-09
**Req-ID:** AC-DA-10; FR-EXBOT-016
**Test Type:** Functional
**Test Phase:** Phase A (v1)
**Description:** Deep-audit Lambda is invoked via SQS message (from bot-scan fan-out). However, `observeDeepAudit()` in v1 is a stub — it does NOT call HL API, does NOT verify hedge size, does NOT check stuck markers, does NOT fetch marginSummary. Worker completes without any HL Rate Limiter calls or Aurora PostgreSQL writes for deep-audit logic. **Phase A tests for deep-audit behavior are deferred to v1.1.**
**Test Focus:** Stub verification — v1 implementation
**Note:** This scenario verifies v1 stub behavior. All deep-audit functional tests are deferred to v1.1.

---

### Scenario ID: TS_EXBOT-deep-audit_032 (NEW)
**Scenario Title:** v1 deep-audit queue wired but safe_mode_tier column not yet in schema
**UC Reference:** UC-EXBOT-deep-audit §1.1; BA response 2026-07-09
**Req-ID:** FR-EXBOT-016
**Test Type:** Integration
**Test Phase:** Phase A (v1)
**Description:** Deep-audit queue is deployed and receives SQS messages from bot-scan, but `safe_mode_tier` column does not exist in Aurora PostgreSQL schema. Worker attempts to process message but encounters schema error. No SAFE_MODE triggers occur. **Periodic 6h cadence via `next_deep_audit_at` is also not wired in v1.** This is expected v1 state — v1.1 will wire both paths.
**Test Focus:** Integration — v1 schema gap
**Note:** This scenario documents v1 known gap. v1.1 will have `safe_mode_tier` column and wired cadence.

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Multi-shard deep-audit (Phase B — 4 shards) | **Resolved (2026-07-09):** Shard iteration handled by bot-scan layer, not deep-audit Lambda. Deep-audit Lambda processes 1 botId per invocation. | Re-design Phase B scenarios when bot-scan multi-shard strategy confirmed (not deep-audit concern) |
| Cadence switching mechanism — where 1h is recorded | **Resolved (2026-07-09):** Lambda writes `bots.next_deep_audit_at`; EventBridge does not self-switch. v1.1 implementation. | Test Lambda write to `bots.next_deep_audit_at` in v1.1 |
| SAFE_MODE auto-recovery from deep-audit entry | FR-EXBOT-050 recovery section is out of scope for deep-audit UC. Deep-audit only triggers entry. | Separate UC or test suite for recovery logic |
| Bot start/lifecycle initialization | Belongs to UC-EXBOT-bot-start | Not in scope |
| INV-STOP stop placement/replacement logic | Belongs to UC-EXBOT-hedge-sync; deep-audit only detects stuck markers | Not in scope |
| Light-check primary detection for stop_replacing_started_at | Primary detection belongs to UC-EXBOT-light-check; deep-audit is secondary backstop | Separate test suite for light-check |
| Performance/throughput testing (10k bots) | NFR-EXBOT-001 applies to light-check only; no throughput requirement for deep-audit | Not in scope |
| HL Rate Limiter + User Lock ordering (OQ-EXBOT-15) | **Resolved (2026-07-09):** Deep-audit v1.1 does not use Redis Redlock (no hedge mutation). OQ-EXBOT-15 only affects hedge-sync. | Tech Lead decision for hedge-sync (separate UC) |
| Security beyond functional auth | Out of scope for functional test scenario design | Defer to security specialist |
| Load/stress testing | Out of scope | Defer to performance specialist |
| HL Rate Limiter integration in Phase A | **Resolved (2026-07-09):** v1 deep-audit is stub, does not call HL API. Phase A tests deferred to v1.1. | Test HL Rate Limiter integration in v1.1 |

---

## Coverage Breakdown

| Test Type | Count | Phase |
|---|---|---|
| Functional | 18 scenarios | v1.1 |
| Integration | 4 scenarios | v1.1 (3) + Phase A (1) |
| Data/State | 6 scenarios | v1.1 |
| End-to-End | 1 scenario | v1.1 |
| Stub Verification | 2 scenarios | Phase A (v1) |
| **Total** | **31 scenarios** | — |

### Coverage by Acceptance Criteria

| AC # | Covered By | Notes |
|---|---|---|
| AC-DA-01 | TS_EXBOT-deep-audit_001 | Happy path (v1.1) |
| AC-DA-02 | TS_EXBOT-deep-audit_002 | Mismatch → SAFE_MODE (v1.1) |
| AC-DA-03 | TS_EXBOT-deep-audit_003 | stop_trigger_crossed_at stuck >30min → SAFE_MODE (v1.1) |
| AC-DA-04 | TS_EXBOT-deep-audit_007 | stop_replacing_started_at stuck >60s → SAFE_MODE (v1.1) |
| AC-DA-05 | TS_EXBOT-deep-audit_011 | HL unreachable → graceful degradation (v1.1) |
| AC-DA-06 | TS_EXBOT-deep-audit_013, TS_EXBOT-deep-audit_014 | Paused bot fully audited (v1.1) |
| AC-DA-07 | TS_EXBOT-deep-audit_015, TS_EXBOT-deep-audit_016, TS_EXBOT-deep-audit_017, TS_EXBOT-deep-audit_018 | High-risk cadence switching (v1.1) |
| AC-DA-08 | TS_EXBOT-deep-audit_019, TS_EXBOT-deep-audit_020 | Idempotency prevents duplicate (v1.1) |
| AC-DA-09 | TS_EXBOT-deep-audit_002, TS_EXBOT-deep-audit_021, TS_EXBOT-deep-audit_029, TS_EXBOT-deep-audit_030 | `last_known_hl_short_size` always synced (v1.1) |
| AC-DA-10 | TS_EXBOT-deep-audit_031, TS_EXBOT-deep-audit_032 | Phase A deferred (v1 stub) |

### Notes
- **Phase A vs v1.1 split:** Phase A (v1) tests verify stub behavior only (TS_031, TS_032). All functional deep-audit tests are deferred to v1.1.
- **Resolved open questions:** Q-DA-03 (shard iteration), Q-DA-04 (cadence switching), Q-DA-06 (OQ-EXBOT-15 N/A), Q-DA-07 (last_known_hl_short_size always synced) — all confirmed by BA 2026-07-09.
- **Out-of-scope items flagged:** Multi-shard Phase B (bot-scan concern), cadence-switch wiring (v1.1), SAFE_MODE auto-recovery, light-check primary detection, INV-STOP internals, HL Rate Limiter + User Lock ordering (hedge-sync decision), performance/load testing.

---

## Change Log

| Version | Date | Description |
|---|---|---|
| v1 | 2026-07-02 | Initial scenario for UC-EXBOT-deep-audit |
| v2 | 2026-07-06 | Updated after BA arc-migration (2026-07-04): Cloudflare → AWS naming. Added TS_029, TS_030 for new open questions. |
| v3 | 2026-07-09 | Updated after BA responses (2026-07-04): All open questions resolved (Q-DA-03, Q-DA-04, Q-DA-06, Q-DA-07). Added TS_031, TS_032 for v1 stub verification. All functional tests deferred to v1.1. Updated architecture notes throughout. |

---

*Test Scenarios — UC-EXBOT-deep-audit v3 (2026-07-09)*
