# Feature Inventory

## Extraction summary
- source strategy: Track-based task breakdown from `exbot-task-breakdown.md` (primary) + system component list from `exbot-implementation-overview.md` (secondary) + previous feature list embedded in existing `project-context-master.md` (Update mode preservation).
- official candidates: 16 tracks/groups (using SH-/EX-/BT- IDs)
- derived candidates: 0 (no need to fall back to requirement-common-files — task breakdown is explicit)
- temporary IDs: 0
- blocked: no

## Feature candidates

| ID | Site | Module | Feature/Use case name | In scope? | Source | Source type | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|
| SH-* | exbot-core | Shared Foundation | Shared types, position math, hedge math, rebalance rules, risk rules, lifecycle, test vectors | Yes | exbot-task-breakdown.md §Foundation | official high-level | High | 8 tasks SH-01..SH-08. Build first, freeze early. |
| EX-01..05 | apps/bnza-exbot | Service & Runtime | Worker init, internal API, service auth, runtime config, health/readiness | Yes | exbot-task-breakdown.md §Service&Runtime | official high-level | High | |
| EX-06..10 | apps/bnza-exbot | Database & State | D1 schema, agent key storage, state repo, idempotency, metrics | Yes | exbot-task-breakdown.md §Database&State | official high-level | High | Dedicated `bnza-exbot-db` (separate from operator D1). |
| EX-11..16 | apps/bnza-exbot | Queues / Cron | Bot Scan, Light Check, Hedge Sync, Reconcile, Deep Audit, Stop Audit | Yes | exbot-task-breakdown.md §Queues/Cron/DOs | official high-level | High | |
| EX-17..19 | apps/bnza-exbot | Durable Objects | UserLockDO, HLRateLimitDO, MarketDataDO | Yes | exbot-task-breakdown.md | official high-level | High | |
| EX-20..25 | apps/bnza-exbot | Hyperliquid Execution | HL Adapter, Cloid/Errors, Agent Key Flow, Hedge Open/Adjust/Close, Native Stop, Reconcile-after-order | Yes | exbot-task-breakdown.md §HL Execution | official high-level | High | |
| EX-26..32 | contracts/bnza-exvault | Smart Contract | Vault contract, Mint, Rebalance, Close, Emergency, Tests, Deploy | Yes (auth+test) / Partial (deploy) | exbot-task-breakdown.md §SC | official high-level | High | EX-32 deploy gated on external governance params. |
| EX-33..39 | apps/bnza-exbot | Bot Lifecycle APIs | Agent Approval, Margin Confirm, Start, Pause/Resume, Stop/Close, Status, Admin Recovery | Yes | exbot-task-breakdown.md | official high-level | High | |
| EX-40..44 | apps/bnza-operator | OPERATOR Facade | Public Routes /api/exbot/*, Ownership/RBAC, Internal Client, Status Mirror Decision, OpenAPI | Yes | exbot-task-breakdown.md | official high-level | High | Service binding to EXBOT (no public internet). |
| EX-45..49 | apps/bnza-exbot | Operations & Verification | Logging/Redaction, Monitoring, A1 Dry-Run, A2 Live $1k, A3 Closed Beta | Yes | exbot-task-breakdown.md | official high-level | High | A2/A3 gated on external governance params. |
| BT-01..04 | backtests/exbot | Data Pipeline | Uniswap data crawl, HL data crawl, cost model, data alignment | Yes | exbot-task-breakdown.md §Backtest | official high-level | High | Subgraph requires API key (Graph Studio). |
| BT-05..08 | backtests/exbot | Simulation Engine | LP simulator, Hedge simulator, Strategy simulator, Event ledger | Yes | exbot-task-breakdown.md | official high-level | High | Imports `exbot-core` (no duplicated logic). |
| BT-09..12 | backtests/exbot | Scenario & Parameter | Scenario runs, parameter sweep, sensitivity analysis, live-vs-backtest guard | Yes | exbot-task-breakdown.md | official high-level | High | |
| BT-13..16 | backtests/exbot | Reporting | PnL, Rebalance, Risk, Go/No-Go reports | Yes | exbot-task-breakdown.md | official high-level | High | |
| (carryover) | system | UI / Mobile | BNZA POOL UI, Admin/Config UI | Deferred | existing project-context-master.md §3.2 | existing dashboard | High | Not in scope for Phase A. |

## Feature inventory delta
- new: 14 track-grouped feature areas (SH-*, EX-01..49, BT-*) — coming from exbot-task-breakdown.md
- existing unchanged: high-level system components list (carries over)
- re-add candidates: none
- not found in current source: none
- need confirmation: official feature inventory (each task has `Acceptance` criteria; QC Lead should review priority + scope)

## Gaps for project context

| Gap | Type | Impact | Suggested owner |
|---|---|---|---|
| Public-facing UI (POOL/MOBILE) feature inventory | Needs BA/Tech Lead source | Phase B+ — not in current scope | BA |
| Test data preparation per feature group | QC-fillable | Need test wallets, faucet plan, HL testnet account list | QC Lead |
| Mapping `exbot-core` golden vectors → SPEC §6/§7 references | Derivable from detailed requirement docs | QC needs to know which SPEC sections govern each test vector | Tech Lead |
