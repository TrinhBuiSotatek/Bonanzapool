---
title: Question Backlog — UC-EXBOT-pause-resume
date: 2026-06-18
author: qc-uc-read-exbot
version: v1
---

# Question Backlog — UC-EXBOT-pause-resume

> Generated: 2026-06-18
> Source: docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260618_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-001 | High | UC §2 Preconditions vs srs/spec.md FR-EXBOT-005 | UC §2 yêu cầu `bots.lifecycle_state='active'` là điều kiện tiên quyết để pause bot. Tuy nhiên, SRS FR-EXBOT-005 chỉ nêu pause đặt `bots.status='paused'` trong khi giữ nguyên `lifecycle_state` — không có ràng buộc `lifecycle_state` phải là `'active'`. Một bot hợp lệ có thể có `status='active'` nhưng `lifecycle_state='hedge_stopped_cooldown'`. BA cần xác nhận: pause có được phép khi `lifecycle_state != 'active'` không? Nếu có, UC §2 cần bỏ ràng buộc này. Nếu không, FR-EXBOT-005 cần bổ sung ràng buộc. | Tester không thể thiết kế test case cho trạng thái `lifecycle_state='hedge_stopped_cooldown'` + `status='active'` mà biết expected result. | Open |
| I-002 | High | UC §4 Resume bước 4 | UC §4 bước 4 ghi: "Worker reads pre-pause `lifecycle_state` from D1 (unchanged) — confirms it matches expected state". Cụm "confirms it matches expected state" không rõ: hệ thống so sánh với giá trị nào? Nếu `lifecycle_state` bị thay đổi trong khi bot đang pause (ví dụ deep-audit kích hoạt transition), hành vi tiếp theo là gì? Có block resume không? Có trả về lỗi không? BA/Tech Lead cần xác định logic xử lý cụ thể. | Tester không thể viết expected result rõ ràng cho bước xác nhận `lifecycle_state` trong luồng resume. | Open |
| I-003 | Medium | UC §7 Postconditions vs srs/erd.md | UC §7 Postconditions đề cập "Audit log entry recorded: 'Bot paused by investor'" và "Bot resumed by investor". Tuy nhiên, `srs/erd.md` không có bảng audit log trong ERD, và không có FR nào trong SRS/FRD định nghĩa ghi audit log cho pause/resume. BA/Tech Lead cần xác nhận: audit log được ghi vào bảng nào trong D1? Nếu chưa có schema, cần thêm vào ERD. | Tester không thể verify expected result về audit log vì không biết schema. | Open |
| I-004 | High | UC §3 bước 1, UC §4 bước 1 | Cả hai luồng pause và resume không có alternate flow cho trường hợp `botId` không tồn tại hoặc bot thuộc về user khác. BA cần xác nhận: HTTP status và message khi botId không hợp lệ hoặc bot không thuộc quyền sở hữu của investor đang request? Đây là kiểm soát authorization cơ bản (ngăn chặn tấn công IDOR). | Tester không thể thiết kế test case bảo mật mà không biết expected response khi cố ý pause/resume bot của người khác. | Open |
| I-005 | Medium | UC §5 Alternate Flows | UC §5 có 3 alternate flow (A1, A2, A3) nhưng thiếu alternate flow cho: pause/resume bot có `status='closing'`; pause/resume bot có `status='error'`. BA cần xác nhận hành vi hệ thống (HTTP status, message) cho hai trường hợp còn thiếu. | Tester không có expected result cho các trạng thái `closing` và `error`. | Open |
| I-006 | High | frd.md FR-EXBOT-003 vs srs/spec.md FR-EXBOT-005 | `frd.md` định nghĩa tính năng Pause/Resume tại `FR-EXBOT-003`. `srs/spec.md` định nghĩa cùng tính năng tại `FR-EXBOT-005`. UC §9 FR Trace cite FR-EXBOT-005 (đúng với spec); US-EXBOT-003 §Trace cite FR-EXBOT-003 (theo frd). Hai nguồn dùng số FR khác nhau cho cùng tính năng. BA cần đồng bộ đánh số FR giữa frd.md và spec.md. | Tester tra cứu "FR-EXBOT-005" trong frd.md sẽ không thấy, gây hiểu nhầm tính năng không có FR backing. Traceability matrix bị gãy. | Open |
| I-007 | High | UC §4 Resume bước 5 vs srs/erd.md bảng bots | UC §4 bước 5 ghi: "set `bot_runtime_state.next_light_check_at` to `now + 5min + jitter`". Nhưng `srs/erd.md` cho thấy `next_light_check_at` là column của bảng `bots`, không phải `bot_runtime_state`. Bảng `bot_runtime_state` không có column này. BA cần xác nhận: UC §4 bước 5 nên là "set `bots.next_light_check_at`" — không phải `bot_runtime_state.next_light_check_at`. | Tester sẽ kiểm tra sai bảng D1 nếu theo UC literal. | Open |
| I-008 | Medium | UC §6 Suppression Behavior vs FR-EXBOT-014 | UC §6 mô tả rõ light-check và hedge-sync bị tắt, deep-audit tiếp tục. Nhưng không đề cập stop monitoring (`price-near-stop-audit` queue). FR-EXBOT-014 quy định "Stop monitoring continues at ALL times including when circuit breaker is open." BA cần xác nhận: stop monitoring có tiếp tục khi bot ở `status='paused'` không? Nếu có, UC §6 cần bổ sung mục này. | Tester không biết có cần thiết kế test case kiểm tra stop monitoring khi bot đang paused không. | Open |
| I-009 | Low | US-EXBOT-003 AC-003-4 vs srs/spec.md E-EXBOT-013 | US-EXBOT-003 AC-003-4 mô tả message từ chối pause trong SAFE_MODE là: "Bot is already in Safe Mode. You can close the bot instead." Nhưng E-EXBOT-013 verbatim trong spec.md §5 là: "Bot is in Safe Mode. You can close the bot instead." (không có chữ "already"). Hai nguồn mâu thuẫn về nội dung message. BA cần xác nhận message chính xác cần implement và test. | Tester không biết expected message nào là đúng khi viết assertion cho test case từ chối pause trong SAFE_MODE. | Open |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason for Deferral | Status |
|----|----------|-----|----------|---------------------|--------|
