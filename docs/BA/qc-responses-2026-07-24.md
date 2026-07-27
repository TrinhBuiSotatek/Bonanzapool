---
type: qc-response
module: exbot
status: draft
created: 2026-07-24
updated: 2026-07-24
owner: "@hienduong"
---

# QC Responses — ExBot Module (2026-07-24)

> File này chỉ lưu ở local — KHÔNG commit, KHÔNG push.

---

## UC-EXBOT-monitor-status — Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status | Ans |
| --- | --- | --- | --- | --- | --- | --- |
| V-009 | H | UC §2 Preconditions (cập nhật 2026-07-20) vs `userstories/us-002.md` Acceptance Criteria (AC-EXBOT-002-1/2/3) | UC nói rõ ExBot Lambda có một điều kiện chặn cứng (`isAdmin` guard) khiến actor Investor nhận 403 trước khi bất kỳ business logic nào chạy trong v1. Nhưng US-EXBOT-002 vẫn viết cả 3 Acceptance Criteria với Given là Investor xem status thành công (kỳ vọng response 200), không có ghi chú v1 gap nào. BA vui lòng xác nhận: (a) US-EXBOT-002 có cần cập nhật thêm ghi chú v1 gap vào cả 3 AC không; (b) phạm vi "Done" của v1 cho happy path này có được coi là đạt khi chỉ verify được bằng actor Admin không. | Nếu không xác nhận, tester đọc US-EXBOT-002 sẽ thiết kế test case theo actor Investor và kỳ vọng 200 — nhưng test case đó sẽ luôn fail trong v1 vì bị 403 isAdmin guard, dễ bị báo nhầm thành bug thay vì hành vi có chủ đích. | Closed | v1 gap: US-EXBOT-002 không testable với Investor actor trong v1. ExBot Lambda isAdmin guard trả về 403 cho non-Admin caller sau khi bot record được tìm thấy (intentional, không phải bug). Cả 3 AC bị block với Investor. Admin actor chỉ verify được API logic. Full acceptance testable từ v1.1 khi isAdmin guard được remove. **Doc đã update:** v1 gap note thêm vào cả 3 AC trong us-002.md. |
| V-010 | L | UC §4 A9/A10 vs `02_backbone/message-list.md` bảng EXBOT | UC cite E-EXBOT-030 (A9) và E-EXBOT-031 (A10) — cả hai đã có nội dung verbatim trong nguồn canonical `srs/spec.md` §5, nhưng bảng mirror `message-list.md` (EXBOT section) chưa được đồng bộ, hiện chỉ dừng ở E-EXBOT-029. BA/Tech Lead vui lòng đồng bộ bảng mirror. | Không block test design (nguồn canonical đã đủ message text), nhưng gây bất tiện nếu tester quen tra `message-list.md` trước khi tra `spec.md`. | Closed | Đã sync. E-EXBOT-030 và E-EXBOT-031 đã được thêm vào message-list.md. Nguồn canonical (srs/spec.md §5) đã có từ trước — đây chỉ là sync mirror. Tester có thể tra cứu cả 2 nơi. |
| V-011 | L | `userstories/us-002.md` §Notes vs UC endpoint path (cập nhật 2026-07-20) | US-002 §Notes vẫn ghi endpoint là `/api/exbot/status` (không có `{botId}`) trong khi UC đã đổi thành `/api/exbot/status/{botId}` từ 2026-07-20. BA vui lòng cập nhật US-002 §Notes cho khớp. | Rủi ro thấp — chỉ ảnh hưởng nếu tester đọc US trước UC và dùng sai endpoint path khi viết test request mẫu. | Closed | Đã fix. US-002 §Notes cập nhật endpoint thành `/api/exbot/status/{botId}` cho khớp với UC (đã update từ 2026-07-20). |
| V-012 | M | UC §2 Preconditions v1 gap note (isAdmin guard) | UC chỉ nói caller không phải Admin "receive 403" nhưng không định nghĩa nội dung message body/E-EXBOT code cụ thể cho lỗi 403 này — khác với các lỗi 403 khác trong UC (đều có E-EXBOT code kèm theo). BA vui lòng xác nhận response body của lỗi 403 isAdmin guard có message text cụ thể không, hay chỉ là 403 trống/generic. | Tác động thấp trong thực tế (actor Investor không thể test path này một cách hợp lệ — đây chính là hành vi bị chặn), nhưng nếu QA cần verify response body chính xác thì thông tin còn thiếu. | Closed | Response body của 403 isAdmin guard là: `{ "reason": "forbidden" }` — không có E-EXBOT code, không có message text. Confirmed từ develop branch `forbidden()` helper. Tester verify: HTTP 403 + `body.reason === "forbidden"`. **Doc đã update:** uc-monitor-status.md Preconditions v1 gap note bổ sung response body format. |
