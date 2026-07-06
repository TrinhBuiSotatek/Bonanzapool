# Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-monitor-status

**Tiêu đề tài liệu:** UC Readiness Audit Report — UC-EXBOT-monitor-status  
**Ngày tạo:** 2026-07-06  
**Tác giả / Agent:** QC UC Read Agent  
**Phiên bản:** v4

---

## Reference Code Glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement for the ExBot module — numbered requirements defining bot behavior, API contracts, and state machine rules. Canonical source for all implementation decisions. | `srs/spec.md` |
| BR-EXBOT-* | Business Rule for ExBot — absolute invariants that must never be violated in code or documentation. | `srs/spec.md` §4 |
| E-EXBOT-* | API-level error code returned by ExBot Lambda through Operator Facade — defines HTTP status code and message content for each error case. | `02_backbone/message-list.md` |
| US-EXBOT-* | User Story for ExBot — acceptance criteria in Given/When/Then format from Investor or Operator perspective. | `userstories/us-*.md` |
| UC-EXBOT-* | Use Case for ExBot — describes system behavior at scenario level, including actors, flows, and FR trace. | `usecases/uc-*.md` |
| OQ-EXBOT-* | Open Question for ExBot — unresolved technical or business question affecting implementation or test design. | `srs/spec.md` §9 |
| Aurora PostgreSQL | AWS Aurora PostgreSQL Serverless v2 — relational database replacing the prior Cloudflare D1 (SQLite) per arc-migration 2026-07-04. Two logical databases: `control_db` (global) and `state_db_shard_xx` (per-shard bot state). | `srs/erd.md`, SRS §1 |
| ExBot Lambda | AWS Lambda function running ExBot business logic — replaces prior "ExBot Worker" (Cloudflare Worker) per arc-migration 2026-07-04. | `userstories/us-002.md`, `usecases/uc-monitor-status.md` changelog 2026-07-04 |
| Pool Slot0 Cache | ElastiCache Redis shared cache for Uniswap V3 pool slot0 data (`sqrtPriceX96`, `currentTick`, `blockNumber`) — replaces prior "MarketDataDO" (Cloudflare Durable Object) per arc-migration 2026-07-04. | `srs/spec.md` FR-EXBOT-093 |
| HMAC Lambda Authorizer | AWS API Gateway Lambda Authorizer using HMAC signature validation — replaces prior Cloudflare service binding + shared-secret header per arc-migration 2026-07-04. | `usecases/uc-monitor-status.md` changelog 2026-07-04 |
| SIWE | Sign-In With Ethereum — wallet-based authentication mechanism relevant to Investor auth flow through POOL UI. | (industry term) |

---

## Feature Brief

UC-EXBOT-monitor-status mô tả một luồng truy vấn chỉ đọc cho phép USDC Investor đã xác thực theo dõi trạng thái vận hành hiện tại của ExBot đang chạy. Toàn bộ luồng xử lý ở phía backend: POOL UI gọi `GET /api/exbot/status` đến Operator Facade, Facade chuyển tiếp yêu cầu đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer. ExBot Lambda đọc từ bốn bảng Aurora PostgreSQL (`bots`, `positions`, `hedge_legs`, `bot_runtime_state`), truy vấn `currentTick` từ Pool Slot0 Cache (ElastiCache Redis), tính toán hai giá trị dẫn xuất (rangeState và drift%), sau đó trả về JSON tổng hợp. Không có thao tác ghi nào xảy ra trong luồng này.

Actor thứ cấp Admin cũng có thể gọi endpoint này và bỏ qua kiểm tra quyền sở hữu ví. Cơ chế xác thực: header `X-Wallet-Address` cho Investor hoặc Admin, và HMAC Lambda Authorizer cho đoạn Facade→Lambda.

**Điểm quan trọng cho v4:** UC được cập nhật ngày 2026-07-04 theo arc-migration, thay thế toàn bộ các thành phần Cloudflare (D1 → Aurora PostgreSQL, ExBot Worker → ExBot Lambda, MarketDataDO → Pool Slot0 Cache, CF service binding + shared-secret → API Gateway + HMAC Lambda Authorizer). Kiểm tra chéo cho thấy UC đã đồng bộ với SRS (erd.md cập nhật 2026-07-04, us-002.md cập nhật 2026-07-04). Tất cả tên thành phần khớp nhau. Vấn đề I-003 (nguồn `targetShortEth`) vẫn còn mở.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-monitor-status | View Active ExBot Status | — (no version field in UC file) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-07-04 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-monitor-status.md` | 2026-07-04 | UC (primary input) | Draft; cập nhật 2026-07-04 arc-migration (D1→Aurora PostgreSQL, ExBot Worker→ExBot Lambda, MarketDataDO→Pool Slot0 Cache, CF service binding→API Gateway + HMAC) |
| `userstories/us-002.md` | 2026-07-04 | US linked to this UC | Draft; cập nhật 2026-07-04 arc-migration: "replace ExBot Worker with ExBot Lambda" |
| `srs/spec.md` | 2026-07-04 | SRS baseline — nguồn sự thật cho tất cả FR | Cập nhật 2026-07-04: sync queue count to 11 (add key-provision) |
| `srs/states.md` | 2026-07-03 | Lifecycle state machine | Cập nhật 2026-07-03: pause chỉ được phép từ `lifecycle_state='active'` |
| `srs/erd.md` | 2026-07-04 | Aurora PostgreSQL data model | Cập nhật 2026-07-04 arc-migration: rename D1 → Aurora PostgreSQL; annotate hl_agent_keys legacy fields as retired |
| `srs/flows.md` | 2026-06-29 | Sequence flow diagrams | Phiên bản mới nhất hiện có |
| `frd.md` | 2026-06-29 | Functional requirements document | Phiên bản mới nhất hiện có |
| `usecases/index.md` | 2026-06-29 | UC catalog and FR trace index | Đã kiểm tra |
| `02_backbone/message-list.md` | 2026-06-26 | E-EXBOT-* error code registry | Đã kiểm tra E-EXBOT-021/022/023 |
| `UC-EXBOT-monitor-status_monitor-status_audited_20260703_v3.md` | 2026-07-03 | Audit report v3 (CONDITIONALLY READY 78/100) | Baseline so sánh cho v4 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Endpoint này tồn tại để USDC Investor có thể kiểm tra bất cứ lúc nào xem ExBot của mình có đang hoạt động đúng không, mà không cần truy cập dashboard nội bộ. Đây cũng là lớp tín hiệu để POOL UI bật hoặc tắt các nút thay đổi trạng thái (pause, close, emergency close) dựa trên `lifecycle_state` và tình trạng margin hiện tại của bot.

Admin actor có thể truy vấn endpoint này để kiểm tra bất kỳ bot nào mà không bị giới hạn quyền sở hữu, phục vụ giám sát vận hành và xử lý sự cố.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| `GET /api/exbot/status` — primary status query | Operator Facade chuyển tiếp yêu cầu đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer; Lambda đọc Aurora PostgreSQL và Pool Slot0 Cache, tính toán giá trị dẫn xuất, trả về JSON | UC §3, FR-EXBOT-090 |
| Multi-table Aurora PostgreSQL read | Đọc `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.last_light_check_at`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status` | UC §3 bước 3 |
| Pool Slot0 Cache query | Lấy `currentTick` từ ElastiCache Redis cache dùng chung (không gọi RPC trực tiếp từ Lambda) | UC §3 bước 4, FR-EXBOT-093 |
| rangeState computation | So sánh `currentTick` với `tickLower`/`tickUpper` theo khoảng nửa mở (`tickLower <= currentTick < tickUpper`); null nếu currentTick không có | UC §3 bước 5 |
| drift% computation | `(\|actualShortEth - targetShortEth\| / targetShortEth) × 100` dùng BigDecimal | UC §3 bước 6, FR-EXBOT-021 |
| JSON response schema | Hai phần: Implemented fields (có ngay) + Pending implementation fields (null cho đến khi triển khai xong) | UC §3 bước 7 |
| Alternate flows A1–A8 | Bao phủ safe_mode, hedge_stopped_cooldown, lp_closing, closed, lp_rebalancing, error, Pool Slot0 Cache unavailable, no bot record | UC §4 |
| Auth: Investor path | Header `X-Wallet-Address`; `wallet_address` phải khớp `bot.user_wallet_address`; không khớp → 403 | UC §2 |
| Auth: Admin path | Header `X-Wallet-Address`; bỏ qua kiểm tra quyền sở hữu | UC §2 |
| Auth: Facade→Lambda | HMAC Lambda Authorizer qua API Gateway; chữ ký không hợp lệ/thiếu → 401 | UC §2 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| POOL UI rendering logic | Hành vi UI component thuộc POOL module scope; UC chỉ bao phủ API response payload | Test scenario cho UC này tập trung vào API response; UI rendering tests nằm ngoài phạm vi |
| Cập nhật margin status | `margin_status` được tính toán trong hedge-sync preflight và deep-audit (FR-EXBOT-060), không phải trong status read | Test phải dùng dữ liệu Aurora PostgreSQL đã cài sẵn với giá trị `margin_status` đã biết |
| Dữ liệu lịch sử / audit trail | UC chỉ trả về snapshot hiện tại; không có truy vấn lịch sử | N/A |
| Pause/resume mutation | Pause là UC riêng; endpoint status là read-only | N/A |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Khởi tạo truy vấn status từ POOL UI; xem trạng thái bot hiện tại, LP range, kích thước hedge, tình trạng margin, nhãn lifecycle | Chỉ có thể truy vấn bot của mình (`wallet_address` phải khớp `bot.user_wallet_address`); read-only — không có mutation | UC §1 Actors |
| Admin | Secondary | Có thể truy vấn status của bất kỳ bot nào mà không cần kiểm tra quyền sở hữu | Bỏ qua kiểm tra `wallet_address == bot.user_wallet_address`; read-only | UC §1 Actors, UC §2 Preconditions |
| Operator Facade | System | Nhận `GET /api/exbot/status` từ POOL UI; kiểm tra header `X-Wallet-Address` (401/403 nếu thất bại); chuyển tiếp đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer | Không sở hữu business logic của ExBot; chỉ làm passthrough | UC §1 Actors, FR-EXBOT-090 |
| ExBot Lambda | System | Đọc Aurora PostgreSQL + Pool Slot0 Cache; tính rangeState và drift%; tổng hợp và trả về JSON status response | Không thể truy cập trực tiếp từ internet; chỉ tiếp nhận qua API Gateway | UC §1 Actors, FR-EXBOT-090 |
| Aurora PostgreSQL (state_db_shard) | System | Nguồn dữ liệu cho bots, positions, hedge_legs, bot_runtime_state | Read-only trong UC này | UC §3, ERD |
| Pool Slot0 Cache (ElastiCache Redis) | System | Cache dùng chung cho Uniswap V3 pool slot0 `currentTick` | Read-only; nếu không có hoặc stale → `current_tick: null` trả về mà không bị chặn | UC §3 bước 4, FR-EXBOT-093 |

**Nhận xét về mức độ sẵn sàng:** Actors được định nghĩa rõ ràng và đủ cho test design theo từng role. Kiểm tra quyền sở hữu của Investor (ví không khớp → 403) được liệt kê trong preconditions nhưng không có alternate flow tương ứng — tạo ra khoảng trống nhỏ trong test design (xem N-002 trong §10.1). Admin bypass được ghi lại rõ ràng.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Caller gửi header `X-Wallet-Address`; thiếu header → 401 từ Operator Facade | Có | UC §2 |
| 2 | Investor: `wallet_address` trong header phải khớp `bot.user_wallet_address` trong Aurora PostgreSQL; không khớp → 403 | Có (đường Investor) | UC §2 |
| 3 | Admin: header `X-Wallet-Address` phải có mặt; bỏ qua kiểm tra quyền sở hữu | Có (đường Admin) | UC §2 |
| 4 | Operator Facade kiểm tra caller không bị block; bị block → 403 | Có | UC §2 |
| 5 | Khi `access_mode=whitelist`: địa chỉ ví caller phải nằm trong whitelist; nếu không → 403 | Có điều kiện | UC §2 |
| 6 | Operator Facade chuyển tiếp đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer; chữ ký không hợp lệ/thiếu → 401 | Có | UC §2 |
| 7 | Route API Gateway từ Operator Facade đến ExBot Lambda được cấu hình và khả dụng | Có | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Truy vấn status (happy path) | Investor nhận response 200 JSON với `status`, `lifecycle_state`, LP range, kích thước hedge, drift%, `margin_status`, và `last_light_check_at` hiện tại. Không có dữ liệu Aurora PostgreSQL nào bị thay đổi. | UC §3 bước 7–10 |
| Truy vấn status với Pool Slot0 Cache không khả dụng | Response 200 JSON với `current_tick: null` và `range_state: null`; tất cả các trường khác được điền bình thường. Không có lỗi, không retry. | UC §4 A8, FR-EXBOT-093 |
| Truy vấn status cho bot đã đóng (closed) | Response 200 JSON với `lifecycle_state='closed'`; bản ghi bot được giữ trong Aurora PostgreSQL. Không phải 404. | UC §4 A3b |
| Truy vấn status cho bot không tồn tại | Response 404 với E-EXBOT-023; UI hiển thị "No active bot found for this account." | UC §4 A4 |
| Operator Facade không khả dụng | 503 Service Unavailable từ lớp infra AWS; không có E-EXBOT code ở application level; UI hiển thị banner lỗi | UC §4 A5 |

---

## 4 và 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 GET /api/exbot/status — ExBot Status Query

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | POOL UI | Gọi `GET /api/exbot/status` với header `X-Wallet-Address` | Operator Facade nhận yêu cầu | — | Thiếu header → 401 | UC §3.1, §2 |
| 2 | Operator Facade | Kiểm tra `X-Wallet-Address`; chuyển tiếp đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer | ExBot Lambda nhận yêu cầu đã được chuyển tiếp | — | Ví bị block → 403; không có trong whitelist → 403; HMAC không hợp lệ → 401; Facade không khả dụng → 503 (infra, A5) | UC §2, §3.2, FR-EXBOT-090 |
| 3 | ExBot Lambda | Đọc từ Aurora PostgreSQL: `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.last_light_check_at`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status` | Bản ghi Aurora PostgreSQL được trả về | — | Không có bản ghi bot → 404 E-EXBOT-023 (A4); `lifecycle_state='lp_closing'` → 200 với E-EXBOT-021 (A3a); `lifecycle_state='closed'` → 200 với E-EXBOT-022 (A3b) | UC §3.3, §4 |
| 4 | ExBot Lambda | Truy vấn `currentTick` từ Pool Slot0 Cache (ElastiCache Redis) | Giá trị `currentTick` được trả về | Pool Slot0 Cache không khả dụng hoặc stale → `current_tick: null`, `range_state: null` (A8); tất cả các trường khác trả về bình thường | — | UC §3.4, FR-EXBOT-093 |
| 5 | ExBot Lambda | Tính `rangeState`: `tickLower <= currentTick < tickUpper` → `"in"`; ngược lại → `"out"` | `range_state` được điền | `current_tick = null` → bỏ qua tính toán, `range_state: null` | — | UC §3.5 |
| 6 | ExBot Lambda | Tính drift%: `(\|last_known_hl_short_size - targetShortEth\| / targetShortEth) × 100` dùng BigDecimal | `drift_pct` được điền | `bots.status='safe_mode'` → A1; `lifecycle_state='hedge_stopped_cooldown'` → A2; `lifecycle_state='lp_rebalancing'` → A6; `status='error'` → A7 | — | UC §3.6, FR-EXBOT-021 |
| 7 | ExBot Lambda | Tổng hợp JSON status response (Implemented fields + Pending implementation fields) | Toàn bộ JSON payload được tổng hợp; Pending fields trả về `null` nếu chưa có | — | — | UC §3.7 |
| 8 | Operator Facade | Trả về JSON response cho POOL UI | 200 OK với status payload | — | — | UC §3.8 |
| 9 | POOL UI | Hiển thị status panel | Investor thấy nhãn trạng thái, LP range, current tick, kích thước hedge, drift%, margin status, thời gian light-check gần nhất | — | — | UC §3.9–10 |

**Alternate flows:**

| Flow | Điều kiện kích hoạt | Phản hồi hệ thống | Hành vi UI |
|---|---|---|---|
| A1 — safe_mode | `bots.status='safe_mode'` | 200 với `safe_mode_reason` trong response | Banner "Safe Mode — No new actions"; tất cả nút mutation bị tắt ngoại trừ "Close Bot (emergency)" |
| A2 — hedge_stopped_cooldown | `bots.lifecycle_state='hedge_stopped_cooldown'` | 200 với timestamp `cooldown_end_at` trong response | "Stop Fired — Cooldown (Xh remaining)"; nút mutation bị tắt |
| A3a — lp_closing | `bots.lifecycle_state='lp_closing'` | 200 với `lifecycle_state='lp_closing'`; message E-EXBOT-021 | "Bot close is in progress. Please wait."; tất cả nút mutation bị tắt |
| A3b — closed | `bots.lifecycle_state='closed'` | 200 với `lifecycle_state='closed'`; message E-EXBOT-022; bản ghi được giữ trong Aurora PostgreSQL | "Bot safely closed. Funds have been returned to your wallet."; tất cả nút mutation bị tắt |
| A4 — no bot record | Không có bản ghi bot trong Aurora PostgreSQL cho botId | 404 E-EXBOT-023 | "No active bot found for this account." Lưu ý: bot `closed` trả về 200, không phải 404 |
| A5 — Facade unavailable | Lỗi ở tầng infra AWS | 503 Service Unavailable; không có E-EXBOT code | Banner "Status service temporarily unavailable" |
| A6 — lp_rebalancing | `bots.lifecycle_state='lp_rebalancing'` | 200 với `lifecycle_state='lp_rebalancing'` | "Rebalancing in progress"; tất cả nút mutation bị tắt |
| A7 — error | `bots.status='error'` | 200 với `status='error'` | "Bot error — admin intervention required"; chỉ "Close Bot (emergency)" được bật |
| A8 — Pool Slot0 Cache null | Pool Slot0 Cache không khả dụng hoặc snapshot stale | 200; `current_tick: null`, `range_state: null`; tất cả các trường khác bình thường | "—" hiển thị cho chỉ số range state |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.lifecycle_state` | Phải là một trong 18 trạng thái canonical được định nghĩa trong SRS | Có | Nhãn lifecycle đúng được trả về trong response | Không áp dụng (vấn đề toàn vẹn dữ liệu Aurora PostgreSQL — ngoài phạm vi UC này) | FR-EXBOT-003, `srs/states.md` |
| rangeState computation | Khoảng nửa mở: `tickLower <= currentTick < tickUpper` | Có | `range_state: "in"` hoặc `"out"` | Nếu `current_tick = null` → `range_state: null` | UC §3 bước 5 |
| drift% computation | Phép tính BigDecimal; không dùng float/number cho giá trị tài chính | Có | Giá trị `drift_pct` chính xác | Phép tính float là vi phạm kiến trúc theo NFR-EXBOT-008 | FR-EXBOT-021, NFR-EXBOT-008 |
| `margin_status` | Một trong: `ok`, `warning`, `critical` (ngưỡng: ok < 0.55, warning 0.55–0.75, critical ≥ 0.75) | Có | Nhãn margin đúng được trả về | Giá trị có thể stale (chỉ cập nhật tại hedge-sync preflight + deep-audit theo FR-EXBOT-060, không trong status read) | FR-EXBOT-060, `srs/states.md` |
| BR-EXBOT-007 — SAFE_MODE không phải trạng thái terminal | Bot SAFE_MODE phải vẫn phản hồi truy vấn status; phải cuối cùng đạt auto-recovery hoặc bot_safe_close | Có | Response 200 với dữ liệu safe_mode | N/A | BR-EXBOT-007 |
| Kiểm tra quyền sở hữu ví của Investor | `X-Wallet-Address` phải bằng `bot.user_wallet_address` cho Investor | Có (đường Investor) | Response 200 | 403 Forbidden | UC §2 |
| Xác thực HMAC Lambda Authorizer | Chữ ký HMAC phải hợp lệ với khóa bí mật API Gateway | Có | Yêu cầu được chuyển tiếp | 401 từ ExBot Lambda | UC §2 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Thiếu header `X-Wallet-Address` | Lỗi API | 401 Unauthorized | Kiểm tra xác thực Operator Facade | UC §2 |
| Ví caller bị Operator Facade block | Lỗi API | 403 Forbidden | Kiểm tra xác thực Operator Facade | UC §2 |
| Ví Investor không khớp `bot.user_wallet_address` | Lỗi API | 403 Forbidden | Kiểm tra quyền sở hữu trong Preconditions | UC §2 |
| HMAC không hợp lệ hoặc thiếu (Facade→Lambda) | Lỗi API | 401 từ ExBot Lambda | Kiểm tra HMAC Lambda Authorizer | UC §2 |
| Không tìm thấy bản ghi bot cho botId | Lỗi API | 404 Not Found — "No active bot found for this account." | E-EXBOT-023 | UC §4 A4 |
| Bot ở trạng thái `lp_closing` | Response API (200) | "Bot close is in progress. Please wait." | E-EXBOT-021 | UC §4 A3a |
| Bot ở trạng thái `closed` | Response API (200) | "Bot safely closed. Funds have been returned to your wallet." | E-EXBOT-022 | UC §4 A3b |
| Lỗi cơ sở hạ tầng Operator Facade | Response ở tầng infra | 503 Service Unavailable — "Status service temporarily unavailable" | Không có E-EXBOT code (tầng infra, không phải application) | UC §4 A5 |
| Pool Slot0 Cache không khả dụng hoặc stale | Null field-level trong response 200 | `current_tick: null`, `range_state: null`; các trường khác được điền bình thường | Không có mã lỗi | UC §4 A8, FR-EXBOT-093 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Status read đọc `hedge_legs.margin_status` | FR-EXBOT-060, hedge-sync preflight, deep-audit | Giá trị `margin_status` được ghi bởi hedge-sync preflight và deep-audit, không phải bởi UC này. Giá trị trả về ở đây có thể stale nếu không có hedge-sync hoặc deep-audit nào chạy gần đây. Test phải xác minh giá trị khớp với giá trị cuối cùng được ghi bởi hedge-sync hoặc deep-audit. | Xác nhận `margin_status` trong response khớp với giá trị Aurora PostgreSQL tại thời điểm truy vấn | FR-EXBOT-060, srs/states.md |
| Status read đọc `bot_runtime_state.last_light_check_at` | UC-EXBOT-light-check | Timestamp phản ánh lần light-check cuối cùng đã hoàn thành. Kịch bản test cho light-check phải xác minh timestamp này được cập nhật đúng; UC status đọc kết quả. | Xác nhận `last_light_check_at` trong response khớp với giá trị Aurora PostgreSQL tại thời điểm truy vấn | UC §3 bước 3, srs/erd.md |
| `lifecycle_state` trong response điều khiển trạng thái nút POOL UI | POOL module (UI buttons) | Nhãn lifecycle không đúng trong response → trạng thái bật/tắt nút không đúng trong UI → hành động người dùng tiềm năng trên bot không nên nhận mutation. Quan trọng về an toàn: nhãn sai trên `lp_closing` có thể cho phép yêu cầu đóng thừa. | Xác minh tất cả 8 lifecycle states được bao phủ trong alternate flows tạo ra nhãn đúng | UC §4 A1–A8, srs/states.md |
| `range_state` trong response | Chỉ số POOL UI | Giá trị `range_state` null hoặc stale ảnh hưởng đến hiển thị chỉ số range. Độ trễ Pool Slot0 Cache truyền trực tiếp đến khả năng quan sát LP range health của nhà đầu tư. | Xác minh đường dẫn null fallback (A8) không tạo ra lỗi hoặc thiếu các trường khác | UC §4 A8, FR-EXBOT-093 |
| ExBot Lambda đọc từ Aurora PostgreSQL (nhiều bảng) | Toàn vẹn dữ liệu cross-table | Status response tổng hợp dữ liệu từ 4 bảng Aurora PostgreSQL. Nếu `bot_id` không khớp giữa các bảng (ví dụ: vấn đề migration hoặc lỗi ghi), response có thể trả về dữ liệu không nhất quán. | Test phải xác minh 4 bảng có dữ liệu nhất quán cho cùng `bot_id`; mọi trường được đọc đều nằm trong ERD | srs/erd.md, FR-EXBOT-090 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — active bot | Bot với `lifecycle_state='active'`, `status='active'` trong Aurora PostgreSQL; Pool Slot0 Cache có `currentTick` hợp lệ; ví Investor khớp `bot.user_wallet_address` | Investor gọi `GET /api/exbot/status` | Response 200 với tất cả Implemented fields được điền; `range_state` được tính là "in" hoặc "out"; `drift_pct` được tính dùng BigDecimal; `margin_status` là một trong ok/warning/critical | UC §3, FR-EXBOT-003 |
| AC-02 | Trạng thái safe_mode | Bot với `bots.status='safe_mode'` | Investor gọi `GET /api/exbot/status` | Response 200 có `safe_mode_reason`; `status='safe_mode'` trong response | UC §4 A1, BR-EXBOT-007 |
| AC-03 | Trạng thái hedge_stopped_cooldown | Bot với `lifecycle_state='hedge_stopped_cooldown'` | Investor gọi `GET /api/exbot/status` | Response 200 có timestamp `cooldown_end_at` | UC §4 A2 |
| AC-04 | Trạng thái lp_closing | Bot với `lifecycle_state='lp_closing'` | Investor gọi `GET /api/exbot/status` | Response 200 với `lifecycle_state='lp_closing'`; response body có message E-EXBOT-021 "Bot close is in progress. Please wait." | UC §4 A3a |
| AC-05 | Trạng thái closed — bản ghi được giữ | Bot với `lifecycle_state='closed'`; bản ghi vẫn tồn tại trong Aurora PostgreSQL | Investor gọi `GET /api/exbot/status` | Response 200 với `lifecycle_state='closed'`; KHÔNG phải 404; response body có message E-EXBOT-022 "Bot safely closed. Funds have been returned to your wallet." | UC §4 A3b |
| AC-06 | Không tìm thấy bản ghi bot | Không có bản ghi nào trong Aurora PostgreSQL cho botId đã cho | Investor gọi `GET /api/exbot/status` | Response 404; E-EXBOT-023 được kích hoạt; message "No active bot found for this account." | UC §4 A4 |
| AC-07 | Pool Slot0 Cache không khả dụng | Bot active; Pool Slot0 Cache trả về null hoặc snapshot stale | Investor gọi `GET /api/exbot/status` | Response 200 với `current_tick: null`, `range_state: null`; tất cả các trường khác được điền; không có 503, không retry | UC §4 A8, FR-EXBOT-093 |
| AC-08 | Trạng thái lp_rebalancing | Bot với `lifecycle_state='lp_rebalancing'` | Investor gọi `GET /api/exbot/status` | Response 200 với `lifecycle_state='lp_rebalancing'` | UC §4 A6 |
| AC-09 | Trạng thái error | Bot với `bots.status='error'` | Investor gọi `GET /api/exbot/status` | Response 200 với `status='error'` | UC §4 A7 |
| AC-10 | Ví Investor không khớp | `wallet_address` của Investor trong header KHÔNG khớp `bot.user_wallet_address` trong Aurora PostgreSQL | Investor gọi `GET /api/exbot/status` | 403 Forbidden | UC §2 Preconditions — không có alternate flow tường minh; nguồn từ precondition |
| AC-11 | Admin bỏ qua kiểm tra quyền sở hữu | Admin actor gửi `X-Wallet-Address` cho bot của người dùng khác | Admin gọi `GET /api/exbot/status` | Response 200 với bot status; kiểm tra quyền sở hữu bị bỏ qua | UC §2 |
| AC-12 | Thiếu X-Wallet-Address | Không có header `X-Wallet-Address` trong yêu cầu | Bất kỳ caller nào gọi `GET /api/exbot/status` | 401 từ Operator Facade | UC §2 |
| AC-13 | HMAC không hợp lệ (Facade→Lambda) | Chữ ký HMAC không hợp lệ trong yêu cầu chuyển tiếp | Facade chuyển tiếp với HMAC sai | 401 từ ExBot Lambda | UC §2 |
| AC-14 | drift% dùng độ chính xác BigDecimal | Bot active; biết giá trị actualShortEth và targetShortEth | Investor gọi `GET /api/exbot/status` | `drift_pct` được tính với BigDecimal; kết quả khớp với giá trị mong đợi không có lỗi làm tròn số dấu phẩy động | FR-EXBOT-021, NFR-EXBOT-008 — Suy luận cần xác nhận (nguồn targetShortEth chưa được xác nhận theo I-003) |
| AC-15 | Pending fields trả về null | Bot active; các trường "Pending implementation" chưa được triển khai | Investor gọi `GET /api/exbot/status` | Tất cả Pending fields trả về `null` trong response; không có lỗi | UC §3 bước 7 null-handling |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Không có SLA độ trễ tường minh nào được định nghĩa cho `GET /api/exbot/status` trong UC này. NFR-EXBOT-002 (hedge-sync 30s) không áp dụng trực tiếp. | Test có thể kiểm tra thời gian phản hồi trong điều kiện bình thường như smoke check; không có SLA cứng cần kiểm chứng | NFR-EXBOT-002 (hedge-sync, không áp dụng trực tiếp) |
| Security | Chữ ký HMAC phải được xác thực bởi Lambda Authorizer; ExBot Lambda không thể truy cập trực tiếp từ internet (gọi trực tiếp trả về 403). | Test phải xác minh 401 khi thiếu/sai HMAC; xác minh ExBot Lambda không thể gọi trực tiếp không qua Facade | UC §2, FR-EXBOT-090, NFR-EXBOT-006 |
| Reliability / Resilience | Pool Slot0 Cache không khả dụng không được chặn response status — hệ thống phải giảm cấp nhẹ nhàng về `current_tick: null` (A8). Operator Facade không khả dụng tạo ra 503 ở tầng infra (A5). | Test đường dẫn fallback A8 là test case bắt buộc; xác minh hành vi 503 khi Facade không khả dụng | UC §4 A8, A5, FR-EXBOT-093 |
| Audit / Logging | FR-EXBOT-090: Operator Facade logs hiển thị các lần gọi API Gateway cho mỗi yêu cầu được proxy | Môi trường test nên xác nhận logging đang hoạt động; không phải assertion chức năng nhưng liên quan đến xác nhận khả năng quan sát | FR-EXBOT-090 |
| Privacy / Compliance | N/A — không có PII mutation trong UC này. Response chứa trạng thái bot và dữ liệu tài chính chỉ hiển thị cho caller đã xác thực. | N/A | |
| Compatibility / Integration | Dual-chain Base + Optimism: `positions.tickLower`, `positions.tickUpper`, và `wethIndex` là các giá trị đặc thù theo chain được lưu trong Aurora PostgreSQL khi mở LP. Endpoint status đọc các giá trị này; chain ID được ẩn trong bản ghi bot. | Test nên bao phủ bot trên cả Base và Optimism để xác minh giá trị LP range đặc thù theo chain được đọc đúng | FR-EXBOT-004, srs/erd.md |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-003 | High | MISSING_INFO | UC §3 bước 6; FR-EXBOT-021; `srs/erd.md` bảng `bot_runtime_state` | Nguồn của `targetShortEth` dùng trong công thức drift% chưa được xác nhận. FR-EXBOT-021 định nghĩa `targetShortEth = lpEthAmount × hedgeRatio` là giá trị được tính toán tại thời điểm hedge-sync. Tuy nhiên, ERD có cột `target_short_size` kiểu TEXT trong `bot_runtime_state`, có thể là giá trị đã được cache từ hedge-sync. UC bước 6 có công thức nhưng không chỉ rõ ExBot Lambda đọc `target_short_size` từ Aurora PostgreSQL hay tính lại từ `lpEthAmount × hedgeRatio` (cần thêm `lp_eth_amount` và `hedge_legs.target_ratio` vào danh sách đọc). Đây là hai cách cài đặt khác nhau và tạo ra kết quả mong đợi khác nhau trong test. Vui lòng xác nhận: (a) nguồn dữ liệu chính xác; (b) bổ sung vào danh sách đọc Aurora PostgreSQL ở UC bước 3; (c) định nghĩa hành vi khi mẫu số bằng 0. | Nếu không xác nhận, không thể chỉ rõ assertion test cho drift% (AC-14). Tester không biết cột nào trong Aurora PostgreSQL cần cài dữ liệu và giá trị mong đợi nào cần kiểm chứng. | Tech Lead / Dev | Open |
| N-001 | Minor | INTERNAL_INCONSISTENCY | UC §3 bước 7 JSON schema | UC schema response chia fields thành "Implemented fields" và "Pending implementation (BA-defined)". Nhãn "Pending" có thể khiến tester bỏ qua assertion cho các trường đó hoàn toàn, thay vì kiểm chứng rằng chúng trả về `null`. Ghi chú null-handling giải quyết một phần ("tất cả pending fields trả về null khi chưa có") nhưng chưa đủ rõ. Khuyến nghị: UC nên làm rõ rằng các trường "Pending" phải luôn trả về `null` (không phải vắng mặt khỏi response JSON) cho đến khi triển khai xong, và thêm ghi chú rằng test PHẢI kiểm chứng null cho các trường này. | Tester có thể bỏ sót assertion cho các trường "Pending", tạo ra khoảng trống coverage. Trường trả về `null` đúng so với trường vắng mặt hoàn toàn trong JSON là hai hành vi khác nhau. | BA / QC Lead | Open |
| N-002 | Minor | MISSING_INFO | UC §2 Preconditions; UC §4 Alternate flows | UC liệt kê ví Investor không khớp → 403 trong phần Preconditions nhưng không định nghĩa nó như một alternate flow có tên (ví dụ A9). Do đó trường hợp 403 này không phải là đường dẫn có thể test tường minh trong cấu trúc flow. Tester đọc chỉ phần alternate flows sẽ không tìm thấy đường dẫn này. | Tính đầy đủ test design: không có alternate flow có tên, trường hợp 403 này có thể bị bỏ sót trong thiết kế scenario. Đây là đường dẫn liên quan đến bảo mật (đọc trái phép bot của người dùng khác) và phải được test tường minh. | BA | Open |
| N-003 | Note | MISSING_INFO | UC §6 FR Trace; `srs/spec.md` | FR Trace trong UC chỉ liệt kê FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-090. Thiếu trong trace: FR-EXBOT-060 (ngưỡng margin status — nguồn cho tính toán ok/warning/critical dùng trong response), FR-EXBOT-093 (Pool Slot0 Cache — nguồn của currentTick dùng cho rangeState), FR-EXBOT-050 (điều kiện vào SAFE_MODE — liên quan đến hành vi A1). FR trace không đầy đủ làm giảm khả năng truy xuất giữa test cases và requirements. | Test cases trace đến FR để báo cáo coverage; FRs bị thiếu sẽ xuất hiện là không được UC này cover dù thực tế được test ngầm. | BA | Open (không phải blocker) |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| I-003: Xác nhận nguồn `targetShortEth` | Data / Implementation | Chặn thiết kế test case đầy đủ cho assertion drift% (AC-14) | Tech Lead / Dev | Open |
| OQ-EXBOT-06: Ngưỡng margin (0.55/0.75) pending Phase 0 backtest | Business Rule / Data | Nếu ngưỡng thay đổi, test data cho test ok/warning/critical margin_status phải được hiệu chỉnh lại | zen (backtest owner) | Open (tracked in spec.md §9) |
| OQ-EXBOT-09: Khoảng thời gian làm mới Pool Slot0 Cache pending Phase 0 NV-12 | Integration / Configuration | Ảnh hưởng đến cài đặt test cho A8 (cách kích hoạt snapshot stale trong môi trường test) | Tech Lead / Phase 0 | Open (tracked in spec.md §9) |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-23 | QC UC Read Agent | Báo cáo audit ban đầu; điểm 51/100 NOT READY; 13 vấn đề mở được xác định |
| v2 | 2026-06-30 | QC UC Read Agent | Re-audit sau khi BA cập nhật; điểm 51/100 NOT READY; các vấn đề I-001 đến I-013 được ghi lại |
| v3 | 2026-07-03 | QC UC Read Agent | Re-audit sau khi BA giải quyết I-001/I-002/I-004/I-005/I-006/I-009/I-010/I-011/I-013; điểm cập nhật lên 78/100 CONDITIONALLY READY; I-003 vẫn còn mở; các quan sát mới N-001/N-002/N-003 được thêm vào |
| v4 | 2026-07-06 | QC UC Read Agent | Re-audit với tài liệu mới nhất sau arc-migration 2026-07-04: UC, erd.md, us-002.md đã đồng bộ (D1→Aurora PostgreSQL, ExBot Worker→ExBot Lambda, MarketDataDO→Pool Slot0 Cache, CF service binding→API Gateway + HMAC). Không phát sinh issue mới từ arc-migration. I-003 vẫn còn mở. Điểm và verdict được duy trì: 82/100 CONDITIONALLY READY (tăng từ 78 do loại bỏ deduction về naming conflict — UC đã cập nhật đúng). |

---

## 10.3 Audit Summary — Readiness Score and Verdict

### Scoring Table

| Area | Description | Max Pts | Score | Notes |
|---|---|---|---|---|
| 1 | Function/Operation & Data Object Inventory | 20 | 18 | Response schema đầy đủ; tất cả 18 lifecycle states được liệt kê; enum sets hoàn chỉnh; UC đã cập nhật đúng tên thành phần sau arc-migration (Aurora PostgreSQL, ExBot Lambda, Pool Slot0 Cache); deduction nhỏ: `target_short_size` chưa được liệt kê tường minh trong danh sách đọc Aurora PostgreSQL ở UC bước 3 (I-003) |
| 2 | Data Object/State Attributes, Business Rules, Validations & Messages | 25 | 21 | Ngưỡng margin được ghi lại (FR-EXBOT-060); quy tắc auth được định nghĩa đầy đủ; null fallback cho Pool Slot0 Cache được chỉ định; mã lỗi E-EXBOT-021/022/023 đã đăng ký; HMAC Lambda Authorizer được mô tả đầy đủ; deduction: không có alternate flow cho ví Investor không khớp 403 (N-002); nhãn "Pending" gây mơ hồ trong response schema (N-001) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 19 | Tất cả alternate flows lifecycle state A1–A8 được bao phủ; công thức tính toán có mặt; auth được ghi lại đầy đủ cho cả hai đoạn; deduction: I-003 chưa được giải quyết (nguồn targetShortEth không rõ → assertion test drift% không thể chỉ rõ đầy đủ); ví không khớp 403 thiếu alternate flow có tên |
| 4 | Functional Integration & Data Consistency | 15 | 13 | Danh sách đọc Aurora PostgreSQL được liệt kê rõ ràng; tích hợp Pool Slot0 Cache được chỉ định; Facade passthrough được định nghĩa; tích hợp dual-chain được xác nhận; deduction nhỏ: không có ghi chú tường minh về hành vi eventual consistency của `margin_status` (cập nhật tại hedge-sync/deep-audit, có thể stale khi status được đọc) |
| 5 | UC/Spec Documentation Quality Issues | 15 | 11 | Các khoảng trống cấu trúc lớn đã được giải quyết trong v3; arc-migration được phản ánh nhất quán trong v4; deduction: nhãn "Pending implementation" tạo mơ hồ trong thiết kế test (N-001); FR trace không đầy đủ — FR-EXBOT-060, FR-EXBOT-093, FR-EXBOT-050 bị thiếu (N-003) |
| **Total** | | **100** | **82** | **CONDITIONALLY READY** |

### Verdict: CONDITIONALLY READY (82/100)

So với v3 (78/100), v4 ghi nhận cải tiến từ arc-migration 2026-07-04: UC, erd.md và us-002.md đều đã được cập nhật nhất quán. Không có mâu thuẫn tên thành phần nào còn tồn tại — tất cả tài liệu đều dùng Aurora PostgreSQL, ExBot Lambda, Pool Slot0 Cache, và API Gateway + HMAC Lambda Authorizer. Điểm tăng từ 78 lên 82 phản ánh việc loại bỏ deduction cho naming conflict tiềm năng đã được giải quyết.

**Một blocker còn lại (I-003):** Nguồn của `targetShortEth` trong công thức drift% chưa được xác nhận. FR-EXBOT-021 định nghĩa nó là giá trị tính toán (`lpEthAmount × hedgeRatio`), nhưng ERD có cột `target_short_size` trong `bot_runtime_state` có thể là giá trị đã cache. Sự mơ hồ này có nghĩa là test case cho drift% (AC-14) không thể chỉ rõ đầy đủ — cài đặt test data và kết quả mong đợi phụ thuộc vào việc Lambda đọc từ Aurora PostgreSQL hay tính lại.

**Khuyến nghị:** Tiến hành thiết kế test scenario cho tất cả các luồng ngoại trừ đường dẫn assertion drift%. Các scenario cho A1–A8, đường dẫn auth, null fallback, và xác nhận response schema có thể được thiết kế ngay. Phác thảo test case drift% như placeholder với công thức và đánh dấu pending theo I-003. Khi I-003 được xác nhận, hoàn thiện assertion drift% và hoàn chỉnh test case set.
