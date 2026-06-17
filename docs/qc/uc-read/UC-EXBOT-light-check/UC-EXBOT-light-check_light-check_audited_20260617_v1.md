---
title: "Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-light-check"
date: 2026-06-17
author: qc-uc-read Agent (first-audit)
version: v1
---

# Báo cáo rà soát mức độ sẵn sàng của Use Case

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-light-check mô tả quy trình **kiểm tra nhẹ định kỳ (periodic light-check)** của hệ thống BNZA-EXBOT — một nền tảng bot delta-hedge LP chạy hoàn toàn trên Cloudflare Workers. Mục tiêu là định kỳ rà soát trạng thái từng bot đang hoạt động để quyết định có cần điều chỉnh hedge hay không, mà hoàn toàn không gọi HL API (không tiêu tốn HL rate-limit weight). Đây là use case backend thuần logic — không có giao diện người dùng.

Luồng hoạt động: Cron Worker (1 phút/lần) → queue `bot-scan` → Scan Worker truy vấn D1 lấy danh sách bot đến hạn → fan-out từng bot sang queue `light-check` → Light-Check Worker đọc D1 + MarketDataDO, tính toán local, đánh giá RebalanceReason[], và quyết định enqueue `hedge-sync` hoặc `price-near-stop-audit` nếu cần.

Các yếu tố ảnh hưởng đến thiết kế test bao gồm: 3 công thức đánh giá lý do rebalance vẫn đang chờ xác nhận từ BA (OQ-EXBOT-10/11/12); 1 luồng xử lý `stop_replacing_started_at` overrun hoàn toàn vắng mặt trong UC; nguồn dữ liệu `hlMarkPrice` cho stop trigger detection chưa xác định cơ chế trong điều kiện BR-EXBOT-003 (0 HL API call). Do đó, **UC này chưa đủ điều kiện để thiết kế test toàn bộ**.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check | — | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| zen / SOTATEK | QC Agent (auto-review) | 2026-06-12 | 2026-06-17 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-light-check.md` | 2026-06-12 | UC chính | File UC nguồn |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-005.md` | — | User Story | US-EXBOT-005 linked |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-006.md` | — | User Story | US-EXBOT-006 linked |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/spec.md` | — | Common rules / FR / BR / OQ | FR-EXBOT-012–016, 023, 032, 033, 093; BR-EXBOT-003, 005; OQ-EXBOT-10/11/12 |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/frd.md` | — | Functional detail | FR-EXBOT-011/012/013/014/015/016/023/032/033 (frd numbering) |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này tồn tại để hệ thống có thể **liên tục giám sát trạng thái delta-hedge và range LP của từng bot mà không phụ thuộc vào HL API**, giúp phát hiện sớm các lệch lạc cần điều chỉnh trong vòng tối đa 5 phút. Đây là cơ chế chính để hệ thống tự động duy trì tính ổn định của các vị thế hedge trong điều kiện thị trường thay đổi.

(Nguồn: uc-light-check.md §1 Actors; spec FR-EXBOT-012; BR-EXBOT-003: "Light-check HL weight = 0. Any HL API call introduced into light-check is an architectural violation.")

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Cron trigger → bot-scan queue | Cron Worker 1 phút/lần enqueue batch bot IDs cần kiểm tra | UC §3 Step 1 |
| Scan Worker fan-out | Truy vấn D1 bot đến hạn, enqueue `light-check` queue, batch-update `next_light_check_at` với jitter ±45s | UC §3 Steps 2–4; spec FR-EXBOT-013 |
| Idempotency guard | Light-Check Worker INSERT `queue_idempotency` trước khi xử lý; UNIQUE conflict → skip | UC §3 Step 5 |
| Đọc trạng thái D1 và MarketDataDO | Lấy `bot_runtime_state`, `hedge_legs`, `circuit_breakers` từ D1; `sqrtPriceX96`, `currentTick` từ MarketDataDO | UC §3 Steps 6–7 |
| Tính `lpEthAmount` local | Tính bằng TickMath + LiquidityAmounts — không RPC, không HL API | UC §3 Step 8; spec FR-EXBOT-017 |
| Đánh giá RebalanceReason[] | Đánh giá 9 lý do canonical theo frd FR-EXBOT-011 / spec FR-EXBOT-023 | UC §3 Step 9 |
| Enqueue hedge-sync (nếu cần) | Nếu có lý do rebalance AND circuit không open → enqueue `hedge-sync` với {botId, reasons, stateVersion} | UC §3 Step 10; spec FR-EXBOT-014 |
| Stop trigger detection | Nếu markPrice ≥ stop_price → guarded write `stop_trigger_crossed_at` (NULL only) + enqueue `price-near-stop-audit` | UC §3 Step 11; spec FR-EXBOT-032 |
| Circuit breaker states | open → suppress hedge-sync; half_open → 1 probe duy nhất (atomic claim) | UC §4 A1/A2 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| `stop_replacing_started_at` overrun detection | Có trong frd FR-EXBOT-011 và spec FR-EXBOT-033 nhưng hoàn toàn vắng mặt trong UC §3 và §4 | **Blocker** — không thể thiết kế test cho path này từ UC |
| Nội dung của `deep-audit` | UC §7 trace FR-EXBOT-016 nhưng không mô tả nội dung deep-audit trong light-check scope | Không block — deep-audit là UC riêng |
| Stop replacement thực thi | Thuộc về worker khác (partial_repair) | Không block UC này |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn | Nguồn |
|---|---|---|---|---|
| Cron Worker (CF Cron Trigger) | System | Trigger định kỳ 1 phút/lần, enqueue `bot-scan` | Chỉ enqueue — không đọc/ghi D1 trực tiếp | UC §3 Step 1 |
| Scan Worker (CF Worker) | System | Truy vấn D1, enqueue `light-check`, batch-update `next_light_check_at` | Đọc/ghi D1; enqueue via `chunkSendBatch` (max 100/batch) | UC §3 Steps 2–4 |
| Light-Check Worker (CF Worker) | System | Thực hiện đánh giá rebalance và stop trigger cho từng bot | Đọc D1, đọc MarketDataDO; enqueue `hedge-sync` hoặc `price-near-stop-audit`; ghi `stop_trigger_crossed_at` (guarded) | UC §3 Steps 5–12 |
| MarketDataDO (CF Durable Object) | External/Cache | Cung cấp dữ liệu pool (`sqrtPriceX96`, `currentTick`) mà không cần RPC | Read-only từ góc độ light-check | UC §3 Step 7; spec FR-EXBOT-093 |

**Nhận xét readiness:** Các actor đã xác định rõ. Không có actor người dùng (UC hoàn toàn tự động). Đủ để thiết kế test theo actor.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot có `status = 'active'` và `next_light_check_at <= now` | Yes | UC §2; uc-light-check.md §3 Step 2 |
| 2 | Bot KHÔNG có `lifecycle_state IN ('lp_rebalancing', 'lp_closing')` | Yes | UC §2; frd FR-EXBOT-011 skip condition |
| 3 | MarketDataDO đang online và có dữ liệu pool hợp lệ | Yes | UC §3 Step 7; spec FR-EXBOT-093 |
| 4 | Message ID trong `queue_idempotency` chưa tồn tại (lần xử lý đầu tiên) | Yes | UC §3 Step 5 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác / path | Trạng thái hệ thống sau khi hoàn tất | Nguồn |
|---|---|---|
| Happy path — không cần rebalance | `queue_idempotency.state = 'succeeded'`; `next_light_check_at` đã được batch-update; không có message mới trong queue | UC §3 Steps 4, 12 |
| Cần rebalance (reasons tìm được) | `hedge-sync` message enqueued với {botId, reasons[], stateVersion}; `queue_idempotency.state = 'succeeded'` | UC §3 Step 10 |
| Stop trigger crossed | `hedge_legs.stop_trigger_crossed_at` set (nếu chưa set); `price-near-stop-audit` enqueued; KHÔNG enqueue `hedge-sync` cho trigger này | UC §3 Step 11; spec FR-EXBOT-032; BR-EXBOT-005 |
| Circuit open | hedge-sync bị suppress; stop monitoring vẫn tiếp tục | UC §4 A1; spec FR-EXBOT-014 |
| Duplicate delivery | Return immediately sau UNIQUE conflict; không xử lý lại | UC §3 Step 5 |

---

## 4. Danh sách UI object và mapping

N/A — UC-EXBOT-light-check là backend worker UC, không có giao diện người dùng. Nền tảng PTL-04 là Cloudflare Workers API-only. Không có wireframe, mockup, hay ASCII screen.

Thay thế: xem Mục 6 cho danh sách operations/functions tương đương.

---

## 5. Thuộc tính và hành vi của UI object

N/A — Không có UI object. Xem Mục 6 cho hành vi của các data objects chính.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng chính: Periodic Light-Check Execution

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Cron Worker | Cron trigger mỗi 1 phút → `chunkSendBatch` → queue `bot-scan` | Batch bot IDs được enqueue | — | — | UC §3 Step 1; spec FR-EXBOT-012 AC |
| 2 | Scan Worker | SELECT D1: `bots WHERE status='active' AND next_light_check_at <= now LIMIT 500` (per shard) | Danh sách bot đến hạn | — | — | UC §3 Step 2 |
| 3 | Scan Worker | `chunkSendBatch` từng bot → queue `light-check` | Một message per bot | — | — | UC §3 Step 3 |
| 4 | Scan Worker | Batch UPDATE `next_light_check_at = now + 5min + random(−45s, +45s)` (1 stmt/shard) | `next_light_check_at` đã rescheduled | — | — | UC §3 Step 4; spec FR-EXBOT-013; NFR-EXBOT-005 |
| 5 | Light-Check Worker | INSERT `queue_idempotency (message_id, state='started')` | Tiếp tục xử lý | — | UNIQUE conflict → return immediately (duplicate delivery skip) | UC §3 Step 5 |
| 6 | Light-Check Worker | READ D1: `bot_runtime_state`, `hedge_legs` (stop_price, margin_status, stop_trigger_crossed_at, stop_replacing_started_at), `circuit_breakers` | Dữ liệu trạng thái bot | — | — | UC §3 Step 6 |
| 7 | Light-Check Worker | READ MarketDataDO: `sqrtPriceX96`, `currentTick` | Dữ liệu pool hiện tại (cached, 0 RPC) | — | Cache stale > 2× TTL: DO log warning + force refresh (hành vi worker chưa định nghĩa — xem Q-007) | UC §3 Step 7; spec FR-EXBOT-093 |
| 8 | Light-Check Worker | Tính `lpEthAmount` bằng TickMath + LiquidityAmounts (local, không RPC, không HL) | `lpEthAmount` tính ra | — | — | UC §3 Step 8; spec FR-EXBOT-017 AC |
| 9 | Light-Check Worker | Đánh giá RebalanceReason[]: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback | reasons[] (empty hoặc có giá trị) | — | Formulas chưa đầy đủ: OQ-EXBOT-10/11/12 — xem Q-003/Q-004/Q-005 | UC §3 Step 9; frd FR-EXBOT-011; spec FR-EXBOT-023 |
| 10 | Light-Check Worker | Nếu reasons[] không rỗng AND circuit != open → enqueue `hedge-sync` với {botId, reasons, stateVersion} | `hedge-sync` enqueued | circuit=half_open: atomic claim `half_open_probe_used` 0→1, nếu claim thành công → enqueue 1 probe; circuit=open → suppress | — | UC §3 Step 10; UC §4 A1/A2; spec FR-EXBOT-014 |
| 11 | Light-Check Worker | Nếu markPrice ≥ stop_price → set `stop_trigger_crossed_at` (guarded: NULL only) + enqueue `price-near-stop-audit` | Stop trigger detected; KHÔNG enqueue hedge-sync | stop_trigger_crossed_at đã set → guard prevents overwrite; price-near-stop-audit vẫn enqueue | — | UC §3 Step 11; spec FR-EXBOT-032; BR-EXBOT-005 |
| 12 | Light-Check Worker | UPDATE `queue_idempotency.state = 'succeeded'` | Processing complete | — | — | UC §3 Step 12 |

**Lưu ý quan trọng (Missing Step):** frd FR-EXBOT-011 và spec FR-EXBOT-033 mô tả thêm một bước: nếu `stop_replacing_started_at IS NOT NULL AND age > 60s` → enqueue `partial_repair` + trigger SAFE_MODE. Bước này **hoàn toàn vắng mặt** trong UC §3 và §4. (Xem Q-001)

#### B. Business rules và validation

| Rule / Object | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| BR-EXBOT-003: 0 HL weight | Light-check không được gọi HL API dưới bất kỳ hình thức nào | Yes | Toàn bộ logic dùng D1 + MarketDataDO | Architectural violation | spec.md BR table; nội dung nguồn: "Light-check HL weight = 0. Any HL API call introduced into light-check is an architectural violation." |
| BR-EXBOT-005: stop_trigger_crossed_at write-once | Set `stop_trigger_crossed_at` CHỈ khi đang NULL | Yes | Ghi thành công lần đầu | Skip ghi (guard prevents overwrite) — price-near-stop-audit vẫn enqueue | spec.md BR table; nội dung nguồn: "`stop_trigger_crossed_at` is write-once per stop event (guarded: only set if currently NULL). This prevents the 30-min SAFE_MODE detection from being defeated by repeated light-check overwrites." |
| FR-EXBOT-023: Canonical RebalanceReason enum | Chỉ dùng 9 giá trị: `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile`. `stop_trigger_crossed` KHÔNG phải RebalanceReason | Yes | Đúng enum → enqueue hedge-sync | Sai enum / alias → undefined behavior | spec FR-EXBOT-023; nội dung nguồn: "No aliases or alternate naming are permitted. `stop_trigger_crossed` is not a `RebalanceReason`; it routes to `price-near-stop-audit`." |
| `chunkSendBatch` (max 100/batch) | Scan Worker KHÔNG được dùng `sendBatch` trực tiếp | Yes | Fan-out đúng throughput | Queue overload / drop | spec FR-EXBOT-010 |
| `next_light_check_at` batch write | 1 UPDATE statement per shard, không per-bot | Yes | D1 write budget tuân thủ NFR-EXBOT-005 | Excess D1 write → NFR violation | spec FR-EXBOT-013; NFR-EXBOT-005 |
| skip condition: lifecycle_state | Bot `lp_rebalancing` hoặc `lp_closing` → skip toàn bộ light-check | Yes | No queue message produced | — | UC §2 preconditions; frd FR-EXBOT-011 |
| drift_threshold formula | `deltaErrorUsd > max($25, lpValueUsd × 3%)` với `deltaErrorUsd = |targetShortEth − actualShortEth| × uniPoolPrice` | Yes | Reason added | No reason | frd FR-EXBOT-011; **lpValueUsd formula undefined** (OQ-EXBOT-11) |
| drift_relative formula | `|target − actual| / target > 0.15` | Yes | Reason added | No reason | frd FR-EXBOT-011 |
| range_boundary_near | Price trong khoảng 90% đến upper/lower bound | Yes | Reason added | No reason | frd FR-EXBOT-011; **tick vs price distance chưa xác định** (OQ-EXBOT-10) |
| funding_alert | 7d funding APR < −15% | Yes | Reason added | No reason | frd FR-EXBOT-011; **công thức APR chưa xác định** (OQ-EXBOT-12) |
| 3-way price split | `uniPoolPrice` (từ MarketDataDO sqrtPriceX96) → drift; `hlMarkPrice` → stop trigger; `hlOraclePrice` → margin. KHÔNG được hoán đổi | Yes | Đúng evaluation | Wrong trigger / wrong drift calculation | frd FR-EXBOT-011; **hlMarkPrice source chưa xác định trong UC** (Q-002) |

#### C. Thông báo, lỗi và phản hồi

N/A — UC này là backend worker, không có UI feedback. Các "thông báo" là queue messages và D1 state transitions:
- Queue `hedge-sync` enqueued → hedge-sync worker nhận
- Queue `price-near-stop-audit` enqueued → stop-audit worker nhận
- Queue `partial_repair` enqueued → repair worker nhận (path này thiếu trong UC — Q-001)
- `queue_idempotency.state` cập nhật theo từng bước

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Light-check enqueue `hedge-sync` | UC-EXBOT-hedge-sync | hedge-sync worker nhận, acquire UserLockDO, thực hiện delta adjustment | `stateVersion` trong message phải khớp D1 tại thời điểm consume — stale messages bị discard | spec FR-EXBOT-025 AC; US-EXBOT-006 AC-02 |
| Light-check enqueue `price-near-stop-audit` | UC-EXBOT-price-near-stop-audit | Stop-audit worker theo dõi stop trigger resolution | `stop_trigger_crossed_at` set once; nếu stuck > 30 min → SAFE_MODE (deep-audit backstop) | spec FR-EXBOT-032; FR-EXBOT-033 |
| Light-check cập nhật `next_light_check_at` | Toàn bộ vòng lặp cron | Jitter ±45s ngăn bot clustering trong 1 cron tick | Batch write per shard — không per-bot | spec FR-EXBOT-013; NFR-EXBOT-005 |
| Scan Worker fan-out via queue | `light-check` queue consumer | 10,000 bots trong 5 phút → mỗi Cron tick ≤ 500/shard via LIMIT | Idempotency guard trên `queue_idempotency` ngăn double-processing khi CF queue redeliver | UC §3 Steps 2–5 |
| MarketDataDO cung cấp pool data | Tất cả Light-Check Workers đồng thời | 0 RPC per worker — tất cả share 1 DO instance | Cache TTL chưa được định nghĩa (không có trong UC/spec) — stale data có thể ảnh hưởng drift và stop evaluation | spec FR-EXBOT-093 |
| `stop_replacing_started_at` overrun | UC-EXBOT-partial-repair (SAFE_MODE trigger) | Nếu stop replacement stuck > 60s → partial_repair + SAFE_MODE | Phát hiện primary qua light-check (≤5 min); backup qua deep-audit | frd FR-EXBOT-011; spec FR-EXBOT-033; **path này thiếu trong UC §3** |
| D1 write: `bot_runtime_state` | D1 state consistency | Chỉ ghi khi có thay đổi (write-on-change) | Không ghi unconditional per-bot UPDATE | NFR-EXBOT-005 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | 0 HL weight cho 10,000 bot | Bot đang active; light-check cycle chạy | Light-check worker xử lý | Không có HL API call nào được thực hiện trong toàn bộ light-check cycle | BR-EXBOT-003; spec FR-EXBOT-012 AC — Confirmed |
| AC-02 | drift calculation dùng uniPoolPrice | Bot có delta drift > ngưỡng | Light-check evaluate drift_threshold | `deltaErrorUsd` tính bằng `|targetShortEth − actualShortEth| × uniPoolPrice` (từ sqrtPriceX96 của MarketDataDO), không dùng hlMarkPrice | frd FR-EXBOT-011 3-way split — Confirmed |
| AC-03 | stop_trigger_crossed_at write-once | `stop_trigger_crossed_at` đã set; light-check tiếp tục chạy | markPrice ≥ stop_price trên lần kiểm tra tiếp theo | `stop_trigger_crossed_at` không bị overwrite; `price-near-stop-audit` vẫn được enqueue | BR-EXBOT-005; spec FR-EXBOT-032 — Confirmed |
| AC-04 | Skip bot lp_rebalancing | Bot có `lifecycle_state = 'lp_rebalancing'` | Light-check worker nhận message | Không có queue message nào được produce; `queue_idempotency.state = 'succeeded'` | UC §2; frd FR-EXBOT-011 — Confirmed |
| AC-05 | Idempotency — duplicate delivery | Message đã được xử lý thành công (state='succeeded') | CF queue redeliver cùng message | Light-Check Worker return ngay sau UNIQUE constraint conflict — không double-process | UC §3 Step 5; spec FR-EXBOT-007 — Confirmed |
| AC-06 | Batch next_light_check_at update | Scan Worker xử lý 1 shard gồm N bots | Cron tick trigger | Chỉ 1 D1 UPDATE statement được thực thi cho shard đó, không N statements | spec FR-EXBOT-013; NFR-EXBOT-005 — Confirmed |
| AC-07 | Circuit open — stop monitoring tiếp tục | `circuit_breakers.state = 'open'`; markPrice ≥ stop_price | Light-check evaluate | `hedge-sync` KHÔNG được enqueue; `price-near-stop-audit` VẪN được enqueue | UC §4 A1; spec FR-EXBOT-014 — Confirmed |
| AC-08 | Circuit half_open — exactly-one probe | `circuit_breakers.state = 'half_open'`; `half_open_probe_used = 0` | Light-check phát hiện rebalance reason | Đúng 1 probe `hedge-sync` được enqueue; `half_open_probe_used` → 1 (atomic). Nếu claim thất bại → không enqueue | UC §4 A2; spec FR-EXBOT-028 AC — **Suy luận cần xác nhận: cơ chế atomic chưa được chỉ định (Q-006)** |
| AC-09 | stop_replacing overrun → partial_repair | `stop_replacing_started_at IS NOT NULL AND age > 60s` | Light-check detect | `partial_repair` message enqueued; SAFE_MODE entered | frd FR-EXBOT-011; spec FR-EXBOT-033 — **Suy luận cần xác nhận: thiếu trong UC §3 (Q-001)** |
| AC-10 | range_boundary_near trigger | Bot LP price ≥ 90% đến upper/lower range bound | Light-check evaluate | `range_boundary_near` added to reasons[]; hedge-sync enqueued | frd FR-EXBOT-011; UC §4 A4 — **Blocked: OQ-EXBOT-10 chưa resolved (Q-003)** |
| AC-11 | drift_threshold trigger | `deltaErrorUsd > max($25, lpValueUsd × 3%)` | Light-check evaluate | `drift_threshold` added to reasons[] | frd FR-EXBOT-011 — **Blocked: OQ-EXBOT-11 chưa resolved (Q-004)** |
| AC-12 | funding_alert trigger | 7d funding APR < −15% | Light-check evaluate | `funding_alert` added to reasons[] | frd FR-EXBOT-011 — **Blocked: OQ-EXBOT-12 chưa resolved (Q-005)** |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Scale target: 10,000 bot trong 5 phút; Cron cycle 1 phút; Scan Worker LIMIT 500/shard | Test load: verify throughput không tụt hạn dưới 5 min per full cycle | spec FR-EXBOT-012 AC |
| HL Rate Limit | 0 HL API weight consumed per light-check cycle | Test: monitor HL weight counter = 0 sau toàn bộ light-check run | BR-EXBOT-003 |
| D1 Write Budget | Chỉ ghi khi có thay đổi (write-on-change); `next_light_check_at` batch 1 stmt/shard | Test: đếm D1 write statements; verify không có unconditional per-bot write | NFR-EXBOT-005 |
| Idempotency | Queue redelivery không gây double-processing | Test: deliver cùng message 2 lần; verify chỉ 1 lần xử lý | spec FR-EXBOT-007 |
| Security | Không có | N/A | — |
| Audit / Logging | MarketDataDO logs warning khi cache stale > 2× refresh interval | Verify log xuất hiện trong stale cache scenario | spec FR-EXBOT-093 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q-001 | High | Missing | frd FR-EXBOT-011; spec FR-EXBOT-033; UC §3 (missing) | UC §3 và §4 hoàn toàn không đề cập đến path xử lý khi `stop_replacing_started_at IS NOT NULL AND age > 60s`. frd FR-EXBOT-011 và spec FR-EXBOT-033 mô tả rõ là phải enqueue `partial_repair` và trigger SAFE_MODE. BA vui lòng thêm path này vào UC §3 (Step 13 mới) hoặc §4 (Alternate A5), và xác nhận đây có thuộc phạm vi light-check không? | Nếu không có trong UC thì tester không thể thiết kế test case cho path này từ tài liệu nguồn. Đây là safety path (SAFE_MODE), bỏ sót sẽ gây rủi ro hệ thống. | BA / zen | Open |
| Q-002 | High | Missing | frd FR-EXBOT-011 (3-way price split); UC §3 Step 7; BR-EXBOT-003 | Light-check sử dụng `hlMarkPrice` để phát hiện stop trigger (Step 11), nhưng UC §3 Step 7 chỉ đề cập đọc `sqrtPriceX96` và `currentTick` từ MarketDataDO. BR-EXBOT-003 cấm HL API call từ light-check. BA vui lòng xác nhận: `hlMarkPrice` được lấy từ đâu mà không vi phạm BR-EXBOT-003? Có Durable Object hoặc D1 cache riêng lưu hlMarkPrice không? | Nếu không có nguồn dữ liệu được xác định, tester không thể biết cần setup dữ liệu nào cho test case stop trigger, và không thể verify architecture constraint BR-EXBOT-003 được tuân thủ. | BA / Tech Lead | Open |
| Q-003 | High | Missing | OQ-EXBOT-10 (spec); frd FR-EXBOT-011; UC §4 A4 | Công thức `range_boundary_near`: "price 90% to upper/lower range" hiện chưa xác định là đo theo tick distance hay price distance. OQ-EXBOT-10 trong spec đang chờ zen xác nhận. BA vui lòng cập nhật frd FR-EXBOT-011 và UC §3 Step 9 sau khi OQ-EXBOT-10 được resolved. | Hai cách đo cho kết quả test input khác nhau hoàn toàn — tester không thể tính boundary value chính xác. | BA / zen | Open |
| Q-004 | High | Missing | OQ-EXBOT-11 (spec); frd FR-EXBOT-011; spec FR-EXBOT-012 | `drift_threshold` formula sử dụng `lpValueUsd × 3%`, nhưng cách tính `lp_value_usd` trong `bot_runtime_state` chưa được định nghĩa. OQ-EXBOT-11 đang block FR-EXBOT-012. BA vui lòng xác nhận: `lp_value_usd` được tính thế nào? Cần reference FR nào để tester biết expected value? | Ngưỡng drift là relative (3% của lpValueUsd), nên test input phụ thuộc hoàn toàn vào giá trị này. Không có công thức = không thể tính expected test data. | BA / zen | Open |
| Q-005 | High | Missing | OQ-EXBOT-12 (spec); frd FR-EXBOT-011 | `funding_alert` trigger: "7d funding APR < −15%". Công thức tổng hợp 7-day APR (cách lấy funding rate từng giờ, cách annualize) chưa được xác định. OQ-EXBOT-12 đang chờ zen. BA vui lòng cập nhật frd FR-EXBOT-011 với công thức chính xác sau khi OQ-EXBOT-12 được resolved. | Không có công thức = tester không thể tính expected APR từ raw funding data để test trigger. | BA / zen | Open |
| Q-006 | Medium | Unclear | UC §4 A2; spec FR-EXBOT-028 AC | UC §4 A2 yêu cầu "atomically claim `half_open_probe_used` 0→1" nhưng không chỉ định cơ chế: D1 transaction (CF D1 không có SELECT FOR UPDATE), Durable Object atomic counter, hay CAS? CF D1 không hỗ trợ row-level locking. BA / Tech Lead vui lòng xác định cơ chế atomic claim được sử dụng và document vào spec FR-EXBOT-028. | Tester cần biết cơ chế để thiết kế concurrent delivery test — verify exactly-one probe không thể thực hiện nếu không biết cơ chế. | BA / Tech Lead | Open |
| Q-007 | Medium | Missing | spec FR-EXBOT-093; UC §3 Step 7 | Khi MarketDataDO cache stale (> 2× refresh interval), spec FR-EXBOT-093 nói DO sẽ log warning và force refresh. Nhưng UC không định nghĩa: Light-Check Worker phải làm gì trong khoảng thời gian chờ refresh? Trả về kết quả đánh giá dựa trên data cũ? Discard message? Wait? | Tester không thể thiết kế test cho stale cache edge case. | BA | Open |
| Q-008 | Medium | Unclear | UC §3 Step 9; spec FR-EXBOT-023; frd FR-EXBOT-011 | spec FR-EXBOT-023 liệt kê 9 canonical RebalanceReason, nhưng frd FR-EXBOT-011 chỉ mô tả công thức evaluation cho ~7 reason (drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback). `manual_admin` và `recovery_reconcile` không có evaluation criteria trong frd. BA vui lòng xác nhận: light-check có chịu trách nhiệm evaluate `manual_admin` và `recovery_reconcile` không? Nếu không, worker nào set các reason này? | Tester cần biết scope của light-check để không thiết kế test sai worker. | BA | Open |
| Q-009 | Medium | Missing | UC §3 Step 10; spec FR-EXBOT-025 AC; US-EXBOT-006 AC-02 | `stateVersion` trong hedge-sync message: UC §3 Step 10 ghi enqueue {botId, reasons, stateVersion} nhưng không chỉ định `stateVersion` được lấy từ field nào trong D1 (đọc tại Step 6?). US-EXBOT-006 AC-02 mô tả stale messages bị discard nhưng không trace về nguồn field. BA vui lòng xác nhận table/column nào cung cấp `stateVersion`. | Tester cần biết để setup đúng `stateVersion` trong queue message khi test stale-message scenario của hedge-sync worker. | BA | Open |
| Q-010 | Low | Unclear | UC §3 Step 2 | Scan Worker batch size: UC §3 Step 2 ngụ ý LIMIT 500/shard. Khi > 500 bot đến hạn trong 1 cron tick trên cùng 1 shard: bots còn lại có bị defer sang tick tiếp theo không, hay Scan Worker loop query nhiều lần trong cùng 1 tick? | Minor — không block test design cho core behavior; có thể ảnh hưởng scale/load test. | BA | Open |
| Q-011 | Low | Internal inconsistency | frd.md FR-EXBOT-011/012 vs spec.md FR-EXBOT-012/013 | frd.md đánh số FR-EXBOT-011 (light-check logic) / FR-EXBOT-012 (jitter), trong khi spec.md dùng FR-EXBOT-012 / FR-EXBOT-013 cho cùng nội dung đó. Nội dung không conflict nhưng số thứ tự khác nhau gây nhầm lẫn khi cross-reference. BA vui lòng align hoặc thêm cross-reference mapping note. | Minor — không block test design. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-10 (range_boundary_near formula) | UC / BA Decision | Block: AC-10, Q-003 — không thể thiết kế boundary test cho range_boundary_near | zen / BA | Open |
| OQ-EXBOT-11 (lpValueUsd formula) | UC / BA Decision | Block: AC-11, Q-004 — không thể tính drift_threshold test data | zen / BA | Open |
| OQ-EXBOT-12 (7d APR formula) | UC / BA Decision | Block: AC-12, Q-005 — không thể tính funding_alert test data | zen / BA | Open |
| MarketDataDO cache TTL definition | Integration / Architecture | Q-007 — stale cache edge case undefined | Tech Lead | Open |
| UC §3 update: stop_replacing_started_at path | UC completeness | Q-001 — missing flow prevents test design | BA | Open |
| hlMarkPrice source architecture | Architecture | Q-002 — stop trigger test setup requires confirmed source | BA / Tech Lead | Open |

---

### 10.3 Audit Summary

#### Bảng điểm đánh giá

| Nhóm đánh giá | Điểm | Trạng thái | Nhận xét ngắn |
|---|---:|---|---|
| F.1 Function/Operation Inventory | 14/20 | ⚠️ Partial | 15 operations documented; missing: stop_replacing path, RebalanceReason subset scope unclear |
| F.2 Object Attributes & Behavior | 10/25 | ⚠️ Partial | 5 critical behaviors blocked by OQ-EXBOT-10/11/12 và hlMarkPrice source gap; cap applied |
| F.3 Functional Logic & Workflow | 10/25 | ⚠️ Partial | Happy path + circuit alternates well-covered; stop_replacing path entirely missing from UC; blocker cap applied |
| F.4 Functional Integration | 9/15 | ⚠️ Partial | Integration topology mostly clear; stateVersion field source undefined; partial_repair path missing |
| F.5 UC Documentation Quality | 8/15 | ⚠️ Partial | UC structurally complete; cross-source conflicts and missing flows penalized; cap applied |
| **Tổng điểm** | **51/100** | **Not Ready** | **UC chưa sẵn sàng cho test design toàn diện — 5 blocker phải giải quyết trước** |

#### Blocker cần xử lý

1. **Q-001** — Path `stop_replacing_started_at` overrun (→ partial_repair + SAFE_MODE) hoàn toàn thiếu trong UC §3/§4, dù đã có trong frd và spec.
2. **Q-002** — Nguồn dữ liệu `hlMarkPrice` cho stop trigger detection chưa xác định, trong khi BR-EXBOT-003 cấm HL API call từ light-check.
3. **Q-003** — OQ-EXBOT-10 chưa resolved: `range_boundary_near` tick vs price distance.
4. **Q-004** — OQ-EXBOT-11 chưa resolved: `lpValueUsd` formula undefined, block `drift_threshold` evaluation.
5. **Q-005** — OQ-EXBOT-12 chưa resolved: 7d funding APR aggregation formula undefined.

#### Vấn đề lớn cần xử lý

1. **Q-006** — Cơ chế atomic claim cho `half_open_probe_used` chưa được chỉ định.
2. **Q-007** — Light-Check Worker behavior khi MarketDataDO cache stale chưa defined.
3. **Q-008** — Scope evaluation của `manual_admin` và `recovery_reconcile` trong light-check chưa rõ.
4. **Q-009** — `stateVersion` field source cho hedge-sync message chưa được trace rõ.

#### Khuyến nghị

UC-EXBOT-light-check có cấu trúc rõ ràng và luồng happy path được mô tả đầy đủ. Tuy nhiên, **5 blocker liên quan đến công thức evaluation và kiến trúc hlMarkPrice** ngăn cản việc thiết kế test case toàn diện. BA cần: (1) phối hợp với zen để close OQ-EXBOT-10/11/12; (2) xác định nguồn hlMarkPrice; (3) thêm path stop_replacing_started_at vào UC §3. Sau khi các blocker này được resolve, UC có thể đạt Conditionally Ready với 4 major issues còn lại.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read Agent (first-audit) | Tạo báo cáo audited lần đầu — UC-EXBOT-light-check trên branch joy |

---

*Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-light-check · v1 · 2026-06-17*
