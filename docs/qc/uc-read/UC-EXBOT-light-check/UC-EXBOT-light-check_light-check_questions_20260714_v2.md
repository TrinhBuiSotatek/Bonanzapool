# Question Backlog

> UC ID: UC-EXBOT-light-check  
> Generated: 2026-06-30  
> Updated: 2026-07-14 (update câu trả lời từ BA responses 2026-07-14; ẩn các câu đã Answered khỏi Open Questions)  
> Source files: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260706_v3.md  
> Author: QC Q&A Agent  
> Version: v2

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| v3-I-03 | High | UC step 9; SRS OQ-EXBOT-12; SRS erd.md | UC step 9 tham chiếu `fundingApr7dPct` từ bảng `funding_rolling_metrics`, nhưng bảng này không có trong ERD (`srs/erd.md`). ERD chỉ có `funding_daily_metrics`. (1) `funding_rolling_metrics` là bảng, view, hay materialized view? (2) Khi nào được cập nhật? (3) Schema gồm những field gì? Ngoài ra OQ-EXBOT-12 (7d APR aggregation formula) vẫn Open trong SRS §9. **Partially resolved 2026-07-14:** `funding_rolling_metrics` đã được bổ sung vào ERD (bảng thật, schema đã biết). Tuy nhiên bảng được cập nhật bởi `bnza-market-cron` worker — **chưa implement ở v1**. Bảng có thể trống; strategy engine fallback sang `fundingRate × 8760` khi không có data. OQ-EXBOT-12 vẫn chưa chính thức closed. | Test case cho `funding_alert` (AC-LC-09) vẫn bị block do `bnza-market-cron` chưa implement ở v1 và OQ-EXBOT-12 chưa closed chính thức. | Partially Resolved — Pending OQ-EXBOT-12 close |
| v3-I-04 | Low | UC step 7; SRS FR-EXBOT-093; SRS OQ-EXBOT-09 | UC step 7 dùng threshold cố định "stale > 5min". SRS FR-EXBOT-093 dùng "stale > 2× refresh interval". Nếu refresh interval = 2.5min thì hai policy tương đương nhau — nhưng OQ-EXBOT-09 (interval chưa được xác định) vẫn Open. BA xác nhận: khi biết refresh interval thực tế, UC step 7 sẽ được update cho khớp với FR-093. | Tester phải biết threshold chính xác để thiết kế boundary test case. Pending zen close OQ-EXBOT-09. | Open — Pending OQ-EXBOT-09 |
| v3-I-06 | Low | SRS §9 OQ-EXBOT-11; UC step 9; AC-LC-07 | SRS §9 OQ-EXBOT-11 (`lpValueUsd` formula) vẫn đánh dấu **Open**, nhưng UC step 9 đã ghi công thức: `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`, và audit v2 đã tạo AC-LC-07 dựa trên công thức này. Nếu zen close OQ-11 với công thức khác, AC-LC-07 và test cases tương ứng cần update. | Tránh tình huống BA/zen close OQ-11 với delta mà QC không biết phải update test cases. | Open — Pending OQ-EXBOT-11 (zen) |

Priority: High = blocks test design, Medium = affects scope/expected result, Low = traceability/quality

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-10 | Low | UC §3 step 5; SRS ERD | UC mô tả idempotency insert nhưng không đề cập `expires_at` field trong `queue_idempotency`. SRS ERD có `expires_at` — Light-Check Worker có set `expires_at` khi insert hay để NULL? Nếu để NULL, table sẽ tích lũy vô hạn theo thời gian. | `expires_at` luôn được set (TTL = 1 phút) khi insert vào `queue_idempotency`. Gap cleanup đã được xử lý: một EventBridge cron job (mỗi 1 giờ) sẽ thực thi `DELETE FROM queue_idempotency WHERE expires_at < now`. Decision này đã được cập nhật vào FR-EXBOT-011 AC trong spec.md và UC step 5. | BA | 2026-07-14 | ✅ Answered |
| v3-I-01 | Low | UC §7 FR Trace; SRS FR-EXBOT-012; FR-EXBOT-040 | UC §7 FR Trace liệt kê FR-EXBOT-013 → 033 nhưng thiếu FR-EXBOT-012 (FR chính của light-check) và FR-EXBOT-040 (Circuit Breaker State Machine). | Đã bổ sung FR-EXBOT-012 (light-check worker logic chính: zero HL calls invariant, circuit breaker suppression, lp_rebalancing skip) và FR-EXBOT-040 (Circuit Breaker State Machine) vào UC §7 FR Trace. | BA | 2026-07-14 | ✅ Answered |
| v3-I-02 | High | US-EXBOT-007 AC-007-1; UC step 10; SRS FR-EXBOT-012 | US-EXBOT-007 AC-007-1 viết: *"the system sets lifecycle_state='lp_rebalancing'"* — ngụ ý light-check set field này. Nhưng UC step 10 và SRS FR-EXBOT-012 nói rõ: light-check KHÔNG set `lifecycle_state='lp_rebalancing'`, đó là trách nhiệm của hedge-sync handler downstream. | AC-007-1 `When` clause đã được sửa. `lifecycle_state='lp_rebalancing'` không phải do light-check set — light-check chỉ detect `range_out` và enqueue message vào hedge-sync queue. Hedge-sync worker là người set `lifecycle_state='lp_rebalancing'` khi bắt đầu xử lý LP rebalance. | BA | 2026-07-14 | ✅ Answered |
| v3-I-07 | Low | SRS flows.md F-01; UC step 11 | F-01 flow diagram trong `srs/flows.md` không có bước nào hiển thị: đọc HL Mark Price Cache tại step 11, enqueue `price-near-stop-audit`, hay logic freeze hedge-sync khi stale. Toàn bộ stop monitoring sub-flow vắng mặt trong diagram. | F-01 đã được update: thêm HL Mark Price Cache participant, thêm stop monitoring sub-flow (step 11) — đọc markPriceUsd, stale check > 120s với band widening + freeze logic, stop trigger guard với PSAQ enqueue. Fixed alt block — circuit half_open branch được thêm. Thêm step 12 overrun check block — atomic safe_mode SET + partial-repair enqueue. | BA | 2026-07-14 | ✅ Answered |
| v3-I-08 | Low | userstories/us-008.md; SRS FR-EXBOT-040 | US-EXBOT-008 (Circuit Breaker) không có changelog entry cho arc-migration 2026-07-04. Nội dung circuit breaker là platform-agnostic, tuy nhiên chưa được BA xác nhận rõ ràng là "không có thay đổi cần thiết cho migration". | US-EXBOT-008 content là platform-agnostic — tất cả ACs chỉ tham chiếu các cột trong bảng `circuit_breakers` và business logic, không có Cloudflare hay AWS-specific terms. Không cần thay đổi cho arc-migration; việc không có changelog entry 2026-07-04 là có chủ ý. | BA | 2026-07-14 | ✅ Answered |
| I-01 | High | UC §3 step 11 note; SRS OQ-EXBOT-017 | Nguồn `hlMarkPrice` dùng để đánh giá stop trigger trong step 11 chưa được xác nhận. Với ràng buộc HL weight = 0 (BR-EXBOT-003), light-check không thể gọi HL để lấy mark price thực. UC đề xuất candidate là `bot_runtime_state.eth_price_usd` nhưng staleness policy hoàn toàn thiếu. | `hlMarkPrice` source = HL Mark Price Cache (ElastiCache Redis) `markPriceUsd` (primary — Fargate HL WS Poller viết); fallback = `bot_runtime_state.eth_price_usd` (last-known từ light-check trước). Stale threshold = 120s → widen near-stop band 2%→4% + freeze hedge-sync. | Tech Lead | 2026-07-03 | ✅ Confirmed |
| I-02 | High | SRS OQ-EXBOT-010 | Công thức tính điều kiện `range_boundary_near` chưa được xác nhận rõ ràng. | OQ-EXBOT-10 closed 2026-07-02: công thức price-based USD được xác nhận. `nearestFraction = min(distToLower, distToUpper) / halfRange`; fires khi `nearestFraction <= rangeBoundaryFraction` (default 0.9). | code (OQ-EXBOT-10 closed) | 2026-07-02 | ✅ Confirmed |
| I-03 | High | SRS OQ-EXBOT-011 | Công thức tính `lpValueUsd` (dùng trong `drift_threshold`) chưa được xác nhận. | `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`. Threshold: `drift_threshold = max($25, lpValueUsd × 3%)`. | code | 2026-07-03 | ✅ Confirmed |
| I-04 | High | SRS OQ-EXBOT-012 | Công thức aggregation 7d funding APR cho `funding_alert` chưa được xác nhận. | Fires khi 7d funding APR < -15%. Primary source: `fundingApr7dPct` từ `funding_rolling_metrics`. Fallback: `fundingRate × 8760`. | code | 2026-07-03 | ✅ Confirmed |
| I-05 | Medium | UC §3 step 10; UC §4 A4 | Khi `RebalanceReason[]` chứa cả `range_out` VÀ các reason khác trong cùng một pass, liệu hedge-sync có được enqueue không hay chỉ `lp_rebalancing` path chạy? | Engine gom tất cả reasons vào `decision.reason[]` và enqueue 1 hedge-sync duy nhất. Light-check không tự set `lifecycle_state='lp_rebalancing'`. | code | 2026-07-03 | ✅ Confirmed |
| I-07 | Medium | UC §3 step 12; SRS FR-EXBOT-033; SRS FR-EXBOT-050 | Khi step 12 chạy (stop replace overrun), cả `bots.lifecycle_state` VÀ `bots.status` đều được update hay chỉ `lifecycle_state`? | Light-Check Worker set cả `bots.status='safe_mode'` VÀ `bots.lifecycle_state='safe_mode'` atomically trong 1 UPDATE — xảy ra trước khi `partial_repair` được enqueue. | code | 2026-07-03 | ✅ Confirmed |
| I-08 | Medium | UC §3 step 4; SRS FR-EXBOT-012 | `next_light_check_at` của các bot bị skip (lp_rebalancing, lp_closing) có được update hay không? | Scan Worker update `next_light_check_at` cho mọi eligible bot (kể cả `lp_rebalancing`, `lp_closing`) trước khi enqueue. | code | 2026-07-03 | ✅ Confirmed |
| I-09 | Medium | UC §3 step 2 | Scan Worker query `LIMIT 500`: khi shard có > 500 bots eligible cùng lúc, các bot vượt LIMIT có được xử lý không? | By design — jitter ±45s deterministic theo `hash(botId)` phân tán bots đều trong 5 phút. Sau downtime, bots vượt LIMIT 500 được xử lý ở cron tick tiếp theo, oldest first. | code | 2026-07-03 | ✅ Confirmed |
| I-11 | Low | UC (Diagram section) | UC có placeholder Mermaid diagram generic thay vì sequence diagram thực. | Trỏ sang **F-01: Queue Fan-Out** trong `srs/flows.md`. | Confirmed | 2026-07-03 | ✅ Confirmed |
| I-12 | Low | UC §3 step 7; SRS FR-EXBOT-093 | UC không mô tả hành vi khi Pool Slot0 Cache stale. | Fail-fast: nếu snapshot stale (> 5 phút) hoặc unreachable → throw ngay tại step 7, skip tick hoàn toàn. | code | 2026-07-03 | ✅ Confirmed |
| I-06 | Medium | UC §3 step 10; SRS FR-EXBOT-010; FR-EXBOT-015 | UC step 10 viết "enqueue lp_rebalancing message + partial_repair" khi phát hiện range_out — mâu thuẫn với SRS FR-EXBOT-015. | 1 message, 1 queue. Chỉ 1 message được enqueue đến partial_repair queue với operation type = LP rebalance. | QC Agent (from SRS FR-EXBOT-010, FR-EXBOT-015) | 2026-06-30 | ✅ Answered |
| I-13 | Low | UC §6; SRS §4 BR-EXBOT-004; BR-EXBOT-007 | UC §6 thiếu reference đến BR-EXBOT-004 và BR-EXBOT-007. | Cả 2 BR tồn tại và áp dụng cho UC này. BR-EXBOT-004: Delta-only hedge adjustment invariant. BR-EXBOT-007: SAFE_MODE is never a terminal state. | QC Agent (from SRS §4) | 2026-06-30 | ✅ Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|
| (No deferred questions.) |  |  |  |  |  |  |  |
