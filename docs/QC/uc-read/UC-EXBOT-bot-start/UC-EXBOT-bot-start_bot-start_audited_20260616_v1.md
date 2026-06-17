# UC Readiness Review — UC-EXBOT-bot-start
**Functional / Black-box Test Readiness**

---

## Feature Brief

UC-EXBOT-bot-start covers the full initialization flow for an ExBot: a USDC Investor triggers a start via the POOL UI, which routes through the OPERATOR Facade to the ExBot Worker (via CF service binding — BR-EXBOT-010). The Worker runs 5 sequential preflight checks (one-bot policy, HL margin ≥ 2×, agent key approved, builder fee confirmed, LP mint simulation), creates a bot record, mints an LP NFT via BnzaExVault.vaultMint(), opens a delta-only HL short (targetShortEth = lpEthAmount × 0.70), performs post-order reconcile to extract entry/liquidation prices, computes a BigDecimal stop trigger price (stopSafetyFactor=0.70 Phase A), places a reduce-only stop market on HL, and transitions the bot to `lifecycle_state='active'`. The bot cannot reach `active` without a confirmed stop (FR-EXBOT-031).

Key constraints: 1 active ExBot per user Phase A (BR-EXBOT-001); ExBot Worker isolated from OPERATOR via CF service binding (BR-EXBOT-010); all financial computations must use BigDecimal (FR-EXBOT-020); `wethIndex` per chain (Base/OP) must be verified and stored (FR-EXBOT-004 — NV-12 pending); HL stop behavior blocked on NV-1/NV-3.

---

## Readiness Verdict

| Overall Score | Verdict |
|---|---|
| **70.8 / 100** | ⚠️ **CONDITIONALLY READY** |

---

## 0. Document Metadata

| UC-ID | Feature Name | Version | Status |
|---|---|---|---|
| UC-EXBOT-bot-start | Start ExBot | Draft (2026-06-12) | Draft |

| Author / BA | Approved By | Date Created | Audit Date |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-16 |

**Input artefacts:**
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-bot-start.md`
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-001.md`
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/frd.md` (FR-EXBOT-001/002/020/021/030/031)
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/spec.md` (FR-EXBOT-001/002/003/004/025/030/031 + BR table)

---

## 1. Objective & Scope ⚠️ Partial

### 1.1 Objective

Enable a USDC Investor to start a new ExBot that automatically manages a delta-hedged LP position on USDC/ETH: earns Uniswap V3 LP fees while the HL short leg suppresses directional ETH loss. The bot must complete a full preflight → LP mint → hedge open → stop placement initialization sequence before becoming active.

### 1.2 In Scope

- 5-step preflight checks (one-bot policy, margin, agent key, builder fee, LP mint simulation)
- Bot record creation and lifecycle state machine initialization (idle → active)
- LP NFT minting via BnzaExVault.vaultMint()
- HL short open (IOC, delta-only, hedgeRatio=0.70)
- Post-order reconcile (entry_price, liquidation_price, effective_leverage)
- Stop trigger price computation (BigDecimal, stopSafetyFactor=0.70)
- Reduce-only stop market placement on HL
- D1 state writes: bots, positions, hedge_legs tables

### 1.3 Out of Scope

- Bot pause/resume (FR-EXBOT-003 / FR-EXBOT-005)
- Light-check and hedge-sync (downstream, triggered after bot is active)
- User redeem / bot safe close
- Multi-bot per user (Phase B+)
- Phase B+ behaviors (manual reset, Phase B stopSafetyFactor)

---

## 2. Actors & Stakeholders ⚠️ Partial

| Actor | Type | Role & Permissions |
|---|---|---|
| USDC Investor (ACT-01) | Primary | Submits start request via POOL UI; must have active HL account, approved agent key, sufficient margin |
| OPERATOR Facade | System | Receives `POST /api/exbot/start`, forwards to ExBot Worker via CF service binding; must NOT co-deploy with ExBot Worker (BR-EXBOT-010) |
| ExBot Worker | System | Executes all preflight checks, creates bot record, orchestrates LP mint + hedge open + stop placement; isolated CF Worker |
| BnzaExVault (Solidity) | System | Holds LP NFT custody; executes `vaultMint()`; emits `VaultMinted` event |
| Hyperliquid (HL) | External | Provides isolated margin account, IOC short order, stop market placement, post-order position data |

⚠️ Gap: ACT-ID not used in UC (just "USDC Investor"); no auth/permission detail for how POOL UI authenticates with OPERATOR; no explicit mention of which HL subaccount/vaultAddress is used.

---

## 3. Preconditions & Postconditions ⚠️ Partial

### 3.1 Preconditions

- User has no existing ExBot with `status IN ('active','paused','closing','safe_mode','error')` (BR-EXBOT-001)
- User's HL isolated margin balance ≥ required margin × 2.0 (required_margin = lpEthAmount × hedgeRatio × hlOraclePrice / leverage)
- User's HL agent key `approval_status='approved'` AND not expired
- Builder fee (5bps) confirmed on HL
- LP mint simulation passes (slippage within tolerance)

⚠️ Gap: No NV gate precondition stated (NV-1/NV-3 for stop system, NV-12 for wethIndex); no precondition for system availability (OPERATOR, ExBot Worker, HL API, BnzaExVault reachable).

### 3.2 Postconditions

| After completing... | System state / Postcondition |
|---|---|
| Successful bot start | `bots.lifecycle_state='active'`, `bots.status='active'` |
| Successful bot start | LP NFT held by BnzaExVault (`positions.custodian='vault'`); `positions.tokenId`, `tickLower`, `tickUpper`, `wethIndex` populated |
| Successful bot start | HL short open with reduce-only stop placed; `hedge_legs.stop_price`, `stop_cloid`, `stop_order_id`, `entry_price`, `effective_leverage` populated |
| Preflight failure (any check) | No bot record created; specific error returned to POOL UI |
| LP mint failure (A4) | Bot enters `error` state; funds returned *(mechanism unspecified — ⚠️ Q5)* |

⚠️ Gap: No failure postcondition for reconcile fail (Step 8) or stop placement fail (Step 10).

---

## 4. API / Queue / State Interface Inventory ⚠️ Partial

> ⚠️ **NOTE:** uc-bot-start.md has NO explicit §2 "API/Interface" section. Interface entries below are reconstructed from §3 Main Scenario + §5 Postconditions. This is the primary source of auto-cap on KA #5.

**REST Endpoints:**

| # | Path | Trigger | Request Fields | Success Response | Error Codes + Messages |
|---|---|---|---|---|---|
| 1 | `POST /api/exbot/start` | USDC Investor submits via POOL UI | ⚠️ Not defined in UC (user_id implicit from auth session; no explicit body schema) | ⚠️ Not defined (inferred: bot status, botId, LP range, hedge size) | See preflight error messages below |

**External Calls (not queue-based):**

| # | Call | Trigger | Parameters | Response | Error Handling |
|---|---|---|---|---|---|
| 2 | `BnzaExVault.vaultMint(...)` | Step 5 — after preflight pass | ⚠️ Not fully specified in UC | `VaultMinted` event with `tokenId` | A4: `error` state + return funds (mechanism unspecified) |
| 3 | HL short IOC order | Step 7 — after LP open | `targetShortEth = lpEthAmount × 0.70`; IOC type | Actual position: `entry_price`, `liquidation_price`, `effective_leverage` | ⚠️ No error flow defined for IOC partial fill or timeout |
| 4 | HL reduce-only stop market | Step 10 — after reconcile | `stop_trigger_px` (BigDecimal); reduce-only; stop market | `stop_order_id`, `stop_cloid` confirmed | ⚠️ No error flow defined for stop placement fail |

**D1 State Objects:**

| # | Table | Trigger | Key Fields Written | Notes |
|---|---|---|---|---|
| 5 | `bots` | Created at Step 4 | `lifecycle_state`, `status`, `user_id` | Transitions through 9 states to `active` |
| 6 | `positions` | Updated at Step 6 | `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'` | `wethIndex` NV-12 ⚠️ |
| 7 | `hedge_legs` | Updated at Steps 9-10 | `entry_price`, `liquidation_price`, `effective_leverage`, `stop_price`, `stop_cloid`, `stop_order_id`, `stop_size`, `stop_distance_pct` | Must not be written before reconcile confirms actual state |

**Queue Consumers:** N/A — bot-start does not produce or consume queues directly.

**Durable Objects:** N/A — bot-start does not use DOs directly (UserLockDO is used in hedge-sync, not bot-start).

---

## 5. System State Model ⚠️ Partial

**Lifecycle State Transitions:**

| From State | Trigger Event | Guard Condition | To State | On Guard Fail |
|---|---|---|---|---|
| `idle` | `POST /api/exbot/start` received | 5 preflight checks pass | `preflight` | Return specific error per failed check; no bot record created |
| `preflight` | Bot record created | — | `lp_opening` | — |
| `lp_opening` | `vaultMint()` called | — | `lp_opened` | A4: enter `error` state |
| `lp_opened` | LP NFT minted, D1 positions updated | — | `hedge_pre_open` | — |
| `hedge_pre_open` | HL IOC short submitted | — | `hedge_post_confirmed` (after reconcile) | ⚠️ No error flow defined |
| `hedge_post_confirmed` | Reconcile complete, D1 hedge_legs updated | Reconcile confirms actual size | `stop_placing` | ⚠️ No error flow defined |
| `stop_placing` | Stop market submitted | — | `stop_verified` | ⚠️ No error flow defined for stop fail |
| `stop_verified` | Stop placement confirmed on HL | FR-EXBOT-031: stop MUST be confirmed | `active` | Cannot reach `active` without confirmed stop |

⚠️ Gap: Error flows for `hedge_pre_open` → fail, `stop_placing` → fail not defined. D1 write atomicity for each transition not stated.

---

## 6. Functional Logic & Workflow Decomposition ⚠️ Partial

### 6.1 Bot Start Flow

**A. Main Flow (Happy Path)**

| Step | Actor | Action | System Response | Notes |
|---|---|---|---|---|
| 1 | USDC Investor | Submit start via POOL UI | — | Requires approved agent key, builder fee, sufficient margin |
| 2 | OPERATOR | Receive `POST /api/exbot/start`, forward to ExBot Worker | ExBot Worker invoked via CF service binding | BR-EXBOT-010: service binding ONLY, no co-deploy |
| 3 | ExBot Worker | Run 5 preflight checks in order | (a) one-bot → (b) margin → (c) agent key → (d) builder fee → (e) LP simulation | FR-EXBOT-001 (spec): query `bot_registry WHERE status IN ('active','paused','closing','safe_mode','error')`; FR-EXBOT-002 (frd): margin = `(lpEthAmount × hedgeRatio × hlOraclePrice) / leverage` |
| 4 | ExBot Worker | Create bot record | `bots.lifecycle_state='preflight'` | Atomic D1 write |
| 5 | ExBot Worker | Call `BnzaExVault.vaultMint(...)` | `VaultMinted` event with `tokenId` | A4: failure → `error` + return funds |
| 6 | ExBot Worker | Update D1 positions | `tokenId, tickLower, tickUpper, wethIndex, lifecycle_state='lp_opened'` | FR-EXBOT-021 (frd): `wethIndex` per chain; NV-12 ⚠️ |
| 7 | ExBot Worker | Open HL short IOC | `targetShortEth = lpEthAmount × 0.70` | FR-EXBOT-020 (frd): BigDecimal only; delta-only invariant |
| 8 | ExBot Worker | Post-order reconcile | Fetch actual HL position; extract `entry_price`, `liquidation_price`, `effective_leverage` | FR-EXBOT-023 (frd): success NOT recorded before reconcile |
| 9 | ExBot Worker | Update D1 hedge_legs; `lifecycle_state='hedge_post_confirmed'` | `entry_price`, `liquidation_price`, `effective_leverage` persisted | — |
| 10 | ExBot Worker | Compute `stop_trigger_px`; place reduce-only stop | `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)` | FR-EXBOT-030 (frd): BigDecimal; prefer HL `liquidationPx`; fallback `1/effective_leverage`; NV-1/NV-3 ⚠️ |
| 11 | ExBot Worker | Confirm stop; `lifecycle_state='stop_verified'` → `'active'` | `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size`, `stop_distance_pct` in `hedge_legs` | FR-EXBOT-031 (frd): bot CANNOT reach `active` without confirmed stop |
| 12 | ExBot Worker | Return response to POOL UI | Bot active; LP range + hedge size visible | — |

**B. Alternate & Error Flows**

| Flow | Trigger | Behavior |
|---|---|---|
| A1 — One-bot policy fail | `count > 0` in bot_registry (preflight check 1) | Reject: "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." (FR-EXBOT-001 verbatim) |
| A2 — Margin insufficient | HL margin < required × 2 (preflight check 2) | Block: "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." (FR-EXBOT-002 verbatim) |
| A3 — Agent key not approved | `approval_status != 'approved'` OR expired (check 3) | Block with message directing user to complete key approval ⚠️ exact message not specified |
| A4 — LP mint fails | `BnzaExVault.vaultMint()` failure (step 5) | Enter `error` state; return funds ⚠️ return mechanism not specified |
| A5 — Builder fee not confirmed | Check 4 fails | Block start ⚠️ error message not specified |
| A6 — LP mint simulation fails | Check 5 fails | Block start ⚠️ error message not specified |

**C. Business Rules (verbatim)**

| Rule ID | Verbatim Text | Source |
|---|---|---|
| BR-EXBOT-001 | "Phase A: 1 user = 1 active ExBot. `status IN ('active','paused','closing','safe_mode','error')` all count toward the limit." | spec.md BR table |
| BR-EXBOT-010 | "ExBot Worker (`apps/bnza-exbot/`) must not be co-deployed with OPERATOR (`apps/bnza-operator/`). They communicate via CF service binding only." | spec.md BR table |
| FR-EXBOT-001 | "The system shall enforce a maximum of one active ExBot per user in Phase A. Before creating a new bot, the system shall query `bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')`. If the count is greater than zero, the start request shall be rejected immediately with a specific error message." | spec.md FR-EXBOT-001 |
| FR-EXBOT-002 | "The system shall run five preflight checks in sequence: (1) one-bot policy check, (2) HL isolated margin balance ≥ required margin × 2.0, (3) HL agent key `approval_status='approved'` and `expires_at` not reached, (4) builder fee (5bps) confirmed on HL, (5) LP mint simulation passes. Any single failure blocks the start with a specific message." | spec.md FR-EXBOT-002 |
| FR-EXBOT-003 | "The initialization sequence is fixed: idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active. No step may be skipped." | spec.md FR-EXBOT-003 |
| FR-EXBOT-030 | "`stop_trigger_px = entry_price × (1 + stop_distance_pct)`; `liq_distance_pct = (liquidation_price − entry_price) / entry_price`; `stop_distance_pct = liq_distance_pct × stopSafetyFactor (0.70 Phase A)`. All stop price computations MUST use BigDecimal (never float)." | frd.md FR-EXBOT-030 |
| FR-EXBOT-031 | "The bot shall not transition to `stop_verified` until stop placement is confirmed. `hedge_legs.stop_price` is always populated when `lifecycle_state='active'`." | frd.md FR-EXBOT-031 |
| FR-EXBOT-004 | "The system shall support Base and Optimism from Phase 1. `wethIndex` (0 or 1, indicating whether WETH is token0 or token1 in the pool) shall be verified per chain and stored in `positions.weth_index` at LP open." | spec.md FR-EXBOT-004 |

---

## 7. Functional Integration Analysis ⚠️ Partial

| Trigger / Event | Downstream Effect | Consistency |
|---|---|---|
| `POST /api/exbot/start` → OPERATOR → ExBot Worker (CF service binding) | All preflight + lifecycle orchestration runs in ExBot Worker | BR-EXBOT-010 hard constraint: service binding ONLY; cannot be tested via direct HTTP to ExBot Worker |
| `BnzaExVault.vaultMint()` → D1 positions | `tokenId`, `tickLower`, `tickUpper`, `wethIndex` persisted; feeds lpEthAmount computation | NV-12 ⚠️: wrong `wethIndex` → wrong lpEthAmount → wrong targetShortEth → wrong stop price cascade |
| HL IOC short → reconcile → hedge_legs | `entry_price`, `liquidation_price`, `effective_leverage` → feeds stop_trigger_px | FR-EXBOT-023 (frd): success NOT recorded before reconcile confirms; IOC partial fill behavior not addressed in UC |
| stop_trigger_px computation → HL stop placement → hedge_legs | `stop_price`, `stop_cloid`, `stop_order_id` → guards `stop_verified` → `active` | NV-1/NV-3 ⚠️: HL stop system behavior unconfirmed; stop_verified state cannot be safely tested until NV-1/NV-3 pass |
| Bot reaches `active` → light-check scheduling starts | `next_light_check_at = now + 5min + jitter` set; Cron → bot-scan → light-check queue | UC-EXBOT-light-check is downstream; bot-start success is prerequisite |

---

## 8. Acceptance Criteria ⚠️ Partial

| AC # | Scenario | Given | When | Then |
|---|---|---|---|---|
| AC-01 | Happy path — all preflight pass, bot starts | Investor: no existing active/paused/closing/safe_mode/error ExBot; HL margin ≥ req×2; agent key approved+not expired; builder fee confirmed | Investor submits start via POOL UI | System creates bot with `lifecycle_state='preflight'`; progresses through full 9-step sequence to `active`; POOL UI shows "Active" with LP range and hedge size |
| AC-02 | One-bot policy blocks second start | Investor already has 1 ExBot with `status='active'` | Investor attempts to start second ExBot | Rejected: "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." No new bot record created |
| AC-03 | Insufficient HL margin blocks start | HL isolated margin = $300; required margin (incl. 2× buffer) = $700 | Investor submits start | Blocked: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit an additional $400 to HL." No bot record created |
| AC-04 | Agent key not approved blocks start | HL agent key `approval_status='pending'` | Investor submits start | Blocked with message indicating agent key must be approved ⚠️ exact message text not defined — see Q8 |
| AC-05 | Stop must be confirmed before `active` | Bot has reached `stop_placing` lifecycle state | Stop placement attempted | Bot CANNOT transition to `stop_verified` → `active` until stop is confirmed on HL (FR-EXBOT-031) |
| AC-06 | Stop price uses BigDecimal | Any bot-start flow | Stop trigger price is computed | `stop_trigger_px` computation uses BigDecimal only; no intermediate `Number()` conversion; formula: `entry_price × (1 + liq_distance_pct × 0.70)` |
| AC-07 | Lifecycle sequence is fixed — no step may be skipped | Any bot-start flow | Bot initialization proceeds | Sequence `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` followed exactly (FR-EXBOT-003) |
| AC-08 | Each preflight failure produces distinct error | Bot with each specific failure condition | Start request submitted | Each of 5 preflight checks produces a distinct, specific error message; no partial bot record left in D1 |
| AC-09 | Postconditions verified on success | Bot reaches `active` | — | `positions.custodian='vault'`; `bots.lifecycle_state='active'`; `bots.status='active'`; `hedge_legs.stop_price` populated; HL short open with reduce-only stop placed |
| AC-10 | wethIndex per chain [BLOCKED: NV-12] | Bot on Base vs bot on OP | LP mint succeeds | `positions.weth_index` populated with chain-specific verified value; LP ETH amount uses this index, not hardcoded assumption — **BLOCKED: NV-12 pending** |
| AC-11 | ExBot Worker not co-deployed with OPERATOR | Bot-start request flows through architecture | — | OPERATOR forwards to ExBot Worker via CF service binding ONLY (BR-EXBOT-010) |

---

## 9. Non-functional Requirements ⚠️ Partial

| Category | Requirement | Source |
|---|---|---|
| Performance | Hedge-sync latency ≤ 30s under normal conditions (relevant to post-start hedge operations) | NFR-EXBOT-002 (frd.md) |
| Rate Limit | HL API usage ≤ 800 weight/min (67% of 1,200/min hard limit) | NFR-EXBOT-004 (frd.md) |
| Dual-chain | Base + Optimism supported from Phase 1; wethIndex verified per chain | NFR-EXBOT-009 (frd.md) |
| Precision | All hedge/stop/margin computations must use BigDecimal; float/number arithmetic forbidden | FR-EXBOT-020/030 (frd.md) |
| Isolation | ExBot Worker must NOT be co-deployed with OPERATOR | BR-EXBOT-010 (spec.md) |
| Latency SLA | ⚠️ No end-to-end bot-start SLA defined in UC (only hedge-sync SLA exists) | Not defined |
| Security | ⚠️ No security NFR in UC for bot-start (agent key handling refs UC-EXBOT-agent-key) | Not defined |

---

## 10. Open Questions & Dependencies

### 10.1 Open Questions
*(See Q-Table in Audit Summary below for all Q1-Q13)*

### 10.2 Dependencies
- UC-EXBOT-agent-key — agent key must be approved before bot-start can pass preflight check 3
- NV-12 — wethIndex for Base+OP (blocks AC-10, LP amount chain)
- NV-1/NV-3 — HL stop system behavior (blocks Steps 10-11, stop_verified → active path)
- FR-EXBOT-004 (spec.md) — dual-chain support; absent from frd.md
- UC-EXBOT-light-check — downstream; starts once bot is active

---

## 11. Change Log

| Version | Date | Author | Summary |
|---|---|---|---|
| v1 | 2026-06-16 | qc-uc-read / run-20260616-210000-udemysen | First audit — uc-bot-start.md + us-001.md; restart fresh |

---

## Audit Summary

### Score Table

| # | Knowledge Area | Max | Score | Status |
|---|---|---|---|---|
| 1 | Feature Identity | 5 | 5 | ✅ |
| 2 | Objective & Scope | 5 | 4 | ⚠️ |
| 3 | Actors & Roles | 10 | 8 | ⚠️ |
| 4 | Preconditions & Postconditions | 10 | 8 | ⚠️ |
| 5 | API / Queue / State Interface Inventory | 15 | 8 | ⚠️ Auto-cap (UC §2 absent) |
| 6 | System State Model | 20 | 14 | ⚠️ |
| 7 | Functional Logic & Workflow Decomposition | 20 | 14 | ⚠️ |
| 8 | Functional Integration Analysis | 20 | 13 | ⚠️ |
| 9 | Acceptance Criteria | 20 | 15 | ⚠️ |
| 10 | Non-functional Requirements | 5 | 3 | ⚠️ |
| **Total** | | **130** | **92 → 70.8/100** | ⚠️ **CONDITIONALLY READY** |

### 📋 Q-Table (Unified Gap & Question Report)

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | High | uc-bot-start.md §3 | `POST /api/exbot/start` request body schema — what fields, types, constraints? | Tester cannot verify request validation without schema | Open |
| Q2 | High | uc-bot-start.md §3 | Success response schema from `POST /api/exbot/start` — fields, types? | Tester cannot verify happy path response | Open |
| Q3 | Medium | uc-bot-start.md §4 A5 | Exact error message when builder fee (5bps) not confirmed? | AC cannot be written as testable Given/When/Then without verbatim message | Open |
| Q4 | Medium | uc-bot-start.md §4 A6 | Exact error message when LP mint simulation fails (preflight check 5)? | Needed for negative path AC | Open |
| Q5 | Medium | uc-bot-start.md §4 A4 | "Return funds" on LP mint failure — which funds, via what mechanism, to where? | Without definition, recovery path cannot be tested | Open |
| Q6 | High | uc-bot-start.md §3 Step 8 | Error flow when post-order reconcile fails — what lifecycle state, is LP unwound? | No alternate flow defined; reconcile-fail test case cannot be written | Open |
| Q7 | High | uc-bot-start.md §3 Step 10 | Error flow when stop placement fails — what lifecycle state, is LP+hedge unwound? | No alternate flow defined; critical path to `active` state | Open |
| Q8 | Medium | uc-bot-start.md §4 A3 + us-001.md AC-4 | Exact error message when agent key not approved/expired? Both documents use vague wording. | AC-04 cannot be precisely tested | Open |
| Q9 | Medium | uc-bot-start.md §3 | Behavior if OPERATOR receives duplicate `POST /api/exbot/start` (idempotency)? | No idempotency mechanism described; duplicate submission could create two bot records | Open |
| Q10 | Low | frd.md §4 | FR-EXBOT-004 (dual-chain) is in spec.md but absent from frd.md §4 — intentional split? | Tester reading only frd.md misses a P0 requirement | Open |
| Q11 | Low | spec.md vs frd.md | Post-order reconcile is "FR-EXBOT-025" in spec.md vs "FR-EXBOT-023" in frd.md — which is canonical? | Traceability gap for downstream test case FR references | Open |
| Q12 (NV-12) | High | GAP-004; project-context-master Q-012 | `wethIndex` confirmed values for Base+OP? | Blocks AC-10, LP amount computation, stop price chain | Open |
| Q13 (NV-1/NV-3) | High | GAP-005; project-context-master Q-011 | HL stop system behavior + stop replacement protocol confirmed? | Blocks Steps 10-11, `stop_verified`→`active` transition, all stop ACs | Open |

### 🟢 What's Good

- **US-001 provides 4 solid Gherkin ACs** covering happy path, one-bot policy, margin, and agent key — well-structured, testable.
- **9-step lifecycle sequence is fully defined** with atomic state names; no ambiguity in the initialization path.
- **Business rule text is verbatim** in both frd.md and spec.md for the critical rules (one-bot, preflight, stop price formula, stop confirmation required).
- **BigDecimal constraint is explicit** for stop price computation — clear testability.
- **BR-EXBOT-010 (service binding isolation)** is stated clearly as an architectural constraint.

### 🧪 Testability Outlook

**Can test now:**
- AC-01 (happy path), AC-02 (one-bot), AC-03 (margin), AC-04 (agent key — with clarified message Q8), AC-05 (stop before active), AC-06 (BigDecimal), AC-07 (lifecycle sequence), AC-08 (distinct errors), AC-09 (postconditions), AC-11 (service binding)

**Cannot test (blocked):**
- AC-10 (wethIndex per chain) — blocked: NV-12
- Stop placement and stop_verified→active path — blocked: NV-1/NV-3
- Reconcile fail error flow (Step 8) — blocked: Q6
- Stop placement fail error flow (Step 10) — blocked: Q7
- Builder fee fail exact message — blocked: Q3
- LP mint sim fail exact message — blocked: Q4
- Return funds mechanism (A4) — blocked: Q5
- Duplicate start idempotency — blocked: Q9

### 📌 Summary & Recommendation

UC-EXBOT-bot-start has a well-defined happy path and one-bot policy enforcement, but suffers from two structural gaps: (1) **UC §2 (API/Interface section) is absent** — the `POST /api/exbot/start` request/response schema is completely unspecified, forcing testers to reverse-engineer from Step 3 narrative; (2) **error flows for the two most critical middle steps (reconcile fail at Step 8, stop placement fail at Step 10) are not defined**. Without these, QA cannot design negative tests for the lifecycle states `hedge_pre_open` through `stop_placing`.

The two NV blockers (NV-12 and NV-1/NV-3) affect the LP amount computation chain and the entire stop system, respectively. Until confirmed, ~3 ACs are untestable.

**Recommendation:** BA should (a) add a §2 API/Interface section to uc-bot-start.md with explicit request/response schema; (b) define error flows for Steps 8 and 10; (c) provide verbatim error messages for A3/A5/A6; (d) track NV-12/NV-1/NV-3 resolution. QA can begin test design for AC-01 through AC-03 and AC-05 through AC-09 and AC-11 immediately.


---
