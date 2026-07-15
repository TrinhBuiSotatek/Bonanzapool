# Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-monitor-status

**Tiêu đề tài liệu:** UC Readiness Audit Report — UC-EXBOT-monitor-status  
**Ngày tạo:** 2026-07-15  
**Tác giả / Agent:** QC UC Read Agent  
**Phiên bản:** v5

---

## Reference Code Glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement for the ExBot module — numbered requirements defining bot behavior, API contracts, and state machine rules. Canonical source for all implementation decisions. | `srs/spec.md` |
| BR-EXBOT-* | Business Rule for ExBot — absolute invariants that must never be violated in code or documentation. | `srs/spec.md` §4 |
| E-EXBOT-* | API-level error code returned by ExBot Lambda through Operator Facade — defines HTTP status code and message content for each error case. | `02_backbone/message-list.md` |
| US-EXBOT-* | User Story for ExBot — acceptance criteria in Given/When/Then format from Investor or Operator perspective. | `userstories/us-*.md` |
| UC-EXBOT-* | Use Case for ExBot — describes system behavior at scenario level, including actors, flows, and FR trace. | `usecases/uc-*.md` |
| NFR-EXBOT-* | Non-Functional Requirement for ExBot — performance, security, reliability constraints. | `srs/spec.md` §3 |
| OQ-EXBOT-* | Open Question for ExBot — unresolved technical or business question affecting implementation or test design. | `srs/spec.md` §9 |
| Aurora PostgreSQL | AWS Aurora PostgreSQL Serverless v2 — relational database thay thế Cloudflare D1 (SQLite) theo arc-migration 2026-07-04. Hai database logic: `control_db` (global) và `state_db_shard_xx` (per-shard bot state). | `srs/erd.md`, SRS §1 |
| ExBot Lambda | AWS Lambda function chạy business logic ExBot — thay thế "ExBot Worker" (Cloudflare Worker) theo arc-migration 2026-07-04. | `usecases/uc-monitor-status.md` changelog 2026-07-04 |
| Pool Slot0 Cache | ElastiCache Redis cache dùng chung cho Uniswap V3 pool slot0 data (`sqrtPriceX96`, `currentTick`, `blockNumber`) — thay thế "MarketDataDO" (Cloudflare Durable Object) theo arc-migration 2026-07-04. | `srs/spec.md` FR-EXBOT-093 |
| HMAC Lambda Authorizer | AWS API Gateway Lambda Authorizer dùng xác thực chữ ký HMAC — thay thế Cloudflare service binding + shared-secret header theo arc-migration 2026-07-04. | `usecases/uc-monitor-status.md` changelog 2026-07-04 |
| SIWE | Sign-In With Ethereum — cơ chế xác thực dựa trên ví, liên quan đến luồng xác thực Investor qua POOL UI. | (industry term) |
| BigDecimal | Kiểu dữ liệu số thập phân chính xác tùy ý, dùng cho mọi tính toán tài chính trong ExBot. Cấm dùng float/number cho giá trị tài chính (NFR-EXBOT-008). | `srs/spec.md` NFR-EXBOT-008, FR-EXBOT-021 |

---

## Feature Brief

UC-EXBOT-monitor-status mô tả luồng truy vấn chỉ đọc `GET /api/exbot/status` cho phép USDC Investor đã xác thực theo dõi trạng thái vận hành hiện tại của ExBot. Toàn bộ luồng xử lý ở phía backend: POOL UI gọi Operator Facade, Facade chuyển tiếp đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer. ExBot Lambda đọc từ bốn bảng Aurora PostgreSQL (`bots`, `positions`, `hedge_legs`, `bot_runtime_state`), truy vấn `currentTick` từ Pool Slot0 Cache (ElastiCache Redis), tính toán hai giá trị dẫn xuất (`rangeState` và `drift_pct`), sau đó trả về JSON tổng hợp. Không có thao tác ghi nào xảy ra trong luồng này.

Actor Admin cũng có thể gọi endpoint và bỏ qua kiểm tra quyền sở hữu ví. Cơ chế xác thực hai lớp: header `X-Wallet-Address` (Investor/Admin) cho đoạn POOL UI → Facade; HMAC Lambda Authorizer cho đoạn Facade → ExBot Lambda.

**Điểm quan trọng cho v5 (re-audit 2026-07-15):** UC cập nhật 2026-07-13 đã giải quyết toàn bộ 4 câu hỏi mở: I-003 (nguồn `targetShortEth` = runtime computed `lp_eth_amount × target_ratio_bps/10000`), N-001 (pending fields phải `null` không phải absent), N-002 (A9 wallet mismatch → 403 E-EXBOT-030), N-003 (FR-EXBOT-050/060/093 bổ sung vào FR Trace). Tuy nhiên cross-check với ERD và spec phát hiện 5 vấn đề mới trong phần "Implemented fields" của JSON response schema (xem §10.1).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-monitor-status | View Active ExBot Status | — (no version field; cập nhật lần cuối 2026-07-14) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-07-14 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-monitor-status.md` | 2026-07-14 | UC (primary input) | Draft; cập nhật 2026-07-13 và 2026-07-14: giải quyết I-003/N-001/N-002/N-003; thêm A9 (wallet mismatch), bổ sung lp_eth_amount + hedge_legs.target_ratio vào step 3, cập nhật FR Trace |
| `userstories/us-002.md` | 2026-07-04 | US linked to this UC | Draft; cập nhật 2026-07-04 arc-migration |
| `srs/spec.md` | 2026-07-14 | SRS baseline — nguồn sự thật cho tất cả FR | Cập nhật 2026-07-13: đăng ký E-EXBOT-030; cập nhật 2026-07-14 I-N1 fix |
| `srs/states.md` | 2026-07-14 | Lifecycle state machine | Cập nhật 2026-07-14: I-N1 fix user_redeem column |
| `srs/erd.md` | 2026-07-14 | Aurora PostgreSQL data model | Cập nhật 2026-07-14: P2 fix funding_rolling_metrics note |
| `srs/flows.md` | 2026-06-29 | Sequence flow diagrams | Phiên bản mới nhất hiện có |
| `02_backbone/message-list.md` | 2026-07-13 | E-EXBOT-* error code registry | Cập nhật 2026-07-13: E-EXBOT-030 đăng ký |
| `UC-EXBOT-monitor-status_monitor-status_questions_20260715_v4.md` | 2026-07-15 | Question backlog (cập nhật mới nhất) | I-003/N-001/N-002/N-003 → Answered |
| `UC-EXBOT-monitor-status_monitor-status_audited_20260706_v4.md` | 2026-07-06 | Audit report v4 (CONDITIONALLY READY 82/100) | Baseline so sánh cho v5 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Endpoint `GET /api/exbot/status` tồn tại để USDC Investor xem trạng thái vận hành hiện tại của ExBot bất cứ lúc nào mà không cần truy cập dashboard nội bộ. Đây cũng là lớp tín hiệu để POOL UI bật hoặc tắt các nút thay đổi trạng thái (pause, close, emergency close) dựa trên `lifecycle_state` và tình trạng margin hiện tại. Admin actor có thể truy vấn bất kỳ bot nào để phục vụ giám sát vận hành và xử lý sự cố.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| `GET /api/exbot/status` — primary status query | Operator Facade chuyển tiếp đến ExBot Lambda qua API Gateway + HMAC Lambda Authorizer; Lambda đọc Aurora PostgreSQL và Pool Slot0 Cache, tính toán giá trị dẫn xuất, trả về JSON | UC §3, FR-EXBOT-090 |
| Multi-table Aurora PostgreSQL read | Đọc `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.lp_eth_amount`, `bot_runtime_state.last_light_check_at`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.target_ratio`, `hedge_legs.margin_status` | UC §3 step 3 (updated 2026-07-13) |
| Pool Slot0 Cache query | Lấy `currentTick` từ ElastiCache Redis (không gọi RPC trực tiếp) | UC §3 step 4, FR-EXBOT-093 |
| `rangeState` computation | So sánh `currentTick` với `tickLower`/`tickUpper`; null nếu `currentTick` null | UC §3 step 5 |
| `drift_pct` computation | `(|actualShortEth - targetShortEth| / targetShortEth) × 100` dùng BigDecimal; `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)`; null nếu `lp_eth_amount = 0` hoặc null | UC §3 step 6, FR-EXBOT-021 |
| JSON response schema — Implemented fields | `bot_id`, `status`, `lifecycle_state`, `safe_mode_tier`, `runtime_health_status`, `last_reconcile_at`, `last_error_code`, `dry_run` | UC §3 step 7 |
| JSON response schema — Pending implementation fields | `tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`, `safe_mode_reason`, `cooldown_end_at` — tất cả phải có mặt dưới dạng `null` cho đến khi triển khai | UC §3 step 7, N-001 fix |
| Alternate flows A1–A9 | Bao phủ `safe_mode`, `hedge_stopped_cooldown`, `lp_closing`, `closed`, `lp_rebalancing`, `error`, Pool Slot0 Cache null, no bot record, wallet mismatch (A9 mới từ N-002 fix) | UC §4 |
| Auth: Investor path | Header `X-Wallet-Address`; phải khớp `bot.user_wallet_address`; không khớp → 403 E-EXBOT-030 (A9) | UC §2, §4 A9 |
| Auth: Admin path | Header `X-Wallet-Address`; bỏ qua kiểm tra quyền sở hữu | UC §2 |
| Auth: Facade → Lambda | HMAC Lambda Authorizer qua API Gateway; chữ ký không hợp lệ → 401 | UC §2 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| POOL UI rendering logic | UC chỉ bao phủ API response payload; hành vi UI component thuộc POOL module scope | Test tập trung vào API response; UI rendering tests nằm ngoài phạm vi |
| Cập nhật `margin_status` | Được tính trong hedge-sync preflight và deep-audit (FR-EXBOT-060), không trong status read | Test phải dùng dữ liệu Aurora PostgreSQL đã cài sẵn |
| Dữ liệu lịch sử / audit trail | UC chỉ trả về snapshot hiện tại | N/A |
| Pause/resume mutation | Pause là UC riêng; endpoint status là read-only | N/A |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Khởi tạo truy vấn status từ POOL UI; xem trạng thái bot, LP range, kích thước hedge, margin status, lifecycle state | Chỉ truy vấn bot của mình (`wallet_address` phải khớp `bot.user_wallet_address`); không khớp → 403 E-EXBOT-030 (A9); read-only | UC §1, §2, §4 A9 |
| Admin | Secondary | Truy vấn status của bất kỳ bot nào để giám sát vận hành và xử lý sự cố | Bỏ qua kiểm tra quyền sở hữu; read-only | UC §1, §2 |
| Operator Facade | System | Nhận `GET /api/exbot/status`; kiểm tra `X-Wallet-Address` (401/403 nếu thất bại); chuyển tiếp đến ExBot Lambda qua API Gateway + HMAC Lambda Authorizer | Không sở hữu ExBot business logic; chỉ passthrough | UC §1, FR-EXBOT-090 |
| ExBot Lambda | System | Đọc Aurora PostgreSQL + Pool Slot0 Cache; tính `rangeState` và `drift_pct`; tổng hợp và trả về JSON status response | Không thể truy cập trực tiếp từ internet; chỉ tiếp nhận qua API Gateway | UC §1, FR-EXBOT-090 |
| Aurora PostgreSQL (state_db_shard) | System | Nguồn dữ liệu cho `bots`, `positions`, `hedge_legs`, `bot_runtime_state` | Read-only trong UC này | UC §3, `srs/erd.md` |
| Pool Slot0 Cache (ElastiCache Redis) | System | Cache dùng chung cho Uniswap V3 pool slot0 `currentTick` | Read-only; nếu unavailable hoặc stale → `current_tick: null`, `range_state: null` (A8) | UC §3 step 4, FR-EXBOT-093 |

**Nhận xét về mức độ sẵn sàng:** Actors được định nghĩa rõ ràng và đủ cho test design theo từng role. A9 (wallet mismatch → 403 E-EXBOT-030) đã được thêm vào Alternate Flows (giải quyết N-002). Admin bypass được ghi lại rõ ràng.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Caller gửi header `X-Wallet-Address`; thiếu header → 401 từ Operator Facade | Có | UC §2 |
| 2 | Investor: `wallet_address` trong header phải khớp `bot.user_wallet_address`; không khớp → 403 E-EXBOT-030 (A9) | Có (đường Investor) | UC §2, §4 A9 |
| 3 | Admin: header `X-Wallet-Address` phải có mặt; bỏ qua kiểm tra quyền sở hữu | Có (đường Admin) | UC §2 |
| 4 | Operator Facade kiểm tra caller không bị block; bị block → 403 | Có | UC §2 |
| 5 | Khi `access_mode=whitelist`: địa chỉ ví caller phải nằm trong whitelist; nếu không → 403 | Có điều kiện | UC §2 |
| 6 | Operator Facade chuyển tiếp đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer; chữ ký không hợp lệ/thiếu → 401 | Có | UC §2 |
| 7 | Route API Gateway từ Operator Facade đến ExBot Lambda được cấu hình và khả dụng | Có | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Truy vấn status (happy path) | Investor nhận response 200 JSON với Implemented fields đầy đủ; Pending fields trả về `null`; không có dữ liệu Aurora PostgreSQL nào bị thay đổi | UC §3 step 7–10 |
| Truy vấn status với Pool Slot0 Cache null | Response 200 với `current_tick: null`, `range_state: null`; các trường khác trả về bình thường | UC §4 A8, FR-EXBOT-093 |
| Truy vấn status cho bot `closed` | Response 200 với `lifecycle_state='closed'`; bản ghi được giữ trong Aurora PostgreSQL | UC §4 A3b |
| Không tìm thấy bản ghi bot | Response 404 với E-EXBOT-023 | UC §4 A4 |
| Wallet mismatch (Investor truy vấn bot của người khác) | Response 403 E-EXBOT-030 | UC §4 A9 |
| Operator Facade không khả dụng | 503 Service Unavailable từ lớp infra AWS; không có E-EXBOT code | UC §4 A5 |

---

## 4 và 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 GET /api/exbot/status — ExBot Status Query

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | POOL UI | Gọi `GET /api/exbot/status` với header `X-Wallet-Address` | Operator Facade nhận yêu cầu | — | Thiếu header → 401 | UC §2, §3.1 |
| 2 | Operator Facade | Kiểm tra `X-Wallet-Address`; chuyển tiếp đến ExBot Lambda qua API Gateway + HMAC Lambda Authorizer | ExBot Lambda nhận yêu cầu đã được chuyển tiếp | — | Ví bị block → 403; không có trong whitelist → 403; HMAC không hợp lệ → 401; Facade không khả dụng → 503 infra (A5) | UC §2, FR-EXBOT-090 |
| 3 | ExBot Lambda | Đọc từ Aurora PostgreSQL: `bots.status`, `bots.lifecycle_state`; `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.lp_eth_amount`, `bot_runtime_state.last_light_check_at`; `positions.tickLower`, `positions.tickUpper`; `hedge_legs.target_ratio`, `hedge_legs.margin_status` | Dữ liệu được trả về | — | Không có bản ghi bot → 404 E-EXBOT-023 (A4); ví Investor không khớp `bot.user_wallet_address` → 403 E-EXBOT-030 (A9) | UC §3.3, §4 A4, A9 |
| 4 | ExBot Lambda | Truy vấn `currentTick` từ Pool Slot0 Cache (ElastiCache Redis) | Giá trị `currentTick` được trả về | Pool Slot0 Cache unavailable hoặc stale → `current_tick: null`, `range_state: null` (A8); các trường khác trả về bình thường | — | UC §3.4, FR-EXBOT-093 |
| 5 | ExBot Lambda | Tính `rangeState`: `tickLower <= currentTick < tickUpper` → `"in"`; ngược lại → `"out"` | `range_state` được điền | `current_tick = null` → bỏ qua tính toán, `range_state: null` | — | UC §3.5 |
| 6 | ExBot Lambda | Tính `drift_pct`: `(|last_known_hl_short_size - targetShortEth| / targetShortEth) × 100` dùng BigDecimal; `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)` per FR-EXBOT-021 | `drift_pct` được điền | `status='safe_mode'` → A1; `lifecycle_state='hedge_stopped_cooldown'` → A2; `lifecycle_state='lp_rebalancing'` → A6; `status='error'` → A7 | `lp_eth_amount = 0` hoặc null → `drift_pct: null` (tránh chia cho 0) | UC §3.6, FR-EXBOT-021 |
| 7 | ExBot Lambda | Tổng hợp JSON status response: Implemented fields + Pending implementation fields (`null`) | Toàn bộ JSON payload được tổng hợp; Pending fields phải có mặt trong JSON với giá trị `null` (không được vắng mặt) | — | — | UC §3.7, N-001 fix |
| 8 | Operator Facade | Trả về JSON response cho POOL UI | 200 OK với status payload | — | — | UC §3.8 |
| 9 | POOL UI | Hiển thị status panel | Investor thấy nhãn trạng thái, LP range, kích thước hedge, drift%, margin status, thời gian light-check gần nhất | — | — | UC §3.9–10 |

**Alternate flows:**

| Flow | Điều kiện kích hoạt | Phản hồi hệ thống | Hành vi UI |
|---|---|---|---|
| A1 — safe_mode | `bots.status='safe_mode'` | 200 với `safe_mode_reason` trong response | Banner "Safe Mode — No new actions"; tất cả nút mutation bị tắt ngoại trừ "Close Bot (emergency)" |
| A2 — hedge_stopped_cooldown | `bots.lifecycle_state='hedge_stopped_cooldown'` | 200 với timestamp `cooldown_end_at` trong response | "Stop Fired — Cooldown (Xh remaining)"; nút mutation bị tắt |
| A3a — lp_closing | `bots.lifecycle_state='lp_closing'` | 200; message E-EXBOT-021 "Bot close is in progress. Please wait." | Tất cả nút mutation bị tắt |
| A3b — closed | `bots.lifecycle_state='closed'` | 200 với `lifecycle_state='closed'`; message E-EXBOT-022 "Bot safely closed. Funds have been returned to your wallet."; bản ghi được giữ trong Aurora PostgreSQL | Tất cả nút mutation bị tắt |
| A4 — no bot record | Không có bản ghi bot trong Aurora PostgreSQL cho botId | 404 E-EXBOT-023 "No active bot found for this account." Lưu ý: bot `closed` trả về 200, không phải 404 | UI hiển thị trạng thái rỗng |
| A5 — Facade unavailable | Lỗi ở tầng infra AWS | 503 Service Unavailable; không có E-EXBOT code | Banner "Status service temporarily unavailable" |
| A6 — lp_rebalancing | `bots.lifecycle_state='lp_rebalancing'` | 200 với `lifecycle_state='lp_rebalancing'` | "Rebalancing in progress"; tất cả nút mutation bị tắt |
| A7 — error | `bots.status='error'` | 200 với `status='error'`; message E-EXBOT-029 | "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close."; chỉ "Close Bot (emergency)" được bật |
| A8 — Pool Slot0 Cache null | Pool Slot0 Cache unavailable hoặc snapshot stale | 200; `current_tick: null`, `range_state: null`; tất cả trường khác bình thường | "—" hiển thị cho chỉ số range state |
| A9 — wallet mismatch | `wallet_address` của Investor không khớp `bot.user_wallet_address` | 403 E-EXBOT-030 "Access denied: this bot does not belong to your account." | UC §4 A9 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.lifecycle_state` | Phải là một trong 18 trạng thái canonical của SRS | Có | Nhãn lifecycle đúng được trả về | Không áp dụng (vấn đề toàn vẹn dữ liệu Aurora PostgreSQL — ngoài phạm vi UC này) | FR-EXBOT-003, `srs/states.md` |
| `rangeState` computation | Khoảng nửa mở: `tickLower <= currentTick < tickUpper`; `range_state: null` nếu `current_tick = null` | Có | `range_state: "in"` hoặc `"out"` | `current_tick: null` → `range_state: null` | UC §3 step 5 |
| `drift_pct` computation | Phép tính BigDecimal; `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)` per FR-EXBOT-021; cấm dùng float/number | Có | Giá trị `drift_pct` chính xác | `lp_eth_amount = 0` hoặc null → `drift_pct: null` (tránh chia cho 0); phép tính float là vi phạm NFR-EXBOT-008 | FR-EXBOT-021, NFR-EXBOT-008 |
| `target_ratio_bps` normalization | UC step 6 dùng `target_ratio_bps` nhưng ERD column là `target_ratio` TEXT — phải qua `normalizeTargetRatioBps()` để chuyển "0.70" → 7000n | Có | Tính toán đúng | Dùng `Number("0.70") × 10000` là vi phạm NFR-EXBOT-008 | FR-EXBOT-021, SRS NFR-EXBOT-008 |
| `margin_status` | Một trong: `ok` (marginUsage < 0.55), `warning` (0.55–0.75), `critical` (≥ 0.75) | Có | Nhãn margin đúng được trả về | Giá trị có thể stale (chỉ cập nhật tại hedge-sync preflight + deep-audit theo FR-EXBOT-060) | FR-EXBOT-060, `srs/states.md` |
| BR-EXBOT-007 — SAFE_MODE không phải trạng thái terminal | Bot SAFE_MODE phải vẫn phản hồi truy vấn status và cuối cùng đạt auto-recovery hoặc bot_safe_close | Có | Response 200 với dữ liệu safe_mode | N/A | BR-EXBOT-007 |
| Kiểm tra quyền sở hữu ví của Investor | `X-Wallet-Address` phải bằng `bot.user_wallet_address` cho Investor | Có (đường Investor) | Response 200 | 403 E-EXBOT-030 (A9) | UC §2, §4 A9 |
| Xác thực HMAC Lambda Authorizer | Chữ ký HMAC phải hợp lệ với khóa bí mật API Gateway | Có | Yêu cầu được chuyển tiếp | 401 từ ExBot Lambda | UC §2 |
| Pending fields trong JSON response | Tất cả Pending fields phải **có mặt** trong JSON với giá trị `null` — không được vắng mặt hoàn toàn | Có | Tất cả field hiện diện với `null` | Vắng mặt field ≠ `null` field — hai hành vi khác nhau | UC §3 step 7, N-001 fix |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Thiếu header `X-Wallet-Address` | Lỗi API | 401 Unauthorized | Kiểm tra xác thực Operator Facade | UC §2 |
| Ví caller bị Operator Facade block | Lỗi API | 403 Forbidden | Kiểm tra xác thực Operator Facade | UC §2 |
| Ví Investor không khớp `bot.user_wallet_address` | Lỗi API | 403 Forbidden — "Access denied: this bot does not belong to your account." | E-EXBOT-030 | UC §4 A9, `message-list.md` |
| HMAC không hợp lệ hoặc thiếu (Facade → Lambda) | Lỗi API | 401 từ ExBot Lambda | Kiểm tra HMAC Lambda Authorizer | UC §2 |
| Không tìm thấy bản ghi bot cho botId | Lỗi API | 404 Not Found — "No active bot found for this account." | E-EXBOT-023 | UC §4 A4, `message-list.md` |
| Bot ở trạng thái `lp_closing` | Response API (200) | "Bot close is in progress. Please wait." | E-EXBOT-021 | UC §4 A3a, `message-list.md` |
| Bot ở trạng thái `closed` | Response API (200) | "Bot safely closed. Funds have been returned to your wallet." | E-EXBOT-022 | UC §4 A3b, `message-list.md` |
| Bot ở trạng thái `error` | Response API (200) | "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close." | E-EXBOT-029 | UC §4 A7, `message-list.md` |
| Lỗi cơ sở hạ tầng Operator Facade | Response ở tầng infra | 503 Service Unavailable — "Status service temporarily unavailable" | Không có E-EXBOT code (tầng infra) | UC §4 A5 |
| Pool Slot0 Cache unavailable hoặc stale | Null field-level trong response 200 | `current_tick: null`, `range_state: null`; các trường khác bình thường | Không có mã lỗi | UC §4 A8, FR-EXBOT-093 |

#### D. Bảng kiểm kê thực thể và field (§F.1 Inventory)

| # | Field trong JSON response | Kiểu | Nguồn cột trong Aurora PG / Cache | Trạng thái | Ghi chú | Nguồn |
|---|---|---|---|---|---|---|
| 1 | `bot_id` | string | `bots.id` (UUID PK) | Implemented | Tên field JSON khác tên PK trong ERD (`id` vs `bot_id`) — xem V-006 | `srs/erd.md` |
| 2 | `status` | string | `bots.status` | Implemented | Coarse status: `active`, `paused`, `error`, `safe_mode`, `closed` | `srs/erd.md`, `srs/states.md` |
| 3 | `lifecycle_state` | string | `bots.lifecycle_state` | Implemented | 18 trạng thái canonical per `srs/states.md` | `srs/states.md`, FR-EXBOT-003 |
| 4 | `runtime_health_status` | string | `bot_runtime_state.health_status` | Implemented | **CONFLICT**: UC dùng `runtime_health_status`; ERD cột là `health_status` — V-001 | `srs/erd.md` |
| 5 | `last_reconcile_at` | string | `bot_runtime_state.last_hl_reconcile_at` | Implemented | **CONFLICT**: UC dùng `last_reconcile_at`; ERD cột là `last_hl_reconcile_at` — V-002 | `srs/erd.md` |
| 6 | `last_error_code` | string\|null | Không rõ nguồn cột | Implemented | Không có cột `last_error_code` trong bất kỳ bảng nào được liệt kê ở UC step 3 | `srs/erd.md` |
| 7 | `safe_mode_tier` | ? | Không xác định | Implemented | **MISSING**: không tồn tại trong bất kỳ bảng ERD nào, không định nghĩa trong `srs/spec.md` — V-003 | — |
| 8 | `dry_run` | boolean | Không xác định | Implemented | **MISSING**: không tồn tại trong bất kỳ bảng ERD nào, không định nghĩa trong `srs/spec.md` — V-004 | — |
| 9 | `tick_lower` | number\|null | `positions.tick_lower` | Pending | Tên cột trong ERD là `tick_lower` (INTEGER) — mapping đúng | `srs/erd.md` |
| 10 | `tick_upper` | number\|null | `positions.tick_upper` | Pending | Tên cột trong ERD là `tick_upper` (INTEGER) — mapping đúng | `srs/erd.md` |
| 11 | `current_tick` | number\|null | Pool Slot0 Cache (ElastiCache Redis) | Pending | Null khi cache unavailable/stale (A8); không phải cột Aurora PG | FR-EXBOT-093 |
| 12 | `range_state` | `"in"`\|`"out"`\|null | Giá trị dẫn xuất | Pending | Tính từ `tickLower <= currentTick < tickUpper`; null khi `current_tick = null` | UC §3 step 5 |
| 13 | `actual_short_eth` | string\|null | `bot_runtime_state.last_known_hl_short_size` | Pending | BigDecimal serialized as string per NFR-EXBOT-008 | `srs/erd.md`, FR-EXBOT-021 |
| 14 | `target_short_eth` | string\|null | Giá trị dẫn xuất | Pending | `lp_eth_amount × (target_ratio_bps / 10000)` per FR-EXBOT-021; BigDecimal | FR-EXBOT-021 |
| 15 | `drift_pct` | number\|null | Giá trị dẫn xuất | Pending | Null khi `lp_eth_amount = 0` hoặc null; BigDecimal per NFR-EXBOT-008 | FR-EXBOT-021, NFR-EXBOT-008 |
| 16 | `margin_status` | string\|null | `hedge_legs.margin_status` | Pending | `ok` / `warning` / `critical`; chỉ cập nhật tại hedge-sync preflight + deep-audit (FR-EXBOT-060) | FR-EXBOT-060, `srs/erd.md` |
| 17 | `last_light_check_at` | string\|null | `bot_runtime_state.last_light_check_at` | Pending | Mapping đúng — cột tồn tại trong ERD | `srs/erd.md` |
| 18 | `safe_mode_reason` | string\|null | Không xác định cột ERD | Pending | **UNCLEAR**: không có cột khớp trong `bots` hoặc `bot_runtime_state` — V-005 | — |
| 19 | `cooldown_end_at` | string\|null | Không xác định cột ERD | Pending | **UNCLEAR**: không có cột khớp trong `bots` hoặc `bot_runtime_state` — V-005 | — |

---

## 7. Phân tích liên kết (Integration Analysis)

| Hệ thống liên kết | Loại tích hợp | Dữ liệu đọc/ghi | Điều kiện phụ thuộc | Rủi ro test | Nguồn |
|---|---|---|---|---|---|
| Aurora PostgreSQL (`state_db_shard`) | Database read | Đọc: `bots`, `positions`, `hedge_legs`, `bot_runtime_state` | Kết nối Aurora PG phải sẵn sàng; nếu unavailable → lỗi hệ thống không được định nghĩa trong UC | Test cần cài sẵn dữ liệu fixture đầy đủ 4 bảng; thiếu row ở bất kỳ bảng nào sẽ gây lỗi join | UC §3, `srs/erd.md` |
| Pool Slot0 Cache (ElastiCache Redis) | Cache read | Đọc: `currentTick` | Nếu unavailable hoặc stale → `current_tick: null`, `range_state: null`; không block response | Test phải bao phủ cả 2 trường hợp: cache có giá trị và cache null | UC §4 A8, FR-EXBOT-093 |
| HMAC Lambda Authorizer (API Gateway) | Auth check | Xác thực chữ ký HMAC | Chữ ký không hợp lệ/thiếu → 401; test cần secret key đúng để tạo test request hợp lệ | Test cần secret key hoặc mock authorizer; không thể test trực tiếp mà không có credential | UC §2, FR-EXBOT-090 |
| Operator Facade | API Gateway / passthrough | Chuyển tiếp `X-Wallet-Address`; kiểm tra caller block/whitelist | Operator Facade phải khả dụng; 503 khi unavailable (tầng infra) | Test end-to-end cần Facade thật; unit test ExBot Lambda có thể dùng mock | UC §1, FR-EXBOT-090 |
| Hyperliquid (on-chain) | Gián tiếp | Dữ liệu LP position (`tickLower`, `tickUpper`) và hedge size (`last_known_hl_short_size`) được phản ánh vào Aurora PG sau mỗi light-check/hedge-sync | Dữ liệu có thể stale nếu light-check chưa chạy gần đây | Test cần dữ liệu Aurora PG fixture phản ánh trạng thái on-chain mong muốn; không gọi trực tiếp Hyperliquid trong UC này | `srs/erd.md`, FR-EXBOT-050 |

**Ghi chú về kiểm kê phụ thuộc on-chain (Blockchain Checklist §6b):**

UC này chạm vào dữ liệu liên quan đến on-chain LP position và HL agent key nhưng không thực hiện giao dịch on-chain trực tiếp trong luồng truy vấn status. Rủi ro test: dữ liệu Aurora PG có thể stale so với trạng thái on-chain thực tế. Test acceptance nên chỉ định rõ trạng thái fixture Aurora PG thay vì phụ thuộc vào dữ liệu on-chain live.

---

## 8. Acceptance Criteria candidates (§F.5)

| ID | User Story | Điều kiện Given | When | Then | Loại | Ghi chú |
|---|---|---|---|---|---|---|
| AC-ms-01 | US-EXBOT-002 AC-EXBOT-002-1 | Bot ở trạng thái `active`; `lp_eth_amount > 0`; Pool Slot0 Cache có `currentTick`; `currentTick` nằm trong `[tickLower, tickUpper)` | Investor gọi `GET /api/exbot/status` | 200 OK; `lifecycle_state='active'`; `range_state='in'`; `drift_pct` là số thập phân dương; 11 Pending fields = `null` | Happy path | Từ UC §3 + US-EXBOT-002 |
| AC-ms-02 | US-EXBOT-002 AC-EXBOT-002-2 | Bot ở trạng thái `safe_mode`; `safe_mode_reason` có giá trị | Investor gọi `GET /api/exbot/status` | 200 OK; `status='safe_mode'`; `safe_mode_reason` có mặt trong response (dù là Pending field — phải là `null` cho đến khi implemented) | Alternate A1 | `safe_mode_reason` hiện là Pending field; khi implemented phải có giá trị |
| AC-ms-03 | US-EXBOT-002 AC-EXBOT-002-3 | Bot ở trạng thái `hedge_stopped_cooldown` | Investor gọi `GET /api/exbot/status` | 200 OK; `lifecycle_state='hedge_stopped_cooldown'`; `cooldown_end_at` có mặt trong response | Alternate A2 | `cooldown_end_at` là Pending; khi implemented phải có timestamp |
| AC-ms-04 | Suy luận cần xác nhận | Pool Slot0 Cache không khả dụng | Investor gọi `GET /api/exbot/status` | 200 OK; `current_tick: null`; `range_state: null`; tất cả trường khác bình thường | Alternate A8 | Từ UC §4 A8 + FR-EXBOT-093 |
| AC-ms-05 | Suy luận cần xác nhận | Investor gọi với `wallet_address` không khớp bot | Investor gọi `GET /api/exbot/status` | 403 Forbidden; body chứa E-EXBOT-030 "Access denied: this bot does not belong to your account." | Error A9 | N-002 fix |
| AC-ms-06 | Suy luận cần xác nhận | Không có bản ghi bot nào trong Aurora PG cho caller | Investor gọi `GET /api/exbot/status` | 404 Not Found; body chứa E-EXBOT-023 "No active bot found for this account." | Error A4 | UC §4 A4 |
| AC-ms-07 | Suy luận cần xác nhận | `lp_eth_amount = 0` trong `bot_runtime_state` | Investor gọi `GET /api/exbot/status` | 200 OK; `drift_pct: null` (không phải 0 hay lỗi) | Edge case drift | FR-EXBOT-021 division-by-zero guard |
| AC-ms-08 | Suy luận cần xác nhận | Bot ở trạng thái `paused` (`bots.status='paused'`, `bots.lifecycle_state` là bất kỳ state nào với `status=paused`) | Investor gọi `GET /api/exbot/status` | 200 OK; `status='paused'`; response đầy đủ 19 fields | Gap: missing alternate flow — V-008 | Không có alternate flow cho `paused` trong UC; xem V-008 |
| AC-ms-09 | Suy luận cần xác nhận | Admin gọi với `wallet_address` khác chủ sở hữu bot | Admin gọi `GET /api/exbot/status` | 200 OK (bypass ownership check); response đầy đủ | Admin bypass | UC §2 |
| AC-ms-10 | Suy luận cần xác nhận | Bot `closed`; bản ghi còn trong Aurora PG | Investor gọi `GET /api/exbot/status` | 200 OK; `lifecycle_state='closed'`; E-EXBOT-022 message | Alternate A3b | UC §4 A3b |

---

## 9. Yêu cầu phi chức năng liên quan

| NFR ID | Nội dung yêu cầu | Áp dụng trong UC này như thế nào | Ghi chú kiểm thử |
|---|---|---|---|
| NFR-EXBOT-008 | Tất cả tính toán tài chính phải dùng BigDecimal; cấm dùng float/number cho giá trị tài chính | `drift_pct`, `target_short_eth`, `actual_short_eth` phải dùng BigDecimal; `target_ratio_bps` phải qua `normalizeTargetRatioBps()` | Test cần kiểm chứng giá trị trả về là string (BigDecimal serialized), không phải float JS; đặt biệt giá trị `target_ratio` dạng "0.70" phải được normalize thành 7000n trước khi tính toán |
| NFR-EXBOT-001 | Latency của Lambda response phải nằm trong giới hạn acceptable dưới tải bình thường | `GET /api/exbot/status` phải đáp ứng SLA latency ngay cả khi multi-table join Aurora PG + Cache query | Test hiệu năng cần thiết kế riêng; không block test design nhưng cần đề xuất cho QC Lead |
| NFR-EXBOT-003 (suy luận) | Bí mật API Gateway (HMAC key) không được lộ trong log | HMAC key dùng để ký request từ Facade → Lambda | Test bảo mật: kiểm tra không có HMAC key trong CloudWatch logs |

---

## 10. Issue Register và Audit Summary

### 10.1 Issue Register

| Issue ID | Loại | Mức độ | Vùng ảnh hưởng | Source trace | Phát hiện | Tác động với tester | Đề xuất câu hỏi / sửa | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| V-001 | CROSS_SOURCE_CONFLICT | Major | §F.1 Inventory, §F.2 Validation, §F.3 Functional Logic | UC step 7 "Implemented fields" liệt kê `runtime_health_status`; `srs/erd.md` bảng `bot_runtime_state` định nghĩa cột là `health_status` (không có tiền tố `runtime_`) | Tên field JSON `runtime_health_status` không khớp tên cột Aurora PG `health_status` trong bảng `bot_runtime_state`. Không rõ ExBot Lambda đọc từ cột `health_status` rồi ánh xạ thành `runtime_health_status` trong JSON, hay tên cột trong ERD bị ghi sai. | Tester không biết nên assertion là `runtime_health_status` hay `health_status`; không thể thiết kế test case kiểm chứng mapping DB → JSON mà không có xác nhận chính xác từ BA/Dev. | BA xác nhận: (a) tên field JSON chính xác trong response là gì; (b) tên cột Aurora PG chính xác trong `bot_runtime_state` là gì; (c) nếu khác nhau, có logic mapping tường minh nào không? | Open |
| V-002 | CROSS_SOURCE_CONFLICT | Major | §F.1 Inventory, §F.3 Functional Logic | UC step 7 "Implemented fields" liệt kê `last_reconcile_at`; `srs/erd.md` bảng `bot_runtime_state` định nghĩa cột là `last_hl_reconcile_at` | Tên field JSON `last_reconcile_at` không khớp tên cột Aurora PG `last_hl_reconcile_at`. Xung đột tương tự V-001 — không rõ đây là mapping có chủ đích hay tên cột bị ghi sai trong UC. | Tester không thể thiết kế test case kiểm chứng giá trị `last_reconcile_at` từ dữ liệu fixture Aurora PG nếu không biết cột thực sự là `last_hl_reconcile_at` hay `last_reconcile_at`. | BA xác nhận: tên field JSON và tên cột Aurora PG chính xác; nếu có ánh xạ, tài liệu hóa rõ ràng trong UC step 7. | Open |
| V-003 | MISSING_INFO | Major | §F.1 Inventory, §F.2 Validation | UC step 7 liệt kê `safe_mode_tier` là "Implemented field"; không có cột `safe_mode_tier` trong bất kỳ bảng nào của `srs/erd.md` (`bots`, `bot_runtime_state`, `hedge_legs`, `positions`); không có định nghĩa trong `srs/spec.md` | Field `safe_mode_tier` được khai báo là đã triển khai nhưng không có bằng chứng nào về nguồn dữ liệu, kiểu dữ liệu, hay giá trị hợp lệ trong toàn bộ tài liệu SRS/ERD. | Tester không thể thiết kế test case kiểm chứng `safe_mode_tier` vì không biết giá trị hợp lệ là gì, đọc từ đâu, hay điều kiện để nó thay đổi. Đây là blocker cho test case liên quan đến SAFE_MODE. | BA định nghĩa trong SRS: (a) nguồn dữ liệu (cột ERD nào hoặc logic tính toán); (b) kiểu dữ liệu; (c) tập giá trị hợp lệ; (d) khi nào thay đổi. | Open |
| V-004 | MISSING_INFO | Major | §F.1 Inventory | UC step 7 liệt kê `dry_run` (boolean) là "Implemented field"; không có cột `dry_run` trong bất kỳ bảng nào của `srs/erd.md`; không có định nghĩa trong `srs/spec.md` | Field `dry_run` được khai báo là boolean đã triển khai nhưng không có bằng chứng về nguồn dữ liệu trong ERD hay spec. | Tester không thể viết test case kiểm chứng `dry_run` vì không có fixture data source nào được xác định. | BA định nghĩa hoặc xác nhận: (a) `dry_run` đọc từ cột nào trong Aurora PG; (b) thêm cột vào ERD nếu đây là field thực; (c) hoặc xóa khỏi UC nếu đây là lỗi. | Open |
| V-005 | UNCLEAR_INFO | Minor | §F.1 Inventory | UC step 7 liệt kê `safe_mode_reason` (string) và `cooldown_end_at` (string) là "Pending implementation fields"; không có cột khớp tên trong `bots` hay `bot_runtime_state` trong `srs/erd.md` | Hai Pending fields không có cột nguồn được xác định trong ERD. Không rõ đây là fields sẽ được thêm vào ERD sau, hay sẽ được tính toán tại runtime, hay ánh xạ từ cột có tên khác. | Tester không thể thiết kế fixture data hoàn chỉnh để kiểm chứng các fields này sau khi implemented. | BA xác định: (a) cột Aurora PG nguồn cho `safe_mode_reason`; (b) cột Aurora PG nguồn cho `cooldown_end_at`; (c) nếu cột chưa tồn tại, lên kế hoạch thêm vào ERD. | Open |
| V-006 | UNCLEAR_INFO | Minor | §F.1 Inventory | UC step 7 dùng `bot_id` làm tên field JSON; `srs/erd.md` bảng `bots` định nghĩa PK là `id` (không phải `bot_id`) | Không rõ ExBot Lambda đọc `bots.id` rồi ánh xạ thành `bot_id` trong JSON response, hay đây là tên field JSON có chủ đích khác tên cột. Hiện tại đây là nhất quán sản phẩm (UUID được dùng nhất quán từ ngoài), nhưng cần tài liệu hóa rõ. | Minor impact: tester cần biết khi dựng fixture `bots.id = "xxx"`, thì `bot_id` trong response phải là `"xxx"`. | BA xác nhận rõ: `bot_id` trong JSON response là alias của `bots.id`; tài liệu hóa mapping trong UC step 7. | Open |
| V-007 | MISSING_INFO | Minor | §F.1 Inventory, §F.2 Validation | UC step 7 "Implemented fields" liệt kê `last_error_code` nhưng không có cột `last_error_code` trong `bots` hay `bot_runtime_state` trong UC step 3 reads list, và không tìm thấy cột này trong `srs/erd.md` | Field `last_error_code` được khai báo là Implemented field nhưng không có nguồn cột Aurora PG rõ ràng trong UC step 3 reads list. UC không chỉ định đọc từ bảng nào. | Tester không thể dựng fixture data cho `last_error_code` vì không biết cột nguồn. | BA thêm `last_error_code` vào reads list ở UC step 3 với bảng nguồn cụ thể; hoặc xác nhận đây là field computed. | Open |
| V-008 | MISSING_INFO | Minor | §F.3 Functional Logic | `srs/states.md` State Registry có trạng thái `active (pre-pause)` với `bots.status='paused'`; UC §4 Alternate Flows không có alternate flow nào cho trường hợp `status='paused'` | Khi bot bị pause, `bots.status='paused'` nhưng `lifecycle_state` vẫn là `active`. UC không định nghĩa response behavior hay UI khi nhận về `status='paused'`. | Tester không có AC để viết test case cho trạng thái `paused`. | BA thêm alternate flow cho `paused` vào UC §4: HTTP status, response schema, UI behavior. | Open |

### 10.2 Phụ thuộc chưa giải quyết

| # | Phụ thuộc | Loại | Tác động | Trạng thái |
|---|---|---|---|---|
| D1 | `srs/erd.md` cần bổ sung định nghĩa cột nguồn cho `safe_mode_tier`, `dry_run`, `last_error_code`, `safe_mode_reason`, `cooldown_end_at` | BA / SRS update | Blocks test case design cho các Implemented fields V-003, V-004, V-007 | Chờ BA xác nhận |
| D2 | Xác nhận tên cột chính xác cho `runtime_health_status` (V-001) và `last_reconcile_at` (V-002) | BA / SRS update | Blocks field-level assertion trong tất cả test case happy path | Chờ BA xác nhận |
| D3 | Thêm alternate flow cho `paused` status (V-008) | UC update | Thiếu test AC cho trạng thái `paused` | Chờ BA update UC |
| D4 | `srs/flows.md` (2026-06-29) chưa được cập nhật theo arc-migration 2026-07-04 | BA / SRS update | Sequence diagrams có thể không phản ánh AWS Lambda / Aurora PG flow mới | Không block ngay; lưu ý cho kỳ audit tiếp theo |

### 10.3 Audit Summary

#### Bảng điểm

| Vùng đánh giá | Điểm tối đa | Điểm đạt | Ghi chú |
|---|---|---|---|
| 1. Inventory đầy đủ (actors, states, fields, messages, flows) | 20 | 17 | Thiếu alternate flow cho `paused` (V-008), `last_error_code` nguồn không rõ (V-007); A1–A9 đầy đủ sau N-002 fix; 19 JSON fields được liệt kê |
| 2. Business rules và validation | 25 | 21 | V-003/V-004 (safe_mode_tier, dry_run chưa định nghĩa) và V-007 (last_error_code nguồn không rõ) không thể viết validation test; các BR còn lại rõ ràng; BR-EXBOT-007 được trace đúng |
| 3. Functional logic (flows, computations, edge cases) | 25 | 22 | V-001/V-002 (field name conflicts) có thể khiến tester assertion sai field; drift_pct computation và null-guard được định nghĩa đầy đủ; rangeState convention tường minh; Pool Slot0 Cache null path đã có |
| 4. Integration và external dependencies | 15 | 13 | Aurora PG 4-table read đầy đủ; Pool Slot0 Cache null path rõ ràng; HMAC auth hai lớp rõ ràng; `srs/flows.md` stale (D4) nhưng không block |
| 5. Document quality (trace, clarity, completeness) | 15 | 12 | FR Trace đầy đủ sau N-003 fix (FR-EXBOT-050/060/093); 5 Open issues trong Issue Register cần BA resolve; `srs/flows.md` stale |
| **Tổng** | **100** | **85** | |

#### Verdict: CONDITIONALLY READY

**Điều kiện để chuyển sang READY:**

1. **[Blocker — Major]** BA xác nhận tên field JSON chính xác cho `runtime_health_status` vs `health_status` (V-001) và `last_reconcile_at` vs `last_hl_reconcile_at` (V-002). Hiện tại tester không thể thiết kế test assertion cho các Implemented fields này.
2. **[Blocker — Major]** BA định nghĩa nguồn dữ liệu Aurora PG cho `safe_mode_tier` (V-003) và `dry_run` (V-004) — hai fields được khai báo là "Implemented" nhưng không có ERD backing.
3. **[Recommended — Minor]** BA xác nhận nguồn cột cho `last_error_code` (V-007), `safe_mode_reason` và `cooldown_end_at` (V-005), và mapping `bot_id` → `bots.id` (V-006).
4. **[Recommended — Minor]** BA thêm alternate flow cho trạng thái `paused` vào UC §4 (V-008).

**Nhận xét tổng thể:** v5 là một bước tiến so với v4 (82/100). Các vấn đề N-001/N-002/N-003/I-003 đã được giải quyết triệt để và phản ánh đúng trong UC. Các vấn đề mới phát hiện (V-001 đến V-008) đều phát sinh từ cross-check SRS/ERD với JSON response schema — đây là lớp kiểm tra quan trọng mà v4 chưa thực hiện đầy đủ. Các issues Major (V-001 đến V-004) cần được giải quyết trước khi tester bắt đầu thiết kế test case cho Implemented fields.

---

## 11. Changelog

| Version | Ngày | Nội dung thay đổi | Tác giả |
|---|---|---|---|
| v1 | 2026-06-30 | Audit đầu tiên | QC UC Read Agent |
| v2 | 2026-07-01 | Cập nhật sau khi đọc thêm us-002.md và message-list.md; bổ sung vào Question backlog | QC UC Read Agent |
| v3 | 2026-07-03 | Cập nhật sau BA answers qc-responses-2026-07-03.md; điểm 78/100 | QC UC Read Agent |
| v4 | 2026-07-06 | Re-audit sau UC update 2026-07-04; phát hiện N-001/N-002/N-003; điểm 82/100 CONDITIONALLY READY | QC UC Read Agent |
| v5 | 2026-07-15 | Re-audit đầy đủ sau UC update 2026-07-14 (giải quyết I-003/N-001/N-002/N-003). Cross-check SRS/ERD phát hiện 8 issues mới (V-001 đến V-008) liên quan đến field name conflicts, missing ERD definitions trong Implemented fields schema. Điểm 85/100 CONDITIONALLY READY. | QC UC Read Agent |

