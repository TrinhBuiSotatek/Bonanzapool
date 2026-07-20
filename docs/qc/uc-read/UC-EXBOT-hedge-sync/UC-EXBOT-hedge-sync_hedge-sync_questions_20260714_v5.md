# Question Backlog

| UC ID | UC-EXBOT-hedge-sync |
|-------|---------------------|
| Ngày tạo | 2026-06-30 |
| Ngày cập nhật | 2026-07-16 |
| Người tạo | QC UC Read ExBot Agent |
| Version | v5 |
| Nguồn audited | UC-EXBOT-hedge-sync_hedge-sync_audited_20260706_v3.md |
| Ghi chú | v5: Q3 answered bởi Tech Lead (2026-07-14). Q-N1 và Q11 answered bởi BA (2026-07-14, qc-responses-2026-07-14.md) — chuyển từ Deferred → Answered. Q1 answered bởi khách (zen) (2026-07-16) — chuyển từ Open → Answered. Q7 không còn bị blocked bởi Q1 nhưng vẫn Open — pending zen. Q2, Q6 vẫn Open — pending zen. |

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q2 | High | UC §3 step 8-9; FR-EXBOT-035; SPEC §19.5 | INV-STOP protocol (§19.5) được mô tả là "protected cancel→place", nhưng chi tiết cụ thể là: (a) place trước rồi cancel sau, hay (b) cancel trước rồi place sau? OQ-EXBOT-002 trong SRS note "Does HL support place-before-cancel stop replacement?". Kết quả quyết định nội dung test case cho bước F1-09 và F1-10. | Không biết path (a) hay (b) → không thể viết test case cho cancel/place sequence và dự kiến vùng thời gian 0-stop tồn tại. | Open — ⏳ Pending zen — OQ-EXBOT-002 |
| Q6 | Medium | FR-EXBOT-036; OQ-EXBOT-011 | `partial_repair` dùng drift_threshold = `deltaErrorUsd > max($25, lpValueUsd × 3%)`. `lpValueUsd` trong công thức được tính như thế nào? OQ-EXBOT-011 (SRS §9) chưa xác nhận formula. | Nếu `lpValueUsd` chưa có formula xác nhận, expected result của test reconcile partial fill không thể tính ra con số cụ thể. | Open — ⏳ Pending zen — OQ-EXBOT-011 |
| Q7 | Medium | UC §3 step 12-13; FR-EXBOT-030 | stop_trigger_px được tính lại sau reconcile, nhưng nếu delta=0 (không có lệnh HL) thì `entry_price` và `liq_price` có được update hay vẫn giữ giá trị cũ? UC step 12-13 ngầm định reconcile luôn trả về giá trị mới, nhưng nếu delta=0 thì `clearinghouseState` có cho `entry_price` mới không? | Nếu `entry_price` không đổi, việc tính lại `stop_trigger_px` cũng cho kết quả cũ → stop replacement trong luồng A6 có thể là no-op. Expected result của AC-11 bị mơ hồ. | Open — ⏳ Pending zen (Q1 đã được trả lời: stop replacement vẫn chạy khi delta=0; Q7 hỏi riêng về việc entry_price/liq_price có được cập nhật từ clearinghouseState hay không) |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Status |
|----|----------|-----|----------|-----------------|--------|
| Q4 | Medium | FR-EXBOT-091; OQ-EXBOT-015 | HLRateLimit và Redlock: rate-limit weight có được tiêu thụ TRƯỚC hay SAU khi giành lock không? | OQ-EXBOT-015 (SRS §9) vẫn Open. Chưa có tài liệu nào xác nhận ordering này. Không block test design hiện tại. | Deferred |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q1 | High | UC §3 step 5 note; OQ-EXBOT-013 (SRS §9) | Khi delta tính bằng 0, Worker có nên bỏ qua lệnh HL và đi thẳng vào INV-STOP stop replacement hay nên abort toàn bộ hedge-sync? UC step 5 note ghi "Behavior pending OQ-EXBOT-013". Nếu skip stop replacement thì stop có thể bị stale khi giá ETH đóng hoặc mở/đóng range. | **Skip lệnh HL, tiếp tục chạy stop replacement.** delta = 0 chỉ có nghĩa là kích thước vị thế đang đúng — mức stop phù hợp vẫn có thể đã dịch chuyển theo giá. Nếu abort thì sẽ tạo ra tình huống ngược: những giai đoạn ổn định (delta không đổi) sẽ khiến stop bị stale. Việc đặt lệnh HL và cập nhật stop là hai mối quan tâm độc lập với nhau. | Khách (zen) | 2026-07-16 | Answered |
| Q3 | High | UC §3 step 4-6; FR-EXBOT-060; OQ-EXBOT-014 | Worker có phải fetch HL marginSummary (để cập nhật margin_status) TRƯỚC hay SAU khi giành Redlock không? OQ-EXBOT-014 trong SRS: "marginSummary fetch ordering in hedge-sync preflight: does the Worker fetch marginSummary before or after acquiring the lock?" Ordering này ảnh hưởng trực tiếp đến lock TTL design: nếu fetch sau lock thì weight HL bị tính vào thời gian giữ khóa. | Worker phải fetch HL marginSummary **SAU** khi giành User Lock (Redis Redlock) để tránh dùng dữ liệu margin cũ do worker khác vừa thay đổi position. Flow đúng: **Lock → fetch marginSummary → cập nhật margin_status → kiểm tra risk → mutation → unlock**. Implication cho test design: (a) lock TTL phải tính bao gồm cả thời gian fetch HL marginSummary; (b) test case timeout scenario phải giả định HL marginSummary call xảy ra trong khi lock đang giữ; (c) nếu HL marginSummary call bị timeout/chậm, heartbeat extend() phải được gọi trước khi TTL=90s hết. | Tech Lead | 2026-07-14 | Answered |
| Q-N1 | Low | UC §7 FR Trace; spec.md FR-EXBOT-092 | UC §7 FR Trace liệt kê `FR-EXBOT-026` (User Lock conceptual) nhưng chưa có `FR-EXBOT-092` (Redlock interface chi tiết: acquire/extend/release, TTL=90s, idempotencyKey pattern, Lua script ownership check). FR-092 được thêm vào SRS trong arc-migration pass 2026-07-03. | `FR-EXBOT-092` (Redlock interface: acquire/extend/release, TTL=90s, idempotencyKey pattern) đã được bổ sung vào UC §7 FR Trace. Gap phát sinh do FR-092 được thêm vào SRS trong arc-migration pass 2026-07-03 nhưng UC chưa được cập nhật kịp thời. | BA — docs/BA/qc-responses-2026-07-14.md | 2026-07-14 | Answered |
| Q11 | Low | UC §3 step 1-3; FR-EXBOT-011/026/027 | UC mô tả rất chi tiết thứ tự: (1) insert idempotency → (2) check stateVersion → (3) acquire lock. Nhưng UC không giải thích lý do kinh doanh tại sao phải theo đúng thứ tự này. | Thứ tự (1) idempotency → (2) stateVersion → (3) lock có business rationale rõ ràng: **Step 1 trước** — `FR-EXBOT-011`: chặn duplicate delivery ngay từ đầu, trước khi tiêu thụ bất kỳ tài nguyên nào. **Step 2 trước lock** — `FR-EXBOT-027`: check stateVersion trước lock để discard message stale mà không tốn TTL của Redlock. **Step 3 sau cùng** — `FR-EXBOT-092`: acquire lock muộn nhất có thể để minimize thời gian giữ lock → giảm rủi ro timeout và contention. | BA — docs/BA/qc-responses-2026-07-14.md | 2026-07-14 | Answered |
| Q12 | Low | flows.md F-02; UC diagram | UC có Mermaid placeholder generic chưa được điền. Diagram module-level có trong flows.md F-02 đủ để tester suy ra luồng. | Mermaid placeholder generic trong UC đã được thay bằng reference rõ ràng đến **flows.md F-02: Hedge-Sync Execution (Delta-Only)**. F-02 cover luồng chính: hedge-sync queue → Hedge-Sync Worker → Redis Redlock acquire/release → Hyperliquid clearinghouseState + adjustShortDelta → reconcile queue → Aurora PostgreSQL update hedge_legs. | BA — docs/BA/qc-responses-2026-07-14.md | 2026-07-14 | Answered |
| Q5 | Medium | UC §4 A4; FR-EXBOT-040 | Partial fill (status='partial') có tăng `failure_count` trong circuit breaker không? | Partial fill **không tăng** `failure_count`. Partial fill routes sang `partial_repair` queue (FR-EXBOT-036). Chỉ `status='failed'` (A3) mới gọi `incrementCircuitBreaker`. UC A4 đã được update. | BA — docs/BA/qc-notes-temp.md | 2026-07-02 | Answered |
| Q8 | Medium | UC §7 FR Trace vs SRS §7 UC Inventory | UC §7 FR Trace thiếu FR-020, FR-021, FR-035; UC thêm FR-036 không có trong SRS §7. | UC §7 thêm FR-020/021/035. SRS §7 UC Inventory thêm FR-036 cho uc-hedge-sync. FR Trace đã sync. | BA — docs/BA/qc-notes-temp.md | 2026-07-02 | Answered |
| Q9 | Medium | UC §2 Preconditions; FR-EXBOT-040 | Worker có kiểm tra lại `circuit_breakers.state` trước khi chạy HL mutation không? | Worker **recheck** `circuit_breakers.state` tại execution time (step 2). Nếu `open` → discard với `status='skipped'`. UC step 2 đã được update. | BA — docs/BA/qc-notes-temp.md | 2026-07-02 | Answered |
| Q10 | Low | UC §3 A2/A6; FR-EXBOT-023 | Cột `reason` trong `rebalance_attempts` ghi giá trị gì khi A2 (stateVersion mismatch) và A6 (delta=0)? | Cả hai = **original `RebalanceReason[]` từ message payload**. Canonical enum giữ nguyên per FR-EXBOT-023. UC A2 và A6 đã được update. | BA — docs/BA/qc-notes-temp.md | 2026-07-02 | Answered |

---

Priority: H = High (chặn thiết kế), M = Medium (ảnh hưởng scope), L = Low (cần biết thêm)
Status: Open | Answered | Deferred
