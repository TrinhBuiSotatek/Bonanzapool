# BNZA EXBOT — Detailed Task Breakdown

> Created: 2026-06-02
> Audience: SOTATEK dev team
> Scope: Concrete sub-tasks + acceptance criteria for every task ID, grouped by track.
> Companion to `exbot-implementation-overview.md`. SPEC §refs point to SPEC v5.2.5.
> Living doc — update here when scope changes.

**ID prefixes:** `SH-` Shared Foundation (`exbot-core`) · `EX-` EXBOT track · `BT-` Backtest track.
SC items are `EX-26..EX-32`.

**Status legend:** ☐ not started · ◐ in progress · ☑ done.

---

## Track: Foundation — `packages/exbot-core` (owner: Leader)

Build first, freeze types + signatures early. Pure logic — no D1/HL/tx/env/secret.

### SH-01 — Project Layout
- ☐ Init monorepo + workspace wiring for the 5 packages (§3 of overview).
- ☐ Shared tsconfig/eslint/prettier; package `@bnza/exbot-core`.
- ☐ CI: build + test all packages; `wrangler dev` boots `apps/bnza-exbot`.
- **Output:** repo skeleton. **Acceptance:** `pnpm -r build` + `pnpm -r test` green.

### SH-02 — Shared Types
- ☐ Define: bot state, lifecycle state, hedge state, `RebalanceReason` enum, PnL model, margin status.
- ☐ Use bigint/decimal-string for ratios/amounts (no float).
- **Output:** `types.ts`. **Acceptance:** types consumed by exbot + backtest compile.

### SH-03 — Position Amount Calculator (§6)
- ☐ Uniswap V3 AMM math: LP token amounts from range + price, LP ETH exposure.
- ☐ tick ↔ price ↔ sqrtPriceX96 conversions.
- **Output:** `position-amount.ts`. **Acceptance:** golden vectors from SPEC §6 pass.

### SH-04 — Hedge Math (§7)
- ☐ `targetShort = lpEthAmount × hedgeRatioBps / 10_000` (70% default).
- ☐ Leverage/margin helper (3x isolated), builder-fee aware (5bps).
- **Output:** `hedge-math.ts`. **Acceptance:** unit tests on target-short + margin.

### SH-05 — Rebalance Rules (§7.3/§7.6)
- ☐ Implement triggers: `drift_threshold` (>max($25, lpValue×3%)), `drift_relative` (>15%), `range_out`, `range_boundary_near` (90%), `margin_warning`, `funding_alert` (7d<−15% APR), `time_fallback` (4h), `manual_admin`/`recovery_reconcile`.
- ☐ Economic gate (§7.5): hedge budget cap — block rebalance if cost > trailing-7d LP fee × 30%.
- ☐ All thresholds config-driven (backtest-tunable), target_ratio normalized to bps.
- **Output:** `rebalance-rules.ts`. **Acceptance:** each trigger has a deterministic test case.

### SH-06 — Risk Rules (§18.4)
- ☐ Margin status (ok/warning/critical), stop trigger, circuit breaker, SAFE_MODE rules.
- ☐ Routing exceptions: `stop_trigger_crossed`/near-stop → stop-audit; `margin_critical` → SAFE_MODE.
- **Output:** `risk-rules.ts`. **Acceptance:** boundary tests around warning/critical thresholds.

### SH-07 — Lifecycle Model
- ☐ Canonical states: preflight → active → paused → closing → closed (+ SAFE_MODE).
- ☐ Allowed transitions as a pure function; reject illegal transitions.
- **Output:** `lifecycle.ts`. **Acceptance:** transition table test.

### SH-08 — Core Test Vectors
- ☐ Deterministic unit tests + golden cases from SPEC for SH-03..07.
- **Output:** `tests/`. **Acceptance:** `pnpm --filter @bnza/exbot-core test` green; coverage on math/rules.

---

## Track 1 — EXBOT (`apps/bnza-exbot` + HL + facade)

Depends on Foundation + `vault-client` interface. DB = dedicated `bnza-exbot-db`. Transport = service binding.

### Service & Runtime
- **EX-01 Worker Service** — ☐ Init `apps/bnza-exbot` Worker + `wrangler.toml` bindings (D1, Queues, DOs, Secrets Store). **Acceptance:** worker boots locally.
- **EX-02 Internal API** — ☐ Internal endpoints (start/status/close/agent-key/margin) consumed by OPERATOR; request/response contract. **Acceptance:** routes return typed stubs.
- **EX-03 Service Auth** — ☐ Validate internal auth token + `auth_context` on every internal call. **Acceptance:** unauthorized call rejected.
- **EX-04 Runtime Config** — ☐ Config module: chains (Base→OP), pool, hedge defaults (70%/3x/5bps), vault addresses, HL network. **Acceptance:** config loads per env.
- **EX-05 Health/Readiness** — ☐ `/health`, `/ready`, `/version`. **Acceptance:** returns ok + build info.

### Database & State (§13)
- **EX-06 D1 Schema** — ☐ Migrations for: bots(+lifecycle_state), positions(custodian=vault), hedge_legs, bot_runtime_state, rebalance_attempts, circuit_breakers (hedge_leg PK), funding_daily_metrics, queue_idempotency, hl_agent_keys. **Acceptance:** migrations run locally.
- **EX-07 Agent Key Storage** — ☐ `hl_agent_keys` with envelope-encryption fields (no plaintext). **Acceptance:** schema stores ciphertext + key ref only.
- **EX-08 State Repository** — ☐ Read/write repo for lifecycle + runtime state. **Acceptance:** CRUD unit tests vs local D1.
- **EX-09 Idempotency Store** — ☐ `queue_idempotency` keys + expiry. **Acceptance:** duplicate key is a no-op.
- **EX-10 Metrics State** — ☐ funding/PnL/attempts/circuit-breaker/audit tables. **Acceptance:** writes + reads tested.

### Queues / Cron / Durable Objects (§10, §11)
- **EX-11 Bot Scan** — ☐ Cron scans due bots + jitter, enqueues light-check. **Acceptance:** due bots enqueued, others skipped.
- **EX-12 Light Check** — ☐ Per-bot health + rebalance detection using cached D1 + MarketDataDO (NO HL fetch). **Acceptance:** emits `RebalanceReason` from core.
- **EX-13 Hedge Sync** — ☐ Event-driven HL mutation, delta-only adjust (§17). **Acceptance:** computes delta, not full close/open.
- **EX-14 Reconcile** — ☐ Confirm actual HL state after order submit. **Acceptance:** state only marked success post-confirm.
- **EX-15 Deep Audit** — ☐ Periodic full reconciliation. **Acceptance:** detects + repairs drift between D1 and HL.
- **EX-16 Stop Audit** — ☐ Priority audit for stop-trigger / near-stop (§19.3). **Acceptance:** runs ahead of routine queues.
- **EX-17 User Lock DO** — ☐ Lease-based lock serializing per-user mutations. **Acceptance:** concurrent mutations serialized.
- **EX-18 HL Rate Limit DO** — ☐ Enforce HL global/user rate limits. **Acceptance:** over-limit calls throttled.
- **EX-19 Market Data DO** — ☐ Cache pool slot0/price shared by all bots. **Acceptance:** one upstream fetch serves many bots.

### Hyperliquid Execution (§8/§9) — pairs with HL dev
- **EX-20 HL Adapter** — ☐ info/exchange wrapper (testnet first). **Acceptance:** reads mark/funding, places test reduce-only order.
- **EX-21 Cloid & Errors** — ☐ Deterministic cloid generation + nested-error parser. **Acceptance:** stable cloid; error cases mapped.
- **EX-22 Agent Key Flow** — ☐ Verify approval, decrypt agent key only when needed, sign orders; Secrets Store. **Acceptance:** key never logged/persisted in plaintext.
- **EX-23 Hedge Open/Adjust/Close** — ☐ IOC short open, reduce-only close, delta-only adjust. **Acceptance:** matches core target within tolerance.
- **EX-24 Native Stop** — ☐ Place/cancel/replace/verify reduce-only stop (§8.4/§19). **Acceptance:** stop lifecycle verified on testnet.
- **EX-25 Reconcile After Order** — ☐ Treat success only after actual position confirmed (§9). **Acceptance:** no premature success write.

### Bot Lifecycle APIs
- **EX-33 Agent Approval API** — ☐ Receive HL agent approval, persist encrypted key. **Acceptance:** key stored encrypted, status updated.
- **EX-34 Margin Confirm API** — ☐ Confirm margin deposit / readiness. **Acceptance:** preflight margin check passes/fails correctly.
- **EX-35 Start Bot** — ☐ Preflight → LP open (vault) → hedge open → stop placement → active. **Acceptance:** full flow reaches `active` (dry-run + A2).
- **EX-36 Pause/Resume** — ☐ Pause preserving LP+hedge, then resume. **Acceptance:** no position change across pause/resume.
- **EX-37 Stop/Close** — ☐ Close hedge, cancel stop, close LP, record final PnL. **Acceptance:** all legs closed, PnL persisted.
- **EX-38 Status API** — ☐ Return LP, hedge, PnL, drawdown, margin, SAFE_MODE. **Acceptance:** matches D1/runtime state.
- **EX-39 Admin Recovery API** — ☐ Manual reset, force SAFE_MODE, circuit-breaker reset. **Acceptance:** admin-only; audited.

### OPERATOR Facade Integration
- **EX-40 Public Facade Routes** — ☐ `/api/exbot/*` in `apps/bnza-operator`. **Acceptance:** routes proxy to EXBOT.
- **EX-41 Ownership/RBAC** — ☐ Validate wallet owner/admin before internal call. **Acceptance:** non-owner rejected.
- **EX-42 Internal Client** — ☐ OPERATOR → EXBOT over service binding. **Acceptance:** binding call works end-to-end.
- **EX-43 Status Mirror Decision** — ☐ Decide if OPERATOR mirrors minimal EXBOT status (open question). **Output:** decision note.
- **EX-44 OpenAPI Contract** — ☐ Document public request/response. **Acceptance:** OpenAPI spec published.

### Operations & Verification
- **EX-45 Logging & Redaction** — ☐ Structured logs + secret redaction. **Acceptance:** no secret in logs (sanitize test).
- **EX-46 Monitoring** — ☐ Queue lag, HL usage, D1 latency, SAFE_MODE, circuit-breaker metrics. **Acceptance:** dashboards/alerts live.
- **EX-47 A1 Dry-Run** — ☐ Full no-live-order flow (start→active→light-check→hedge-sync dry mode→status). **Acceptance:** dry-run DoD met (API/D1/queue/core/security/ops).
- **EX-48 A2 Live $1k** — ☐ One-user live test: real LP + real HL hedge, small fund. **Acceptance:** A2 exit criteria (vault owns NFT, hedge in tolerance, stop ok, reconcile correct, SAFE_MODE works, PnL near backtest).
- **EX-49 A3 Closed Beta** — ☐ 5–10 user beta readiness plan. **Output:** A3 plan/report (follow-on phase).

---

## Track 2 — Backtest (`backtests/exbot`)

TS/Node, imports `exbot-core`. Mainnet historical data, read-only.

### Data Pipeline
- **BT-01 Uniswap Data** — ☐ Crawl Base USDC/ETH 0.3% pool: price, ticks, liquidity, swaps, fees (subgraph; RPC fallback). **Acceptance:** continuous series for chosen range, cached.
- **BT-02 Hyperliquid Data** — ☐ Crawl HL mark/oracle price + funding history (Info API). **Acceptance:** funding + price series cached.
- **BT-03 Cost Model Data** — ☐ Define gas, slippage, bridge, builder fee 5bps, PF 30% assumptions. **Output:** cost config.
- **BT-04 Data Alignment** — ☐ Clean, normalize, UTC-align all series. **Acceptance:** single aligned timeline, gaps reported.

### Simulation Engine
- **BT-05 LP Simulator** — ☐ Simulate LP value, fee accrual, range status, IL/LVR (uses core position-amount). **Acceptance:** reproduces a known LP's return within tolerance (BT-12).
- **BT-06 Hedge Simulator** — ☐ Simulate short PnL, funding, margin, stop, rebalance (uses core hedge-math). **Acceptance:** hedge PnL matches manual calc on a sample.
- **BT-07 Strategy Simulator** — ☐ Drive core rebalance/risk rules end-to-end over the timeline. **Acceptance:** triggers fire at expected timestamps.
- **BT-08 Event Ledger** — ☐ Record every rebalance/stop/funding/close/fee event. **Acceptance:** ledger reconstructs final PnL.

### Scenario & Parameter Testing
- **BT-09 Scenario Runs** — ☐ ETH up, ETH down, in-range ±5%, tail cases. **Output:** per-scenario results.
- **BT-10 Parameter Sweep** — ☐ Sweep range width, hedge ratio, leverage, thresholds, cooldown, stop factor. **Output:** sweep matrix.
- **BT-11 Sensitivity Analysis** — ☐ Which param hurts/helps APR, drawdown, rebalance cost. **Output:** analysis report.
- **BT-12 Live-vs-Backtest Guard** — ☐ Define expected live discount/tolerance (~20–30%). **Output:** calibration notes.

### Reporting
- **BT-13 PnL Report** — ☐ Net APR after LP fee − IL − hedge cost − funding − gas − PF. **Output:** report.
- **BT-14 Rebalance Report** — ☐ Rebalance count + cost by `RebalanceReason`. **Output:** report section.
- **BT-15 Risk Report** — ☐ Max drawdown, worst 1d/7d, stop count, margin events. **Output:** report section.
- **BT-16 Go/No-Go Report** — ☐ Decide whether defaults are acceptable for live. **Output:** decision report.

---

## Track 2 — SC (`contracts/bnza-exvault`)

Foundry/Solidity. Authoring + tests run first with placeholder addresses; deploy/integration needs external governance params.

### Runs first (placeholder addresses)
- **EX-26 Vault Contract** — ☐ New `BnzaExVault` for EXBOT custody (does not touch BnzaRouter/BnzaLpBot, INV-5). **Acceptance:** compiles, interface matches `vault-client`.
- **EX-27 Vault Mint** — ☐ `vaultMint`: open LP NFT into vault custody. **Acceptance:** `NFPM.ownerOf(tokenId) == vault`.
- **EX-28 Vault Rebalance** — ☐ `vaultRebalance`: operator-only LP NFT rebalance. **Acceptance:** only authorizedOperator; NFT not transferable out (INV-1).
- **EX-29 Vault Close** — ☐ `vaultClose` (+`vaultCollect`): close LP, return assets per spec. **Acceptance:** assets returned, PF path correct.
- **EX-30 Emergency Controls** — ☐ pause/unpause, rotateOperator, emergencyTransfer (multiSig-only). **Acceptance:** emergency paths multiSig-gated.
- **EX-31 Vault Tests** — ☐ Unit + fork + invariant (Foundry) with placeholder addresses. **Acceptance:** `forge test` green; invariant `ownerOf==vault` holds.

### Needs external governance params before deploy
- **EX-32 Vault Deploy** — ☐ Deploy scripts (Base + OP) + address registry. Needs deploy address / authorizedOperator / multiSig set + threshold + final ABI. **Acceptance:** deployed + verified; vault-client integrated; A2 on-chain checks pass.

---

## Dependency Notes

- `exbot-core` (SH-*) blocks BT-05..08 and EX-12/13/23 — build + freeze first.
- `vault-client` interface (SH-01 / overview §4.0) lets Track 1 (EX-23) and SC (EX-26) proceed in parallel.
- EX-32 + EX-48 (A2) gated on external governance params.
- BT-12 must use the same `exbot-core` as live — no duplicated logic.
