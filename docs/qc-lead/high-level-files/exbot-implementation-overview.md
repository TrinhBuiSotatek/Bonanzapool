# BNZA EXBOT — Implementation Overview & Checklist

> Created: 2026-06-02
> Audience: SOTATEK dev team
> Scope: Locked decisions, architecture overview, planned source structure, and per-track init checklist.
> Source: SPEC v5.2.5, BNZA_EXBOT_Proposal.md, exbot-backtest-overview.md.
> Living doc — update here when decisions change.

---

## 1. Locked Decisions

### 1.1 Technical decisions

| Decision | Choice | Rationale |
|---|---|---|
| EXBOT database | **Dedicated `bnza-exbot-db`** (not shared with OPERATOR D1) | EXBOT is a separate Worker with its own hot-path writes; isolate blast-radius; protect `hl_agent_keys` table; keep the facade boundary clean. OPERATOR passes `auth_context`, so no JOIN against user tables is needed. |
| OPERATOR ↔ EXBOT transport | **Cloudflare service binding** (Worker→Worker) + internal auth (defense-in-depth) | EXBOT stays off the public internet; low latency; matches the facade boundary. Fallback to authenticated HTTPS only if the two Workers ever live in different Cloudflare accounts. |
| Backtest dataset | **Base USDC/ETH 0.3% from ~Aug 2023 → present** as primary | Matches the live chain; add an Ethereum mainnet proxy only if a longer regime history is required. |
| Performance-fee config / vault governance params | Treated as **external config** (deploy address per chain, authorizedOperator, multiSig signer set + threshold, fee distribution, final ABI) — supplied before deploy | Contract authoring + tests proceed with placeholder addresses; only on-chain deploy and live integration depend on these params. |

### 1.2 Architecture principles

- All meaningful strategy logic lives in **`exbot-core`** (pure logic). EXBOT and Backtest differ only in side effects.
- Build **`exbot-core` first** and **freeze its types + signatures early** — both tracks import it.
- OPERATOR is a **facade**; it does **not** run any EXBOT hot path (light-check, HL orders, queue runtime, strategy math).
- `BnzaExVault` is a brand-new contract; it does **not** modify `BnzaRouter v2.2.1` / `BnzaLpBot v1.1` (non-interfering, INV-5).
- Never log/store the HL master key or any plaintext agent key. Never use floats for important ratios/thresholds.

### 1.3 Team model (2 tracks + floating leader)

| Role | Responsibility |
|---|---|
| **Leader** | Stand up architecture first → owns `exbot-core` → helps offload Track 1 → QA/DevOps (back-loaded, W7–W10) |
| **Track 1 — EXBOT** | Live service `apps/bnza-exbot` + HL adapter + vault-client integration |
| **Track 2 — Backtest** | Data crawl + `backtests/exbot` simulator/reports |
| **Track 2 — SC** | `contracts/bnza-exvault` (dedicated Solidity); pivots to help Track 2 data/reports after the contract ships |

Ownership boundary: **authoring** the contract belongs to SC; the **vault-client integration** (code inside `apps/bnza-exbot`) belongs to Track 1, with SC as advisor.

---

## 2. Architecture Overview

### 2.1 Component boundary

```txt
                         +------------------------+
                         |   packages/exbot-core  |   pure logic, no side effects
                         |  position / hedge /    |   (imported by both tracks)
                         |  rebalance / risk /    |
                         |  lifecycle / pnl       |
                         +-----------+------------+
                                     |
            +------------------------+------------------------+
            |                                                 |
            v                                                 v
   +------------------+                              +------------------+
   | apps/bnza-exbot  |  live runtime                | backtests/exbot  |  offline sim
   |  D1 + Queue + DO |                              |  data + reports  |
   |  HL adapter      |                              +------------------+
   |  vault-client    |
   +----+--------+----+
        |        |
        |        v
        |   +------------------------+
        |   | contracts/bnza-exvault |  LP NFT custody (operator/multiSig)
        |   +------------------------+
        v
   +----------------------+        service binding         +------------------+
   | apps/bnza-operator   | <----------------------------> |  EXBOT internal  |
   | facade: /api/exbot/* |  (auth_context, internal auth) |  API             |
   +----------------------+                                +------------------+
        ^
        | public
   POOL / MOBILE / ADMIN
```

### 2.2 Request flow (facade → live)

```txt
POOL/MOBILE/ADMIN
  -> apps/bnza-operator  /api/exbot/start
       1. check X-Wallet-Address, blocked/allowed/admin, ownership
       2. normalize request + build auth_context
       3. env.EXBOT.fetch(...) over service binding   <-- never hits the public internet
  -> apps/bnza-exbot internal API
       4. validate internal auth + auth_context
       5. create bot state (pending) in D1, enqueue
       6. return fast { bot_id, status: pending }
  -> heavy work runs in EXBOT's internal queues (hedge-sync, reconcile, ...)
```

### 2.3 Same logic — two runtimes

```txt
Rule (exbot-core):  drift > 15%  => rebalance

EXBOT live:                         Backtest:
  -> enqueue hedge-sync               -> record a simulated rebalance event
  -> send real order to HL            -> compute fee/slippage/funding/PnL
  -> update D1 after reconcile        -> feed into the report
```

### 2.4 Data store boundary

```txt
bnza-operator D1          bnza-exbot-db (DEDICATED)
  user/wallet/whitelist     bots (+lifecycle_state)
  POOL existing tables      positions (custodian=vault)
                            hedge_legs, bot_runtime_state
                            rebalance_attempts, circuit_breakers
                            funding_daily_metrics, queue_idempotency
                            hl_agent_keys (envelope-encrypted)
```

---

## 3. Planned Source Structure

```txt
packages/exbot-core      # Shared pure logic (build first, freeze early)
apps/bnza-exbot          # Live EXBOT Cloudflare Worker (D1 + Queue + DO + HL + vault-client)
backtests/exbot          # Offline simulation + reports
contracts/bnza-exvault   # Solidity LP NFT custody (Foundry)
apps/bnza-operator       # Existing facade/gateway (adds /api/exbot/*)
```

---

## 4. Init Checklist By Track

### 4.0 Shared — blocks both tracks (do first)

**External / infra dependencies**
- Repo access + reference source for `BnzaRouter v2.2.1` / `BnzaLpBot v1.1`.
- HL testnet credentials (builder account, agent-key flow on testnet).
- Cloudflare account: D1, R2, Queues, Secrets Store, Durable Objects bindings ready.
- Confirm data sources: HL funding data + Uniswap pool data (subgraph / RPC archive).

**Repo skeleton + Core (SH-01..SH-08)**
- Monorepo skeleton + workspace wiring (5 packages from §3). (SH-01)
- `exbot-core`: shared types — bot state, lifecycle, hedge state, RebalanceReason, PnL model. (SH-02)
- `exbot-core`: function skeletons + signatures (position-amount, hedge-math, rebalance-rules, risk-rules, lifecycle, pnl). (SH-03..SH-07)
- `exbot-core`: unit test skeleton + golden/test vectors from SPEC. (SH-08)
- **Freeze the core contract (types + signatures) early.**
- CI/env spike: monorepo build/test pipeline + `wrangler dev` running.

**Architecture lock (before deep coding)**
- Boundary diagram (core/exbot/backtest/vault/operator).
- Define the `vault-client` interface (between `apps/bnza-exbot` ↔ contract) so Track 1 and SC code against the same contract in parallel.
- Define the OPERATOR→EXBOT internal API contract (request/response) over the service binding.

---

### 4.1 Track 1 — EXBOT (Live Service + HL Adapter + Vault Integration)

Depends on: core skeleton + interfaces (§4.0), dedicated D1, service binding.

**Service & runtime skeleton**
- Init `apps/bnza-exbot` Worker + `wrangler.toml` + health/readiness/version. (EX-01, EX-05)
- Internal API skeleton (start/status/close) — routes + auth validation only. (EX-02)
- Service auth layer skeleton. (EX-03)
- Runtime config module: chains, pool, hedge defaults, vault address (TBD), HL network. (EX-04)
- `@bnza/exbot-core` imports and bundles cleanly inside the Worker.

**DB & state skeleton (dedicated D1)**
- D1 schema draft + local migration (9 tables from §2.4). (EX-06..EX-10)
- State repository skeleton. (EX-08)

**Queue / Cron / DO declaration (bindings only, no logic yet)**
- Declare queues: bot-scan, light-check, hedge-sync, reconcile, deep-audit, stop-audit, notification, metrics-rollup + DLQ. (EX-11..EX-16)
- Declare DOs: UserLockDO, HLRateLimitDO, MarketDataDO. (EX-17..EX-19)
- Cron trigger skeleton (scan + jitter).

**HL adapter prep**
- HL adapter skeleton: info/exchange wrapper stub (testnet). (EX-20)
- Cloid generation + nested-error parser stub. (EX-21)
- Verify on HL testnet: read mark/funding, place a test reduce-only order.
- Agent-key envelope encryption design + Secrets Store wiring (no real keys yet). (EX-07, EX-22)

**Vault integration point**
- `bnza-exvault-client.ts` stub against the §4.0 interface (awaits SC contract). (EX-23)
- Define the post-order reconcile point (interface). (EX-25)

**OPERATOR facade skeleton (service binding)**
- Route skeleton `/api/exbot/*` in `apps/bnza-operator` — TODO integration. (EX-40)
- Ownership/RBAC guard skeleton. (EX-41)
- Internal client skeleton OPERATOR→EXBOT over the service binding. (EX-42)

---

### 4.2 Track 2 — Backtest + Data Crawl

Depends on: core skeleton (§4.0), Base dataset (~Aug 2023+).

**Backtest skeleton**
- Init `backtests/exbot`: `data/`, `simulator/`, `reports/`, `cli.ts`, `configs/`, `outputs/`.
- Config schema (period/pool/strategy/costs) — per `base-usdc-eth-default.json`.
- `@bnza/exbot-core` imports and runs in the backtest locally (Node).
- Simulator module skeleton: lp/hedge/strategy (calls core). (BT-05..BT-07)
- Event ledger skeleton. (BT-08)

**Data pipeline prep (Base primary)**
- Lock Uniswap V3 USDC/ETH 0.3% (Base) source: subgraph / RPC archive — price, tick, liquidity, swaps, fees. (BT-01)
- Lock Hyperliquid source: mark/oracle price + funding history. (BT-02)
- Cost-model config draft: gas, slippage, bridge, builder fee 5bps, PF 30%. (BT-03)
- Plan data alignment + UTC normalization. (BT-04)
- Prepare one known-LP/golden case to validate the engine before final runs. (BT-12)

**Data crawl — stack & approach**

This is API/RPC data ingestion, **not** web scraping — no Scrapy/Puppeteer/Playwright.

- **Language: TypeScript/Node** (not Python). The backtest must `import` `exbot-core` so strategy logic never drifts from live; a Python crawler/sim cannot import the TS core and would force duplicated logic.
- **Cache pattern:** `crawl raw → cache to disk (data/cache/*) → align/clean → simulator reads cache`. Crawl only on cache miss — subgraph/RPC are rate-limited and slow to re-fetch.

| Data | Source | Tooling |
|---|---|---|
| Uniswap V3 (Base) aggregates + swaps | The Graph subgraph (GraphQL) | `graphql-request` |
| ↳ fallback (granularity/coverage gaps) | Archive RPC + Swap/Mint/Burn logs | `viem` (`getLogs` + decode) |
| Hyperliquid mark/funding | HL Info API (`candleSnapshot`, `fundingHistory`) | TS SDK or raw `fetch` |
| Rate limit + retry | — | `p-limit` + `p-retry` |
| Fetched-data validation | — | `zod` |
| Exact decimal math (no float) | — | `dnum` or `decimal.js` |
| Cleaned-data storage | — | CSV (`papaparse`) or Parquet (`apache-arrow`) |

**Subgraph coverage — verification status (as of 2026-06-02, live check pending):**
- Uniswap V3 is deployed on Base since ~Aug 2023; the V3 subgraph for Base is served via **The Graph decentralized network**, which **requires an API key** (Graph Studio, billed in GRT/credits) — the legacy hosted service is sunset.
- **To confirm at implementation time:** (1) exact Base deployment ID via the Graph gateway, (2) that the **0.3% fee-tier** USDC/WETH pool has enough liquidity/volume on Base to be representative — much Base ETH/USDC liquidity sits in the **0.05%** tier, so verify the 0.3% pool isn't too thin before locking it as the backtest target, (3) history depth reaches the chosen start (~Aug 2023). If subgraph gaps appear, switch BT-01 to the archive-RPC fallback.

---

### 4.3 Track 2 — SC (BnzaExVault)

**Runs first (no external params needed — use placeholder addresses):**
- Init Foundry project `contracts/bnza-exvault` (src/test/script). (EX-26)
- BnzaExVault interface: vaultMint, vaultRebalance, vaultClose, vaultCollect, pause/unpause, rotateOperator, emergency recovery. (EX-27..EX-30)
- Match the interface to the `vault-client` from §4.0 (Track 1 integration point).
- Invariant spec: `NFPM.ownerOf(tokenId) == address(BnzaExVault)`.
- Unit / fork / invariant tests with placeholder addresses. (EX-31)

**Needs external governance params before deploy/integration:**
- Final ABI confirmation (before freezing the interface for Track 1).
- Deploy script + address registry for Base + OP — needs deploy address / authorizedOperator / multiSig signer set + threshold. (EX-32)
- vault-client ↔ live integration + on-chain verification (A2).

---

## 5. Definition of Done — Init Phase

- `exbot-core`: types + signatures + test skeleton, contract frozen.
- `apps/bnza-exbot`: health endpoint ok, internal API skeleton, D1 migration runs locally, queues/DOs declared.
- `backtests/exbot`: CLI skeleton, config example, simulator skeleton imports core, data sources locked.
- `contracts/bnza-exvault`: Foundry project + interface + test skeleton (placeholder, awaits deploy params).
- `apps/bnza-operator`: facade route skeleton + TODO integration point.
- §1.1 decisions applied; §4.0 dependencies in place.

## 6. Open Questions

- Does OPERATOR keep a minimal status mirror, or always query EXBOT status live? (Not blocking init — decide once the internal API exists.)
- Who may adjust strategy parameters when live results diverge from backtest? (Decide before the validation phase.)
