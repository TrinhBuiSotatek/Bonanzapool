# Question Backlog — UC-EXBOT-deep-audit

> Generated: 2026-06-19  
> Source files: `docs/qc/uc-read/UC-EXBOT-deep-audit/UC-EXBOT-deep-audit_deep-audit_audited_20260619_v1.md`

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-01 | High | UC §A1; SRS FR-EXBOT-016 | UC §A1 mô tả khi HL unreachable: "skip HL-dependent steps (2, 3, 4, 6, 7)". Tuy nhiên: (a) "step 4" trong UC là bước check `stop_trigger_crossed_at` — bước này chỉ đọc D1, không gọi HL, tại sao lại bị skip? (b) "step 7" là agent key expiry check — bước này chỉ đọc D1, không gọi HL, tại sao bị skip? Nếu D1-only steps bị skip khi HL unavailable, `margin_status` và agent key expiry sẽ không được check ngay cả khi dữ liệu D1 đã có. BA/Tech Lead xác nhận: khi HL unreachable trong A1, "skip HL-dependent steps" cụ thể bao gồm những bước nào? stop_trigger check và agent key check có bị skip không? | Tester không thể biết chính xác tập hợp operations nào vẫn chạy khi HL unreachable; bỏ sót test case quan trọng về partial audit behavior | Open |
| I-02 | High | UC §A3, §A4; SRS FR-EXBOT-050; US-010 AC-010-2 | UC §A3 (reconcile mismatch → SAFE_MODE) và §A4 (stuck stop marker → SAFE_MODE) đều ghi "enqueue admin notification" nhưng không phân biệt: notification gửi đến admin, investor, hay cả hai? SRS FR-EXBOT-050 ghi "alert user/admin" nhưng UC không làm rõ. US-010 AC-010-2 ghi rõ "both the investor and admin receive alerts" cho margin critical, nhưng không rõ mismatch/stuck marker có cùng behavior không. BA/Tech Lead xác nhận: khi deep-audit trigger SAFE_MODE qua A3 (mismatch) và A4 (stuck marker), notification gửi đến ai — investor, admin, hay cả hai? | Tester không thể viết expected result cho notification recipients trong A3/A4 test cases | Open |
| I-03 | High | UC §3 bước 6; SRS FR-EXBOT-060; US-010 AC-010-1, AC-010-2 | UC §3 bước 6 chỉ ghi "update hedge_legs.margin_status" nhưng không mô tả: (a) khi margin_status chuyển từ `ok` → `warning`, notification "Margin warning for your ExBot. Consider depositing additional margin to HL." có được enqueue trong cùng deep-audit cycle không? (b) "Second consecutive critical reading" để trigger SAFE_MODE (US-010 AC-010-2) được track bằng cơ chế nào — field trong D1, hay logic so sánh với previous reading trong same worker? Không có field nào trong erd.md track "consecutive critical count". BA/Tech Lead làm rõ: (1) margin warning notification enqueued trong deep-audit không? (2) consecutive critical count được track như thế nào? | Tester không thể test margin transition notifications và SAFE_MODE-via-critical flow mà không biết luồng chính xác | Open |
| I-07 | High | UC §A3, §A4; SRS FR-EXBOT-050 | UC mô tả ba paths (A3, A4 ×2) có thể trigger SAFE_MODE nhưng không mô tả: (a) nếu cả A3 (mismatch) VÀ A4 (stuck stop) đều true trong cùng một audit cycle, SAFE_MODE được triggered một lần hay nhiều lần? Có idempotency không? (b) Sau khi SAFE_MODE được set trong bước 3 (mismatch), worker có tiếp tục check bước 4, 5 (stuck markers) không, hay exit early? (c) Sau SAFE_MODE entry, margin update (bước 6), agent key check (bước 7), và timestamp write (bước 8) có tiếp tục chạy không? | Tester cần biết total behavior khi nhiều conditions đồng thời — có thể affect audit completeness và idempotency | Open |
| I-08 | Medium | UC §3; SRS FR-EXBOT-050; US-010 AC-010-4 | SRS FR-EXBOT-050 định nghĩa 7 SAFE_MODE conditions: reconcile mismatch, margin_status='critical' ×2, effective_leverage > 4.5, liquidation_price within 5%, stop_trigger stuck, stop_replacing stuck, HL unreachable > 5 min. Deep-audit UC chỉ cover 3 trong 7 (mismatch, stop_trigger stuck, stop_replacing stuck). US-010 AC-010-4 mô tả effective_leverage > 4.5 trigger nhưng không chỉ rõ đây là trong deep-audit hay hedge-sync. BA/Tech Lead xác nhận: `effective_leverage > 4.5` và `liquidation_price within 5% of hlMarkPrice` có được check trong deep-audit không? | Tester có thể miss test cases cho effective_leverage và liquidation_price conditions nếu chúng thuộc deep-audit scope | Open |

Priority: High = blocks test design, Medium = affects scope/coverage, Low = cleanup/traceability  
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

_(No answered questions yet.)_

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|
| I-04 | Low | UC §3 bước 7; SRS FR-EXBOT-083; erd.md | UC §3 bước 7 check `hl_agent_keys.expires_at - now <= 7 days` nhưng không chỉ rõ: (a) chỉ check key với `approval_status='approved'` hay check tất cả key? (b) Nếu user có một key `approved` sắp hết hạn VÀ một key `pending` đang chờ approve, notification có được gửi không? SRS FR-EXBOT-083 ghi "existing approved key remains active" trong window pending→approved, nhưng không nói về notification behavior trong trường hợp này. | Deferred — edge case not critical for initial test design; can be addressed in later test cycles. | QC Lead | 2026-06-24 | Deferred |
| I-05 | High | UC §3 bước 8; UC §5 Postconditions; erd.md | UC §3 bước 8 và §5 Postconditions đều ghi `hedge_legs.last_audit_at = now`. Tuy nhiên erd.md `hedge_legs` schema KHÔNG có field `last_audit_at` — `hedge_legs` chỉ có `last_stop_audit_at` và `updated_at`. Field `last_deep_audit_at` tồn tại trong `bot_runtime_state`, không phải `hedge_legs`. BA vui lòng xác nhận: bước 8 update field nào trong schema — `bot_runtime_state.last_deep_audit_at`? Hay có field `hedge_legs.last_audit_at` chưa được thêm vào erd.md? | Deferred — test design can proceed using `bot_runtime_state.last_deep_audit_at` from erd.md; BA clarification on field name can be obtained later. | QC Lead | 2026-06-24 | Deferred |
| I-06 | Low | UC §5 Postconditions | UC có hai mục `## Postconditions` — mục §5 có nội dung đúng và cụ thể. Mục thứ hai (sau §5, trước §6) là placeholder template: "System state reflects the completed audit", "NFR-ADM-005". NFR-ADM-005 là NFR của module Admin, không phải ExBot. Cùng pattern với uc-hedge-sync và uc-user-redeem. BA vui lòng xóa phần placeholder Postconditions thứ hai. | Deferred — documentation cleanup issue; does not block test design; BA can clean up in next revision. | QC Lead | 2026-06-24 | Deferred |

_(No deferred questions yet.)_