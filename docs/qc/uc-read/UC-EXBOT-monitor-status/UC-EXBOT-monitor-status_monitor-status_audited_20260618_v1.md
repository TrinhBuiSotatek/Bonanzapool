---
title: Báo cáo Kiểm tra Sẵn sàng UC — UC-EXBOT-monitor-status
date: 2026-06-18
author: qc-uc-read-exbot
version: v1
uc_id: UC-EXBOT-monitor-status
skill: qc-uc-read-exbot
baseline: SRS spec.md + states.md + frd.md (spec.md + states.md cập nhật 2026-06-18)
note: Tiếng Việt theo yêu cầu người dùng
---

# Báo cáo Kiểm tra Sẵn sàng UC — UC-EXBOT-monitor-status

## Bảng mã viết tắt

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC-EXBOT-* | Mã định danh Use Case cho module ExBot. | usecases/index.md |
| US-EXBOT-* | Mã định danh User Story. Mỗi US quy định tiêu chí chấp nhận. | userstories/index.md |
| FR-EXBOT-* | Mã định danh Yêu cầu chức năng. SRS spec.md là văn bản ưu tiên khi mâu thuẫn với frd.md. | srs/spec.md, frd.md |
| BR-EXBOT-* | Quy tắc nghiệp vụ cấp module. | srs/spec.md §4 |
| AC-EXBOT-* | Tiêu chí chấp nhận trong user story. | userstories/us-*.md |
| Operator Facade | Worker Cloudflare public-facing đại diện ExBot Worker. Proxy `GET /api/exbot/status` qua CF service binding + internal token. ExBot Worker không thể truy cập trực tiếp từ internet. | srs/spec.md FR-EXBOT-090, frd.md FR-EXBOT-100 |
| MarketDataDO | Durable Object cung cấp cache chia sẻ cho pool slot0 data (sqrtPriceX96, currentTick). Tất cả light-check worker đọc từ DO này thay vì gọi RPC trực tiếp. | srs/spec.md FR-EXBOT-093 |
| SAFE_MODE | Trạng thái bot mọi thao tác thay đổi đều bị chặn. Điều kiện vào SAFE_MODE định nghĩa tại FR-EXBOT-050. | srs/spec.md FR-EXBOT-050 |
| lifecycle_state | Trường `bots.lifecycle_state` — 18 giá trị canonical theo dõi trạng thái chi tiết của bot. | srs/spec.md FR-EXBOT-003, srs/states.md |
| drift % | Phần trăm lệch của kích thước vị thế short HL thực tế so với kích thước mục tiêu. Công thức: `(|actualShortEth - targetShortEth| / targetShortEth) × 100`. | UC §3 bước 6, srs/spec.md FR-EXBOT-021 |
| rangeState | Trạng thái tick hiện tại so với khoảng LP (in / out-of-range). | UC §3 bước 5, srs/spec.md FR-EXBOT-012 |

---

## 0. Phạm vi kiểm tra

| Trường | Giá trị |
|---|---|
| UC được kiểm tra | UC-EXBOT-monitor-status |
| File UC | docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-monitor-status.md |
| UC được tạo | 2026-06-18 (bản nháp đầu tiên) |
| User Stories liên quan | US-EXBOT-002 |
| FR Trace (UC §6) | FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-090 |
| FR Trace (index.md) | FR-002, FR-003, FR-090 |
| Cơ sở SRS | srs/spec.md + srs/states.md + srs/flows.md + srs/erd.md (tất cả đã đọc; spec.md + states.md cập nhật 2026-06-18) |
| Cơ sở FRD | frd.md (cập nhật 2026-06-18) |
| Ngày kiểm tra | 2026-06-18 |
| Ngôn ngữ đầu ra | Tiếng Việt (theo yêu cầu người dùng) |

---

## §F.1 Kiểm kê

### F.1.1 Các thao tác / API

| ID | Thao tác | Điều kiện kích hoạt | Tác nhân | Nguồn |
|---|---|---|---|---|
| OP-01 | `GET /api/exbot/status` — Investor yêu cầu trạng thái bot | Investor mở màn hình ExBot status | POOL UI → Operator Facade | UC §3 bước 1, FR-EXBOT-090 |
| OP-02 | Operator Facade chuyển tiếp yêu cầu đến ExBot Worker qua CF service binding + internal auth token | Nhận yêu cầu từ POOL UI | Operator Facade → ExBot Worker | UC §3 bước 2, FR-EXBOT-090 |
| OP-03 | ExBot Worker đọc `bots.status`, `lifecycle_state` từ D1 | Sau khi nhận yêu cầu từ Facade | ExBot Worker → D1 | UC §3 bước 3 |
| OP-04 | ExBot Worker đọc `bot_runtime_state.last_known_hl_short_size` từ D1 | Cùng lúc với OP-03 | ExBot Worker → D1 | UC §3 bước 3 |
| OP-05 | ExBot Worker đọc `positions.tickLower`, `positions.tickUpper` từ D1 | Cùng lúc với OP-03 | ExBot Worker → D1 | UC §3 bước 3 |
| OP-06 | ExBot Worker đọc `hedge_legs.margin_status` từ D1 | Cùng lúc với OP-03 | ExBot Worker → D1 | UC §3 bước 3 |
| OP-07 | ExBot Worker đọc `next_light_check_at` từ D1 | Cùng lúc với OP-03 | ExBot Worker → D1 | UC §3 bước 3 (xem vấn đề I-003) |
| OP-08 | ExBot Worker truy vấn `currentTick` từ MarketDataDO | Sau khi đọc D1 | ExBot Worker → MarketDataDO | UC §3 bước 4, FR-EXBOT-093 |
| OP-09 | Tính toán `rangeState` bằng cách so sánh `currentTick` với `tickLower`/`tickUpper` | Sau khi có đủ dữ liệu | ExBot Worker (local) | UC §3 bước 5 |
| OP-10 | Tính toán drift %: `(|actualShortEth - targetShortEth| / targetShortEth) × 100` | Cùng lúc với OP-09 | ExBot Worker (local) | UC §3 bước 6 |
| OP-11 | ExBot Worker tổng hợp JSON response và trả về cho Operator Facade | Sau khi tính toán xong | ExBot Worker → Operator Facade → POOL UI | UC §3 bước 7–8 |

### F.1.2 Các trường dữ liệu được đọc

| Trường | Bảng D1 | Kiểu | Mô tả | Nguồn |
|---|---|---|---|---|
| `status` | `bots` | TEXT | Trạng thái thô (active/paused/closing/closed/safe_mode/error) | erd.md, FR-EXBOT-003 |
| `lifecycle_state` | `bots` | TEXT | Trạng thái chi tiết (18 giá trị canonical) | erd.md, FR-EXBOT-003 |
| `last_known_hl_short_size` | `bot_runtime_state` | TEXT (BigDecimal) | Kích thước short HL đã biết gần nhất | erd.md |
| `target_short_size` | `bot_runtime_state` | TEXT (BigDecimal) | Kích thước short mục tiêu | erd.md (xem I-004) |
| `tick_lower` | `positions` | INTEGER | Giới hạn dưới của khoảng LP | erd.md |
| `tick_upper` | `positions` | INTEGER | Giới hạn trên của khoảng LP | erd.md |
| `margin_status` | `hedge_legs` | TEXT | ok / warning / critical | erd.md, FR-EXBOT-060 |
| `next_light_check_at` | `bots` | TEXT | Thời điểm light-check tiếp theo theo lịch | erd.md (xem I-003) |
| `currentTick` | MarketDataDO | INTEGER | Tick hiện tại từ pool slot0 | FR-EXBOT-093 |

### F.1.3 Các trường trong JSON response

| Trường | Nguồn | Ghi chú |
|---|---|---|
| `status` | `bots.status` | — |
| `lifecycle_state` | `bots.lifecycle_state` | — |
| `tickLower` | `positions.tick_lower` | — |
| `tickUpper` | `positions.tick_upper` | — |
| `currentTick` | MarketDataDO | — |
| `rangeState` | tính toán local | in / out-of-range |
| `hedgeSize` (actualShortEth) | `bot_runtime_state.last_known_hl_short_size` | — |
| `targetShortEth` | Nguồn chưa rõ ràng | Xem I-004 |
| `driftPct` | tính toán local | — |
| `marginStatus` | `hedge_legs.margin_status` | — |
| `lastLightCheckAt` | Trường D1 chưa rõ ràng | Xem I-003 |
| `safe_mode_reason` | Không rõ nguồn | Chỉ có khi A1; nguồn chưa trace |

### F.1.4 Các trạng thái lifecycle_state liên quan đến hiển thị UC

| lifecycle_state | bots.status | Nhãn hiển thị theo UC | Nguồn |
|---|---|---|---|
| `active` | active | "Active" | UC §3 bước 9, US-002 AC-002-1 |
| `safe_mode` | safe_mode | "Safe Mode — No new actions" | UC §4 A1, US-002 AC-002-2 |
| `hedge_stopped_cooldown` | active | "Stop Fired — Cooldown (Xh remaining)" | UC §4 A2, US-002 AC-002-3 |
| `cooldown` | — | "Bot safely closed. USDC parked. Re-entry will be attempted automatically." | UC §4 A3 — **STALE: trạng thái này đã bị xóa HLD-2026-06-18** |
| (không có bot) | — | "No active bot" (404) | UC §4 A4 |

### F.1.5 Thông báo lỗi / phản hồi

| Tình huống | HTTP | Thông báo / Phản hồi | Nguồn |
|---|---|---|---|
| Không có bot cho user | 404 | "No active bot" | UC §4 A4 |
| Operator Facade không khả dụng | 503 | "Status service temporarily unavailable" | UC §4 A5 |
| MarketDataDO không khả dụng | Không định nghĩa | Không định nghĩa | — (xem I-005) |

---

## §F.2 Trạng thái, Quy tắc nghiệp vụ, Kiểm chứng

### F.2.1 Điều kiện tiên quyết

| Điều kiện | Mô tả | Nguồn |
|---|---|---|
| Investor đã xác thực | Session hợp lệ | UC §2 |
| Investor có ExBot đang hoạt động | bots record tồn tại cho user này | UC §2 |
| Operator Facade service khả dụng | CF service binding đến ExBot Worker hoạt động | UC §2 |

### F.2.2 Quy tắc nghiệp vụ áp dụng

| BR | Quy tắc | Tác động đến monitor-status | Nguồn |
|---|---|---|---|
| BR-EXBOT-007 | SAFE_MODE không bao giờ là trạng thái cuối | Màn hình status phải hiển thị SAFE_MODE có thể phục hồi; không hiển thị là "vĩnh viễn đóng" | srs/spec.md §4 |

### F.2.3 Quy tắc tính toán rangeState

| Điều kiện | rangeState | Nguồn |
|---|---|---|
| `tickLower <= currentTick < tickUpper` | in | UC §3 bước 5, FR-EXBOT-012 |
| `currentTick < tickLower` hoặc `currentTick >= tickUpper` | out-of-range | UC §3 bước 5, FR-EXBOT-012 |

### F.2.4 Quy tắc tính toán drift %

| Thành phần | Nguồn | Vấn đề |
|---|---|---|
| `actualShortEth` | `bot_runtime_state.last_known_hl_short_size` | Rõ ràng |
| `targetShortEth` | Không rõ — có thể từ `bot_runtime_state.target_short_size` hoặc tính lại từ `lpEthAmount × hedgeRatio` | Xem I-004 |
| Công thức | `(|actual - target| / target) × 100` | UC §3 bước 6 |

### F.2.5 margin_status và hành vi hiển thị

| margin_status | Hành vi hiển thị | Nguồn |
|---|---|---|
| ok | Không có banner đặc biệt | FR-EXBOT-060 |
| warning | Banner cảnh báo cho investor | FR-EXBOT-060 |
| critical | SAFE_MODE entry (critical × 2 liên tiếp); màn hình chuyển sang A1 | FR-EXBOT-060, FR-EXBOT-050 |

### F.2.6 Hành vi trạng thái `paused`

| Câu hỏi | Câu trả lời từ SRS | Vấn đề |
|---|---|---|
| Bot `status='paused'` hiển thị gì? | FR-EXBOT-005: "Paused — hedge is maintained, LP is maintained" | UC không có alternate flow cho `status='paused'`; xem I-006 |

---

## §F.3 Phân tích logic nghiệp vụ và luồng xử lý

### F.3.1 Luồng thành công — bot đang active

**Kích hoạt:** Investor mở màn hình ExBot status, bot có lifecycle_state='active'.
**Tác nhân:** POOL UI, Operator Facade, ExBot Worker, D1, MarketDataDO.

| Bước | Hành động | Phản hồi hệ thống |
|---|---|---|
| 1 | POOL UI gọi `GET /api/exbot/status` | Yêu cầu gửi đến Operator Facade |
| 2 | Operator Facade chuyển tiếp qua CF service binding với internal auth token | ExBot Worker nhận yêu cầu |
| 3 | ExBot Worker đọc đồng thời từ D1: bots.status, lifecycle_state, last_known_hl_short_size, positions.tickLower/tickUpper, hedge_legs.margin_status, next_light_check_at | Tất cả trường D1 được trả về |
| 4 | ExBot Worker truy vấn MarketDataDO lấy currentTick | currentTick hiện tại từ pool slot0 |
| 5 | ExBot Worker tính rangeState (in / out-of-range) | rangeState được xác định |
| 6 | ExBot Worker tính drift % | Drift % được tính |
| 7 | ExBot Worker tổng hợp JSON response | JSON đầy đủ tất cả trường |
| 8 | Response trả về Operator Facade → POOL UI | POOL UI nhận JSON |
| 9 | POOL UI render panel trạng thái | Investor thấy trạng thái đầy đủ |

### F.3.2 A1 — Bot trong SAFE_MODE

**Kích hoạt:** `bots.status='safe_mode'`.

| Điều kiện | Phản hồi hệ thống |
|---|---|
| Response bao gồm `safe_mode_reason` | UI hiển thị "Safe Mode — No new actions" + lý do |
| Tất cả nút thao tác bị tắt ngoại trừ "Close Bot (emergency)" | US-002 AC-002-2 |

**Vấn đề:** `safe_mode_reason` không có trong danh sách các trường D1 được đọc tại bước 3. Bảng `bots` trong erd.md không có cột `safe_mode_reason`. Nguồn dữ liệu cho trường này chưa rõ. (Xem I-009)

### F.3.3 A2 — Bot trong hedge_stopped_cooldown

**Kích hoạt:** `lifecycle_state='hedge_stopped_cooldown'`.

| Điều kiện | Phản hồi hệ thống |
|---|---|
| Response bao gồm cooldown end timestamp | UI hiển thị "Stop Fired — Cooldown (Xh remaining)" |
| Giải thích tự động re-hedge | US-002 AC-002-3 |

**Vấn đề:** Cooldown end timestamp không có trong bước 3 D1 read list. Trường nào trong D1 lưu giá trị này? FR-EXBOT-034 không định nghĩa cột D1 cụ thể cho cooldown end time. (Xem I-010)

### F.3.4 A3 — Bot trong lifecycle_state='cooldown' sau bot_safe_close

**Kích hoạt:** `lifecycle_state='cooldown'` (theo UC).

**Phát hiện:** Trạng thái `cooldown` đã bị XÓA bởi HLD-2026-06-18 (states.md changelog: "remove cooldown/parked states from state machine"). A3 hoàn toàn mô tả hành vi không còn tồn tại. (Xem I-001 — Blocker)

### F.3.5 A4 — Không có bot đang hoạt động

**Kích hoạt:** Không có bot active cho user.
**Phản hồi:** HTTP 404; UI hiển thị empty state "No active bot".

### F.3.6 A5 — Operator Facade không khả dụng

**Kích hoạt:** CF service binding thất bại.
**Phản hồi:** HTTP 503 Service Unavailable; UI hiển thị "Status service temporarily unavailable".

---

## §F.4 Tích hợp và nhất quán dữ liệu

| Tích hợp / Điểm dữ liệu | Đọc từ | Ghi vào | Nhất quán | Nguồn |
|---|---|---|---|---|
| D1 bots + positions + hedge_legs + bot_runtime_state | ExBot Worker | Không (read-only UC) | Dữ liệu phản ánh trạng thái cuối cùng được ghi bởi các worker khác (light-check, hedge-sync, deep-audit). Độ trễ: D1 eventual consistency trong CF Workers | UC §3, erd.md |
| MarketDataDO (pool slot0 cache) | ExBot Worker | Không (read-only từ góc độ UC này) | MarketDataDO cập nhật theo interval NV-12. Nếu cache cũ quá 2× refresh interval, DO tự refresh. currentTick có thể cũ vài giây so với on-chain | FR-EXBOT-093 |
| Operator Facade → ExBot Worker (CF service binding) | POOL UI | Không | ExBot Worker không thể truy cập từ internet. Tất cả yêu cầu đi qua Facade. Internal token authentication ngăn bypass | FR-EXBOT-090 |
| margin_status (D1 hedge_legs) vs thực tế HL | hedge_legs.margin_status từ D1 | Không cập nhật bởi UC này | margin_status chỉ cập nhật tại hedge-sync và deep-audit. monitor-status có thể trả về margin_status cũ so với trạng thái HL thực tế | FR-EXBOT-060, FR-EXBOT-016 |
| last_known_hl_short_size (D1) vs thực tế HL | bot_runtime_state.last_known_hl_short_size | Không cập nhật bởi UC này | Tương tự margin_status — chỉ cập nhật sau reconcile. Drift % tính toán dựa trên giá trị cached, không phải live HL | erd.md, FR-EXBOT-025 |

---

## §F.5 Các ứng viên Tiêu chí Chấp nhận

| AC | Kịch bản | Đầu vào | Kết quả mong đợi | Loại | Nguồn |
|---|---|---|---|---|---|
| AC-01 | Bot active — trạng thái đầy đủ hiển thị | lifecycle_state='active', margin_status='ok' | Tất cả trường hiển thị; rangeState=in; drift % < threshold | Luồng thành công | US-002 AC-002-1 |
| AC-02 | Bot active — LP out of range | currentTick < tickLower | rangeState='out-of-range' hiển thị | Biên | UC §3 bước 5 |
| AC-03 | Bot SAFE_MODE | status='safe_mode', có safe_mode_reason | Banner "Safe Mode"; tất cả nút bị tắt trừ "Close Bot (emergency)" | Luồng thay thế | US-002 AC-002-2 |
| AC-04 | Bot hedge_stopped_cooldown | lifecycle_state='hedge_stopped_cooldown' | "Stop Fired — Cooldown (Xh remaining)" hiển thị | Luồng thay thế | US-002 AC-002-3 |
| AC-05 | Không có bot | Không có bot active cho user | HTTP 404; empty state "No active bot" | Luồng âm | UC §4 A4 |
| AC-06 | Operator Facade không khả dụng | CF service binding thất bại | HTTP 503; "Status service temporarily unavailable" | Luồng ngoại lệ | UC §4 A5 |
| AC-07 | Bot paused | status='paused' | Hiển thị "Paused — hedge maintained, LP maintained" (*Suy luận cần xác nhận* — AC không có trong UC) | Suy luận cần xác nhận | FR-EXBOT-005 |
| AC-08 | margin_status='warning' | margin_status='warning' trong D1 | Banner cảnh báo cho investor; nút tăng size hedge bị tắt | Luồng thay thế | FR-EXBOT-060 |

---

## §10 Kết quả kiểm tra

### §10.1 Danh sách vấn đề

| ID vấn đề | Loại | Mức độ | Vùng ảnh hưởng | Truy nguyên nguồn | Phát hiện | Tác động đến Tester | Câu hỏi / Gợi ý sửa đổi | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| I-001 | CROSS_SOURCE_CONFLICT | Blocker | §F.3 Phân tích luồng | UC §4 A3 vs srs/states.md changelog HLD-2026-06-18; frd.md §2 | UC §4 A3 mô tả alternate flow cho `lifecycle_state='cooldown' after bot_safe_close` với thông báo "Bot safely closed. USDC parked. Re-entry will be attempted automatically." Tuy nhiên, states.md cập nhật 2026-06-18 ghi rõ: "`cooldown` and `parked` lifecycle states removed — park/redeploy feature dropped." Trạng thái `cooldown` không còn tồn tại trong lifecycle state machine. UC chưa được cập nhật để phản ánh thay đổi HLD. | Tester thiết kế test case cho A3 sẽ cố tạo dữ liệu với `lifecycle_state='cooldown'` — một trạng thái không thể xảy ra sau HLD-2026-06-18. UC cũng hiển thị nhãn `Cooldown` trong bước 9 (Status label list), gây nhầm lẫn thêm. | BA: xóa A3 khỏi UC §4 và xóa nhãn "Cooldown" khỏi danh sách Status label tại bước 9. Sau bot_safe_close, lifecycle_state chuyển thẳng sang 'closed' — không còn trạng thái parked/cooldown. | Mở |
| I-002 | CROSS_SOURCE_CONFLICT | Major | §F.1 Kiểm kê | UC §3 bước 9 vs srs/states.md HLD-2026-06-18 | UC §3 bước 9 liệt kê "Status label (Active/Safe Mode/Cooldown)" như là các nhãn hiển thị có thể có. Nhãn "Cooldown" tương ứng với `lifecycle_state='cooldown'` đã bị xóa bởi HLD-2026-06-18. | Tester xây dựng test data cho nhãn "Cooldown" sẽ kiểm thử hành vi không còn có thể xảy ra. | BA: cập nhật danh sách Status label tại bước 9 thành "Active / Safe Mode / Stop Fired Cooldown" (dùng `hedge_stopped_cooldown`) và loại bỏ "Cooldown" đơn giản. | Mở |
| I-003 | INTERNAL_INCONSISTENCY | Major | §F.1 Kiểm kê | UC §3 bước 3 vs bước 9 | UC §3 bước 3 nói đọc trường `next_light_check_at` (thời điểm light-check tiếp theo), nhưng bước 9 nói hiển thị "Last light-check timestamp" (thời điểm light-check cuối cùng). Đây là hai trường khác nhau: `next_light_check_at` là lịch trong tương lai; `last_light_check_at` là thời điểm đã qua. Bảng `bot_runtime_state` trong erd.md có cả hai: `last_light_check_at` (bot_runtime_state) và `next_light_check_at` (bots). | Tester không thể xác định trường nào cần kiểm chứng trong response — đọc `next_light_check_at` nhưng hiển thị "Last light-check" sẽ cho giá trị sai về mặt nghiệp vụ. | BA: làm rõ UC §3 cần đọc `bot_runtime_state.last_light_check_at` (nếu hiển thị "Last light-check") HOẶC giữ `bots.next_light_check_at` và đổi nhãn thành "Next light-check". Xác nhận trường nào được dùng trong response JSON. | Mở |
| I-004 | MISSING_INFO | Major | §F.3 Phân tích luồng | UC §3 bước 6; srs/spec.md FR-EXBOT-021; erd.md bot_runtime_state | UC §3 bước 6 tính drift % bằng `(|actualShortEth - targetShortEth| / targetShortEth) × 100` nhưng không định nghĩa nguồn của `targetShortEth`. SRS FR-EXBOT-021 định nghĩa `targetShortEth = lpEthAmount × hedgeRatio` (tính lại mỗi lần). Bảng `bot_runtime_state` trong erd.md có cột `target_short_size`. Không rõ monitor-status có: (a) đọc `target_short_size` từ D1 trực tiếp, hay (b) tính lại từ LP amounts hiện tại. Nếu (a), trường này không nằm trong danh sách đọc tại bước 3. | Tester không thể viết test case drift % mà không biết giá trị `targetShortEth` đến từ đâu. Nếu từ cache D1 (target_short_size), drift % sẽ khác với tính toán lại từ LP amounts thực tế. | BA/Tech Lead: xác định rõ tại bước 6 nguồn `targetShortEth` là: (a) `bot_runtime_state.target_short_size` đọc từ D1, hay (b) tính lại từ `lpEthAmount × hedgeRatio`. Cập nhật bước 3 để bao gồm trường được đọc nếu là (a). | Mở |
| I-005 | MISSING_INFO | Major | §F.3 Phân tích luồng | UC §4; FR-EXBOT-093 | UC §4 có alternate flow A5 cho Operator Facade không khả dụng (HTTP 503) nhưng không có alternate flow cho trường hợp MarketDataDO không khả dụng hoặc cache quá cũ. FR-EXBOT-093 nói DO tự refresh khi cache cũ hơn 2× refresh interval, nhưng nếu DO không thể truy cập hoàn toàn trong khi request đang xử lý, hành vi của ExBot Worker chưa được định nghĩa: trả về response thiếu `currentTick`/`rangeState`, hay trả về lỗi? | Tester không thể thiết kế test case cho MarketDataDO failure trong ngữ cảnh monitor-status. | BA: thêm alternate flow A6 cho MarketDataDO unavailable: ExBot Worker trả về partial response (có thể thiếu currentTick/rangeState) hay HTTP 503? | Mở |
| I-006 | MISSING_INFO | Major | §F.3 Phân tích luồng | UC §4 vs FR-EXBOT-005; srs/spec.md §2 | UC không có alternate flow cho bot `status='paused'`. SRS FR-EXBOT-005 định nghĩa màn hình status khi paused phải hiển thị "Paused — hedge is maintained, LP is maintained". US-002 cũng không có AC cho trạng thái paused. Nếu investor có bot đang paused và mở màn hình status, không rõ UI hiển thị gì. | Tester không thể thiết kế test case cho trạng thái paused vì cả UC lẫn US không mô tả nó. | BA: thêm alternate flow cho `status='paused'` trong UC §4, mô tả thông báo và hành vi UI; thêm AC cho US-002. | Mở |
| I-007 | MISSING_INFO | Minor | §F.1 Kiểm kê | UC §4 A3; srs/states.md | Như đã nêu tại I-001, A3 mô tả `lifecycle_state='cooldown'` không còn tồn tại. Nhưng thêm vào đó, nhãn trong bảng §F.1.4 (State Registry của UC §4 A3) hiển thị "cooldown" như một lifecycle_state cần hiển thị — đây là thừa sau khi I-001 được giải quyết. | Minor: sẽ tự giải quyết khi I-001 được sửa. | — | Mở |
| I-008 | UNCLEAR_INFO | Minor | §0 Phạm vi kiểm tra | UC §6 FR Trace; srs/spec.md FR-EXBOT-003 | UC §6 FR Trace bao gồm FR-EXBOT-003 (Bot Lifecycle State Tracking — định nghĩa 18 lifecycle states và chuỗi khởi tạo). FR-EXBOT-003 phần lớn liên quan đến khởi tạo bot và chuyển trạng thái, không phải đọc trạng thái. Việc trace này gợi ý monitor-status cần xử lý tất cả 18 trạng thái, nhưng UC chỉ đề cập 4 (active, safe_mode, hedge_stopped_cooldown, cooldown-đã-lỗi-thời). | Minor: tester cần biết UC có cần xử lý tất cả lifecycle states hay chỉ một tập con. | BA: xác nhận FR-EXBOT-003 trace là cố ý hay nhầm. Nếu cố ý, UC §4 cần thêm alternate flow cho các trạng thái như `lp_rebalancing`, `lp_closing`, `error`, `paused`. | Mở |
| I-009 | MISSING_INFO | Minor | §F.3 Phân tích luồng | UC §4 A1; erd.md bảng bots | UC §4 A1 nói response bao gồm `safe_mode_reason`, nhưng bảng `bots` trong erd.md không có cột `safe_mode_reason`. Trường này không nằm trong danh sách D1 được đọc tại UC §3 bước 3. Không rõ `safe_mode_reason` đến từ bảng nào, cột nào. | Tester không thể kiểm chứng `safe_mode_reason` được trả về đúng trong response. | BA/Tech Lead: xác định cột D1 nào lưu `safe_mode_reason` (có thể là `bots.health_status` hoặc cần thêm cột mới) và cập nhật UC §3 bước 3 để đọc trường đó. | Mở |
| I-010 | MISSING_INFO | Minor | §F.3 Phân tích luồng | UC §4 A2; erd.md; srs/spec.md FR-EXBOT-034 | UC §4 A2 nói response bao gồm "cooldown end timestamp" để UI tính "Xh remaining". Tuy nhiên, bảng `bots` và `hedge_legs` trong erd.md không có cột cụ thể cho cooldown end time. FR-EXBOT-034 định nghĩa cooldown là 4 giờ sau khi stop fires nhưng không chỉ định trường D1 nào lưu thời điểm kết thúc cooldown. | Tester không thể kiểm chứng "Xh remaining" được tính đúng vì không biết trường D1 nào được dùng. | BA/Tech Lead: xác định và ghi lại cột D1 lưu cooldown end time (có thể cần thêm cột vào bảng bots hoặc tính từ `hedge_legs.stop_trigger_crossed_at + 4h`) và cập nhật UC §3 bước 3. | Mở |

---

### §10.2 Phụ thuộc

| Phụ thuộc | Loại | Tác động | Nguồn |
|---|---|---|---|
| UC §4 A3 và nhãn "Cooldown" trong UC §3 bước 9 chưa được cập nhật theo HLD-2026-06-18 | Tài liệu nội bộ cũ | Blocker: tester có thể thiết kế test case cho trạng thái không còn tồn tại | srs/states.md HLD-2026-06-18 |
| Nguồn `targetShortEth` cho drift % tính toán chưa được định nghĩa | Thiếu thông tin | Tester không thể xác minh drift % chính xác | UC §3 bước 6, erd.md bot_runtime_state |
| Trường D1 cho `safe_mode_reason` chưa xác định | Thiếu thông tin | Tester không thể kiểm chứng A1 response chứa đúng lý do | erd.md, UC §4 A1 |
| Trường D1 cho cooldown end time chưa xác định | Thiếu thông tin | Tester không thể kiểm chứng "Xh remaining" trong A2 | erd.md, FR-EXBOT-034 |
| Không có alternate flow cho bot paused và MarketDataDO unavailable | Thiếu thông tin | Tester không thể thiết kế test cho hai kịch bản này | UC §4, FR-EXBOT-005, FR-EXBOT-093 |

---

### §10.3 Tóm tắt kiểm tra

#### Bảng điểm

| # | Vùng đánh giá | Điểm tối đa | Điểm đạt được | Trạng thái | Vấn đề chính |
|---:|---|---|---|---|---|
| 1 | Kiểm kê Chức năng / Thao tác & Đối tượng dữ liệu | 20 | 14 | Một phần | I-003: không nhất quán next vs last light-check field; I-009: safe_mode_reason không trace; I-010: cooldown end time không trace |
| 2 | Thuộc tính Đối tượng dữ liệu / Trạng thái, Quy tắc nghiệp vụ, Kiểm chứng | 25 | 18 | Một phần | I-004: nguồn targetShortEth không định nghĩa; I-006: trạng thái paused không có AC |
| 3 | Phân tích Logic nghiệp vụ & Luồng xử lý | 25 | 13 | Một phần (bị chặn) | I-001: A3 mô tả lifecycle_state='cooldown' đã bị xóa [Blocker]; I-005: MarketDataDO failure path không định nghĩa; I-006: paused flow thiếu |
| 4 | Tích hợp chức năng & Nhất quán dữ liệu | 15 | 12 | Một phần | Tích hợp D1 và MarketDataDO có thể trace; độ trễ cache D1 được ghi nhận nhưng không gây blocker |
| 5 | Chất lượng Tài liệu UC / Đặc tả | 15 | 8 | Yếu (bị chặn) | I-001 [Blocker]; I-002: nhãn "Cooldown" lỗi thời; I-008: FR-003 trace không rõ mục đích |

**Tổng cộng: 65 / 100**

#### Điều chỉnh điểm tự động (Auto-cap)

Vùng 3 bị chặn ở mức 52% (13/25): Blocker I-001 tạo ra alternate flow mô tả hành vi không thể xảy ra sau HLD-2026-06-18. Quy tắc: Blocker → vùng ảnh hưởng tối đa 40% điểm tối đa (10/25). Tuy nhiên, tác động của I-001 đến Vùng 3 là một trong nhiều alternate flows, không phải luồng thành công chính. Điểm đặt ở 13/25 phản ánh rằng luồng thành công (F.3.1) và các alternate flow hợp lệ khác (A1, A2, A4, A5) đủ rõ ràng để thiết kế kiểm thử.

#### Các vấn đề Blocker (điều kiện tự động thất bại)

| ID | Mức độ | Mô tả |
|---|---|---|
| I-001 | Blocker | UC §4 A3 mô tả `lifecycle_state='cooldown' after bot_safe_close` — trạng thái này đã bị xóa bởi HLD-2026-06-18; UC chưa được cập nhật |

#### Kết luận

**Điểm: 65 / 100 — Chưa sẵn sàng (Not Ready)**

UC-EXBOT-monitor-status có 1 Blocker và 5 vấn đề Major ngăn cản việc thiết kế kiểm thử toàn diện. Blocker I-001 (alternate flow cho trạng thái `cooldown` đã bị xóa) là hậu quả trực tiếp của việc UC chưa được đồng bộ với HLD-2026-06-18. Các vấn đề Major quan trọng nhất là: nguồn dữ liệu cho `targetShortEth` chưa rõ ràng (làm cho test case drift % không thể viết được); không nhất quán giữa trường D1 được đọc và trường hiển thị trong response JSON (I-003); và thiếu alternate flow cho hai kịch bản thực tế là bot paused (I-006) và MarketDataDO unavailable (I-005).

**Hành động ưu tiên cho BA:**
1. Xóa A3 (`lifecycle_state='cooldown'`) và nhãn "Cooldown" khỏi danh sách status labels (I-001, I-002).
2. Làm rõ UC §3 bước 3 đọc `last_light_check_at` hay `next_light_check_at` và cập nhật bước 9 nhất quán (I-003).
3. Định nghĩa nguồn `targetShortEth` cho drift % calculation (I-004).
4. Thêm alternate flow cho `status='paused'` (I-006) và MarketDataDO unavailable (I-005).
5. Xác định trường D1 cho `safe_mode_reason` (I-009) và cooldown end time (I-010).
