# QC Site Map: Bonanzapool

**Trạng thái:** Draft  
**Mode:** Initialization  
**Ngày tạo/cập nhật:** 2026-06-15  
**Người chuẩn bị:** QC Site Map Agent  
**Người review:** QC Lead  
**Baseline:** `project-context-master.md`  
**Mục đích:** Cung cấp bản đồ site/screen/navigation theo góc nhìn QC để hỗ trợ review spec, thiết kế scenario/test case, đánh giá impact, regression và verify bug.

> File này là screen-first QC site map.  
> File này không thay thế `project-context-master.md`, feature list, spec, wireframe, API doc hoặc `qc-dashboard.md`.

---

## 1. Metadata

| Thuộc tính | Giá trị |
|---|---|
| Project / Product | Bonanzapool — BNZA Ecosystem |
| Platform | Web (CF Pages / Vercel) + API-only Backend (CF Workers) |
| Source baseline | `project-context-master.md` (2026-06-15) |
| Site map readiness | Partial — ADMIN/POOL/EX screen details cần wireframe; EXBOT backend-only (no UI screens) |
| Source quality | Mixed — feature-map.md + backbone.md (official); screen tree Derived từ navigation schema + feature descriptions |
| Dashboard relationship | Feature-level handoff only |
| Ghi chú | PTL-01 (WL Mobile) và PTL-06 (WL Admin) = OOS Helix — liệt kê tham khảo, không tạo test cases |

---

## 2. Sources consolidated

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | project-context-master.md | no-version | Project baseline | 2026-06-15 |
| 2 | feature-map.md (02_backbone) | no-version | Feature index / Portal registry / Actor registry | 2026-06-15 |
| 3 | backbone.md (02_backbone) | no-version | Navigation schema / Permissions / Feature map / Dependency graph | 2026-06-15 |
| 4 | backbone-index.md (02_backbone) | no-version | Section navigator / trace anchors | 2026-06-15 |
| 5 | common-rules.md (02_backbone) | no-version | Business rules BR-MOB/EX/PL/ADM/WLA | 2026-06-15 |
| 6 | exbot/usecases/index.md | no-version | Use case index — UC-EXBOT-* | 2026-06-15 |
| 7 | exbot/srs/spec.md | no-version | SRS EXBOT — FR-EXBOT-* | 2026-06-15 |

---

## 3. Site / Portal / App overview

| Portal ID | Site / Portal / App | Mục đích | Nhóm user chính | Navigation schema | Sotatek? |
|---|---|---|---|---|---|
| PTL-01 **[OOS — Helix]** | wl.bnza.io — WL Mobile | Mobile PWA: SIWE auth, reward, claim USDC, bot ops, community | ACT-03 WL End User | Bottom tab: Home / Bot / Earnings / Settings | ❌ |
| PTL-02 | ops.bnza.io — BNZA-ADMIN | Admin: WL partner mgmt, PF, IB, bot config, dashboard, system | ACT-04 Admin (zen) | Sidebar: Dashboard / WL Partners / PF Distribution / IB / Bot Config / TOKEN / System / Reports | ✅ |
| PTL-03 | ex.bnza.io — BNZA-EX | Perps trading (Hyperliquid direct) + TradingView | ACT-01, ACT-05 | Top nav: Chart / Trade / Positions / History | ✅ |
| PTL-04 | api.bnza.io/exbot — BNZA-EXBOT Infra | Backend bot engine (no UI — API-only) | ACT-06 OPERATOR (System) | N/A — CF Workers API endpoints | ✅ |
| PTL-05 | pool.bnza.io — BNZA-POOL | LP bot management Steps 7-8: multi-bot, earnings, chain switch | ACT-01, ACT-04 | Top nav: Dashboard / AI Bot / Portfolio / Settings | ✅ |
| PTL-06 **[OOS — Helix]** | wl-admin.bnza.io — WL Admin | Daily MLM distribution ops, reward computation, on-chain payout | ACT-07 WL Operator Admin | Sidebar: Dashboard / Distribution Jobs / Users / Referral Tree / Distributor Contract / Reward Settings / Admins & Auth | ❌ |

---

## 4. Screen-first site map tree

```text
Bonanzapool — BNZA Ecosystem
│
├── PTL-02: BNZA-ADMIN (ops.bnza.io) [Auth: Wallet + CF Access]
│   ├── /dashboard                    → SCR-ADM-01 Dashboard
│   ├── /wl-partners                  → SCR-ADM-02 WL Partners List
│   │   ├── [Modal] New/Edit Partner  → SCR-ADM-02a
│   │   ├── /wl-partners/:id/members  → SCR-ADM-02b Member Lifecycle
│   │   └── /wl-partners/:id/wallets  → SCR-ADM-02c Master Wallets
│   ├── /wl-bot-monitor               → SCR-ADM-03 WL Bot Lifecycle Monitor
│   ├── /pf-distribution              → SCR-ADM-04 PF Distribution
│   ├── /ib-management                → SCR-ADM-05 IB Management
│   ├── /bot-type-config              → SCR-ADM-06 Bot Type Config
│   ├── /users                        → SCR-ADM-07 User Management
│   ├── /token-management             → SCR-ADM-08 TOKEN Management
│   ├── /system-settings              → SCR-ADM-09 System Settings
│   ├── /relayer-monitor              → SCR-ADM-10 Relayer Monitor
│   └── /reports                      → SCR-ADM-11 Reports
│
├── PTL-03: BNZA-EX (ex.bnza.io) [Auth: Wallet direct HL]
│   ├── /chart                        → SCR-EX-01 TradingView Chart
│   ├── /trade                        → SCR-EX-02 Order Placement Panel
│   ├── /positions                    → SCR-EX-03 Open Positions & PnL
│   └── /history                      → SCR-EX-04 Order History
│
├── PTL-04: BNZA-EXBOT Infra (api.bnza.io/exbot) [No UI — Backend API]
│   ├── POST /api/exbot/start         → API-XB-01 Bot Start
│   ├── GET  /api/exbot/status        → API-XB-02 Bot Status
│   ├── POST /api/exbot/close         → API-XB-03 Bot Close
│   ├── POST /api/exbot/agent-key     → API-XB-04 Agent Key Submit
│   ├── POST /api/exbot/margin        → API-XB-05 Margin Adjustment
│   ├── [Queue] bot-scan              → QUE-XB-01
│   ├── [Queue] light-check           → QUE-XB-02
│   ├── [Queue] hedge-sync            → QUE-XB-03
│   ├── [Queue] reconcile             → QUE-XB-04
│   ├── [Queue] deep-audit            → QUE-XB-05
│   ├── [Queue] price-near-stop-audit → QUE-XB-06
│   ├── [Queue] partial_repair        → QUE-XB-07
│   ├── [Queue] user_redeem (P=HIGH)  → QUE-XB-08
│   ├── [Queue] notification          → QUE-XB-09
│   ├── [Queue] metrics-rollup        → QUE-XB-10
│   ├── [DO] HLRateLimitDO            → DO-XB-01
│   ├── [DO] UserLockDO               → DO-XB-02
│   └── [DO] MarketDataDO             → DO-XB-03
│
├── PTL-05: BNZA-POOL (pool.bnza.io) [Auth: Wallet]
│   ├── /dashboard                    → SCR-POOL-01 Dashboard (multi-bot overview)
│   ├── /ai-bot                       → SCR-POOL-02 AI Bot Tab (Step 7 Multi-Bot Grid)
│   │   ├── BotCard (per bot)         → SCR-POOL-02a
│   │   └── [Modal] Create Bot        → SCR-POOL-02b
│   ├── /portfolio                    → SCR-POOL-03 Portfolio / Earnings
│   ├── /settings                     → SCR-POOL-04 Settings / Chain Switch
│   └── [Step 8] plan_specs mgmt      → SCR-POOL-05 Plan Specs (Admin view)
│
├── PTL-01: WL Mobile (wl.bnza.io) [OOS — Helix]
│   ├── /connect                      → [OOS] SIWE Auth / WL Gate
│   ├── /home                         → [OOS] Home Dashboard
│   ├── /bot                          → [OOS] Bot Operations
│   ├── /earnings                     → [OOS] Reward Display + Claim
│   └── /settings                     → [OOS] Settings
│
└── PTL-06: WL Admin (wl-admin.bnza.io) [OOS — Helix]
    ├── /wl-dashboard                 → [OOS] Dashboard
    ├── /wl-distribution-jobs         → [OOS] Distribution Jobs
    ├── /wl-users                     → [OOS] Users
    ├── /wl-referral-tree             → [OOS] Referral Tree
    ├── /wl-distributor-contract      → [OOS] Distributor Contract
    ├── /wl-reward-settings           → [OOS] Reward Settings
    └── /wl-admins-auth               → [OOS] Admins & Auth
```

---

## 5. Screen / Page inventory

### PTL-02 — BNZA-ADMIN

| Screen ID | Portal | Area | Screen / Page | Type | Platform | Source | Status |
|---|---|---|---|---|---|---|---|
| SCR-ADM-01 | PTL-02 | Dashboard | Dashboard (TVL, bot count, revenue, user count) | Dashboard | Web Admin | backbone.md §5.2 FM-ADM-05 | Derived |
| SCR-ADM-02 | PTL-02 | WL Partners | WL Partners List + Detail | Page + Modal | Web Admin | backbone.md §5.2 FM-ADM-01 | Derived |
| SCR-ADM-02a | PTL-02 | WL Partners | New/Edit Partner Modal (name, logo, referral_code, deposit_tier, wallet) | Modal | Web Admin | feature-map.md FM-ADM-01 | Derived |
| SCR-ADM-02b | PTL-02 | WL Partners | Member Lifecycle Tab (register, leaving, rejoin, epoch) | Tab | Web Admin | backbone.md §5.2 FM-ADM-01 | Derived |
| SCR-ADM-02c | PTL-02 | WL Partners | Master Wallets Tab (per-chain, rotation two-phase) | Tab | Web Admin | backbone.md §5.2 FM-ADM-01 | Derived |
| SCR-ADM-03 | PTL-02 | WL Bot Monitor | WL Bot Lifecycle Monitor (pending_set SLA, failed_set, needs_repair, force-normalize) | Page | Web Admin | feature-map.md FM-ADM-10 | Derived |
| SCR-ADM-04 | PTL-02 | PF Distribution | PF Distribution Dashboard (70/30 split, remittance trigger, history) | Page | Web Admin | feature-map.md FM-ADM-02 | Derived |
| SCR-ADM-05 | PTL-02 | IB Management | IB List + CRUD (real D1 data, commission tracking) | Page | Web Admin | feature-map.md FM-ADM-03 | Derived |
| SCR-ADM-06 | PTL-02 | Bot Config | Bot Type Config (deposit tiers, EXBOT params, cooldown 10-180 min) | Page | Web Admin | feature-map.md FM-ADM-04 | Derived |
| SCR-ADM-07 | PTL-02 | User Management | User List (wallet, role, bots count, RBAC actions) | Page | Web Admin | feature-map.md FM-ADM-11 | Derived |
| SCR-ADM-08 | PTL-02 | TOKEN | TOKEN Management (mock — burn/supply/vesting/treasury) | Page | Web Admin | feature-map.md FM-ADM-07 | Derived |
| SCR-ADM-09 | PTL-02 | System | System Settings (system_config key-value, last modified) | Page | Web Admin | feature-map.md FM-ADM-08 | Derived |
| SCR-ADM-10 | PTL-02 | System | Relayer Monitor (wallet address, ETH balance, last tx, health) | Page | Web Admin | feature-map.md FM-ADM-09 | Derived |
| SCR-ADM-11 | PTL-02 | Reports | Reports (fee collection, bot performance, user activity, date-range) | Page | Web Admin | feature-map.md FM-ADM-06 | Derived |

### PTL-03 — BNZA-EX

| Screen ID | Portal | Area | Screen / Page | Type | Platform | Source | Status |
|---|---|---|---|---|---|---|---|
| SCR-EX-01 | PTL-03 | Trading | TradingView Advanced Chart (chartingLibraryAdapter.js) | Page | Web | feature-map.md FM-EX-01 | Derived |
| SCR-EX-02 | PTL-03 | Trading | Order Placement Panel (place/cancel/modify — agent key, no MetaMask popup) | Panel/Form | Web | feature-map.md FM-EX-03 | Derived |
| SCR-EX-03 | PTL-03 | Trading | Open Positions & PnL (margin, effectiveLeverage, liquidationPx) | Page | Web | backbone.md §4.3 | Derived |
| SCR-EX-04 | PTL-03 | History | Order History | Page | Web | backbone.md §4.3 | Derived |

### PTL-04 — BNZA-EXBOT Infra (API/Backend — không có màn hình UI)

| Screen ID | Portal | Area | Endpoint / Component | Type | Platform | Source | Status |
|---|---|---|---|---|---|---|---|
| API-XB-01 | PTL-04 | OPERATOR Facade | POST /api/exbot/start | REST API | CF Workers | srs/spec.md FM-XB-06 | Confirmed |
| API-XB-02 | PTL-04 | OPERATOR Facade | GET /api/exbot/status | REST API | CF Workers | srs/spec.md FM-XB-06 | Confirmed |
| API-XB-03 | PTL-04 | OPERATOR Facade | POST /api/exbot/close | REST API | CF Workers | srs/spec.md FM-XB-06 | Confirmed |
| API-XB-04 | PTL-04 | OPERATOR Facade | POST /api/exbot/agent-key | REST API | CF Workers | srs/spec.md FM-XB-06 | Confirmed |
| API-XB-05 | PTL-04 | OPERATOR Facade | POST /api/exbot/margin | REST API | CF Workers | srs/spec.md FM-XB-06 | Confirmed |
| QUE-XB-01 | PTL-04 | Queue | bot-scan queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-02 | PTL-04 | Queue | light-check queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-03 | PTL-04 | Queue | hedge-sync queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-04 | PTL-04 | Queue | reconcile queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-05 | PTL-04 | Queue | deep-audit queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-06 | PTL-04 | Queue | price-near-stop-audit consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-07 | PTL-04 | Queue | partial_repair queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-08 | PTL-04 | Queue | user_redeem queue consumer (HIGHEST PRIORITY, SLA 5min) | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-09 | PTL-04 | Queue | notification queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| QUE-XB-10 | PTL-04 | Queue | metrics-rollup queue consumer | Queue Worker | CF Workers | srs/spec.md FM-XB-02 | Confirmed |
| DO-XB-01 | PTL-04 | Durable Object | HLRateLimitDO (sliding window 800 wt/min) | DO | CF Workers | srs/spec.md FM-XB-03 | Confirmed |
| DO-XB-02 | PTL-04 | Durable Object | UserLockDO (lease-based 90s TTL, 1-user mutex) | DO | CF Workers | srs/spec.md FM-XB-03 | Confirmed |
| DO-XB-03 | PTL-04 | Durable Object | MarketDataDO (sqrtPriceX96/tick cache) | DO | CF Workers | srs/spec.md FM-XB-03 | Confirmed |

### PTL-05 — BNZA-POOL

| Screen ID | Portal | Area | Screen / Page | Type | Platform | Source | Status |
|---|---|---|---|---|---|---|---|
| SCR-POOL-01 | PTL-05 | Dashboard | Dashboard overview (multi-bot summary, chain switch) | Dashboard | Web | feature-map.md FM-PL-01 | Derived |
| SCR-POOL-02 | PTL-05 | AI Bot | Step 7 Multi-Bot Grid (Active Bots section, max 10/chain) | Page | Web | feature-map.md FM-PL-01 | Confirmed |
| SCR-POOL-02a | PTL-05 | AI Bot | BotCard (status, invested, P&L, uptime, evaluation) | Card component | Web | common-rules.md BR-PL-23/24 | Confirmed |
| SCR-POOL-02b | PTL-05 | AI Bot | Create Bot Modal / form (chain, TVL min $1k, gas check) | Modal | Web | common-rules.md BR-PL-21/22 | Derived |
| SCR-POOL-03 | PTL-05 | Portfolio | Portfolio / Earnings (P&L, fee breakdown) | Page | Web | backbone.md §4.5 | Derived |
| SCR-POOL-04 | PTL-05 | Settings | Settings / Chain Switch (Base/OP, BR-PL-01) | Page | Web | common-rules.md BR-PL-01 | Confirmed |
| SCR-POOL-05 | PTL-05 | OPS (Admin) | Step 8 plan_specs management (version history, immutability, outdated warning) | Page (Admin-only) | Web | feature-map.md FM-PL-02 | Derived |

---

## 6. Navigation & screen flow

| Flow ID | Flow name | Role | Start screen | Main path | End screen / outcome | Related feature(s) | Notes |
|---|---|---|---|---|---|---|---|
| SFLOW-001 | Admin đăng nhập BNZA-ADMIN | ACT-04 | — | Wallet connect → CF Access verify | SCR-ADM-01 Dashboard | FM-ADM-05 | Wallet + CF Access required (zen@bnza.io) |
| SFLOW-002 | WL Partner onboarding | ACT-04 | SCR-ADM-02 WL Partners | Danh sách → New Partner → fill form → save | SCR-ADM-02 updated | FM-ADM-01 | Bao gồm member tab + master wallet tab |
| SFLOW-003 | WL Bot Force-normalize | ACT-04 | SCR-ADM-03 WL Bot Monitor | Detect failed_set → retry / force-normalize (2-phase: unset on-chain → DB NULL) | Bot status reset | FM-ADM-10 | BR-ADM-031: 2-phase không thể skip |
| SFLOW-004 | End User xem bots (POOL) | ACT-01 | SCR-POOL-01 | Connect wallet → Dashboard → AI Bot tab | SCR-POOL-02 Multi-Bot Grid | FM-PL-01 | Chain switch (Base/OP) persist localStorage |
| SFLOW-005 | Bot start flow (POOL → EXBOT) | ACT-01 | SCR-POOL-02b | Create Bot → atomic-start (3 retry) → OPERATOR proxy → ExBot API-XB-01 | Bot active | FM-XB-07 / FM-XB-09 | BR-PL-16: retry 3 lần, fatal modal nếu fail |
| SFLOW-006 | Bot stop / user redeem | ACT-01 | SCR-POOL-02a BotCard | Stop → confirm → on-chain TX → OPERATOR → QUE-XB-08 user_redeem | Bot closed, funds returned | FM-XB-08 / UC-EXBOT-user-redeem | LP-first, hedge SLA 5 min, highest priority queue |
| SFLOW-007 | Light-check cron (EXBOT auto) | ACT-06 OPERATOR | — (cron trigger) | bot-scan → QUE-XB-01 → QUE-XB-02 light-check (D1 cache, no HL call) | Rebalance enqueued or no-op | FM-XB-07 / UC-EXBOT-light-check | Zero HL calls in light-check phase |
| SFLOW-008 | Hedge-sync (delta adjustment) | ACT-06 OPERATOR | QUE-XB-02 → | QUE-XB-03 hedge-sync → UserLockDO lease → HLRateLimitDO → HL delta-only order → reconcile | D1 updated, stop replaced | FM-XB-05 / UC-EXBOT-hedge-sync | Delta-only, never full close/open |
| SFLOW-009 | Trader đặt lệnh BNZA-EX | ACT-05 | SCR-EX-01 Chart | Agent key setup → builder fee approval → SCR-EX-02 order panel → sign via agent key | Order filled on HL | FM-EX-01/02/03 | BR-EX-04: agent key ký, không MetaMask popup |
| SFLOW-010 | Admin xem System Settings | ACT-04 | SCR-ADM-09 | sidebar Settings → view key-value + last modified | SCR-ADM-09 | FM-ADM-08 | BR-ADM-028: global_bot_enabled=false dừng ngay |
| SFLOW-011 | Bot agent key submit & approve | ACT-01 / ACT-04 | — | User submit agent key → API-XB-04 → CF Secrets Store → zen approve | approval_status=approved | FM-XB-12 / UC-EXBOT-agent-key | AES-GCM envelope encryption, no raw key in D1 |

---

## 7. Role / access by screen

| Role / Actor | Accessible site/module | Accessible screen(s) | Key actions | Restriction / Rule | Source | Status |
|---|---|---|---|---|---|---|
| ACT-01 End User (LP) | PTL-03 EX, PTL-05 POOL | SCR-EX-01..04, SCR-POOL-01..04 | View charts, place orders, create/stop bot, view portfolio | Phase A: max 1 active ExBot. Max 10 bots/chain (BR-PL-11). Chains: Base/OP only (BR-PL-01). | backbone.md §3/§4 | Confirmed |
| ACT-04 Admin (zen) | PTL-02 ADMIN, PTL-04 (config), PTL-05 | SCR-ADM-01..11, API-XB-01..05 (config), SCR-POOL-05 | Full admin: WL onboarding, bot config, system settings, plan_specs mgmt, force-stop | CF Access required. `global_bot_enabled=false` → halt all bots (BR-ADM-028). | backbone.md §3/§4.2 | Confirmed |
| ACT-05 Trader | PTL-03 EX | SCR-EX-01..04 | TradingView charts, order placement, positions, history | Direct HL — không qua OPERATOR. BR-EX-06. Builder fee approval required (BR-EX-03). | backbone.md §4.3 | Confirmed |
| ACT-06 OPERATOR (System) | PTL-04 EXBOT Infra | API-XB-01..05, QUE-XB-01..10, DO-XB-01..03 | Queue processing, D1 read/write, HL calls, cron execution | Internal auth only. Không có public endpoint. Không thể transfer tài sản user ra ngoài BnzaExVault. | backbone.md §4.4 | Confirmed |
| ACT-03 WL End User **[OOS — Helix]** | PTL-01 WL Mobile | [OOS screens] | SIWE auth, bot ops, reward, claim | OOS — Helix scope. | feature-map.md §3.1 | OOS |
| ACT-07 WL Operator Admin **[OOS — Helix]** | PTL-06 WL Admin | [OOS screens] | Distribution ops, tree mgmt, payout, reconciliation | OOS — Helix scope. SSO + 2FA TOTP. | feature-map.md §3.0 | OOS |

---

## 8. Screen ↔ Feature mapping

| Screen ID | Screen / Page | Feature ID | Feature name | Mapping type | Regression anchor? | Notes |
|---|---|---|---|---|---|---|
| SCR-ADM-01 | Dashboard | FM-ADM-05 | Dashboard | Primary | Yes | KPI từ OPERATOR `/api/admin/stats`. KV cache 5min TTL. |
| SCR-ADM-02 | WL Partners List | FM-ADM-01 | WL Partner Onboarding | Primary | Yes | Bao gồm referral_code auto-gen, logo CF R2. |
| SCR-ADM-02a | New/Edit Partner Modal | FM-ADM-01 | WL Partner Onboarding | Primary | No | BR-ADM-001..007. |
| SCR-ADM-02b | Member Lifecycle Tab | FM-ADM-01 | WL Partner Onboarding | Supporting | Yes | BR-ADM-009..013. Two-phase leave. |
| SCR-ADM-02c | Master Wallets Tab | FM-ADM-01 | WL Partner Onboarding | Supporting | Yes | BR-ADM-013. Rotation two-phase. |
| SCR-ADM-03 | WL Bot Monitor | FM-ADM-10 | WL Bot Lifecycle Monitor | Primary | Yes | 6-state machine. BR-ADM-031..034. |
| SCR-ADM-04 | PF Distribution | FM-ADM-02 | PF Distribution | Primary | No | pfCollector single EOA. Off-chain tracking only. |
| SCR-ADM-05 | IB Management | FM-ADM-03 | IB Management | Primary | No | Replace mockIBs with real D1 data. |
| SCR-ADM-06 | Bot Type Config | FM-ADM-04 | Bot Type Config | Primary | Yes | EXBOT params (hedge_ratio, leverage, stop_safety_factor) — zen provides values (BR-ADM-021). |
| SCR-ADM-07 | User Management | FM-ADM-11 | User Management | Primary | No | RBAC-based. Read-only list in Phase A. |
| SCR-ADM-08 | TOKEN Management | FM-ADM-07 | TOKEN Management | Primary | No | Mock data — không có on-chain tx. |
| SCR-ADM-09 | System Settings | FM-ADM-08 | System Settings | Primary | Yes | `global_bot_enabled` flag = halt all. BR-ADM-028/029. |
| SCR-ADM-10 | Relayer Monitor | FM-ADM-09 | Relayer Monitor | Primary | No | Balance threshold alert. |
| SCR-ADM-11 | Reports | FM-ADM-06 | Reports | Primary | No | Real data, date-range queries. |
| SCR-EX-01 | TradingView Chart | FM-EX-01, FM-EX-02 | TradingView Integration + Chart Data Feed | Primary | No | chartingLibraryAdapter.js. HL WebSocket data feed. |
| SCR-EX-02 | Order Placement | FM-EX-03 | Order Placement | Primary | Yes | Agent key signs. No MetaMask popup per trade (BR-EX-04). |
| SCR-EX-03 | Positions & PnL | FM-EX-03 | Order Placement | Supporting | No | Real HL data. |
| SCR-EX-04 | Order History | FM-EX-03 | Order Placement | Supporting | No | HL API direct. |
| API-XB-01 | POST /api/exbot/start | FM-XB-06, FM-XB-07, FM-XB-09 | OPERATOR Facade + Lifecycle + Phase A1 | Primary | Yes | 5 preflight checks. FR-EXBOT-001/002/003. |
| API-XB-02 | GET /api/exbot/status | FM-XB-06 | OPERATOR Facade | Primary | No | |
| API-XB-03 | POST /api/exbot/close | FM-XB-06, FM-XB-08 | OPERATOR Facade + Close/Redeem | Primary | Yes | user_redeem LP-first. close_operations idempotency. |
| API-XB-04 | POST /api/exbot/agent-key | FM-XB-06, FM-XB-12 | OPERATOR Facade + Envelope Encryption | Primary | Yes | AES-GCM, no raw key in D1/logs. FR-EXBOT-002. |
| API-XB-05 | POST /api/exbot/margin | FM-XB-06 | OPERATOR Facade | Primary | No | |
| QUE-XB-01 | bot-scan | FM-XB-02, FM-XB-07 | Queue Topology + Lifecycle | Primary | Yes | Fan-out trigger cho light-check. |
| QUE-XB-02 | light-check | FM-XB-02, FM-XB-07 | Queue Topology + Lifecycle | Primary | Yes | Zero HL calls. D1 cache only. 8 trigger evaluation. |
| QUE-XB-03 | hedge-sync | FM-XB-02, FM-XB-05 | Queue Topology + HL Adapter | Primary | Yes | Delta-only. UserLockDO. HLRateLimitDO. |
| QUE-XB-04 | reconcile | FM-XB-02, FM-XB-05 | Queue Topology + HL Adapter | Primary | Yes | Post-order reconcile, phát hiện desync. |
| QUE-XB-05 | deep-audit | FM-XB-04 | Cron Jobs | Supporting | Yes | 6h interval. D1 ↔ HL/Uniswap full reconcile. |
| QUE-XB-08 | user_redeem (HIGHEST PRIO) | FM-XB-08 | Close/Redeem Operations | Primary | Yes | SLA 5 min. LP-first. close_operations idempotency. |
| DO-XB-01 | HLRateLimitDO | FM-XB-03 | Durable Objects | Primary | Yes | 800 wt/min budget. Sliding window. |
| DO-XB-02 | UserLockDO | FM-XB-03 | Durable Objects | Primary | Yes | 90s lease. Prevents nonce collision. |
| DO-XB-03 | MarketDataDO | FM-XB-03 | Durable Objects | Primary | Yes | sqrtPriceX96/tick cache cho light-check. |
| SCR-POOL-02 | Multi-Bot Grid (Step 7) | FM-PL-01 | Step 7 Multi-Bot | Primary | Yes | Max 10/chain. Chain switch. BR-PL-11. |
| SCR-POOL-02a | BotCard | FM-PL-01 | Step 7 Multi-Bot | Primary | Yes | Evaluation = Σ(liquidityUSD + unclaimedFeesUSD). P&L = Evaluation − invested_amount (immutable). BR-PL-23/24. |
| SCR-POOL-02b | Create Bot Modal | FM-PL-01 | Step 7 Multi-Bot | Supporting | No | Min TVL $1k (BR-PL-21). Gas reserve 0.001 ETH (BR-PL-22). |
| SCR-POOL-04 | Chain Switch Settings | FM-PL-01 | Step 7 Multi-Bot | Supporting | Yes | Base/OP only (BR-PL-01). Persist localStorage (BR-MOB-009). |
| SCR-POOL-05 | Plan Specs Mgmt (Step 8) | FM-PL-02 | Step 8 plan_specs | Primary | Yes | Simultaneous deploy POOL+OPERATOR+ADMIN. |

### Feature-level coverage summary for dashboard

| Feature ID | Feature name | Mapped screen(s) | Site map status | Gap / Note |
|---|---|---|---|---|
| FM-ADM-01 | WL Partner Onboarding | SCR-ADM-02, 02a, 02b, 02c | Partial | Wireframe chi tiết chưa có. Screen tree từ navigation schema + feature description. |
| FM-ADM-02 | PF Distribution | SCR-ADM-04 | Partial | |
| FM-ADM-03 | IB Management | SCR-ADM-05 | Partial | |
| FM-ADM-04 | Bot Type Config | SCR-ADM-06 | Partial | |
| FM-ADM-05 | Dashboard (Admin) | SCR-ADM-01 | Partial | |
| FM-ADM-06 | Reports | SCR-ADM-11 | Partial | |
| FM-ADM-07 | TOKEN Management | SCR-ADM-08 | Partial | Mock data only, P3. |
| FM-ADM-08 | System Settings | SCR-ADM-09 | Partial | |
| FM-ADM-09 | Relayer Monitor | SCR-ADM-10 | Partial | |
| FM-ADM-10 | WL Bot Lifecycle Monitor | SCR-ADM-03 | Partial | |
| FM-ADM-11 | User Management | SCR-ADM-07 | Partial | |
| FM-EX-01 | TradingView Integration | SCR-EX-01 | Partial | TradingView license cần confirm. |
| FM-EX-02 | Chart Data Feed | SCR-EX-01 | Partial | HL WebSocket feed. |
| FM-EX-03 | Order Placement | SCR-EX-02, 03, 04 | Partial | |
| FM-EX-04 | i18n (BNZA-EX) | SCR-EX-01..04 (shared) | Partial | 5 languages. BR-EX-08 (no TS). |
| FM-XB-01 | D1 Schema | — (no UI) | Mapped | Backend-only. 9 tables. |
| FM-XB-02 | Queue Topology | QUE-XB-01..10 | Mapped | 10 queues confirmed. |
| FM-XB-03 | Durable Objects | DO-XB-01..03 | Mapped | 3 DOs confirmed. |
| FM-XB-04 | Cron Jobs | QUE-XB-05 (deep-audit) | Mapped | Cron `*/360` + hourly metrics + 6h stop-integrity. |
| FM-XB-05 | HL Adapter | QUE-XB-03, QUE-XB-04 | Mapped | Rate limit, cloid, delta-only, reconcile. |
| FM-XB-06 | OPERATOR Facade API | API-XB-01..05 | Mapped | 5 endpoints confirmed. |
| FM-XB-07 | Lifecycle State Machine | API-XB-01, QUE-XB-01/02 | Mapped | 18 states. FR-EXBOT-003. |
| FM-XB-08 | Close/Redeem Operations | API-XB-03, QUE-XB-08 | Mapped | user_redeem + bot_safe_close. |
| FM-XB-09 | Phase A1 Dry Run | API-XB-01..05 | Mapped | Blocked on Phase 0 Gate (4 conditions). |
| FM-XB-12 | Envelope Encryption | API-XB-04 | Mapped | AES-GCM. No raw key. |
| FM-PL-01 | Step 7 Multi-Bot | SCR-POOL-01..04 | Partial | Navigation schema confirmed. Wireframe chi tiết chưa có. |
| FM-PL-02 | Step 8 plan_specs | SCR-POOL-05 | Partial | Simultaneous deploy với OPERATOR+ADMIN. |
| FM-OPW-01 | DB Migrations 0024–0027 | — (no UI) | Mapped | Backend only. |
| FM-OPW-02 | Ledger API | — (API) | Mapped | GET /wl/ledger/* HMAC-SHA256. |
| FM-OPW-03 | Bot API | — (API) | Mapped | POST /wl/bot/* two-phase commits. |
| FM-OPW-04 | Post-Record Webhook | — (API) | Mapped | POST to tenant wl_codes.post_record_url. |
| FM-OPW-05 | WlNetSent Scanner | — (Cron/Queue) | Mapped | Scan WlNetSent events 5 min. |
| FM-OPW-06 | Reconcilers | — (Cron) | Mapped | setBotWlMaster reconciler + wlMaster invariant. |
| FM-OPW-07 | fee_collections Exclusion | — (code change) | Mapped | 7 OPERATOR files. |
| FM-WLC-01 | WL Contract Upgrades (A–K) | — (Smart Contract) | Mapped | 11 contract changes. Phase 2. |
| FM-WLA-01..07 | WL Admin System **[OOS]** | [OOS — Helix screens] | Missing | OOS — Helix scope. Không tạo test cases. |
| FM-MOB-01..11 | WL Mobile **[OOS]** | [OOS — Helix screens] | Missing | OOS — Helix scope. Không tạo test cases. |

---

## 9. Screen ↔ Data / API / Integration / State touchpoints

| Screen / Flow | Data object / API / Integration / State | Rule / lifecycle liên quan | QC impact | Source |
|---|---|---|---|---|
| SCR-POOL-02a BotCard | `bots.status`, `positions.liquidityUSD`, `positions.unclaimedFeesUSD`, `bots.invested_amount` | BR-PL-23/24: Evaluation + P&L formula; `invested_amount` immutable sau start | Test: P&L display sau rebalance — invested_amount không được thay đổi | common-rules.md |
| SCR-POOL-04 Chain Switch | localStorage `bnza_mobile_chain`, Uniswap V3 pool per-chain | BR-PL-01: chỉ Base/OP; wethIndex khác nhau per-chain (SPEC v5.2.6 NV-12) | Test: switch chain → pool address + wethIndex phải thay đổi đúng | SPEC v5.2.6 §6.4 |
| API-XB-01 /start | `bots.lifecycle_state` (18 states), `bot_registry`, D1 preflight | FR-EXBOT-001/002: 1-bot policy + 5 preflight checks | Test mỗi preflight check fail → distinct error message; test khi bot đang active → reject | srs/spec.md |
| QUE-XB-02 light-check | `MarketDataDO` (sqrtPriceX96/tick), `bot_runtime_state`, D1 cache | Không gọi HL API. 8 trigger conditions. No Float (bigint) | Test: trigger evaluation với biên giá out-of-range, boundary_near | srs/spec.md |
| QUE-XB-03 hedge-sync | `UserLockDO` (lease 90s), `HLRateLimitDO` (800 wt/min), Hyperliquid REST | Delta-only. Budget cap 30%. NV-1/NV-3 phải confirm trước stop impl | Test: 2 concurrent hedge-sync cùng user → 2nd phải chờ lease; test budget cap block | srs/spec.md, SPEC v5.2.6 |
| QUE-XB-08 user_redeem | `close_operations` (idempotency ledger), BnzaExVault on-chain, Hyperliquid | LP-first. SLA 5 min hedge close. Idempotency prevents double settlement | Test: network failure giữa chừng → retry không double-settle | srs/spec.md |
| API-XB-04 agent-key | `hl_agent_keys` (encrypted in D1), CF Secrets Store | AES-GCM envelope. No plaintext key in D1/logs | Test: log output không có raw key; test expiry → preflight reject | srs/spec.md, SPEC v5.2.6 §21.5 |
| SCR-ADM-09 System Settings | `system_config` key-value D1, OPERATOR API | BR-ADM-028: `global_bot_enabled=false` halt all immediately | Test: flip flag → verify all bot processing stops; BR-ADM-029: `safe_mode=true` requires zen approval | common-rules.md |
| SCR-ADM-03 WL Bot Monitor | `wl_activation_status`, `wl_members` D1, on-chain wlMaster | BR-ADM-031: force-normalize 2-phase (unset on-chain → DB NULL). BR-ADM-033: auto-normalize >48h | Test: stuck failed_set >48h → auto-normalize triggered; test 2-phase constraint | common-rules.md |
| SCR-EX-02 Order Placement | HL API (direct), agent key, builder fee | BR-EX-04: agent key ký, no MetaMask. BR-EX-03: builder fee approval required before first trade | Test: first trade without builder fee approval → blocked; test agent key flow | common-rules.md |

---

## 10. Regression / impact anchors

| Anchor | Type | Related feature(s) | Related screen(s) | Vì sao quan trọng | Suggested regression focus |
|---|---|---|---|---|---|
| Bot Lifecycle State Machine (18 states) | Core flow | FM-XB-07 | API-XB-01, QUE-XB-01/02 | Sai state transition → bot bị kẹt hoặc tài sản user bị lock | Test toàn bộ state transitions: idle→active, active→safe_mode, active→closed. Test illegal transitions. |
| UserLockDO lease mechanism | Shared component | FM-XB-03 | QUE-XB-03, QUE-XB-04, QUE-XB-08 | Nếu lock fail → nonce collision trên HL subaccount → order lỗi | Test concurrent hedge-sync cùng user. Test lease expiry và renewal. |
| HLRateLimitDO sliding window | Integration | FM-XB-03 | QUE-XB-03 | Vượt 800 wt/min → HL rate limit error → cascade rebalance fail | Test: load 10 bots cùng lúc, verify không vượt budget. Test throttle retry. |
| user_redeem queue (HIGHEST PRIO) | Core flow | FM-XB-08 | QUE-XB-08, API-XB-03 | LP-first SLA 5 min — nếu miss → user funds locked | Test: user_redeem luôn được process trước hedgesync khi queue đầy. Test SLA timeout. |
| BotCard Evaluation + P&L display | Data state | FM-PL-01 | SCR-POOL-02a | `invested_amount` immutable — nếu sai → user thấy P&L sai, trust issue | Test P&L sau mỗi rebalance: E = Σ(liqUSD + feesUSD), P&L = E - invested_amount bất biến. |
| global_bot_enabled System Setting | Permission | FM-ADM-08 | SCR-ADM-09 | Kill switch toàn hệ thống — sai state → dừng nhầm hoặc không dừng được | Test toggle flag → verify immediate halt. Test UI acknowledgment dialog cho safe_mode. |
| WL Bot force-normalize 2-phase | Core flow | FM-ADM-10 | SCR-ADM-03 | Nếu skip unset on-chain → bot stop sẽ gửi net đến sai master wallet | Test: không thể set DB=NULL trước khi confirm wlMaster[tokenId]==0 on-chain. |
| agent-key encryption / no plaintext | Security | FM-XB-12 | API-XB-04 | Raw key trong log → full HL account compromise | Test: log sanitization. Check D1 `hl_agent_keys` — phải chỉ có encrypted data, không có raw. |
| Dual-chain wethIndex (Base vs OP) | Integration | FM-XB-07, FM-PL-01 | SCR-POOL-04, API-XB-01 | Sai wethIndex → sai LP amount calc → toàn bộ hedge size sai | Test: verify wethIndex per-chain trước khi impl. Xem NV-12 (Q-012). |
| atomic-start retry (3 times) | Core flow | FM-PL-01 | SCR-POOL-02b | Full fail = fatal modal; retry không đúng → bot kẹt ở preflight | Test: 1st attempt fail → retry. 3rd fail → fatal modal. No partial bot record in D1. |

---

## 11. Gaps / conflicts / assumptions

| ID | Issue | Type | Impact to QC | Suggested owner | Priority | Status |
|---|---|---|---|---|---|---|
| GAP-001 | Không có wireframe chính thức cho PTL-02 BNZA-ADMIN | Missing | Screen tree PTL-02 hoàn toàn Derived từ navigation schema + feature desc. Có thể miss screens/modals | BA (hien.duong) | High | Open |
| GAP-002 | Không có wireframe cho PTL-05 BNZA-POOL Steps 7-8 | Missing | SCR-POOL-01..05 Derived. Chi tiết tabs, modal flows cần xác nhận | BA | Medium | Open |
| GAP-003 | PTL-04 EXBOT là backend-only — không có UI screens. Site map chỉ list API endpoints + Queues + DOs | Assumption | QC sẽ test qua API calls và D1 state inspection, không có UI để automate | QC Lead | Medium | Open |
| GAP-004 | NV-12 chưa xác nhận: pool address Base + OP và wethIndex per-chain | Missing | SCR-POOL-04 chain switch và API-XB-01 start sẽ dùng sai pool nếu wethIndex sai | BNZA (zen) — Q-012 | High | Open |
| GAP-005 | NV-1/NV-3 chưa xác nhận: §19.5 stop replacement chưa được implement | Missing | QUE-XB-03 hedge-sync: stop placement logic có thể thay đổi sau khi NV-1/NV-3 confirmed | SOTATEK Phase 0 | High | Open |
| GAP-006 | EXBOT Phase 0 Gate chưa pass — 4 điều kiện chưa đủ | Constraint | QC không thể test HL integration cho đến khi gate pass. D1 schema + Queue skeleton only. | zen / SOTATEK | High | Open |
| GAP-007 | BNZA-EX (PTL-03) viết bằng JS thuần, không có TypeScript | Assumption | Test automation khó hơn; type safety không có. BR-EX-08. | QC Lead | Low | Open |
| GAP-008 | BNZA-EX "Bots" tab là placeholder — deferred (OQ-EX-01) | Missing | SCR-EX-* không có EXBOT integration screen. Nếu cần test thì cần quyết định từ zen. | zen (BR-EX-09) | Low | Open |
| GAP-009 | Chưa có SRS/wireframe cho FM-OPW-01..07 (OPERATOR WL Backend) | Missing | API test cho WL stream 1/2/3 cần contract spec chi tiết (HMAC auth, request/response schema) | BA | Medium | Open |
| GAP-010 | Không có module BA docs cho PTL-02 BNZA-ADMIN (chỉ có feature-map.md mô tả ngắn) | Missing | Test coverage cho FM-ADM-* cần FRD/SRS của bnza-admin module | BA | High | Open |

---

## 12. Readiness assessment

| Area | Status | Reason | Required action |
|---|---|---|---|
| Screen inventory — PTL-02 ADMIN | Partial | Derived từ nav schema + feature desc. Không có wireframe chính thức. | Cần BA cung cấp wireframe/screen list cho bnza-admin. |
| Screen inventory — PTL-03 EX | Partial | Navigation schema confirmed (Chart/Trade/Positions/History). Feature desc đủ để tạo skeleton. | Xác nhận với BA chi tiết Bots tab (placeholder?). |
| Screen inventory — PTL-04 EXBOT (API-only) | Ready | API endpoints, Queues, DOs đều confirmed từ SRS spec.md. | N/A — backend test via API/D1 inspection. |
| Screen inventory — PTL-05 POOL | Partial | FM-PL-01/02 confirmed. Navigation schema có. Wireframe chi tiết Step 7/8 cần xác nhận. | BA cung cấp wireframe Step 7-8. |
| Navigation flow | Partial | Flows chính đã capture (10 flows). Chưa có chi tiết error flows ADMIN và EX. | Bổ sung error flows sau khi có wireframe. |
| Role/access by screen | Ready | Confirmed từ backbone.md §3/§4. 7 actors, 6 portals, OOS markers rõ ràng. | N/A |
| Screen-feature mapping | Ready | Tất cả Confirmed/Derived screens đều được map tới Feature ID. 37 features mapped. | Xác nhận Feature IDs với BA khi FRD hoàn thiện. |
| Data/API/integration/state touchpoints | Partial | EXBOT touchpoints rất chi tiết. ADMIN/POOL/EX ở mức vừa đủ. | Bổ sung sau khi có FRD ADMIN module. |
| Regression/impact usage | Ready | 10 anchors đã identify với regression focus cụ thể. | Review với QC Lead trước khi viết test plan. |
| Dashboard feature-level handoff | Ready | Feature-level coverage summary đầy đủ 37+ features với status. | Auto-invoke qc-dashboard-sync. |

**Kết luận:** Tạm đủ  
**Ghi chú cho QC Lead:**
1. Site map hiện tại đủ để bắt đầu test plan cho PTL-04 EXBOT Infra (API-only — sources confirmed) và PTL-05 POOL Steps 7-8.
2. PTL-02 ADMIN cần wireframe chính thức trước khi viết test scenarios chi tiết.
3. EXBOT Phase 0 Gate chưa pass — QC không test HL integration cho đến khi zen confirm 4 điều kiện.
4. Ưu tiên: (1) Theo dõi NV-1/NV-3/NV-12 (Q-011/Q-012); (2) Request wireframe BA cho ADMIN; (3) Confirm wethIndex Base/OP với zen trước khi code EXBOT LP calc.
