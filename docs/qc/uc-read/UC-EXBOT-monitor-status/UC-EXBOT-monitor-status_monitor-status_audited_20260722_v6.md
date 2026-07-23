# Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-monitor-status

**Tiêu đề tài liệu:** UC Readiness Audit Report — UC-EXBOT-monitor-status
**Ngày tạo:** 2026-07-22
**Tác giả / Agent:** QC UC Read Agent
**Phiên bản:** v6

---

## Reference Code Glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement của module ExBot — các yêu cầu được đánh số định nghĩa hành vi bot, API contract, và rule của state machine. Là nguồn sự thật cho mọi quyết định triển khai. | `srs/spec.md` |
| BR-EXBOT-* | Business Rule của ExBot — các nguyên tắc bất biến tuyệt đối, không được vi phạm dù trong code hay tài liệu. | `srs/spec.md` §4 |
| E-EXBOT-* | Mã lỗi cấp API do ExBot Lambda trả về qua Operator Facade — quy định HTTP status code và nội dung message cho từng trường hợp lỗi. Nguồn canonical chính thức là `srs/spec.md` §5; `02_backbone/message-list.md` chỉ là bảng mirror tham khảo nhanh (xem V-010). | `srs/spec.md` §5 |
| MSG-SUC-* | Mã thông báo thành công hiển thị trên POOL UI sau khi thao tác mutation hoàn tất (ví dụ pause/resume). Khác với E-EXBOT-031 (label hiển thị khi xem status của bot đang `paused`) — hai loại message này phục vụ hai màn hình/thời điểm khác nhau, không dùng thay thế nhau. | `02_backbone/message-list.md` |
| US-EXBOT-* | User Story của ExBot — acceptance criteria dạng Given/When/Then từ góc nhìn Investor hoặc Operator. | `userstories/us-*.md` |
| UC-EXBOT-* | Use Case của ExBot — mô tả hành vi hệ thống ở mức scenario, bao gồm actor, luồng xử lý, và FR trace. | `usecases/uc-*.md` |
| NFR-EXBOT-* | Yêu cầu phi chức năng của ExBot — các ràng buộc về performance, security, reliability. | `srs/spec.md` §3 |
| OQ-EXBOT-* | Câu hỏi mở (Open Question) của ExBot — câu hỏi kỹ thuật hoặc nghiệp vụ chưa giải quyết, ảnh hưởng đến triển khai hoặc thiết kế test. | `srs/spec.md` §9 |
| Aurora PostgreSQL | AWS Aurora PostgreSQL Serverless v2 — cơ sở dữ liệu quan hệ, thay thế Cloudflare D1 (SQLite) theo arc-migration 2026-07-04. Gồm hai loại database logic: `control_db` (toàn cục) và `state_db_shard_xx` (theo shard, lưu state từng bot). | `srs/erd.md`, SRS §1 |
| ExBot Lambda | AWS Lambda function chạy business logic của ExBot — thay thế "ExBot Worker" (Cloudflare Worker) theo arc-migration 2026-07-04. | `usecases/uc-monitor-status.md` changelog 2026-07-04 |
| Pool Slot0 Cache | ElastiCache Redis cache dùng chung cho dữ liệu slot0 của pool Uniswap V3 (`sqrtPriceX96`, `currentTick`, `blockNumber`) — thay thế "MarketDataDO" (Cloudflare Durable Object) theo arc-migration 2026-07-04. | `srs/spec.md` FR-EXBOT-093 |
| HMAC Lambda Authorizer | AWS API Gateway Lambda Authorizer dùng để xác thực chữ ký HMAC (Hash-based Message Authentication Code — cơ chế xác thực bằng chữ ký mã hóa dựa trên khóa bí mật chung) — thay thế Cloudflare service binding + shared-secret header theo arc-migration 2026-07-04. | `usecases/uc-monitor-status.md` changelog 2026-07-04 |
| SIWE | Sign-In With Ethereum — cơ chế xác thực dựa trên ví, liên quan đến luồng xác thực Investor qua POOL UI. | (industry term) |
| BigDecimal | Kiểu dữ liệu số thập phân có độ chính xác tùy ý, dùng cho mọi phép tính tài chính trong ExBot. Cấm dùng kiểu float/number cho giá trị tài chính (NFR-EXBOT-008) vì có thể gây sai số làm tròn. | `srs/spec.md` NFR-EXBOT-008, FR-EXBOT-021 |
| isAdmin guard | Điều kiện chặn cứng trong code ExBot Lambda: nếu caller không có quyền Admin, request bị trả 403 ngay trước khi bất kỳ business logic nào của endpoint này chạy. Đây là thiếu sót đã biết của v1 (v1 gap) — đường xử lý dành cho Investor đang chờ triển khai. | `usecases/uc-monitor-status.md` §2 Preconditions |

---

## Feature Brief

UC-EXBOT-monitor-status mô tả luồng truy vấn chỉ đọc `GET /api/exbot/status/{botId}` cho phép USDC Investor đã xác thực theo dõi trạng thái vận hành hiện tại của bot ExBot của mình. Toàn bộ luồng xử lý nằm ở phía backend: POOL UI gọi Operator Facade, Facade chuyển tiếp đến ExBot Lambda qua API Gateway với HMAC Lambda Authorizer. ExBot Lambda đọc từ bốn bảng Aurora PostgreSQL (`bots`, `positions`, `hedge_legs`, `bot_runtime_state`), truy vấn `currentTick` từ Pool Slot0 Cache (ElastiCache Redis), tính toán hai giá trị dẫn xuất (`range_state` và `drift_pct`), sau đó trả về JSON tổng hợp. Không có thao tác ghi nào xảy ra trong luồng này. Actor Admin cũng có thể gọi endpoint này và được bỏ qua bước kiểm tra quyền sở hữu ví.

**Điểm quan trọng nhất của kỳ re-audit này (2026-07-22):** UC cập nhật ngày 2026-07-20 bổ sung một ghi chú thiếu sót nghiêm trọng của v1 vào phần Preconditions — ExBot Lambda có một điều kiện chặn cứng gọi là **isAdmin guard**: bất kỳ caller nào không có quyền Admin (tức là Investor, actor chính của UC này) sẽ nhận về lỗi 403 ngay trước khi business logic của endpoint chạy. Nói cách khác, trong v1, **toàn bộ các scenario dành cho Investor trong UC này chưa thể kiểm thử được** — endpoint hiện tại chỉ thực sự hoạt động cho actor Admin. Đây là thông tin đã được ghi lại rõ ràng trong tài liệu, nhưng ghi chú "v1 gap" này chỉ được gắn vào phần Preconditions và vào luồng thay thế A10 (`paused`) — chưa được lặp lại ở các luồng A1–A9, khiến người đọc lướt qua từng luồng thay thế riêng lẻ có thể hiểu nhầm rằng các luồng đó đã kiểm thử được cho Investor ngay bây giờ (xem V-009).

Ngoài ra, kỳ audit trước (v5, 85/100) đã đặt ra 8 câu hỏi mở (V-001 đến V-008) về xung đột tên field JSON so với tên cột ERD và các field "Implemented" thiếu nguồn dữ liệu. BA đã trả lời đầy đủ 7/8 câu hỏi này (`qc-responses-2026-07-20.md`, @hienduong, 2026-07-20) và UC đã được cập nhật trực tiếp để phản ánh 2 trong số đó (`last_error_code` nguồn dữ liệu — V-007; alternate flow A10 cho trạng thái `paused` — V-008). Riêng V-001 (`runtime_health_status` vs `health_status`) vẫn còn Open về mặt hình thức (câu trả lời BA trong file phản hồi trùng lặp nguyên văn câu hỏi, chưa phải một câu trả lời thực sự) nhưng có bằng chứng gián tiếp mạnh: changelog của `srs/erd.md` ngày 2026-07-20 cho thấy dev đã tự sửa tên cột ERD thành `runtime_health_status` để khớp với UC, đã xác nhận qua code `runtime-state.ts` và `get-bot-status` handler.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-monitor-status | View Active ExBot Status | — (không có version field; cập nhật lần cuối 2026-07-20/21) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-07-21 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-monitor-status.md` | 2026-07-20/21 | UC (primary input) | Cập nhật 2026-07-20: sửa endpoint thành `/{botId}`, thêm ghi chú v1 gap isAdmin guard vào Preconditions, thêm A10 (`paused`); cập nhật 2026-07-21: đăng ký E-EXBOT-031, trích dẫn trong A10 |
| `userstories/us-002.md` | 2026-07-04 | US linked to this UC | Không thay đổi từ kỳ audit trước; phần Notes vẫn ghi endpoint cũ không có `{botId}` (xem V-011) |
| `srs/spec.md` | (không version field; đã kiểm tra §5 Error Codes) | SRS baseline — nguồn sự thật cho mọi FR và E-code | Xác nhận E-EXBOT-030 (đăng ký 2026-07-13) và E-EXBOT-031 (đăng ký 2026-07-21) đã có trong §5, đúng như UC trích dẫn |
| `srs/states.md` | (đã kiểm tra State Registry) | Lifecycle state machine | Xác nhận state `active (pre-pause)` với `bots.status='paused'`, pause chỉ được phép từ `lifecycle_state='active'` |
| `srs/erd.md` | Changelog 2026-07-20 | Aurora PostgreSQL data model | Cập nhật 2026-07-20: thêm cột `safe_mode_tier` vào `bot_runtime_state`; sửa `health_status` → `runtime_health_status` — hai thay đổi này trực tiếp đóng V-003 và làm rõ V-001 |
| `frd.md` | Changelog 2026-07-14 (I-N4 fix) | FRD | Xác nhận FR-EXBOT-100 (§4.11 Operator Facade Endpoints) vẫn là số khác với FR-EXBOT-090 (Operator Facade API) trong `spec.md` — vấn đề numbering cũ, đã Answered không-blocking ở I-007/I-014, không re-raise |
| `02_backbone/common-rules.md` | (đọc toàn bộ) | Common Rules | **Không có section BR-EXBOT-*** trong file này — BR-EXBOT-007 phải trace về `srs/spec.md` §4, không phải `common-rules.md` (sửa lại trích dẫn nguồn so với v5) |
| `02_backbone/message-list.md` | (đọc toàn bộ EXBOT section) | E-EXBOT-* mirror registry | Bảng EXBOT dừng ở E-EXBOT-029; chưa mirror E-EXBOT-030/031 — xem V-010 |
| `UC-EXBOT-monitor-status_monitor-status_questions_20260715_v4.md` | Cập nhật in-place 2026-07-22 | Question backlog | V-002 đến V-008 → Answered (@hienduong, 2026-07-20); V-001 vẫn Open |
| `UC-EXBOT-monitor-status_monitor-status_audited_20260715_v5.md` | 2026-07-15 | Audit report v5 (85/100, CONDITIONALLY READY) | Baseline so sánh cho v6 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Endpoint `GET /api/exbot/status/{botId}` tồn tại để USDC Investor xem trạng thái vận hành hiện tại của ExBot bất cứ lúc nào mà không cần truy cập dashboard nội bộ. Đây cũng là lớp tín hiệu để POOL UI bật hoặc tắt các nút thay đổi trạng thái (pause, close, emergency close) dựa trên `lifecycle_state` và tình trạng margin hiện tại. Admin actor có thể truy vấn bất kỳ bot nào để phục vụ giám sát vận hành và xử lý sự cố.

**Ghi chú readiness quan trọng:** trong v1, mục tiêu nghiệp vụ nói trên chỉ thực hiện được cho actor Admin. Đường xử lý cho Investor — actor chính mà mục tiêu nghiệp vụ này hướng tới — bị chặn bởi isAdmin guard (xem Feature Brief và §2 Actor).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| `GET /api/exbot/status/{botId}` — primary status query | Operator Facade chuyển tiếp đến ExBot Lambda qua API Gateway + HMAC Lambda Authorizer; Lambda đọc Aurora PostgreSQL và Pool Slot0 Cache, tính toán giá trị dẫn xuất, trả về JSON | UC §3, FR-EXBOT-090 |
| Multi-table Aurora PostgreSQL read | Đọc `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.lp_eth_amount`, `bot_runtime_state.last_light_check_at`, `bot_runtime_state.last_error_code` (v1 gap — cột chưa có trong schema, luôn `null`), `positions.tickLower`, `positions.tickUpper`, `hedge_legs.target_ratio`, `hedge_legs.margin_status` | UC §3 step 3 |
| Pool Slot0 Cache query | Lấy `currentTick` từ ElastiCache Redis (không gọi RPC trực tiếp) | UC §3 step 4, FR-EXBOT-093 |
| `range_state` computation | So sánh `currentTick` với `tickLower`/`tickUpper`; null nếu `currentTick` null | UC §3 step 5 |
| `drift_pct` computation | `(|actualShortEth - targetShortEth| / targetShortEth) × 100` dùng BigDecimal; `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)`; null nếu `lp_eth_amount = 0` hoặc null | UC §3 step 6, FR-EXBOT-021 |
| JSON response schema — Implemented fields | `bot_id`, `status`, `lifecycle_state`, `safe_mode_tier` (v1 gap, luôn `null`), `runtime_health_status`, `last_reconcile_at` (v1 gap, luôn `null`), `last_error_code` (v1 gap, luôn `null`), `dry_run` | UC §3 step 7 |
| JSON response schema — Pending implementation fields | `tick_lower`, `tick_upper`, `current_tick`, `range_state`, `actual_short_eth`, `target_short_eth`, `drift_pct`, `margin_status`, `last_light_check_at`, `safe_mode_reason` (v1 gap, luôn `null`), `cooldown_end_at` (v1 gap, luôn `null`) — tất cả phải có mặt dưới dạng `null` cho đến khi triển khai | UC §3 step 7 |
| Alternate flows A1–A10 | Bao phủ `safe_mode`, `hedge_stopped_cooldown`, `lp_closing`, `closed`, `lp_rebalancing`, `error`, Pool Slot0 Cache null, wallet mismatch, và `paused` (A10 — mới thêm 2026-07-20) | UC §4 |
| Auth: Investor path | Header `X-Wallet-Address`; phải khớp `bot.user_wallet_address`; không khớp → 403 E-EXBOT-030 (A9). **Ngoài ra, mọi request từ Investor còn bị chặn sớm hơn bởi isAdmin guard trong v1 (xem §2 Preconditions)** | UC §2, §4 A9 |
| Auth: Admin path | Header `X-Wallet-Address`; bỏ qua kiểm tra quyền sở hữu; là actor duy nhất thực sự vượt qua được isAdmin guard trong v1 | UC §2 |
| Auth: Facade → Lambda | HMAC Lambda Authorizer qua API Gateway; chữ ký không hợp lệ → 401 | UC §2 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| POOL UI rendering logic | UC chỉ bao phủ API response payload; hành vi UI component thuộc phạm vi module POOL | Test tập trung vào API response; UI rendering test nằm ngoài phạm vi |
| Cập nhật `margin_status` | Được tính trong hedge-sync preflight và deep-audit (FR-EXBOT-060), không trong luồng đọc status | Test phải dùng dữ liệu Aurora PostgreSQL đã cài sẵn (fixture) |
| Dữ liệu lịch sử / audit trail | UC chỉ trả về snapshot hiện tại | N/A |
| Pause/resume mutation | Pause là UC riêng; endpoint status ở đây là read-only | N/A |
| Đường xử lý Investor trong v1 | isAdmin guard chặn toàn bộ request Investor trước khi chạy business logic; đường xử lý này thuộc phạm vi UC nhưng **chưa triển khai** — chờ v1.1 | Test case theo actor Investor phải đánh dấu "Blocked — chờ v1.1", chỉ test case theo actor Admin mới thực thi được ngay trong v1 |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Xem trạng thái bot của mình, LP range, kích thước hedge, margin status, lifecycle state | Chỉ truy vấn bot của mình (`wallet_address` phải khớp `bot.user_wallet_address`), không khớp → 403 E-EXBOT-030 (A9); read-only. **v1 gap:** trước cả bước kiểm tra ownership, request của Investor đã bị isAdmin guard chặn ở tầng đầu, trả về 403 ngay lập tức — mọi scenario của Investor trong UC này (bao gồm cả happy path) đều không thể thực thi được trong v1 | UC §1, §2, §4 A9, A10 |
| Admin | Secondary | Truy vấn status của bất kỳ bot nào để giám sát vận hành và xử lý sự cố | Bỏ qua kiểm tra quyền sở hữu ví; read-only. **Là actor duy nhất vượt qua được isAdmin guard trong v1** — mọi test case chức năng trong v1 phải chạy dưới actor Admin | UC §1, §2 |
| Operator Facade | System | Nhận `GET /api/exbot/status/{botId}`; kiểm tra `X-Wallet-Address` (401/403 nếu thất bại); chuyển tiếp đến ExBot Lambda qua API Gateway + HMAC Lambda Authorizer | Không sở hữu business logic của ExBot; chỉ đóng vai trò passthrough | UC §1, FR-EXBOT-090 |
| ExBot Lambda | System | Áp dụng isAdmin guard; đọc Aurora PostgreSQL + Pool Slot0 Cache; tính `range_state` và `drift_pct`; tổng hợp và trả về JSON status response | Không thể truy cập trực tiếp từ internet; chỉ tiếp nhận qua API Gateway; **v1 gap:** chặn cứng non-Admin caller trước khi chạy logic | UC §2, §3, FR-EXBOT-090 |
| Aurora PostgreSQL (`state_db_shard`) | System | Nguồn dữ liệu cho `bots`, `positions`, `hedge_legs`, `bot_runtime_state` | Read-only trong UC này | UC §3, `srs/erd.md` |
| Pool Slot0 Cache (ElastiCache Redis) | System | Cache dùng chung cho `currentTick` của pool Uniswap V3 | Read-only; nếu unavailable hoặc stale → `current_tick: null`, `range_state: null` (A8) | UC §3 step 4, FR-EXBOT-093 |

**Nhận xét về mức độ sẵn sàng:** Actor được định nghĩa rõ ràng, nhưng mức độ sẵn sàng để test theo role đã thay đổi đáng kể so với v5: trong v1, chỉ actor Admin thực sự thực thi được toàn bộ luồng; actor Investor — actor chính (Primary) của UC — bị chặn hoàn toàn bởi isAdmin guard. Đây là điểm quan trọng nhất tester cần nắm trước khi thiết kế test case theo role (xem V-009 tại §10.1).

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
| 8 | **v1 gap:** caller phải có quyền Admin — ExBot Lambda có isAdmin guard chặn cứng, non-Admin caller (Investor) nhận 403 trước khi bất kỳ business logic nào chạy; đường xử lý Investor đang chờ triển khai | Có (chặn toàn bộ actor Investor trong v1) | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Admin truy vấn status (happy path, v1) | Nhận response 200 JSON với Implemented fields đầy đủ (một số luôn `null` do v1 gap — xem §6.1.D); Pending fields trả về `null`; không có dữ liệu Aurora PostgreSQL nào bị thay đổi | UC §3 step 7–10 |
| Investor truy vấn status (v1) | 403 Forbidden do isAdmin guard — không đến được business logic, bất kể `wallet_address` có khớp hay không | UC §2 v1 gap |
| Truy vấn status với Pool Slot0 Cache null | Response 200 với `current_tick: null`, `range_state: null`; các trường khác trả về bình thường | UC §4 A8, FR-EXBOT-093 |
| Truy vấn status cho bot `closed` | Response 200 với `lifecycle_state='closed'`; bản ghi được giữ trong Aurora PostgreSQL | UC §4 A3b |
| Truy vấn status cho bot `paused` | Response 200 với `status='paused'`, `lifecycle_state` giữ giá trị trước khi pause; E-EXBOT-031 hiển thị trên UI | UC §4 A10 |
| Không tìm thấy bản ghi bot | Response 404 với E-EXBOT-023 | UC §4 A4 |
| Wallet mismatch (Investor truy vấn bot của người khác) | Response 403 E-EXBOT-030 — **về lý thuyết**; trong v1 request Investor không tới được bước kiểm tra này vì đã bị isAdmin guard chặn trước | UC §4 A9, §2 v1 gap |
| Operator Facade không khả dụng | 503 Service Unavailable từ lớp infra AWS; không có E-EXBOT code | UC §4 A5 |

---

## 4 và 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 GET /api/exbot/status/{botId} — ExBot Status Query

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | POOL UI | Gọi `GET /api/exbot/status/{botId}` với header `X-Wallet-Address` | Operator Facade nhận yêu cầu | — | Thiếu header → 401 | UC §2, §3.1 |
| 2 | Operator Facade | Kiểm tra `X-Wallet-Address`; chuyển tiếp đến ExBot Lambda qua API Gateway + HMAC Lambda Authorizer | ExBot Lambda nhận yêu cầu đã được chuyển tiếp | — | Ví bị block → 403; không có trong whitelist → 403; HMAC không hợp lệ → 401; Facade không khả dụng → 503 infra (A5) | UC §2, FR-EXBOT-090 |
| 2b | ExBot Lambda | Áp dụng isAdmin guard (v1 gap) trước khi xử lý business logic | Nếu caller có quyền Admin → tiếp tục bước 3 | — | Caller không có quyền Admin (Investor) → 403 ngay lập tức, không chạy các bước tiếp theo | UC §2 (changelog 2026-07-20) |
| 3 | ExBot Lambda | Đọc từ Aurora PostgreSQL: `bots.status`, `bots.lifecycle_state`; `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.lp_eth_amount`, `bot_runtime_state.last_light_check_at`, `bot_runtime_state.last_error_code` (v1 gap — cột chưa có trong schema, hardcode `null`); `positions.tickLower`, `positions.tickUpper`; `hedge_legs.target_ratio`, `hedge_legs.margin_status` | Dữ liệu được trả về | — | Không có bản ghi bot → 404 E-EXBOT-023 (A4); ví Investor không khớp `bot.user_wallet_address` → 403 E-EXBOT-030 (A9) — chỉ áp dụng về lý thuyết, vì trong v1 request Investor đã bị chặn ở bước 2b | UC §3.3, §4 A4, A9 |
| 4 | ExBot Lambda | Truy vấn `currentTick` từ Pool Slot0 Cache (ElastiCache Redis) | Giá trị `currentTick` được trả về | Pool Slot0 Cache unavailable hoặc stale → `current_tick: null`, `range_state: null` (A8); các trường khác trả về bình thường | — | UC §3.4, FR-EXBOT-093 |
| 5 | ExBot Lambda | Tính `range_state`: `tickLower <= currentTick < tickUpper` → `"in"`; ngược lại → `"out"` | `range_state` được điền | `current_tick = null` → bỏ qua tính toán, `range_state: null` | — | UC §3.5 |
| 6 | ExBot Lambda | Tính `drift_pct`: `(|actualShortEth - targetShortEth| / targetShortEth) × 100` dùng BigDecimal; `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)` per FR-EXBOT-021 | `drift_pct` được điền | `status='safe_mode'` → A1; `lifecycle_state='hedge_stopped_cooldown'` → A2; `lifecycle_state='lp_rebalancing'` → A6; `status='error'` → A7; `status='paused'` → A10 | `lp_eth_amount = 0` hoặc null → `drift_pct: null` (tránh chia cho 0) | UC §3.6, FR-EXBOT-021 |
| 7 | ExBot Lambda | Tổng hợp JSON status response: Implemented fields + Pending implementation fields (`null`) | Toàn bộ JSON payload được tổng hợp; Pending fields phải có mặt trong JSON với giá trị `null` (không được vắng mặt) | — | — | UC §3.7 |
| 8 | Operator Facade | Trả về JSON response cho POOL UI | 200 OK với status payload | — | — | UC §3.8 |
| 9 | POOL UI | Hiển thị status panel | Investor/Admin thấy nhãn trạng thái, LP range, kích thước hedge, drift%, margin status, thời gian light-check gần nhất | — | — | UC §3.9–10 |

**Alternate flows:**

| Flow | Điều kiện kích hoạt | Phản hồi hệ thống | Hành vi UI | Ghi chú v1 gap |
|---|---|---|---|---|
| A1 — safe_mode | `bots.status='safe_mode'` | 200 với `safe_mode_reason` trong response | Banner "Safe Mode — No new actions"; tất cả nút mutation bị tắt ngoại trừ "Close Bot (emergency)" | `safe_mode_reason` là Pending field, cột `bot_runtime_state.safe_mode_reason` chưa tồn tại — luôn trả về `null` trong v1 (V-005 Answered) |
| A2 — hedge_stopped_cooldown | `bots.lifecycle_state='hedge_stopped_cooldown'` | 200 với timestamp `cooldown_end_at` trong response | "Stop Fired — Cooldown (Xh remaining)"; nút mutation bị tắt | `cooldown_end_at` là Pending field, cột chưa tồn tại — luôn trả về `null` trong v1 (V-005 Answered) |
| A3a — lp_closing | `bots.lifecycle_state='lp_closing'` | 200; message E-EXBOT-021 "Bot close is in progress. Please wait." | Tất cả nút mutation bị tắt | — |
| A3b — closed | `bots.lifecycle_state='closed'` | 200 với `lifecycle_state='closed'`; message E-EXBOT-022 "Bot safely closed. Funds have been returned to your wallet."; bản ghi được giữ trong Aurora PostgreSQL | Tất cả nút mutation bị tắt | — |
| A4 — no bot record | Không có bản ghi bot trong Aurora PostgreSQL cho `botId` | 404 E-EXBOT-023 "No active bot found for this account." Lưu ý: bot `closed` trả về 200, không phải 404 | UI hiển thị trạng thái rỗng | — |
| A5 — Facade unavailable | Lỗi ở tầng infra AWS (API Gateway hoặc Lambda cold-start/throttle) | 503 Service Unavailable; không có E-EXBOT code | Banner "Status service temporarily unavailable" | — |
| A6 — lp_rebalancing | `bots.lifecycle_state='lp_rebalancing'` | 200 với `lifecycle_state='lp_rebalancing'` | "Rebalancing in progress"; tất cả nút mutation bị tắt | — |
| A7 — error | `bots.status='error'` | 200 với `status='error'`; message E-EXBOT-029 | "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close."; chỉ "Close Bot (emergency)" được bật | — |
| A8 — Pool Slot0 Cache null | Pool Slot0 Cache unavailable hoặc snapshot stale | 200; `current_tick: null`, `range_state: null`; tất cả trường khác bình thường | "—" hiển thị cho chỉ số range state | — |
| A9 — wallet mismatch | `wallet_address` của Investor không khớp `bot.user_wallet_address` | 403 E-EXBOT-030 "Access denied: this bot does not belong to your account." | UC §4 A9 | **v1 gap:** không thể thực thi bằng actor Investor trong v1 vì đã bị isAdmin guard chặn trước khi tới bước kiểm tra ownership (xem V-009) |
| A10 — paused | `bots.status='paused'` (status overlay — `lifecycle_state` giữ nguyên giá trị trước khi pause, thường là `active`) | 200 với `status='paused'`, `lifecycle_state=<giá trị được giữ nguyên>`; UI hiển thị E-EXBOT-031 "Bot Paused. Hedge and LP are maintained. You may still redeem." | Tất cả nút mutation bị tắt; riêng `user_redeem` vẫn được phép theo State Registry | **v1 gap:** chưa thể kiểm thử đầy đủ cho actor Investor cho đến khi isAdmin guard được gỡ bỏ (V-008 Answered) |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.lifecycle_state` | Phải là một trong các trạng thái canonical của State Registry trong `srs/states.md` | Có | Nhãn lifecycle đúng được trả về | Không áp dụng (vấn đề toàn vẹn dữ liệu Aurora PostgreSQL — ngoài phạm vi UC này) | FR-EXBOT-003, `srs/states.md` |
| `range_state` computation | Khoảng nửa mở: `tickLower <= currentTick < tickUpper`; `range_state: null` nếu `current_tick = null` | Có | `range_state: "in"` hoặc `"out"` | `current_tick: null` → `range_state: null` | UC §3 step 5 |
| `drift_pct` computation | Phép tính BigDecimal; `targetShortEth = lp_eth_amount × (target_ratio_bps / 10000)` per FR-EXBOT-021; cấm dùng float/number | Có | Giá trị `drift_pct` chính xác | `lp_eth_amount = 0` hoặc null → `drift_pct: null` (tránh chia cho 0); phép tính float là vi phạm NFR-EXBOT-008 | FR-EXBOT-021, NFR-EXBOT-008 |
| `margin_status` | Một trong: `ok` (marginUsage < 0.55), `warning` (0.55–0.75), `critical` (≥ 0.75) | Có | Nhãn margin đúng được trả về | Giá trị có thể stale (chỉ cập nhật tại hedge-sync preflight + deep-audit theo FR-EXBOT-060) | FR-EXBOT-060, `srs/states.md` |
| BR-EXBOT-007 — SAFE_MODE không phải trạng thái terminal | Bot ở SAFE_MODE phải vẫn phản hồi truy vấn status và cuối cùng đạt auto-recovery hoặc chuyển qua `bot_safe_close` | Có | Response 200 với dữ liệu safe_mode | N/A | `srs/spec.md` §4 (BR-EXBOT-007 — sửa lại nguồn trích dẫn so với v5; `common-rules.md` không có section BR-EXBOT-*) |
| Kiểm tra quyền sở hữu ví của Investor | `X-Wallet-Address` phải bằng `bot.user_wallet_address` cho Investor | Có (đường Investor, về lý thuyết) | Response 200 | 403 E-EXBOT-030 (A9) | UC §2, §4 A9 |
| **isAdmin guard (v1 gap)** | Caller phải có quyền Admin; không có business logic nào chạy cho non-Admin caller | Có, chặn trước mọi rule khác | Request tiếp tục xử lý (chỉ Admin) | 403 ngay lập tức cho Investor, không phân biệt lý do khác | UC §2 (changelog 2026-07-20) |
| Xác thực HMAC Lambda Authorizer | Chữ ký HMAC phải hợp lệ với khóa bí mật API Gateway | Có | Yêu cầu được chuyển tiếp | 401 từ ExBot Lambda | UC §2 |
| Pending fields trong JSON response | Tất cả Pending fields phải **có mặt** trong JSON với giá trị `null` — không được vắng mặt hoàn toàn | Có | Tất cả field hiện diện với `null` | Vắng mặt field ≠ `null` field — hai hành vi khác nhau | UC §3 step 7 |
| `safe_mode_tier` (v1 gap) | Enum `warning`/`restricted`/`frozen`; cột `bot_runtime_state.safe_mode_tier` đã được thêm vào ERD (2026-07-20) nhưng logic set giá trị `restricted`/`frozen` mới hoạt động một phần trong v1 (`warning` chưa có điều kiện kích hoạt) | Có | Giá trị enum đúng khi có điều kiện kích hoạt | Luôn `null` cho đến khi `enterSafeMode()` set giá trị; test theo từng tier chỉ thực thi đầy đủ từ v1.1 | V-003 Answered, `srs/erd.md` |
| `dry_run` | Đọc từ biến môi trường `EXBOT_DRY_RUN`, không phải cột DB; `true` → mọi lệnh gọi Hyperliquid bị short-circuit (không gửi lệnh thật) | Có | Trả về boolean đúng theo config môi trường | N/A | V-004 Answered |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Thiếu header `X-Wallet-Address` | Lỗi API | 401 Unauthorized | Kiểm tra xác thực Operator Facade | UC §2 |
| Ví caller bị Operator Facade block | Lỗi API | 403 Forbidden | Kiểm tra xác thực Operator Facade | UC §2 |
| Caller không có quyền Admin (v1 gap isAdmin guard) | Lỗi API | 403 Forbidden — chặn trước business logic, không có message code riêng được UC định nghĩa | Không có E-EXBOT code — xem V-012 | UC §2 (changelog 2026-07-20) |
| Ví Investor không khớp `bot.user_wallet_address` | Lỗi API (về lý thuyết trong v1) | 403 Forbidden — "Access denied: this bot does not belong to your account." | E-EXBOT-030 | UC §4 A9, `srs/spec.md` §5 |
| HMAC không hợp lệ hoặc thiếu (Facade → Lambda) | Lỗi API | 401 từ ExBot Lambda | Kiểm tra HMAC Lambda Authorizer | UC §2 |
| Không tìm thấy bản ghi bot cho `botId` | Lỗi API | 404 Not Found — "No active bot found for this account." | E-EXBOT-023 | UC §4 A4, `srs/spec.md` §5 |
| Bot ở trạng thái `lp_closing` | Response API (200) | "Bot close is in progress. Please wait." | E-EXBOT-021 | UC §4 A3a, `srs/spec.md` §5 |
| Bot ở trạng thái `closed` | Response API (200) | "Bot safely closed. Funds have been returned to your wallet." | E-EXBOT-022 | UC §4 A3b, `srs/spec.md` §5 |
| Bot ở trạng thái `error` | Response API (200) | "Bot encountered a critical error. Admin intervention required. You may close the bot via emergency close." | E-EXBOT-029 | UC §4 A7, `srs/spec.md` §5 |
| Bot ở trạng thái `paused` | Response API (200) | "Bot Paused. Hedge and LP are maintained. You may still redeem." | E-EXBOT-031 | UC §4 A10, `srs/spec.md` §5 (chưa có trong `message-list.md` — xem V-010) |
| Lỗi cơ sở hạ tầng Operator Facade | Response ở tầng infra | 503 Service Unavailable — "Status service temporarily unavailable" | Không có E-EXBOT code (tầng infra) | UC §4 A5 |
| Pool Slot0 Cache unavailable hoặc stale | Null field-level trong response 200 | `current_tick: null`, `range_state: null`; các trường khác bình thường | Không có mã lỗi | UC §4 A8, FR-EXBOT-093 |

#### D. Bảng kiểm kê thực thể và field (§F.1 Inventory)

| # | Field trong JSON response | Kiểu | Nguồn cột trong Aurora PG / Cache / Env | Trạng thái | Ghi chú | Nguồn |
|---|---|---|---|---|---|---|
| 1 | `bot_id` | string | `bots.id` (UUID PK) | Implemented | Alias của `bots.id`, xác nhận bởi BA (V-006 Answered) | `srs/erd.md`, V-006 |
| 2 | `status` | string | `bots.status` | Implemented | Coarse status: `active`, `paused`, `error`, `safe_mode`, `closed` | `srs/erd.md`, `srs/states.md` |
| 3 | `lifecycle_state` | string | `bots.lifecycle_state` | Implemented | Trạng thái canonical theo `srs/states.md` | `srs/states.md`, FR-EXBOT-003 |
| 4 | `runtime_health_status` | string | `bot_runtime_state.runtime_health_status` | Implemented | v5 ghi nhận conflict với ERD (cột cũ là `health_status`); ERD đã được dev sửa 2026-07-20 để khớp UC. Về mặt tài liệu, BA answer chính thức vẫn Open (V-001) — xem §10.1 | `srs/erd.md` (đã sửa 2026-07-20), V-001 |
| 5 | `last_reconcile_at` | string\|null | `bot_runtime_state.last_hl_reconcile_at` (JSON field bỏ tiền tố `hl_` khi expose ra API — chủ đích, không phải lỗi) | Implemented | **v1 gap:** mapping từ DB sang response chưa cài đặt, luôn trả về `null`; sẽ mở khóa ở v1.1 khi `getRuntimeState` hoàn thiện | `srs/erd.md`, V-002 Answered |
| 6 | `last_error_code` | string\|null | `bot_runtime_state.last_error_code` | Implemented | **v1 gap:** cột chưa tồn tại trong schema; `getRuntimeState` hardcode `null`; sẽ được bổ sung ở v1.1, ghi bởi `upsertRuntimeState` | UC §3 step 3, V-007 Answered |
| 7 | `safe_mode_tier` | string\|null | `bot_runtime_state.safe_mode_tier` (cột đã thêm vào ERD 2026-07-20; enum `warning`\|`restricted`\|`frozen`) | Implemented | **v1 gap:** cột schema DB chưa tồn tại thực tế trong v1, luôn trả về `null`; `restricted`/`frozen` set bởi `enterSafeMode()`, `warning` chưa có điều kiện kích hoạt nào trong v1 | `srs/erd.md`, V-003 Answered |
| 8 | `dry_run` | boolean | Biến môi trường `EXBOT_DRY_RUN` (không phải cột DB) | Implemented | Không cần thêm vào ERD vì không phải dữ liệu lưu trữ; short-circuit mọi lệnh gọi Hyperliquid khi `true` | V-004 Answered |
| 9 | `tick_lower` | number\|null | `positions.tick_lower` | Pending | Mapping đúng tên cột | `srs/erd.md` |
| 10 | `tick_upper` | number\|null | `positions.tick_upper` | Pending | Mapping đúng tên cột | `srs/erd.md` |
| 11 | `current_tick` | number\|null | Pool Slot0 Cache (ElastiCache Redis) | Pending | Null khi cache unavailable/stale (A8); không phải cột Aurora PG | FR-EXBOT-093 |
| 12 | `range_state` | `"in"`\|`"out"`\|null | Giá trị dẫn xuất | Pending | Tính từ `tickLower <= currentTick < tickUpper`; null khi `current_tick = null` | UC §3 step 5 |
| 13 | `actual_short_eth` | string\|null | `bot_runtime_state.last_known_hl_short_size` | Pending | BigDecimal serialized as string per NFR-EXBOT-008 | `srs/erd.md`, FR-EXBOT-021 |
| 14 | `target_short_eth` | string\|null | Giá trị dẫn xuất | Pending | `lp_eth_amount × (target_ratio_bps / 10000)` per FR-EXBOT-021; BigDecimal | FR-EXBOT-021 |
| 15 | `drift_pct` | number\|null | Giá trị dẫn xuất | Pending | Null khi `lp_eth_amount = 0` hoặc null; BigDecimal per NFR-EXBOT-008 | FR-EXBOT-021, NFR-EXBOT-008 |
| 16 | `margin_status` | string\|null | `hedge_legs.margin_status` | Pending | `ok` / `warning` / `critical`; chỉ cập nhật tại hedge-sync preflight + deep-audit (FR-EXBOT-060) | FR-EXBOT-060, `srs/erd.md` |
| 17 | `last_light_check_at` | string\|null | `bot_runtime_state.last_light_check_at` | Pending | Mapping đúng — cột tồn tại trong ERD | `srs/erd.md` |
| 18 | `safe_mode_reason` | string\|null | `bot_runtime_state.safe_mode_reason` (v1 gap — cột chưa tồn tại) | Pending | **v1 gap:** luôn `null` cho đến v1.1 | `srs/erd.md`, V-005 Answered |
| 19 | `cooldown_end_at` | string\|null | `bot_runtime_state.cooldown_end_at` (v1 gap — cột chưa tồn tại) | Pending | **v1 gap:** luôn `null` cho đến v1.1 | `srs/erd.md`, V-005 Answered |

**Ghi chú tổng hợp về v1 gap:** trong 8 field "Implemented" (dòng 1–8), có 5 field luôn trả về `null` trong v1 (`last_reconcile_at`, `last_error_code`, `safe_mode_tier`, và hai Pending field `safe_mode_reason`/`cooldown_end_at`) — chỉ `bot_id`, `status`, `lifecycle_state`, `runtime_health_status`, `dry_run` có giá trị thực trong v1. Tester cần thiết kế assertion `=== null` riêng cho các field v1 gap, không kỳ vọng giá trị thực cho đến v1.1.

---

## 7. Phân tích liên kết (Integration Analysis)

| Hệ thống liên kết | Loại tích hợp | Dữ liệu đọc/ghi | Điều kiện phụ thuộc | Rủi ro test | Nguồn |
|---|---|---|---|---|---|
| Aurora PostgreSQL (`state_db_shard`) | Database read | Đọc: `bots`, `positions`, `hedge_legs`, `bot_runtime_state` | Kết nối Aurora PG phải sẵn sàng; nếu unavailable → lỗi hệ thống không được định nghĩa trong UC | Test cần cài sẵn dữ liệu fixture đầy đủ 4 bảng; thiếu row ở bất kỳ bảng nào sẽ gây lỗi join | UC §3, `srs/erd.md` |
| Pool Slot0 Cache (ElastiCache Redis) | Cache read | Đọc: `currentTick` | Nếu unavailable hoặc stale → `current_tick: null`, `range_state: null`; không block response | Test phải bao phủ cả 2 trường hợp: cache có giá trị và cache null | UC §4 A8, FR-EXBOT-093 |
| HMAC Lambda Authorizer (API Gateway) | Auth check | Xác thực chữ ký HMAC | Chữ ký không hợp lệ/thiếu → 401; test cần secret key đúng để tạo test request hợp lệ | Test cần secret key hoặc mock authorizer; không thể test trực tiếp mà không có credential | UC §2, FR-EXBOT-090 |
| Operator Facade | API Gateway / passthrough | Chuyển tiếp `X-Wallet-Address`; kiểm tra caller block/whitelist | Operator Facade phải khả dụng; 503 khi unavailable (tầng infra) | Test end-to-end cần Facade thật; unit test ExBot Lambda có thể dùng mock | UC §1, FR-EXBOT-090 |
| isAdmin guard (nội bộ ExBot Lambda) | In-process check | Không đọc/ghi dữ liệu; chỉ kiểm tra role của caller | Guard chạy trước bất kỳ Aurora PG/Cache read nào | **Rủi ro cao:** mọi test scenario theo actor Investor (bao gồm happy path, A1–A10 phía Investor) đều bị chặn ở tầng này trong v1 — không phản ánh đúng luồng nghiệp vụ dự kiến cuối cùng, chỉ có thể verify hành vi 403; test coverage đầy đủ cho Investor phải chờ v1.1 | UC §2 (changelog 2026-07-20) |
| Hyperliquid (on-chain) | Gián tiếp | Dữ liệu LP position (`tickLower`, `tickUpper`) và hedge size (`last_known_hl_short_size`) được phản ánh vào Aurora PG sau mỗi light-check/hedge-sync | Dữ liệu có thể stale nếu light-check chưa chạy gần đây | Test cần dữ liệu Aurora PG fixture phản ánh trạng thái on-chain mong muốn; không gọi trực tiếp Hyperliquid trong UC này | `srs/erd.md`, FR-EXBOT-050 |

**Ghi chú về kiểm kê phụ thuộc on-chain (Blockchain Checklist §6b):**

UC này chạm vào dữ liệu liên quan đến on-chain LP position và HL agent key nhưng không thực hiện giao dịch on-chain trực tiếp trong luồng truy vấn status. Rủi ro test: dữ liệu Aurora PG có thể stale so với trạng thái on-chain thực tế. Test acceptance nên chỉ định rõ trạng thái fixture Aurora PG thay vì phụ thuộc vào dữ liệu on-chain live.

---

## 8. Acceptance Criteria candidates (§F.5)

| ID | User Story | Điều kiện Given | When | Then | Loại | Ghi chú |
|---|---|---|---|---|---|---|
| AC-ms-01 | US-EXBOT-002 AC-EXBOT-002-1 | Bot ở trạng thái `active`; `lp_eth_amount > 0`; Pool Slot0 Cache có `currentTick`; `currentTick` nằm trong `[tickLower, tickUpper)`; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `lifecycle_state='active'`; `range_state='in'`; `drift_pct` là số thập phân dương; các field v1 gap (`last_reconcile_at`, `last_error_code`, `safe_mode_tier`, `safe_mode_reason`, `cooldown_end_at`) = `null` | Happy path | **Cập nhật so với v5:** happy path chỉ thực thi được với actor Admin trong v1, không phải Investor như US-EXBOT-002 mô tả (isAdmin guard) |
| AC-ms-01b | Suy luận cần xác nhận | Bot ở trạng thái `active`; caller là Investor có `wallet_address` khớp `bot.user_wallet_address` | Investor gọi `GET /api/exbot/status/{botId}` | 403 Forbidden do isAdmin guard — **không phải** 200 như US-EXBOT-002 AC-EXBOT-002-1 mô tả | Gap giữa US và v1 gap (v1) | Mới thêm ở v6; xem V-009 |
| AC-ms-02 | US-EXBOT-002 AC-EXBOT-002-2 | Bot ở trạng thái `safe_mode`; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `status='safe_mode'`; `safe_mode_reason` = `null` (v1 gap, cột chưa tồn tại) | Alternate A1 | Cập nhật: `safe_mode_reason` luôn `null` trong v1 (V-005 Answered), không có giá trị thật như v5 giả định |
| AC-ms-03 | US-EXBOT-002 AC-EXBOT-002-3 | Bot ở trạng thái `hedge_stopped_cooldown`; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `lifecycle_state='hedge_stopped_cooldown'`; `cooldown_end_at` = `null` (v1 gap, cột chưa tồn tại) | Alternate A2 | Cập nhật: `cooldown_end_at` luôn `null` trong v1 (V-005 Answered) |
| AC-ms-04 | Suy luận cần xác nhận | Pool Slot0 Cache không khả dụng; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `current_tick: null`; `range_state: null`; tất cả trường khác bình thường | Alternate A8 | Từ UC §4 A8 + FR-EXBOT-093 |
| AC-ms-05 | Suy luận cần xác nhận | Admin gọi API thay mặt Investor với `wallet_address` không khớp bot (theo lý thuyết) | Admin/Investor gọi `GET /api/exbot/status/{botId}` | Về lý thuyết: 403 E-EXBOT-030; **thực tế trong v1:** nếu caller là Investor, request đã bị 403 isAdmin guard chặn trước khi tới bước kiểm tra ownership — không thể phân biệt hai loại 403 bằng test case ở tầng API trong v1 | Error A9 (Blocked bởi v1 gap) | Cập nhật so với v5: đã xác nhận thứ tự guard (isAdmin trước wallet-match); xem V-009 |
| AC-ms-06 | Suy luận cần xác nhận | Không có bản ghi bot nào trong Aurora PG cho `botId`; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 404 Not Found; body chứa E-EXBOT-023 "No active bot found for this account." | Error A4 | UC §4 A4 |
| AC-ms-07 | Suy luận cần xác nhận | `lp_eth_amount = 0` trong `bot_runtime_state`; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `drift_pct: null` (không phải 0 hay lỗi) | Edge case drift | FR-EXBOT-021 division-by-zero guard |
| AC-ms-08 | US §4 A10 | Bot ở trạng thái `paused` (`bots.status='paused'`); caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `status='paused'`; `lifecycle_state` giữ giá trị trước pause; message E-EXBOT-031 | Alternate A10 | **Đã đóng V-008** (v5); cập nhật v6: `E-EXBOT-031` chưa có trong `message-list.md` mirror (V-010); test theo Investor bị Blocked bởi isAdmin guard |
| AC-ms-09 | Suy luận cần xác nhận | Admin gọi với `wallet_address` khác chủ sở hữu bot | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK (bypass ownership check); response đầy đủ | Admin bypass | UC §2 |
| AC-ms-10 | Suy luận cần xác nhận | Bot `closed`; bản ghi còn trong Aurora PG; caller có quyền Admin | Admin gọi `GET /api/exbot/status/{botId}` | 200 OK; `lifecycle_state='closed'`; E-EXBOT-022 message | Alternate A3b | UC §4 A3b |

---

## 9. Yêu cầu phi chức năng liên quan

| NFR ID | Nội dung yêu cầu | Áp dụng trong UC này như thế nào | Ghi chú kiểm thử |
|---|---|---|---|
| NFR-EXBOT-008 | Tất cả tính toán tài chính phải dùng BigDecimal; cấm dùng float/number cho giá trị tài chính | `drift_pct`, `target_short_eth`, `actual_short_eth` phải dùng BigDecimal; `target_ratio_bps` phải qua `normalizeTargetRatioBps()` | Test cần kiểm chứng giá trị trả về là string (BigDecimal serialized), không phải float JS |
| NFR-EXBOT-001 | Latency của Lambda response phải nằm trong giới hạn acceptable dưới tải bình thường | `GET /api/exbot/status/{botId}` phải đáp ứng SLA latency ngay cả khi multi-table join Aurora PG + Cache query | Test hiệu năng cần thiết kế riêng; không block test design nhưng cần đề xuất cho QC Lead |
| NFR-EXBOT-003 (suy luận) | Bí mật API Gateway (HMAC key) không được lộ trong log | HMAC key dùng để ký request từ Facade → Lambda | Test bảo mật: kiểm tra không có HMAC key trong CloudWatch logs |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Issue Register

| Issue ID | Loại | Mức độ | Vùng ảnh hưởng | Source trace | Phát hiện | Tác động với tester | Đề xuất câu hỏi / sửa | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| V-001 | CROSS_SOURCE_CONFLICT | Major | §F.1 Inventory, §F.2 Validation | UC §3 step 7 dùng field JSON `runtime_health_status`; `srs/erd.md` **trước 2026-07-20** định nghĩa cột là `health_status` | UC dùng tên field `runtime_health_status`; ERD trước đây ghi tên cột khác. Changelog `srs/erd.md` ngày 2026-07-20 cho thấy dev đã tự sửa tên cột ERD thành `runtime_health_status` để khớp UC (xác nhận qua code `runtime-state.ts` + `get-bot-status` handler). Tuy nhiên, trong file câu hỏi (`..._questions_20260715_v4.md`), câu trả lời chính thức của BA cho câu hỏi này chỉ lặp lại nguyên văn nội dung câu hỏi — chưa phải một xác nhận thực sự bằng lời của BA. | Về mặt kỹ thuật, cột ERD hiện đã khớp tên field JSON nên tester có thể tạm dùng `runtime_health_status` cho cả hai phía khi viết fixture và assertion. Nhưng vì chưa có xác nhận chính thức bằng lời từ BA, chưa nên coi đây là "closed" chính thức trên hồ sơ audit. | BA xác nhận lại bằng một câu trả lời thực sự (không phải lặp lại câu hỏi): tên field JSON và tên cột ERD hiện tại là `runtime_health_status` ở cả hai phía, và việc sửa ERD ngày 2026-07-20 là quyết định cuối cùng. | Open (bằng chứng kỹ thuật đã đủ, nhưng cần BA xác nhận chính thức cho hồ sơ) |
| V-002 | CROSS_SOURCE_CONFLICT | — | §F.1 Inventory | UC §3 step 7 `last_reconcile_at` vs ERD `last_hl_reconcile_at` | BA xác nhận: khác tên có chủ đích (tiền tố `hl_` bị bỏ khi expose ra API); tester dùng `last_reconcile_at`. Trong v1, trường này luôn trả về `null` (mapping DB → response chưa cài đặt; mở khóa ở v1.1). | Đã rõ — tester chỉ cần thêm assertion `=== null` cho v1. | — | Resolved (Answered — @hienduong, 2026-07-20) |
| V-003 | MISSING_INFO | — | §F.1 Inventory, §F.2 Validation | UC §3 step 7 `safe_mode_tier` vs `srs/erd.md` | BA xác nhận nguồn: `bot_runtime_state.safe_mode_tier` (cột đã thêm vào ERD 2026-07-20); enum `warning`/`restricted`/`frozen`; điều kiện kích hoạt `restricted`/`frozen` đã định nghĩa qua `enterSafeMode()`, `warning` chưa có điều kiện trong v1. Trong v1, field luôn `null` (cột DB thực tế chưa tồn tại). | Test theo từng tier chỉ thiết kế và thực thi được từ v1.1. | — | Resolved (Answered — @hienduong, 2026-07-20) |
| V-004 | MISSING_INFO | — | §F.1 Inventory | UC §3 step 7 `dry_run` vs `srs/erd.md` | BA xác nhận: không phải cột DB, đọc từ biến môi trường `EXBOT_DRY_RUN`; boolean; khi `true` mọi lệnh gọi Hyperliquid bị short-circuit. | Test cần set biến môi trường thay vì fixture DB. | — | Resolved (Answered — @hienduong, 2026-07-20) |
| V-005 | UNCLEAR_INFO | — | §F.1 Inventory | UC §3 step 7 `safe_mode_reason`, `cooldown_end_at` vs `srs/erd.md` | BA xác nhận cả hai đúng là Pending fields, nguồn dự kiến là `bot_runtime_state.safe_mode_reason` / `bot_runtime_state.cooldown_end_at` — cả hai là v1 gap, cột chưa tồn tại, luôn `null` trong v1. | Test cần assertion `=== null`, không phải `undefined`, cho đến v1.1. | — | Resolved (Answered — @hienduong, 2026-07-20) |
| V-006 | UNCLEAR_INFO | — | §F.1 Inventory | UC §3 step 7 `bot_id` vs `srs/erd.md` `bots.id` | BA xác nhận `bot_id` = alias của `bots.id`. | Fixture: set `bots.id = "xxx"` → `bot_id` trong response phải là `"xxx"`. | — | Resolved (Answered — @hienduong, 2026-07-20) |
| V-007 | MISSING_INFO | — | §F.1 Inventory, §F.2 Validation | UC §3 step 3 reads list vs `last_error_code` trong step 7 schema | BA xác nhận nguồn: `bot_runtime_state.last_error_code`; v1 gap — cột chưa tồn tại, hardcode `null`. UC đã được cập nhật để thêm field này vào danh sách reads ở step 3 kèm chú thích v1 gap. | Test chỉ cần assertion `=== null` cho v1. | — | Resolved (Answered — @hienduong, 2026-07-20; và tự cập nhật vào UC) |
| V-008 | MISSING_INFO | — | §F.3 Functional Logic | `srs/states.md` State Registry có trạng thái `active (pre-pause)` (`bots.status='paused'`) vs UC §4 Alternate Flows (v5: chưa có flow cho `paused`) | UC đã được cập nhật thêm Alternate Flow A10: `status='paused'` → 200, `lifecycle_state` giữ giá trị trước pause, message E-EXBOT-031, `user_redeem` vẫn được phép. BA answer bổ sung ghi chú: A10 chỉ kiểm thử đầy đủ được cho Investor sau khi isAdmin guard được gỡ (liên hệ trực tiếp đến V-009). | AC-ms-08 đã có thể thiết kế cho actor Admin; actor Investor phải đánh dấu Blocked. | — | Resolved (Answered — @hienduong, 2026-07-20; UC cập nhật A10 ngày 2026-07-20/21) |
| V-009 | CROSS_SOURCE_CONFLICT | Major | §F.3 Functional Logic (actor/permission behavior), §2 Actor | UC §2 Preconditions (cập nhật 2026-07-20): "ExBot Lambda has a hard `isAdmin` guard — non-Admin callers (Investor) receive 403 before any business logic runs" — mâu thuẫn trực tiếp với `userstories/us-002.md` (không đổi từ 2026-07-04), nơi cả 3 Acceptance Criteria (AC-EXBOT-002-1/2/3) đều viết "Given the investor has an ExBot..." và mong đợi màn hình status hiển thị thành công (200) | UC (nguồn mới nhất, 2026-07-20) nói rõ Investor — actor Primary của UC này — nhận 403 ngay lập tức trong v1, không tới được business logic. Nhưng US-EXBOT-002, vẫn đang mô tả 3 acceptance criteria với Given là Investor xem thành công màn hình status, không có ghi chú nào về v1 gap này. Đây là mâu thuẫn trực tiếp giữa UC và US chưa được đối soát: US mô tả hành vi của v1.1 (hoặc target hoàn chỉnh), UC mô tả đúng hành vi hiện tại của v1. | Tester đọc riêng US-EXBOT-002 sẽ thiết kế test case AC-EXBOT-002-1/2/3 dưới actor Investor và kỳ vọng response 200 — nhưng test case đó sẽ **luôn fail** trong v1 vì bị 403 isAdmin guard. Nếu không có ghi chú rõ ràng, tester dễ báo nhầm đây là bug thay vì hành vi có chủ đích của v1. | BA xác nhận: (a) US-EXBOT-002 cần thêm ghi chú "v1 gap — chỉ Admin verify được trong v1, Investor path chờ v1.1" vào cả 3 AC; (b) xác nhận lại phạm vi release: happy path/AC-EXBOT-002-1/2/3 có được coi là "Done" cho v1 khi chỉ verify bằng Admin không. | Open |
| V-010 | INTERNAL_INCONSISTENCY | Minor | §F.1 Inventory, §6.C Messages | UC §4 A9 cite E-EXBOT-030, A10 cite E-EXBOT-031; `02_backbone/message-list.md` bảng EXBOT mirror dừng ở E-EXBOT-029, chưa có 2 mã này | Cả hai mã E-EXBOT-030 và E-EXBOT-031 **đã có nội dung verbatim đầy đủ trong nguồn canonical** `srs/spec.md` §5 (dòng 582–583), nên tester vẫn lấy được message text chính xác để viết assertion. Vấn đề chỉ là bảng mirror trong `message-list.md` (dùng để tra cứu nhanh, tự khai là không phải nguồn canonical) chưa được đồng bộ — không phải BLOCKED_EVIDENCE. | Không block test design vì nguồn canonical đã đủ; chỉ gây bất tiện nhỏ nếu tester quen tra `message-list.md` trước. | BA/Tech Lead đồng bộ bảng mirror `message-list.md` — thêm dòng E-EXBOT-030 và E-EXBOT-031 (copy verbatim từ `spec.md` §5); dọn luôn dòng "Symbol not found" đặt lạc trong section EXBOT (thuộc bnza-ex, không phải EXBOT). | Open |
| V-011 | INTERNAL_INCONSISTENCY | Minor | §0 Artefact metadata | `userstories/us-002.md` §Notes: "ExBot Lambda returns status data via Operator Facade `/api/exbot/status`" — không có `{botId}`; UC đã đổi endpoint thành `/api/exbot/status/{botId}` từ 2026-07-20 | US-002 chưa được cập nhật theo thay đổi endpoint path của UC. Không ảnh hưởng logic nghiệp vụ, chỉ là chi tiết kỹ thuật của endpoint. | Rủi ro thấp: tester đọc US trước UC có thể dùng sai endpoint path khi viết test request mẫu, nhưng UC (nguồn chính) đã đúng. | BA cập nhật `us-002.md` §Notes cho khớp endpoint path hiện tại (tùy chọn, không block). | Open |
| V-012 | MISSING_INFO | Minor | §6.C Messages | UC §2 Preconditions v1 gap note không định nghĩa nội dung message body cụ thể cho trường hợp 403 do isAdmin guard | UC chỉ nói "receive 403" nhưng không có message text hoặc E-EXBOT code cho response body của lỗi này — khác với các lỗi 403 khác trong UC (đều có E-EXBOT code đi kèm). | Tác động thấp trong thực tế vì actor Investor không thể test được path này một cách hợp lệ (đây chính là hành vi bị chặn); nhưng nếu QA cần verify response body chính xác (không chỉ status code), thông tin này còn thiếu. | BA xác nhận: response body của lỗi 403 isAdmin guard có message text cụ thể không, hay chỉ là 403 trống/generic. | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| D1 | v1.1 rollout: bổ sung cột `bot_runtime_state.safe_mode_tier` (thực tế), `last_hl_reconcile_at` mapping, `last_error_code`, `safe_mode_reason`, `cooldown_end_at` | Data / Backend | Đến khi hoàn tất, 5 field Implemented/Pending luôn `null` — test theo giá trị thật của các field này phải hoãn sang v1.1 | Chờ v1.1 |
| D2 | Gỡ bỏ isAdmin guard trong ExBot Lambda để mở đường xử lý Investor | Backend / Architecture | Toàn bộ scenario Investor (happy path, A1–A10 dưới góc nhìn Investor) không thể test đầy đủ đến khi gỡ guard này | Chờ v1.1 (liên hệ V-009) |
| D3 | BA xác nhận lại chính thức (không lặp câu hỏi) cho V-001 | UC / Question backlog | Chưa có xác nhận bằng lời chính thức, dù bằng chứng ERD đã đủ mạnh | Chờ BA xác nhận |
| D4 | Đồng bộ `message-list.md` mirror với `spec.md` §5 (thêm E-EXBOT-030/031, dọn dòng lạc "Symbol not found") | BA / Tech Lead | Không block, chỉ gây bất tiện tra cứu | Chờ BA/Tech Lead update |
| D5 | Cập nhật `us-002.md` để phản ánh v1 gap isAdmin guard trong AC | BA / US update | Nếu không cập nhật, tester dựa vào US một cách máy móc sẽ thiết kế test case luôn fail trong v1 | Chờ BA update |

### 10.3 Audit Summary

#### Bảng điểm

| Vùng đánh giá | Điểm tối đa | Điểm đạt | Ghi chú |
|---|---|---|---|
| 1. Function/Operation & Data Object Inventory | 20 | 18 | Inventory đầy đủ 19 field + isAdmin guard được ghi nhận như một precondition; A1–A10 đầy đủ; trừ điểm nhẹ cho message-list.md mirror thiếu E-EXBOT-030/031 (V-010) và thiếu message body cho lỗi isAdmin guard (V-012) |
| 2. Data Object/State Attributes, BR, Validations & Messages | 25 | 23 | 7/8 vấn đề Major/Minor của v5 (V-002 đến V-008) đã được BA trả lời đầy đủ và có nguồn cột rõ ràng; V-001 còn thiếu xác nhận chính thức (trừ điểm nhẹ); BR-EXBOT-007 đã sửa lại nguồn trích dẫn đúng (`spec.md` §4) |
| 3. Functional Logic & Workflow Decomposition | 25 | 17 | **Capped 70% (17/25) theo scoring-rubric §8** — do mâu thuẫn chưa giải quyết giữa UC (isAdmin guard chặn Investor) và US-EXBOT-002 (AC viết cho Investor, kỳ vọng 200) làm thay đổi hành vi mong đợi cho actor chính của UC (V-009) |
| 4. Functional Integration & Data Consistency | 15 | 14 | Aurora PG 4-bảng, Pool Slot0 Cache null-path, HMAC hai lớp đều rõ ràng; isAdmin guard được mô tả đúng vị trí trong luồng xử lý (trước bước đọc DB) |
| 5. UC/Spec Documentation Quality Issues | 15 | 8 | **Capped 8/15 theo scoring-rubric §8** — cùng lý do V-009 (mâu thuẫn chưa giải quyết giữa UC và US thay đổi hành vi mong đợi) |
| **Tổng** | **100** | **80** | |

#### Verdict: CONDITIONALLY READY

**Điều kiện để chuyển sang READY:**

1. **[Blocker cần giải quyết trước khi thiết kế test case cho actor Investor — Major]** BA xác nhận và cập nhật `us-002.md` để phản ánh v1 gap isAdmin guard: cả 3 AC (AC-EXBOT-002-1/2/3) hiện viết cho actor Investor nhưng thực tế trong v1 chỉ Admin verify được (V-009). Cho đến khi có xác nhận, mọi test case theo actor Investor phải đánh dấu "Blocked — chờ v1.1", chỉ test case theo actor Admin được thực thi ngay.
2. **[Recommended — Major với bằng chứng kỹ thuật đã đủ]** BA xác nhận lại chính thức tên field/cột cho `runtime_health_status` (V-001) — bằng chứng ERD hiện tại đã đủ mạnh để tạm coi là resolved về mặt kỹ thuật, nhưng hồ sơ audit cần một câu trả lời thực sự thay vì lặp lại câu hỏi.
3. **[Recommended — Minor]** BA/Tech Lead đồng bộ bảng mirror `message-list.md` với `spec.md` §5 (V-010) và cập nhật `us-002.md` endpoint path (V-011).
4. **[Recommended — Minor]** BA xác nhận nội dung response body cho lỗi 403 do isAdmin guard (V-012).

**Nhận xét tổng thể:** v6 là một bước tiến rõ rệt so với v5 (85/100) về mặt trả lời câu hỏi — 7/8 issues cũ (V-002 đến V-008) đã được BA giải quyết đầy đủ và UC đã tự cập nhật để phản ánh phần lớn các câu trả lời đó. Tuy nhiên, điểm tổng giảm nhẹ xuống 80/100 vì kỳ audit này phát hiện một vấn đề mới có tác động lớn hơn tổng hợp các vấn đề cũ: **isAdmin guard trong v1 chặn toàn bộ business logic cho actor Investor — actor Primary của UC này** — và vấn đề này tạo ra mâu thuẫn trực tiếp, chưa giải quyết, với Acceptance Criteria hiện tại của US-EXBOT-002 (V-009). Đây là điểm quan trọng nhất QC Lead và BA cần thống nhất trước khi giao cho tester thiết kế test case: phạm vi test v1 thực tế chỉ bao phủ actor Admin; toàn bộ nghiệp vụ dành cho Investor (đúng như mục tiêu ban đầu của UC) phải chờ v1.1 gỡ isAdmin guard.

---

## 11. Changelog

| Version | Ngày | Nội dung thay đổi | Tác giả |
|---|---|---|---|
| v1 | 2026-06-30 | Audit đầu tiên | QC UC Read Agent |
| v2 | 2026-07-01 | Cập nhật sau khi đọc thêm us-002.md và message-list.md; bổ sung vào Question backlog | QC UC Read Agent |
| v3 | 2026-07-03 | Cập nhật sau BA answers qc-responses-2026-07-03.md; điểm 78/100 | QC UC Read Agent |
| v4 | 2026-07-06 | Re-audit sau UC update 2026-07-04; phát hiện N-001/N-002/N-003; điểm 82/100 CONDITIONALLY READY | QC UC Read Agent |
| v5 | 2026-07-15 | Re-audit đầy đủ sau UC update 2026-07-14 (giải quyết I-003/N-001/N-002/N-003). Cross-check SRS/ERD phát hiện 8 issues mới (V-001 đến V-008). Điểm 85/100 CONDITIONALLY READY | QC UC Read Agent |
| v6 | 2026-07-22 | Re-audit sau BA answers `qc-responses-2026-07-20.md` (đóng V-002 đến V-008) và UC update 2026-07-20/21 (endpoint `/{botId}`, isAdmin guard v1 gap, A10 `paused` + E-EXBOT-031). Phát hiện vấn đề mới có tác động lớn: isAdmin guard chặn toàn bộ actor Investor trong v1, mâu thuẫn với AC của US-EXBOT-002 (V-009); cùng 3 issue Minor mới (V-010, V-011, V-012). Điểm 80/100 CONDITIONALLY READY (giảm nhẹ so với v5 do V-009 bị cap theo scoring-rubric) | QC UC Read Agent |

---

*Báo cáo audited UC readiness — v6*
