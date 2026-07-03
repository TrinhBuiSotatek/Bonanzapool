# Question Backlog

> UC ID: UC-EXBOT-light-check  
> Generated: 2026-06-30  
> Updated: 2026-07-03 (cập nhật câu trả lời từ BA/Tech Lead/code)  
> Source files: docs/qc/uc-read/UC-EXBOT-light-check/UC-EXBOT-light-check_light-check_audited_20260630_v1.md  
> Author: QC Q&A Agent  
> Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-02 | High | SRS OQ-EXBOT-010 | Công thức tính điều kiện `range_boundary_near` chưa được xác nhận rõ ràng: code trả lời công thức price-based `nearestFraction = min(distToLower, distToUpper) / halfRange`, fires khi `nearestFraction <= 0.9`. Tuy nhiên ví dụ đi kèm (range $3,000–$3,400: trigger khi giá ≤ $3,020 hoặc ≥ $3,380) mâu thuẫn với công thức — $3,020 và $3,380 đều nằm trong range, chưa chạm boundary. | Theo như ví dụ thì giá trị $3,020 & $3,380 đều nằm trong range thì chưa đạt trigger nhưng docs đang báo là trigger, QC cần BA clear lại giá trị này. | ⏳ Pending BA |
| I-10 | Low | UC §3 step 5; SRS ERD | UC mô tả idempotency insert nhưng không đề cập `expires_at` field trong `queue_idempotency`. SRS ERD có `expires_at` — Light-Check Worker có set `expires_at` khi insert hay để NULL? Nếu để NULL, table sẽ tích lũy vô hạn theo thời gian. BA đã xác nhận `expires_at` luôn được set (TTL = 1 phút), nhưng chưa có giải pháp cho việc thiếu cleanup job purge expired rows. | Ảnh hưởng đến long-running test scenarios và môi trường test — table bloat có thể gây slow query trong CI. Dev team cần thêm scheduled purge. | ⏳ Pending Tech Lead (cleanup solution) |

Priority: High = blocks test design, Medium = affects scope/expected result, Low = traceability/quality

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-01 | High | UC §3 step 11 note; SRS OQ-EXBOT-017 | Nguồn `hlMarkPrice` dùng để đánh giá stop trigger trong step 11 chưa được xác nhận. Với ràng buộc HL weight = 0 (BR-EXBOT-003), light-check không thể gọi HL để lấy mark price thực. UC đề xuất candidate là `bot_runtime_state.eth_price_usd` nhưng staleness policy hoàn toàn thiếu. | `hlMarkPrice` source = `HlMarkDO.markPriceUsd` (primary); fallback = `bot_runtime_state.eth_price_usd` (last-known từ light-check trước). Stale threshold = 120s → widen near-stop band 2%→4% + freeze hedge-sync. Detection latency tối đa ~7 phút. | Tech Lead | 2026-07-03 | ✅ Confirmed |
| I-03 | High | SRS OQ-EXBOT-011 | Công thức tính `lpValueUsd` (dùng trong `drift_threshold`) chưa được xác nhận. | `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`. Threshold: `drift_threshold = max($25, lpValueUsd × 3%)`. Follow code hiện tại. | code | 2026-07-03 | ✅ Confirmed |
| I-04 | High | SRS OQ-EXBOT-012 | Công thức aggregation 7d funding APR cho `funding_alert` chưa được xác nhận. | Fires khi 7d funding APR < -15%. Primary source: `fundingApr7dPct` từ `funding_rolling_metrics` — đọc trực tiếp. Fallback: `fundingRate × 8760` (annualize per-hour rate). | code | 2026-07-03 | ✅ Confirmed |
| I-05 | Medium | UC §3 step 10; UC §4 A4 | Khi `RebalanceReason[]` chứa cả `range_out` VÀ các reason khác trong cùng một pass, liệu hedge-sync có được enqueue không hay chỉ `lp_rebalancing` path chạy? | Engine gom tất cả reasons vào `decision.reason[]` và enqueue 1 hedge-sync duy nhất. Light-check không tự set `lifecycle_state='lp_rebalancing'` — đó là việc của hedge-sync handler downstream. | code | 2026-07-03 | ✅ Confirmed |
| I-07 | Medium | UC §3 step 12; SRS FR-EXBOT-033; SRS FR-EXBOT-050 | Khi step 12 chạy (stop replace overrun), cả `bots.lifecycle_state` VÀ `bots.status` đều được update hay chỉ `lifecycle_state`? Worker nào thực hiện? | Light-Check Worker set cả `bots.status='safe_mode'` VÀ `bots.lifecycle_state='safe_mode'` atomically trong 1 UPDATE — xảy ra trước khi `partial_repair` được enqueue. Tester cần assert cả 2 fields trong cùng 1 check. | code | 2026-07-03 | ✅ Confirmed |
| I-08 | Medium | UC §3 step 4; SRS FR-EXBOT-012 | `next_light_check_at` của các bot bị skip (lp_rebalancing, lp_closing) có được update hay không? | Scan Worker update `next_light_check_at` cho mọi eligible bot (kể cả `lp_rebalancing`, `lp_closing`) trước khi enqueue. Bot bị Light-Check Worker skip vẫn được reschedule đúng 5 phút sau — không bị flood khi recovery. | code | 2026-07-03 | ✅ Confirmed |
| I-09 | Medium | UC §3 step 2 | Scan Worker query `LIMIT 500`: khi shard có > 500 bots eligible cùng lúc, các bot vượt LIMIT có được xử lý không? Có pagination không? | By design — jitter ±45s deterministic theo `hash(botId)` phân tán bots đều trong 5 phút, steady state không bao giờ overflow. Sau downtime, bots vượt LIMIT 500 được xử lý ở cron tick tiếp theo (1 phút sau), oldest first. Không cần pagination, không mất bot. | code | 2026-07-03 | ✅ Confirmed |
| I-11 | Low | UC (Diagram section) | UC có placeholder Mermaid diagram generic (User → System) thay vì sequence diagram thực. | Trỏ sang **F-01: Queue Fan-Out** trong `srs/flows.md` — full sequence Cron Worker → Scan Worker → Light-Check Worker fan-out → hedge-sync enqueue. | Confirmed | 2026-07-03 | ✅ Confirmed |
| I-12 | Low | UC §3 step 7; SRS FR-EXBOT-093 | UC không mô tả hành vi khi `MarketDataDO` cache stale (> 2× refresh interval): Light-Check Worker dùng stale data hay chờ DO refresh? | Fail-fast: nếu snapshot stale (> 5 phút) hoặc DO unreachable → throw ngay tại step 7, skip tick hoàn toàn. Không dùng stale data, không chờ refresh. Test design: stale MarketDataDO = light-check skip, không evaluate trigger nào. | code | 2026-07-03 | ✅ Confirmed |
| I-06 | Medium | UC §3 step 10; SRS FR-EXBOT-010; FR-EXBOT-015 | UC step 10 viết "enqueue lp_rebalancing message + partial_repair" khi phát hiện range_out — mâu thuẫn với SRS FR-EXBOT-015 ngụ ý chỉ dùng 1 queue. | 1 message, 1 queue. SRS FR-EXBOT-015 (verbatim): "transition bots.lifecycle_state to lp_rebalancing and enqueue an LP rebalance operation via the partial_repair queue." Cụm từ "lp_rebalancing message" trong UC mô tả hành động set lifecycle_state, không phải tên queue. Chỉ 1 message được enqueue đến partial_repair queue với operation type = LP rebalance. | QC Agent (from SRS FR-EXBOT-010, FR-EXBOT-015) | 2026-06-30 | ✅ Answered |
| I-13 | Low | UC §6; SRS §4 BR-EXBOT-004; BR-EXBOT-007 | UC §6 thiếu reference đến BR-EXBOT-004 và BR-EXBOT-007 dù cả hai BR liên quan trực tiếp đến logic UC. | Cả 2 BR tồn tại và áp dụng cho UC này. BR-EXBOT-004: "Delta-only hedge adjustment is the invariant default." (apply khi light-check enqueue hedge-sync, step 10). BR-EXBOT-007: "SAFE_MODE is never a terminal state." (apply khi step 12 trigger SAFE_MODE). | QC Agent (from SRS §4) | 2026-06-30 | ✅ Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|
| (No deferred questions.) |  |  |  |  |  |  |  |