---
type: backbone
status: in-review
created: 2026-05-20
updated: "2026-06-18"
owner: "@hien.duong"
engagement_mode: formal
lang: en
priority: P0
tags: []
version: "0.7.0"
links:
  - ../../01_intake/intake.md
changelog:
  - "2026-06-18 | /ba-do hld-decisions | §5.4 FM-XB-07/08: drop park/redeploy, update states; §8.7: strategy dispatch pattern + PositionManager NFT custody + emergencyTransfer Operator-only; §8.9.2 Phase 0: remove multiSig; §8.9.6: update bot_safe_close rule"
  - "2026-06-17 | /ba-do propagation | add FM-ADM-11 and FM-ADM-12 entries to §5.2; update FM-ADM-06 description (add WL OpFee/PF Breakdown)"
  - "2026-06-16 | /ba-impact | absorb WL_SPECv1.7.6_EN.md + DELTA v1.7.5→v1.7.6 + WL_HANDOVER_EN + WL_ADMIN_API_GUIDE_EN + WL_API_CONNECTION_GUIDE_EN: §5.2 FM-ADM-01 API surface + state machines; §8.10 WL API Surface (new); §11 Source Traceability updated with 5 new entries"
  - "2026-06-12 | manual | §8.9: absorb SPEC_v5.2.6_EN.md key content inline — Phase 0 conditions, NV-1–14 table, all formulas (LP calc, hedge target, stop price, margin thresholds, preflight), price 3-way split, behavioral rules; §11: add source row"
  - "2026-06-08 | manual | OOS markings: PTL-01/PTL-06 + ACT-03/ACT-07 (§2/§3); §4.1/§4.7 OOS banners; §5.0/§5.0B OOS banners; §6 deps (remove Helix-side rows); §7 priorities (remove FM-WLA/FM-MOB); §0 delivery structure updated; §8.8 context-only note added"
  - "2026-06-04 | /ba-impact | sync WL_SPEC_SOTATEK_EN_v1.1 §4.4: thêm §8.1 WL post-record auth row (HMAC-SHA256 Helix server-to-server, CORS N/A, explicit starter wallet); clarify §6 stream 3 endpoint path (atomic-start/stop)"
  - "2026-06-04 | /ba-impact | sync with WL_SPEC_SOTATEK_EN_v1.0: expand FM-ADM-01 (member lifecycle + master wallet); reduce FM-ADM-02 (BnzaSplitter removed, off-chain only); add FM-ADM-10 (WL bot lifecycle monitor); add ADMIN→OPERATOR WL lifecycle dependency; update fee model PF row (pfCollector single EOA); update §8.8.3 money flow (pfCollector + wlMaster)"
  - "2026-06-02 | manual | admin module boundary: rewrite §5.0 FM-WLA (thêm screen mapping, DB summary, supporting modals); rewrite §5.2 BNZA-ADMIN (thêm actor/folder/boundary note; expand FM-ADM-01→09 descriptions); update PTL-06 tech stack §2; thêm §4.7 WL-ADMIN permissions; update §8.1 auth model (split BNZA-ADMIN vs WL-ADMIN rows); thêm §8.8.9 admin boundary table + interaction point"
  - "2026-06-01 | manual | rewrite §11 Source Traceability: replace external paths with inline absorption map; all content now self-contained"
  - "2026-06-01 | manual | add §8.8 WL+MLM System Architecture: inline 3-layer structure, money flow, terminology, rank/title tables, title differential method, distribution pipeline — BA doc self-contained"
  - 2026-06-01 | manual | consolidate PTL-07 (WL Mobile) into PTL-01 (BNZA-MOBILE) as single WL Mobile module; remove PTL-07 row; rewrite FM-MOB feature map (remove EXBOT/Margin, add Reward/Claim/Community/SIWE); update permissions, auth model, dependencies
  - 2026-06-01 | manual | add 2-line delivery structure; add WL+MLM modules (wl-admin PTL-06, wl-mobile PTL-07); add ACT-07 WL Operator Admin; update portal matrix, permissions, feature map, dependency table
  - "2026-06-01 | manual | absorb WL_SPEC §7B/§7C: add 3 BNZA→WL API streams to dependency table; updated: 2026-06-01"
  - "2026-05-27 | manual | meeting 2026-05-27: revised §7 priority (EXBOT removed from Tier 0, MLM-first, June 2 date); flagged 10k bot scale as under review"
  - "2026-05-26 | manual | update from SPEC v5.2.5 + ECOSYSTEM_OVERVIEW v2.0: added §8.7 EXBOT contract architecture (BnzaExVault Option C), Phase 0 gate note in §5.4 FM-XB"
  - "2026-05-26 | manual | sync client-docs: updated §8.2 fee model with PF ratio split (0.2970075 vs 0.2985 per convert_to_usdc); added Router v2.2.2 breaking changes note"
  - "2026-05-21 | manual | codebase audit: corrected tech stacks, portal matrix versions, deployment topology, added §8.7 Codebase Maturity Assessment, updated OQ status"
  - "2026-05-20 | /ba-start | resolved OQ-1: Monorepo, updated §8.4 deployment topology"
  - 2026-05-20 | /ba-start | initial backbone from intake
---

# BNZA Ecosystem — SOTATEK Scope: Requirements Backbone

## Markers

- **📋 Spec** — feature is in the original client spec
- **⚡ Dev-built** — feature was built by dev team, NOT in client spec

---

## 0. Delivery Structure

| Line | Scope | Modules |
|------|-------|---------|
| **Line 1** | WL + MLM system development + maintain Pool/Exchange | `smart-contracts` (BnzaRouterUpgradeable + BnzaLpBot), `bnza-operator-wl` (PTL-04 WL backend), `admin`, `bnza-pool`, `bnza-ex` |
| **Line 2** | Exchange Bot + Backtest development | `exbot`, `backtest` (TBD) |
| **Integration point** | ExBot integrated into WL (future milestone) | Lines converge when ExBot replaces/extends LPBot as WL bot engine |

> **OOS note:** `wl-admin` (PTL-06) and `wl-mobile` (PTL-01) are Helix-owned — Sotatek scope does NOT include building or maintaining these systems. See §5.0 and §5.0B for reference-only content.

---

## 1. Shared Actors

| Actor ID | Name | Description | Auth Mechanism |
|----------|------|-------------|----------------|
| ACT-01 | End User (LP) | Retail user who creates/manages LP Bots, views earnings, deposits/withdraws | Wallet connect (X-Wallet-Address header) |
| ACT-02 | WL Partner | Institutional broker using branded MLM platform, viewing earnings, managing end-users | Wallet connect + WL invite code verification |
| ACT-03 | WL End User | MLM participant under a WL operator, using the WL Mobile app | SIWE (Sign-In with Ethereum) → 24h JWT; tenant resolved by subdomain + signature domain |
| ACT-04 | Admin (zen) | System administrator, full access ADMIN portal | Wallet connect + Cloudflare Access (zen@bnza.io) |
| ACT-05 | Trader | Perpetuals trader on the EX platform (Hyperliquid) | Wallet connect (direct Hyperliquid, no OPERATOR) |
| ACT-06 | OPERATOR (System) | Backend automation — cron jobs, relayers, queue consumers | Internal (no user auth, system-level) |
| ACT-07 | WL Operator Admin | WL operations team — monitors/operates daily reward distribution, manages referral tree, handles incidents | SSO (Cloudflare Access) + 2FA (TOTP) |

---

## 2. Portal Matrix

| Portal ID | Domain | Project | Tech Stack (verified 2026-05-21) | Hosting | Auth Layer |
|-----------|--------|---------|------------|---------|------------|
| PTL-01 **[OOS — Helix scope]** | wl.bnza.io (TBD) | WL Mobile | Vite + React 19 + TS 5.9 + Zustand + Tailwind 4 + shadcn/ui + Reown AppKit + PWA | CF Pages | SIWE/JWT (24h) |
| PTL-02 | ops.bnza.io | BNZA-ADMIN | React 19.2 + Vite 8.0 + TS 5.9 + Tailwind 4.2 + shadcn/ui + React Router 7.14 + TanStack Query 5.100 | CF Pages | Wallet + CF Access + RBAC |
| PTL-03 | ex.bnza.io | BNZA-EX | React 18.3 + Vite 6.0 + JavaScript (no TS) + Wagmi 3.6 + @nktkas/hyperliquid 0.32 | CF Pages | Wallet (direct HL) |
| PTL-04 | api.bnza.io/exbot | BNZA-EXBOT Infra | CF Workers (standalone `apps/bnza-exbot/`) + D1 (ExBot schema) + 8 Queues + DO (3: HLRateLimitDO, UserLockDO, MarketDataDO) | CF Workers | Internal (service binding from OPERATOR) |
| PTL-05 | pool.bnza.io | BNZA-POOL Steps 7-8 | Next.js 16.2 + React 19.2 + TS 5.9 + Tailwind 4 + shadcn/ui + Wagmi 2.19 + TanStack Query 5.94 | Vercel | Wallet |
| PTL-06 **[OOS — Helix scope]** | wl-admin.bnza.io (TBD) | WL Admin System (bnza-wl-admin) | CF Pages (frontend) + CF Workers (backend/cron) + CF D1 (25 tables) + CF Queues | CF Pages + CF Workers | SSO (CF Access) + 2FA (TOTP mandatory); roles: Super / Operator / Read-only |

---

## 3. Permissions Matrix — Cross-Project (Actor × Portal Access)

| Actor | PTL-01 WL MOBILE **[OOS]** | PTL-02 ADMIN | PTL-03 EX | PTL-04 EXBOT Infra | PTL-05 POOL | PTL-06 WL Admin **[OOS]** |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| ACT-01 End User | — | — | Full | — | Full | — |
| ACT-02 WL Partner | View earnings | — | — | — | — | — |
| ACT-03 WL End User **[OOS — Helix scope]** | Full | — | — | — | — | — |
| ACT-04 Admin (zen) | — | Full | — | Config | Full | — |
| ACT-05 Trader | — | — | Full | — | — | — |
| ACT-06 OPERATOR | — | — | — | Full (system) | — | — |
| ACT-07 WL Operator Admin **[OOS — Helix scope]** | — | — | — | — | — | Full |

**Legend**: Full = all features; Config = API management endpoints only; View earnings = read-only dashboard; — = no access

---

## 4. Permissions Matrix — Per-Project (Actor × Actions)

### 4.1 WL Mobile (PTL-01)

> **⚠️ OUT OF SCOPE — Helix (WL operator) owned. Sotatek scope = BNZA-OPERATOR backend + smart contracts only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B. Kept as reference only.**

| Action | ACT-03 WL End User | ACT-02 WL Partner |
|--------|:---:|:---:|
| Sign in via SIWE (wallet connect + sign) | ✅ | ✅ |
| View fee reward + referral reward (post-allocation) | ✅ | ✅ (own users) |
| View claimable balance | ✅ | — |
| Claim USDC (RewardDistributor.claim()) | ✅ | — |
| View LP Bot positions (from admin system API) | ✅ | ✅ (own users) |
| Start Bot (zapMint via user wallet, wl_code) | ✅ | — |
| Stop Bot (via user wallet) | ✅ | — |
| View community / referral tree | ✅ | ✅ |
| Switch chain (Base/OP) | ✅ | ✅ |

### 4.2 BNZA-ADMIN (PTL-02)

| Action | ACT-04 Admin (zen) |
|--------|:---:|
| WL Partner onboarding (create/edit/deactivate) | ✅ |
| WL Partner earnings tracking | ✅ |
| WL Payout history & remittance trigger | ✅ |
| PF Distribution dashboard (70% user / 30% BNZA) | ✅ |
| IB Management (real data) | ✅ |
| Bot Type Configuration (tiers, strategy params, limits) | ✅ |
| TOKEN Management (burn/supply/vesting/treasury) | ✅ |
| Dashboard (real metrics) | ✅ |
| System Settings | ✅ |
| Relayer monitoring | ✅ |
| Reports | ✅ |
| Bot plan_specs version management (Step 8) | ✅ |
| Bot list + force-stop (Step 8) | ✅ |

### 4.3 BNZA-EX (PTL-03)

| Action | ACT-01 End User | ACT-05 Trader |
|--------|:---:|:---:|
| View TradingView Advanced Charts | ✅ | ✅ |
| Place perpetual orders (Hyperliquid) | ✅ | ✅ |
| View positions & PnL | ✅ | ✅ |
| Manage margin | ✅ | ✅ |

### 4.4 BNZA-EXBOT Infrastructure (PTL-04)

| Action | ACT-06 OPERATOR (System) | ACT-04 Admin |
|--------|:---:|:---:|
| Queue processing (bot-scan, light-check, hedge-sync, reconcile, deep-audit, price-near-stop-audit, partial_repair, user_redeem, notification, metrics-rollup) | ✅ | — |
| Cron execution (deep-audit) | ✅ | — |
| D1 read/write (ExBot tables) | ✅ | — |
| Durable Object management (HLRateLimitDO, UserLockDO, MarketDataDO) | ✅ | — |
| API: start bot (via Operator facade) | — | ✅ |
| API: status bot (via Operator facade) | — | ✅ |
| API: close bot (via Operator facade) | — | ✅ |
| API: agent-key management | — | ✅ |
| API: margin adjustment | — | ✅ |
| Hyperliquid adapter calls | ✅ | — |

### 4.5 BNZA-POOL Steps 7-8 (PTL-05)

| Action | ACT-01 End User | ACT-04 Admin |
|--------|:---:|:---:|
| View Active Bots (multi-bot grid) | ✅ | ✅ |
| Create new Bot (max 10/chain) | ✅ | — |
| Start/Stop Bot (wallet TX) | ✅ | — |
| Switch chain (Base/OP) | ✅ | ✅ |
| View BotCard (status, invested, earnings) | ✅ | ✅ |
| See outdated plan_specs warning | ✅ | ✅ |
| Manage plan_specs versions (Step 8 OPS) | — | ✅ |
| Force-stop Bot (Step 8 OPS) | — | ✅ |

### 4.7 WL Admin System (PTL-06)

> **⚠️ OUT OF SCOPE — Helix (WL operator) owned. Sotatek scope = BNZA-OPERATOR backend + smart contracts only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B. Kept as reference only.**

| Action | ACT-07 Super | ACT-07 Operator | ACT-07 Read-only |
|--------|:---:|:---:|:---:|
| View Distribution Jobs (all chains) | ✅ | ✅ | ✅ |
| Recover BLOCKED distribution job | ✅ | ✅ | — |
| Force skip (ABANDONED) | ✅ | — | — |
| Manual GO (PENDING_SNAPSHOT) | ✅ | ✅ | — |
| View Users (cumulative, Cap, lineage) | ✅ | ✅ | ✅ |
| Manually add user to referral tree | ✅ | ✅ | — |
| Change referral parent | ✅ | ✅ | — |
| Regenerate tree snapshot | ✅ | ✅ | — |
| View Distributor Contract (balance, headroom) | ✅ | ✅ | ✅ |
| Refill Treasury → Distributor | ✅ | ✅ | — |
| Propose setDailyLimit / setMinPayout (multisig) | ✅ | — | — |
| Emergency Pause RewardDistributor | ✅ | — | — |
| Edit Reward Settings (rank/title/referral/Cap) | ✅ | — | — |
| Manage Admins & Auth (invite/role/policy) | ✅ | — | — |

**Legend**: Super = all features; Operator = distribution ops + tree + refill, no settings; Read-only = view only

---

## 5. Feature Map

### 5.0 WL Admin System — PTL-06 (Priority: P0 — Line 1 Core)

> **⚠️ OOS — Helix (WL operator) scope. Sotatek does NOT build or maintain this system. Kept as reference only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B.**
> All files in `03_modules/admin/wl-admin/` are marked `status: out-of-scope`.

**Actor**: ACT-07 (WL Operator Admin) | **Role**: Layer B — compute MLM allocation + on-chain payout
**Folder**: `03_modules/admin/wl-admin/` (WL-ADMIN sub-system, screens prefixed `wl-`)

| Sub-module | Description | Priority | Screens (§3 WL_ADMIN_SPEC) |
|------------|-------------|----------|---------------------------|
| FM-WLA-01: Distribution Pipeline **[OOS — Helix]** | Daily job state machine: BOT_SYNC → LEDGER_FETCH → PENDING_SNAPSHOT → SNAPSHOT → UPLINE → COMPUTED → ENQUEUED → ONCHAIN → VALIDATED → COMPLETED. BLOCKED recovery per phase. | P0 | `wl-distribution-jobs` |
| FM-WLA-02: Reward Computation Engine **[OOS — Helix]** | Rank reward (30–62% of net) + title differential V1–V7 (MLM-pool basis, structurally non-breakable) + same-rank bonus (5% envelope) + leader token airdrop (V4+, non-USDC, bonus_airdrops) | P0 | (backend, no dedicated screen) |
| FM-WLA-03: RewardDistributor Integration **[OOS — Helix]** | Push/Claim hybrid payout via on-chain RewardDistributor (Base + OP). clientNonce idempotency. Cap double-check before ONCHAIN send. | P0 | `wl-distributor-contract` |
| FM-WLA-04: BNZA API Integration **[OOS — Helix]** | Ledger API HMAC-SHA256 pull (stream 1, net per user per chain) + Position API (stream 2, AUM for rank/Cap) + Bot Operations API (stream 3, bot start/stop wl_code) | P0 | `wl-dashboard` (health indicators) |
| FM-WLA-05: Admin Console **[OOS — Helix]** | 7 pages + 9 supporting modals. PC-only (min 1280px). SSO + 2FA. All writes require reason note + Slack audit mirror. | P0 | `wl-dashboard`, `wl-distribution-jobs`, `wl-users`, `wl-referral-tree`, `wl-distributor-contract`, `wl-reward-settings`, `wl-admins-auth` |
| FM-WLA-06: Multi-tenant Config **[OOS — Helix]** | Tenant config per WL operator: brand (name/logo/theme), chains, wallet addresses (pool/distributor/treasury), rank table, title table, referral rates, Cap, minPayout. No WL-specific values hardcoded. | P1 | `wl-reward-settings` (tabs: Rank / Title / Referral / Cap / Bonus) |
| FM-WLA-07: Daily Reconciliation **[OOS — Helix]** | 6-point reconciliation cron (UTC 06:00): ledger↔compute, compute↔accrual, payment↔on-chain, cumulative invariant, pool validation, unexpected addRewards detection. Strong alert on delta. | P1 | `wl-dashboard` (alerts panel) |

**Supporting modals** (all require reason note M9): Emergency stop (M1) / BLOCKED recovery (M2) / Failed payment drawer (M3) / Manual add user (M4) / Add/change referral edge (M5) / Snapshot regeneration (M6) / Refill/cap change (M7) / Admin invite (M8) / Reason input (M9)

**DB**: 25 D1 tables — Master (5: tenants, rank_tiers, title_tiers, referral_levels, reward_settings) / User (3: users, referral_edges, tree_snapshots) / Ledger (2) / Distribution (8) / On-chain (3) / Position (1: bot_positions_mirror) / Operations (3: admins, audit_logs, alerts)

### 5.0B WL Mobile (PTL-01) — (Priority: P0 — Line 1 Core)

> **⚠️ OOS — Helix (WL operator) scope. Sotatek does NOT build or maintain this system. Kept as reference only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B.**
> All files in `03_modules/mobile/` are marked `status: out-of-scope`.

> Previously listed as separate PTL-07. Consolidated into PTL-01 (single module, single codebase).

| Sub-module | Description | Priority | Source |
|------------|-------------|----------|--------|
| FM-MOB-01: SIWE Auth + WL Gate **[OOS — Helix]** | Wallet connect → SIWE sign-in → 24h JWT; tenant resolved by subdomain + signature domain | P0 | WL_MOBILE_SPEC §2.1 |
| FM-MOB-02: Reward Display **[OOS — Helix]** | Fee reward + referral reward + leader perk (post-allocation only, no raw LP fees); all data from admin system API | P0 | WL_MOBILE_SPEC §5.1, §6 |
| FM-MOB-03: Claim USDC **[OOS — Helix]** | Claim from RewardDistributor (user-borne gas); sync after claim via Transfer event + supplementary POST | P0 | WL_MOBILE_SPEC §4 |
| FM-MOB-04: Bot Operations **[OOS — Helix]** | Bot start (zapMint via user wallet, wl_code propagation) + stop; Base/OP only | P0 | WL_MOBILE_SPEC §3 |
| FM-MOB-05: LP Bot Status **[OOS — Helix]** | Active positions list from admin system API; AUM, status, started_at; no raw uncollected fees | P0 | WL_MOBILE_SPEC §5.2 |
| FM-MOB-06: Community / Referral Tree **[OOS — Helix]** | Team TVL, direct referral count, total downline, per-tier rates, downline list | P1 | WL_MOBILE_SPEC §5.3 |
| FM-MOB-07: Multi-tenant Branding **[OOS — Helix]** | Logo, theme color, rank table, title table, referral tiers from tenant config API | P1 | WL_MOBILE_SPEC §7 |
| FM-MOB-08: Chain Switching **[OOS — Helix]** | Base (8453) + OP (10) only; Arbitrum excluded; persists in localStorage | P1 | WL_MOBILE_SPEC §0 |
| FM-MOB-09: Settings **[OOS — Helix]** | Language (ja/en per tenant), network, font size, wallet disconnect | P1 | WL_MOBILE_SPEC §5.4 |
| FM-MOB-10: PWA **[OOS — Helix]** | Manifest, service worker, 100dvh, safe-area, offline shell | P1 | WL_MOBILE_SPEC §9 |
| FM-MOB-11: i18n **[OOS — Helix]** | ja/en minimum; per tenant-supported languages | P2 | WL_MOBILE_SPEC §5.4 |

### 5.2 BNZA-ADMIN (PTL-02) — (Priority: P0 — WL Launch Critical)

**Actor**: ACT-04 (zen) | **Role**: Manage BNZA product infrastructure + WL partner accounts
**Folder**: `03_modules/admin/bnza-admin/` (BNZA-ADMIN sub-system, screens without `wl-` prefix)

> Note: FM-ADM-01 creates WL partner accounts (onboarding). Daily MLM operations for those partners run on PTL-06 (FM-WLA-01→07), not here.

| Sub-module | Description | Priority | Effort |
|------------|-------------|----------|--------|
| FM-ADM-01: WL Partner Onboarding + Member + Master Wallet Management | Create/edit/deactivate WL partner records: name, logo (CF R2), referral code (auto 8-char or manual), deposit tier (1k/5k/10k), main wallet, languages, status. View partner earnings summary + payout history. **Thêm mới (WL_SPEC v1)**: (a) wl_members lifecycle — register member (wallet + wl_code), two-phase leave (pending_unset → unset confirmed → left), rejoin (membership_epoch++); (b) wl_master_wallets per chain — địa chỉ nhận net thay WL pool, rotation two-phase (unset old → set new on-chain); (c) wl_codes.status suspend/resume — dừng toàn bộ delivery cho WL. | P0 | 1.5w |

> **[EXPANDED SCOPE — WL_SPEC_SOTATEK_EN_v1.0 §6, §9.2, §9.3]**
> Client spec cũ (WL_SPEC.md §1): chỉ nói "WL code issuance + WL pool wallet registration" — không có member lifecycle.
> Spec mới: 3 concerns mới thuộc BNZA-ADMIN:
> (a) `wl_members` — mỗi WL user là 1 row; leaving là two-phase (không instant NULL vì net có thể
>     đang in-flight đến old master); `membership_epoch` dùng để Helix tách distribution trước/sau leave.
> (b) `wl_master_wallets` — thay thế concept "WL pool wallet"; net đi đến 1 master account per WL per chain.
> (c) Suspend/resume `wl_code` — khi suspend, toàn bộ daily/rebalance delivery dừng; pending_unset
>     cho active bots.
> Downstream khi /ba-impact: FM-ADM-01 screen cần thêm "Members" tab + "Master Wallets" tab.
> wl-admin FRD §4.2 BR-WLA-022: wl_code trong WL-ADMIN tenant config phải match
> wl_members + wl_master_wallets trong BNZA-ADMIN D1.

> **[API SURFACE — WL_ADMIN_API_GUIDE_EN (2026-06-16)]** Auth plane: `/api/wl-admin/*` dùng `X-Wallet-Address` header (KHÔNG phải HMAC — khác hoàn toàn với `/api/wl/*` Helix-facing). Roles: `viewer` (read) / `admin|operator` (member writes) / `super_admin` (wl_code + master writes). Endpoints: `GET/POST /codes`, `PATCH /codes/:wl_code`, `POST /codes/:wl_code/rotate-key`, `GET/POST /members`, `PATCH /members/:id`, `GET/POST /masters`, `PATCH /masters/:id`.
>
> **wl_codes state machine**: `active ↔ suspended` (PATCH trigger; on-chain unset/hold async via suspend cron Layer B — not instantaneous).
> **wl_members state machine**: `(none) → active → leaving → left → active (rejoin, epoch++)`. One-wallet-one-WL constraint (★ E-5): wallet cannot be active/leaving in two WLs simultaneously. Optimistic locking on transitions (409 not_found_or_wrong_state on stale call).
> **wl_master_wallets**: bookkeeping-only endpoints; on-chain rotation (★ F-3) is Layer B cron, not these endpoints.
> **api_key vs secret**: `POST /codes` returns `api_key` (public identifier, `wlk_` prefix). HMAC secret is NEVER stored in D1 — BNZA places it in `WL_API_SECRETS` Workers Secret out of band. FE never handles the secret.

| FM-ADM-02: PF Distribution Config | Off-chain tracking và config UI cho PF recipients. **Scope giảm so với trước**: PF on-chain vẫn về `pfCollector` single EOA (0xa5B8...C969) — không có BnzaSplitter contract interaction. UI chỉ manage `fee_distributions` table (ai nhận bao nhiêu, off-chain config) và display PF collection history. | P0 | 0.5w |

> **[SCOPE REDUCTION — WL_SPEC_SOTATEK_EN_v1.0 §1.2 vs WL_SPEC.md cũ §5]**
> Client spec cũ định nghĩa BnzaSplitter contract — on-chain immediate distribution tới 10 recipients.
> Spec mới loại BnzaSplitter khỏi v1. BNZA tự handle PF distribution off-chain trong v1.
> FM-ADM-02 không cần: gọi BnzaSplitter setters, trigger on-chain distribution, manage groupId.
> FM-ADM-02 chỉ cần: manage fee_distributions rows (wallet + share + is_remainder) + display history.

| FM-ADM-10: WL Bot Lifecycle Monitor | Monitor screen cho `wl_activation_status` backlog: pending_set SLA, failed_set queue, needs_repair alerts, rotation in progress, wl_unattributed_events SLA breach. Admin actions: retry set, force-normalize (two-phase: unset confirmed + on-chain==0 read → NULL). Trigger setBotWlMaster/unsetBotWlMaster via OPERATOR API. | P1 | 0.5w |

> **[NEW FEATURE — WL_SPEC_SOTATEK_EN_v1.0 §5.1.1, §5.1.2, §6.3, §11]**
> Spec mới định nghĩa 6-state WL bot activation machine:
> NULL | pending_set | active | failed_set | pending_unset | needs_repair
> Khi bots stuck (failed_set > 48h → auto force-normalize; needs_repair → delivery bị dừng),
> zen cần monitor để thấy và trigger recovery. Không có trong bất kỳ client spec cũ nào.
> "Force-normalize" là two-phase: không thể chỉ set DB=NULL nếu on-chain wlMaster còn set —
> user stop sau đó sẽ vẫn gửi net đến master (sai intent).
> Downstream khi /ba-impact: bnza-admin FRD cần FM-ADM-10 section + SRS cần 1 screen mới.
| FM-ADM-03: IB Management | Replace mockIBs with real D1 data (ib_partners table). CRUD: name, wallet, commission_rate, status. | P1 | 0.5w |
| FM-ADM-04: Bot Type Config | Complete partial impl: deposit tiers, cooldown range (10–180 min), EXBOT strategy params (hedge_ratio/leverage/stop_safety_factor — zen provides values). | P1 | 0.5w |
| FM-ADM-05: Dashboard | Real metrics: active bot count, total AUM, daily revenue, total users, EXBOT count. From OPERATOR `/api/admin/stats` (KV-cached, 5 min TTL). | P2 | 0.5w |
| FM-ADM-06: Reports | Real-data reports: fee collection, bot performance, user activity, WL OpFee/PF Breakdown per-WL aggregated. Date-range queries. | P2 | 0.5w |
| FM-ADM-07: TOKEN Mgmt | Burn/supply/vesting/treasury/builder-fee (keep mock, BNZA Token contract NOT in SOTATEK scope). | P3 | — |
| FM-ADM-08: System Settings | Manage system_config key-value pairs (global_bot_enabled, access_mode, max_bots_per_user, safe_mode, exbot_enabled, etc.). Show current value + last modified. | P2 | 0.5w |
| FM-ADM-09: Relayer Monitor | Relayer status: wallet address, ETH balance, last tx hash + timestamp, health (balance > threshold). | P2 | 0.5w |
| FM-ADM-11: User Management | View and manage all registered users: wallet address, role (viewer/admin/super_admin), registration date, linked bots count. Read-only list with RBAC-based action controls (super_admin only for block/unblock). | P1 | — |
| FM-ADM-12: Audit Log Viewer | Paginated, filterable read-only viewer for all audit log entries (NFR-ADM-005). Filters: date range (max 90 days), module, action, actor. Detail drawer shows old/new values. Append-only — no edit/delete. | P0 | 0.5w |

### 5.3 BNZA-EX (Priority: P2 — Non-blocking)

| Sub-module | Description | Priority | Effort |
|------------|-------------|----------|--------|
| FM-EX-01: TradingView Integration | Implement `chartingLibraryAdapter.js` (Advanced Charts) | P2 | 1w |
| FM-EX-02: Chart Data Feed | Hyperliquid market data → TradingView format | P2 | 0.5w |
| FM-EX-03: Order Placement | Integrate order UI with chart | P2 | 0.5w |

### 5.4 BNZA-EXBOT Infrastructure (Priority: P0 — WL Launch Critical)

| Sub-module | Description | Priority | Effort |
|------------|-------------|----------|--------|
| FM-XB-01: D1 Schema | 5 primary tables (bots, bot_runtime_state, hedge_legs, hl_agent_keys, queue_idempotency); optimistic concurrency via state_version guard | P0 | 0.5w |
| FM-XB-02: Queue Topology | 10 queues: bot-scan, light-check, hedge-sync, reconcile, deep-audit, price-near-stop-audit, partial_repair, user_redeem (highest priority, SLA 5 min), notification, metrics-rollup | P0 | 1w |
| FM-XB-03: Durable Objects | HLRateLimitDO (sliding-window, 800 weight/min budget), UserLockDO (lease-based 90s TTL, 1-user mutex), MarketDataDO (sqrtPriceX96/tick cache) | P0 | 0.5w |
| FM-XB-04: Cron Jobs | `*/360 * * * *` deep-audit + hourly metrics-rollup + 6h stop-integrity scan | P1 | 0.5w |
| FM-XB-05: HL Adapter | Rate limit (1,200 wt/min, BNZA budget 800), cloid deterministic generation, nested error parser, delta-only adjustShortDelta, post-order reconcile, agent key decrypt | P1 | 1w |
| FM-XB-06: API Endpoints (Operator Facade) | `/api/exbot/*` proxy: start, status, close, agent-key, margin — OPERATOR forwards to ExBot Worker via service binding; ExBot NOT public | P1 | 1w |
| FM-XB-07: Lifecycle State Machine | 18 states: idle→preflight→lp_opening→lp_opened→hedge_pre_open→hedge_post_confirmed→stop_placing→stop_verified→active; runtime: hedge_stopped_cooldown, lp_rebalancing, lp_closing, closed, safe_mode, error; PAUSED=status-level only. Note: `cooldown` and `parked` lifecycle states removed (park/redeploy feature dropped per client HLD decision 2026-06-18) | P0 | 1w |
| FM-XB-08: Close/Redeem Operations | Two systems: (A) user_redeem = LP-first instant redemption (on-chain guarantee, hedge close SLA 5 min); (B) bot_safe_close = hedge-first, USDC returned to user via RedemptionQueue FIFO fulfill (park/redeploy loop dropped per HLD 2026-06-18); close_operations idempotency ledger prevents double settlement | P0 | 0.5w |

> **EXBOT Phase 0 Gate (blocks Phase A start)**: Prerequisites per SPEC v5.2.6 §0.3 — (1) zen approves SPEC v5.2.6; (2) BnzaExVault deployed, Base + OP addresses/operator finalized (2 sets) — multiSig no longer required for emergencyTransfer (Operator-only when paused, per HLD 2026-06-18); (3) HL agent key encryption method confirmed; (4) WL stability gate — 7 consecutive days post-launch with zero SAFE_MODE + no major incident. Before all 4 met: SOTATEK prepares D1 schema + Queue skeleton only — no HL integration.

> **D1 Architecture (2 DBs)**: `control_db` (users, bot_registry, shard_registry, hl_agent_keys) + `state_db_shard_xx` (bots, positions, hedge_legs, bot_runtime_state, circuit_breakers, rebalance_attempts, lp_operations, close_operations, queue_idempotency, funding_daily_metrics, hourly/daily_bot_metrics). Phase A: 1 shard; Phase B: 4; Phase C: 16 (deferred). R2 archive + Analytics Engine: Phase B+.

### 5.5 BNZA-POOL Steps 7-8 (Priority: P1 — Post-WL)

| Sub-module | Description | Priority | Effort |
|------------|-------------|----------|--------|
| FM-PL-01: Step 7 Multi-Bot | BotCard grid, Active Bots section, chain-switching, max 10/chain | P1 | 1.5w |
| FM-PL-02: Step 8 plan_specs | Version management across POOL + OPERATOR + OPS, immutability model | P1 | 4w |

---

## 6. Cross-Project Dependency Graph

```
                    ┌──────────────┐
                    │   OPERATOR   │ (api.bnza.io — shared backend)
                    │   (existing) │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────────┐
          │                │                    │
          ▼                ▼                    ▼
   ┌─────────────┐  ┌───────────┐      ┌─────────────┐
   │   MOBILE    │  │   ADMIN   │      │ POOL Steps  │
   │  (PTL-01)   │  │  (PTL-02) │      │   (PTL-05)  │
   └──────┬──────┘  └─────┬─────┘      └──────┬──────┘
          │                │                    │
          │                │                    │
          ▼                ▼                    │
   ┌─────────────┐  ┌───────────┐              │
   │ EXBOT Infra │  │ EXBOT Infra│              │
   │  (PTL-04)   │◄─┤  (PTL-04) │              │
   └─────────────┘  └───────────┘              │
                                                │
   ┌─────────────┐                              │
   │     EX      │ (independent — no OPERATOR)  │
   │  (PTL-03)   │                              │
   └─────────────┘                              │
                                                │
   ┌─────────────────────────────────────────────┘
   │  Step 8 requires simultaneous deploy:
   │  POOL + OPERATOR + OPS (ADMIN)
   └──────────────────────────────────────────────
```

### Dependency Table

| From (depends on) | To (provides) | Interface | Blocking? |
|---|---|---|---|
| WL Mobile → WL Admin Backend **[OOS — Helix interface]** | Reward summary, history, positions, community, airdrops, tenant config | REST API (`/api/mobile/*`, SIWE/JWT) | Yes |
| WL Mobile → WL Backend → BNZA OPERATOR **[OOS — Helix initiates; BNZA OPERATOR exposes endpoint]** | Bot start/stop (stream 3, §7C); wl_code propagation | SIWE/JWT (mobile→WL) + HMAC-SHA256 (WL→BNZA `/api/wl/*`); **WL post-record specifically: Helix server calls BNZA `/api/bot-configs/atomic-start` + `/api/bot-configs/:id/stop` via HMAC-SHA256 server-to-server (finalized v1.1 §4.4)** | Yes |
| WL Mobile → RewardDistributor (on-chain) **[OOS — user wallet interaction, Helix app]** | Claim USDC (user-borne gas, Base + OP) | Solidity `claim()` via user wallet | Yes |
| WL Admin Backend → BNZA OPERATOR **[OOS — Helix pulls; BNZA OPERATOR exposes Ledger API]** | Ledger API — net records (stream 1, §7) | HMAC-SHA256 + nonce, PULL | Yes |
| WL Admin Backend → BNZA OPERATOR **[OOS — Helix pulls; BNZA OPERATOR exposes Position API]** | Position API — AUM/status for rank/Cap (stream 2, §7B) | HMAC-SHA256 + nonce, PULL | Yes |
| WL Admin Backend → RewardDistributor **[OOS — Helix-owned payout]** | On-chain payout (Base + OP mainnet) | Solidity `addRewards` (clientNonce) | Yes |
| MOBILE → Router/LPBot | Bot start/stop (user wallet TX, zapMint/stop) | On-chain (user wallet signs) | No (existing) |
| ADMIN → OPERATOR | WL, PF, IB, Bot config, TOKEN endpoints | REST API (admin role) | Yes |
| ADMIN → OPERATOR | WL bot lifecycle: setBotWlMaster, unsetBotWlMaster, wl_activation_status transitions, wl_members CRUD, wl_master_wallets CRUD | REST API (admin role) + on-chain tx via OPERATOR Relayer | Yes |

> **[NEW DEPENDENCY — WL_SPEC_SOTATEK_EN_v1.0 §5.1, §6.3, §9.1–§9.3]**
> Trước: BNZA-ADMIN chỉ quản lý static WL partner config (wl_codes, wl_pool_wallets).
> Mới: BNZA-ADMIN là control plane cho WL bot net routing:
> - setBotWlMaster/unsetBotWlMaster: BNZA-ADMIN trigger → OPERATOR fires on-chain tx via Relayer.
> - wl_members CRUD: BNZA-ADMIN manages D1 table; OPERATOR reconciler reads để set bot state.
> - wl_activation_status transitions: OPERATOR cron đọc wl_members + wl_codes để quyết định
>   pending_set / active / failed_set / pending_unset / needs_repair.
| ADMIN → EXBOT Infra | EXBOT management endpoints | Via OPERATOR API | Partial |
| EXBOT Infra → OPERATOR | OPERATOR proxies `/api/exbot/*` into ExBot Worker via service binding + internal token | CF service binding (Worker-to-Worker) | Yes |
| EXBOT Infra → zen | Interface specs (D1 schema, Queue topology, API contracts) | Documentation | **Blocker** (OQ-2) |
| EXBOT Infra → Hyperliquid | Trading API (testnet first) | External API | Yes |
| **ExBot → WL (future)** | **ExBot replaces/extends LPBot as WL bot engine** | **TBD — integration point Line 1 × Line 2** | **Future milestone** |
| POOL Step 7 → OPERATOR | `bot-positions` API (multi-bot data) | REST API | Yes |
| POOL Step 8 → OPERATOR | plan_specs APIs (version, history, current) | REST API (new endpoints) | Yes |
| POOL Step 8 → ADMIN | Bot plan version management UI, force-stop | Simultaneous deploy | Yes |
| EX → TradingView | Charting library license | License procurement | **Blocker** (OQ-3 resolved: zen funds) |
| EX → Hyperliquid | Market data feed | External API (direct) | No |

---

## 7. Priority Ordering

> **Revised 2026-06-01:** Project restructured into 2 parallel lines. Line 1 focuses on WL+MLM system (new) + maintain Pool/EX. Line 2 focuses on ExBot+Backtest. Lines converge at ExBot-into-WL integration point.

### Line 1 — Tier 0 (WL+MLM Core)

1. **Smart Contracts** — FM-WLC-01 (BnzaRouterUpgradeable + BnzaLpBot WL changes A–K)
2. **BNZA-OPERATOR WL Backend** — FM-OPW-01/02/03/04/07 (DB migrations, Ledger API, Bot API, post-record webhook, fee_collections exclusion)
3. **BNZA-ADMIN** — FM-ADM-01 (WL Mgmt) + FM-ADM-02 (PF Distribution)
4. **OPERATOR** — Pre-launch hotfixes (P0-F.0: C1, C2, H1, H2, H3)

> **OOS (Helix scope — not Sotatek deliverables):** FM-WLA-01/02/03/04/05 (WL Admin System core), FM-MOB-01/02/03/04/05/08 (WL Mobile core)

### Line 1 — Tier 1 (Post-WL launch)

5. **BNZA-OPERATOR WL Backend** — FM-OPW-05/06 (WlNetSent scanner, reconcilers)
6. **BNZA-ADMIN** — FM-ADM-03/04 (IB Mgmt, Bot Type Config)
7. **POOL Step 7** — FM-PL-01 (Multi-Bot)

> **OOS (Helix scope):** FM-WLA-06/07 (WL Admin multi-tenant + reconciliation), FM-MOB-06/07/09/10 (WL Mobile community + branding + settings + PWA)

### Line 1 — Tier 2 (Enhancement)

8. **POOL Step 8** — FM-PL-02 (plan_specs Version)
9. **BNZA-ADMIN** — FM-ADM-05/06/08/09 (Dashboard, Reports, Settings, Relayer)
10. **EX** — FM-EX-01/02/03 (TradingView)

> **OOS (Helix scope):** FM-MOB-11 (WL Mobile i18n)

### Line 2 — Tier 0 (ExBot Core)

1. **EXBOT Infra** — FM-XB-01/02/03 (D1 Schema, Queue, DO) — Phase A1 readiness
2. **EXBOT Infra** — FM-XB-04/05/06 (Cron, HL Adapter, API) — Phase A full

> EXBOT Phase A cannot begin until Phase 0 gate conditions are met AND WL stability gate passes (7 days post-launch, no SAFE_MODE). See intake.md LD-8.

### Integration Point (future)

- **ExBot → WL**: ExBot integrated as bot engine for WL users. Replaces/extends LPBot. Timing: post-ExBot Phase A completion + WL stability gate.

---

## 8. System-Level Constraints

### 8.1 Authentication Model

| Layer | Mechanism | Applies to |
|---|---|---|
| Primary | `X-Wallet-Address` header (no signature) | POOL, BNZA-ADMIN → OPERATOR |
| BNZA-ADMIN | Cloudflare Access (zen@bnza.io) second layer + wallet connect | PTL-02 only |
| BNZA-ADMIN RBAC | `admin_wallets` table + `/api/me` role check (super_admin / admin / viewer) | PTL-02 endpoints |
| WL-ADMIN | SSO (Cloudflare Access) + 2FA (TOTP mandatory); roles: Super / Operator / Read-only | PTL-06 only |
| WL Mobile | SIWE (Sign-In with Ethereum) → 24h JWT; tenant resolved by subdomain + signature domain | PTL-01 → PTL-06 Backend |
| WL post-record (bot start/stop) | HMAC-SHA256 (§7.2 scheme); Helix server → BNZA OPERATOR; server-to-server (CORS N/A); starter wallet passed explicitly by Helix server; anti-spoofing: tx_hash + NPM ownerOf + BotStarted/ZapMintFor event decode (§4.4 finalized v1.1) | `/api/bot-configs/atomic-start`, `/api/bot-configs/:id/stop` (WL path only) |
| Direct | Wallet connect → Hyperliquid API | PTL-03 only (no OPERATOR) |

### 8.2 Fee Model (Router v2.2.2)

| Fee Type | Rate | Recipient | Relevant Projects |
|---|---|---|---|
| Swap fee | 0.5% | Protocol | MOBILE (display), ADMIN (reports) |
| opFee | 0.5% | Treasury (0x2455...3A0a) | ADMIN (reports) |
| Performance Fee (PF) | 30% of earnings | pfCollector EOA (0xa5B8...C969) — single account, no on-chain Splitter in v1 | ADMIN (PF Distribution off-chain config) |

> **[SCOPE CHANGE — WL_SPEC_SOTATEK_EN_v1.0 §1.2]**
> BnzaSplitter removed từ v1. PF distribution off-chain là concern của BNZA (FM-ADM-02).
> Tất cả module-level artifacts derive từ backbone này — /ba-impact sẽ sync FM-ADM-02 từ note này.
| PF Ratio — convert_to_usdc=1 | 0.2970075 of earnings | User receives USDC | POOL (stop flow), MOBILE (earnings display) |
| PF Ratio — convert_to_usdc=0 | 0.2985 of earnings | User receives native tokens | POOL (stop flow), MOBILE (earnings display) |
| WL Split | 70% partner / 30% BNZA | WL partner wallets | ADMIN (WL Mgmt), MOBILE (earnings display) |

> **Note — Router v2.2.2-fix-2 breaking changes (Step 6, zen's work, NOT SOTATEK scope):**
> - `closeForUser`: 8 → 7 args (removed `convertPrincipalToUsdc` — now always converts to USDC)
> - `collectForUser`: unified signature (was split into two variants)
> - `rebalanceForBot`: new function added (Operator-only)
> - New deployed addresses: OP `0xe4E873DCef553dAb821B03a3caC36B84C5f16B8D`, Base `0xc70cDE10aE7b7630FBF0778D23A04a84B8f82130`
> - LPBot v1.2: `collectForSelf` now takes 2 args (added `convertToUsdc bool`); `startBot` struct has 11 fields (added `convertToUsdc`, `autoCompound`)
> - SOTATEK must use these new addresses and ABIs in all integrations.

### 8.3 Scale Requirements

| Metric | Target | Source | Relevant Projects |
|---|---|---|---|
| Bot count | 10,000 from day one | Queue v2 SPEC | EXBOT Infra, POOL Step 7 — **feasibility under review** (CF concurrent worker limit; Daniel report pending) |
| Max Bots per chain | 10 (20 total) | POOL Step 7 SPEC | POOL, MOBILE |
| Bot-check latency | <100ms | Roadmap M3 | EXBOT Infra |
| API latency | <100ms p95 | Roadmap M3 | All (via OPERATOR) |
| Uptime | 99.9% | Roadmap M3 | All |
| MOBILE FPS | 60fps | Mobile SPEC | MOBILE |

### 8.4 Deployment Topology

| Project | Platform | Deploy Method | Branch Strategy |
|---|---|---|---|
| MOBILE | CF Pages | `wrangler pages deploy dist/` | Monorepo (packages/mobile) |
| ADMIN | CF Pages | `wrangler pages deploy dist/` | Monorepo (packages/admin) |
| EX | CF Pages | `wrangler pages deploy dist/` | Monorepo (packages/ex) |
| EXBOT Infra | CF Workers | `wrangler deploy` (`apps/bnza-exbot/` — standalone Worker) | Monorepo (apps/bnza-exbot) |
| POOL Steps 7-8 | Vercel | Push to `main` (auto-deploy) | Existing repo (separate — not in SOTATEK monorepo) |

### 8.5 Shared Design Language

| Aspect | Standard | Applies to |
|---|---|---|
| UI Framework | shadcn/ui + Tailwind | MOBILE, ADMIN, POOL |
| Theme | Dark UI | MOBILE, EX |
| Responsive | PWA (MOBILE), Desktop-first (ADMIN, POOL, EX) | All frontends |
| i18n | 5 languages (en/ja/zh/ko/vi) | MOBILE, POOL |
| Wallet | Reown AppKit | MOBILE, ADMIN, POOL |

### 8.6 Testing Standards (per LD — resolved OQ-7)

| Project | Unit Tests | E2E Tests | Integration Tests |
|---|---|---|---|
| MOBILE | ✅ (80%+) | ✅ (critical flows: WL gate, deposit, bot lifecycle) | — |
| ADMIN | ✅ (80%+) | ✅ (critical flows: WL mgmt, PF distribution) | — |
| EX | ✅ (80%+) | — | — |
| EXBOT Infra | — | — | ✅ (queue processing, HL API calls) |
| POOL Steps 7-8 | ✅ (80%+) | ✅ (Step 8 E2E per spec) | — |

---

### 8.7 EXBOT Contract Architecture (updated 2026-06-18 per HLD decisions)

EXBOT uses a **strategy dispatch** pattern (DELEGATECALL) — vault holds USDC only; LP NFT custody is separated into `BnzaExPositionManager`. Not an extension of BnzaRouter.

| Contract | Module | Status | Responsibility |
|---|---|---|---|
| BnzaRouter v2.2.2-fix-2 | BNZA-POOL (existing) | Deployed OP + Base | LP Bot (user self-custody) |
| BnzaExVault | BNZA-EXBOT only | Not deployed (zen scope) | USDC custody + `executeStrategy` dispatch |
| BnzaExPositionManager | BNZA-EXBOT only | Not deployed (zen scope) | LP NFT custody (not vault) |
| OpenPositionStrategyV1 | BNZA-EXBOT only | Not deployed (zen scope) | Open LP position (stateless) |
| RedeemStrategyV1 | BNZA-EXBOT only | Not deployed (zen scope) | Close/redeem (stateless) |
| RebalanceStrategyV1 | BNZA-EXBOT only | Not deployed (zen scope) | Range rebalance (stateless) |
| CollectFeeStrategyV1 | BNZA-EXBOT only | Not deployed (zen scope) | Fee collection (stateless) |
| TokenRouter | BNZA-EXBOT only | Not deployed (zen scope) | Fee/payout routing |
| RedemptionQueue | BNZA-EXBOT only | Not deployed (zen scope) | Async HL redemption FIFO queue |

**Architecture decisions (HLD 2026-06-18, client approved):**
- Vault API: `executeStrategy(strategy, user, botId, params)` — not `vaultMint/vaultClose/vaultRebalance` (dropped)
- NFT custody: `BnzaExPositionManager` holds LP NFTs; vault holds USDC only (INV-1 §15.5.1 superseded)
- Park/redeploy: dropped — no `CloseDestination` enum, no `uninvested_balances`, no `FundsParked/Redeployed/Withdrawn` events
- Emergency: `emergencyTransfer(user, botId)` — Operator role, paused-only, no recipient param (funds return to user only), emits `EmergencyRecovery` event. Multi-sig not required.
- RedemptionQueue: FIFO `fulfillRequest(tokens, amounts)` — on-chain operator→user payout

**Constraints for SOTATEK:**
- BnzaRouter unchanged — integrate as-is
- All ExBot contracts: zen designs + deploys; SOTATEK integrates against zen-provided ABI
- Phase A cannot begin until BnzaExVault is deployed (see Phase 0 gate §5.4)
- Terminology: "BnzaExVault/Vault" (Solidity contract) ≠ "vaultAddress" (HL subaccount ID)

---

### 8.8 WL+MLM System Architecture

> **Context note:** This section documents all 3 layers (A/B/C) of the WL+MLM architecture as reference. Layer A (BNZA contracts + BNZA-OPERATOR backend) is Sotatek scope. Layer B (WL Admin System — PTL-06) and Layer C (WL Mobile App — PTL-01) are Helix-owned OOS. Kept here as architectural context only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B.

This section is the canonical inline reference for the WL+MLM system. All module-level artifacts (mobile, wl-admin) derive from this section. No need to read external client specs.

#### 8.8.1 3-Layer Responsibility Boundary

```
┌──────────────────────────────────────────────────────────────┐
│ [Layer A] BNZA core                                          │
│   Each user's LP earned → deduct opFee/PF → net sent to WL  │
│   pool. Ledger API provides "whose / how much net".          │
│   Principal returned DIRECTLY to user (never through WL).   │
└───────────────┬──────────────────────────────────────────────┘
                │ ① net remittance (USDC, per chain)
                │ ② Ledger PULL (HMAC-SHA256)
                ▼
┌──────────────────────────────────────────────────────────────┐
│ [Layer B] WL Admin System  (PTL-06)                          │
│   Fetch ledger → compute rank reward + MLM bonuses (off-chain│
│   → instruct RewardDistributor to pay out (on-chain)         │
│   + Admin console: monitoring, tenant config, incidents      │
└───────────────┬──────────────────────────────────────────────┘
                │ ③ RewardDistributor pays finalized amount to each user
                ▼
┌──────────────────────────────────────────────────────────────┐
│ [Layer C] WL Mobile  (PTL-01)                                │
│   Displays only finalized post-allocation amounts            │
│   ★ Raw Uniswap uncollected fees are NEVER shown             │
└──────────────────────────────────────────────────────────────┘
```

| Layer | Party | Responsibility | Execution |
|---|---|---|---|
| A | BNZA | Deduct opFee/PF; send net to `wlMaster[tokenId]`; provide ledger. Principal returned directly to user. | On-chain (Router) + API |
| B | WL Admin System | Compute MLM allocation from net; pay out via RewardDistributor. | Compute = off-chain / Payout = on-chain |
| C | WL Mobile | Display only. No computation, no remittance. | Frontend |

**Regulatory key point**: Principal is returned directly to the user by BNZA — it never enters the WL master account. The admin system handles only net (fee revenue share) and never touches the principal.

---

#### 8.8.2 Terminology

| Term | Definition |
|---|---|
| **WL** | White-label MLM operator. BNZA's customer. |
| **Tenant** | One WL operator = one tenant. Admin system and mobile are multi-tenant. |
| **earned** | Raw uncollected fees generated by a user's Uniswap V3 LP position. |
| **net** | Amount sent to `wlMaster[tokenId]` = earned − opFee (0.5%) − PF (30% of afterOp). Allocation source. |
| **WL bot** | A bot instance where `wlMaster[tokenId] != 0`; i.e., a bot associated with a whitelabel partner's master wallet on-chain. |
| **WL master account** | Per-bot, per-chain address stored in Router on-chain storage (`wlMaster[tokenId]`). Set by BNZA via `setBotWlMaster` after bot start. Net from WL bot fees is sent here; principal never enters here. |
| **Fee reward** | User's own share = net × rank reward rate (30–62%). |
| **MLM pool** | Remainder = net × (1 − rank reward rate). Source for all MLM bonuses. |
| **Referral reward** | Allocated from MLM pool: per-tier referral + title differential + same-rank bonus. |
| **Rank** | Investment tier based on user's AUM. Determines fee reward rate. |
| **Title** | MLM tier (V1–V7) based on team TVL. Basis for title differential bonus. |
| **RewardDistributor** | On-chain payout contract (Base/OP) deployed by WL. Distributes finalized USDC. |
| **Claimable** | Amount unclaimed on RewardDistributor (accrued below minPayout threshold). |
| **Push** | Auto-send by admin system when reward ≥ minPayout. WL bears gas. |
| **Claim** | Manual pull by user via RewardDistributor.claim(). User bears gas. |
| **Cap** | Optional reward ceiling = AUM × cap_multiplier. Per-tenant config. |
| **Leader perk** | Non-USDC token/airdrop for V4+ title holders. Separate track (bonus_airdrops). |

---

#### 8.8.3 Money Flow — End-to-End

```
[Layer A: BNZA core]
earned (user's raw LP uncollected fees)
  − opFee 0.5%                → BNZA treasury (Buyback & Burn)
  = afterOp
  − PF (afterOp × PF rate)    → pfCollector EOA (BNZA's share, single account, no on-chain Splitter in v1)
  = net                       ★ WL bot: sent to wlMaster[tokenId] (master account per WL, USDC)
                                Regular bot: sent to user (pair or USDC per preference)
```

> **[SYNC WITH WL_SPEC_SOTATEK_EN_v1.0 §1.2, §2, §5.1]**
> Hai thay đổi so với client spec cũ:
> (1) PF → `pfCollector` single EOA, không phải BnzaSplitter contract.
> (2) WL bot net → `wlMaster[tokenId]` (1 master account per WL), không phải "WL pool".
> Tất cả module-level artifacts derive từ §8.8 — khi /ba-impact chạy cho admin/mobile,
> chúng sẽ kế thừa money flow corrected này.

[Layer B: Admin System — allocation from net]
net
  ├─ Fee reward = net × rank reward rate (30–62%)
  │     → User's own share. Displayed on mobile as "Fee reward".
  │
  └─ MLM pool = net × (1 − rank reward rate)   [38–70% of net]
        ★ ALL MLM bonuses come from this pool. Never added directly to net.
        ├─ Referral reward  = MLM pool × tier rate (e.g. 10% L1 / 5% L2 / 2% L3)
        ├─ Title bonus      = differential method (see §8.8.5)
        ├─ Same-rank bonus  = MLM pool × 5% total envelope, split equally
        ├─ Leader bonus     = token/airdrop (NOT USDC), V4+ only → bonus_airdrops
        └─ Remainder        = WL treasury share

[Layer B → User]
RewardDistributor (Base/OP) pays finalized USDC:
  fee reward + referral + title diff + same-rank
  Leader bonus paid separately (token/airdrop track)
```

**Structural guarantee**: All MLM bonuses are paid from the MLM pool. Title uses differential method → lineage total is capped at the highest title rate. Structurally impossible to exceed the pool.

---

#### 8.8.4 Rank Table (default — per tenant config)

| Rank | Min AUM (USD) | Fee Reward Rate |
|---|---|---|
| starter | $1,000 | 30% |
| basic | $5,000 | 40% |
| advanced | $10,000 | 48% |
| professional | $50,000 | 55% |
| elite | $100,000 | 62% |

Rank is determined by user's current AUM. Rank table is per-tenant and fully configurable.

---

#### 8.8.5 Title Table & Differential Method (default — per tenant config)

| Title | Min Team TVL | Diff Bonus Rate | Conditions |
|---|---|---|---|
| V1 | $0 | 5% | — |
| V2 | $50,000 | 8% | 5 direct active referrals + V1 on 2 lines / starter+ |
| V3 | $150,000 | 12% | 6 direct active referrals + V2 on 2 lines / basic+ |
| V4 | $500,000 | 16% | 7 direct active referrals + V3 on 2 lines / advanced+ |
| V5 | $2,000,000 | 20% | 8 direct active referrals + V4 on 3 lines / professional+ |
| V6 | $6,000,000 | 25% | 9 direct active referrals + V5 on 3 lines / professional+ |
| V7 | $18,000,000 | 30% | 10 direct active referrals + V6 on 3 lines / professional+ |

**Differential method**: Each upline receives only the diff% over the immediate downstream title holder's rate.

Example — User A (V1, 5%) → B (V3, 12%) → C (V5, 20%):
- C receives: 20% of MLM pool from A's net
- B receives: (12% − 5%) = 7% of MLM pool from A's net
- Next upline above C: (their title rate − 20%) of MLM pool

Lineage total never exceeds the highest title rate in the chain.

---

#### 8.8.6 Tenant Config Schema

Each WL operator has an isolated tenant config. Items that vary per WL:

```jsonc
{
  "tenant_id": "wl_xxx",
  "wl_code": "XXX",                    // BNZA-side ledger key
  "branding": {
    "name": "Helix",
    "logo_url": "...",
    "theme_color": "#..."              // Mobile is fixed dark; theme applies to accent colors
  },
  "chains": [8453, 10],               // Base + OP only. Arbitrum excluded.
  "wallets": {
    "wl_master_wallets":  { "8453": "0x...", "10": "0x..." },
    "reward_distributor": { "8453": "0x...", "10": "0x..." },
    "treasury":           { "8453": "0x...", "10": "0x..." }
  },
  "rank_table": [                     // AUM thresholds → fee reward rate
    { "rank": "starter",      "min_usd": 1000,   "fee_rate_pct": 30 },
    { "rank": "basic",        "min_usd": 5000,   "fee_rate_pct": 40 },
    { "rank": "advanced",     "min_usd": 10000,  "fee_rate_pct": 48 },
    { "rank": "professional", "min_usd": 50000,  "fee_rate_pct": 55 },
    { "rank": "elite",        "min_usd": 100000, "fee_rate_pct": 62 }
  ],
  "title_table": [                    // Team TVL thresholds → title + diff bonus rate
    { "title": "V1", "team_tvl_usd": 0,         "diff_bonus_pct": 5.0  },
    { "title": "V2", "team_tvl_usd": 50000,     "diff_bonus_pct": 8.0  },
    { "title": "V3", "team_tvl_usd": 150000,    "diff_bonus_pct": 12.0 },
    { "title": "V4", "team_tvl_usd": 500000,    "diff_bonus_pct": 16.0 },
    { "title": "V5", "team_tvl_usd": 2000000,   "diff_bonus_pct": 20.0 },
    { "title": "V6", "team_tvl_usd": 6000000,   "diff_bonus_pct": 25.0 },
    { "title": "V7", "team_tvl_usd": 18000000,  "diff_bonus_pct": 30.0 }
  ],
  "referral_levels": [                // Per-tier referral rates (MLM-pool basis)
    { "level": 1, "rate_pct": 10 },
    { "level": 2, "rate_pct": 5  },
    { "level": 3, "rate_pct": 2  }
  ],
  "reward_settings": {
    "cap_enabled": false,
    "cap_multiplier": 3.0,            // Reward cap = AUM × multiplier
    "cap_overflow": "forfeit",        // forfeit | carry
    "min_payout_usd": 10.0,           // Below this → accrues as claimable
    "same_rank_bonus_pct": 5.0,       // Total envelope, split equally among same-rank
    "leader_bonus": {
      "min_title": "V4",
      "asset": "BONANZA"              // Non-USDC token/airdrop
    }
  },
  "reown_project_id": "...",          // Per-tenant Reown AppKit project ID
  "status": "active"                  // active | suspended
}
```

---

#### 8.8.7 Distribution Pipeline (Layer B — Admin System)

The admin system runs a daily distribution job through this state machine:

```
PENDING → BOT_SYNC → LEDGER_FETCH → PENDING_SNAPSHOT → SNAPSHOT
       → UPLINE → COMPUTED → ENQUEUED → ONCHAIN → VALIDATED → COMPLETED
                                                ↘ BLOCKED / ABANDONED
```

| Phase | What happens |
|---|---|
| BOT_SYNC | Sync AUM from BNZA Bot API; freeze for today's computation |
| LEDGER_FETCH | PULL BNZA Ledger API (HMAC-SHA256); get net per user per chain |
| PENDING_SNAPSHOT | Operational gate — resolve registration omissions; manual GO or timeout |
| SNAPSHOT | Freeze today's referral tree |
| UPLINE | Resolve each user's upline lineage |
| COMPUTED | Compute fee reward + MLM bonuses (MLM-pool basis) + Cap |
| ENQUEUED | Batch distribution queue entries |
| ONCHAIN | Send to RewardDistributor (payout tx) |
| VALIDATED | Verify on-chain arrival; update cumulative totals |
| COMPLETED | All batches finalized |

Mobile only sees the output of VALIDATED — finalized amounts via `/api/mobile/summary`.

---

#### 8.8.8 Mobile Display Rules

| Show | Never show |
|---|---|
| Fee reward (net × rank rate) | Raw Uniswap LP uncollected fees |
| Referral reward (from MLM pool) | Others' detailed amounts |
| Claimable balance | Raw allocations before deduction |
| Own rank / title / team TVL | — |

All displayed amounts come from Admin System API — already finalized post-deduction. Mobile must not read LP NFTs directly.

---

#### 8.8.9 Admin Module Boundary — BNZA-ADMIN vs WL-ADMIN

The "admin" module previously in `03_modules/admin/` has been split into **two dedicated folders**, one per sub-system.

```
zen creates WL partner account "Helix" on BNZA-ADMIN (PTL-02)
                    ↓
WL ops team "Helix" logs into WL-ADMIN (PTL-06) to run daily MLM operations
```

| Dimension | BNZA-ADMIN (Sub-system A) | WL-ADMIN (Sub-system B) |
|---|---|---|
| **Portal** | PTL-02 — ops.bnza.io | PTL-06 — wl-admin.bnza.io |
| **Actor** | ACT-04 (zen) | ACT-07 (WL Operator Admin) |
| **Auth** | Wallet + CF Access + RBAC | SSO (CF Access) + 2FA TOTP |
| **Manages** | BNZA product infra (bots, plans, users, access, relayer, PF config) + WL partner account onboarding | Daily MLM distribution ops (jobs, tree, distributor, reward settings) |
| **Does NOT manage** | Daily MLM distribution pipeline, referral tree, distributor contract | Bot configs, plan specs, access control, PF split config |
| **Screens prefix** | (no prefix) — dashboard, bots, users, plans, logs, ib, whitelabel, fee-distribution, system-settings, relayer, reports, wl-monitor | `wl-` — wl-dashboard, wl-distribution-jobs, wl-users, wl-referral-tree, wl-distributor-contract, wl-reward-settings, wl-admins-auth |
| **Backend** | Calls OPERATOR API (api.bnza.io) | Own CF Workers + D1 + Queues; also calls BNZA Ledger/Position/Bot APIs |
| **Data source** | OPERATOR D1 (shared with other modules) | Own D1 (25 tables, separate from BNZA OPERATOR) |

**Key interaction point**: BNZA-ADMIN creates `wl_partners` records (FM-ADM-01). These records define the `wl_code` that WL-ADMIN uses as tenant identifier for the Ledger API (FM-WLA-04). BNZA-ADMIN does not write to WL-ADMIN's D1 tables.

---

| OQ | Status | Impact on Backbone | Action |
|---|---|---|---|
| OQ-1: Monorepo strategy | **Resolved: Monorepo** | Deployment topology updated (§8.4 — monorepo branch strategy) | Done |
| OQ-2: EXBOT interface specs | Hold (escalate zen) | **Blocker** for FM-XB-01→06 detailed requirements | Escalate immediately; start with known patterns from Queue v2 |
| OQ-6: PF WL remittance flow | **Resolved** | FM-ADM-02 is off-chain config only. fee_distributions records BNZA's internal PF allocation. WL 70/30 split is Helix's concern — not SOTATEK/BNZA-ADMIN scope (BR-ADM-020). Real API live as of 2026-06-12. | Resolved via uc-pf-distribution.md 2026-06-04; confirmed real API 2026-06-12 |
| OQ-8: Staging environment | Hold | Affects deployment guide; non-blocking for development | Staging domains defined in deployment guide but not confirmed |

---

### 8.9 EXBOT Strategy Spec — v5.2.6 Key Content

> **Source:** SPEC_v5.2.6_EN.md — client-provided, NOT in repo. File path at time of writing: `/Users/hienduong/Downloads/SPEC_v5.2.6_EN.md`.
> v5.2.6 is the **Final Approved** version (3-AI QA: Claude Code + Codex + GPT, Theme A–F). Unlike v5.2.3–v5.2.5 (doc-sync only), **v5.2.6 contains behavioral changes**. Where any module artifact (SRS/FRD/UC) conflicts with v5.2.6, v5.2.6 prevails.

#### 8.9.1 What changed in v5.2.6 vs v5.2.5

| Theme | Changes |
|---|---|
| A | Stop subsystem fully BigDecimal; protected stop replacement invariant (INV-STOP §19.5); automatic cooldown ladder after stop fires; circuit breaker stored-column canonical |
| B | `lp_operations` ledger (on-chain success + D1 failure recovery); close/redeem state machine ledger (`close_operations`); dust close bypass; `partial_repair` promoted to first-class queue; lifecycle enum canonicalized (B-5); queue idempotency ledger (B-6); one-bot preflight gap fix |
| C | Margin warning guard; margin definition fixed + preflight 2.0× buffer; price 3-way split (uniPoolPrice / hlMarkPrice / hlOraclePrice); budget overflow = proportional scale-down ladder (not hedge ratio change); **light-check HL-inviolability restored** (no HL fetch in light-check, ever) |
| D | D1 write budget gate; D1 Free tier corrected to 500 MB; max 6 simultaneous outbound connections per CF Worker |
| E | **Dual-chain from Phase 1 = Base + Optimism both from day 1** (not Base-only then add OP) |
| F | §0.5 NV table added (NV-1 to NV-14); version bump |

#### 8.9.2 Phase 0 Start Conditions (§0.3 / §30)

All 4 must be met before Phase A implementation begins:
1. zen approves SPEC v5.2.6 (document finalized) ✅ done
2. BnzaExVault + BnzaExPositionManager deployed on Base + Optimism — addresses, `authorizedOperator` confirmed by zen (multiSig no longer required for emergencyTransfer per HLD 2026-06-18)
3. HL agent key encryption method confirmed (NV-3 result finalizes §19.5 path a vs b)
4. WL stability gate: 7 consecutive days post-launch with zero SAFE_MODE + no major incident

#### 8.9.3 NV Items — External Assumptions to Verify in Phase 0

Owner: NV-1–11 = SOTATEK | NV-12 = BNZA (zen)

| NV | Category | What to verify | Blocks |
|---|---|---|---|
| NV-1 | HL | Exact API fields of isolated margin (`marginBalanceUsd`, `marginRequiredUsd`) + acceptance spec of reduce-only stop | §18.4 margin formula; §19.5 branch |
| NV-2 | HL | Whether `clearinghouseState` returns `entryPx` / `liquidationPx` / `effectiveLeverage` / `isolatedMargin` | §17.3 / §19.1 |
| NV-3 | HL | **Whether duplicate reduce-only stops are accepted on the same leg** → determines §19.5 path (a) or (b). Also: reduce-only stop size > position; `cancelByCloid` after trigger fire | §19.5 INV-STOP implementation |
| NV-4 | HL | Native trigger stop: mark-price vs oracle-price firing; immediate-trigger rejection; partial fill behavior | §8.4 / §19.2 |
| NV-5 | HL | Cloid duplication behavior (idempotency — prevents double submission) | §8.5 / §13.8 |
| NV-6 | HL | Order/info behavior when `subaccount + vaultAddress` specified; behavior on agent key expiry/revocation | §8.3 / §16.5 / §21.5 |
| NV-7 | HL | Measured rate-limit weight per endpoint (`clearinghouseState`=2 confirmed; others TBD) + `userRateLimit` endpoint | §9 HLRateLimitDO |
| NV-8 | CF | Workers subrequest limit (Paid=10,000); simultaneous open connections=6 | §5.2 |
| NV-9 | CF | D1 queries Paid=1,000; single-thread write; write QPS under 10k load | §5.2 D1 budget |
| NV-10 | CF | Queue throughput 5,000/s; batch 100; concurrency 250; wall time 15 min | §10 queue arch |
| NV-11 | CF | DO single-thread; lease behavior; Secrets Store binding decrypt round-trip | §11 / §21.5 |
| NV-12 | Chain | **Base + Optimism pool address; token0/token1 order (`wethIndex`); BnzaExVault deploy address** | §6.4 LP calc; §15.5.6 |
| NV-13 | HL | ETH perp min order / min notional / dust handling (write-off for size below minimum close) | §17.2 dust close |
| NV-14 | HL | Builder fee 5bps approval flow (on-chain or API?); billing timing; interaction with agent key/subaccount | §2 / §8 preflight |

> NV-3 and NV-12 are the most critical — do not implement §19.5 (stop replacement) or §6.4 (dual-chain LP) until these are confirmed.

#### 8.9.4 Key Formulas

**LP Position Amount (Uniswap V3 — §6.2)**

```
S = sqrt(currentPrice),  A = sqrt(P_lower),  B = sqrt(P_upper),  L = liquidity

current_tick < tick_lower  →  amount0 = L×(1/A − 1/B),  amount1 = 0
tick_lower ≤ current_tick < tick_upper  →  amount0 = L×(B−S)/(S×B),  amount1 = L×(S−A)
current_tick ≥ tick_upper  →  amount0 = 0,  amount1 = L×(B−A)

lpEthAmount = (wethIndex === 0) ? amount0Human : amount1Human
```

Implementation: `LiquidityAmounts.getAmountsForLiquidity(sqrtPriceX96, sqrtA, sqrtB, liquidity)` — never use `depositedToken − withdrawnToken + collectedFees` (carter2099 bug).

**Hedge Target (§7.1)**
```
targetShortEth = lpEthAmount × hedgeRatio  (Phase A: hedgeRatio = 0.70 fixed)
```
Always use BigDecimal. Normalize via `normalizeTargetRatioBps("0.70") → 7000n`. Never `Number("0.70") × 10000`.

**Rebalance Triggers (§7.3) — all BigDecimal**
```
deltaErrorUsd = |targetShortEth − actualShortEth| × uniPoolPrice
lpValueUsd    = from bot_runtime_state.lp_value_usd
drift_threshold   : deltaErrorUsd > max($25, lpValueUsd × 3%)
drift_relative    : |target − actual| / target > 0.15
range_boundary_near: price 90% to upper/lower tick
funding_alert      : 7d funding APR < −15%  (Phase A: sum of latest 7 rows in funding_daily_metrics)
time_fallback      : 4h since last adjustment
```

> ⚠️ `deltaErrorUsd` uses `uniPoolPrice` (LP valuation price), NOT `hlMarkPrice` or `hlOraclePrice` — v5.2.6 X-5 3-way price split.

**Stop Trigger Price (§19.1)**
```
effective_leverage  = notional_usd / isolated_margin_usd   (NOT the inverse)
notional_usd        = abs(sizeEth) × entryPrice

if liquidationPrice available:
  liq_distance_pct = (liquidationPrice − entryPrice) / entryPrice
else (fallback):
  liq_distance_pct ≒ 1 / effective_leverage

stop_trigger_px = entryPrice × (1 + liq_distance_pct × stopSafetyFactor)
stopSafetyFactor: Phase A = 0.70  |  Phase B+ = TBD via backtest (OQ)
```
All BigDecimal — no intermediate `Number()` conversion.

**Margin Status (§18.4)**
```
marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage
marginUsage       = marginRequiredUsd / marginBalanceUsd

ok:       marginUsage < 0.55
warning:  0.55 ≤ marginUsage < 0.75
critical: marginUsage ≥ 0.75
```
Updated only at: (1) just before hedge-sync; (2) deep-audit. Light-check reads D1 only — **never fetches HL marginSummary**.

**Preflight Margin Check (§18.4 / C-2)**
```
required = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage
pass condition: isolatedMarginBalance ≥ required × 2.0
```

#### 8.9.5 Price 3-Way Split (v5.2.6 X-5)

| Price | Source | Used for |
|---|---|---|
| `uniPoolPrice` | Uniswap V3 pool slot0 (via MarketDataDO) | LP drift valuation (`deltaErrorUsd`); LP amount calc |
| `hlMarkPrice` | HL mark price | Stop trigger detection in light-check (`price >= stop_price`) |
| `hlOraclePrice` | HL oracle price | Margin calculation; preflight |

Never mix these three.

#### 8.9.6 Key Behavioral Rules (v5.2.6 non-negotiable)

| Rule | Detail |
|---|---|
| INV-STOP | While HL short is non-zero, a verified reduce-only stop must always exist. The only exception is inside the `replaceStopProtected` critical section (max 60s). §17.2 never calls `cancelByCloid`/`placeReduceOnlyStopMarket` directly — only via `replaceStopProtected`. |
| Light-check HL weight = 0 | Absolute. No HL fetch of any kind in light-check, including margin. Margin status = read from D1 `hedge_legs.margin_status` only. v5.2.6 C-5 explicitly removes the old "fetch margin every 30 min" rule. |
| Delta-only hedge | `adjustShortDelta(target − actual)` is the default. Full close→open is only for: target=0 (bot close), emergency reset, or manual reset (Phase B+). |
| Budget overflow = scale-down ladder | Do NOT change `hedgeRatio`. Scale LP + hedge proportionally together: 100% → 50% → 25%. Idempotent via `scale_step_pct` absolute value in D1. |
| After stop fires | Transition `lifecycle_state = 'hedge_stopped_cooldown'`, keep LP, suppress hedge-sync. After 4h: auto re-hedge. After 3 stops in 7 days: `bot_safe_close` → §16.7 closed loop. |
| user_redeem = LP-first | On-chain `BnzaExVault.redeem()` returns LP USDC to user **unconditionally in the same tx**. HL hedge close is best-effort (SLA 5 min). Hedge failure → `residual_hl_liability`, never blocks LP repayment. |
| bot_safe_close = hedge-first | Order: close HL → call `executeStrategy(RedeemStrategyV1)` → enqueue `RedemptionQueue.createRequest` → Operator `fulfillRequest` pays user FIFO. No park/redeploy loop (dropped HLD 2026-06-18). After hedge+LP close: `lifecycle_state = 'closed'`. |
| Dual-chain from Phase 1 | Base + Optimism both from day 1. `wethIndex` (0 or 1) must be verified per chain at LP open — never hardcoded. Pool addresses pending NV-12. |

---

### 8.10 WL API Surface — Two Distinct Auth Planes

> **Source:** WL_ADMIN_API_GUIDE_EN.md + WL_API_CONNECTION_GUIDE_EN.md (absorbed 2026-06-16)
> Two completely separate API surfaces with different auth mechanisms. Never mix credentials.

#### 8.10.1 Plane separation

| Plane | Mount | Auth | Caller | Purpose |
|---|---|---|---|---|
| **Admin plane** | `/api/wl-admin/*` | `X-Wallet-Address` header + `admin_wallets` role check (same as rest of ADMIN) | SOTATEK admin FE (PTL-02) | CRUD ledger/bookkeeping: wl_codes, wl_members, wl_master_wallets |
| **Helix plane** | `/api/wl/*` | HMAC-SHA256 + nonce + body signing (`body_sha256`, G-7) — 4 mandatory headers: `x-api-key`, `x-timestamp`, `x-nonce`, `x-signature` | Helix server (server-to-server) | Ledger API pull + Bot/Position API |

#### 8.10.2 Admin plane — role gates (from `access-control.ts`)

| Role | Gate | Allowed on |
|---|---|---|
| `viewer` | `requireViewer` | All GET endpoints |
| `admin` / `super_admin` | `requireOperator` | `POST /members`, `PATCH /members/:id` |
| `super_admin` only | `requireSuperAdmin` | `POST/PATCH /codes`, `POST /codes/:wl_code/rotate-key`, `POST/PATCH /masters` |

#### 8.10.3 wl_codes state machine

```
POST /codes ──▶ active ──────────────────────────────▶ suspended
                  ▲   PATCH {status:"suspended"}             │
                  └──────────────────────────────────────────┘
                        PATCH {status:"active"} (resume)
```
- `→ suspended`: trigger for §12 suspend flow; cron (Layer B) performs actual on-chain unset/hold asynchronously. UI should show "suspending…" not "suspended & settled".
- New member registration rejected when WL is suspended (`409 wl_code_suspended`).

#### 8.10.4 wl_members state machine

```
          POST /members (new)          PATCH action=start_leaving
(none) ──────────────────────▶ active ───────────────────────────▶ leaving
                                  ▲  ▲                                 │
           PATCH cancel_leaving   │  └─────────────────────────────────┘
                                  │
                                  │  POST /members (rejoin, epoch++)
                                  └──────────── left ◀── PATCH action=mark_left
```
- **One-wallet-one-WL constraint (★ E-5)**: wallet cannot be `active`/`leaving` in two WLs simultaneously → `409 active_in_another_wl`.
- Optimistic locking on transitions: `409 not_found_or_wrong_state` when row is not in expected `from` state — re-fetch and retry.
- `membership_epoch` increments on each rejoin (★ B-2).

#### 8.10.5 wl_master_wallets

- Endpoints are bookkeeping-only. On-chain rotation (★ F-3) is Layer B cron, not these endpoints.
- One master per `(wl_code, chain_id)` — `409 already_exists_for_chain` on duplicate.
- `chain_id` ∈ {10 (OP), 8453 (Base)} only.

#### 8.10.6 api_key vs HMAC secret

- `POST /codes` and `rotate-key` generate and return `api_key` (public identifier, `wlk_` prefix) — visible in `GET /codes`.
- HMAC **secret** is NEVER stored in D1, never returned by any endpoint. BNZA places it in `WL_API_SECRETS` Workers Secret out of band.
- FE never handles the HMAC secret. Surface the `next_step` reminder to operators on create/rotate.
- Rotate-key is breaking for the partner: old `api_key` stops resolving immediately. Must coordinate WL_API_SECRETS update + Helix notification before triggering.

#### 8.10.7 v1.7.6 increment: opFee/PF ledger capture (§3.7.1)

- WlNetSent scanner (§3.7) now also records `opfee_usd` / `pf_usd` from the same tx's on-chain transfers (Router→treasury / Router→pfCollector).
- Columns `opfee_usd` / `pf_usd` already exist in `wl_bot_payouts` since migration 0026 — **no new migration**.
- Scanner-side only: no contract change, no change to Helix disclosure (§7.4).
- Impact on admin: Reports screen (FM-ADM-06) can surface WL opFee/PF breakdown per bot. NULL = uncomputable; 0 = dust (§2.1); >0 = confirmed.

#### 8.10.8 WL implementation backlog (BNZA-owned, post-launch)

From WL_HANDOVER_EN.md §B — settled decisions, not re-open items:
1. Rotation-trigger admin endpoint (state machine §6.8 implemented; initiation currently manual DB op)
2. Guard on `PATCH /wl-admin/masters/:id` direct changes (today trips invariant reconciler → needs_repair)
3. Queue-consumer WL branches (production runs `USE_QUEUE=false` — port June WL/serial-path changes before enabling Queue v2)
4. GC cron for acked `wl_holds` / old escalations
5. ZapMintFor start-path fallback (TODO in code)
6. D1 integration tests for WL SQL

---

## 10. Recommended Next Steps

1. **Complete FRD cho Smart Contracts** — `03_modules/_shared/frd-wl-contracts.md` (DONE ✅)
2. **Complete FRD cho BNZA-OPERATOR WL Backend** — `03_modules/operator/frd-wl.md` (DONE ✅)
3. **Emit FRD cho BNZA-MOBILE** — WL gate + LP Bot status (Line 1, P0)
4. **Emit FRD cho BNZA-ADMIN** — WL Mgmt + PF Distribution (Line 1, P0)
5. **Escalate OQ-2** — Ask zen for EXBOT interface specs (Line 2 blocker)

> **Note:** `wl-admin` (PTL-06) and `wl-mobile` (PTL-01) FRD generation is Helix responsibility — not Sotatek. All files in those modules are kept as reference only (`status: out-of-scope`).

### Suggested FRD Order (Line 1 — Sotatek Scope)

| Order | Module | Reason |
|---|---|---|
| 1 | `smart-contracts` | Phase 2 contracts; foundational for WL net routing |
| 2 | `bnza-operator-wl` | Phase 1/1.5 OPERATOR WL backend; Ledger API + scanner |
| 3 | `mobile` (BNZA-MOBILE) | WL launch critical, greenfield build |
| 4 | `admin` (BNZA-ADMIN) | WL launch critical, mock→real |
| 5 | `bnza-pool` | Post-WL, well-specified |
| 6 | `bnza-ex` | Lowest priority, well-scoped |

### Commands

```
# Gen FRD cho BNZA-MOBILE
/ba-start frd --slug bnza-sotatek-260519-0000 --module mobile

# Gen FRD cho BNZA-ADMIN
/ba-start frd --slug bnza-sotatek-260519-0000 --module admin
```

---

## 11. Source Traceability

> All content in this backbone is self-contained. External client documents have been absorbed inline — no external file access is needed to understand this document.

| Backbone Section | Absorbed from | Inline location |
|---|---|---|
| Actors | Module SPECs (auth sections) | §1 Shared Actors |
| Portal Matrix | Deployment Guide + Module SPECs | §2 Portal Matrix |
| Permissions | Module SPECs (access control) + OPERATOR SPEC (RBAC) | §3–§4 Permissions |
| Feature Map | Intake §3 (scope definition per module) | §5 Feature Map |
| WL Smart Contracts FRD | WL_SPEC_SOTATEK_EN_v1.1.md §5.1–§5.6, §10.3 | `03_modules/_shared/frd-wl-contracts.md` |
| BNZA-OPERATOR WL Backend FRD | WL_SPEC_SOTATEK_EN_v1.1.md §2–§10, Appendix A/B | `03_modules/operator/frd-wl.md` |
| Dependencies | Intake §4 + OPERATOR Queue v2 SPEC + Router SPEC | §6 Dependency Graph |
| Priority | Intake §5 (timeline) + Roadmap milestones | §7 Priority Ordering |
| Auth model | Module SPECs + OPERATOR SPEC | §8.1 Authentication Model |
| Fee model | Router v2 SPEC (SPEC_V2.md) | §8.2 Fee Model |
| Scale requirements | Queue v2 SPEC §1.2 + Roadmap M3 | §8.3 Scale Requirements |
| Deployment topology | Deployment Guide + codebase audit 2026-05-21 | §8.4 Deployment Topology |
| Design language | Module SPECs (UI sections) | §8.5 Shared Design Language |
| Testing standards | Intake §7 (OQ-7 resolved) | §8.6 Testing Standards |
| EXBOT contract architecture | SPEC v5.2.1 Option C decision | §8.7 EXBOT Contract Architecture |
| WL+MLM system architecture | WL_SPECv1.7.6_EN.md (all layers); Layer B/C = Helix-owned OOS, kept as reference | §8.8 WL+MLM System Architecture |
| OQs | Intake §10 (inherited hold items) | §9 Inherited Open Questions |
| EXBOT strategy SPEC (zen-approved, source of truth for Module 4) | **SPEC_v5.2.6_EN.md** — client-provided external file, NOT in repo. Local path at time of writing: `/Users/hienduong/Downloads/SPEC_v5.2.6_EN.md`. Repo only has v5.2.5 at `docs/bnza-exbot/docs/SPEC_v5.2.5.md`. Key content absorbed inline in §8.9. | §8.9 (formulas, NV items, behavioral rules, Phase 0 conditions) |
| WL API surface: admin plane vs Helix plane, auth separation, wl_codes/wl_members/wl_master_wallets state machines, api_key/secret separation, v1.7.6 opFee/PF scanner capture, post-launch backlog | **WL_ADMIN_API_GUIDE_EN.md** (absorbed 2026-06-16) + **WL_SPECv1.7.6_EN.md** §3.7.1 (absorbed 2026-06-16) + **WL_SPEC_TO_v1.7.6_DELTA_EN.md** §1/§4/§6 (absorbed 2026-06-16) + **WL_HANDOVER_EN.md** §A/§B/§C (absorbed 2026-06-16). Note: WL_SPEC_TO_v1.7.5_DELTA_EN.md content was applied manually Jun 04 (backbone sync WL_SPEC_SOTATEK_EN_v1.0/v1.1); now formally logged. WL_API_CONNECTION_GUIDE_EN.md is Helix-facing only — no SOTATEK admin impact; logged in intake §13. | §8.10 WL API Surface |
