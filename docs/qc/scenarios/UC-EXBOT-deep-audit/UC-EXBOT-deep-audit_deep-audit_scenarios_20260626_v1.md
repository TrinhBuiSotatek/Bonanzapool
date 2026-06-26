# Test Scenarios — UC-EXBOT-deep-audit Periodic Deep Audit

> Source: docs/qc/uc-read/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_deep-audit_audited_20260626_v2.md
> Generated: 2026-06-26
> Domain/Architecture: Cloudflare Workers + Hyperliquid, queue/cron/Durable-Object, D1

---

## UC-EXBOT-deep-audit — Periodic Deep Audit and Backstop SAFE_MODE Detection

### Scenario ID: TS_UC-EXBOT-deep-audit_001
**Scenario Title:** Happy path — deep-audit completes without detecting any risk condition
**UC Reference:** UC-EXBOT-deep-audit §3 Main Success Scenario
**Req-ID:** FR-EXBOT-016; AC-C1, AC-C10
**Test Type:** Functional
**Description:** Trigger a deep-audit cycle for an active bot whose HL short size matches D1 record, margin is healthy, and no stop markers are stuck; the system fetches clearinghouseState and marginSummary, updates margin_status, checks agent key expiry, records audit timestamp, and marks queue_idempotency as succeeded.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-deep-audit_002
**Scenario Title:** Reconcile mismatch triggers SAFE_MODE entry
**UC Reference:** UC-EXBOT-deep-audit §A3
**Req-ID:** FR-EXBOT-050; AC-C2
**Test Type:** Functional
**Description:** During deep-audit, the actual short size from HL differs from hedge_legs.last_known_hl_short_size; the system records the mismatch in D1, triggers SAFE_MODE, and enqueues an admin notification with the size delta and message E-EXBOT-011.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_003
**Scenario Title:** effective_leverage > 4.5 triggers SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.7
**Req-ID:** FR-EXBOT-050; US-010 AC-010-4; AC-C3
**Test Type:** Functional
**Description:** During deep-audit, effective_leverage from clearinghouseState exceeds 4.5; the system triggers SAFE_MODE and enqueues an admin alert with the exact effective_leverage value.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_004
**Scenario Title:** Liquidation price within 5% of hlMarkPrice triggers SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.8
**Req-ID:** FR-EXBOT-050; AC-C4
**Test Type:** Functional
**Description:** During deep-audit, the liquidation_price is within 5% of current hlMarkPrice; the system triggers SAFE_MODE.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_005
**Scenario Title:** stop_trigger_crossed_at stuck > 30 minutes triggers SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §3 Step 8; §A4
**Req-ID:** FR-EXBOT-033; BR-EXBOT-005; AC-C5
**Test Type:** Functional
**Description:** A bot has stop_trigger_crossed_at set and the elapsed time exceeds 30 minutes; the system triggers SAFE_MODE and enqueues an admin escalation notification with the timestamp and reason "stop_trigger_crossed_at stuck > 30min".
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_006
**Scenario Title:** stop_replacing_started_at stuck > 60 seconds triggers SAFE_MODE (secondary backstop)
**UC Reference:** UC-EXBOT-deep-audit §3 Step 9; §A4
**Req-ID:** FR-EXBOT-033; AC-C6
**Test Type:** Functional
**Description:** A bot has stop_replacing_started_at set and the elapsed time exceeds 60 seconds; the system triggers SAFE_MODE as the secondary backstop and enqueues an admin escalation with reason "stop_replacing_started_at stuck > 60s".
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_007
**Scenario Title:** HL unreachable triggers high-risk cadence switch
**UC Reference:** UC-EXBOT-deep-audit §A1
**Req-ID:** FR-EXBOT-016; SRS FR-EXBOT-091
**Test Type:** Functional
**Description:** HLRateLimitDO returns {allowed: false} or HL API returns 5xx; the system skips HL-dependent steps, switches cadence to 1 hour, and enqueues a "Hyperliquid API unreachable" notification.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-deep-audit_008
**Scenario Title:** Paused bot receives full audit at 6-hour cadence
**UC Reference:** UC-EXBOT-deep-audit §A2
**Req-ID:** FR-EXBOT-016; AC-C1
**Test Type:** Functional
**Description:** A bot with status='paused' fires its deep-audit cron; the system runs full audit including all 5 detection paths, does not skip any check, and maintains 6-hour cadence.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_009
**Scenario Title:** Queue idempotency prevents duplicate audit execution
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.3
**Req-ID:** FR-EXBOT-016; AC-C10
**Test Type:** Idempotency/Concurrency
**Description:** The queue redelivers the same message_id that already exists in queue_idempotency with state='succeeded'; the system returns immediately without reprocessing (UNIQUE constraint conflict).
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-deep-audit_010
**Scenario Title:** margin_usage < 0.55 updates margin_status to 'ok'
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.12
**Req-ID:** FR-EXBOT-060; AC-C11
**Test Type:** Data/State
**Description:** Deep-audit fetches marginSummary and computes marginUsage = 0.42 (< 0.55); the system updates hedge_legs.margin_status to 'ok' — no notification sent.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-deep-audit_011
**Scenario Title:** margin_usage ≥ 0.55 and < 0.75 triggers 'warning' status and investor notification
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.12, F1.13
**Req-ID:** FR-EXBOT-060; US-010 AC-010-1; AC-C11
**Test Type:** Data/State
**Description:** Deep-audit computes marginUsage = 0.62 (within warning band); the system updates margin_status to 'warning' and enqueues a notification to the investor: "Margin warning for your ExBot. Consider depositing additional margin to HL."
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-deep-audit_012
**Scenario Title:** margin_usage ≥ 0.75 (first reading) sets 'critical' but does NOT trigger SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §F.2; FR-EXBOT-060
**Req-ID:** FR-EXBOT-060; US-010 AC-010-2
**Test Type:** Data/State
**Description:** First critical reading (marginUsage = 0.78, ≥ 0.75); the system updates margin_status to 'critical' but does NOT trigger SAFE_MODE — SAFE_MODE requires two consecutive critical readings.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-deep-audit_013
**Scenario Title:** Second consecutive margin_usage ≥ 0.75 triggers SAFE_MODE
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.12; FR-EXBOT-050
**Req-ID:** FR-EXBOT-050; US-010 AC-010-2
**Test Type:** Data/State
**Description:** Previous deep-audit already set margin_status='critical'; current deep-audit reads marginUsage = 0.80 (second consecutive critical); the system triggers SAFE_MODE with investor and admin alerts: "Bot entered Safe Mode — Margin critical. Please deposit additional margin to HL."
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-deep-audit_014
**Scenario Title:** Agent key expiring within 7 days triggers expiry notification
**UC Reference:** UC-EXBOT-deep-audit §3 Step 14
**Req-ID:** FR-EXBOT-083; AC-C8
**Test Type:** Functional
**Description:** A bot's approved agent key expires in 5 days; deep-audit detects expires_at - now <= 7 days and enqueues the notification: "Your HL agent key expires in 5 days. Submit a new key to avoid bot interruption."
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-deep-audit_015
**Scenario Title:** Agent key expiry check skips pending status key
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.14
**Req-ID:** FR-EXBOT-083; AC-C9
**Test Type:** Functional
**Description:** A bot has a pending agent key with expires_at in 5 days; the system does NOT enqueue an expiry notification for the pending key — only keys with approval_status='approved' are checked.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-deep-audit_016
**Scenario Title:** Normal cadence transitions to high-risk (1 hour) after circuit breaker opens
**UC Reference:** UC-EXBOT-deep-audit §2; FR-EXBOT-016
**Req-ID:** FR-EXBOT-016; AC-C7
**Test Type:** Functional
**Description:** A bot's circuit_breakers.state transitions to 'open'; subsequent deep-audit recalculates next_deep_audit_at = now + 1 hour (high-risk cadence).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-deep-audit_017
**Scenario Title:** Normal cadence transitions to high-risk (1 hour) when margin_status becomes 'warning'
**UC Reference:** UC-EXBOT-deep-audit §2; FR-EXBOT-016
**Req-ID:** FR-EXBOT-016; AC-C7
**Test Type:** Functional
**Description:** Deep-audit updates margin_status to 'warning'; the system recalculates next_deep_audit_at = now + 1 hour.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-deep-audit_018
**Scenario Title:** Multiple SAFE_MODE conditions in same cycle — all trigger idempotently
**UC Reference:** UC-EXBOT-deep-audit §F.4 Integration point
**Req-ID:** FR-EXBOT-050; AC-C12
**Test Type:** Idempotency/Concurrency
**Description:** Both reconcile mismatch AND stop_trigger_crossed_at stuck are true in the same cycle; the system triggers SAFE_MODE for both but continues executing remaining checks (margin update, agent key check, timestamp) — SAFE_MODE is idempotent.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-deep-audit_019
**Scenario Title:** SAFE_MODE triggered but deep-audit continues when HL recovers
**UC Reference:** UC-EXBOT-deep-audit §F.4 Integration point
**Req-ID:** FR-EXBOT-050
**Test Type:** Functional
**Description:** Bot is in SAFE_MODE; deep-audit runs and HL becomes reachable again; the system completes the audit without re-triggering SAFE_MODE for already-resolved conditions.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-deep-audit_020
**Scenario Title:** Bot in safe_mode remains excluded from hedge-sync but deep-audit can run
**UC Reference:** UC-EXBOT-deep-audit §1.3 Ngoài phạm vi
**Req-ID:** FR-EXBOT-050
**Test Type:** Functional
**Description:** Bot status='safe_mode'; deep-audit worker processes this bot and completes successfully — SAFE_MODE does not block deep-audit, only blocks hedge-sync and LP operations.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-deep-audit_021
**Scenario Title:** HLRateLimitDO denies clearinghouseState but allows marginSummary
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.4, F1.11
**Req-ID:** FR-EXBOT-091
**Test Type:** Integration
**Description:** First HL call (clearinghouseState) is denied by rate limiter; second call (marginSummary) is allowed; audit is partial — marginSummary is fetched but clearinghouseState checks (reconcile, effective_leverage, liquidation_price) are skipped.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-deep-audit_022
**Scenario Title:** HLRateLimitDO denies marginSummary but allows clearinghouseState
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.4, F1.11
**Req-ID:** FR-EXBOT-091
**Test Type:** Integration
**Description:** First HL call (clearinghouseState) is allowed; second call (marginSummary) is denied; clearinghouseState checks run, margin_status update is skipped, audit is partial.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-deep-audit_023
**Scenario Title:** Bot scope includes only active and paused bots — error status excluded
**UC Reference:** UC-EXBOT-deep-audit §2 Preconditions
**Req-ID:** FR-EXBOT-016
**Test Type:** Functional
**Description:** Cron fires for bots with status IN ('active', 'paused'); bots with status='error' are not included in deep-audit scope.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-deep-audit_024
**Scenario Title:** HLRateLimitDO weight consumption — deep-audit declares weight=2 for clearinghouseState
**UC Reference:** UC-EXBOT-deep-audit §F.1 F1.4; FR-EXBOT-091
**Req-ID:** FR-EXBOT-091
**Test Type:** Integration
**Description:** Deep-audit worker declares weight=2 before fetching clearinghouseState; HLRateLimitDO validates against 800 weight/min budget and returns {allowed: true/false}.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-deep-audit_025
**Scenario Title:** stop_trigger_crossed_at write-once guard prevents false-positive stuck detection
**UC Reference:** UC-EXBOT-deep-audit §F.2; BR-EXBOT-005
**Req-ID:** BR-EXBOT-005
**Test Type:** Data/State
**Description:** stop_trigger_crossed_at is already set from a previous light-check pass; the timestamp is NOT overwritten by deep-audit (write-once guard); stuck detection uses the original timestamp correctly.
**Test Focus:** Boundary

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| SAFE_MODE auto-recovery flow | UC scope: only trigger, not recovery | Defer to SAFE_MODE recovery UC |
| bot_safe_close initiation from SAFE_MODE | UC scope: SAFE_MODE is a trigger condition only | Defer to uc-bot-safe-close |
| Margin thresholds 0.55/0.75 finalization | Pending OQ-EXBOT-06 (zen backtest) | Wait for zen to finalize thresholds |
| Performance/scale test (10k bots) | NFR: not functional test scope | Defer to performance team |
| Security audit of AES-256-GCM key encryption | NFR: beyond functional test scope | Defer to security team |
