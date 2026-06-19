---
title: Danh sách câu hỏi tồn đọng — UC-EXBOT-monitor-status
date: 2026-06-19
author: qc-uc-read-exbot
version: v2
---

# Danh sách câu hỏi tồn đọng — UC-EXBOT-monitor-status

> Tạo ngày: 2026-06-19
> Nguồn: docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260618_v1.md
> Bản dịch tiếng Việt từ: UC-EXBOT-monitor-status_monitor-status_questions_20260618_v1.md

---

## Câu hỏi đang mở

| ID | Ưu tiên | Tham chiếu | Nội dung câu hỏi | Vì sao quan trọng | Trạng thái |
|----|---------|------------|------------------|-------------------|------------|
| I-001 | High | UC §4 A3 vs srs/states.md HLD-2026-06-18; frd.md §2 | UC §4 A3 mô tả một alternate flow cho `lifecycle_state='cooldown'` sau bot_safe_close với message "Bot safely closed. USDC parked. Re-entry will be attempted automatically." Tuy nhiên, states.md cập nhật 2026-06-18 đã xóa rõ ràng các trạng thái `cooldown` và `parked`. UC chưa được cập nhật. BA cần: xóa A3 khỏi UC §4 và xóa nhãn "Cooldown" khỏi danh sách nhãn trạng thái ở bước 9. Sau bot_safe_close, lifecycle chuyển thẳng sang `closed` — không còn trạng thái parked/cooldown. | Tester thiết kế test case cho A3 sẽ tạo dữ liệu test với `lifecycle_state='cooldown'` — một trạng thái không thể tồn tại sau HLD-2026-06-18. Nhãn "Cooldown" ở bước 9 càng làm tăng thêm nhầm lẫn. | Mở |
| I-002 | High | UC §3 bước 9 vs srs/states.md HLD-2026-06-18 | UC §3 bước 9 liệt kê "Status label (Active/Safe Mode/Cooldown)" là các nhãn hiển thị có thể có. Nhãn "Cooldown" tương ứng với `lifecycle_state='cooldown'` đã bị xóa bởi HLD-2026-06-18. BA cần: cập nhật danh sách nhãn trạng thái ở bước 9 để xóa "Cooldown" và chỉ dùng các trạng thái hợp lệ sau HLD. | Tester tạo dữ liệu test cho nhãn "Cooldown" sẽ kiểm tra hành vi không thể xảy ra. | Mở |
| I-003 | High | UC §3 bước 3 vs bước 9; erd.md bảng bots + bot_runtime_state | UC §3 bước 3 đọc `next_light_check_at` (timestamp lên lịch trong tương lai từ bảng `bots`), nhưng bước 9 lại hiển thị "Last light-check timestamp" (timestamp trong quá khứ). Đây là hai trường khác nhau: `bots.next_light_check_at` và `bot_runtime_state.last_light_check_at`. BA cần làm rõ: trường nào được đọc và hiển thị? Cập nhật bước 3 để ghi rõ tên trường D1 chính xác, và đồng bộ nhãn ở bước 9 cho khớp (hoặc "Lần kiểm tra cuối" đọc `last_light_check_at`, hoặc "Lần kiểm tra tiếp theo" đọc `next_light_check_at`). | Tester không thể xác định trường nào cần kiểm tra trong response — đọc `next_light_check_at` nhưng hiển thị là "Last light-check" sẽ cho ra giá trị sai về mặt ngữ nghĩa. | Mở |
| I-004 | High | UC §3 bước 6; srs/spec.md FR-EXBOT-021; erd.md bot_runtime_state | UC §3 bước 6 tính drift% theo công thức `(|actualShortEth - targetShortEth| / targetShortEth) × 100` nhưng không định nghĩa nguồn của `targetShortEth`. SRS FR-EXBOT-021 định nghĩa `targetShortEth = lpEthAmount × hedgeRatio` (tính lại mỗi lần). erd.md `bot_runtime_state` có column `target_short_size`. Câu hỏi: monitor-status (a) đọc `target_short_size` từ D1 trực tiếp, hay (b) tính lại từ LP amounts hiện tại? Nếu (a), trường này không có trong danh sách đọc D1 ở bước 3. BA/Tech Lead cần chỉ định rõ nguồn của `targetShortEth` để tính drift% trong UC này. | Tester không thể viết test case cho drift% mà không biết `targetShortEth` lấy từ đâu. Nếu từ giá trị D1 đã cache, drift% có thể khác với kết quả tính lại theo thời gian thực. | Mở |
| I-005 | High | UC §4; srs/spec.md FR-EXBOT-093 | UC §4 có alternate flow A5 cho trường hợp Operator Facade không khả dụng (HTTP 503) nhưng không có alternate flow cho trường hợp MarketDataDO không khả dụng hoặc cache của DO vượt quá 2 lần chu kỳ làm mới. FR-EXBOT-093 quy định DO tự làm mới khi dữ liệu cũ, nhưng nếu DO hoàn toàn không thể truy cập trong lúc xử lý request, hành vi của ExBot Worker chưa được định nghĩa: trả về response một phần (thiếu currentTick/rangeState), hay trả về HTTP 503? BA cần bổ sung alternate flow A6 cho trường hợp MarketDataDO không khả dụng. | Tester không thể thiết kế test case cho tình huống MarketDataDO bị lỗi trong ngữ cảnh monitor-status. | Mở |
| I-006 | High | UC §4; srs/spec.md FR-EXBOT-005; US-EXBOT-002 | UC §4 không có alternate flow cho `status='paused'`. SRS FR-EXBOT-005 định nghĩa màn hình trạng thái cho bot đang pause phải hiển thị "Paused — hedge is maintained, LP is maintained." US-002 cũng không có AC cho trạng thái paused. BA cần bổ sung alternate flow cho `status='paused'` vào UC §4, mô tả message và hành vi hiển thị; đồng thời bổ sung AC tương ứng vào US-002. | Tester không thể thiết kế test case cho trạng thái paused vì cả UC lẫn US đều không mô tả nó. | Mở |
| I-007 | Medium | UC §7 FR Trace; srs/spec.md FR-EXBOT-003 | UC §6 FR Trace bao gồm FR-EXBOT-003 (Bot Lifecycle State Tracking — định nghĩa 18 trạng thái lifecycle và chuỗi khởi tạo). Phần lớn FR-003 liên quan đến khởi tạo bot và chuyển trạng thái, không phải đọc trạng thái. Nếu trace này có chủ ý, UC §4 cần bổ sung alternate flow cho đủ 18 trạng thái lifecycle (ví dụ: `lp_rebalancing`, `lp_closing`, `error`). BA cần xác nhận: FR-003 trace có chủ ý không? Nếu có, cần bổ sung alternate flow cho các trạng thái còn thiếu. Nếu không, xóa FR-003 khỏi FR Trace. | Tester cần biết 18 trạng thái lifecycle có nằm trong phạm vi UC này không hay chỉ là tập con đang hiển thị. | Mở |
| I-008 | Medium | UC §4 A1; erd.md bảng bots; srs/spec.md FR-EXBOT-050 | UC §4 A1 nêu response bao gồm `safe_mode_reason`, nhưng bảng `bots` trong erd.md không có column `safe_mode_reason`. Trường này cũng không có trong danh sách đọc D1 ở bước 3. Bảng `bots` có `health_status` có thể dùng cho mục đích này, nhưng chưa được xác nhận. BA/Tech Lead cần xác định column D1 nào lưu `safe_mode_reason` (hoặc có cần thêm column mới không) và cập nhật UC §3 bước 3 để đọc trường đó. | Tester không thể xác minh `safe_mode_reason` được trả về đúng trong response A1 nếu không biết column nguồn. | Mở |
| I-009 | Medium | UC §4 A2; erd.md; srs/spec.md FR-EXBOT-034 | UC §4 A2 nêu response bao gồm "cooldown end timestamp" để giao diện tính "còn Xh". Tuy nhiên, các bảng `bots` và `hedge_legs` trong erd.md không có column nào lưu thời điểm kết thúc cooldown. FR-EXBOT-034 định nghĩa cooldown là 4 giờ sau khi stop kích hoạt nhưng không chỉ định column D1 nào lưu thời gian kết thúc. BA/Tech Lead cần: định nghĩa column D1 lưu thời gian kết thúc cooldown (có thể cần thêm column mới, hoặc tính từ `hedge_legs.stop_trigger_crossed_at + 4h`) và cập nhật UC §3 bước 3 để đọc trường đó. | Tester không thể xác minh "còn Xh" được tính đúng nếu không biết trường D1 nào là nguồn. | Mở |

---

## Câu hỏi đã được trả lời

| ID | Ưu tiên | Tham chiếu | Nội dung câu hỏi | Câu trả lời | Người trả lời | Ngày | Trạng thái |
|----|---------|------------|------------------|-------------|---------------|------|------------|

---

## Câu hỏi tạm hoãn

| ID | Ưu tiên | Tham chiếu | Nội dung câu hỏi | Lý do hoãn | Trạng thái |
|----|---------|------------|------------------|------------|------------|
