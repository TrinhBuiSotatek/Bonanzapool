---
type: srs-flows
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-14
owner: "@hienduong"
changelog:
  - 2026-07-14 | manual | P2 fix: F-01 step 11 — normalize "freeze routine hedge-sync" to "suppress routine hedge-sync (this tick only)" for consistency with circuit open branch
  - 2026-07-14 | manual | I-N3 fix: F-04 add hedge_close_pending transition after lock acquired, before closeShortReduceOnlyIoc call
  - 2026-07-14 | manual | I-03 fix: F-04 add User Lock (Redis Redlock) participant; add lock acquire/release block around HL operations; fix close_operations notation (requested → lp_closed → funds_returned); add SLA breach note on re-queue
  - 2026-07-13 | manual | v3-I-07 fix: F-01 add HL Mark Price Cache participant + stop monitoring sub-flow (step 11); fix alt block — add circuit half_open branch, remove stop trigger from rebalance alt; add overrun check block (step 12)
  - 2026-07-07 | manual | split F-03 into F-03a (auto key-provision on deposit) and F-03b (user-triggered bot start via POST /api/exbot/start)
  - 2026-07-04 | arc-migration | replace Cloudflare primitives with AWS equivalents across F-01, F-02, F-03, F-04, F-05
  - 2026-06-29 | manual | rewrite F-03: deposit-triggered KMS key-provision + Signing Lambda flow; remove manual Investor/Operator path
  - 2026-06-20 | /ba-do | QC audit fixes: F-05 rewritten — remove park/re-entry/cooldown, reflect direct close flow
  - 2026-06-12 | /ba-start srs | initial draft
---

# SRS Flows — BNZA-EXBOT Infrastructure

## F-01: Queue Fan-Out (Cron → Scan → Light-Check → Hedge-Sync)

```mermaid
sequenceDiagram
    participant Cron as "EventBridge Scheduler (1 min)"
    participant ScanQ as "bot-scan queue"
    participant ScanW as "Scan Worker"
    participant LCQ as "light-check queue"
    participant LCW as "Light-Check Worker"
    participant HSQ as "hedge-sync queue"
    participant PSAQ as "price-near-stop-audit queue"
    participant PRQ as "partial-repair queue"
    participant D1 as "Aurora PostgreSQL"
    participant MDO as "Pool Slot0 Cache (ElastiCache Redis)"
    participant HLC as "HL Mark Price Cache (ElastiCache Redis)"

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

    alt decision.action = REBALANCE AND circuit != open
        LCW->>HSQ: enqueue hedge-sync {botId, reasons, stateVersion}
    else circuit half_open
        LCW->>D1: atomically claim half_open_probe_used
        LCW->>HSQ: enqueue 1 probe hedge-sync
    else circuit open
        Note over LCW: suppress hedge-sync; continue to stop monitoring
    end

    Note over LCW,HLC: Stop monitoring — always runs regardless of rebalance decision (step 11)
    LCW->>HLC: read markPriceUsd
    alt HL Mark Price Cache stale > 120s
        Note over LCW: widen stop band 2%→4%; suppress routine hedge-sync (this tick only); fallback to bot_runtime_state.eth_price_usd
    else markPrice >= stop_price
        LCW->>D1: SET stop_trigger_crossed_at (write-once guard — skip if already set)
        LCW->>PSAQ: enqueue price-near-stop-audit
    end

    opt stop_replacing_started_at IS SET AND overrun > 60s
        Note over LCW: step 12 — overrun detected
        LCW->>D1: atomic UPDATE bots SET status='safe_mode', lifecycle_state='safe_mode'
        LCW->>PRQ: enqueue partial_repair(reason='stop_replacing_overrun')
    end
```

## F-02: Hedge-Sync Execution (Delta-Only)

```mermaid
sequenceDiagram
    participant HSQ as hedge-sync queue
    participant HSW as Hedge-Sync Worker
    participant UDO as "Redis Redlock"
    participant HL as Hyperliquid API
    participant D1 as "Aurora PostgreSQL"
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

## F-03a: Auto Key-Provision on Deposit

> **Triggered automatically** when Chain Indexer (Fargate) detects an on-chain deposit. No user action required. Bot start does NOT happen here — this flow only provisions the HL account so it is ready when the user later calls Start Bot.

```mermaid
sequenceDiagram
    participant CHAIN as "Chain Indexer (Fargate)"
    participant KPQ as "key-provision queue"
    participant KP as "Key-Provision Worker"
    participant KMS as "AWS KMS"
    participant HL as "Hyperliquid"
    participant DB as "Aurora PostgreSQL (control_db + shard)"

    CHAIN->>CHAIN: on-chain deposit event detected
    CHAIN->>KPQ: enqueue key-provision job {userId, depositAmount, txHash}
    KPQ->>KP: deliver message

    KP->>KMS: GenerateKeyPair (master key)
    KMS-->>KP: hl_user_address (public only — private key stays in KMS HSM)
    KP->>KMS: GenerateKeyPair (agent key)
    KMS-->>KP: agent_address (public only — private key stays in KMS HSM)

    KP->>HL: approveAgent(hl_user_address, agent_address)
    HL-->>KP: agent registered as delegate

    KP->>DB: INSERT hl_agent_keys (key_status='active', agent_address, hl_user_address)
    Note over KP,DB: Flow ends here — bot start is user-initiated (see F-03b)
```

## F-03b: User-Triggered Bot Start

> **Triggered by user** calling `POST /api/exbot/start` via POOL UI. Key-provision must already be complete (`key_status='active'`) from F-03a. Preflight now includes vault balance check as first guard.

```mermaid
sequenceDiagram
    participant INV as "USDC Investor (POOL UI)"
    participant EXW as "ExBot Lambda"
    participant DB as "Aurora PostgreSQL (control_db + shard)"
    participant HL as "Hyperliquid"
    participant VAULT as "BnzaExVault"
    participant SL as "Signing Lambda"
    participant KMS as "AWS KMS"

    INV->>EXW: POST /api/exbot/start
    EXW->>DB: one-bot policy check (bot_registry)
    EXW->>VAULT: check vault balance > 0 for user (block with E-EXBOT-025 if no deposit)
    EXW->>HL: getMarginSummary (preflight margin check)
    EXW->>DB: key_status='active' check — block with E-EXBOT-017 if not active
    EXW->>EXW: builder fee check
    EXW->>EXW: LP mint simulation
    EXW->>DB: create bot record (lifecycle_state=preflight)

    EXW->>VAULT: vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)
    VAULT-->>EXW: emit VaultMinted(user, botId, tokenId, liquidity)
    EXW->>DB: update positions (tokenId, tickLower, tickUpper, wethIndex, lifecycle_state=lp_opened)

    EXW->>SL: openShortIoc(targetSize, cloid, hl_user_address)
    SL->>KMS: kms:Sign (order payload via agent key)
    KMS-->>SL: signature
    SL->>HL: signed short IOC order
    EXW->>HL: reconcilePosition (verify actual size)
    EXW->>DB: update hedge_legs (entry_price, liq_price, effective_leverage, lifecycle_state=hedge_post_confirmed)

    EXW->>EXW: computeStopTriggerPx (BigDecimal, safetyFactor=0.70)
    EXW->>SL: placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)
    SL->>KMS: kms:Sign (stop order payload via agent key)
    KMS-->>SL: signature
    SL->>HL: signed stop order placed
    EXW->>DB: update hedge_legs (stop_cloid, stop_price, lifecycle_state=stop_verified → active)
    EXW-->>INV: bot started successfully
```

## F-04: Close Flow — user_redeem (LP-First)

```mermaid
sequenceDiagram
    participant INV as Investor
    participant VAULT as "BnzaExVault (on-chain)"
    participant EVWATCHER as Redeem Event Watcher
    participant UREQ as user_redeem queue
    participant UREW as Redeem Worker
    participant UDO as "User Lock (Redis Redlock)"
    participant HL as Hyperliquid
    participant D1 as "Aurora PostgreSQL"

    INV->>VAULT: redeem(tokenId) [on-chain tx]
    VAULT-->>INV: LP liquidated, LP-portion USDC returned in same tx
    VAULT->>EVWATCHER: emit RedemptionEvent(botId, redeemTxHash, userAddress)

    EVWATCHER->>UREQ: enqueue {botId, redeemTxHash, userAddress} [highest priority]
    UREQ->>UREW: deliver (SLA: 5 min from detection)

    UREW->>D1: insert close_operations (kind=user_redeem, state=requested)
    UREW->>D1: update close_operations state=lp_closed
    UREW->>D1: update close_operations state=funds_returned

    UREW->>UDO: acquire(holderToken, ttl=90s, idempotencyKey=user-redeem:{botId}:{redeemTxHash})
    alt lock held by hedge-sync worker
        UDO-->>UREW: acquired=false
        UREW->>UREQ: re-queue with delay
        Note over UREW: SLA clock still running — delay > 5 min total → A1 SLA breach alert
    else lock acquired
        UDO-->>UREW: acquired=true
        UREW->>D1: update close_operations state=hedge_close_pending
        UREW->>HL: closeShortReduceOnlyIoc (full close, cloid)
        UREW->>HL: cancelStop (via §19.5 replaceStopProtected with size=0)
        UREW->>HL: reconcilePosition (verify size=0)
        UREW->>D1: update close_operations (state=hedge_closed)
        UREW->>UDO: release(holderToken)
    end

    UREW->>VAULT: send HL-portion USDC to user (RedemptionQueue ledger)
    UREW->>D1: update close_operations (state=done), lifecycle_state=closed

    alt hedge close fails
        UREW->>UDO: release(holderToken)
        UREW->>D1: close_operations.state=residual_hl_liability
        UREW->>D1: enqueue admin notification (outstanding liability amount)
        Note over UREW: LP-portion repayment NOT reverted
    end
```

## F-05: bot_safe_close (Direct Close via RedemptionQueue)

```mermaid
sequenceDiagram
    actor Investor
    participant OperatorFacade
    participant ExBotLambda
    participant RedemptionQueue
    participant Operator

    Investor->>OperatorFacade: POST /api/exbot/close
    OperatorFacade->>ExBotLambda: forward via API Gateway + HMAC Lambda Authorizer
    ExBotLambda->>ExBotLambda: executeStrategy(RedeemStrategyV1)
    ExBotLambda->>RedemptionQueue: createRequest(botId, userId, amount)
    RedemptionQueue-->>ExBotLambda: requestId
    ExBotLambda->>ExBotLambda: lifecycle_state = 'closing'
    ExBotLambda-->>Investor: "Close request queued. Funds will be returned after FIFO processing."
    Operator->>RedemptionQueue: fulfillRequest(requestId) [FIFO]
    RedemptionQueue-->>Investor: funds transferred
    ExBotLambda->>ExBotLambda: lifecycle_state = 'closed'
```
