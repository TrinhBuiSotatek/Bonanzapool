# QC Site Map: BNZA Ecosystem

**Ngay tao:** 2026-06-30
**Nguoi chuan bi:** QC Site Map Agent
**Nguoi review:** QC Lead / Trinh.Bui
**Version:** v1

---

## 1. Tong quan (Metadata)

| Hang muc | Noi dung |
|---|---|
| Mode | Initialization |
| Chat luong nguon site map | Derived (khong co wireframe chinh thuc; suy luan tu project-context-master.md + feature-map.md + backbone.md) |
| Muc do san sang | Partial — PTL-04 la API-only/backend (khong co man hinh); PTL-01/PTL-06 la OOS (Helix) |
| Baseline | project-context-master.md (2026-06-30) |
| Quan he qc-dashboard.md | Site map nay la nguon feature list cho qc-dashboard-sync (top-down mode) |
| Quan he qc-data-map.md | Data/state touchpoints tom tat o Section 9; chi tiet entity/lifecycle xem qc-data-map.md |

---

## 2. Nguon da tham khao (Sources consolidated)

| # | File | Version | Loai | Ghi chu |
|---|---|---|---|---|
| 1 | project-context-master.md | Khong co version (edit in-place) | Context tong quan du an | Baseline chinh |
| 2 | feature-map.md | Khong co version | Portal/actor registry, feature index | Nguon portal + FM-* IDs |
| 3 | backbone.md | Khong co version | Kien truc, business rules, behavioral rules | Nguon flow + constraint |
| 4 | project-config.md | v1 | Cau hinh du an | Domain, description |

---

## 3. Tong quan he thong / portal / app

| Portal ID | Ten/domain | Loai | Module chinh | Actor chinh | Pham vi |
|---|---|---|---|---|---|
| PTL-01 | wl.bnza.io (TBD) | PWA Mobile | SIWE Auth, Reward, Claim, Bot Ops, LP Status, Community, Branding | ACT-03 (WL End User) | **OOS — Helix scope** |
| PTL-02 | ops.bnza.io | Web Admin | WL Partner, PF, IB, Bot Config, Audit Log, User Mgmt, Reports | ACT-04 (Admin/zen) | Sotatek scope |
| PTL-03 | ex.bnza.io | Web Trading | TradingView, Order, Positions | ACT-05 (Trader) | Sotatek scope; P2 |
| PTL-04 | api.bnza.io | Backend / API | ExBot Worker, 10 queues, 3 Durable Objects, cron jobs | ACT-06 (OPERATOR System) | Sotatek scope; khong co UI |
| PTL-05 | pool.bnza.io | Web App | Multi-bot grid, plan_specs, Portfolio | ACT-01 (End User) | Sotatek scope |
| PTL-06 | wl-admin.bnza.io (TBD) | Web Admin | Distribution Jobs, Referral Tree, Distributor Contract, Reward Settings | ACT-07 (WL Operator Admin) | **OOS — Helix scope** |

> **Luu y QC:** PTL-01 va PTL-06 la OOS — Helix scope. QC chi test phia BNZA OPERATOR API ma Helix goi vao. PTL-04 khong co man hinh UI; tat ca test la logic/API.


---

## 4. Cay man hinh (Screen-first tree)

```
BNZA Ecosystem
|
|-- PTL-02: BNZA-ADMIN (ops.bnza.io)
|   |-- [LOGIN] Xac thuc Admin (Wallet + CF Access)
|   |-- Dashboard (tong quan TVL, bots, revenue, user count)
|   |-- WL Management
|   |   |-- Danh sach WL Partner
|   |   |-- Tao / chinh sua / vo hieu hoa WL Partner
|   |   |-- Xem thu nhap partner + lich su payout
|   |-- PF Distribution
|   |   |-- Dashboard phan phoi PF (70/30)
|   |   |-- Lich su chi tra PF
|   |-- IB Management
|   |   |-- Danh sach IB
|   |   |-- Tao / sua / xoa IB
|   |-- Bot Type Config
|   |   |-- Danh sach bot type
|   |   |-- Cau hinh strategy, tier, limit, cooldown
|   |-- WL Bot Lifecycle Monitor
|   |   |-- Theo doi wl_activation_status backlog
|   |   |-- Retry-set / force-normalize bot
|   |-- User Management
|   |   |-- Danh sach user + wallet + role
|   |-- Audit Log Viewer
|   |   |-- Tim kiem / loc audit log (to 90 ngay)
|   |   |-- Chi tiet old/new values
|   |-- Reports
|   |   |-- Fee collection report
|   |   |-- Bot performance report
|   |   |-- User activity report
|   |-- System Settings
|   |   |-- system_config, allowed/blocked addresses
|   |-- Relayer Monitor
|   |   |-- Trang thai relayer, balance, nonce, health
|   |-- TOKEN Management (mock, P3)
|
|-- PTL-03: BNZA-EX (ex.bnza.io)
|   |-- [LOGIN] Ket noi vi (Wallet direct)
|   |-- TradingView Chart
|   |   |-- Chart voi datafeed Hyperliquid WebSocket
|   |   |-- Click-to-trade, TP/SL lines
|   |-- Trade Panel
|   |   |-- Dat lenh perpetual
|   |-- Positions / History
|
|-- PTL-04: BNZA-EXBOT Infra (api.bnza.io) -- BACKEND ONLY, KHONG CO UI
|   |-- [API] POST /api/exbot/start
|   |-- [API] POST /api/exbot/stop
|   |-- [API] POST /api/exbot/pause
|   |-- [API] POST /api/exbot/resume
|   |-- [API] GET /api/exbot/status
|   |-- [API] POST /api/exbot/agent-key-approval
|   |-- [API] POST /api/exbot/margin-deposit-confirmed
|   |-- [Queue] bot-start / bot-stop / hedge-sync / user-redeem / light-check / notification (+ DLQ)
|   |-- [Cron] deep-audit / metrics-rollup / stop-integrity-scan
|   |-- [DO] HLRateLimitDO / UserLockDO / MarketDataDO
|
|-- PTL-05: BNZA-POOL (pool.bnza.io)
|   |-- [LOGIN] Wallet connect
|   |-- Dashboard (tong quan bots, P&L, TVL)
|   |-- AI Bot / Multi-Bot Grid
|   |   |-- Danh sach bots per chain (max 10/chain)
|   |   |-- Tao / start / stop bot
|   |   |-- BotCard: trang thai, P&L, LP range
|   |-- Portfolio
|   |   |-- Tong hop vi tri, P&L, lich su
|   |-- Plan Specs Management
|   |   |-- Version management plan_specs
|   |   |-- Canh bao outdated
|   |-- Settings
|   |   |-- Cau hinh account
|   |-- /buy (Banxa Fiat On-Ramp -- mock, P3)
|
|-- PTL-01: WL Mobile -- OOS (Helix scope, tham khao)
|   |-- [Ghi chu: Helix build; QC chi test OPERATOR API contract phia BNZA]
|
|-- PTL-06: WL Admin System -- OOS (Helix scope, tham khao)
    |-- [Ghi chu: Helix build; QC chi test OPERATOR Ledger/Bot API phia BNZA]
```

---

## 5. Kiem ke man hinh (Screen inventory)

> **Luu y:** Khong co wireframe chinh thuc. Tat ca man hinh duoi day la `Derived` tu feature-map.md + backbone.md. PTL-04 la API-only, khong co man hinh.

### PTL-02 — BNZA-ADMIN

| SCR ID | Ten man hinh | Loai | Trang thai | Nguon |
|---|---|---|---|---|
| SCR-ADM-001 | Xac thuc Admin | Page (Login/Auth) | Derived | feature-map.md PTL-02 nav + backbone.md §8 auth |
| SCR-ADM-002 | Dashboard Admin | Page | Derived | FM-ADM-05 |
| SCR-ADM-003 | Danh sach WL Partner | Page | Derived | FM-ADM-01 |
| SCR-ADM-004 | Tao / chinh sua WL Partner | Form/Modal | Derived | FM-ADM-01 |
| SCR-ADM-005 | Thu nhap partner + payout history | Page/Tab | Derived | FM-ADM-01 |
| SCR-ADM-006 | PF Distribution Dashboard | Page | Derived | FM-ADM-02 |
| SCR-ADM-007 | Lich su chi tra PF | Page/Tab | Derived | FM-ADM-02 |
| SCR-ADM-008 | Danh sach IB | Page | Derived | FM-ADM-03 |
| SCR-ADM-009 | Tao / sua / xoa IB | Form/Modal | Derived | FM-ADM-03 |
| SCR-ADM-010 | Bot Type Config List | Page | Derived | FM-ADM-04 |
| SCR-ADM-011 | Cau hinh Bot Type (edit form) | Form/Modal | Derived | FM-ADM-04 |
| SCR-ADM-012 | WL Bot Lifecycle Monitor | Page | Derived | FM-ADM-10 |
| SCR-ADM-013 | User Management List | Page | Derived | FM-ADM-11 |
| SCR-ADM-014 | Audit Log Viewer | Page | Derived | FM-ADM-12 |
| SCR-ADM-015 | Audit Log Detail | Page/Modal | Derived | FM-ADM-12 |
| SCR-ADM-016 | Reports | Page | Derived | FM-ADM-06 |
| SCR-ADM-017 | System Settings | Page | Derived | FM-ADM-08 |
| SCR-ADM-018 | Relayer Monitor | Page | Derived | FM-ADM-09 |
| SCR-ADM-019 | TOKEN Management | Page | Derived | FM-ADM-07 |

### PTL-03 — BNZA-EX

| SCR ID | Ten man hinh | Loai | Trang thai | Nguon |
|---|---|---|---|---|
| SCR-EX-001 | Ket noi vi (Login/Auth) | Page | Derived | PTL-03 nav, backbone.md §8 |
| SCR-EX-002 | TradingView Chart + Trade Panel | Page (chu yeu) | Derived | FM-EX-01, FM-EX-02, FM-EX-03 |
| SCR-EX-003 | Positions / History | Page/Tab | Derived | FM-EX-03 scope |

### PTL-04 — BNZA-EXBOT (API-only, khong co man hinh)

> PTL-04 la backend/API — khong co man hinh nguoi dung. Lieu ket qua kiem thu la logic, API response, trang thai D1/queue/DO.

| Op ID | API / Queue / Cron / DO | Loai | Trang thai | Nguon |
|---|---|---|---|---|
| OP-XB-001 | POST /api/exbot/start | API endpoint | Derived | FM-XB-06, FM-XB-08 |
| OP-XB-002 | POST /api/exbot/stop | API endpoint | Derived | FM-XB-06, FM-XB-08 |
| OP-XB-003 | POST /api/exbot/pause | API endpoint | Derived | FM-XB-06, FM-XB-08 |
| OP-XB-004 | POST /api/exbot/resume | API endpoint | Derived | FM-XB-06, FM-XB-08 |
| OP-XB-005 | GET /api/exbot/status | API endpoint | Derived | FM-XB-06, FM-XB-08 |
| OP-XB-006 | POST /api/exbot/agent-key-approval | API endpoint | Derived | FM-XB-06, FM-XB-08 |
| OP-XB-007 | Queue: bot-start worker | Queue processor | Derived | FM-XB-02, backbone.md FLOW-001 |
| OP-XB-008 | Queue: hedge-sync worker | Queue processor | Derived | FM-XB-02, FLOW-002 |
| OP-XB-009 | Queue: user-redeem worker | Queue processor | Derived | FM-XB-02, FLOW-003 |
| OP-XB-010 | Queue: bot-stop / bot-safe-close workers | Queue processor | Derived | FM-XB-02, FLOW-004 |
| OP-XB-011 | Queue: light-check worker | Queue processor | Derived | FM-XB-02, backbone.md §8.9.6 |
| OP-XB-012 | Queue: notification worker | Queue processor | Derived | FM-XB-02 |
| OP-XB-013 | Cron: deep-audit (*/360 min) | Cron job | Derived | FM-XB-04 |
| OP-XB-014 | Cron: metrics-rollup (hourly) | Cron job | Derived | FM-XB-04 |
| OP-XB-015 | Cron: stop-integrity-scan (6h) | Cron job | Derived | FM-XB-04 |
| OP-XB-016 | DO: HLRateLimitDO | Durable Object | Derived | FM-XB-03 |
| OP-XB-017 | DO: UserLockDO | Durable Object | Derived | FM-XB-03 |
| OP-XB-018 | DO: MarketDataDO | Durable Object | Derived | FM-XB-03 |

### PTL-05 — BNZA-POOL

| SCR ID | Ten man hinh | Loai | Trang thai | Nguon |
|---|---|---|---|---|
| SCR-PL-001 | Ket noi vi (Wallet connect) | Page | Derived | PTL-05 nav, backbone.md |
| SCR-PL-002 | Dashboard / Home | Page | Derived | PTL-05 nav |
| SCR-PL-003 | Multi-Bot Grid / Active Bots | Page | Derived | FM-PL-01 |
| SCR-PL-004 | BotCard (trang thai + P&L) | Component tren SCR-PL-003 | Derived | FM-PL-01 |
| SCR-PL-005 | Tao Bot moi | Form/Modal | Derived | FM-PL-01 scope |
| SCR-PL-006 | Portfolio | Page | Derived | PTL-05 nav |
| SCR-PL-007 | Plan Specs Management | Page | Derived | FM-PL-02 |
| SCR-PL-008 | Settings | Page | Derived | PTL-05 nav |
| SCR-PL-009 | /buy (Fiat On-Ramp Banxa — mock) | Page | Derived | FM-PL-03 |


---

## 6. Luong dieu huong va flow man hinh

### 6.1 PTL-02 BNZA-ADMIN

```
[Wallet + CF Access] --> SCR-ADM-001 (Auth) --> Dashboard (SCR-ADM-002)
                          |
                          +-- Sidebar: WL Mgmt --> SCR-ADM-003 --> SCR-ADM-004 (Tao/Edit)
                          |                     --> SCR-ADM-005 (Earnings)
                          |
                          +-- Sidebar: PF --> SCR-ADM-006 --> SCR-ADM-007
                          +-- Sidebar: IB --> SCR-ADM-008 --> SCR-ADM-009
                          +-- Sidebar: Bots --> SCR-ADM-010 --> SCR-ADM-011
                          +-- Sidebar: WL Bot Monitor --> SCR-ADM-012 (action: retry-set / force-normalize)
                          +-- Sidebar: Users --> SCR-ADM-013
                          +-- Sidebar: Audit Log --> SCR-ADM-014 --> SCR-ADM-015 (detail)
                          +-- Sidebar: Reports --> SCR-ADM-016
                          +-- Sidebar: Settings --> SCR-ADM-017
                          +-- Sidebar: Relayer --> SCR-ADM-018
```

### 6.2 PTL-05 BNZA-POOL

```
[Wallet connect] --> SCR-PL-001 --> SCR-PL-002 (Dashboard)
                       |
                       +-- Top nav: AI Bot --> SCR-PL-003 (Multi-Bot Grid)
                       |                     --> SCR-PL-004 (BotCard)
                       |                     --> SCR-PL-005 (Tao Bot)
                       +-- Top nav: Portfolio --> SCR-PL-006
                       +-- Top nav: Settings --> SCR-PL-008
                       +-- /buy --> SCR-PL-009 (Banxa mock)
                       +-- Plan Specs --> SCR-PL-007
```

### 6.3 Flow he thong cap project (cross-portal)

| Flow ID | Mo ta | Man hinh / Entry point | Portal |
|---|---|---|---|
| FLOW-001 | LP Bot Start (ExBot) | SCR-PL-005 (hoac Admin goi API) --> OP-XB-001 (POST /start) --> Queue bot-start --> HL hedge | PTL-05 / PTL-04 |
| FLOW-002 | Hedge Sync | OP-XB-008 (queue hedge-sync) --> HL API delta adjust --> D1 update | PTL-04 internal |
| FLOW-003 | User Redeem | BnzaExVault on-chain redeem event --> OP-XB-009 (user-redeem queue) --> LP close + fund return + hedge close async | PTL-04 / on-chain |
| FLOW-004 | Bot Safe Close | Admin action hoac auto trigger --> OP-XB-010 (bot-safe-close) --> HL close --> LP close --> RedemptionQueue | PTL-02 (trigger) / PTL-04 |
| FLOW-005 | WL MLM Distribution | Helix cron goi BNZA OPERATOR Ledger API --> tinh reward --> phan phoi qua RewardDistributor | OOS Helix / PTL-04 backend |
| FLOW-006 | WL Partner Onboarding | SCR-ADM-003/004 --> OPERATOR API --> wl_code active --> setBotWlMaster on-chain via Relayer | PTL-02 / PTL-04 backend |

---

## 7. Quyen truy cap theo man hinh va role

| Portal | Man hinh | ACT-01 (End User) | ACT-02 (WL Partner) | ACT-04 (Admin/zen) | ACT-05 (Trader) | ACT-06 (OPERATOR) | Ghi chu |
|---|---|---|---|---|---|---|---|
| PTL-02 | Tat ca SCR-ADM-* | - | - | Read/Write (RBAC: super_admin/admin/viewer) | - | - | Cloudflare Access + Wallet; Audit Log Viewer append-only |
| PTL-03 | SCR-EX-001/002/003 | Read (chart) | - | - | Read/Write (vi direct HL) | - | P2; wallet direct HL, khong qua OPERATOR |
| PTL-04 | Tat ca OP-XB-* | - | - | Write (API triggers) | - | Internal (service binding) | Khong co public API; ExBot goi qua OPERATOR |
| PTL-05 | SCR-PL-001 den 009 | Read/Write (bots, portfolio) | - | Read (config admin) | - | - | Wallet connect; max 10 bots/chain |

**Luu y quyen dac biet:**
- `X-Wallet-Address` header (khong signature) la auth chinh cho POOL va BNZA-ADMIN --> OPERATOR.
- Helix server goi BNZA OPERATOR qua HMAC-SHA256 cho `/api/wl/*` va bot start/stop webhooks.
- BNZA-ADMIN them Cloudflare Access (zen@bnza.io) ngoai wallet.
- Audit Log: append-only, moi writes BNZA-ADMIN yeu cau reason note + Slack audit mirror.

---

## 8. Man hinh - Feature mapping

> Moi man hinh co trang thai Confirmed/Derived phai duoc map den Feature/UC ID. SCR PTL-04 la logic operation (khong co man hinh).

### PTL-02 — BNZA-ADMIN

| SCR ID | Ten man hinh | Feature ID | Feature name | Folder alias | In scope? | Site map status |
|---|---|---|---|---|---|---|
| SCR-ADM-001 | Auth Admin | FM-ADM-01 (auth prerequisite) | WL Partner Onboarding | bnza-admin-auth | Yes | Derived |
| SCR-ADM-002 | Dashboard Admin | FM-ADM-05 | Dashboard | bnza-admin-dashboard | Yes (P2) | Derived |
| SCR-ADM-003 | Danh sach WL Partner | FM-ADM-01 | WL Partner Onboarding | bnza-admin-wl-partner | Yes (P0) | Derived |
| SCR-ADM-004 | Tao/chinh sua WL Partner | FM-ADM-01 | WL Partner Onboarding | bnza-admin-wl-partner | Yes (P0) | Derived |
| SCR-ADM-005 | Earnings + payout WL | FM-ADM-01 | WL Partner Onboarding | bnza-admin-wl-partner | Yes (P0) | Derived |
| SCR-ADM-006 | PF Distribution | FM-ADM-02 | PF Distribution | bnza-admin-pf | Yes (P0) | Derived |
| SCR-ADM-007 | Lich su PF | FM-ADM-02 | PF Distribution | bnza-admin-pf | Yes (P0) | Derived |
| SCR-ADM-008 | IB List | FM-ADM-03 | IB Management | bnza-admin-ib | Yes (P1) | Derived |
| SCR-ADM-009 | IB Form | FM-ADM-03 | IB Management | bnza-admin-ib | Yes (P1) | Derived |
| SCR-ADM-010 | Bot Type List | FM-ADM-04 | Bot Type Config | bnza-admin-bot-type | Yes (P1) | Derived |
| SCR-ADM-011 | Bot Type Edit | FM-ADM-04 | Bot Type Config | bnza-admin-bot-type | Yes (P1) | Derived |
| SCR-ADM-012 | WL Bot Lifecycle Monitor | FM-ADM-10 | WL Bot Lifecycle Monitor | bnza-admin-wl-bot-monitor | Yes (P1) | Derived |
| SCR-ADM-013 | User Management | FM-ADM-11 | User Management | bnza-admin-users | Yes (P1) | Derived |
| SCR-ADM-014 | Audit Log List | FM-ADM-12 | Audit Log Viewer | bnza-admin-audit-log | Yes (P0) | Derived |
| SCR-ADM-015 | Audit Log Detail | FM-ADM-12 | Audit Log Viewer | bnza-admin-audit-log | Yes (P0) | Derived |
| SCR-ADM-016 | Reports | FM-ADM-06 | Reports | bnza-admin-reports | Yes (P2) | Derived |
| SCR-ADM-017 | System Settings | FM-ADM-08 | System Settings | bnza-admin-settings | Yes (P2) | Derived |
| SCR-ADM-018 | Relayer Monitor | FM-ADM-09 | Relayer Monitor | bnza-admin-relayer | Yes (P2) | Derived |
| SCR-ADM-019 | TOKEN Management | FM-ADM-07 | TOKEN Management | bnza-admin-token | Yes (P3/mock) | Derived |

### PTL-03 — BNZA-EX

| SCR ID | Ten man hinh | Feature ID | Feature name | Folder alias | In scope? | Site map status |
|---|---|---|---|---|---|---|
| SCR-EX-001 | Auth EX (wallet direct) | FM-EX-01 (prerequisite) | TradingView Integration | bnza-ex-auth | Yes (P2) | Derived |
| SCR-EX-002 | Chart + Trade Panel | FM-EX-01, FM-EX-02, FM-EX-03 | TradingView, Chart Feed, Order Placement | bnza-ex-trading | Yes (P2) | Derived |
| SCR-EX-003 | Positions/History | FM-EX-03 | Order Placement | bnza-ex-trading | Yes (P2) | Derived |

### PTL-04 — BNZA-EXBOT (logic operations)

| Op ID | API/Queue/Cron/DO | Feature IDs | Feature name | Folder alias | In scope? | Site map status |
|---|---|---|---|---|---|---|
| OP-XB-001 | POST /api/exbot/start | FM-XB-06, FM-XB-08 | API Endpoints, OPERATOR API Exbot | exbot-api | Yes (P1) | Derived |
| OP-XB-002..006 | stop/pause/resume/status/agent-key | FM-XB-06, FM-XB-08 | API Endpoints | exbot-api | Yes (P1) | Derived |
| OP-XB-007 | Queue bot-start | FM-XB-01, FM-XB-02, FM-XB-09 | D1, Queue, Phase A1 | exbot-bot-start | Yes (P0) | Derived |
| OP-XB-008 | Queue hedge-sync | FM-XB-02, FM-XB-05 | Queue, HL Adapter | exbot-hedge-sync | Yes (P1) | Derived |
| OP-XB-009 | Queue user-redeem | FM-XB-02 | Queue Topology | exbot-user-redeem | Yes (P0) | Derived |
| OP-XB-010 | Queue bot-stop/safe-close | FM-XB-02 | Queue Topology | exbot-bot-stop | Yes (P0) | Derived |
| OP-XB-011 | Queue light-check | FM-XB-02 | Queue Topology | exbot-light-check | Yes (P0) | Derived |
| OP-XB-012 | Queue notification | FM-XB-02 | Queue Topology | exbot-notification | Yes (P1) | Derived |
| OP-XB-013..015 | Cron jobs (3) | FM-XB-04 | Cron Jobs | exbot-cron | Yes (P1) | Derived |
| OP-XB-016 | DO HLRateLimitDO | FM-XB-03 | Durable Objects | exbot-durable-objects | Yes (P0) | Derived |
| OP-XB-017 | DO UserLockDO | FM-XB-03 | Durable Objects | exbot-durable-objects | Yes (P0) | Derived |
| OP-XB-018 | DO MarketDataDO | FM-XB-03 | Durable Objects | exbot-durable-objects | Yes (P0) | Derived |

### PTL-05 — BNZA-POOL

| SCR ID | Ten man hinh | Feature ID | Feature name | Folder alias | In scope? | Site map status |
|---|---|---|---|---|---|---|
| SCR-PL-001 | Wallet connect | FM-PL-01 (prerequisite) | Step 7 Multi-Bot | bnza-pool-auth | Yes (P1) | Derived |
| SCR-PL-002 | Dashboard/Home | FM-PL-01 | Step 7 Multi-Bot | bnza-pool-dashboard | Yes (P1) | Derived |
| SCR-PL-003 | Multi-Bot Grid | FM-PL-01 | Step 7 Multi-Bot | bnza-pool-multi-bot | Yes (P1) | Derived |
| SCR-PL-004 | BotCard | FM-PL-01 | Step 7 Multi-Bot | bnza-pool-multi-bot | Yes (P1) | Derived |
| SCR-PL-005 | Tao Bot moi | FM-PL-01 | Step 7 Multi-Bot | bnza-pool-multi-bot | Yes (P1) | Derived |
| SCR-PL-006 | Portfolio | FM-PL-01 (scope) | Step 7 Multi-Bot | bnza-pool-portfolio | Yes (P1) | Derived |
| SCR-PL-007 | Plan Specs Management | FM-PL-02 | Step 8 plan_specs | bnza-pool-plan-specs | Yes (P1) | Derived |
| SCR-PL-008 | Settings | FM-PL-01 (nav) | Multi-Bot | bnza-pool-settings | Yes (P1) | Derived |
| SCR-PL-009 | /buy Banxa mock | FM-PL-03 | Fiat On-Ramp (Banxa) | bnza-pool-buy | Yes (P3/mock) | Derived |

### BNZA-OPERATOR WL Backend (backend features, khong co man hinh)

| Feature ID | Feature name | Folder alias | In scope? | Ghi chu |
|---|---|---|---|---|
| FM-OPW-01 | DB Migrations 0024-0027 | operator-wl-db | Yes (P0) | Backend-only |
| FM-OPW-02 | Ledger API | operator-wl-ledger | Yes (P0) | HMAC-SHA256; Helix pulls |
| FM-OPW-03 | Bot API | operator-wl-bot | Yes (P0) | Two-phase commit transitions |
| FM-OPW-04 | Post-Record Helix Webhook | operator-wl-webhook | Yes (P0) | Trigger sau attribution |
| FM-OPW-05 | WlNetSent Scanner | operator-wl-scanner | Yes (P0) | Cron 5 phut; zero-loss |
| FM-OPW-06 | Reconcilers | operator-wl-reconciler | Yes (P1) | backoff retry |
| FM-OPW-07 | fee_collections Exclusion | operator-wl-fee-exclusion | Yes (P0) | Parallel Phase 1 |

### WL Smart Contracts

| Feature ID | Feature name | Folder alias | In scope? | Ghi chu |
|---|---|---|---|---|
| FM-WLC-01 | WL Contract Upgrades A-K | wl-contracts | Yes (P0) | 11 contract changes; zen deploys |


---

## 9. Diem cham du lieu / API / integration / trang thai (Data/API touchpoints)

> Phan nay tom tat cac touchpoint co anh huong den kiem thu integration, chuyen trang thai, hoac regression. Chi tiet entity/lifecycle xem qc-data-map.md.

### PTL-02 — BNZA-ADMIN

| Man hinh | OPERATOR API endpoint | Entity/State lien quan | Rule / rui ro kiem thu |
|---|---|---|---|
| SCR-ADM-003/004 | POST /api/wl-partners | wl_codes, wl_members, wl_master_wallets | Tat ca writes yeu cau reason note + Slack audit mirror |
| SCR-ADM-012 | POST /api/bot-configs/:id/wl-retry-set, /wl-force-normalize | wl_activation_status (5 trang thai) | Two-phase commit; SLA pending_set; auto force-normalize 48h |
| SCR-ADM-014 | GET /api/audit-logs | audit_log | Append-only; filter toi da 90 ngay; old/new values |

### PTL-04 — BNZA-EXBOT (backend operations)

| Operation | Integration / data dependency | State machine / rule |
|---|---|---|
| Queue bot-start | HL API (open short + place stop), BnzaExVault (allocate USDC), D1 bots | bots.lifecycle_state: idle --> preflight --> ... --> active |
| Queue hedge-sync | HL API (adjustShortDelta), D1 bots/hedge_legs | Delta-only; BigDecimal; INV-STOP phai luon co stop verified |
| Queue user-redeem | BnzaExVault.redeem() (on-chain), D1 close_operations | close_operations state machine; BR-EXBOT-006: LP phat truoc |
| Queue light-check | D1 hedge_legs.margin_status (KHONG fetch HL) | Light-check HL weight = 0 -- tuyet doi |
| DO UserLockDO | TTL 90s; phai acquire truoc moi HL operation | Test TTL expiry, contention 2 worker cung luc |
| DO HLRateLimitDO | 800 wt/min budget (HL total 1200); sliding window | Test rate exceeded, backoff, retry |
| Cron stop-integrity-scan (6h) | D1 bots (lifecycle_state = active), HL API (verify stop exists) | INV-STOP invariant; auto escalation khi vi pham |

### PTL-05 — BNZA-POOL

| Man hinh | OPERATOR API | Entity / Rule |
|---|---|---|
| SCR-PL-003/004 | GET /api/bot-positions | bots table; chain filter; max 10/chain |
| SCR-PL-007 | OPERATOR migration 0008 | plan_specs version; immutability; outdated warning |

### BNZA-OPERATOR WL Backend

| Feature | Integration | Rule |
|---|---|---|
| FM-OPW-02 Ledger API | HMAC-SHA256; Helix pulls | Min disclosure: khong expose position_id / pool / token symbols; range cap 90 ngay |
| FM-OPW-05 WlNetSent Scanner | WlNetSent event on-chain (5 phut scan) | holds-first; unattributed retry max 288; zero-loss |
| FM-OPW-03 Bot API | setBotWlMaster/unsetBotWlMaster via Relayer | Two-phase commit; reconciler backoff 5/30/300/1800s |

---

## 10. Diem neo regression / impact anchors

| Muc do | Man hinh / Operation | Ly do la diem neo regression |
|---|---|---|
| CRITICAL | OP-XB-007 (bot-start queue) | Tao LP + hedge + stop; failure = user mat tien |
| CRITICAL | OP-XB-008 (hedge-sync) | INV-STOP invariant; delta-only; BigDecimal -- bat ky loi nao la critical |
| CRITICAL | OP-XB-009 (user-redeem) | BR-EXBOT-006 LP truoc; close_operations idempotency; SLA 5 phut |
| CRITICAL | OP-XB-010 (bot-safe-close) | hedge-first; LP pay unconditional; residual_hl_liability path |
| CRITICAL | OP-XB-011 (light-check) | HL weight = 0 tuyet doi; bat ky fetch HL la regression critical |
| HIGH | OP-XB-016/017/018 (3 Durable Objects) | Rate limit, lock contention, MarketData stale -- anh huong toan he thong |
| HIGH | SCR-ADM-003/004 (WL Partner Onboarding) | Ket noi den wl_code, on-chain setBotWlMaster -- cascade nhieu entity |
| HIGH | SCR-ADM-012 (WL Bot Lifecycle Monitor) | wl_activation_status 5-state; failed_set > 48h auto force-normalize |
| HIGH | SCR-ADM-014 (Audit Log Viewer) | Append-only; khong duoc sua/xoa; quyen filter |
| MEDIUM | FM-OPW-05 (WlNetSent Scanner) | Zero-loss guarantee; reorg detection |
| MEDIUM | FM-OPW-02 (Ledger API) | Min disclosure rules; HMAC auth |
| MEDIUM | SCR-PL-003/004 (Multi-Bot Grid) | Max 10/chain constraint; chain filter |
| MEDIUM | FM-OPW-03 (Bot API) | Two-phase commit cho wl transitions |

---

## 11. Khoang trong / mau thuan / gia dinh

| ID | Loai | Mo ta | Anh huong QC | Priority | Owner |
|---|---|---|---|---|---|
| GAP-001 | Khoang trong man hinh | Khong co wireframe chinh thuc cho bat ky portal nao. Tat ca man hinh la Derived tu feature-map.md + backbone.md. | Man hinh co the thieu hoac ten sai -- QC Lead nen confirm truoc khi review spec | High | QC Lead / BA |
| GAP-002 | Khoang trong environment | Test environment (staging) chua duoc confirm (OQ-8 trong project-context-master.md Q-001). PTL-04 ExBot -- khong biet URL wrangler config test. | Khong the test integration ExBot neu chua co environment | High | QC Lead / Ops |
| GAP-003 | Thieu man hinh PTL-04 | PTL-04 la API-only/backend. Khong co man hinh nguoi dung. QC phai test qua API / queue / D1 truc tiep. | Toan bo PTL-04 la logic test -- can tool (REST client, D1 direct, HL testnet) | Medium | QC Lead |
| GAP-004 | OOS scope (PTL-01/PTL-06) | Man hinh WL Mobile va WL Admin System la OOS. QC chi test OPERATOR API contract phia BNZA. | Phan biet ro rang dau la trong scope, dau chi la API contract verification | High | QC Lead |
| GAP-005 | NV-3 (stop behavior) | Chua confirm duplicate reduce-only stop behavior -- anh huong test case §19.5 hedge-sync | Test case cho INV-STOP path (b) chua thiet ke duoc | High | SOTATEK (verify voi HL) |
| GAP-006 | NV-12 (pool address, wethIndex) | Base + OP pool addresses chua confirm -- anh huong LP amount calc test | Test LP calc per chain co the sai neu wethIndex chua confirm | High | zen |
| GAP-007 | FM-ADM-13/14/15 chua co spec | Escalations Dashboard, Holds Review, Attribution History -- spec dang authoring | 3 feature nay chua the design test case | Medium | BA (hien.duong) |
| ASS-001 | Gia dinh navigation | PTL-02 Sidebar navigation duoc suy luan tu PTL-02 nav schema trong feature-map.md ("Sidebar: Dashboard / WL / PF / IB / Bots / TOKEN / Settings / Reports"). Chua co wireframe confirm. | Neu nav thay doi, screen mapping phai cap nhat | Medium | QC Lead confirm |
| ASS-002 | Gia dinh PTL-05 nav | PTL-05 top nav duoc suy luan tu PTL-05 nav schema ("Top nav: Dashboard / AI Bot / Portfolio / Settings"). | Neu nav thay doi, screen mapping phai cap nhat | Medium | QC Lead confirm |

---

## 12. Danh gia muc do san sang

| Portal / Area | Trang thai | Ly do | Viec can lam |
|---|---|---|---|
| PTL-02 BNZA-ADMIN | Partial | Man hinh Derived; FM-ADM-13/14/15 chua co spec | Confirm man hinh voi BA; cho spec FM-ADM-13/14/15 |
| PTL-03 BNZA-EX | Partial | Man hinh Derived; P2 priority | Co the test sau; confirm wireframe khi co |
| PTL-04 BNZA-EXBOT | Partial | API/queue/cron Derived; environment chua confirm; Phase 0 gate chua du | Confirm environment; Phase 0 gate pass truoc khi test integration |
| PTL-05 BNZA-POOL | Partial | Man hinh Derived | Confirm man hinh; plan_specs migration 0008 chua deploy |
| OPERATOR WL Backend | Partial | Feature Derived tu feature-map; contract FM-WLC-01 chua deploy | Cho Phase 2 contract deploy; confirm HMAC test key |
| WL Smart Contracts | Partial | zen deploy; SOTATEK integrate against ABI | Can ABI + testnet address truoc khi test integration |

**Ket luan tong the:** Site map san sang o muc **Partial**. Du de qc-dashboard-sync tao feature list va QC Lead bat dau review spec cac module P0/T0. Chua san sang de test integration ExBot end-to-end vi Phase 0 gate chua pass va environment chua confirm.

---

## 13. Bang alias folder (Folder alias map)

> Dung de qc-dashboard-sync map folder on-disk den Feature ID chuan.

| Folder alias | Feature ID | Feature name | Portal |
|---|---|---|---|
| bnza-admin-wl-partner | FM-ADM-01 | WL Partner Onboarding | PTL-02 |
| bnza-admin-pf | FM-ADM-02 | PF Distribution | PTL-02 |
| bnza-admin-ib | FM-ADM-03 | IB Management | PTL-02 |
| bnza-admin-bot-type | FM-ADM-04 | Bot Type Config | PTL-02 |
| bnza-admin-dashboard | FM-ADM-05 | Dashboard | PTL-02 |
| bnza-admin-reports | FM-ADM-06 | Reports | PTL-02 |
| bnza-admin-token | FM-ADM-07 | TOKEN Management | PTL-02 |
| bnza-admin-settings | FM-ADM-08 | System Settings | PTL-02 |
| bnza-admin-relayer | FM-ADM-09 | Relayer Monitor | PTL-02 |
| bnza-admin-wl-bot-monitor | FM-ADM-10 | WL Bot Lifecycle Monitor | PTL-02 |
| bnza-admin-users | FM-ADM-11 | User Management | PTL-02 |
| bnza-admin-audit-log | FM-ADM-12 | Audit Log Viewer | PTL-02 |
| bnza-ex-trading | FM-EX-01, FM-EX-02, FM-EX-03, FM-EX-04 | TradingView, Chart, Order, i18n | PTL-03 |
| exbot-api | FM-XB-06, FM-XB-08 | API Endpoints, OPERATOR API | PTL-04 |
| exbot-bot-start | FM-XB-01, FM-XB-02, FM-XB-09, FM-XB-12, FM-XB-13 | D1, Queue, Phase A1, Encryption, Hotfixes | PTL-04 |
| exbot-hedge-sync | FM-XB-02, FM-XB-05 | Queue, HL Adapter | PTL-04 |
| exbot-user-redeem | FM-XB-02 | Queue Topology | PTL-04 |
| exbot-bot-stop | FM-XB-02 | Queue Topology | PTL-04 |
| exbot-light-check | FM-XB-02 | Queue Topology | PTL-04 |
| exbot-notification | FM-XB-02 | Queue Topology | PTL-04 |
| exbot-cron | FM-XB-04 | Cron Jobs | PTL-04 |
| exbot-durable-objects | FM-XB-03 | Durable Objects | PTL-04 |
| exbot-phase-progression | FM-XB-09, FM-XB-10, FM-XB-11 | Phase A1/A2/A3 | PTL-04 |
| bnza-pool-multi-bot | FM-PL-01 | Step 7 Multi-Bot | PTL-05 |
| bnza-pool-plan-specs | FM-PL-02 | Step 8 plan_specs | PTL-05 |
| bnza-pool-buy | FM-PL-03 | Fiat On-Ramp (Banxa) | PTL-05 |
| wl-contracts | FM-WLC-01 | WL Contract Upgrades A-K | Shared |
| operator-wl-db | FM-OPW-01 | DB Migrations 0024-0027 | PTL-04 backend |
| operator-wl-ledger | FM-OPW-02 | Ledger API | PTL-04 backend |
| operator-wl-bot | FM-OPW-03 | Bot API | PTL-04 backend |
| operator-wl-webhook | FM-OPW-04 | Post-Record Helix Webhook | PTL-04 backend |
| operator-wl-scanner | FM-OPW-05 | WlNetSent Scanner | PTL-04 backend |
| operator-wl-reconciler | FM-OPW-06 | Reconcilers | PTL-04 backend |
| operator-wl-fee-exclusion | FM-OPW-07 | fee_collections Exclusion | PTL-04 backend |

