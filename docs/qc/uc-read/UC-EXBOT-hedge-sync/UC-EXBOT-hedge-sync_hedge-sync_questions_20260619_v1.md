# Question Backlog — UC-EXBOT-hedge-sync

> Generated: 2026-06-19  
> Source files: `docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260618_v1.md`

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-01 | High | UC §3 Main Flow Bước 5-6; SRS FR-EXBOT-022 | UC không mô tả hành vi khi `delta = 0` (tức là kích thước short thực tế đã bằng kích thước mục tiêu). Theo logic delta-only, không có lệnh HL nào nên được gửi và worker nên ghi `status='skipped'` hoặc `status='no_action'`. Tuy nhiên UC không định nghĩa luồng này. BA/Tech Lead vui lòng xác nhận: khi delta = 0, worker ghi `rebalance_attempts` với status gì, và có update `queue_idempotency.state='succeeded'` không? | Tester không thể viết test case cho edge case delta = 0 vì expected result chưa được định nghĩa | Open |
| I-02 | High | UC §A5; SRS FR-EXBOT-033; FRD §FR-EXBOT-031 | UC §A5 mô tả luồng khi `stop_replacing_started_at` stuck > 60s như sau: "Enter SAFE_MODE (see uc-deep-audit.md — FR-EXBOT-016 secondary detection path)". Đây là mô tả **sai** và **thiếu** vì: (1) SRS FR-EXBOT-033 định nghĩa rõ **primary detection là light-check** (≤5 min), không phải deep-audit; (2) deep-audit chỉ là secondary backstop. UC hoàn toàn bỏ sót luồng primary (light-check detect và enter SAFE_MODE trong vòng 5 phút), tạo ra ấn tượng sai rằng chỉ deep-audit mới detect được. BA/Tech Lead vui lòng cập nhật A5 để: (a) mô tả primary path = light-check enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE trong ≤5 min, (b) đề cập secondary path = deep-audit. | Tester sẽ thiết kế test sai nếu chỉ kiểm tra deep-audit interval (6h/1h) thay vì light-check interval (5 min) cho scenario này — dẫn đến bỏ sót test case SLA quan trọng | Open |
| I-03 | High | UC §A3; SRS FR-EXBOT-040; US-008 AC-1 | UC §A3 và SRS FR-EXBOT-040 đều ghi "3 consecutive failures within 24h" nhưng không định nghĩa rõ "consecutive" có nghĩa là gì trong ngữ cảnh này: (a) 3 lần thất bại liên tiếp bất kể thời gian giữa các lần, (b) 3 lần thất bại trong rolling window 24h không nhất thiết liên tiếp, hay (c) 3 lần thất bại liên tiếp mà không có lần thành công nào xen giữa, trong window 24h? US-008 AC-1 ghi "2 previous failed attempts within the last 24h → third fails → circuit opens" — ngụ ý rolling window, nhưng từ "consecutive" trong SRS mâu thuẫn với diễn đạt này. Tech Lead vui lòng xác nhận: khi nào failure_count reset về 0? Nếu có 1 lần success giữa 3 lần fail, circuit có mở không? | Tester cần biết chính xác điều kiện để viết test circuit breaker; nếu định nghĩa sai, test có thể pass/fail sai | Open |
| I-04 | Medium | SRS FR-EXBOT-060; UC §3 Main Flow; FRD §4.7 | SRS FR-EXBOT-060 định nghĩa: margin status được update "just before hedge-sync (fetch HL marginSummary)". UC hoàn toàn bỏ sót bước này. Không rõ: (a) bước fetch `marginSummary` xảy ra ở vị trí nào trong flow (trước hay sau khi acquire lock?), (b) nếu `margin_status='warning'` được phát hiện tại thời điểm này thì size-increase hedge adjustment bị chặn như thế nào (UC không mô tả), (c) nếu `margin_status='critical'` (×2 consecutive) thì hedge-sync abort và enter SAFE_MODE ngay không? | Tester không thể test các trường hợp `margin_warning` và `margin_critical` xảy ra ngay tại thời điểm hedge-sync mà không có flow rõ ràng trong UC | Open |
| I-05 | Medium | SRS FR-EXBOT-091; UC §3 Main Flow | UC không đề cập bất kỳ interaction nào với `HLRateLimitDO` trước khi gọi HL. Theo SRS FR-EXBOT-091, mọi HL API call phải khai báo weight trước và nhận `{allowed: boolean, retryAfterMs}`. Nếu `allowed=false`, caller phải re-queue với delay và không gửi lệnh. Hành vi này hoàn toàn vắng mặt trong UC. BA/Tech Lead vui lòng xác nhận: khi `HLRateLimitDO` trả `allowed=false` trong khi hedge-sync đang hold `UserLockDO` lease, worker có release lock trước khi re-queue không? | Thiếu test case quan trọng về rate limit behavior trong hedge-sync | Open |
| I-06 | Medium | SRS FR-EXBOT-080, FR-EXBOT-082; UC §3 Main Flow | UC không đề cập bước giải mã HL agent key (AES-GCM decrypt) trước khi ký lệnh HL. Đây là bước bắt buộc theo FR-EXBOT-080. Không rõ: (a) decrypt xảy ra ở bước nào trong flow, (b) nếu key bị revoke trong khi hedge-sync đang chạy thì worker xử lý thế nào (FR-EXBOT-082 nói vào SAFE_MODE), (c) nếu `expires_at` đã qua thì worker xử lý thế nào. | Tester cần biết các failure path của agent key decryption để thiết kế test case bảo mật và SAFE_MODE | Open |
| I-07 | Low | UC §3 (§5 Postconditions) | UC có 2 mục `## Postconditions` — một ở §5 và một ngay sau §5: mục thứ hai là placeholder template chưa được xóa ("System state reflects the completed operation", "NFR-ADM-005"). Nội dung này không liên quan đến ExBot (NFR-ADM-005 là NFR của module Admin, không phải ExBot). BA vui lòng dọn sạch phần placeholder này. | Gây nhầm lẫn khi đọc UC; Tester có thể nghĩ NFR-ADM-005 áp dụng cho ExBot | Open |
| I-08 | Low | UC §Trigger; SRS flows.md F-01 | UC §Trigger ghi: "User navigates to the relevant screen or initiates the described action." — đây là placeholder template chưa được cập nhật, không mô tả đúng trigger thực tế của UC này. Trigger thực tế là: light-check worker enqueue `hedge-sync` message khi phát hiện `RebalanceReason[]`. BA vui lòng cập nhật mô tả trigger cho đúng. | Khi đọc UC lần đầu, Tester có thể nhầm đây là UC có UI trigger | Open |
| I-09 | Low | UC §7 FR Trace; SRS FR-EXBOT-023 | UC §7 FR Trace liệt kê: `FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-036` — nhưng bỏ sót `FR-EXBOT-021` (LP position amount calculation), `FR-EXBOT-023` (canonical RebalanceReason enum), `FR-EXBOT-030` (stop trigger price computation), `FR-EXBOT-035` (INV-STOP protocol), `FR-EXBOT-040` (circuit breaker), tất cả đều được mô tả trong Main Flow của UC. | Trace không đầy đủ làm khó khăn cho QC khi cần tìm nguồn gốc rule | Open |

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

_(No deferred questions.)_
