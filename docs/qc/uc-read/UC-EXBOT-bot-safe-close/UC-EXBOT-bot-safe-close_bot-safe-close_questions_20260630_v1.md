# Question Backlog

> Generated: 2026-06-30
> Source: UC-EXBOT-bot-safe-close readiness review

---

## Open Questions

> **Policy:** Khong tu suy luan. Tat ca cau hoi can BA/Tech Lead xac nhan dua tren documents.

| ID | Uu tien | Ref | Question | Evidence in Docs | Why It Matters | Owner |
|----|----------|-----|----------|------------------|----------------|-------|
| Q1 | Major | FR-EXBOT-073 step 4 vs UC step 5 | LP close method conflict: FR-EXBOT-073 step 4 noi `BnzaExVault.redeem(tokenId)`, UC step 5 noi `vault.executeStrategy(RedeemStrategyV1, user, botId, params)`. US-EXBOT-009 AC-009-1 cung noi `executeStrategy`. Khong co document nao xac nhan cai nao dung. | FR-EXBOT-073: "call BnzaExVault.redeem(tokenId)"<br>UC step 5: "Call vault.executeStrategy(RedeemStrategyV1)"<br>US-EXBOT-009 AC-009-1: "vault.executeStrategy(RedeemStrategyV1) closes the LP position" | Affects test steps: hai function khac nhau hoan toan ve ABI call | BA / Tech Lead |
| Q2 | Major | US-EXBOT-012 AC-012-1 | US-EXBOT-012 AC-012-1 van noi "BnzaExVault.vaultClose is called, USDC parked into uninvested_balances". Day la park/redeploy feature da bi drop theo HLD 2026-06-18 nhung AC khong duoc update. | US-EXBOT-012 AC-012-1: "BnzaExVault.vaultClose is called, USDC parked into uninvested_balances"<br>HLD 2026-06-18 changelog: "drop park/redeploy/re-entry loop"<br>FR-EXBOT-070: "No park/redeploy loop (dropped HLD 2026-06-18)" | AC khong reflect feature da drop — tester se design test sai | BA |
| Q3 | Major | UC §3 (preconditions) | UC §3 preconditions chi noi "Trigger condition met" nhung khong specify rang bot phai co `bots.status IN ('active','safe_mode','paused')` (khong phai 'closed'). Khong co document nao explicit ve dieu nay. | UC §2: "Trigger condition met: circuit breaker retries exhausted, OR margin critical + SAFE_MODE irrecoverable, OR 3 stops within 7 days, OR admin force-close"<br>Khong co document nao noi ro ve bots.status prerequisite | Tester can biet trigger tren closed bot co duoc accept khong | BA |
| Q4 | Medium | UC §1, SRS flows.md F-05 | UC khong de cap queue idempotency cho Close Worker. Close Worker duoc trigger nhu the nao — via queue message hay direct call? flows.md F-05 diagram rat simplified, khong show queue consumer pattern. Khong co document nao mo ta trigger mechanism. | UC §1: "Primary: ExBot System Operator (Close Worker)"<br>flows.md F-05: simplified diagram<br>FR-EXBOT-010 (queues): khong co dedicated "bot_safe_close" queue | Tester can biet trigger mechanism de design test cho duplicate scenario | Tech Lead |
| Q5 | Medium | UC A1, US-EXBOT-009 AC-009-2 | UC A1 noi "admin escalation notification sent" nhung khong specify noi dung message. US-EXBOT-009 cung khong define. Khong co E-* code cho residual_hl_liability scenario. Khong co document nao dinh nghia message content. | UC §4 A1: "admin escalation notification sent"<br>US-EXBOT-009 AC-009-2: "admin escalation notification is sent"<br>message-list.md: khong co E-* code cho residual_hl_liability | Expected result khong ro — test khong the verify message content | BA |
| Q6 | Medium | UC §4 A3 vs US-EXBOT-009 AC-009-4 | AC-009-4 noi "bots.status remains 'closing' until fulfillRequest completes" nhung khong co document nao noi ro khi nao `bots.status='closing'` duoc set. Sau step 2 (hedge_close_pending) hay step 8 (redemption_queued)? | US-EXBOT-009 AC-009-4: "bots.status remains 'closing' until fulfillRequest completes"<br>Khong co document nao mo ta khi nao bots.status chuyen sang 'closing' | Lifecycle state timing can ro de test dung | BA |
| Q7 | Medium | UC §3 vs FR-EXBOT-072 | UC §3 preconditions khong de cap UserLockDO requirement. FR-EXBOT-026, 092 specify acquire UserLockDO cho hedge-sync, nhung khong co document nao xac nhan dieu nay co apply cho Close Worker khong. UC step 2 mention UserLockDO nhung khong noi ro day co bat buoc khong. | UC step 2: "acquire UserLockDO lease"<br>FR-EXBOT-026, 092: cho hedge-sync<br>Khong co document nao xac nhan cho Close Worker | Tester can biet close operation co can lock khong | Tech Lead |
| Q8 | Medium | FR-EXBOT-073 vs SRS states.md | FR-EXBOT-073 step 3 noi "stop cancelled" nhung close_operations states table (states.md) khong co `stop_canceled` state. Khong co document nao giai thich day la action hay state. | FR-EXBOT-073 step 3: "stop cancelled"<br>states.md close_operations: requested, lp_closed, funds_returned, hedge_close_pending, hedge_closed, redemption_queued, residual_hl_liability, done — khong co stop_canceled | Documentation inconsistency | BA |
| Q11 | Minor | US-EXBOT-009 AC-EXBOT-009-2 | AC-009-2 noi "bots.status transitions to 'safe_mode'" sau hedge fail nhung khong specify `bots.lifecycle_state`. states.md cho thay SAFE_MODE co the la ca hai, nhung khong ro khi nao nao. | states.md: safe_mode xuat hien o ca lifecycle_state va bots.status<br>US-EXBOT-009 AC-009-2: "bots.status transitions to 'safe_mode'"<br>Khong co document nao noi ro lifecycle_state behavior khi vao SAFE_MODE | Affects test assertion | BA / Tech Lead |

---

## Answered Questions

_(None)_

---

## Deferred Questions

> **Reason for Deferral:** Documents co the suy luan duoc, nhung khong du evidence de ket luan chan chan. QC Lead co the tu xu ly khi design test.

| ID | Uu tien | Ref | Question | Reason for Deferral | Owner |
|----|----------|-----|----------|---------------------|-------|
| Q9 | Minor | FR-EXBOT-072, UC §3 | FR-EXBOT-072 noi "idempotency_key UNIQUE enforced" va "trigger_reason populated" nhung khong dinh nghia format/value cu the. | FR-EXBOT-072 da noi ro rang cac field nay ton tai va duoc enforce. Khong can exact format de design test co ban — chi can verify UNIQUE constraint hoat dong. | QC Lead |
| Q10 | Minor | SRS flows.md F-05 | flows.md F-05 diagram rat simplified. | Diagram chi la visual aid, khong phai source of truth. UC step-by-step va FR-EXBOT-073 da mo ta day du. | BA |

---

## Summary

| Status | Count |
|--------|-------|
| Open | 9 |
| Deferred | 2 (Q9, Q10) |
| Answered | 0 |

---

*Generated by qc-uc-read-exbot skill*
