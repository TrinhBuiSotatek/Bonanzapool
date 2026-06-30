# Question Backlog

| UC ID | UC-EXBOT-hedge-sync |
|-------|---------------------|
| Ngày tạo | 2026-06-30 |
| Người tạo | QC UC Read ExBot Agent |
| Version | v1 |
| Nguồn audited | UC-EXBOT-hedge-sync_hedge-sync_audited_20260630_v1.md |

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | High | UC §3 step 5 note; OQ-EXBOT-013 (SRS §9) | Khi delta tính bằng 0, Worker có nên bỏ qua lệnh HL và đi thẳng vào INV-STOP stop replacement hay nên abort toàn bộ hedge-sync? UC chỉ ghi "Behavior pending OQ-EXBOT-013". Nếu skip stop replacement thì stop có thể bị stale khi giá ETH đóng hoặc mở/đóng range. | Nếu delta=0 nhưng stop cần cập nhật (do giá entry thay đổi từ reconcile trước), việc bỏ qua stop replacement là bug. Tester không thể viết expected result cho luồng A6 này. | Open |
| Q2 | High | UC §3 step 8-9; FR-EXBOT-035; SPEC §19.5 | INV-STOP protocol (§19.5) được mô tả là "protected cancel->place", nhưng chi tiết cụ thể là: (a) place trước rồi cancel sau, hay (b) cancel trước rồi place sau, hay (c) các trường hợp nào đi đường (a) vs (b)? OQ-EXBOT-002 trong SRS note "Does HL support place-before-cancel stop replacement?". Kết quả quyết định nội dung test case cho bước F1-09 và F1-10. | Không biết path (a) hay (b) -> không thể viết test case cho cancel/place sequence và dự kiến vùng thời gian 0-stop tồn tại. | Open |
| Q3 | High | UC §3 step 6; FR-EXBOT-060; SRS §FR-060 | Worker có phải fetch HL marginSummary (để cập nhật margin_status) TRƯỚC hay SAU khi giành UserLockDO không? OQ-EXBOT-014 trong SRS: "marginSummary fetch ordering in hedge-sync preflight: does the Worker fetch marginSummary before or after acquiring UserLockDO?" Ordering này ảnh hưởng trực tiếp đến lock TTL design: nếu fetch trước lock thì TTL 90s có thể hết trước khi lệnh xong; nếu fetch sau lock thì weight HL bị tính vào thời gian giữ khóa. | Nếu fetch sau lock mà mất nhiều thời gian, heartbeat có thể bị bỏ lỡ -> khóa tự động giải phóng -> race condition. Tester không thể viết test cho timeout scenario. | Open |
| Q5 | Medium | UC §4 A4; FR-EXBOT-040; SRS §FR-040 | "Consecutive failures" trong circuit breaker được UC định nghĩa là "rolling 24h window, no intervening success". Nhưng khi có PARTIAL fill (status='partial', không phải 'success' hay 'failed') -- partial có được coi là "failure" để tăng failure_count không? | Nếu partial fill không tăng failure_count, circuit có thể không bao giờ open dù có nhiều partial fail. | Open |
| Q6 | Medium | FR-EXBOT-036; SRS §FR-036; OQ-EXBOT-011 | `partial_repair` dùng threshold riêng hay cùng `drift_threshold` với light-check không? Nếu cùng, `lpValueUsd` trong công thức `max($25, lpValueUsd × 3%)` được tính như thế nào? OQ-EXBOT-011 (SRS §9) chưa xác nhận formula của `lpValueUsd`. | Nếu `lpValueUsd` chưa có formula xác nhận, expected result của test reconcile partial fill không thể tính ra con số cụ thể. | Open |
| Q7 | Medium | UC §3 step 12-13; FR-EXBOT-030; SRS §FR-030 | stop_trigger_px được "tính lại" sau reconcile, nhưng công thức chỉ dùng entry_price và liq_price từ reconcile. Câu hỏi: nếu delta=0 (không có lệnh HL) thì entry_price và liq_price có được update hay vẫn giữ giá trị cũ? UC step 12-13 ngầm định rằng reconcile luôn trả về giá trị mới, nhưng nếu delta=0 và không có lệnh HL nào được gửi thì clearinghouseState có cho entry_price mới không? | Nếu entry_price không đổi (vì delta=0, không có fill), việc tính lại stop_trigger_px cũng cho kết quả cũ -> stop replacement trong luồng A6 có thể là no-op. Expected result của AC-11 bị mơ hồ. | Open |
| Q8 | Medium | UC §7 FR Trace vs SRS §7 UC Inventory | UC §7 FR Trace của `uc-hedge-sync` ghi: "FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-036". SRS §7 UC Inventory cho `uc-hedge-sync` ghi: "FR-EXBOT-020, 021, 022, 024, 025, 026, 027, 035". Các FR khác nhau: UC thiếu FR-020 (LP position amount calculation), FR-021 (BigDecimal target computation), FR-035 (INV-STOP); UC thêm FR-036 (partial_repair) không có trong SRS §7. | FR-020 (Uniswap V3 AMM formula) và FR-021 (BigDecimal normalizeTargetRatioBps) là phần cốt lõi của hedge-sync; nếu không có trong FR Trace thì test sẽ thiếu coverage cho tính toán target size. | Open |
| Q9 | Medium | UC §2 Preconditions; SRS §FR-026; FR-EXBOT-040 | Nếu circuit chuyển sang `open` trong khoảng thời gian giữa light-check enqueue và Worker execute (vd: một hedge-sync khác thất bại trong lúc message đang chờ trong queue), Worker có kiểm tra lại `circuit_breakers.state` trước khi chạy HL mutation không? Nếu có thì ở bước nào (trước lock, sau lock)? Nếu không có recheck, Worker sẽ chạy hedge-sync khi circuit đang `open`. | Race condition này không được document. `stateVersion` check (FR-EXBOT-027) chỉ bảo vệ stale bot config, không bảo vệ circuit state. Tester không biết expected behavior khi circuit chuyển open giữa enqueue và execute. | Open |
| Q10 | Low | UC §3 A2/A6; FR-EXBOT-023; ERD rebalance_attempts | Cột `reason` trong `rebalance_attempts` ghi giá trị gì khi: (a) A2 (stateVersion mismatch, status='skipped') và (b) A6 (delta=0)? RebalanceReason enum canonical (spec.md FR-EXBOT-023) không có giá trị nào tương ứng với delta=0 hay stateVersion mismatch. UC:57 chỉ ghi "Log reason in rebalance_attempts" mà không chỉ định giá trị cụ thể. | Ảnh hưởng expected result khi test audit log cho cả hai luồng A2 và A6. | Open |

Priority: H = High (chặn thiết kế), M = Medium (ảnh hưởng scope), L = Low (cần biết thêm)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q6 | Medium | FR-EXBOT-036; SRS §FR-036 | `partial_repair` dùng cùng `drift_threshold` với light-check hay threshold riêng? | Cùng threshold canonical `drift_threshold = deltaErrorUsd > max($25, lpValueUsd × 3%)` — FR-EXBOT-036 AC dùng tên `drift_threshold` mà không định nghĩa lại, dẫn chiếu đến định nghĩa trong frd.md:165 và backbone.md:911. Không có threshold riêng cho `partial_repair`. Phần còn lại (`lpValueUsd` chưa có formula xác nhận — OQ-EXBOT-011) tách thành câu hỏi mới Q6 (giữ Open). | QC Investigation — 2026-06-30 | 2026-06-30 | Answered |
| Q9 | Medium | UC §2 Preconditions; spec.md:152; us-008.md AC-008-2 | Ai/khi nào kiểm tra `circuit_breakers.state`? | (1) Light-check kiểm tra circuit **trước khi enqueue** `hedge-sync` (`circuit_breakers.state != 'open'`) — xác nhận tại spec.md:152 FR-EXBOT-012. (2) Worker gọi `allowHedgeSync` tại execution time để claim `half_open` probe slot atomically (`half_open_probe_used` 0→1) — xác nhận tại us-008.md AC-008-2 và spec.md:360. Phần còn lại (race condition circuit chuyển `open` giữa enqueue và execute) giữ Open trong Q9. | QC Investigation — 2026-06-30 | 2026-06-30 | Answered |
| Q10 | Low | UC §3 A2; spec.md:276 FR-EXBOT-027 | A2 (stateVersion mismatch): `rebalance_attempts` có được ghi không? | **Có** — spec.md:276 FR-EXBOT-027 xác nhận rõ: "the worker shall discard the message (record `rebalance_attempts.status='skipped'`)". UC:53 A2 cũng xác nhận "discard; status='skipped'". Phần còn lại (giá trị cụ thể của cột `reason` cho A2 và A6) giữ Open trong Q10. | QC Investigation — 2026-06-30 | 2026-06-30 | Answered |
| Q11 | Low | UC §3 step 1-3; FR-EXBOT-011; FR-EXBOT-027 | Tại sao thứ tự bước 1 (insert idempotency) → 2 (check stateVersion) → 3 (acquire lock) phải theo đúng thứ tự này? | Thứ tự có lý do kỹ thuật được document rõ: (1) Insert idempotency trước mọi thứ — spec.md:142 FR-EXBOT-011 yêu cầu insert "at the start of processing"; UNIQUE conflict → exit ngay, không tốn D1 read hay lock. (2) Check stateVersion trước lock — spec.md:276 FR-EXBOT-027 phát biểu explicit "Before acquiring the UserLockDO lease"; nếu message stale thì không cần chiếm lock, tránh block worker khác. (3) Acquire lock sau cùng — chỉ giữ lock trong thời gian thực sự cần thiết cho HL mutation. Đây là ràng buộc correctness có nguồn document, không phải implementation detail. | QC Investigation — 2026-06-30 | 2026-06-30 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Status |
|----|----------|-----|----------|-----------------|--------|
| Q4 | High | UC §3 step 5-6; FR-EXBOT-091; SRS §FR-091 | HLRateLimitDO và UserLockDO: rate-limit weight có được tiêu thụ TRƯỚC hay SAU khi giành lock không? | OQ-EXBOT-015 (SRS §9) vẫn Open. Chưa có tài liệu nào xác nhận ordering này. Cần BA/Dev xác nhận khi thiết kế triển khai FR-EXBOT-091. | Open |
| Q12 | Low | flows.md F-02; UC chưa có diagram | UC có Mermaid placeholder generic chưa được điền. Diagram module-level có trong flows.md F-02 (actors: queue, worker, DO, HL API, D1) nhưng không phải UC-level diagram. | Không block test design — flows.md F-02 đủ để tester suy ra luồng. BA điền UC diagram khi có thời gian. | Open |
