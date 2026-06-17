---
source_skill: qc-site-map
handoff_type: site-map-feature-coverage
mode: update (Line scope split)
generated_at: 2026-06-17T09:00:00+07:00
line_scope_note: "Line 1 ĐÃ HOÀN THÀNH (QC done). Line 2 (FM-XB-01→13) là phạm vi QC hoạt động duy nhất sắp tới."
---

# Site Map Handoff for Dashboard — Bonanzapool (BNZA Ecosystem — SOTATEK Scope)

## Feature-level site map coverage

| Feature ID | Feature name | Site / Portal | Module | Mapped screen(s) | Folder alias(es) | In scope? | Site map status | Notes |
|---|---|---|---|---|---|---|---|---|
| FM-WLA-01 | Distribution Pipeline | PTL-06 wl-admin.bnza.io (TBD) | WL-ADMIN | SCR-WLA-02 wl-distribution-jobs; SCR-WLA-01 wl-dashboard | — | Need confirm | Mapped | Q-014 mở — Layer B Helix build hay SOTATEK build. |
| FM-WLA-02 | Reward Computation Engine | PTL-06 | WL-ADMIN | SCR-WLA-03 wl-users (Cap); SCR-WLA-06 wl-reward-settings | — | Need confirm | Partial | Backend logic — không có screen riêng. Q-014 + Q-004..Q-008 mở. |
| FM-WLA-03 | RewardDistributor Integration | PTL-06 + on-chain Base/OP | WL-ADMIN | SCR-WLA-05 wl-distributor-contract | — | Need confirm | Mapped | Multisig pause/unpause. Q-014. |
| FM-WLA-04 | BNZA API Integration (3 stream HMAC) | PTL-06 ↔ PTL-04 | WL-ADMIN ↔ OPERATOR | SCR-WLA-01 wl-dashboard (health) | — | Need confirm | Partial | Backend HMAC-SHA256. Q-014. |
| FM-WLA-05 | Admin Console — 7 page | PTL-06 | WL-ADMIN | SCR-WLA-01..07 + 9 supporting modal | — | Need confirm | Mapped | Mọi write yêu cầu reason note M9 + Slack mirror. Q-014. |
| FM-WLA-06 | Multi-tenant Config | PTL-06 | WL-ADMIN | SCR-WLA-06 wl-reward-settings | — | Need confirm | Mapped | tenants D1 table. Q-014. |
| FM-WLA-07 | Daily Reconciliation (6-point cron UTC 06:00) | PTL-06 | WL-ADMIN | SCR-WLA-01 wl-dashboard (alerts) | — | Need confirm | Partial | Backend cron. Q-014. |
| FM-MOB-01 | SIWE Auth + WL Gate | PTL-01 wl.bnza.io (TBD) | BNZA-MOBILE | SCR-MOB-01 scr-wl-gate | — | Yes | Mapped | T0 WL Launch. |
| FM-MOB-02 | Reward Display | PTL-01 | BNZA-MOBILE | SCR-MOB-02 scr-home | — | Yes | Mapped | T0. Post-allocation only (BR-MOB-004). |
| FM-MOB-03 | Claim USDC | PTL-01 | BNZA-MOBILE | SCR-MOB-02 (claimable card) | — | Yes | Partial | Không có screen riêng, dùng modal trong scr-home. |
| FM-MOB-04 | Bot Operations | PTL-01 | BNZA-MOBILE | SCR-MOB-03 scr-bot; SCR-MOB-04 scr-position (stop) | — | Yes | Mapped | T0. WL bot ép convertToUsdc=true, autoCompound=false. |
| FM-MOB-05 | LP Bot Status | PTL-01 | BNZA-MOBILE | SCR-MOB-03 scr-bot; SCR-MOB-04 scr-position | — | Yes | Mapped | T0. |
| FM-MOB-06 | Community / Referral Tree | PTL-01 | BNZA-MOBILE | SCR-MOB-07 scr-community | — | Yes | Mapped | T1. |
| FM-MOB-07 | Multi-tenant Branding | PTL-01 | BNZA-MOBILE | (cross-cutting — apply globally) | — | Yes | Partial | Ảnh hưởng mọi screen; không có screen dedicated. |
| FM-MOB-08 | Chain Switching | PTL-01 | BNZA-MOBILE | Header all screens | — | Yes | Mapped | T1. Base + OP only. |
| FM-MOB-09 | Settings | PTL-01 | BNZA-MOBILE | SCR-MOB-06 scr-settings | — | Yes | Mapped | T1. |
| FM-MOB-10 | PWA | PTL-01 | BNZA-MOBILE | (cross-cutting — manifest + SW + offline shell) | — | Yes | Partial | Không có screen — verify install + offline. |
| FM-MOB-11 | i18n | PTL-01 | BNZA-MOBILE | (cross-cutting) | — | Yes | Partial | T2. Verify mọi screen render đúng locale. |
| FM-ADM-01 | WL Partner Onboarding + Member + Master Wallet | PTL-02 ops.bnza.io | BNZA-ADMIN | SCR-BADM-02 whitelabel | — | Yes | Mapped | T0. Boundary BNZA-ADMIN vs WL-ADMIN. |
| FM-ADM-02 | PF Distribution Config | PTL-02 | BNZA-ADMIN | SCR-BADM-03 fee-distribution | — | Yes | Mapped | T0. Q-002 mở (WL 70/30 remittance flow). |
| FM-ADM-03 | IB Management | PTL-02 | BNZA-ADMIN | SCR-BADM-04 ib | — | Yes | Mapped | T1. Replace mockIBs. |
| FM-ADM-04 | Bot Type Config | PTL-02 | BNZA-ADMIN | SCR-BADM-05 bots; SCR-BADM-06 plans | — | Yes | Mapped | T1. cooldown 10–180 min. |
| FM-ADM-05 | Dashboard (real metrics) | PTL-02 | BNZA-ADMIN | SCR-BADM-01 dashboard | — | Yes | Mapped | T2. KV-cached 5 min TTL. |
| FM-ADM-06 | Reports | PTL-02 | BNZA-ADMIN | SCR-BADM-12 reports | — | Yes | Mapped | T2. |
| FM-ADM-07 | TOKEN Management (mock) | PTL-02 | BNZA-ADMIN | SCR-BADM-13 burn; SCR-BADM-14 supply; SCR-BADM-15 vesting; SCR-BADM-16 treasury; SCR-BADM-17 builder-fee | — | Need confirm | Mapped | T3 mock. Q-011 mở. |
| FM-ADM-08 | System Settings | PTL-02 | BNZA-ADMIN | SCR-BADM-10 system-settings | — | Yes | Mapped | T2. |
| FM-ADM-09 | Relayer Monitor | PTL-02 | BNZA-ADMIN | SCR-BADM-11 relayer | — | Yes | Mapped | T2. |
| FM-ADM-10 | WL Bot Lifecycle Monitor (6-state) | PTL-02 | BNZA-ADMIN | SCR-BADM-18 wl-monitor | — | Yes | Mapped | T1. State machine 6-state. |
| FM-EX-01 | TradingView Integration (Advanced Charts) | PTL-03 ex.bnza.io | BNZA-EX | SCR-EX-02 trade | — | Yes | Mapped | T2. License OQ-3 resolved. |
| FM-EX-02 | Chart Data Feed (Hyperliquid WS → UDF) | PTL-03 | BNZA-EX | SCR-EX-02 trade; SCR-EX-01 portfolio (read) | — | Yes | Mapped | T2. Trực tiếp HL, không qua OPERATOR. |
| FM-EX-03 | Order Placement (click-to-trade + TP/SL) | PTL-03 | BNZA-EX | SCR-EX-02 trade | — | Yes | Mapped | T2. |
| FM-XB-01 | EXBOT D1 Schema (9 tables) | PTL-04 api.bnza.io | BNZA-EXBOT Infra | (no UI — backend) | — | Yes | Missing | Backend-only. Q-001 blocker. |
| FM-XB-02 | EXBOT Queue Topology (6 queue) | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-03 | EXBOT Durable Objects | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-04 | EXBOT Cron Jobs | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-05 | HL Adapter | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-06 | EXBOT API Endpoints | PTL-04 | BNZA-EXBOT Infra | (no UI — trigger qua PTL-02 future) | — | Yes | Missing | Backend-only. |
| FM-XB-07 | Router Extension (Solidity) | On-chain | BNZA-EXBOT Infra | (no UI — Solidity) | — | Yes | Missing | Smart contract. |
| FM-XB-08 | OPERATOR API EXBOT Endpoints | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-09 | Phase A1 — Dry Run | PTL-04 + HL testnet | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-10 | Phase A2 — Live $1k Test | PTL-04 + HL mainnet | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Backend-only. |
| FM-XB-11 | Phase A3 — Closed Beta 5–10 WL user | PTL-04 + PTL-01 | BNZA-EXBOT Infra ↔ MOBILE | (mobile UI dùng tạm) | — | Yes | Partial | UI mobile được tận dụng. |
| FM-XB-12 | Envelope Encryption | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | CF Secrets Store. |
| FM-XB-13 | Pre-launch Hotfixes | PTL-04 | BNZA-EXBOT Infra | (no UI) | — | Yes | Missing | Bug fix. |
| FM-PL-01 | Step 7 Multi-Bot | PTL-05 pool.bnza.io | BNZA-POOL | SCR-POOL-03 bot; SCR-POOL-07 positions; SCR-POOL-04 dashboard | — | Yes | Mapped | T1. BotCard grid, max 10/chain. |
| FM-PL-02 | Step 8 plan_specs Version Management | PTL-05 + PTL-02 + PTL-04 | BNZA-POOL + BNZA-ADMIN | SCR-POOL-03 bot (warning); SCR-BADM-06 plans (mgmt) | — | Yes | Mapped | T1/T2. Cần simultaneous deploy. |

## Feature-level gaps

| Feature ID | Feature name | Gap | Impact to QC | Owner | Priority |
|---|---|---|---|---|---|
| FM-WLA-01..07 (toàn bộ) | WL-ADMIN scope | `intake.md §9` nói Layer B là Helix build, không phải SOTATEK; `feature-map.md §3.0` vẫn liệt kê đầy đủ trong scope SOTATEK. | Quyết định toàn bộ effort QC cho PTL-06. (Q-014.) | QC Lead / BA / zen | High |
| FM-WLA-02 | Reward Computation Engine | 5 WL operator open question chưa chốt: same-rank bonus eligibility (Q-004), leader airdrop formula (Q-005), Cap policy (Q-006), AUM=0 handling (Q-007), cross-chain claim UX (Q-008). | Reward engine test design không có expected result. | WL operator (BA escalate) | High |
| FM-ADM-02 | PF Distribution | OQ-6 (Q-002): cơ chế daily remittance WL 70/30 chưa rõ. | Không xác định expected result remittance flow. | BA / Tech Lead | High |
| FM-ADM-07 | TOKEN Management (mock) | Q-011: chưa rõ có cần QC pass 5 screen TOKEN mock hay không. | Có thể tốn effort cho feature ngoài scope. | QC Lead / zen | Low |
| FM-XB-01..13 (toàn bộ) | EXBOT Infra | OQ-2 (Q-001): zen interface specs (D1 schema, Queue topology, API contract) chưa có. | Blocker Line 2; không thiết kế test FM-XB family. | zen (BA escalate) | High |
| FM-MOB-10 / FM-MOB-11 | PWA / i18n | Cross-cutting, không có screen riêng — readiness Partial. | Test plan PWA install + i18n cần verify trên mọi screen. | QC Lead | Medium |
| FM-PL-02 | Step 8 plan_specs | Cần simultaneous deploy POOL + OPERATOR + OPS — coordination chưa có gate cụ thể. | Regression scope cross-portal phức tạp. | Dev / DevOps | Medium |
| FM-EX-01..03 | EX Trading | Stack plain JavaScript (không TS) khác hẳn ADMIN/POOL — coverage tool/test framework có thể khác. | Test harness cần xác nhận. | QC Lead / Dev | Low |

## Unmapped screens

| Screen ID | Screen / Page | Why unmapped | Suggested action |
|---|---|---|---|
| SCR-MOB-05 | Notifications (`/notifications`) | Không có FM-* trace; BA chưa định nghĩa push notification flow. | Hỏi BA gán FM-* hoặc xác nhận là maintain feature. |
| SCR-BADM-07 | User Management | Mark "maintain" trong ascii-screen index — không có FM-*. | Tạo FM-ADM-USER hoặc xác nhận là cross-cutting. |
| SCR-BADM-08 | Access Control | "maintain" — không có FM-*. | Tạo FM-ADM-ACCESS hoặc xác nhận. |
| SCR-BADM-09 | Audit Logs | "maintain" — không có FM-*. | Tạo FM-ADM-AUDIT hoặc xác nhận. |
| SCR-POOL-01 | Bot Create (pre-rewrite) | Historical — superseded by SCR-POOL-03 Bot canonical. | Quyết định có test legacy hay không (GAP-007). |
| SCR-POOL-02 | Bot Monitor (pre-rewrite) | Historical — superseded by SCR-POOL-03. | Như trên. |
| SCR-POOL-06 | Pool List | Superseded by SCR-POOL-05 Pairs. | Như trên. |
| (PTL-04 EXBOT Infra) | All FM-XB-01..13 | Backend-only — không có screen. | Quyết định cách track FM-XB trong dashboard (integration/system row riêng). GAP-002. |

## Dashboard update recommendation

| Feature ID | Line | QC Status | Recommended dashboard note | Reason |
|---|---|---|---|---|
| FM-WLA-01..07 (7 row) | L1 | ✅ Done | OOS (Helix scope). Giữ row nhưng đánh dấu Done. | Line 1 hoàn thành. Dependency context only. |
| FM-MOB-01..11 (11 row) | L1 | ✅ Done | Giữ row, đánh dấu Done. | Line 1 hoàn thành. |
| FM-ADM-01..10 (10 row) | L1 | ✅ Done | Giữ row, đánh dấu Done. | Line 1 hoàn thành. |
| FM-EX-01..03 (3 row) | L1 | ✅ Done | Giữ row, đánh dấu Done. | Line 1 hoàn thành. |
| FM-PL-01..02 (2 row) | L1 | ✅ Done | Giữ row, đánh dấu Done. | Line 1 hoàn thành. |
| FM-XB-01..13 (13 row) | **L2** | 🔜 **ACTIVE** | **PHẠM VI QC DUY NHẤT.** Backend-only, no UI. Chờ Q-001 zen specs. | Line 2 — phạm vi QC hoạt động duy nhất sắp tới. |
