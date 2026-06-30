# Site Map Handoff: BNZA Ecosystem
**Date:** 2026-06-30
**Source:** qc-site-map Initialization run (run-20260630-000002-trinhbui)
**Mode:** Initialization -- auto-invoke qc-dashboard-sync

---

## Feature List for qc-dashboard-sync (Top-down)

Tung dong duoi day la mot feature/UC can duoc tao row trong qc-dashboard.md.
Moi dong: Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes

### PTL-02 BNZA-ADMIN

| Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes |
|---|---|---|---|---|---|---|---|
| FM-ADM-01 | WL Partner Onboarding | SCR-ADM-003, SCR-ADM-004, SCR-ADM-005 | bnza-admin-wl-partner | Yes (P0) | Derived | Khong co wireframe | Cascade: wl_codes, wl_master_wallets, on-chain setBotWlMaster |
| FM-ADM-02 | PF Distribution | SCR-ADM-006, SCR-ADM-007 | bnza-admin-pf | Yes (P0) | Derived | Khong co wireframe | daily-collector cron dependency |
| FM-ADM-03 | IB Management | SCR-ADM-008, SCR-ADM-009 | bnza-admin-ib | Yes (P1) | Derived | Khong co wireframe | -- |
| FM-ADM-04 | Bot Type Config | SCR-ADM-010, SCR-ADM-011 | bnza-admin-bot-type | Yes (P1) | Derived | Khong co wireframe | cooldown range 10-180 min |
| FM-ADM-05 | Dashboard | SCR-ADM-002 | bnza-admin-dashboard | Yes (P2) | Derived | -- | -- |
| FM-ADM-06 | Reports | SCR-ADM-016 | bnza-admin-reports | Yes (P2) | Derived | -- | -- |
| FM-ADM-07 | TOKEN Management | SCR-ADM-019 | bnza-admin-token | Yes (P3/mock) | Derived | -- | Mock only |
| FM-ADM-08 | System Settings | SCR-ADM-017 | bnza-admin-settings | Yes (P2) | Derived | -- | All writes: reason note + Slack audit |
| FM-ADM-09 | Relayer Monitor | SCR-ADM-018 | bnza-admin-relayer | Yes (P2) | Derived | -- | -- |
| FM-ADM-10 | WL Bot Lifecycle Monitor | SCR-ADM-012 | bnza-admin-wl-bot-monitor | Yes (P1) | Derived | -- | wl_activation_status 5-state; 48h SLA |
| FM-ADM-11 | User Management | SCR-ADM-013 | bnza-admin-users | Yes (P1) | Derived | -- | RBAC read-only viewer |
| FM-ADM-12 | Audit Log Viewer | SCR-ADM-014, SCR-ADM-015 | bnza-admin-audit-log | Yes (P0) | Derived | -- | Append-only; filter max 90 days |

### PTL-03 BNZA-EX

| Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes |
|---|---|---|---|---|---|---|---|
| FM-EX-01 | TradingView Integration | SCR-EX-002 | bnza-ex-trading | Yes (P2) | Derived | TradingView license needed | -- |
| FM-EX-02 | Chart Data Feed | SCR-EX-002 | bnza-ex-trading | Yes (P2) | Derived | -- | HL WebSocket dependency |
| FM-EX-03 | Order Placement | SCR-EX-002, SCR-EX-003 | bnza-ex-trading | Yes (P2) | Derived | -- | Direct HL; no OPERATOR |
| FM-EX-04 | i18n | SCR-EX-001..003 (cross-cutting) | bnza-ex-trading | Yes (P2) | Derived | -- | 5 languages |

### PTL-04 BNZA-EXBOT Infrastructure

| Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes |
|---|---|---|---|---|---|---|---|
| FM-XB-01 | D1 Schema | API-only (no screen) | exbot-bot-start | Yes (P0) | Derived | Need signed-off schema | Parent of all ExBot operations |
| FM-XB-02 | Queue Topology | API-only (no screen) | exbot-api | Yes (P0) | Derived | -- | 10 queues + DLQ; idempotency critical |
| FM-XB-03 | Durable Objects | API-only (no screen) | exbot-durable-objects | Yes (P0) | Derived | -- | HLRateLimitDO, UserLockDO, MarketDataDO |
| FM-XB-04 | Cron Jobs | API-only (no screen) | exbot-cron | Yes (P1) | Derived | Interval TBD | deep-audit, metrics-rollup, stop-integrity |
| FM-XB-05 | HL Adapter | API-only (no screen) | exbot-hedge-sync | Yes (P1) | Derived | NV-3, NV-12 open | Rate limit, cloid, error parser |
| FM-XB-06 | API Endpoints | API-only (no screen) | exbot-api | Yes (P1) | Derived | -- | 7 endpoints via OPERATOR facade |
| FM-XB-07 | Router Extension (Solidity) | API-only (on-chain) | exbot-bot-start | Yes (P1) | Derived | zen Solidity specs needed | LP NFT custody |
| FM-XB-08 | OPERATOR API ExBot Endpoints | API-only (no screen) | exbot-api | Yes (P1) | Derived | -- | -- |
| FM-XB-09 | Phase A1 Dry Run | API-only (no screen) | exbot-bot-start | Yes (P0) | Derived | Phase 0 gate not passed | Critical: Phase 0 gate 4 dieu kien |
| FM-XB-10 | Phase A2 Live $1k Test | API-only (no screen) | exbot-phase-progression | Yes (P1) | Derived | Blocked by A1 | -- |
| FM-XB-11 | Phase A3 Closed Beta | API-only (no screen) | exbot-phase-progression | Yes (P1) | Derived | Blocked by A2 | -- |
| FM-XB-12 | Envelope Encryption | API-only (no screen) | exbot-bot-start | Yes (P0) | Derived | HL agent key method TBD | Master key CF Secrets; per-bot encrypted D1 |
| FM-XB-13 | Pre-launch Hotfixes | API-only (no screen) | exbot-bot-start | Yes (P0) | Derived | -- | Must fix before Phase A1 |

### PTL-05 BNZA-POOL

| Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes |
|---|---|---|---|---|---|---|---|
| FM-PL-01 | Step 7 Multi-Bot | SCR-PL-001..006, SCR-PL-008 | bnza-pool-multi-bot | Yes (P1) | Derived | Khong co wireframe | max 10/chain; chain filter |
| FM-PL-02 | Step 8 plan_specs | SCR-PL-007 | bnza-pool-plan-specs | Yes (P1) | Derived | Migration 0008 not yet deployed | Version immutability; outdated warning |
| FM-PL-03 | Fiat On-Ramp (Banxa) | SCR-PL-009 | bnza-pool-buy | Yes (P3/mock) | Derived | Mock only | -- |

### BNZA-OPERATOR WL Backend (backend features)

| Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes |
|---|---|---|---|---|---|---|---|
| FM-OPW-01 | DB Migrations 0024-0027 | API-only | operator-wl-db | Yes (P0) | Derived | Need migration scripts | Parent of all WL backend |
| FM-OPW-02 | Ledger API | API-only | operator-wl-ledger | Yes (P0) | Derived | Min disclosure rules must verify | HMAC-SHA256; 90-day cap |
| FM-OPW-03 | Bot API | API-only | operator-wl-bot | Yes (P0) | Derived | Two-phase commit; on-chain dep | wl_members lifecycle |
| FM-OPW-04 | Post-Record Helix Webhook | API-only | operator-wl-webhook | Yes (P0) | Derived | Depends FM-OPW-05 attribution | HMAC signature; retry on fail |
| FM-OPW-05 | WlNetSent Scanner | API-only | operator-wl-scanner | Yes (P0) | Derived | FM-WLC-01 Phase 2 deploy needed | Zero-loss; reorg detection |
| FM-OPW-06 | Reconcilers | API-only | operator-wl-reconciler | Yes (P1) | Derived | -- | backoff 5/30/300/1800s, max 20 |
| FM-OPW-07 | fee_collections Exclusion | API-only | operator-wl-fee-exclusion | Yes (P0) | Derived | -- | Parallel Phase 1; prevent double-count |

### WL Smart Contracts

| Feature ID | Feature name | Mapped screens | Folder alias(es) | In scope? | Site map status | Gaps | Regression notes |
|---|---|---|---|---|---|---|---|
| FM-WLC-01 | WL Contract Upgrades A-K | API-only (on-chain) | wl-contracts | Yes (P0) | Derived | zen deploys; need ABI+address | 11 changes A-K; Phase 2 |

---

## Unmapped screens
Khong co man hinh nao ma khong the map duoc toi feature. Tat ca SCR-* va OP-XB-* da duoc map.

## Handoff notes
- PTL-01 va PTL-06 la OOS (Helix scope) -- KHONG tao dashboard row cho cac FM-WLA-* va FM-MOB-*.
- PTL-04 khong co man hinh; toan bo test la logic/API.
- Phase 0 gate chua pass -- ExBot integration test bi block.
- NV-3, NV-12 chua duoc confirm -- anh huong test design cho hedge-sync va LP calc.

