# Question Backlog

> Generated: 2026-06-30
> Source: UC-EXBOT-bot-safe-close readiness review
> Updated: 2026-07-06 (re-audit v3; Q7 resolved by BA update 2026-07-04)
> Audit report: UC-EXBOT-bot-safe-close_bot-safe-close_audited_20260706_v3.md

---

## Open Questions

> **Policy:** Không tự suy luận. Tất cả câu hỏi cần BA/Tech Lead xác nhận dựa trên documents.

| ID | Ưu tiên | Ref | Question | Evidence in Docs | Why It Matters | Owner | Status |
|----|----------|-----|----------|------------------|----------------|-------|--------|
| Q4 | Medium | UC §1, SRS flows.md F-05, FR-EXBOT-073 | UC §1 liệt kê "ExBot System Operator (Close Worker)" là Primary Actor. Tuy nhiên, từ UC §3 và FR-EXBOT-073, Close Worker không tự quyết định trigger — nó chỉ thực thi flow khi được gọi. 5 trigger conditions thực tế đến từ: (1) deep-audit worker, (2) hedge-sync worker, (3) partial_repair worker, (4) light-check/hedge-stopped, HOẶC (5) admin qua `POST /api/exbot/close`. Không có dedicated `bot_safe_close` queue trong 11 queues (FR-EXBOT-010). Vậy "Close Worker" trong UC §1 là **architecture component (ExBot Lambda)** hay **actor**? BA xác nhận lại role của Close Worker trong UC. | UC §1: "Primary: ExBot System Operator (Close Worker)"<br>UC §3 Step 1: "Close Worker: acquire User Lock..."<br>FR-EXBOT-073: 5 trigger conditions<br>FR-EXBOT-010: 11 queues — không có bot_safe_close queue | Nếu Close Worker là architecture chứ không phải actor, thì UC §1 Actor list cần được cập nhật để phản ánh đúng. Trigger mechanism cần được ghi rõ trong UC. | BA | ⏳ Pending |
| Q9 | Medium | FR-EXBOT-072, UC §3 | FR-EXBOT-072 nói "idempotency_key UNIQUE enforced" và "trigger_reason populated" nhưng không có document nào định nghĩa format/value cụ thể. | FR-EXBOT-072: "idempotency_key UNIQUE enforced", "trigger_reason populated"<br>UC §3: Preconditions<br>SRS erd.md: close_operations table | Nếu không biết format, không thể verify UNIQUE constraint hoạt động đúng trong test. BA cần bổ sung: (1) format/value của `idempotency_key` (ví dụ: `{botId}:{kind}:{trigger_timestamp}`), (2) format/value của `trigger_reason` (ví dụ: enum values: `circuit_breaker_exhausted`, `margin_critical`, `3_stops_7d`, `partial_repair_exhausted`, `admin_force_close`). | BA | ⏳ Pending |

---

## Answered Questions

| ID | Ưu tiên | Ref | Question | Answer Summary | Source |
|----|----------|-----|----------|----------------|--------|
| Q1 | Major | FR-EXBOT-073 step 4 vs UC step 5 | LP close method conflict | `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` là đúng. FR-EXBOT-073 step 4 đã được sửa: LP close qua BnzaExPositionManager, fees routed via LpFeeOps, PositionClosed event emitted. | docs/BA/qc-notes-temp.md — Q1 UC-EXBOT-bot-safe-close |
| Q2 | Major | US-EXBOT-012 AC-012-1 | US-EXBOT-012 AC-012-1 park/redeploy đã bị drop | AC-012-1 đã được cập nhật: bỏ dòng vaultClose/park, thêm `vault.executeStrategy(RedeemStrategyV1)` + `RedemptionQueue.createRequest` + `fulfillRequest`. | docs/BA/qc-notes-temp.md — Q2 UC-EXBOT-bot-safe-close |
| Q3 | Major | UC §3 (preconditions) | bots.status prerequisite cho trigger | Trigger chỉ hợp lệ khi `bots.status NOT IN ('closed', 'closing')`. Reject được enforce ở DB level bởi UNIQUE constraint trên `close_operations.idempotency_key` (FR-EXBOT-072). UC §2 Preconditions đã được update. | docs/BA/qc-notes-temp.md — Q3 UC-EXBOT-bot-safe-close |
| Q5 | Medium | UC A1, US-EXBOT-009 AC-009-2 | Message content cho admin escalation notification | Thêm E-EXBOT-018: "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability." — internal alert. UC A1 và message-list.md đã được update. | docs/BA/qc-notes-temp.md — Q5 UC-EXBOT-bot-safe-close |
| Q6 | Medium | UC §4 A3 vs US-EXBOT-009 AC-009-4 | Khi nào `bots.status='closing'` được set | Set tại **step 1** — ngay khi trigger fires và `close_operations` row được tạo. `lifecycle_state='lp_closing'` set đồng thời. Giữ đến step 11 khi `fulfillRequest` hoàn tất → chuyển sang `'closed'`. UC step 1 đã được update. | docs/BA/qc-notes-temp.md — Q6 UC-EXBOT-bot-safe-close |
| Q7 | Medium | UC §3 step 2 vs FR-EXBOT-092 | Step 2 nói "acquire UserLockDO lease" — UserLockDO là Cloudflare Durable Object, không tồn tại trong ExBot architecture (FR-EXBOT-092 chỉ định Redis Redlock via ElastiCache). | **UC 2026-07-04 đã cập nhật:** Step 2 now correctly says "acquire User Lock (Redis Redlock via ElastiCache) lease". UserLockDO đã được thay hoàn toàn bằng Redis Redlock trong toàn bộ ExBot. | UC changelog 2026-07-04: "replace UserLockDO with User Lock (Redis Redlock via ElastiCache)" |
| Q8 | Medium | FR-EXBOT-073 vs SRS states.md | "stop cancelled" là action hay state | `stop cancelled` là **action**, không phải state riêng. `closeShortReduceOnlyIoc` và `replaceStopProtected(size=0)` đều là actions trong step 2 (`hedge_close_pending`). `close_operations.state` chỉ advance lên `hedge_closed` sau khi reconcile confirm HL size = 0 AND stop đã cancel. FR-EXBOT-073 đã được update. | docs/BA/qc-notes-temp.md — Q8 UC-EXBOT-bot-safe-close |
| Q11 | Minor | US-EXBOT-009 AC-EXBOT-009-2 | `bots.lifecycle_state` khi vào safe_mode | Cả hai đều chuyển sang `'safe_mode'` — `lifecycle_state` và `status` có cùng giá trị per `states.md`. AC-009-2 đã được update để ghi rõ `lifecycle_state='safe_mode'`. | docs/BA/qc-notes-temp.md — Q11 UC-EXBOT-bot-safe-close |

---

## Deferred Questions

> **Reason for Deferral:** Documents có thể suy luận được, nhưng không đủ evidence để kết luận chắc chắn. QC Lead có thể tự xử lý khi design test.

| ID | Ưu tiên | Ref | Question | Reason for Deferral | Owner |
|----|----------|-----|----------|---------------------|-------|
| Q10 | Minor | SRS flows.md F-05, UC Figure 1 | flows.md F-05 và UC Figure 1 (Mermaid diagram) đều simplified — không reflect executeStrategy, hedge close step, idempotency_key, hay state progression chi tiết. UC diagram chỉ có 2 bước (Trigger → Operator fulfillRequest). | Diagram là visual aid, không phải source of truth. UC step-by-step và FR-EXBOT-073 đã mô tả đầy đủ. Không ảnh hưởng test design vì step-by-step đã rõ. | BA |

---

## Summary

| Status | Count |
|--------|-------|
| Open (Pending BA) | 2 (Q4, Q9) |
| Answered | 8 (Q1, Q2, Q3, Q5, Q6, Q7, Q8, Q11) |
| Deferred | 1 (Q10) |
| **Total** | **11** |

---

*Generated by qc-uc-read-exbot skill*
