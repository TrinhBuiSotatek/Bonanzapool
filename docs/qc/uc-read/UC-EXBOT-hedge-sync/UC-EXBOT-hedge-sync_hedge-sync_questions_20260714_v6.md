# Question Backlog

| UC ID | UC-EXBOT-hedge-sync |
|-------|---------------------|
| Ngày tạo | 2026-06-30 |
| Ngày cập nhật | 2026-07-24 |
| Người tạo | QC UC Read ExBot Agent |
| Version | v6 |
| Nguồn audited | UC-EXBOT-hedge-sync_hedge-sync_audited_20260706_v3.md |
| Ghi chú | v6: Q2, Q6, Q7 answered bởi BA (@hienduong) (2026-07-20, qc-responses-2026-07-20.md) — chuyển từ Open → Answered. **Lưu ý Q7 vs Q1:** Q1 (2026-07-16, zen) trả lời "skip lệnh HL, tiếp tục stop replacement"; Q7 (2026-07-20, BA) trả lời khi delta=0 → `no_op_dust` ngay lập tức, không có stop replacement. Q7 answer mới hơn, có source code reference (`rebalance.ts` line 83–84) → Q7 là nguồn canonical; Q1 cần được hiểu lại: "skip lệnh HL" = no_op_dust, nghĩa là cả stop replacement cũng không chạy khi delta đủ nhỏ (< 0.000001). |

---

## Open Questions

_Không còn câu hỏi mở._

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Status |
|----|----------|-----|----------|-----------------|--------|
| Q4 | Medium | FR-EXBOT-091; OQ-EXBOT-015 | HLRateLimit và Redlock: rate-limit weight có được tiêu thụ TRƯỚC hay SAU khi giành lock không? | OQ-EXBOT-015 (SRS §9) vẫn Open. Chưa có tài liệu nào xác nhận ordering này. Không block test design hiện tại. | Deferred |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q2 | High | UC §3 step 8-9; FR-EXBOT-035; SPEC §19.5 | INV-STOP protocol (§19.5) được mô tả là "protected cancel→place", nhưng chi tiết cụ thể là: (a) place trước rồi cancel sau, hay (b) cancel trước rồi place sau? OQ-EXBOT-002 trong SRS note "Does HL support place-before-cancel stop replacement?". Kết quả quyết định nội dung test case cho bước F1-09 và F1-10. | **Place-before-cancel** là path chính thức theo zen (OQ-EXBOT-002 đã Closed). Sequence chuẩn: (1) Place stop mới → (2) Verify stop mới active (`verifyStopPlaced`) → (3) Cancel stop cũ — chỉ sau khi bước 2 thành công. **Không có vùng 0-stop tại bất kỳ thời điểm nào.** Direct cancel-then-place là forbidden. **Failure case:** Nếu place stop mới thất bại → stop cũ vẫn còn active → `partial_repair` được enqueue. Không vào SAFE_MODE ở bước này. **Test case F1-09/F1-10:** Verify sequence place → verify → cancel; mock place failure → verify stop cũ vẫn còn active và partial_repair được enqueue. | BA — docs/BA/qc-responses-2026-07-20.md | 2026-07-20 | Answered |
| Q6 | Medium | FR-EXBOT-036; OQ-EXBOT-011 | `partial_repair` dùng drift_threshold = `deltaErrorUsd > max($25, lpValueUsd × 3%)`. `lpValueUsd` trong công thức được tính như thế nào? OQ-EXBOT-011 (SRS §9) chưa xác nhận formula. | OQ-EXBOT-011 đã Closed — zen confirmed: `lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount` (principal only, exclude tokensOwed; price = Uniswap pool slot0). `drift_threshold = max($25, lpValueUsd × 3%)`. | BA — docs/BA/qc-responses-2026-07-20.md | 2026-07-20 | Answered |
| Q7 | Medium | UC §3 step 12-13; FR-EXBOT-030 | stop_trigger_px được tính lại sau reconcile, nhưng nếu delta=0 (không có lệnh HL) thì `entry_price` và `liq_price` có được update hay vẫn giữ giá trị cũ? UC step 12-13 ngầm định reconcile luôn trả về giá trị mới, nhưng nếu delta=0 thì `clearinghouseState` có cho `entry_price` mới không? | Khi delta = 0 (hoặc abs < 0.000001): hedge-sync trả về `status: no_op_dust` ngay lập tức — không gọi HL order, không reconcile, không update `entry_price`/`liq_price`, không replace stop. Tất cả giữ nguyên giá trị cũ. `stop_trigger_px` không được tính lại. Confirmed từ develop branch `rebalance.ts` line 83–84 và `handler-impl.ts` (không có stop replacement nào chạy sau `dispatchAction`). **Lưu ý về Q1 vs Q7:** Q1 (zen, 2026-07-16) trả lời "skip lệnh HL, tiếp tục stop replacement" — Q7 answer này làm rõ hơn: khi delta đủ nhỏ (< 0.000001) → no_op_dust, không có stop replacement. Nếu delta=0 theo nghĩa toán học chính xác nhưng abs > 0.000001, flow có thể khác; Q7 answer là nguồn canonical cho trường hợp no_op_dust threshold. | BA — docs/BA/qc-responses-2026-07-20.md | 2026-07-20 | Answered |
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
