---
type: common-rules
status: draft
created: 2026-06-02
updated: 2026-06-09
owner: "@hien.duong"
changelog:
  - "2026-06-09 | /ba-do F1 | removed PL-SCREEN section (lines 167–226); CR-BEH/CR-DIS/CR-VAL/BR-0x codes are screen-local — canonical source is each screen file §5"
  - "2026-06-02 | /ba-qc-export | initial compile: extracted BR-MOB, BR-EX, BR-PL, BR-ADM, BR-WLA from module srs/spec.md and ascii-screen files"
---

# Common Rules — Cross-Module Business Rules

> Canonical registry for all Business Rules across the bonanzapool project.
> Each module's rules are prefixed by module code. Rules are sourced from each module's `srs/spec.md`.
> **Do not define BRs inline in screen files** — reference by ID from this registry.

---

## MOB — Mobile App

| ID | Rule | Scope |
|----|------|-------|
| BR-MOB-001 | All app routes blocked until valid JWT exists in localStorage | All screens |
| BR-MOB-002 | JWT TTL is 24h. On expiry, re-prompt SIWE sign (silent — no full disconnect, no error banner). | Auth |
| BR-MOB-003 | Tenant is resolved server-side from subdomain + SIWE signature domain. Frontend cannot override tenant. | Auth, all API calls |
| BR-MOB-004 | Mobile MUST NOT read LP NFT data directly. All displayed amounts come from admin system API. | Reward display, positions |
| BR-MOB-005 | Bot startup forced params: `convertToUsdc=true`, `autoCompound=false`. Required to send USDC to `wlMaster[tokenId]` and simplify the rebalance hook. | Bot operations |
| BR-MOB-006 | Bot operations only on Base (8453) or OP (10). Prompt chain switch if wallet is on another chain. | Bot operations |
| BR-MOB-007 | Push-paid rewards do not require Claim. Claim targets fractions below `minPayout` threshold only. | Claim |
| BR-MOB-008 | During RewardDistributor Pause, Claim is disabled. Show "Receiving is currently paused". | Claim |
| BR-MOB-009 | Selected chain persists in localStorage key `bnza_mobile_chain`. Default: Base (8453). | Chain switching |
| BR-MOB-010 | Wallet disconnect clears JWT and redirects to Connect screen. | Auth, Settings |

---

## EX — BNZA Exchange (bnza-ex)

| ID | Rule | Scope |
|----|------|-------|
| BR-EX-01 | Arbitrum (chain ID 42161) is the only supported network. No chain switching is needed for Hyperliquid trading. | All screens |
| BR-EX-02 | The agent wallet is a private key stored in browser storage, validated to match the user's connected wallet address. | Agent setup |
| BR-EX-03 | Builder fee approval is required before the user can place their first trade. | Agent setup |
| BR-EX-04 | All Hyperliquid actions (place / cancel / modify order) are signed by the agent key — no MetaMask popup per trade. | Order flow |
| BR-EX-05 | The full list of available perpetual symbols is loaded when the app starts. | Symbol selector |
| BR-EX-06 | The app connects directly to Hyperliquid — no OPERATOR API involved. | All API calls |
| BR-EX-07 | **Known tech debt (P2 fix):** The wallet connect metadata URL currently points to "app.bnza.io" instead of the correct "ex.bnza.io". | Wallet connect |
| BR-EX-08 | The app is written in plain JavaScript (no TypeScript) — different from ADMIN and POOL. | Dev constraint |
| BR-EX-09 | The "Bots" tab is a placeholder — EXBOT integration is deferred pending a decision from zen (OQ-EX-01). | Bots tab |

---

## PL — BNZA Pool (bnza-pool)

| ID | Rule | Scope |
|----|------|-------|
| BR-PL-01 | Supported chains: OP (10) + Base (8453) only. | All screens |
| BR-PL-02 | Pool address from `Factory.getPool` on-chain, not DB. | Bot creation |
| BR-PL-03 | Token prices from Hyperliquid (not CoinGecko). | Price display |
| BR-PL-04 | Stablecoins (USDC/USDT/DAI/BUSD) fixed at $1.0. | Price display |
| BR-PL-05 | Price cache: 15s TTL. | Price display |
| BR-PL-06 | Slippage: `DEFAULT_SLIPPAGE_BPS = 100` (1%). | Bot start/stop |
| BR-PL-07 | Stop TX deadline: now + 1200s (20 min). | Bot stop |
| BR-PL-08 | PF ratio: `convert_to_usdc=1` → 0.2970075, else 0.2985. | Bot stop |
| BR-PL-09 | OPERATOR API failure after on-chain success = still treated as success. | Bot stop |
| BR-PL-10 | localStorage fallback for bot configs/rules (migration period only). | Bot config |
| BR-PL-11 | Max 10 bots per chain (UI enforcement only — API doesn't enforce). | Bot creation |
| BR-PL-12 | i18n: 5 languages (en/ja/ko/zh/vi). | All screens |
| BR-PL-13 | WL launch: whitelist check gates access on landing page. | Landing / auth |
| BR-PL-14 | `already_stopped` error from API treated as success. | Bot stop |
| BR-PL-15 | Bot start: Operator path is ERC20-only (`msg.value == 0`); ETH input must be wrapped to WETH first. | Bot start |
| BR-PL-16 | `atomic-start` retried 3 times with exponential backoff (2s/4s/6s); full failure = fatal modal. | Bot start |
| BR-PL-17 | `plan_specs` cached in localStorage with 5-min TTL; fallback to hardcoded defaults. | Plan display |
| BR-PL-18 | `convert_to_usdc` is immutable after bot start (stored in `bot_configs`, used in stop PF calc). | Bot config |
| BR-PL-19 | `auto_compound` fixed 0 in v1.2 pre-launch (v1.3 feature). | Bot start |
| BR-PL-20 | Notifications polled every 30s. | Notifications |
| BR-PL-21 | Min TVL: $1,000 USD (configurable via `NEXT_PUBLIC_MIN_TVL_USD`). | Bot creation |
| BR-PL-22 | Gas reserve check: 0.001 ETH estimated before bot start. | Bot start |
| BR-PL-23 | Evaluation = Σ (liquidityUSD + unclaimedFeesUSD) for active positions only. | Bot card display |
| BR-PL-24 | P&L = Evaluation − invested_amount (`invested_amount` is immutable after bot start). | Bot card display |
| BR-PL-25 | Uptime = floor((now − started_at) / 86,400,000 ms); does not reset on rebalance. | Bot card display |

---

## ADM — BNZA Admin (bnza-admin)

| ID | Rule | Scope / Source |
|----|------|----------------|
| BR-ADM-001 | `referral_code` must be unique across all WL partners. | FRD §1.4 |
| BR-ADM-002 | Only `super_admin` can create, update, or disable WL partners. | FRD §1.4 |
| BR-ADM-003 | `fixed_deposit_usd` must be one of: 1000, 5000, 10000. | FRD §1.4 |
| BR-ADM-004 | Disabling a WL partner does not affect existing active bots. | FRD §1.4 |
| BR-ADM-005 | Logo upload must be stored in CF R2; URL stored in `logo_url`. | FRD §1.4 |
| BR-ADM-006 | `referral_code` auto-generation: 8-char alphanumeric, uppercase. | FRD §1.4 |
| BR-ADM-007 | `wl_code` must be unique; once set, immutable without WL-ADMIN team coordination. | FRD §1.4 |
| BR-ADM-008 | Boundary: FM-ADM-01 manages WL partner records only; daily MLM ops are PTL-06 scope. | FRD §1.4 |
| BR-ADM-009 | One wallet can only be `active` or `leaving` in one WL at a time. | FRD §1.8 |
| BR-ADM-010 | While a member is `leaving`, new bot starts for that wallet are rejected. | FRD §1.8 |
| BR-ADM-011 | Member leave is two-phase: `initiate-leave` → `leaving`; `confirm-leave` after on-chain unset confirmed. | FRD §1.8 |
| BR-ADM-012 | `membership_epoch` increments on every rejoin; included in Ledger API response for Helix. | FRD §1.8 |
| BR-ADM-013 | One master wallet per WL per chain. Rotation is two-phase; bot delivery suspended during rotation. | FRD §1.8 |
| BR-ADM-014 | Suspend (`wl_codes.status='suspended'`) pauses all net delivery; OPERATOR cron moves bots to `pending_unset`. | FRD §1.8 |
| BR-ADM-015 | Exactly one `fee_distributions` row must have `is_remainder=true`. | FRD §2.4 |
| BR-ADM-016 | Sum of all non-remainder `share_ratio` values must be < 1.0. | FRD §2.4 |
| BR-ADM-017 | Maximum 10 `fee_distributions` entries. | FRD §2.4 |
| BR-ADM-018 | `fee_distributions` is off-chain config only — no on-chain tx triggered. PF flows to `pfCollector` single EOA. | FRD §2.4 |
| BR-ADM-019 | Audit log entry created on every create/update/delete to `fee_distributions`. | FRD §2.4 |
| BR-ADM-020 | `fee_distributions` records BNZA's internal off-chain tracking of PF allocation (separate from WL split). | FRD §2.4 |
| BR-ADM-021 | EXBOT config fields (`hedge_ratio`, `leverage`, `stop_safety_factor`) are interface-only — zen provides values. | FRD §3.4 |
| BR-ADM-022 | `cooldown_range_min` must be between 10 and 180 minutes. | FRD §3.4 |
| BR-ADM-023 | Per-WL bot type selection: current default is EXBOT for all WL partners. | FRD §3.4 |
| BR-ADM-024 | Replace `mockIBs` hardcoded data with real D1 data. | FRD §4.3 |
| BR-ADM-025 | IB commission tracking is display-only in Phase C.2. | FRD §4.3 |
| BR-ADM-026 | Dashboard stats must use real D1 data — no mock/seeded data. | FRD §5.3 |
| BR-ADM-027 | Expensive aggregations cached in KV with TTL ≤ 5 minutes. | FRD §5.3 |
| BR-ADM-028 | `global_bot_enabled=false` halts all bot processing immediately. | FRD §6.3 |
| BR-ADM-029 | `safe_mode=true` requires zen approval to disable; UI must show acknowledgment dialog. | FRD §6.3 |
| BR-ADM-030 | System Settings UI must show current value + last modified timestamp per key. | FRD §6.3 |
| BR-ADM-031 | Force-normalize is two-phase — OPERATOR must fire `unsetBotWlMaster` on-chain and confirm `wlMaster[tokenId]==0` before setting `wl_code=NULL`. | FRD §10.4 |
| BR-ADM-032 | Retry set re-checks `wl_members.status='active'` AND `wl_codes.status='active'` before firing `setBotWlMaster`. | FRD §10.4 |
| BR-ADM-033 | `failed_set` bots stuck for 48h are auto-force-normalized by OPERATOR cron. | FRD §10.4 |
| BR-ADM-034 | `needs_repair` bots are excluded from daily/rebalance delivery. Only admin recovery action returns them to `active`. | FRD §10.4 |

---

## WLA — WL Admin (wl-admin)

| ID | Rule | Scope |
|----|------|-------|
| BR-WLA-001 | One job per day per tenant. Cannot create second job if today's is not COMPLETED or ABANDONED. | FM-WLA-01 |
| BR-WLA-002 | Manual GO at PENDING_SNAPSHOT requires reason note ≥ 10 chars. Auto-timeout if no omissions (OQ-WLA-06). | FM-WLA-01 |
| BR-WLA-003 | ABANDONED is irreversible. Super only + reason note required. | FM-WLA-01 |
| BR-WLA-004 | All state transitions logged to `audit_logs` with actor, timestamp, reason. | FM-WLA-01 |
| BR-WLA-005 | BLOCKED recovery must be attempted before ABANDONED is allowed. | FM-WLA-01 |
| BR-WLA-006 | `paused_waiting` set automatically when RewardDistributor paused during ONCHAIN. Resumes after unpause. | FM-WLA-01 |
| BR-WLA-007 | All MLM bonuses paid from MLM pool. Not added on top of net. | FM-WLA-02 |
| BR-WLA-008 | Title differential is non-breakable: lineage total ≤ highest title rate in chain. | FM-WLA-02 |
| BR-WLA-009 | Same-rank bonus envelope = MLM pool × 5%, split equally among users sharing same rank that day. | FM-WLA-02 |
| BR-WLA-010 | Leader bonus (V4+) is non-USDC token airdrop tracked in `bonus_airdrops` — separate from USDC flow. | FM-WLA-02 |
| BR-WLA-011 | Cap overflow policy (forfeit or carry) is per-tenant config. Default: forfeit. | FM-WLA-02 |
| BR-WLA-012 | Computation is idempotent — re-running for same `job_id` with frozen snapshot = same result. | FM-WLA-02 |
| BR-WLA-013 | AUM=0 users receive no fee reward (rank = none). May still receive upline bonuses. | FM-WLA-02 |
| BR-WLA-014 | `clientNonce` must be unique per job. Re-sending with same nonce is a no-op. | FM-WLA-03 |
| BR-WLA-015 | Before ONCHAIN phase, verify distributor balance ≥ today's total payout. Insufficient → BLOCKED. | FM-WLA-03 |
| BR-WLA-016 | Emergency Pause sets all active ONCHAIN jobs to `paused_waiting`. Resumes after unpause + confirmation. | FM-WLA-03 |
| BR-WLA-017 | Base (8453) and OP (10) distributors operate independently. | FM-WLA-03 |
| BR-WLA-018 | Distributor private key stored in CF Secrets Store. Not in D1 or env vars. | FM-WLA-03 |
| BR-WLA-019 | All BNZA API calls use HMAC-SHA256 signing. Key in CF Secrets Store. | FM-WLA-04 |
| BR-WLA-020 | Nonce must be unique per BNZA API request. Stored in D1 before each call. | FM-WLA-04 |
| BR-WLA-021 | Stream 1 (Ledger) is authoritative for net amounts. WL-ADMIN does not compute net. | FM-WLA-04 |
| BR-WLA-022 | `wl_code` used in all 3 BNZA API streams is read from local tenant config, not fetched from BNZA-ADMIN at runtime. | FM-WLA-04 |
| BR-WLA-023 | BNZA API error during LEDGER_FETCH or BOT_SYNC → job BLOCKED + Slack alert. | FM-WLA-04 |
| BR-WLA-024 | Every write action requires M9 reason note ≥ 10 characters. | FM-WLA-05 |
| BR-WLA-025 | Every write action mirrored to Slack audit channel within 5 seconds. | FM-WLA-05 |
| BR-WLA-026 | Session timeout: 8 hours idle. Re-auth via Cloudflare Access required. | FM-WLA-05 |
| BR-WLA-027 | TOTP 2FA mandatory for all roles. Enforced during admin invite flow. | FM-WLA-05 |
| BR-WLA-028 | PC-only console (min-width 1280px). Mobile not supported. | FM-WLA-05 |
| BR-WLA-029 | No WL-specific values hardcoded. All tenant config from `tenants` table. | FM-WLA-06 |
| BR-WLA-030 | `wl_code` in tenant config is read-only after initialization. | FM-WLA-06 |
| BR-WLA-031 | `rank_table` and `title_table` changes take effect from next distribution job (not retroactive). | FM-WLA-06 |
| BR-WLA-032 | Multi-tenant switching resolved at request time via tenant context header from SSO. | FM-WLA-06 |
| BR-WLA-033 | Critical reconciliation failure → Slack alert + `reconciliation_status = failed` on job. | FM-WLA-07 |
| BR-WLA-034 | Warning reconciliation failures logged and surfaced on Dashboard. Not blocking next job. | FM-WLA-07 |
| BR-WLA-035 | Unexpected `addRewards` detection → Slack Critical + dashboard red banner. Does not auto-pause. | FM-WLA-07 |

---

## Code Namespace Convention

> Canonical source for MSG/CR code numbering across modules.

### MSG-codes — Screen Display Messages

**Format:** `MSG-{TYPE}-{NN}` where TYPE ∈ {`ERR`, `WRN`, `SUC`, `INF`}

| Module | Portal | NN Range |
|--------|--------|----------|
| bnza-pool | PTL-05 | 01–49 |
| bnza-admin | PTL-02 | 50–99 |
| wl-admin | PTL-06 | 100–149 |

### CR-codes — Common Rules

**Format:** `CR-{TYPE}-{NN}` where TYPE ∈ {`BEH`, `DIS`, `VAL`}

| Module | NN Range |
|--------|----------|
| bnza-pool | 01–49 |
| bnza-admin | 50–99 |
| wl-admin | 100–149 |

