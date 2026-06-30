---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-29
owner: "@hienduong"
linked_stories: [US-EXBOT-001]
changelog:
  - 2026-06-29 | manual | flow change: trigger→system (deposit+key-provision); remove agent key approval precondition; rewrite step 3 (key_status check); remove A3/A9; add Signing Lambda to actors
  - 2026-06-20 | /ba-do | QC audit fixes: A5-A11 added, step 7/10 named params, A3 verbatim fix, on-chain preconditions confirmed, FR trace note, stale template removed
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-bot-start: Start ExBot

## Trigger

System-initiated: on-chain deposit detected by chain indexer (Fargate) → key-provision worker completes master key + agent key generation in AWS KMS → bot start enqueued automatically.

---

## 1. Actors
- **Primary:** System (key-provision worker, after deposit detected by chain indexer)
- **System:** ExBot Worker, BnzaExVault (Solidity), Hyperliquid, AWS KMS, Signing Lambda

## 2. Preconditions
- User has no existing ExBot with `status IN ('active','paused','closing','safe_mode','error')`
- User has HL account with isolated margin balance ≥ required × 2.0
- `hl_agent_keys.key_status='active'` for this user (provisioned by key-provision worker after deposit)
- Builder fee (5bps) confirmed on HL
- ERC-20 allowance: User has approved BnzaExVault to spend USDC ≥ deposit amount
- Native gas: User wallet holds sufficient ETH/native token for vault tx gas

## 3. Main Success Scenario
1. Key-provision worker enqueues bot-start job after setting `hl_agent_keys.key_status='active'`
2. ExBot Worker receives bot-start job
3. ExBot Worker runs preflight: one-bot check → margin check → `hl_agent_keys.key_status='active'` check (block with E-EXBOT-017 if not active) → builder fee check → LP mint simulation
4. ExBot Worker creates bot record (`lifecycle_state='preflight'`)
5. ExBot Worker calls `BnzaExVault.vaultMint(...)` → receives `VaultMinted` event with `tokenId`
6. D1 `positions` updated with `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'`
7. ExBot Worker requests HL short IOC via Signing Lambda (`targetShortEth = lpEthAmount × hedgeRatio (Phase A = 0.70)`)
8. Post-order reconcile: fetches actual HL position, extracts `entry_price`, `liquidation_price`, `effective_leverage`
9. `lifecycle_state='hedge_post_confirmed'`; D1 `hedge_legs` updated
10. Computes `stop_trigger_px` (BigDecimal, `stopSafetyFactor (Phase A = 0.70)`); places reduce-only stop market on HL via Signing Lambda
11. Stop confirmed → `lifecycle_state='stop_verified'` → `'active'`
12. Bot active; status visible in POOL UI on next status poll

## 4. Alternate Flows
- **A1 (one-bot policy fail):** Step 3 — reject with "You already have an active ExBot."
- **A2 (margin insufficient):** Step 3 — block with margin amount details
- **A4 (LP mint fails):** Step 5 — enter `error` state, return funds
- **A5 (builder fee not confirmed):** Step 3 — block with "Builder fee (5bps) must be confirmed on HL before starting."
- **A6 (LP mint simulation fail):** Step 3 — block with simulation error details; no vault call made.
- **A7 (HL unreachable):** Step 5 or 7 — enter `error` state; return "HL service unavailable, please retry."
- **A8 (stop placement fail):** Step 10 — enter `error` state; HL short open but stop not confirmed; alert operator.
- **A10 (HL order rejection):** Step 7 — HL rejects IOC order; enter `error` state; return HL rejection reason.
- **A11 (reconcile mismatch):** Step 8 — actual size deviates > threshold; enqueue `partial_repair`; alert operator.

## 5. Postconditions
- `bots.lifecycle_state='active'`, `bots.status='active'`
- LP NFT held by BnzaExVault (`positions.custodian='vault'`)
- HL short open with reduce-only stop placed
- `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` populated

## 6. Business Rules
- BR-EXBOT-001 (one-bot policy), BR-EXBOT-010 (standalone Worker)

---

## Diagram

> See **F-03: Bot Initialization Flow** in [`srs/flows.md`](../srs/flows.md) — full sequence from on-chain deposit → chain indexer (Fargate) → key-provision worker (AWS KMS) → HL approveAgent → bot-start → preflight → LP mint → hedge open (Signing Lambda) → stop place → active.

## 7. FR Trace
FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-004, FR-EXBOT-020, FR-EXBOT-030, FR-EXBOT-031

Note: frd.md uses implementation grouping numbers; srs/spec.md is canonical. Trace here always refers srs/spec.md.
