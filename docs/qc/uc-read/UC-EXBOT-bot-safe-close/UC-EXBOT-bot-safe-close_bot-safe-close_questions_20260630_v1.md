# Question Backlog

> Generated: 2026-06-30
> Source: UC-EXBOT-bot-safe-close readiness review
> Updated: 2026-07-02 (BA responses filled; audited report: UC-EXBOT-bot-safe-close_bot-safe-close_audited_20260702_v2.md)

---

## Open Questions

> **Policy:** Khong tu suy luan. Tat ca cau hoi can BA/Tech Lead xac nhan dua tren documents.

| ID | Uu tien | Ref | Question | Evidence in Docs | Why It Matters | Owner |
|----|----------|-----|----------|------------------|----------------|-------|
| Q4 | Medium | UC §1, SRS flows.md F-05 | UC khong de cap queue idempotency cho Close Worker. Close Worker duoc trigger nhu the nao — via queue message hay direct call? flows.md F-05 diagram rat simplified, khong show queue consumer pattern. Khong co document nao mo ta trigger mechanism. | UC §1: "Primary: ExBot System Operator (Close Worker)"<br>flows.md F-05: simplified diagram<br>FR-EXBOT-010 (queues): khong co dedicated "bot_safe_close" queue | Tester can biet trigger mechanism de design test cho duplicate scenario | **⏳ Pending Tech Lead** — Nhờ chị Trinh check với dev team. (Đã được cập nhật ở file: `docs/BA/qc-notes-temp.md` — Q4 UC-EXBOT-bot-safe-close) | Tech Lead |
| Q7 | Medium | UC §3 vs FR-EXBOT-072 | UC §3 preconditions khong de cap UserLockDO requirement. FR-EXBOT-026, 092 specify acquire UserLockDO cho hedge-sync, nhung khong co document nao xac nhan dieu nay co apply cho Close Worker khong. UC step 2 mention UserLockDO nhung khong noi ro day co bat buoc khong. | UC step 2: "acquire UserLockDO lease"<br>FR-EXBOT-026, 092: cho hedge-sync<br>Khong co document nao xac nhan cho Close Worker | Tester can biet close operation co can lock khong | **⏳ Pending Tech Lead** — Nhờ Tech Lead xác nhận. (Đã được cập nhật ở file: `docs/BA/qc-notes-temp.md` — Q7 UC-EXBOT-bot-safe-close) | Tech Lead |

---

## Answered Questions

| ID | Uu tien | Ref | Question | Answer Summary | Source |
|----|----------|-----|----------|----------------|--------|
| Q1 | Major | FR-EXBOT-073 step 4 vs UC step 5 | LP close method conflict | `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` là đúng. FR-EXBOT-073 step 4 đã được sửa: LP close qua BnzaExPositionManager, fees routed via LpFeeOps, PositionClosed event emitted. | docs/BA/qc-notes-temp.md — Q1 UC-EXBOT-bot-safe-close |
| Q2 | Major | US-EXBOT-012 AC-012-1 | US-EXBOT-012 AC-012-1 park/redeploy đã bị drop | AC-012-1 đã được cập nhật: bỏ dòng vaultClose/park, thêm `vault.executeStrategy(RedeemStrategyV1)` + `RedemptionQueue.createRequest` + `fulfillRequest`. | docs/BA/qc-notes-temp.md — Q2 UC-EXBOT-bot-safe-close |
| Q3 | Major | UC §3 (preconditions) | bots.status prerequisite cho trigger | Trigger chỉ hợp lệ khi `bots.status NOT IN ('closed', 'closing')`. Reject được enforce ở DB level bởi UNIQUE constraint trên `close_operations.idempotency_key` (FR-EXBOT-072). UC §2 Preconditions đã được update. | docs/BA/qc-notes-temp.md — Q3 UC-EXBOT-bot-safe-close |
| Q5 | Medium | UC A1, US-EXBOT-009 AC-009-2 | Message content cho admin escalation notification | Thêm E-EXBOT-018: "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability." — internal alert. UC A1 và message-list.md đã được update. | docs/BA/qc-notes-temp.md — Q5 UC-EXBOT-bot-safe-close |
| Q6 | Medium | UC §4 A3 vs US-EXBOT-009 AC-009-4 | Khi nào `bots.status='closing'` được set | Set tại **step 1** — ngay khi trigger fires và `close_operations` row được tạo. `lifecycle_state='lp_closing'` set đồng thời. Giữ đến step 11 khi `fulfillRequest` hoàn tất → chuyển sang `'closed'`. UC step 1 đã được update. | docs/BA/qc-notes-temp.md — Q6 UC-EXBOT-bot-safe-close |
| Q8 | Medium | FR-EXBOT-073 vs SRS states.md | "stop cancelled" là action hay state | `stop cancelled` là **action**, không phải state riêng. `closeShortReduceOnlyIoc` và `replaceStopProtected(size=0)` đều là actions trong step 2 (`hedge_close_pending`). `close_operations.state` chỉ advance lên `hedge_closed` sau khi reconcile confirm HL size = 0 AND stop đã cancel. FR-EXBOT-073 đã được update. | docs/BA/qc-notes-temp.md — Q8 UC-EXBOT-bot-safe-close |
| Q11 | Minor | US-EXBOT-009 AC-EXBOT-009-2 | `bots.lifecycle_state` khi vào safe_mode | Cả hai đều chuyển sang `'safe_mode'` — `lifecycle_state` và `status` có cùng giá trị per `states.md`. AC-009-2 đã được update để ghi rõ `lifecycle_state='safe_mode'`. | docs/BA/qc-notes-temp.md — Q11 UC-EXBOT-bot-safe-close |

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
| Open (Pending Tech Lead) | 2 (Q4, Q7) |
| Answered | 7 (Q1, Q2, Q3, Q5, Q6, Q8, Q11) |
| Deferred | 2 (Q9, Q10) |
| **Total** | **11** |

---

*Generated by qc-uc-read-exbot skill*
