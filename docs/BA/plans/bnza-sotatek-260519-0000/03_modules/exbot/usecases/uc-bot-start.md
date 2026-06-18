---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-12
owner: "@hienduong"
linked_stories: [US-EXBOT-001]
changelog:
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-bot-start: Start ExBot

## Trigger

User navigates to the relevant screen or initiates the described action.

---

## 1. Actors
- **Primary:** USDC Investor (via POOL UI → Operator Facade → ExBot Worker)
- **System:** ExBot Worker, BnzaExVault (Solidity), Hyperliquid

## 2. Preconditions
- User has no existing ExBot with `status IN ('active','paused','closing','safe_mode','error')`
- User has HL account with isolated margin balance ≥ required × 2.0
- User's HL agent key `approval_status='approved'` and not expired
- Builder fee (5bps) confirmed on HL

## 3. Main Success Scenario
1. Investor submits start request via POOL UI
2. OPERATOR receives `POST /api/exbot/start`, forwards to ExBot Worker via service binding
3. ExBot Worker runs preflight: one-bot check → margin check → agent key check → builder fee check → LP mint simulation
4. ExBot Worker creates bot record (`lifecycle_state='preflight'`)
5. ExBot Worker calls `BnzaExVault.vaultMint(...)` → receives `VaultMinted` event with `tokenId`
6. D1 `positions` updated with `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'`
7. ExBot Worker opens HL short IOC (`targetShortEth = lpEthAmount × 0.70`)
8. Post-order reconcile: fetches actual HL position, extracts `entry_price`, `liquidation_price`, `effective_leverage`
9. `lifecycle_state='hedge_post_confirmed'`; D1 `hedge_legs` updated
10. Computes `stop_trigger_px` (BigDecimal, safetyFactor=0.70); places reduce-only stop market on HL
11. Stop confirmed → `lifecycle_state='stop_verified'` → `'active'`
12. Response returned to POOL UI: bot active

## 4. Alternate Flows
- **A1 (one-bot policy fail):** Step 3 — reject with "You already have an active ExBot."
- **A2 (margin insufficient):** Step 3 — block with margin amount details
- **A3 (agent key pending):** Step 3 — block with "Agent key must be approved first"
- **A4 (LP mint fails):** Step 5 — enter `error` state, return funds

## 5. Postconditions
- `bots.lifecycle_state='active'`, `bots.status='active'`
- LP NFT held by BnzaExVault (`positions.custodian='vault'`)
- HL short open with reduce-only stop placed
- `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` populated

---

## Postconditions

- System state reflects the completed operation
- Relevant audit log entries recorded (NFR-ADM-005)
- Affected bot state transitions persisted in D1

## 6. Business Rules
- BR-EXBOT-001 (one-bot policy), BR-EXBOT-010 (standalone Worker)

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
FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-004, FR-EXBOT-020, FR-EXBOT-030, FR-EXBOT-031
