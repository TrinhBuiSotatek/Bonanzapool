# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Document title:** UC Readiness Review — UC-EXBOT-light-check (Execute Periodic Light-Check)
**Date created:** 2026-07-06
**Author/Agent:** qc-uc-read-exbot
**Version:** v3

---

## Feature Brief - Tóm tắt nghiệp vụ

UC-EXBOT-light-check mô tả quy trình hệ thống tự động kiểm tra sức khỏe của từng ExBot theo chu kỳ 5 phút. Không có bất kỳ lệnh gọi API đến Hyperliquid (HL) nào trong toàn bộ luồng này — đây là bất biến kiến trúc cốt lõi (BR-EXBOT-003). Toàn bộ dữ liệu lấy từ Aurora PostgreSQL và ElastiCache Redis.

Luồng chạy theo 3 tầng worker: (1) **EventBridge Scheduler** (1 phút/lần) enqueue `bot-scan`; (2) **Scan Worker** đọc Aurora PostgreSQL để lấy danh sách bot đến hạn kiểm tra, enqueue `light-check` per-bot, cập nhật batch `next_light_check_at`; (3) **Light-Check Worker** đọc trạng thái bot từ Aurora PostgreSQL, đọc dữ liệu giá từ Pool Slot0 Cache (ElastiCache Redis), tính `lpEthAmount`, đánh giá `RebalanceReason[]`, và fan-out: enqueue `hedge-sync` nếu cần rebalance, hoặc enqueue `price-near-stop-audit` nếu stop trigger crossed.

Ngoài việc đánh giá rebalance, mỗi light-check pass còn kiểm tra: (a) `stop_replacing_started_at` overrun > 60s → SAFE_MODE + `partial_repair`; (b) `markPrice >= stop_price` (via HL Mark Price Cache, ElastiCache Redis) → ghi `stop_trigger_crossed_at` + `price-near-stop-audit`. Stop monitoring chạy mọi lúc kể cả khi circuit breaker `open`.

So với v2 (20260703), thay đổi lớn nhất trong v3 là **AWS migration** hoàn chỉnh: Cloudflare Workers/D1/Durable Objects được thay bằng AWS Lambda/Aurora PostgreSQL/ElastiCache Redis. UC đã được cập nhật changelog 2026-07-04 để phản ánh migration này. Audit v3 tập trung kiểm tra: (1) sự đồng nhất giữa UC mới và SRS mới; (2) các FR trace còn thiếu trong UC; (3) các điểm không nhất quán còn sót lại sau migration.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check | 2026-07-04 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | TBD | 2026-06-12 | 2026-07-04 (arc-migration) |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `uc-light-check.md` | 2026-07-04 | UC | Đã cập nhật arc-migration |
| `srs/spec.md` | 2026-07-04 | SRS | Source of truth — AWS Lambda/Aurora PostgreSQL/ElastiCache Redis |
| `srs/states.md` | 2026-07-03 | State diagram | 18 lifecycle states; circuit breaker; margin status |
| `srs/flows.md` | 2026-07-04 | Flow diagram | F-01: Queue Fan-Out (EventBridge → Scan → Light-Check → Hedge-Sync) |
| `srs/erd.md` | 2026-07-04 | ERD | Aurora PostgreSQL schema |
| `frd.md` | 2026-07-04 | FRD | FR-EXBOT-011, 012 light-check spec |
| `userstories/us-005.md` | 2026-07-04 | US | US-EXBOT-005: Light-check no HL |
| `userstories/us-006.md` | 2026-07-04 | US | US-EXBOT-006: Delta-only hedge |
| `userstories/us-007.md` | 2026-07-04 | US | US-EXBOT-007: LP range rebalance |
| `userstories/us-008.md` | 2026-06-12 | US | US-EXBOT-008: Circuit breaker |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này đảm bảo mỗi ExBot đang hoạt động được kiểm tra định kỳ 5 phút một lần mà không tiêu tốn bất kỳ HL rate limit nào. Mục tiêu là phát hiện sớm các tình huống cần điều chỉnh hedge (drift, range_out, funding, margin warning, v.v.) và kích hoạt đúng fan-out action. Đây là vòng lặp giám sát chủ động không thể thiếu cho hệ thống quản lý 10.000 bot đồng thời trên AWS.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Cron fan-out | EventBridge Scheduler 1min → `bot-scan` queue | UC §3 step 1; SRS FR-EXBOT-010 |
| Scan Worker query | Chọn bots active, `next_light_check_at <= now`, LIMIT 500, oldest-first | UC §3 step 2; SRS FR-EXBOT-012 |
| Scan Worker enqueue | `chunkSendBatch` per-bot vào `light-check` queue | UC §3 step 3; SRS FR-EXBOT-010 |
| next_light_check_at batch update | 1 UPDATE/shard cho TẤT CẢ eligible bots (kể cả bots bị skip) | UC §3 step 4; SRS FR-EXBOT-013 |
| Idempotency check | INSERT `queue_idempotency` (state='started'); UNIQUE conflict → skip | UC §3 step 5; SRS FR-EXBOT-011 |
| Bot state read | Đọc Aurora PostgreSQL: `bot_runtime_state`, `lifecycle_state`, `hedge_legs` | UC §3 step 6 |
| Pool Slot0 Cache read | Đọc ElastiCache Redis: `sqrtPriceX96`, `currentTick`; stale > 5min → fail-fast | UC §3 step 7; SRS FR-EXBOT-093 |
| lpEthAmount computation | TickMath + LiquidityAmounts, zero HL calls | UC §3 step 8; SRS FR-EXBOT-020 |
| RebalanceReason[] evaluation | drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback | UC §3 step 9; SRS FR-EXBOT-023 |
| Hedge-sync fan-out | Enqueue 1 hedge-sync với `reasons[]` khi REBALANCE và circuit != open | UC §3 step 10; SRS FR-EXBOT-012 |
| Stop trigger detection | Đọc HL Mark Price Cache (ElastiCache Redis); stale > 120s → fallback + freeze + widen band | UC §3 step 11; SRS OQ-EXBOT-17 |
| SAFE_MODE entry | `stop_replacing_started_at` overrun > 60s → atomic UPDATE (status + lifecycle_state) + `partial_repair` | UC §3 step 12; SRS FR-EXBOT-033 |
| Idempotency finalize | UPDATE `queue_idempotency.state='succeeded'` | UC §3 step 13 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Hedge-sync execution | Xử lý sau khi hedge-sync message được enqueue — thuộc UC-EXBOT-hedge-sync | Cần test riêng |
| LP rebalance execution | Quá trình rebalance thực tế (BnzaExVault.vaultRebalance) — thuộc hedge-sync handler downstream | Cần test riêng |
| Deep-audit | Backstop detection cho `stop_replacing_started_at` stuck > 60s — thuộc UC-EXBOT-deep-audit | Cần test riêng |
| Stop-audit execution | Xử lý sau khi `price-near-stop-audit` được enqueue — thuộc UC separate | Cần test riêng |
| SAFE_MODE auto-recovery | Quá trình thoát SAFE_MODE — thuộc SRS FR-EXBOT-050 | Cần test riêng |
| Pool Slot0 Cache write | Fargate HL WS Poller viết cache — không thuộc ExBot Lambda scope | N/A cho light-check test |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| EventBridge Scheduler (1 min) | System | Trigger chính — enqueue `bot-scan` | Chỉ enqueue, không đọc Aurora PostgreSQL trực tiếp | UC §1; SRS FR-EXBOT-010 |
| Scan Worker (Lambda) | System | Đọc Aurora PostgreSQL, enqueue `light-check` per-bot, batch UPDATE `next_light_check_at` | Chỉ đọc + batch write Aurora PostgreSQL; không gọi HL | UC §1; SRS FR-EXBOT-012 |
| Light-Check Worker (Lambda) | System | Tính toán, đánh giá RebalanceReason[], fan-out | Zero HL calls; chỉ đọc Aurora PostgreSQL + ElastiCache Redis | UC §1; SRS BR-EXBOT-003 |
| Aurora PostgreSQL (state_db_shard) | System | Lưu trạng thái bot | Source of truth cho lifecycle_state, hedge_legs, bot_runtime_state | UC §1; SRS §1 |
| Pool Slot0 Cache (ElastiCache Redis) | System | Cung cấp `sqrtPriceX96`, `currentTick` | Fargate poller viết; Lambda đọc; stale > 5min → fail-fast | UC §1; SRS FR-EXBOT-093 |
| HL Mark Price Cache (ElastiCache Redis) | System | Cung cấp `markPriceUsd` cho stop trigger detection | Stale > 120s → fallback + widen band + freeze hedge-sync | UC §3 step 11; SRS OQ-EXBOT-17 |

**Nhận xét readiness:** Actor rõ ràng sau migration — tất cả Cloudflare primitives (D1, Durable Objects, Cron Worker) đã được thay bằng AWS equivalents. HL Mark Price Cache giờ là ElastiCache Redis key thay vì HlMarkDO. Tuy nhiên, UC chưa ghi rõ key name của HL Mark Price Cache trong ElastiCache Redis (chỉ nói "HL Mark Price Cache" chung chung) — minor issue cho test design.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot có `status='active'` và `next_light_check_at <= now` | Yes | UC §2; SRS FR-EXBOT-012 |
| 2 | `lifecycle_state NOT IN ('lp_rebalancing', 'lp_closing')` | Yes | UC §2; SRS states.md |
| 3 | `status != 'paused'` | Yes | UC §2; SRS FR-EXBOT-003 |
| 4 | Pool Slot0 Cache (ElastiCache Redis) khả dụng và không stale (≤ 5min) | Yes (nếu stale → skip, không lỗi toàn hệ thống) | UC §3 step 7; A1 |
| 5 | Bot có bản ghi trong `bot_runtime_state`, `hedge_legs`, `positions` | Yes | UC §3 step 6 |
| 6 | EventBridge Scheduler đang chạy và `bot-scan` queue có tin nhắn | Yes | UC §3 step 1 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Không cần rebalance | `queue_idempotency.state='succeeded'`; không có message mới trong queue | UC §3 step 13 |
| Cần rebalance (drift, range_out, v.v.) | 1 `hedge-sync` message enqueued với `reasons[]`; `queue_idempotency.state='succeeded'` | UC §3 step 10 |
| Stop trigger crossed | `hedge_legs.stop_trigger_crossed_at` set (write-once); `price-near-stop-audit` enqueued | UC §3 step 11; SRS FR-EXBOT-032 |
| Pool Slot0 Cache stale/unreachable | Tick bị skip hoàn toàn; không có mutation; `queue_idempotency.state` vẫn `'started'` | UC A1 |
| `stop_replacing_started_at` overrun | `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` (atomic); `partial_repair` enqueued | UC §3 step 12; SRS FR-EXBOT-033 |
| Bot bị skip (lp_rebalancing/paused) | Bot không được enqueue; `next_light_check_at` vẫn được cập nhật trong batch | UC §3 step 4; SRS FR-EXBOT-012 |

---

## 4. Bảng mã viết tắt

| Code / Prefix | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| BR-EXBOT-* | Business Rule — quy tắc nghiệp vụ bất biến của ExBot. BR-EXBOT-003: mọi light-check phải có HL weight = 0. | `srs/spec.md` §Business Rules |
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng ExBot. Mỗi FR mô tả hành vi cụ thể của một worker hoặc service. | `srs/spec.md` §FR |
| NFR-EXBOT-* | Non-Functional Requirement — yêu cầu phi chức năng (throughput, connection limit, latency). | `srs/spec.md` §NFR |
| OQ-EXBOT-* | Open Question — câu hỏi chưa được chốt trong SRS. Mỗi OQ có trạng thái Open/Closed. | `srs/spec.md` §Open Questions |
| AC-LC-* | Acceptance Criteria cho UC-EXBOT-light-check — điều kiện nghiệm thu cụ thể của UC này. | `uc-light-check.md` (audited) |
| US-EXBOT-* | User Story ExBot — mô tả hành vi từ góc nhìn actor. Linked với UC để xác nhận ACs. | `userstories/` |
| Pool Slot0 Cache | ElastiCache Redis cache chứa `sqrtPriceX96`, `currentTick`, `blockNumber` — do Fargate HL WS Poller viết, Lambda ExBot đọc. Thay thế MarketDataDO (Cloudflare Durable Object) sau migration. | `srs/spec.md` FR-EXBOT-093 |
| HL Mark Price Cache | ElastiCache Redis key `markPriceUsd` — do Fargate HL WS Poller viết. Dùng cho stop trigger detection. Thay thế HlMarkDO (Cloudflare Durable Object) sau migration. | `uc-light-check.md` step 11; SRS OQ-EXBOT-17 |
| SIWE | Sign-In With Ethereum — phương thức xác thực người dùng bằng chữ ký ví ETH. Không trực tiếp liên quan đến light-check. | Industry standard |
| LP | Liquidity Provider — vị thế Uniswap V3 của bot được đại diện bởi một NFT position (tokenId). Trong ExBot, LP position được bọc bởi BnzaExVault; raw fee chưa collected KHÔNG được hiển thị trực tiếp. | `srs/spec.md` §LP |

---

## 5. Bảng kiểm kê chức năng (§F.1 Inventory)

### 5.1 Operations & Triggers

| Operation ID | Tên operation | Trigger | Actor | Input chính | Output | Nguồn |
|---|---|---|---|---|---|---|
| OP-LC-01 | Cron fan-out | EventBridge Scheduler 1min schedule | EventBridge | Shard windows | `bot-scan` messages in SQS queue | SRS FR-EXBOT-010; UC step 1 |
| OP-LC-02 | Scan Worker query | `bot-scan` message dequeue | Scan Worker (Lambda) | `status='active'`, `next_light_check_at <= now` | List of eligible `botId[]`, max 500 oldest-first | SRS FR-EXBOT-012; UC step 2 |
| OP-LC-03 | Scan Worker enqueue per-bot | After query result | Scan Worker (Lambda) | `botId[]` | `light-check` messages, one per bot | SRS FR-EXBOT-010; UC step 3 |
| OP-LC-04 | Batch update `next_light_check_at` | After enqueue | Scan Worker (Lambda) | `botId[]`, `now + 5min + jitter(±45s)` | Aurora PostgreSQL batch UPDATE 1 statement/shard | SRS FR-EXBOT-013; UC step 4 |
| OP-LC-05 | Idempotency INSERT | On light-check message dequeue | Light-Check Worker (Lambda) | `message_id` | INSERT `queue_idempotency(state='started', expires_at=now+1min)` | SRS FR-EXBOT-011; UC step 5 |
| OP-LC-06 | Bot state read | After idempotency check | Light-Check Worker (Lambda) | `botId` | `bot_runtime_state`, `lifecycle_state`, `hedge_legs` from Aurora PostgreSQL | SRS FR-EXBOT-012; UC step 6 |
| OP-LC-07 | Pool Slot0 Cache read | After bot state read | Light-Check Worker (Lambda) | — | `sqrtPriceX96`, `currentTick` từ ElastiCache Redis | SRS FR-EXBOT-093; UC step 7 |
| OP-LC-08 | `lpEthAmount` computation | After cache read | Light-Check Worker (Lambda) | `sqrtPriceX96`, `currentTick`, `liquidity` | `lpEthAmount` (local TickMath + LiquidityAmounts) | SRS FR-EXBOT-020; UC step 8 |
| OP-LC-09 | RebalanceReason[] evaluation | After lpEthAmount | Light-Check Worker (Lambda) | `lpEthAmount`, `lastKnownHLShort`, `marginStatus`, `fundingApr7dPct`, `currentTick` | `decision.reason[]`, `decision.action` | SRS FR-EXBOT-023; UC step 9 |
| OP-LC-10 | Hedge-sync enqueue | `decision.action = REBALANCE` AND circuit != open | Light-Check Worker (Lambda) | `{botId, reasons[], stateVersion}` | 1 `hedge-sync` message enqueued | SRS FR-EXBOT-012; UC step 10 |
| OP-LC-11 | Stop trigger detection | After rebalance check | Light-Check Worker (Lambda) | `markPriceUsd` (HL Mark Price Cache), `stop_price` | `stop_trigger_crossed_at` write-once; `price-near-stop-audit` enqueued | SRS FR-EXBOT-032; UC step 11 |
| OP-LC-12 | SAFE_MODE entry check | After stop check | Light-Check Worker (Lambda) | `stop_replacing_started_at` | Atomic UPDATE (`status='safe_mode'`, `lifecycle_state='safe_mode'`); `partial_repair` enqueued | SRS FR-EXBOT-033; UC step 12 |
| OP-LC-13 | Idempotency finalize | After all checks | Light-Check Worker (Lambda) | `message_id` | UPDATE `queue_idempotency.state='succeeded'` | SRS FR-EXBOT-011; UC step 13 |

### 5.2 Data Objects & Fields

| Table / Object | Field | Type | Mô tả | Nguồn |
|---|---|---|---|---|
| `bots` | `status` | enum: `active`, `paused`, `safe_mode`, `error`, `closing` | Trạng thái hoạt động của bot | SRS ERD |
| `bots` | `lifecycle_state` | enum (18 giá trị: `active`, `lp_rebalancing`, `lp_closing`, `hedge_stopped_cooldown`, `safe_mode`, ...) | Trạng thái lifecycle state machine | SRS states.md |
| `bots` | `stop_replacing_started_at` | timestamp \| null | Thời điểm bắt đầu quá trình replace stop order | SRS FR-EXBOT-033 |
| `bot_runtime_state` | `last_known_hl_short_size` | decimal | Kích thước short HL cuối đã biết | SRS ERD |
| `bot_runtime_state` | `eth_price_usd` | decimal | Giá ETH lần cuối biết — fallback khi HL Mark Price Cache stale | SRS ERD; UC step 11 |
| `bot_runtime_state` | `sqrt_price_x96` | string (uint160) | sqrtPriceX96 từ Pool Slot0 Cache đã được persist | SRS ERD |
| `bot_runtime_state` | `current_tick` | int | currentTick từ Pool Slot0 Cache đã được persist | SRS ERD |
| `hedge_legs` | `stop_price` | decimal | Ngưỡng giá kích hoạt stop | SRS ERD |
| `hedge_legs` | `stop_trigger_crossed_at` | timestamp \| null | Write-once — thời điểm stop trigger bị crossed | SRS ERD; BR-EXBOT-005 |
| `hedge_legs` | `margin_status` | enum: `ok`, `warning`, `critical` | Trạng thái margin của bot | SRS ERD |
| `circuit_breakers` | `state` | enum: `closed`, `open`, `half_open` | Trạng thái circuit breaker của hedge leg | SRS ERD |
| `queue_idempotency` | `message_id` | varchar (UNIQUE) | ID message SQS để tránh xử lý trùng | SRS FR-EXBOT-011; UC step 5 |
| `queue_idempotency` | `state` | enum: `started`, `succeeded` | Trạng thái xử lý của message | SRS FR-EXBOT-011 |
| `queue_idempotency` | `expires_at` | timestamp | TTL = now+1min; không có cleanup job (Gap I-05) | UC step 5 |
| Pool Slot0 Cache | `sqrtPriceX96` | uint160 | sqrtPriceX96 của pool Uniswap V3 | SRS FR-EXBOT-093 |
| Pool Slot0 Cache | `currentTick` | int | currentTick của pool Uniswap V3 | SRS FR-EXBOT-093 |
| Pool Slot0 Cache | `updatedAt` | timestamp | Thời điểm cập nhật cache — dùng để xác định stale | SRS FR-EXBOT-093 |
| HL Mark Price Cache | `markPriceUsd` | decimal | Giá mark của ETH từ Hyperliquid | UC step 11; SRS OQ-EXBOT-17 |
| HL Mark Price Cache | `updatedAt` | timestamp | Thời điểm cập nhật — stale > 120s → fallback | UC step 11 |
| `funding_rolling_metrics` | `fundingApr7dPct` | decimal | 7-ngày APR funding (primary source cho funding_alert) | UC step 9 |

**Lưu ý:** Bảng `funding_rolling_metrics` được tham chiếu tại UC step 9 nhưng KHÔNG xuất hiện trong ERD (`srs/erd.md`). Đây là Issue I-03 (MISSING_INFO, Major) — xem §10.1.

### 5.3 Enum sets (đầy đủ)

**`bots.lifecycle_state` (từ `srs/states.md`):**
`active`, `lp_rebalancing`, `lp_closing`, `hedge_stopped_cooldown`, `safe_mode`, `error`, `closing`, `closed`, `paused`, `initializing`, `pending_deposit`, `pending_start`, `starting`, `pending_close`, `partial_close`, `pending_recovery`, `recovering`, `terminated`

**`circuit_breakers.state`:** `closed`, `open`, `half_open`

**`bots.status`:** `active`, `paused`, `safe_mode`, `error`, `closing`

**`RebalanceReason[]` (từ UC step 9 + SRS):**
`drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`

---

## 6. Luồng xử lý (§F.3)

### 6.1 Happy Path — Scan + Light-Check thành công, không cần rebalance

**Trigger:** EventBridge Scheduler fires 1min
**Actor:** EventBridge Scheduler → Scan Worker → Light-Check Worker
**Pre-condition:** Bot `status='active'`, `next_light_check_at <= now`, `lifecycle_state='active'`, Pool Slot0 Cache fresh (< 5min)

| Step | Action | System response |
|---|---|---|
| 1 | EventBridge enqueues `bot-scan` | SQS message visible to Scan Worker |
| 2 | Scan Worker queries Aurora PostgreSQL LIMIT 500 | Trả về danh sách `botId[]` |
| 3 | Scan Worker `chunkSendBatch` per-bot vào `light-check` queue | N messages enqueued |
| 4 | Scan Worker batch UPDATE `next_light_check_at = now + 5min + jitter` | 1 UPDATE statement / shard |
| 5 | LCW INSERT `queue_idempotency(state='started')` | Thành công (không có conflict) |
| 6 | LCW đọc Aurora PostgreSQL: bot state + hedge_legs | Dữ liệu hợp lệ |
| 7 | LCW đọc Pool Slot0 Cache: `sqrtPriceX96`, `currentTick` | Cache fresh — OK |
| 8 | LCW tính `lpEthAmount` via TickMath | `lpEthAmount > 0` |
| 9 | LCW đánh giá RebalanceReason[] | Không có reason nào fired |
| 10 | `decision.action = NO_ACTION` | Không enqueue hedge-sync |
| 11 | LCW đọc HL Mark Price Cache: `markPriceUsd` | `markPrice < stop_price` → không kích hoạt stop |
| 12 | Check `stop_replacing_started_at`: null | Không vào SAFE_MODE |
| 13 | LCW UPDATE `queue_idempotency.state='succeeded'` | OK |
**Expected result:** Không có message mới, `next_light_check_at` đã được cập nhật, HL API calls = 0.

### 6.2 Alternate Flow — Pool Slot0 Cache stale (A1)

**Trigger:** LCW đọc Pool Slot0 Cache tại step 7 → `updatedAt > 5min ago`
**Expected result:** LCW throw, skip tick hoàn toàn. Không có mutation nào với Aurora PostgreSQL. `queue_idempotency.state` vẫn `'started'` (chưa finalize). Bot sẽ được kiểm tra lại ở `next_light_check_at`.

**Gap cần lưu ý:** UC không ghi rõ LCW có UPDATE `queue_idempotency.state='failed'` khi skip hay không. Nếu không update, `queue_idempotency.state='started'` tồn tại mãi cho đến khi `expires_at` hết hạn (1min). Tester cần xác nhận behavior này.

### 6.3 Alternate Flow — Circuit Breaker open (A2)

**Trigger:** `circuit_breakers.state='open'` tại step 10
**Expected result:** hedge-sync KHÔNG được enqueue. Luồng tiếp tục đến step 11 (stop monitoring vẫn chạy). Nếu `markPrice >= stop_price`, vẫn enqueue `price-near-stop-audit`. SAFE_MODE check (step 12) vẫn chạy.

### 6.4 Alternate Flow — Circuit Breaker half_open (A3)

**Trigger:** `circuit_breakers.state='half_open'` tại step 10
**Expected result:** LCW atomically claim `half_open_probe_used`. Enqueue 1 probe hedge-sync (không enqueue thêm hedge-sync nào khác cho bot này trong tick này).

**UC không ghi rõ:** Điều gì xảy ra nếu `half_open_probe_used` đã được claimed bởi một worker khác trong cùng tick? Race condition này không được mô tả trong UC — tester cần xác nhận.

### 6.5 Stop Trigger Crossed

**Trigger:** `markPriceUsd >= hedge_legs.stop_price` tại step 11
**Pre-condition:** `stop_trigger_crossed_at IS NULL` (write-once guard)
**Expected result:**
- `hedge_legs.stop_trigger_crossed_at` được set = now
- `price-near-stop-audit` được enqueue
- Nếu cùng lúc `decision.action = REBALANCE`: hedge-sync bị "freeze" (không enqueue) vì đã có stop trigger. Hành vi freeze này là kết quả của "widen near-stop band" — UC ghi "freeze routine hedge-sync after stop check" nhưng chưa định nghĩa rõ điều kiện cụ thể.

**A4:** Nếu `stop_trigger_crossed_at IS NOT NULL` → KHÔNG overwrite. Vẫn enqueue `price-near-stop-audit`.

### 6.6 HL Mark Price Cache stale (UC step 11 — stale > 120s)

**Trigger:** `HL Mark Price Cache.updatedAt > 120s ago`
**Expected result:**
- Log `hl_mark_price_stale` audit event
- Widen near-stop band 2% → 4%
- Freeze routine hedge-sync (nếu có) sau stop check
- Fallback sang `bot_runtime_state.eth_price_usd` để đánh giá stop trigger

### 6.7 SAFE_MODE Entry (step 12)

**Trigger:** `stop_replacing_started_at IS NOT NULL` AND `now - stop_replacing_started_at > 60s`
**Expected result (atomic):**
- Trong 1 SQL statement: `UPDATE bots SET status='safe_mode', lifecycle_state='safe_mode' WHERE bot_id=...`
- Sau đó (sau khi UPDATE commit): `partial_repair(reason='stop_replacing_overrun')` được enqueue
- `queue_idempotency.state='succeeded'` vẫn được UPDATE ở step 13

---

## 7. Tích hợp & Nhất quán dữ liệu (§F.4)

| Integration point | Read by | Write by | Consistency concern | Nguồn |
|---|---|---|---|---|
| Aurora PostgreSQL `bots` | Scan Worker (query), LCW (read + write) | LCW (SAFE_MODE UPDATE), hedge-sync handler | Concurrent update: LCW và hedge-sync handler đều có thể write `lifecycle_state` → cần `stateVersion` check | SRS FR-EXBOT-012; UC step 10 |
| Aurora PostgreSQL `bot_runtime_state` | LCW | LCW (viết lại sau reconcile — NOT trong light-check); hedge-sync | Light-check chỉ đọc, không viết `bot_runtime_state` trực tiếp | SRS ERD |
| Pool Slot0 Cache (ElastiCache Redis) | LCW | Fargate HL WS Poller | Stale > 5min → LCW skip tick. LCW không viết Pool Slot0 Cache. | SRS FR-EXBOT-093 |
| HL Mark Price Cache (ElastiCache Redis) | LCW | Fargate HL WS Poller | Stale > 120s → fallback + freeze. LCW không viết cache. | UC step 11 |
| `queue_idempotency` | LCW (check UNIQUE conflict) | LCW | Không có cleanup job → bảng tích lũy theo thời gian (Gap I-05) | UC step 5 |
| `hedge-sync` SQS queue | hedge-sync handler | LCW | LCW enqueue exactly 1 per tick khi REBALANCE; hedge-sync xử lý async | SRS FR-EXBOT-010 |
| `price-near-stop-audit` SQS queue | stop-audit handler | LCW | LCW enqueue khi stop crossed; handler xử lý async | UC step 11 |
| `partial_repair` SQS queue | deep-audit/repair handler | LCW | LCW enqueue sau atomic SAFE_MODE UPDATE | SRS FR-EXBOT-033 |

---

## 8. Acceptance Criteria (§F.5)

| AC ID | Nội dung AC | Loại | Nguồn | Tester-ready? |
|---|---|---|---|---|
| AC-LC-01 | Khi `status='active'` và `next_light_check_at <= now`, bot được Scan Worker chọn và enqueue `light-check` | Functional | UC step 2; SRS FR-EXBOT-012 | Yes |
| AC-LC-02 | Khi `lifecycle_state='lp_rebalancing'`, bot KHÔNG được Light-Check Worker xử lý rebalance evaluation | Functional | UC §2; SRS states.md | Yes |
| AC-LC-03 | Pool Slot0 Cache stale > 5min → LCW skip tick hoàn toàn, không có mutation | Alternate | UC A1; SRS FR-EXBOT-093 | Yes |
| AC-LC-04 | Zero HL API calls trong toàn bộ light-check pipeline | Architectural | BR-EXBOT-003; SRS FR-EXBOT-012 | Yes |
| AC-LC-05 | `next_light_check_at` được batch UPDATE (1 statement/shard) cho TẤT CẢ eligible bots, kể cả bots bị skip | Functional | UC step 4; SRS FR-EXBOT-013 | Yes |
| AC-LC-06 | Idempotency: UNIQUE conflict trên `message_id` → skip, không process trùng | Functional | UC step 5; SRS FR-EXBOT-011 | Yes |
| AC-LC-07 | `drift_threshold` = `max($25, lpValueUsd × 3%)` với `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)` | Functional (formula) | UC step 9; SRS OQ-EXBOT-11 | **Partial** — OQ-EXBOT-11 vẫn Open trong SRS §9; formula có trong UC nhưng chưa được chốt trong SRS |
| AC-LC-08 | `range_boundary_near` fires khi `min(distToLower, distToUpper) / halfRange <= 0.9` (price-based USD) | Functional (formula) | UC step 9; SRS OQ-EXBOT-10 closed | Yes |
| AC-LC-09 | `funding_alert` fires khi 7d APR < -15%; primary source: `fundingApr7dPct` từ `funding_rolling_metrics` | Functional | UC step 9; SRS OQ-EXBOT-12 | **Blocked** — OQ-EXBOT-12 (7d APR aggregation formula) vẫn Open; `funding_rolling_metrics` không có trong ERD (I-03) |
| AC-LC-10 | Strategy engine gom ALL fired reasons vào `decision.reason[]`, enqueue 1 hedge-sync duy nhất | Functional | UC step 10; SRS FR-EXBOT-012 | Yes |
| AC-LC-11 | `range_out` được enqueue vào hedge-sync như các trigger khác; LCW KHÔNG set `lifecycle_state='lp_rebalancing'` | Functional | UC step 10; SRS FR-EXBOT-015 | Yes |
| AC-LC-12 | Circuit breaker `open` → hedge-sync bị suppress; stop monitoring (step 11) vẫn tiếp tục | Alternate | UC A2; SRS FR-EXBOT-014 | Yes |
| AC-LC-13 | `markPrice >= stop_price` → `stop_trigger_crossed_at` được set (write-once); `price-near-stop-audit` enqueued | Functional | UC step 11; SRS FR-EXBOT-032 | Yes |
| AC-LC-14 | HL Mark Price Cache stale > 120s → fallback `eth_price_usd`; widen near-stop band 2%→4%; freeze routine hedge-sync | Alternate | UC step 11; SRS OQ-EXBOT-17 closed | Yes |
| AC-LC-15 | `stop_replacing_started_at` overrun > 60s → SAFE_MODE atomic UPDATE (`status` + `lifecycle_state`) + `partial_repair` enqueued | Functional | UC step 12; SRS FR-EXBOT-033 | Yes |
| AC-LC-16 | Circuit breaker `half_open` → enqueue 1 probe hedge-sync (atomic claim `half_open_probe_used`) | Alternate | UC A3; SRS FR-EXBOT-040 | Yes |
| AC-LC-17 | LIMIT 500 + jitter: overflow → oldest-first catch-up qua successive ticks; no flood sau downtime | Non-functional | UC step 2; SRS FR-EXBOT-012 | Yes |
| AC-LC-18 | `queue_idempotency.expires_at` luôn được set = now+1min; không có cleanup job | Gap / NFR | UC step 5 (gap note) | Yes (gap confirmed) |

---

## 9. Business Rules áp dụng

| BR ID | Nội dung | Nguồn | Liên quan đến UC steps |
|---|---|---|---|
| BR-EXBOT-003 | HL weight = 0 trong toàn bộ light-check. Bất kỳ HL fetch nào là vi phạm kiến trúc. | SRS §BR | steps 1–13 |
| BR-EXBOT-005 | `stop_trigger_crossed_at` là write-once — một khi đã set, không được overwrite. | SRS §BR | step 11, A4 |

---

## 10. Issue Register, Dependencies, và Audit Summary

### §10.1 Issue Register

| Issue ID | Loại | Mức độ | Khu vực ảnh hưởng | Nguồn trace | Phát hiện | Tác động đến tester | Đề xuất fix / câu hỏi | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| I-01 | MISSING_INFO | Minor | FR Trace completeness | UC §7 FR Trace; SRS FR-EXBOT-012, FR-EXBOT-040 | UC §7 FR Trace liệt kê: `FR-EXBOT-013, 014, 015, 016, 023, 032, 033` — nhưng THIẾU `FR-EXBOT-012` (FR chính của light-check, mô tả toàn bộ logic worker bao gồm circuit breaker suppression, lp_rebalancing skip) và `FR-EXBOT-040` (Circuit Breaker State Machine, được test trong A2/A3). Hai FR này là cốt lõi của UC nhưng không xuất hiện trong trace. | Tester thiếu con đường trace ngược từ UC → FR để viết test traceability matrix. Test report sẽ thiếu link đến FR-012 và FR-040. | BA bổ sung FR-EXBOT-012 và FR-EXBOT-040 vào UC §7 FR Trace. | Open |
| I-02 | CROSS_SOURCE_CONFLICT | Major | US-007 vs UC/SRS lifecycle_state | US-EXBOT-007 AC-007-1; UC step 10; SRS FR-EXBOT-012, FR-EXBOT-015 | US-EXBOT-007 AC-007-1 viết: *"When the light-check detects range_out and hedge-sync triggers LP rebalance, **then the system sets lifecycle_state='lp_rebalancing'**"* — ngụ ý light-check set lifecycle_state. Nhưng UC step 10 và SRS FR-EXBOT-012 nói rõ: light-check KHÔNG set `lifecycle_state='lp_rebalancing'`, đó là trách nhiệm của hedge-sync handler downstream. Conflict này đã được sửa trong UC audit v2 nhưng US-EXBOT-007 vẫn dùng wording cũ. Vòng lặp migration 2026-07-04 update US-007 cho D1→Aurora PostgreSQL nhưng KHÔNG fix AC content. | Tester viết test case dựa trên US-007 AC-1 sẽ sai: họ sẽ kỳ vọng light-check set lifecycle_state, dẫn đến test fail sai do sai expectation. | BA update US-EXBOT-007 AC-007-1: "...then hedge-sync handler (downstream) sets lifecycle_state='lp_rebalancing'." | Open |
| I-03 | MISSING_INFO | Major | funding_alert formula / ERD | UC step 9; SRS OQ-EXBOT-12; SRS erd.md | UC step 9 viết: *"primary source `fundingApr7dPct` from `funding_rolling_metrics`"*. Nhưng bảng `funding_rolling_metrics` KHÔNG xuất hiện trong SRS ERD (`srs/erd.md`). ERD chỉ có `funding_daily_metrics` (với các field: `bot_id`, `bucket_day`, `funding_paid_usd`, `funding_received_usd`, `funding_net_usd`, `events_count`). Không có rolling aggregate pre-computed table nào trong ERD. | Tester không thể thiết kế test case cho `funding_alert` (pre-condition setup) vì không biết `funding_rolling_metrics` được tạo ở đâu, cập nhật như thế nào, và field schema là gì. Ngoài ra OQ-EXBOT-12 (7d APR aggregation formula) vẫn Open trong SRS §9, nghĩa là formula chưa được chốt. | (1) BA xác nhận `funding_rolling_metrics` là view/materialized view hay table riêng. (2) Thêm `funding_rolling_metrics` vào ERD hoặc ghi rõ nó là derived artifact. (3) Close OQ-EXBOT-12 trước khi test design. | Open |
| I-04 | UNCLEAR_INFO | Minor | Pool Slot0 Cache staleness policy | UC step 7; SRS FR-EXBOT-093; SRS OQ-EXBOT-09 | UC step 7 viết stale > 5min → fail-fast. SRS FR-EXBOT-093 viết: stale > **2× refresh interval** triggers forced refresh + warning log. Hai policy này có thể là cùng một điều kiện nếu refresh interval = 2.5min (2 × 2.5 = 5min), NHƯNG OQ-EXBOT-09 (ElastiCache Redis pool slot0 cache refresh interval) vẫn còn Open trong SRS §9 — interval chưa được xác định chính thức. Do đó, không thể xác nhận hai policy này có tương đương hay không. | Tester phải chọn threshold kiểm tra (5min hay 2×X?). Nếu interval thay đổi sau khi OQ-EXBOT-09 đóng, test case sẽ cần update. | Close OQ-EXBOT-09 với giá trị cụ thể. Confirm UC step 7 "5min" có phải là tham số cố định hay là derived từ FR-EXBOT-093. | Open |
| I-05 | MISSING_INFO | Minor | queue_idempotency cleanup | UC step 5 (gap note) | UC step 5 ghi rõ gap: "no scheduled cleanup job exists to purge expired rows — table will accumulate over time." Đây là gap đã được nhận diện trong UC. | Tester cần thiết kế test NFR cho bảng tích lũy (row count growth), nhưng không có acceptance criteria cho rate of growth hay cleanup SLA. | Dev team confirm kế hoạch thêm cleanup job. Nếu không có kế hoạch, ghi nhận là known technical debt với monitoring alert. | Open |
| I-06 | UNCLEAR_INFO | Minor | OQ-EXBOT-11 (lpValueUsd formula) status mismatch | SRS §9 OQ-EXBOT-11; UC step 9; audit v2 AC-LC-07 | SRS §9 OQ-EXBOT-11 vẫn đánh dấu **Open**: *"lpValueUsd formula... pending zen confirm"*. Nhưng UC step 9 đã ghi công thức cụ thể: `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`; và audit v2 đã tạo AC-LC-07 dựa trên công thức này và mark test-ready. Conflict về trạng thái: UC/audit v2 đã tiến trước SRS. | Nếu BA/zen cuối cùng close OQ-EXBOT-11 với công thức khác, AC-LC-07 và các test case liên quan phải update lại. | BA close OQ-EXBOT-11 trong SRS với công thức từ UC step 9, hoặc cập nhật UC nếu công thức được chỉnh sửa. | Open |
| I-07 | MISSING_INFO | Minor | F-01 flow diagram thiếu step 11 | SRS flows.md F-01; UC step 11 | F-01 flow diagram trong `srs/flows.md` mô tả: EventBridge Scheduler → Scan Worker → Light-Check Worker → Hedge-Sync. Diagram có chú thích `MDO as "ElastiCache Redis"` (Pool Slot0 Cache) cho step 7, nhưng KHÔNG có bước nào hiển thị việc đọc HL Mark Price Cache (ElastiCache Redis) tại step 11 hay việc enqueue `price-near-stop-audit`. Toàn bộ stop monitoring logic không có trong flow diagram. | Tester dựa vào F-01 để hiểu luồng sẽ bỏ sót stop trigger path. Việc không có diagram cho stop monitoring tăng nguy cơ thiếu test coverage cho I-02 path. | BA bổ sung step 11 (HL Mark Price Cache read) và `price-near-stop-audit` enqueue vào F-01, hoặc tạo riêng một diagram cho stop monitoring sub-flow. | Open |
| I-08 | MISSING_INFO | Minor | US-EXBOT-008 không được update với arc-migration | userstories/us-008.md; SRS FR-EXBOT-040 | US-EXBOT-008 (Circuit Breaker) không có changelog entry 2026-07-04 (arc-migration). Tuy nhiên, nội dung circuit breaker (state transitions, failure counting, probe logic) là platform-agnostic — không phụ thuộc D1/CloudflareWorkers/ElastiCache Redis. Do đó, đây là minor gap về traceability chứ không phải functional conflict. | Tester biết US-008 chưa được xác nhận qua arc-migration checklist. | BA xác nhận US-008 không cần update hoặc thêm changelog note "platform-agnostic, no change required for arc-migration". | Open |

### §10.2 Dependencies & Blockers

| Dependency | Loại | Ảnh hưởng | Status |
|---|---|---|---|
| OQ-EXBOT-09 (Pool Slot0 Cache refresh interval) | Open Question → Blocks | Test case cho Pool Slot0 Cache staleness boundary value không thể confirm threshold | Open |
| OQ-EXBOT-11 (lpValueUsd formula confirmation) | Open Question → Blocks | AC-LC-07 sẽ cần update nếu zen đề xuất formula khác | Open |
| OQ-EXBOT-12 (7d APR aggregation formula) | Open Question → Hard Blocks | `funding_alert` test cases KHÔNG thể thiết kế đầy đủ cho đến khi OQ-12 được close VÀ `funding_rolling_metrics` ERD được định nghĩa | Open |
| `funding_rolling_metrics` ERD definition | Missing artifact → Hard Blocks | Không có schema → không thể setup test data cho funding_alert | Open |
| US-EXBOT-007 AC-007-1 conflict fix | BA action needed | Nếu không fix, tester viết expected result sai cho lp_rebalancing test cases | Open |

### §10.3 Audit Summary — Scoring

| Khu vực đánh giá | Điểm tối đa | Phát hiện chính | Điểm đạt | Ghi chú |
|---|---|---|---|---|
| **A1 — Completeness of requirement coverage** | 25 | I-01 (FR Trace thiếu FR-012/040, Minor), I-07 (F-01 diagram thiếu step 11, Minor) | 22 | Nội dung UC đủ, FR trace và flow diagram chưa đầy đủ |
| **A2 — Internal & cross-source consistency** | 25 | I-02 (US-007 AC-1 conflict với UC step 10, **Major**) | 18 | 1 Major conflict vẫn chưa được giải quyết trong US-007 sau migration |
| **A3 — Clarity & testability** | 20 | I-04 (staleness threshold ambiguous, Minor), I-06 (OQ-11 status mismatch, Minor) | 16 | Hầu hết các formula và ACs đã đủ rõ; 2 minor ambiguity |
| **A4 — Traceability & evidence** | 15 | I-03 (funding_rolling_metrics thiếu trong ERD, **Major** → Hard Blocks test design) | 9 | Hard Blocker cho funding_alert test design — không có ERD + OQ-12 còn Open |
| **A5 — Completeness of preconditions & postconditions** | 15 | I-05 (queue_idempotency cleanup gap, Minor, đã ghi nhận trong UC), I-08 (US-008 migration check) | 12 | Preconditions/postconditions đủ; minor gaps đã được noted trong UC |
| **Tổng** | **100** | | **77** | |

**Verdict: CONDITIONALLY READY**

UC-EXBOT-light-check có đủ nội dung để thiết kế phần lớn test cases (các AC từ AC-LC-01 đến AC-LC-18, ngoại trừ funding_alert). Tuy nhiên có 2 điểm cần hành động trước khi test design hoàn chỉnh:

**Blockers trước test design đầy đủ:**
1. **[Hard Blocker] I-03** — `funding_rolling_metrics` chưa có ERD schema và OQ-EXBOT-12 (7d APR formula) vẫn Open. Test case cho `funding_alert` (AC-LC-09) không thể thiết kế pre-condition đúng cho đến khi 2 việc này được giải quyết.
2. **[Major] I-02** — US-EXBOT-007 AC-007-1 vẫn nói "light-check sets lifecycle_state='lp_rebalancing'" — trái với UC step 10 và SRS FR-EXBOT-012/015. Tester cần được hướng dẫn follow UC + SRS, không follow US-007 AC-1.

**Recommendation:** Tiến hành thiết kế test cases cho tất cả AC ngoại trừ AC-LC-09 (`funding_alert`). Đồng thời, BA cần: (1) update US-EXBOT-007 AC-007-1; (2) định nghĩa `funding_rolling_metrics` trong ERD hoặc ghi rõ là derived artifact; (3) close OQ-EXBOT-12; (4) bổ sung FR-EXBOT-012 và FR-EXBOT-040 vào UC §7 FR Trace.

---

## Bảng mã viết tắt (Reference Code Glossary)

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement — specific behavior requirement for ExBot components. FR-EXBOT-012 is the main light-check FR. | `srs/spec.md` §2 |
| BR-EXBOT-* | Business Rule — immutable invariant. BR-EXBOT-003: zero HL API calls in light-check. | `srs/spec.md` §Business Rules |
| OQ-EXBOT-* | Open Question — unresolved question in SRS. Open = pending decision; Closed = resolved with specific answer. | `srs/spec.md` §9 |
| AC-LC-* | Acceptance Criteria for UC-EXBOT-light-check. Created by QC during audit phases. | This document + prior audited reports |
| SIWE | Sign-In With Ethereum — wallet-signature authentication method. Not directly used in light-check flow. | Industry standard |
| LP | Liquidity Provider — a Uniswap V3 position owned by the bot. Each LP position is wrapped by BnzaExVault; raw uncollected fees are never surfaced to end-users directly. | `srs/spec.md` §LP |
| SQS | Simple Queue Service — AWS managed message queue. Replaces Cloudflare Queues after arc-migration. | AWS; `srs/spec.md` |
| Lambda | AWS Lambda — serverless function runtime. Replaces Cloudflare Workers after arc-migration. | AWS; `srs/spec.md` §1.1 |
| ElastiCache Redis | AWS managed Redis cluster — hosts Pool Slot0 Cache and HL Mark Price Cache. Replaces Cloudflare Durable Objects (MarketDataDO, HlMarkDO) after arc-migration. | `srs/spec.md` FM-XB-03 |
| Aurora PostgreSQL | AWS Aurora PostgreSQL Serverless v2 — replaces Cloudflare D1 (SQLite). Source of truth for bot state. | `srs/spec.md` FM-XB-01 |
| EventBridge Scheduler | AWS EventBridge Scheduler — replaces Cloudflare Cron Worker. Triggers bot-scan every 1 minute. | `srs/spec.md` FM-XB-04 |
| HL | Hyperliquid — decentralized perpetual exchange. ExBot manages short hedge positions on HL. Light-check makes zero HL API calls (BR-EXBOT-003). | Industry; project context |
| KMS | Key Management Service — AWS service for managing encryption keys. Used for agent key signing in HL Adapter. | AWS; `srs/spec.md` FM-XB-05 |
