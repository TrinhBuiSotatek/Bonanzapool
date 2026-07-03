---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-07-03
owner: "@hienduong"
linked_stories: [US-EXBOT-004]
changelog:
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
- Bot `status='active'` (or paused/safe_mode — user may redeem from any non-closed state)
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
8. Redeem Worker acquires `UserLockDO` lease for this user
9. Redeem Worker calls HL full close (`closeShortReduceOnlyIoc`, cloid) — retries up to 3 times on reject/timeout before escalating
10. Cancels existing stop via `§19.5 replaceStopProtected` with size=0
11. Reconcile: verify HL position size = 0
12. Update `close_operations.state='hedge_closed'`
13. Send HL-portion USDC to investor (tracked in `RedemptionQueue` ledger)
14. Update `close_operations.state='done'`; `bots.lifecycle_state='closed'`
15. Update `queue_idempotency.state='succeeded'`

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

> **No diagram yet.** Add a Mermaid sequence diagram or PlantUML flow chart documenting the actor-system interaction for this use case.

```mermaid
sequenceDiagram
    actor User
    participant System
    User->>System: Trigger action
    System-->>User: Response
```

## 7. FR Trace
FR-EXBOT-070
