---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-12
owner: "@hienduong"
linked_stories: [US-EXBOT-009]
changelog:
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-bot-safe-close: System-Initiated Safe Close + Auto Re-Entry

## 1. Actors
- **Primary:** ExBot System Operator (Close Worker, Re-Entry Worker)
- **System:** Hyperliquid, BnzaExVault, D1

## 2. Preconditions
- Trigger condition met: circuit breaker retries exhausted, OR margin critical + SAFE_MODE irrecoverable, OR 3 stops within 7 days, OR admin force-close

## 3. Main Success Scenario
1. Trigger creates `close_operations` row (kind='bot_safe_close', state='requested')
2. Close Worker: acquire `UserLockDO` lease; full close HL short (`closeShortReduceOnlyIoc`)
3. Cancel stop via `§19.5 replaceStopProtected` with size=0
4. Reconcile: verify HL size = 0; update `close_operations.state='hedge_closed'`
5. Call `BnzaExVault.vaultClose(tokenId, dest=UNINVESTED)`
6. `FundsParked(user, botId, amount)` event emitted; `close_operations.state='funds_parked'`
7. D1 `uninvested_balances` updated with parked USDC amount
8. `close_operations.state='done'`; `bots.lifecycle_state='cooldown'` (60 min default)
9. Investor notification: "Bot safely closed. USDC parked. Re-entry will be attempted automatically."

**Re-Entry Loop (every 60 min during cooldown):**
10. Re-Entry Worker reads `funding_daily_metrics` (last 7 rows) — 7d funding APR
11. Reads `uninvestedBalanceOf(user, botId)` **on-chain** (canonical, not D1)
12. If 7d APR > −15% AND preflight (2.0× buffer) passes AND on-chain balance > 0:
    a. Acquire `UserLockDO` lease
    b. Call `BnzaExVault.redeploy(botId)` → `FundsRedeployed` event confirmed
    c. D1 `uninvested_balances` updated to 0 (CAS UPDATE)
    d. Run open flow (§16.1): preflight → lp_opening → ... → active
    e. Investor notification: "Bot re-started automatically."
13. Else: keep `lifecycle_state='cooldown'`; retry next interval

## 4. Alternate Flows
- **A1 (3rd safe_close within 7 days):** After step 8 → `lifecycle_state='parked'` (24h interval) + admin escalation
- **A2 (hedge close impossible):** Step 3 — `close_operations.state='residual_hl_liability'` + SAFE_MODE; do NOT touch LP
- **A3 (on-chain balance = 0 at re-entry):** Step 11 — correct D1 to match on-chain; abort re-entry; carry over to next interval
- **A4 (redeploy tx reverts — concurrent withdraw):** Step 12b — structural backstop by Vault on-chain balance enforcement; abort re-entry; carry over

## 5. Postconditions
- After safe_close: `lifecycle_state='cooldown'` or `'parked'`, USDC in `uninvested_balances`
- After re-entry success: `lifecycle_state='active'`, `uninvested_balances=0`

## 6. Business Rules
- BR-EXBOT-007 (SAFE_MODE not a terminal state)

## 7. FR Trace
FR-EXBOT-072, FR-EXBOT-073
