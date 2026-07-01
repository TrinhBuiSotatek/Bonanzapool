# Test Scenarios — UC-EXBOT-bot-start Khởi động ExBot

> Nguồn: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260630_v1.md Hỏi & Đáp: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_questions_20260701_v2.md Ngày tạo: 2026-07-01 Kiến trúc/Miền: Cloudflare Workers (ExBot Worker + Key-Provision Worker) + AWS KMS (Signing Lambda) + Hyperliquid perp API + BnzaExVault on-chain (Base + Optimism) + Cloudflare D1 (control_db + state_db_shard) + Queues (key-provision, bot-start) + Durable Objects (HLRateLimitDO)

---

## UC-EXBOT-bot-start — Khởi động ExBot (hệ thống tự kích hoạt sau khi nạp tiền on-chain)

---

### Scenario ID: TS_UC-EXBOT-bot-start_001

**Scenario Title:** Luồng chính — toàn bộ quy trình khởi động bot từ key-provision đến trạng thái active **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-001, FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-004, FR-EXBOT-020, FR-EXBOT-025, FR-EXBOT-030, FR-EXBOT-031, FR-EXBOT-080 **Test Type:** End-to-End **Description:** Kích hoạt toàn bộ luồng khởi động bot cho người dùng chưa có ExBot đang hoạt động, đủ ký quỹ HL isolated (>= yêu cầu × 2.0), hàng `hl_agent_keys.key_status='active'` đã được xác nhận, phí builder đã xác nhận (5bps), và mô phỏng mint LP thành công. Hệ thống phải đi qua đúng 9 trạng thái vòng đời theo thứ tự (preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active), không bỏ qua trạng thái nào, mỗi chuyển đổi được lưu nguyên tử vào D1. Sau khi đạt `active`: `bots.lifecycle_state='active'`, `bots.status='active'`, `positions.custodian='vault'` với tokenId được điền, `hedge_legs.stop_price` và `stop_cloid` được điền (chuỗi BigDecimal), và không có khóa bí mật dạng plaintext trong `hl_agent_keys`. **Test Focus:** Luồng chính **Note:** Đây là kịch bản end-to-end quan trọng nhất — xác nhận toàn bộ 9 bước lifecycle chạy đúng thứ tự, không bước nào bị bỏ qua hoặc lặp lại, và dữ liệu cuối cùng trên D1 đầy đủ trước khi bot đi vào vận hành.

---

### Scenario ID: TS_UC-EXBOT-bot-start_002

**Scenario Title:** Key-provision — KMS tạo master key và agent key, khóa bí mật không bao giờ rời khỏi HSM **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-080, NFR-EXBOT-006 **Test Type:** Chức năng **Description:** Kích hoạt luồng key-provision sau sự kiện nạp tiền on-chain. Key-Provision Worker phải gọi KMS `GenerateKeyPair` hai lần (master key, sau đó agent key). Kiểm tra: (1) KMS chỉ trả về địa chỉ public (`hl_user_address`, `agent_address`) — không có khóa bí mật nào xuất hiện trong phản hồi worker, hàng D1, hoặc log ứng dụng; (2) hàng `hl_agent_keys` được ghi với `key_status='active'`, `hl_user_address` và `agent_address` được điền; (3) không có giá trị khóa bí mật thô trong bất kỳ luồng log nào. **Test Focus:** Luồng chính **Note:** Kiểm tra yêu cầu bảo mật cốt lõi: khóa bí mật phải ở lại trong AWS KMS HSM, D1 chỉ lưu địa chỉ public. Bất kỳ rò rỉ nào vào log hoặc D1 đều là lỗ hổng bảo mật nghiêm trọng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_003

**Scenario Title:** Key-provision — đăng ký HL approveAgent thành công trước khi key_status được đặt thành active **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-080 **Test Type:** Chức năng **Description:** Sau khi KMS tạo cả hai cặp khóa, Key-Provision Worker gọi HL `approveAgent(hl_user_address, agent_address)`. Kiểm tra rằng `hl_agent_keys.key_status` chỉ được đặt thành `'active'` SAU KHI HL xác nhận đăng ký agent — không phải trước. Nếu xác nhận HL đang chờ, `key_status` phải giữ nguyên `'provisioning'` và chưa có job `bot-start` nào được thêm vào hàng đợi. **Test Focus:** Chuyển đổi trạng thái **Note:** Kiểm tra tính đúng thứ tự của chuyển đổi trạng thái: nếu `key_status` được đặt thành `active` trước khi HL xác nhận, bot có thể khởi động với một agent key chưa được đăng ký và sẽ thất bại khi đặt lệnh.

---

### Scenario ID: TS_UC-EXBOT-bot-start_004

**Scenario Title:** Key-provision — lỗi KMS trong quá trình tạo khóa kích hoạt thử lại và cảnh báo admin sau 3 lần thất bại **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-080, IC-EXBOT-005 **Test Type:** Chức năng **Description:** Mô phỏng `ThrottlingException` của KMS (hoặc lỗi tương đương) trong quá trình `GenerateKeyPair`. Key-Provision Worker phải thử lại tối đa 3 lần với exponential backoff. Sau lần thất bại thứ 3, phải gửi cảnh báo admin. Kiểm tra: (1) không có hàng `hl_agent_keys` nào được tạo với `key_status='active'`; (2) thông báo admin được kích hoạt; (3) không có job `bot-start` nào được thêm vào hàng đợi. **Test Focus:** Lỗi/Ngoại lệ **Note:** Xác nhận cơ chế retry và cảnh báo: nếu KMS không khả dụng tạm thời, hệ thống không được để người dùng chờ vô hạn hoặc tạo dữ liệu không nhất quán — sau 3 lần thất bại phải có người được thông báo.

---

### Scenario ID: TS_UC-EXBOT-bot-start_005

**Scenario Title:** Key-provision — lỗi HL approveAgent giữ key_status ở provisioning và kích hoạt thử lại **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-080 **Test Type:** Chức năng **Description:** Mô phỏng lỗi gọi HL `approveAgent` sau khi cả hai cặp khóa KMS đã được tạo. Kiểm tra: (1) `hl_agent_keys.key_status` giữ nguyên `'provisioning'` (không đặt thành `'active'`); (2) Key-Provision Worker thêm lại vào hàng đợi retry qua key-provision queue; (3) cảnh báo admin được gửi khi vi phạm SLA; (4) không có job `bot-start` nào được thêm vào hàng đợi cho đến khi `key_status='active'` được xác nhận. **Test Focus:** Lỗi/Ngoại lệ **Note:** Trường hợp lỗi một phần: KMS đã tạo khóa nhưng HL chưa đăng ký agent. Trạng thái `provisioning` là rào chắn để ngăn bot khởi động với agent key chưa được HL công nhận.

---

### Scenario ID: TS_UC-EXBOT-bot-start_006

**Scenario Title:** Key-provision — thông điệp hàng đợi trùng lặp không tạo ra cặp khóa thứ hai **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-011, FR-EXBOT-080, BR-EXBOT-012 **Test Type:** Chức năng **Description:** Gửi cùng một thông điệp hàng đợi `key-provision` hai lần (mô phỏng Cloudflare Queue giao ít nhất một lần). Kiểm tra: (1) lần giao thứ hai gặp xung đột ràng buộc UNIQUE trên `queue_idempotency.message_id` và thoát ngay lập tức mà không gọi KMS lần nữa; (2) chỉ có một hàng `hl_agent_keys` với `key_status='active'` tồn tại cho người dùng; (3) không có job `bot-start` thứ hai nào được thêm vào hàng đợi. **Test Focus:** Tính đồng nhất/Đồng thời **Note:** Cloudflare Queue có cơ chế giao ít nhất một lần (at-least-once delivery) — thông điệp có thể được giao lại khi worker timeout hoặc crash. `queue_idempotency` là rào chắn duy nhất ngăn việc tạo hai cặp khóa cho cùng một người dùng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_007

**Scenario Title:** Key-provision — ràng buộc DB đảm bảo chỉ có một hàng agent key active mỗi người dùng **UC Reference:** UC-EXBOT-bot-start **Req-ID:** BR-EXBOT-012, FR-EXBOT-080 **Test Type:** Dữ liệu/Trạng thái **Description:** Cố gắng chèn hàng `hl_agent_keys` thứ hai với `key_status='active'` cho cùng một người dùng khi đã có một hàng `active` tồn tại (mô phỏng race condition hoặc tái cấp phát khóa sai cấu hình). Kiểm tra rằng ràng buộc ở cấp DB (BR-EXBOT-012: chỉ một hàng `active` mỗi người dùng tại bất kỳ thời điểm nào) từ chối lần chèn thứ hai, và hàng active hiện tại vẫn còn nguyên vẹn. **Test Focus:** Chuyển đổi trạng thái **Note:** Ràng buộc này bảo vệ tính toàn vẹn của hệ thống ký lệnh: nếu tồn tại hai agent key active, Signing Lambda không biết dùng khóa nào để ký lệnh HL và có thể gây xung đột.

---

### Scenario ID: TS_UC-EXBOT-bot-start_008

**Scenario Title:** Preflight bước 1 — chính sách một bot chặn khởi động khi người dùng đã có ExBot đang hoạt động **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-001, BR-EXBOT-001 **Test Type:** Chức năng **Description:** Kích hoạt thông điệp hàng đợi `bot-start` cho người dùng đã có bot với `status='active'` trong `bot_registry`. Kiểm tra: (1) E-EXBOT-001 ("You already have an active ExBot. Close or wait for the existing bot to finish.") được trả về; (2) không có bản ghi bot mới nào được tạo trong D1; (3) số lượng bản ghi trong `bot_registry` cho người dùng vẫn là 1. **Test Focus:** Luồng thay thế **Note:** Chính sách một bot (one-bot policy) là rào chắn nghiệp vụ cơ bản: một người dùng không thể vận hành hai ExBot đồng thời vì điều đó sẽ tạo ra hai vị thế short hedge độc lập không được quản lý phối hợp.

---

### Scenario ID: TS_UC-EXBOT-bot-start_009

**Scenario Title:** Preflight bước 1 — chính sách một bot tính cả trạng thái paused, closing, safe_mode, và error **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-001, BR-EXBOT-001 **Test Type:** Chức năng **Description:** Thực hiện 4 kịch bản riêng biệt: kích hoạt job `bot-start` khi người dùng có bot với `status='paused'`; sau đó `status='closing'`; sau đó `status='safe_mode'`; sau đó `status='error'`. Trong mỗi trường hợp, kiểm tra E-EXBOT-001 được trả về và không có bản ghi bot mới nào được tạo. Cả bốn trạng thái đều được tính vào giới hạn một bot theo BR-EXBOT-001. **Test Focus:** Luồng thay thế **Note:** Bốn trạng thái này đều chỉ ra bot chưa kết thúc chu kỳ — có thể còn vị thế LP mở hoặc hedge đang hoạt động trên HL. Cho phép tạo bot mới trong các trạng thái này sẽ dẫn đến tình trạng hai LP position và hai hedge tồn tại đồng thời.

---

### Scenario ID: TS_UC-EXBOT-bot-start_010

**Scenario Title:** Preflight bước 1 — cho phép khởi động khi bot duy nhất của người dùng có status='closed' **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-001, BR-EXBOT-001 **Test Type:** Chức năng **Description:** Kích hoạt job `bot-start` cho người dùng có một bot duy nhất với `status='closed'`. Kiểm tra preflight bước 1 thành công (số lượng query cho các trạng thái không hợp lệ = 0) và luồng tiến tới preflight bước 2. Bot đã `closed` không được chặn lần khởi động mới. **Test Focus:** Luồng thay thế **Note:** `closed` là trạng thái kết thúc — LP đã được rút, hedge đã được đóng, vòng đời hoàn tất. Đây là trạng thái duy nhất cho phép người dùng khởi động bot mới mà không vi phạm chính sách một bot.

---

### Scenario ID: TS_UC-EXBOT-bot-start_011

**Scenario Title:** Preflight bước 2 — kiểm tra ký quỹ thành công ở đúng 2.0× ký quỹ yêu cầu (biên giới) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-061, FR-EXBOT-002 **Test Type:** Chức năng **Description:** Đặt số dư HL isolated margin của người dùng bằng đúng `(lpEthAmount × hedgeRatio × hlOraclePrice / leverage) × 2.0`. Kiểm tra preflight bước 2 thành công và luồng tiến tới bước 3. Công thức phải dùng `hlOraclePrice` cụ thể (không phải HL mark price hay giá pool Uniswap). **Test Focus:** Biên giới **Note:** Kiểm tra biên chính xác tại ngưỡng 2.0×: bất kỳ giá trị nào nhỏ hơn dù chỉ $1 sẽ bị từ chối (xem TS_012). Công thức phải dùng `hlOraclePrice` — dùng mark price hay giá Uniswap sẽ cho kết quả sai trong điều kiện thị trường biến động.

---

### Scenario ID: TS_UC-EXBOT-bot-start_012

**Scenario Title:** Preflight bước 2 — kiểm tra ký quỹ thất bại khi thiếu $1 so với 2.0× yêu cầu (không đủ) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-061, FR-EXBOT-002 **Test Type:** Chức năng **Description:** Đặt số dư HL isolated margin của người dùng bằng `(yêu cầu × 2.0) − $1`. Kiểm tra: (1) E-EXBOT-002 được trả về với số tiền yêu cầu đúng, số tiền hiện tại, và mức thiếu hụt ($1); (2) không có bản ghi bot nào được tạo; (3) preflight dừng ở bước 2. **Test Focus:** Biên giới **Note:** Xác nhận kiểm tra biên âm: số tiền thiếu hụt trong thông báo lỗi phải chính xác để người dùng biết cần nạp thêm bao nhiêu — không được làm tròn hay xấp xỉ.

---

### Scenario ID: TS_UC-EXBOT-bot-start_013

**Scenario Title:** Preflight bước 2 — HL API không khả dụng trả về E-EXBOT-008 và chặn khởi động mà không tạo bản ghi bot **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, E-EXBOT-008 **Test Type:** Chức năng **Description:** Mô phỏng HL API không khả dụng khi ExBot Worker lấy `marginSummary` trong preflight bước 2. Kiểm tra: (1) yêu cầu khởi động thất bại ngay lập tức với E-EXBOT-008 ("Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."); (2) không có bản ghi bot nào được tạo trong D1; (3) preflight không tiến tới bước 3. (Hành vi đã xác nhận từ câu trả lời I-03: timeout HL ở preflight = thất bại ngay lập tức, không retry.) **Test Focus:** Lỗi/Ngoại lệ **Note:** Preflight được thiết kế để fail-fast khi HL không khả dụng — không retry ở bước này. Lý do: preflight chỉ kiểm tra điều kiện trước khi tạo bản ghi và thực hiện giao dịch on-chain; retry sẽ tạo ra độ trễ không cần thiết và không an toàn trước khi bất kỳ tài sản nào được commit.

---

### Scenario ID: TS_UC-EXBOT-bot-start_014

**Scenario Title:** Preflight bước 2 — trọng số rate-limit HL vẫn bị tính ngay cả khi bước preflight sau đó thất bại **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, FR-EXBOT-091 **Test Type:** Tích hợp **Description:** Thực hiện luồng bot-start trong đó preflight bước 2 (kiểm tra ký quỹ, weight=2) thành công nhưng preflight bước 3 (kiểm tra key_status) thất bại. Kiểm tra qua trạng thái sliding-window của `HLRateLimitDO` rằng weight=2 đã được khai báo và tiêu thụ ở bước 2 và không bị hoàn lại do thất bại ở bước 3. Điều này theo FR-EXBOT-091: trọng số được hạch toán trước khi gọi HL và tiêu thụ bất kể kết quả downstream. **Test Focus:** Tích hợp **Note:** Trọng số rate-limit HL được ghi nhận tại thời điểm gọi API, không phụ thuộc vào kết quả của các bước sau. Nếu trọng số bị hoàn lại khi bước sau thất bại, có thể vượt quá giới hạn tốc độ HL trong các tình huống retry liên tục.

---

### Scenario ID: TS_UC-EXBOT-bot-start_015

**Scenario Title:** Preflight bước 3 — chưa cấp phát khóa chặn khởi động với E-EXBOT-017 **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, FR-EXBOT-080, E-EXBOT-017 **Test Type:** Chức năng **Description:** Kích hoạt job `bot-start` cho người dùng không có hàng `hl_agent_keys` với `key_status='active'` (ví dụ: luồng key-provision chưa hoàn tất). Kiểm tra: (1) E-EXBOT-017 ("Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup.") được trả về; (2) không có bản ghi bot nào được tạo; (3) preflight dừng ở bước 3 mà không đến bước 4. **Test Focus:** Luồng thay thế **Note:** Agent key là điều kiện tiên quyết để Signing Lambda ký lệnh HL. Khởi động bot mà không có key active sẽ dẫn đến thất bại khi đặt lệnh hedge — preflight phải phát hiện sớm để tránh trạng thái LP mở nhưng không có hedge.

---

### Scenario ID: TS_UC-EXBOT-bot-start_016

**Scenario Title:** Preflight bước 4 — phí builder chưa xác nhận chặn khởi động với E-EXBOT-005 **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, E-EXBOT-005 **Test Type:** Chức năng **Description:** Kích hoạt job `bot-start` trong đó các bước preflight 1-3 đều thành công nhưng phí builder (5bps) chưa được xác nhận trên HL. Kiểm tra: (1) E-EXBOT-005 ("HL builder fee (5bps) approval required before starting ExBot.") được trả về; (2) không có bản ghi bot nào được tạo; (3) preflight dừng ở bước 4 mà không đến bước 5. Lưu ý: endpoint HL chính xác cho kiểm tra phí đang chờ OQ-EXBOT-05 — kịch bản này kiểm tra hành vi cổng, không phải cài đặt endpoint. **Test Focus:** Luồng thay thế **Note:** Phí builder 5bps là điều kiện bắt buộc của HL để ExBot Worker được phép đặt lệnh thay mặt người dùng. Nếu không kiểm tra ở preflight, bot sẽ mở LP trước rồi thất bại ở bước hedge — dẫn đến LP mở mà không có hedge.

---

### Scenario ID: TS_UC-EXBOT-bot-start_017

**Scenario Title:** Preflight bước 4 — kiểm tra phí builder chỉ một lần khi khởi động; phí đã xác nhận từ phiên trước vẫn được chấp nhận **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, E-EXBOT-005 **Test Type:** Chức năng **Description:** Kích hoạt bot-start cho người dùng có phí builder đã được xác nhận trong phiên trước (không phải lần thử khởi động hiện tại). Kiểm tra preflight bước 4 thành công — hệ thống chấp nhận phí builder đã xác nhận trước đó, không yêu cầu xác nhận on-chain hoặc API mới cho mỗi lần thử khởi động. (Đã xác nhận bởi câu trả lời I-10: kiểm tra phí builder là kiểm tra một lần khi khởi động, không phải luồng xác nhận lại.) **Test Focus:** Luồng chính **Note:** Phí builder HL được đăng ký một lần trên HL và tồn tại vĩnh viễn cho đến khi người dùng thu hồi. Kiểm tra lại mỗi lần khởi động sẽ tốn thêm API call không cần thiết và có thể tạo ra false-negative nếu HL tạm thời không khả dụng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_018

**Scenario Title:** Preflight bước 5 — mô phỏng LP mint thất bại chặn khởi động với E-EXBOT-006 **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, E-EXBOT-006 **Test Type:** Chức năng **Description:** Kích hoạt job `bot-start` trong đó tất cả các bước preflight 1-4 thành công nhưng mô phỏng LP mint thất bại (ví dụ: thanh khoản pool quá thấp cho số tiền nạp). Kiểm tra: (1) E-EXBOT-006 ("LP mint simulation failed. Check pool liquidity or adjust deposit amount.") được trả về; (2) không có bản ghi bot nào được tạo trong D1; (3) không có giao dịch on-chain nào được gọi (chỉ mô phỏng, không tiêu gas). **Test Focus:** Luồng thay thế **Note:** Bước mô phỏng này là lớp bảo vệ cuối cùng trước khi thực sự gọi `vaultMint` on-chain. Thực hiện mô phỏng trước giúp phát hiện điều kiện thất bại mà không tốn gas hay tạo ra trạng thái on-chain cần được dọn dẹp.

---

### Scenario ID: TS_UC-EXBOT-bot-start_019

**Scenario Title:** Preflight thất bại — không có bản ghi bot nào còn lại trong D1 sau khi bất kỳ bước preflight nào thất bại **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, FR-EXBOT-003 **Test Type:** Chức năng **Description:** Với mỗi bước preflight riêng lẻ (bước 1-5), kích hoạt thất bại ở bước đó. Sau mỗi thất bại, truy vấn D1 `bot_registry` và kiểm tra không có bản ghi mới nào tồn tại cho người dùng. Bản ghi bot chỉ được tạo SAU KHI tất cả 5 kiểm tra preflight thành công (UC §3 bước 4). Không có bản ghi nào trong bất kỳ tình huống thất bại nào. **Test Focus:** Lỗi/Ngoại lệ **Note:** Bản ghi bot trong D1 là cam kết về trạng thái — một khi được tạo, hệ thống giả định có tài sản đang được quản lý. Bản ghi được tạo sớm khi preflight chưa hoàn tất sẽ dẫn đến trạng thái không nhất quán và gây khó khăn cho các luồng dọn dẹp sau này.

---

### Scenario ID: TS_UC-EXBOT-bot-start_020

**Scenario Title:** Tạo bản ghi bot — lifecycle_state='preflight' được ghi nguyên tử sau khi tất cả preflight thành công **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003 **Test Type:** Dữ liệu/Trạng thái **Description:** Sau khi tất cả 5 kiểm tra preflight thành công, kiểm tra rằng bản ghi bot được tạo trong D1 với `lifecycle_state='preflight'` và `status` được đặt thành giá trị phù hợp, trong một thao tác nguyên tử duy nhất. Bản ghi phải tồn tại trong D1 TRƯỚC KHI bất kỳ giao dịch on-chain `vaultMint` nào được gọi. Truy vấn D1 giữa thời điểm hoàn tất preflight và gọi vault để xác nhận. **Test Focus:** Chuyển đổi trạng thái **Note:** Tạo bản ghi nguyên tử trước khi gọi on-chain đảm bảo nếu worker crash sau khi `vaultMint` gửi đi nhưng trước khi nhận event, hệ thống vẫn có trạng thái để reconcile. Không có bản ghi = không thể phát hiện LP đã mint mà chưa được theo dõi.

---

### Scenario ID: TS_UC-EXBOT-bot-start_021

**Scenario Title:** LP mint — lifecycle tiến từ lp_opening đến lp_opened sau sự kiện VaultMinted **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003, FR-EXBOT-004 **Test Type:** Dữ liệu/Trạng thái **Description:** Sau khi bản ghi bot được tạo với `lifecycle_state='preflight'`, ExBot Worker gọi `BnzaExVault.vaultMint(...)`. Khi sự kiện on-chain `VaultMinted(user, botId, tokenId, liquidity)` được nhận, kiểm tra: (1) `positions.token_id` được điền với `tokenId` đúng từ sự kiện; (2) `positions.custodian='vault'`; (3) `positions.tick_lower`, `positions.tick_upper` được lưu; (4) `bots.lifecycle_state='lp_opened'`. **Test Focus:** Nhất quán on-chain↔off-chain **Note:** Dữ liệu từ sự kiện `VaultMinted` là nguồn sự thật duy nhất cho `tokenId` — không được suy diễn hay tính toán từ phía off-chain. `tokenId` này sẽ được dùng trong các luồng `user_redeem` và `bot_safe_close` để gọi `BnzaExVault.redeem(tokenId)`.

---

### Scenario ID: TS_UC-EXBOT-bot-start_022

**Scenario Title:** LP mint — lỗi on-chain vaultMint chuyển bot sang trạng thái error (A4) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003, UC §4 A4 **Test Type:** Chức năng **Description:** Mô phỏng lỗi on-chain `BnzaExVault.vaultMint(...)` (ví dụ: revert do vượt ngưỡng slippage hoặc không đủ allowance). Kiểm tra: (1) `bots.lifecycle_state` chuyển sang `'error'`; (2) không có `tokenId` LP NFT nào được ghi vào `positions`; (3) bản ghi bot phản ánh trạng thái error. Lưu ý: cơ chế "hoàn trả tiền" cho A4 đang chờ OQ-EXBOT-08 (ABI chưa xác nhận) — kịch bản này chỉ kiểm tra chuyển đổi trạng thái; điều kiện hậu kiểm on-chain về thu hồi tiền nằm trong Out-of-Scope Flags. **Test Focus:** Lỗi/Ngoại lệ **Note:** Khi `vaultMint` revert on-chain, không có LP NFT nào được tạo — trạng thái `error` là chính xác vì không có tài sản nào cần bảo vệ. Cơ chế hoàn tiền (nếu có) cần được xác nhận riêng qua OQ-EXBOT-08.

---

### Scenario ID: TS_UC-EXBOT-bot-start_023

**Scenario Title:** LP mint — weth_index được lưu đúng trong positions sau VaultMinted trên chain Base **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-004, NFR-EXBOT-009 **Test Type:** Dữ liệu/Trạng thái **Description:** Hoàn tất LP mint trên chain Base (chainId=8453). Sau sự kiện `VaultMinted`, kiểm tra `positions.weth_index` được điền đúng giá trị (0 hoặc 1) cho pool USDC/WETH 0.3% trên Base — không phải hằng số cứng mà được đọc từ cấu hình đã kiểm chứng theo chain. Việc tính LP ETH amount phải dùng `weth_index` được lưu này. Lưu ý: giá trị chính xác chờ giải quyết OQ-EXBOT-03; kịch bản này kiểm tra rằng trường được điền từ cấu hình, không phải hardcode 0. **Test Focus:** Nhất quán on-chain↔off-chain **Note:** `weth_index` xác định WETH ở vị trí token0 hay token1 trong pool Uniswap V3. Nếu hardcode sai, tất cả phép tính LP ETH amount sẽ bị lệch — dẫn đến hedge size sai và tỷ lệ delta không chính xác.

---

### Scenario ID: TS_UC-EXBOT-bot-start_024

**Scenario Title:** LP mint — weth_index được lưu đúng trong positions sau VaultMinted trên chain Optimism **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-004, NFR-EXBOT-009 **Test Type:** Dữ liệu/Trạng thái **Description:** Hoàn tất LP mint trên chain Optimism (chainId=10). Sau sự kiện `VaultMinted`, kiểm tra `positions.weth_index` được điền đúng giá trị cho pool USDC/WETH 0.3% trên Optimism — độc lập với giá trị chain Base. Nếu cả hai chain có cùng thứ tự WETH thì giá trị có thể giống nhau, nhưng nguồn phải là cấu hình theo từng chain, không phải giả định cứng. Lưu ý: chờ giải quyết OQ-EXBOT-03. **Test Focus:** Nhất quán on-chain↔off-chain **Note:** Base và Optimism có thể có thứ tự token khác nhau trong pool USDC/WETH — cần kiểm tra độc lập từng chain thay vì giả định giống nhau. Đây là dạng lỗi cấu hình dễ bỏ sót khi chỉ test một chain.

---

### Scenario ID: TS_UC-EXBOT-bot-start_025

**Scenario Title:** Mở hedge — targetShortEth được tính bằng BigDecimal, không phải JS float **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-021, NFR-EXBOT-008 **Test Type:** Chức năng **Description:** Sau trạng thái `lp_opened`, kích hoạt tính toán hedge. Kiểm tra rằng `targetShortEth = lpEthAmount × 0.70` được tính bằng BigDecimal. Cụ thể: (1) không có chuyển đổi `Number()` nào được dùng cho `lpEthAmount` hay `hedgeRatio`; (2) kết quả lưu trong D1 là chuỗi TEXT (không phải JSON number); (3) `normalizeTargetRatioBps("0.70")` trả về 7000n (không phải 6999n hay 7001n do làm tròn float). **Test Focus:** Biên giới **Note:** JS float có sai số biểu diễn nhị phân: `0.70 * someEthAmount` bằng JS float có thể cho 6999 hay 7001 thay vì 7000. Khi hedge size sai dù nhỏ, delta của danh mục sẽ lệch và hệ thống có thể đặt lệnh với kích thước không khớp với LP position.

---

### Scenario ID: TS_UC-EXBOT-bot-start_026

**Scenario Title:** Mở hedge — Signing Lambda ký lệnh short IOC qua KMS agent key và gửi đến HL **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-080, NFR-EXBOT-006 **Test Type:** Tích hợp **Description:** Sau khi `targetShortEth` được tính, ExBot Worker gửi yêu cầu ký đến Signing Lambda. Kiểm tra: (1) Signing Lambda gọi KMS `kms:Sign` dùng agent key (không phải master key); (2) lệnh IOC đã ký được gửi đến HL; (3) Signing Lambda là IAM principal duy nhất được phép gọi `kms:Sign`; (4) không có khóa bí mật nào xuất hiện trong payload đã ký hoặc trong bộ nhớ/log của ExBot Worker. **Test Focus:** Tích hợp **Note:** Phân tách đặc quyền: ExBot Worker chỉ giao tiếp với Signing Lambda qua API nội bộ — không bao giờ trực tiếp gọi KMS. Nếu ExBot Worker có quyền gọi `kms:Sign`, đây là lỗ hổng IAM nghiêm trọng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_027

**Scenario Title:** Mở hedge — cloid xác định được dùng cho lệnh short IOC **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-024 **Test Type:** Chức năng **Description:** Kiểm tra cloid cho lệnh short IOC bot-start được tính là `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Gửi cùng một lần thử bot-start (cùng `botId`, `attemptId`, `stage`, `version`) hai lần phải tạo ra cùng cloid. Nếu HL loại trùng lặp, lần gửi thứ hai phải được phát hiện và bỏ qua sau reconcile mà không đặt lệnh trùng. **Test Focus:** Tính đồng nhất/Đồng thời **Note:** cloid xác định cho phép ExBot Worker gửi lại lệnh sau khi retry mà không lo bị HL coi là lệnh mới — HL sẽ loại trùng lặp dựa trên cloid. Đây là cơ chế phòng ngừa đặt hai lệnh short khi worker bị restart giữa chừng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_028

**Scenario Title:** Mở hedge — HL API không khả dụng khi gửi short IOC chuyển lifecycle sang trạng thái error (A7) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** UC §4 A7, E-EXBOT-008 **Test Type:** Chức năng **Description:** Mô phỏng HL API không khả dụng khi ExBot Worker gửi lệnh short IOC (sau trạng thái `lp_opened`). Kiểm tra: (1) `bots.lifecycle_state` chuyển sang `'error'`; (2) E-EXBOT-008 được hiển thị; (3) LP NFT vẫn được giữ bởi BnzaExVault (LP đã mint rồi — bot vào trạng thái error với LP mở nhưng không có hedge). Không có lệnh stop nào được đặt ở trạng thái này. **Test Focus:** Lỗi/Ngoại lệ **Note:** Đây là tình huống nguy hiểm nhất trong luồng khởi động: LP đã được tạo (tài sản đã lock on-chain) nhưng hedge chưa mở. Bot ở trạng thái `error` với LP không được bảo vệ — cần có quy trình phục hồi rõ ràng (xem A4 recovery).

---

### Scenario ID: TS_UC-EXBOT-bot-start_029

**Scenario Title:** Mở hedge — lệnh IOC bị sàn HL từ chối chuyển lifecycle sang trạng thái error (A10) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** UC §4 A10 **Test Type:** Chức năng **Description:** Mô phỏng HL chấp nhận yêu cầu đã ký nhưng từ chối lệnh IOC (ví dụ: không đủ ký quỹ tại thời điểm đặt lệnh, self-trade, hoặc tham số lệnh sai). Kiểm tra: (1) `bots.lifecycle_state` chuyển sang `'error'`; (2) lý do từ chối của HL được ghi lại; (3) không có vị thế hedge nào tồn tại trên HL sau thất bại. **Test Focus:** Lỗi/Ngoại lệ **Note:** Khác với TS_028 (API không khả dụng), ở đây HL phản hồi thành công nhưng từ chối lệnh vì lý do nghiệp vụ. Lý do từ chối cần được ghi lại để tester và BA có thể phân biệt lỗi tham số lệnh với lỗi kết nối.

---

### Scenario ID: TS_UC-EXBOT-bot-start_030

**Scenario Title:** Reconcile sau hedge — vị thế HL thực tế được xác nhận, hedge_legs cập nhật, lifecycle tiến đến hedge_post_confirmed **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-025 **Test Type:** Dữ liệu/Trạng thái **Description:** Sau khi lệnh short IOC được đặt, ExBot Worker lấy `clearinghouseState` từ HL để reconcile. Kiểm tra: (1) kích thước short thực tế khớp với kích thước kỳ vọng; (2) `hedge_legs.entry_price`, `hedge_legs.liquidation_price`, và `hedge_legs.effective_leverage` được điền bằng chuỗi BigDecimal; (3) `hedge_legs.last_known_hl_short_size` được cập nhật; (4) `bots.lifecycle_state` chuyển sang `'hedge_post_confirmed'`; (5) không có `rebalance_attempts.status='success'` nào được ghi trước khi reconcile xác nhận trạng thái. **Test Focus:** Nhất quán on-chain↔off-chain **Note:** Reconcile là bước xác minh độc lập: không tin vào phản hồi đặt lệnh mà phải truy vấn lại `clearinghouseState` để lấy dữ liệu vị thế chính thức. `liquidation_price` thu được ở bước này sẽ được dùng để tính stop price.

---

### Scenario ID: TS_UC-EXBOT-bot-start_031

**Scenario Title:** Reconcile sau hedge — lệch ngưỡng thêm thông điệp partial_repair vào hàng đợi và cảnh báo operator (A11) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-025, UC §4 A11, E-EXBOT-011 **Test Type:** Chức năng **Description:** Mô phỏng bước reconcile trả về kích thước short HL thực tế lệch so với kích thước kỳ vọng vượt quá `drift_threshold` đã cấu hình. Kiểm tra: (1) thông điệp `partial_repair` được thêm vào hàng đợi; (2) cảnh báo operator được kích hoạt với E-EXBOT-011 (nội bộ: "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation."); (3) bot không tiến đến bước đặt stop. Lưu ý: giá trị `drift_threshold` chính xác đang chờ giải quyết I-02 / OQ-EXBOT-11 — kịch bản này kiểm tra logic rẽ nhánh khi vượt ngưỡng. **Test Focus:** Luồng thay thế **Note:** Lệch kích thước hedge có thể xảy ra do IOC chỉ khớp một phần. Nếu không phát hiện và xử lý, bot sẽ hoạt động với tỷ lệ hedge sai — delta của danh mục sẽ không được trung hòa đúng cách.

---

### Scenario ID: TS_UC-EXBOT-bot-start_032

**Scenario Title:** Tính stop price — công thức BigDecimal dùng liquidation_price với stopSafetyFactor=0.70 **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-030, NFR-EXBOT-008 **Test Type:** Chức năng **Description:** Sau trạng thái `hedge_post_confirmed`, tính `stop_trigger_px` theo công thức: `stop_trigger_px = entry_price × (1 + ((liquidation_price − entry_price) / entry_price) × 0.70)`. Kiểm tra: (1) tất cả phép tính dùng BigDecimal, không có chuyển đổi `Number()` nào ở giữa; (2) với vị thế isolated margin 3×, `stop_trigger_px < liquidation_price` với khoảng cách ít nhất 30%; (3) giá trị được lưu dưới dạng chuỗi TEXT BigDecimal trong `hedge_legs.stop_price`. **Test Focus:** Biên giới **Note:** stopSafetyFactor=0.70 có nghĩa stop sẽ kích hoạt ở 70% khoảng cách từ giá vào đến giá thanh lý — giữ lại 30% đệm an toàn. Nếu dùng JS float tính công thức này, sai số làm tròn có thể khiến stop giá thực tế nằm gần giá thanh lý hơn mức an toàn.

---

### Scenario ID: TS_UC-EXBOT-bot-start_033

**Scenario Title:** Tính stop price — fallback về 1/effective_leverage khi liquidationPx không có sẵn **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-030 **Test Type:** Chức năng **Description:** Mô phỏng `clearinghouseState` trả về trường `liquidationPx` là null hoặc không có. Kiểm tra rằng stop price chuyển sang dùng: `stop_trigger_px = entry_price × (1 + (1 / effective_leverage) × 0.70)` — công thức fallback đã được ghi tài liệu. Ràng buộc BigDecimal vẫn áp dụng cho phép tính fallback. **Test Focus:** Luồng thay thế **Note:** HL có thể không trả về `liquidationPx` trong một số điều kiện thị trường hoặc cấu hình tài khoản. Công thức fallback đảm bảo bot vẫn có stop price hợp lý thay vì thất bại hoàn toàn — nhưng cần xác nhận công thức fallback được kiểm tra độc lập.

---

### Scenario ID: TS_UC-EXBOT-bot-start_034

**Scenario Title:** Đặt stop — stop market reduce-only được đặt và xác nhận; lifecycle tiến đến stop_verified rồi active **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-031, FR-EXBOT-003 **Test Type:** Dữ liệu/Trạng thái **Description:** Sau khi `stop_trigger_px` được tính, ExBot Worker đặt stop market reduce-only qua Signing Lambda. Kiểm tra: (1) stop được đặt với giá trigger đúng và kích thước đúng; (2) HL xác nhận lệnh stop; (3) `hedge_legs.stop_cloid` và `hedge_legs.stop_price` được ghi; (4) `bots.lifecycle_state` chuyển sang `'stop_verified'` rồi ngay lập tức sang `'active'`; (5) bot không thể đạt trạng thái `active` mà không có stop đã xác nhận — bất biến INV-STOP được thỏa mãn ngay từ khởi tạo. **Test Focus:** Chuyển đổi trạng thái **Note:** INV-STOP là bất biến cốt lõi của hệ thống: không có bot nào được phép ở trạng thái `active` mà không có stop lệnh đang hoạt động trên HL. Vi phạm bất biến này đồng nghĩa vị thế short không được bảo vệ khi giá đảo chiều mạnh.

---

### Scenario ID: TS_UC-EXBOT-bot-start_035

**Scenario Title:** Lỗi đặt stop — lifecycle chuyển đổi theo states.md (stop_placing → safe_mode) và E-EXBOT-009 được hiển thị (A8 — chờ BA xác nhận trạng thái) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-031, UC §4 A8, E-EXBOT-009 **Test Type:** Chức năng **Description:** Mô phỏng HL từ chối hoặc không xác nhận stop market reduce-only sau khi lệnh short IOC đã được khớp. Kiểm tra: (1) E-EXBOT-009 ("Failed to place native stop on Hyperliquid. Bot cannot activate without a stop.") được kích hoạt; (2) cảnh báo operator được gửi; (3) bot KHÔNG đạt `lifecycle_state='active'`; (4) vị thế short HL vẫn còn mở. Lưu ý: UC §4 A8 ghi `lifecycle_state='error'` nhưng `srs/states.md` biểu đồ trạng thái cho thấy `stop_placing → safe_mode` — trạng thái đích (error hay safe_mode) cần được BA xác nhận (I-06 đang mở). Kịch bản này kiểm tra cổng thất bại và cảnh báo; trạng thái đích kỳ vọng được gắn cờ là chưa rõ. **Test Focus:** Lỗi/Ngoại lệ **Note:** Xung đột giữa UC §4 A8 (→ error) và states.md (→ safe_mode) là vấn đề quan trọng cần giải quyết: `safe_mode` ngụ ý có thể phục hồi tự động, còn `error` yêu cầu can thiệp thủ công. Sự khác biệt này ảnh hưởng đến luồng phục hồi và thông báo người dùng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_036

**Scenario Title:** Máy trạng thái lifecycle — tất cả 9 trạng thái khởi tạo chuyển đổi theo đúng thứ tự **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003 **Test Type:** Dữ liệu/Trạng thái **Description:** Thực hiện bot-start luồng chính đầy đủ và quan sát `bots.lifecycle_state` trong D1 tại mỗi bước. Kiểm tra thứ tự chính xác là: `preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` — không bỏ trạng thái nào, không lặp trạng thái nào, và mỗi chuyển đổi được lưu nguyên tử trước khi bước tiếp theo bắt đầu. Bất kỳ trạng thái nào đến sai thứ tự hoặc bị thiếu đều là lỗi. **Test Focus:** Chuyển đổi trạng thái **Note:** Máy trạng thái lifecycle là nguồn sự thật duy nhất về tiến trình khởi động của bot. Mỗi trạng thái tương ứng với một cam kết về tài sản — lưu trạng thái nguyên tử trước mỗi bước đảm bảo có thể phục hồi nếu worker crash.

---

### Scenario ID: TS_UC-EXBOT-bot-start_037

**Scenario Title:** Máy trạng thái lifecycle — không tạo bản ghi bot nếu preflight thất bại (idle không trở thành preflight khi thất bại) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, FR-EXBOT-003 **Test Type:** Dữ liệu/Trạng thái **Description:** Kích hoạt thất bại preflight ở bước 1 (chính sách một bot). Kiểm tra `bots.lifecycle_state` của người dùng không có hàng `'preflight'` mới. Bot vẫn ở trạng thái khái niệm `idle` — tức là không có bản ghi nào được tạo. Ràng buộc: tạo bản ghi bot chỉ xảy ra sau KHI tất cả 5 kiểm tra preflight thành công. **Test Focus:** Chuyển đổi trạng thái **Note:** `idle` không phải trạng thái được lưu trong D1 — nó là trạng thái ngầm định "chưa có bot". Bất kỳ hàng nào được tạo trước khi preflight hoàn tất đều là dữ liệu rác và sẽ gây nhầm lẫn cho các truy vấn kiểm tra one-bot policy.

---

### Scenario ID: TS_UC-EXBOT-bot-start_038

**Scenario Title:** Máy trạng thái lifecycle — chuyển đổi từ hedge_pre_open sang safe_mode khi lệnh short HL thất bại **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003, srs/states.md **Test Type:** Dữ liệu/Trạng thái **Description:** Mô phỏng lỗi lệnh short IOC HL trong quá trình chuyển đổi `hedge_pre_open` → `hedge_post_confirmed` (A7 hoặc A10). Theo `srs/states.md`, các chuyển đổi hợp lệ từ `hedge_pre_open` là: → `hedge_post_confirmed` (thành công) hoặc → `safe_mode` (lệnh HL thất bại). Kiểm tra rằng khi IOC thất bại, lifecycle state chuyển sang `safe_mode` (theo states.md) — không phải `error`. Đối chiếu với UC §4 A7/A10 ghi `error` — states.md là máy trạng thái có thẩm quyền. **Test Focus:** Chuyển đổi trạng thái **Note:** `srs/states.md` được xem là tài liệu có thẩm quyền hơn UC §4 A7/A10 vì nó mô tả đặc tả máy trạng thái đã được thiết kế cẩn thận. Mâu thuẫn này cần được BA xác nhận — kịch bản này kiểm tra behavior theo states.md.

---

### Scenario ID: TS_UC-EXBOT-bot-start_039

**Scenario Title:** Tính đồng nhất hàng đợi bot-start — giao thông điệp bot-start trùng lặp không tạo bot thứ hai **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-011, NFR-EXBOT-007 **Test Type:** Chức năng **Description:** Giao cùng một thông điệp hàng đợi `bot-start` hai lần (kịch bản giao lại). Kiểm tra: (1) lần giao thứ hai gặp xung đột ràng buộc UNIQUE trên `queue_idempotency.message_id` và thoát ngay lập tức; (2) chỉ có một bản ghi bot tồn tại trong D1 cho người dùng; (3) không có lệnh HL trùng lặp nào được gửi; (4) không có hàng `positions` hoặc `hedge_legs` trùng lặp nào được tạo. **Test Focus:** Tính đồng nhất/Đồng thời **Note:** Cloudflare Queue at-least-once delivery có thể giao lại thông điệp nếu worker timeout hoặc xảy ra lỗi mạng sau khi đã xử lý một phần. `queue_idempotency` là rào chắn duy nhất ngăn giao dịch on-chain và lệnh HL bị thực hiện hai lần.

---

### Scenario ID: TS_UC-EXBOT-bot-start_040

**Scenario Title:** Thông điệp bot-start đồng thời cho cùng người dùng — chỉ một bot được tạo **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-001, FR-EXBOT-011, BR-EXBOT-001 **Test Type:** Chức năng **Description:** Gửi hai thông điệp hàng đợi `bot-start` đồng thời cho cùng một người dùng (mô phỏng race condition — ví dụ: hai sự kiện nạp tiền on-chain được xử lý đồng thời). Kiểm tra rằng kiểm tra chính sách một bot (FR-EXBOT-001) kết hợp với `queue_idempotency` đảm bảo chỉ có một bản ghi bot được tạo. Worker thứ hai phải gặp ràng buộc UNIQUE của idempotency hoặc gặp kiểm tra chính sách một bot sau khi bot đầu tiên được tạo. **Test Focus:** Tính đồng nhất/Đồng thời **Note:** Race condition này xảy ra thực tế khi người dùng nạp tiền nhiều lần nhanh hoặc khi sự kiện on-chain được phát lại. Cả `queue_idempotency` lẫn one-bot policy đều là rào chắn — kiểm tra cần xác nhận ít nhất một trong hai phát huy tác dụng.

---

### Scenario ID: TS_UC-EXBOT-bot-start_041

**Scenario Title:** Bảo mật — hàng hl_agent_keys không chứa khóa bí mật dạng plaintext sau khi cấp phát **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-080, NFR-EXBOT-006 **Test Type:** Chức năng **Description:** Sau khi key-provision hoàn tất và bot-start chạy, dump bảng `hl_agent_keys` từ D1. Kiểm tra: (1) tất cả hàng chỉ chứa địa chỉ public (`hl_user_address`, `agent_address`) và metadata; (2) không có trường nào chứa mẫu khóa bí mật dạng hex-encoded hoặc base64-encoded 256-bit/512-bit; (3) log ứng dụng trong khoảng thời gian cấp phát không có giá trị khóa thô. Khóa bí mật phải ở lại trong AWS KMS HSM. **Test Focus:** Luồng chính **Note:** Kiểm tra bảo mật định kỳ — không chỉ test một lần. Nếu bất kỳ đường dẫn code nào log hoặc serialize khóa bí mật, điều đó sẽ không hiển thị trong testing thông thường nhưng có thể bị phát hiện bởi kẻ tấn công có quyền đọc log.

---

### Scenario ID: TS_UC-EXBOT-bot-start_042

**Scenario Title:** Bảo mật — yêu cầu HTTP trực tiếp đến ExBot Worker trả về 403 (không công khai truy cập) **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-090, BR-EXBOT-010 **Test Type:** Chức năng **Description:** Gửi yêu cầu HTTP POST trực tiếp đến URL của ExBot Worker (bỏ qua OPERATOR Facade / CF service binding). Kiểm tra Worker trả về 403 và không xử lý yêu cầu. Tất cả thao tác bot-start chỉ được truy cập qua OPERATOR Facade tại `POST /api/exbot/start`, được ủy quyền qua CF service binding với xác thực token nội bộ. **Test Focus:** Phân quyền/Vai trò **Note:** Nếu ExBot Worker có thể truy cập trực tiếp qua HTTP public, bất kỳ ai biết URL đều có thể kích hoạt bot-start mà không cần xác thực. CF service binding đảm bảo chỉ OPERATOR Facade được phép gọi Worker.

---

### Scenario ID: TS_UC-EXBOT-bot-start_043

**Scenario Title:** Tích hợp — sau khi bot đạt active, light-check và deep-audit được lên lịch **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003, FR-EXBOT-012, FR-EXBOT-016 **Test Type:** Tích hợp **Description:** Sau khi `bots.lifecycle_state='active'` được đặt, kiểm tra: (1) `bots.next_light_check_at` được đặt thành `now + 5 phút + jitter(−45 giây, +45 giây)` theo FR-EXBOT-013; (2) bot sẽ được cron scan light-check tiếp theo phát hiện; (3) deep-audit được lên lịch trong vòng 6 giờ tiếp theo. Các phụ thuộc cross-UC (UC-EXBOT-light-check, UC-EXBOT-deep-audit) được kích hoạt bởi chuyển đổi lifecycle `active`. **Test Focus:** Tích hợp **Note:** `active` không phải trạng thái kết thúc — đây là điểm bắt đầu của vòng lặp giám sát định kỳ. Nếu `next_light_check_at` không được đặt đúng, bot sẽ chạy mà không có giám sát và bất biến INV-STOP có thể bị vi phạm mà không ai biết.

---

### Scenario ID: TS_UC-EXBOT-bot-start_044

**Scenario Title:** Tích hợp — sau khi bot đạt active, status API trả về trạng thái active **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-090, FR-EXBOT-003 **Test Type:** Tích hợp **Description:** Sau khi `bots.lifecycle_state='active'`, gọi `GET /api/exbot/status` qua OPERATOR Facade. Kiểm tra: (1) phản hồi bao gồm `status='active'`, `botId`, và các trường tóm tắt hedge/LP; (2) phản hồi không tiết lộ bất kỳ key material nào; (3) log OPERATOR cho thấy yêu cầu được ủy quyền qua CF service binding đến ExBot Worker. **Test Focus:** Tích hợp **Note:** Status API là giao diện người dùng duy nhất để quan sát trạng thái bot — người dùng không đọc trực tiếp D1. Nếu API trả về sai trạng thái hoặc thiếu trường, người dùng sẽ không biết bot đang hoạt động hay đang gặp sự cố.

---

### Scenario ID: TS_UC-EXBOT-bot-start_045

**Scenario Title:** Tích hợp — tokenId được lưu trong positions khớp với LP NFT on-chain đang được BnzaExVault giữ **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-004, FR-EXBOT-070 **Test Type:** Tích hợp **Description:** Sau khi bot-start hoàn tất, truy vấn on-chain BnzaExVault để lấy LP NFT đang được giữ cho người dùng. Kiểm tra `positions.token_id` trong D1 khớp với `tokenId` thực tế từ sự kiện `VaultMinted` và NFT hiện đang được BnzaExVault giữ (`custodian='vault'`). Tính nhất quán này rất quan trọng cho các luồng `user_redeem` và `bot_safe_close` sau này, các luồng đó gọi `BnzaExVault.redeem(tokenId)`. **Test Focus:** Nhất quán on-chain↔off-chain **Note:** Nếu `tokenId` trong D1 không khớp với on-chain, các luồng rút tiền sau này sẽ gọi `redeem` với sai ID — giao dịch sẽ revert hoặc tệ hơn là rút nhầm NFT của người dùng khác.

---

### Scenario ID: TS_UC-EXBOT-bot-start_046

**Scenario Title:** Nghiệm thu — toàn bộ khởi tạo kết quả bot có stop_price < liquidation_price và đệm >= 30% **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-030, AC-13 **Test Type:** Nghiệm thu **Description:** Hoàn tất bot-start đầy đủ với vị thế isolated margin 3× đã biết trên HL. Sau trạng thái `active`: kiểm tra `hedge_legs.stop_price` (BigDecimal) nhỏ hơn `hedge_legs.liquidation_price`, với khoảng cách ít nhất 30% của phạm vi giá vào đến giá thanh lý (stopSafetyFactor=0.70 có nghĩa stop kích hoạt ở 70% khoảng cách đến giá thanh lý). Điều này xác nhận đệm an toàn stop được thực thi đúng. **Test Focus:** Luồng chính **Note:** Đây là tiêu chí nghiệm thu quan trọng nhất về mặt rủi ro tài chính: nếu stop quá gần giá thanh lý, trong điều kiện thị trường biến động mạnh (slippage), lệnh stop có thể không được thực hiện trước khi bị thanh lý.

---

### Scenario ID: TS_UC-EXBOT-bot-start_047

**Scenario Title:** Nghiệm thu — thông báo lỗi ký quỹ hiển thị đúng số tiền yêu cầu và mức thiếu hụt **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-061, AC-03 **Test Type:** Nghiệm thu **Description:** Kích hoạt bot-start với `marginBalance=$300` và yêu cầu (×2.0) =$700. Kiểm tra thông điệp E-EXBOT-002 chứa: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit $400 to HL." Mức thiếu hụt phải chính xác đến đô la gần nhất (không làm xấp xỉ). **Test Focus:** Luồng thay thế **Note:** Thông báo lỗi với số tiền chính xác giúp người dùng biết cần nạp thêm đúng bao nhiêu — không thừa không thiếu. Số liệu xấp xỉ hoặc làm tròn sai có thể khiến người dùng nạp thêm nhưng vẫn thiếu và không hiểu tại sao bot vẫn không khởi động.

---

### Scenario ID: TS_UC-EXBOT-bot-start_048

**Scenario Title:** Nghiệm thu — không có bản ghi bot nào được tạo khi bất kỳ bước preflight đơn lẻ nào thất bại **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-002, FR-EXBOT-003, AC-02/03/04/05/06 **Test Type:** Nghiệm thu **Description:** Với mỗi kịch bản thất bại preflight (chính sách một bot, ký quỹ không đủ, chưa cấp phát khóa, thiếu phí builder, mô phỏng thất bại), kiểm tra không có bản ghi bot nào tồn tại trong D1 cho người dùng sau thất bại. Việc tạo bất kỳ bản ghi bot nào là lỗi theo FR-EXBOT-002. **Test Focus:** Luồng thay thế **Note:** Bao phủ đầy đủ 5 điều kiện preflight trong một kịch bản nghiệm thu — xác nhận rằng không có đường dẫn code nào trong 5 trường hợp tạo bản ghi sớm.

---

### Scenario ID: TS_UC-EXBOT-bot-start_049

**Scenario Title:** Nghiệm thu — thông điệp bot-start được giao lại tạo ra đúng một lần thực hiện thành công **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-011, AC-14, NFR-EXBOT-007 **Test Type:** Nghiệm thu **Description:** Giao cùng một thông điệp hàng đợi `bot-start` hai lần (mô phỏng retry hàng đợi). Kiểm tra: (1) đúng một bản ghi bot được tạo; (2) đúng một tập hàng `positions` và `hedge_legs` được ghi; (3) đúng một vị thế short HL được mở; (4) lần giao thứ hai thoát ngay lập tức sau xung đột UNIQUE của `queue_idempotency` mà không có thao tác ghi D1 hay gọi HL nào. Đây là tiêu chí nghiệm thu tính đồng nhất tiêu chuẩn. **Test Focus:** Tính đồng nhất/Đồng thời **Note:** Tiêu chí "đúng một lần" phải được kiểm tra ở cấp độ tích hợp thực — không chỉ đếm bản ghi D1 mà còn phải xác nhận không có lệnh HL trùng lặp qua log giao dịch HL.

---

### Scenario ID: TS_UC-EXBOT-bot-start_050

**Scenario Title:** Nghiệm thu — tất cả 9 trạng thái lifecycle chuyển đổi đúng thứ tự và bot đạt active với hedge và stop đã xác nhận **UC Reference:** UC-EXBOT-bot-start **Req-ID:** FR-EXBOT-003, AC-01 **Test Type:** Nghiệm thu **Description:** Thực hiện bot-start luồng chính đầy đủ và ghi lại chuỗi giá trị `bots.lifecycle_state` quan sát được trong D1. Chuỗi phải chính xác là: `preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`. Trạng thái cuối: `bots.status='active'`, `hedge_legs.stop_price` được điền (chuỗi BigDecimal khác null), `positions.token_id` được điền, `positions.custodian='vault'`. Bất kỳ sai lệch nào trong chuỗi trạng thái hoặc trường cuối bị thiếu đều là lỗi. **Test Focus:** Luồng chính **Note:** Kịch bản nghiệm thu tổng hợp — bao phủ cả máy trạng thái lẫn tính đầy đủ dữ liệu cuối. Đây là kịch bản Go/No-Go cuối cùng trước khi chấp nhận tính năng bot-start cho môi trường production.

---

## ⚠️ Các vấn đề ngoài phạm vi

| Khu vực kịch bản | Lý do | Hành động đề xuất |
|---|---|---|
| Điều kiện hậu kiểm A4 — cơ chế hoàn tiền on-chain sau khi LP mint thất bại | BỊ CHẶN: ABI BnzaExVault chưa được xác nhận (OQ-EXBOT-08 Đang mở; IC-EXBOT-002). Không thể xác định revert là tự động hay cần ExBot Worker thực hiện hành động rõ ràng. I-05 Hoãn. | Giải quyết OQ-EXBOT-08 → xác nhận ABI → thêm kiểm tra điều kiện hậu kiểm cụ thể vào kịch bản TS_022 |
| Kiểm tra biên lệch reconcile — giá trị drift_threshold chính xác | BỊ CHẶN: Giá trị drift_threshold chưa được định nghĩa trong FR-EXBOT-025 hoặc UC §4 A11. I-02 Đang mở; OQ-EXBOT-11 (lpValueUsd × 3% ứng cử viên) chưa được zen xác nhận. | Giải quyết I-02 / OQ-EXBOT-11 → thêm kịch bản biên tại ngưỡng, ngưỡng−1, ngưỡng+1 |
| Kiểm tra phí builder preflight — endpoint HL chính xác và trọng số | BỊ CHẶN: OQ-EXBOT-05 (NV-14) Đang mở — cơ chế phê duyệt phí builder (giao dịch on-chain hay gọi API) chưa được xác nhận. I-07 Hoãn. | Giải quyết OQ-EXBOT-05 → thêm kịch bản tích hợp endpoint cụ thể cho bước 4 |
| Trạng thái đích kỳ vọng A8 — mơ hồ error hay safe_mode | VẤN ĐỀ MỞ I-06: UC §4 A8 ghi error nhưng srs/states.md cho thấy stop_placing → safe_mode. Luồng phục hồi cũng chưa được định nghĩa. Kịch bản TS_035 kiểm tra cổng thất bại nhưng gắn cờ trạng thái đích là chưa rõ. | BA/zen xác nhận states.md là có thẩm quyền → cập nhật TS_035 trạng thái kỳ vọng; thêm kịch bản luồng phục hồi nếu đường dẫn safe_mode |
| Giá trị weth_index chính xác theo từng chain (Base 8453 / OP 10) | BỊ CHẶN: OQ-EXBOT-03 (NV-12) Đang mở — địa chỉ pool và thứ tự token WETH cho USDC/WETH 0.3% chưa được xác nhận. Kịch bản TS_023/TS_024 kiểm tra trường được điền từ cấu hình nhưng không thể khẳng định giá trị cụ thể. I-04 Hoãn. | Giải quyết OQ-EXBOT-03 → cập nhật TS_023/TS_024 với giá trị kỳ vọng cụ thể |
| Kiểm tra hiệu năng/tải — 10.000 bot đồng thời | NFR: HIỆU NĂNG / TẢI — FR-EXBOT-011 / NFR-EXBOT-001. Ngoài phạm vi QC chức năng. | Chuyển cho chuyên gia kiểm tra tải dùng k6 hoặc tương đương |
| Kiểm tra bảo mật chuyên sâu — IAM KMS biên giới, leo thang đặc quyền Signing Lambda | NFR: BẢO MẬT ngoài kiểm tra xác thực chức năng. Kịch bản chức năng TS_041/TS_042 bao phủ bề mặt quan sát được; kiểm tra IAM chuyên sâu nằm ngoài phạm vi. | Chuyển cho chuyên gia bảo mật cloud |