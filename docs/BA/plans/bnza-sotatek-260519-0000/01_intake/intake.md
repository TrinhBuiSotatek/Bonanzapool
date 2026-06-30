---
type: intake
status: in-review
created: 2026-05-19
updated: 2026-06-26
owner: "@hien.duong"
priority: P0
tags: []
version: "0.7.0"
links:
  - 01_intake/plan.md
engagement_mode: formal
lang: en
changelog:
  - "2026-06-26 | manual | renumber OQ-ADM-* to match 3-digit zero-padded format"
  - "2026-06-18 | /ba-do audit-v1.7.6 | §3 Module 2: HMAC show-once, UNION revenue, raw USDC display, task F P3 backlog (3 screens); §4.6: BNZA-ADMIN role matrix Viewer/Admin|Operator/Super_Admin"
  - "2026-06-18 | /ba-do hld-decisions | §3 Module 4: update smart contracts list (9 contracts, strategy dispatch, PositionManager); add emergencyTransfer constraint; Phase 0 condition 2 remove multiSig"
  - "2026-06-16 | /ba-impact | §13 Document History: absorb WL_SPECv1.7.6_EN + DELTA v1.7.5→v1.7.6 + WL_HANDOVER_EN + WL_ADMIN_API_GUIDE_EN + WL_API_CONNECTION_GUIDE_EN; backbone §8.10 + §5.2 FM-ADM-01 API detail updated"
  - "2026-06-12 | /ba-do drift-2 | §3.2 Current State sync: WL Master Wallet + PF Distribution → ✅ Real API; WL Mgmt → 🟡 Partial; WL Member + WL Bot Monitor → 🔸 Mock UI"
  - "2026-06-04 | /ba-impact | sync WL_SPEC_SOTATEK_EN_v1.1 §4.4: thêm §4.2 LPBot constraint về dual-auth post-record (HMAC WL path vs X-Wallet-Address regular path); CORS N/A; explicit starter wallet"
  - "2026-06-04 | /ba-impact | sync with WL_SPEC_SOTATEK_EN_v1.0: BnzaSplitter→pfCollector; thêm WL member lifecycle + master wallet + bot activation monitor vào BNZA-ADMIN scope; update PF Distribution task; update Out of Scope; thêm Router wlMaster + LPBot stop constraints; resolve merge conflict"
  - "2026-06-02 | manual | Module 1A: rewrite WL Admin description — phân biệt rõ WL-ADMIN (PTL-06) vs BNZA-ADMIN (PTL-02); thêm portal/actor/folder ref; cleanup OQs; Module 2: thêm portal/actor/folder ref; rewrite \"what manages/does not manage\" boundary; update §4.6 auth model thêm row PTL-06 WL-ADMIN"
  - 2026-06-02 | manual | remove external source path references from all module sections — content is self-contained
  - "2026-06-01 | manual | §13: rename \"Source Documents\" → \"Document History\"; replace external paths with absorption map — all content now inline, no external file access needed"
  - "2026-06-01 | manual | Module 1B: inline full WL+MLM architecture (3-layer structure, money flow, terminology, tenant config schema, title differential method, regulatory principle) — BA doc now self-contained, no need to read client spec"
  - 2026-06-01 | manual | consolidate WL Mobile (PTL-07) into BNZA-MOBILE (PTL-01) as single unified WL Mobile module; remove separate Module 1B entry; update auth model, source, key features
  - 2026-06-01 | manual | restructure into 2 parallel lines; add WL+MLM system scope (Line 1); ExBot+Backtest as Line 2; integration point at ExBot-into-WL; add Helix handover context + new source docs
  - "2026-05-27 | manual | meeting 2026-05-27: MLM-first strategy (LD-8), EXBOT deferred post-WL, June 2nd go-live scope, scalability risk (Daniel report), mainnet migration risk (Andrew report)"
  - "2026-05-26 | manual | update from ECOSYSTEM_OVERVIEW v2.0 + SPEC v5.2.5: BnzaExVault decision, EXBOT Phase 0 gate (4 conditions), P0-F.0 hotfix list, SPEC version ref corrected"
  - "2026-05-26 | manual | sync client-docs: updated §13 source paths to docs/ prefix; updated Assumption 5 (Router v2.2.2-fix-2 + LPBot v1.2 deployed by zen, Step 6 OOS)"
  - "2026-05-21 | manual | codebase audit: corrected tech stacks, deployment topology, current state per actual source-code monorepo; resolved OQ-1 deployment paths; added LD-7 monorepo layout"
  - "2026-05-20 | /ba-start | resolved OQ-1: Monorepo"
  - 2026-05-20 | /ba-start | added Locked Decisions (LD-1→LD-6) + artifact structure
  - 2026-05-19 | /ba-start | resolved 4/8 OQs, updated intake with resolutions
  - 2026-05-19 | /ba-start | initial intake from existing docs + cross-module brainstorm
---

# BNZA Ecosystem — SOTATEK Scope Intake

## Markers

- **📋 Spec** — feature is in the original client spec
- **⚡ Dev-built** — feature was built by dev team, NOT in client spec

---

## 1. Project Context

**Project**: BNZA Ecosystem — Automated DeFi/CeDeFi platform
**Client**: MEGABUCKS, Inc. (zen — Founder/CTO)
**Vendor**: SOTATEK (8-week engineering contract, May 18 – July 12, 2026)
**BA Scope**: SOTATEK deliverables only
**Engagement Mode**: Formal (full artifact set for vendor handoff)

---

## 1A. Delivery Structure — 2 Parallel Lines

Project is organized into **2 parallel delivery lines** that operate independently and converge at the ExBot-into-WL integration point.

### Line 1 — WL + MLM System + Maintain Pool/Exchange

**Scope**:
- Develop WL + MLM system (admin tool + mobile MLM app) — new scope from Helix handover
- Maintain and fix bugs: BNZA-POOL + BNZA-EX (existing products)

**Modules**: `wl-admin`, `wl-mobile`, `mobile` (BNZA-MOBILE), `admin` (BNZA-ADMIN), `bnza-pool`, `bnza-ex`

### Line 2 — Exchange Bot + Backtest

**Scope**:
- Develop Exchange Bot infrastructure (EXBOT)
- Develop Backtest system

**Modules**: `exbot`, `backtest` (TBD)

### Integration Point

The two lines **converge** when Exchange Bot is integrated into the WL system — ExBot becomes the bot engine powering WL users' positions, replacing/extending LPBot. This integration point is a future milestone, not in current sprint scope.

---

## 2. Stakeholders

| Role | Name/Entity | Interest | Influence |
|------|-------------|----------|-----------|
| Founder/CTO | zen | Strategy, EXBOT R&D, final approval | Decision maker |
| Engineering Vendor | SOTATEK (8 engineers) | Implementation, testing, deployment | Executor |
| AI Advisor | Claude | Technical Q&A, design review, bridge | Facilitator |
| End Users | Retail LP users, traders | Self-directed LP/trading | Consumer |
| WL Partners | Institutional brokers | Branded MLM platform for end-users | Revenue driver |
| WL End Users | MLM participants under each WL | Earn rewards via referral tree | Consumer |
| WL Operator Admins | WL operations team | Monitor/operate daily reward distribution | Internal ops |
| IBs | Introducing Brokers | Referral-based LP service | Distribution |

---

## 3. Scope Definition (SOTATEK Deliverables)

### Line 1 Modules

#### Module 1A: WL Admin System — PTL-06 (NEW — Line 1) 📋 Spec

**Portal**: PTL-06 — `wl-admin.bnza.io` (TBD)
**Primary Actor**: ACT-07 (WL Operator Admin) — WL operations team; internal tool, not visible to end users
**BA Folder**: `03_modules/admin/` (sub-system B within admin module — see §3 Module 2 for sub-system A)

**Description**: Layer B of the 3-layer WL structure (see §1B.1). An internal PC-only tool used by the WL operator's own operations team to **monitor, operate, and recover** the daily MLM reward distribution. The system receives net from BNZA via Ledger API, computes MLM allocation off-chain, and pays out via on-chain RewardDistributor.

**What WL-ADMIN manages** (daily operations):
- Daily distribution pipeline — monitor state machine, recover from BLOCKED states
- Referral tree — view/edit parent-child relationships, resolve registration omissions
- Per-user MLM data — cumulative reward, Cap status, AUM, lineage
- Distributor Contract — USDC balance monitoring, refill Treasury → Distributor
- Reward Settings — rank table, title table, referral rates, Cap enable/disable, same-rank bonus
- Admins & Auth — manage WL ops team accounts (email/role/2FA)

**What WL-ADMIN does NOT manage** (out of scope for this system):
- WL partner account creation (that is BNZA-ADMIN PTL-02 / zen's responsibility)
- BNZA bot configs, plan specs, access control (BNZA-ADMIN only)
- Fee distributions (PF 70/30 split — BNZA-ADMIN only)

**Key Features**:
- Daily distribution pipeline (state machine: BOT_SYNC → LEDGER_FETCH → PENDING_SNAPSHOT → SNAPSHOT → UPLINE → COMPUTED → ENQUEUED → ONCHAIN → VALIDATED → COMPLETED)
- Reward computation: rank reward (30–62%) + title differential V1–V7 + same-rank bonus (5%) + leader token airdrop (V4+)
- RewardDistributor on-chain payout (Base + OP mainnet, Push/Claim hybrid, minPayout threshold)
- Admin console: 7 pages — Dashboard / Distribution Jobs / Users / Referral Tree / Distributor Contract / Reward Settings / Admins & Auth
- Multi-tenant: one codebase supports multiple WL operators (switched by tenant config)
- BNZA API integration: Ledger API HMAC-SHA256 (stream 1) + Position API (stream 2) + Bot Operations API (stream 3)
- **Delivery phases**: Phase 1 (OPERATOR API + HMAC-SHA256 auth for Helix server-to-server calls) → Phase 1.5 (WlNetSent on-chain event scanner + `wl_token_attribution_history` reconciler — indexes block-time-correct WL attribution per tokenId: `wl_code`, `membership_epoch`, `master_wallet_address`, `bot_config_id`, `bot_position_id` per block range) → Phase 2 (contract upgrade deploy: `BnzaRouterUpgradeable` + `BnzaLpBot` WL extensions)

**Auth**: SSO (Cloudflare Access) + 2FA (TOTP mandatory). All write operations require reason note + Slack audit mirror. Roles: Super / Operator / Read-only.

**Tech Stack**: Cloudflare Pages (frontend) + Cloudflare Workers (backend/cron) + Cloudflare D1 (25 tables) + Cloudflare Queues
**Effort**: TBD (pending SOTATEK technical proposal)

**Open questions (pending WL operator confirmation)**:
- Same-rank bonus eligibility (same title vs same rank, equal vs weighted split)
- Leader airdrop token formula + conditions (`leader_bonus_json`)
- Cap policy (forfeit vs carry, enabled at launch?)
- AUM=0 / below-lowest-rank handling (no fee reward vs save at lowest rank)
- Cross-chain claimable UX (separate per chain vs aggregate to representative chain)

---

### Module 1B: WL Mobile (Unified — Line 1) 📋 Spec

**Reference base**: `bnza-ecosystem/oceanpool-mobile-mlm` (Oceanpool mock — Next.js, MLM-focused UI)

**Note**: Previously split into "Module 1B (WL Mobile PTL-07)" and "Module 1C (BNZA-MOBILE PTL-01)". Consolidated into one module. Single codebase, single portal. EXBOT flow excluded from scope (deferred post-WL per LD-8).

**Description**: Layer C of the 3-layer WL structure. Mobile PWA for MLM participants under each WL operator. Displays only finalized post-allocation amounts computed by the admin system (Layer B). Core PWA infrastructure (WL gate, LP Bot, chain switching) combined with MLM reward/claim/community features.

**Tech Stack**: Vite + React 19 + TypeScript 5.9 + Zustand + Tailwind 4 + shadcn/ui + Reown AppKit + PWA
**Hosting**: Cloudflare Pages
**Effort**: 3-4 weeks (2 FE engineers)

---

#### 1B.1 System Architecture — 3-Layer Structure

The WL+MLM system is organized into 3 layers with strict responsibility boundaries:

```
┌──────────────────────────────────────────────────────────────┐
│ [Layer A] BNZA core                                          │
│   Each user's LP earned → deduct opFee/PF → send net to WL  │
│   pool. Provide Ledger API (whose / how much net).           │
│   Principal returned DIRECTLY to user (never through WL).   │
└───────────────┬──────────────────────────────────────────────┘
                │ ① net remittance (USDC, per chain)
                │ ② Ledger PULL (HMAC-SHA256)
                ▼
┌──────────────────────────────────────────────────────────────┐
│ [Layer B] WL Admin System  (Module 1A)                       │
│   Fetch ledger → compute rank reward + MLM bonuses (off-chain│
│   → instruct RewardDistributor to pay out (on-chain)         │
│   + Admin console for monitoring, tenant config, incidents   │
└───────────────┬──────────────────────────────────────────────┘
                │ ③ RewardDistributor pays finalized amount to each user
                ▼
┌──────────────────────────────────────────────────────────────┐
│ [Layer C] WL Mobile  (Module 1B — this module)               │
│   Displays only finalized post-allocation amounts            │
│   ★ Raw Uniswap uncollected fees are NEVER shown             │
└──────────────────────────────────────────────────────────────┘
```

| Layer | Party | Responsibility |
|---|---|---|
| A | BNZA | Deduct opFee/PF from earned; send net to `wlMaster[tokenId]`; provide ledger. Principal returned directly to user. |
| B | WL Admin System | Compute MLM allocation from net; pay out via RewardDistributor on-chain. |
| C | WL Mobile | Display only. No computation, no remittance. |

**Regulatory key point**: Principal is returned directly to the user by BNZA — it never enters the WL master account. The admin system handles only net (fee revenue share) and never touches the principal.

---

#### 1B.2 Terminology Glossary

| Term | Definition |
|---|---|
| **WL** | White-label MLM operator. BNZA's customer. |
| **Tenant** | One WL operator = one tenant. Admin system and mobile are multi-tenant. |
| **earned** | Raw uncollected fees generated by a user's Uniswap V3 LP position. |
| **net** | Amount sent to `wlMaster[tokenId]` = earned − opFee (0.5%) − PF (30% of afterOp). Allocation source. |
| **WL master account** | Per-bot, per-chain address stored in Router on-chain storage (`wlMaster[tokenId]`). Set by BNZA via `setBotWlMaster` after bot start. Net from WL bot fees is sent here; principal never enters here. |
| **Fee reward** | User's own share of net = net × rank reward rate (30–62%). Displayed on mobile. |
| **MLM pool** | Remainder after fee reward = net × (1 − rank reward rate). Source for all MLM bonuses. |
| **Referral reward** | Allocated from MLM pool to uplines: per-tier referral + title differential + same-rank bonus. |
| **Rank** | Investment tier based on user's AUM. Determines fee reward rate (30–62%). |
| **Title** | MLM tier (V1–V7) based on team TVL. Basis for title differential bonus. |
| **RewardDistributor** | On-chain payout contract (Base/OP) deployed by WL. Distributes finalized USDC to each user. |
| **Claimable** | Amount sitting unclaimed on RewardDistributor (accrued below minPayout threshold). |
| **Push** | Auto-send by admin system when accumulated reward ≥ minPayout. WL bears gas. |
| **Claim** | Manual pull by user via RewardDistributor.claim(). User bears gas. For fractions below minPayout. |
| **Cap** | Optional reward ceiling per tenant = AUM × cap_multiplier. When reached, no further reward accrues. |
| **Leader perk** | Non-USDC token/airdrop bonus for V4+ title holders. Separate track (bonus_airdrops). |

---

#### 1B.3 Money Flow — End-to-End

```
[Layer A: BNZA core]
earned (user's raw LP uncollected fees)
  − opFee 0.5%                → BNZA treasury (Buyback & Burn)
  = afterOp
  − PF (afterOp × PF rate)    → pfCollector EOA (BNZA's share, single account, no on-chain Splitter in v1)
  = net                       ★ Sent to WL master account (USDC, per chain, per WL bot)
```

> **[SCOPE CHANGE — WL_SPEC_SOTATEK_EN_v1.0 §1.2, §2]**
> Hai thay đổi so với client spec cũ (WL_SPEC.md §3, §5):
> (1) PF → `pfCollector` single EOA, không phải BnzaSplitter contract. BnzaSplitter removed từ v1.
> (2) Net của WL bot → `wlMaster[tokenId]` (1 master account per WL), không phải "WL pool wallet"
>     theo model cũ. Helix (WL) tự handle MLM distribution từ master account này.
> Cả hai điểm này ảnh hưởng trực tiếp đến FM-ADM-02 (PF Distribution) và FM-ADM-01
> (WL partner → master wallet) trong BNZA-ADMIN.

[Layer B: Admin System — allocation from net]
net
  ├─ Fee reward = net × rank reward rate (30–62%)
  │     → User's own share. Displayed on mobile as "Fee reward".
  │
  └─ MLM pool = net × (1 − rank reward rate)   [38–70% of net]
        ★ ALL MLM bonuses come from this pool. Never added directly to net.
        ├─ Referral reward  = MLM pool × tier rate (e.g. 10% L1 / 5% L2 / 2% L3)
        ├─ Title bonus      = differential method (see §1B.5)
        ├─ Same-rank bonus  = MLM pool × 5% total envelope, split equally
        ├─ Leader bonus     = token/airdrop (NOT USDC), V4+ only → bonus_airdrops
        └─ Remainder        = WL treasury share

[Layer B → User]
RewardDistributor (Base/OP) pays finalized USDC:
  fee reward + referral + title diff + same-rank
  Leader bonus paid separately (token/airdrop track)
```

**Structural guarantee**: All MLM bonuses are paid from the MLM pool (not added to net). Title uses differential method → lineage total is capped at the highest title rate. It is structurally impossible to exceed the pool.

---

#### 1B.4 Rank Table (default — per tenant config)

| Rank | Min AUM (USD) | Fee Reward Rate |
|---|---|---|
| starter | $1,000 | 30% |
| basic | $5,000 | 40% |
| advanced | $10,000 | 48% |
| professional | $50,000 | 55% |
| elite | $100,000 | 62% |

Rank is determined by the user's current AUM. Higher AUM → higher rank → higher fee reward rate. Rank table is per-tenant and configurable.

---

#### 1B.5 Title Table & Differential Method (default — per tenant config)

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

Example: User A (V1, 5%) → B (V3, 12%) → C (V5, 20%)
- C receives: 20% of MLM pool from A's net
- B receives: (12% − 5%) = 7% of MLM pool from A's net (only the diff over A)
- A's upline above C: (next title rate − 20%) of MLM pool

This ensures the lineage total never exceeds the highest title rate in the chain.

---

#### 1B.6 Mobile — 3 Communication Partners

Mobile communicates with 3 distinct systems. Do not confuse them.

| # | Partner | Purpose | Direction | Funds |
|---|---|---|---|---|
| ① | Admin System API (Layer B) | All display data — finalized post-allocation amounts, rank, tree, tenant config | Read only | Not moved |
| ② | BNZA Bot API (OPERATOR) | Bot start/stop (creating/dissolving LP positions) | User-initiated | Moved by user's own wallet |
| ③ | RewardDistributor (on-chain) | Claim USDC rewards | User-initiated | Received by user |

**Critical rule**: Mobile MUST NOT read LP NFTs directly. All displayed amounts come from Admin System API (①) — already finalized post-deduction.

---

#### 1B.7 Key Features

- SIWE/JWT auth (24h, re-sign on expiry; tenant resolved by subdomain + signature domain)
- WL gate: wallet connect → SIWE sign-in (no invite code)
- Fee reward display (net × rank reward rate, from admin system API — no raw LP fees)
- Referral reward display (referral + title diff + same-rank, from MLM pool)
- Leader perk display (token/airdrop, V4+, from bonus_airdrops)
- Claimable balance + Claim USDC (RewardDistributor.claim(), gas borne by user)
- Bot start/stop via user wallet (zapMint/stop, wl_code propagation)
- LP Bot status display (from admin system API, not OPERATOR directly)
- Referral tree / community view (team TVL, downline list, per-tier rates)
- Multi-tenant branding (logo, theme, rank table, referral tiers from tenant config)
- Chain switching (Base 8453 + OP 10 only; Arbitrum excluded)
- PWA (manifest, service worker, 100dvh, safe-area)
- i18n (ja/en minimum; per tenant-supported languages)

---

#### 1B.8 Dependencies

- Admin system API (`/api/mobile/*`, SIWE/JWT) — provides all display data
- BNZA Bot API (OPERATOR, via WL backend) — Bot start/stop with wl_code
- RewardDistributor on-chain (Base + OP) — Claim flow
- Reown AppKit (wallet connect + SIWE) — already used in POOL + ADMIN

---

### Module 2: BNZA-ADMIN — PTL-02 (Real API Integration — Line 1) 📋 Spec / ⚡ Dev-built

**Portal**: PTL-02 — `ops.bnza.io`
**Primary Actor**: ACT-04 (zen / Admin) — Cloudflare Access (zen@bnza.io) + wallet connect
**BA Folder**: `03_modules/admin/` (sub-system A within admin module — see §3 Module 1A for sub-system B)

**Description**: Internal management dashboard for zen to oversee the entire BNZA ecosystem. Manages product infrastructure, configs, and WL partner accounts. Currently many features are UI skeletons (mock). SOTATEK needs to connect them to the real OPERATOR API.

**What BNZA-ADMIN manages**:
- Bot configs: view all bots, force-stop, plan_specs version management
- User management: allowed/blocked addresses, RBAC roles
- WL partner onboarding: create/edit/deactivate WL partner accounts (name, logo, referral code, deposit tier) — this creates the WL partner record; daily operations happen in WL-ADMIN (PTL-06)
- WL member lifecycle: register member (wallet + wl_code), initiate two-phase leave (pending → unset confirmed → left), rejoin (epoch++), membership_epoch tracking
- WL master wallet management per chain: register, rotate (two-phase: unset old → set new on-chain), suspend/resume wl_code
- WL bot activation state machine monitor: view pending_set SLA / failed_set / needs_repair backlogs; admin actions: retry set, force-normalize (two-phase)
- PF distribution config: set recipients and shares (off-chain tracking only; PF on-chain still goes to pfCollector EOA single account)
- IB partner management: introduce broker CRUD
- System settings: global switches (global_bot_enabled, safe_mode, exbot_enabled, etc.)
- Relayer monitoring: balance, health status
- Reports: fee collection, bot performance, user activity
- TOKEN management: burn/supply/vesting/treasury/builder-fee (mock OK, P3)

**Current State** (verified from source 2026-05-21):
- ✅ Real API ⚡ Dev-built: POOL management, User management, Audit logs, Access Control, Auth/RBAC, Bot configs, Bot positions, Rules, Notifications, Fee collections, Fee distributions, Daily snapshots, Relayer wallets, Plan specs, WL Master Wallet Mgmt, PF Distribution
- ✅ Scaffold complete ⚡ Dev-built: 16 pages registered (dashboard, users, bots, logs, fee-distribution, access, system, builder-fee, burn, supply, vesting, treasury, ib, whitelabel, relayer, reports)
- ✅ Wallet integration ⚡ Dev-built: @reown/appkit with X-Wallet-Address header
- 🟡 Partial ⚡ Dev-built: WL Management (suspend/resume real API; list/CRUD still mock)
- 🔸 Mock UI ⚡ Dev-built: WL Member Lifecycle, WL Bot Lifecycle Monitor (UI added post-2026-05-21, no real API)
- 🔸 Mock/incomplete 📋 Spec: TOKEN mgmt, IB mgmt, Dashboard metrics, System Settings, Relayer monitoring, Reports

**SOTATEK Tasks** (convert mock → real API):
- **E: WL Management** — Partner onboarding, earnings tracking, payout history, logo dynamic switching; **thêm mới**: WL member lifecycle UI (register/leave/rejoin/epoch), master wallet management per chain, wl_code suspend/resume; **API Key management**: tạo/revoke API key cho WL partner — FE hiển thị HMAC secret key **một lần duy nhất** (show-once), không lưu hoặc xử lý secret key sau đó
- **E2: WL Bot Lifecycle Monitor** *(new)* — Monitor screen cho `wl_activation_status` backlog (pending_set SLA, failed_set, needs_repair, rotation in progress, wl_unattributed_events SLA breach); admin actions: retry set, force-normalize; trigger setBotWlMaster/unsetBotWlMaster via OPERATOR API

  > **[NEW — WL_SPEC_SOTATEK_EN_v1.0 §5.1.1, §5.1.2, §6.3, §11]**
  > Spec mới: BNZA-ADMIN là control plane cho WL bot activation state machine.
  > 6 states: NULL | pending_set | active | failed_set | pending_unset | needs_repair.
  > Khi bot stuck, zen cần UI để thấy và trigger recovery (retry/force-normalize two-phase).
  > Không có trong client spec cũ.

- **G: PF Distribution** — Off-chain tracking và config UI cho PF recipients. **Scope giảm so với trước**: PF on-chain vẫn về `pfCollector` single EOA (0xa5B8...C969) — không cần BnzaSplitter contract interaction. UI chỉ manage `fee_distributions` table (ai nhận bao nhiêu, off-chain) và display PF collection history.

  > **[SCOPE CHANGE — WL_SPEC_SOTATEK_EN_v1.0 §1.2 vs WL_SPEC.md cũ §5]**
  > Client spec cũ định nghĩa BnzaSplitter contract — on-chain immediate distribution tới
  > tối đa 10 recipients per group. Spec mới loại BnzaSplitter khỏi v1.
  > BNZA tự handle PF distribution off-chain trong v1. FM-ADM-02 screen không cần
  > gọi BnzaSplitter setters hay trigger on-chain distribution.

- **I: Bot Type Configuration** — Deposit tiers, strategy parameters, limits (complete partial implementation)
- **D: IB Management** — Replace mockIBs with real data
- **C: TOKEN Management** — burn/supply/vesting/treasury/builder-fee (depends on OPERATOR endpoints)
- Dashboard, System Settings, Relayer, Reports — real data integration. **Revenue UNION model**: Dashboard/Reports hiển thị daily revenue = UNION của `fee_collections` (LP bot + EXBOT) và `wl_bot_payouts` (WL bots). **Raw USDC display**: payout/ledger views hiển thị raw on-chain amounts từ `wl_bot_payouts.opfee_usdc` + `pf_usdc` (không phải USD estimate; column suffix `_usdc` per audit v1.7.6; xem OQ-ADM-019 trong FRD)
- E2E tests (Step 8-7, not started)
- **F: Post-Launch Backlog (P3)** — 3 màn hình mới, xây sau go-live: (1) **Escalations Dashboard** — monitor `wl_escalations` table (deep reorg alert, block_hash divergence event; maps FM-ADM-13); (2) **Holds & Corrections** — review `wl_holds`, ACK/mark-resolved flow (maps FM-ADM-14); (3) **Attribution History** — read-only viewer cho `wl_token_attribution_history` (maps FM-ADM-15). Không nằm trong sprint hiện tại.

**Tech Stack** (verified): React 19.2.4 + Vite 8.0.4 + TypeScript 5.9.3 + Tailwind 4.2.2 + shadcn/ui + React Router 7.14.0 + TanStack React Query 5.100.5 + Recharts 3.8.1

**Effort**: 2-3 weeks (1 FE engineer)

**Dependencies**:
- OPERATOR API endpoints (WL, PF distribution, TOKEN endpoints not yet built; 19 other endpoints operational)
- Fee structure: PF 30% model (Router v2.2.2) — Router v1.1 deployed with swapFeeBps 0.5%, collectFeeBps 0.5%, pfBps 30%
- Cloudflare Access (second auth layer for admin)
- i18n: en/ja dictionaries already present

---

### Module 3: BNZA-EX (TradingView Integration — Line 1 Maintain) 📋 Spec / ⚡ Dev-built

**Description**: Hyperliquid perpetuals trading frontend at ex.bnza.io. Needs to integrate TradingView Advanced Charts to replace the current free widget.

**Current State** (verified from source 2026-05-21):
- TradingView Lightweight Charts already integrated and functional ⚡ Dev-built (not "coming soon")
- `tradingview/` directory contains: chartAdapter.js, chartEmbed.js, chartSymbol.js, chartTypes.js, useChartSymbol.js, chartLocale.js, widgetAdapter.js ⚡ Dev-built
- Hyperliquid integration active via @nktkas/hyperliquid 0.32.1 ⚡ Dev-built
- Portfolio page functional ⚡ Dev-built
- 8 language support (ja, en, ko, zh, vi + more) ⚡ Dev-built
- Playwright 1.49.1 already configured for testing ⚡ Dev-built

**SOTATEK Tasks**:
- Upgrade from TradingView Lightweight Charts to TradingView Advanced Charts (licensed)
- Implement `chartingLibraryAdapter.js` (Advanced Charts datafeed + UDF format)
- Configure chart data feed (Hyperliquid WebSocket → TradingView UDF format, symbol resolution, history)
- Order placement UI update (integrate with chart, click-to-trade, TP/SL lines)
- Unit tests (80%+ coverage)

**Tech Stack** (verified): React 18.3.1 + Vite 6.0.3 + JavaScript (NO TypeScript) + Wagmi 3.6.0 + Viem 2.47.6 + TanStack React Query 5.95.2 + Recharts 3.8.1 + @nktkas/hyperliquid 0.32.1

**Effort**: 1-2 weeks (1 FE engineer)

**Dependencies**:
- TradingView Advanced Charts license (needs procurement — zen funds confirmed)
- Hyperliquid API (direct, no OPERATOR dependency) — already integrated
- Adapter interface already defined in codebase (chartAdapter.js branches WIDGET vs CHARTING_LIBRARY)

**Note**: EX uses React 18 + plain JSX (NOT TypeScript). Different stack from ADMIN.

---

### Module 4: BNZA-EXBOT Infrastructure (Line 2) 📋 Spec

**Description**: Backend infrastructure for EXBOT (managed delta-hedged LP Bot). SOTATEK builds infra only — trading logic is zen's proprietary.

**Current Codebase State** (verified 2026-06-12, SPEC v5.2.6 + Google Doc + Sheet):
ExBot runs as a **standalone Cloudflare Worker** at `apps/bnza-exbot/` — separate from OPERATOR. The OPERATOR is a **thin public-facing facade** that forwards only `start/status/close` into ExBot Worker via Cloudflare service binding + internal token. ExBot Worker is NOT directly public.

Dev progress as of tracker (Google Sheet):
- Strategy & Math Engine: **Done** (duy.nguyen6)
- HL SDK spike: **Done**; live HL adapter (signing, orders, position sync): **In Progress** (luong.tran)
- Cron scheduler + Queue wiring: **Done** (structure only, handlers no-op) (duy.nguyen6)
- Vault smart contracts (BnzaExVault.sol): **Todo** (truong.nguyen2)
- Operator Facade API (`/api/exbot/*`): **Todo** (duy.nguyen11)
- Pool UI — EXBOT tab: **Todo** (duy.nguyen11)

**SOTATEK Tasks** (infrastructure per zen's interface specs, SPEC v5.2.6):
- **D1 Schema** (primary tables per SPEC v5.2.6 Theme D): `bots`, `bot_runtime_state`, `hedge_legs`, `hl_agent_keys`, `queue_idempotency`; optimistic concurrency via `state_version` guard
- **Queue Topology** (10 queues): `bot-scan`, `light-check`, `hedge-sync`, `reconcile`, `deep-audit`, `price-near-stop-audit`, `partial_repair`, `user_redeem` (highest priority, SLA 5 min), `notification`, `metrics-rollup`
- **Durable Objects**: `HLRateLimitDO` (sliding-window rate limit for HL API), `UserLockDO` (lease-based 1-bot-per-user lock), `MarketDataDO` (price/tick cache for light-check)
- **Cron Jobs**: deep-audit `*/360 * * * *`, other intervals TBD per SPEC
- **Hyperliquid Adapter**: Rate limit handling (1,200 weight/min ceiling), cloid tracking, error parser, reconcile glue; light-check must NOT call HL directly (rate limit exceeded at 10k bots)
- **Operator Facade API additions** (`/api/exbot/*`): `start`, `status`, `close`, `agent-key`, `margin` — proxied only, ExBot Worker owns logic
- **Smart Contracts** (9 contracts, zen's scope + SOTATEK integration via ABI): BnzaExVault (USDC custody + `executeStrategy` dispatch), BnzaExPositionManager (LP NFT custody — separate from vault), OpenPositionStrategyV1, RedeemStrategyV1, RebalanceStrategyV1, CollectFeeStrategyV1 (stateless strategies via DELEGATECALL), TokenRouter (fee/payout routing), RedemptionQueue (FIFO async HL redemption queue), ExbotSetupBatch (deploy + wiring)
- **Integration tests**: Queue processing, HL API calls

**Architecture Constraints** (SPEC v5.2.6):
- ExBot Worker standalone — NOT co-deployed with OPERATOR
- Producer/Consumer separation; 10,000 bot throughput = 33.3 bots/sec (Phase A: 1 D1 shard)
- No per-bot HL API call in light-check (rate limit constraint)
- Delta-only hedge adjustment: adjust only Δ(targetSize − actualSize); full close forbidden except for target=0 / emergency / manual reset
- `emergencyTransfer(user, botId)`: Operator-only when contract is paused; no recipient param (funds return to user's own address only); emits `EmergencyRecovery` event. Multi-sig not required.
- D1 write budget gate (Theme D): gated writes to prevent CF D1 write limit breach
- Dual-chain from Phase 1: Base + Optimism LP side; `wethIndex` per chain; hedge side (HL ETH-USD perp) chain-independent
- Agent key encryption: AES-GCM (crypto.subtle), DEK wrapped by master key (Cloudflare Secrets Store), rotation support
- BnzaExVault naming: "BnzaExVault/Vault" = LP NFT custody Solidity contract; "vaultAddress/subaccount" = HL subaccount identifier — unrelated despite name similarity

**Effort**: 3-4 weeks (1 BE engineer)

**Dependencies**:
- zen's interface specifications (SPEC v5.2.6 — zen-exclusive algorithm details; SOTATEK sees interface contracts only)
- Hyperliquid API access (testnet first, mainnet Phase A2+)
- BnzaExVault + BnzaExPositionManager deployment + dual-chain addresses/operator finalized (2 sets: Base + OP)
- HL agent key encryption method finalized (Phase 0 gate condition)

**Phase 0 Start Conditions** (all 4 must clear before Phase A):
1. zen approves SPEC v5.2.6
2. BnzaExVault + BnzaExPositionManager deployed; Base + OP addresses, operator address confirmed (multiSig no longer required for emergencyTransfer per HLD 2026-06-18)
3. HL agent key encryption method confirmed
4. WL stability gate: 7 consecutive days post-launch, zero SAFE_MODE, no major incident

**Confidentiality**: Trading strategy logic (PositionCalc, hedge math, stop strategy, edge filter) is zen-exclusive. SOTATEK sees only infrastructure interfaces.

---

### Module 5: BNZA-POOL Steps 7-8 (Line 1 Maintain) 📋 Spec

#### Step 7: Multi-Bot Support (9-12h)

**Description**: Redesign the AI Bot page for multi-Bot support.

**Current Codebase State** (verified 2026-05-21): POOL app (`apps/bnza-pool/`) is fully operational with:
- 62 React components, 8 pages (dashboard, pools, positions, bot, rules, settings, earnings)
- Bot management already functional (single-bot): BotCard, bot creation, start/stop via wallet TX
- Chain switching already implemented (Base, OP, Arbitrum, Mainnet via Wagmi/Reown AppKit)
- i18n already in 5 languages (ja, en, ko, zh, vi) via `src/i18n/`
- OPERATOR API integration via `lib/operator-api.ts` (bot-configs, bot-positions endpoints exist)
- Data layer: Subgraph + On-chain reads + OPERATOR API

**Key Changes**:
- Remove top 3 KPI cards (duplication with portfolio page)
- Remove "Auto-Configuration Confirmation" (Q7 conflict mitigation)
- Add "Active Bots" section (3-column grid, BotCard component)
- Chain-switching style (show bots for current chain only)
- Max 10 Bots per chain (20 total)
- Bot label: `LP_BOT #<position_id>`
- invested_amount stored as USD-converted value
- Complete i18n in 5 languages

**Phases**:
- Phase 1+3: Remove top KPIs + aggressive Coming Soon + cleanup (3-4h)
- Phase 2: BotCard + Active Bots list + bot-positions API (5-6h)
- Phase 4: Complete i18n (1-2h)

#### Step 8: plan_specs Version Management (29-35h)

**Description**: Integration across 3 repos (POOL + OPERATOR + OPS) for plan_specs version management.

**Key Changes**:
- POOL: Dynamic settings via OPERATOR API, plan_specs_version + snapshot at createConfig, outdated warning on BotCard
- OPERATOR: plan_specs_history table, system_config.plan_specs_current_version, public + admin APIs
- OPS (ADMIN): Auth foundation, Bot plan version management UI, Bot list + force-stop

**Design Policy**:
- plan_specs immutability (v1 never changes, new version = new row)
- bot_configs.snapshot saves plan_specs at createConfig time (immutable)
- localStorage 5-min TTL on POOL side
- BotCard outdated warning when currentVersion ≠ bot_configs.plan_specs_version

**Sub-steps**: 8-1 through 8-7 (schema + APIs + OPS auth + whitelist + Bot plan UI + Bot list + E2E tests)

**Effort**: 29-35h total (4-5 business days)

**Dependencies**:
- OPERATOR D1 migration 0008 (version schema)
- CORS update for ops.bnza.io
- Simultaneous deploy POOL + OPS

---

## 4. Cross-Module Dependencies (Non-SOTATEK → SOTATEK Impact)

### 4.1 Router v2.2.2 (Solidity, on-chain)

| Constraint | Impact on SOTATEK |
|---|---|
| Fee model: 0.5% swap + 0.5% opFee + 30% PF | ADMIN PF distribution UI must match exactly |
| closeForSelf always converts to USDC | MOBILE earnings display = USDC |
| Bot path fixed to USDC/WETH pair | MOBILE Bot UI only shows USDC/WETH |
| setApprovalForAll required for new Router | MOBILE must handle approval flow |
| `wlMaster[tokenId]` mapping in Router storage (post-WL upgrade) | WL bot net → master account, not user. BNZA-ADMIN triggers setBotWlMaster/unsetBotWlMaster via OPERATOR. MOBILE stop flow: principal → user (regulatory clean), net → wlMaster address |

> **[NEW CONSTRAINT — WL_SPEC_SOTATEK_EN_v1.0 §5.1, §5.2.0, §10.3]**
> Router v2 sau WL upgrade thêm `mapping(uint256 => address) public wlMaster` trong Router storage.
> Internal payout functions (_collectAndPayout / _closeAndPayout / _rebalanceClose) đọc
> `wlMaster[tokenId]` trực tiếp — cả Operator path lẫn user self-call đều cho cùng kết quả.
> `setBotWlMaster` / `unsetBotWlMaster` là Operator-only functions.
> `require(wlRecipient == wlMaster[tokenId])` trong public functions là last-line defense.
> Rebalance: Router tự migrate `wlMaster[newTokenId] = wlMaster[oldTokenId]` trong cùng tx.
> ADMIN impact: FM-ADM-01 screen cần quản lý master wallet + trigger set/unset.
> MOBILE impact: stop confirmation cần note net đi đến WL master (không về user như regular bot).

### 4.2 LPBot v1.0.7 (Solidity, on-chain)

| Constraint | Impact on SOTATEK |
|---|---|
| startBot/stopBot callable by user wallet | MOBILE integrates wallet TX for bot lifecycle |
| stopBot net recipient = on-chain `wlMaster[tokenId]`; principal always → user | MOBILE stop flow for WL bots: principal returns to user, net goes to WL master account (not user) |
| **WL bot start/stop post-record: dual auth** | Regular bot start/stop: X-Wallet-Address (existing). WL bot path: Helix server calls BNZA `/api/bot-configs/atomic-start` and `/api/bot-configs/:id/stop` via **HMAC-SHA256** (same scheme as Ledger API §7.2), server-to-server (CORS N/A), starter wallet passed explicitly by Helix. BNZA verifies via tx_hash + NPM ownerOf + BotStarted/ZapMintFor event decode. **(Finalized v1.1 §4.4)** |
| rebalanceBot only by operator | MOBILE cannot trigger rebalance (display only) |
| Rebalance cooldown (10-180 min) | ADMIN Bot Type Config must respect this range |
| Max 10 Bots per chain | POOL Step 7 enforces this limit in UI |

> **[CHANGED BEHAVIOR — WL_SPEC_SOTATEK_EN_v1.0 §4.1, §5.1 step 4, §10.3]**
> Cũ (WL_SPEC.md §6.2): stop → "send net to WL pool" — cơ chế chưa rõ.
> Mới: stopBot là user-signed, Router đọc `wlMaster[tokenId]` on-chain để quyết định net recipient.
> User không thể thay đổi net recipient (không có Operator arg trong stopBot).
> WL bots buộc `autoCompound=false` + `convertToUsdc=true` (enforced on-chain, §5.3).

### 4.3 OPERATOR Queue v2 Architecture

| Constraint | Impact on SOTATEK |
|---|---|
| Producer/Consumer separation | EXBOT infra must follow same pattern (bot-checker.ts, rule-checker.ts are reference implementations) |
| RelayerLockDO per-relayer lock | EXBOT must use same DO pattern (already implemented in `src/lib/relayer-lock-do.ts`) |
| D1 hot + R2 archive | EXBOT tables follow same lifecycle (22 migrations already exist) |
| 10,000 Bot scale from day one | EXBOT infra must be scale-ready |
| daily-collect drain SLO 3h | EXBOT daily operations must not conflict |
| Queue Stage 2 in progress | 3 queues defined (daily-collect, bot-check, rule-check), consumer handlers pending — EXBOT adds 6 new queues |
| Max batch 100, timeout 30s, concurrency 1, retries 3 | EXBOT queues should follow same config pattern |

### 4.4 Technical Debt (36 items)

| High-Priority Item | Impact on SOTATEK |
|---|---|
| #9: Synchronous loop scalability | EXBOT infra must use Queue, not sync loops |
| #11: bot_positions registration failure | POOL Step 7 multi-bot must fix this |
| #12: Bot-ownership logic bug | POOL Step 7 must address |
| #14: Mock data dependency | ADMIN real API integration removes this |
| #18: min_collect_usd not referenced | EXBOT infra should implement threshold |

### 4.5 Strategy v2.0.1

| Decision | Impact on SOTATEK |
|---|---|
| Input: both pair-side tokens | POOL UI accepts USDC or ETH for Bot |
| Output: USDC standardized | All earnings displays in USDC |
| Bot path: USDC/WETH only | MOBILE/ADMIN Bot UI fixed to this pair |
| WL model: 70% partner / 30% BNZA | ADMIN PF distribution must implement this split |

### 4.6 Authentication Model

| Layer | Mechanism | Modules |
|---|---|---|
| Primary | X-Wallet-Address header (no signature) | All frontends → OPERATOR |
| BNZA-ADMIN | Cloudflare Access (zen@bnza.io) + wallet connect + RBAC role check (`/api/me`). Roles: **Viewer** (read-only all) / **Admin\|Operator** (member writes, `wl_members` PATCH, lifecycle ops) / **Super_Admin** (`wl_codes` create/edit + `wl_master_wallets` writes) | PTL-02 only |
| WL-ADMIN | SSO (Cloudflare Access) + 2FA (TOTP mandatory); roles: Super / Operator / Read-only | PTL-06 only |
| WL Mobile | SIWE (Sign-In with Ethereum) → 24h JWT; tenant resolved by subdomain + signature domain | PTL-01 only |

---

## 6. Non-Functional Requirements

| Category | Requirement | Source |
|---|---|---|
| Performance | Sub-100ms bot-check latency | Roadmap M3 |
| Performance | 60fps on MOBILE | Mobile SPEC §15 |
| Availability | 99.9% uptime SLA | Roadmap M3 |
| Scale | 10,000 Bots from day one | Queue v2 SPEC §1.2 — **feasibility under review** (CF concurrent worker limit concern; Daniel preparing infrastructure report) |
| Security | OWASP Top 10 audit | Roadmap M3 |
| i18n | 5 languages (en/ja/zh/ko/vi) | All frontend modules |
| Testing | 80%+ unit test coverage | Roadmap M2 |
| Testing | E2E tests for critical flows | Roadmap M2 |
| Accessibility | PWA (MOBILE), responsive (ADMIN/POOL) | Module SPECs |
| Deployment | CF Workers (OPERATOR), Vercel (POOL), CF Pages (ADMIN, EX, MOBILE) | Deployment guide |
| Build | pnpm 10.11.0 + Turbo 2.5.4 monorepo orchestration | Verified from source |

---

## 7. Assumptions

1. zen provides EXBOT interface specifications (D1 schema, Queue topology, API contracts) before SOTATEK starts EXBOT infra work
2. TradingView Advanced Charts license is procured before EX integration starts (zen funds confirmed)
3. ~~Monorepo strategy decision (May 24) does not block individual module development~~ **Resolved: Monorepo confirmed.** Layout: `apps/bnza-{pool,operator,admin,ex,ecosystem}`, `contracts/bnza-{router,lpbot,contracts}`, `packages/shared-{types,utils}`
4. OPERATOR existing endpoints (bot-configs, users, access-control, bot-positions, rules, notifications, fee-distributions, fee-collections, plan-specs, daily-snapshots, relayer-wallets — 19 total) remain stable during SOTATEK work
5. Router v2.2.2-fix-2 (OP: `0xe4E873DCef553dAb821B03a3caC36B84C5f16B8D`, Base: `0xc70cDE10aE7b7630FBF0778D23A04a84B8f82130`) and LPBot v1.2 (OP: `0xeFA6036307bb4A781bdB27e4Cbf314c9386F9572`, Base: `0xAA42Bb3408Af361013352998FB6A046A790DA814`) are deployed and stable. Step 6 migration (Router v2.2.2 + LPBot v1.2) was completed by zen — NOT SOTATEK scope. SOTATEK builds on top of these deployed versions.
6. Hyperliquid testnet access is available for EXBOT integration testing
7. WL launch decision (May 27) determines priority ordering — if deferred, EXBOT infra priority drops
8. MOBILE will be created as new app `apps/bnza-mobile/` following same patterns as existing apps (Vite + React 19 + TS + Tailwind 4 + shadcn/ui + Reown AppKit)
9. EXBOT infra is a **standalone Cloudflare Worker** at `apps/bnza-exbot/` — NOT co-deployed with `apps/bnza-operator/`. OPERATOR is a thin facade that proxies only `start/status/close` into ExBot Worker via service binding. ~~(v5.2.5 assumed co-deployment — corrected per v5.2.6 + Google Doc June 2026)~~
10. Existing POOL app (Next.js 16, fully operational) requires minimal refactoring for Step 7 multi-bot — primarily UI changes to bot page
11. EXBOT Phase A cannot begin until Phase 0 completes all 4 gate conditions (SPEC v5.2.6 §0.3): (1) zen approves SPEC v5.2.6; (2) BnzaExVault deployed + Base + OP addresses/operator/multiSig finalized (2 sets); (3) HL agent key encryption method confirmed; (4) WL stability gate — 7 consecutive days post-launch with zero SAFE_MODE + no major incident

---

## 8. Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| EXBOT interface specs delayed (zen dependency) | Medium | High | Start with D1 schema + Queue topology (known from README); defer HL adapter until specs arrive |
| WL launch scope too aggressive | Medium | High | Decision checkpoint May 27 confirmed; MLM-first strategy reduces scope |
| MOBILE + ADMIN not ready for WL launch | Medium | High | Dedicated 2 FE + 1 FE; weekly progress reviews |
| TradingView license procurement delay | Low | Medium | EX integration is lowest priority; can defer without blocking WL |
| OPERATOR API changes during development | Low | Medium | API contract freeze during SOTATEK sprint; versioned endpoints |
| Monorepo migration conflicts | Low | Medium | Decision by May 24; if monorepo, migration is separate task |
| Queue v2 architecture complexity for EXBOT | Medium | Medium | Follow existing patterns exactly; pair with zen for architecture review |
| 10,000 bot concurrency on CF infrastructure | **Medium** | **High** | **Daniel preparing CF infrastructure feasibility report — decision pending** |
| Mainnet data migration (~8 users, ~250k fund volume) | Medium | High | Andrew preparing migration validation plan; must ensure data integrity before monorepo deploy |

---

## 9. Out of Scope (Explicitly Excluded)

- EXBOT trading strategy logic (zen proprietary)
- Router/LPBot smart contract modifications (except WL upgrade additions per WL_SPEC_SOTATEK_EN_v1.0 §5 — those are SOTATEK scope)
- TOKEN contract modifications
- Buy & Burn contract
- POOL core features beyond Steps 7-8
- OPERATOR Queue v2 core implementation (already specified, separate from EXBOT)
- Multi-region deployment (Phase 3)
- Enterprise SLA features
- Marketing / community engagement
- **BnzaSplitter on-chain contract** — removed from v1 scope per WL_SPEC_SOTATEK_EN_v1.0 §1.2. PF về pfCollector single EOA trong v1.
- **MLM reward computation, referral tree management, RewardDistributor payout (Layer B)** — Helix/WL build, not SOTATEK scope per WL_SPEC_SOTATEK_EN_v1.0 §0 intro. BA docs cho `wl-admin/` và `mobile/` vẫn relevant làm interface context, nhưng implementation Layer B+C là phía Helix.

> **[EXPLICIT SCOPE CLARIFICATION — WL_SPEC_SOTATEK_EN_v1.0 §0, §1.2]**
> SOTATEK scope = Layer A infrastructure: contract changes (§5) + off-chain OPERATOR additions
> (Ledger API, Bot API, DB migrations 0024-0027, reconciler crons, HMAC auth, WL bot lifecycle).
> Layer B (WL-ADMIN: reward engine, RewardDistributor, referral tree distribution) + Layer C (Mobile
> display of MLM results) là Helix build. BNZA/SOTATEK cung cấp API cho Helix đọc, không build
> phần tính toán và phân phối MLM.

---

## 10. Open Questions

- [x] OQ-1: Monorepo strategy — **Resolved: Monorepo.** All SOTATEK modules in a single repo. Decision before the May 24 deadline.
- [ ] OQ-2: EXBOT interface specs — when will zen provide D1 schema + Queue topology + API contracts? **Hold: unknown, need to escalate and ask zen.** Potential blocker for EXBOT infra.
- [x] OQ-3: TradingView license — **Resolved: zen/MEGABUCKS funds. SOTATEK can procure if needed. Not blocking.**
- [x] OQ-4: MOBILE WL gate — **Resolved: Mock first (Phase 1 UI verification). Production invite flow (server-side verify) implemented later when the OPERATOR endpoint is ready.**
- [x] OQ-5: ADMIN TOKEN management — **Resolved: Keep mock, low priority. Not needed for WL launch.**
- [x] OQ-6: ADMIN PF distribution — **Resolved: FM-ADM-02 is off-chain config only.** `fee_distributions` table records BNZA's internal PF allocation. The 70%/30% WL split is Helix's distribution concern — not SOTATEK/BNZA-ADMIN scope (BR-ADM-020). Real API live as of 2026-06-12.
- [x] OQ-7: Testing strategy — **Resolved: Per-module strategy.** MOBILE/ADMIN: unit + E2E (critical flows). EXBOT infra: integration tests (queue, HL API). POOL/EX: unit tests (80%+ coverage).
- [ ] OQ-8: Staging environment — **Hold: not yet decided.** Noted in backbone.

---

## 11. Locked Decisions

| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| LD-1 | Each module is treated as a separate project in BA artifacts | Separate repos, different tech stacks, independent deployment, separate teams, own SPECs | 2026-05-20 |
| LD-2 | Sub-modules are sections within each project's FRD/SRS/stories (not separate artifacts) | Keeps artifact count manageable; sub-modules share context within a project | 2026-05-20 |
| LD-3 | System-level backbone covers shared actors, portal matrix, cross-project dependencies | Modules share OPERATOR backend, Router/LPBot on-chain, auth model, design language | 2026-05-20 |
| LD-4 | Module-level artifacts live in `03_modules/{module_slug}/` | BA-kit modular architecture; each project gets own frd.md, srs.md, user-stories.md | 2026-05-20 |
| LD-5 | Engagement mode: Formal | Full artifact set for vendor handoff (SOTATEK 8-week contract) | 2026-05-19 |
| LD-6 | Scope: SOTATEK deliverables only (MOBILE, ADMIN, EX, EXBOT infra, POOL Steps 7-8) | Non-SOTATEK modules (Router, LPBot, Token) are context inputs, not BA targets | 2026-05-19 |
| LD-7 | Monorepo layout: `apps/bnza-{name}` for apps, `contracts/bnza-{name}` for Solidity, `packages/shared-{name}` for shared libs | Verified from source-code; pnpm 10.11 + Turbo 2.5.4 + TS 5.9.3; MOBILE created as new app, EXBOT built within OPERATOR | 2026-05-21 |
| LD-8 | WL go-live strategy: MLM with LPBot first (June 2); EXBOT deferred ~6 weeks post-WL | Business urgency — WL partner discussions already ongoing; EXBOT not ready in time. Post-EXBOT completion, system migrates/replaces LPBot with EXBOT. | 2026-05-27 |
| LD-9 | Project organized into 2 parallel delivery lines: Line 1 (WL+MLM + maintain Pool/EX), Line 2 (ExBot+Backtest) | Clear team ownership; lines converge at ExBot-into-WL integration point | 2026-06-01 |
| LD-10 | WL+MLM system uses Helix source code as reference base (tagged `helix-baseline`); reward engine must be replaced before production | Client handover 2026-05-29; Helix uses profit-direct model, BNZA WL uses pool-based infinite-depth differential — infrastructure reusable, compensation logic must be rebuilt | 2026-06-01 |

### Artifact Structure (locked)

```
docs/sotatek/ba/plans/bnza-sotatek-260519-0000/
├── 01_intake/                           ← system-level context
│   ├── intake.md                      ← project context, stakeholders, scope
│   └── plan.md                        ← delivery plan
├── 02_backbone/                       ← system-level shared
│   ├── backbone.md                   ← actors, portals, permissions, constraints
│   └── feature-map.md                 ← feature map reference
└── 03_modules/
    ├── bnza-ex/                       ← BNZA-EX (hyperliquid trading)
    │   ├── frd.md
    │   ├── srs/spec.md
    │   ├── usecases/
    │   ├── userstories/
    │   └── ascii-screen/
    ├── bnza-pool/                      ← BNZA-POOL (Steps 7-8)
    │   ├── frd.md
    │   ├── srs/spec.md
    │   ├── usecases/
    │   ├── userstories/
    │   └── ascii-screen/
    ├── admin/
    ├── mobile/
    ├── operator/
    └── exbot/
```

---

## 12. Recommended Next Steps

1. **Build backbone** — Requirements backbone from intake (feature map, actor map, module boundaries, priority ordering)
2. **Escalate OQ-2** — Ask zen for EXBOT interface specs timeline
3. **Emit FRD per module** — Functional Requirements Document (5 modules)
4. **Emit User Stories** — Per module, prioritized by WL launch critical path
5. **Emit SRS** — Selective (MOBILE + ADMIN first, then EXBOT infra, then EX + POOL Steps)
6. **Wireframe constraints** — For MOBILE (critical, new UI) and ADMIN WL/PF screens

---

## 13. Document History

> All content from the source documents listed below has been absorbed inline into this intake and the backbone. No external file access is needed to understand the project scope.

| Document | Absorbed into | Key content absorbed |
|---|---|---|
| BNZA Ecosystem Overview v2.0 | intake §1–§9 | Business model, 13 sections, all modules, stakeholders |
| SOTATEK Task List | intake §3 (scope per module) | Categorized tasks A–J, priority ordering |
| SOTATEK Onboarding | backbone §8.4 | Dev approach, deployment conventions |
| WL Platform Core Spec | intake §1B + backbone §8.8 | 3-layer structure, money flow, tenant config, BNZA connection points |
| WL Admin Spec | intake §1A + backbone §8.8 | Distribution pipeline, reward computation, DB schema, API design |
| WL Mobile Spec | intake §1B.7 + backbone §5.0B | Post-allocation display, SIWE auth, bot ops, claim, community |
| WL BNZA Side Spec | backbone §6 (dependency table) | BNZA side: net remittance, ledger API, 3 streams (§7/§7B/§7C) |
| WL Overview | intake §1A.1 (3-layer diagram) | Task boundaries, 3-layer overview. **Note: `docs/wl/OVERVIEW.en.md` is deprecated as of 2026-06-12** — references BnzaSplitter/groupId architecture that is no longer valid. Content superseded by WL_SPECv1.7.x line. |
| Helix Handover README | intake §1A (Helix reuse strategy) | Repo overview, reuse/modify/build-new summary |
| Helix vs WL Diff Report | intake §1A (open questions) | Full comparison, adaptation plan, infinite-depth differential pseudocode |
| EX SPEC | intake §3 Module 3 + bnza-ex/frd.md §0 | TradingView integration gap, agent wallet model |
| EXBOT SPEC v5.2.5 | intake §3 Module 4 + backbone §8.7 | Infrastructure scope, phase progression, confidentiality |
| OPERATOR SPEC | intake §3 Module 2 + backbone §8.1 | Backend architecture, fee structure, RBAC |
| OPERATOR Queue v2 | intake §4.3 + backbone §6 | Scale architecture, Queue patterns |
| OPERATOR DB Schema | intake §3 Module 4 (D1 tables) | D1 tables, relationships |
| OPERATOR Tech Debt | intake §4.4 | 36 items affecting SOTATEK work |
| POOL SPEC | intake §3 Module 5 + bnza-pool/frd.md §0 | Frontend architecture, data layer |
| POOL Step 7 | intake §3 Module 5 + bnza-pool/frd.md §FM-PL-01 | Multi-bot support spec |
| POOL Step 8 | intake §3 Module 5 + bnza-pool/frd.md §FM-PL-02 | plan_specs version management |
| Router v2 SPEC | backbone §8.2 + bnza-pool/frd.md §0 | On-chain fee model, call paths, breaking changes |
| LPBot SPEC | bnza-pool/frd.md §0 | Bot lifecycle, amount calculation, v1.2 ABI changes |
| Token Module | intake §9 (out of scope) | ERC-20 deployed on Base — NOT SOTATEK scope |
| **WL_SPEC_TO_v1.7.5_DELTA_EN.md** (`docs/`) | backbone §5.2 FM-ADM-01/02/10 (applied manually 2026-06-04) | 7 architecture-level changes vs old WL_SPEC.md: wlMaster on-chain mapping, WlNetSent event-based ledger, BnzaSplitter removed, wl_activation_status state machine, rebalance attribution, HMAC+body signing, raw USDC amounts. Formally logged 2026-06-16. |
| **WL_SPECv1.7.5_EN.md** (`docs/`) *(= WL_SPEC_SOTATEK_EN_v1.0 in backbone nomenclature)* | backbone §5.2/§6/§8.1/§8.8 (absorbed 2026-06-04) | Full BNZA-side integration spec: wlMaster architecture, Ledger/Bot/Position APIs, member lifecycle, master wallet management, bot activation state machine, migrations 0024–0028 |
| **WL_SPECv1.7.6_EN.md** (`docs/`) *(= WL_SPEC_SOTATEK_EN_v1.1 — latest canonical)* | backbone §8.8 (version reference updated) + backbone §8.10 §8.10.7 (opFee/PF capture, absorbed 2026-06-16) | v1.7.6 increment over v1.7.5: §3.7.1 — WlNetSent scanner now records `opfee_usd`/`pf_usd` from same tx on-chain transfers (Router→treasury/pfCollector). Columns already in migration 0026. Scanner-side only — no contract change, no new migration. |
| **WL_SPEC_TO_v1.7.6_DELTA_EN.md** (`docs/`) | backbone §8.10 §8.10.7 (absorbed 2026-06-16) | Delta v1.7.5→v1.7.6: single addition §3.7.1 opFee/PF ledger capture. Confirms v1.7.6 supersedes v1.7.5 as canonical spec. |
| **WL_HANDOVER_EN.md** (`docs/`) | backbone §8.10 §8.10.8 (absorbed 2026-06-16) | Spec-to-code mapping (Section A): `src/api/wl-admin.ts`, `src/cron/wl-lifecycle.ts`, `src/cron/wl-reconciler.ts`, etc. Post-launch backlog (Section B): 6 items BNZA-owned. Deliberate decisions & accepted risks (Section C): 12 design decisions + 3 accepted risks — settled, not to re-open. Triple-AI QA (3 rounds, 13 fixes, converged SHIP). |
| **WL_ADMIN_API_GUIDE_EN.md** (`docs/`) | backbone §5.2 FM-ADM-01 API detail + backbone §8.10 §8.10.1–§8.10.6 (absorbed 2026-06-16) | Admin plane auth (`X-Wallet-Address`, NOT HMAC); role gates (viewer/operator/super_admin per endpoint); wl_codes state machine (active↔suspended); wl_members state machine (none→active→leaving→left→active, one-wallet-one-WL E-5, optimistic locking); wl_master_wallets (bookkeeping-only); api_key vs HMAC secret separation; full error code table. |
| **WL_API_CONNECTION_GUIDE_EN.md** (`docs/`) | Not absorbed into backbone (Helix-facing, no SOTATEK admin impact). Logged for traceability. | HMAC-SHA256 signing spec for Helix server-to-server integration: canonical string format, 4 mandatory headers, nonce/timestamp window, endpoint contracts, test vectors, reference client. Audience: QC engineers + Helix FE developers. |
