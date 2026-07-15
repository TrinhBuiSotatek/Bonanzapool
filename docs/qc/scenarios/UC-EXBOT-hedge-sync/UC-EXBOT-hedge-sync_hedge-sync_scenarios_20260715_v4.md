# Test Scenarios — UC-EXBOT-hedge-sync Execute Delta-Only Hedge Adjustment

> Source: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260715_v4.md
> Generated: 2026-07-15
> Author: QC Func Scenario Design ExBot Agent
> Version: v4
> Domain/Architecture: AWS Lambda (ExBot) + Hyperliquid API + Aurora PostgreSQL (control_db + state_db_shard) + Redis Redlock via ElastiCache (UserLock) + HLRateLimit (ElastiCache) + SQS queue topology (hedge-sync → reconcile → partial_repair)
>
> **Changes from v3 (4 new scenarios added):**
> - NEW: TS_053 — marginSummary fetch sequence: margin_status updated AFTER lock, BEFORE mutation (Q3 closed)
> - NEW: TS_054 — slow marginSummary call triggers extend() to prevent TTL expiry (Q3 closed)
> - NEW: TS_055 — step 2 short-circuit: stateVersion mismatch discards before circuit recheck (N4-03)
> - NEW: TS_056 — F-01 light-check "suppress this tick only" ≠ permanent suppress; next tick resumes (flows.md F-01 fix)
> - UPDATED: Out-of-Scope Flags — Q3 removed (answered); Q1/Q2/Q6 remain blocked
> - Scenarios TS_001–TS_052 carry forward unchanged from v3


---

## Bảng mã viết tắt

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| HL | Hyperliquid — sàn giao dịch perpetual bên ngoài. Trong dự án, ExBot short ETH trên HL để hedge LP position trên Uniswap V3. Mọi lệnh delta, stop market đều gửi qua HL API. | (tên sản phẩm) |
| Aurora PostgreSQL | AWS Aurora PostgreSQL Serverless v2 — cơ sở dữ liệu quan hệ phân tán. ExBot dùng control_db và state_db_shard để lưu trạng thái bot, hedge_legs, queue_idempotency, v.v. | SRS §1.1, FM-XB-01 |
| SQS | AWS Simple Queue Service — hàng đợi message thay thế Cloudflare Queue. ExBot dùng 11 queue SQS FIFO bao gồm hedge-sync, reconcile, partial_repair, user_redeem, v.v. | SRS §FM-XB-02 |
| ElastiCache | AWS ElastiCache Redis — cluster Redis chia sẻ cho 3 mục đích: HLRateLimit (rate limiter), UserLock via Redlock (mutex per-user), pool slot0 cache (MarketData). | SRS §FM-XB-03, FR-EXBOT-091/092/093 |
| Redlock | Redis Redlock distributed mutex algorithm — cung cấp phân tán mutex per-user qua ElastiCache. Interface: acquire(holderToken, ttl=90s, idempotencyKey) → {acquired, lockKey}; extend(holderToken, ttl); release(holderToken, idempotencyKey). holderToken mismatch = no-op. | FR-EXBOT-092 |
| INV-STOP | Invariant: khi HL short khác 0, phải luôn tồn tại verified reduce-only stop. Giao thức INV-STOP (§19.5 SPEC) là protected cancel→place nhằm không bao giờ để khoảng thời gian không có stop. | FR-EXBOT-032/035, SPEC §19.5 |
| cloid | Client Order ID — mã lệnh tất định theo công thức keccak256. Dùng để HL dedup và ExBot idempotency khi retry. Công thức: first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}")). | FR-EXBOT-022/024 |
| BigDecimal | Kiểu số thập phân chính xác tùy ý (không float). Mọi phép tính hedge, stop, margin trong ExBot bắt buộc dùng BigDecimal. | NFR-EXBOT-008 |
| delta | Chênh lệch giữa targetShortEth và actualShortEth. Chỉ phần chênh lệch này được gửi lên HL (delta-only invariant). | FR-EXBOT-020/022 |
| stateVersion | Số phiên bản trạng thái bot trong Aurora PostgreSQL (bot_runtime_state.state_version). Dùng để phát hiện message queue lỗi thời, tránh race condition. | FR-EXBOT-027 |
| circuit breaker | Cơ chế bảo vệ tự động ngừng enqueue hedge-sync khi có 3 lần thất bại liên tiếp trong 24h. 3 trạng thái: closed, open, half_open. | FR-EXBOT-040 |
| partial_repair | Hàng đợi và worker xử lý khi reconcile phát hiện fill một phần (|actual − target| > drift_threshold). | FR-EXBOT-036 |
| marginUsage | Tỷ lệ ký quỹ: marginRequiredUsd / marginBalanceUsd. Ngưỡng warning: 0.55–0.75; critical: ≥ 0.75. | FR-EXBOT-060 |
| SAFE_MODE | Trạng thái bot không cho phép bất kỳ mutation nào. Bot chỉ được monitor và retry kết nối. | FR-EXBOT-050 |
| RebalanceReason | Enum lý do kích hoạt hedge-sync. Giá trị cụ thể là canonical enum trong FR-EXBOT-023; không thêm giá trị mới. | FR-EXBOT-023 |
| marginSummary | Dữ liệu ký quỹ được fetch từ HL API sau khi acquire Redlock — dùng để update margin_status trước khi thực hiện hedge mutation. | FR-EXBOT-060, Q3 answer (Tech Lead 2026-07-14) |


## UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_001
**Scenario Title:** Happy path — delta dương, bot active, circuit closed, lock free, reconcile thành công
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027
**Test Type:** Functional
**Description:** Gửi message hedge-sync hợp lệ với stateVersion khớp Aurora PostgreSQL, bot đang ở trạng thái active, circuit breaker closed, User Lock chưa bị giữ, và targetShortEth > actualShortEth (delta dương). Hệ thống phải hoàn thành đầy đủ: insert idempotency, check stateVersion, recheck circuit tại execution time, acquire Redlock, fetch HL position, tính delta bằng BigDecimal, gửi adjustShortDelta với cloid tất định, enqueue reconcile, thực hiện INV-STOP stop replacement, release lock. Reconcile worker xác nhận size khớp expected, cập nhật hedge_legs và bot_runtime_state, insert rebalance_attempts với status='success' và reason = original RebalanceReason[] từ message payload.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_002
**Scenario Title:** Happy path — delta âm, giảm short (reduce-only)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, SRS §FR-022
**Test Type:** Functional
**Description:** Gửi message hedge-sync với delta âm (targetShortEth < actualShortEth). Hệ thống phải tính delta âm bằng BigDecimal và gửi adjustShortDelta reduce-only. Reconcile xác nhận size sau khi giảm. Không được gửi full close rồi open lại — chỉ được gửi phần delta chênh lệch (bất biến BR-EXBOT-004).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_003
**Scenario Title:** Idempotency — message_id đã tồn tại trong queue_idempotency
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-011, NFR-EXBOT-007
**Test Type:** Functional
**Description:** Deliver cùng một message (cùng message_id) vào hàng đợi hedge-sync lần thứ hai trong khi message đó đã được xử lý trước đó (queue_idempotency.state='succeeded'). Worker phải phát hiện UNIQUE conflict khi insert message_id và return immediately mà không gửi bất kỳ HL order nào, không thay đổi Aurora PostgreSQL state.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_004
**Scenario Title:** Idempotency — message_id đang ở state='started' (delivery đồng thời)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-011, NFR-EXBOT-007
**Test Type:** Functional
**Description:** Deliver cùng message_id vào hedge-sync khi một instance worker khác đang xử lý (queue_idempotency.state='started'). Worker thứ hai phải gặp UNIQUE constraint conflict và return immediately, không gửi HL order. Chỉ có đúng 1 trong 2 worker tiếp tục xử lý.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_005
**Scenario Title:** stateVersion mismatch — discard message không gửi HL order
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-027, SRS §FR-027
**Test Type:** Functional
**Description:** Gửi message với message.stateVersion=5 nhưng Aurora PostgreSQL bot_runtime_state.state_version=6 (message đã lỗi thời). Worker phải đọc stateVersion từ Aurora PostgreSQL trước khi acquire Redlock, phát hiện mismatch, discard message, và insert rebalance_attempts với status='skipped' và reason = original RebalanceReason[] từ message payload. Không được gửi HL order. Không acquire User Lock.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_006
**Scenario Title:** stateVersion mismatch — stateVersion message cao hơn Aurora PostgreSQL (bất thường)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-027
**Test Type:** Functional
**Description:** Gửi message với message.stateVersion=7 nhưng Aurora PostgreSQL state_version=6 (message từ tương lai — không hợp lệ). Worker phải xử lý trường hợp này: hoặc discard (mismatch), hoặc xử lý nếu spec cho phép. Kết quả phải nhất quán và không gây double mutation.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_007
**Scenario Title:** User Lock lock đang bị giữ — re-queue với delay
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, FR-EXBOT-092
**Test Type:** Functional
**Description:** Worker gọi User Lock (Redis Redlock).acquire() khi một worker khác đang giữ lease cho cùng user. Redlock trả về acquired=false và currentHolderExpiresAt. Worker phải không gửi HL order và re-queue message với delay phù hợp (FR-EXBOT-026: acquired=false → re-queue with delay). Không được bỏ message hay xử lý khi chưa có lock.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_008
**Scenario Title:** User Lock TTL hết hạn trong khi worker đang xử lý — extend để gia hạn
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, FR-EXBOT-092
**Test Type:** Functional
**Description:** Worker acquire Redlock thành công nhưng xử lý mất hơn 30 giây. Worker phải gọi User Lock.extend(holderToken, ttlMs) trước khi TTL 90s hết để gia hạn lease (FR-EXBOT-092: extend gọi Lua script kiểm tra ownership). Nếu extend thành công, worker tiếp tục xử lý và release lock trong finally block sau khi hoàn thành.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_009
**Scenario Title:** User Lock TTL tự hết — worker tiếp theo phải reconcile trước khi mutation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, FR-EXBOT-092
**Test Type:** Integration
**Description:** Worker A acquire Redlock nhưng bị crash hoặc không gọi extend, TTL 90s hết và lock tự động giải phóng (ElastiCache TTL expiry). Worker B acquire lock sau đó và phải fetch actual HL position để reconcile trước khi submit bất kỳ lệnh HL mới nào. Không được "blind submit" dựa vào state Aurora PostgreSQL cũ.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_010
**Scenario Title:** HL getPosition thất bại — bot vào SAFE_MODE sau 5 phút không truy cập được
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-050, SRS §FR-050; E-EXBOT-008: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."
**Test Type:** Functional
**Description:** HL API không trả về kết quả khi worker gọi getPosition (clearinghouseState). Sau khi HL không truy cập được liên tục quá 5 phút, hệ thống phải chuyển bot sang lifecycle_state='safe_mode'. Thông báo E-EXBOT-008 được gửi: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_011
**Scenario Title:** HL order bị reject (insufficient margin) — incrementCircuitBreaker chỉ khi status='failed', enqueue notification
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, FR-EXBOT-035, UC §4 A3; E-EXBOT-007: "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin."
**Test Type:** Functional
**Description:** Worker gửi adjustShortDelta nhưng HL trả về lỗi insufficient margin (status='failed'). Worker phải: ghi rebalance_attempts.status='failed', gọi incrementCircuitBreaker (failure_count tăng 1), enqueue notification với event=hedge_failure. Lỗi E-EXBOT-007 được ghi. Lưu ý: đây là path duy nhất gọi incrementCircuitBreaker — partial fill KHÔNG gọi incrementCircuitBreaker (xác nhận Q5).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_012
**Scenario Title:** Circuit breaker — 3 lần thất bại liên tiếp trong 24h → circuit open
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, US-EXBOT-008 AC-008-1
**Test Type:** Functional
**Description:** Sau 2 lần thất bại trước đó (failure_count=2), attempt thứ 3 cũng fail. incrementCircuitBreaker lần 3 chuyển circuit_breakers.state='open' và đặt reset_at = now + 1h. Light-check lần tiếp theo không được enqueue hedge-sync cho bot này; stop monitoring vẫn tiếp tục.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_013
**Scenario Title:** Circuit open — message cũ (enqueue trước khi circuit open) bị discard qua stateVersion
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-012, FR-EXBOT-040
**Test Type:** Functional
**Description:** Circuit breaker vừa chuyển sang 'open'. Message hedge-sync đã enqueue ngay trước đó vẫn còn trong hàng đợi. Worker nhận message, check stateVersion — vì state_version đã tăng sau khi circuit open, message bị discard (status='skipped'). Không gửi HL order.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_014
**Scenario Title:** Circuit half_open — đúng 1 probe được phép (atomic claim half_open_probe_used)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, US-EXBOT-008 AC-008-2
**Test Type:** Functional
**Description:** circuit_breakers.state='half_open' và reset_at đã đến. Light-check enqueue đúng 1 message hedge-sync (probe) và đặt half_open_probe_used=1 (atomic 0→1). Mọi attempt tiếp theo trong cùng half_open phải bị chặn — half_open_probe_used không thể set thành 1 hai lần.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_015
**Scenario Title:** Circuit half_open probe thành công → circuit closed, failure_count=0
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, US-EXBOT-008 AC-008-3
**Test Type:** Functional
**Description:** Probe hedge-sync trong trạng thái half_open thành công và reconcile xác nhận size. Circuit phải chuyển state='closed' và failure_count=0. Normal operation phục hồi — light-check tiếp theo có thể enqueue hedge-sync bình thường.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_016
**Scenario Title:** Circuit half_open probe thất bại → circuit open lại, reset_at gia hạn
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, US-EXBOT-008 AC-008-4
**Test Type:** Functional
**Description:** Probe hedge-sync trong trạng thái half_open thất bại (HL reject). Circuit phải chuyển về state='open' và đặt reset_at = now + 1h (gia hạn mới). Admin notification được gửi. Bot không hedge-sync cho đến khi reset_at mới đến.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_017
**Scenario Title:** Bất biến delta-only — tuyệt đối không gửi full close+open trong hedge-sync bình thường
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync BR-EXBOT-004, FR-EXBOT-022
**Test Type:** Functional
**Description:** Worker xử lý hedge-sync với drift_threshold trigger. Hệ thống chỉ gửi adjustShortDelta, không được gửi sequence closeShort rồi openShort mới. Reconcile xác nhận size = target ± tolerance. Vi phạm BR-EXBOT-004 nếu có close+open sequence.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_018
**Scenario Title:** margin_status='warning' — chỉ cho phép reduce-only, chặn tăng size
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060
**Test Type:** Functional
**Description:** hedge_legs.margin_status='warning' trong Aurora PostgreSQL khi worker đọc. Nếu delta dương (tăng size), worker phải chặn, không gửi adjustShortDelta increase. Nếu delta âm (giảm size), reduce-only vẫn được phép gửi bình thường.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_019
**Scenario Title:** Biên marginUsage = 0.55 (đúng ngưỡng warning)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060
**Test Type:** Data/State
**Description:** marginUsage tính bằng BigDecimal bằng đúng 0.55. Trạng thái phải là 'warning' (không phải 'ok'). Size-increase bị disable. Cảnh báo gửi đến Investor.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_020
**Scenario Title:** Biên marginUsage = 0.5499 (ngay dưới ngưỡng warning)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060
**Test Type:** Data/State
**Description:** marginUsage = 0.5499 (< 0.55). Trạng thái phải là 'ok'. Size-increase được phép. Tính toán BigDecimal để không sai số floating point.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_021
**Scenario Title:** Biên marginUsage = 0.75 (đúng ngưỡng critical)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060
**Test Type:** Data/State
**Description:** marginUsage = 0.75 (đúng ngưỡng critical, confirmed 2 lần liên tiếp). Bot phải chuyển sang lifecycle_state='safe_mode'. Tất cả mutation bị chặn. Cảnh báo gửi đến cả Investor và Admin.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_022
**Scenario Title:** Biên marginUsage = 0.7499 (ngay dưới critical, trên warning)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060
**Test Type:** Data/State
**Description:** marginUsage = 0.7499 (< 0.75). Trạng thái phải là 'warning', không phải 'critical'. Size-increase bị disable nhưng bot chưa vào SAFE_MODE. Xác nhận critical chỉ trigger khi ≥ 0.75 xảy ra 2 lần liên tiếp.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_023
**Scenario Title:** marginUsage critical — confirm 1 lần (chưa đủ 2 lần liên tiếp) — KHÔNG vào SAFE_MODE
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060
**Test Type:** Data/State
**Description:** marginUsage ≥ 0.75 xảy ra 1 lần. Chưa đủ ×2 consecutive để trigger SAFE_MODE. Bot phải ở trạng thái 'critical' warning nhưng chưa chuyển sang safe_mode. Lần tiếp theo nếu vẫn ≥ 0.75 thì mới trigger.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_024
**Scenario Title:** INV-STOP — cancel stop trước, sau đó place stop mới (không để khoảng trống)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-032, FR-EXBOT-035, SPEC §19.5
**Test Type:** Functional
**Description:** Sau khi adjustShortDelta thay đổi size, stop cũ cần được thay thế bằng stop mới với size khớp hedge. Worker phải thực hiện INV-STOP protocol (§19.5): đặt stop_replacing_started_at trước khi cancel, sau đó place stop mới, cuối cùng clear trong finally block. Không được có khoảng thời gian vị thế không có stop. Verify sau khi hoàn thành: hedge_legs.stop_cloid khớp với cloid mới, stop_price khớp tính toán BigDecimal.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_025
**Scenario Title:** INV-STOP — stop placement thất bại, stop_replacing_started_at không được giữ >60s → SAFE_MODE
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-032, FR-EXBOT-050
**Test Type:** Functional
**Description:** Worker bắt đầu INV-STOP protocol (đặt stop_replacing_started_at), cancel stop cũ, nhưng place stop mới thất bại. stop_replacing_started_at bị stuck hơn 60 giây. Hệ thống phải phát hiện stuck marker và chuyển bot sang lifecycle_state='safe_mode'. Đây là fail-safe để ngăn hedge không có stop bảo vệ.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_026
**Scenario Title:** INV-STOP — crash giữa cancel và place (process restart) — stop_replacing_started_at dùng để phát hiện trạng thái không nhất quán
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-032, SPEC §19.5
**Test Type:** Integration
**Description:** Worker cancel stop thành công rồi crash trước khi place stop mới. Sau khi restart, deep-audit hoặc recovery worker phát hiện stop_replacing_started_at ≠ null và verifies không có active stop trên HL. Recovery phải trigger SAFE_MODE hoặc place lại stop — không được bỏ qua trạng thái không nhất quán này.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_027
**Scenario Title:** Reconcile — actual HL size khớp expectedAbsSize trong tolerance
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-025, FR-EXBOT-036
**Test Type:** Integration
**Description:** Reconcile worker nhận message từ reconcile queue, fetch actual HL position, và xác nhận |actual − expected| ≤ drift_threshold. Hệ thống phải update hedge_legs, bot_runtime_state.last_known_hl_short_size, insert rebalance_attempts với status='success' và reason = original RebalanceReason[] từ message payload.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_028
**Scenario Title:** Reconcile — partial fill, |actual − target| > drift_threshold → enqueue partial_repair
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-036
**Test Type:** Integration
**Description:** Reconcile phát hiện |actual HL size − expectedAbsSize| > drift_threshold (fill một phần). Worker phải enqueue message vào partial_repair queue và insert rebalance_attempts với status='partial'. KHÔNG gọi incrementCircuitBreaker — partial fill không phải failure HL rejection (xác nhận từ Q5 audit).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_029
**Scenario Title:** Reconcile — HL position = 0 sau khi adjust (không kỳ vọng)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-025, FR-EXBOT-036
**Test Type:** Data/State
**Description:** Reconcile fetch HL position và nhận được size = 0 trong khi expected > 0. Hệ thống phải ghi nhận đây là reconcile mismatch nghiêm trọng, không phải partial fill, và xử lý phù hợp (SAFE_MODE hoặc escalate). Không được silent-ignore.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_030
**Scenario Title:** cloid tất định — retry cùng attempt gửi cùng cloid, HL dedup không double-apply
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, FR-EXBOT-024
**Test Type:** Functional
**Description:** Worker retry adjustShortDelta với cùng botId, attemptId, stage, version. cloid phải tính ra cùng giá trị (first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))). HL nhận order với cloid đã tồn tại và trả về idempotent response — không execute lại lệnh. Verify HL short size không thay đổi so với lần đầu.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_031
**Scenario Title:** cloid khác nhau cho các stage khác nhau trong cùng attemptId
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, FR-EXBOT-024
**Test Type:** Functional
**Description:** Trong cùng attemptId, adjustShortDelta (stage='adjust') và replaceStop (stage='stop') phải có cloid khác nhau. Hai lệnh này là 2 operations độc lập — không thể dùng chung cloid. Verify bằng cách inspect cloid trong rebalance_attempts và hedge_legs.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_032
**Scenario Title:** Persistence — rebalance_attempts ghi đúng reason = original RebalanceReason[] cho mọi outcome
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-023, FR-EXBOT-025; Aurora PostgreSQL rebalance_attempts
**Test Type:** Data/State
**Description:** Sau khi hedge-sync hoàn thành (bất kể happy path, A2 fail, A3 skip), rebalance_attempts.reason phải chứa original RebalanceReason[] từ message payload, không được thay thế hay modify. Verify 3 outcomes: status='success', 'failed', 'skipped' — tất cả phải giữ nguyên reason gốc từ message.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_033
**Scenario Title:** Aurora PostgreSQL stateVersion tăng sau khi hedge-sync thành công
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-027
**Test Type:** Data/State
**Description:** Sau khi reconcile xác nhận thành công và Aurora PostgreSQL được update, bot_runtime_state.state_version phải tăng. Message hedge-sync cũ (với stateVersion cũ) được enqueue lại phải bị discard bởi worker tiếp theo vì mismatch.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_034
**Scenario Title:** Lifecycle state 'active' — hedge-sync được phép chạy bình thường
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync states.md State Registry
**Test Type:** Functional
**Description:** Bot ở lifecycle_state='active'. Worker nhận message hedge-sync, check state, proceed bình thường. Happy path hoàn thành. Verify State Registry — chỉ 'active' cho phép event-driven hedge-sync.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_035
**Scenario Title:** Lifecycle state 'safe_mode' — hedge-sync bị chặn, stop monitoring vẫn active
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync states.md State Registry; FR-EXBOT-050
**Test Type:** Functional
**Description:** Bot ở lifecycle_state='safe_mode'. Worker nhận message hedge-sync và phải block — không gửi HL order. Tuy nhiên stop monitoring vẫn phải tiếp tục (safe_mode chỉ block mutations, không block monitoring). Verify rebalance_attempts insert với status='skipped'.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_036
**Scenario Title:** Lifecycle state 'hedge_stopped_cooldown' — hedge-sync bị suppress 4h sau stop trigger
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync states.md State Registry
**Test Type:** Functional
**Description:** Bot ở lifecycle_state='hedge_stopped_cooldown'. Light-check phải chạy (state: run (no hedge-sync)) nhưng không được enqueue hedge-sync trong suốt 4h cooldown. Sau khi cooldown kết thúc và re-hedge thành công, bot trở về 'active' và hedge-sync có thể enqueue lại.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_037
**Scenario Title:** Concurrency — 2 workers race để acquire User Lock cùng lúc (chỉ 1 thành công)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, FR-EXBOT-092
**Test Type:** Integration
**Description:** Hai worker cùng xử lý message hedge-sync cho cùng user (do SQS redelivery hoặc multiple invocations). Cả hai gọi User Lock (Redis Redlock).acquire() đồng thời. Chỉ đúng 1 worker nhận acquired=true; worker còn lại nhận acquired=false và phải re-queue with delay. Verify không có double-mutation trên HL.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_038
**Scenario Title:** stateVersion check trước lock acquire — tránh waste acquire khi message lỗi thời
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-027, flows.md F-02
**Test Type:** Functional
**Description:** Worker phải check stateVersion từ Aurora PostgreSQL TRƯỚC khi gọi User Lock.acquire(). Nếu mismatch detected sớm, worker discard message mà không tốn lock acquire overhead. Verify ordering: stateVersion check → (mismatch → discard, không acquire) vs (match → acquire lock → tiếp tục).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_039
**Scenario Title:** circuit recheck tại execution time — circuit open sau khi message đã dequeue
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-012, FR-EXBOT-040
**Test Type:** Functional
**Description:** Message hedge-sync enqueue khi circuit='closed'. Giữa lúc enqueue và dequeue, circuit chuyển sang 'open' (3 failures xảy ra). Worker phải check circuit state từ Aurora PostgreSQL tại execution time (không phải lúc enqueue). Nếu circuit open, suppress mutation và discard message.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_040
**Scenario Title:** delta = 0 (target = actual, không cần điều chỉnh)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, BR-EXBOT-004
**Test Type:** Functional
**Description:** Worker tính delta = targetShortEth − actualShortEth = 0 (bằng BigDecimal). Không cần gửi HL order. Worker phải xử lý case này gracefully — không gửi zero-size order, không gây lỗi. Verify Aurora PostgreSQL: rebalance_attempts insert với status='success' (no-op) và hedge_legs không thay đổi.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_041
**Scenario Title:** drift_threshold trigger — delta nhỏ hơn minimum tick size HL
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, NFR-EXBOT-008
**Test Type:** Boundary
**Description:** Tính delta bằng BigDecimal cho ra giá trị nhỏ hơn minimum order size của HL (ví dụ 0.0001 ETH). Worker phải xử lý trường hợp này: hoặc discard (no-op dưới ngưỡng), hoặc round lên minimum tick, không được gửi invalid order. Behavior phải được xác định rõ (chưa có trong UC — confirm với BA).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_042
**Scenario Title:** RebalanceReason enum — hedge-sync với reason không thuộc canonical enum
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-023
**Test Type:** Functional
**Description:** Message hedge-sync chứa reason nằm ngoài canonical RebalanceReason enum. Worker phải reject hoặc handle gracefully — không được process lệnh với unknown reason. Verify behavior: lỗi được ghi, không có mutation HL, không insert rebalance_attempts với invalid reason.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_043
**Scenario Title:** BigDecimal — phép tính delta không dùng float/Number() (NFR-EXBOT-008)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync NFR-EXBOT-008
**Test Type:** Functional
**Description:** Kiểm tra computation delta = targetShortEth − actualShortEth với giá trị cần nhiều chữ số thập phân (ví dụ 0.1234567890123456789 ETH). Kết quả tính bằng BigDecimal phải chính xác — không có sai số floating point. Verify bằng cách so sánh kết quả với expected exact value, không dùng approxEqual.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_044
**Scenario Title:** E2E flow — Light-Check phát hiện drift → enqueue hedge-sync → execute → reconcile → Aurora PostgreSQL update
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync flows.md F-01, F-02
**Test Type:** End-to-End
**Description:** Cron trigger EventBridge → scan worker → light-check worker đọc bot_runtime_state, tính lpEthAmount, evaluate RebalanceReason list, phát hiện drift đủ ngưỡng → enqueue hedge-sync message. Hedge-sync worker execute full flow (stateVersion check, lock, getPosition, adjustShortDelta, INV-STOP, enqueue reconcile, release lock). Reconcile worker verify fill, update Aurora PostgreSQL. Toàn bộ E2E flow kết thúc với rebalance_attempts.status='success' và hedge_legs cập nhật.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_045
**Scenario Title:** E2E flow — Light-Check với circuit open: scan enqueue light-check, light-check suppress hedge-sync, stop monitoring vẫn run
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, flows.md F-01
**Test Type:** End-to-End
**Description:** Circuit='open'. Cron → scan → light-check chạy bình thường. Light-check tính RebalanceReason và phát hiện drift, nhưng phải suppress hedge-sync enqueue vì circuit open. Price-near-stop-audit vẫn có thể enqueue nếu có stop trigger. Verify hedge-sync queue không nhận message mới, stop monitoring tiếp tục.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_046
**Scenario Title:** Acceptance — delta-only invariant không bao giờ bị vi phạm (BR-EXBOT-004)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync BR-EXBOT-004
**Test Type:** Acceptance
**Description:** Trong mọi scenario hedge-sync bình thường, hệ thống chỉ gửi adjustShortDelta (delta phần chênh lệch), không gửi full close+reopen. Acceptance test: submit 5 hedge-sync với delta values khác nhau (dương, âm, nhỏ, lớn, gần 0) và verify HL order log chỉ chứa adjustShortDelta orders, không có closeShort + openShort sequence nào.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_047
**Scenario Title:** Acceptance — User Lock release luôn xảy ra trong finally block, không bị giữ khi crash
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, FR-EXBOT-092
**Test Type:** Acceptance
**Description:** Trong mọi exit path của hedge-sync worker (success, fail, exception), User Lock (Redlock) phải được release trong finally block. Verify: inject crash sau adjustShortDelta, confirm lock được release sau khi worker restart. TTL failsafe (ElastiCache auto-expire 90s) là last resort, không phải primary release mechanism.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_048
**Scenario Title:** Acceptance — circuit breaker failure_count chỉ tăng khi HL reject status='failed', không tăng khi partial fill
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040
**Test Type:** Acceptance
**Description:** Kiểm tra circuit breaker counting logic: (1) HL order fail → failure_count tăng 1. (2) HL order partial fill → failure_count KHÔNG tăng. (3) Reconcile mismatch → failure_count KHÔNG tăng (chỉ tăng khi status='failed' HL rejection). Verify Aurora PostgreSQL circuit_breakers.failure_count sau từng scenario.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_049
**Scenario Title:** Acceptance — stop monitoring vẫn chạy khi circuit='open' hoặc 'half_open'
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, states.md Circuit Breaker States
**Test Type:** Acceptance
**Description:** Khi circuit ở trạng thái 'open' hoặc 'half_open', hedge-sync bị blocked nhưng Stop Monitoring PHẢI tiếp tục hoạt động (theo State Registry). Verify: circuit='open', light-check không enqueue hedge-sync, nhưng price-near-stop-audit vẫn được enqueue khi price gần stop trigger.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_050
**Scenario Title:** Integration — SQS FIFO message ordering: hedge-sync messages cùng botId được xử lý theo thứ tự
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync SRS §FM-XB-02
**Test Type:** Integration
**Description:** SQS FIFO queue đảm bảo ordering cho cùng MessageGroupId (botId). Gửi 2 message hedge-sync liên tiếp cho cùng botId với stateVersion lần lượt là 5 và 6. Message v5 phải được process trước v6. Sau khi v5 xử lý xong và state_version tăng lên 6, message v6 khớp stateVersion và tiếp tục. Không có race condition.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_051
**Scenario Title:** Integration — partial_repair worker nhận message từ partial_repair queue và điều chỉnh phần còn thiếu
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-036
**Test Type:** Integration
**Description:** Reconcile phát hiện partial fill và enqueue partial_repair. partial_repair worker nhận message và tính phần delta còn thiếu (expectedAbsSize − actualAbsSize). Worker gửi adjustShortDelta bổ sung. Reconcile xác nhận size sau repair. Verify rebalance_attempts cuối cùng có status='success' sau repair.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_052
**Scenario Title:** Integration — key_status='active' check trước khi Signing Lambda ký lệnh HL
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync states.md Agent Key Status; SRS F-02
**Test Type:** Integration
**Description:** Signing Lambda phải verify hl_agent_keys.key_status='active' trước khi ký bất kỳ HL order nào. Nếu key_status='revoked' hoặc 'superseded', lệnh không được ký. Worker nhận signing error và phải escalate (không silent-fail). Verify: inject key_status='revoked', confirm adjustShortDelta không gửi đến HL.
**Test Focus:** Integration

---

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_053
**Scenario Title:** marginSummary fetch xảy ra sau khi acquire Redlock — margin_status được cập nhật trước khi thực hiện mutation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 4; FR-EXBOT-060; FR-EXBOT-092; Q3 answer (Tech Lead 2026-07-14)
**Test Type:** Functional
**Description:** Sau khi Worker acquire User Lock (Redlock) thành công, Worker phải fetch HL marginSummary (cùng với clearinghouseState tại step 4), tính marginUsage bằng BigDecimal, và cập nhật hedge_legs.margin_status trong Aurora PostgreSQL TRƯỚC khi thực hiện adjustShortDelta. Đây là thứ tự bắt buộc: Lock → fetch marginSummary + clearinghouseState → update margin_status → kiểm tra risk threshold → mutation → unlock. Không được dùng dữ liệu margin_status cũ từ trước khi lock để quyết định mutation.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_054
**Scenario Title:** HL marginSummary call chậm trong khi đang giữ lock — extend() được gọi trước khi TTL=90s hết
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 4; FR-EXBOT-092; Q3 answer (Tech Lead 2026-07-14)
**Test Type:** Functional
**Description:** Worker acquire Redlock (TTL=90s) và bắt đầu fetch HL marginSummary tại step 4. HL API phản hồi chậm (giả lập latency > 80s). Worker phải gọi User Lock.extend(holderToken, ttlMs) trước khi TTL=90s hết để gia hạn lease — đảm bảo lock không bị tự giải phóng bởi ElastiCache TTL expiry trong khi Worker vẫn đang fetch dữ liệu margin. Verify: sau khi marginSummary trả về, Worker tiếp tục xử lý bình thường và release lock trong finally block; Aurora PostgreSQL không thấy lock contention do TTL expiry.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_055
**Scenario Title:** Step 2 short-circuit: stateVersion mismatch discard trước khi circuit recheck được thực hiện
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync §3 step 2; FR-EXBOT-027; FR-EXBOT-040; flows.md F-02; N4-03
**Test Type:** Functional
**Description:** Gửi message hedge-sync với stateVersion lỗi thời (message.stateVersion < Aurora PostgreSQL state_version). Worker thực hiện step 2: kiểm tra stateVersion TRƯỚC, phát hiện mismatch, và discard message ngay lập tức với status='skipped' và reason = original RebalanceReason[]. Worker KHÔNG thực hiện circuit recheck (không đọc circuit_breakers.state). Đây là short-circuit theo thứ tự từ flows.md F-02 — stateVersion check first, circuit recheck second. Verify: không có Aurora PostgreSQL read nào cho circuit_breakers sau khi stateVersion mismatch detected.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_056
**Scenario Title:** F-01 "suppress this tick only" — light-check suppress hedge-sync 1 tick, tick tiếp theo resume bình thường
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync flows.md F-01 step 11 (updated 2026-07-14); FR-EXBOT-033
**Test Type:** Functional
**Description:** Light-check worker phát hiện điều kiện suppress (ví dụ: bot đang trong thao tác ưu tiên cao hơn trong tick này — F-01 step 11 "suppress routine hedge-sync (this tick only)"). Worker KHÔNG enqueue hedge-sync message trong tick hiện tại. Tuy nhiên, suppress chỉ có hiệu lực cho tick này — không phải circuit open, không phải safe_mode. Tick tiếp theo (≤5 phút sau) light-check đánh giá lại bình thường: nếu drift vẫn vượt ngưỡng, hedge-sync được enqueue. Verify: chỉ đúng 1 tick bị suppress, tick kế tiếp có hedge-sync message trong queue.
**Test Focus:** Alternative flow

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| delta=0 exact behavior (send no-op vs skip) | UC A6 documents "skip HL, proceed to stop replacement" nhưng note "Behavior pending OQ-EXBOT-013". BLOCKED: Q1 — zen confirmation outstanding. TS_040 covers suy luận nhưng expected result chưa hoàn chỉnh. | Chờ zen trả lời OQ-EXBOT-013 trước khi finalize test case chi tiết cho A6. |
| Minimum order size handling khi delta < HL tick size (TS_041) | UC không định nghĩa cách xử lý delta nhỏ hơn minimum tick size HL. BLOCKED: chưa có spec. | Resolve qua qc-qna trước khi thiết kế test case atomic. |
| Q1 (OQ-EXBOT-013): delta=0 exact behavior | BLOCKED: OQ-EXBOT-013 chưa được zen trả lời. TS_040 có thể thiếu expected result cho stop replacement path. | Chờ zen trả lời OQ-EXBOT-013. |
| Q2 (OQ-EXBOT-002): INV-STOP cancel/place ordering | BLOCKED: OQ-EXBOT-002 — behavior place-before-cancel vs cancel-before-place chưa xác nhận. TS_024/025/026 liên quan đến INV-STOP sequence có thể cần update. | Chờ zen trả lời OQ-EXBOT-002. |
| Q6 (OQ-EXBOT-011): lpValueUsd formula cho partial_repair drift_threshold | BLOCKED: OQ-EXBOT-011 — công thức tính lpValueUsd chưa được confirm. TS_028 (partial_repair threshold) thiếu expected numeric value. | Chờ zen trả lời OQ-EXBOT-011. |
| Q7: entry_price/liq_price update khi delta=0 | BLOCKED bởi Q1. Nếu Q1 confirm delta=0 → stop replacement thì Q7 cần được resolve để tester biết entry_price có update không. | Chờ Q1 resolved. |
| Performance / Load testing | Out-of-scope cho logic scenario skill. Throughput (hedge-sync latency, SQS batch size) cần load testing. | Delegate sang performance testing team. |
| Security testing ngoài functional auth (key_status check) | Out-of-scope. Key management security, KMS HSM audit, AWS IAM policy audit không thuộc functional scenario. | Delegate sang security audit. |

