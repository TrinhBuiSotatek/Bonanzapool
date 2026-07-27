---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-25
owner: "@hienduong"
linked_stories: [US-EXBOT-006, US-EXBOT-008]
changelog:
  - 2026-07-25 | /ba-impact | OQ-13 zen override: delta=0 → skip HL order, proceed to stop replacement (step 5+A6); OQ-14/15: lock→weight→call ordering note (step 3)
  - 2026-07-20 | manual | OQ-EXBOT-013 closed: fix Step 5 note + A6 — delta=0 returns no_op_dust immediately, no stop replacement or reconcile (confirmed from develop branch rebalance.ts + handler-impl.ts)
  - 2026-07-13 | manual | Q12 fix: replace generic Mermaid placeholder with reference to flows.md F-02
  - 2026-07-13 | manual | Q-N1 fix: add FR-EXBOT-092 to §7 FR Trace (missing after arc-migration 2026-07-03)
  - 2026-07-04 | arc-migration | replace UserLockDO with User Lock (Redis Redlock via ElastiCache), D1 with Aurora PostgreSQL per FR-EXBOT-092
  - 2026-06-20 | /ba-do | QC audit fixes: trigger updated, step 5 delta=0 note, A5 primary/secondary fix, A6 added, BR consecutive failures def, stale template removed
  - 2026-06-18 | /ba-do | add US-008 to linked_stories; fix phantom ref in A5 to point at uc-deep-audit.md
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-hedge-sync: Execute Delta-Only Hedge Adjustment

## Trigger

hedge-sync Worker dequeues a message from the hedge-sync queue. Message is enqueued by light-check (primary, FR-EXBOT-033, ≤5 min cadence) or deep-audit (secondary backstop). Message payload: `{botId, reasons: RebalanceReason[], stateVersion}`.

---

## 1. Actors
- **Primary:** ExBot System Operator (Hedge-Sync Worker)
- **System:** User Lock (Redis Redlock via ElastiCache), Hyperliquid, Aurora PostgreSQL, Reconcile Worker

## 2. Preconditions
- `hedge-sync` message received with `{botId, reasons: RebalanceReason[], stateVersion}`
- Bot `status='active'`, `lifecycle_state='active'`
- `circuit_breakers.state IN ('closed','half_open')`

## 3. Main Success Scenario
1. Worker inserts `message_id` into `queue_idempotency` (started); UNIQUE conflict → skip
2. Worker reads Aurora PostgreSQL `bots.state_version`; if mismatch with message `stateVersion` → discard (status='skipped'); Worker rechecks `circuit_breakers.state` at execution time; if `open` → discard (status='skipped'); no HL order submitted
3. Worker calls `User Lock.acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})`. All decision inputs (including `marginSummary`) must be fetched inside this lock critical section (OQ-EXBOT-14). Rate-limit weight must be consumed after lock acquisition — ordering: lock → weight → call; on rate-limit hit, release lock and retry with backoff (OQ-EXBOT-15)
4. Fetch actual HL position via `clearinghouseState` (weight=2)
5. Compute `delta = BigDecimal(targetShortEth).sub(actualShortEth)` (BigDecimal only, no float)
   - If delta=0: skip HL order submission, proceed directly to stop replacement (step 8). delta=0 means position size is correct — stop level may still have moved with price and must be refreshed (OQ-EXBOT-13 zen confirmed). No reconcile needed; entry_price/liq_price unchanged.
6. Submit delta-only adjustment via `adjustShortDelta(delta, cloid)` (increase or reduce-only)
7. Enqueue `reconcile` message: `{botId, attemptId, expectedAbsSize, hedgeLegId}`
8. Execute stop replacement via INV-STOP protocol (§19.5): `stop_replacing_started_at` set, protected cancel→place
9. Clear `stop_replacing_started_at` in finally block
10. `User Lock.release(holderToken, idempotencyKey, result)`
11. Reconcile Worker: fetch actual HL position, verify size = expected
12. Extract `entry_price`, `liquidation_price`, `effective_leverage` from reconcile
13. Recompute `stop_trigger_px` (BigDecimal); record new `stop_cloid`, `stop_price` in `hedge_legs`
14. Update `bot_runtime_state.last_known_hl_short_size = reconciled_size`
15. Insert `rebalance_attempts` row (status='success')
16. Update `queue_idempotency.state='succeeded'`

## 4. Alternate Flows
- **A1 (lock held):** Step 3 — `acquired=false`; re-queue with delay; no HL order
- **A2 (stateVersion mismatch):** Step 2 — discard; status='skipped'; reason = original RebalanceReason[] from message payload; no HL order
- **A3 (HL order rejection):** Step 6 — record rebalance_attempts (status='failed'); call `incrementCircuitBreaker`; enqueue notification
- **A4 (partial fill):** Step 11 — reconcile detects partial mismatch; enqueue `partial_repair` message; `incrementCircuitBreaker` is NOT called (partial fill is not a failure — repair path handles remaining delta)
- **A5 (stop_replacing_started_at stuck > 60s):** Primary detection by light-check (FR-EXBOT-033, ≤5 min). deep-audit is secondary backstop only. Enter SAFE_MODE.
- **A6 (delta=0, no HL order):** Step 5 — skip HL order, proceed to stop replacement (step 8). Stop freshness is independent of position-size delta (OQ-EXBOT-13 zen confirmed). No reconcile, entry_price/liq_price unchanged. reason = original RebalanceReason[] from message payload.

## 5. Postconditions
- `hedge_legs` updated: `stop_price`, `entry_price`, `effective_leverage`, `stop_replacing_started_at=NULL`
- `bot_runtime_state.last_known_hl_short_size` = reconciled value
- `rebalance_attempts` row inserted with final status
- `circuit_breakers.failure_count` incremented on failure (or reset on half_open success)

## 6. Business Rules
- BR-EXBOT-004 (delta-only invariant)
- "Consecutive failures" definition: rolling 24h window, no intervening success. Source: FR-EXBOT-040 AC.

---

## Diagram

> See **F-02: Hedge-Sync Execution (Delta-Only)** in [`srs/flows.md`](../srs/flows.md) — full sequence from hedge-sync queue → Hedge-Sync Worker → Redis Redlock → Hyperliquid → reconcile → Aurora PostgreSQL update.

## 7. FR Trace
FR-EXBOT-020, FR-EXBOT-021, FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-035, FR-EXBOT-036, FR-EXBOT-092
