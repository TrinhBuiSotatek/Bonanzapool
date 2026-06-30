# EXBOT on AWS — Architecture

## 1. Overview

EXBOT is a managed delta-neutral LP bot: it runs concentrated liquidity on Uniswap V3 and a short ETH perp hedge on Hyperliquid (HL). Today the runtime lives on Cloudflare (Workers + D1 + Durable Objects + Queues + cron). This document describes the AWS-native target.

**Design principles**
- Pure logic ports verbatim — `exbot-strategy`, HL adapter, `shared-position-math` have no Cloudflare dependency. Only the binding layer is rebuilt.
- **1 ECS-Fargate watcher + multi-Lambda.** Lambda hosts the event/API work; a single always-on Fargate task hosts the two long-lived watchers Lambda cannot — the HL websocket market-data poller and the on-chain log indexer.
- **Aurora PostgreSQL Serverless v2** as the relational source of truth (not DynamoDB — schema is relational, query/join/aggregate heavy, needs ACID).
- **Per-user KMS custody** — keys never leave the HSM; signing happens in a dedicated Lambda.

---

## 2. Target AWS architecture

![Target AWS architecture](images/01-target-architecture.png)

**Cloudflare → AWS service mapping**

| Cloudflare primitive | AWS replacement | Note |
|---|---|---|
| Worker (handlers) | **Lambda** (event/API) + **ECS Fargate** (watchers) | hybrid compute |
| D1 (SQLite) | **Aurora PostgreSQL Serverless v2** | schema lifted ~1:1; advisory lock absorbs `UserLockDO` |
| 8 Queues | **SQS** *or* **Redis BullMQ** (option open) | serial hedge-sync/reconcile/stop need ordering — SQS FIFO (`MsgGroup=botId`) or BullMQ per-bot concurrency=1; advisory lock guarantees exactly-one either way |
| 2 Crons | **EventBridge Scheduler** | 1m / 5m scan ticks |
| `UserLockDO` | **Postgres advisory lock** | one fewer service |
| `HLRateLimitDO` | **ElastiCache Redis** | atomic token bucket (global 800 / user 80 per min) |
| `MarketDataDO` + `HlMarkDO` | **Redis cache + Fargate poller** | poller writes, Lambdas read |
| Secrets Store (HL DEK) | **KMS + Secrets Manager** | native custody — no cross-cloud signing hop |
| Service binding (OPERATOR→EXBOT) | **API Gateway (HTTP API) + Lambda authorizer** | HMAC short-lived token |

**Ingress.** OPERATOR (Cloudflare) calls EXBOT only on the coarse control plane — `create bot` / `close bot` — through API Gateway, authorized by a Lambda authorizer validating an HMAC short-lived token (reuses the existing `EXBOT_INTERNAL_AUTH_TOKEN` concept), with an `Idempotency-Key` header. There is **no cross-cloud hop on the per-order path**.

**Compute = ECS on Fargate (launch type Fargate).** A single ECS service, `desiredCount=1`, health-check + auto-restart, ~$10–20/mo for a 0.25 vCPU / 0.5 GB task. It runs two watchers: the **HL websocket market-data / mark-price poller**, and the **chain indexer** (watches on-chain logs to confirm transactions and keep state in sync). EKS/EC2 would be needless ops for one task.

---

## 3. Bot lifecycle & event pipeline

![Bot lifecycle and event pipeline](images/02-lifecycle-pipeline.png)

- **Control plane** — OPERATOR → API Gateway → Ingress Lambda writes the bot row + state to Aurora and enqueues work.
- **Scan pipeline** — EventBridge cron fans out per active bot: `bot-scan → light-check → hedge-sync → reconcile`, each a queue (SQS or Redis BullMQ) + consumer.
  - `light-check` evaluates the 8 triggers against **cached** Redis/Aurora data — **no HL API call**.
  - `hedge-sync` runs **serial** (SQS FIFO `MsgGroup=botId`, or BullMQ per-bot concurrency=1), acquires the Postgres **advisory lock**, reserves the Redis rate-limit token, and places the HL order via the Signing Lambda. This is what preserves **exactly-one hedge-sync per bot** (the #1 double-hedge correctness invariant).
  - `reconcile` reads the actual HL position and writes state back to Aurora.
- **Exception routing** — `light-check` diverts to `stop-audit` (priority, pre-liquidation) or `deep-audit / SAFE_MODE` (tiered: warn / restrict / freeze) when a stop is crossed or margin is critical.
- **Per-bot state machine** — `IDLE → LP_OPENING → ACTIVE → CLOSING → CLOSED`.

---

## 4. KMS custody signing

![KMS custody signing](images/03-kms-custody-signing.png)

| KMS key | Scope | Signs |
|---|---|---|
| **Operator key** (1, role-based) | EVM vault | the 4 `executeStrategy` calls (open / rebalance / redeem / collect) |
| **Per-user MASTER key** | withdraw authority | `withdraw3` + HL `approveAgent` |
| **Per-user AGENT key** | trade-only | HL place / reduce orders |

All signing goes through the **Signing Lambda**, which independently re-validates the request and enforces a **per-wallet nonce lock**. The private key **never leaves KMS**; only the signing-Lambda IAM role may call `kms:Sign`.

---

## 5. Key decisions

| Area | Decision |
|---|---|
| Migration strategy | **A — serverless-native now** (pre-prod, no live-fund cutover) |
| Compute | **ECS on Fargate ×1** (watchers) **+ multi-Lambda** (event/API) |
| Database | **Aurora PostgreSQL Serverless v2** (cap max ACU low + scale-to-0 for pre-prod) |
| Queues / cron | **SQS** (Standard + FIFO) **or Redis BullMQ** — option open · **EventBridge Scheduler** |
| Coordination | Postgres advisory lock (`UserLock`) · Redis (rate-limit, cache) |
| Ingress auth | API Gateway + HMAC short-lived token (Lambda authorizer); mTLS upgrade path |
| Operator EVM key | **single KMS key** (role-based), no key in app memory |
| Custody | per-user master + agent KMS; per-wallet nonce lock; signing Lambda only |
| IaC | **AWS CDK (TypeScript)** |
| Region | **ap-southeast-1** (legal to confirm Curaçao residency) |

**Deferred to a later phase:** double-entry accounting ledger (proof-of-reserves).
**Open (business input, non-blocking):** monthly AWS cost ceiling; projected active-user / AUM range.

---

## 6. What ports free vs. rebuilt

- **Verbatim:** `packages/exbot-strategy` (trigger/sizing/risk engine), `packages/exbot-integrations` (HL adapter), `shared-position-math`, backtest packages.
- **Rebuilt:** the Cloudflare binding layer only — the service mapping table in §2.

---

## 7. Top risk

**Double-hedge.** The Durable-Object single-thread guarantee ("exactly-one hedge-sync per bot") must be reproduced exactly under the chosen queue (SQS FIFO or BullMQ) + Postgres advisory lock, or the bot double-hedges. This is the primary correctness risk and needs dedicated concurrency tests at cutover.
