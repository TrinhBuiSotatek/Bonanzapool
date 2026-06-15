---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-12
owner: "@hienduong"
linked_stories: [US-EXBOT-006]
changelog:
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-hedge-sync: Execute Delta-Only Hedge Adjustment

## 1. Actors
- **Primary:** ExBot System Operator (Hedge-Sync Worker)
- **System:** UserLockDO, Hyperliquid, D1, Reconcile Worker

## 2. Preconditions
- `hedge-sync` message received with `{botId, reasons: RebalanceReason[], stateVersion}`
- Bot `status='active'`, `lifecycle_state='active'`
- `circuit_breakers.state IN ('closed','half_open')`

## 3. Main Success Scenario
1. Worker inserts `message_id` into `queue_idempotency` (started); UNIQUE conflict → skip
2. Worker reads D1 `bots.state_version`; if mismatch with message `stateVersion` → discard (status='skipped')
3. Worker calls `UserLockDO.acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})`
4. Fetch actual HL position via `clearinghouseState` (weight=2)
5. Compute `delta = BigDecimal(targetShortEth).sub(actualShortEth)` (BigDecimal only, no float)
6. Submit delta-only adjustment via `adjustShortDelta(delta, cloid)` (increase or reduce-only)
7. Enqueue `reconcile` message: `{botId, attemptId, expectedAbsSize, hedgeLegId}`
8. Execute stop replacement via INV-STOP protocol (§19.5): `stop_replacing_started_at` set, protected cancel→place
9. Clear `stop_replacing_started_at` in finally block
10. `UserLockDO.release(holderToken, idempotencyKey, result)`
11. Reconcile Worker: fetch actual HL position, verify size = expected
12. Extract `entry_price`, `liquidation_price`, `effective_leverage` from reconcile
13. Recompute `stop_trigger_px` (BigDecimal); record new `stop_cloid`, `stop_price` in `hedge_legs`
14. Update `bot_runtime_state.last_known_hl_short_size = reconciled_size`
15. Insert `rebalance_attempts` row (status='success')
16. Update `queue_idempotency.state='succeeded'`

## 4. Alternate Flows
- **A1 (lock held):** Step 3 — `acquired=false`; re-queue with delay; no HL order
- **A2 (stateVersion mismatch):** Step 2 — discard; status='skipped'; no HL order
- **A3 (HL order rejection):** Step 6 — record rebalance_attempts (status='failed'); call `incrementCircuitBreaker`; enqueue notification
- **A4 (partial fill):** Step 11 — reconcile detects partial mismatch; enqueue `partial_repair` message
- **A5 (stop_replacing_started_at stuck > 60s detected by audit):** Enter SAFE_MODE (separate UC: deep-audit)

## 5. Postconditions
- `hedge_legs` updated: `stop_price`, `entry_price`, `effective_leverage`, `stop_replacing_started_at=NULL`
- `bot_runtime_state.last_known_hl_short_size` = reconciled value
- `rebalance_attempts` row inserted with final status
- `circuit_breakers.failure_count` incremented on failure (or reset on half_open success)

## 6. Business Rules
- BR-EXBOT-004 (delta-only invariant)

## 7. FR Trace
FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-036
