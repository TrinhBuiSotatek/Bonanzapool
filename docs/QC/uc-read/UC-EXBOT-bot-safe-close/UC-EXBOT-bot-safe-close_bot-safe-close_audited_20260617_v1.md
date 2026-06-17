# UC Readiness Review — UC-EXBOT-bot-safe-close
> Document Title: UC-EXBOT-bot-safe-close Readiness Review v1
> Date Created: 2026-06-17 | Author/Agent: qc-uc-read (run-20260617-130500-udemysen) | Version: v1

---

## Feature Brief

UC-EXBOT-bot-safe-close covers the system-initiated, hedge-first close of an ExBot when unsafe conditions are detected (circuit breaker exhausted, margin critical, 3 stops in 7 days, partial repair exhausted, or admin force-close). The sequence is atomic: Close Worker → HL full close → stop cancel → LP close via BnzaExVault → USDC parked to `uninvested_balances` on-chain → `lifecycle_state='cooldown'`. A separate Re-Entry Worker polls every 60 min: if 7d APR > −15% AND preflight 2.0× buffer AND on-chain balance > 0, the bot self-recovers via `BnzaExVault.redeploy`. Third close within 7 days escalates to `parked` (24h interval) with admin notification. SAFE_MODE is never a terminal state (BR-EXBOT-007).

---

## Readiness Verdict

| Overall Score | Verdict |
|---|---|
| **69.2 / 100** | ❌ **NOT READY** |

**Primary blockers:** NV-3 (INV-STOP stop cancel path), `vaultClose` vs `redeem` method name conflict between UC and spec.

---

## 0. Document Metadata

| UC-ID | Feature Name | Version | Status |
|---|---|---|---|
| UC-EXBOT-bot-safe-close | System Hedge-first Close + USDC park + automatic re-entry closed loop | v1 | Draft |

| Author / BA | Date Created | Last Updated |
|---|---|---|
| @hienduong (BA) | 2026-06-12 | 2026-06-17 |

---

## 1. Objective & Scope

### 1.1 Objective
Provide a system-initiated safe exit that: (a) closes the HL hedge before touching the LP to prevent unhedged position risk; (b) parks USDC in `uninvested_balances` accessible to the user at any time; (c) autonomously attempts re-entry after cooldown, eliminating the need for manual intervention on recoverable conditions.

### 1.2 In Scope
- 5 trigger conditions for `bot_safe_close` initiation (FR-EXBOT-072)
- Hedge-first, LP-second, USDC-park execution sequence (FR-EXBOT-073 6-state machine)
- Up to 3 hedge close retries before admin escalation
- `lifecycle_state='cooldown'` → re-entry loop (every 60 min)
- Re-entry judgment: 7d APR + preflight 2.0× + on-chain balance check
- 3rd close within 7d → `lifecycle_state='parked'` (24h interval) + admin escalation
- `SAFE_MODE` as a non-terminal state (BR-EXBOT-007)
- Idempotency: `close_operations.idempotency_key UNIQUE`

### 1.3 Out of Scope
- `user_redeem` (LP-first, user-initiated) — covered by `UC-EXBOT-user-redeem`
- Manual USDC withdrawal from `uninvested_balances`
- Key management during re-entry (covered by `UC-EXBOT-agent-key`)

---

## 2. Actors & Stakeholders

| Actor | Type | Role |
|---|---|---|
| ExBot System Operator | Primary | System actor; represents Close Worker + Re-Entry Worker CF Workers |
| Close Worker | System | CF Worker; executes hedge-first close sequence |
| Re-Entry Worker | System | CF Worker; runs re-entry judgment every 60 min during cooldown/parked |
| Hyperliquid (HL) | External | Target for full close + stop cancel; source of reconcile data |
| BnzaExVault (Solidity) | System (on-chain) | LP liquidation (`vaultClose` or `redeem`); USDC parking (`uninvested_balances`); re-entry via `redeploy` |
| Cloudflare D1 | System | `close_operations`, `uninvested_balances`, `funding_daily_metrics` |
| UserLockDO | System (CF DO) | Per-user HL mutation lock (close + re-entry) |
| Investor | Stakeholder | Receives notifications; uninvested USDC is theirs to withdraw |

---

## 3. Preconditions & Postconditions

### 3.1 Preconditions
Any ONE of 5 trigger conditions (FR-EXBOT-072):
1. `circuit_breakers.state='open'` and `reset_at` extended ≥3× without probe success
2. `margin_status='critical'` twice → SAFE_MODE with no auto-recovery path
3. `lifecycle_state='hedge_stopped_cooldown'` entered 3rd time within 7-day rolling window
4. `partial_repair` consumer fails 3 consecutive repair attempts for same trigger event
5. Admin invokes `/api/exbot/close` explicitly

*(Inferred)* NV-3: INV-STOP §19.5 stop cancel path must be confirmed before step 3 implementation.

### 3.2 Postconditions

| Outcome | System State |
|---|---|
| Happy path (close) | `lifecycle_state='cooldown'`; `close_operations.state='done'`; USDC in `uninvested_balances` on-chain |
| Re-entry success | `lifecycle_state='active'`; `uninvested_balances=0` on-chain; bot running |
| A1 (3rd close within 7d) | `lifecycle_state='parked'`; admin escalation; investor notified |
| A2 (hedge close impossible) | `close_operations.state='residual_hl_liability'`; SAFE_MODE; LP untouched |
| A3 (re-entry: balance=0) | D1 corrected to on-chain; re-entry aborted; lifecycle stays 'cooldown' |
| A4 (redeploy reverts) | Re-entry aborted; carry over to next interval |

---

## 4. API / Queue / State Interface Inventory

> UC §2 = trigger preconditions only, no interface inventory. Auto-cap applied: KA #5 max 8/15.

**HL API (Close Cycle):**

| # | Method | Notes |
|---|---|---|
| 1 | `closeShortReduceOnlyIoc(cloid)` | Full close, target=0 |
| 2 | `replaceStopProtected(size=0)` — §19.5 | Stop cancel; ⚠️ NV-3 blocker |
| 3 | `clearinghouseState` (reconcile) | Verify size=0 |

**On-chain (Close + Re-entry):**

| # | Method/Event | Notes |
|---|---|---|
| 4 | `BnzaExVault.vaultClose(tokenId, dest=UNINVESTED)` | ⚠️ CONFLICT: spec FR-EXBOT-073 uses `redeem(tokenId)` |
| 5 | `FundsParked(user, botId, amount)` event | Emitted after vaultClose |
| 6 | `uninvestedBalanceOf(user, botId)` READ | On-chain canonical; used at re-entry judgment |
| 7 | `BnzaExVault.redeploy(botId)` | ⚠️ ABI unconfirmed |
| 8 | `FundsRedeployed` event | Confirmed after redeploy |

**D1:**

| # | Table | Operation |
|---|---|---|
| 9 | `close_operations` | INSERT + 6-state transitions; `idempotency_key UNIQUE` |
| 10 | `uninvested_balances` | UPDATE (park amount); CAS UPDATE to 0 (re-entry); ⚠️ CAS key undefined |
| 11 | `funding_daily_metrics` | READ last 7 rows (7d APR) |

**DO:**

| # | DO | Lease | Notes |
|---|---|---|---|
| 12 | `UserLockDO.acquire/release` | 90s | ⚠️ Release not listed in re-entry steps |

**Notification Queue:**

| # | Trigger | Message |
|---|---|---|
| 13 | Cooldown entry | "Bot safely closed. USDC parked. Re-entry will be attempted automatically." |
| 14 | Re-entry success | "Bot re-started automatically." |
| 15 | Parked transition | "Bot parked after repeated stops. System will continue recovery attempts every 24h." |

---

## 5. System State Model

**`close_operations` State Machine (✅ matches spec FR-EXBOT-073):**

| State | Trigger | Next State | On Fail |
|---|---|---|---|
| `requested` | Trigger condition fires | `hedge_close_pending` | — |
| `hedge_close_pending` | HL close + reconcile | `hedge_closed` | Retry ≤3×; then `residual_hl_liability` + SAFE_MODE |
| `hedge_closed` | Stop cancelled + reconcile pass | `lp_closed` | — |
| `lp_closed` | `vaultClose/redeem` confirmed | `funds_parked` | — |
| `funds_parked` | `FundsParked` event | `done` | — |
| `done` | All steps complete | — | → `lifecycle_state='cooldown'` |

**`bots.lifecycle_state` Transitions:**

| From | Trigger | To | Notes |
|---|---|---|---|
| active/safe_mode | `bot_safe_close` → done | cooldown | 60-min interval |
| cooldown | Re-entry pass | active | Full open flow |
| cooldown | 3rd close in 7d | parked | 24h interval |
| parked | Re-entry pass | active | Same conditions as cooldown |

---

## 6. Functional Logic & Workflow Decomposition

### 6.1 Main Flow — Close Sequence (9 Steps)

| Step | Actor | Action | FR Ref | Gap |
|---|---|---|---|---|
| 1 | Trigger | Creates `close_operations` row (state='requested', `trigger_reason` populated) | FR-EXBOT-072 | |
| 2 | Close Worker | Acquires `UserLockDO` lease; calls `closeShortReduceOnlyIoc(cloid)` | FR-EXBOT-073 | |
| 3 | Close Worker | Cancels stop via `§19.5 replaceStopProtected(size=0)` | FR-EXBOT-073 | ⚠️ NV-3 blocker |
| 4 | Close Worker | Reconciles: verifies HL size=0; `state='hedge_closed'` | FR-EXBOT-073 | ⚠️ Retry 3× before escalate — absent from main flow |
| 5 | Close Worker | Calls `BnzaExVault.vaultClose(tokenId, dest=UNINVESTED)` | FR-EXBOT-073 | ⚠️ Method conflict vs spec `redeem(tokenId)` |
| 6 | Close Worker | Detects `FundsParked` event; `state='funds_parked'` | FR-EXBOT-073 | |
| 7 | Close Worker | D1 `uninvested_balances` updated with parked USDC | FR-EXBOT-071 | |
| 8 | Close Worker | `state='done'`; `lifecycle_state='cooldown'` (60 min) | FR-EXBOT-071 | ⚠️ UserLockDO release not listed |
| 9 | Close Worker | Sends investor notification | FR-EXBOT-071 | |

### 6.2 Re-Entry Loop (Every 60 Min)

| Step | Actor | Action | FR Ref | Gap |
|---|---|---|---|---|
| 10 | Re-Entry Worker | Reads `funding_daily_metrics` (last 7 rows) — 7d APR | FR-EXBOT-071 | |
| 11 | Re-Entry Worker | Reads `uninvestedBalanceOf(user, botId)` **on-chain** (canonical) | FR-EXBOT-071 | |
| 12 | Re-Entry Worker | If 7d APR > −15% AND preflight 2.0× AND balance > 0: (a) `UserLockDO.acquire`; (b) `redeploy(botId)` → `FundsRedeployed`; (c) D1 CAS UPDATE to 0; (d) run open flow §16.1; (e) `lifecycle_state='active'`; notification | FR-EXBOT-071 | ⚠️ DO release absent; CAS key undefined; timer mechanism undefined |
| 13 | Re-Entry Worker | Else: keep `lifecycle_state='cooldown'`; retry next interval | FR-EXBOT-071 | |

**Business Rules:**

| Rule | Text |
|---|---|
| BR-EXBOT-007 | SAFE_MODE is never a terminal state — recovery path must always exist |

### 6.3 Alternate Flows

| ID | Trigger | Outcome |
|----|---------|---------|
| A1 (3rd close within 7d) | After step 8 | `lifecycle_state='parked'` (24h); admin escalation; investor notification |
| A2 (hedge impossible) | Steps 2–3 failure | `residual_hl_liability` + SAFE_MODE; LP untouched; ⚠️ retry count per spec = 3× (absent from UC) |
| A3 (balance=0 at re-entry) | Step 11 | D1 corrected to on-chain; abort re-entry; carry over |
| A4 (redeploy reverts) | Step 12b | Vault backstop; abort re-entry; carry over |

---

## 7. Functional Integration Analysis

| Trigger / Event | Cross-Op Impact | Check |
|---|---|---|
| 5 trigger conditions | All create same `close_operations` row structure; `idempotency_key UNIQUE` prevents duplicates | Concurrent admin force-close + circuit breaker → UNIQUE rejects second; confirmed by FR-EXBOT-072 AC |
| HL 3-call close (close + cancel + reconcile) | HL weight budget: 3 calls per close cycle; must not exceed 800wt/min | ⚠️ UC does not compute weight |
| `replaceStopProtected(size=0)` | Stop must be cancelled; test cannot be written without NV-3 resolution | ⚠️ B1 blocker |
| `vaultClose` vs `redeem` | UC and spec disagree on LP close method name for bot_safe_close | ⚠️ B2 blocker — canonical method unclear |
| `uninvestedBalanceOf` (on-chain) at re-entry | Prevents re-entry with stale D1 data after user withdrawal | ✅ Strong canonical source usage |
| Re-entry `redeploy` tx revert (A4) | Vault on-chain balance enforcement backstop; re-entry aborts safely | ✅ Defined alternate flow |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then |
|---|---|---|---|---|
| AC-01 | Happy close | Active/safe_mode ExBot; trigger fires | `close_operations` row created | HL closed (size=0); vaultClose called; FundsParked emitted; 6-state machine completes; `lifecycle_state='cooldown'`; investor notified |
| AC-02 | Re-entry success | lifecycle='cooldown'; 60 min elapsed | 7d APR > −15% + preflight 2.0× + balance > 0 | `redeploy` called; `FundsRedeployed` confirmed; open flow runs; `lifecycle_state='active'`; investor notified |
| AC-03 | 3rd close in 7d | 2 prior safe_closes in 7d window | 3rd `bot_safe_close` completes | `lifecycle_state='parked'`; admin escalation; investor notification |
| AC-04 | Re-entry balance=0 | lifecycle='cooldown'; re-entry runs | `uninvestedBalanceOf` = 0 | D1 corrected; abort re-entry (no error); lifecycle stays 'cooldown' |
| AC-05 | Sequential state machine | `close_operations` row exists | Processing runs | States transition sequentially; `lp_closed` never before `hedge_closed`; failure holds at failed step |
| AC-06 | Duplicate trigger | Same `idempotency_key` triggered twice | Second `close_operations` INSERT | UNIQUE constraint rejects; no double close |
| AC-07 | On-chain canonical | D1 `uninvested_balances` stale | Re-entry judgment | Uses `uninvestedBalanceOf` on-chain, not D1 |

---

## 9. Non-functional Requirements

| Category | Requirement | Source |
|---|---|---|
| SAFE_MODE | Never terminal — recovery path always exists | BR-EXBOT-007 |
| Cooldown | 60 min default; 24h in parked state | FR-EXBOT-071 |
| Idempotency | `close_operations.idempotency_key UNIQUE` | FR-EXBOT-072 |
| Hedge retry | Up to 3× before admin escalation | FR-EXBOT-073 |
| On-chain canonical | Re-entry capital check uses `uninvestedBalanceOf` (not D1) | FR-EXBOT-071 |
| ⚠️ HL weight budget | 3 HL calls per close cycle; weight not calculated | NFR-EXBOT-004 |
| ⚠️ DLQ | Not defined for close or re-entry workers | — |
| ⚠️ Re-entry idempotency | `redeploy` idempotency undefined — what if re-entry worker crashes mid-redeploy? | — |

---

## 10. Open Questions & Dependencies

### 10.1 Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | NV-3; OQ-EXBOT-02 | INV-STOP §19.5 path for stop cancel (size=0) — path (a) or (b)? | Blocks step 3 test | Open |
| Q2 | H | uc-bot-safe-close.md §3 step 5 vs spec FR-EXBOT-073 | UC uses `vaultClose(tokenId, dest=UNINVESTED)`; spec uses `redeem(tokenId)` — canonical LP close method? | Blocks on-chain LP close test | Open |
| Q3 | H | spec FR-EXBOT-073 | Hedge retry: 3× sequential HL close calls or 3 re-queue cycles? What is the retry delay? | AC for retry-before-escalation | Open |
| Q4 | M | uc-bot-safe-close.md §3 step 12b | `BnzaExVault.redeploy(botId)` ABI and contract address (Base + OP)? | Blocks re-entry on-chain tests | Open |
| Q5 | M | uc-bot-safe-close.md §3 step 12 | Re-entry "every 60 min" — via Cron, CF DO alarm, or queued delay? | Test scheduling for AC-02 | Open |
| Q6 | M | uc-bot-safe-close.md §3 step 12c | CAS update for D1 `uninvested_balances` — compare condition? Concurrency behavior? | Race condition test coverage | Open |
| Q7 | M | uc-bot-safe-close.md §3 step 2, 12a | `UserLockDO.release` absent from both loops — in `finally` block? | Lock cleanup verification | Open |
| Q8 | L | uc-bot-safe-close.md §4 | DLQ policy for close and re-entry workers? | Worker-failure tests blocked | Open |
| Q9 | L | uc-bot-safe-close.md §4 A1 | Parked state recovery conditions — same as cooldown (7d APR + 2.0×) or different? | Parked recovery test matrix | Open |

### 10.2 Dependencies

| Dependency | Notes |
|---|---|
| NV-3 (OQ-EXBOT-02) | INV-STOP path for stop cancel |
| BnzaExVault ABI | Both `vaultClose/redeem` and `redeploy` ABIs needed |
| `UC-EXBOT-bot-start` | Provides bot in active state with LP + HL short + stop |

---

## 11. Change Log

| Version | Date | Author | Summary |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read (run-20260617-130500-udemysen) | Initial first-audit |

---

## Audit Summary

### Score Breakdown

| # | Knowledge Area | Max | Score | Status |
|---|---|---|---|---|
| 1 | Feature Identity | 5 | 5 | ✅ |
| 2 | Objective & Scope | 5 | 4 | ✅ |
| 3 | Actors & User Roles | 10 | 9 | ✅ |
| 4 | Preconditions & Postconditions | 10 | 7 | ⚠️ |
| 5 | API/Queue/State Interface | 15 | 8 | ⚠️ AUTO-CAP |
| 6 | System State Model | 20 | 14 | ✅ |
| 7 | Functional Logic | 20 | 13 | ⚠️ |
| 8 | Integration Analysis | 20 | 12 | ⚠️ |
| 9 | Acceptance Criteria | 20 | 15 | ✅ |
| 10 | NFRs | 5 | 3 | ⚠️ |
| **TOTAL** | | **130** | **90** | |

**Raw: 90/130 → Final: 69.2/100 → ❌ NOT READY**

### Blockers
- **B1** — NV-3: INV-STOP stop cancel path unconfirmed (step 3)
- **B2** — `vaultClose` vs `redeem` method name conflict (UC step 5 vs spec FR-EXBOT-073)

### Strengths
- `close_operations` 6-state machine matches spec FR-EXBOT-073 exactly — no conflict (unlike user-redeem)
- 4 well-formed Gherkin ACs in US-009 covering close, re-entry, 3rd-parked, balance=0
- On-chain canonical source for re-entry capital check explicitly stated
- A4 (redeploy revert backstop) defined as alternate flow

### Recommendation
DO NOT begin test design. Resolve B1 (NV-3) and B2 (`vaultClose` vs `redeem`) first. Also clarify hedge retry mechanism (W1), re-entry timer implementation (W3), and CAS update key (W4).

### 📋 Unified Gap & Question Report

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | NV-3; OQ-EXBOT-02 | INV-STOP §19.5 path for stop cancel (size=0) — path (a) or (b)? | Blocks step 3 stop cancel test | Open |
| Q2 | H | uc-bot-safe-close.md §3 step 5 vs spec FR-EXBOT-073 | UC uses `vaultClose(tokenId, dest=UNINVESTED)`; spec uses `redeem(tokenId)` — canonical LP close method for bot_safe_close? | Canonical LP close method for test ABI call | Open |
| Q3 | H | spec FR-EXBOT-073 | Hedge retry: 3 sequential HL close calls or 3 re-queue cycles? Retry delay between attempts? | AC for retry-before-escalation cannot be written | Open |
| Q4 | M | uc-bot-safe-close.md §3 step 12b | `BnzaExVault.redeploy(botId)` ABI and contract address (Base + OP)? | Blocks re-entry on-chain tests | Open |
| Q5 | M | uc-bot-safe-close.md §3 step 12 | Re-entry "every 60 min" — Cron, CF DO alarm, or queued delay? | Test scheduling for AC-02 | Open |
| Q6 | M | uc-bot-safe-close.md §3 step 12c | CAS update condition for D1 `uninvested_balances`? Concurrency behavior? | Race condition test coverage | Open |
| Q7 | M | uc-bot-safe-close.md §3 step 2, 12a | `UserLockDO.release` absent from both close loop and re-entry loop — `finally` block? | Lock cleanup verification | Open |
| Q8 | L | uc-bot-safe-close.md §4 | DLQ policy for close and re-entry workers? | Worker-failure tests blocked | Open |
| Q9 | L | uc-bot-safe-close.md §4 A1 | Parked state recovery conditions — same as cooldown or different threshold? | Parked recovery test matrix | Open |
