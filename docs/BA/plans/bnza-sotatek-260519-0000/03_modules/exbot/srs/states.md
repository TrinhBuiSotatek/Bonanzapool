---
type: srs-states
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-18
owner: "@hienduong"
changelog:
  - 2026-06-18 | /ba-do hld-decisions | remove cooldown/parked states from state machine; remove funds_parked from close_operations; update bot_safe_close terminal transition
  - 2026-06-12 | /ba-start srs | initial draft
---

# SRS States — BNZA-EXBOT Infrastructure

## Bot Lifecycle State Machine

States are stored in `bots.lifecycle_state` (fine-grained) and `bots.status` (coarse-grained).

```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> preflight : start request + one-bot check passes
    preflight --> lp_opening : all preflight checks pass
    preflight --> [*] : any preflight fails (no bot created)
    lp_opening --> lp_opened : VaultMinted event confirmed
    lp_opening --> error : LP mint fails
    lp_opened --> hedge_pre_open : LP confirmed
    hedge_pre_open --> hedge_post_confirmed : HL short IOC filled + reconcile
    hedge_pre_open --> safe_mode : HL order fails
    hedge_post_confirmed --> stop_placing : reconcile verified
    stop_placing --> stop_verified : stop placed + confirmed
    stop_placing --> safe_mode : stop placement fails
    stop_verified --> active : bot fully initialized
    active --> lp_rebalancing : range_out detected
    lp_rebalancing --> active : LP rebalance complete
    lp_rebalancing --> safe_mode : LP rebalance fails
    active --> hedge_stopped_cooldown : stop trigger fired
    hedge_stopped_cooldown --> active : re-hedge success after 4h cooldown
    hedge_stopped_cooldown --> safe_mode : re-hedge fails
    active --> lp_closing : close request (user_redeem or bot_safe_close)
    lp_closing --> closed : close complete (user_redeem path)
    lp_closing --> closed : close complete (bot_safe_close path — funds via RedemptionQueue)
    active --> safe_mode : SAFE_MODE triggers
    safe_mode --> active : auto-recovery (3 reconciles + margin ok)
    safe_mode --> closed : irrecoverable → bot_safe_close
    active --> error : critical bug / LP NFT anomaly
    error --> [*] : admin resolution required
```

## State Registry

| lifecycle_state | bots.status | Description | Light-Check | Hedge-Sync | Deep-Audit |
|----------------|------------|-------------|------------|-----------|-----------|
| `idle` | (pre-create) | Not started | — | — | — |
| `preflight` | (transitional) | Running preflight checks | skip | skip | skip |
| `lp_opening` | (transitional) | LP mint in progress | skip | skip | skip |
| `lp_opened` | (transitional) | LP minted, hedge not yet open | skip | skip | skip |
| `hedge_pre_open` | (transitional) | Opening HL short | skip | skip | skip |
| `hedge_post_confirmed` | (transitional) | Short confirmed, stop not placed | skip | skip | skip |
| `stop_placing` | (transitional) | Placing native stop | skip | skip | skip |
| `stop_verified` | (transitional) | Stop confirmed | skip | skip | skip |
| `active` | active | Normal monitoring | every 5 min | event-driven | every 6h |
| `hedge_stopped_cooldown` | active | Stop fired; hedge-sync suppressed 4h | run (no hedge-sync) | suppressed | every 6h |
| `lp_rebalancing` | active | LP range rebalance in progress | **skip** | skip | skip |
| `lp_closing` | closing | Close in progress | **skip** | skip | skip |
| `closed` | closed | Fully closed | skip | skip | skip |
| `safe_mode` | safe_mode | No mutations; monitor only | limited (no HL) | blocked | when HL recovers |
| `error` | error | Admin required | skip | skip | skip |
| (pre-pause value) | paused | Hedge maintained; no new mutations | skip | skip | every 6h |

**Note (HLD 2026-06-18):** `cooldown` and `parked` lifecycle states removed — park/redeploy feature dropped. After bot_safe_close, lifecycle transitions directly to `closed`.

## Circuit Breaker States (`circuit_breakers.state`)

```mermaid
stateDiagram-v2
    [*] --> closed
    closed --> open : 3 consecutive failures within 24h\nreset_at = now + 1h
    open --> half_open : reset_at reached
    half_open --> closed : probe hedge-sync succeeds
    half_open --> open : probe fails\nreset_at = now + 1h
```

| State | Hedge-Sync Allowed | Stop Monitoring |
|-------|-------------------|----------------|
| `closed` | Yes | Yes |
| `open` | No (suppressed) | Yes — ALWAYS |
| `half_open` | One probe only (atomic claim) | Yes — ALWAYS |

## Margin Status (`hedge_legs.margin_status`)

| State | marginUsage | Hedge Behavior | Alert |
|-------|------------|---------------|-------|
| `ok` | < 0.55 | Normal | None |
| `warning` | 0.55–0.75 | Size-increase disabled | Investor (UI banner) |
| `critical` | ≥ 0.75 (×2 consecutive) | Enter SAFE_MODE | Investor + Admin |
| `safe_mode` | (via SAFE_MODE entry) | All mutations blocked | Investor + Admin |

## close_operations States

| State | user_redeem | bot_safe_close |
|-------|------------|---------------|
| `requested` | ✓ | ✓ |
| `lp_closed` | ✓ (LP liquidated on-chain) | ✓ (after hedge close) |
| `funds_returned` | ✓ (LP-portion USDC to user in same tx) | — |
| `hedge_close_pending` | ✓ (after funds_returned) | ✓ (first step after requested) |
| `hedge_closed` | ✓ | ✓ |
| `redemption_queued` | — | ✓ (RedemptionQueue.createRequest enqueued) |
| `residual_hl_liability` | if hedge close fails | if hedge close fails |
| `done` | ✓ | ✓ |
