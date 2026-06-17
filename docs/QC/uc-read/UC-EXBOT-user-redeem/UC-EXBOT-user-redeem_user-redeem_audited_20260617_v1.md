# UC Readiness Review — UC-EXBOT-user-redeem
> Document Title: UC-EXBOT-user-redeem Readiness Review v1
> Date Created: 2026-06-17 | Author/Agent: qc-uc-read (run-20260617-110000-udemysen) | Version: v1

---

## Feature Brief

UC-EXBOT-user-redeem covers the user-initiated LP-first redemption flow. The investor calls `BnzaExVault.redeem(tokenId)` on-chain; the Solidity contract instantly liquidates the LP position and returns the LP-portion USDC to the investor in the same transaction — this is an **unconditional on-chain guarantee** (`BR-EXBOT-006`). The emitted `RedemptionEvent` triggers the Redeem Event Watcher, which enqueues a highest-priority `user_redeem` message. The Redeem Worker then acquires `UserLockDO`, closes the HL short via `closeShortReduceOnlyIoc`, cancels the stop via INV-STOP protocol (size=0), reconciles HL position to zero, sends the HL-portion USDC, and transitions `bots.lifecycle_state='closed'`.

SLA: HL hedge close must complete within 5 minutes of event detection (NFR-EXBOT-003). SLA breach triggers admin escalation but does NOT reverse the LP-portion repayment. HL failure results in `residual_hl_liability` state with admin notification.

---

## Readiness Verdict

| Overall Score | Verdict |
|---|---|
| **65.4 / 100** | ❌ **NOT READY** |

**Primary blockers:** NV-3 (INV-STOP path for stop cancel), OQ-EXBOT-08 (BnzaExVault ABI unconfirmed), `close_operations` state machine conflict between UC and spec.

---

## 0. Document Metadata

| UC-ID | Feature Name | Version | Status |
|---|---|---|---|
| UC-EXBOT-user-redeem | User-initiated LP-first Redemption + HL hedge close (SLA 5 min) | v1 | Draft |

| Author / BA | Date Created | Last Updated |
|---|---|---|
| @hienduong (BA) | 2026-06-12 | 2026-06-17 |

---

## 1. Objective & Scope

### 1.1 Objective
Provide investors with a self-service, trustless exit mechanism: `BnzaExVault.redeem` liquidates the LP and returns capital on-chain instantly, while the system asynchronously closes the HL hedge. The LP-portion return is guaranteed regardless of hedge close outcome.

### 1.2 In Scope
- Investor calling `BnzaExVault.redeem(tokenId)` on-chain
- Instant LP liquidation + LP-portion USDC return in same on-chain tx
- `RedemptionEvent` detection and `user_redeem` queue enqueue
- Highest-priority worker: HL full close + stop cancel + reconcile
- HL-portion USDC delivery tracking (`RedemptionQueue` ledger)
- `bots.lifecycle_state → 'closed'`
- SLA 5-min hedge close monitoring and breach escalation
- `residual_hl_liability` state and admin notification on hedge close failure
- Duplicate message deduplication via `queue_idempotency`

### 1.3 Out of Scope
- `bot_safe_close` (hedge-first, system-initiated) — covered by `UC-EXBOT-bot-safe-close`
- User USDC withdrawal from `uninvested_balances` (separate flow)
- Admin-initiated force close

---

## 2. Actors & Stakeholders

| Actor | Type | Role |
|---|---|---|
| USDC Investor | Primary | Initiates on-chain `BnzaExVault.redeem(tokenId)`; receives LP-portion USDC in same tx |
| BnzaExVault (Solidity) | System (on-chain) | Liquidates LP, returns LP-portion USDC, emits `RedemptionEvent` |
| Redeem Event Watcher | System | Monitors on-chain events; enqueues `user_redeem` queue message |
| user_redeem Worker | System | CF Worker; acquires lock, closes HL, cancels stop, reconciles, sends HL-portion |
| Hyperliquid (HL) | External | Target for full close + stop cancel; source of reconcile data |
| Cloudflare D1 | System | `close_operations`, `queue_idempotency`, `RedemptionQueue` ledger |
| UserLockDO | System (CF DO) | Per-user HL mutation lock |

---

## 3. Preconditions & Postconditions

### 3.1 Preconditions
- Bot `status='active'` OR `status='paused'` OR `status='safe_mode'` (UC allows redeem from any non-closed state)
- Investor holds LP NFT redemption rights via BnzaExVault
- *(Inferred — not listed in UC)* NV-3: INV-STOP stop cancel path must be confirmed before step 10 implementation
- *(Inferred — not listed in UC)* OQ-EXBOT-08: BnzaExVault ABI and contract address deployed before on-chain testing

### 3.2 Postconditions

| Outcome | System State |
|---|---|
| Happy path | `bots.lifecycle_state='closed'`; LP-portion USDC in investor wallet (on-chain); HL-portion USDC sent; `close_operations.state='done'` |
| A1 (SLA breach) | HL still processing; admin alert raised; LP-portion NOT reverted |
| A2 (HL close fails) | `close_operations.state='residual_hl_liability'`; admin notified; LP-portion NOT reversed |
| A3 (duplicate message) | No mutation; existing `close_operations` unchanged |

---

## 4. API / Queue / State Interface Inventory

> UC §2 ABSENT. All entries reconstructed from §3. Auto-cap applied: KA #5 max 8/15.

**On-chain Interactions:**

| # | Method | Trigger | Notes |
|---|---|---|---|
| 1 | `BnzaExVault.redeem(tokenId)` | Investor action | LP liquidated + LP-portion USDC returned in same tx; ⚠️ ABI unconfirmed (OQ-EXBOT-08) |
| 2 | `RedemptionEvent(botId, redeemTxHash, userAddress)` | Emitted by BnzaExVault | Detected by Redeem Event Watcher |

**Queue Consumer:**

| # | Queue | Trigger | Priority | DLQ Policy | Idempotency Key | SLA |
|---|---|---|---|---|---|---|
| 3 | `user_redeem` | `RedemptionEvent` detected | Highest | ⚠️ Not defined in UC | `message_id` (queue_idempotency) | 5 min from event detection |

**DO:**

| # | DO | Lease Duration | Contention | Release Step |
|---|---|---|---|---|
| 4 | `UserLockDO.acquire/release` | 90s | `acquired=false` → ⚠️ behavior not defined in UC | ⚠️ Release step absent from UC main flow |

**HL API Calls:**

| # | Method | Notes |
|---|---|---|
| 5 | `closeShortReduceOnlyIoc(cloid)` | Full close; target=0 |
| 6 | `§19.5 replaceStopProtected(size=0)` | Stop cancel; ⚠️ NV-3 blocks path selection |
| 7 | `clearinghouseState` (reconcile) | Verify size=0 post-close |

**D1 Tables:**

| # | Table | Operation |
|---|---|---|
| 8 | `queue_idempotency` | INSERT (started) + UPDATE (succeeded) |
| 9 | `close_operations` | INSERT + state machine updates; ⚠️ UC states conflict with spec FR-EXBOT-073 |
| 10 | `RedemptionQueue` ledger | INSERT HL-portion tracking entry |

---

## 5. System State Model

**Lifecycle Transitions:**

| From State | Trigger | Guard | To State | On Fail |
|---|---|---|---|---|
| `active` / `paused` / `safe_mode` | `BnzaExVault.redeem` + event detected | `queue_idempotency` UNIQUE not conflicting | `closing` (inferred) → `closed` | A2: `residual_hl_liability`; lifecycle may stay active temporarily |
| Any | `close_operations` duplicate | `idempotency_key UNIQUE` constraint | Rejected | No state change |

**`close_operations` State Machine (⚠️ CONFLICT):**

| UC Step 7 States | Spec FR-EXBOT-073 States | Conflict |
|---|---|---|
| `lp_closed→funds_returned` (initial) | `requested→hedge_close_pending→hedge_closed→lp_closed→funds_parked→done` | UC states do not match spec — canonical source unclear |

**Queue Behavior:**

| Queue | DLQ Policy | Idempotency | Priority | SLA |
|---|---|---|---|---|
| `user_redeem` | ⚠️ Not defined | `message_id` (UNIQUE) | Highest | 5 min hedge close |

**DO Behavior:**

| DO | Lease | Expiry | Release |
|---|---|---|---|
| `UserLockDO` | 90s | Auto-release | ⚠️ Release step not in UC main flow |

---

## 6. Functional Logic & Workflow Decomposition

### 6.1 Main Flow (15 Steps)

| Step | Actor | Action | FR Ref | Gap |
|---|---|---|---|---|
| 1 | Investor | `BnzaExVault.redeem(tokenId)` on-chain | FR-EXBOT-070 | |
| 2 | BnzaExVault | LP liquidated: decreaseLiquidity 100% + collect + swap to USDC | FR-EXBOT-070 | |
| 3 | BnzaExVault | LP-portion USDC transferred to investor wallet in same tx | BR-EXBOT-006 | On-chain guarantee |
| 4 | BnzaExVault | Emits `RedemptionEvent(botId, redeemTxHash, userAddress)` | FR-EXBOT-070 | |
| 5 | Redeem Event Watcher | Detects event; enqueues `user_redeem` (highest priority) | FR-EXBOT-070 | SLA clock starts here |
| 6 | Redeem Worker | INSERT `queue_idempotency` (started); UNIQUE conflict → A3 | FR-EXBOT-070 | |
| 7 | Redeem Worker | Creates `close_operations` row (kind='user_redeem') | FR-EXBOT-070 | ⚠️ Initial state mismatch with spec |
| 8 | Redeem Worker | Acquires `UserLockDO` lease | FR-EXBOT-026 (inferred) | |
| 9 | Redeem Worker | HL full close `closeShortReduceOnlyIoc(cloid)` | FR-EXBOT-070 | |
| 10 | Redeem Worker | Cancel stop via `§19.5 replaceStopProtected(size=0)` | FR-EXBOT-035 (inferred) | ⚠️ NV-3 blocker |
| 11 | Redeem Worker | Reconcile: verify HL position = 0 | FR-EXBOT-070 | |
| 12 | Redeem Worker | `close_operations.state='hedge_closed'` | FR-EXBOT-070 | |
| 13 | Redeem Worker | Send HL-portion USDC to investor; `RedemptionQueue` ledger entry | FR-EXBOT-070 | ⚠️ Transfer mechanism undefined |
| 14 | Redeem Worker | `close_operations.state='done'`; `bots.lifecycle_state='closed'` | FR-EXBOT-070 | ⚠️ UserLockDO release not listed |
| 15 | Redeem Worker | `queue_idempotency.state='succeeded'` | — | |

**Business Rules (verbatim):**

| Rule | Text |
|---|---|
| BR-EXBOT-006 | "`user_redeem` LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user." (P0) |

### 6.2 Alternate Flows

| ID | Trigger | Outcome |
|---|---|---|
| A1 (SLA breach) | 5 min elapsed, hedge not confirmed closed | Admin alert "user_redeem SLA breached for bot {id}"; LP-portion NOT reverted |
| A2 (HL close fails) | Step 9 HL call fails | `close_operations.state='residual_hl_liability'`; admin notified with bot_id, hedge size, USD value; LP-portion NOT reversed |
| A3 (duplicate message) | Step 6: `queue_idempotency` UNIQUE conflict | Return immediately; no HL mutation |

---

## 7. Functional Integration Analysis

| Trigger / Event | Cross-Op Impact | Consistency Check |
|---|---|---|
| `BnzaExVault.redeem` on-chain | LP liquidated + USDC returned atomically on-chain; cannot be reversed by worker | ⚠️ OQ-EXBOT-08: ABI unconfirmed; test requires deployed contract on Base/OP testnet |
| `RedemptionEvent` → worker | Worker must close HL within 5min SLA; LP already settled | HL 3-call cycle (close + stop cancel + reconcile): weight not calculated; must not exceed 800wt/min |
| `replaceStopProtected(size=0)` | Stop must be cancelled before or concurrently with position close | ⚠️ NV-3: path (a)/(b) unconfirmed; test cannot be written |
| A2 `residual_hl_liability` | Admin must receive bot_id + hedge size + USD value | Admin notification content not precisely defined in UC |
| `close_operations` state machine | UC §3 step 7 uses different state names than spec FR-EXBOT-073 | Must be reconciled before state transition tests can be written |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then |
|---|---|---|---|---|
| AC-01 | Happy path | Active ExBot; investor holds LP NFT | `BnzaExVault.redeem(tokenId)` called | LP liquidated in same tx; LP-portion USDC in investor wallet; HL hedge closed within 5min; `lifecycle_state='closed'` |
| AC-02 | SLA breach | user_redeem worker processing | 5 min elapsed without hedge close confirmation | Admin alert raised with bot {id}; LP-portion NOT reverted |
| AC-03 | HL close fails | LP-portion already returned | HL API unavailable → close fails | `close_operations.state='residual_hl_liability'`; admin notified with bot_id + hedge size + USD value; LP-portion NOT reversed |
| AC-04 | Double settlement prevention | Same close_operations idempotency_key | Second `close_operations` INSERT | UNIQUE constraint rejects; no duplicate settlement |
| AC-05 | On-chain guarantee | Any hedge outcome | `BnzaExVault.redeem` tx confirmed | LP-portion USDC in investor wallet regardless of hedge close result |
| AC-06 | Duplicate queue message | Same `message_id` delivered twice | `queue_idempotency` INSERT | UNIQUE conflict → skip; no second HL mutation |

---

## 9. Non-functional Requirements

| Category | Requirement | Source |
|---|---|---|
| SLA | HL hedge close within 5 min of event detection; overrun → admin alert | NFR-EXBOT-003 |
| Priority | `user_redeem` queue: highest priority (above all other queues) | FR-EXBOT-070 |
| Idempotency | `queue_idempotency.message_id` UNIQUE + `close_operations.idempotency_key` UNIQUE | FR-EXBOT-070 |
| Unconditional repayment | LP-portion USDC cannot be blocked or reversed by hedge close outcome | BR-EXBOT-006 |
| ⚠️ BigDecimal | Not stated in UC for `closeShortReduceOnlyIoc` cloid computation | — |
| ⚠️ HL weight budget | 3 HL API calls per close cycle; weight impact not calculated in UC | NFR-EXBOT-004 |
| ⚠️ DLQ policy | Not defined for `user_redeem` despite being SLA-bound | — |

---

## 10. Open Questions & Dependencies

### 10.1 Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | NV-3; OQ-EXBOT-02 | INV-STOP §19.5 path for stop cancel during close (size=0) — path (a) or (b)? | Blocks step 10 test | Open |
| Q2 | H | OQ-EXBOT-08 | BnzaExVault final ABI and contract address (Base + Optimism)? | Blocks all on-chain redeem tests | Open |
| Q3 | H | uc-user-redeem.md §3 step 7 vs spec FR-EXBOT-073 | `close_operations` state machine mismatch — UC uses `lp_closed→funds_returned`; spec uses `requested→hedge_close_pending→...→done`. Which is canonical? | Tester cannot write state machine AC | Open |
| Q4 | H | uc-user-redeem.md §3 | SLA 5-min timer: when does the clock start? How is breach detected (polling? deadline worker?) | AC-02 cannot be tested without mechanism | Open |
| Q5 | M | uc-user-redeem.md §3 step 8 | `UserLockDO.release` absent from main flow — is it called? In `finally` block? | Lock cleanup unverifiable | Open |
| Q6 | M | uc-user-redeem.md §3 step 13 | HL-portion USDC send mechanism — direct transfer, via which wallet/account? | AC for HL-portion delivery cannot be written | Open |
| Q7 | M | uc-user-redeem.md §2 Preconditions | Does same flow apply for `paused` and `safe_mode` bots? Any state-specific behavior? | Test matrix incomplete | Open |
| Q8 | L | uc-user-redeem.md §4 | DLQ policy for `user_redeem` queue? | Queue reliability tests undefined | Open |

### 10.2 Dependencies

| Dependency | Notes |
|---|---|
| NV-3 (OQ-EXBOT-02) | INV-STOP path for stop cancel |
| OQ-EXBOT-08 | BnzaExVault ABI deployment on Base + OP |
| `UC-EXBOT-bot-start` | Provides bot in active state with LP NFT and HL stop |

---

## 11. Change Log

| Version | Date | Author | Summary |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read (run-20260617-110000-udemysen) | Initial first-audit |

---

## Audit Summary

### Score Breakdown

| # | Knowledge Area | Max | Score | Status |
|---|---|---|---|---|
| 1 | Feature Identity | 5 | 5 | ✅ |
| 2 | Objective & Scope | 5 | 3 | ⚠️ |
| 3 | Actors & User Roles | 10 | 10 | ✅ |
| 4 | Preconditions & Postconditions | 10 | 7 | ⚠️ |
| 5 | API/Queue/State Interface | 15 | 8 | ⚠️ AUTO-CAP |
| 6 | System State Model | 20 | 11 | ⚠️ |
| 7 | Functional Logic | 20 | 13 | ⚠️ |
| 8 | Integration Analysis | 20 | 12 | ⚠️ |
| 9 | Acceptance Criteria | 20 | 13 | ⚠️ |
| 10 | NFRs | 5 | 3 | ⚠️ |
| **TOTAL** | | **130** | **85** | |

**Raw: 85/130 → Final: 65.4/100 → ❌ NOT READY**

### Blockers
- **B1** — NV-3: INV-STOP stop cancel path unconfirmed (step 10)
- **B2** — OQ-EXBOT-08: BnzaExVault ABI + contract address not deployed

### Strengths
- LP-portion unconditional guarantee (BR-EXBOT-006) is explicit and testable on-chain
- `queue_idempotency` + `close_operations.idempotency_key` UNIQUE — double settlement prevention clear
- SLA 5-min requirement explicitly stated (NFR-EXBOT-003)
- 3 well-formed Gherkin ACs cover happy path, SLA breach, and HL fail

### Recommendation
DO NOT begin test design. Resolve B1 (NV-3) + B2 (OQ-EXBOT-08) first. Also align `close_operations` state machine between UC and spec before writing state transition tests.

### 📋 Unified Gap & Question Report

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | NV-3; OQ-EXBOT-02 | INV-STOP §19.5 path for stop cancel (size=0) — path (a) or (b)? | Blocks step 10 stop-cancel test | Open |
| Q2 | H | OQ-EXBOT-08 | BnzaExVault final ABI and contract address (Base + OP)? | Blocks all on-chain redeem tests | Open |
| Q3 | H | uc-user-redeem.md §3 step 7 vs spec FR-EXBOT-073 | `close_operations` state machine mismatch — UC vs spec — which is canonical? | State transition AC cannot be written | Open |
| Q4 | H | uc-user-redeem.md §3 | SLA 5-min timer mechanism — when does clock start, how is breach detected? | AC-02 requires mechanism to test | Open |
| Q5 | M | uc-user-redeem.md §3 step 8 | `UserLockDO.release` absent from main flow — is it in `finally` block? | Lock cleanup unverifiable | Open |
| Q6 | M | uc-user-redeem.md §3 step 13 | HL-portion USDC send mechanism — which wallet/account? | HL-portion AC cannot be written | Open |
| Q7 | M | uc-user-redeem.md §2 Preconditions | Same flow for `paused` and `safe_mode` bots? Any state-specific differences? | Test matrix incomplete | Open |
| Q8 | L | uc-user-redeem.md §4 | DLQ policy for `user_redeem` queue? | Queue-failure tests undefined | Open |
