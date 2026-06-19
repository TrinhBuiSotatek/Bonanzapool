---
title: Báo cáo Kiểm tra Sẵn sàng UC — UC-EXBOT-bot-safe-close
date: 2026-06-18
author: qc-uc-read-exbot
version: v2
uc_id: UC-EXBOT-bot-safe-close
skill: qc-uc-read-exbot
baseline: SRS spec.md + states.md + frd.md cập nhật 2026-06-18
note: Bản dịch tiếng Việt của v1 (tiếng Anh — theo yêu cầu người dùng)
---

# Báo cáo Kiểm tra Sẵn sàng UC — UC-EXBOT-bot-safe-close

## Feature Brief

UC-EXBOT-bot-safe-close mô tả quy trình hệ thống tự động đóng một bot ExBot đang hoạt động khi bot đó không còn có thể vận hành an toàn. Luồng này được kích hoạt bởi một trong năm điều kiện: bộ ngắt mạch (circuit breaker) hết toàn bộ lần thử lại mà không có lần thăm dò thành công; sự kiện ký quỹ ở mức nguy hiểm (margin critical) dẫn đến SAFE_MODE không thể tự phục hồi; lệnh dừng lỗ (stop-loss) kích hoạt ba lần trong vòng bảy ngày; bộ xử lý partial_repair thất bại ba lần liên tiếp cho cùng một sự kiện; hoặc admin gọi trực tiếp API force-close. Không có thao tác nào của nhà đầu tư khởi động luồng này — nhà đầu tư chỉ nhận thông báo sau khi quá trình đóng bot hoàn tất.

Thứ tự thực hiện việc đóng bot được quy định chặt chẽ: xử lý vị thế hedge trước, đóng vị thế LP sau, thanh toán tiền cuối cùng. Close Worker phải chiếm giữ khóa `UserLockDO` (TTL=90 giây) trước khi tác động vào Hyperliquid, thực hiện lệnh `closeShortReduceOnlyIoc` để đưa vị thế short về 0, hủy lệnh stop qua `replaceStopProtected(size=0)`, sau đó xác nhận vị thế HL bằng 0 trước khi tiếp tục. Chỉ sau khi `close_operations.state` đạt `hedge_closed`, worker mới gọi `vault.executeStrategy(RedeemStrategyV1)` để đóng LP NFT thông qua BnzaExPositionManager. Phí được chuyển qua LpFeeOps (phí vận hành và phí hiệu suất tính bằng pair currency), và vốn gốc được trả lại bằng pair currency với tùy chọn chuyển đổi sang USDC. Phần thanh toán từ HL được Operator xử lý ngoài chuỗi thông qua `RedemptionQueue.fulfillRequest` (theo thứ tự FIFO) — tiền của nhà đầu tư không bị mất nếu Operator chậm xử lý, vì yêu cầu vẫn còn trong hàng đợi.

Các điểm cần chú ý khi thiết kế test: (1) máy trạng thái `close_operations` có bảy trạng thái — bộ test cần bao phủ toàn bộ các chuyển đổi trạng thái, kể cả đường dẫn `residual_hl_liability` và trường hợp hết số lần thử lại; (2) `srs/spec.md FR-EXBOT-072` và `srs/erd.md` định nghĩa ràng buộc `UNIQUE` trên `close_operations.idempotency_key` ngăn tạo hai dòng đóng bot trùng nhau — UC không đề cập cơ chế bảo vệ này, nhưng cần có test case cho tình huống kích hoạt đồng thời (xem Issue I-001 và §F.1.2); (3) flows.md F-05 và US-012 AC-012-1 đã lỗi thời tại thời điểm kiểm tra (vòng lặp park/re-entry và tham chiếu `vaultClose`) — các test case nào tham chiếu các đường dẫn đó sẽ không hợp lệ cho đến khi BA cập nhật tài liệu. Đường dẫn khẩn cấp của admin (`emergencyTransfer`) là cơ chế dự phòng tách biệt khỏi máy trạng thái đóng bot thông thường và yêu cầu OPERATOR_ROLE với hợp đồng đang ở trạng thái tạm dừng (paused).

## Bảng mã viết tắt

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC-EXBOT-* | Mã định danh Use Case cho module ExBot. Mỗi UC bao phủ một luồng nghiệp vụ của hệ thống ExBot backend. | usecases/index.md |
| US-EXBOT-* | Mã định danh User Story. Mỗi US quy định tiêu chí chấp nhận cho một phần hành vi của bot. | userstories/index.md |
| FR-EXBOT-* | Mã định danh Yêu cầu chức năng. Xuất hiện trong cả SRS (spec.md) và FRD (frd.md) — cả hai dùng cùng tiền tố nhưng đánh số khác nhau; SRS là văn bản ưu tiên khi có mâu thuẫn. | srs/spec.md, frd.md |
| BR-EXBOT-* | Quy tắc nghiệp vụ. Các bất biến cấp module, áp dụng xuyên suốt các use case. Định nghĩa trong srs/spec.md §4. | srs/spec.md §4 |
| AC-EXBOT-* | Tiêu chí chấp nhận. Viết theo cú pháp Gherkin trong các user story. | userstories/us-*.md |
| FM-XB-* | Mã định danh Feature Map từ backbone.md — ánh xạ tới các vùng chức năng trong SRS §1.2. | backbone.md |
| close_operations | Bảng D1 theo dõi máy trạng thái của cả hai hệ thống đóng (user_redeem và bot_safe_close). Mỗi dòng có: kind, state, idempotency_key (UNIQUE). | srs/erd.md |
| RedemptionQueue | Hợp đồng hàng đợi FIFO trên chuỗi. bot_safe_close đưa khoản thanh toán phần HL vào đây; Operator gọi fulfillRequest để trả tiền cho người dùng on-chain. | srs/spec.md FR-EXBOT-073 |
| RedeemStrategyV1 | Chiến lược đóng vị thế LP truyền vào BnzaExVault.executeStrategy(). Đốt LP NFT, định tuyến phí qua LpFeeOps, hoàn trả vốn gốc theo cặp tiền tệ. | UC §3, srs/spec.md FR-EXBOT-073 |
| emergencyTransfer | Hàm của BnzaExVault chỉ được gọi bởi OPERATOR_ROLE khi hợp đồng đang tạm dừng. Chuyển USDC + LP NFT của người dùng về chính địa chỉ của họ. Phát sự kiện EmergencyRecovery. Không yêu cầu xác nhận đa chữ ký. | frd.md §2 (ghi chú HLD 2026-06-18) |
| UserLockDO | Durable Object cung cấp khóa loại trừ dựa trên thuê bao (lease). Worker thực hiện bot_safe_close phải giành được lease trước khi thực hiện bất kỳ thao tác nào trên HL. TTL=90s. | srs/spec.md FR-EXBOT-092 |
| SAFE_MODE | Trạng thái bot trong đó mọi thao tác thay đổi đều bị chặn. Các thao tác được phép: đọc trạng thái, gửi cảnh báo, giám sát stop, light-check (phần không gọi HL), deep-audit khi HL phục hồi. Điều kiện kích hoạt định nghĩa tại FR-EXBOT-050. | srs/spec.md FR-EXBOT-050 |
| residual_hl_liability | Trạng thái của close_operations khi việc đóng vị thế hedge trên HL thất bại. Báo hiệu cho admin rằng còn một khoản nợ HL tồn đọng cần giải quyết. | srs/states.md, srs/spec.md FR-EXBOT-073 |

---

## 0. Phạm vi kiểm tra

| Trường | Giá trị |
|---|---|
| UC được kiểm tra | UC-EXBOT-bot-safe-close |
| File UC | docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-bot-safe-close.md |
| UC được cập nhật | 2026-06-18 (bỏ luồng park/redeploy/re-entry; luồng mới: executeStrategy → RedemptionQueue FIFO) |
| User Stories liên quan | US-EXBOT-009, US-EXBOT-010, US-EXBOT-012 |
| FR Trace (UC §7) | FR-EXBOT-070, FR-EXBOT-072, FR-EXBOT-073 |
| FR Trace (index.md) | FR-070, FR-071, FR-072, FR-073 |
| Cơ sở SRS | srs/spec.md + srs/states.md + srs/flows.md + srs/erd.md (tất cả đã đọc; spec.md + states.md cập nhật 2026-06-18) |
| Cơ sở FRD | frd.md (cập nhật 2026-06-18) |
| Ngày kiểm tra | 2026-06-18 |
| Ngôn ngữ đầu ra | Tiếng Việt (theo yêu cầu người dùng) |

---

## §F.1 Kiểm kê

### F.1.1 Các thao tác / hàm

| ID | Thao tác | Điều kiện kích hoạt | Tác nhân | Nguồn |
|---|---|---|---|---|
| OP-01 | Tạo dòng close_operations (kind='bot_safe_close', state='requested') | Một trong 5 điều kiện kích hoạt | Close Worker | FR-EXBOT-072, FR-EXBOT-073 |
| OP-02 | Giành lease UserLockDO (TTL=90s) | Trước mọi thao tác trên HL | Close Worker | FR-EXBOT-092 |
| OP-03 | closeShortReduceOnlyIoc — đóng toàn bộ vị thế short HL (target=0) | Sau khi giành được lease | Close Worker → HL | FR-EXBOT-073 bước 2 |
| OP-04 | replaceStopProtected(size=0) — hủy lệnh stop theo giao thức §19.5 INV-STOP | Sau khi xác nhận short HL đã đóng | Close Worker → HL | FR-EXBOT-073 bước 3, UC §3 bước 3 |
| OP-05 | Đối chiếu: xác nhận kích thước HL = 0; cập nhật close_operations.state='hedge_closed' | Sau khi hủy stop | Close Worker → D1 | FR-EXBOT-073 bước 4 |
| OP-06 | vault.executeStrategy(RedeemStrategyV1, user, botId, params) — đóng vị thế LP | Sau khi xác nhận hedge_closed | Close Worker → BnzaExVault (on-chain) | FR-EXBOT-073 bước 5, UC §3 bước 5 |
| OP-07 | Định tuyến phí qua LpFeeOps (phí vận hành + phí hiệu suất theo cặp tiền tệ) | Bên trong quá trình thực thi RedeemStrategyV1 | BnzaExVault → LpFeeOps | UC §3 bước 6 |
| OP-08 | Cập nhật close_operations.state='lp_closed'; phát sự kiện PositionClosed | Sau khi đốt LP NFT | BnzaExPositionManager → D1 | FR-EXBOT-073 bước 5, UC §3 bước 7 |
| OP-09 | RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId) | Sau khi lp_closed | Close Worker → RedemptionQueue (on-chain) | FR-EXBOT-073 bước 5, UC §3 bước 8 |
| OP-10 | Cập nhật close_operations.state='redemption_queued'; phát sự kiện RequestCreated | Sau khi gọi createRequest | D1 / RedemptionQueue | FR-EXBOT-073 bước 5, UC §3 bước 9 |
| OP-11 | RedemptionQueue.fulfillRequest(tokens, amounts) — lấy theo FIFO, safeTransferFrom on-chain | Operator gọi thủ công | Operator → RedemptionQueue | FR-EXBOT-073 bước 6, UC §3 bước 10 |
| OP-12 | Cập nhật close_operations.state='done'; bots.status='closed'; phát sự kiện RequestFulfilled | Sau khi xác nhận fulfillRequest | D1 / RedemptionQueue | FR-EXBOT-073 bước 6, UC §3 bước 11 |
| OP-13 | Gửi thông báo cho nhà đầu tư: "Bot safely closed. Funds have been returned to your wallet." | Sau khi done | notification queue | UC §3 bước 12, FR-EXBOT-070 |
| OP-14 | Thông báo leo thang cho admin | Lần kích hoạt bot_safe_close thứ 3 trong 7 ngày | notification queue | UC §4 A4, FR-EXBOT-072 |
| OP-15 | emergencyTransfer(user, botId) — chỉ OPERATOR_ROLE, khi hợp đồng tạm dừng | Quyết định của Admin/Operator | OPERATOR_ROLE → BnzaExVault | US-012 AC-012-3, frd.md §2 |

### F.1.2 Các điều kiện kích hoạt bot_safe_close

| # | Điều kiện | Tiêu chí | Nguồn |
|---|---|---|---|
| T1 | Circuit breaker kiệt sức | circuit_breakers.state='open' VÀ reset_at được gia hạn 3+ lần mà không có probe thành công | FR-EXBOT-072 |
| T2 | Margin ở mức critical + SAFE_MODE không thể phục hồi | margin_status='critical' hai lần liên tiếp → SAFE_MODE, không còn đường phục hồi tự động | FR-EXBOT-072 |
| T3 | 3 lần stop trong 7 ngày | lifecycle_state='hedge_stopped_cooldown' được vào lần thứ 3 trong cửa sổ trượt 7 ngày | FR-EXBOT-072, FR-EXBOT-034 |
| T4 | partial_repair kiệt sức | partial_repair consumer thất bại 3 lần liên tiếp cho cùng một sự kiện kích hoạt | FR-EXBOT-072, FR-EXBOT-036 |
| T5 | Admin buộc đóng | Admin gọi /api/exbot/close một cách tường minh | FR-EXBOT-072, FR-EXBOT-090 |

### F.1.3 Máy trạng thái close_operations

| Trạng thái | Áp dụng cho | Ý nghĩa | Nguồn |
|---|---|---|---|
| requested | bot_safe_close | Dòng đã được tạo, điều kiện kích hoạt đã nhận | FR-EXBOT-073, states.md |
| hedge_close_pending | bot_safe_close | Đang trong quá trình đóng vị thế short HL | FR-EXBOT-073 (SRS), ghi chú UC §3 bước 2 |
| hedge_closed | cả hai | Vị thế HL đã xác nhận kích thước=0, lệnh stop đã hủy | FR-EXBOT-073, states.md |
| lp_closed | cả hai | LP NFT đã đốt; sự kiện PositionClosed đã phát | FR-EXBOT-073, states.md |
| redemption_queued | bot_safe_close | RedemptionQueue.createRequest đã hoàn tất | FR-EXBOT-073, states.md |
| residual_hl_liability | cả hai | Đóng HL thất bại; cần admin giải quyết khoản nợ tồn đọng | FR-EXBOT-073, states.md |
| done | cả hai | fulfillRequest đã hoàn tất; tiền đã về tay người dùng on-chain | FR-EXBOT-073, states.md |

### F.1.4 Các sự kiện được phát

| Sự kiện | Bên phát | Thời điểm | Nguồn |
|---|---|---|---|
| PositionClosed | BnzaExPositionManager | Sau khi đốt LP NFT (bước lp_closed) | UC §3 bước 7 |
| RequestCreated | RedemptionQueue | Sau khi gọi createRequest (bước redemption_queued) | UC §3 bước 9 |
| RequestFulfilled | RedemptionQueue | Sau khi fulfillRequest (bước done) | UC §3 bước 11 |
| EmergencyRecovery | BnzaExVault | Sau khi emergencyTransfer hoàn tất | US-012 AC-012-3 |

### F.1.5 Các đối tượng dữ liệu và trường quan trọng

| Đối tượng | Các trường chính | Nguồn |
|---|---|---|
| close_operations | id, bot_id, kind, state, idempotency_key (UNIQUE), trigger_reason, hedge_close_tx, lp_close_tx, usdc_amount, residual_amount, created_at, updated_at | erd.md |
| bots | id, status, lifecycle_state | erd.md |
| hedge_legs | stop_order_id, stop_cloid, stop_replacing_started_at, margin_status | erd.md |
| lp_operations | id, bot_id, op_type, idempotency_key, tx_hash, pre_token_id, post_token_id, status | erd.md |
| circuit_breakers | state, reset_at, failure_count, half_open_probe_used | erd.md |

---

## §F.2 Trạng thái, Quy tắc nghiệp vụ, Kiểm chứng và Thông báo

### F.2.1 Vòng đời close_operations — luồng bot_safe_close

| Bước | Trạng thái trước | Trạng thái sau | Điều kiện / Kích hoạt | Kiểm chứng / Quy tắc | Nguồn |
|---|---|---|---|---|---|
| 1 | (chưa có) | requested | Một trong T1–T5 kích hoạt | idempotency_key UNIQUE — từ chối dòng trùng lặp | FR-EXBOT-072, FR-EXBOT-073 |
| 2 | requested | hedge_close_pending | Close Worker giành UserLockDO, bắt đầu đóng short HL | UserLockDO TTL=90s; closeShortReduceOnlyIoc (target=0) | FR-EXBOT-073, FR-EXBOT-092 |
| 3 | hedge_close_pending | hedge_closed | Xác nhận vị thế HL kích thước=0; hủy stop qua replaceStopProtected(size=0) | Thử lại tối đa 3 lần khi thất bại; lần thứ 3 thất bại thì leo thang cho admin, giữ nguyên tại hedge_close_pending | FR-EXBOT-073 |
| 4 | hedge_closed | lp_closed | vault.executeStrategy(RedeemStrategyV1) hoàn tất; PositionClosed phát | KHÔNG thực hiện đóng LP trước khi xác nhận hedge_closed | FR-EXBOT-073 |
| 5 | lp_closed | redemption_queued | RedemptionQueue.createRequest đã thêm vào hàng đợi; RequestCreated phát | — | FR-EXBOT-073 |
| 6 | redemption_queued | done | Operator gọi fulfillRequest; safeTransferFrom on-chain; RequestFulfilled phát; bots.status='closed' | Thứ tự FIFO được RedemptionQueue thực thi; tiền người dùng không mất nếu Operator chậm trễ | FR-EXBOT-073 |

**Luồng thất bại:** Nếu đóng HL thất bại → giữ nguyên tại hedge_close_pending; tối đa 3 lần thử; leo thang cho admin. Việc đóng LP sẽ không bao giờ được thực hiện cho đến khi xác nhận hedge đã đóng.

**Trường hợp không thể đóng hedge:** close_operations.state='residual_hl_liability' + SAFE_MODE (UC §4 A1). Admin phải giải quyết khoản nợ HL tồn đọng.

### F.2.2 Các quy tắc nghiệp vụ áp dụng cho UC này

| BR | Quy tắc | Tác động đến bot_safe_close | Nguồn |
|---|---|---|---|
| BR-EXBOT-006 | Việc hoàn trả phần LP của user_redeem là vô điều kiện | Không áp dụng trực tiếp cho bot_safe_close (sử dụng RedemptionQueue, không phải hoàn trả LP tức thì) | srs/spec.md §4 |
| BR-EXBOT-007 | SAFE_MODE không bao giờ là trạng thái cuối — phải dẫn đến phục hồi tự động HOẶC bot_safe_close | SAFE_MODE không thể phục hồi → bot_safe_close là lối thoát cuối cùng | srs/spec.md §4 |
| BR-EXBOT-008 | BnzaExVault (hợp đồng LP NFT) ≠ vaultAddress (tài khoản con HL) — không được nhầm lẫn | RedeemStrategyV1 gọi BnzaExVault; đây là phía LP, không phải tài khoản con HL | srs/spec.md §4 |

### F.2.3 Thẩm quyền emergencyTransfer (US-012 AC-012-3)

| Thuộc tính | Giá trị | Nguồn |
|---|---|---|
| Bên gọi | Chỉ OPERATOR_ROLE | US-012 AC-012-3, ghi chú HLD frd.md §2 |
| Điều kiện | Hợp đồng BnzaExVault đang tạm dừng | US-012 AC-012-3 |
| Người nhận | Chính địa chỉ của người dùng — không có tham số recipient | US-012 AC-012-3, ghi chú HLD frd.md §2 |
| Xác nhận đa chữ ký | KHÔNG yêu cầu | US-012 AC-012-3 (cập nhật HLD 2026-06-18) |
| Sự kiện phát | EmergencyRecovery | US-012 AC-012-3 |
| Trạng thái bot sau | error | US-012 AC-012-3 |

### F.2.4 Quy tắc chi tiết các điều kiện kích hoạt

| Điều kiện | Tiêu chí đầu vào | Chi tiết | Nguồn |
|---|---|---|---|
| T1 (circuit breaker kiệt sức) | circuit_breakers.state='open' VÀ reset_at gia hạn 3+ lần | Ngưỡng "kiệt sức" (3 lần gia hạn) không định nghĩa trong phần thân UC; chỉ định nghĩa trong FR-EXBOT-072 | FR-EXBOT-072 |
| T2 (margin critical + SAFE_MODE) | margin_status='critical' 2 lần liên tiếp → SAFE_MODE, không phục hồi được | Không thể phục hồi tự động nghĩa là 3 lần đối chiếu đều thất bại + HL không phản hồi | FR-EXBOT-072, FR-EXBOT-050 |
| T3 (3 stop trong 7 ngày) | lifecycle_state='hedge_stopped_cooldown' vào lần thứ 3 trong cửa sổ 7 ngày | Cửa sổ trượt; số lần stop được theo dõi ngầm từ rebalance_attempts hoặc các dòng close_operations | FR-EXBOT-072, FR-EXBOT-034 |
| T4 (partial_repair kiệt sức) | 3 lần thất bại liên tiếp của partial_repair cho cùng một sự kiện kích hoạt | Sau 3 lần thất bại, partial_repair worker tạo dòng close_operations | FR-EXBOT-036, FR-EXBOT-072 |
| T5 (admin buộc đóng) | Admin gọi /api/exbot/close | trigger_reason='admin_force_close' trong close_operations | FR-EXBOT-072, FR-EXBOT-090 |

---

## §F.3 Phân tích logic nghiệp vụ và luồng xử lý

### F.3.1 Luồng thành công — bot_safe_close (T1/T2/T3/T4/T5)

**Kích hoạt:** Một trong 5 điều kiện được xác nhận.
**Tác nhân:** Close Worker (hệ thống), Operator (bước fulfillRequest thủ công).
**Đầu vào:** bot_id, trigger_reason, địa chỉ ví người dùng.

| Bước | Hành động | Phản hồi hệ thống | Thay đổi trạng thái |
|---|---|---|---|
| 1 | Điều kiện kích hoạt; Close Worker tạo dòng close_operations (kind='bot_safe_close') | idempotency_key UNIQUE được kiểm tra — yêu cầu trùng bị từ chối im lặng | close_operations.state = requested |
| 2 | Close Worker giành lease UserLockDO (TTL=90s); gọi closeShortReduceOnlyIoc (đóng toàn bộ, target=0) trên HL | Lease được cấp; lệnh đóng short HL được gửi đi | close_operations.state = hedge_close_pending |
| 3 | Hủy lệnh stop qua replaceStopProtected(size=0) — giao thức §19.5 INV-STOP | Lệnh stop đã hủy trên HL | — |
| 4 | Đối chiếu: xác nhận kích thước vị thế HL = 0; ghi close_operations.state='hedge_closed' vào D1 | Vị thế HL xác nhận bằng 0 | close_operations.state = hedge_closed |
| 5 | Gọi vault.executeStrategy(RedeemStrategyV1, user, botId, params) — đóng LP NFT thông qua BnzaExPositionManager | LP NFT bị đốt | — |
| 6 | RedeemStrategyV1 định tuyến phí qua LpFeeOps (phí vận hành + phí hiệu suất tính bằng pair currency); trả vốn gốc bằng pair currency (tùy chọn convertPrincipalToUsdc) | Phí và vốn gốc được tách riêng | — |
| 7 | BnzaExPositionManager phát sự kiện PositionClosed; ghi close_operations.state='lp_closed' vào D1 | Sự kiện có thể quan sát bởi các indexer | close_operations.state = lp_closed |
| 8 | Close Worker gọi RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId) | Sự kiện RequestCreated phát on-chain | — |
| 9 | Ghi close_operations.state='redemption_queued' vào D1 | Phần thanh toán từ HL được đưa vào hàng đợi | close_operations.state = redemption_queued |
| 10 | Operator gọi RedemptionQueue.fulfillRequest(tokens, amounts) — lấy FIFO; safeTransferFrom(operator, user, amount) on-chain | Sự kiện RequestFulfilled phát on-chain | — |
| 11 | Ghi close_operations.state='done'; bots.status='closed' vào D1 | Bản ghi bot được đóng | close_operations.state = done; bots.status = closed |
| 12 | Thông báo gửi đến nhà đầu tư | "Bot safely closed. Funds have been returned to your wallet." | — |

### F.3.2 A1 — Không thể đóng Hedge

**Kích hoạt:** UC §4 A1 — Bước 3 (vị thế short HL không thể đóng hoàn toàn về 0; lỗi HL API hoặc lệnh bị từ chối).
**Quy tắc:** KHÔNG thực hiện đóng LP cho đến khi xác nhận hedge đã đóng.

| Bước | Hành động | Phản hồi hệ thống |
|---|---|---|
| 1 | Close Worker thử lại closeShortReduceOnlyIoc tối đa 3 lần | Thất bại lần thứ 3 kích hoạt leo thang cho admin |
| 2 | close_operations.state='residual_hl_liability' | Bot vào SAFE_MODE |
| 3 | Admin được thông báo về khoản nợ HL tồn đọng với số tiền chính xác | Admin phải giải quyết thủ công |

### F.3.3 A2 — Đóng LP bị hoàn lại (Revert)

**Kích hoạt:** UC §4 A2 — Bước 5 (vault.executeStrategy(RedeemStrategyV1) bị hoàn lại on-chain).

| Bước | Hành động | Phản hồi hệ thống |
|---|---|---|
| 1 | Thử lại tối đa 3 lần | Mỗi lần thử lại gọi cùng chiến lược |
| 2 | Lần thứ 3 thất bại | Leo thang cho admin; close_operations giữ nguyên tại lp_closed đang chờ |

### F.3.4 A3 — RedemptionQueue fulfillRequest bị trì hoãn / thất bại

**Kích hoạt:** UC §4 A3 — Bước 10 (Operator chưa gọi fulfillRequest, hoặc lệnh gọi on-chain thất bại).

| Điều kiện | Phản hồi hệ thống |
|---|---|
| Operator chưa gọi fulfillRequest | Yêu cầu vẫn trong hàng đợi; bots.status giữ nguyên 'closing' |
| Cuộc gọi on-chain thất bại | Yêu cầu vẫn trong hàng đợi; Operator thử lại; tiền người dùng không bị mất (on-chain) |

### F.3.5 A4 — Bot_safe_close lần thứ 3 trong 7 ngày

**Kích hoạt:** UC §4 A4 — Bước 1 (lần kích hoạt thứ 3 trong cửa sổ 7 ngày liên tiếp).

| Bước | Hành động | Phản hồi hệ thống |
|---|---|---|
| 1 | Điều kiện kích hoạt lần thứ 3 | Tạo dòng close_operations bình thường |
| 2 | Thực thi luồng đóng bình thường (hedge → LP → RedemptionQueue) | Thông báo leo thang cho admin gửi đồng thời |
| 3 | Sau khi fulfillRequest | bots.status='closed' |

### F.3.6 emergencyTransfer (US-012 AC-012-3)

**Kích hoạt:** Hợp đồng BnzaExVault đang tạm dừng; Operator (OPERATOR_ROLE) quyết định dùng luồng khẩn cấp.

| Bước | Hành động | Phản hồi hệ thống |
|---|---|---|
| 1 | OPERATOR_ROLE gọi emergencyTransfer(user, botId) | Tiền chuyển về chính địa chỉ của người dùng (không thể chuyển hướng) |
| 2 | Sự kiện EmergencyRecovery phát on-chain | Các indexer / cảnh báo phát hiện ngay lập tức |
| 3 | bot.status được đặt thành 'error' | Không yêu cầu xác nhận đa chữ ký |

### F.3.7 Admin buộc đóng bot đã closed (US-012 AC-012-4)

**Kích hoạt:** Admin cố buộc đóng bot có lifecycle_state='closed'.
**Phản hồi:** Hệ thống từ chối với thông báo "Bot {id} is already closed. No action needed." Không tạo dòng close_operations.

---

## §F.4 Tích hợp và nhất quán dữ liệu

| Tích hợp / Điểm dữ liệu | Tác động vào | Tác động ra | Nhất quán sau thao tác | Nguồn |
|---|---|---|---|---|
| HL API (closeShortReduceOnlyIoc, replaceStopProtected) | Trạng thái vị thế live trên Hyperliquid | Cập nhật hedge_legs.margin_status; xác nhận kích thước=0 | Kích thước vị thế HL phải = 0 trước khi thực hiện đóng LP | FR-EXBOT-073, FR-EXBOT-092 |
| UserLockDO (Durable Object) | Tất cả thao tác trên HL của mọi worker | Lease lease exclusive; TTL=90s tự hết hạn | Bất biến: không có hai worker nào được thực hiện đột biến HL đồng thời cho cùng một người dùng | FR-EXBOT-092 |
| BnzaExVault.executeStrategy(RedeemStrategyV1) (on-chain) | LP NFT token, vị thế Uniswap V3 | Phát PositionClosed; vốn gốc và phí được chuyển về người dùng | LP NFT bị đốt; tiền được chuyển; trạng thái close_operations ghi lp_closed | FR-EXBOT-073, UC §3 |
| LpFeeOps (định tuyến phí) | Số tiền trả về của RedeemStrategyV1 | Phí vận hành + hiệu suất được khấu trừ trước khi trả vốn gốc | Phí được chia tách từ vốn gốc; tổng = vốn gốc + phí | UC §3 bước 6 |
| RedemptionQueue.createRequest (on-chain) | Bộ đếm hàng đợi FIFO | Phát RequestCreated; lưu (user, botId, tokenId, hlPortionId) | Yêu cầu không thể xóa; Operator phải fulfillRequest để hoàn thành | FR-EXBOT-073, UC §3 bước 8-9 |
| RedemptionQueue.fulfillRequest (on-chain) | Số dư của Operator (tokens, amounts) | safeTransferFrom on-chain đến địa chỉ ví người dùng; phát RequestFulfilled | Tiền người dùng không bị mất dù Operator bị trì hoãn; FIFO được thực thi bởi hợp đồng | FR-EXBOT-073, UC §3 bước 10-11 |
| Bảng D1 close_operations | Không | Chuỗi chuyển trạng thái: requested → hedge_close_pending → hedge_closed → lp_closed → redemption_queued → done (hoặc residual_hl_liability) | idempotency_key UNIQUE ngăn chặn các dòng trùng lặp; mỗi bước chỉ ghi vào bảng D1 sau khi thao tác ngoài xác nhận thành công | FR-EXBOT-072, FR-EXBOT-073 |
| Bảng D1 bots | Không | bots.status='closing' (bắt đầu), 'closed' (sau done) hoặc 'error' (sau emergencyTransfer) | bots.status không được đặt thành 'closed' cho đến khi fulfillRequest xác nhận; không có trạng thái trung gian thiếu nhất quán | FR-EXBOT-073, US-012 AC-012-3 |

---

## §F.5 Các ứng viên Tiêu chí Chấp nhận

| AC | Kịch bản | Đầu vào | Kết quả mong đợi | Loại | Nguồn |
|---|---|---|---|---|---|
| AC-01 | Luồng thành công T1 (circuit breaker kiệt sức) | bot_id hợp lệ, T1 kích hoạt | close_operations tiến qua tất cả 6 trạng thái; bots.status='closed'; thông báo gửi cho nhà đầu tư | Luồng thành công | FR-EXBOT-072, FR-EXBOT-073, US-009 AC-009-1 |
| AC-02 | Luồng thành công T5 (admin buộc đóng) | Admin gọi /api/exbot/close | Giống AC-01; trigger_reason='admin_force_close' trong close_operations | Luồng thành công | FR-EXBOT-072, FR-EXBOT-090, US-012 AC-012-1 (cần xác nhận — US-012 cũ) |
| AC-03 | Hedge close thất bại sau 3 lần thử (A1) | Lỗi HL API | close_operations.state='residual_hl_liability'; bot vào SAFE_MODE; admin được thông báo với số tiền chính xác; LP không bị đóng | Luồng thất bại | FR-EXBOT-073, US-009 AC-009-2 |
| AC-04 | LP close bị hoàn lại (A2) | vault.executeStrategy hoàn lại sau 3 lần thử | Leo thang cho admin; close_operations giữ nguyên tại lp_closed đang chờ; hedge không bị tái mở | Luồng thất bại | FR-EXBOT-073 |
| AC-05 | fulfillRequest bị trì hoãn (A3) | Operator chưa gọi fulfillRequest | Yêu cầu còn trong hàng đợi; bots.status='closing'; tiền người dùng không bị mất | Luồng thất bại | FR-EXBOT-073, US-009 AC-009-4 |
| AC-06 | Bot_safe_close lần thứ 3 trong 7 ngày (A4) | bot_id, lần kích hoạt thứ 3 trong cửa sổ 7 ngày | Luồng đóng bình thường thực thi; thông báo leo thang admin gửi đồng thời | Luồng thay thế | FR-EXBOT-072, US-009 AC-009-3 |
| AC-07 | emergencyTransfer — chỉ OPERATOR_ROLE, hợp đồng tạm dừng | OPERATOR_ROLE gọi emergencyTransfer(user, botId) | Tiền về đúng địa chỉ người dùng; sự kiện EmergencyRecovery phát; bot.status='error'; không yêu cầu đa chữ ký | Bảo mật / khẩn cấp | US-012 AC-012-3 |
| AC-08 | Admin buộc đóng bot đã closed | Admin gọi /api/exbot/close, bot.lifecycle_state='closed' | Hệ thống từ chối với thông báo "Bot {id} is already closed. No action needed." Không tạo dòng close_operations | Kiểm tra biên | US-012 AC-012-4 |

---

## §10 Kết quả kiểm tra

### §10.1 Danh sách vấn đề

| ID vấn đề | Loại | Mức độ | Vùng ảnh hưởng | Truy nguyên nguồn | Phát hiện | Tác động đến Tester | Câu hỏi / Gợi ý sửa đổi | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| I-001 | MISSING_INFO | Blocker | §F.3 Phân tích luồng | UC §3 bước 2–3 vs FR-EXBOT-073 bước 2; states.md bảng close_operations | Trạng thái close_operations `hedge_close_pending` được định nghĩa trong cả states.md lẫn FR-EXBOT-073 là trạng thái trong quá trình đóng vị thế short HL, nhưng UC §3 hoàn toàn không đề cập trạng thái này — UC nhảy thẳng từ bước 1 (tạo close_operations với state=requested) sang bước 2 (giành lease + đóng HL) mà không có bước chuyển trạng thái trung gian. | Tester không thể xác định khi nào hedge_close_pending được đặt cũng như không thể kiểm chứng nó trong kiểm thử tích hợp. Chuỗi chuyển trạng thái trong trace kiểm thử sẽ thiếu một bước chuyển. | BA/Tech Lead: thêm một bước tường minh vào UC §3 giữa bước 1 và bước 2 để ghi close_operations.state='hedge_close_pending', đồng nhất với FR-EXBOT-073. | Mở |
| I-002 | CROSS_SOURCE_CONFLICT | Blocker | §F.3 Phân tích luồng | US-EXBOT-012 AC-012-1 vs FR-EXBOT-070 (spec.md + frd.md, cập nhật 2026-06-18) | US-012 AC-012-1 (luồng thành công của admin force-close) tham chiếu `BnzaExVault.vaultClose` và `uninvested_balances` — cả hai đã bị loại bỏ bởi HLD-2026-06-18. FR-EXBOT-070 (tài liệu chuẩn) khẳng định "Không sử dụng uninvested_balances hoặc uninvestedBalanceOf API" và mô tả executeStrategy(RedeemStrategyV1) là phương thức đóng LP. | Lập trình viên đọc US-012 sẽ xây dựng lời gọi vaultClose() và bảng uninvested_balances — cả hai đều không tồn tại trong kiến trúc HLD-2026-06-18. Kiểm thử tích hợp cho admin force-close sẽ xác minh một lời gọi on-chain sai. | BA: cập nhật US-012 AC-012-1 để thay vaultClose/uninvested_balances bằng đường dẫn executeStrategy(RedeemStrategyV1) + RedemptionQueue, nhất quán với AC-012-3 và FR-EXBOT-073. | Mở |
| I-003 | CROSS_SOURCE_CONFLICT | Blocker | §0 Phạm vi kiểm tra | usecases/index.md dòng UC-EXBOT-bot-safe-close vs phần thân UC (cập nhật 2026-06-18); FR-EXBOT-070 | Mô tả trong index.md vẫn còn là "System hedge-first close + USDC park + automatic re-entry closed loop" — đây là mô tả trước HLD-2026-06-18. Phần thân UC đã được cập nhật 2026-06-18 để loại bỏ park/re-entry. Ngoài ra, FR Trace của index.md bao gồm FR-071 nhưng UC §7 FR Trace thì không. | Người đọc dùng index.md làm tài liệu tham khảo nhanh sẽ hiểu sai phạm vi UC. Sự không khớp về trace FR-071 dẫn đến phạm vi kiểm thử không đầy đủ. | BA: (1) cập nhật mô tả index.md phản ánh luồng hiện tại; (2) xác nhận FR-EXBOT-071 có áp dụng cho UC này hay chỉ cho user_redeem. | Mở |
| I-004 | CROSS_SOURCE_CONFLICT | Blocker | §F.3 Phân tích luồng | srs/flows.md F-05 (cập nhật lần cuối 2026-06-12) vs srs/spec.md FR-EXBOT-070/073 + srs/states.md + frd.md (tất cả cập nhật 2026-06-18) | flows.md F-05 vẫn còn toàn bộ vòng lặp park/re-entry: vaultClose(tokenId, dest=UNINVESTED), sự kiện FundsParked, lifecycle_state=cooldown (60 phút), uninvestedBalanceOf(user, botId), trạng thái parked, và vòng lặp REENTRY worker. Tất cả đều mâu thuẫn với spec.md FR-EXBOT-070/073 và states.md ghi chú HLD-2026-06-18. Ngoài ra, frd.md FR-EXBOT-031 vẫn còn tham chiếu "§16.7 cooldown closed loop". | Lập trình viên hoặc tester đọc flows.md F-05 sẽ xây dựng/kiểm thử re-entry worker và trạng thái cooldown không còn tồn tại. Dữ liệu kiểm thử với lifecycle_state='cooldown' hoặc 'parked' sẽ kiểm thử hành vi không thể xảy ra. | BA: (1) cập nhật flows.md F-05 thay thế park/re-entry bằng đường dẫn executeStrategy(RedeemStrategyV1) → RedemptionQueue FIFO; (2) cập nhật frd.md FR-EXBOT-031 để xóa tham chiếu §16.7. | Mở |
| I-005 | MISSING_INFO | Major | §F.2 Điều kiện và quy tắc | FR-EXBOT-072; UC §2 điều kiện tiên quyết | UC §2 điều kiện tiên quyết liệt kê 4 điều kiện kích hoạt nhưng bỏ qua điều kiện thứ 5 từ FR-EXBOT-072: partial_repair kiệt sức (partial_repair consumer thất bại 3 lần liên tiếp cho cùng một sự kiện kích hoạt). Ràng buộc UNIQUE của idempotency_key (ngăn chặn dòng close_operations thứ hai khi đã có yêu cầu đang chờ) cũng không có trong điều kiện tiên quyết. | Tester không thể thiết kế test case cho điều kiện kích hoạt partial_repair-kiệt-sức (T4). Điều kiện idempotency bị bỏ sót có nghĩa là kịch bản trigger trùng lặp không có cơ sở trong UC. | BA: thêm partial_repair kiệt sức là điều kiện kích hoạt thứ 5 trong UC §2, và ghi chú ràng buộc idempotency_key. | Mở |
| I-006 | MISSING_INFO | Major | §F.3 Phân tích luồng | UC §3 bước 5–6; FR-EXBOT-073 | UC §3 bước 5 gọi vault.executeStrategy(RedeemStrategyV1, user, botId, params) nhưng cấu trúc tham số `params` không được định nghĩa. Bước 6 đề cập "optional convertPrincipalToUsdc" mà không chỉ định khi nào cờ này là true hay false, ai thiết lập nó, hoặc giá trị mặc định là gì. FR-EXBOT-073 (SRS) cũng không định nghĩa cấu trúc params. | Tester không thể viết kiểm thử tích hợp cho bước đóng LP mà không biết lược đồ params. Một bài kiểm thử cho "phí trả về theo cặp tiền tệ vs USDC" đòi hỏi phải biết tham số nào kiểm soát điều này. | BA/Tech Lead: định nghĩa cấu trúc params đầy đủ cho RedeemStrategyV1, bao gồm kiểu dữ liệu, giá trị mặc định, và khi nào convertPrincipalToUsdc là true. | Mở |
| I-007 | INTERNAL_INCONSISTENCY | Major | §F.3 Phân tích luồng | UC §4 A1 vs US-009 AC-009-2 vs FR-EXBOT-073 | Trạng thái được giữ khi đóng HL thất bại được mô tả không nhất quán: UC §4 A1 nói "close_operations.state='residual_hl_liability'"; US-009 AC-009-2 nói "close_operations.state giữ nguyên tại 'hedge_close_pending'"; FR-EXBOT-073 nói "thử lại tối đa 3 lần trước khi leo thang cho admin và giữ tại hedge_close_pending". Ranh giới giữa hedge_close_pending (trong quá trình thử lại) và residual_hl_liability (sau khi cạn kiệt tất cả lần thử lại) không được định nghĩa trong UC. | Tester không thể xác định trạng thái nào cần kiểm chứng tại thời điểm nào trong đường dẫn thất bại. Kiểm thử tích hợp có thể xác minh sai trạng thái. | BA: làm rõ trong UC §4 A1 rằng hedge_close_pending được giữ trong 3 lần thử, sau đó chuyển sang residual_hl_liability sau khi tất cả lần thử đều thất bại. Cập nhật US-009 AC-009-2 để phù hợp. | Mở |
| I-008 | MISSING_INFO | Major | §0 Phạm vi kiểm tra | FR-EXBOT-034; FR-EXBOT-036; UC §7 FR Trace; index.md FR Trace | UC §7 FR Trace (FR-070, FR-072, FR-073) thiếu FR-EXBOT-034 (Stop Cooldown — định nghĩa điều kiện kích hoạt T3 "3 lần stop trong 7 ngày") và FR-EXBOT-036 (Partial Repair — định nghĩa điều kiện kích hoạt T4). Index.md cũng bao gồm FR-071 không có trong UC §7. | Tester sử dụng UC §7 làm ranh giới phạm vi sẽ bỏ sót hoàn toàn các đường dẫn kích hoạt T3 và T4. | BA: thêm FR-034 và FR-036 vào UC §7 FR Trace; giải quyết sự không khớp FR-071. | Mở |
| I-009 | MISSING_INFO | Major | §F.1 Kiểm kê | FR-EXBOT-072; FR-EXBOT-040; erd.md circuit_breakers | Điều kiện kích hoạt T1 (circuit breaker kiệt sức) được định nghĩa trong FR-EXBOT-072 là "reset_at gia hạn 3 lần trở lên mà không có probe thành công." Tuy nhiên, bảng circuit_breakers trong erd.md không có cột nào để theo dõi số lần gia hạn (không có extension_count hoặc tương tự). Máy trạng thái circuit breaker (FR-EXBOT-040) không mô tả cách theo dõi số lần gia hạn. | Tester không thể tái tạo điều kiện kích hoạt T1 trong môi trường kiểm thử mà không biết mô hình dữ liệu theo dõi số lần gia hạn. | BA/Tech Lead: xác định rõ extension_count có được thêm vào bảng circuit_breakers hay không, hoặc giải thích cách điều kiện "3 lần gia hạn" được đánh giá. | Mở |
| I-010 | MISSING_INFO | Minor | §F.3 Phân tích luồng | UC §3 bước 2; FR-EXBOT-092; FR-EXBOT-026 | UC §3 bước 2 nói "giành lease UserLockDO" nhưng không chỉ định hành vi khi việc giành lock thất bại (acquired=false). FR-EXBOT-026 định nghĩa hành vi xếp lại hàng đợi cho hedge-sync khi thất bại lock, nhưng không có quy tắc tương đương cho bot_safe_close. Về lý thuyết, một hedge-sync khác của cùng người dùng có thể đang giữ lock khi bot_safe_close kích hoạt. | Tester không thể thiết kế bài kiểm thử cho tranh chấp lock trong khi bot_safe_close đang diễn ra. Nếu close worker không thể giành lock, hành vi hệ thống là không xác định. | BA: thêm luồng thay thế trong UC §4 cho trường hợp thất bại giành UserLockDO trong ngữ cảnh bot_safe_close: xếp lại hàng đợi, chờ đợi, hay leo thang? | Mở |
| I-011 | MISSING_INFO | Minor | §F.1 Kiểm kê | FR-EXBOT-072; erd.md bảng close_operations | FR-EXBOT-072 khẳng định "Tất cả năm đường dẫn kích hoạt đều tạo dòng close_operations với trigger_reason được điền." Tuy nhiên, bảng close_operations trong erd.md KHÔNG bao gồm cột trigger_reason. Cột này xuất hiện trong yêu cầu SRS nhưng vắng mặt trong lược đồ. | Lập trình viên xây dựng migration D1 sẽ không biết cần thêm cột trigger_reason. Tester kiểm chứng việc ghi trigger_reason không có cơ sở lược đồ. | BA: thêm cột trigger_reason vào close_operations trong erd.md, hoặc ghi lại cách tiếp cận thay thế. | Mở |
| I-012 | AMBIGUOUS_WORDING | Minor | §0 Phạm vi kiểm tra | Tiêu đề file UC vs changelog UC | Tiêu đề UC "UC-EXBOT-bot-safe-close: System-Initiated Safe Close + Auto Re-Entry" vẫn còn "Auto Re-Entry" đã bị loại bỏ theo changelog 2026-06-18. | Gây nhầm lẫn nhỏ về khả năng đọc cho bất kỳ ai đọc qua tiêu đề UC. | BA: cập nhật tiêu đề UC để loại bỏ "Auto Re-Entry". | Mở |

---

### §10.2 Phụ thuộc

| Phụ thuộc | Loại | Tác động | Nguồn |
|---|---|---|---|
| flows.md F-05 chưa được cập nhật lên HLD-2026-06-18 | Tài liệu nội bộ cũ | Blocker: developer/tester đọc flows.md F-05 sẽ xây dựng/kiểm thử vòng lặp park/re-entry không còn tồn tại | srs/flows.md (cập nhật lần cuối 2026-06-12) |
| US-012 AC-012-1 chưa được cập nhật lên HLD-2026-06-18 | Tài liệu nội bộ cũ | Blocker: tham chiếu BnzaExVault.vaultClose và uninvested_balances đã bị loại bỏ | userstories/us-012.md |
| Cấu trúc params RedeemStrategyV1 chưa được định nghĩa | Thiếu thông tin | Tester không thể viết kiểm thử tích hợp cho bước đóng LP | FR-EXBOT-073, UC §3 bước 5–6 |
| Mô hình dữ liệu theo dõi số lần gia hạn circuit breaker chưa rõ ràng | Thiếu thông tin | Tester không thể tái tạo điều kiện kích hoạt T1 | erd.md circuit_breakers, FR-EXBOT-040 |
| Hành vi UserLockDO khi thất bại giành lock chưa được định nghĩa cho bot_safe_close | Thiếu thông tin | Tester không thể thiết kế bài kiểm thử tranh chấp lock | FR-EXBOT-092, UC §3 bước 2 |

---

### §10.3 Tóm tắt kiểm tra

#### Bảng điểm

| # | Vùng đánh giá | Điểm tối đa | Điểm đạt được | Trạng thái | Vấn đề chính |
|---:|---|---|---|---|---|
| 1 | Kiểm kê Chức năng / Thao tác & Đối tượng dữ liệu | 20 | 15 | Một phần | I-008: FR trace thiếu FR-034, FR-036; I-011: cột trigger_reason vắng mặt trong ERD |
| 2 | Thuộc tính Đối tượng dữ liệu / Trạng thái, Quy tắc nghiệp vụ, Kiểm chứng & Thông báo | 25 | 17 | Một phần | I-007: ranh giới trạng thái hedge_close_pending vs residual_hl_liability chưa rõ ràng; I-009: ngưỡng circuit breaker kiệt sức không thể theo dõi trong D1 |
| 3 | Phân tích Logic nghiệp vụ & Luồng xử lý | 25 | 13 | Một phần (bị chặn) | I-001: trạng thái hedge_close_pending thiếu trong luồng UC [Blocker]; I-002: US-012 AC-012-1 lỗi thời với vaultClose/uninvested_balances [Blocker]; I-005: điều kiện kích hoạt T4 (partial_repair) thiếu trong UC §2; I-007: ranh giới trạng thái thất bại chưa rõ ràng |
| 4 | Tích hợp chức năng & Nhất quán dữ liệu | 15 | 11 | Một phần | I-010: tranh chấp UserLockDO trong bot_safe_close chưa được ghi lại; I-006: params RedeemStrategyV1 chưa được định nghĩa |
| 5 | Chất lượng Tài liệu UC / Đặc tả | 15 | 5 | Yếu (bị chặn) | I-003: mô tả index.md lỗi thời [Blocker]; I-004: flows.md F-05 lỗi thời với vòng lặp park/re-entry [Blocker]; I-012: tiêu đề UC lỗi thời |

**Tổng cộng: 61 / 100**

#### Điều chỉnh điểm tự động (Auto-cap)

- Vùng 3 bị chặn ở mức 52% (13/25): Blocker I-001 ngăn cản việc hiểu bước chuyển trạng thái close_operations quan trọng. Quy tắc: Blocker → vùng ảnh hưởng tối đa 40% điểm tối đa (10/25). Tuy nhiên nhiều vấn đề Major (I-005, I-007) cũng làm giảm điểm vùng 3 độc lập. Điểm đặt ở 13/25 phản ánh tác động kết hợp.
- Vùng 5 bị chặn ở mức 33% (5/15): Hai Blocker (I-003, I-004) liên quan đến mâu thuẫn chưa giải quyết giữa các nguồn ảnh hưởng đến hành vi mong đợi. Quy tắc: mâu thuẫn chưa giải quyết giữa các nguồn → Vùng 5 tối đa 8/15. Tiếp tục bị chặn từ các mô tả lỗi thời → 5/15.

#### Các vấn đề Blocker (điều kiện tự động thất bại)

| ID | Mức độ | Mô tả |
|---|---|---|
| I-001 | Blocker | Trạng thái hedge_close_pending vắng mặt trong luồng UC §3 — tạo ra sự không nhất quán với FR-EXBOT-073 |
| I-002 | Blocker | US-012 AC-012-1 tham chiếu vaultClose / uninvested_balances lỗi thời — mâu thuẫn trực tiếp với FR-EXBOT-070/073 |
| I-003 | Blocker | Mô tả UC trong index.md vẫn còn là "USDC park + automatic re-entry closed loop" — mâu thuẫn với phần thân UC và SRS |
| I-004 | Blocker | flows.md F-05 vẫn còn toàn bộ vòng lặp park/re-entry mâu thuẫn với spec.md + states.md + frd.md (tất cả cập nhật 2026-06-18) |

#### Kết luận

**Điểm: 61 / 100 — Chưa sẵn sàng (Not Ready)**

4 vấn đề Blocker chưa được giải quyết. Không thể bắt đầu thiết kế kiểm thử cho đến khi:
1. US-012 AC-012-1 được cập nhật để thay vaultClose/uninvested_balances bằng executeStrategy(RedeemStrategyV1) + RedemptionQueue.
2. flows.md F-05 được cập nhật để phản ánh việc chuyển thẳng sang trạng thái closed (không có re-entry worker).
3. Mô tả trong index.md được cập nhật.
4. UC §3 được bổ sung tường minh bước chuyển trạng thái hedge_close_pending.

Ngoài ra, 3 vấn đề Major (I-005, I-006, I-007) làm giảm phạm vi các kịch bản có thể kiểm thử cho điều kiện kích hoạt T4, params đóng LP, và ranh giới trạng thái thất bại. Các vấn đề này cần được giải quyết để đạt trạng thái Có thể sẵn sàng có điều kiện sau khi các Blocker được xử lý.
