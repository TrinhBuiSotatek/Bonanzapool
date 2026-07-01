# Question Backlog

> UC ID: UC-EXBOT-light-check Generated: 2026-06-30 Source files: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260630_v1.md Author: QC Q&A Agent Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-01 | High | UC §3 step 11 note; SRS OQ-EXBOT-017 | Nguồn hlMarkPrice dùng để đánh giá stop trigger trong step 11 chưa được xác nhận. Với ràng buộc HL weight = 0 (BR-EXBOT-003), light-check không thể gọi HL để lấy mark price thực. UC đề xuất candidate là bot_runtime_state.eth_price_usd nhưng chính sách staleness (staleness policy) hoàn toàn thiếu: nếu giá lưu trong D1 đã stale bao lâu thì còn được dùng để evaluate stop trigger? | Tester không thể verify hành vi đúng khi eth_price_usd stale, dẫn đến không thể thiết kế test case cho AC-LC-06 và AC-LC-07. | Open |
| I-02 | High | SRS OQ-EXBOT-010 | Công thức tính điều kiện range_boundary_near chưa được xác nhận: UC mô tả "price 90% to range upper/lower" nhưng không rõ đây là tick-based (currentTick >= tickUpper - 0.10 × (tickUpper - tickLower)) hay price-based (sqrtPrice >= sqrtUpper × 0.90). Hai cách tính cho kết quả khác nhau đáng kể. | Tester không thể xây dựng test data chính xác cho scenario range_boundary_near, dẫn đến test case không reliable. | Open |
| I-03 | High | SRS OQ-EXBOT-011 | Công thức tính lpValueUsd (dùng trong điều kiện drift_threshold: deltaErrorUsd > max($25, lpValueUsd × 3%)) chưa được xác nhận. SRS đề xuất (lpEthAmount × uniPoolPrice) + lpUsdcAmount nhưng chưa được zen confirm. Tester không thể tính expected deltaErrorUsd mà không biết lpValueUsd. | Blocks test case cho AC-LC-14 và mọi test liên quan đến drift_threshold condition. | Open |
| I-04 | High | SRS OQ-EXBOT-012 | Công thức aggregation 7d funding APR cho điều kiện funding_alert chưa được xác nhận. SRS đề xuất candidate nhưng zen chưa confirm annualization formula. Tester không thể tính threshold −15% từ raw data funding_daily_metrics. | Blocks test case cho scenario funding_alert reason. | Open |
| I-05 | Medium | UC §3 step 10; UC §4 A4 | UC step 10 mô tả: nếu RebalanceReason[] chứa range_out, set lifecycle_state='lp_rebalancing' và enqueue lp_rebalancing + partial_repair; các reason khác enqueue hedge-sync. Chưa rõ: nếu RebalanceReason[] chứa CẢ range_out VÀ các reason khác (ví dụ drift_threshold) trong cùng một pass, liệu hedge-sync có được enqueue không hay chỉ lp_rebalancing path chạy? UC §4 A4 chỉ clarify range_boundary_near, không giải quyết trường hợp mixed reasons. | Tester không thể xác định expected behavior khi multiple reasons cùng xuất hiện, đặc biệt khi range_out kết hợp với drift_threshold. | Open |
| I-07 | Medium | UC §3 step 12; SRS FR-EXBOT-033; SRS FR-EXBOT-050 | UC step 12 mô tả khi stop replace overrun phát hiện: "set lifecycle_state='safe_mode'". SRS FR-EXBOT-050 định nghĩa trong SAFE_MODE cần cả bots.status='safe_mode'. Cần làm rõ: khi step 12 chạy, cả bots.lifecycle_state VÀ bots.status đều được update hay chỉ lifecycle_state? Và Light-Check Worker hay partial_repair worker thực hiện update này? | Ảnh hưởng đến verify order of operations trong test — tester cần biết thời điểm chính xác status thay đổi để assert đúng. | Open |
| I-08 | Medium | UC §3 step 4; SRS FR-EXBOT-012 | UC step 4: Scan Worker batch-update next_light_check_at sau khi enqueue. SRS FR-EXBOT-012: light-check skip hoàn toàn khi lifecycle_state IN ('lp_rebalancing','lp_closing') hoặc status='paused'. Câu hỏi: next_light_check_at của các bot bị skip có được update hay không? Nếu không, sau khi thoát trạng thái lp_rebalancing, bot sẽ ngay lập tức eligible cho light-check (next_light_check_at vẫn <= now) thay vì chờ 5 phút. | Ảnh hưởng đến post-recovery scheduling behavior — nếu không update, bot recovery có thể bị flood light-check. | Open |
| I-09 | Medium | UC §3 step 2 | Scan Worker query: SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500. Khi shard có > 500 bots eligible cùng lúc: các bot vượt LIMIT 500 có được xử lý trong Cron cycle tiếp theo (1 phút) không? Hay có pagination/multi-batch mechanism? Không có mô tả về cách xử lý overflow này. | Ảnh hưởng đến NFR-EXBOT-001 (10.000 bots / 5 min) — nếu overflow không được xử lý đúng, một số bot sẽ miss light-check window. | Open |
| I-10 | Low | UC §3 step 5; SRS ERD | UC mô tả idempotency insert nhưng không đề cập expires_at field trong queue_idempotency. SRS ERD có expires_at — Light-Check Worker có set expires_at khi insert hay để NULL? Nếu để NULL, table sẽ tích lũy vô hạn theo thời gian. | Ảnh hưởng đến long-running test scenarios và môi trường test — table bloat có thể gây slow query trong CI. | Open |
| I-11 | Low | UC (Diagram section) | UC có placeholder Mermaid diagram với nội dung generic (User → System) thay vì sequence diagram thực mô tả Cron → Scan → Light-Check → fan-out flow. Diagram thực sự mô tả actor-system interaction sẽ giúp verify timing order của các alternate flows (A1, A2) phức tạp. | Không block test design nhưng tăng risk hiểu sai timing sequence khi thiết kế test cho concurrent scenarios. | Open |
| I-12 | Low | UC §3 step 7; SRS FR-EXBOT-093 | UC không mô tả hành vi khi MarketDataDO cache stale (> 2× refresh interval) trong context light-check: Light-Check Worker có dùng stale data để evaluate RebalanceReason[] hay phải chờ DO refresh? SRS FR-EXBOT-093 định nghĩa forced refresh và warning log nhưng không nói rõ light-check sẽ xử lý thế nào khi đang chờ refresh. | Tester cần biết expected behavior để design test case cho MarketDataDO stale scenario — tránh false positive khi test với stale cache. | Open |

Priority: High = blocks test design, Medium = affects scope/expected result, Low = traceability/quality

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-06 | Medium | UC §3 step 10; SRS FR-EXBOT-010; FR-EXBOT-015 | UC step 10 viết "enqueue lp_rebalancing message + partial_repair" khi phát hiện range_out — mâu thuẫn với SRS FR-EXBOT-015 ngụ ý chỉ dùng 1 queue. | 1 message, 1 queue. SRS FR-EXBOT-010 liệt kê đúng 10 queue, không có queue nào tên lp_rebalancing. SRS FR-EXBOT-015 (verbatim): "transition bots.lifecycle_state to lp_rebalancing and enqueue an LP rebalance operation via the partial_repair queue." Cụm từ "lp_rebalancing message" trong UC mô tả hành động set lifecycle_state, không phải tên queue. Chỉ 1 message được enqueue đến partial_repair queue với operation type = LP rebalance. | QC Agent (from SRS FR-EXBOT-010, FR-EXBOT-015) | 2026-06-30 | Answered |
| I-13 | Low | UC §6; SRS §4 BR-EXBOT-004; BR-EXBOT-007 | UC §6 thiếu reference đến BR-EXBOT-004 và BR-EXBOT-007 dù cả hai BR liên quan trực tiếp đến logic UC. | Cả 2 BR tồn tại và áp dụng cho UC này. SRS §4 (verbatim): BR-EXBOT-004: "Delta-only hedge adjustment is the invariant default. Full close → open in normal hedge-sync is a bug." (apply khi light-check enqueue hedge-sync, step 10). BR-EXBOT-007: "SAFE_MODE is never a terminal state. Every SAFE_MODE path must lead to auto-recovery or bot_safe_close." (apply khi step 12 trigger SAFE_MODE). UC §6 đơn giản bỏ sót 2 reference này — là documentation gap, không phải lỗi logic. QC Lead nên bổ sung BR-EXBOT-004 và BR-EXBOT-007 vào UC §6 Business Rules. | QC Agent (from SRS §4 BR-EXBOT-004, BR-EXBOT-007) | 2026-06-30 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|
| (No deferred questions.) |  |  |  |  |  |  |  |