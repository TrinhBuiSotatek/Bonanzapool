# Báo cáo rà soát mức độ sẵn sàng của Use Case

| Tiêu đề | UC-EXBOT-hedge-sync: Execute Delta-Only Hedge Adjustment |
|---------|------------------------------------------------------|
| Ngày tạo | 2026-06-30 |
| Người viết | QC UC Read ExBot Agent |
| Phiên bản | v1 |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-hedge-sync mô tả quy trình tự động điều chỉnh vị thế short ETH trên Hyperliquid (HL) của một ExBot đang hoạt động, dựa trên nguyên tắc "delta-only" -- chỉ điều chỉnh phần chênh lệch giữa kích thước short mục tiêu và kích thước short thực tế, không bao giờ đóng toàn bộ rồi mở lại trong quá trình hedge-sync bình thường.

**Ai vận hành:** Không có người dùng trực tiếp can thiệp vào luồng này. Actor chính là Hedge-Sync Worker (một Cloudflare Worker) xử lý message từ hàng đợi `hedge-sync`. Bộ khởi động là light-check worker (cadence 5 phút) hoặc deep-audit worker (backstop). Nhà đầu tư (Investor) không thực hiện hành động gì trong UC này.

**Điều kiện khởi chạy:** Bot phải đang ở trạng thái `status='active'`, `lifecycle_state='active'`; circuit breaker phải ở trạng thái `closed` hoặc `half_open`; worker phải nhận được message `{botId, reasons: RebalanceReason[], stateVersion}` từ hàng đợi.

**Luồng xử lý chính:** Worker kiểm tra idempotency (tránh xử lý trùng lặp), xác minh `stateVersion` khớp với D1, giành khóa `UserLockDO` (mutex 90 giây cho từng user), lấy vị thế thực tế từ HL, tính delta BigDecimal, gửi lệnh điều chỉnh delta, thay stop via INV-STOP protocol (giao thức bảo vệ tránh vi phạm bất biến "lúc nào cũng phải có stop tối thiểu"), đợi reconcile worker xác nhận kết quả, cập nhật D1 và ghi log.

**Quy tắc nghiệp vụ nổi bật:** delta-only là bất biến mặc định (BR-EXBOT-004); stop monitoring không thể tắt dù mạch ngắt mở hay đóng (FR-EXBOT-014); mọi phép tính hedge và stop phải dùng BigDecimal, không dùng float (NFR-EXBOT-008); `stop_replacing_started_at` phải được xóa trong `finally` block sau khi thay stop (FR-EXBOT-035).

**Liên kết:** UC-EXBOT-light-check (khởi tạo hedge-sync); UC-EXBOT-deep-audit (backup khởi tạo); UC-EXBOT-bot-safe-close (trigger khi 3 lần stop trong 7 ngày hoặc sai số không sửa được).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-hedge-sync | Execute Delta-Only Hedge Adjustment | updated 2026-06-20 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | (chưa có) | 2026-06-12 | 2026-06-20 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-hedge-sync.md` | 2026-06-20 | UC | Nguồn chính |
| `userstories/us-006.md` | 2026-06-12 | User Story | Linked story |
| `userstories/us-008.md` | 2026-06-12 | User Story | Linked story |
| `srs/spec.md` | 2026-06-29 | SRS | Nguồn sự thật |
| `srs/states.md` | 2026-06-18 | State diagram | Trạng thái bot/circuit/margin |
| `srs/flows.md` | 2026-06-29 | Flow diagram | F-02 Hedge-Sync Execution |
| `srs/erd.md` | 2026-06-29 | ERD | Schema D1 |
| `frd.md` | 2026-06-29 | FRD | Yêu cầu chức năng |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-hedge-sync tồn tại để giữ cho vị thế short ETH trên Hyperliquid (HL) luôn xấp xỉ bằng giá trị ETH thật sự đang trong LP position trên Uniswap V3. Khi giá ETH thay đổi làm LP drift (sai số giữa target và actual vượt ngưỡng), worker tự động điều chỉnh chỉ bằng phần chênh lệch (delta), giữ chi phí giao dịch và mức độ ảnh hưởng HL thấp nhất có thể. Đồng thời UC đảm bảo stop-loss luôn tồn tại và được cập nhật sau mỗi lần thay đổi vị thế.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Kiểm tra idempotency (queue dedup) | Insert `message_id` vào `queue_idempotency`; UNIQUE conflict = skip | FR-EXBOT-011, SRS §FR-011 |
| Kiểm tra stateVersion | Đọc `bots.state_version` từ D1; mismatch = discard (status='skipped') | FR-EXBOT-027, SRS §FR-027 |
| Giành khóa UserLockDO | acquire(holderToken, ttl=90s, idempotencyKey) để đảm bảo chỉ 1 worker điều chỉnh HL cùng lúc cho 1 user | FR-EXBOT-026, SRS §FR-026 |
| Lấy vị thế thực tế từ HL | getPosition via clearinghouseState (weight=2) | SRS §FR-025, flows.md F-02 |
| Tính delta (BigDecimal) | delta = targetShortEth - actualShortEth; đặt lệnh điều chỉnh delta hoặc bỏ qua nếu delta=0 | FR-EXBOT-022, SRS §FR-022 |
| Gửi lệnh adjustShortDelta via cloid | Lệnh delta-only với cloid tất định; retry dùng cloid cũ; payload đổi = tăng version | FR-EXBOT-024, SRS §FR-024 |
| Enqueue reconcile | Gửi message reconcile {botId, attemptId, expectedAbsSize, hedgeLegId} | SRS flows.md F-02 |
| Thay stop via INV-STOP protocol | stop_replacing_started_at set trước; cancel + place stop; clear trong finally | FR-EXBOT-035, SRS §FR-035 |
| Giải phóng khóa UserLockDO | release(holderToken, idempotencyKey, result) trong finally block | FR-EXBOT-026 |
| Reconcile Worker xác nhận | Fetch actual HL position, verify size = expected, extract entry_price/liq_price/effective_leverage | FR-EXBOT-025, SRS §FR-025 |
| Cập nhật D1 sau reconcile | hedge_legs.stop_price, entry_price, effective_leverage; bot_runtime_state.last_known_hl_short_size; rebalance_attempts (status='success') | FR-EXBOT-025, SRS §FR-025 |
| Quản lý circuit breaker | incrementCircuitBreaker khi HL order bị reject; 3 failures trong 24h -> circuit open | FR-EXBOT-040, SRS §FR-040 |
| Enqueue partial_repair khi fill một phần | reconcile phát hiện \|actual - target\| > drift_threshold -> enqueue partial_repair | FR-EXBOT-036, SRS §FR-036 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Logic tính targetShortEth (PositionCalc, hedge math) | Zen-proprietary, SRS §1.3 Out of Scope | Giá trị target đưa vào như tham số đầu vào; không test công thức |
| Đặt stop lần đầu (bot-start) | Thuộc UC-EXBOT-bot-start | Precondition: stop đã tồn tại trước hedge-sync |
| Deep-audit cron | Thuộc UC-EXBOT-deep-audit | Liên kết vì deep-audit là backstop enqueue hedge-sync |
| LP rebalance | Thuộc UC-EXBOT-light-check / partial_repair | range_out không đi qua hedge-sync |
| user_redeem / bot_safe_close | Thuộc UC khác | Hedge-sync không xử lý close path (target=0 thuộc close path riêng) |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| Hedge-Sync Worker | Primary / System | Xử lý message từ hàng đợi; giành khóa; gửi lệnh HL; giải phóng khóa | Không có permission người dùng; hoạt động dưới quyền của ExBot Worker (CF Worker IAM role); ký lệnh HL qua Signing Lambda (kms:Sign) | UC §1 Actors, SRS §1.1 |
| UserLockDO | Secondary / System | Cấp phát và quản lý lease mutex cho từng user (TTL 90s) | Không lưu trữ state nghiệp vụ; chỉ quản lý lease; auto-release khi TTL hết | FR-EXBOT-026, SRS §FR-092 |
| Hyperliquid (HL) | External | Nhận lệnh delta, thực hiện, trả kết quả | Giới hạn rate limit 800 weight/min toàn hệ thống (BNZA budget); weight getPosition = 2 | FR-EXBOT-091, IC-EXBOT-001 |
| D1 (control_db + state_db_shard) | System | Lưu trữ và cung cấp trạng thái bot, hedge_legs, rebalance_attempts, queue_idempotency | Write-on-change; ADD COLUMN only sau Phase A | FR-EXBOT-080, BR-EXBOT-009 |
| Reconcile Worker | Secondary / System | Xác nhận kết quả sau khi lệnh được xử lý; cập nhật hedge_legs và bot_runtime_state | Không gửi lệnh HL; chỉ đọc và cập nhật D1 | UC §3 step 11-14, flows.md F-02 |
| Signing Lambda | System / External | Ký lệnh HL bằng KMS agent key | Ký lệnh qua kms:Sign; private key không bao giờ ra khỏi KMS HSM | FR-EXBOT-080, NFR-EXBOT-006 |

**Nhận xét readiness:** Actor đã đủ rõ để thiết kế test theo role. Chưa có role-permission matrix tường minh cho hedge-sync worker (ai có thể gọi, ai được gọi qua hàng đợi), nhưng trong bối cảnh backend-only thì điều này chấp nhận được — truy cập qua hàng đợi là duy nhất, không có human actor.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Message từ hàng đợi `hedge-sync` có payload `{botId, reasons: RebalanceReason[], stateVersion}` | Yes | UC §2 Preconditions |
| 2 | `bots.status='active'` và `bots.lifecycle_state='active'` | Yes | UC §2 Preconditions |
| 3 | `circuit_breakers.state IN ('closed','half_open')` | Yes | UC §2 Preconditions |
| 4 | Bot có ít nhất 1 `hl_agent_keys` row với `key_status='active'` (đã được provisioned từ trước) | Yes (implied) | FR-EXBOT-080, states.md Agent Key Status |
| 5 | `hedge_legs` row tồn tại với stop được đặt (stop_cloid, stop_price không null) | Yes (implied) | FR-EXBOT-031, UC §5 Postconditions |
| 6 | `queue_idempotency`: message_id chưa có hoặc đã có với state='succeeded'/'failed' (duplicate detection) | Yes | FR-EXBOT-011 |

### 3.2 Kết quả sau khi hoàn tất (happy path)

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Điều chỉnh hedge thành công | `hedge_legs.stop_price`, `entry_price`, `effective_leverage` được cập nhật; `stop_replacing_started_at=NULL` | UC §5, SRS §FR-025 |
| Cập nhật trạng thái HL hot | `bot_runtime_state.last_known_hl_short_size` = giá trị reconcile xác nhận | UC §5, SRS §FR-025 |
| Ghi log kết quả | `rebalance_attempts` row được insert với `status='success'` và đầy đủ trường: old_short_size, target_short_size, reconciled_short_size, adjust_cloid, stop_cloid | UC §3 step 15, ERD |
| Idempotency hoàn tất | `queue_idempotency.state='succeeded'` cho message_id này | UC §3 step 16 |
| Circuit breaker đặt lại (nếu half_open probe) | `circuit_breakers.state='closed'`, `failure_count=0` | FR-EXBOT-040, US-EXBOT-008 AC-008-3 |
| Khóa được giải phóng | `UserLockDO` không còn giữ lease cho holderToken này | FR-EXBOT-026 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng chính: Xử lý message hedge-sync (delta-only adjustment)

#### §F.1 — Inventory: Function / Operation / Data Object / State

| # | Hạng mục | Loại | Trigger / Input | Output / Effect | Enum / State / Type | Nguồn |
|---|---|---|---|---|---|---|
| F1-01 | `queue_idempotency` INSERT (dedup check) | Operation | message_id từ queue payload | UNIQUE conflict = skip; success = proceed | state: started / succeeded / failed / retryable | FR-EXBOT-011, SRS §FR-011 |
| F1-02 | stateVersion check | Operation | message.stateVersion vs bots.state_version trong D1 | Match = proceed; mismatch = discard (status='skipped') | -- | FR-EXBOT-027, SRS §FR-027 |
| F1-03 | `UserLockDO.acquire` | Operation | holderToken (UUID), ttl=90s, idempotencyKey='hedge-sync:{botId}:{stateVersion}' | acquired=true / acquired=false + currentHolderExpiresAt | acquired: boolean | FR-EXBOT-026, SRS §FR-092 |
| F1-04 | Fetch actual HL position | External API call | botId / hl_user_address | actualShortEth (TEXT/BigDecimal), entry_price, liq_price, effective_leverage | clearinghouseState response; weight=2 | SRS §FR-025, flows.md F-02 |
| F1-05 | Tính delta (BigDecimal) | Computation | targetShortEth (từ D1 bot_runtime_state.target_short_size), actualShortEth | delta = targetShortEth.sub(actualShortEth); có thể âm (reduce) hoặc dương (increase) hoặc 0 | BigDecimal; không float | FR-EXBOT-022, SRS §FR-021 |
| F1-06 | `adjustShortDelta(delta, cloid)` | External API call | delta (BigDecimal), cloid (deterministic keccak256) | Fill confirmation (partial hoặc full) | cloid format: first128BitsHex(keccak256('bnza:{botId}:{attemptId}:{stage}:{version}')) | FR-EXBOT-024, SRS §FR-024 |
| F1-07 | Enqueue reconcile message | Operation | {botId, attemptId, expectedAbsSize, hedgeLegId} | Message được đưa vào hàng đợi reconcile | -- | flows.md F-02, SRS |
| F1-08 | INV-STOP: set stop_replacing_started_at | Operation | bắt đầu critical section thay stop | hedge_legs.stop_replacing_started_at = now | TEXT (ISO 8601) | FR-EXBOT-035, SRS §FR-035 |
| F1-09 | INV-STOP: cancel stop trên HL | External API call | stop_cloid hiện tại hoặc stop_order_id | Stop bị hủy trên HL | -- | FR-EXBOT-035, §19.5 SPEC |
| F1-10 | INV-STOP: đặt stop mới trên HL | External API call | stop_trigger_px (BigDecimal, đã tính lại), size, cloid mới | Stop được đặt trên HL; trả về stop_order_id mới | reduce-only stop market | FR-EXBOT-035, SRS §FR-030 |
| F1-11 | INV-STOP: clear stop_replacing_started_at | Operation | finally block sau INV-STOP | hedge_legs.stop_replacing_started_at = NULL | -- | FR-EXBOT-035 |
| F1-12 | `UserLockDO.release` | Operation | holderToken, idempotencyKey, result | Lease được giải phóng; kết quả có thể cache replay | -- | FR-EXBOT-026, SRS §FR-092 |
| F1-13 | Reconcile Worker: fetch actual HL position | External API call | botId / hl_user_address (sau khi lệnh đã xử lý) | actualShortSize, entry_price, liq_price, effective_leverage (mới) | weight=2 | FR-EXBOT-025, flows.md F-02 |
| F1-14 | Reconcile Worker: xác nhận size | Validation | actualShortSize vs expectedAbsSize | Match = success; mismatch = partial fill -> enqueue partial_repair | tolerance: phụ thuộc OQ-EXBOT-04 (dust threshold) | FR-EXBOT-025, SRS §FR-025 |
| F1-15 | Reconcile Worker: tính lại stop_trigger_px | Computation | entry_price (mới), liq_price (mới), effective_leverage, stopSafetyFactor=0.70 | stop_trigger_px mới (BigDecimal) | Formula: entry_price x (1 + liq_distance_pct x stopSafetyFactor) | FR-EXBOT-030, SRS §FR-030 |
| F1-16 | Cập nhật D1 hedge_legs | Write | entry_price, liq_price, effective_leverage, stop_price, stop_cloid mới | hedge_legs row được cập nhật | stop_price stored as TEXT | FR-EXBOT-025, SRS §FR-025 |
| F1-17 | Cập nhật D1 bot_runtime_state | Write | reconciled_size | last_known_hl_short_size = reconciled_size | state_version tăng 1 | FR-EXBOT-025, SRS |
| F1-18 | Insert rebalance_attempts | Write | botId, attemptId, old_short_size, target_short_size, reconciled_short_size, adjust_cloid, stop_cloid, status, reason | Row mới trong audit ledger | status: success / failed / partial / skipped | FR-EXBOT-025, SRS, ERD |
| F1-19 | Update queue_idempotency | Write | message_id | state='succeeded' | state: started / succeeded / failed / retryable | FR-EXBOT-011 |
| F1-20 | incrementCircuitBreaker | Operation | hedge_leg_id, failure | failure_count tăng 1; nếu failure_count=3 trong 24h -> circuit open | circuit_breakers.state: closed / open / half_open | FR-EXBOT-040, US-EXBOT-008 |
| F1-21 | Enqueue partial_repair | Operation | botId, attemptId, reason='partial_fill' | Message vào hàng đợi partial_repair | -- | FR-EXBOT-036 |
| F1-22 | Enqueue notification | Operation | botId, user_id, event=hedge_failure | Message vào hàng đợi notification | -- | UC §4 A3 |
| F1-23 | `UserLockDO.heartbeat` | Operation | holderToken, ttl extension | Gia hạn lease nếu công việc vượt 30 giây | -- | FR-EXBOT-026, SRS §FR-092 |
| F1-24 | Bot state machine: `bots.lifecycle_state` | Data object | Trạng thái hiện tại của bot trong UC này | Trong hedge-sync, lifecycle_state không đổi (vẫn 'active' trong happy path) | active là trạng thái duy nhất được phép khi hedge-sync chạy | states.md State Registry |
| F1-25 | Circuit breaker half_open probe | State | circuit_breakers.state='half_open' | Dùng đúng 1 probe; `half_open_probe_used` 0->1 atomic | half_open_probe_used: INTEGER (0/1) | FR-EXBOT-040, SRS §FR-040 |

#### §F.2 — Thuộc tính data / state, Business Rules, Validation, Messages (theo từng hạng mục F1)

| F1 Ref | Trường / Rule / Validation | Điều kiện | Bắt buộc? | Kết quả hợp lệ | Kết quả không hợp lệ | Nguồn |
|---|---|---|---|---|---|---|
| F1-01 | message_id UNIQUE trong queue_idempotency | Insert với state='started' | Yes | Proceed xử lý | UNIQUE conflict = return immediately (duplicate delivery) | FR-EXBOT-011, SRS §FR-011 |
| F1-02 | stateVersion phải khớp với D1 | Đọc trước khi acquire lock | Yes | Proceed | Discard; rebalance_attempts.status='skipped'; không gửi HL order | FR-EXBOT-027 |
| F1-03 | holderToken: UUID do caller sinh ra | Mỗi lần gọi phải sinh token mới | Yes | acquired=true, leaseId trả về | acquired=false + currentHolderExpiresAt; re-queue với delay | FR-EXBOT-026, SRS §FR-092 |
| F1-03 | TTL 90s | Nếu công việc >30s phải heartbeat | Yes | Lease còn hiệu lực | TTL hết -> auto-release; worker tiếp theo reconcile trước khi gửi HL | FR-EXBOT-026 |
| F1-03 | idempotencyKey='hedge-sync:{botId}:{stateVersion}' | Pattern cố định | Yes | Cache replay nếu đã xử lý stateVersion này rồi | -- | FR-EXBOT-026, SRS §FR-092 |
| F1-04 | HL weight=2 (getPosition) | Trước mọi HL mutation | Yes | Trả về actualShortEth, entry_price, liq_price, effective_leverage | E-EXBOT-008 nếu HL không truy cập được; bot vào SAFE_MODE | IC-EXBOT-001, SRS §FR-050 |
| F1-05 | BigDecimal bắt buộc; không float | Tất cả phép tính tài chính | Yes | delta là BigDecimal chính xác | Float arithmetic = bug, NFR vi phạm | NFR-EXBOT-008, FR-EXBOT-021 |
| F1-05 | normalizeTargetRatioBps() | Chuyển "0.70" -> 7000n BigInt | Yes | Chuẩn hóa đúng; '0.70' -> 7000n | Number("0.73") * 10000 là bug | SRS §FR-021 |
| F1-05 | delta=0 | Tính delta = 0 (target = actual) | No | Bỏ qua HL order; đi thẳng đến bước thay stop; ghi log trong rebalance_attempts | N/A | UC §3 step 5 note, A6; OQ-EXBOT-013 (open) |
| F1-06 | cloid tất định: keccak256('bnza:{botId}:{attemptId}:{stage}:{version}') | Mỗi lần gửi lệnh | Yes | Same retry = same cloid (HL dedup hoặc skip) | payload đổi phải tăng version; duplicate cloid -> reconcile trước, không blind retry | FR-EXBOT-024, SRS §FR-024 |
| F1-06 | adjustShortDelta: chỉ delta, không close+open | Trong quá trình hedge-sync bình thường | Yes | Chỉ gửi delta | Full close/open trong hedge-sync bình thường = BR-EXBOT-004 vi phạm | BR-EXBOT-004, FR-EXBOT-022 |
| F1-06 | margin_status check trước khi tăng size | margin_status='warning' trong D1 | Yes | 'warning' -> tắt increase; chỉ cho reduce-only | Nếu tăng size khi warning = vi phạm FR-EXBOT-060 | FR-EXBOT-060, SRS |
| F1-08 đến F1-11 | INV-STOP: stop_replacing_started_at set trước | Bắt đầu critical section | Yes | Được set = now; phải clear trong finally | Nếu không xóa trong finally -> stuck > 60s -> SAFE_MODE (light-check primary detection <=5 phút) | FR-EXBOT-035, FR-EXBOT-033 |
| F1-09 | Cancel stop phải qua INV-STOP protocol | Cấm direct cancel-then-place | Yes | Stop được hủy an toàn | Direct cancel-then-place không bảo vệ = BR vi phạm | FR-EXBOT-035, SPEC §19.5 |
| F1-14 | Reconcile mismatch -> partial_repair | \|actual - target\| > drift_threshold | Conditional | partial_repair được enqueue | SAFE_MODE nếu liên tiếp 3 lần thất bại partial repair | FR-EXBOT-036, FR-EXBOT-025 |
| F1-15 | stop_trigger_px (BigDecimal): entry_price x (1 + liq_distance_pct x 0.70) | Sau mọi reconcile | Yes | Giá trị BigDecimal chính xác | Float intermediate = vi phạm NFR-EXBOT-008 | FR-EXBOT-030, SRS §FR-030 |
| F1-15 | liq_distance_pct = (liq_price - entry_price) / entry_price | Ưu tiên HL liq_price; fallback 1/effective_leverage | Yes | BigDecimal; dùng HL value khi có | Fallback chỉ khi liq_price không có | SRS §FR-030 |
| F1-20 | failure_count: rolling 24h window, không có success xen giữa | Sau HL rejection | Yes | 3 consecutive failures -> circuit open; reset_at = now + 1h | Partial/failed không đặt lại circuit (chỉ success mới đặt lại) | FR-EXBOT-040, UC §6 Business Rules |
| F1-20 | half_open_probe_used: atomic 0->1 claim | Chỉ trong trạng thái half_open | Yes | Dùng 1 probe được phép | Probe thứ 2 trong cùng half_open bị chắc chắn chặn | FR-EXBOT-040, SRS §FR-040 |
| F1-25 | Circuit open: hedge-sync bị chặn | circuit_breakers.state='open' | Yes | Không có message nào được enqueue cho bot này (do light-check suppress) | Nếu worker nhận được message cũ trước khi circuit open -> discard theo stateVersion check | FR-EXBOT-012, FR-EXBOT-040 |

#### §F.3 — Luồng xử lý: Happy path / Alternate / Exception

| # | Luồng | Trigger | Input chính | Output / Hiệu ứng hệ thống | Actor / Permission | Phản hồi hệ thống | Nguồn |
|---|---|---|---|---|---|---|---|
| L1 | Happy path: delta dương (tăng short) | message đã queue, circuit closed, lock free, delta > 0 | botId, stateVersion, reasons | lệnh adjustShortDelta gửi thành công; reconcile xác nhận; hedge_legs + bot_runtime_state cập nhật; rebalance_attempts status='success' | Hedge-Sync Worker + Reconcile Worker | queue_idempotency.state='succeeded'; hedge_legs.stop_price mới; log ghi nhận | UC §3, flows.md F-02 |
| L2 | Happy path: delta âm (giảm short / reduce-only) | tương tự L1 nhưng target < actual | delta < 0 | adjustShortDelta reduce-only; reconcile xác nhận; cập nhật D1 | Hedge-Sync Worker | Như L1 | UC §3, SRS §FR-022 |
| L3 | A6 (delta=0): không gửi lệnh HL | target = actual sau khi tính | delta = 0 | Bỏ qua HL order; đi thẳng đến INV-STOP stop replacement; ghi rebalance_attempts (reason=delta_zero, hoặc skip HL order) | Hedge-Sync Worker | Log lý do trong rebalance_attempts; queue_idempotency.state='succeeded' | UC §3 step 5 note, A6; OQ-EXBOT-013 open |
| L4 | A1 (lock held): re-queue | lock đang được giữ bởi worker khác | acquired=false | Worker không gửi HL order; message được re-queue với delay | Hedge-Sync Worker | không có output ngoài re-queue | UC §4 A1, FR-EXBOT-026 |
| L5 | A2 (stateVersion mismatch): discard | state_version D1 > message.stateVersion | mismatch | discard; rebalance_attempts.status='skipped' | Hedge-Sync Worker | không có output ngoài ghi log | UC §4 A2, FR-EXBOT-027 |
| L6 | A3 (HL order rejection): circuit increment | HL từ chối lệnh (ví dụ insufficient margin) | HL error response | rebalance_attempts.status='failed'; incrementCircuitBreaker; enqueue notification | Hedge-Sync Worker | E-EXBOT-007: "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." (HTTP 502) | UC §4 A3, FR-EXBOT-040, SRS §5 |
| L7 | Duplicate message delivery (idempotency) | Same message_id được deliver lần 2 | UNIQUE conflict | Return immediately; không xử lý lần 2 | Hedge-Sync Worker | không có output | FR-EXBOT-011, UC §3 step 1 |
| L8 | A4 (partial fill): enqueue partial_repair | reconcile phát hiện \|actual - target\| > drift_threshold | partial mismatch | enqueue partial_repair; rebalance_attempts.status='partial' (hoặc failed) | Reconcile Worker | Repair attempt với cloid mới (version tăng) | UC §4 A4, FR-EXBOT-036 |
| L9 | A5 (stop_replacing_started_at stuck > 60s): SAFE_MODE | INV-STOP bị gián đoạn; worker crash | stop_replacing_started_at không được xóa | Primary detection: light-check phát hiện và enqueue partial_repair + SAFE_MODE (<= 5 phút); Secondary: deep-audit backstop | Light-Check Worker (primary) | Bot vào lifecycle_state='safe_mode' | UC §4 A5, FR-EXBOT-033, FR-EXBOT-035 |
| L10 | Circuit half_open probe | circuit_breakers.state='half_open', reset_at đã đến | 1 message duy nhất được phép | Probe chạy như bình thường; nếu thành công -> circuit closed + failure_count=0; nếu thất bại -> circuit open lại + reset_at = now + 1h; admin notification | Hedge-Sync Worker | US-EXBOT-008 AC-008-3 / AC-008-4 | FR-EXBOT-040, US-EXBOT-008 |
| L11 | HL API unreachable (getPosition fail) | HL không truy cập được | HL timeout / connection error | Bot vào SAFE_MODE sau 5 phút không truy cập được | Hedge-Sync Worker | E-EXBOT-008: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." (HTTP 503) | FR-EXBOT-050, SRS §5 E-EXBOT-008 |
| L12 | KMS signing failure (Signing Lambda) | KMS lỗi trong quá trình ký lệnh | KMS API error | Bot vào SAFE_MODE; admin alert; không có lệnh HL nào được gửi | Signing Lambda -> Hedge-Sync Worker | Admin notification | FR-EXBOT-080 KMS failure handling, IC-EXBOT-005 |

#### §F.4 — Liên kết và nhất quán dữ liệu (Integration & Data Consistency)

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| hedge-sync gửi lệnh adjustShortDelta thành công | Reconcile Worker -> hedge_legs, bot_runtime_state | D1 phải reflect HL actual position sau reconcile; nếu D1 stale -> drift tiếp theo bị tính sai | Sau reconcile: hedge_legs.entry_price và bot_runtime_state.last_known_hl_short_size phải khớp với clearinghouseState | FR-EXBOT-025, flows.md F-02 |
| rebalance_attempts.status='success' được ghi | Thống kê / dashboard / deep-audit | failure_count trong circuit_breakers chỉ reset về 0 khi half_open probe thành công, không phải khi bất kỳ lệnh nào thành công | failure_count không tự reset; chỉ circuit closed state mới tạo ra hàm ý reset | FR-EXBOT-040 |
| INV-STOP protocol chạy | hedge_legs.stop_replacing_started_at, stop_price, stop_cloid | stop_replacing_started_at phải = NULL sau khi hoàn thành (bất kể thành công hay thất bại); nếu still set -> light-check sẽ enqueue partial_repair và bật SAFE_MODE | Kiểm tra: stop_replacing_started_at=NULL sau khi hedge-sync hoàn thành; stop_price và stop_cloid cập nhật | FR-EXBOT-035, FR-EXBOT-033 |
| stateVersion check trước khi acquire lock | bot_runtime_state.state_version, rebalance_attempts | Khi worker A đang xử lý, nếu worker B gửi message với stateVersion cũ thì worker B sẽ discard -> tránh race condition double-submit | state_version trong D1 phải tăng sau mỗi successful rebalance; message cũ (stateVersion thấp hơn) phải bị discard không gửi HL | FR-EXBOT-027, SRS §FR-027 |
| circuit_breakers cập nhật (open/half_open/closed) | light-check worker (suppress hedge-sync khi open), hedge-sync worker (probe khi half_open) | Khi circuit open: light-check không enqueue hedge-sync (nhưng vẫn enqueue price-near-stop-audit) | circuit_breakers.state thay đổi phải được đọc chính xác bởi light-check ở lượt tiếp theo; không dùng cache | FR-EXBOT-012, FR-EXBOT-040, FR-EXBOT-014 |
| partial_repair được enqueue | Repair Worker -> hedge_legs, rebalance_attempts | Nếu repair thất bại 3 lần -> bot_safe_close; close_operations row được tạo | Repair attempt dùng cloid khác (version tăng); sau 3 thất bại phải tạo close_operations row | FR-EXBOT-036, FR-EXBOT-072 |
| hedge-sync chạy trong lúc margin_status='warning' | hedge_legs.margin_status, size increase logic | Warning: chỉ cho phép reduce-only; block tăng size; thông báo Investor qua POOL UI | margin_status được đọc từ D1 (không HL fetch trong light-check); chỉ cập nhật qua hedge-sync preflight và deep-audit | FR-EXBOT-060, BR-EXBOT-003 |
| HL getPosition (weight=2) được gọi | HLRateLimitDO (800 weight/min budget) | Mỗi hedge-sync consumer dùng ít nhất 2 weight (getPosition trước khi gửi lệnh); nếu có nhiều bot chạy đồng thời, tổng weight có thể đạt giới hạn | Weight được khai báo trước khi gọi; HLRateLimitDO trả về {allowed:false, retryAfterMs} nếu quá hạn mức | IC-EXBOT-001, FR-EXBOT-091 |
| KMS signing failure (Signing Lambda) | bot SAFE_MODE, hedge_legs, admin notification | KMS failure trong quá trình ký lệnh HL -> hedge mutation không hoàn thành -> bot vào SAFE_MODE | Sau KMS failure: bot_runtime_state.health_status = safe_mode (hoặc tương đương); admin được báo | FR-EXBOT-080 |
| UserLockDO TTL hết trong khi công việc đang chạy | lease auto-release, worker tiếp theo có thể lấy khóa | Nếu worker không gọi heartbeat trước 90s: khóa tự động giải phóng; worker tiếp theo acquire và reconcile trước khi gửi bất kỳ lệnh mới | Worker tiếp theo phải reconcile actual HL state trước khi submit lệnh mới (không blind submit) | FR-EXBOT-026, SRS §FR-092 |

#### §F.5 — Acceptance Criteria Candidates (Suy luận, cần xác nhận)

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path -- delta dương, reconcile thành công | Bot active, circuit closed, lock free, stateVersion khớp, delta > 0 | Worker xử lý message hedge-sync | adjustShortDelta được gọi với delta chính xác; reconcile xác nhận size; hedge_legs.stop_price cập nhật; rebalance_attempts.status='success' | UC §3, SRS §FR-022/025 |
| AC-02 | Idempotency -- message giao 2 lần | Same message_id đã có trong queue_idempotency với state='started' hoặc 'succeeded' | Worker nhận cùng message lần 2 | UNIQUE conflict; worker return immediately; không có HL order nào được gửi | FR-EXBOT-011 |
| AC-03 | stateVersion mismatch | message.stateVersion=5, nhưng D1 state_version=6 | Worker kiểm tra trước khi acquire lock | discard; rebalance_attempts.status='skipped'; không có HL order | FR-EXBOT-027 |
| AC-04 | Lock held -- re-queue | Worker khác đang giữ UserLockDO cho cùng user | Worker gọi acquire | acquired=false; message được re-queue với delay; không HL order | FR-EXBOT-026 |
| AC-05 | Delta-only -- không close+open trong bình thường | drift_threshold trigger, delta > 0 | hedge-sync chạy | Chỉ adjustShortDelta được gọi; không có closeShort + openShort sequence | BR-EXBOT-004, FR-EXBOT-022 |
| AC-06 | BigDecimal -- không float | delta tính từ targetShortEth và actualShortEth | Kiểm tra code | Không có Number() intermediate trong phép tính delta hoặc stop_trigger_px | NFR-EXBOT-008 |
| AC-07 | INV-STOP -- stop_replacing_started_at bị xóa trong finally | INV-STOP protocol chạy | stop đặt xong (hoặc lỗi) | stop_replacing_started_at=NULL bất kể kết quả | FR-EXBOT-035 |
| AC-08 | Circuit: 3 liên tiếp thất bại -> open | 2 failed attempts trong 24h, attempt thứ 3 fail | incrementCircuitBreaker lần 3 | circuit_breakers.state='open', reset_at=now+1h; light-check tiếp theo không enqueue hedge-sync | FR-EXBOT-040, US-EXBOT-008 AC-008-1 |
| AC-09 | Circuit half_open probe: 1 probe duy nhất | circuit='half_open', reset_at đã đến | light-check chạy | Đúng 1 hedge-sync message được enqueue; half_open_probe_used=1; probe thứ 2 bị chặn | FR-EXBOT-040, US-EXBOT-008 AC-008-2 |
| AC-10 | Partial fill -> partial_repair | reconcile phát hiện \|actual-target\| > drift | Reconcile Worker xử lý | partial_repair message được enqueue; rebalance_attempts.status='partial' | FR-EXBOT-036 |
| AC-11 | delta=0: bỏ qua HL order, tiếp tục stop replacement | computed delta = 0 | Worker tính delta | Không gửi HL order; đi thẳng đến INV-STOP; ghi log; queue_idempotency.state='succeeded' | UC §3 step 5 note, A6; **Suy luận cần xác nhận** (OQ-EXBOT-013) |
| AC-12 | KMS signing failure -> SAFE_MODE | Signing Lambda bị lỗi trong lúc ký lệnh | Worker gửi request đến Signing Lambda | Lệnh không được gửi; bot vào SAFE_MODE; admin được báo | FR-EXBOT-080 KMS failure handling; **Suy luận cần xác nhận** |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| hedge-sync thành công (state_version tăng) | light-check worker (đọc state_version tiếp theo) | Message hedge-sync cũ (stateVersion thấp) sẽ bị discard bởi worker tiếp theo | state_version D1 tăng chậu đối với mỗi successful rebalance | FR-EXBOT-027 |
| circuit_breakers.state đổi sang 'open' | light-check worker | light-check bắt đầu suppress hedge-sync; stop monitoring vẫn tiếp tục | circuit state cần được phản ánh ngay lập tức trong D1 để light-check đọc đúng | FR-EXBOT-012, FR-EXBOT-014 |
| rebalance_attempts.status='failed' + incrementCircuitBreaker | Tổng kết circuit breaker | Nếu 3 failures liên tiếp: circuit open -> toàng bộ hedge-sync cho đến khi half_open -> closed | failure_count tăng đúng, không de-dup, không tăng kép nếu message được deliver 2 lần (idempotency bảo vệ) | FR-EXBOT-040, FR-EXBOT-011 |
| partial_repair enqueue (3 lần thất bại) | close_operations (bot_safe_close trigger) | 3 partial repair failures -> tạo close_operations row -> kích hoạt bot_safe_close | close_operations.idempotency_key UNIQUE ngăn double-trigger | FR-EXBOT-036, FR-EXBOT-072 |
| hedge_legs.margin_status cập nhật (trong preflight hedge-sync) | SAFE_MODE (nếu critical 2 lần liên tiếp) | margin_status='critical' 2 lần liên tiếp -> SAFE_MODE; hedge-sync tiếp theo bị block | D1 phản ánh margin_status chính xác; light-check chỉ đọc D1 (không HL fetch) | FR-EXBOT-050, FR-EXBOT-060 |
| hedge-sync trong trạng thái half_open (probe) | circuit_breakers (reset khi thành công) | Probe thành công -> circuit closed, failure_count=0, normal operation phục hồi | failure_count và circuit state cần được cập nhật atomic | FR-EXBOT-040 |

---

## 8. Acceptance Criteria (từ source)

| AC # | Scenario | Given -- điều kiện | When -- hành động | Then -- kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path -- delta adjustment + reconcile | hedge-sync message nhận được, stateVersion khớp D1, circuit closed, lock free | Worker xử lý end-to-end | adjustShortDelta gửi thành công; reconcile xác nhận size; hedge_legs và bot_runtime_state cập nhật; rebalance_attempts.status='success' | US-EXBOT-006 AC-006-1 |
| AC-02 | stateVersion mismatch -- discard | message.stateVersion=5 nhưng D1 state_version=6 | Worker kiểm tra stateVersion | Discard; rebalance_attempts.status='skipped'; không HL order | US-EXBOT-006 AC-006-2, FR-EXBOT-027 |
| AC-03 | Lock chưa lấy được -- re-queue | Worker khác đang giữ lock | acquire trả về acquired=false | Re-queue với delay; không HL order | US-EXBOT-006 AC-006-3, FR-EXBOT-026 |
| AC-04 | HL order rejection -- circuit increment | HL trả về error (e.g., insufficient margin) | Worker nhận lỗi từ HL | rebalance_attempts.status='failed'; incrementCircuitBreaker; sau 3 consecutive failures trong 24h -> circuit open; notification | US-EXBOT-006 AC-006-4, FR-EXBOT-040 |
| AC-05 | Circuit mở sau 3 failures liên tiếp | 2 failures trước đó trong 24h, attempt thứ 3 fail | Third hedge-sync failure | circuit_breakers.state='open', reset_at=now+1h; light-check không enqueue hedge-sync tiếp theo; stop monitoring vẫn chạy | US-EXBOT-008 AC-008-1, FR-EXBOT-040 |
| AC-06 | Circuit chuyển sang half_open | circuit='open', reset_at đã đến | light-check evaluate | Exactly 1 hedge-sync message được enqueue (probe); half_open_probe_used=1 | US-EXBOT-008 AC-008-2, FR-EXBOT-040 |
| AC-07 | Probe thành công -- circuit đóng | half_open probe chạy thành công | Reconcile xác nhận size | circuit_breakers.state='closed', failure_count=0 | US-EXBOT-008 AC-008-3 |
| AC-08 | Probe thất bại -- circuit mở lại | half_open probe fail | Failure được ghi nhận | circuit_breakers.state='open', reset_at=now+1h; admin notification | US-EXBOT-008 AC-008-4 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Latency | 1 hedge-sync should complete within 30s under normal conditions | Test độ trễ từ lúc nhận message đến khi queue_idempotency.state='succeeded' | NFR-EXBOT-002 |
| Rate Limit | HL API usage <=800 weight/min (67% của 1200 hard limit); getPosition weight=2 | Test đếm weight tiêu thụ trong 1 phút khi nhiều hedge-sync chạy đồng thời | NFR-EXBOT-004, IC-EXBOT-001 |
| Precision / BigDecimal | Tất cả tính toán hedge và stop phải dùng BigDecimal; float/number arithmetic bị cấm | Test đơn vị cho normalizeTargetRatioBps, delta calc, stop_trigger_px; không intermediate Number() | NFR-EXBOT-008, FR-EXBOT-021/030 |
| Idempotency | message_id UNIQUE; cloid tất định | Test giao cùng message 2 lần -> chỉ 1 lần xử lý; test retry với cùng cloid | NFR-EXBOT-007, FR-EXBOT-011/024 |
| Concurrency | Max 6 outbound connections per CF Worker invocation | Test: hedge-sync không mở >6 kết nối song song trong 1 invocation | NFR-EXBOT-011 |
| Security | Private key không lộ ra ngoài KMS; Signing Lambda là IAM principal duy nhất có kms:Sign | Kiểm tra D1 dump không có plaintext key; log audit không có raw key | NFR-EXBOT-006, FR-EXBOT-080 |
| Audit / Logging | rebalance_attempts row phải tồn tại cho mọi attempt (kể cả skipped/failed) | Test: sau mọi hedge-sync (bất kể kết quả), phải có rebalance_attempts row với đầy đủ trường | FR-EXBOT-025, ERD |
| Availability | SAFE_MODE không phải trạng thái kết thúc; phải có đường phục hồi (auto hoặc bot_safe_close) | Test: sau khi vào SAFE_MODE, hệ thống cho phép auto-recovery khi đủ điều kiện | NFR-EXBOT-010, BR-EXBOT-007 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận (Issue Register)

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q1 | High | MISSING_INFO | UC §3 step 5 note; OQ-EXBOT-013 (SRS §9) | Khi delta tính bằng 0, Worker có nên bỏ qua lệnh HL và đi thẳng vào INV-STOP stop replacement hay nên abort toàn bộ hedge-sync? UC chỉ ghi "Behavior pending OQ-EXBOT-013". Nếu skip stop replacement thì stop có thể bị stale khi giá ETH đóng hoặc mở/đóng range. | Nếu delta=0 nhưng stop cần cập nhật (do giá entry thay đổi từ reconcile trước), việc bỏ qua stop replacement là bug. Tester không thể viết expected result cho luồng A6 này. | Tech Lead | Open |
| Q2 | High | MISSING_INFO | UC §3 step 8-9; FR-EXBOT-035; SPEC §19.5 | INV-STOP protocol (§19.5) được mô tả là "protected cancel->place", nhưng chi tiết cụ thể là: (a) place trước rồi cancel sau, hay (b) cancel trước rồi place sau, hay (c) các trường hợp nào đi đường (a) vs (b)? OQ-EXBOT-002 trong SRS note "Does HL support place-before-cancel stop replacement?". Kết quả quyết định nội dung test case cho bước F1-09 và F1-10. | Không biết path (a) hay (b) -> không thể viết test case cho cancel/place sequence và dự kiến vùng thời gian 0-stop tồn tại. | Tech Lead / BA | Open |
| Q3 | High | MISSING_INFO | UC §3 step 6; FR-EXBOT-060; SRS §FR-060 | Worker có phải fetch HL marginSummary (để cập nhật margin_status) TRƯỚC hay SAU khi giành UserLockDO không? OQ-EXBOT-014 trong SRS: "marginSummary fetch ordering in hedge-sync preflight: does the Worker fetch marginSummary before or after acquiring UserLockDO?" Ordering này ảnh hưởng trực tiếp đến lock TTL design. | Nếu fetch sau lock mà mất nhiều thời gian, heartbeat có thể bị bỏ lỡ -> khóa tự động giải phóng -> race condition. Tester không thể viết test cho timeout scenario. | Tech Lead | Open |
| Q4 | High | MISSING_INFO | UC §3 step 5-6; FR-EXBOT-091; SRS §FR-091 | HLRateLimitDO và UserLockDO: rate-limit weight có được tiêu thụ TRƯỚC hay SAU khi giành lock không? OQ-EXBOT-015 trong SRS: "should rate-limit weight be consumed before or after lock acquisition?" | Ảnh hưởng test case cho trường hợp: HL rate limit hit trong khi worker đang giữ UserLockDO lease -- hiện tại không rõ ràng phải xử lý như thế nào. | Tech Lead | Open |
| Q5 | Medium | MISSING_INFO | UC §4 A4; FR-EXBOT-040; SRS §FR-040 | "Consecutive failures" trong circuit breaker được UC định nghĩa là "rolling 24h window, no intervening success". Nhưng khi có PARTIAL fill (status='partial') -- partial có được coi là "failure" để tăng failure_count không? | Nếu partial fill không tăng failure_count, circuit có thể không bao giờ open dù có nhiều partial fail. | Tech Lead / BA | Open |
| Q6 | Medium | MISSING_INFO | FR-EXBOT-036; SRS §FR-036 | Chi tiết vấn đề khi reconcile phát hiện partial mismatch: ngưỡng chính xác để phát hiện "partial fill" là gì? drift_threshold của `partial_repair` có phải cùng threshold với `drift_threshold` trong light-check (max($25, lpValueUsd x 3%)) không? OQ-EXBOT-004 (dust handling) liên quan. | Nếu threshold khác nhau, expected result của test reconcile partial fill sẽ khác. | Tech Lead | Open |
| Q7 | Medium | UNCLEAR_INFO | UC §3 step 12-13; FR-EXBOT-030; SRS §FR-030 | stop_trigger_px được "tính lại" sau reconcile, nhưng nếu delta=0 (không có lệnh HL) thì entry_price và liq_price có được update hay vẫn giữ giá trị cũ? UC step 12-13 ngầm định rằng reconcile luôn trả về giá trị mới. | Nếu entry_price không đổi (vì delta=0, không có fill), việc tính lại stop_trigger_px cũng cho kết quả cũ -> stop replacement trong luồng A6 có thể là no-op. Expected result của AC-11 bị mơ hồ. | BA / Tech Lead | Open |
| Q8 | Medium | CROSS_SOURCE_CONFLICT | UC §7 FR Trace vs SRS §7 UC Inventory | UC §7 FR Trace của `uc-hedge-sync` ghi: "FR-EXBOT-022, 024, 025, 026, 027, 036". SRS §7 UC Inventory ghi: "FR-EXBOT-020, 021, 022, 024, 025, 026, 027, 035". UC thiếu FR-020 (LP position amount calculation), FR-021 (BigDecimal target computation), FR-035 (INV-STOP); UC thêm FR-036 (partial_repair) không có trong SRS §7. | FR-020 và FR-021 là phần cốt lõi của hedge-sync; nếu không có trong FR Trace thì test sẽ thiếu coverage cho tính toán target size. | BA | Open |
| Q9 | Medium | UNCLEAR_INFO | UC §2 Preconditions; SRS §FR-026 | Precondition của UC chỉ ghi "circuit_breakers.state IN ('closed','half_open')". Nhưng UC không mô tả rõ: ai/khi nào kiểm tra circuit state -- là trong message khi enqueue, hay trong Worker trước khi acquire lock, hay sau khi acquire lock? | Thiếu bước xử lý khi circuit đổi trạng thái giữa enqueue và execute. Tester không biết nên expect Worker hủy hay vẫn chạy. | BA / Tech Lead | Open |
| Q10 | Low | MISSING_INFO | UC §3, SRS; ERD rebalance_attempts | Trường `reason` trong `rebalance_attempts` (RebalanceReason CSV): khi A6 (delta=0), `reason` được ghi là gì? Và khi A2 (stateVersion mismatch), rebalance_attempts có được ghi không? UC chỉ mô tả status='skipped' nhưng không rõ ràng. | Ảnh hưởng expected result khi test audit log. | Tech Lead | Open |
| Q11 | Low | SOLUTION_DETAIL_LEAK | UC §3 step 1-3; FR-EXBOT-011/026/027 | UC mô tả rất chi tiết về quy trình: (1) insert idempotency, (2) check stateVersion, (3) acquire lock -- theo đúng thứ tự này. Nhưng UC không giải thích lý do kinh doanh tại sao phải theo đúng thứ tự này. Đây là implementation detail đang lọt vào UC document. | Nếu thứ tự thay đổi trong implementation, UC sẽ "sai" dù logic nghiệp vụ không thay đổi. | BA | Open |
| Q12 | Low | MISSING_INFO | flows.md F-02; UC chưa có diagram | UC có một Mermaid placeholder diagram với User->System template generic, không mô tả actor-system interaction thực tế cho hedge-sync. Diagram trong flows.md F-02 đầy đủ hơn nhưng là sequence diagram ở mức module, không phải UC-level. | Thiếu visual representation để confirm luồng; tester phải tự suy ra từ text. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-013: delta=0 behavior | UC / Tech decision | Blocks test design cho luồng A6 (AC-11) | Tech Lead | Open |
| OQ-EXBOT-002: HL place-before-cancel stop? | Integration / HL API | Blocks test design cho INV-STOP cancel/place sequence (F1-09/F1-10) | Tech Lead / BA | Open |
| OQ-EXBOT-014: marginSummary fetch order | UC / Tech decision | Blocks test case cho timeout và heartbeat scenarios | Tech Lead | Open |
| OQ-EXBOT-015: rate-limit weight timing vs lock | UC / Tech decision | Blocks test case cho rate-limit + lock interaction | Tech Lead | Open |
| OQ-EXBOT-004: HL min order size / dust | Integration / HL API | Ảnh hưởng threshold cho partial fill detection (Q6) | Tech Lead | Open |
| SPEC §19.5 INV-STOP protocol chi tiết | Integration / HL API | Chi tiết cancel/place path chưa được confirm | BA / zen | Open |
| BnzaExVault final ABI (OQ-EXBOT-008) | Integration | Không trực tiếp ảnh hưởng hedge-sync nhưng ảnh hưởng close flow liên kết | zen | Open |

---

## 10.3 Audit Summary — Bảng điểm và Verdict

### Bảng điểm

| # | Khu vực đánh giá | Điểm tối đa | Điểm đạt | Trạng thái | Ghi chú chủ yếu |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 17 | Partial | 25 F1 items được liệt kê đầy đủ và atomic; 2 điểm trừ: (a) UC FR Trace thiếu FR-020/021/035 (Q8); (b) UC diagram là placeholder generic, không mô tả interaction thực tế (Q12) |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 18 | Partial | BR-EXBOT-004/005/007/009 được mô tả; delta=0 behavior chưa chốt (Q1 Blocker); INV-STOP path (a) vs (b) chưa rõ (Q2 Blocker); marginSummary fetch order chưa rõ (Q3 High); rate-limit+lock interaction chưa rõ (Q4 High) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 18 | Partial | 12 luồng được mô tả (L1-L12); luồng A6 delta=0 có expected result mơ hồ (Q1); luồng INV-STOP cancel/place sequence chưa rõ (Q2); circuit state change giữa enqueue và execute chưa có xử lý (Q9) |
| 4 | Functional Integration & Data Consistency | 15 | 12 | Partial | Nhận quan on-chain/off-chain nhất quán (D1 vs HL); HLRateLimitDO weight accounting; UserLockDO TTL; partial_repair -> bot_safe_close chain. 3 điểm trừ: lock+rate-limit ordering chưa rõ (Q4), partial fill threshold chưa rõ (Q6) |
| 5 | UC / Spec Documentation Quality Issues | 15 | 9 | Partial | 3 Blocker-impact issues (Q1 delta=0 unresolved, Q2 INV-STOP path unresolved, Q3 marginSummary order); CROSS_SOURCE_CONFLICT FR Trace (Q8); 1 SOLUTION_DETAIL_LEAK vừa (Q11); UC diagram là placeholder (Q12) |
| **Tổng** | | **100** | **74** | **Conditionally Ready** | |

### Auto-cap check

- Không có scoring area = 0.
- Không có required artefact bị blocked.
- Area 2 và Area 3 có Blocker-impact issues nhưng không cap xuống 0 vì core behavior (happy path, circuit breaker, idempotency) vẫn rõ ràng từ SRS.
- Area 5: CROSS_SOURCE_CONFLICT (Q8) -> cap area 5 max 70%; tại 9/15 điểm (60% of max) vẫn trong band cho phép sau cap.

### Blocks và issues chính

**Blocker-level (ảnh hưởng test design):**
- **Q1** -- delta=0 behavior (OQ-EXBOT-013): luồng A6 chưa có expected result rõ ràng. Nếu delta=0 thì có chạy stop replacement hay không? Tester không thể viết AC-11.
- **Q2** -- INV-STOP path (OQ-EXBOT-002): cancel-before-place vs place-before-cancel trên HL chưa được confirm. Ảnh hưởng toàn bộ test cho F1-09/F1-10.

**Major issues (ảnh hưởng coverage nhưng không block hoàn toàn):**
- **Q3** -- marginSummary fetch order (OQ-EXBOT-014): ảnh hưởng test timeout/heartbeat scenario.
- **Q4** -- rate-limit vs lock ordering (OQ-EXBOT-015): ảnh hưởng test concurrent rate-limit case.
- **Q8** -- CROSS_SOURCE_CONFLICT: FR Trace trong UC thiếu FR-020/021/035 so với SRS §7.

### Khuyến nghị

UC-EXBOT-hedge-sync đạt 74/100 điểm -- **Conditionally Ready**. Phần core của hedge-sync (delta-only invariant, idempotency, UserLockDO, circuit breaker, reconcile, D1 update) được mô tả đầy đủ và nhất quán với SRS. Tester có thể bắt đầu thiết kế test cho các luồng chính (L1-L5, L7-L8, L10), và các test case circuit breaker (AC-05 đến AC-08).

Trước khi thiết kế test cho luồng A6 (delta=0) và test case INV-STOP cancel/place sequence, QC Lead nên chuyển Q1 và Q2 cho Tech Lead để lấy câu trả lời. Sau khi có câu trả lời, nên re-audit nhanh (Update mode) để cập nhật expected result tương ứng.

**Hành động đề xuất:**
1. QC Lead chuyển Q1, Q2, Q3, Q4 cho Tech Lead (dựa trên OQ-EXBOT-013, 002, 014, 015 trong SRS).
2. BA xác nhận Q5 (partial count vào failure_count?) và Q8 (thống nhất FR Trace giữa UC và SRS).
3. Bắt đầu thiết kế test scenarios cho các luồng rõ ràng (L1, L2, L4, L5, L7, L8, L10, L11, L12) -- không cần chờ Q1/Q2.
4. Re-audit sau khi Q1 và Q2 được trả lời.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu |

---

*Báo cáo rà soát mức độ sẵn sàng UC — ExBot logic-only variant*
