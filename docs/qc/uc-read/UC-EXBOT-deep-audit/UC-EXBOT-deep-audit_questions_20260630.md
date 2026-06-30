# Question Backlog

> Generated: 2026-06-30
> Source files: UC-EXBOT-deep-audit_audited_20260630_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q-DA-01 | High | UC A4; spec.md §5 Error Codes; frd.md §4.6 | UC A4 mô tả admin escalation notification được enqueue khi stuck marker detected, nhưng không có nội dung message cụ thể được định nghĩa trong UC hoặc trong spec.md error codes. spec.md E-EXBOT-008 (HL unreachable) và E-EXBOT-011 (reconcile mismatch) có nội dung, nhưng không có E-code tương ứng cho hai stuck marker cases. BA vui lòng xác định: (1) Admin notification message cho "stop_trigger_crossed_at stuck > 30min" có nội dung chính xác là gì? (2) Admin notification message cho "stop_replacing_started_at stuck > 60s" có nội dung chính xác là gì? (3) Có cần E-code riêng cho các notification này không? | Test case không thể verify expected notification content khi không có message definition chính xác. Đây là Blocker cho notification testing. | Open |
| Q-DA-02 | Medium | UC §6 Business Rules; FR-EXBOT-033 | Không rõ ràng deep-audit cho paused bot có check stop_trigger_crossed_at và stop_replacing_started_at stuck markers không — vì stopped marker chỉ được set khi stop trigger fires (trong light-check), và stopped bot thường không ở trạng thái paused. Edge case: active bot → stop trigger fires → light-check sets stop_trigger_crossed_at → user pauses bot → marker stuck > 30 min trên paused bot. Deep-audit A2 path nói "all detection paths execute" nhưng UC không verify cụ thể. | Tester cần biết liệu stuck marker detection hoạt động cho paused bot hay không để design test đúng scope. | Open |
| Q-DA-03 | Medium | UC Step 1; erd.md | UC Step 1 nói worker reads bots.status, bots.lifecycle_state, hedge_legs, circuit_breakers.state, margin_status từ D1. Tuy nhiên, không rõ ràng deep-audit worker đọc tất cả bots một lần rồi xử lý tuần tự, hay đọc theo shard. spec.md NFR-EXBOT-012 đề cập D1 sharding nhưng deep-audit UC không specify shard iteration strategy. BA vui lòng xác nhận: Deep-audit worker đọc bots theo cách nào — scan tất cả shards, hay một cron trigger per shard? | Multi-shard test design phụ thuộc vào shard iteration strategy. Nếu không rõ, tester không thể design test cho Phase B (4 shards). | Open |
| Q-DA-04 | Low | UC A1; spec.md E-EXBOT-008 | UC A1 nói "update cadence to high-risk interval (1 hour)" khi HL unreachable. Tuy nhiên, không rõ điều này được ghi vào đâu trong D1 — có phải bots.next_deep_audit_at không? erd.md có bots.next_deep_audit_at field. Nhưng UC không specify writer. BA vui lòng xác nhận: Khi cadence switch 6h → 1h, worker có update bots.next_deep_audit_at để reflect 1h interval không, hay cron schedule tự handle switching dựa trên current state? | Tester cần verify cadence switching mechanism để design test đúng behavior. | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

_(No deferred questions — all questions transferred from audited report.)_
