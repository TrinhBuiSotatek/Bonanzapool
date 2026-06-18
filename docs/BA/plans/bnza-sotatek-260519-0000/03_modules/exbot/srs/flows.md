---
type: srs-flows
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-12
owner: "@hienduong"
changelog:
  - 2026-06-12 | /ba-start srs | initial draft
---

# SRS Flows — BNZA-EXBOT Infrastructure

## F-01: Queue Fan-Out (Cron → Scan → Light-Check → Hedge-Sync)

```mermaid
sequenceDiagram
    participant Cron as "Cron Worker (1 min)"
    participant ScanQ as "bot-scan queue"
    participant ScanW as "Scan Worker"
    participant LCQ as "light-check queue"
    participant LCW as "Light-Check Worker"
    participant HSQ as "hedge-sync queue"
    participant PSAQ as "price-near-stop-audit queue"
    participant D1 as "D1"
    participant MDO as "MarketDataDO"

    Cron->>ScanQ: sendBatch via chunkSendBatch
    ScanQ->>ScanW: deliver batch
    ScanW->>D1: SELECT bots WHERE status = active
    ScanW->>LCQ: chunkSendBatch per bot
    ScanW->>D1: batch UPDATE next_light_check_at

    LCQ->>LCW: deliver message
    LCW->>D1: read bot_runtime_state
    LCW->>MDO: read sqrtPriceX96, currentTick
    LCW->>LCW: compute lpEthAmount (zero HL calls)
    LCW->>LCW: evaluate RebalanceReason list

    alt rebalance needed
        LCW->>HSQ: enqueue hedge-sync
    else stop trigger detected
        LCW->>D1: SET stop_trigger_crossed_at
        LCW->>PSAQ: enqueue price-near-stop-audit
    else circuit open
        Note over LCW: suppress hedge-sync
    end
```

## F-02: Hedge-Sync Execution (Delta-Only)

```mermaid
sequenceDiagram
    participant HSQ as hedge-sync queue
    participant HSW as Hedge-Sync Worker
    participant UDO as UserLockDO
    participant HL as Hyperliquid API
    participant D1 as D1
    participant RQ as reconcile queue

    HSQ->>HSW: deliver {botId, reasons, stateVersion}
    HSW->>D1: check stateVersion match (abort if mismatch → status=skipped)
    HSW->>UDO: acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})
    alt lock held by another worker
        UDO-->>HSW: acquired=false
        HSW->>HSQ: re-queue with delay
    else lock acquired
        UDO-->>HSW: acquired=true
        HSW->>HL: getPosition (clearinghouseState, weight=2)
        HSW->>HSW: compute delta = targetShortEth - actualShortEth (BigDecimal)
        HSW->>HL: adjustShortDelta(delta) via cloid (deterministic)
        HSW->>HL: (if stop resize needed) replaceStop via INV-STOP protocol
        HSW->>RQ: enqueue {botId, attemptId, expectedAbsSize, hedgeLegId}
        HSW->>UDO: release(holderToken)
    end

    RQ->>HSW: reconcile worker fetches actual HL position
    HSW->>D1: update hedge_legs (stop_price, entry_price, liq_price, effective_leverage)
    HSW->>D1: update bot_runtime_state.last_known_hl_short_size
    HSW->>D1: insert rebalance_attempts (status=success/failed/partial)
```

## F-03: Bot Initialization Flow

```mermaid
sequenceDiagram
    participant INV as "Investor (POOL UI)"
    participant OP as Operator Facade
    participant EXW as ExBot Worker
    participant HL as Hyperliquid
    participant VAULT as BnzaExVault
    participant D1 as "D1 (control_db + shard)"

    INV->>OP: POST /api/exbot/start
    OP->>EXW: forward via service binding
    EXW->>D1: one-bot policy check (bot_registry)
    EXW->>HL: getMarginSummary (preflight margin check)
    EXW->>D1: check hl_agent_keys (approved, not expired)
    EXW->>EXW: LP mint simulation
    EXW->>D1: create bot record (lifecycle_state=preflight)

    EXW->>VAULT: vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)
    VAULT-->>EXW: emit VaultMinted(user, botId, tokenId, liquidity)
    EXW->>D1: update positions (tokenId, tickLower, tickUpper, wethIndex, lifecycle_state=lp_opened)

    EXW->>HL: openShortIoc(targetSize, cloid)
    EXW->>HL: reconcilePosition (verify actual size)
    EXW->>D1: update hedge_legs (entry_price, liq_price, effective_leverage, lifecycle_state=hedge_post_confirmed)

    EXW->>EXW: computeStopTriggerPx (BigDecimal, safetyFactor=0.70)
    EXW->>HL: placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)
    EXW->>D1: update hedge_legs (stop_cloid, stop_price, lifecycle_state=stop_verified → active)

    EXW-->>OP: {status: active, botId}
    OP-->>INV: Bot started successfully
```

## F-04: Close Flow — user_redeem (LP-First)

```mermaid
sequenceDiagram
    participant INV as Investor
    participant VAULT as "BnzaExVault (on-chain)"
    participant EVWATCHER as Redeem Event Watcher
    participant UREQ as user_redeem queue
    participant UREW as Redeem Worker
    participant HL as Hyperliquid
    participant D1 as D1

    INV->>VAULT: redeem(tokenId) [on-chain tx]
    VAULT-->>INV: LP liquidated, LP-portion USDC returned in same tx
    VAULT->>EVWATCHER: emit RedemptionEvent(botId, redeemTxHash, userAddress)

    EVWATCHER->>UREQ: enqueue {botId, redeemTxHash, userAddress} [highest priority]
    UREQ->>UREW: deliver (SLA: 5 min from detection)

    UREW->>D1: create close_operations (kind=user_redeem, state=lp_closed→funds_returned)
    UREW->>HL: closeShortReduceOnlyIoc (full close, cloid)
    UREW->>HL: cancelStop (via §19.5 replaceStopProtected with size=0)
    UREW->>HL: reconcilePosition (verify size=0)
    UREW->>D1: update close_operations (state=hedge_closed)
    UREW->>VAULT: send HL-portion USDC to user (RedemptionQueue ledger)
    UREW->>D1: update close_operations (state=done), lifecycle_state=closed

    alt hedge close fails
        UREW->>D1: close_operations.state=residual_hl_liability
        UREW->>D1: enqueue admin notification (outstanding liability amount)
        Note over UREW: LP-portion repayment NOT reverted
    end
```

## F-05: bot_safe_close + Automatic Re-Entry

```mermaid
sequenceDiagram
    participant TRIGGER as "Trigger (circuit/margin/admin)"
    participant CLOSEW as Close Worker
    participant HL as Hyperliquid
    participant VAULT as BnzaExVault
    participant D1 as D1
    participant REENTRY as "Re-Entry Worker (60min interval)"

    TRIGGER->>CLOSEW: initiate bot_safe_close
    CLOSEW->>D1: close_operations (kind=bot_safe_close, state=requested)
    CLOSEW->>HL: closeShort (full close)
    CLOSEW->>HL: cancelStop
    CLOSEW->>D1: close_operations state=hedge_closed
    CLOSEW->>VAULT: vaultClose(tokenId, dest=UNINVESTED)
    VAULT-->>CLOSEW: emit FundsParked(user, botId, amount)
    CLOSEW->>D1: close_operations state=funds_parked → done
    CLOSEW->>D1: lifecycle_state=cooldown (60 min)
    CLOSEW->>D1: enqueue notification (cooldown entry)

    loop Every 60 min during cooldown
        REENTRY->>D1: read funding_daily_metrics (7d APR)
        REENTRY->>VAULT: uninvestedBalanceOf(user, botId) [on-chain read, canonical]
        alt funding APR > -15% AND preflight passes AND balance > 0
            REENTRY->>VAULT: redeploy(botId) → FundsRedeployed event
            REENTRY->>D1: update uninvested_balances = 0
            REENTRY->>D1: run open flow (lifecycle_state=preflight → ... → active)
        else conditions not met
            REENTRY->>D1: keep lifecycle_state=cooldown
        end
    end

    alt 3rd bot_safe_close within 7 days
        CLOSEW->>D1: lifecycle_state=parked (24h interval)
        CLOSEW->>D1: admin escalation notification
    end
```
