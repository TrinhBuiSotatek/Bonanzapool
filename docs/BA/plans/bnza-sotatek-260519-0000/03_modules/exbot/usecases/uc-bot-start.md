---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-20
owner: "@hienduong"
linked_stories: [US-EXBOT-001]
changelog:
  - 2026-07-20 | manual | A11 fix: replace incorrect drift_threshold reference with exact-fill threshold confirmed from develop branch; note drift_threshold belongs to light-check only; close OQ-EXBOT-11 dependency
  - 2026-07-09 | manual | P2 fix: remove builder fee from Preconditions — runtime check in preflight step 2, not a pre-assumed condition
  - 2026-07-08 | /ba-do | I-13: add FR-EXBOT-003/011/081/091 to FR Trace §7; I-11: A7/A10 error state → safe_mode; I-12: register E-EXBOT-026
  - 2026-07-07 | manual | flow change: trigger→user-initiated (POST /api/exbot/start); add vault balance preflight check; rewrite Trigger/Actors/Preconditions/Steps 1-2/A3
  - 2026-07-04 | arc-migration | replace Cloudflare primitives with AWS equivalents (D1→Aurora PostgreSQL, ExBot Worker→ExBot Lambda, BR-EXBOT-010 annotation standalone Worker→standalone Lambda)
  - 2026-06-29 | manual | flow change: trigger→system (deposit+key-provision); remove agent key approval precondition; rewrite step 3 (key_status check); remove A3/A9; add Signing Lambda to actors
  - 2026-06-20 | /ba-do | QC audit fixes: A5-A11 added, step 7/10 named params, A3 verbatim fix, on-chain preconditions confirmed, FR trace note, stale template removed
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-bot-start: Start ExBot

## Trigger

User-initiated: USDC Investor calls `POST /api/exbot/start` via POOL UI after completing an on-chain deposit. Key-provision (KMS key generation + HL `approveAgent`) runs automatically at deposit time (see F-03a) — bot start is a separate, explicit user action.

---

## 1. Actors
- **Primary:** USDC Investor (via POOL UI / `POST /api/exbot/start`)
- **System:** ExBot Lambda, BnzaExVault (Solidity), Hyperliquid, AWS KMS, Signing Lambda

## 2. Preconditions
- User has completed an on-chain deposit; `BnzaExVault` balance > 0 for this user
- Key-provision has completed: `hl_agent_keys.key_status='active'` for this user
- User has no existing ExBot with `status IN ('active','paused','closing','safe_mode','error')`
- User has HL account with isolated margin balance ≥ required × 2.0
- Native gas: User wallet holds sufficient ETH/native token for vault tx gas

## 3. Main Success Scenario
1. Investor calls `POST /api/exbot/start` → ExBot Lambda receives request
2. ExBot Lambda runs preflight: one-bot check → vault balance check (block with E-EXBOT-025 if no deposit) → margin check → `hl_agent_keys.key_status='active'` check (block with E-EXBOT-017 if not active) → builder fee check → LP mint simulation
3. ExBot Lambda creates bot record (`lifecycle_state='preflight'`)
4. ExBot Lambda calls `BnzaExVault.vaultMint(...)` → receives `VaultMinted` event with `tokenId`
5. Aurora PostgreSQL `positions` updated with `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'`
6. ExBot Lambda requests HL short IOC via Signing Lambda (`targetShortEth = lpEthAmount × hedgeRatio (Phase A = 0.70)`)
7. Post-order reconcile: fetches actual HL position, extracts `entry_price`, `liquidation_price`, `effective_leverage`
8. `lifecycle_state='hedge_post_confirmed'`; Aurora PostgreSQL `hedge_legs` updated
9. Computes `stop_trigger_px` (BigDecimal, `stopSafetyFactor (Phase A = 0.70)`); places reduce-only stop market on HL via Signing Lambda
10. Stop confirmed → `lifecycle_state='stop_verified'` → `'active'`
11. Bot active; status visible in POOL UI on next status poll

## 4. Alternate Flows
- **A1 (one-bot policy fail):** Step 2 — reject with "You already have an active ExBot."
- **A2 (margin insufficient):** Step 2 — block with margin amount details
- **A3 (no vault deposit):** Step 2 — block with E-EXBOT-025 "No confirmed deposit found. Please complete an on-chain deposit before starting the bot."
- **A4 (LP mint fails):** Step 4 — enter `error` state (E-EXBOT-028); no funds moved; admin intervention required
- **A5 (builder fee not confirmed):** Step 2 — block with E-EXBOT-005
- **A6 (LP mint simulation fail):** Step 2 — block with E-EXBOT-006; no vault call made.
- **A7 (HL unreachable):** Step 4 or 6 — enter `safe_mode`; alert operator; auto-recovery per FR-EXBOT-050 (retry when HL responsive + 3 reconciles succeed; if irrecoverable → bot_safe_close).
- **A8 (stop placement fail):** Step 9 — enter `safe_mode`; HL short open but stop not confirmed; alert operator; auto-recovery per FR-EXBOT-050 (retry when HL responsive + 3 reconciles succeed; if irrecoverable → bot_safe_close).
- **A9 (key not yet provisioned):** Step 2 — block with E-EXBOT-017 "Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete."
- **A10 (HL order rejection):** Step 6 — HL rejects IOC order; enter `safe_mode` (E-EXBOT-026); alert operator; auto-recovery per FR-EXBOT-050 (retry when HL responsive + 3 reconciles succeed; if irrecoverable → bot_safe_close).
- **A11 (reconcile mismatch):** Step 7 — actual size deviates > threshold; enqueue `partial_repair`; alert operator. *(threshold: exact fill required — actual HL position size must equal target; any partial fill results in `reconcile_partial` status → partial_repair flow. Note: `drift_threshold = max($25, lpValueUsd × 3%)` is the light-check rebalance trigger, unrelated to this reconcile step.)*

## 5. Postconditions
- `bots.lifecycle_state='active'`, `bots.status='active'`
- LP NFT held by BnzaExVault (`positions.custodian='vault'`)
- HL short open with reduce-only stop placed
- `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` populated

## 6. Business Rules
- BR-EXBOT-001 (one-bot policy), BR-EXBOT-010 (standalone Lambda)

---

## Diagram

> See **F-03a: Auto Key-Provision on Deposit** and **F-03b: User-Triggered Bot Start** in [`srs/flows.md`](../srs/flows.md) — F-03a covers on-chain deposit → chain indexer (Fargate) → key-provision worker (AWS KMS) → HL approveAgent. F-03b covers user API call → preflight → LP mint → hedge open (Signing Lambda) → stop place → active.

## 7. FR Trace
FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-004, FR-EXBOT-011, FR-EXBOT-020, FR-EXBOT-030, FR-EXBOT-031, FR-EXBOT-081, FR-EXBOT-091

Note: frd.md uses implementation grouping numbers; srs/spec.md is canonical. Trace here always refers srs/spec.md.
