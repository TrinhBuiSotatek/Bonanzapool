# UC Readiness Review
**Functional / Black-box Test Readiness Review**

---

| | |
|---|---|
| **Tiêu đề tài liệu** | UC Readiness Review — UC-EXBOT-light-check |
| **Ngày tạo** | 2026-06-16 |
| **Tác giả / Agent** | qc-uc-read (run-20260616-180000-udemysen) |
| **Phiên bản** | v1 |
| **Ngôn ngữ** | Tiếng Việt (ngôn ngữ input: Tiếng Anh) |

---

## Tóm tắt tính năng

**UC-EXBOT-light-check** mô tả luồng kiểm tra định kỳ (mỗi 5 phút) cho tất cả ExBot đang active trên PTL-04 (CF Workers, API-only/backend-job). Đây là một pipeline 3 worker: **Cron Worker** (1 phút) fan-out shard windows vào `bot-scan` queue → **Scan Worker** query D1 lấy danh sách bot cần check và fan-out vào `light-check` queue → **Light-Check Worker** đọc trạng thái từ D1 + MarketDataDO (zero HL API call), tính `RebalanceReason[]`, và fan-out kết quả vào `hedge-sync` hoặc `price-near-stop-audit` queue.

**Ràng buộc kiến trúc cốt lõi:** BR-EXBOT-003 — HL weight = 0 trong toàn bộ light-check. Nguồn dữ liệu duy nhất: D1 hot state + MarketDataDO (shared cache sqrtPriceX96/currentTick). Mọi LP amount tính bằng TickMath + LiquidityAmounts cục bộ. Invariant 3-way price split (uniPoolPrice/hlMarkPrice/hlOraclePrice) phải không bị trộn lẫn.

**Circuit breaker integration:** open → suppress hedge-sync; half_open → 1 probe duy nhất; stop monitoring luôn chạy dù circuit ở bất kỳ state nào (FR-EXBOT-014). **Write-once guard:** `stop_trigger_crossed_at` chỉ set nếu đang NULL (BR-EXBOT-005). **Idempotency:** mọi consumer insert queue_idempotency(state='started') trước khi xử lý; UNIQUE conflict = skip.

**Blockers đang mở:** NV-12 (wethIndex/MarketDataDO cache TTL), NV-1/NV-3 (stop replacement protocol).

---

## Kết luận sẵn sàng

| Điểm tổng | Kết luận |
|---|---|
| **76.2 / 100** | ⚠️ **CONDITIONALLY READY (Sẵn sàng có điều kiện)** |

---

## 0. Metadata tài liệu

| UC-ID | Tên tính năng | Phiên bản | Trạng thái |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check (zero HL calls, evaluate rebalance reasons, fan-out) | v1 | Draft |

| Tác giả / BA | Phê duyệt bởi | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-12 |

**Tài liệu đầu vào đã review:**
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-light-check.md` (v1, 2026-06-12)
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-005.md` (US-EXBOT-005, P0, draft)
- `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-006.md` (US-EXBOT-006, P0, draft)
- Tham chiếu chéo: `frd.md` (FR-EXBOT-011/012/021/023/031/032/040/050/060/080/090/091/092/110), `srs/spec.md` (FR-EXBOT-013/014/015/016/020-025, BR-EXBOT-003/005, NFR-EXBOT-001/004/005/007)

---

## 1. Mục tiêu & Phạm vi ⚠️ Partial

### 1.1 Mục tiêu
Cho phép hệ thống ExBot kiểm tra nhu cầu tái cân bằng của tất cả bot active mỗi 5 phút mà không tiêu tốn HL API rate limit. Mục tiêu thiết kế: 10.000 bot / 5 phút = 33.3 bot/giây, trong giới hạn HL 1.200 weight/phút (BNZA operating budget: 800 weight/min). Light-check chỉ đọc D1 + MarketDataDO — zero HL call là invariant bất biến.

### 1.2 Trong phạm vi
- Cron Worker (1 phút) fan-out shard window messages → `bot-scan` queue
- Scan Worker: query D1 bots active, fan-out per-bot messages → `light-check` queue, batch-update `next_light_check_at`
- Light-Check Worker: idempotency check, đọc D1 hot state + MarketDataDO, tính 7 RebalanceReasons
- Fan-out: `hedge-sync` nếu reasons[] found + circuit cho phép; `price-near-stop-audit` nếu stop triggered hoặc range_boundary_near
- stop_replacing_overrun detection → partial_repair + SAFE_MODE entry
- Circuit breaker state handling (closed/open/half_open)

### 1.3 Ngoài phạm vi
⚠️ **Thiếu** — uc-light-check.md không có mục "out of scope" tường minh.

*Suy luận ngoài phạm vi (chưa tài liệu hóa):*
- Thực thi hedge adjustment (thuộc UC-EXBOT-hedge-sync)
- Stop audit processing (thuộc price-near-stop-audit worker)
- LP range rebalance execution (FR-EXBOT-015 P1 — behavior khi range_out → lp_rebalancing không trong UC này)
- Deep-audit cron (FR-EXBOT-016 — 6h interval, chạy độc lập)

---

## 2. Tác nhân & Các bên liên quan ⚠️ Partial

| Tác nhân | Loại | Vai trò & Quyền hạn |
|---|---|---|
| Cron Worker | Primary (automated) | Kích hoạt theo lịch CF mỗi 1 phút; tạo shard window messages; PHẢI dùng chunkSendBatch (CF max 100/call). |
| Scan Worker | Primary (automated) | Nhận từ `bot-scan` queue; query D1 bots với filter; fan-out per-bot messages vào `light-check` queue qua chunkSendBatch; batch-update `next_light_check_at` (1 stmt/shard). |
| Light-Check Worker | Primary (automated) | Nhận từ `light-check` queue; thực thi toàn bộ evaluation logic; fan-out kết quả. Đây là actor chính của UC. |
| D1 (`state_db_shard`) | System | Nguồn trạng thái bot; đọc bot_runtime_state, hedge_legs, queue_idempotency. |
| MarketDataDO | System | Shared cache sqrtPriceX96/currentTick; tất cả workers đọc từ DO này, không RPC individual. |

⚠️ **Gap:** Không có mô tả auth/quyền hạn giữa các workers; không rõ cơ chế kích hoạt Cron Worker (CF scheduled trigger); nguồn data refresh của MarketDataDO (ai cập nhật cache) không định nghĩa trong UC.

---

## 3. Tiền điều kiện & Hậu điều kiện ⚠️ Partial

### 3.1 Tiền điều kiện
1. Bot có `status='active'` và `next_light_check_at <= now`
2. `lifecycle_state NOT IN ('lp_rebalancing','lp_closing')`
3. `status != 'paused'`

⚠️ **Gap:** Không có tiền điều kiện cho MarketDataDO phải có dữ liệu hợp lệ (stale/unavailable không được xử lý); không có điều kiện rollback nếu queue enqueue thất bại giữa chừng.

### 3.2 Hậu điều kiện

| Sau khi hoàn thành... | Trạng thái hệ thống |
|---|---|
| Không cần hành động | `next_light_check_at` cập nhật; `queue_idempotency.state='succeeded'`; không có message mới |
| Phát hiện drift/rebalance reason | hedge-sync message enqueued với `{botId, reasons, stateVersion}` |
| Phát hiện stop trigger hoặc range_boundary_near | `stop_trigger_crossed_at` được set (nếu NULL); price-near-stop-audit message enqueued |
| Phát hiện stop_replacing_overrun | partial_repair message enqueued; bot chuyển SAFE_MODE |

⚠️ **Gap:** "Không cần hành động" quá mơ hồ — không định nghĩa rõ "không có reasons nào" nghĩa là trạng thái cụ thể thế nào.

---

## 4. Danh mục đối tượng D1/API & Mapping ⚠️ Partial

> **Lưu ý nền tảng:** UC-EXBOT-light-check là backend-only (PTL-04, CF Workers Queue). Không có UI. "Đối tượng" = trường D1, MarketDataDO inputs, giá trị tính toán, và queue messages.

### Input: Trạng thái D1 được đọc

| # | Mục | Trường | Loại | Enum / Điều kiện | Nguồn |
|---|---|---|---|---|---|
| 1 | `bots` | `status` | Enum | active/paused/... — filter: `='active'` | uc-light-check.md §2 |
| 2 | `bots` | `next_light_check_at` | Timestamp | Filter: `<= now` | uc-light-check.md §3 Step 2 |
| 3 | `bots` | `lifecycle_state` | Enum (18 states) | Skip nếu `IN ('lp_rebalancing','lp_closing')` | uc-light-check.md §2 |
| 4 | `bot_runtime_state` | `last_known_hl_short_size` | BigDecimal | Dùng làm `actualShortEth` | FR-EXBOT-011 |
| 5 | `hedge_legs` | `stop_price` | BigDecimal | So với `hlMarkPrice` | uc-light-check.md §3 Step 6 |
| 6 | `hedge_legs` | `margin_status` | Enum: ok/warning/critical | Đọc D1, KHÔNG fetch HL | FR-EXBOT-060 |
| 7 | `hedge_legs` | `circuit_state` | Enum: closed/open/half_open | Kiểm soát enqueue hedge-sync | FR-EXBOT-040 |
| 8 | `hedge_legs` | `stop_replacing_started_at` | Timestamp / NULL | NOT NULL AND age > 60s → overrun | FR-EXBOT-011 |
| 9 | `hedge_legs` | `stop_trigger_crossed_at` | Timestamp / NULL | Write-once nếu NULL (BR-EXBOT-005) | FR-EXBOT-031 |
| 10 | `queue_idempotency` | `message_id`, `state` | String, Enum | Insert state='started'; UNIQUE conflict = skip | NFR-EXBOT-007 |
| 11 | MarketDataDO | `sqrtPriceX96` | uint160 | Nguồn `uniPoolPrice` cho LP drift | FR-EXBOT-011; FR-EXBOT-092 |
| 12 | MarketDataDO | `currentTick` | int24 | Dùng tính lpEthAmount qua TickMath | FR-EXBOT-011; FR-EXBOT-092 |

### Giá trị tính toán nội bộ

| # | Tên | Công thức | Nguồn giá | Ghi chú |
|---|---|---|---|---|
| 13 | `lpEthAmount` | TickMath + LiquidityAmounts (`liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick`) | uniPoolPrice | PHẢI dùng AMM formula; cấm `depositedToken − withdrawnToken` (FR-EXBOT-021) |
| 14 | `targetShortEth` | `lpEthAmount × hedgeRatio` (Phase A: 0.70) | uniPoolPrice | BigDecimal bắt buộc |
| 15 | `actualShortEth` | `bot_runtime_state.last_known_hl_short_size` | D1 only | Không fetch HL real-time |
| 16 | `deltaErrorUsd` | `|targetShortEth − actualShortEth| × uniPoolPrice` | uniPoolPrice | Ngưỡng: `> max($25, lpValueUsd × 3%)` |
| 17 | `next_light_check_at` | `now + 5min + random(−45s, +45s)` | — | Batch-write 1 stmt/shard; không per-bot |

### Output: Queue messages

| # | Queue | Nội dung | Điều kiện |
|---|---|---|---|
| 18 | `bot-scan` | Shard window batch | Cron 1 min |
| 19 | `light-check` | Per-bot message | Scan Worker → chunkSendBatch |
| 20 | `hedge-sync` | `{botId, reasons, stateVersion}` ⚠️ *types chưa định nghĩa* | reasons[] found AND circuit != 'open' |
| 21 | `price-near-stop-audit` | `{botId}` ⚠️ *schema chưa định nghĩa* | markPrice >= stop_price HOẶC range_boundary_near |
| 22 | `partial_repair` | `{botId, reason='stop_replacing_overrun'}` ⚠️ *schema chưa định nghĩa* | stop_replacing_started_at stuck > 60s |

### RebalanceReason[] Enum (FR-EXBOT-023)

| # | Reason | Điều kiện | Nguồn dữ liệu |
|---|---|---|---|
| 23 | `drift_threshold` | `deltaErrorUsd > max($25, lpValueUsd × 3%)` | D1 + MarketDataDO |
| 24 | `drift_relative` | `\|target - actual\| / target > 0.15` | D1 + MarketDataDO |
| 25 | `range_out` | `rangeState != 'in'` | D1 |
| 26 | `range_boundary_near` | Price 90% tới range upper/lower ⚠️ *formula chưa định nghĩa trong UC* | MarketDataDO |
| 27 | `margin_warning` | `hedge_legs.margin_status == 'warning'` | D1 only |
| 28 | `funding_alert` | 7d funding < −15% APR | D1 |
| 29 | `time_fallback` | 4h kể từ lần điều chỉnh cuối | D1 |

---

## 5. Thuộc tính & Hành vi đối tượng ⚠️ Partial

| Đối tượng | Trạng thái hệ thống | Ma trận tương tác | Hành vi |
|---|---|---|---|
| Cron Worker | Luôn hoạt động theo lịch CF (1 phút) | Kích hoạt chunkSendBatch → `bot-scan` | Tạo shard-window messages; PHẢI dùng chunkSendBatch; cấm direct `queue.sendBatch()` |
| Scan Worker | Nhận từ `bot-scan` queue | Query D1, fan-out `light-check`, batch-update D1 | SELECT LIMIT 500/shard; 1 D1 stmt/shard cho `next_light_check_at`; không per-bot individual write |
| Light-Check Worker | Nhận từ `light-check` queue | Đọc D1 + MarketDataDO; tính RebalanceReason[]; fan-out | Idempotency-first; zero HL calls; evaluate circuit/stop/overrun; update idempotency='succeeded' khi xong |
| `queue_idempotency` | state: started → succeeded | Insert tại đầu; update tại cuối | UNIQUE conflict trên `message_id` → return ngay; ngăn double-processing |
| Circuit Breaker | closed / open / half_open | Đọc từ `hedge_legs.circuit_state` | open → suppress hedge-sync; half_open → 1 probe atomic; stop monitoring LUÔN chạy |
| `stop_trigger_crossed_at` | NULL → Timestamp (write-once) | Set khi markPrice >= stop_price | Guarded: chỉ set nếu NULL (BR-EXBOT-005); nếu đã có → không ghi đè; vẫn enqueue price-near-stop-audit |
| `stop_replacing_started_at` | NULL / Timestamp | Kiểm tra mỗi light-check pass | NOT NULL AND age > 60s → partial_repair + SAFE_MODE |
| MarketDataDO | Shared cache sqrtPriceX96/currentTick | Đọc bởi tất cả light-check workers | Cache TTL per NV-12 (⚠️ chưa xác nhận); stale cache → drift calculation sai |

⚠️ **Platform-specific gap (API-only):** Hành vi khi D1 read thất bại, MarketDataDO không phản hồi, chunkSendBatch enqueue fail — không được mô tả trong UC.

---

## 6. Logic nghiệp vụ & Phân tích luồng ⚠️ Partial

### 6.1 Hàm: Thực thi Light-Check định kỳ

**A. Luồng công việc**

| Bước | Tác nhân | Hành động | Phản hồi hệ thống (Happy Path) | Luồng thay thế |
|---|---|---|---|---|
| 1 | Cron Worker | chunkSendBatch → `bot-scan` với shard windows | Messages enqueued | — |
| 2 | Scan Worker | `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500` | Danh sách bot | — |
| 3 | Scan Worker | chunkSendBatch per-bot messages → `light-check` queue | Messages enqueued | — |
| 4 | Scan Worker | Batch-update `next_light_check_at = now + 5min + jitter(±45s)` (1 stmt/shard) | D1 cập nhật | — |
| 5 | Light-Check Worker | Insert `message_id` vào `queue_idempotency` (state='started') | Ghi nhận | UNIQUE conflict → return ngay (dedup) |
| 6 | Light-Check Worker | Đọc D1: `last_known_hl_short_size`, `lifecycle_state`, `stop_price`, `margin_status`, `circuit_state`, `stop_replacing_started_at` | Trạng thái loaded | — |
| 7 | Light-Check Worker | Đọc MarketDataDO: `sqrtPriceX96`, `currentTick` (ZERO HL call) | Dữ liệu giá loaded | — |
| 8 | Light-Check Worker | Tính `lpEthAmount` qua TickMath + LiquidityAmounts (cục bộ) | lpEthAmount computed | — |
| 9 | Light-Check Worker | Đánh giá RebalanceReason[] dùng D1 + MarketDataDO | reasons[] | A4: lifecycle IN ('lp_rebalancing','lp_closing') OR status='paused' → skip toàn bộ |
| 10 | Light-Check Worker | Nếu reasons[] found AND circuit != 'open': enqueue `hedge-sync` | hedge-sync enqueued | A1: circuit='open' → suppress; A2: circuit='half_open' → 1 probe atomic |
| 11 | Light-Check Worker | Nếu markPrice >= stop_price: set `stop_trigger_crossed_at` (guarded); enqueue `price-near-stop-audit` | stop-audit enqueued | A3: `stop_trigger_crossed_at` đã set → không ghi đè, vẫn enqueue; A4: range_boundary_near → cũng enqueue |
| 11b | Light-Check Worker | Nếu `stop_replacing_started_at` NOT NULL AND age > 60s: enqueue partial_repair + SAFE_MODE | SAFE_MODE entered | — |
| 12 | Light-Check Worker | Update `queue_idempotency.state='succeeded'` | Idempotency hoàn thành | — |

**B. Quy tắc nghiệp vụ & Validation**

| Mã | Nội dung | Áp dụng tại |
|---|---|---|
| BR-EXBOT-003 | Light-check HL weight = 0. Bất kỳ HL API call nào là vi phạm kiến trúc. | Toàn bộ Steps 6-11 |
| BR-EXBOT-005 | `stop_trigger_crossed_at` write-once (guarded: chỉ set nếu NULL). | Step 11 |
| FR-EXBOT-011 | 3-way price split không được trộn: uniPoolPrice cho LP drift; hlMarkPrice cho stop trigger; hlOraclePrice cho margin calc. | Steps 8-11 |
| FR-EXBOT-013 | `next_light_check_at = now + 5min + random(−45s, +45s)`; batch-write 1 stmt/shard. | Step 4 |
| FR-EXBOT-023 | Chỉ dùng canonical RebalanceReason[] enum. `stop_trigger_crossed` KHÔNG phải RebalanceReason. | Steps 9-10 |
| NFR-EXBOT-001 | 10.000 bot / 5 phút sustained; zero HL weight. | Kiến trúc |
| NFR-EXBOT-005 | Không có unconditional UPDATE per-bot; write-on-change only. | Steps 4, 12 |
| NFR-EXBOT-007 | Mọi queue consumer: idempotency ledger insert trước; UNIQUE conflict = skip. | Steps 5, 12 |

**C. Phản hồi / Output**

- **Không hành động:** reasons[] rỗng + không có stop trigger → cập nhật `next_light_check_at` + idempotency
- **hedge-sync enqueued:** reasons[] found + circuit closed (hoặc 1 probe khi half_open)
- **price-near-stop-audit enqueued:** markPrice >= stop_price HOẶC range_boundary_near — LUÔN enqueue dù circuit open
- **partial_repair + SAFE_MODE:** stop_replacing_started_at stuck > 60s

### 6.2 Các luồng thay thế

| Luồng | Điều kiện | Hành vi |
|---|---|---|
| A1 — Circuit open | circuit_state='open' ở Step 10 | Suppress hedge-sync; TIẾP TỤC stop monitoring |
| A2 — Circuit half_open | circuit_state='half_open' ở Step 10 | 1 probe atomic (half_open_probe_used 0→1); suppress sau khi đã dùng |
| A3 — stop_trigger_crossed_at đã set | stop_trigger_crossed_at IS NOT NULL ở Step 11 | Không ghi đè; vẫn enqueue price-near-stop-audit |
| A4 — Bot đang rebalancing/closing/paused | lifecycle/status conditions ở Step 9 | Skip toàn bộ evaluation; sang bot tiếp theo |

---

## 7. Phân tích tích hợp chức năng ⚠️ Partial

| Trigger / Hành động | Ảnh hưởng downstream | Nhất quán dữ liệu |
|---|---|---|
| Light-check enqueue hedge-sync | hedge-sync worker (US-006) nhận; acquire UserLockDO lease; delta-only adjustment; post-order reconcile cập nhật `last_known_hl_short_size` | `stateVersion` trong message phải khớp D1; mismatch → discard (US-006 AC-2) |
| Light-check phát hiện stop trigger | `stop_trigger_crossed_at` set (write-once); price-near-stop-audit enqueued | Stuck > 30 min → SAFE_MODE (phát hiện bởi deep-audit FR-EXBOT-016 hoặc light-check FR-EXBOT-031) |
| Scan Worker batch-update next_light_check_at | 1 stmt/shard; jitter phân phối đều | Nếu batch thất bại → bot có thể không re-schedule đúng hạn |
| stop_replacing_started_at stuck > 60s | partial_repair enqueued + SAFE_MODE | FR-EXBOT-032 yêu cầu clear trong `finally` block để tránh false positive |
| MarketDataDO cache | Tất cả workers dùng chung `sqrtPriceX96`/`currentTick` | Cache TTL chưa xác nhận (NV-12 🔴 B1); stale → sai lpEthAmount → sai drift detection |

⚠️ **Platform-specific gap (API-only):** CF Queue at-least-once delivery semantics + idempotency handling chưa mô tả đủ cho tester.

---

## 8. Tiêu chí chấp nhận ⚠️ Partial

| AC # | Kịch bản | Given | When | Then |
|---|---|---|---|---|
| AC-01 | Happy path — phát hiện drift, enqueue hedge-sync | Bot active, `\|targetShortEth - lastKnownShortEth\| × uniPoolPrice > $25`, circuit closed | Light-check worker xử lý bot này | Đánh giá RebalanceReason[] dùng D1 + MarketDataDO (zero HL call); hedge-sync enqueued với reasons=['drift_threshold'] và stateVersion; next_light_check_at cập nhật |
| AC-02 | Stop trigger phát hiện, route sang stop-audit | Bot active, markPrice >= stop_price | Light-check worker xử lý | `stop_trigger_crossed_at` được set (chỉ khi NULL); price-near-stop-audit enqueued; KHÔNG enqueue hedge-sync |
| AC-03 | Circuit open — hedge-sync bị suppress | Bot active với circuit_state='open' | Light-check worker xử lý | KHÔNG enqueue hedge-sync; VẪN đánh giá và enqueue price-near-stop-audit nếu stop triggered; không skip bot hoàn toàn |
| AC-04 | lifecycle đang lp_rebalancing — skip toàn bộ | Bot với lifecycle_state='lp_rebalancing' | Light-check worker gặp bot này | Bỏ qua toàn bộ evaluation và enqueuing; sang bot tiếp theo không lỗi |
| AC-05 | Idempotency — message trùng lặp | Light-check worker nhận message_id đã xử lý trước | Insert queue_idempotency(state='started') | UNIQUE conflict → return ngay; không tính toán, không enqueue |
| AC-06 | stop_trigger_crossed_at write-once | Bot có stop_trigger_crossed_at đã set (NOT NULL) | Light-check phát hiện markPrice >= stop_price lại | Không ghi đè stop_trigger_crossed_at; vẫn enqueue price-near-stop-audit |
| AC-07 | next_light_check_at batch-write | Scan Worker xử lý 1 shard với N bots | Sau khi fan-out xong | D1 update `next_light_check_at` được thực hiện bằng 1 statement cho toàn shard; không có per-bot individual UPDATE |
| AC-08 | stop_replacing_overrun detection | `stop_replacing_started_at` IS NOT NULL và age > 60s | Light-check worker kiểm tra | partial_repair enqueued với reason='stop_replacing_overrun'; SAFE_MODE được kích hoạt |
| AC-09 | Circuit half_open — 1 probe duy nhất | Bot với circuit_state='half_open', half_open_probe_used=0 | Light-check worker xử lý | Chỉ 1 hedge-sync probe được enqueue (atomic half_open_probe_used 0→1) |
| AC-10 | range_boundary_near — enqueue stop-audit | Bot với price tại 90% boundary range | Light-check worker xử lý | price-near-stop-audit enqueued; hedge-sync KHÔNG được enqueue chỉ vì lý do này |
| AC-11 | 3-way price split | Light-check tính deltaErrorUsd và đánh giá stop | Đọc dữ liệu giá | deltaErrorUsd dùng uniPoolPrice (sqrtPriceX96); stop comparison dùng hlMarkPrice; không trộn lẫn |
| AC-12 | Zero HL call invariant | Bất kỳ light-check cycle nào với 10.000 bots | Hoàn thành một chu kỳ 5 phút | HL API rate limit weight consumed = 0 |

---

## 9. Yêu cầu phi chức năng ⚠️ Partial

| Danh mục | Yêu cầu | Nguồn |
|---|---|---|
| Throughput | 10.000 bot / chu kỳ 5 phút = 33.3 bot/giây sustained | NFR-EXBOT-001; US-005 |
| Rate limit HL | HL API weight = 0 trong mọi light-check; BNZA operating budget: 800 weight/min | NFR-EXBOT-004; BR-EXBOT-003 |
| D1 Write | Không có unconditional UPDATE per-bot; write-on-change only; batch next_light_check_at (1 stmt/shard) | NFR-EXBOT-005; FR-EXBOT-013 |
| Idempotency | Mọi queue consumer insert idempotency ledger trước khi xử lý; UNIQUE conflict = skip | NFR-EXBOT-007 |
| Precision | Tất cả tính toán hedge/LP dùng BigDecimal; float/number arithmetic cấm | NFR-EXBOT-008 |
| Latency SLA | ⚠️ Không có SLA tường minh cho end-to-end light-check latency trong UC | Không định nghĩa |
| CF Workers limits | ⚠️ CF Workers max 6 simultaneous outbound connections/invocation (FR-EXBOT-110) không đề cập trong UC | FR-EXBOT-110 — chưa tham chiếu trong UC |

---

## 10. Câu hỏi mở & Phụ thuộc

### 10.1 Câu hỏi mở
*(Xem Bảng Q-Table tại Audit Summary bên dưới để biết toàn bộ Q1-Q13)*

### 10.2 Phụ thuộc
- FR-EXBOT-040 (Circuit Breaker State Machine) — quyết định hedge-sync enqueue
- FR-EXBOT-015 (LP Range Rebalance) P1 — downstream của `range_out` reason
- FR-EXBOT-016 (Deep-Audit Cron) — phát hiện stuck stop_trigger_crossed_at độc lập
- NV-12 — wethIndex + MarketDataDO cache TTL (chưa xác nhận)
- NV-1/NV-3 — stop replacement protocol (chưa xác nhận)
- UC-EXBOT-hedge-sync — consumer downstream của hedge-sync queue

---

## 11. Change Log

| Phiên bản | Ngày | Tác giả | Tóm tắt |
|---|---|---|---|
| v1 | 2026-06-16 | qc-uc-read / run-20260616-180000-udemysen | First audit — uc-light-check.md + us-005.md + us-006.md |

---

## Audit Summary

### Bảng điểm tổng hợp

> KA #1 → §0 · #2 → §1 · #3 → §2 · #4 → §3 · #5 → §4 · #6 → §5 · #7 → §6 · #8 → §7 · #9 → §8 · #10 → §9

| # | Lĩnh vực kiến thức | Max | Điểm | Trạng thái |
|---|---|---|---|---|
| 1 | Nhận diện tính năng | 5 | 5 | ✅ |
| 2 | Mục tiêu & Phạm vi | 5 | 4 | ⚡ |
| 3 | Tác nhân & Vai trò | 10 | 8 | ⚡ |
| 4 | Tiền/Hậu điều kiện | 10 | 8 | ⚡ |
| 5 | Danh mục đối tượng D1/API | 15 | 11 | ⚡ |
| 6 | Thuộc tính & Hành vi | 20 | 14 | ⚡ |
| 7 | Logic nghiệp vụ & Luồng | 20 | 15 | ⚡ |
| 8 | Phân tích tích hợp | 20 | 13 | ⚡ |
| 9 | Tiêu chí chấp nhận | 20 | 14 | ⚡ |
| 10 | Yêu cầu phi chức năng | 5 | 3 | ⚡ |
| **Tổng** | | **130** | **95/130 → 73.1/100** | ⚠️ **CONDITIONALLY READY** |

> **Lưu ý:** Điểm Phase 2 tính được 99/130 = 76.2. Sau review lại KA #8 (tích hợp) thấy thiếu sót nhiều hơn dự kiến → điều chỉnh xuống 13/20. Điểm cuối chính thức: **95/130 → 73.1/100**.

### 📋 Bảng Q-Table (Câu hỏi & Gap thống nhất)

| ID | Ưu tiên | Ref | Câu hỏi | Tại sao quan trọng | Trạng thái |
|---|---|---|---|---|---|
| Q1 | Medium | uc-light-check.md §3 Step 10 | Schema message `hedge-sync` (`{botId, reasons, stateVersion}`) — kiểu dữ liệu chính xác, format, required fields là gì? | Tester không thể xác minh message payload đúng hay sai nếu không có schema | Open |
| Q2 | Medium | uc-light-check.md §3 Step 11 | Schema message `price-near-stop-audit` — fields, types là gì? | Tester cần biết message content để viết AC cho stop-audit consumer | Open |
| Q3 | Low | FR-EXBOT-011 | Schema message `partial_repair (reason='stop_replacing_overrun')` — fields, types là gì? | Cần để test stop_replacing_overrun detection path | Open |
| Q4 | High | frd.md FR-EXBOT-092 | MarketDataDO cache TTL và refresh cadence là bao lâu? Nếu cache stale/unavailable, light-check có fallback không? | Cache stale → sai lpEthAmount → sai hedge target → false positive/negative drift detection | Open |
| Q5 | Medium | uc-light-check.md §3 Step 2 | Khi số bot active trong 1 shard > 500 (LIMIT 500), Scan Worker có tiếp tục scan trong cùng cron tick không? Behavior overflow là gì? | Ở scale 10.000 bots, >500/shard hoàn toàn có thể xảy ra | Open |
| Q6 | Medium | N/A (Missing) | Khi Light-Check Worker không đọc được D1 (network/timeout) → hành vi là gì? Bot bị skip không? queue_idempotency có cập nhật không? | Tester không thể viết negative test cho D1 failure path | Open |
| Q7 | Medium | N/A (Missing) | Khi chunkSendBatch enqueue hedge-sync thất bại → hành vi là gì? Có retry không? Bot có mất đợt check này không? | Cần để test queue enqueue failure path | Open |
| Q8 | Low | uc-light-check.md frontmatter linked_stories | US-006 (delta-only hedge-sync) mô tả hedge-sync worker behavior, không phải light-check actor. linked_stories cần cập nhật để phản ánh đúng ranh giới UC. | Tránh nhầm lẫn khi tester mapping US sang test case | Open |
| Q9 | Medium | FR-EXBOT-031 vs FR-EXBOT-016 | stop_trigger_crossed_at stuck > 30 min → SAFE_MODE: ai là người detect chính — light-check hay deep-audit? UC không đề cập. | Tester cần biết để viết test case cho SAFE_MODE trigger path đúng component | Open |
| Q10 | Low | uc-light-check.md §4 A4 | range_boundary_near threshold "90%" — tính từ đâu, 90% khoảng cách tick hay 90% giá trị tuyệt đối? | Không xác định threshold → không thể viết boundary test case | Open |
| Q11 | Medium | uc-light-check.md §4 A2 | Khi circuit_state='half_open' và half_open_probe_used đã = 1 (probe đã dùng): light-check suppress hoàn toàn hay trigger reset attempt? | Cần để test half_open với probe đã dùng — edge case quan trọng | Open |
| Q12 (NV-12) | High | GAP-004; project-context-master Q-012 | wethIndex đã xác nhận cho Base và OP là gì? MarketDataDO cache TTL là bao nhiêu? | wethIndex sai → hedge target sai; cache TTL chưa biết → không test được staleness behavior | Open |
| Q13 (NV-1/NV-3) | High | GAP-005; project-context-master Q-011 | Giao thức stop replacement đã xác nhận chưa? stop_replacing_overrun detection có phụ thuộc NV-1/NV-3 không? | INV-STOP protocol và stop_replacing_started_at stuck detection đều liên quan | Open |

### 🟢 Điểm tốt

- **UC-005 có 4 Gherkin ACs chất lượng cao** — bao phủ đủ happy path, stop trigger, circuit open, lifecycle skip. Đây là US được viết tốt nhất trong nhóm ExBot.
- **3-way price split được áp dụng nhất quán** trong mọi bước tính toán — không phát hiện vi phạm trong tài liệu.
- **Circuit breaker và write-once guard** được định nghĩa rõ ràng với behavior tường minh.
- **Idempotency pattern** nhất quán: queue_idempotency insert-first cho mọi consumer.
- **Zero-HL-call invariant** (BR-EXBOT-003) được tham chiếu rõ ràng và là tiêu chí testable.

### 🧪 Testability Outlook

**Có thể test ngay:**
- Zero HL call invariant (AC-12)
- drift_threshold và drift_relative detection (AC-01)
- Circuit breaker open — suppress hedge-sync, keep stop monitoring (AC-03)
- stop_trigger_crossed_at write-once guard (AC-06)
- Idempotency dedup (AC-05)
- lifecycle skip (AC-04)
- batch-write next_light_check_at (AC-07)
- 3-way price split correctness (AC-11)

**Chưa thể test (bị chặn bởi gap):**
- MarketDataDO stale behavior (blocked: Q4 / NV-12)
- stop_replacing_overrun detection end-to-end (blocked: Q3 / NV-1/NV-3)
- Scan Worker overflow behavior khi >500 bots/shard (blocked: Q5)
- D1 read failure handling (blocked: Q6)
- Queue enqueue failure handling (blocked: Q7)
- range_boundary_near boundary test (blocked: Q10)
- half_open probe-used edge case (blocked: Q11)

**Gợi ý focus test khi gap được giải quyết:**
- Happy path: light-check với 1 bot drift → hedge-sync enqueued với đúng reasons/stateVersion
- Alternate: stop trigger detection → price-near-stop-audit, KHÔNG hedge-sync
- Boundary: deltaErrorUsd tại đúng ngưỡng $25 và lpValueUsd × 3%
- Circuit integration: open → suppress; half_open → 1 probe; close → normal
- Idempotency: replayed message_id → no duplicate enqueue
- Scale: N bots với mixed states → chỉ bots hợp lệ được enqueue

### 📌 Tóm tắt & Khuyến nghị

Tập tài liệu cho UC-EXBOT-light-check **có nền tảng tốt**: US-005 cung cấp ACs chất lượng, uc-light-check.md mô tả đầy đủ luồng chính và 4 alternate flows, các ràng buộc cốt lõi (zero-HL, 3-way price split, write-once, idempotency) được ghi nhận rõ. Tuy nhiên, **có 2 nhóm gap chính cần giải quyết trước khi test design đầy đủ:**

1. **Gap kỹ thuật (cần BA bổ sung):** Schema message cho hedge-sync/price-near-stop-audit/partial_repair chưa định nghĩa (Q1-Q3); error handling cho D1/DO/queue failure chưa tài liệu hóa (Q6-Q7); MarketDataDO cache TTL chưa rõ (Q4); Scan Worker overflow behavior chưa định nghĩa (Q5).

2. **Blockers bên ngoài (cần zen xác nhận):** NV-12 (wethIndex + MarketDataDO TTL, Q12) và NV-1/NV-3 (stop replacement, Q13).

**Khuyến nghị:** QA có thể bắt đầu design test case cho các ACs không phụ thuộc vào blockers (AC-01 đến AC-12 trừ stop-related). Tạm hoãn test cases cho MarketDataDO staleness và stop_replacing_overrun cho đến khi NV-12/NV-1/NV-3 được xác nhận. Ưu tiên BA trả lời Q1-Q4 trước vì ảnh hưởng trực tiếp đến khả năng viết integration test.

