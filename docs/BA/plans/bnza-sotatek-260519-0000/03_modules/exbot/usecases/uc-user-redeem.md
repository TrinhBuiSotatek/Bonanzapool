---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-25
owner: "@hienduong"
linked_stories: [US-EXBOT-004]
changelog:
  - 2026-07-25 | /ba-impact | C-1: step 6 + diagram ref → Postgres advisory lock
  - 2026-07-24 | /ba-do | Change A: rewrite trigger model — user clicks Close Bot on BNZP UI → Operator API → Operator executes vaultClose on-chain (LP-first); retire Redeem Event Watcher; remove "same tx on-chain guarantee"; rename UC to user_close
  - 2026-07-20 | manual | step 14 expanded: hl_withdraw (principalAmount = withdrawable delta) + hl_fulfill (CCTP + fulfillRequest) — aligns with close chain lp_leg_exec→hedge_sync→hl_withdraw→hl_fulfill
  - 2026-07-14 | manual | replace generic Mermaid placeholder with reference to flows.md F-04
  - 2026-07-14 | manual | I-N3 fix: add hedge_close_pending transition as step 9 (after lock acquired, before HL close call); renumber steps 10–15 to 11–16
  - 2026-07-14 | manual | I-N2 fix: clarify closeShortReduceOnlyIoc retry strategy — in-invocation (3 retries within same Lambda invocation, inside Redlock block); no SQS re-queue per retry
  - 2026-07-14 | manual | I-N1 fix: expand Preconditions — enumerate all allowed lifecycle_states for user_redeem; clarify on-chain validation (tokenId ownership only, no lifecycle_state check); add lp_rebalancing edge case note
  - 2026-07-04 | arc-migration | replace UserLockDO with User Lock (Redis Redlock via ElastiCache) per FR-EXBOT-092
  - 2026-07-03 | /ba-do | I-11: define retry count 3 for closeShortReduceOnlyIoc (align with bot_safe_close); arc update deferred
  - 2026-07-03 | /ba-do | I-09: remove duplicate boilerplate Postconditions section
  - 2026-07-03 | /ba-do | I-08: expand A2 to cover reconcile failure — same residual_hl_liability path, SAFE_MODE does not apply
  - 2026-07-03 | /ba-do | I-06: add A2 postconditions — bots.lifecycle_state='error', bots.status='error' when hedge close fails
  - 2026-07-03 | /ba-do | I-05: register E-EXBOT-024 (user_redeem hedge close failed); UC A2 updated to cite E-EXBOT-024
  - 2026-07-03 | /ba-do | I-04: fix close_operations notation — step 7 expanded to 3 transitions (requested -> lp_closed -> funds_returned)
  - 2026-07-03 | /ba-do | I-01: remove FR-EXBOT-071 from FR Trace — FR does not exist in frd.md, not in scope of user-redeem
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-user-close: User-Initiated Close (LP-First, Operator-Executed)

## Trigger

User clicks "Close Bot" on BNZP UI → POOL UI calls Operator API (`POST /api/exbot/close`) → Operator enqueues user_close job (highest priority).

---

## 1. Actors
- **Primary:** USDC Investor (via BNZP UI)
- **System:** Operator API, user_close Worker, BnzaExVault (Solidity), Master Signing Lambda, AWS KMS, Hyperliquid

## 2. Preconditions
- Bot `lifecycle_state IN ('active', 'paused', 'hedge_stopped_cooldown', 'lp_rebalancing', 'safe_mode', 'error')` — user may initiate close from any non-closed state
- User is authenticated on BNZP UI; wallet address matches bot owner
- Note for `lp_rebalancing`: if user triggers close mid-rebalance, Operator queues the close request; execution begins after rebalance completes
- Investor holds LP NFT via BnzaExVault (managed by Operator on behalf of user)

## 3. Main Success Scenario
1. User clicks "Close Bot" on BNZP UI and confirms close
2. POOL UI calls `POST /api/exbot/close` → Operator API validates ownership and lifecycle_state
3. Operator enqueues `user_close` job (highest priority queue)
4. user_close Worker inserts `message_id` into `queue_idempotency` (started); UNIQUE conflict → skip
5. user_close Worker creates `close_operations` row: Insert (kind='user_close', state='requested')
6. user_close Worker acquires a Postgres advisory lock for this user
7. Update `close_operations.state = 'hedge_close_pending'` (recovery checkpoint — marks hedge close as in-progress before HL call)
8. user_close Worker calls HL full close (`closeShortReduceOnlyIoc`, cloid) via Agent Signing Lambda + AWS KMS — retries up to 3 times in-invocation (within the same Lambda invocation, inside the advisory lock) on reject/timeout; after 3 failures → A2
9. Cancels existing stop via `§19.5 replaceStopProtected` with size=0
10. Reconcile: verify HL position size = 0
11. Update `close_operations.state='hedge_closed'`
12. Operator calls `BnzaExVault.vaultClose(dest=USER)` via Master Signing Lambda + AWS KMS — LP instantly liquidated (decreaseLiquidity 100% + collect + swap to USDC)
13. Update `close_operations.state='lp_closed'`; LP-portion USDC transferred to investor's wallet on-chain
14. Update `close_operations.state='funds_returned'`
15. HL-portion settlement (`hl_withdraw → hl_fulfill`):
    - **15a (`hl_withdraw`):** query `clearinghouseState.withdrawable` from HL API (initial); sign master withdraw3 for full amount via Master Signing Lambda; poll until balance ≤ threshold (final); record `redemption_requests.principal_amount = initial − final`
    - **15b (`hl_fulfill`):** ensure operator has enough USDC on redemption chain — skip CCTP if already funded, otherwise burn on Arbitrum + mint via CCTP bridge; mark `ready_to_fulfill`
    - **15c:** call `RedemptionQueue.fulfillRequest` on-chain (FIFO enforced by contract); `safeTransferFrom(operator, investor, principal_amount)`
16. Update `close_operations.state='done'`; `bots.lifecycle_state='closed'`
17. Update `queue_idempotency.state='succeeded'`
18. POOL UI shows close confirmation to user

## 4. Alternate Flows
- **A1 (SLA breach — hedge not closed within 5 min of Operator close request):** Admin alert: "user_close SLA breached for bot {id}"; LP-portion repayment NOT reverted
- **A2 (HL hedge close fails after 3 retries or reconcile mismatch — HL position ≠ 0):** `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; admin notified (E-EXBOT-024); LP-portion repayment NOT reversed; SAFE_MODE does NOT apply (LP already liquidated)
- **A3 (duplicate message delivery):** Step 4 — `queue_idempotency` UNIQUE conflict → return immediately
- **A4 (vaultClose on-chain fails):** Step 12 — Operator retries (max 3); on final failure: `close_operations.state='error'`; admin notified; hedge already closed (step 11); manual LP close required

## 5. Postconditions

**Happy path:**
- `bots.lifecycle_state='closed'`
- LP-portion USDC sent to investor's wallet (Operator-executed vaultClose)
- HL-portion USDC sent post-hedge-close
- `close_operations.state='done'`

**A2 (hedge close fails):**
- `bots.lifecycle_state='error'`, `bots.status='error'`
- LP close has NOT yet occurred (hedge-first guard: hedge must close before LP close)
- `close_operations.state='residual_hl_liability'`
- Admin notified (E-EXBOT-024); manual HL position close required before LP close can proceed

---

## 6. Business Rules
- BR-EXBOT-006 (LP repayment unconditional — never blocked by hedge close failure)

---

## Diagram

> See **F-04: Close Flow — user_close (LP-First, Operator-Executed)** in [`srs/flows.md`](../srs/flows.md) — full sequence from BNZP UI close request → Operator API → user_close queue → user_close Worker → Postgres advisory lock → Hyperliquid hedge close → BnzaExVault LP close (Master Signing Lambda) → Aurora PostgreSQL update.

## 7. FR Trace
FR-EXBOT-070
