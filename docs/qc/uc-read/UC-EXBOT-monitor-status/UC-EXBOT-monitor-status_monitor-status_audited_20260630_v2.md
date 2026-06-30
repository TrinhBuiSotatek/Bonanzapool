# Báo Cáo Rà Soát Mức Độ Sẵn Sàng Use Case — UC-EXBOT-monitor-status

**Tiêu đề tài liệu:** Rà Soát UC — Xem Trạng Thái ExBot Đang Hoạt Động  
**Ngày tạo:** 2026-06-30  
**Tác giả / Agent:** QC UC Read ExBot Agent (`qc-uc-read-exbot`)  
**Phiên bản:** v2 (bản dịch tiếng Việt của v1)

---

## Tóm Tắt Nghiệp Vụ (Feature Brief)

UC-EXBOT-monitor-status mô tả luồng truy vấn chỉ-đọc cho phép nhà đầu tư USDC đã xác thực theo dõi tình trạng thực tế của ExBot đang chạy của mình. Toàn bộ luồng là backend: POOL UI gọi `GET /api/exbot/status` lên Operator Facade, Facade chuyển tiếp yêu cầu đến ExBot Worker qua service binding của Cloudflare. ExBot Worker đọc nhiều bảng D1 (bots, positions, hedge_legs, bot_runtime_state), truy vấn tick hiện tại từ `MarketDataDO`, tính toán hai giá trị dẫn xuất (rangeState và drift %) rồi trả về payload JSON tổng hợp. Không có thay đổi dữ liệu nào xảy ra trong luồng này; mọi thao tác ghi đều bằng không.

Từ góc độ kiểm thử, UC này đáng chú ý vì response trạng thái tổng hợp dữ liệu từ bốn bảng D1 cộng với một truy vấn Durable Object trực tiếp, trả về các nhãn lifecycle state để điều khiển trạng thái hiển thị trên UI, và là bề mặt quan sát chính cho nhà đầu tư và operator. Tính đúng đắn của nhãn trạng thái và các giá trị dẫn xuất (drift %, rangeState) quyết định việc các nút hành động ở POOL UI (đóng khẩn cấp, rebalance) có được kích hoạt hay không.

Hai điểm kiểm tra chéo quan trọng: (1) giá trị lifecycle state trong response phải khớp với máy trạng thái 18 trạng thái trong `srs/states.md`, và (2) drift % phải dùng `last_known_hl_short_size` so với target, đòi hỏi một trường D1 cụ thể mà UC bỏ sót trong danh sách đọc. Một alternate flow (A3) tham chiếu lifecycle state (`cooldown`) đã bị xóa trong HLD 2026-06-18, khiến mô tả flow đó không còn phản ánh thực tế và không thể kiểm thử được.

---

## Bảng Mã Viết Tắt

| Mã / Tiền tố | Ý nghĩa + Vai trò trong dự án này | Định nghĩa tại |
|---|---|---|
| FR-EXBOT-* | Functional Requirement của module ExBot — các yêu cầu đánh số định nghĩa hành vi bot, API contract và quy tắc máy trạng thái | `srs/spec.md` (canonical) và `frd.md` (lưu ý: cùng số FR có nội dung khác nhau ở hai tài liệu — xem I-007, I-014) |
| BR-EXBOT-* | Business Rule của ExBot — các bất biến tuyệt đối không được vi phạm trong code hay tài liệu (ví dụ: SAFE_MODE không bao giờ là trạng thái kết thúc, chỉ điều chỉnh delta hedge, light-check HL weight = 0) | `srs/spec.md` §4 và `02_backbone/common-rules.md` |
| E-EXBOT-* | Mã lỗi cấp API do ExBot Worker trả về qua Operator Facade — nguồn chính thức cho nội dung thông báo lỗi và HTTP status code | `02_backbone/message-list.md` phần EXBOT |
| US-EXBOT-* | User Story của ExBot — acceptance criteria theo dạng Given/When/Then từ góc nhìn Investor hoặc Operator | `userstories/us-*.md` |
| UC-EXBOT-* | Use Case của ExBot — mô tả hành vi hệ thống ở cấp kịch bản, bao gồm actor, flow và FR trace | `usecases/uc-*.md` |
| OQ-EXBOT-* | Câu hỏi mở của ExBot — câu hỏi kỹ thuật hoặc nghiệp vụ chưa giải quyết, ảnh hưởng đến thiết kế triển khai hoặc test | `srs/spec.md` §9 |
| D1 | Cloudflare D1 — cơ sở dữ liệu tương thích SQLite dùng để lưu trạng thái bot, vị thế, hedge leg và runtime state. Hai CSDL logic: `control_db` (global, cross-shard) và `state_db_shard_xx` (trạng thái bot theo shard) | `srs/erd.md`, SRS §1 |
| DO | Durable Object — đơn vị tính toán trạng thái của Cloudflare Workers; dùng làm khóa phân tán (UserLockDO), rate limiter (HLRateLimitDO) và cache dữ liệu thị trường (MarketDataDO) | SRS §1, `srs/spec.md` FR-EXBOT-093 |
| MarketDataDO | Durable Object cache sqrtPriceX96 và tick hiện tại từ pool Uniswap V3. Dùng trong UC này để tính rangeState | `srs/spec.md` FR-EXBOT-093 |
| SIWE | Sign-In With Ethereum — cơ chế xác thực dựa trên ví. Có thể liên quan đến luồng auth của nhà đầu tư qua POOL UI | (thuật ngữ ngành) |

---

## 0. Thông Tin Tài Liệu

| UC ID | Tên Feature / Use Case | Phiên bản | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-monitor-status | Xem Trạng Thái ExBot Đang Hoạt Động | (không có trường version trong file UC) | Draft |

| Tác giả / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-06-18 |

| Tài liệu đã đọc | Phiên bản / Ngày cập nhật | Vai trò | Ghi chú |
|---|---|---|---|
| `usecases/uc-monitor-status.md` | 2026-06-18 | UC (input chính) | Draft |
| `userstories/us-002.md` | 2026-06-18 | US liên kết với UC | Draft |
| `srs/spec.md` | 2026-06-29 | SRS baseline — nguồn chính xác | Phiên bản mới nhất |
| `srs/states.md` | 2026-06-18 (cập nhật 2026-06-29) | Máy trạng thái lifecycle | Phiên bản mới nhất — lưu ý cập nhật 2026-06-29 |
| `srs/flows.md` | 2026-06-29 | Sequence flow | Phiên bản mới nhất |
| `srs/erd.md` | 2026-06-29 | Mô hình dữ liệu D1 | Phiên bản mới nhất |
| `frd.md` | 2026-06-29 | Yêu cầu chức năng | Phiên bản mới nhất |
| `usecases/index.md` | 2026-06-29 | Danh mục UC và FR trace | Phiên bản mới nhất |
| `userstories/index.md` | — | Danh mục US | Đã kiểm tra |
| `02_backbone/common-rules.md` | 2026-06-26 | Registry BR-EXBOT-* | Phiên bản mới nhất |
| `02_backbone/message-list.md` | 2026-06-26 | Registry mã lỗi E-EXBOT-* | Phiên bản mới nhất |

---

## 1. Mục Tiêu và Phạm Vi

### 1.1 Mục Tiêu Nghiệp Vụ

Endpoint trạng thái tồn tại để nhà đầu tư USDC có thể kiểm tra bất kỳ lúc nào xem ExBot của họ có đang hoạt động đúng không, mà không cần quyền truy cập vào dashboard nội bộ. Endpoint này cũng đóng vai trò phát tín hiệu để POOL UI bật hoặc tắt các nút hành động thay đổi trạng thái (tạm dừng, đóng, đóng khẩn cấp) dựa trên lifecycle state hiện tại và tình trạng ký quỹ của bot.

### 1.2 Trong Phạm Vi

| Hạng mục / Chức năng | Mô tả | Nguồn |
|---|---|---|
| `GET /api/exbot/status` — truy vấn trạng thái chính | Operator Facade chuyển tiếp yêu cầu đến ExBot Worker; Worker đọc D1 và MarketDataDO, tính các giá trị dẫn xuất, trả về JSON tổng hợp | UC §3, SRS FR-EXBOT-090 |
| Đọc nhiều bảng D1 | Đọc `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status`, và `next_light_check_at` | UC §3 bước 3 |
| Truy vấn MarketDataDO | Lấy tick hiện tại (`currentTick`) từ `MarketDataDO` để tính rangeState | UC §3 bước 4, SRS FR-EXBOT-093 |
| Tính rangeState | So sánh `currentTick` với `tickLower`/`tickUpper` để ra kết quả in-range hoặc out-of-range | UC §3 bước 5 |
| Tính drift % | `(\|actualShortEth − targetShortEth\| / targetShortEth) × 100` | UC §3 bước 6 |
| Alternate flow | A1 (safe_mode), A2 (hedge_stopped_cooldown), A3 (cooldown — **không còn hiệu lực, xem I-001**), A4 (không có bot đang chạy — 404), A5 (Operator Facade không khả dụng — 503) | UC §4 |
| Quy tắc nghiệp vụ | BR-EXBOT-007: SAFE_MODE không bao giờ là trạng thái kết thúc | UC §Business Rules |

### 1.3 Ngoài Phạm Vi / Chưa Bao Gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến kiểm thử |
|---|---|---|
| Hiển thị POOL UI | UI thuộc phạm vi module POOL (PTL-05); module ExBot chỉ sở hữu payload API response | Không cần kiểm thử UI cho UC này |
| Các thao tác thay đổi trạng thái (tạm dừng, đóng) | Thuộc các UC riêng (UC-EXBOT-pause-resume, UC-EXBOT-bot-safe-close) | Không kiểm thử ở đây |
| Endpoint đóng bot từ phía Admin | UC riêng (UC-EXBOT-bot-safe-close, actor: Admin) | Không kiểm thử ở đây |
| Các lifecycle state: `lp_rebalancing`, `lp_closing`, `error`, `closed` (đang hoạt động) | UC không định nghĩa hành vi của status response cho các trạng thái này (xem I-005) | Khoảng trống — không thể thiết kế test case cho các trạng thái này |
| Fallback khi MarketDataDO bị stale | UC không mô tả hành vi khi cache bị stale hoặc DO không khả dụng (xem I-013) | Khoảng trống |

---

## 2. Actor, Vai Trò và Quyền Hạn

| Actor / Vai trò | Loại | Vai trò trong UC này | Quyền hạn / Giới hạn | Nguồn |
|---|---|---|---|---|
| Nhà đầu tư USDC | Chính | Khởi tạo truy vấn trạng thái qua POOL UI; nhận response chỉ-đọc | Chỉ đọc; không có khả năng thay đổi dữ liệu qua UC này | UC §1 Actors, US-EXBOT-002 |
| Operator Facade (hệ thống OPERATOR) | Hệ thống | Proxy đơn giản: chuyển tiếp `GET /api/exbot/status` đến ExBot Worker qua CF service binding với internal auth token | Không có logic nghiệp vụ; chỉ chuyển tiếp xác thực | UC §3 bước 2, SRS FR-EXBOT-090 |
| ExBot Worker | Hệ thống | Đọc bảng D1, truy vấn MarketDataDO, tính giá trị dẫn xuất, trả về JSON tổng hợp | Không thay đổi dữ liệu trong UC này | UC §3 bước 3–7, SRS FR-EXBOT-090 |
| MarketDataDO | Ngoài (Durable Object) | Cung cấp `currentTick` và `sqrtPriceX96` để tính rangeState | Chỉ đọc cache; không ghi | UC §3 bước 4, SRS FR-EXBOT-093 |

**Nhận xét về mức độ sẵn sàng của actor:** Có xung đột được ghi nhận giữa UC (actor = Nhà đầu tư USDC) và FRD FR-EXBOT-100 (actor cho `GET /api/exbot/status` = Admin). US-EXBOT-002 xác nhận rõ đây là use case của Investor. Xung đột này phải được giải quyết trước khi viết test case liên quan đến xác thực. Xem I-002.

---

## 3. Điều Kiện Trước và Kết Quả Sau

### 3.1 Điều Kiện Trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Nhà đầu tư đã xác thực (session/JWT hợp lệ) | Có | UC §2 |
| 2 | Nhà đầu tư có ExBot đang chạy (`bots.status IN ('active', 'safe_mode')` hoặc các trạng thái active liên quan) | Có (để nhận response không phải 404) | UC §2, SRS FR-EXBOT-003 |
| 3 | Dịch vụ Operator Facade đang hoạt động với CF service binding hợp lệ đến ExBot Worker | Có (để nhận response không phải 503) | UC §2 |
| 4 | ExBot Worker có quyền đọc D1 (control_db + state_db_shard) | Có | SRS §1.1, FR-EXBOT-090 |
| 5 | `MarketDataDO` có bản cache hợp lệ cho địa chỉ pool (Base hoặc Optimism) | Có (để tính rangeState) — fallback chưa định nghĩa | UC §3 bước 4, SRS FR-EXBOT-093 |

### 3.2 Kết Quả Sau Khi Hoàn Tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Truy vấn trạng thái thành công | Không ghi D1; không thay đổi trạng thái. Response payload được trả về POOL UI bao gồm `status`, `lifecycle_state`, khoảng LP range, tick hiện tại, rangeState, kích thước hedge thực tế, kích thước hedge mục tiêu, drift %, tình trạng ký quỹ và timestamp light-check. | UC §5, §3 bước 7–8 |
| Response 404 (không có bot đang chạy) | Không thay đổi trạng thái; trả về lỗi. | UC §A4 |
| Response 503 (Facade không khả dụng) | Không thay đổi trạng thái; trả về lỗi cho POOL UI. | UC §A5 |

---

## 6. Phân Rã Nghiệp Vụ và Luồng Xử Lý

### 6.1 Chức Năng: GET /api/exbot/status — Truy Vấn Trạng Thái ExBot Đang Hoạt Động

#### §F.1 — Kiểm Kê Chức Năng

**Các thao tác và trigger:**

| Hạng mục | Loại | Trigger / Input | Output | Nguồn trong D1 / SRS |
|---|---|---|---|---|
| `GET /api/exbot/status` — Operator Facade tiếp nhận | API endpoint | Yêu cầu HTTP GET từ POOL UI | Yêu cầu nội bộ chuyển tiếp đến ExBot Worker | SRS FR-EXBOT-090, UC §3 bước 1 |
| Chuyển tiếp qua CF service binding | Thao tác hệ thống | Operator Facade tiếp nhận yêu cầu | Yêu cầu được giao cho ExBot Worker kèm internal auth token | SRS FR-EXBOT-090, UC §3 bước 2 |
| Đọc `bots.status` | Đọc D1 | ExBot Worker xử lý yêu cầu | Giá trị enum trạng thái thô | ERD bảng `bots`, UC §3 bước 3 |
| Đọc `bots.lifecycle_state` | Đọc D1 | ExBot Worker xử lý yêu cầu | Giá trị enum lifecycle chi tiết (18 giá trị) | ERD bảng `bots`, SRS FR-EXBOT-003, UC §3 bước 3 |
| Đọc `bot_runtime_state.last_known_hl_short_size` | Đọc D1 | ExBot Worker xử lý yêu cầu | Kích thước hedge thực tế hiện tại theo ETH (TEXT BigDecimal) | ERD `bot_runtime_state`, UC §3 bước 3 |
| Đọc `bot_runtime_state.target_short_size` | Đọc D1 | ExBot Worker xử lý yêu cầu | Kích thước hedge mục tiêu (cần cho tính drift %) | ERD `bot_runtime_state` — **KHÔNG có trong danh sách đọc tại UC §3 bước 3 (xem I-003)** |
| Đọc `positions.tickLower` | Đọc D1 | ExBot Worker xử lý yêu cầu | Giới hạn tick dưới của LP range (INTEGER) | ERD `positions`, UC §3 bước 3 |
| Đọc `positions.tickUpper` | Đọc D1 | ExBot Worker xử lý yêu cầu | Giới hạn tick trên của LP range (INTEGER) | ERD `positions`, UC §3 bước 3 |
| Đọc `hedge_legs.margin_status` | Đọc D1 | ExBot Worker xử lý yêu cầu | Tình trạng ký quỹ: `ok` / `warning` / `critical` | ERD `hedge_legs`, SRS FR-EXBOT-060, UC §3 bước 3 |
| Đọc `next_light_check_at` hoặc `last_light_check_at` | Đọc D1 | ExBot Worker xử lý yêu cầu | Timestamp hiển thị là "Last light-check" | UC §3 bước 3 đọc `next_light_check_at`; UC §3 bước 9 gắn nhãn là "Last light-check timestamp" — **mâu thuẫn (xem I-004)**; trường đúng để biểu thị "lần check cuối" là `bot_runtime_state.last_light_check_at` |
| Đọc `MarketDataDO.currentTick` | Đọc Durable Object | ExBot Worker xử lý yêu cầu | Tick hiện tại từ cache slot0 của pool Uniswap V3 | SRS FR-EXBOT-093, UC §3 bước 4 |
| Tính `rangeState` | Tính toán dẫn xuất | `currentTick` so với `tickLower`/`tickUpper` | Chuỗi `'in'` hoặc `'out'` | UC §3 bước 5 — công thức chưa định nghĩa chính xác (xem I-012) |
| Tính drift % | Tính toán dẫn xuất | `last_known_hl_short_size` (thực tế) so với `target_short_size` (mục tiêu) | `(\|thực tế − mục tiêu\| / mục tiêu) × 100` theo % | UC §3 bước 6 — nguồn của targetShortEth chưa xác định (xem I-003) |
| Tạo JSON response | Hệ thống | Toàn bộ dữ liệu trên | HTTP 200 với payload tổng hợp | UC §3 bước 7 — schema chưa định nghĩa (xem I-006) |

**Các lifecycle state được UC bao phủ:**

| `bots.lifecycle_state` | `bots.status` | Mức độ bao phủ trong UC | Nguồn |
|---|---|---|---|
| `active` | active | ✅ — kịch bản thành công chính ở bước 9 nhãn "Active" | SRS states.md, UC §3 bước 9 |
| `safe_mode` | safe_mode | ✅ — A1, hiển thị "Safe Mode — Không có hành động mới" + `safe_mode_reason` | SRS states.md, UC §A1 |
| `hedge_stopped_cooldown` | active | ✅ — A2, hiển thị trạng thái cooldown còn Xh | SRS states.md, UC §A2 |
| `cooldown` | — | ❌ **TRẠNG THÁI ĐÃ BỊ XÓA** — A3 tham chiếu trạng thái này, nhưng đã bị loại bỏ trong HLD 2026-06-18 | SRS states.md ghi chú (2026-06-18) — **I-001 Blocker** |
| `lp_rebalancing` | active | ❌ THIẾU — UC không có alternate flow cho trạng thái này | SRS states.md — **I-005 Major** |
| `lp_closing` | closing | ❌ THIẾU — UC không có alternate flow cho trạng thái này | SRS states.md — **I-005 Major** |
| `error` | error | ❌ THIẾU — UC không có alternate flow cho trạng thái này | SRS states.md — **I-005 Major** |
| `closed` (bot tồn tại nhưng đã đóng) | closed | ❌ THIẾU — UC dùng 404 cho "không có bot đang chạy" nhưng không định nghĩa response cho bot đã đóng | SRS states.md — **I-005 Major** |

**Sự kiện phát sinh / thông báo:**

| Trường hợp | Loại response | Nội dung | Mã đã đăng ký | Nguồn |
|---|---|---|---|---|
| Không có bot đang chạy cho người dùng | HTTP 404 | "No active bot" (trạng thái rỗng trên UI) | Chưa có mã E-EXBOT (xem I-009) | UC §A4 |
| Operator Facade không khả dụng | HTTP 503 | "Status service temporarily unavailable" | Chưa có mã E-EXBOT (xem I-010) | UC §A5 |
| HL API không truy cập được khi lấy trạng thái (bot đang ở SAFE_MODE) | Trường status = `safe_mode` | Trường `safe_mode_reason` trong response | E-EXBOT-008 (gián tiếp; bot đã vào safe_mode trước đó) | UC §A1 |

#### §F.2 — Thuộc Tính, Quy Tắc Nghiệp Vụ và Kiểm Tra Hợp Lệ

| Trường / Đối tượng / Quy tắc | Điều kiện / Ràng buộc | Bắt buộc? | Kết quả hợp lệ | Kết quả không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Enum hợp lệ của `bots.status` | Phải là một trong: `active`, `paused`, `closing`, `closed`, `safe_mode`, `error` | Có | Trả về một trong 6 giá trị | Không áp dụng — đọc từ D1 | SRS FR-EXBOT-003, states.md |
| Enum hợp lệ của `bots.lifecycle_state` | Phải là một trong 18 giá trị canonical (xem State Registry trong states.md) | Có | Trả về giá trị canonical | Không áp dụng — đọc từ D1 | SRS FR-EXBOT-003 |
| Enum hợp lệ của `hedge_legs.margin_status` | `ok` / `warning` / `critical` — tính từ ngưỡng `marginUsage` (0,55 / 0,75) | Có | Trả về một trong 3 giá trị | Không áp dụng — đọc từ D1, được ghi trong hedge-sync preflight hoặc deep-audit | SRS FR-EXBOT-060 |
| Tính `rangeState` | `currentTick` so với `tickLower` và `tickUpper` — điều kiện biên inclusive/exclusive chưa định nghĩa | Có | `'in'` hoặc `'out'` | — | UC §3 bước 5 — **I-012: điều kiện biên chưa xác định** |
| Công thức drift % | `(\|last_known_hl_short_size − target_short_size\| / target_short_size) × 100` — yêu cầu `target_short_size` từ `bot_runtime_state` | Có | Giá trị phần trăm drift dạng số | Chia cho 0 nếu `target_short_size = 0` — hành vi chưa định nghĩa | UC §3 bước 6, ERD `bot_runtime_state` — **I-003: nguồn chưa xác định** |
| BR-EXBOT-007 | SAFE_MODE không bao giờ là trạng thái kết thúc; mọi đường dẫn SAFE_MODE đều dẫn đến auto-recovery hoặc `bot_safe_close`. UC trích dẫn quy tắc này. | Có | Endpoint trạng thái là chỉ-đọc; quy tắc này chi phối hành vi downstream, không ảnh hưởng trực tiếp đến status response | Response không bị ảnh hưởng; các UC mutation downstream bị ảnh hưởng | SRS §4 BR-EXBOT-007, common-rules.md |
| Trường `safe_mode_reason` | Được đưa vào response khi `bots.status = 'safe_mode'` (A1). Tên trường trong response schema chưa định nghĩa. | Có (cho A1) | Văn bản `safe_mode_reason` được đưa vào | — | UC §A1 — **I-006: schema chưa định nghĩa** |
| Xác thực (POOL UI → Facade) | Cơ chế chưa được chỉ định | Có — test không thể thiết kế nếu không biết loại auth | Auth hợp lệ → yêu cầu được chuyển tiếp | Auth thất bại → 401/403 (UC không đề cập) | UC §2 Preconditions, SRS FR-EXBOT-090 — **I-011: minor** |
| Internal auth token (Facade → ExBot Worker) | CF service binding + internal token; cơ chế kiểm tra chưa được chỉ định | Có | Token hợp lệ → Worker xử lý | Token không hợp lệ → 403 (UC không đề cập) | UC §3 bước 2 — **I-011: minor** |

**Xử lý lifecycle state trong status response — theo từng trạng thái:**

UC nêu Alternate Flow A1 bao phủ `safe_mode` và A2 bao phủ `hedge_stopped_cooldown`. Tuy nhiên UC không nêu liệu tập đầy đủ các trường D1 (LP range, kích thước hedge, drift %, ký quỹ) có luôn được trả về bất kể lifecycle state hay không, hay một số trường bị null trong các trạng thái nhất định. Ví dụ: trong `lp_rebalancing`, một LP position mới đang được tạo — `tickLower`/`tickUpper` có thể đề cập đến vị thế cũ. Hành vi này chưa được chỉ định trong UC.

#### §F.3 — Logic Chức Năng và Luồng Xử Lý

| Bước | Actor | Trigger / Hành động | Response happy path | Alternate path | Exception path | Nguồn |
|---|---|---|---|---|---|---|
| 1 | POOL UI | Nhà đầu tư chuyển đến màn hình trạng thái ExBot → POOL UI gọi `GET /api/exbot/status` | Yêu cầu HTTP gửi đến Operator Facade | — | Lỗi mạng → UI xử lý trạng thái offline | UC §3 bước 1 |
| 2 | Operator Facade | Tiếp nhận `GET /api/exbot/status` → chuyển tiếp đến ExBot Worker qua CF service binding kèm internal auth token | ExBot Worker tiếp nhận yêu cầu | A5: Facade không khả dụng → HTTP 503 cho POOL UI | Facade sập hoặc binding lỗi → 503 | UC §3 bước 2, SRS FR-EXBOT-090 |
| 3 | ExBot Worker | Tra cứu bản ghi bot cho người dùng đã xác thực | Tìm thấy bản ghi bot trong D1 | A4: Không có bot đang chạy → HTTP 404 | Lỗi đọc D1 → chưa định nghĩa trong UC | UC §3 bước 3, §A4 |
| 4 | ExBot Worker | Đọc các trường từ D1: `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status`, timestamp field | Tất cả trường được trả về thành công | — | Lỗi đọc D1 một phần → chưa định nghĩa trong UC | UC §3 bước 3 |
| 5 | ExBot Worker | Truy vấn `MarketDataDO` để lấy `currentTick` | `currentTick` được trả về | MarketDataDO bị stale → hành vi chưa định nghĩa | MarketDataDO không khả dụng → hành vi chưa định nghĩa (xem I-013) | UC §3 bước 4, SRS FR-EXBOT-093 |
| 6 | ExBot Worker | Tính `rangeState` = so sánh `currentTick` với `tickLower`/`tickUpper` | `rangeState = 'in'` hoặc `'out'` | — | Điều kiện biên tại đúng `tickLower` hoặc `tickUpper` → chưa định nghĩa (xem I-012) | UC §3 bước 5 |
| 7 | ExBot Worker | Tính drift % dùng `last_known_hl_short_size` (thực tế) và `target_short_size` (nguồn chưa xác định — xem I-003) | Giá trị drift % dạng số | `target_short_size = 0` → chia cho 0 (chưa định nghĩa) | — | UC §3 bước 6 |
| 8 | ExBot Worker | Tạo JSON response với tất cả các trường đã tính và đọc | HTTP 200 JSON response — schema chưa định nghĩa (xem I-006) | — | — | UC §3 bước 7 |
| 9 | Operator Facade | Truyền response của ExBot Worker qua cho POOL UI | HTTP 200 được chuyển tiếp | — | — | UC §3 bước 8 |
| 10 | POOL UI | Hiển thị bảng trạng thái | Nhãn trạng thái, LP range, chỉ báo rangeState, thông tin hedge, drift %, tình trạng ký quỹ, timestamp được hiển thị | A1: `safe_mode` → banner "Safe Mode", nút bị vô hiệu hóa trừ đóng khẩn cấp; A2: `hedge_stopped_cooldown` → đếm ngược cooldown; A3: **KHÔNG CÒN HIỆU LỰC — xem I-001**; A4: trạng thái rỗng | — | UC §3 bước 9, §4 |

**Alternate flow A3 — tham chiếu trạng thái lỗi thời (Blocker I-001):**

UC A3 nêu: `lifecycle_state='cooldown' sau bot_safe_close` → UI hiển thị "Bot safely closed. USDC parked. Re-entry will be attempted automatically."

Theo `srs/states.md` (cập nhật 2026-06-18): các lifecycle state `cooldown` và `parked` **đã bị xóa**. Sau `bot_safe_close`, `lifecycle_state` chuyển trực tiếp sang `closed` và `bots.status='closed'`. Thông báo đúng trong SRS FR-EXBOT-070 là "Bot safely closed. Funds have been returned to your wallet." — không phải "USDC parked. Re-entry will be attempted automatically." (vòng lặp park/re-entry đã bị bỏ trong HLD 2026-06-18). A3 như hiện tại không thể kiểm thử được theo spec hiện hành.

#### §F.4 — Tích Hợp Chức Năng và Nhất Quán Dữ Liệu (Ảnh Hưởng Chéo)

| Hành động kích hoạt | Khu vực / UC / Module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| `GET /api/exbot/status` đọc `hedge_legs.margin_status` | `margin_status` được ghi bởi hedge-sync preflight và deep-audit (SRS FR-EXBOT-060) | Status response có thể không phản ánh ký quỹ thực tế nếu hedge-sync chưa chạy gần đây | `margin_status` trong response phản ánh lần ghi D1 gần nhất, không phải trạng thái HL trực tiếp — độ trễ = thời gian kể từ hedge-sync hoặc deep-audit cuối (tối đa 6 giờ cho bot đã tạm dừng) | SRS FR-EXBOT-060 |
| `GET /api/exbot/status` truy vấn `MarketDataDO.currentTick` | `MarketDataDO` được dùng chung bởi tất cả light-check worker (SRS FR-EXBOT-093) | Endpoint trạng thái tạo thêm tải lên `MarketDataDO`; TTL cache ảnh hưởng độ tươi của `currentTick` để tính rangeState | Khoảng thời gian stale của cache chưa định nghĩa (OQ-EXBOT-09). Nếu cache cũ hơn 5 phút, `rangeState` có thể khác với kết quả light-check worker tính | SRS FR-EXBOT-093, OQ-EXBOT-09 |
| `GET /api/exbot/status` đọc `bot_runtime_state.last_known_hl_short_size` | Được ghi bởi hedge-sync reconcile (SRS FR-EXBOT-025) | Kích thước hedge hiển thị có thể không cập nhật so với vị thế HL thực tế nếu hedge-sync chưa chạy gần đây | Nguồn chính xác cho kích thước hedge là HL; `last_known_hl_short_size` trong D1 chỉ được cập nhật sau mỗi lần reconcile. Status hiển thị giá trị D1, không phải vị thế HL trực tiếp | SRS FR-EXBOT-025, ERD |
| Status response điều khiển trạng thái nút ở POOL UI | Module POOL UI (PTL-05) | Trạng thái `safe_mode` vô hiệu hóa các nút mutation; độ chính xác của status ảnh hưởng trực tiếp đến các hành động có thể thực hiện của nhà đầu tư | Dữ liệu: `bots.status` và `lifecycle_state` nhất quán với nhau (cả hai được ghi atomic theo SRS FR-EXBOT-003). Không có vấn đề eventual-consistency cho hai trường này. | SRS FR-EXBOT-003, UC §A1 |
| Không có bot đang chạy (A4) trả về 404 | POOL UI hiển thị trạng thái rỗng | Nhà đầu tư biết không có ExBot nào đang chạy | Response 404 không ảnh hưởng đến trạng thái D1 nào | UC §A4 |
| Phụ thuộc vào `UC-EXBOT-bot-start` | Status UC phụ thuộc vào việc bot đã tồn tại trong D1 với dữ liệu khởi tạo đúng (lifecycle_state, positions, hedge_legs đã được điền) | Status sẽ trả về dữ liệu thiếu/null nếu khởi động bot chưa hoàn chỉnh — hành vi chưa định nghĩa trong UC | Điều kiện trước: bot phải đã hoàn thành chuỗi khởi tạo (`lifecycle_state='active'` tối thiểu) | SRS FR-EXBOT-003, UC §2 |

#### §F.5 — Acceptance Criteria Đề Xuất

| AC # | Kịch bản | Given — Điều kiện | When — Hành động | Then — Kết quả mong đợi | Nguồn / Ghi chú |
|---|---|---|---|---|---|
| AC-01 | Bot đang hoạt động — response đầy đủ | Bot có `lifecycle_state='active'`, `bots.status='active'`, positions và hedge_legs hợp lệ trong D1 | Nhà đầu tư gọi `GET /api/exbot/status` | HTTP 200 response bao gồm: nhãn status "Active", `tickLower`, `tickUpper`, tick hiện tại từ MarketDataDO, rangeState ('in' hoặc 'out'), `last_known_hl_short_size`, `target_short_size`, drift % (tính đúng), `margin_status` ('ok'/'warning'/'critical'), và timestamp | UC §3 main scenario, US-EXBOT-002 AC-EXBOT-002-1 |
| AC-02 | Safe Mode — response bao gồm safe_mode_reason | Bot có `bots.status='safe_mode'` | Nhà đầu tư gọi `GET /api/exbot/status` | HTTP 200, response body bao gồm trường `safe_mode_reason`; POOL UI hiển thị banner "Safe Mode — Không có hành động mới" kèm lý do | UC §A1, US-EXBOT-002 AC-EXBOT-002-2 |
| AC-03 | Stop cooldown — response bao gồm thời điểm kết thúc cooldown | Bot có `lifecycle_state='hedge_stopped_cooldown'` | Nhà đầu tư gọi `GET /api/exbot/status` | HTTP 200, response bao gồm timestamp kết thúc cooldown; POOL UI hiển thị "Stop Fired — Cooldown (còn Xh)" | UC §A2, US-EXBOT-002 AC-EXBOT-002-3 |
| AC-04 | Không có bot đang chạy — response 404 | Nhà đầu tư không có bot trong D1 hoặc bot có `status='closed'` | Nhà đầu tư gọi `GET /api/exbot/status` | HTTP 404 response; POOL UI hiển thị trạng thái rỗng "No active bot" | UC §A4 — **Suy luận cần xác nhận**: UC không định nghĩa liệu bot đã đóng trả về 404 hay response trạng thái closed cụ thể |
| AC-05 | rangeState in-range — tick nằm trong biên | `tickLower <= currentTick` và `currentTick < tickUpper` (điều kiện biên TBD) | Nhà đầu tư gọi `GET /api/exbot/status` | `rangeState = 'in'` trong response | UC §3 bước 5 — **Suy luận cần xác nhận**: điều kiện biên tại đúng tickLower và tickUpper chưa định nghĩa |
| AC-06 | rangeState out-of-range — tick dưới biên dưới | `currentTick < tickLower` | Nhà đầu tư gọi `GET /api/exbot/status` | `rangeState = 'out'` trong response | UC §3 bước 5 |
| AC-07 | Tính drift % | Bot có `last_known_hl_short_size = 1,0 ETH`, `target_short_size = 0,9 ETH` | Nhà đầu tư gọi `GET /api/exbot/status` | `drift_pct = (\|1,0 − 0,9\| / 0,9) × 100 ≈ 11,1%` trong response | UC §3 bước 6 — **Suy luận cần xác nhận**: tên trường cho targetShortEth trong D1 chưa xác nhận |
| AC-08 | Operator Facade không khả dụng | Dịch vụ Facade bị ngừng | Nhà đầu tư gọi `GET /api/exbot/status` | HTTP 503 được trả về; POOL UI hiển thị banner lỗi "Status service temporarily unavailable" | UC §A5 |

---

## §7 — Ảnh Hưởng Tích Hợp và Phân Tích Phụ Thuộc

| UC liên quan | Phụ thuộc / Điểm kết hợp | Rủi ro hồi quy | Nhận xét |
|---|---|---|---|
| UC-EXBOT-bot-start | Status UC giả định bot đã có dữ liệu khởi tạo đầy đủ trong D1 (lifecycle_state, positions, hedge_legs, bot_runtime_state). Nếu UC-EXBOT-bot-start bị lỗi giữa chừng, status response có thể trả về dữ liệu null/thiếu cho một số trường | Rủi ro cao: kiểm thử E2E của UC này yêu cầu UC-EXBOT-bot-start phải hoạt động đúng | Điều kiện trước của UC §2 cần bổ sung: bot phải hoàn thành chuỗi khởi tạo trước khi UC này hợp lệ |
| UC-EXBOT-hedge-sync | `hedge_legs.margin_status` và `bot_runtime_state.last_known_hl_short_size` được ghi bởi hedge-sync. Status response phản ánh giá trị D1 từ lần hedge-sync gần nhất, không phải trạng thái HL thực tế | Rủi ro trung bình: status có thể không cập nhật sau sự kiện thay đổi ký quỹ HL | Đây là sự trì hoãn đã biết; vấn đề là thiếu định nghĩa ngưỡng trễ tối đa |
| UC-EXBOT-pause-resume | `bots.status='paused'` là một trong 6 giá trị enum hợp lệ nhưng không có alternate flow nào trong UC này mô tả trạng thái paused | Rủi ro thấp: thiếu alternate flow cho trạng thái `paused` và `lp_rebalancing` trong UC (xem I-005) | BA cần thêm alternate flow cho ít nhất `paused` và `lp_rebalancing` |
| UC-EXBOT-emergency-close | `bots.status='closing'` là trạng thái trung gian trong khi đóng khẩn cấp. UC hiện tại không định nghĩa response khi bot đang ở trạng thái `closing` | Rủi ro trung bình: investor kiểm tra status ngay sau khi kích hoạt đóng khẩn cấp có thể nhận được response trạng thái `closing` không có mô tả trong UC | Cần alternate flow cho trạng thái `closing` trong UC |
| MarketDataDO (Durable Object dùng chung) | `currentTick` được lấy từ `MarketDataDO` — được dùng chung bởi tất cả light-check worker. Cache TTL và fallback behavior khi DO bị stale/unavailable chưa định nghĩa (I-013, OQ-EXBOT-09) | Rủi ro cao cho môi trường sản xuất tải cao: nếu nhiều status request đồng thời đến cùng lúc với light-check, có thể gây tranh chấp trên MarketDataDO | Cần định nghĩa behavior và fallback trong OQ-EXBOT-09 trước khi test tích hợp |

---

## §8 — Acceptance Criteria

Xem §F.5 ở trên để biết danh sách đầy đủ acceptance criteria đề xuất.

---

## §9 — Yêu Cầu Phi Chức Năng Liên Quan

| ID NFR | Yêu cầu | Nguồn |
|---|---|---|
| NFR-EXBOT-008 | Tính toán drift % PHẢI dùng BigDecimal (không phải số thực dấu phẩy động JavaScript) để tránh sai số làm tròn — đặc biệt quan trọng khi kích thước hedge lớn hoặc tỷ lệ phần trăm rất nhỏ | SRS NFR-EXBOT-008 |
| NFR-EXBOT-009 | `GET /api/exbot/status` phải trả về response trong vòng 500ms ở phân vị thứ 99 trong điều kiện vận hành bình thường | SRS NFR-EXBOT-009 |
| NFR-EXBOT-010 | Không có dữ liệu trạng thái bot nhạy cảm (ID bot, địa chỉ ví, kích thước position) được ghi vào log ở cấp thông tin — chỉ ghi vào log debug khi bật chế độ debug | SRS NFR-EXBOT-010 |
| NFR-EXBOT-011 | Endpoint trạng thái phải là idempotent: gọi nhiều lần liên tiếp không được tạo ra bất kỳ thay đổi dữ liệu nào (UC này là chỉ-đọc — điều này được thỏa mãn bởi thiết kế) | SRS NFR-EXBOT-011 |
| OQ-EXBOT-09 | Cache TTL của MarketDataDO và hành vi khi cache hết hạn chưa được xác định — ảnh hưởng đến tính tươi của rangeState | SRS §9 |
| NFR-EXBOT-015 | Đường dẫn đọc D1 phải xử lý gracefully trường hợp không tìm thấy dữ liệu (trả về 404 thay vì 500) | SRS NFR-EXBOT-015 |

---

## §10 — Danh Sách Vấn Đề

### §10.1 — Đăng Ký Vấn Đề (I-001 đến I-014)

| ID | Mức độ | Loại | Tiêu đề | Mô tả ngắn | Ảnh hưởng QC | Tham chiếu |
|---|---|---|---|---|---|---|
| I-001 | Blocker | Mâu thuẫn | A3 tham chiếu lifecycle state đã bị xóa | UC Alternate Flow A3 mô tả `lifecycle_state='cooldown'` và thông báo "USDC parked. Re-entry will be attempted automatically." — cả hai đã bị xóa trong HLD 2026-06-18. Sau `bot_safe_close`, hệ thống chuyển thẳng sang `closed`. Thông báo đúng là "Bot safely closed. Funds have been returned to your wallet." | Tester sẽ thiết kế test case cho lifecycle state không tồn tại. Test execution luôn fail. UC không sẵn sàng cho test design. | UC §A3 so với `srs/states.md` (ghi chú 2026-06-18), SRS FR-EXBOT-070 |
| I-002 | Major | Mâu thuẫn | Actor mâu thuẫn giữa UC và FRD | UC định nghĩa primary actor là "USDC Investor (read-only)". FRD §4.11 FR-EXBOT-100 liệt kê Actor là "Admin". US-EXBOT-002 xác nhận đây là UC của Investor. Hai tài liệu có thẩm quyền mâu thuẫn về việc ai gọi endpoint này. | Các test case xác thực không thể thiết kế được: POOL UI xác thực Investor hay Admin? | UC §1 Actors so với FRD §4.11 FR-EXBOT-100 |
| I-003 | Major | Thiếu | Nguồn `target_short_size` không rõ trong drift % | UC step 6 tính `drift %` dùng `targetShortEth` nhưng step 3 không liệt kê `bot_runtime_state.target_short_size` trong D1 reads. Chưa rõ giá trị này được đọc từ D1 hay tính lại. | Test không thể verify giá trị nào được dùng cho `targetShortEth`. Chia cho 0 khi `target_short_size = 0` chưa được xử lý. | UC §3 bước 3 và 6 so với SRS ERD `bot_runtime_state` |
| I-004 | Major | Mâu thuẫn | Mâu thuẫn timestamp light-check trong UC | UC step 3 đọc `bots.next_light_check_at` (lần TIẾP THEO được lên lịch) nhưng step 9 gắn nhãn hiển thị là "Last light-check timestamp" (lần CUỐI đã hoàn tất — field đúng là `bot_runtime_state.last_light_check_at`). | Test assertion không thể viết được: giá trị timestamp hiển thị là lần check đã qua hay lần tiếp theo? | UC §3 bước 3 và 9 so với SRS ERD `bots` + `bot_runtime_state` |
| I-005 | Major | Thiếu | Thiếu alternate flow cho nhiều lifecycle state | UC chỉ mô tả 3 trong số 15 lifecycle state (active, safe_mode, hedge_stopped_cooldown). Thiếu: `lp_rebalancing`, `lp_closing`, `error`, `closed`, `paused`. | Test case cho bot ở các trạng thái còn lại không thể thiết kế được. | UC §4 Alternate Flows so với `srs/states.md` State Registry |
| I-006 | Major | Thiếu | Không có JSON response schema HTTP 200 | Không có JSON schema cho HTTP 200 response trong UC, SRS hay FRD. Key names cho derived fields (`rangeState`, `drift_pct`) không được chỉ định. | Test không thể assert field names của response. UC không thể test ở cấp API contract. | UC §3 bước 7–8 so với SRS FR-EXBOT-090 |
| I-007 | Minor | Mâu thuẫn | FR-EXBOT-090 được gán cho hai nội dung khác nhau | Trong FRD, FR-EXBOT-090 trỏ đến "HLRateLimitDO". Trong SRS, FR-EXBOT-090 trỏ đến "Operator Facade API". Cùng số FR, hai nội dung khác nhau. | Traceability bị broken — người đọc FRD §4.10 sẽ thấy sai nội dung. | FRD §4.10 so với SRS §2 FR-EXBOT-090 |
| I-008 | Minor | Không nhất quán | FR trace không đồng bộ giữa UC và US | UC FR trace: `FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-090`. US-EXBOT-002 FR trace: `FR-EXBOT-002, FR-EXBOT-050`. FR-EXBOT-050 (SAFE_MODE Entry Conditions) liên quan trực tiếp đến A1 nhưng thiếu trong UC FR trace. | Traceability không đầy đủ: tester review flow A1 không thể trace về FR định nghĩa nó. | UC §FR Trace so với US-EXBOT-002 §Trace |
| I-009 | Minor | Thiếu | Không có E-EXBOT code cho 404 "no active bot" | Alternate Flow A4 trả về HTTP 404 nhưng không có E-EXBOT-* code được đăng ký trong `message-list.md` cho trường hợp này. | Test không thể verify nội dung error response body cho 404. | UC §A4 so với `02_backbone/message-list.md` |
| I-010 | Minor | Thiếu | Message text 503 không được đăng ký | Alternate Flow A5 trả về message "Status service temporarily unavailable" nhưng không được đăng ký trong `message-list.md`. | Test không thể verify nội dung message text chính xác của 503 response. | UC §A5 so với `02_backbone/message-list.md` |
| I-011 | Minor | Thiếu | Cơ chế xác thực không được chỉ định | Cơ chế auth không được chỉ định cho cả hai đoạn: (a) POOL UI → Facade và (b) Facade → ExBot Worker "internal auth token". | Các test case authentication-path không thể thiết kế được. | UC §2 Preconditions, §3 bước 2 so với SRS FR-EXBOT-090 |
| I-012 | Minor | Thiếu | Điều kiện biên rangeState không định nghĩa | Công thức rangeState mô tả so sánh `currentTick` với `tickLower`/`tickUpper` nhưng không định nghĩa điều kiện biên inclusive/exclusive. | Edge case test tại exact boundary ticks không thể thiết kế. | UC §3 bước 5 so với SRS FR-EXBOT-012 |
| I-013 | Minor | Thiếu | Fallback MarketDataDO không được định nghĩa | UC step 4 truy vấn `MarketDataDO` để lấy `currentTick` nhưng không mô tả behavior khi DO unavailable hoặc cache stale. | Test scenario: MarketDataDO bị forced refresh khi status được gọi — response behavior không xác định. | UC §3 bước 4 so với SRS FR-EXBOT-093, OQ-EXBOT-09 |
| I-014 | Lưu ý | Không nhất quán | Mapping FR identifier không nhất quán giữa FRD và SRS | SRS FR-EXBOT-002 = "Bot Start Preflight Checks"; FRD FR-EXBOT-002 = "Bot Lifecycle State Machine". Cùng ID, nội dung khác nhau. Tương tự FR-EXBOT-003. | FR trace gây nhầm lẫn tùy thuộc vào tài liệu nào được tra cứu. Không block test design UC này nhưng ảnh hưởng traceability toàn dự án. | UC §FR Trace so với FRD §4.1 so với SRS §2 |

### §10.2 — Phụ Thuộc Giải Quyết Vấn Đề

| Vấn đề | Cần từ | Ưu tiên | Ghi chú |
|---|---|---|---|
| I-001: Viết lại A3 | BA | Blocker — phải giải quyết trước khi thiết kế test | Xóa tham chiếu `cooldown`/`parked`; thay bằng hành vi `closed` sau `bot_safe_close` và message text đúng từ FR-EXBOT-070 |
| I-003: Xác nhận nguồn `target_short_size` | BA hoặc Tech Lead | Major | Xác nhận đọc từ `bot_runtime_state.target_short_size` và hành vi chia cho 0 |
| I-005: Thêm alternate flow cho lifecycle states còn thiếu | BA | Major | Cần ít nhất `paused`, `lp_rebalancing`, `error`, `closed` |
| I-006: Định nghĩa JSON response schema HTTP 200 | BA hoặc Tech Lead | Major — cần thiết để test API contract | Liệt kê tất cả field names, types, optionality |

### §10.3 — Tóm Tắt Đánh Giá

**Bảng điểm đánh giá:**

| Tiêu chí | Điểm số | Tối đa | Ghi chú |
|---|---|---|---|
| Định nghĩa đầy đủ và nhất quán | 6 | 20 | -12: A3 lỗi thời (Blocker), actor mâu thuẫn (Major), schema thiếu (Major) |
| Traceability | 8 | 15 | -5: FR numbering không nhất quán |
| Testability | 7 | 20 | -8: thiếu schema, thiếu alternate flow, thiếu điều kiện biên |
| Tích hợp và phụ thuộc | 10 | 15 | -3: MarketDataDO fallback chưa định nghĩa |
| Acceptance criteria | 9 | 15 | Có US với ACs, tuy nhiên phụ thuộc vào các Major issues |
| Tuân thủ blockchain (D1 + HL) | 11 | 15 | -2: nguồn target_short_size chưa rõ; -2: BigDecimal requirement chưa được tham chiếu trong UC |
| **Tổng** | **51** | **100** | |

**Danh sách kiểm tra blockchain:**

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Dual-chain (Base + Optimism) | Chưa đề cập | UC không đề cập đến địa chỉ MarketDataDO riêng theo chain |
| BigDecimal cho phép tính tài chính | Được đề cập | SRS NFR-EXBOT-008 — nhưng UC không tham chiếu |
| D1 stale data handling | Không đủ | Fallback cho MarketDataDO stale/unavailable chưa định nghĩa |
| Bất biến INV-STOP | Không liên quan | UC này là chỉ-đọc, không kích hoạt stop |

**Vấn đề Blocker:**
- **I-001** — A3 tham chiếu `lifecycle_state='cooldown'` đã bị xóa (HLD 2026-06-18). Vòng lặp park/re-entry đã bị bỏ. A3 không thể kiểm thử được và phải được viết lại trước khi thiết kế test.

**Vấn đề Major (cần giải quyết trước khi test):**
- **I-002** — Mâu thuẫn actor (Investor vs Admin) giữa UC và FRD
- **I-003** — Nguồn `target_short_size` cho drift % chưa xác nhận
- **I-004** — Mâu thuẫn timestamp light-check (next vs last)
- **I-005** — Thiếu alternate flow cho `paused`, `lp_rebalancing`, `error`, `closed`
- **I-006** — Thiếu JSON response schema HTTP 200

**Phán quyết cuối:**

> **CHƯA SẴN SÀNG (51/100)**
>
> UC-EXBOT-monitor-status chưa sẵn sàng cho test design theo nghĩa nghiêm túc. Blocker I-001 đủ để dừng: tester được giao thiết kế test case cho một lifecycle state không tồn tại. Thêm vào đó, không có JSON response schema (I-006), actor mâu thuẫn (I-002), và thiếu alternate flow cho phần lớn lifecycle states (I-005) khiến phạm vi test không thể xác định đầy đủ. Hành động khuyến nghị: BA giải quyết I-001, I-003, I-005, I-006 trong phiên làm việc tiếp theo; sau đó gửi lại để đánh giá lại.

---

## §11 — Nhật Ký Thay Đổi

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | `qc-uc-read-exbot` agent | Tạo mới — báo cáo rà soát ban đầu bằng tiếng Anh |
| v2 | 2026-06-30 | `qc-uc-read-exbot` agent | Bản dịch tiếng Việt của v1 |
