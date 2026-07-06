---
title: "UC Readiness Review — UC-EXBOT-user-redeem (User-Initiated Redemption)"
date_created: 2026-07-04
author: QC UC Read ExBot Agent
version: v3
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-user-redeem.md (updated 2026-07-04)
prior_report: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260703_v2.md
---

# UC Readiness Review — UC-EXBOT-user-redeem v3

## Feature Brief

**UC-EXBOT-user-redeem** covers the investor-initiated redemption flow for the BNZA ExBot managed LP-hedge bot. It is an LP-first, on-chain-guaranteed close: the investor calls `BnzaExVault.redeem(tokenId)` directly on-chain, which instantly liquidates the LP and returns the LP-portion USDC in the same transaction. The off-chain Redeem Worker then closes the HL short hedge independently (SLA: 5 min). The HL-portion USDC is sent to the investor via the `RedemptionQueue` ledger after hedge close. If hedge close fails (after 3 retries or reconcile mismatch), the bot enters `residual_hl_liability` state and admin is notified via E-EXBOT-024. The LP-portion repayment is unconditional and never reversed.

**Change in this version (2026-07-04):** BA replaced `UserLockDO` with `User Lock (Redis Redlock via ElastiCache)` per `FR-EXBOT-092`. This resolves the terminology mismatch that was the core of issue I-03, but the open behavior question (acquired=false → re-queue vs spin-wait) and the missing F-04 diagram participant are now answered by FR-EXBOT-026 and FR-EXBOT-092.

---

## Reference Code Glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case ID — ExBot module | usecases/index.md |
| FR-EXBOT-* | Functional Requirement — ExBot SRS spec | srs/spec.md |
| BR-EXBOT-* | Business Rule — ExBot module | srs/spec.md §BR section |
| E-EXBOT-* | Error/Alert message code — ExBot | backbone/message-list.md |
| SLA | Service Level Agreement — time bound guarantee for async operations | industry term |
| HL | Hyperliquid — external perpetual DEX used for delta-hedge short position | proper noun |
| LP | Liquidity Provider — Uniswap V3 position managed by BnzaExVault | industry term |
| IOC | Immediate-or-Cancel — HL order type used for hedge close | industry term |
| Redlock | Redis Redlock distributed mutex algorithm — prevents concurrent HL mutations per user | industry term |
| ElastiCache | AWS ElastiCache Redis — shared Redis cluster for rate limiter, UserLock, pool slot0 cache | proper noun |
| SQS | AWS Simple Queue Service — message queue replacing Cloudflare Queue | proper noun |

---

## §0 Scope & Linked Artifacts

| Item | Value |
|---|---|
| UC ID | UC-EXBOT-user-redeem |
| Linked User Story | US-EXBOT-004 |
| FR Trace | FR-EXBOT-070 |
| SRS Baseline | srs/spec.md, srs/states.md, srs/flows.md, srs/erd.md (as of 2026-07-04) |
| Prior audit | UC-EXBOT-user-redeem_user-redeem_audited_20260703_v2.md (Conditionally Ready, 81/100) |

---

## §1 Actors

| Actor | Role |
|---|---|
| USDC Investor | Primary — initiates redemption on-chain via `BnzaExVault.redeem(tokenId)` |
| BnzaExVault (on-chain) | LP liquidation + LP-portion USDC return (same tx) + emits `RedemptionEvent` |
| Redeem Event Watcher | Detects on-chain `RedemptionEvent`; enqueues to `user_redeem` queue |
| Redeem Worker (AWS Lambda) | Processes close: lock → HL hedge close → stop cancel → reconcile → HL-portion send |
| Hyperliquid | External perp DEX — target of `closeShortReduceOnlyIoc` and stop cancel |
| Aurora PostgreSQL | Off-chain state store: `close_operations`, `bots`, `queue_idempotency` |
| ElastiCache Redis | Provides Redis Redlock mutex (UserLock) per user |

---

## §2 Preconditions

- Bot `status='active'` (or paused/safe_mode — user may redeem from any non-closed state)
- Investor holds LP NFT redemption rights via BnzaExVault

**Note — I-N1 (Open):** UC §2 specifies "any non-closed state" but states.md State Registry does not explicitly list which states permit a close request beyond `active→lp_closing`. States `hedge_stopped_cooldown`, `lp_rebalancing`, and `error` are not confirmed in states.md as allowing user_redeem initiation. BA update (2026-07-04) did not address this gap.

---

## §3 Main Success Scenario

| Step | Action | Actor | State/Data Effect |
|---|---|---|---|
| 1 | Investor calls `BnzaExVault.redeem(tokenId)` on-chain | Investor | On-chain tx submitted |
| 2 | BnzaExVault liquidates LP (decreaseLiquidity 100% + collect + swap to USDC) | BnzaExVault | LP position closed on-chain |
| 3 | LP-portion USDC transferred to investor wallet in same tx (on-chain guarantee) | BnzaExVault | BR-EXBOT-006 enforced |
| 4 | `RedemptionEvent(botId, redeemTxHash, userAddress)` emitted | BnzaExVault | Event on-chain |
| 5 | Redeem Event Watcher detects event; enqueues to `user_redeem` queue (highest priority) | Event Watcher | Message in SQS FIFO queue |
| 6 | Redeem Worker inserts `message_id` into `queue_idempotency` (started); UNIQUE conflict → skip | Redeem Worker | Idempotency check |
| 7 | Redeem Worker creates `close_operations` row: insert (kind='user_redeem', state='requested') → update state='lp_closed' → update state='funds_returned' | Redeem Worker | DB: close_operations row; 3 transitions confirmed on-chain |
| 8 | Redeem Worker acquires User Lock (Redis Redlock via ElastiCache) lease for this user | Redeem Worker | Distributed mutex acquired; FR-EXBOT-092 |
| 9 | Redeem Worker calls HL full close (`closeShortReduceOnlyIoc`, cloid) — retries up to 3 times on reject/timeout before escalating | Redeem Worker | HL order submitted; FR-EXBOT-022 (deterministic cloid) |
| 10 | Cancels existing stop via `§19.5 replaceStopProtected` with size=0 | Redeem Worker | Stop cancelled via INV-STOP protocol |
| 11 | Reconcile: verify HL position size = 0 | Redeem Worker | FR-EXBOT-025 |
| 12 | Update `close_operations.state='hedge_closed'` | Redeem Worker | DB update |
| 13 | Send HL-portion USDC to investor (tracked in `RedemptionQueue` ledger) | Redeem Worker | I-02: mechanism unspecified |
| 14 | Update `close_operations.state='done'`; `bots.lifecycle_state='closed'` | Redeem Worker | Terminal state |
| 15 | Update `queue_idempotency.state='succeeded'` | Redeem Worker | Idempotency finalized |

**Gap — Missing `hedge_close_pending` transition:** states.md close_operations table confirms `hedge_close_pending` is a valid state for user_redeem (step between `funds_returned` and `hedge_closed`). UC main flow steps 7–12 skip from `funds_returned` directly to `hedge_closed` without setting `hedge_close_pending`. This is a missing state transition — tester cannot know when the state is `hedge_close_pending` during normal flow.

---

## §4 Alternate Flows

| Flow | Trigger | System Behavior |
|---|---|---|
| A1 — SLA Breach | Hedge not closed within 5 min from event detection | Admin alert: "user_redeem SLA breached for bot {id}"; LP-portion repayment NOT reverted (E-EXBOT-010) |
| A2 — HL Close Fails | 3 retries exhausted OR reconcile mismatch (HL position ≠ 0) | `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; `bots.status='error'`; admin notified (E-EXBOT-024); SAFE_MODE does NOT apply; LP-portion NOT reversed |
| A3 — Duplicate Message | `queue_idempotency` UNIQUE conflict at step 6 | Immediate return — no duplicate processing |

---

## §5 Postconditions

**Happy path:**
- `bots.lifecycle_state='closed'`
- `close_operations.state='done'`
- LP-portion USDC in investor wallet (on-chain, unconditional from step 3)
- HL-portion USDC sent post-hedge-close via RedemptionQueue ledger

**A2 path:**
- `bots.lifecycle_state='error'`, `bots.status='error'`
- `close_operations.state='residual_hl_liability'`
- LP-portion USDC in investor wallet (on-chain, not reversed)
- Admin notified (E-EXBOT-024); manual HL position close required


---

## §6 Business Rules

| Code | Verbatim | Enforcement Point |
|---|---|---|
| BR-EXBOT-006 | LP repayment unconditional — never blocked by hedge close failure | BnzaExVault (on-chain, step 2–3); A2 explicitly states LP-portion NOT reversed |

---

## §7 FR Trace

| FR | Relevance |
|---|---|
| FR-EXBOT-070 | Two close systems (user_redeem + bot_safe_close) via close_operations ledger |
| FR-EXBOT-022 | Deterministic cloid for closeShortReduceOnlyIoc |
| FR-EXBOT-024 | Cloid formula: `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` |
| FR-EXBOT-025 | Post-order reconcile: verify HL position size = 0 |
| FR-EXBOT-026 | User Lock (Redis Redlock): acquire before any HL mutation; acquired=false → re-queue with delay |
| FR-EXBOT-092 | Redis Redlock interface: `acquire`, `extend`, `release`; TTL=90s; idempotencyKey pattern |

---

## §F.1 Function/Operation Inventory

| Function | Trigger | Input | Output | Source |
|---|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` | Investor on-chain call | tokenId | LP liquidated + LP-portion USDC to investor (same tx) + RedemptionEvent emitted | UC §3 step 1–4 |
| Redeem Event Watcher enqueue | RedemptionEvent detected | botId, redeemTxHash, userAddress | Message in user_redeem queue | UC §3 step 5 |
| queue_idempotency check | Worker receives message | message_id | Idempotency insert or skip | UC §3 step 6 |
| close_operations row create | Worker starts processing | kind='user_redeem' | Row inserted: state='requested'→'lp_closed'→'funds_returned' | UC §3 step 7 |
| UserLock acquire (Redlock) | Before HL mutation | userId, TTL=90s, holderToken | acquired=true \| false | UC §3 step 8; FR-EXBOT-026; FR-EXBOT-092 |
| `closeShortReduceOnlyIoc` (cloid) | After lock acquired | botId, full close target=0 | HL short position closed; up to 3 retries | UC §3 step 9; FR-EXBOT-022 |
| `replaceStopProtected(size=0)` | After hedge close attempt | stop cloid | Stop order cancelled | UC §3 step 10 |
| reconcilePosition | After close + cancel | HL position query | Actual size = 0 confirmed | UC §3 step 11; FR-EXBOT-025 |
| close_operations state update | After reconcile | state='hedge_closed' | DB update | UC §3 step 12 |
| HL-portion USDC send | After hedge_closed | RedemptionQueue ledger | HL-portion USDC to investor | UC §3 step 13; I-02 open |
| close_operations + bots update | After HL-portion send | state='done', lifecycle_state='closed' | Terminal state | UC §3 step 14 |
| queue_idempotency finalize | End of processing | state='succeeded' | Idempotency complete | UC §3 step 15 |

---

## §F.2 States, Preconditions, Business Rules per Function

| Function | Pre-state | Post-state (happy) | Post-state (A2) | Business Rule | Message |
|---|---|---|---|---|---|
| BnzaExVault.redeem | Bot non-closed (active/paused/safe_mode per UC §2) | LP liquidated on-chain | — | BR-EXBOT-006 | — |
| close_operations create | — | requested→lp_closed→funds_returned | — | — | — |
| UserLock acquire | No lock held by other caller | Lock held by this Worker | — | FR-EXBOT-026: acquired=false → re-queue with delay | — |
| closeShortReduceOnlyIoc | funds_returned; lock held | hedge_close_pending (implicit)→hedge_closed | residual_hl_liability after 3 retries | FR-EXBOT-022 (cloid) | E-EXBOT-024 on failure |
| HL-portion USDC send | hedge_closed | done | — | — | — |
| A1 SLA | hedge not closed within 5 min | — | Admin alert | — | E-EXBOT-010 |
| A2 hedge close fail | 3 retries or reconcile mismatch | — | residual_hl_liability; error | BR-EXBOT-006 (LP not reversed) | E-EXBOT-024 |

---

## §F.3 Flow Paths

### Happy Path (F-04 alignment)
Investor redeem (on-chain) → LP liquidated + LP-portion returned in same tx → RedemptionEvent emitted → queue enqueue (highest priority) → Worker: idempotency check → close_operations (requested→lp_closed→funds_returned) → UserLock acquire (Redlock) → closeShortReduceOnlyIoc (3 retry max) → replaceStopProtected(size=0) → reconcile (size=0) → close_operations hedge_closed → HL-portion USDC to investor → close_operations done; bots.lifecycle_state='closed' → idempotency succeeded

### A1 (SLA Breach)
Normal flow proceeds — admin alert fires if hedge not closed within 5 min from detection. LP-portion already returned. Flow does not branch at A1; it is a parallel monitoring alert.

### A2 (Hedge Close Fails)
close_operations: funds_returned → [closeShortReduceOnlyIoc fails ×3 OR reconcile mismatch] → residual_hl_liability; bots.lifecycle_state='error'; bots.status='error'; E-EXBOT-024 admin alert. LP-portion NOT reversed.

### A3 (Duplicate Message)
queue_idempotency UNIQUE conflict at step 6 → immediate return; no duplicate close_operations row.

---

## §F.4 Cross-Function / Integration Effects

| Integration Point | Effect | Source |
|---|---|---|
| BnzaExVault on-chain → off-chain worker | Redeem tx hash used as idempotency anchor; RedemptionEvent triggers queue | UC §3 step 4–5 |
| close_operations ↔ bots | close_operations.state='done' → bots.lifecycle_state='closed'; A2 → bots.lifecycle_state='error' | UC §5 |
| UserLock (Redlock) ↔ HL mutation | Lock must be held before any HL call; released in finally block | FR-EXBOT-026; FR-EXBOT-092 |
| queue_idempotency ↔ worker | UNIQUE constraint prevents double settlement; succeeded on happy path | UC §3 step 6/15 |
| close_operations.idempotency_key UNIQUE | Prevents duplicate close_operations row (FR-EXBOT-070 AC) | FR-EXBOT-070 |
| close_operations.residual_amount | Stores outstanding HL liability amount on A2 | ERD close_operations.residual_amount TEXT |

---

## §F.5 Acceptance Criteria Candidates

| AC | Source | Status |
|---|---|---|
| LP-portion USDC returned to investor in same on-chain tx regardless of hedge outcome | BR-EXBOT-006; UC §3 step 3 | Confirmed |
| close_operations transitions: requested→lp_closed→funds_returned→[hedge_close_pending]→hedge_closed→done | states.md; UC §3 step 7–14 | Partial — hedge_close_pending missing from UC main flow |
| Duplicate message delivery results in no second close_operations row | queue_idempotency UNIQUE; UC A3 | Confirmed |
| A2: bots.lifecycle_state='error', bots.status='error'; E-EXBOT-024 admin alert | UC §5 A2; I-06 answer | Confirmed |
| A2: LP-portion NOT reversed | BR-EXBOT-006; UC A2 | Confirmed |
| closeShortReduceOnlyIoc retries ≤ 3 before escalating | UC §3 step 9; I-11 answer | Confirmed |
| UserLock: acquired=false → re-queue with delay (not spin-wait) | FR-EXBOT-026; FR-EXBOT-092 | Confirmed (FR-EXBOT-026 text) |
| SAFE_MODE does NOT apply on A2 | UC A2; I-08 answer | Confirmed |


---

## §10.1 Issue Register

| Issue ID | Type | Severity | Affected Area | Source Trace | Finding | Impact on Tester | Suggested Fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-02 | MISSING_INFO | High | §3 step 13; §F.1 | UC step 13 "Send HL-portion USDC to investor (tracked in RedemptionQueue ledger)"; flows.md F-04 line 168 | The mechanism by which the Redeem Worker sends HL-portion USDC to the investor remains unspecified: (a) who computes the HL-portion amount (total USDC from closeShortReduceOnlyIoc minus fees?); (b) who executes the on-chain transfer (Worker directly or via Operator Facade?); (c) is the tx hash stored in close_operations? F-04 diagram shows `UREW->>VAULT: send HL-portion USDC to user (RedemptionQueue ledger)` but does not show the payment mechanism. | Tester cannot verify HL-portion amount correctness or trace the on-chain transfer for step 13. | BA to define: HL-portion computation formula, executing actor, and whether close_operations stores the transfer tx hash. | Open — pending AWS arc update |
| I-03 | MISSING_INFO | Medium | §3 step 8; FR-EXBOT-026; flows.md F-04 | UC step 8 now uses correct terminology (Redis Redlock). FR-EXBOT-026 text confirmed: "if acquired=false, the worker re-queues the message with a delay." F-04 diagram still has no UserLock/Redlock participant. | (a) Terminology resolved — Redlock now matches FR-EXBOT-092. (b) acquired=false behavior resolved — re-queue with delay per FR-EXBOT-026. (c) REMAINING GAP: flows.md F-04 sequence diagram does not show Redlock acquire/release steps, while F-02 (hedge-sync) does show the lock. Testers reading F-04 cannot trace lock contention scenario. | BA to update F-04 sequence diagram to add Redlock participant (acquire before HL call, release in finally block). | Partially Resolved — acquired=false behavior confirmed via FR-EXBOT-026; F-04 diagram still missing Redlock |
| I-N1 | MISSING_INFO | Medium | UC §2 Preconditions; states.md State Registry | UC §2 v2 (2026-07-03): "Bot status='active' (or paused/safe_mode — user may redeem from any non-closed state)". states.md State Registry does not list which states permit a close request; only the `active→lp_closing` transition is shown in the state diagram. | BA update 2026-07-04 did not address this gap. Tester cannot confirm: (a) hedge_stopped_cooldown allows redeem; (b) lp_rebalancing allows redeem; (c) error state allows redeem. | BA to update states.md State Registry to mark which lifecycle_state values allow user_redeem initiation, or add a transition `paused/safe_mode/hedge_stopped_cooldown→lp_closing` to the state diagram. | Open — unaddressed by 2026-07-04 update |
| I-N2 | UNCLEAR_INFO | Low | UC §3 step 9 | UC step 9: "retries up to 3 times on reject/timeout before escalating". Retry strategy details not defined: (a) same Lambda invocation vs re-queue; (b) backoff delay. | Minor — retry count (3) is confirmed. Retry mechanism details needed only for negative/boundary test cases on retry behavior. | BA to specify: in-invocation retry (synchronous) or message re-queue with delay. If re-queue with delay, confirm total max time for 3 retries stays within SLA. | Open — Low priority |
| I-N3 | MISSING_INFO | Medium | UC §3 step 7–12; states.md close_operations | states.md close_operations table: `hedge_close_pending` is listed as a valid state for user_redeem (✓ in user_redeem column). UC main flow steps 7–12 do not include a transition to `hedge_close_pending` — it jumps from `funds_returned` (step 7) directly to `hedge_closed` (step 12). The state exists in the canonical state table but is absent from the UC scenario description. | Tester cannot design a test case for the `hedge_close_pending` state in user_redeem because the UC does not say when the close_operations row enters this state during the happy path. The state diagram suggests it is set before/during the hedge close attempt (steps 9–11), but the UC is silent. | BA to clarify: when does close_operations transition to `hedge_close_pending` in user_redeem? Add this transition to UC §3 (e.g., after step 7, before step 9: "update close_operations.state='hedge_close_pending'"). | Open — New issue found in v3 re-audit |

---

## §10.2 Dependencies

| Dependency | Status | Impact |
|---|---|---|
| AWS arc migration: HL-portion transfer mechanism | Outdated — pending update | Blocks I-02 |
| states.md State Registry — allowed initiating states for user_redeem | Not updated | Blocks I-N1 |
| flows.md F-04 sequence diagram — Redlock participant | Not updated | Open I-03 (minor) |
| close_operations hedge_close_pending in UC main flow | Missing | Open I-N3 |

---

## §10.3 Audit Summary

### Scoring Table

| Area | Max | v1 Score | v2 Score | v3 Score | Delta v2→v3 | Notes |
|---|---|---|---|---|---|---|
| 1. Completeness of main flow | 25 | 14 | 16 | 18 | +2 | I-N3 new gap (hedge_close_pending missing): −2; I-03 lock behavior resolved: +2; net 0; arc migration label updated on I-03: +1; Redlock terminology fix: +1 |
| 2. Alternate / exception flow coverage | 20 | 12 | 16 | 16 | 0 | A1/A2/A3 all documented. No change. |
| 3. Business rule traceability | 15 | 12 | 15 | 15 | 0 | BR-EXBOT-006 fully traced. No new rules. |
| 4. Cross-source consistency (UC vs SRS) | 20 | 12 | 13 | 14 | +1 | Redlock terminology now consistent with FR-EXBOT-092; F-04 diagram still outdated (I-03) |
| 5. Testability / clarity | 20 | 14 | 18 | 17 | −1 | I-N3 (new): hedge_close_pending transition missing reduces testability for state test cases |
| **Total** | **100** | **64→67*** | **81** | **80** | **−1** | |

*v1 score corrected: Blocker auto-cap removed when I-01 resolved; recalculated 67.

**Score: 80/100 — Conditionally Ready** (threshold: ≥80 Conditionally Ready, ≥90 Ready)

### Verdict: CONDITIONALLY READY (80/100)

**Positive changes since v2:**
- UserLockDO → Redis Redlock (FR-EXBOT-092) terminology now consistent with SRS.
- I-03 acquired=false behavior confirmed via FR-EXBOT-026 — no longer a blocker.
- Area 4 improved: UC-to-SRS consistency better on the locking mechanism.

**Remaining blockers / high issues:**
- **I-02 (High):** HL-portion USDC transfer mechanism still unspecified. Tester cannot verify step 13. Pending AWS arc update.
- **I-N3 (Medium — New):** `close_operations.hedge_close_pending` state is confirmed in states.md for user_redeem but absent from UC §3 main flow. Tester cannot design state-transition test cases for this state.

**Open medium issues:**
- **I-N1 (Medium):** Precondition "any non-closed state" not reflected in states.md — specific states (hedge_stopped_cooldown, lp_rebalancing, error) not confirmed.
- **I-03 (Medium — Partially Resolved):** F-04 diagram missing Redlock participant. Minor — behavior is confirmed in FR-EXBOT-026.

**Open low issues:**
- **I-N2 (Low):** retry strategy details (in-invocation vs re-queue, backoff) not specified.

**Recommendation:** Proceed to test scenario design for all confirmed flows (happy path + A2 + A3). Hold test case design for step 13 (HL-portion) until I-02 resolved. Add `hedge_close_pending` transition test cases only after BA confirms UC §3 (I-N3 resolved). I-N1 does not block happy-path design but blocks boundary/negative test cases on allowed pre-states.

---

*Report generated by: QC UC Read ExBot Agent | Device: MTS-978 | Run ID: run-20260704-000019-trinhbui*

