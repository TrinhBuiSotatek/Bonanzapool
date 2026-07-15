# Test Scenarios — UC-EXBOT-monitor-status Monitor Status

> **Nguồn:** docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260715_v5.md
> **Ngày tạo:** 2026-07-15
> **Tác giả:** qc-func-scenario-design-exbot
> **Phiên bản:** v4
> **Domain/Architecture:** AWS Lambda (ExBot) + Aurora PostgreSQL Serverless v2 (`state_db_shard`) + ElastiCache Redis (Pool Slot0 Cache) — Back-End only, không có UI; xác thực qua HMAC Lambda Authorizer giữa Operator Facade và ExBot Lambda.

---

## Bảng mã viết tắt

| Code / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC-EXBOT | Use Case — ExBot module. Trong dự án: mỗi UC mô tả một nghiệp vụ cụ thể của hệ thống bot giao dịch tự động. | usecases/index.md |
| BR-EXBOT | Business Rule — quy tắc nghiệp vụ ràng buộc hành vi của ExBot. | common-rules.md |
| E-EXBOT | Error code — mã lỗi định danh thông báo lỗi của ExBot trả về cho client. | message-list.md |
| NFR-EXBOT | Non-Functional Requirement — yêu cầu phi chức năng (hiệu năng, bảo mật, độ chính xác tính toán). | frd.md |
| HMAC | Hash-based Message Authentication Code — thuật toán xác thực yêu cầu giữa Operator Facade và ExBot Lambda qua API Gateway. Trong dự án: HMAC-SHA256, khoá do Facade giữ. | (industry term) |
| EP | Equivalence Partitioning — phân vùng tương đương, kỹ thuật thiết kế test chia miền đầu vào thành các lớp có hành vi tương tự. | (industry term) |
| BVA | Boundary Value Analysis — phân tích giá trị biên, tập trung vào giá trị tại ranh giới của điều kiện. | (industry term) |

---

## UC-EXBOT-monitor-status — Monitor Status

### Scenario ID: TS_UC-EXBOT-monitor-status_001
**Scenario Title:** Happy path — bot đang hoạt động bình thường, trả về đầy đủ 8 trường đã triển khai
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §3 Main Flow
**Test Type:** Functional
**Description:** Gửi yêu cầu `GET /api/exbot/status` với chữ ký HMAC hợp lệ từ ví đã đăng ký whitelist; bot đang ở trạng thái `running`, có dữ liệu đầy đủ trên Aurora PG và Pool Slot0 Cache. Hệ thống phải trả về HTTP 200 với đủ 8 trường đã triển khai có giá trị hợp lệ (không null, không thiếu): `bot_id`, `status`, `margin_status`, `range_state`, `drift_pct`, `lp_eth_amount`, `lp_usdc_amount`, và trường timestamp reconcile (tên thực tế cần xác nhận theo V-002).
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-monitor-status_002
**Scenario Title:** Happy path — 11 trường Pending phải xuất hiện trong response với giá trị null
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Data Contract — Pending Fields
**Test Type:** Functional
**Description:** Trong cùng response HTTP 200 của luồng chính, kiểm tra rằng 11 trường ở trạng thái Pending (`target_ratio`, `actual_ratio`, `pnl_unrealized`, `pnl_realized`, `funding_earned`, `net_eth`, `net_usdc`, `hedge_size`, `hedge_entry_price`, `liquidation_price`, `health_score`) đều xuất hiện trong JSON body với giá trị `null`. Không được thiếu bất kỳ trường nào — response thiếu trường và response có trường với giá trị null là hai trường hợp khác nhau.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_003
**Scenario Title:** A1 — bot ở trạng thái `safe_mode`, response phản ánh đúng trạng thái
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A1; BR-EXBOT-007
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `safe_mode` trên Aurora PG. Gửi `GET /api/exbot/status` với HMAC hợp lệ. Hệ thống phải trả về HTTP 200 với `status = "safe_mode"`. Theo BR-EXBOT-007: `SAFE_MODE` không bao giờ là trạng thái kết thúc — trường `status` phải đọc trực tiếp từ DB, không được mã hoá cứng trong code.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_004
**Scenario Title:** A2 — bot ở trạng thái `hedge_stopped_cooldown`, response phản ánh đúng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A2
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `hedge_stopped_cooldown` trên Aurora PG. Gửi `GET /api/exbot/status` với HMAC hợp lệ. Hệ thống phải trả về HTTP 200 với `status = "hedge_stopped_cooldown"`. Kiểm tra giá trị `status` được đọc trực tiếp từ cột trạng thái trong bảng `bots` / `bot_runtime_state`, không phải logic phân nhánh cứng.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_005
**Scenario Title:** A3a — bot đang trong quá trình đóng (`lp_closing`), response trả về đúng trạng thái và thông báo
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A3a
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `lp_closing`. Gửi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `status = "lp_closing"`. Thông báo trả về phải khớp E-EXBOT-021: "Bot close is in progress. Please wait." — không được trả về thông báo của trạng thái khác.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_006
**Scenario Title:** A3b — bot đã đóng hoàn toàn (`closed`), response trả về đúng trạng thái và thông báo
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A3b
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `closed`. Gửi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `status = "closed"`. Thông báo phải khớp E-EXBOT-022: "Bot safely closed. Funds have been returned to your wallet." Kiểm tra `closed` không bị nhầm với `lp_closing`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_007
**Scenario Title:** A4 — không tìm thấy bot nào cho tài khoản này, trả về lỗi E-EXBOT-023
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A4
**Test Type:** Functional
**Description:** Dùng ví hợp lệ đã xác thực HMAC nhưng chưa có bot nào được tạo cho ví này trong Aurora PG. Gửi `GET /api/exbot/status`. Hệ thống phải trả về lỗi với thông báo khớp E-EXBOT-023: "No active bot found for this account." Không được trả về HTTP 200 với body rỗng hay null.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_008
**Scenario Title:** A5 — Operator Facade không kết nối được đến ExBot Lambda, trả về lỗi phù hợp
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A5
**Test Type:** Integration
**Description:** Mô phỏng ExBot Lambda không phản hồi (timeout hoặc cold-start quá hạn). Kiểm tra rằng Operator Facade trả về thông báo lỗi rõ ràng cho client thay vì để client nhận HTTP 200 với body rỗng hoặc chờ vô thời hạn. Hệ thống không được để lộ chi tiết nội bộ AWS (ARN, stack trace) trong response lỗi.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_009
**Scenario Title:** A6 — bot đang trong trạng thái `lp_rebalancing`, response phản ánh đúng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A6
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `lp_rebalancing` trên Aurora PG. Gửi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `status = "lp_rebalancing"`. Trạng thái này là tạm thời trong vòng đời bot — kiểm tra rằng hệ thống không nhầm với `running` hay `safe_mode`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_010
**Scenario Title:** A7 — bot ở trạng thái `error`, response trả về E-EXBOT-029
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A7
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `error`. Gửi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `status = "error"` và thông báo khớp E-EXBOT-029: "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close." Không được trả về thông báo của trạng thái khác.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_011
**Scenario Title:** A8 — Pool Slot0 Cache không khả dụng, `range_state` trả về null
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A8
**Test Type:** Integration
**Description:** Thiết lập ElastiCache Redis (Pool Slot0 Cache) không phản hồi hoặc trả về lỗi khi truy vấn `currentTick`. Gửi `GET /api/exbot/status`. Hệ thống phải trả về HTTP 200 với `range_state = null`. Các trường khác phải vẫn có giá trị hợp lệ — cache không khả dụng không được gây lỗi toàn bộ response.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_012
**Scenario Title:** A9 — ví wallet không khớp với bot trong DB, trả về 403 E-EXBOT-030
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 Alternative Flow A9 (bổ sung 2026-07-13)
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status` với chữ ký HMAC hợp lệ từ ví A, nhưng trong Aurora PG bot đang liên kết với ví B (khác ví A). Hệ thống phải trả về HTTP 403 với thông báo khớp E-EXBOT-030: "Access denied: this bot does not belong to your account." Ví A không được đọc dữ liệu của bot thuộc ví B.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_013
**Scenario Title:** Auth — thiếu header HMAC, Lambda Authorizer từ chối yêu cầu
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6 Auth — HMAC Authorizer
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status` không có header xác thực HMAC (hoặc header rỗng). Lambda Authorizer phải từ chối yêu cầu trước khi ExBot Lambda xử lý. Kiểm tra hệ thống trả về HTTP 401 hoặc 403 — không được trả về HTTP 200 hay để yêu cầu thông qua ExBot Lambda.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_014
**Scenario Title:** Auth — chữ ký HMAC không hợp lệ (sai khoá hoặc payload đã bị thay đổi), Lambda Authorizer từ chối
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6 Auth — HMAC Authorizer
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status` với header HMAC được tạo từ khoá sai, hoặc payload đã bị chỉnh sửa sau khi ký. Lambda Authorizer phải phát hiện chữ ký không khớp và từ chối yêu cầu. Không được để yêu cầu thông qua ExBot Lambda với chữ ký giả mạo.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_015
**Scenario Title:** Auth — ví không nằm trong whitelist, Lambda Authorizer từ chối
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6 Auth — Whitelist
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status` từ ví hợp lệ về mặt HMAC nhưng địa chỉ ví không được đăng ký trong danh sách whitelist. Lambda Authorizer phải từ chối yêu cầu. Kiểm tra hệ thống trả về mã lỗi phù hợp — không được để ví không trong whitelist đọc dữ liệu bot.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_016
**Scenario Title:** Auth — Admin bypass, truy cập thành công bất kể ví không có bot
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6 Auth — Admin Role
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status` từ tài khoản Admin với HMAC hợp lệ. Kiểm tra rằng Admin có thể đọc dữ liệu trạng thái bot bất kể ví Admin không phải ví chủ sở hữu bot. Response phải trả về HTTP 200 với dữ liệu bot hợp lệ — Admin không bị chặn bởi kiểm tra wallet mismatch (A9).
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_017
**Scenario Title:** EP — `margin_status = "normal"`, response phản ánh đúng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: margin_status
**Test Type:** Functional
**Description:** Thiết lập điều kiện để hệ thống tính toán `margin_status = "normal"` (giá trị thấp hơn ngưỡng cảnh báo). Gửi `GET /api/exbot/status`. Hệ thống phải trả về `margin_status = "normal"` trong response. Kiểm tra giá trị này được đọc hoặc tính từ nguồn thực tế, không phải giá trị mặc định cứng.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_018
**Scenario Title:** EP — `margin_status = "warning"`, response phản ánh đúng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: margin_status
**Test Type:** Functional
**Description:** Thiết lập điều kiện để hệ thống tính toán `margin_status = "warning"` (tỷ lệ sử dụng margin đạt ngưỡng cảnh báo nhưng chưa đến ngưỡng nguy hiểm). Gửi `GET /api/exbot/status`. Hệ thống phải trả về `margin_status = "warning"`. Kiểm tra `warning` không bị nhầm với `normal` hay `critical`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_019
**Scenario Title:** EP — `margin_status = "critical"`, response phản ánh đúng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: margin_status
**Test Type:** Functional
**Description:** Thiết lập điều kiện để hệ thống tính toán `margin_status = "critical"` (tỷ lệ sử dụng margin vượt ngưỡng nguy hiểm). Gửi `GET /api/exbot/status`. Hệ thống phải trả về `margin_status = "critical"`. Kiểm tra `critical` không bị nhầm với `warning`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_020
**Scenario Title:** BVA rangeState — `currentTick = tickLower` (ranh giới dưới, inclusive), `range_state = "in"`
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: range_state; công thức `tickLower <= currentTick < tickUpper`
**Test Type:** Data/State
**Description:** Thiết lập Pool Slot0 Cache trả về `currentTick = tickLower` (đúng bằng giới hạn dưới của range LP). Gửi `GET /api/exbot/status`. Theo công thức `tickLower <= currentTick < tickUpper`, điều kiện `tickLower <= currentTick` là đúng → hệ thống phải trả về `range_state = "in"`. Đây là trường hợp biên inclusive phía dưới.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_021
**Scenario Title:** BVA rangeState — `currentTick = tickLower - 1` (ngay dưới ranh giới dưới), `range_state = "out"`
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: range_state; công thức `tickLower <= currentTick < tickUpper`
**Test Type:** Data/State
**Description:** Thiết lập `currentTick = tickLower - 1`. Theo công thức, `tickLower <= currentTick` sai → hệ thống phải trả về `range_state = "out"`. Kiểm tra hệ thống không nhầm biên dưới là "in".
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_022
**Scenario Title:** BVA rangeState — `currentTick = tickUpper - 1` (ngay dưới ranh giới trên, inclusive), `range_state = "in"`
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: range_state; công thức `tickLower <= currentTick < tickUpper`
**Test Type:** Data/State
**Description:** Thiết lập `currentTick = tickUpper - 1`. Theo công thức, `currentTick < tickUpper` là đúng và `tickLower <= currentTick` cũng đúng → hệ thống phải trả về `range_state = "in"`. Đây là giá trị tick cuối cùng vẫn còn trong range.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_023
**Scenario Title:** BVA rangeState — `currentTick = tickUpper` (đúng bằng ranh giới trên, exclusive), `range_state = "out"`
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: range_state; công thức `tickLower <= currentTick < tickUpper`
**Test Type:** Data/State
**Description:** Thiết lập `currentTick = tickUpper`. Theo công thức, `currentTick < tickUpper` sai → hệ thống phải trả về `range_state = "out"`. Đây là trường hợp biên exclusive phía trên — `tickUpper` KHÔNG nằm trong range.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_024
**Scenario Title:** drift_pct — tính toán chính xác với BigDecimal, không dùng float
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: drift_pct; NFR-EXBOT-008
**Test Type:** Data/State
**Description:** Thiết lập dữ liệu `lp_eth_amount > 0` và `target_ratio_bps` có giá trị xác định. Gửi `GET /api/exbot/status`. Kiểm tra `drift_pct` được tính theo công thức `(|actualShortEth − targetShortEth| / targetShortEth) × 100` với `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)` qua `normalizeTargetRatioBps()`. Kết quả phải chính xác đến mức chứng minh được dùng BigDecimal (không có sai số float). NFR-EXBOT-008: mọi phép tính tài chính phải dùng BigDecimal, cấm dùng float.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_025
**Scenario Title:** drift_pct — `lp_eth_amount = 0`, trả về `drift_pct = null` (không chia cho 0)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: drift_pct — null guard
**Test Type:** Data/State
**Description:** Thiết lập `lp_eth_amount = 0` trong Aurora PG. Gửi `GET /api/exbot/status`. Hệ thống phải trả về `drift_pct = null` vì `targetShortEth = 0` → chia cho 0 là không xác định. Kiểm tra hệ thống không trả về lỗi 500, không trả về infinity hay NaN, không crash Lambda.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_026
**Scenario Title:** drift_pct — `lp_eth_amount = null`, trả về `drift_pct = null`
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: drift_pct — null guard
**Test Type:** Data/State
**Description:** Thiết lập `lp_eth_amount = null` trong Aurora PG. Gửi `GET /api/exbot/status`. Hệ thống phải trả về `drift_pct = null`. Kiểm tra null guard xử lý đúng cả khi `lp_eth_amount` là null (không chỉ khi = 0).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_027
**Scenario Title:** BR-EXBOT-007 — `safe_mode` không phải trạng thái kết thúc, bot có thể tiếp tục sau safe_mode
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** BR-EXBOT-007
**Test Type:** Data/State
**Description:** Thiết lập bot ở trạng thái `safe_mode`, lấy status (phải trả về `"safe_mode"`). Sau đó chuyển bot sang trạng thái `running`. Gửi lại `GET /api/exbot/status`. Hệ thống phải trả về `status = "running"` — xác nhận rằng `safe_mode` không khoá vĩnh viễn trạng thái bot. BR-EXBOT-007 cấm coi `SAFE_MODE` là trạng thái terminal.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_028
**Scenario Title:** State transition — bot chuyển từ `running` sang `safe_mode`, response phản ánh ngay lập tức
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §3 + §5 A1; BR-EXBOT-007
**Test Type:** Data/State
**Description:** Lấy status khi bot đang `running` (phải trả về `"running"`). Sau đó kích hoạt chuyển trạng thái sang `safe_mode` trên Aurora PG. Gửi `GET /api/exbot/status` ngay sau. Hệ thống phải trả về `status = "safe_mode"` — xác nhận hệ thống đọc trạng thái từ DB theo thời gian thực, không cache trạng thái cũ.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_029
**Scenario Title:** State transition — bot chuyển từ `running` sang `error`, response phản ánh ngay lập tức
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §5 A7
**Test Type:** Data/State
**Description:** Lấy status khi bot đang `running`. Sau đó kích hoạt trạng thái `error` trên Aurora PG. Gửi `GET /api/exbot/status`. Hệ thống phải trả về `status = "error"` với thông báo E-EXBOT-029. Xác nhận chuyển trạng thái `running → error` được phản ánh ngay, không bị trễ hay cache cũ.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_030
**Scenario Title:** Tính nhất quán dữ liệu — `bot_id` trong response khớp với `bots.id` trong Aurora PG
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Field: bot_id; V-006
**Test Type:** Data/State
**Description:** Gửi `GET /api/exbot/status` và lấy giá trị `bot_id` trong response. Kiểm tra trực tiếp trên Aurora PG rằng `bot_id` khớp với `bots.id` (alias xác nhận từ V-006). Không được trả về `bot_id` là ID của bảng khác hoặc giá trị giả.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_031
**Scenario Title:** Tính nhất quán dữ liệu — `lp_eth_amount` và `lp_usdc_amount` khớp với bảng `positions`
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6.1.D Field Inventory — positions table
**Test Type:** Data/State
**Description:** Gửi `GET /api/exbot/status`. Lấy `lp_eth_amount` và `lp_usdc_amount` từ response. Kiểm tra hai giá trị này khớp với dữ liệu tương ứng trong bảng `positions` của Aurora PG cho bot đang truy vấn. Không được trả về giá trị từ vòng đời cũ hay dữ liệu của bot khác.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_032
**Scenario Title:** Tính nhất quán dữ liệu — `range_state` khớp với `currentTick` từ Pool Slot0 Cache
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §7 Integration — Pool Slot0 Cache
**Test Type:** Integration
**Description:** Ghi nhận `currentTick` đang có trong ElastiCache Redis tại thời điểm gửi yêu cầu. Gửi `GET /api/exbot/status`. Kiểm tra `range_state` trong response phải nhất quán với `currentTick` đó theo công thức `tickLower <= currentTick < tickUpper`. Nếu `currentTick` thay đổi giữa hai lần gọi liên tiếp, `range_state` phải phản ánh giá trị mới nhất.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_033
**Scenario Title:** Concurrent read — nhiều yêu cầu GET /api/exbot/status đồng thời, không trả về dữ liệu bị trộn lẫn
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §3 Main Flow; NFR-EXBOT-001
**Test Type:** Integration
**Description:** Gửi đồng thời nhiều yêu cầu `GET /api/exbot/status` từ cùng một ví (ít nhất 5 request song song). Kiểm tra tất cả response đều trả về HTTP 200 với dữ liệu nhất quán — không có response nào thiếu trường, dữ liệu không bị trộn lẫn giữa các request. Đây là read-only endpoint, không có mutation, nhưng cần xác nhận Lambda không có race condition trên pool kết nối Aurora PG.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_034
**Scenario Title:** Tính idempotent — gọi GET /api/exbot/status nhiều lần liên tiếp, dữ liệu bot không thay đổi
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §3 Main Flow
**Test Type:** Integration
**Description:** Gửi `GET /api/exbot/status` 3 lần liên tiếp trong điều kiện không có mutation nào xảy ra giữa các lần gọi. Kiểm tra tất cả response trả về dữ liệu giống nhau (cùng `bot_id`, `status`, `lp_eth_amount`, v.v.). Đây là endpoint đọc thuần túy — không được có tác dụng phụ hay thay đổi trạng thái Aurora PG.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_035
**Scenario Title:** HMAC — khoá HMAC bị xoay vòng (rotate), xác thực phải sử dụng khoá hiện hành
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6 Auth; NFR-EXBOT-003
**Test Type:** Integration
**Description:** Sau khi xoay vòng khoá HMAC (key rotation), gửi `GET /api/exbot/status` với chữ ký được tạo từ khoá mới. Kiểm tra Lambda Authorizer chấp nhận yêu cầu. Đồng thời gửi thêm yêu cầu với chữ ký từ khoá cũ — yêu cầu đó phải bị từ chối. NFR-EXBOT-003: khoá HMAC phải được bảo vệ và có cơ chế xoay vòng.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_036
**Scenario Title:** Acceptance — response đúng cấu trúc JSON contract với tổng 19 trường (8 Implemented + 11 Pending)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §4 Data Contract; AC-ms-01
**Test Type:** Acceptance
**Description:** Gửi `GET /api/exbot/status` trong điều kiện bot đang `running`. Kiểm tra JSON body chứa đúng 19 trường như đã định nghĩa trong Data Contract: 8 trường Implemented có giá trị thực và 11 trường Pending có giá trị `null`. Không được có thêm trường không khai báo, không được thiếu trường. Đây là kiểm tra chấp nhận toàn bộ API contract.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_037
**Scenario Title:** Acceptance — response HTTP 200 trả về trong thời gian phù hợp (NFR-EXBOT-001)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §9 NFR; NFR-EXBOT-001
**Test Type:** Acceptance
**Description:** Gửi `GET /api/exbot/status` trong điều kiện Aurora PG và ElastiCache Redis đang hoạt động bình thường. Đo thời gian từ khi gửi yêu cầu đến khi nhận response. Kết quả phải đáp ứng ngưỡng độ trễ quy định trong NFR-EXBOT-001. Kiểm tra thực hiện trong môi trường staging với tải trọng thực tế.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_038
**Scenario Title:** Error guessing — Aurora PG không phản hồi trong khi đọc bảng `bots`, Lambda trả về lỗi rõ ràng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §7 Integration — Aurora PostgreSQL
**Test Type:** Integration
**Description:** Mô phỏng Aurora Serverless v2 đang trong giai đoạn cold-start (scaling from zero) hoặc bị timeout khi ExBot Lambda truy vấn bảng `bots`. Gửi `GET /api/exbot/status`. Kiểm tra Lambda không trả về HTTP 200 với body rỗng hoặc dữ liệu một phần — phải trả về lỗi rõ ràng và không để lộ chi tiết kết nối DB trong response.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_039
**Scenario Title:** Error guessing — dữ liệu `bot_runtime_state` không đồng bộ với `bots`, response phản ánh trạng thái nào?
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §6.1.D Field Inventory; V-001
**Test Type:** Data/State
**Description:** Tạo tình huống dữ liệu không nhất quán: bảng `bots` có `status = "running"` nhưng `bot_runtime_state` có trường sức khoẻ chỉ ra trạng thái lỗi. Gửi `GET /api/exbot/status`. Kiểm tra hệ thống xử lý không nhất quán như thế nào — response phải rõ ràng, không im lặng bỏ qua. Lưu ý: kết quả bị chặn một phần bởi V-001 (tên trường `runtime_health_status` vs `health_status` chưa xác nhận).
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_040
**Scenario Title:** E2E — đọc trạng thái sau khi bot vừa hoàn thành một chu kỳ rebalance, dữ liệu phải cập nhật
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC-EXBOT-monitor-status §3 Main Flow; §7 Integration
**Test Type:** End-to-End
**Description:** Kích hoạt một chu kỳ rebalance hoàn chỉnh (lp_rebalancing → running). Ngay sau khi bot trở về trạng thái `running`, gửi `GET /api/exbot/status`. Kiểm tra `lp_eth_amount`, `lp_usdc_amount`, `drift_pct`, và `range_state` phản ánh dữ liệu sau rebalance (không phải dữ liệu cũ trước rebalance). Đây là kiểm tra end-to-end tính nhất quán giữa vòng đời bot và dữ liệu status.
**Test Focus:** Happy path

---

## ⚠️ Out-of-Scope Flags

| Khu vực scenario | Lý do | Hành động đề xuất |
|---|---|---|
| `safe_mode_tier` — phân nhánh theo cấp độ safe mode | **BLOCKED (V-003):** trường `safe_mode_tier` chưa có định nghĩa trong ERD (`srs/erd.md`). Không có thông tin về các giá trị enum, điều kiện chuyển trạng thái, hay ý nghĩa từng tier. | Đề nghị BA bổ sung vào ERD và `common-rules.md`. Sau khi có định nghĩa → chạy lại `qc-uc-read-exbot` rồi thiết kế lại scenario. |
| `dry_run` — chế độ mô phỏng không thực thi | **BLOCKED (V-004):** trường `dry_run` trong response chưa có cột tương ứng trong ERD. Không rõ nguồn dữ liệu, kiểu dữ liệu, hay ảnh hưởng đến hành vi bot. | Đề nghị BA khai báo cột ERD và giải thích ngữ nghĩa. Sau khi có định nghĩa → thiết kế lại scenario. |
| Tên trường `runtime_health_status` / `health_status` | **BLOCKED (V-001):** tên trường trong JSON response (`runtime_health_status`) xung đột với tên cột trong ERD (`health_status`). Không thể viết assertion chính xác cho trường này. | BA/Dev cần xác nhận tên chính thức. Scenario 039 ghi chú tình huống nhưng không thể viết assertion đầy đủ cho trường này cho đến khi có xác nhận. |
| Tên trường timestamp reconcile (`last_reconcile_at` vs `last_hl_reconcile_at`) | **BLOCKED (V-002):** tên trường trong JSON response xung đột với tên cột trong ERD. Scenario 001 và các scenario liên quan đến timestamp reconcile dùng placeholder mô tả thay vì tên trường cứng. | BA/Dev cần xác nhận tên trường chính thức trong response và ERD. |
| `paused` — trạng thái tạm dừng | **BLOCKED (V-008):** không có alternate flow cho trạng thái `paused` trong UC. Không rõ response trả về gì khi bot ở trạng thái `paused`. | Đề nghị BA bổ sung alternate flow A10 cho `paused`. Sau khi có mô tả → thiết kế scenario tương ứng. |
| Kiểm tra hiệu năng và tải trọng | **Out-of-scope:** kiểm tra throughput, stress test, latency dưới tải cao là phạm vi NFR/performance testing, không phải functional scenario. | Chuyển sang kế hoạch kiểm tra hiệu năng riêng biệt (performance test plan). |
| Bảo mật ngoài xác thực chức năng (penetration testing, injection) | **Out-of-scope:** phân tích lỗ hổng bảo mật, SQL injection, API fuzzing không thuộc phạm vi skill này. | Chuyển sang security testing specialist. |
