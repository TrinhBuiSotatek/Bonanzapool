---
type: feature-map
status: in-review
created: 2026-05-20
updated: 2026-06-08
owner: "@hien.duong"
lang: en
links:
  - ../../02_backbone/backbone.md
changelog:
  - "2026-06-08 | manual | scope correction per WL_SPEC_SOTATEK_EN_v1.1.md Appendix B: mark FM-WLA-01→07 and FM-MOB-01→11 OOS (Helix scope); mark PTL-01/PTL-06 and ACT-03/ACT-07 OOS; add §3.6 WL Smart Contracts (FM-WLC-01) and §3.7 BNZA-OPERATOR WL Backend (FM-OPW-01→07); update §4 deps and §5 tiers"
  - "2026-06-07 | manual | QC-C3: add FM-ADM-11 User Management (📋 Spec — admin SPEC.md Feature F, /users, useUsers, Step 8-5.6)"
  - "2026-06-04 | manual | fix FM-ADM-10: redefine as WL Bot Lifecycle Monitor (was incorrectly set to Audit Logs); move FM-ADM-10 from T2 to T1; priority P2→P1"
  - 2026-06-03 | manual | resolve merge conflict; rewrite §3.1 BNZA-MOBILE FM-MOB-01→11 to reflect WL Mobile scope (SIWE, Reward Display, Claim, Bot Ops, LP Bot Status, Community, Branding, Chain Switching, Settings, PWA, i18n); update §4 deps and §5 priority tiers; add FM-ADM-10 Audit Logs
  - 2026-06-02 | /ba-impact | update FM-WLA target artifact column → frd-wl-admin.md (Option B separate file)
  - 2026-06-02 | manual | thêm PTL-06 vào §1 Portal Registry; thêm ACT-07 vào §2 Actor Registry; thêm §3.0 WL-ADMIN feature index (FM-WLA-01→07 với full scope/deps/artifact); rename §3.2 BNZA-ADMIN + thêm boundary note + rewrite FM-ADM-01 description
  - 2026-06-01 | manual | fix external ref to STEP_6_SPEC.md → internal ref-step6-context.md
  - 2026-05-27 | manual | added Markers section (⚡/📋 convention); added Source column to all FM tables
  - "2026-05-26 | manual | sync client-docs: added FM-XB-07→FM-XB-13 (Router Extension, OPERATOR API, Phase A1/A2/A3, Envelope Encryption, Pre-launch Hotfixes); added Step 6 OOS note to §3.5; updated priority tiers and cross-deps"
  - 2026-05-21 | manual | added FM-MOB-07 to FM-MOB-11 (Notification, Position, Margin Alert, Settings, Home Dashboard); promoted FM-MOB-11 to T0; updated cross-deps and priority tiers
  - 2026-05-20 | /ba-start | initial feature-map from backbone
---

# BNZA Ecosystem — Feature Map (System-Level Index)

> This file is the single source of truth for module-level artifacts.
> When writing FRD/SRS/stories for any module, reference the FM-ID from this file.
> DO NOT redefine actors, portals, or navigation at the module level.

---

## Markers

- **📋 Spec** — feature is in the original client spec
- **⚡ Dev-built** — feature was built by dev team, NOT in client spec

---

## 1. Portal Registry (Locked)

| Portal ID | Domain         | Project          | Primary Actor            | Navigation Schema                                                     |
| --------- | -------------- | ---------------- | ------------------------ | --------------------------------------------------------------------- |
| PTL-01    | wl.bnza.io (TBD) | BNZA-MOBILE (WL Mobile) | ACT-03 (WL End User) | Bottom tab: Home / Bot / Earnings / Settings — **[OOS — Helix scope]** |
| PTL-02    | ops.bnza.io    | BNZA-ADMIN       | ACT-04 (Admin/zen)       | Sidebar: Dashboard / WL / PF / IB / Bots / TOKEN / Settings / Reports |
| PTL-03    | ex.bnza.io     | BNZA-EX          | ACT-05 (Trader)          | Top nav: Chart / Trade / Positions / History                          |
| PTL-04    | api.bnza.io    | BNZA-EXBOT Infra | ACT-06 (OPERATOR)        | N/A (backend, no UI)                                                  |
| PTL-05    | pool.bnza.io   | BNZA-POOL        | ACT-01 (End User)        | Top nav: Dashboard / AI Bot / Portfolio / Settings                    |
| PTL-06    | wl-admin.bnza.io (TBD) | WL Admin System | ACT-07 (WL Operator Admin) | Sidebar: Dashboard / Distribution Jobs / Users / Referral Tree / Distributor Contract / Reward Settings / Admins & Auth — **[OOS — Helix scope]** |

---

## 2. Actor Registry (Locked)

| Actor ID | Name | Portals Accessed | Authentication |
|----------|-----|-------------------|----------|
| ACT-01 | End User (LP) | PTL-03, PTL-05 | Wallet connect |
| ACT-02 | WL Partner | PTL-01 (view earnings) | Wallet + WL code |
| ACT-03 | WL End User | PTL-01 **[OOS — Helix scope]** | SIWE → 24h JWT (tenant by subdomain) |
| ACT-04 | Admin (zen) | PTL-02, PTL-04 (config), PTL-05 | Wallet + CF Access (zen@bnza.io) |
| ACT-05 | Trader | PTL-03 | Wallet (direct HL) |
| ACT-06 | OPERATOR (System) | PTL-04 | Internal |
| ACT-07 | WL Operator Admin | PTL-06 **[OOS — Helix scope]** | SSO (CF Access) + 2FA TOTP; roles: Super / Operator / Read-only |

---

## 3. Feature Index

### 3.0 WL Admin System (PTL-06) — Actor: ACT-07

> **⚠️ OOS — Helix (WL operator) scope. Sotatek does NOT build or maintain this system. Kept as reference only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B.**
> **Folder**: `03_modules/admin/wl-admin/` (all files marked `status: out-of-scope`)
> **Role**: Layer B — daily MLM distribution ops. Does NOT manage BNZA product infra (that is PTL-02).

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-WLA-01 | Distribution Pipeline **[OOS — Helix]** | Daily state machine BOT_SYNC → LEDGER_FETCH → PENDING_SNAPSHOT → SNAPSHOT → UPLINE → COMPUTED → ENQUEUED → ONCHAIN → VALIDATED → COMPLETED. BLOCKED recovery per phase (refetch / retry / requeue / refill / abandon). paused_waiting when distributor is paused. | P0 | BNZA Ledger API, BNZA Bot API | `03_modules/admin/wl-admin/frd.md` § Distribution Pipeline | 📋 Spec |
| FM-WLA-02 | Reward Computation Engine **[OOS — Helix]** | Fee reward (net × rank rate 30–62%) + title differential V1–V7 (MLM-pool basis, structurally non-breakable) + same-rank bonus (5% envelope, equal split) + leader token airdrop (V4+, non-USDC, bonus_airdrops). Floor to 6 decimals. Cap double-check before ONCHAIN. | P0 | FM-WLA-01, tenant config (rank/title/referral tables) | `03_modules/admin/wl-admin/frd.md` § Reward Computation | 📋 Spec |
| FM-WLA-03 | RewardDistributor Integration **[OOS — Helix]** | Push (auto when claimable ≥ minPayout, WL bears gas) + Claim (user-initiated, user bears gas). clientNonce idempotency. Emergency Pause (PAUSER hot wallet, immediate) / Unpause via multisig proposal. Per-chain (Base 8453 + OP 10). | P0 | RewardDistributor contract (Base + OP), CF Secrets Store (distributor key) | `03_modules/admin/wl-admin/frd.md` § RewardDistributor | 📋 Spec |
| FM-WLA-04 | BNZA API Integration **[OOS — Helix]** | Stream 1: Ledger API HMAC-SHA256 pull (`/api/wl/ledger`, net per user per chain). Stream 2: Position API (`/api/wl/portfolio`, AUM for rank/Cap). Stream 3: Bot Operations API (`/internal/bot/sync`, sync bot_positions_mirror for BOT_SYNC phase). | P0 | BNZA OPERATOR API (api.bnza.io) | `03_modules/admin/wl-admin/frd.md` § BNZA API | 📋 Spec |
| FM-WLA-05 | Admin Console — 7 Pages **[OOS — Helix]** | Dashboard (KPI + health + emergency stop) / Distribution Jobs (state machine progress + BLOCKED recovery + batch list) / Users (cumulative + Cap + lineage) / Referral Tree (hierarchy view + parent change + omission resolution) / Distributor Contract (balance + refill + multisig proposals) / Reward Settings (rank/title/referral/Cap tabs) / Admins & Auth (roles + 2FA + session policy). All writes require reason note + Slack audit mirror. | P0 | FM-WLA-01→04 | `03_modules/admin/wl-admin/ascii-screen/wl-*.md` | 📋 Spec |
| FM-WLA-06 | Multi-tenant Config **[OOS — Helix]** | Tenant config per WL operator: branding (name/logo/theme), chains [8453,10], wallet addresses (pool/distributor/treasury per chain), rank_table, title_table, referral_levels, reward_settings (Cap/minPayout/same_rank/leader). No WL-specific values hardcoded. | P1 | CF D1 `tenants` table | `03_modules/admin/wl-admin/frd.md` § Multi-tenant | 📋 Spec |
| FM-WLA-07 | Daily Reconciliation **[OOS — Helix]** | 6-point cron (UTC 06:00): (1) ledger↔compute, (1b) WL treasury sanity, (2) compute↔accrual, (3) payment↔on-chain, (4) cumulative invariant, (5) pool validation, (6) unexpected addRewards detection. Strong alert on any delta. | P1 | FM-WLA-01, CF D1 all distribution tables | `03_modules/admin/wl-admin/frd.md` § Reconciliation | 📋 Spec |

### 3.1 BNZA-MOBILE (PTL-01)

> **⚠️ OOS — Helix (WL operator) scope. Sotatek does NOT build or maintain this system. Kept as reference only. Reference: WL_SPEC_SOTATEK_EN_v1.1.md Appendix B.**
> **Folder**: `03_modules/mobile/` (all files marked `status: out-of-scope`)

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-MOB-01 | SIWE Auth + WL Gate **[OOS — Helix]** | Wallet connect via Reown AppKit, SIWE sign-in (nonce → signature → 24h JWT), tenant resolution by subdomain, WL gate blocking unauthenticated routes | P0 | Admin System SIWE API | `03_modules/mobile/frd.md` § FM-MOB-01 | 📋 Spec |
| FM-MOB-02 | Reward Display **[OOS — Helix]** | Cumulative reward card (fee + referral breakdown), rank & title, cap status (tenant-optional), revenue trend chart (1W/1M/3M/All), receipt history with status tags, leader perk (V4+) | P0 | Admin System `/api/mobile/summary`, `/api/mobile/history` | `03_modules/mobile/frd.md` § FM-MOB-02 | 📋 Spec |
| FM-MOB-03 | Claim USDC **[OOS — Helix]** | Claimable balance display, Receive All confirmation, RewardDistributor.claim() via user wallet, post-claim sync, paused state when contract is_paused | P0 | RewardDistributor contract (Base + OP), Admin System `/api/mobile/sync-after-claim` | `03_modules/mobile/frd.md` § FM-MOB-03 | 📋 Spec |
| FM-MOB-04 | Bot Operations **[OOS — Helix]** | Bot startup (3 sequential wallet TXs: USDC approve → setApprovalForAll → zapMint → OPERATOR register), bot stop (confirm → stop TX → UI update) | P0 | OPERATOR API `/api/bot/register`, LpBot contract | `03_modules/mobile/frd.md` § FM-MOB-04 | 📋 Spec |
| FM-MOB-05 | LP Bot Status **[OOS — Helix]** | Active positions list (data from Admin API only — never raw LP reads), chain filter, total AUM, no raw uncollected fees shown | P0 | Admin System `/api/mobile/positions` | `03_modules/mobile/frd.md` § FM-MOB-05 | 📋 Spec |
| FM-MOB-06 | Community / Referral Tree **[OOS — Helix]** | Team TVL stats, direct + total downline counts, downline list with referral rate, L1/L2/L3 rates from tenant config | P1 | Admin System `/api/mobile/community` | `03_modules/mobile/frd.md` § FM-MOB-06 | 📋 Spec |
| FM-MOB-07 | Multi-tenant Branding **[OOS — Helix]** | Tenant config load on app start (name, logo, theme_color, chains, rank_table, title_table, referral_levels, cap_enabled, reown_project_id, supported_languages). Dynamic Reown project ID. | P1 | Admin System `/api/mobile/tenant-config` | `03_modules/mobile/frd.md` § FM-MOB-07 | 📋 Spec |
| FM-MOB-08 | Chain Switching **[OOS — Helix]** | Header toggle Base (8453) / OP (10). Arbitrum excluded. Data re-filtered on switch. Wallet chain switch via Reown AppKit. Persists in localStorage. | P1 | Reown AppKit | `03_modules/mobile/frd.md` § FM-MOB-08 | 📋 Spec |
| FM-MOB-09 | Settings **[OOS — Helix]** | Language selector (from tenant supported_languages, min ja/en), network display, wallet disconnect (JWT clear → connect screen). All persist in localStorage. | P1 | — (local state) | `03_modules/mobile/frd.md` § FM-MOB-09 | 📋 Spec |
| FM-MOB-10 | PWA **[OOS — Helix]** | Web app manifest, service worker (cache-first static / network-first API), offline fallback, 100dvh fix, safe-area-inset for notch devices | P1 | — | `03_modules/mobile/frd.md` § FM-MOB-10 | 📋 Spec |
| FM-MOB-11 | i18n **[OOS — Helix]** | Min ja + en. Additional languages per tenant supported_languages. Browser locale auto-detected on first visit. Intl.NumberFormat for amounts. Locale persists in localStorage. | P2 | — | `03_modules/mobile/frd.md` § FM-MOB-11 | 📋 Spec |

### 3.2 BNZA-ADMIN (PTL-02) — Actor: ACT-04

> **Folder**: `03_modules/admin/bnza-admin/` (dedicated sub-folder — frd.md, ascii-screen/, usecases/, userstories/, srs/)
> **Role**: Manage BNZA product infra + WL partner account onboarding. Does NOT run daily MLM distribution (that is PTL-06).

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-ADM-01 | WL Partner Onboarding | Create/edit/deactivate WL partner account records: name, logo (CF R2 upload), referral_code (auto 8-char alphanumeric or manual, unique), fixed_deposit_usd (1k/5k/10k), main_wallet, languages, status. View partner earnings summary + payout history. NOT the daily MLM ops (those are PTL-06 FM-WLA). | P0 | OPERATOR API `/api/wl-partners` | `03_modules/admin/bnza-admin/frd.md` § WL Partner Onboarding | 📋 Spec |
| FM-ADM-02 | PF Distribution | Daily PF distribution dashboard (70/30), remittance trigger, history | P0 | OPERATOR API `/api/admin/pf/*`, daily-collector cron | `03_modules/admin/bnza-admin/frd.md` § PF Distribution | 📋 Spec |
| FM-ADM-03 | IB Management | Replace mockIBs with real data, IB CRUD, commission tracking | P1 | OPERATOR API `/api/admin/ib/*` | `03_modules/admin/bnza-admin/frd.md` § IB Management | ⚡ Dev-built |
| FM-ADM-04 | Bot Type Config | Deposit tiers, strategy parameters, limits, cooldown range 10-180 min | P1 | OPERATOR API `/api/admin/bot-types/*` | `03_modules/admin/bnza-admin/frd.md` § Bot Type Config | ⚡ Dev-built |
| FM-ADM-05 | Dashboard | Real metrics: TVL, active bots, revenue, user count | P2 | OPERATOR API `/api/admin/stats` | `03_modules/admin/bnza-admin/frd.md` § Dashboard | 📋 Spec |
| FM-ADM-06 | Reports | Real-data reports: fee collection, bot performance, user activity | P2 | OPERATOR API `/api/admin/reports/*` | `03_modules/admin/bnza-admin/frd.md` § Reports | 📋 Spec |
| FM-ADM-07 | TOKEN Management | Burn/supply/vesting/treasury/builder-fee (keep mock) | P3 | OPERATOR API (not yet available) | `03_modules/admin/bnza-admin/frd.md` § TOKEN Mgmt | ⚡ Dev-built |
| FM-ADM-08 | System Settings | Configuration management: system_config, allowed/blocked addresses | P2 | OPERATOR API `/api/admin/config/*` | `03_modules/admin/bnza-admin/frd.md` § System Settings | ⚡ Dev-built |
| FM-ADM-09 | Relayer Monitor | Relayer status: balance, nonce, last TX, health | P2 | OPERATOR API `/api/admin/relayers` | `03_modules/admin/bnza-admin/frd.md` § Relayer Monitor | ⚡ Dev-built |
| FM-ADM-10 | WL Bot Lifecycle Monitor | Monitor `wl_activation_status` backlog: pending_set SLA, failed_set queue, needs_repair alerts, rotation in progress, wl_unattributed_events SLA breach. Admin actions: retry-set, force-normalize (two-phase). Triggers `setBotWlMaster`/`unsetBotWlMaster` via OPERATOR API. | P1 | OPERATOR API `/api/admin/wl-bot-monitor`, `/api/bot-configs/:id/wl-retry-set`, `/api/bot-configs/:id/wl-force-normalize` | `03_modules/admin/bnza-admin/frd.md` § WL Bot Lifecycle Monitor | 📋 Spec |
| FM-ADM-11 | User Management | View and manage all registered users: wallet address, role (viewer/admin/super_admin), registration date, linked bots count. Read-only list with RBAC-based action controls. | P1 | OPERATOR API `/api/users` (`useUsers`, Step 8-5.6) | `03_modules/admin/bnza-admin/frd.md` § User Management | 📋 Spec |

### 3.3 BNZA-EX (PTL-03)

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-EX-01 | TradingView Integration | Implement `chartingLibraryAdapter.js`, configure datafeed, theme matching | P2 | TradingView license (zen-funded) | `03_modules/bnza-ex/frd.md` § TradingView Integration | 📋 Spec |
| FM-EX-02 | Chart Data Feed | Hyperliquid WebSocket → TradingView UDF format, symbol resolution, history | P2 | Hyperliquid API (direct) | `03_modules/bnza-ex/frd.md` § Chart Data Feed | 📋 Spec |
| FM-EX-03 | Order Placement | Integrate order panel with chart, click-to-trade, TP/SL lines | P2 | Hyperliquid API (direct) | `03_modules/bnza-ex/frd.md` § Order Placement | 📋 Spec |
| FM-EX-04 | i18n | UI supports 5 languages: en/ja/zh/ko/vi. Language selector in header. Locale persists in localStorage. | P2 | — | `03_modules/bnza-ex/frd.md` § i18n | 📋 Spec |

### 3.4 BNZA-EXBOT Infrastructure (PTL-04)

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-XB-01 | D1 Schema | 9 EXBOT tables in D1, migration, indexes, FK constraints | P0 | zen interface specs (OQ-2) | `03_modules/exbot-infra/frd.md` § D1 Schema | ⚡ Dev-built |
| FM-XB-02 | Queue Topology | 6 queues, DLQ, retry policy, batch size, concurrency limits | P0 | OPERATOR Queue v2 architecture | `03_modules/exbot-infra/frd.md` § Queue Topology | ⚡ Dev-built |
| FM-XB-03 | Durable Objects | HLRateLimitDO, UserLockDO, MarketDataDO — lease, TTL, alarm config | P0 | OPERATOR DO patterns | `03_modules/exbot-infra/frd.md` § Durable Objects | ⚡ Dev-built |
| FM-XB-04 | Cron Jobs | deep-audit `*/360`, intervals TBD, error handling, alerting | P1 | zen interface specs | `03_modules/exbot-infra/frd.md` § Cron Jobs | ⚡ Dev-built |
| FM-XB-05 | HL Adapter | Rate limit (1200 req/min), cloid generation, error parser, reconcile glue | P1 | Hyperliquid API testnet | `03_modules/exbot-infra/frd.md` § HL Adapter | ⚡ Dev-built |
| FM-XB-06 | API Endpoints | start, stop, pause, status, agent-key-approval — request/response contracts | P1 | zen interface specs | `03_modules/exbot-infra/frd.md` § API Endpoints | ⚡ Dev-built |
| FM-XB-07 | Router Extension (Solidity) | LP NFT custody by Router, rebalance/close/collect Operator-only, emergency multi-sig | P1 | zen interface specs, Solidity engineer | `03_modules/exbot-infra/frd.md` § Router Extension | ⚡ Dev-built |
| FM-XB-08 | OPERATOR API — EXBOT Endpoints | 7 endpoints: start/stop/pause/resume/status/agent-key-approval/margin-deposit-confirmed | P1 | FM-XB-01, FM-XB-02 | `03_modules/exbot-infra/frd.md` § OPERATOR API Additions | ⚡ Dev-built |
| FM-XB-09 | Phase A1 — Dry Run | Single-user dry-run, no live HL mutation, SOTATEK infra + zen strategy | P0 | FM-XB-01→FM-XB-06 | `03_modules/exbot-infra/frd.md` § Phase Progression | ⚡ Dev-built |
| FM-XB-10 | Phase A2 — Live $1k Test | Live test with zen's own funds, SOTATEK monitors infra | P1 | FM-XB-09 | `03_modules/exbot-infra/frd.md` § Phase Progression | ⚡ Dev-built |
| FM-XB-11 | Phase A3 — Closed Beta | 5-10 WL users via MOBILE, 4 weeks | P1 | FM-XB-10 | `03_modules/exbot-infra/frd.md` § Phase Progression | ⚡ Dev-built |
| FM-XB-12 | Envelope Encryption | HL agent keys: master key in CF Secrets Store, per-bot key encrypted in D1 | P0 | zen interface specs | `03_modules/exbot-infra/frd.md` § HL Adapter | ⚡ Dev-built |
| FM-XB-13 | Pre-launch Hotfixes | WETH calc bug, executeRebalanceAction missing recordFeeCollection, leaseExpireCron, RelayerLockDO persistence, system_config seed | P0 | — | `03_modules/exbot-infra/frd.md` § Pre-launch Hotfixes | ⚡ Dev-built |

### 3.5 BNZA-POOL Steps 7-8 (PTL-05)

> **Note — Pool Step 6 (OOS):** Router v2.2.2-fix-2 + LPBot v1.2 migration (address updates, ABI changes) was completed by zen. NOT SOTATEK scope. See `03_modules/bnza-pool/ref-step6-context.md` for reference.

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-PL-01 | Step 7 Multi-Bot | BotCard grid, Active Bots section, chain-switching, max 10/chain, label format | P1 | OPERATOR API `/api/bot-positions` | `03_modules/pool-steps/frd.md` § Step 7 Multi-Bot | 📋 Spec |
| FM-PL-02 | Step 8 plan_specs | Version management across POOL+OPERATOR+OPS, immutability, snapshot, outdated warning | P1 | OPERATOR migration 0008, simultaneous deploy | `03_modules/pool-steps/frd.md` § Step 8 plan_specs | 📋 Spec |
| FM-PL-03 | Fiat On-Ramp (Banxa) | `/buy` route embeds Banxa widget with wallet address pre-filled; mock data (MOCK_RATES, MOCK_HISTORY) — no live Banxa API | P3 | — | `03_modules/bnza-pool/usecases/uc-buy.md` | ⚡ Dev-built |

### 3.6 WL Smart Contracts — Sotatek Scope

> **Contracts:** `BnzaRouterUpgradeable.sol` + `BnzaLpBot.sol`
> **Phase:** Phase 2 (contract changes A–K) + Phase 3 (ABI integration in OPERATOR)
> **FRD Artifact:** `03_modules/_shared/frd-wl-contracts.md`

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-WLC-01 | WL Contract Upgrades (A–K) | 11 contract changes: wlMaster mapping (A), setBotWlMaster/unsetBotWlMaster operator-only setters (B), net/principal split in internal payout functions (C), wlMaster migration on rebalance (D), WlNetSent event (E), WL bot on-chain constraints (F), self-call protection for self functions (G), require mismatch check (H), 5-arg constructor with immutable USDC (I), wlRecipient pass-through in LpBot (J), custom errors (K) | P0 | Phase 1 BNZA-OPERATOR complete before Phase 2 deploy | `03_modules/_shared/frd-wl-contracts.md` | 📋 Spec |

### 3.7 BNZA-OPERATOR WL Backend — Sotatek Scope

> **Portal:** PTL-04 (BNZA-OPERATOR — api.bnza.io, Cloudflare Workers)
> **FRD Artifact:** `03_modules/operator/frd-wl.md`

| FM-ID | Name | Scope Description | Priority | Dependencies | Target Artifact | Source |
|-------|-----|----------------|----------|-----------|---------------|--------|
| FM-OPW-01 | DB Migrations 0024–0027 | bot_configs WL columns (0024); wl_members/wl_codes/wl_master_wallets tables (0025); wl_bot_payouts/wl_token_attribution_history (0026); wl_compensation_queue (0027) | P0 | — | `03_modules/operator/frd-wl.md` §1 | 📋 Spec |
| FM-OPW-02 | Ledger API | GET /wl/ledger/transactions, /summary, /bot-aum. HMAC-SHA256 auth. Min disclosure: no position_id/pool/token symbols. Range cap 90 days. | P0 | FM-OPW-01 | `03_modules/operator/frd-wl.md` §2 | 📋 Spec |
| FM-OPW-03 | Bot API | POST /wl/bot/register, /leave, /suspend, /resume, /force-normalize, /rotate-master, GET /status. Two-phase commit for all unset transitions. | P0 | FM-OPW-01 | `03_modules/operator/frd-wl.md` §3 | 📋 Spec |
| FM-OPW-04 | Post-Record Helix Webhook | After wl_bot_payouts reaches attributed, POST to tenant wl_codes.post_record_url with HMAC signature. | P0 | FM-OPW-01, FM-OPW-05 | `03_modules/operator/frd-wl.md` §4 | 📋 Spec |
| FM-OPW-05 | WlNetSent Scanner (Phase 1.5) | Scans WlNetSent events from chain every 5 min. Holds-first decision, attribution lookup, unattributed retry (max 288), reorg detection. Zero-loss guarantee. | P0 | FM-OPW-01, FM-WLC-01 (Phase 2 contracts deployed) | `03_modules/operator/frd-wl.md` §5 | 📋 Spec |
| FM-OPW-06 | Reconcilers (Phase 1.5) | setBotWlMaster reconciler (retry failed on-chain calls, backoff 5/30/300/1800s, max 20 attempts). wlMaster invariant reconciler (chain↔DB divergence detection). | P1 | FM-OPW-01, FM-OPW-03 | `03_modules/operator/frd-wl.md` §6 | 📋 Spec |
| FM-OPW-07 | fee_collections Exclusion | Update 7 OPERATOR files: add WL bot exclusion filter to fee_collections queries to prevent double-counting. Parallel to Phase 1. | P0 | FM-OPW-01 | `03_modules/operator/frd-wl.md` §7 | 📋 Spec |

---

## 4. Cross-Feature Dependencies (Quick Reference)

| FM-ID | Blocked by | Blocks |
|-------|----------|----------|
| FM-ADM-01 | OPERATOR WL admin endpoints | FM-ADM-02 (WL must exist before PF distribution) |
| FM-ADM-02 | daily-collector cron, OQ-6 (WL remittance flow) | — |
| FM-XB-01 | OQ-2 (zen interface specs) | FM-XB-02, FM-XB-03, FM-XB-04, FM-XB-05, FM-XB-06, FM-XB-07, FM-XB-08 |
| FM-XB-02 | FM-XB-01 (schema must exist before queue writes) | FM-XB-04, FM-XB-05, FM-XB-09 |
| FM-XB-07 | FM-XB-01, zen Solidity specs | FM-XB-08 (Router extension needed for EXBOT API) |
| FM-XB-08 | FM-XB-01, FM-XB-02, FM-XB-07 | — |
| FM-XB-09 | FM-XB-01, FM-XB-02, FM-XB-03, FM-XB-12 | FM-XB-10 |
| FM-XB-10 | FM-XB-09 | FM-XB-11 |
| FM-XB-11 | FM-XB-10 | — |
| FM-XB-12 | zen CF Secrets Store design | FM-XB-09 (encryption must be in place before dry-run) |
| FM-XB-13 | — (hotfixes, no upstream dependency) | FM-XB-09 (must fix before Phase A1) |
| FM-EX-01 | TradingView license | FM-EX-02, FM-EX-03 |
| FM-PL-01 | OPERATOR bot-positions API | — |
| FM-PL-02 | OPERATOR migration 0008, FM-PL-01 (Step 7 before Step 8) | — |
| FM-PL-03 | — (dev-built, no spec dependency) | — |
| FM-OPW-01 | — | FM-OPW-02, FM-OPW-03, FM-OPW-04, FM-OPW-05, FM-OPW-06, FM-OPW-07 |
| FM-OPW-02 | FM-OPW-01 | — |
| FM-OPW-03 | FM-OPW-01 | FM-OPW-04 (bot state must exist before post-record) |
| FM-OPW-04 | FM-OPW-01, FM-OPW-05 (attribution must happen before webhook) | — |
| FM-OPW-05 | FM-OPW-01, FM-WLC-01 Phase 2 deployed | FM-OPW-04 |
| FM-OPW-06 | FM-OPW-01, FM-OPW-03 | — |
| FM-OPW-07 | FM-OPW-01 | — |
| FM-WLC-01 | Phase 1 BNZA-OPERATOR (FM-OPW-01→07) complete | FM-OPW-05 (scanner needs WlNetSent ABI) |

---

## 5. Priority Tiers (Locked)

| Tier | FM-IDs |
|------|--------|
| T0 — WL Launch | FM-OPW-01, FM-OPW-02, FM-OPW-03, FM-OPW-04, FM-OPW-07, FM-WLC-01, FM-ADM-01, FM-ADM-02, FM-XB-01, FM-XB-02, FM-XB-03, FM-XB-09, FM-XB-12, FM-XB-13 |
| T1 — Core Dev | FM-OPW-05, FM-OPW-06, FM-ADM-03, FM-ADM-04, FM-ADM-10, FM-ADM-11, FM-PL-01, FM-XB-04, FM-XB-05, FM-XB-06, FM-XB-07, FM-XB-08, FM-XB-10 |
| T2 — Enhancement | FM-PL-02, FM-ADM-05, FM-ADM-06, FM-ADM-08, FM-ADM-09, FM-EX-01, FM-EX-02, FM-EX-03, FM-EX-04, FM-XB-11 |
| T3 — Low Priority | FM-ADM-07, FM-PL-03 |

---

## 6. Traceability Template

When a module FRD/SRS/stories references the feature map:

```markdown
**Trace:** FM-MOB-01 (Feature Map § 3.1)
**Portal:** PTL-01
**Primary Actor:** ACT-03
**Priority:** P0 / T0
```

Every FR-*, UC-*, US-* in module artifacts MUST trace back to at least 1 FM-ID in this file.
