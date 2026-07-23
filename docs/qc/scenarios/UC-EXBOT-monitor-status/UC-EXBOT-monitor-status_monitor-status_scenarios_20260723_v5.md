# Test Scenarios — UC-EXBOT-monitor-status Monitor Status

> **Nguồn:** docs/qc/uc-read/UC-EXBOT-monitor-status/UC-EXBOT-monitor-status_monitor-status_audited_20260722_v6.md
> **Ngày tạo:** 2026-07-23
> **Tác giả:** qc-func-scenario-design-exbot
> **Phiên bản:** v5
> **Domain/Architecture:** AWS Lambda (ExBot Lambda) + Aurora PostgreSQL Serverless v2 (`state_db_shard`) + ElastiCache Redis (Pool Slot0 Cache) — Back-End only, không có UI; xác thực hai lớp: Operator Facade kiểm tra `X-Wallet-Address`/whitelist, sau đó HMAC Lambda Authorizer xác thực chữ ký giữa Operator Facade và ExBot Lambda qua API Gateway.

---

## Bảng mã viết tắt

| Code / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC-EXBOT | Use Case — module ExBot. Mỗi UC mô tả một nghiệp vụ cụ thể của hệ thống bot giao dịch tự động (LP trên Uniswap V3 + hedge trên Hyperliquid). | `usecases/uc-*.md` |
| BR-EXBOT | Business Rule — quy tắc nghiệp vụ bất biến ràng buộc hành vi của ExBot, không được vi phạm dù trong code hay tài liệu. | `srs/spec.md` §4 |
| FR-EXBOT | Functional Requirement — yêu cầu chức năng đánh số của ExBot, định nghĩa hành vi bot, API contract, và rule của state machine. | `srs/spec.md` |
| NFR-EXBOT | Non-Functional Requirement — yêu cầu phi chức năng (hiệu năng, bảo mật, độ chính xác tính toán) của ExBot. | `srs/spec.md` §3 |
| E-EXBOT | Mã lỗi cấp API do ExBot Lambda trả về qua Operator Facade — quy định HTTP status code và nội dung message cho từng trường hợp lỗi. Nguồn canonical là `srs/spec.md` §5. | `srs/spec.md` §5 |
| AC-ms | Acceptance Criteria candidate của UC-EXBOT-monitor-status — điều kiện chấp nhận suy ra từ UC/US, dùng làm cơ sở thiết kế scenario Acceptance. | Audit report v6 §8 |
| V-XXX | Issue ID trong Issue Register của audit report — định danh một gap/mâu thuẫn/câu hỏi mở đã được QC ghi nhận. | Audit report v6 §10.1 |
| isAdmin guard | Điều kiện chặn cứng trong code ExBot Lambda: nếu caller không có quyền Admin, request bị trả 403 ngay trước khi bất kỳ business logic nào của endpoint này chạy. Đây là thiếu sót đã biết của v1 (v1 gap) — đường xử lý Investor đang chờ v1.1. Đây là điểm thay đổi lớn nhất so với bản scenario v4. | UC §2 Preconditions, audit v6 V-009 |
| Aurora PostgreSQL | AWS Aurora PostgreSQL Serverless v2 — cơ sở dữ liệu quan hệ lưu `bots`, `positions`, `hedge_legs`, `bot_runtime_state`. | `srs/erd.md` |
| Pool Slot0 Cache | ElastiCache Redis cache dùng chung cho dữ liệu slot0 (`currentTick`) của pool Uniswap V3. | FR-EXBOT-093 |
| HMAC | Hash-based Message Authentication Code — xác thực chữ ký giữa Operator Facade và ExBot Lambda qua API Gateway Lambda Authorizer. | (industry term) |
| BigDecimal | Kiểu dữ liệu số thập phân có độ chính xác tùy ý, bắt buộc cho mọi phép tính tài chính trong ExBot (cấm dùng float/number — NFR-EXBOT-008). | NFR-EXBOT-008 |
| EP | Equivalence Partitioning — phân vùng tương đương, kỹ thuật thiết kế test chia miền đầu vào thành các lớp có hành vi tương tự. | (industry term) |
| BVA | Boundary Value Analysis — phân tích giá trị biên, tập trung vào giá trị tại ranh giới của điều kiện. | (industry term) |
| v1 gap | Ghi chú xuyên suốt UC/audit report cho các field hoặc luồng xử lý mà v1 chưa triển khai đầy đủ (luôn trả về `null`, hoặc bị chặn hoàn toàn bởi isAdmin guard); dự kiến hoàn thiện ở v1.1. | UC changelog 2026-07-20 |

---

## UC-EXBOT-monitor-status — Monitor Status

### Scenario ID: TS_UC-EXBOT-monitor-status_001
**Scenario Title:** Happy path Admin — 4 trường Implemented có giá trị thực (không phải v1-gap null) được trả về đúng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A step 1-9; AC-ms-01
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` với header `X-Wallet-Address` của một Admin hợp lệ và chữ ký HMAC hợp lệ; bot đang ở trạng thái `active`, có dữ liệu đầy đủ trên Aurora PostgreSQL và Pool Slot0 Cache. Hệ thống phải trả về HTTP 200 với 4 trường Implemented có giá trị thực: `bot_id`, `status`, `lifecycle_state`, `runtime_health_status`, và `dry_run` phản ánh đúng biến môi trường `EXBOT_DRY_RUN`. Đây là actor duy nhất thực thi được happy path trong v1 (isAdmin guard).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_002
**Scenario Title:** Happy path — 11 trường Pending phải xuất hiện trong response với giá trị null
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.D Field Inventory — Pending Fields; AC-ms-01
**Test Type:** Functional
**Description:** Trong cùng response HTTP 200 của Admin ở happy path, kiểm tra 11 trường Pending (`tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`, `safe_mode_reason`, `cooldown_end_at`) đều xuất hiện trong JSON body. Với dữ liệu fixture đầy đủ (bot `active`, Pool Slot0 Cache có giá trị), các trường đã triển khai tính toán (`tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`) phải có giá trị thực; chỉ hai trường v1 gap (`safe_mode_reason`, `cooldown_end_at`) mới bắt buộc `null`. Response thiếu trường và response có trường giá trị null là hai trường hợp khác nhau — không được thiếu bất kỳ trường nào.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_003
**Scenario Title:** v1-gap fields — 5 trường luôn trả về null bất kể trạng thái bot, phân biệt với null theo điều kiện runtime
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.D Field Inventory — ghi chú tổng hợp v1 gap; V-002, V-003, V-005, V-007 Answered
**Test Type:** Functional
**Description:** Với bot ở nhiều trạng thái khác nhau (`active`, `safe_mode`, `error`), gửi `GET /api/exbot/status/{botId}` bằng actor Admin. Kiểm tra 5 trường `last_reconcile_at`, `last_error_code`, `safe_mode_tier`, `safe_mode_reason`, `cooldown_end_at` luôn trả về `null` trong mọi trường hợp — đây là do cột DB tương ứng chưa tồn tại/mapping chưa cài đặt trong v1, khác với `current_tick`/`range_state` chỉ null khi Pool Slot0 Cache không khả dụng (A8). Assertion phải khẳng định "luôn null trong v1" thay vì "null có điều kiện".
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_004
**Scenario Title:** Permission — Investor gọi API với ví khớp chủ sở hữu bot vẫn bị 403 do isAdmin guard chặn trước khi tới bước kiểm tra ownership
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §2 Preconditions #8; §6.1.A step 2b; AC-ms-01b; V-009
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` với chữ ký HMAC hợp lệ từ một ví Investor mà `wallet_address` khớp đúng `bot.user_wallet_address`. Vì caller không có quyền Admin, ExBot Lambda phải trả về HTTP 403 ngay tại bước 2b (isAdmin guard) — không được trả về HTTP 200 như US-EXBOT-002 AC-EXBOT-002-1 mô tả. Đây là hành vi thực tế của v1 (khác với US, xem V-009), không phải bug — mục đích scenario là ghi lại đúng hành vi hiện tại, không phải hành vi mục tiêu của v1.1.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_005
**Scenario Title:** Permission — Investor gọi API với ví KHÔNG khớp chủ sở hữu bot cũng nhận cùng 403 isAdmin guard, không thể phân biệt với trường hợp ví khớp
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A step 2b, step 3; §4 A9; AC-ms-05; V-009
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` với chữ ký HMAC hợp lệ từ ví Investor A, trong khi bot thuộc về ví Investor B (mismatch). Vì isAdmin guard (bước 2b) chạy trước bước kiểm tra ownership (bước 3, A9), request phải bị chặn ở bước 2b với HTTP 403 — cùng kết quả với scenario 004 (ví khớp). Kết hợp với scenario 004, hai scenario này tạo thành bảng quyết định xác nhận thứ tự guard: {Investor, khớp} → 403 và {Investor, không khớp} → 403 giống nhau, chứng minh tầng wallet-match (E-EXBOT-030) không thể kiểm thử độc lập bằng actor Investor trong v1.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_006
**Scenario Title:** Permission — Admin truy vấn bot không thuộc ví của Admin vẫn trả về 200, bỏ qua kiểm tra ownership
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §2 Preconditions #3; AC-ms-09
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` với chữ ký HMAC hợp lệ từ ví Admin, trong khi `botId` thuộc về một ví Investor khác hoàn toàn. Hệ thống phải trả về HTTP 200 với dữ liệu bot đầy đủ — Admin vượt qua cả isAdmin guard (bước 2b) và bước kiểm tra ownership (bước 3 chỉ áp dụng cho Investor) mà không bị chặn ở bất kỳ tầng nào.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_007
**Scenario Title:** Permission — response body của lỗi 403 isAdmin guard chưa có message text hoặc E-EXBOT code định nghĩa
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.C; V-012
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` bằng actor Investor (bị chặn ở bước 2b). Kiểm tra response HTTP 403 — tại thời điểm viết scenario này, UC chưa định nghĩa nội dung message body cụ thể cho lỗi này (khác với các lỗi 403 khác trong UC đều có E-EXBOT code kèm theo, ví dụ E-EXBOT-030). Assertion chỉ nên kiểm tra HTTP status code = 403; không viết assertion cứng cho message text cho đến khi BA xác nhận (V-012 Open).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_008
**Scenario Title:** Routing — botId path param bị thiếu hoặc sai định dạng, hệ thống trả về lỗi rõ ràng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A step 1; FR-EXBOT-090
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/` (thiếu `{botId}`) hoặc `GET /api/exbot/status/not-a-uuid` (sai định dạng UUID) với actor Admin và HMAC hợp lệ. Kiểm tra hệ thống không trả về HTTP 200 hoặc lỗi 500 không rõ nguyên nhân — phải trả về lỗi định tuyến/validation rõ ràng ở tầng API Gateway hoặc Operator Facade trước khi tới ExBot Lambda.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_009
**Scenario Title:** A4 — không tìm thấy bản ghi bot cho botId, trả về 404 E-EXBOT-023
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A4; §6.1.C
**Test Type:** Functional
**Description:** Actor Admin gửi `GET /api/exbot/status/{botId}` với một `botId` hợp lệ về định dạng nhưng không có bản ghi tương ứng trong Aurora PostgreSQL. Hệ thống phải trả về HTTP 404 với thông báo khớp E-EXBOT-023: "No active bot found for this account." Không được trả về HTTP 200 với body rỗng hay null. Lưu ý: bot `closed` vẫn giữ bản ghi và trả về 200 (A3b), khác với trường hợp không có bản ghi này.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_010
**Scenario Title:** A1 — bot ở trạng thái safe_mode, response phản ánh đúng trạng thái (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A1; BR-EXBOT-007; AC-ms-02
**Test Type:** Functional
**Description:** Thiết lập bot ở trạng thái `bots.status='safe_mode'` trên Aurora PostgreSQL. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `status = "safe_mode"`. Trường `safe_mode_reason` phải là `null` (v1 gap — cột chưa tồn tại, V-005 Answered), không phải giá trị thật như bản scenario v4 giả định trước khi có câu trả lời BA.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_011
**Scenario Title:** A2 — bot ở trạng thái hedge_stopped_cooldown, cooldown_end_at luôn null trong v1 (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A2; AC-ms-03
**Test Type:** Functional
**Description:** Thiết lập `bots.lifecycle_state='hedge_stopped_cooldown'`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `lifecycle_state = "hedge_stopped_cooldown"`. Trường `cooldown_end_at` phải là `null` vì cột DB chưa tồn tại trong v1 (V-005 Answered) — không được trả về timestamp giả hoặc lỗi.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_012
**Scenario Title:** A3a — bot đang trong quá trình đóng (lp_closing), message khớp E-EXBOT-021 (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A3a
**Test Type:** Functional
**Description:** Thiết lập `bots.lifecycle_state='lp_closing'`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `lifecycle_state = "lp_closing"`. Thông báo trả về phải khớp E-EXBOT-021: "Bot close is in progress. Please wait." — không được trả về thông báo của trạng thái khác.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_013
**Scenario Title:** A3b — bot đã đóng hoàn toàn (closed), bản ghi vẫn còn trong Aurora PostgreSQL (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A3b; AC-ms-10
**Test Type:** Functional
**Description:** Thiết lập `bots.lifecycle_state='closed'`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 (không phải 404) với `lifecycle_state = "closed"`; thông báo phải khớp E-EXBOT-022: "Bot safely closed. Funds have been returned to your wallet." Kiểm tra `closed` không bị nhầm với `lp_closing` hay với trường hợp không có bản ghi (A4, scenario 009).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_014
**Scenario Title:** A5 — lỗi tầng infra AWS (API Gateway/Lambda cold-start hoặc throttle), trả về 503 không lộ chi tiết nội bộ
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A5
**Test Type:** Integration
**Description:** Mô phỏng lỗi tầng infra AWS khiến Operator Facade không kết nối được ExBot Lambda (timeout hoặc cold-start quá hạn). Gửi `GET /api/exbot/status/{botId}` với actor Admin. Kiểm tra hệ thống trả về HTTP 503 "Status service temporarily unavailable" (không có E-EXBOT code, đây là lỗi tầng infra) — không để lộ ARN, stack trace, hay chi tiết nội bộ AWS trong response, và không để client chờ vô thời hạn.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_015
**Scenario Title:** A6 — bot đang trong trạng thái lp_rebalancing, không bị nhầm với running hay safe_mode (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A6
**Test Type:** Functional
**Description:** Thiết lập `bots.lifecycle_state='lp_rebalancing'`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `lifecycle_state = "lp_rebalancing"`. Trạng thái này là tạm thời trong vòng đời bot — kiểm tra hệ thống không nhầm với `active` hay `safe_mode`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_016
**Scenario Title:** A7 — bot ở trạng thái error, response trả về E-EXBOT-029 (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A7
**Test Type:** Functional
**Description:** Thiết lập `bots.status='error'`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `status = "error"` và thông báo khớp E-EXBOT-029: "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close." Không được trả về thông báo của trạng thái khác.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_017
**Scenario Title:** A10 — bot ở trạng thái paused, lifecycle_state giữ giá trị trước pause, message khớp E-EXBOT-031 (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A10; AC-ms-08; V-008 Answered
**Test Type:** Functional
**Description:** Thiết lập `bots.status='paused'` với `lifecycle_state='active'` (giá trị được giữ nguyên từ trước khi pause, theo State Registry — pause là status overlay, không đổi lifecycle_state). Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `status = "paused"`, `lifecycle_state = "active"` (không đổi), và thông báo khớp E-EXBOT-031: "Bot Paused. Hedge and LP are maintained. You may still redeem." Đây là alternate flow mới thêm 2026-07-20/21, chưa từng có trong scenario v4. Scenario này chỉ kiểm thử được cho Admin trong v1 — variant Investor bị Blocked (xem Out-of-Scope Flags).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-monitor-status_018
**Scenario Title:** A8 — Pool Slot0 Cache không khả dụng, current_tick và range_state trả về null, các trường khác vẫn bình thường (actor Admin)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A8; FR-EXBOT-093; AC-ms-04
**Test Type:** Integration
**Description:** Thiết lập ElastiCache Redis (Pool Slot0 Cache) không phản hồi hoặc trả về lỗi khi ExBot Lambda truy vấn `currentTick`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về HTTP 200 với `current_tick: null` và `range_state: null`. Các trường khác (`bot_id`, `status`, `lifecycle_state`, `margin_status`, v.v.) phải vẫn có giá trị hợp lệ — cache không khả dụng không được gây lỗi toàn bộ response.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_019
**Scenario Title:** Auth — thiếu header X-Wallet-Address, Operator Facade trả về 401 trước khi tới ExBot Lambda
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §3.1 điều kiện #1; §6.1.C
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` không có header `X-Wallet-Address` (hoặc header rỗng). Operator Facade phải từ chối yêu cầu với HTTP 401 trước khi chuyển tiếp đến ExBot Lambda. Kiểm tra hệ thống không trả về HTTP 200 và không để yêu cầu thông qua tầng isAdmin guard.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_020
**Scenario Title:** Auth — ví caller bị Operator Facade block, trả về 403 trước khi tới ExBot Lambda
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §3.1 điều kiện #4
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` từ một ví đã bị Operator Facade đánh dấu block. Hệ thống phải trả về HTTP 403 ngay tại Operator Facade — không được để yêu cầu thông qua đến ExBot Lambda dù ví đó có phải Admin hay không.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_021
**Scenario Title:** Auth — access_mode=whitelist, ví không nằm trong whitelist bị từ chối
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §3.1 điều kiện #5
**Test Type:** Functional
**Description:** Với hệ thống đang ở `access_mode=whitelist`, gửi `GET /api/exbot/status/{botId}` từ một ví hợp lệ về mặt HMAC nhưng không có trong danh sách whitelist. Operator Facade phải từ chối yêu cầu với HTTP 403. Kiểm tra ví không trong whitelist không đọc được dữ liệu bot dù có quyền Admin.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_022
**Scenario Title:** Auth — chữ ký HMAC không hợp lệ (sai khoá hoặc payload bị thay đổi), Lambda Authorizer từ chối
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §3.1 điều kiện #6
**Test Type:** Functional
**Description:** Gửi `GET /api/exbot/status/{botId}` với header HMAC được tạo từ khoá sai, hoặc payload đã bị chỉnh sửa sau khi ký. HMAC Lambda Authorizer phải phát hiện chữ ký không khớp và trả về HTTP 401. Không được để yêu cầu thông qua ExBot Lambda với chữ ký giả mạo, dù ví đó thuộc actor Admin.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_023
**Scenario Title:** Decision Table — kết hợp {actor} × {wallet-match} xác nhận đúng thứ tự isAdmin guard chạy trước wallet-match check
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A step 2b, step 3; AC-ms-05; V-009
**Test Type:** Functional
**Description:** Chạy 4 tổ hợp trên cùng một bot fixture: (1) Admin + botId thuộc ví khác → 200 (bypass ownership); (2) Admin + botId thuộc chính ví Admin → 200; (3) Investor + wallet khớp bot → 403 isAdmin guard; (4) Investor + wallet không khớp bot → 403 isAdmin guard (không phải 403 E-EXBOT-030). Bảng quyết định phải xác nhận: guard isAdmin quyết định HTTP status trước, wallet-match chỉ có ý nghĩa khi actor là Admin (không chặn) hoặc không bao giờ được ExBot Lambda đánh giá tới khi actor là Investor trong v1.
**Test Focus:** Permission/Role

---

### Scenario ID: TS_UC-EXBOT-monitor-status_024
**Scenario Title:** EP — margin_status = "ok", marginUsage dưới ngưỡng cảnh báo
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: margin_status; FR-EXBOT-060
**Test Type:** Data/State
**Description:** Thiết lập `hedge_legs.margin_status` sao cho `marginUsage < 0.55`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `margin_status = "ok"`. Kiểm tra giá trị được đọc trực tiếp từ `hedge_legs.margin_status` (cập nhật tại hedge-sync preflight/deep-audit theo FR-EXBOT-060), không phải giá trị tính lại tại thời điểm đọc status.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_025
**Scenario Title:** BVA margin_status — marginUsage = 0.55 (đúng ngưỡng dưới), phải là "warning" không phải "ok"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: margin_status — ngưỡng 0.55–0.75
**Test Type:** Data/State
**Description:** Thiết lập `marginUsage = 0.55` (đúng bằng ngưỡng dưới của dải "warning"). Actor Admin gửi `GET /api/exbot/status/{botId}`. Theo định nghĩa `warning: 0.55–0.75` (inclusive dưới), hệ thống phải trả về `margin_status = "warning"`, không phải `"ok"`. Đây là giá trị biên dưới của dải warning.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_026
**Scenario Title:** BVA margin_status — marginUsage ngay dưới 0.55, vẫn là "ok"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: margin_status — ngưỡng 0.55–0.75
**Test Type:** Data/State
**Description:** Thiết lập `marginUsage` ngay dưới 0.55 (giá trị Limit-1 theo độ chính xác BigDecimal đang dùng, ví dụ 0.549999). Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `margin_status = "ok"`. Kiểm tra hệ thống không nhầm biên dưới của "warning" thành "ok" bị mở rộng.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_027
**Scenario Title:** BVA margin_status — marginUsage = 0.75 (đúng ngưỡng dưới của critical), phải là "critical" không phải "warning"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: margin_status — ngưỡng ≥ 0.75
**Test Type:** Data/State
**Description:** Thiết lập `marginUsage = 0.75` (đúng bằng ngưỡng của dải "critical", định nghĩa là `≥ 0.75`). Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `margin_status = "critical"`, không phải `"warning"`. Đây là giá trị biên inclusive của "critical".
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_028
**Scenario Title:** BVA margin_status — marginUsage ngay dưới 0.75, vẫn là "warning"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: margin_status — ngưỡng ≥ 0.75
**Test Type:** Data/State
**Description:** Thiết lập `marginUsage` ngay dưới 0.75 (ví dụ 0.749999). Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `margin_status = "warning"`. Kiểm tra hệ thống không nhầm biên dưới của "critical" thành "warning" bị mở rộng lên quá ngưỡng.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_029
**Scenario Title:** BVA range_state — currentTick = tickLower (ranh giới dưới, inclusive), range_state = "in"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: range_state; công thức tickLower <= currentTick < tickUpper
**Test Type:** Data/State
**Description:** Thiết lập Pool Slot0 Cache trả về `currentTick = tickLower` (đúng bằng giới hạn dưới của range LP). Actor Admin gửi `GET /api/exbot/status/{botId}`. Theo công thức `tickLower <= currentTick < tickUpper`, điều kiện `tickLower <= currentTick` đúng → hệ thống phải trả về `range_state = "in"`. Đây là trường hợp biên inclusive phía dưới.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_030
**Scenario Title:** BVA range_state — currentTick = tickLower - 1 (ngay dưới ranh giới dưới), range_state = "out"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: range_state; công thức tickLower <= currentTick < tickUpper
**Test Type:** Data/State
**Description:** Thiết lập `currentTick = tickLower - 1`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Theo công thức, `tickLower <= currentTick` sai → hệ thống phải trả về `range_state = "out"`. Kiểm tra hệ thống không nhầm biên dưới là "in".
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_031
**Scenario Title:** BVA range_state — currentTick = tickUpper - 1 (ngay dưới ranh giới trên), range_state = "in"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: range_state; công thức tickLower <= currentTick < tickUpper
**Test Type:** Data/State
**Description:** Thiết lập `currentTick = tickUpper - 1`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Theo công thức, `currentTick < tickUpper` đúng và `tickLower <= currentTick` cũng đúng → hệ thống phải trả về `range_state = "in"`. Đây là giá trị tick cuối cùng vẫn còn trong range.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_032
**Scenario Title:** BVA range_state — currentTick = tickUpper (đúng bằng ranh giới trên, exclusive), range_state = "out"
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: range_state; công thức tickLower <= currentTick < tickUpper
**Test Type:** Data/State
**Description:** Thiết lập `currentTick = tickUpper`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Theo công thức, `currentTick < tickUpper` sai → hệ thống phải trả về `range_state = "out"`. Đây là trường hợp biên exclusive phía trên — `tickUpper` KHÔNG nằm trong range.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_033
**Scenario Title:** drift_pct — tính toán chính xác bằng BigDecimal, không dùng float (NFR-EXBOT-008)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: drift_pct; NFR-EXBOT-008; FR-EXBOT-021
**Test Type:** Data/State
**Description:** Thiết lập `lp_eth_amount > 0` và `target_ratio_bps` có giá trị xác định (đi qua `normalizeTargetRatioBps()`). Actor Admin gửi `GET /api/exbot/status/{botId}`. Kiểm tra `drift_pct` được tính theo công thức `(|actualShortEth − targetShortEth| / targetShortEth) × 100` với `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)`. Kết quả và `actual_short_eth`/`target_short_eth` phải được serialize dưới dạng string (BigDecimal), không phải số float JS — không có sai số làm tròn.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_034
**Scenario Title:** BVA drift_pct — lp_eth_amount = 0, trả về drift_pct = null (division-by-zero guard)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: drift_pct — null guard; AC-ms-07
**Test Type:** Data/State
**Description:** Thiết lập `lp_eth_amount = 0` trong Aurora PostgreSQL. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `drift_pct = null` vì `targetShortEth = 0` → chia cho 0 không xác định. Kiểm tra hệ thống không trả về HTTP 500, không trả về `Infinity` hay `NaN`, không crash Lambda.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_035
**Scenario Title:** BVA drift_pct — lp_eth_amount = null, trả về drift_pct = null
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.B Field: drift_pct — null guard
**Test Type:** Data/State
**Description:** Thiết lập `lp_eth_amount = null` trong Aurora PostgreSQL. Actor Admin gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `drift_pct = null`. Kiểm tra null guard xử lý đúng cả khi `lp_eth_amount` là null (không chỉ khi bằng 0).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-monitor-status_036
**Scenario Title:** State transition — BR-EXBOT-007, safe_mode không phải trạng thái kết thúc, bot có thể tiếp tục sau safe_mode
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** BR-EXBOT-007 (`srs/spec.md` §4)
**Test Type:** Data/State
**Description:** Thiết lập bot ở trạng thái `safe_mode` bằng actor Admin, lấy status (phải trả về `status = "safe_mode"`). Sau đó chuyển bot sang trạng thái `active` trên Aurora PostgreSQL. Gửi lại `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `status = "active"` — xác nhận `safe_mode` không khoá vĩnh viễn trạng thái bot. BR-EXBOT-007 cấm coi `SAFE_MODE` là trạng thái terminal.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_037
**Scenario Title:** State transition — bot chuyển từ active sang safe_mode, response phản ánh ngay lập tức không cache trạng thái cũ
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A step 6 (bảng luồng thay thế A1); BR-EXBOT-007
**Test Type:** Data/State
**Description:** Lấy status khi bot đang `active` (phải trả về `status = "active"`). Sau đó chuyển trạng thái sang `safe_mode` trên Aurora PostgreSQL. Gửi `GET /api/exbot/status/{botId}` ngay sau. Hệ thống phải trả về `status = "safe_mode"` — xác nhận hệ thống đọc trạng thái từ DB theo thời gian thực, không cache trạng thái cũ.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_038
**Scenario Title:** State transition — bot chuyển từ active sang error, response phản ánh ngay lập tức
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A7
**Test Type:** Data/State
**Description:** Lấy status khi bot đang `active`. Sau đó chuyển trạng thái `error` trên Aurora PostgreSQL. Gửi `GET /api/exbot/status/{botId}`. Hệ thống phải trả về `status = "error"` với thông báo E-EXBOT-029. Xác nhận chuyển trạng thái `active → error` được phản ánh ngay, không bị trễ hay cache cũ.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_039
**Scenario Title:** State transition — bot chuyển từ active sang paused rồi trở lại active, status/lifecycle_state phản ánh đúng tại mỗi bước
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A10; State Registry `srs/states.md`
**Test Type:** Data/State
**Description:** Lấy status khi bot đang `active` (`status="active"`, `lifecycle_state="active"`). Chuyển sang `paused` (`status="paused"`, `lifecycle_state` giữ nguyên `"active"`). Gửi status — kiểm tra đúng theo mô tả A10. Sau đó resume lại `active`. Gửi status lần cuối — kiểm tra `status` trở lại `"active"`. Đây là scenario mới cho state machine `paused`, chưa từng có trong bản v4 (do A10 mới được UC bổ sung ngày 2026-07-20).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-monitor-status_040
**Scenario Title:** Tính nhất quán dữ liệu — bot_id trong response khớp với bots.id trong Aurora PostgreSQL
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.D Field: bot_id; V-006 Answered
**Test Type:** Data/State
**Description:** Actor Admin gửi `GET /api/exbot/status/{botId}` và lấy giá trị `bot_id` trong response. Kiểm tra trực tiếp trên Aurora PostgreSQL rằng `bot_id` khớp với `bots.id` (xác nhận là alias theo V-006 Answered). Không được trả về `bot_id` là ID của bảng khác hoặc giá trị giả.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_041
**Scenario Title:** Tính nhất quán dữ liệu — actual_short_eth và target_short_eth khớp với bot_runtime_state/positions
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.D Field Inventory — `bot_runtime_state.last_known_hl_short_size`; FR-EXBOT-021
**Test Type:** Data/State
**Description:** Actor Admin gửi `GET /api/exbot/status/{botId}`. Lấy `actual_short_eth` từ response và so sánh với `bot_runtime_state.last_known_hl_short_size` trong Aurora PostgreSQL cho đúng bot đang truy vấn. Lấy `target_short_eth` và xác nhận bằng công thức tính lại từ `lp_eth_amount` và `target_ratio_bps`. Không được trả về giá trị từ vòng đời cũ hay dữ liệu của bot khác.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-monitor-status_042
**Scenario Title:** Tính nhất quán dữ liệu — range_state khớp với currentTick từ Pool Slot0 Cache tại đúng thời điểm gọi
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §7 Integration — Pool Slot0 Cache
**Test Type:** Integration
**Description:** Ghi nhận `currentTick` đang có trong ElastiCache Redis tại thời điểm gửi yêu cầu. Actor Admin gửi `GET /api/exbot/status/{botId}`. Kiểm tra `range_state` trong response phải nhất quán với `currentTick` đó theo công thức `tickLower <= currentTick < tickUpper`. Nếu `currentTick` thay đổi giữa hai lần gọi liên tiếp, `range_state` phải phản ánh giá trị mới nhất.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-monitor-status_043
**Scenario Title:** Concurrent read — nhiều yêu cầu GET status đồng thời cho cùng botId, không trả về dữ liệu bị trộn lẫn
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A Main Flow; NFR-EXBOT-001
**Test Type:** Integration
**Description:** Actor Admin gửi đồng thời ít nhất 5 request `GET /api/exbot/status/{botId}` song song cho cùng một bot. Kiểm tra tất cả response đều trả về HTTP 200 với dữ liệu nhất quán — không có response nào thiếu trường, dữ liệu không bị trộn lẫn giữa các request. Đây là read-only endpoint, không có mutation, nhưng cần xác nhận Lambda không có race condition trên pool kết nối Aurora PostgreSQL.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_044
**Scenario Title:** Tính idempotent — gọi GET status nhiều lần liên tiếp không có mutation, dữ liệu bot không thay đổi
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A Main Flow
**Test Type:** Integration
**Description:** Actor Admin gửi `GET /api/exbot/status/{botId}` 3 lần liên tiếp trong điều kiện không có mutation nào xảy ra giữa các lần gọi. Kiểm tra tất cả response trả về dữ liệu giống nhau (cùng `bot_id`, `status`, `lifecycle_state`, `range_state`, v.v.). Đây là endpoint đọc thuần túy — không được có tác dụng phụ hay thay đổi trạng thái Aurora PostgreSQL.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_045
**Scenario Title:** Concurrent read-during-write — gọi GET status trong khi một light-check/hedge-sync khác đang ghi vào bot_runtime_state cho cùng bot
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §7 Integration Analysis — rủi ro test Aurora PostgreSQL
**Test Type:** Integration
**Description:** Kích hoạt một tiến trình light-check hoặc hedge-sync đang ghi cập nhật vào `bot_runtime_state` cho một bot, đồng thời actor Admin gửi `GET /api/exbot/status/{botId}` cho đúng bot đó. Kiểm tra response trả về HTTP 200 với dữ liệu là một snapshot nhất quán (không đọc được trạng thái nửa-ghi/half-written giữa hai lần commit) — không trả về lỗi, không trả về dữ liệu hỗn hợp giữa giá trị cũ và mới của các cột khác nhau trong cùng một row.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-monitor-status_046
**Scenario Title:** Error guessing — Aurora PostgreSQL cold-start hoặc timeout khi đọc bảng bots, Lambda trả về lỗi rõ ràng
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §7 Integration — Aurora PostgreSQL
**Test Type:** Integration
**Description:** Mô phỏng Aurora Serverless v2 đang trong giai đoạn cold-start (scaling from zero) hoặc bị timeout khi ExBot Lambda truy vấn bảng `bots`. Actor Admin gửi `GET /api/exbot/status/{botId}`. Kiểm tra Lambda không trả về HTTP 200 với body rỗng hoặc dữ liệu một phần — phải trả về lỗi rõ ràng và không để lộ chi tiết kết nối DB trong response.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_047
**Scenario Title:** Error guessing — một trong 4 bảng Aurora PostgreSQL thiếu row tương ứng gây lỗi join, hệ thống không trả về dữ liệu một phần âm thầm
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §7 Integration Analysis — rủi ro test multi-table join
**Test Type:** Integration
**Description:** Thiết lập fixture sao cho bảng `bots` có bản ghi hợp lệ nhưng bảng `positions` (hoặc `hedge_legs`) không có row tương ứng cho bot đó (ví dụ bot vừa tạo, chưa có LP position). Actor Admin gửi `GET /api/exbot/status/{botId}`. Kiểm tra hệ thống xử lý rõ ràng: hoặc trả về các trường liên quan là `null` một cách có chủ đích, hoặc trả về lỗi rõ ràng — không được trả về HTTP 200 với dữ liệu join sai (ví dụ `tick_lower`/`tick_upper` của bot khác do lỗi join).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_048
**Scenario Title:** Error guessing — Pool Slot0 Cache trả về snapshot stale (có giá trị nhưng đã cũ) khác với trường hợp unavailable hoàn toàn
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §4 A8; UC §2 vai trò Pool Slot0 Cache
**Test Type:** Integration
**Description:** Thiết lập Pool Slot0 Cache có giá trị `currentTick` nhưng dữ liệu đó đã cũ (stale — `blockNumber` cách xa block hiện tại). Actor Admin gửi `GET /api/exbot/status/{botId}`. Kiểm tra hệ thống có phân biệt hành vi giữa "cache stale nhưng có giá trị" (theo UC §2, coi như tương đương unavailable, trả `current_tick: null`) và "cache có giá trị mới" — không âm thầm trả về `range_state` được tính từ dữ liệu stale mà không có cảnh báo nào.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-monitor-status_049
**Scenario Title:** Acceptance — response đúng cấu trúc JSON contract với tổng 19 trường (8 Implemented + 11 Pending)
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.D Field Inventory; AC-ms-01
**Test Type:** Acceptance
**Description:** Actor Admin gửi `GET /api/exbot/status/{botId}` trong điều kiện bot đang `active`. Kiểm tra JSON body chứa đúng 19 trường như đã định nghĩa trong Field Inventory: 8 trường Implemented (`bot_id`, `status`, `lifecycle_state`, `safe_mode_tier`, `runtime_health_status`, `last_reconcile_at`, `last_error_code`, `dry_run`) và 11 trường Pending (`tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`, `safe_mode_reason`, `cooldown_end_at`). Không được có thêm trường không khai báo, không được thiếu trường. Đây là kiểm tra chấp nhận toàn bộ API contract.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_050
**Scenario Title:** Acceptance — AC-ms-01 đầy đủ: happy path Admin với currentTick trong range, drift_pct dương, toàn bộ 5 field v1-gap = null
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** AC-ms-01
**Test Type:** Acceptance
**Description:** Thiết lập bot ở trạng thái `active`; `lp_eth_amount > 0`; Pool Slot0 Cache có `currentTick` nằm trong `[tickLower, tickUpper)`; caller có quyền Admin. Gửi `GET /api/exbot/status/{botId}`. Kiểm tra đồng thời toàn bộ điều kiện Then của AC-ms-01: HTTP 200; `lifecycle_state='active'`; `range_state='in'`; `drift_pct` là số thập phân dương (BigDecimal, không phải float); và 5 field v1-gap (`last_reconcile_at`, `last_error_code`, `safe_mode_tier`, `safe_mode_reason`, `cooldown_end_at`) đều bằng `null`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_051
**Scenario Title:** E2E — đọc trạng thái ngay sau khi bot hoàn thành một chu kỳ rebalance, dữ liệu phải cập nhật không dùng cache cũ
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §6.1.A Main Flow; §7 Integration
**Test Type:** End-to-End
**Description:** Kích hoạt một chu kỳ rebalance hoàn chỉnh (`lp_rebalancing` → `active`). Ngay sau khi bot trở về trạng thái `active`, actor Admin gửi `GET /api/exbot/status/{botId}`. Kiểm tra `tick_lower`, `tick_upper`, `actual_short_eth`, `target_short_eth`, `drift_pct`, và `range_state` phản ánh dữ liệu sau rebalance (không phải dữ liệu cũ trước rebalance). Đây là kiểm tra end-to-end tính nhất quán giữa vòng đời bot và dữ liệu status.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-monitor-status_052
**Scenario Title:** E2E — HMAC key bị xoay vòng (rotate), Facade → Lambda phải dùng khoá hiện hành, khoá cũ bị từ chối
**UC Reference:** UC-EXBOT-monitor-status — Monitor Status
**Req-ID:** UC §2 Auth; NFR-EXBOT-003
**Test Type:** Integration
**Description:** Sau khi xoay vòng khoá HMAC (key rotation) cho HMAC Lambda Authorizer, gửi `GET /api/exbot/status/{botId}` với chữ ký được tạo từ khoá mới bằng actor Admin. Kiểm tra Lambda Authorizer chấp nhận yêu cầu (HTTP 200). Đồng thời gửi thêm yêu cầu với chữ ký từ khoá cũ — yêu cầu đó phải bị từ chối (HTTP 401). NFR-EXBOT-003: khoá HMAC phải được bảo vệ và có cơ chế xoay vòng.
**Test Focus:** Integration

---

## ⚠️ Out-of-Scope Flags

| Khu vực scenario | Lý do | Hành động đề xuất |
|---|---|---|
| Toàn bộ scenario theo actor Investor (happy path, A1–A10 dưới góc nhìn Investor, kể cả A9 wallet-mismatch với dữ liệu thật) | **BLOCKED (V-009, D2):** isAdmin guard trong v1 chặn 403 mọi request Investor trước khi business logic chạy — không thể thiết kế test case theo actor Investor có kỳ vọng HTTP 200 hoặc bất kỳ dữ liệu status thật nào. Các scenario 004, 005, 023 trong file này chỉ verify được hành vi 403 của guard, không verify được nghiệp vụ Investor thật. | Chờ v1.1 gỡ isAdmin guard (D2) và BA cập nhật `us-002.md` (V-009, D5). Sau khi gỡ guard, thiết kế lại toàn bộ scenario theo actor Investor tương ứng với các scenario Admin hiện có (001–002, 010–018, 029–042). |
| `safe_mode_tier` — phân nhánh theo giá trị `warning` | **BLOCKED một phần (V-003 Answered nhưng còn giới hạn):** cột `bot_runtime_state.safe_mode_tier` đã có trong ERD nhưng cột schema DB thực tế chưa tồn tại trong v1; điều kiện kích hoạt `warning` chưa được định nghĩa dù `restricted`/`frozen` đã có qua `enterSafeMode()`. | Sau khi cột DB thực tế được triển khai và điều kiện `warning` được định nghĩa (D1, chờ v1.1) → thiết kế scenario theo từng tier (`warning`/`restricted`/`frozen`). |
| `last_reconcile_at`, `last_error_code`, `safe_mode_reason`, `cooldown_end_at` — giá trị thật (không phải null) | **BLOCKED (D1):** cả 4 field đều là v1 gap, mapping DB → response hoặc cột DB chưa tồn tại; chỉ có thể test assertion `=== null` (đã có ở scenario 003), không thể test giá trị thật cho đến v1.1. | Chờ v1.1 hoàn tất D1 → thiết kế scenario giá trị thật cho từng field. |
| Kiểm tra hiệu năng và tải trọng (NFR-EXBOT-001) | **Out-of-scope:** kiểm tra throughput, stress test, latency dưới tải cao là phạm vi NFR/performance testing, không phải functional scenario. UC §9 đã ghi "cần đề xuất cho QC Lead". | Chuyển sang kế hoạch kiểm tra hiệu năng riêng biệt (performance test plan), đề xuất cho QC Lead. |
| Bảo mật ngoài xác thực chức năng (kiểm tra HMAC key không lộ trong CloudWatch logs — NFR-EXBOT-003) | **Out-of-scope:** phân tích lỗ hổng bảo mật, kiểm tra log leakage, penetration testing không thuộc phạm vi functional scenario design; scenario 052 trong file này chỉ verify hành vi chức năng của key rotation (accept/reject), không verify việc key có bị log hay không. | Chuyển sang security testing specialist / security test plan riêng. |
| Response body message text cho lỗi 403 isAdmin guard | **BLOCKED (V-012):** UC chưa định nghĩa nội dung message cụ thể cho lỗi này; scenario 007 chỉ verify được HTTP status code. | Chờ BA xác nhận nội dung response body (V-012) → bổ sung assertion message text. |

