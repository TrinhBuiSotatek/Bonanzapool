---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-14
owner: "@hienduong"
linked_stories: [US-EXBOT-005, US-EXBOT-006, US-EXBOT-007, US-EXBOT-008]
changelog:
  - 2026-07-14 | manual | P2 fix: add FR-EXBOT-011 to §7 FR Trace — referenced in step 5 but missing from trace
  - 2026-07-13 | manual | v3-I-01 fix: add FR-EXBOT-012 and FR-EXBOT-040 to §7 FR Trace
  - 2026-07-13 | manual | I-10 fix: replace cleanup gap note with EventBridge cron 1h purge per FR-EXBOT-011 AC
  - 2026-07-04 | arc-migration | replace Cloudflare primitives with AWS equivalents (D1→Aurora PostgreSQL, MarketDataDO→Pool Slot0 Cache (ElastiCache Redis), HlMarkDO→HL Mark Price Cache (ElastiCache Redis), Cron Worker→EventBridge Scheduler)
  - 2026-07-02 | /ba-do | I-09: step 2 LIMIT 500 overflow behavior. I-10: step 5 expires_at TTL + cleanup gap. I-11: diagram → F-01 reference. I-12: step 7 MarketDataDO stale fail-fast + A5 added
  - 2026-07-02 | /ba-do | I-01: hlMarkPrice source HlMarkDO + fallback + staleness 120s. I-02: range_boundary_near price-based formula. I-03: drift_threshold lpValueUsd formula. I-04: funding_alert 7d APR formula. I-05: step 10 rewrite — range_out routes to hedge-sync like other triggers; remove phantom lp_rebalancing queue. I-07: step 12 rewrite — both status+lifecycle_state set atomically before partial_repair enqueue. I-08: step 4 clarify next_light_check_at updated for all eligible bots including skipped
  - 2026-06-20 | /ba-do | QC audit fixes: step 10 split, step 12 overrun check, A4 routing fix, hedge_stopped_cooldown note, A5 stale template removed, OQ-017 cross-ref, stale template removed
  - 2026-06-18 | /ba-do | add US-007 (LP rebalance trigger) and US-008 (circuit breaker) to linked_stories
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-light-check: Execute Periodic Light-Check

## Trigger

EventBridge Scheduler fires on 1-minute schedule → enqueues `bot-scan` message → Scan Worker dequeues and dispatches per-bot `light-check` messages.

---

## 1. Actors
- **Primary:** ExBot System Operator (EventBridge Scheduler → Scan Worker → Light-Check Worker)
- **System:** Aurora PostgreSQL (state_db_shard), Pool Slot0 Cache (ElastiCache Redis), HL Mark Price Cache (ElastiCache Redis)

## 2. Preconditions
- Bot `status='active'` and `next_light_check_at <= now`
- `lifecycle_state NOT IN ('lp_rebalancing','lp_closing')`
- `status != 'paused'`
- Note: bots with `lifecycle_state='hedge_stopped_cooldown'` are NOT skipped — light-check runs normally; hedge-sync is suppressed only for those bots.

## 3. Main Success Scenario
1. EventBridge Scheduler (1 min) calls `chunkSendBatch` to `bot-scan` queue with shard windows
2. Scan Worker queries Aurora PostgreSQL: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now ORDER BY next_light_check_at LIMIT 500`. Bots beyond 500 are processed in the next EventBridge Scheduler tick (1 min later), oldest first — by design, jitter ±45s prevents overflow in steady state
3. Scan Worker sends per-bot messages to `light-check` queue via `chunkSendBatch`
4. Scan Worker updates `next_light_check_at = now + 5min + jitter(±45s)` for **every eligible bot** (including bots in `lp_rebalancing`, `lp_closing`) before enqueuing — bots that Light-Check Worker later skips due to `lifecycle_state` check are still rescheduled correctly and will not be flooded on recovery
5. Light-Check Worker inserts `message_id` into `queue_idempotency` (state='started', expires_at=now+1min); UNIQUE conflict → skip. Note: `expires_at` is always set (default TTL=1min); an EventBridge cron job (every 1 hour) purges rows WHERE expires_at < now to prevent unbounded table growth (per FR-EXBOT-011 AC).
6. Light-Check Worker reads from Aurora PostgreSQL: `bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs` (stop_price, margin_status, circuit_state)
7. Light-Check Worker reads from the Pool Slot0 Cache (ElastiCache Redis): `sqrtPriceX96`, `currentTick` (zero HL API calls). If snapshot stale (> 5 min) or the cache is unreachable → throw immediately, skip tick for this bot entirely (no trigger evaluation)
8. Computes `lpEthAmount` via TickMath + LiquidityAmounts (local, no RPC)
9. Evaluates `RebalanceReason[]` using only Aurora PostgreSQL + Pool Slot0 Cache state. `range_boundary_near` uses price-based USD: fires when `min(distToLower, distToUpper) / halfRange <= rangeBoundaryFraction` (default 0.9). `drift_threshold` uses `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`; threshold = `max($25, lpValueUsd × 3%)`. `funding_alert` fires when 7d APR < -15%: primary source `fundingApr7dPct` from `funding_rolling_metrics`; fallback `fundingRate × 8760`
10. Strategy engine evaluates all fired triggers → `decision.reason[]`. If `decision.action = REBALANCE` AND `circuit_state != 'open'`: enqueue **1 hedge-sync** with `{botId, reasons: decision.reason[], stateVersion}`. `range_out` is included in `reasons[]` like any other trigger — light-check does NOT set `lifecycle_state='lp_rebalancing'` or enqueue a separate `lp_rebalancing` queue. LP rebalance lifecycle transition is handled by hedge-sync handler downstream
11. Read `markPrice` from the HL Mark Price Cache (ElastiCache Redis) `markPriceUsd` (primary); if the cache `updatedAt > 120s` → stale: audit `hl_mark_price_stale`, widen near-stop band 2%→4%, freeze routine hedge-sync after stop check; fallback to `bot_runtime_state.eth_price_usd` (last-known from prior light-check). If `markPrice >= stop_price`: set `stop_trigger_crossed_at` (guarded); enqueue `price-near-stop-audit`
12. Check `stop_replacing_started_at`: if set and overrun > 60s → Light-Check Worker atomically sets **both** `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` in a single UPDATE, then enqueues `partial_repair(reason='stop_replacing_overrun')`. Status change happens **before** the partial_repair message is in the queue
13. Update `queue_idempotency.state='succeeded'`

## 4. Alternate Flows
- **A1 (Pool Slot0 Cache stale/unreachable):** Step 7 — snapshot age > 5 min or the cache is unreachable → skip tick entirely; no trigger evaluation; next light-check runs normally at `next_light_check_at`
- **A2 (circuit open):** Step 10 — suppress hedge-sync; continue to step 11 (stop monitoring always runs)
- **A3 (circuit half_open):** Step 10 — atomically claim `half_open_probe_used`; enqueue one probe hedge-sync
- **A4 (stop trigger crossed_at already set):** Step 11 — do NOT overwrite; still enqueue price-near-stop-audit
- **A5 (range_boundary_near):** `range_boundary_near` is a `RebalanceReason[]` → routed to hedge-sync (not price-near-stop-audit). `price-near-stop-audit` is only for `stop_trigger_crossed`.

## 5. Postconditions
- One of: no action needed, hedge-sync enqueued, or price-near-stop-audit enqueued
- `next_light_check_at` updated in Aurora PostgreSQL (batch write per shard)
- HL API call count: 0 (invariant)

## 6. Business Rules
- BR-EXBOT-003 (HL weight = 0), BR-EXBOT-005 (stop_trigger_crossed_at write-once)

---

## Diagram

> See **F-01: Queue Fan-Out (EventBridge Scheduler → Scan → Light-Check → Hedge-Sync)** in [`srs/flows.md`](../srs/flows.md) — full sequence from EventBridge Scheduler → Scan Worker → Light-Check Worker fan-out → hedge-sync enqueue.

## 7. FR Trace
FR-EXBOT-011, FR-EXBOT-012, FR-EXBOT-013, FR-EXBOT-014, FR-EXBOT-015, FR-EXBOT-016, FR-EXBOT-023, FR-EXBOT-032, FR-EXBOT-033, FR-EXBOT-040
