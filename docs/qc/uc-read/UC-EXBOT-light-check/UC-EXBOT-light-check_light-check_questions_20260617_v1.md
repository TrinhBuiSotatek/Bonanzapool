---
title: "Question Backlog — UC-EXBOT-light-check"
date: 2026-06-17
author: qc-qna Agent
version: v1
---

# Question Backlog

> Generated: 2026-06-17
> Source files: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260617_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q-001 | High | frd FR-EXBOT-011; spec FR-EXBOT-033; UC §3 (missing) | UC §3 và §4 hoàn toàn không đề cập đến path xử lý khi `stop_replacing_started_at IS NOT NULL AND age > 60s`. frd FR-EXBOT-011 và spec FR-EXBOT-033 mô tả rõ là phải enqueue `partial_repair` và trigger SAFE_MODE. BA vui lòng thêm path này vào UC §3 (Step 13 mới) hoặc §4 (Alternate A5), và xác nhận đây có thuộc phạm vi light-check không? | Nếu không có trong UC thì tester không thể thiết kế test case cho path này từ tài liệu nguồn. Đây là safety path (SAFE_MODE), bỏ sót sẽ gây rủi ro hệ thống. | Open |
| Q-002 | High | frd FR-EXBOT-011 (3-way price split); UC §3 Step 7; BR-EXBOT-003 | Light-check sử dụng `hlMarkPrice` để phát hiện stop trigger (Step 11), nhưng UC §3 Step 7 chỉ đề cập đọc `sqrtPriceX96` và `currentTick` từ MarketDataDO. BR-EXBOT-003 cấm HL API call từ light-check. BA vui lòng xác nhận: `hlMarkPrice` được lấy từ đâu mà không vi phạm BR-EXBOT-003? Có Durable Object hoặc D1 cache riêng lưu hlMarkPrice không? | Nếu không có nguồn dữ liệu được xác định, tester không thể biết cần setup dữ liệu nào cho test case stop trigger, và không thể verify architecture constraint BR-EXBOT-003 được tuân thủ. | Open |
| Q-003 | High | OQ-EXBOT-10 (spec); frd FR-EXBOT-011; UC §4 A4 | Công thức `range_boundary_near`: "price 90% to upper/lower range" hiện chưa xác định là đo theo tick distance hay price distance. OQ-EXBOT-10 trong spec đang chờ zen xác nhận. BA vui lòng cập nhật frd FR-EXBOT-011 và UC §3 Step 9 sau khi OQ-EXBOT-10 được resolved. | Hai cách đo cho kết quả test input khác nhau hoàn toàn — tester không thể tính boundary value chính xác. | Open |
| Q-004 | High | OQ-EXBOT-11 (spec); frd FR-EXBOT-011; spec FR-EXBOT-012 | `drift_threshold` formula sử dụng `lpValueUsd × 3%`, nhưng cách tính `lp_value_usd` trong `bot_runtime_state` chưa được định nghĩa. OQ-EXBOT-11 đang block FR-EXBOT-012. BA vui lòng xác nhận: `lp_value_usd` được tính thế nào? Cần reference FR nào để tester biết expected value? | Ngưỡng drift là relative (3% của lpValueUsd), nên test input phụ thuộc hoàn toàn vào giá trị này. Không có công thức = không thể tính expected test data. | Open |
| Q-005 | High | OQ-EXBOT-12 (spec); frd FR-EXBOT-011 | `funding_alert` trigger: "7d funding APR < −15%". Công thức tổng hợp 7-day APR (cách lấy funding rate từng giờ, cách annualize) chưa được xác định. OQ-EXBOT-12 đang chờ zen. BA vui lòng cập nhật frd FR-EXBOT-011 với công thức chính xác sau khi OQ-EXBOT-12 được resolved. | Không có công thức = tester không thể tính expected APR từ raw funding data để test trigger. | Open |
| Q-006 | Medium | UC §4 A2; spec FR-EXBOT-028 AC | UC §4 A2 yêu cầu "atomically claim `half_open_probe_used` 0→1" nhưng không chỉ định cơ chế: D1 transaction (CF D1 không có SELECT FOR UPDATE), Durable Object atomic counter, hay CAS? CF D1 không hỗ trợ row-level locking. BA / Tech Lead vui lòng xác định cơ chế atomic claim được sử dụng và document vào spec FR-EXBOT-028. | Tester cần biết cơ chế để thiết kế concurrent delivery test — verify exactly-one probe không thể thực hiện nếu không biết cơ chế. | Open |
| Q-007 | Medium | spec FR-EXBOT-093; UC §3 Step 7 | Khi MarketDataDO cache stale (> 2× refresh interval), spec FR-EXBOT-093 nói DO sẽ log warning và force refresh. Nhưng UC không định nghĩa: Light-Check Worker phải làm gì trong khoảng thời gian chờ refresh? Trả về kết quả đánh giá dựa trên data cũ? Discard message? Wait? | Tester không thể thiết kế test cho stale cache edge case. | Open |
| Q-008 | Medium | UC §3 Step 9; spec FR-EXBOT-023; frd FR-EXBOT-011 | spec FR-EXBOT-023 liệt kê 9 canonical RebalanceReason, nhưng frd FR-EXBOT-011 chỉ mô tả công thức evaluation cho ~7 reason (drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback). `manual_admin` và `recovery_reconcile` không có evaluation criteria trong frd. BA vui lòng xác nhận: light-check có chịu trách nhiệm evaluate `manual_admin` và `recovery_reconcile` không? Nếu không, worker nào set các reason này? | Tester cần biết scope của light-check để không thiết kế test sai worker. | Open |
| Q-009 | Medium | UC §3 Step 10; spec FR-EXBOT-025 AC; US-EXBOT-006 AC-02 | `stateVersion` trong hedge-sync message: UC §3 Step 10 ghi enqueue {botId, reasons, stateVersion} nhưng không chỉ định `stateVersion` được lấy từ field nào trong D1 (đọc tại Step 6?). US-EXBOT-006 AC-02 mô tả stale messages bị discard nhưng không trace về nguồn field. BA vui lòng xác nhận table/column nào cung cấp `stateVersion`. | Tester cần biết để setup đúng `stateVersion` trong queue message khi test stale-message scenario của hedge-sync worker. | Open |
| Q-010 | Low | UC §3 Step 2 | Scan Worker batch size: UC §3 Step 2 ngụ ý LIMIT 500/shard. Khi > 500 bot đến hạn trong 1 cron tick trên cùng 1 shard: bots còn lại có bị defer sang tick tiếp theo không, hay Scan Worker loop query nhiều lần trong cùng 1 tick? | Minor — không block test design cho core behavior; có thể ảnh hưởng scale/load test. | Open |
| Q-011 | Low | frd.md FR-EXBOT-011/012 vs spec.md FR-EXBOT-012/013 | frd.md đánh số FR-EXBOT-011 (light-check logic) / FR-EXBOT-012 (jitter), trong khi spec.md dùng FR-EXBOT-012 / FR-EXBOT-013 cho cùng nội dung đó. Nội dung không conflict nhưng số thứ tự khác nhau gây nhầm lẫn khi cross-reference. BA vui lòng align hoặc thêm cross-reference mapping note. | Minor — không block test design. | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Status |
|----|----------|-----|----------|-----------------|--------|
