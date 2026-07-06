# Test Scenarios — UC-EXBOT-monitor-status: View Active ExBot Status

> **Nguồn:** `docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260706_v4.md`  
> **Ngày tạo:** 2026-07-06  
> **Domain/Architecture:** AWS Lambda (ExBot Lambda) + Aurora PostgreSQL Serverless v2 + ElastiCache Redis (Pool Slot0 Cache) + API Gateway + HMAC Lambda Authorizer — no UI; tất cả kết quả kiểm thử là API response, trạng thái Aurora PostgreSQL, và logic dẫn xuất.  
> **Phiên bản:** v3 (cập nhật 2026-07-06: gen lại toàn bộ theo arc-migration — D1→Aurora PostgreSQL, ExBot Worker→ExBot Lambda, MarketDataDO→Pool Slot0 Cache, shared-secret→HMAC Lambda Authorizer; 49 scenarios từ audit v4)

---

## UC-EXBOT-monitor-status — View Active ExBot Status

---

### Scenario ID: TS_UC-EXBOT-monitor-status_001
**Scenario Title:** Happy path — bot active, Pool Slot0 Cache có tick hợp lệ, Investor là chủ sở hữu
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3, FR-EXBOT-090, FR-EXBOT-003
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` với `X-Wallet-Address` khớp `bot.user_wallet_address`; bot có `lifecycle_state='active'`, `status='active'`; Pool Slot0 Cache trả về `currentTick` hợp lệ. Hệ thống phải trả về HTTP 200 với tất cả Implemented fields được điền đầy đủ, `range_state` là `"in"` hoặc `"out"`, `drift_pct` được tính bằng BigDecimal, `margin_status` là một trong `ok/warning/critical`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_002
**Scenario Title:** Pending fields trả về null — không vắng mặt khỏi JSON response
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 7, AC-15
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi các trường Pending implementation chưa được triển khai. Hệ thống phải trả về HTTP 200 với tất cả Pending fields (`tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`, `safe_mode_reason`, `cooldown_end_at`) có mặt trong JSON response với giá trị `null` — không bị vắng mặt hoàn toàn.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_003
**Scenario Title:** A1 — bot ở trạng thái safe_mode, response có safe_mode_reason
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A1, BR-EXBOT-007, FR-EXBOT-050
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `bots.status='safe_mode'`. Hệ thống phải trả về HTTP 200 với `status='safe_mode'` và trường `safe_mode_reason` chứa lý do vào SAFE_MODE (không phải null). BR-EXBOT-007: SAFE_MODE không phải trạng thái terminal — bot vẫn phản hồi truy vấn status.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_004
**Scenario Title:** A2 — bot ở trạng thái hedge_stopped_cooldown, response có cooldown_end_at
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A2, FR-EXBOT-034
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `bots.lifecycle_state='hedge_stopped_cooldown'`. Hệ thống phải trả về HTTP 200 với `lifecycle_state='hedge_stopped_cooldown'` và trường `cooldown_end_at` chứa timestamp kết thúc cooldown (không phải null).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_005
**Scenario Title:** A3a — bot ở trạng thái lp_closing, response có message E-EXBOT-021
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A3a, AC-04
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `bots.lifecycle_state='lp_closing'`. Hệ thống phải trả về HTTP 200 với `lifecycle_state='lp_closing'` và message E-EXBOT-021: "Bot close is in progress. Please wait." trong response body.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_006
**Scenario Title:** A3b — bot ở trạng thái closed, trả về 200 (không phải 404), message E-EXBOT-022
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A3b, AC-05
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `bots.lifecycle_state='closed'`; bản ghi bot vẫn tồn tại trong Aurora PostgreSQL. Hệ thống phải trả về HTTP 200 (KHÔNG phải 404) với `lifecycle_state='closed'` và message E-EXBOT-022: "Bot safely closed. Funds have been returned to your wallet."
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_007
**Scenario Title:** A4 — không có bản ghi bot nào trong Aurora PostgreSQL, trả về 404 E-EXBOT-023
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A4, AC-06
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` với `botId` không tồn tại bản ghi nào trong Aurora PostgreSQL. Hệ thống phải trả về HTTP 404 với E-EXBOT-023: "No active bot found for this account."
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_008
**Scenario Title:** A5 — Operator Facade không khả dụng, trả về 503 không có E-EXBOT code
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A5, FR-EXBOT-090
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi Operator Facade hoặc API Gateway không khả dụng (lỗi ở tầng infra AWS). Hệ thống phải trả về HTTP 503 Service Unavailable. Response không được chứa E-EXBOT-* code (đây là lỗi tầng infra, không phải application-defined).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_009
**Scenario Title:** A6 — bot ở trạng thái lp_rebalancing, trả về 200 với lifecycle_state đúng
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A6, AC-08
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `bots.lifecycle_state='lp_rebalancing'`. Hệ thống phải trả về HTTP 200 với `lifecycle_state='lp_rebalancing'`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_010
**Scenario Title:** A7 — bot ở trạng thái error, trả về 200 với status='error'
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A7, AC-09
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `bots.status='error'`. Hệ thống phải trả về HTTP 200 với `status='error'`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_011
**Scenario Title:** A8 — Pool Slot0 Cache không khả dụng, current_tick và range_state là null, các trường khác bình thường
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A8, FR-EXBOT-093, AC-07
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi Pool Slot0 Cache (ElastiCache Redis) không trả được dữ liệu hoặc snapshot đã stale. Hệ thống phải trả về HTTP 200 với `current_tick: null` và `range_state: null`; tất cả các trường Aurora PostgreSQL khác (`status`, `lifecycle_state`, `margin_status`, `last_light_check_at`, v.v.) được điền bình thường. Không có HTTP 503, không có retry.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_012
**Scenario Title:** A8 — Pool Slot0 Cache stale (snapshot cũ), xử lý giống unavailable
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A8, FR-EXBOT-093
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi Pool Slot0 Cache có dữ liệu nhưng `blockNumber` stale (vượt quá 2× khoảng thời gian làm mới theo OQ-EXBOT-09). Hệ thống phải xử lý snapshot stale giống như cache không khả dụng — trả về `current_tick: null`, `range_state: null`; không block response.
**Test Focus:** Alternative flow


---

### Scenario ID: TS_UC-EXBOT-monitor-status_013
**Scenario Title:** BVA rangeState — currentTick bằng đúng tickLower (biên dưới inclusive)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 5
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `currentTick == tickLower` (biên dưới). Theo khoảng nửa mở `[tickLower, tickUpper)`, hệ thống phải trả về `range_state: "in"`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_014
**Scenario Title:** BVA rangeState — currentTick bằng tickLower - 1 (dưới biên dưới)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 5
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `currentTick == tickLower - 1` (một bước dưới biên). Hệ thống phải trả về `range_state: "out"`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_015
**Scenario Title:** BVA rangeState — currentTick bằng đúng tickUpper (biên trên exclusive)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 5
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `currentTick == tickUpper` (biên trên). Theo khoảng nửa mở `[tickLower, tickUpper)`, `tickUpper` không được bao gồm. Hệ thống phải trả về `range_state: "out"`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_016
**Scenario Title:** BVA rangeState — currentTick bằng tickUpper - 1 (trong range, sát biên trên)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 5
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `currentTick == tickUpper - 1` (một bước trong biên). Hệ thống phải trả về `range_state: "in"`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_017
**Scenario Title:** BVA rangeState — currentTick là null, range_state phải null (không tính toán)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 5, §4 A8
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi Pool Slot0 Cache không có `currentTick` (`current_tick: null`). Hệ thống phải bỏ qua tính toán rangeState và trả về `range_state: null` — không được trả về `"in"` hoặc `"out"` dựa trên giả định.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_018
**Scenario Title:** BVA margin_status — marginUsage bằng đúng ngưỡng 0.55 (ranh giới ok/warning)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §6.1B, FR-EXBOT-060
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `hedge_legs.margin_status='warning'` (đã được lưu bởi hedge-sync preflight tại đúng ngưỡng marginUsage = 0.55). Hệ thống phải trả về `margin_status: "warning"` trong response — không phải `"ok"`. Lưu ý: status read đọc giá trị từ Aurora PostgreSQL, không tính lại. Test data phải cài `margin_status='warning'` sẵn.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_019
**Scenario Title:** BVA margin_status — marginUsage dưới 0.55 (trạng thái ok)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §6.1B, FR-EXBOT-060
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `hedge_legs.margin_status='ok'` (marginUsage < 0.55). Hệ thống phải trả về `margin_status: "ok"`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_020
**Scenario Title:** BVA margin_status — marginUsage bằng đúng ngưỡng 0.75 (ranh giới warning/critical)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §6.1B, FR-EXBOT-060
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `hedge_legs.margin_status='critical'` (đã được lưu bởi hedge-sync preflight tại đúng ngưỡng marginUsage = 0.75). Hệ thống phải trả về `margin_status: "critical"`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_021
**Scenario Title:** drift% — giữ chỗ pending I-003 (nguồn targetShortEth chưa xác nhận)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 6, FR-EXBOT-021, NFR-EXBOT-008
**Test Type:** Functional
**Description:** ⚠️ **PLACEHOLDER — blocked theo I-003.** Gọi `GET /api/exbot/status` với giá trị `actualShortEth` và `targetShortEth` đã biết. Hệ thống phải tính `drift_pct = (|actualShortEth - targetShortEth| / targetShortEth) × 100` bằng BigDecimal; kết quả không được có lỗi làm tròn số dấu phẩy động. Assertion cụ thể bị block: không thể xác định nguồn `targetShortEth` (đọc từ `bot_runtime_state.target_short_size` hay tính lại từ `lpEthAmount × hedgeRatio`) cho đến khi Tech Lead giải quyết I-003.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_022
**Scenario Title:** drift% — mẫu số (targetShortEth) bằng 0, hành vi hệ thống cần xác nhận
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 6, FR-EXBOT-021
**Test Type:** Functional
**Description:** ⚠️ **PLACEHOLDER — blocked theo I-003(c).** Gọi `GET /api/exbot/status` trong điều kiện `targetShortEth = 0` (ví dụ: bot vừa close hedge, target = 0). Hệ thống không được thực hiện phép chia cho 0. Hành vi mong đợi (null, 0, hay lỗi cụ thể) cần được BA/Tech Lead định nghĩa trước khi có thể viết assertion.
**Test Focus:** Error/Exception


---

### Scenario ID: TS_UC-EXBOT-monitor-status_023
**Scenario Title:** Auth — thiếu header X-Wallet-Address, Operator Facade trả về 401
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2, AC-12
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` không có header `X-Wallet-Address`. Operator Facade phải trả về HTTP 401 Unauthorized ngay lập tức, không chuyển tiếp yêu cầu đến ExBot Lambda.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_024
**Scenario Title:** Auth — ví Investor không khớp bot.user_wallet_address, trả về 403
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2, AC-10
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` với `X-Wallet-Address` của một Investor nhưng `wallet_address` không khớp `bot.user_wallet_address` trong Aurora PostgreSQL (Investor đang cố đọc bot của người dùng khác). Hệ thống phải trả về HTTP 403 Forbidden.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_025
**Scenario Title:** Auth — ví Investor bị block bởi Operator Facade, trả về 403
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` với `X-Wallet-Address` của ví đã bị Operator Facade block. Hệ thống phải trả về HTTP 403 Forbidden — không chuyển tiếp đến ExBot Lambda.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_026
**Scenario Title:** Auth — HMAC signature không hợp lệ trong request Facade→Lambda, trả về 401
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2, AC-13, FR-EXBOT-090
**Test Type:** Functional
**Description:** Operator Facade chuyển tiếp yêu cầu đến ExBot Lambda qua API Gateway nhưng HMAC signature không hợp lệ hoặc thiếu. HMAC Lambda Authorizer phải từ chối và trả về HTTP 401.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_027
**Scenario Title:** Auth — Admin bypass kiểm tra quyền sở hữu ví, đọc được bot của người dùng khác
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2, AC-11
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` với `X-Wallet-Address` của Admin để truy vấn bot thuộc về Investor khác (wallet khác với Admin). Hệ thống phải trả về HTTP 200 với dữ liệu bot đầy đủ — kiểm tra quyền sở hữu được bỏ qua cho Admin.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_028
**Scenario Title:** Auth — Investor đọc đúng bot của mình (ownership match), được phép truy cập
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §2, AC-01
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` với `X-Wallet-Address` khớp chính xác `bot.user_wallet_address`. Hệ thống phải trả về HTTP 200 với dữ liệu bot của Investor đó — không bị 403.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_029
**Scenario Title:** State transition — bot ở trạng thái paused (status=paused, lifecycle_state=active)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §6.1, FR-EXBOT-003, srs/states.md
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi bot bị pause (`bots.status='paused'`, `lifecycle_state='active'`). Theo FR-EXBOT-003, pause giữ nguyên `lifecycle_state` ở giá trị trước khi pause. Hệ thống phải trả về HTTP 200 phản ánh đúng cả hai giá trị (`status='paused'`, `lifecycle_state='active'`).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_030
**Scenario Title:** State transition — bot ở trạng thái transitional (lp_opening), response phản ánh đúng
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §6.1, FR-EXBOT-003, srs/states.md
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi bot đang ở trạng thái transitional trong quá trình khởi tạo (`lifecycle_state='lp_opening'` hoặc các transitional states khác). Hệ thống phải trả về HTTP 200 với `lifecycle_state` phản ánh đúng trạng thái transitional hiện tại — không trả về 404 hay lỗi.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_031
**Scenario Title:** Tính nhất quán dữ liệu — last_light_check_at phản ánh đúng thời gian light-check gần nhất
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 3, §7
**Test Type:** Data/State
**Description:** Sau khi một light-check hoàn thành (cập nhật `bot_runtime_state.last_light_check_at`), gọi `GET /api/exbot/status`. Hệ thống phải trả về `last_light_check_at` khớp chính xác với giá trị trong Aurora PostgreSQL tại thời điểm truy vấn — không phải giá trị cũ hay dự đoán.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_032
**Scenario Title:** Tính nhất quán dữ liệu — margin_status là giá trị cuối cùng được ghi bởi hedge-sync/deep-audit, không tính lại
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §7, FR-EXBOT-060
**Test Type:** Data/State
**Description:** Cài `hedge_legs.margin_status='warning'` trong Aurora PostgreSQL (mô phỏng hedge-sync preflight đã cập nhật). Gọi `GET /api/exbot/status`. Hệ thống phải trả về `margin_status: "warning"` — đúng với giá trị trong Aurora PostgreSQL, không tính lại từ HL API (light-check HL weight = 0 theo BR-EXBOT-003).
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_033
**Scenario Title:** Tính nhất quán dữ liệu — response tổng hợp đúng từ 4 bảng Aurora PostgreSQL khác nhau
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 3, srs/erd.md
**Test Type:** Data/State
**Description:** Cài dữ liệu nhất quán trên 4 bảng: `bots`, `positions`, `hedge_legs`, `bot_runtime_state` — với các giá trị phân biệt cho từng bảng. Gọi `GET /api/exbot/status`. Hệ thống phải trả về response tổng hợp đúng từ tất cả 4 bảng theo đúng `bot_id` — không bị trộn dữ liệu giữa các bảng hay giữa các bot.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_034
**Scenario Title:** Dual-chain — bot trên Base trả về LP range đúng (tick_lower/tick_upper từ Base pool)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §9, FR-EXBOT-004, srs/erd.md
**Test Type:** Data/State
**Description:** Gọi `GET /api/exbot/status` cho bot đang chạy trên Base (chain 8453). Hệ thống phải trả về `tick_lower` và `tick_upper` từ bảng `positions` của bot trên Base — không bị lẫn với giá trị của bot Optimism.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_035
**Scenario Title:** Dual-chain — bot trên Optimism trả về LP range đúng (tick_lower/tick_upper từ OP pool)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §9, FR-EXBOT-004, srs/erd.md
**Test Type:** Data/State
**Description:** Gọi `GET /api/exbot/status` cho bot đang chạy trên Optimism (chain 10). Hệ thống phải trả về `tick_lower` và `tick_upper` từ bảng `positions` của bot trên Optimism — `wethIndex` của mỗi chain được lưu riêng tại thời điểm mở LP và được đọc đúng.
**Test Focus:** Integration


---

### Scenario ID: TS_UC-EXBOT-monitor-status_036
**Scenario Title:** Tích hợp chuỗi đầy đủ — POOL UI → Operator Facade → ExBot Lambda → Aurora PostgreSQL (luồng chuyển tiếp chuẩn)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 (toàn bộ), FR-EXBOT-090
**Test Type:** Integration
**Description:** Thực hiện `GET /api/exbot/status` từ POOL UI với đầy đủ HMAC signature hợp lệ. Kiểm chứng rằng yêu cầu đi qua đúng chuỗi: POOL UI → Operator Facade → API Gateway → HMAC Lambda Authorizer (thành công) → ExBot Lambda → Aurora PostgreSQL → trả response về POOL UI. Tất cả các tầng đều xử lý đúng và HTTP 200 được trả về với đủ dữ liệu.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_037
**Scenario Title:** Đọc đồng thời — hai request GET /api/exbot/status cùng bot_id gửi đồng thời, không có race condition hay dữ liệu lẫn
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3, FR-EXBOT-090
**Test Type:** Integration
**Description:** Gửi đồng thời hai request `GET /api/exbot/status` cho cùng một `bot_id` (mô phỏng hai phiên Investor/Admin truy cập cùng lúc). Cả hai phải nhận được HTTP 200 với dữ liệu nhất quán và đồng nhất — không có race condition làm lẫn dữ liệu giữa hai response, không có deadlock hay error.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_038
**Scenario Title:** Idempotency — cùng một request GET /api/exbot/status gửi lại nhiều lần, response không thay đổi nếu dữ liệu bot không đổi
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3
**Test Type:** Integration
**Description:** Gửi `GET /api/exbot/status` cho cùng một `bot_id` nhiều lần liên tiếp mà không có thay đổi trạng thái bot ở giữa. Mỗi response phải trả về cùng dữ liệu — endpoint là read-only, không có side effect, không có mutation nào được thực hiện.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_039
**Scenario Title:** E2E — sau khi bot được khởi động (bot-start), truy vấn status phản ánh lifecycle_state='active'
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3, FR-EXBOT-003, srs/states.md
**Test Type:** End-to-End
**Description:** Khởi động bot (UC-EXBOT-bot-start flow hoàn thành). Sau đó gọi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `lifecycle_state='active'` và `status='running'` — phản ánh đúng trạng thái bot sau khi bot-start hoàn thành. Kiểm chứng rằng Aurora PostgreSQL được cập nhật đúng trước khi status được query.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_040
**Scenario Title:** E2E — sau khi light-check hoàn thành, last_light_check_at trong response được cập nhật chính xác
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 3, §7
**Test Type:** End-to-End
**Description:** Ghi nhận giá trị `last_light_check_at` trước khi light-check chạy. Kích hoạt light-check (bot ở trạng thái active). Sau khi light-check hoàn thành và `bot_runtime_state.last_light_check_at` được cập nhật trong Aurora PostgreSQL, gọi `GET /api/exbot/status`. Hệ thống phải trả về `last_light_check_at` mới (lớn hơn giá trị trước) — không phải timestamp cũ.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_041
**Scenario Title:** Acceptance — AC-EXBOT-002-1: Investor có bot active xem được đầy đủ status panel
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-1
**Test Type:** Acceptance
**Description:** Investor có bot với `lifecycle_state='active'` gọi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với tất cả các trường đầy đủ: `status`, `lifecycle_state`, `tick_lower`, `tick_upper`, `current_tick`, `range_state` (in/out), `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at` — đủ để POOL UI hiển thị panel bot status đầy đủ.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_042
**Scenario Title:** Acceptance — AC-EXBOT-002-2: Bot ở SAFE_MODE — response có safe_mode_reason, tất cả mutation buttons bị vô hiệu hóa trừ emergency close
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-2, BR-EXBOT-007
**Test Type:** Acceptance
**Description:** Investor có bot với `status='safe_mode'` gọi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `status='safe_mode'` và trường `safe_mode_reason` không null — chứa lý do kích hoạt Safe Mode. Response phải đủ để POOL UI hiển thị banner "Safe Mode — No new actions" và chỉ cho phép "Close Bot (emergency)".
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_043
**Scenario Title:** Acceptance — AC-EXBOT-002-3: Bot trong hedge_stopped_cooldown — response có cooldown_end_at
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** US-EXBOT-002 AC-EXBOT-002-3
**Test Type:** Acceptance
**Description:** Investor có bot với `lifecycle_state='hedge_stopped_cooldown'` gọi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `lifecycle_state='hedge_stopped_cooldown'` và `cooldown_end_at` không null (ISO 8601 string). Response phải đủ để POOL UI hiển thị "Stop Fired — Cooldown (Xh remaining)" và các mutation buttons bị vô hiệu hóa.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_044
**Scenario Title:** Invalid state transition — không thể gọi mutation trên bot đang ở safe_mode thông qua endpoint status (read-only, endpoint không thực hiện write)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §1, BR-EXBOT-007
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi bot đang ở `status='safe_mode'`. Kiểm chứng rằng endpoint này là read-only — không có thay đổi state nào được thực hiện bởi chính endpoint status, dù bot đang ở trạng thái bất kỳ. Response trả về HTTP 200 phản ánh đúng `safe_mode` state hiện tại.
**Test Focus:** State transition


---

### Scenario ID: TS_UC-EXBOT-monitor-status_045
**Scenario Title:** BVA margin_status — margin_status khi chưa có dữ liệu hedge_legs (Pending — giá trị null)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 3, §7; FR-EXBOT-060
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi `hedge_legs.margin_status` chưa được cập nhật bởi bất kỳ lần chạy hedge-sync/deep-audit nào (giá trị NULL trong Aurora PostgreSQL). Hệ thống phải trả về `margin_status: null` — thuộc nhóm Pending implementation fields, không trả về giá trị mặc định sai như "ok".
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_046
**Scenario Title:** Pending fields — tất cả 11 trường Pending implementation trả về null khi chưa được triển khai
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 7 (null-handling note)
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi chức năng Pending implementation chưa được triển khai (môi trường chỉ có Implemented fields). Kiểm chứng rằng tất cả 11 trường Pending (`tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`, `safe_mode_reason`, `cooldown_end_at`) đều có mặt trong JSON với giá trị `null` — không phải vắng mặt khỏi response (absent từ JSON là hành vi khác với null).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_047
**Scenario Title:** Implemented fields — 8 trường Implemented luôn có giá trị không null khi bot tồn tại và active
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §3 bước 7
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi bot tồn tại với `lifecycle_state='active'`. Kiểm chứng rằng tất cả 8 trường Implemented (`bot_id`, `status`, `lifecycle_state`, `safe_mode_tier`, `runtime_health_status`, `last_reconcile_at`, `last_error_code`, `dry_run`) đều có mặt trong JSON response — không có trường nào vắng mặt khỏi response. Lưu ý: `safe_mode_tier`, `last_reconcile_at`, `last_error_code` có thể là null nhưng phải có mặt.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_048
**Scenario Title:** State transition — bot ở trạng thái error (status='error') yêu cầu admin can thiệp
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4 A7, srs/states.md
**Test Type:** Functional
**Description:** Gọi `GET /api/exbot/status` khi bot có `status='error'` (A7). Hệ thống phải trả về HTTP 200 với `status='error'` — response đủ để POOL UI hiển thị "Bot error — admin intervention required" và chỉ cho phép "Close Bot (emergency)".
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_049
**Scenario Title:** Kiểm tra toàn bộ các trạng thái lifecycle_state hợp lệ — mỗi state trả về đúng giá trị trong response (EP per state)
**UC Reference:** UC-EXBOT-monitor-status — View Active ExBot Status
**Req-ID:** UC-EXBOT-monitor-status §4, srs/states.md, FR-EXBOT-003
**Test Type:** Functional
**Description:** Đối với mỗi `lifecycle_state` hợp lệ trong state machine (`active`, `lp_rebalancing`, `lp_closing`, `closed`, `hedge_stopped_cooldown`, `lp_opening`, và các transitional states khác theo srs/states.md), gọi `GET /api/exbot/status`. Kiểm chứng rằng `lifecycle_state` trong response khớp chính xác với giá trị đang lưu trong Aurora PostgreSQL — không có state nào bị chuyển đổi sai hay mất thông tin.
**Test Focus:** State transition

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---------------|--------|--------------------|
| drift% boundary values và divide-by-zero handling | **BLOCKED: I-003** — nguồn dữ liệu `targetShortEth` chưa được xác nhận (UC step 3 thiếu, FR-EXBOT-021 có thể tính lại hoặc đọc từ `bot_runtime_state.target_short_size`). Không thể thiết kế assertion chính xác khi không biết nguồn giá trị đầu vào. | Resolve I-003 qua qc-qna → BA confirm (a) nguồn target_short_eth, (b) behavior khi mẫu số = 0 → re-design TS_021 và TS_022 sau khi có câu trả lời |
| Performance / Load testing (throughput GET /api/exbot/status dưới tải cao) | **NFR: PERFORMANCE** — nằm ngoài scope Functional của skill này | Defer đến performance testing chuyên biệt với k6 / Artillery |
| Security penetration testing (injection, replay attack HMAC, brute-force signature) | **NFR: SECURITY (beyond functional auth)** — phần auth được cover bởi TS_023–TS_028; các attack vector nâng cao nằm ngoài scope | Defer đến security testing chuyên biệt (OWASP, penetration test) |
| Kiểm chứng giá trị `tick_lower` / `tick_upper` từ smart contract trực tiếp (on-chain ↔ off-chain consistency cho LP position) | **BLOCKED: scope** — UC này chỉ đọc từ Aurora PostgreSQL (off-chain mirror), không trực tiếp query on-chain. Consistency giữa on-chain và Aurora PostgreSQL thuộc về UC-EXBOT-bot-start hoặc UC-EXBOT-lp-rebalance khi position được mở/điều chỉnh | Verify on-chain ↔ Aurora sync trong UC bot-start/rebalance; UC này chỉ cần verify Aurora reads đúng |
| whitelist mode 403 (access_mode=whitelist, ví ngoài whitelist) | **BLOCKED: N-002** — chưa có alternate flow tường minh cho trường hợp này trong UC (N-002 open question yêu cầu BA thêm A9). TS_025 bao phủ một phần nhưng chưa đủ scenario tường minh. | Resolve N-002 → BA thêm alternate flow A9 → thiết kế scenario đầy đủ sau khi A9 được định nghĩa |
| dry_run mode behavior (dry_run=true) — các giá trị có khác không khi dry_run=true | Không được mô tả trong UC, không có FR tường minh cho hành vi này trong status response | BA xác nhận liệu dry_run field trong status response có ảnh hưởng đến logic nào không, hay chỉ là readonly flag |

