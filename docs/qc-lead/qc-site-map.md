# QC Site Map: Bonanzapool (BNZA Ecosystem — SOTATEK Scope)

**Trạng thái:** Draft → Updated (Line scope split)
**Mode:** Update
**Ngày tạo/cập nhật:** 2026-06-17
**Người chuẩn bị:** QC Site Map Agent (`qc-site-map`)
**Người review:** QC Lead
**Baseline:** `project-context-master.md` (updated 2026-06-16 — Line scope split)
**Mục đích:** Cung cấp bản đồ site/screen/navigation theo góc nhìn QC. **Lưu ý:** Line 1 đã hoàn thành, Line 2 (EXBOT Infra) là phạm vi QC hoạt động duy nhất sắp tới — xem §0.

> File này là **screen-first QC site map**.
> File này không thay thế `project-context-master.md`, `feature-map.md`, spec, wireframe, API doc, DB schema hoặc `qc-dashboard.md`.
> File này bổ sung góc nhìn **SCREEN-centric** trong bộ 3 trục QC context: **project / screen / data**.

---

## 0. Chỉ thị phạm vi QC hiện tại

> **Kế thừa từ `project-context-master.md` (2026-06-16).** Xem file gốc để biết chi tiết.

| Line | Trạng thái QC | Vai trò trong site map |
|------|---------------|------------------------|
| **Line 1** (PTL-01, PTL-02, PTL-03, PTL-05, PTL-06, FM-WLC-01, FM-OPW-01→07) | ✅ **ĐÃ HOÀN THÀNH** | Screen/flow/touchpoint giữ nguyên làm **dependency context**. KHÔNG thiết kế test mới. |
| **Line 2** (PTL-04, FM-XB-01→FM-XB-13) | 🔜 **SẮP LÀM** | **Phạm vi QC hoạt động duy nhất.** Backend-only, không có screen — test integration/system. |

---

## 1. Metadata

| Thuộc tính | Giá trị |
|---|---|
| Project / Product | Bonanzapool — BNZA Ecosystem (gói SOTATEK) |
| Platform | Hỗn hợp: PWA mobile-hybrid (PTL-01) + web-responsive desktop-first (PTL-02, PTL-05, PTL-06) + plain JS web (PTL-03) + API-only backend (PTL-04) |
| Source baseline | `project-context-master.md` (2026-06-16, Updated — Line scope split) |
| Site map readiness | Partial — screen inventory dùng ASCII wireframe làm proxy cho wireframe chính thức. |
| Source quality | Derived (từ ascii-screen index + feature-map + backbone); chưa có wireframe Figma chính thức. |
| Dashboard relationship | Feature-level handoff only (`.claude/skills/qc-dashboard-sync/inbox/site-map-handoff.md`). |
| Data-map relationship | `qc-data-map.md` dùng file này làm screen baseline. |
| Phạm vi QC hiện tại | **Line 1 ĐÃ HOÀN THÀNH** — screen/flow/touchpoint Line 1 giữ nguyên làm dependency context. **Line 2 (EXBOT Infra PTL-04, FM-XB-01→13) là phạm vi QC duy nhất sắp tới** — backend-only, không có screen. |
| Ghi chú | 6 portal — PTL-01..06; 43 screen (PTL-04 không UI); 42 FM-ID; 7 actor. |

---

## 2. Sources consolidated

> Bảng này liệt kê các file đã được đọc và tổng hợp ra nội dung phía dưới. Lần chạy update sau sẽ so version trong tên file (`_v<N>`) để biết source có thay đổi hay không.

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | project-context-master.md | không có version | Project baseline (Line scope split update) | 2026-06-17 |
| 2 | feature-map.md | không có version | Feature inventory + Portal & Actor registry + Priority tier | 2026-06-08 |
| 3 | backbone.md | không có version | Architecture + Auth + Permissions + Dependency + WL+MLM 3-layer | 2026-06-08 |
| 4 | intake.md | không có version | Product brief + Scope per module + WL Mobile 3 communication partners | 2026-06-08 |
| 5 | common-rules.md | không có version | Business rules per module (BR-*) | 2026-06-08 |
| 6 | message-list.md | không có version | UI message catalog (E-*) | 2026-06-08 |
| 7 | admin/bnza-admin/ascii-screen/index.md | không có version | Screen list — 18 file (Sidebar nav) | 2026-06-08 |
| 8 | admin/wl-admin/ascii-screen/index.md | không có version | Screen list — 7 page + 9 supporting modal (Sidebar nav, PC-only ≥1280px) | 2026-06-08 |
| 9 | bnza-ex/ascii-screen/index.md | không có version | Screen list — 2 screen (Top nav `ex-topnav`) | 2026-06-08 |
| 10 | bnza-pool/ascii-screen/index.md | không có version | Screen list — 9 screen (Left sidebar `pool-sidebar`) | 2026-06-08 |
| 11 | mobile/ascii-screen/index.md | không có version | Screen list — 7 screen (Bottom tab 5 + WL Gate + Community) | 2026-06-08 |
| 12 | operator/ascii-screen/api-overview.md | không có version | API-only backend (no UI) — chỉ ghi nhận để xác định PTL-04 không có screen | 2026-06-08 |

---

## 3. Site / Portal / App overview

| Site / Portal / App | Mục đích | Nhóm user chính | Module / Area chính | Ghi chú QC |
|---|---|---|---|---|
| PTL-01 `wl.bnza.io` (TBD) — WL Mobile (BNZA-MOBILE) | App PWA cho WL End User: xem reward sau allocation, claim USDC, vận hành LP Bot, xem community/referral. | ACT-03 WL End User; ACT-02 WL Partner (view earnings). | `apps/bnza-mobile/`. Navigation `bottom-tab-5` (Home / Bot / Position / Notifications / Settings) + pre-auth WL Gate + ngoài tab Community. | Auth SIWE → JWT 24h; chain Base+OP; viewport mobile; mọi số liệu post-allocation, không hiện raw LP fees. |
| PTL-02 `ops.bnza.io` — BNZA-ADMIN | Internal management cho zen — quản lý bots, plans, WL partner, PF off-chain, IB, system settings, relayer, reports, WL Bot Lifecycle Monitor. | ACT-04 Admin (zen). | `apps/bnza-admin/`. Navigation Sidebar — 18 page (Dashboard / WL / PF / IB / Bots / TOKEN / Settings / Reports + WL Bot Monitor). | Auth Wallet + CF Access (`zen@bnza.io`) + RBAC. Desktop-first. Một số screen TOKEN giữ mock (T3, `Q-011`). |
| PTL-03 `ex.bnza.io` — BNZA-EX | Frontend trading perpetuals Hyperliquid + TradingView Advanced Charts. | ACT-01 End User, ACT-05 Trader. | `apps/bnza-ex/`. Navigation Top nav (Trade / Portfolio / History). | Plain JavaScript (không TS). Trực tiếp HL — không qua OPERATOR. Chain Arbitrum 42161. |
| PTL-04 `api.bnza.io` — BNZA-EXBOT Infra | Backend EXBOT trên CF Workers (cùng deploy với OPERATOR) — không có UI. | ACT-06 OPERATOR (system); ACT-04 Admin cho config (qua PTL-02). | `apps/bnza-operator/`. 19 endpoint hiện + 7 EXBOT endpoint mới (FM-XB-08) + 6 queue mới + 3 DO mới + cron. | Không có screen — chỉ ghi nhận touchpoint trong §9. Trading logic là zen-exclusive. |
| PTL-05 `pool.bnza.io` — BNZA-POOL | Frontend LP Bot retail (Step 7 multi-bot + Step 8 plan_specs versioning). | ACT-01 End User; ACT-04 Admin (xem). | `apps/bnza-pool/`. Navigation Left sidebar (Dashboard / AI Bot / Pairs / Positions / Rules / Settings + Earnings). | Hosting Vercel (riêng repo). Chain Base+OP. |
| PTL-06 `wl-admin.bnza.io` (TBD) — WL-ADMIN | Internal tool cho WL Operator Admin — distribution pipeline daily, reward computation, RewardDistributor, admin console, multi-tenant, reconciliation. | ACT-07 WL Operator Admin (Super / Operator / Read-only). | `apps/bnza-wl-admin/`. Navigation Sidebar — 7 page chính + 9 modal hỗ trợ. PC-only ≥1280px. | Auth SSO (CF Access) + 2FA TOTP. **Open question Q-014:** SOTATEK build hay chỉ là interface context cho Helix? Đợi BA/zen chốt. |

---

## 4. Screen-first site map tree

```text
Bonanzapool (BNZA Ecosystem — SOTATEK Scope)
├── PTL-01 WL Mobile (PWA, bottom-tab-5 + pre-auth WL Gate + Community)
│   ├── [pre-auth] SCR-MOB-01  WL Gate                               (UC-wl-gate)
│   ├── Home    SCR-MOB-02  Home Dashboard                            (UC-home-dashboard, UC-chain-switching)
│   ├── Bot     SCR-MOB-03  LP Bot Status                             (UC-lp-bot-status, UC-chain-switching)
│   ├── Position SCR-MOB-04 Position screen                           (UC-position-screen)
│   ├── Notif   SCR-MOB-05  Notifications                             (UC-notifications)
│   ├── Settings SCR-MOB-06 Settings                                  (—)
│   └── [outside-tab] SCR-MOB-07 Community / Referral Tree            (UC-community)
│
├── PTL-02 BNZA-ADMIN (Sidebar 18 page)
│   ├── Dashboard      SCR-BADM-01 Dashboard                          (FM-ADM-05)
│   ├── WL             SCR-BADM-02 WL Partner Mgmt (whitelabel)       (FM-ADM-01)
│   ├── PF             SCR-BADM-03 PF Distribution (fee-distribution) (FM-ADM-02)
│   ├── IB             SCR-BADM-04 IB Management                      (FM-ADM-03)
│   ├── Bots           SCR-BADM-05 Bot Management                     (FM-ADM-04)
│   │                  SCR-BADM-06 Bot Plan Specs (plans)             (FM-ADM-04 / FM-PL-02 Step 8 OPS)
│   ├── Users          SCR-BADM-07 User Management                    (maintain)
│   ├── Access         SCR-BADM-08 Access Control                     (maintain)
│   ├── Logs           SCR-BADM-09 Audit Logs                         (maintain)
│   ├── Settings       SCR-BADM-10 System Settings                    (FM-ADM-08)
│   ├── Relayer        SCR-BADM-11 Relayer Monitor                    (FM-ADM-09)
│   ├── Reports        SCR-BADM-12 Reports                            (FM-ADM-06)
│   ├── TOKEN          SCR-BADM-13 Burn (mock)                        (FM-ADM-07 T3 — Q-011)
│   │                  SCR-BADM-14 Supply (mock)                      (FM-ADM-07 T3 — Q-011)
│   │                  SCR-BADM-15 Vesting (mock)                     (FM-ADM-07 T3 — Q-011)
│   │                  SCR-BADM-16 Treasury (mock)                    (FM-ADM-07 T3 — Q-011)
│   │                  SCR-BADM-17 Builder Fee (mock)                 (FM-ADM-07 T3 — Q-011)
│   └── WL Bot Monitor SCR-BADM-18 WL Bot Lifecycle Monitor           (FM-ADM-10)
│
├── PTL-03 BNZA-EX (Top nav: Trade / Portfolio / History)
│   ├── Portfolio  SCR-EX-01 Portfolio (current)                      (UC-ex-overview)
│   └── Trade      SCR-EX-02 Trade (draft)                            (UC-order-placement, UC-tradingview, UC-agent-wallet)
│
├── PTL-04 BNZA-EXBOT Infra (api.bnza.io — API-only, no UI)
│   └── (Không có screen — xem §9 touchpoint API/Queue/DO/cron)
│
├── PTL-05 BNZA-POOL (Left sidebar `pool-sidebar`)
│   ├── Dashboard   SCR-POOL-04 Dashboard (current)                   (UC-dashboard)
│   ├── AI Bot      SCR-POOL-03 Bot (current canonical)               (UC-bot-lifecycle)
│   │                SCR-POOL-01 Bot Create (pre-rewrite)              (UC-bot-lifecycle — historical)
│   │                SCR-POOL-02 Bot Monitor (pre-rewrite)             (UC-bot-lifecycle — historical)
│   ├── Pairs       SCR-POOL-05 Pairs (current)                       (UC-pool-discovery)
│   │                SCR-POOL-06 Pool List (superseded by Pairs)       (UC-pool-discovery — historical)
│   ├── Positions   SCR-POOL-07 Positions (current)                   (UC-position-management)
│   ├── Rules       SCR-POOL-08 Rules (current)                       (UC-automation-rules)
│   └── Settings    SCR-POOL-09 Settings (current)                    (UC-settings)
│
└── PTL-06 WL-ADMIN (Sidebar 7 page + 9 supporting modal, PC ≥1280px)
    ├── Dashboard           SCR-WLA-01 wl-dashboard                  (FM-WLA-05 + FM-WLA-04 health + FM-WLA-07 alerts)
    ├── Distribution Jobs   SCR-WLA-02 wl-distribution-jobs          (FM-WLA-01 + FM-WLA-05)
    ├── Users               SCR-WLA-03 wl-users                      (FM-WLA-05)
    ├── Referral Tree       SCR-WLA-04 wl-referral-tree              (FM-WLA-05)
    ├── Distributor Contract SCR-WLA-05 wl-distributor-contract      (FM-WLA-03 + FM-WLA-05)
    ├── Reward Settings     SCR-WLA-06 wl-reward-settings            (FM-WLA-06 + FM-WLA-05)
    └── Admins & Auth       SCR-WLA-07 wl-admins-auth                (FM-WLA-05)
        ▸ M1 Emergency Stop (wl-dashboard §8)
        ▸ M2 BLOCKED Recovery (wl-distribution-jobs §7)
        ▸ M3 Failed Payment Drawer (wl-distribution-jobs §7)
        ▸ M4 Manual Add User (wl-users §6)
        ▸ M5 Add / Change Referral Edge (wl-referral-tree §6)
        ▸ M6 Snapshot Regeneration (wl-referral-tree §6)
        ▸ M7 Refill / Cap Change (wl-distributor-contract §6)
        ▸ M8 Admin Invite (wl-admins-auth §7)
        ▸ M9 Reason Note (shared — bắt buộc cho M1–M8, mọi write-op)
```

---

## 5. Screen / Page inventory

| Screen ID | Site / Portal | Area / Module | Screen / Page | Type | Platform | Source | Status |
|---|---|---|---|---|---|---|---|
| SCR-MOB-01 | PTL-01 | BNZA-MOBILE | WL Gate (pre-auth `/`) | Page | Mobile (PWA) | `mobile/ascii-screen/scr-wl-gate.md` | Derived |
| SCR-MOB-02 | PTL-01 | BNZA-MOBILE | Home Dashboard (`/home`) | Dashboard | Mobile (PWA) | `mobile/ascii-screen/scr-home.md` | Derived |
| SCR-MOB-03 | PTL-01 | BNZA-MOBILE | LP Bot Status (`/bot`) | Page | Mobile (PWA) | `mobile/ascii-screen/scr-bot.md` | Derived |
| SCR-MOB-04 | PTL-01 | BNZA-MOBILE | Position screen (`/positions`) | Page | Mobile (PWA) | `mobile/ascii-screen/scr-position.md` | Derived |
| SCR-MOB-05 | PTL-01 | BNZA-MOBILE | Notifications (`/notifications`) | Page | Mobile (PWA) | `mobile/ascii-screen/scr-notification.md` | Derived |
| SCR-MOB-06 | PTL-01 | BNZA-MOBILE | Settings (`/settings`) | Page | Mobile (PWA) | `mobile/ascii-screen/scr-settings.md` | Derived |
| SCR-MOB-07 | PTL-01 | BNZA-MOBILE | Community / Referral Tree (`/community`) | Page | Mobile (PWA) | `mobile/ascii-screen/scr-community.md` | Derived |
| SCR-BADM-01 | PTL-02 | BNZA-ADMIN | Dashboard | Dashboard | Web (Admin) | `admin/bnza-admin/ascii-screen/dashboard.md` | Derived |
| SCR-BADM-02 | PTL-02 | BNZA-ADMIN | WL Partner Mgmt (whitelabel) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/whitelabel.md` | Derived |
| SCR-BADM-03 | PTL-02 | BNZA-ADMIN | PF Distribution (fee-distribution) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/fee-distribution.md` | Derived |
| SCR-BADM-04 | PTL-02 | BNZA-ADMIN | IB Management | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/ib.md` | Derived |
| SCR-BADM-05 | PTL-02 | BNZA-ADMIN | Bot Management | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/bots.md` | Derived |
| SCR-BADM-06 | PTL-02 | BNZA-ADMIN | Bot Plan Specs (plans) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/plans.md` | Derived |
| SCR-BADM-07 | PTL-02 | BNZA-ADMIN | User Management | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/users.md` | Derived |
| SCR-BADM-08 | PTL-02 | BNZA-ADMIN | Access Control | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/access-control.md` | Derived |
| SCR-BADM-09 | PTL-02 | BNZA-ADMIN | Audit Logs | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/logs.md` | Derived |
| SCR-BADM-10 | PTL-02 | BNZA-ADMIN | System Settings | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/system-settings.md` | Derived |
| SCR-BADM-11 | PTL-02 | BNZA-ADMIN | Relayer Monitor | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/relayer.md` | Derived |
| SCR-BADM-12 | PTL-02 | BNZA-ADMIN | Reports | Report | Web (Admin) | `admin/bnza-admin/ascii-screen/reports.md` | Derived |
| SCR-BADM-13 | PTL-02 | BNZA-ADMIN | TOKEN — Burn (mock) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/burn.md` | Need confirm |
| SCR-BADM-14 | PTL-02 | BNZA-ADMIN | TOKEN — Supply (mock) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/supply.md` | Need confirm |
| SCR-BADM-15 | PTL-02 | BNZA-ADMIN | TOKEN — Vesting (mock) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/vesting.md` | Need confirm |
| SCR-BADM-16 | PTL-02 | BNZA-ADMIN | TOKEN — Treasury (mock) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/treasury.md` | Need confirm |
| SCR-BADM-17 | PTL-02 | BNZA-ADMIN | TOKEN — Builder Fee (mock) | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/builder-fee.md` | Need confirm |
| SCR-BADM-18 | PTL-02 | BNZA-ADMIN | WL Bot Lifecycle Monitor | Page | Web (Admin) | `admin/bnza-admin/ascii-screen/wl-monitor.md` | Derived |
| SCR-EX-01 | PTL-03 | BNZA-EX | Portfolio | Dashboard | Web | `bnza-ex/ascii-screen/portfolio.md` | Confirmed (status=current) |
| SCR-EX-02 | PTL-03 | BNZA-EX | Trade (chart + order panel) | Page | Web | `bnza-ex/ascii-screen/trade.md` | Derived (status=draft) |
| SCR-POOL-01 | PTL-05 | BNZA-POOL | Bot Create (pre-rewrite) | Form | Web | `bnza-pool/ascii-screen/bot-create.md` | Derived (historical, draft) |
| SCR-POOL-02 | PTL-05 | BNZA-POOL | Bot Monitor (pre-rewrite) | Page | Web | `bnza-pool/ascii-screen/bot-monitor.md` | Derived (historical, draft) |
| SCR-POOL-03 | PTL-05 | BNZA-POOL | Bot (canonical) | Page | Web | `bnza-pool/ascii-screen/bot.md` | Confirmed (status=current) |
| SCR-POOL-04 | PTL-05 | BNZA-POOL | Dashboard | Dashboard | Web | `bnza-pool/ascii-screen/dashboard.md` | Confirmed (status=current) |
| SCR-POOL-05 | PTL-05 | BNZA-POOL | Pairs | Page | Web | `bnza-pool/ascii-screen/pairs.md` | Confirmed (status=current) |
| SCR-POOL-06 | PTL-05 | BNZA-POOL | Pool List (superseded) | Page | Web | `bnza-pool/ascii-screen/pool-list.md` | Need confirm (superseded by SCR-POOL-05) |
| SCR-POOL-07 | PTL-05 | BNZA-POOL | Positions | Page | Web | `bnza-pool/ascii-screen/positions.md` | Confirmed (status=current) |
| SCR-POOL-08 | PTL-05 | BNZA-POOL | Rules | Page | Web | `bnza-pool/ascii-screen/rules.md` | Confirmed (status=current) |
| SCR-POOL-09 | PTL-05 | BNZA-POOL | Settings | Page | Web | `bnza-pool/ascii-screen/settings.md` | Confirmed (status=current) |
| SCR-WLA-01 | PTL-06 | WL-ADMIN | wl-dashboard (KPI + health + emergency stop) | Dashboard | Web (Admin, PC ≥1280px) | `admin/wl-admin/ascii-screen/wl-dashboard.md` | Derived |
| SCR-WLA-02 | PTL-06 | WL-ADMIN | wl-distribution-jobs (state machine + BLOCKED recovery) | Page | Web (Admin) | `admin/wl-admin/ascii-screen/wl-distribution-jobs.md` | Derived |
| SCR-WLA-03 | PTL-06 | WL-ADMIN | wl-users (cumulative + Cap + lineage) | Page | Web (Admin) | `admin/wl-admin/ascii-screen/wl-users.md` | Derived |
| SCR-WLA-04 | PTL-06 | WL-ADMIN | wl-referral-tree (hierarchy + parent change) | Page | Web (Admin) | `admin/wl-admin/ascii-screen/wl-referral-tree.md` | Derived |
| SCR-WLA-05 | PTL-06 | WL-ADMIN | wl-distributor-contract (balance + refill + multisig proposal) | Page | Web (Admin) | `admin/wl-admin/ascii-screen/wl-distributor-contract.md` | Derived |
| SCR-WLA-06 | PTL-06 | WL-ADMIN | wl-reward-settings (Rank / Title / Referral / Cap / Bonus) | Page | Web (Admin) | `admin/wl-admin/ascii-screen/wl-reward-settings.md` | Derived |
| SCR-WLA-07 | PTL-06 | WL-ADMIN | wl-admins-auth (role + 2FA + session policy) | Page | Web (Admin) | `admin/wl-admin/ascii-screen/wl-admins-auth.md` | Derived |
| (PTL-04) | PTL-04 | BNZA-EXBOT Infra | (API-only, no UI) | — | API | `operator/ascii-screen/api-overview.md` | N/A |

---

## 6. Navigation & screen flow

| Flow ID | Flow name | Role | Start screen | Main path | End screen / outcome | Related feature(s) | Notes |
|---|---|---|---|---|---|---|---|
| FLOW-MOB-01 | WL End User sign in & xem reward | ACT-03 | SCR-MOB-01 WL Gate | WL Gate → wallet connect → SIWE sign → JWT 24h → SCR-MOB-02 Home | Home Dashboard hiển thị fee+referral reward post-allocation | FM-MOB-01 + FM-MOB-02 + FM-MOB-07 (tenant config) | BR-MOB-001..003. Tenant resolved server-side. |
| FLOW-MOB-02 | Claim USDC | ACT-03 | SCR-MOB-02 Home | Home → claimable card → Receive All → ký TX `RewardDistributor.claim()` → sync after claim | Toast success, balance update | FM-MOB-03 + FM-WLA-03 | BR-MOB-007/008. Pause → claim disable (E-MOB-007). |
| FLOW-MOB-03 | Start LP Bot WL | ACT-03 | SCR-MOB-03 Bot | Bot → "Create" → 3 TX (USDC approve → setApprovalForAll → zapMint) → OPERATOR `/api/bot/register` → Bot list update | Bot active, hiển thị trong SCR-MOB-04 Position | FM-MOB-04 + OPERATOR API | BR-MOB-005/006. WL bot ép `convertToUsdc=true`, `autoCompound=false`. Helix server-to-server qua HMAC-SHA256. |
| FLOW-MOB-04 | Stop Bot WL | ACT-03 | SCR-MOB-04 Position | Position → bot row → Stop → confirm → user wallet ký stop TX | Bot stopped; principal → user, net → wlMaster[tokenId] | FM-MOB-04 + Router | Stop TX deadline +1200s. `already_stopped` treated success. |
| FLOW-MOB-05 | Chain switching (Base ↔ OP) | ACT-03 | Header any screen | Header chain toggle → Reown AppKit prompt switch → re-filter data | UI reload với chain mới; persist localStorage | FM-MOB-08 | BR-MOB-009. Arbitrum loại trừ. |
| FLOW-MOB-06 | Xem community / referral tree | ACT-03 | SCR-MOB-02 Home | Home → menu → SCR-MOB-07 Community | Team TVL + downline + per-tier rate | FM-MOB-06 | Read-only. |
| FLOW-WLA-01 | Daily MLM distribution run | System cron + ACT-07 | (cron daily) | State machine: PENDING → BOT_SYNC → LEDGER_FETCH (HMAC) → PENDING_SNAPSHOT (operational gate, manual GO) → SNAPSHOT → UPLINE → COMPUTED → ENQUEUED → ONCHAIN (RewardDistributor) → VALIDATED → COMPLETED | Reward đến tay user (Push hoặc Claim) | FM-WLA-01 + FM-WLA-02 + FM-WLA-03 + FM-WLA-04 | Hiển thị thực tế trên SCR-WLA-02 wl-distribution-jobs. BLOCKED → M2 modal recovery. |
| FLOW-WLA-02 | BLOCKED recovery | ACT-07 Operator | SCR-WLA-02 | Operator chọn job BLOCKED → M2 modal → chọn action (refetch / retry / requeue / refill / abandon) + reason note M9 → audit log + Slack mirror | Job tiếp tục hoặc abandoned | FM-WLA-01 + FM-WLA-05 | Force skip (ABANDONED) chỉ Super. |
| FLOW-WLA-03 | Refill Distributor & Emergency Pause | ACT-07 | SCR-WLA-05 | Refill: Treasury → Distributor (M7 modal + reason note). Emergency Pause: SCR-WLA-01 dashboard → M1 (PAUSER hot wallet, immediate) | RewardDistributor `paused`; user thấy `E-MOB-007` | FM-WLA-03 + FM-WLA-05 | Unpause yêu cầu multisig proposal. |
| FLOW-WLA-04 | Edit tenant reward settings | ACT-07 Super | SCR-WLA-06 | Rank / Title / Referral / Cap / Bonus tab → edit → M9 reason → audit + Slack | Tenant config updated | FM-WLA-06 + FM-WLA-02 | Chỉ Super. |
| FLOW-BADM-01 | WL Partner onboarding | ACT-04 | SCR-BADM-02 whitelabel | Tạo WL partner: name + logo (CF R2) + auto/manual referral_code 8-char + deposit tier 1k/5k/10k + main wallet + languages | Tạo `wl_partners` + `wl_code` + cấu hình tab Members + Master Wallets | FM-ADM-01 | BR-ADM-001..008. Chỉ super_admin (BR-ADM-002). |
| FLOW-BADM-02 | WL member lifecycle (register / leave / rejoin) | ACT-04 | SCR-BADM-02 (Members tab) | Register member: wallet + wl_code → row `active`. Initiate leave → `leaving` (two-phase, bot start mới bị reject). On-chain unset confirmed → confirm-leave → `left`. Rejoin → `membership_epoch++`. | Member state updated; Ledger API trả epoch cho Helix | FM-ADM-01 | BR-ADM-009..012. |
| FLOW-BADM-03 | WL master wallet rotation | ACT-04 | SCR-BADM-02 (Master Wallets tab) | Two-phase: unset old → set new on-chain. Delivery suspended trong rotation. | Net chảy đến master mới | FM-ADM-01 | BR-ADM-013. |
| FLOW-BADM-04 | PF Distribution config | ACT-04 | SCR-BADM-03 fee-distribution | CRUD `fee_distributions` rows: wallet + share_ratio + is_remainder. Tổng non-remainder < 1.0; max 10. | Off-chain config; PF on-chain vẫn về `pfCollector` EOA. | FM-ADM-02 | BR-ADM-015..020. Audit log mỗi CRUD. |
| FLOW-BADM-05 | WL Bot Lifecycle recovery | ACT-04 | SCR-BADM-18 wl-monitor | Monitor backlog (`pending_set`, `failed_set`, `needs_repair`, `pending_unset`). Action: retry-set (re-check member.active + wl_code.active) hoặc force-normalize (two-phase: unset on-chain → wlMaster[tokenId]==0 → DB wl_code=NULL). | Bot trở về NULL/active | FM-ADM-10 + OPERATOR + Router | BR-ADM-031..033. failed_set 48h auto-force-normalize. |
| FLOW-BADM-06 | plan_specs version publish (Step 8) | ACT-04 | SCR-BADM-06 plans | Publish version mới → `plan_specs_history` + `system_config.plan_specs_current_version` → POOL refresh trong 5 min TTL → BotCard outdated warning khi current ≠ snapshot. | Bot tạo mới snapshot version. | FM-PL-02 + FM-ADM-04 | Cần simultaneous deploy POOL + OPERATOR + OPS. BR-PL-17. |
| FLOW-POOL-01 | LP Bot lifecycle (regular) | ACT-01 | SCR-POOL-04 Dashboard | Dashboard → AI Bot SCR-POOL-03 → Create → atomic-start (Operator path ERC20-only) → bot active → BotCard (Active Bots grid) | Bot tạo on-chain, hiển thị trong Positions SCR-POOL-07 | FM-PL-01 + FM-PL-02 + UC-bot-lifecycle | BR-PL-15..16 (atomic-start retry 3x exponential 2/4/6s). |
| FLOW-POOL-02 | Bot stop (regular) | ACT-01 | SCR-POOL-07 Positions | Position → Stop → user wallet ký TX (deadline now+1200s) → OPERATOR cập nhật | Earnings = USDC sau PF (convert_to_usdc=1 → 0.2970075 PF) | FM-PL-01 + UC-bot-lifecycle | BR-PL-06..09. `already_stopped` success. |
| FLOW-POOL-03 | Chain switching POOL | ACT-01 | Sidebar any screen | Chain toggle Base/OP → re-filter bots theo chain | UI reload | UC-bot-lifecycle | Base + OP only (BR-PL-01). Max 10 bot/chain (BR-PL-11). |
| FLOW-EX-01 | Agent wallet setup & trade | ACT-05 / ACT-01 | SCR-EX-01 Portfolio | Portfolio → connect ví → tạo agent key (BR-EX-02) → builder fee approval (BR-EX-03) → SCR-EX-02 Trade → place order ký bằng agent key | Order match trên HL (Arbitrum 42161) | FM-EX-01..03 + UC-agent-wallet, UC-order-placement, UC-tradingview | Trực tiếp HL, không qua OPERATOR. |

---

## 7. Role / access by screen

| Role / User type | Accessible site/module | Accessible screen | Key actions | Restriction / Rule | Source | Status |
|---|---|---|---|---|---|---|
| ACT-01 End User (LP) | PTL-05 POOL + PTL-03 EX | Toàn bộ SCR-POOL-01..09 + SCR-EX-01..02 | Tạo/start/stop bot POOL; trade HL trên EX. | Auth `X-Wallet-Address` cho POOL → OPERATOR. EX dùng wallet trực tiếp HL. | backbone §4.3 + §4.5 | Confirmed |
| ACT-02 WL Partner | PTL-01 MOBILE (read-only earning) | SCR-MOB-02, SCR-MOB-03, SCR-MOB-04, SCR-MOB-07 | Xem earning + downline của user thuộc WL của mình. | Read-only. Wallet + WL invite code. | backbone §4.1 | Derived |
| ACT-03 WL End User | PTL-01 MOBILE | SCR-MOB-01..07 | SIWE → claim USDC + start/stop bot + xem reward + community + chain switch + settings. | Auth SIWE → JWT 24h, tenant server-side. Bot ops Base/OP only. | backbone §4.1 + BR-MOB-001..010 | Derived |
| ACT-04 Admin (zen) | PTL-02 BNZA-ADMIN + PTL-04 EXBOT Infra (config) + PTL-05 POOL (view) | SCR-BADM-01..18 + (PTL-04 không UI) + SCR-POOL-* (view + Step 8 actions) | WL partner onboarding (Super) + PF config + IB + Bot Type + System Settings + Relayer Monitor + WL Bot Lifecycle Monitor + plan_specs version + force-stop bot. | Wallet + CF Access (`zen@bnza.io`) + RBAC `super_admin`/`admin`/`viewer`. Một số action chỉ Super. | backbone §4.2 + §4.5 + BR-ADM-002 | Derived |
| ACT-05 Trader | PTL-03 EX | SCR-EX-01, SCR-EX-02 | View chart + place perpetual order. | Wallet trực tiếp HL. Chain Arbitrum 42161 (BR-EX-01). | backbone §4.3 | Confirmed |
| ACT-06 OPERATOR (System) | PTL-04 EXBOT Infra | (No UI) | Queue processing + cron + D1 read/write + DO management + HL adapter calls. | Internal — không user auth. | backbone §4.4 | N/A — system actor |
| ACT-07 WL Operator Admin Super | PTL-06 WL-ADMIN | SCR-WLA-01..07 + tất cả 9 modal | Full quyền: distribution recovery, force skip, manual GO, tree edit, refill, propose multisig, emergency pause, reward settings, admins & auth. | SSO (CF Access) + 2FA TOTP. Mọi write-op yêu cầu reason note M9 + Slack audit mirror. | backbone §4.7 | Derived |
| ACT-07 WL Operator Admin Operator | PTL-06 WL-ADMIN | SCR-WLA-01..07 (read) + một số write-op (recovery, manual GO, tree edit, refill) | Distribution ops + tree management + refill — KHÔNG được force skip, multisig propose, emergency pause, edit reward settings, admins & auth. | SSO + 2FA TOTP. | backbone §4.7 | Derived |
| ACT-07 WL Operator Admin Read-only | PTL-06 WL-ADMIN | SCR-WLA-01..07 (read) | View only. | SSO + 2FA TOTP. | backbone §4.7 | Derived |

---

## 8. Screen ↔ Feature mapping

| Screen ID | Screen / Page | Feature ID | Feature name | Mapping type | Regression anchor? | Notes |
|---|---|---|---|---|---|---|
| SCR-MOB-01 | WL Gate | FM-MOB-01 | SIWE Auth + WL Gate | Primary | Yes | Tenant resolved server-side; mobile blocked routes (BR-MOB-001). |
| SCR-MOB-02 | Home Dashboard | FM-MOB-02 / FM-MOB-07 / FM-MOB-08 | Reward Display / Multi-tenant Branding / Chain Switching | Primary / Supporting / Supporting | Yes | Post-allocation only (BR-MOB-004). |
| SCR-MOB-03 | LP Bot Status | FM-MOB-04 / FM-MOB-05 / FM-MOB-08 | Bot Operations / LP Bot Status / Chain Switching | Primary / Primary / Supporting | Yes | WL bot constraint `convertToUsdc=true`, `autoCompound=false` (BR-MOB-005). |
| SCR-MOB-04 | Position | FM-MOB-05 / FM-MOB-04 (stop) | LP Bot Status / Bot Operations | Primary / Supporting | Yes | — |
| SCR-MOB-05 | Notifications | — | (no FM trace) | Unknown | No | Unmapped — chờ BA gán FM. |
| SCR-MOB-06 | Settings | FM-MOB-09 / FM-MOB-11 / FM-MOB-08 | Settings / i18n / Chain Switching | Primary / Supporting / Supporting | No | Disconnect → clear JWT (BR-MOB-010). |
| SCR-MOB-07 | Community | FM-MOB-06 | Community / Referral Tree | Primary | No | Team TVL + downline. |
| SCR-BADM-01 | Dashboard | FM-ADM-05 | Dashboard | Primary | No | KV-cached 5 min TTL (BR-ADM-027). |
| SCR-BADM-02 | WL Partner Mgmt | FM-ADM-01 | WL Partner Onboarding + Member + Master Wallet | Primary | Yes | BR-ADM-001..014. Boundary với PTL-06 (BR-ADM-008). |
| SCR-BADM-03 | PF Distribution | FM-ADM-02 | PF Distribution Config | Primary | Yes | BR-ADM-015..020. Off-chain only, pfCollector EOA. |
| SCR-BADM-04 | IB Management | FM-ADM-03 | IB Management | Primary | No | Replace mockIBs (BR-ADM-024). |
| SCR-BADM-05 | Bot Management | FM-ADM-04 | Bot Type Config | Primary | Yes | cooldown 10–180 min (BR-ADM-022). |
| SCR-BADM-06 | Bot Plan Specs | FM-PL-02 / FM-ADM-04 | Step 8 plan_specs Version / Bot Type Config | Primary / Supporting | Yes | BR-PL-17. Cần simultaneous deploy. |
| SCR-BADM-07 | User Management | — | (maintain) | Unknown | No | Unmapped — maintain feature. |
| SCR-BADM-08 | Access Control | — | (maintain) | Unknown | Yes | Permission rule cấp data — ảnh hưởng nhiều feature. |
| SCR-BADM-09 | Audit Logs | — | (maintain) | Unknown | No | Read-only audit (cross-cutting). |
| SCR-BADM-10 | System Settings | FM-ADM-08 | System Settings | Primary | Yes | `global_bot_enabled`, `safe_mode`, `exbot_enabled` (BR-ADM-028..030). |
| SCR-BADM-11 | Relayer Monitor | FM-ADM-09 | Relayer Monitor | Primary | No | Health check. |
| SCR-BADM-12 | Reports | FM-ADM-06 | Reports | Primary | No | Date-range queries. |
| SCR-BADM-13..17 | TOKEN (Burn/Supply/Vesting/Treasury/Builder Fee) | FM-ADM-07 | TOKEN Management (mock) | Primary | No | T3 mock. Q-011 mở. |
| SCR-BADM-18 | WL Bot Lifecycle Monitor | FM-ADM-10 | WL Bot Lifecycle Monitor | Primary | Yes | BR-ADM-031..033. 6-state machine. |
| SCR-EX-01 | Portfolio | FM-EX-02 / FM-EX-03 (post-trade) | Chart Data Feed / Order Placement | Supporting | No | Status = current từ code audit. |
| SCR-EX-02 | Trade | FM-EX-01 / FM-EX-02 / FM-EX-03 | TradingView Integration / Chart Data Feed / Order Placement | Primary | Yes | BR-EX-02..04 agent key. |
| SCR-POOL-01 | Bot Create (historical) | FM-PL-01 (regress) | Step 7 Multi-Bot | Supporting (legacy) | No | Pre-rewrite — kept for traceability. |
| SCR-POOL-02 | Bot Monitor (historical) | FM-PL-01 (regress) | Step 7 Multi-Bot | Supporting (legacy) | No | Pre-rewrite. |
| SCR-POOL-03 | Bot | FM-PL-01 | Step 7 Multi-Bot | Primary | Yes | BotCard grid, max 10/chain (BR-PL-11). |
| SCR-POOL-04 | Dashboard | UC-dashboard | (POOL UC) | Primary | No | Aggregate metrics. |
| SCR-POOL-05 | Pairs | UC-pool-discovery | (POOL UC) | Primary | No | Replace Pool List. |
| SCR-POOL-06 | Pool List (superseded) | UC-pool-discovery (regress) | (POOL UC legacy) | Supporting (legacy) | No | Kept for traceability. |
| SCR-POOL-07 | Positions | UC-position-management / FM-PL-01 | (POOL UC) / Step 7 Multi-Bot | Primary | Yes | Stop flow. |
| SCR-POOL-08 | Rules | UC-automation-rules | (POOL UC) | Primary | No | Cron + threshold rule. |
| SCR-POOL-09 | Settings | UC-settings | (POOL UC) | Primary | No | i18n + chain default. |
| SCR-WLA-01 | wl-dashboard | FM-WLA-05 / FM-WLA-04 (health) / FM-WLA-07 (alerts) | Admin Console / BNZA API Integration health / Daily Reconciliation alerts | Primary / Supporting / Supporting | Yes | M1 Emergency Stop. |
| SCR-WLA-02 | wl-distribution-jobs | FM-WLA-01 / FM-WLA-05 | Distribution Pipeline / Admin Console | Primary / Supporting | Yes | M2, M3 modal. |
| SCR-WLA-03 | wl-users | FM-WLA-05 / FM-WLA-02 (Cap) | Admin Console / Reward Computation (Cap) | Primary / Supporting | Yes | M4 Manual Add User. |
| SCR-WLA-04 | wl-referral-tree | FM-WLA-05 | Admin Console | Primary | Yes | M5 Add/Change Edge, M6 Snapshot Regeneration. |
| SCR-WLA-05 | wl-distributor-contract | FM-WLA-03 / FM-WLA-05 | RewardDistributor Integration / Admin Console | Primary / Supporting | Yes | M7 Refill / Cap Change. |
| SCR-WLA-06 | wl-reward-settings | FM-WLA-06 / FM-WLA-02 | Multi-tenant Config / Reward Computation | Primary / Supporting | Yes | Chỉ Super edit. |
| SCR-WLA-07 | wl-admins-auth | FM-WLA-05 | Admin Console | Primary | No | M8 Admin Invite. |
| (No-UI) | PTL-04 EXBOT Infra | FM-XB-01..13 | All EXBOT features | Backend-only | Yes | Test integration trên queue + HL API (backbone §8.6). |

### Feature-level coverage summary for dashboard

| Feature ID | Feature name | Site / Portal | Module | Mapped screen(s) | Folder alias(es) | Line | In scope? | QC Status | Site map status | Gap / Note |
|---|---|---|---|---|---|---|---|---|---|---|
| FM-WLA-01 | Distribution Pipeline | PTL-06 | WL-ADMIN | SCR-WLA-02, SCR-WLA-01 | — | L1 | OOS (Helix) | ✅ Done | Mapped | Dependency context only. |
| FM-WLA-02 | Reward Computation Engine | PTL-06 | WL-ADMIN | SCR-WLA-03, SCR-WLA-06 | — | L1 | OOS (Helix) | ✅ Done | Partial | Dependency context only. |
| FM-WLA-03 | RewardDistributor Integration | PTL-06 + on-chain | WL-ADMIN | SCR-WLA-05 | — | L1 | OOS (Helix) | ✅ Done | Mapped | Dependency context only. |
| FM-WLA-04 | BNZA API Integration (3 stream) | PTL-06 ↔ PTL-04 | WL-ADMIN ↔ OPERATOR | SCR-WLA-01 (health) | — | L1 | OOS (Helix) | ✅ Done | Partial | Dependency context only. |
| FM-WLA-05 | Admin Console — 7 page | PTL-06 | WL-ADMIN | SCR-WLA-01..07 + 9 modal | — | L1 | OOS (Helix) | ✅ Done | Mapped | Dependency context only. |
| FM-WLA-06 | Multi-tenant Config | PTL-06 | WL-ADMIN | SCR-WLA-06 | — | L1 | OOS (Helix) | ✅ Done | Mapped | Dependency context only. |
| FM-WLA-07 | Daily Reconciliation (6-point cron) | PTL-06 | WL-ADMIN | SCR-WLA-01 (alerts) | — | L1 | OOS (Helix) | ✅ Done | Partial | Dependency context only. |
| FM-MOB-01 | SIWE Auth + WL Gate | PTL-01 | BNZA-MOBILE | SCR-MOB-01 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-02 | Reward Display | PTL-01 | BNZA-MOBILE | SCR-MOB-02 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-03 | Claim USDC | PTL-01 | BNZA-MOBILE | SCR-MOB-02 (claimable card) | — | L1 | Yes | ✅ Done | Partial | QC đã hoàn thành. |
| FM-MOB-04 | Bot Operations | PTL-01 | BNZA-MOBILE | SCR-MOB-03, SCR-MOB-04 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-05 | LP Bot Status | PTL-01 | BNZA-MOBILE | SCR-MOB-03, SCR-MOB-04 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-06 | Community / Referral Tree | PTL-01 | BNZA-MOBILE | SCR-MOB-07 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-07 | Multi-tenant Branding | PTL-01 | BNZA-MOBILE | SCR-MOB-02 (apply globally) | — | L1 | Yes | ✅ Done | Partial | QC đã hoàn thành. |
| FM-MOB-08 | Chain Switching | PTL-01 | BNZA-MOBILE | Header all screens | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-09 | Settings | PTL-01 | BNZA-MOBILE | SCR-MOB-06 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-MOB-10 | PWA | PTL-01 | BNZA-MOBILE | (cross-cutting) | — | L1 | Yes | ✅ Done | Partial | QC đã hoàn thành. |
| FM-MOB-11 | i18n | PTL-01 | BNZA-MOBILE | (cross-cutting) | — | L1 | Yes | ✅ Done | Partial | QC đã hoàn thành. |
| FM-ADM-01 | WL Partner Onboarding + Member + Master Wallet | PTL-02 | BNZA-ADMIN | SCR-BADM-02 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-02 | PF Distribution Config | PTL-02 | BNZA-ADMIN | SCR-BADM-03 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-03 | IB Management | PTL-02 | BNZA-ADMIN | SCR-BADM-04 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-04 | Bot Type Config | PTL-02 | BNZA-ADMIN | SCR-BADM-05, SCR-BADM-06 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-05 | Dashboard (real metrics) | PTL-02 | BNZA-ADMIN | SCR-BADM-01 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-06 | Reports | PTL-02 | BNZA-ADMIN | SCR-BADM-12 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-07 | TOKEN Management (mock) | PTL-02 | BNZA-ADMIN | SCR-BADM-13..17 | — | L1 | Yes | ✅ Done | Mapped | T3 mock — QC đã hoàn thành. |
| FM-ADM-08 | System Settings | PTL-02 | BNZA-ADMIN | SCR-BADM-10 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-09 | Relayer Monitor | PTL-02 | BNZA-ADMIN | SCR-BADM-11 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-ADM-10 | WL Bot Lifecycle Monitor | PTL-02 | BNZA-ADMIN | SCR-BADM-18 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-EX-01 | TradingView Integration | PTL-03 | BNZA-EX | SCR-EX-02 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-EX-02 | Chart Data Feed | PTL-03 | BNZA-EX | SCR-EX-02, SCR-EX-01 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-EX-03 | Order Placement | PTL-03 | BNZA-EX | SCR-EX-02 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-XB-01 | EXBOT D1 Schema (9 tables) | PTL-04 | BNZA-EXBOT Infra | (no UI — backend) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** Q-001 blocker. |
| FM-XB-02 | EXBOT Queue Topology (6 queue) | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-03 | EXBOT Durable Objects | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-04 | EXBOT Cron Jobs | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-05 | HL Adapter | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-06 | EXBOT API Endpoints | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-07 | Router Extension (Solidity) | On-chain | BNZA-EXBOT Infra | (no UI — Solidity) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-08 | OPERATOR API EXBOT Endpoints | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-09 | Phase A1 — Dry Run | PTL-04 + HL testnet | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-10 | Phase A2 — Live $1k Test | PTL-04 + HL mainnet | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-11 | Phase A3 — Closed Beta 5–10 WL user | PTL-04 + PTL-01 | BNZA-EXBOT Infra ↔ MOBILE | (mobile UI dùng tạm) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Partial | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-12 | Envelope Encryption | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-XB-13 | Pre-launch Hotfixes | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | **L2** | **Yes** | 🔜 **ACTIVE** | Missing (screen-side) | **PHẠM VI QC DUY NHẤT.** |
| FM-PL-01 | Step 7 Multi-Bot | PTL-05 | BNZA-POOL | SCR-POOL-03, SCR-POOL-07, SCR-POOL-04 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-PL-02 | Step 8 plan_specs Version Management | PTL-05 + PTL-02 + PTL-04 | BNZA-POOL + BNZA-ADMIN | SCR-POOL-03, SCR-BADM-06 | — | L1 | Yes | ✅ Done | Mapped | QC đã hoàn thành. |
| FM-WLC-01 | Router + LPBot WL Changes A–K | On-chain | Smart Contracts | (no UI) | — | L1 | Yes | ✅ Done | N/A | QC đã hoàn thành. |
| FM-OPW-01→07 | OPERATOR WL Backend | PTL-04 | BNZA-OPERATOR | (no UI) | — | L1 | Yes | ✅ Done | N/A | QC đã hoàn thành. Là dependency chính cho Line 2. |

---

## 9. Screen ↔ Data / API / Integration / State touchpoints

| Screen / Flow | Data object / API / Integration / State | Rule / lifecycle liên quan | QC impact | Source |
|---|---|---|---|---|
| SCR-MOB-01 → SIWE flow | Helix admin system `/api/mobile/siwe-nonce` + `/api/mobile/siwe-verify` (issue JWT 24h) | Tenant resolved server-side từ subdomain + signature domain (BR-MOB-003). | Test: HTTP 401 sai chữ ký (E-MOB-001); HTTP 403 tenant mismatch (E-MOB-002); HTTP 429 rate limit (E-MOB-003). | backbone §6 + common-rules + message-list |
| SCR-MOB-02 / SCR-MOB-03 / SCR-MOB-04 → Helix admin API | `/api/mobile/summary`, `/api/mobile/positions`, `/api/mobile/history`, `/api/mobile/community`, `/api/mobile/tenant-config` (SIWE/JWT) | Read-only. Post-allocation only — không hiện raw LP fees. | Test: fail → E-MOB-004/005/006. | backbone §6 |
| SCR-MOB-03 / SCR-MOB-04 → BNZA OPERATOR (Helix server-to-server) | `/api/bot-configs/atomic-start`, `/api/bot-configs/:id/stop` (WL path HMAC-SHA256) | starter wallet truyền explicit; anti-spoofing tx_hash + NPM ownerOf + BotStarted/ZapMintFor event decode. | Test: HMAC sai/nonce replay → reject; ownerOf không khớp → reject. | backbone §8.1 + §6 |
| SCR-MOB-03 → Router + LPBot on-chain | `setApprovalForAll` + `zapMint` + `stopBot` (Base/OP) | `convertToUsdc=true`, `autoCompound=false` ép on-chain (BR-MOB-005). | Test: bot WL bắt buộc USDC out; user ký 3 TX tuần tự. | backbone §8.2 |
| SCR-MOB-03 → Bot register | OPERATOR `/api/bot/register` | Sau ký TX thành công thì call register; fail handle bằng E-MOB-009. | Test: TX success nhưng register fail → có recover path không? | message-list E-MOB-009 |
| SCR-MOB-02 / SCR-MOB-Claim flow → RewardDistributor on-chain | `RewardDistributor.claim()` (Base 8453 + OP 10) | Push (≥ minPayout, WL gas) / Claim (user gas). Paused → claim disabled. | Test: ETH insufficient → E-MOB-008; pause → E-MOB-007. | BR-MOB-007/008 |
| SCR-MOB-02 → Sync after claim | Helix `/api/mobile/sync-after-claim` | Transfer event + supplementary POST. | Test: sync fail → có retry hay UI fail-soft? | backbone §6 |
| SCR-WLA-02 distribution-jobs ↔ OPERATOR (3 stream) | `/api/wl/ledger` (Stream 1 net), `/api/wl/portfolio` (Stream 2 AUM), `/internal/bot/sync` (Stream 3 bot mirror) — HMAC-SHA256 PULL | State machine BOT_SYNC → ... → COMPLETED (backbone §8.8.7). BLOCKED recovery per phase. | Test: HMAC sai/replay → reject; mỗi phase fail → BLOCKED + recovery option đúng. | backbone §8.8 |
| SCR-WLA-05 distributor-contract ↔ RewardDistributor | `addRewards` (clientNonce idempotency); Pause/Unpause via multisig (PAUSER hot wallet pause khẩn) | Push tự động khi ≥ minPayout. | Test: dup clientNonce → reject; pause → user bị E-MOB-007. | backbone §6 + intake §3 Module 1A |
| SCR-WLA-06 reward-settings | WL-ADMIN D1 `tenants`, `rank_tiers`, `title_tiers`, `referral_levels`, `reward_settings` | Multi-tenant per WL operator. | Test: edit settings → audit log + Slack mirror; mọi tab phải bảo toàn config khác. | backbone §8.8.6 |
| SCR-BADM-02 whitelabel ↔ OPERATOR | OPERATOR `/api/wl-partners` (CRUD); members tab + master wallets tab + `wl_codes` suspend/resume | `wl_codes` immutable sau set; suspend dừng toàn bộ delivery → OPERATOR cron move bot → `pending_unset` (BR-ADM-014). | Test: dup `referral_code` → 409 E-ADM-001; suspend → bot ops blocked. | BR-ADM-001..014 |
| SCR-BADM-03 fee-distribution ↔ OPERATOR | `fee_distributions` table; daily-collector cron; pfCollector EOA on-chain | Chính xác 1 `is_remainder=true`; sum non-remainder < 1.0; max 10 rows; off-chain only (BR-ADM-015..020). | Test: edit vi phạm → reject + audit; WL 70/30 remittance flow chưa rõ (Q-002). | BR-ADM-015..020 |
| SCR-BADM-18 wl-monitor ↔ OPERATOR ↔ Router | OPERATOR `/api/admin/wl-bot-monitor`, `/api/bot-configs/:id/wl-retry-set`, `/api/bot-configs/:id/wl-force-normalize`; on-chain `setBotWlMaster`/`unsetBotWlMaster` | State machine 6-state. force-normalize two-phase: on-chain `wlMaster[tokenId]==0` rồi mới set DB `wl_code=NULL` (BR-ADM-031). failed_set 48h auto-force-normalize (BR-ADM-033). | Test: chỉ set DB không đủ; phải verify on-chain. | BR-ADM-031..033 + backbone §6 |
| SCR-BADM-06 plans ↔ POOL ↔ OPERATOR | `plan_specs`, `plan_specs_history`, `system_config.plan_specs_current_version`; POOL localStorage 5 min TTL | Immutable (BR-PL-17). BotCard outdated warning khi version lệch. | Test: edit version cũ → reject; bot start mới snapshot current. | BR-PL-17 + intake §3 Module 5 |
| SCR-POOL-03 / SCR-POOL-07 ↔ OPERATOR | `/api/bot-configs/atomic-start`, `:id/stop` (regular path `X-Wallet-Address`); `/api/bot-positions` | Retry 3x exponential (BR-PL-16); deadline +1200s (BR-PL-07); `already_stopped` success (BR-PL-14); OPERATOR fail sau on-chain success vẫn success (BR-PL-09). | Test: TX flow + fallback. | BR-PL-06..18 |
| SCR-EX-02 ↔ Hyperliquid | `@nktkas/hyperliquid 0.32.1`, agent key signing | BR-EX-04: order ký bằng agent key, không popup. | Test: agent mismatch → reject (BR-EX-02). | BR-EX-02..06 |
| PTL-04 (no UI) → 3 queue hiện hữu | OPERATOR Queues: `bnza-daily-collect-queue`, `bnza-bot-check-queue`, `bnza-rule-check-queue` | Max batch 100, timeout 30s, concurrency 1, retries 3. | Test: integration test (backbone §8.6). | intake §4.3 |
| PTL-04 (no UI) → 6 queue EXBOT mới | bot-scan, light-check, hedge-sync, reconcile, deep-audit, stop-audit | Pending FM-XB-02; chờ zen specs (Q-001). | Test: integration test pattern + Producer/Consumer separation. | feature-map §3.4 |
| PTL-04 (no UI) → DO + Cron + HL adapter | HLRateLimitDO, UserLockDO, MarketDataDO; cron `*/360 * * * *` deep-audit; HL adapter rate limit 1200 req/min | FM-XB-03/04/05/12 (envelope encryption HL agent key). | Test: rate limit reject; reconcile log; envelope encryption secret không lộ. | feature-map §3.4 |
| All admin (PTL-02, PTL-06) | Audit log entries | Mọi write WL-ADMIN: reason note M9 + Slack mirror. BNZA-ADMIN: audit log mỗi CRUD `fee_distributions` (BR-ADM-019). | Test: audit log đầy đủ actor + action + before/after + timestamp. | backbone §5.0 + BR-ADM-019 |

> Chi tiết entity lifecycle, CRUD role, relationship và feature-entity coverage được quản lý trong `qc-data-map.md`. Section này chỉ giữ touchpoint ở góc nhìn screen/flow.

---

## 10. Regression / impact anchors

| Anchor | Type | Related feature(s) | Related screen(s) | Vì sao quan trọng | Suggested regression focus |
|---|---|---|---|---|---|
| Daily MLM distribution pipeline | Core flow | FM-WLA-01, FM-WLA-02, FM-WLA-03, FM-WLA-04, FM-WLA-07 | SCR-WLA-02, SCR-WLA-05, SCR-WLA-01 | Bất kỳ thay đổi nào ở Ledger/Position/Bot API, tenant config, hoặc RewardDistributor đều có thể làm sai allocation toàn hệ thống. | Run full daily job sandbox với ≥3 user; check 6-point reconciliation strong alert. |
| WL bot lifecycle state machine (6-state) | Permission + Workflow | FM-ADM-10, FM-MOB-04 | SCR-BADM-18, SCR-MOB-03 | Bot stuck failed_set/needs_repair sẽ ngừng delivery; force-normalize sai two-phase có thể mất route net. | Mỗi transition state, đặc biệt failed_set 48h auto-force-normalize, retry-set re-check (BR-ADM-032). |
| WL Mobile auth (SIWE → JWT) | Permission | FM-MOB-01 | SCR-MOB-01 | Lỗ hổng auth ảnh hưởng toàn bộ data hiển thị mobile (tenant isolation). | Test BR-MOB-003 frontend không override tenant; JWT expiry → silent re-sign (BR-MOB-002). |
| BNZA ↔ Helix HMAC-SHA256 server-to-server | Integration | FM-WLA-04, FM-MOB-04 | (backend) + SCR-MOB-03 | Hỏng auth path WL post-record gây block hoặc spoof. | Test nonce replay, HMAC sai, tx_hash anti-spoof. |
| PF distribution config off-chain | Data state | FM-ADM-02 | SCR-BADM-03 | Vi phạm BR-ADM-015..020 dẫn đến chia thưởng sai. | Test edge case: nhiều remainder, sum vượt, > 10 rows. |
| plan_specs version (Step 8) | Cross-system | FM-PL-02, FM-ADM-04 | SCR-BADM-06, SCR-POOL-03 | Cần simultaneous deploy POOL + OPERATOR + OPS. | Test BotCard outdated warning + immutability. |
| WL partner suspend/resume + master wallet rotation | Data state | FM-ADM-01 | SCR-BADM-02 | Sai có thể dừng/sai routing net của toàn bộ WL. | Test BR-ADM-013/014. |
| Router v2.2.2-fix-2 + LPBot v1.2 ABI breaking change | Integration | FM-MOB-04, FM-PL-01, FM-PL-02 | SCR-MOB-03, SCR-POOL-03 | `closeForUser` 7 args, `startBot` 11 fields, `convertToUsdc` thêm — module dùng sai ABI sẽ fail. | Test mọi call site phải dùng ABI mới. |
| Chain switching guard (Base/OP only cho LP) | Permission/State | FM-MOB-08, FM-PL-01 | All MOBILE + SCR-POOL-* | Arbitrum xuất hiện trong wallet user (vì EX trên Arbitrum) → UI bot ops phải nhắc switch. | Test E-MOB-010 prompt chain switch. |
| Hyperliquid agent key flow | Permission | FM-EX-01..03 | SCR-EX-02 | Agent key store browser — mất → mất quyền trade; mismatch → reject. | Test BR-EX-02..04 + agent rotation. |
| TOKEN screens (mock) | Scope | FM-ADM-07 | SCR-BADM-13..17 | Q-011 mở — nếu giữ pass test sẽ tốn effort vô ích. | Quyết định scope test sau khi BA chốt Q-011. |
| EXBOT Phase A gates (4 điều kiện) | Workflow | FM-XB-09..11 | (no UI) | Phase A không bắt đầu được nếu thiếu zen approve/Vault/encryption/WL stability. | QC theo dõi 4 gate; không design test live HL trước khi gate mở. |

---

## 11. Gaps / conflicts / assumptions

| ID | Issue | Type | Impact to QC | Suggested owner | Priority | Status |
|---|---|---|---|---|---|---|
| GAP-001 | Không có wireframe Figma chính thức; chỉ có ASCII wireframe trong từng `03_modules/<mod>/ascii-screen/`. | Missing | Khó review UI chi tiết, đo độ phủ visual; QA UI cần chờ Figma hoặc dùng code làm proxy. | BA / Designer | Medium | Open |
| GAP-002 | PTL-04 EXBOT Infra không có UI nhưng feature FM-XB-01..13 đều "Missing (screen-side)" trong feature coverage — đây là backend-only và bản chất không có screen. | Assumption | Cần xác nhận với QC Lead là FM-XB-* sẽ KHÔNG có dashboard row screen, chỉ row integration/system test. | QC Lead | Low | Open |
| GAP-003 | TOKEN screens (SCR-BADM-13..17) đều `In scope? = Need confirm` vì `FM-ADM-07` là T3 mock. | Unclear | Nếu giữ pass test cho 5 screen, tốn effort vô ích; nếu bỏ, có thể thiếu coverage tối thiểu. | QC Lead / zen | Low | Open (Q-011) |
| GAP-004 | PTL-06 WL-ADMIN — `intake.md §9` ghi Layer B là Helix build, không phải SOTATEK; `feature-map.md §3.0` vẫn liệt kê đủ FM-WLA-01..07 trong scope. Toàn bộ 7 row WLA trong feature coverage = `Need confirm`. | Conflict | Quyết định toàn bộ effort QC cho PTL-06 và việc có chạy `qc-site-map` cho folder `03_modules/admin/wl-admin/` hay không. | QC Lead / BA / zen | High | Open (Q-014) |
| GAP-005 | SCR-MOB-05 Notifications chưa có FM-* trace. Settings (SCR-MOB-06) một phần trace FM-MOB-09 nhưng không có spec push notification flow. | Missing | Test case Notifications không có expected result. | BA | Medium | Open |
| GAP-006 | SCR-BADM-07 (Users), SCR-BADM-08 (Access Control), SCR-BADM-09 (Audit Logs) đều "maintain" — không có FM-* trace. | Missing | Cross-cutting feature ảnh hưởng nhiều flow; nếu không tạo FM riêng, không có row dashboard. | QC Lead / BA | Medium | Open |
| GAP-007 | SCR-POOL-01/02 (pre-rewrite) và SCR-POOL-06 (superseded) còn trong index — có nên test hay không? | Unclear | Tốn effort nếu test legacy; thiếu regression nếu bỏ. | QC Lead / Dev | Low | Open |
| GAP-008 | URL chính thức PTL-01 (`wl.bnza.io`) và PTL-06 (`wl-admin.bnza.io`) đều TBD. | Missing | Tester không biết môi trường nào để execute. | DevOps / BA | High | Open (gắn Q-012) |
| GAP-009 | Wireframe `bnza-pool/ascii-screen/index.md` `stale_status = unknown`; nhiều file `validated_at`/`validated_by` để trống. | Unclear | Không chắc screen list còn chính xác với codebase hiện tại. | BA | Medium | Open |
| GAP-010 | Không có file "release notes" hoặc "change log" tập trung; mọi thay đổi nằm trong `changelog:` frontmatter từng file. | Missing | Khó theo dõi delta theo phiên bản tài liệu. | BA | Low | Open |
| GAP-011 | Schema D1 cấp WL-ADMIN (25 tables) chỉ có summary trong `intake.md §3 Module 1A` — không có file ERD/DB schema chi tiết trong High-level-files. | Missing | `qc-data-map.md` chỉ derive cấp summary, không có ground truth field-level. | BA / Tech Lead | Medium | Open |
| GAP-012 | OPERATOR DB Schema nằm tại `docs/bnza-docs/{en,jp}/modules/operator/DB_SCHEMA.md` NHƯNG không nằm trong `High-level-files` registered (path-registry). | Conflict (registration) | Skill này không "official" được phép đọc file ngoài High-level-files; nếu cần, QC Lead cần update path-registry. | QC Lead | Medium | Open |

---

## 12. Readiness assessment

| Area | Status | Reason | Required action |
|---|---|---|---|
| Screen inventory | Ready | 43 screen có ID + source ascii-screen index canonical (5 module). | Confirm `stale_status` cho POOL + EX index. |
| Navigation flow | Ready | 8 flow MOBILE + 4 flow WLA + 6 flow BADM + 3 flow POOL + 1 flow EX. Cơ bản đủ cho scenario design. | Bổ sung flow Notifications + flow Audit Logs nếu cần. |
| Role/access by screen | Ready | 7 actor + permission matrix per portal (PTL-01..06) từ `backbone.md §4`. | — |
| Screen-feature mapping | Partial | 42 FM-ID mapped; 5 TOKEN screen `Need confirm` (Q-011); 7 WLA screen `Need confirm` (Q-014); 13 FM-XB-* "Missing (screen-side)" vì backend-only. | Chờ Q-011, Q-014 chốt. |
| Data/API/integration/state touchpoints | Partial | Touchpoint cấp summary đủ; chi tiết field-level chờ FRD/DB schema. | Bổ sung khi OPERATOR DB_SCHEMA + WL-ADMIN 25 tables có chi tiết. |
| Regression/impact usage | Ready | 12 anchor regression đã xác định ưu tiên. | — |
| Dashboard feature-level handoff | Ready | 42 row feature coverage + folder alias blank (Init mode). | Auto-invoke `qc-dashboard-sync` sau khi commit. |
| Data-map baseline usability | Partial | `qc-data-map.md` được tạo cùng init, baseline cấp summary cho ~20 entity. | Bổ sung khi có DB schema chi tiết. |

**Kết luận:** Tạm đủ.
**Ghi chú cho QC Lead:** **Line 1 đã hoàn thành** — tất cả feature FM-MOB-*, FM-ADM-*, FM-EX-*, FM-PL-*, FM-WLC-01, FM-OPW-01→07 đều ✅ Done. Screen/flow/touchpoint Line 1 giữ nguyên làm dependency context. **Line 2 (EXBOT Infra FM-XB-01→13) là phạm vi QC hoạt động duy nhất sắp tới** — backend-only trên PTL-04, còn chờ Q-001 (zen specs) và 4 gate conditions Phase 0.

---

## 13. Folder alias map (Mode 3 only)

> Section này chỉ dùng khi `qc-dashboard-sync` phát hiện UC folder orphan và `qc-site-map` Mode 3 đã reconcile alias. Initialization mode chưa có dữ liệu — để trống.

| Canonical Feature ID | Feature name | Folder alias(es) | Source / Reason | Last reconciled |
|---|---|---|---|---|
| (chưa có) | — | — | — | — |
