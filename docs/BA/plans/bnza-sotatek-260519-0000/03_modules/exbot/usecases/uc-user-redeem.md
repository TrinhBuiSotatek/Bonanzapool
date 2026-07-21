---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-20
owner: "@hienduong"
linked_stories: [US-EXBOT-004]
changelog:
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

# UC-EXBOT-user-redeem: User-Initiated Redemption (LP-First)

## Trigger

User navigates to the relevant screen or initiates the described action.

---

## 1. Actors
- **Primary:** USDC Investor (on-chain tx + POOL UI)
- **System:** BnzaExVault (Solidity), Redeem Event Watcher, user_redeem Worker, Hyperliquid

## 2. Preconditions
- Bot `lifecycle_state IN ('active', 'paused', 'hedge_stopped_cooldown', 'lp_rebalancing', 'safe_mode', 'error')` — user may initiate on-chain redeem from any non-closed state; `BnzaExVault` contract does not check `lifecycle_state`; only tokenId ownership (`position.owner == user` AND `position.botId == botId`) is validated on-chain
- Note for `lp_rebalancing`: if user calls `redeem(oldTokenId)` mid-rebalance (before backend persists `newTokenId`), on-chain tx reverts safely (NFT already burned); `redeem(newTokenId)` succeeds after rebalance completes
- Investor holds LP NFT redemption rights via BnzaExVault

## 3. Main Success Scenario
1. Investor calls `BnzaExVault.redeem(tokenId)` on-chain
2. BnzaExVault instantly liquidates LP (decreaseLiquidity 100% + collect + swap to USDC)
3. LP-portion USDC transferred to investor's wallet **in the same on-chain transaction** (on-chain guarantee)
4. `RedemptionEvent(botId, redeemTxHash, userAddress)` emitted
5. Redeem Event Watcher detects event; enqueues to `user_redeem` queue (highest priority)
6. Redeem Worker inserts `message_id` into `queue_idempotency` (started); UNIQUE conflict → skip
7. Redeem Worker creates `close_operations` row:
   - Insert (kind='user_redeem', state='requested')
   - Update state=`lp_closed` (LP liquidated on-chain — confirmed from step 2)
   - Update state=`funds_returned` (LP-portion USDC in investor wallet — on-chain guarantee from step 3)
8. Redeem Worker acquires a User Lock (Redis Redlock via ElastiCache) lease for this user
9. Update `close_operations.state = 'hedge_close_pending'` (recovery checkpoint — marks hedge close as in-progress before HL call; if Lambda crashes here, recovery worker knows to resume hedge close)
10. Redeem Worker calls HL full close (`closeShortReduceOnlyIoc`, cloid) — retries up to 3 times in-invocation (within the same Lambda invocation, inside the Redlock-acquired block) on reject/timeout; after 3 failures → A2
11. Cancels existing stop via `§19.5 replaceStopProtected` with size=0
12. Reconcile: verify HL position size = 0
13. Update `close_operations.state='hedge_closed'`
14. HL-portion settlement (same chain as bot_safe_close: `hl_withdraw → hl_fulfill`):
    - **14a (`hl_withdraw`):** query `clearinghouseState.withdrawable` from HL API (initial); sign master withdraw3 for full amount; poll until balance ≤ threshold (final); record `redemption_requests.principal_amount = initial − final` (USDC 6-decimal base units, net of PnL/funding/fees — HL API returns net balance, no per-fee breakdown)
    - **14b (`hl_fulfill`):** ensure operator has enough USDC on redemption chain — skip CCTP if already funded (reserved liquidity), otherwise burn on Arbitrum + mint via CCTP bridge; mark `ready_to_fulfill`
    - **14c:** call `RedemptionQueue.fulfillRequest` on-chain (FIFO enforced by contract); `safeTransferFrom(operator, investor, principal_amount)`
15. Update `close_operations.state='done'`; `bots.lifecycle_state='closed'`
16. Update `queue_idempotency.state='succeeded'`

## 4. Alternate Flows
- **A1 (SLA breach — hedge not closed within 5 min):** Admin alert: "user_redeem SLA breached for bot {id}"; LP-portion repayment NOT reverted
- **A2 (HL hedge close fails after 3 retries or reconcile mismatch — HL position ≠ 0):** `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; admin notified (E-EXBOT-024); LP-portion repayment NOT reversed; SAFE_MODE does NOT apply (LP already liquidated)
- **A3 (duplicate message delivery):** Step 6 — `queue_idempotency` UNIQUE conflict → return immediately

## 5. Postconditions

**Happy path:**
- `bots.lifecycle_state='closed'`
- LP-portion USDC already in investor wallet (on-chain guarantee from step 3)
- HL-portion USDC sent post-hedge-close
- `close_operations.state='done'`

**A2 (hedge close fails):**
- `bots.lifecycle_state='error'`, `bots.status='error'`
- LP-portion USDC already in investor wallet (on-chain guarantee, not reversed)
- `close_operations.state='residual_hl_liability'`
- Admin notified (E-EXBOT-024); manual HL position close required

---

## 6. Business Rules
- BR-EXBOT-006 (LP repayment unconditional — never blocked by hedge close failure)

---

## Diagram

> See **F-04: Close Flow — user_redeem (LP-First)** in [`srs/flows.md`](../srs/flows.md) — full sequence from on-chain redeem → Redeem Event Watcher → user_redeem queue → Redeem Worker → User Lock (Redis Redlock) → Hyperliquid close → Aurora PostgreSQL update.

## 7. FR Trace
FR-EXBOT-070
