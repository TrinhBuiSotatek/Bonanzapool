# Question Backlog — UC-EXBOT-light-check

> Generated: 2026-06-16 Source files: docs/QC/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260616_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | M | uc-light-check.md §3 Step 10 | Schema message hedge-sync ({botId, reasons, stateVersion}) — kiểu dữ liệu chính xác, format, required fields là gì? | Tester không thể xác minh message payload đúng hay sai nếu không có schema | Open |
| Q2 | M | uc-light-check.md §3 Step 11 | Schema message price-near-stop-audit — fields, types là gì? | Tester cần biết message content để viết AC cho stop-audit consumer | Open |
| Q3 | L | FR-EXBOT-011 | Schema message partial_repair (reason='stop_replacing_overrun') — fields, types là gì? | Cần để test stop_replacing_overrun detection path | Open |
| Q4 | H | frd.md FR-EXBOT-092 | MarketDataDO cache TTL và refresh cadence là bao lâu? Nếu cache stale/unavailable, light-check có fallback không? | Cache stale → sai lpEthAmount → sai hedge target → false positive/negative drift detection | Open |
| Q5 | M | uc-light-check.md §3 Step 2 | Khi số bot active trong 1 shard > 500 (LIMIT 500), Scan Worker có tiếp tục scan trong cùng cron tick không? Behavior overflow là gì? | Ở scale 10.000 bots, >500/shard hoàn toàn có thể xảy ra | Open |
| Q6 | M | N/A (Missing) | Khi Light-Check Worker không đọc được D1 (network/timeout) → hành vi là gì? Bot bị skip không? queue_idempotency có cập nhật không? | Tester không thể viết negative test cho D1 failure path | Open |
| Q7 | M | N/A (Missing) | Khi chunkSendBatch enqueue hedge-sync thất bại → hành vi là gì? Có retry không? Bot có mất đợt check này không? | Cần để test queue enqueue failure path | Open |
| Q8 | L | uc-light-check.md frontmatter linked_stories | US-006 (delta-only hedge-sync) mô tả hedge-sync worker behavior, không phải light-check actor. linked_stories cần cập nhật để phản ánh đúng ranh giới UC. | Tránh nhầm lẫn khi tester mapping US sang test case | Open |
| Q9 | M | FR-EXBOT-031 vs FR-EXBOT-016 | stop_trigger_crossed_at stuck > 30 min → SAFE_MODE: ai là người detect chính — light-check hay deep-audit? UC không đề cập. | Tester cần biết để viết test case cho SAFE_MODE trigger path đúng component | Open |
| Q10 | L | uc-light-check.md §4 A4 | range_boundary_near threshold "90%" — tính từ đâu, 90% khoảng cách tick hay 90% giá trị tuyệt đối? | Không xác định threshold → không thể viết boundary test case | Open |
| Q11 | M | uc-light-check.md §4 A2 | Khi circuit_state='half_open' và half_open_probe_used đã = 1 (probe đã dùng): light-check suppress hoàn toàn hay trigger reset attempt? | Cần để test half_open với probe đã dùng — edge case quan trọng | Open |
| Q12 | H | GAP-004; project-context-master Q-012 | wethIndex đã xác nhận cho Base và OP là gì? MarketDataDO cache TTL là bao nhiêu? | wethIndex sai → hedge target sai; cache TTL chưa biết → không test được staleness behavior | Open |
| Q13 | H | GAP-005; project-context-master Q-011 | Giao thức stop replacement đã xác nhận chưa? stop_replacing_overrun detection có phụ thuộc NV-1/NV-3 không? | INV-STOP protocol và stop_replacing_started_at stuck detection đều liên quan | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know) Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|