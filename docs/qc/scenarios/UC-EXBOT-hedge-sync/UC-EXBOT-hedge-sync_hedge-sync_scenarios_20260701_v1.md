# Test Scenarios — UC-EXBOT-hedge-sync Execute Delta-Only Hedge Adjustment

> Source: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260630_v1.md
> Generated: 2026-07-01
> Domain/Architecture: Cloudflare Workers + Hyperliquid API + D1 (control_db + state_db_shard) + Durable Objects (UserLockDO, HLRateLimitDO) + queue topology (hedge-sync → reconcile → partial_repair)

---

## Bảng mã viết tắt

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| HL | Hyperliquid — sàn giao dịch perpetual bên ngoài. Trong dự án, ExBot short ETH trên HL để hedge LP position trên Uniswap V3. Mọi lệnh delta, stop market đều gửi qua HL API. | (tên sản phẩm) |
| DO | Durable Object — đơn vị compute có trạng thái bền vững trên Cloudflare Workers. ExBot dùng 3 DO: UserLockDO, HLRateLimitDO, MarketDataDO. | (Cloudflare platform term) |
| D1 | Cloudflare D1 — cơ sở dữ liệu SQLite phân tán. ExBot dùng control_db và state_db_shard để lưu trạng thái bot, hedge_legs, queue_idempotency, v.v. | (Cloudflare platform term) |
| INV-STOP | Invariant: khi HL short khác 0, phải luôn tồn tại verified reduce-only stop. Giao thức INV-STOP (§19.5 SPEC) là protected cancel→place nhằm không bao giờ để khoảng thời gian không có stop. | FR-EXBOT-032/035, SPEC §19.5 |
| cloid | Client Order ID — mã lệnh tất định theo công thức keccak256. Dùng để HL dedup và ExBot idempotency khi retry. | FR-EXBOT-022/024 |
| BigDecimal | Kiểu số thập phân chính xác tùy ý (không float). Mọi phép tính hedge, stop, margin trong ExBot bắt buộc dùng BigDecimal. | NFR-EXBOT-008 |
| delta | Chênh lệch giữa targetShortEth và actualShortEth. Chỉ phần chênh lệch này được gửi lên HL (delta-only invariant). | FR-EXBOT-020/022 |
| stateVersion | Số phiên bản trạng thái bot trong D1 (bot_runtime_state.state_version). Dùng để phát hiện message queue lỗi thời, tránh race condition. | FR-EXBOT-027 |
| UserLockDO | Durable Object cung cấp lease mutex per-user, TTL 90s. Phải acquire trước bất kỳ HL mutation nào. | FR-EXBOT-026/091 |
| circuit breaker | Cơ chế bảo vệ tự động ngừng enqueue hedge-sync khi có 3 lần thất bại liên tiếp trong 24h. 3 trạng thái: closed, open, half_open. | FR-EXBOT-040 |
| partial_repair | Hàng đợi và worker xử lý khi reconcile phát hiện fill một phần (|actual − target| > drift_threshold). | FR-EXBOT-036 |
| marginUsage | Tỷ lệ ký quỹ: marginRequiredUsd / marginBalanceUsd. Ngưỡng warning: 0.55–0.75; critical: ≥ 0.75. | FR-EXBOT-060 |
| SAFE_MODE | Trạng thái bot không cho phép bất kỳ mutation nào. Bot chỉ được monitor và retry kết nối. | FR-EXBOT-050 |

---

## UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_001
**Scenario Title:** Happy path — delta dương, bot active, circuit closed, lock free, reconcile thành công
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027
**Test Type:** Functional
**Description:** Gửi message hedge-sync hợp lệ với stateVersion khớp D1, bot đang ở trạng thái active, circuit breaker closed, UserLockDO chưa bị giữ, và targetShortEth > actualShortEth (delta dương). Hệ thống phải hoàn thành đầy đủ: insert idempotency, check stateVersion, acquire lock, fetch HL position, tính delta bằng BigDecimal, gửi adjustShortDelta với cloid tất định, enqueue reconcile, thực hiện INV-STOP stop replacement, release lock. Reconcile worker xác nhận size khớp expected, cập nhật hedge_legs và bot_runtime_state, insert rebalance_attempts với status='success'.
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
**Description:** Deliver cùng một message (cùng message_id) vào hàng đợi hedge-sync lần thứ hai trong khi message đó đã được xử lý trước đó (queue_idempotency.state='succeeded'). Worker phải phát hiện UNIQUE conflict khi insert message_id và return immediately mà không gửi bất kỳ HL order nào, không thay đổi D1 state.
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
**Description:** Gửi message với message.stateVersion=5 nhưng D1 bot_runtime_state.state_version=6 (message đã lỗi thời). Worker phải đọc stateVersion từ D1 trước khi acquire lock, phát hiện mismatch, discard message, và insert rebalance_attempts với status='skipped'. Không được gửi HL order. Không acquire UserLockDO.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_006
**Scenario Title:** stateVersion mismatch — stateVersion message cao hơn D1 (bất thường)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-027
**Test Type:** Functional
**Description:** Gửi message với message.stateVersion=7 nhưng D1 state_version=6 (message từ tương lai — không hợp lệ). Worker phải xử lý trường hợp này: hoặc discard (mismatch), hoặc xử lý nếu spec cho phép. Kết quả phải nhất quán và không gây double mutation.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_007
**Scenario Title:** UserLockDO lock đang bị giữ — re-queue với delay
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, SRS §FR-092
**Test Type:** Functional
**Description:** Worker gọi UserLockDO.acquire() khi một worker khác đang giữ lease cho cùng user. DO trả về acquired=false và currentHolderExpiresAt. Worker phải không gửi HL order và re-queue message với delay phù hợp. Không được bỏ message hay xử lý khi chưa có lock.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_008
**Scenario Title:** UserLockDO TTL hết hạn trong khi worker đang xử lý — heartbeat để gia hạn
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, SRS §FR-092
**Test Type:** Functional
**Description:** Worker acquire lease thành công nhưng xử lý mất hơn 30 giây. Worker phải gọi UserLockDO.heartbeat() trước khi TTL 90s hết để gia hạn lease. Nếu heartbeat thành công, worker tiếp tục xử lý và release lock trong finally block sau khi hoàn thành.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_009
**Scenario Title:** UserLockDO TTL tự hết — worker tiếp theo phải reconcile trước khi mutation
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-026, SRS §FR-092
**Test Type:** Integration
**Description:** Worker A acquire lock nhưng bị crash hoặc không gọi heartbeat, TTL 90s hết và lock tự động giải phóng. Worker B acquire lock sau đó và phải fetch actual HL position để reconcile trước khi submit bất kỳ lệnh HL mới nào. Không được "blind submit" dựa vào state D1 cũ.
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
**Scenario Title:** HL order bị reject (insufficient margin) — incrementCircuitBreaker, enqueue notification
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-040, UC §4 A3; E-EXBOT-007: "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin."
**Test Type:** Functional
**Description:** Worker gửi adjustShortDelta nhưng HL trả về lỗi insufficient margin. Worker phải: ghi rebalance_attempts.status='failed', gọi incrementCircuitBreaker (failure_count tăng 1), enqueue notification với event=hedge_failure. Lỗi E-EXBOT-007 được ghi: "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin."
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
**Description:** hedge_legs.margin_status='warning' trong D1 khi worker đọc. Nếu delta dương (tăng size), worker phải chặn, không gửi adjustShortDelta increase. Nếu delta âm (giảm size), reduce-only vẫn được phép gửi bình thường.
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
**Scenario Title:** Biên marginUsage = 0.75 lần thứ 2 liên tiếp (ngưỡng critical → SAFE_MODE)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-060, FR-EXBOT-050
**Test Type:** Data/State
**Description:** marginUsage = 0.75 hai lần liên tiếp (critical). Lần đầu set margin_status='critical'; lần thứ hai phải trigger SAFE_MODE và alert admin. Mọi hedge mutation bị blocked sau khi vào SAFE_MODE.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_022
**Scenario Title:** BigDecimal — tính delta không dùng float/Number() intermediate
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync NFR-EXBOT-008, FR-EXBOT-021; normalizeTargetRatioBps("0.70") → 7000n
**Test Type:** Functional
**Description:** Kiểm tra rằng delta = targetShortEth.sub(actualShortEth) được tính hoàn toàn bằng BigDecimal. Không có Number() intermediate trong toàn bộ pipeline tính delta. normalizeTargetRatioBps("0.70") trả về 7000n (không phải 0.7 hay 7000.0). Number("0.73") * 10000 không xuất hiện trong codebase.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_023
**Scenario Title:** BigDecimal — tính stop_trigger_px không dùng float
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-030, NFR-EXBOT-008
**Test Type:** Functional
**Description:** Sau reconcile, Reconcile Worker tính stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70). Toàn bộ phép tính dùng BigDecimal. liq_distance_pct = (liq_price − entry_price) / entry_price ưu tiên HL liq_price; fallback sang 1/effective_leverage chỉ khi HL không trả về liq_price. Không có intermediate Number() conversion.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_024
**Scenario Title:** cloid tất định — cùng retry (same attemptId+stage+version) cho cùng cloid
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022/024
**Test Type:** Functional
**Description:** Worker gửi lệnh adjustShortDelta với cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}")). Khi retry cùng attempt (cùng attemptId, stage, version không đổi), cloid phải giống hệt lần trước. HL dedup hoặc worker phát hiện duplicate cloid và reconcile trước khi retry, không blind submit lần thứ hai.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_025
**Scenario Title:** cloid thay đổi khi payload đổi — version tăng
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-022/024
**Test Type:** Functional
**Description:** Sau khi delta thay đổi (payload mới), worker phải tăng version trong cloid formula. Cloid mới khác cloid cũ. Điều này đảm bảo HL không dedup nhầm lệnh mới với lệnh cũ đã hủy.
**Test Focus:** Idempotency/Concurrency

---


### Scenario ID: TS_UC-EXBOT-hedge-sync_026
**Scenario Title:** INV-STOP — stop_replacing_started_at được set trước và clear trong finally block
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-035, SRS §FR-035
**Test Type:** Functional
**Description:** Khi worker bắt đầu INV-STOP critical section (thay stop), hedge_legs.stop_replacing_started_at phải được set = now trước khi cancel/place stop. Sau khi hoàn thành (dù thành công hay thất bại), stop_replacing_started_at phải được clear = NULL trong finally block. Kiểm tra D1 sau khi hedge-sync hoàn thành: stop_replacing_started_at = NULL.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_027
**Scenario Title:** INV-STOP — stop_replacing_started_at bị stuck >60s → SAFE_MODE qua light-check (≤5 phút)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-033/035, SRS §FR-033
**Test Type:** Integration
**Description:** Worker bị crash hoặc treo trong critical section INV-STOP, không clear stop_replacing_started_at. Light-check lần tiếp theo (tối đa 5 phút sau) phải phát hiện stop_replacing_started_at IS NOT NULL AND age > 60s, enqueue partial_repair với reason='stop_replacing_overrun', và trigger SAFE_MODE entry. Primary detection path ≤5 phút.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_028
**Scenario Title:** INV-STOP — stop_replacing_started_at stuck được deep-audit phát hiện (backstop nếu light-check bỏ lỡ)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-033, SRS §FR-033
**Test Type:** Integration
**Description:** Trường hợp light-check bị skip (ví dụ worker crash trước khi chạy check), deep-audit chạy sau đó phát hiện stop_replacing_started_at stuck > 60s và trigger SAFE_MODE (secondary/backstop detection). Xác nhận deep-audit đủ khả năng detect và escalate dù light-check bỏ lỡ.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_029
**Scenario Title:** Reconcile — xác nhận size khớp expected sau adjustShortDelta
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-025, SRS §FR-025
**Test Type:** Integration
**Description:** Sau khi worker gửi adjustShortDelta thành công và enqueue reconcile message, Reconcile Worker fetch actual HL position, so sánh actualShortSize với expectedAbsSize. Khi size khớp (trong tolerance), worker cập nhật hedge_legs (stop_price, entry_price, effective_leverage) và bot_runtime_state.last_known_hl_short_size. rebalance_attempts.status='success' chỉ được ghi sau khi reconcile xác nhận.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_030
**Scenario Title:** Reconcile — partial fill, |actual − target| > drift_threshold → enqueue partial_repair
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-036, FR-EXBOT-025, UC §4 A4
**Test Type:** Integration
**Description:** Reconcile Worker phát hiện |actualShortSize − expectedAbsSize| > drift_threshold (lệnh fill một phần). Worker phải enqueue partial_repair message với reason='partial_fill' và ghi rebalance_attempts.status='partial'. Không được đánh dấu thành công khi chưa reconcile đúng.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_031
**Scenario Title:** partial_repair — 3 lần thất bại liên tiếp → trigger bot_safe_close
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-036, FR-EXBOT-072
**Test Type:** Integration
**Description:** Sau 3 lần partial_repair thất bại liên tiếp cho cùng trigger event, hệ thống phải tạo close_operations row với trigger_reason='partial_repair_exhausted' và kích hoạt bot_safe_close. Mỗi repair attempt dùng cloid riêng (version tăng). Sau 3 fail, không được retry thêm.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_032
**Scenario Title:** D1 consistency sau reconcile — hedge_legs và bot_runtime_state phải khớp HL actual
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-025, §F.4
**Test Type:** Data/State
**Description:** Sau khi reconcile thành công, kiểm tra tính nhất quán dữ liệu: hedge_legs.entry_price và hedge_legs.stop_price phải reflect giá trị từ clearinghouseState mới nhất; bot_runtime_state.last_known_hl_short_size phải bằng reconciled_short_size. Nếu D1 stale → drift tiếp theo được tính sai.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_033
**Scenario Title:** state_version tăng sau reconcile — message cũ với stateVersion thấp hơn bị discard
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-027, §F.4
**Test Type:** Data/State
**Description:** Sau khi hedge-sync thành công, state_version trong D1 tăng 1. Message hedge-sync cũ (với stateVersion thấp hơn) vẫn còn trong hàng đợi phải bị discard khi worker đọc và compare. Tránh race condition double-submit trong khi worker A đang xử lý.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_034
**Scenario Title:** stop monitoring luôn tiếp tục kể cả khi circuit breaker open
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-014, SRS §FR-014
**Test Type:** Functional
**Description:** Khi circuit_breakers.state='open', light-check phải suppress enqueue hedge-sync nhưng vẫn tiếp tục đánh giá stop trigger và enqueue price-near-stop-audit khi markPrice ≥ stop_price. Không được suppress stop monitoring dưới bất kỳ điều kiện nào.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_035
**Scenario Title:** KMS signing failure — lệnh không gửi, bot vào SAFE_MODE
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-080, IC-EXBOT-005
**Test Type:** Functional
**Description:** Signing Lambda bị lỗi trong quá trình ký lệnh HL (KMS API error). Lệnh adjustShortDelta không được gửi. Bot phải vào SAFE_MODE và admin được alert. Không có lệnh HL nào được submit dù một phần. Recovery theo SAFE_MODE standard path.
**Test Focus:** Error/Exception

---


### Scenario ID: TS_UC-EXBOT-hedge-sync_036
**Scenario Title:** HLRateLimitDO — weight budget vượt 800/min, worker không được gọi HL
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync IC-EXBOT-001, FR-EXBOT-091, NFR-EXBOT-004
**Test Type:** Integration
**Description:** Worker khai báo weight trước khi gọi HL getPosition (weight=2). Nếu HLRateLimitDO trả về {allowed: false, retryAfterMs}, worker phải không gọi HL và re-queue message với delay bằng retryAfterMs. Tổng weight HL trong 60s không được vượt 800.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_037
**Scenario Title:** UserLockDO — holderToken mismatch khi release (no-op, không lỗi)
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-091/092, SRS §FR-092
**Test Type:** Integration
**Description:** Worker gọi UserLockDO.release() với holderToken không khớp với holder hiện tại (ví dụ do TTL đã hết và worker khác đã acquire). DO phải xử lý như no-op — không raise error, không giải phóng lease của holder thật. Caller không được bị crash vì mismatch này.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_038
**Scenario Title:** Audit log — rebalance_attempts row tồn tại cho mọi attempt kể cả skipped/failed
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-025, NFR-EXBOT-007, ERD
**Test Type:** Functional
**Description:** Sau mọi kết quả hedge-sync (success, failed, skipped, partial), phải tồn tại đúng 1 row trong rebalance_attempts với đầy đủ trường: botId, attemptId, old_short_size, target_short_size, reconciled_short_size (nếu có), adjust_cloid, stop_cloid, status, reason. Không được bỏ qua ghi log dù bất kỳ path nào.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_039
**Scenario Title:** End-to-end — từ light-check enqueue đến D1 update sau reconcile hoàn chỉnh
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync FR-EXBOT-011/022/025/026/027/035/040, US-EXBOT-006 AC-006-1
**Test Type:** End-to-End
**Description:** Luồng đầy đủ: (1) light-check phát hiện drift_threshold và enqueue hedge-sync message; (2) hedge-sync worker xử lý: insert idempotency, check stateVersion, acquire lock, fetch HL, tính delta, gửi lệnh, INV-STOP stop replacement, enqueue reconcile, release lock; (3) reconcile worker xác nhận size, cập nhật hedge_legs + bot_runtime_state, insert rebalance_attempts success; (4) queue_idempotency.state='succeeded'. Toàn bộ pipeline phải hoàn thành và D1 phản ánh đúng state HL.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_040
**Scenario Title:** Acceptance — adjustShortDelta gửi đúng delta, reconcile xác nhận, D1 cập nhật
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-006 AC-006-1, FR-EXBOT-022/025
**Test Type:** Acceptance
**Description:** Điều kiện: bot active, circuit closed, lock free, stateVersion khớp, delta > 0. Khi worker xử lý end-to-end, kết quả mong đợi: adjustShortDelta gửi thành công với đúng delta value; reconcile xác nhận size; hedge_legs.stop_price cập nhật; bot_runtime_state.last_known_hl_short_size cập nhật; rebalance_attempts.status='success'. (Ref: US-EXBOT-006 AC-006-1)
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_041
**Scenario Title:** Acceptance — stateVersion mismatch discard
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-006 AC-006-2, FR-EXBOT-027
**Test Type:** Acceptance
**Description:** Điều kiện: message.stateVersion=5 nhưng D1 state_version=6. Khi worker kiểm tra stateVersion, kết quả: discard; rebalance_attempts.status='skipped'; không có HL order nào được gửi. (Ref: US-EXBOT-006 AC-006-2)
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_042
**Scenario Title:** Acceptance — lock held re-queue
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-006 AC-006-3, FR-EXBOT-026
**Test Type:** Acceptance
**Description:** Điều kiện: worker khác đang giữ UserLockDO cho cùng user. Khi acquire trả về acquired=false, kết quả: message được re-queue với delay; không có HL order nào được gửi. (Ref: US-EXBOT-006 AC-006-3)
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_043
**Scenario Title:** Acceptance — HL order rejection → circuit increment
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-006 AC-006-4, FR-EXBOT-040
**Test Type:** Acceptance
**Description:** Điều kiện: HL trả về error (insufficient margin). Khi worker nhận lỗi, kết quả: rebalance_attempts.status='failed'; incrementCircuitBreaker; sau 3 consecutive failures trong 24h → circuit open; notification enqueued. (Ref: US-EXBOT-006 AC-006-4)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_044
**Scenario Title:** Acceptance — circuit open sau 3 failures, stop monitoring vẫn chạy
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-008 AC-008-1, FR-EXBOT-040/014
**Test Type:** Acceptance
**Description:** Điều kiện: 2 failures trước trong 24h, attempt thứ 3 fail. Kết quả: circuit_breakers.state='open', reset_at=now+1h; light-check tiếp theo không enqueue hedge-sync; stop monitoring vẫn chạy (price-near-stop-audit không bị suppress). (Ref: US-EXBOT-008 AC-008-1)
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_045
**Scenario Title:** Acceptance — circuit chuyển half_open, 1 probe duy nhất được enqueue
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-008 AC-008-2, FR-EXBOT-040
**Test Type:** Acceptance
**Description:** Điều kiện: circuit='open', reset_at đã đến. Khi light-check evaluate, kết quả: đúng 1 hedge-sync message được enqueue (probe); half_open_probe_used=1. (Ref: US-EXBOT-008 AC-008-2)
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_046
**Scenario Title:** Acceptance — probe half_open thành công → circuit closed
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-008 AC-008-3, FR-EXBOT-040
**Test Type:** Acceptance
**Description:** Điều kiện: half_open probe chạy thành công, reconcile xác nhận size. Kết quả: circuit_breakers.state='closed', failure_count=0. (Ref: US-EXBOT-008 AC-008-3)
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-hedge-sync_047
**Scenario Title:** Acceptance — probe half_open thất bại → circuit mở lại
**UC Reference:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment
**Req-ID:** UC-EXBOT-hedge-sync US-EXBOT-008 AC-008-4, FR-EXBOT-040
**Test Type:** Acceptance
**Description:** Điều kiện: half_open probe fail. Kết quả: circuit_breakers.state='open', reset_at=now+1h; admin notification. (Ref: US-EXBOT-008 AC-008-4)
**Test Focus:** State transition

---

## ⚠️ Out-of-Scope Flags

| Vùng scenario | Lý do | Hành động đề xuất |
|---|---|---|
| Luồng A6 (delta=0): hành vi khi tính delta bằng 0 — có tiếp tục INV-STOP stop replacement không? | BLOCKED: OQ-EXBOT-013 (Q1 audited report) — chưa chốt expected result. Tester không thể viết AC-11 cho đến khi Tech Lead trả lời. | Giải quyết qua qc-qna + re-audit. Sau khi có câu trả lời, bổ sung scenario delta=0 vào v2. |
| Trình tự INV-STOP cancel/place: cancel-before-place hay place-before-cancel trên HL? | BLOCKED: OQ-EXBOT-002 (Q2 audited report) — chưa confirm. Ảnh hưởng test case chi tiết cho F1-09/F1-10. | Giải quyết qua SOTATEK verify với HL (NV-3). Sau khi rõ, bổ sung scenario cho đúng path vào v2. |
| Performance / load: throughput 10,000 bots/5min, HL API weight budget dưới tải cao | NFR — ngoài phạm vi functional QC | Defer to performance/load test specialist |
| Security: KMS key không lộ trong log/DB, IAM kms:Sign | NFR — ngoài phạm vi functional QC | Security review riêng |
| Partial fill threshold chính xác (drift_threshold cho partial_repair vs light-check) | BLOCKED: Q6 — OQ-EXBOT-004 (dust threshold) chưa confirm | Sau khi BA/Tech Lead chốt threshold, cập nhật scenario 030 với giá trị cụ thể |
| marginSummary fetch ordering (trước hay sau acquire lock) | BLOCKED: Q3 — OQ-EXBOT-014 | Ảnh hưởng test timeout/heartbeat; defer đến khi Tech Lead trả lời |

