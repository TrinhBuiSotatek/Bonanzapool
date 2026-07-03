# Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC ID:** UC-EXBOT-light-check  
**Tên feature:** Execute Periodic Light-Check  
**Ngày tạo:** 2026-07-03  
**Người viết:** QC UC Read Exbot Agent  
**Version:** v2  
**Lý do cập nhật:** Cập nhật Issue Register với câu trả lời từ BA/Tech Lead/code (10/12 câu hỏi open trong v1 đã được giải đáp). Tính lại điểm và verdict.

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-light-check mô tả quy trình định kỳ (5 phút/lần) mà hệ thống ExBot dùng để đánh giá từng bot đang hoạt động xem có cần điều chỉnh hedge, cân bằng lại LP, hay phát hiện stop trigger không — mà **không thực hiện bất kỳ lời gọi API nào đến Hyperliquid (HL weight = 0)**. Đây là luồng fan-out trung tâm của ExBot: Cron Worker → bot-scan queue → Scan Worker → light-check queue → Light-Check Worker, kết thúc bằng việc enqueue sang `hedge-sync`, `price-near-stop-audit`, hoặc `partial_repair` queue tùy tình huống.

Điều kiện cần: bot có `status='active'` và `next_light_check_at <= now`, và `lifecycle_state` không thuộc `lp_rebalancing` hoặc `lp_closing`, và `status != 'paused'`. Các bot ở trạng thái `hedge_stopped_cooldown` vẫn chạy light-check bình thường nhưng không enqueue hedge-sync.

Hệ thống đọc hai nguồn: D1 (`bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs`) và `MarketDataDO` (`sqrtPriceX96`, `currentTick`). Từ đó tính `lpEthAmount` qua công thức Uniswap V3 TickMath + LiquidityAmounts (tính local, không RPC), sau đó đánh giá danh sách `RebalanceReason[]` theo quy tắc 3-way price split (v5.2.6 X-5): `uniPoolPrice` cho drift valuation, `hlMarkPrice` cho stop trigger, `hlOraclePrice` cho margin.

**Cập nhật v2:** `hlMarkPrice` source đã được xác nhận — primary: `HlMarkDO.markPriceUsd`; fallback: `bot_runtime_state.eth_price_usd` khi DO unreachable. Stale threshold = 120s → widen near-stop band 2%→4% + freeze hedge-sync. Công thức `range_boundary_near` (price-based, `nearestFraction <= 0.9`), `lpValueUsd` (`max(0, lpEthAmount × currentPriceUsd)`), và 7d funding APR (`fundingApr7dPct` từ `funding_rolling_metrics`) đều đã được confirm từ code.

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| BR-EXBOT-* | Business Rule — quy tắc nghiệp vụ bắt buộc của ExBot | SRS §4 |
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng ExBot | FRD §4 / SRS §2 |
| AC-EXBOT-* | Acceptance Criteria — tiêu chí nghiệm thu từ user story | User stories |
| OQ-EXBOT-* | Open Question — câu hỏi mở chưa được giải đáp | SRS §9 |
| US-EXBOT-* | User Story — câu chuyện người dùng của ExBot | userstories/ |
| HL | Hyperliquid — sàn giao dịch perp on-chain nơi ExBot đặt lệnh hedge short | FRD §2 |
| D1 | Cloudflare D1 — cơ sở dữ liệu SQLite phân tán lưu trạng thái bot | FRD §4.9 |
| DO | Durable Object — đối tượng stateful của Cloudflare Workers (HLRateLimitDO, UserLockDO, MarketDataDO, HlMarkDO) | FRD §4.10 |
| cloid | Client Order ID — mã định danh lệnh phía client, deterministic để idempotency | FRD §4.3 |
| INV-STOP | Invariant: protected stop replacement protocol — thay stop phải dùng thủ tục bảo vệ, không cancel-then-place trực tiếp | SRS FR-EXBOT-035 |
| SAFE_MODE | Trạng thái an toàn của bot — chặn toàn bộ mutation, chỉ cho phép đọc/alert/recovery | SRS FR-EXBOT-050 |
| LP | Liquidity Provider position — vị thế thanh khoản Uniswap V3 được wrap thành NFT (tokenId) trong BnzaExVault | FRD §1 |
| RPC | Remote Procedure Call — lời gọi đến blockchain node để đọc on-chain data | (industry term) |
| KMS | AWS Key Management Service — dịch vụ sinh và lưu trữ khóa, khóa riêng không bao giờ rời KMS | FRD §4.9 FR-EXBOT-080 |

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check | 2026-06-20 (cập nhật lần cuối) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-20 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò | Ghi chú |
|---|---|---|---|
| `usecases/uc-light-check.md` | 2026-06-20 | UC | File chính được audit |
| `srs/spec.md` | 2026-06-29 | SRS (source of truth) | FR-EXBOT-011, 012, 013, 014, 015, 016, 032, 033 |
| `srs/states.md` | 2026-06-18 | State diagram | Bot lifecycle, circuit breaker, margin status |
| `srs/flows.md` | 2026-06-29 | Flow diagram | F-01 Queue Fan-Out |
| `srs/erd.md` | 2026-06-29 | ERD | bots, bot_runtime_state, hedge_legs, circuit_breakers, queue_idempotency |
| `frd.md` | 2026-06-29 | FRD | FR-EXBOT-011–016, 023, 032, 033 |
| `userstories/us-005.md` | 2026-06-12 | User Story | AC-EXBOT-005-1..4 |
| `userstories/us-006.md` | 2026-06-12 | User Story | AC-EXBOT-006-1..4 |
| `userstories/us-007.md` | 2026-06-12 | User Story | AC-EXBOT-007-1..4 |
| `userstories/us-008.md` | 2026-06-12 | User Story | AC-EXBOT-008-1..4 |
| `usecases/index.md` | 2026-06-29 | Index | Xác nhận linked stories |
| `userstories/index.md` | 2026-06-29 | Index | Xác nhận FR trace |
| `docs/BA/qc-notes-temp.md` | 2026-07-03 | BA/Tech Lead answers | Nguồn câu trả lời cho I-01 đến I-12 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Light-check là vòng lặp giám sát định kỳ trung tâm của ExBot. Mục tiêu là đánh giá liên tục 10.000 bot ở chu kỳ 5 phút mà không tiêu tốn bất kỳ HL API rate-limit nào (BR-EXBOT-003). Kết quả của mỗi lần light-check là quyết định fan-out: enqueue hedge-sync nếu cần điều chỉnh delta, enqueue price-near-stop-audit nếu phát hiện stop trigger, enqueue partial_repair nếu phát hiện overrun stop replace, hoặc không làm gì nếu bot đang ổn.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Cron → Scan fan-out | Cron Worker (1 phút) gọi `chunkSendBatch` đến bot-scan queue; Scan Worker query D1 và gửi message per-bot đến light-check queue; batch-update `next_light_check_at` cho mọi bot eligible kể cả bị skip | UC §3 steps 1–4; SRS FR-EXBOT-012, 013 |
| Idempotency check | Light-Check Worker insert `message_id` vào `queue_idempotency` (state='started', expires_at=now+1min); UNIQUE conflict → skip | UC §3 step 5; SRS FR-EXBOT-011 |
| Đọc D1 + MarketDataDO | Đọc `bot_runtime_state`, `lifecycle_state`, `hedge_legs`; đọc `sqrtPriceX96`, `currentTick` từ MarketDataDO; fail-fast nếu DO stale > 5 phút | UC §3 steps 6–7 |
| Tính `lpEthAmount` | TickMath + LiquidityAmounts local, không RPC | UC §3 step 8; SRS FR-EXBOT-012 |
| Đánh giá RebalanceReason[] | 7 reason: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback | UC §3 step 9; SRS FR-EXBOT-023 |
| Fan-out hedge-sync | Engine gom tất cả reasons vào `decision.reason[]` và enqueue 1 hedge-sync duy nhất (kể cả khi range_out kết hợp với reasons khác); circuit != open bắt buộc | UC §3 step 10; SRS FR-EXBOT-015 |
| Stop trigger detection | `markPrice >= stop_price` → set `stop_trigger_crossed_at` (guarded) + enqueue price-near-stop-audit; `hlMarkPrice` = `HlMarkDO.markPriceUsd` (primary), fallback `eth_price_usd` khi stale > 120s → widen near-stop band | UC §3 step 11; SRS FR-EXBOT-032 |
| Stop replace overrun check | `stop_replacing_started_at IS NOT NULL AND age > 60s` → set `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` atomic trong 1 UPDATE → enqueue partial_repair | UC §3 step 12; SRS FR-EXBOT-033 |
| Finalize idempotency | Update `queue_idempotency.state='succeeded'` | UC §3 step 13 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Xử lý hedge-sync worker | UC này chỉ enqueue; logic điều chỉnh delta là `uc-hedge-sync` | Tester cần đọc uc-hedge-sync để test downstream |
| Xử lý price-near-stop-audit worker | Ngoài scope UC này | — |
| Xử lý partial_repair worker | Ngoài scope UC này | — |
| Deep-audit backstop | `uc-deep-audit` là backstop phát hiện stuck markers, không phải light-check | Dependency cần theo dõi |
| Cleanup job cho `queue_idempotency` | Dev team cần thêm scheduled purge — ngoài scope UC | Minor concern cho môi trường test |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn | Nguồn |
|---|---|---|---|---|
| Cron Worker (1 min) | System | Khởi động fan-out mỗi 1 phút | Chỉ enqueue bot-scan; không đọc/ghi D1 trực tiếp | UC §1 |
| Scan Worker | System | Query D1 lấy danh sách bot eligible; enqueue light-check per-bot; batch-update `next_light_check_at` cho mọi bot kể cả bị skip | Đọc/ghi D1 state_db_shard | UC §1, §3 steps 1–4 |
| Light-Check Worker | System | Xử lý từng message light-check: đọc D1 + MarketDataDO, tính toán, fan-out | Ghi D1 (queue_idempotency, lifecycle_state, stop_trigger_crossed_at, bots.status+lifecycle_state atomic); enqueue đến hedge-sync / price-near-stop-audit / partial_repair queues; KHÔNG gọi HL API | UC §1; SRS BR-EXBOT-003 |
| D1 (state_db_shard) | System | Lưu trạng thái bot runtime, hedge legs, circuit breaker | Read/write by Light-Check Worker | UC §1, §3 |
| MarketDataDO | System | Cache pool slot0 (`sqrtPriceX96`, `currentTick`) | Read-only by Light-Check Worker; fail-fast nếu stale > 5 phút | UC §3 step 7; SRS FR-EXBOT-093 |
| HlMarkDO | System | Cache HL mark price (`markPriceUsd`); primary source cho stop trigger evaluation | Read-only; fallback sang `bot_runtime_state.eth_price_usd` khi stale > 120s | UC §3 step 11; confirmed Tech Lead |

**Nhận xét readiness:** Actor và vai trò đủ rõ cho test logic. Light-Check Worker là actor chính với ràng buộc tuyệt đối HL weight = 0. `HlMarkDO` đã được xác nhận là primary source cho stop trigger evaluation (v2). Không có actor người dùng (no UI) — đúng scope.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot `status='active'` | Yes | UC §2; SRS FR-EXBOT-012 |
| 2 | `next_light_check_at <= now` | Yes | UC §2; SRS FR-EXBOT-012 |
| 3 | `lifecycle_state NOT IN ('lp_rebalancing', 'lp_closing')` (cho Light-Check Worker processing; Scan Worker vẫn update `next_light_check_at` cho các bot này) | Yes | UC §2; SRS FR-EXBOT-012 |
| 4 | `status != 'paused'` | Yes | UC §2; SRS FR-EXBOT-003 |
| 5 | Bots với `lifecycle_state='hedge_stopped_cooldown'` KHÔNG bị skip — light-check chạy bình thường, chỉ hedge-sync bị suppressed | Yes | UC §2 note; SRS states.md |
| 6 | `MarketDataDO` có dữ liệu hợp lệ (stale ≤ 5 phút) — nếu stale hoặc unreachable → fail-fast, skip tick | Yes | UC §3 step 7; SRS FR-EXBOT-093 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Không cần action | Không có message enqueued; `queue_idempotency.state='succeeded'`; `next_light_check_at` đã được batch-update | UC §5; step 13 |
| Hedge-sync cần | `hedge-sync` message enqueued với `{botId, reasons, stateVersion}`; `queue_idempotency.state='succeeded'` | UC §3 step 10; SRS FR-EXBOT-012 |
| range_out phát hiện (+ possible other reasons) | Engine enqueue 1 hedge-sync duy nhất với tất cả reasons; `lifecycle_state='lp_rebalancing'` set downstream bởi hedge-sync handler | UC §3 step 10; confirmed code |
| Stop trigger phát hiện | `hedge_legs.stop_trigger_crossed_at` được set (nếu NULL); `price-near-stop-audit` enqueued; KHÔNG enqueue hedge-sync | UC §3 step 11; SRS FR-EXBOT-032 |
| Stop replace overrun | `bots.status='safe_mode'` VÀ `bots.lifecycle_state='safe_mode'` set atomic trong 1 UPDATE (trước khi enqueue); `partial_repair(reason='stop_replacing_overrun')` enqueued | UC §3 step 12; SRS FR-EXBOT-033; confirmed code |
| Duplicate message | Light-check worker exit ngay sau UNIQUE conflict trên `queue_idempotency` | UC §3 step 5; SRS FR-EXBOT-011 |
| `next_light_check_at` | Batch-update: `now + 5min + jitter(±45s)`, 1 statement per shard, cho MỌI bot eligible kể cả bị skip | UC §3 step 4; SRS FR-EXBOT-013; confirmed code |
| HL API call count | = 0 (invariant) | UC §5; SRS BR-EXBOT-003 |
| MarketDataDO stale | Light-check skip hoàn toàn — không evaluate trigger nào; không dùng stale data | SRS FR-EXBOT-093; confirmed code |

---

## §F.1 — Function / Operation & Data Object Inventory

| # | Item | Loại | Trigger / Source | Input | Output / Effect | Data Objects & Fields | Enum / State set | Events / Messages | Source trace |
|---|---|---|---|---|---|---|---|---|---|
| F1-01 | Cron fan-out to bot-scan | Operation | Cron 1 min | — | Batch messages to bot-scan queue via `chunkSendBatch` | — | — | — | UC §3 step 1; SRS FR-EXBOT-012 |
| F1-02 | Scan Worker query eligible bots | Operation | bot-scan queue message | D1: `bots` table | List of botIds eligible for light-check | `bots.status`, `bots.next_light_check_at`, `bots.lifecycle_state` | `status='active'`; `next_light_check_at <= now`; `LIMIT 500`; jitter ±45s hash(botId) phân tán đều — steady state không overflow | — | UC §3 step 2; confirmed code |
| F1-03 | Scan Worker enqueue per-bot to light-check queue | Operation | Result of F1-02 | List of botIds (chỉ bots không bị skip bởi lifecycle filter) | Messages in light-check queue via `chunkSendBatch` | — | — | — | UC §3 step 3; SRS FR-EXBOT-010 |
| F1-04 | Batch-update `next_light_check_at` | Operation | After enqueue | botIds per shard (mọi bot eligible kể cả lp_rebalancing/lp_closing) | `next_light_check_at = now + 5min + jitter(±45s)` written to D1 (1 stmt/shard) | `bots.next_light_check_at` | — | — | UC §3 step 4; SRS FR-EXBOT-013; confirmed code |
| F1-05 | Idempotency insert | Operation | Light-Check Worker start | `message_id` | `queue_idempotency` row inserted với `state='started'`, `expires_at=now+1min`; UNIQUE conflict → skip | `queue_idempotency.message_id`, `queue_idempotency.state`, `queue_idempotency.expires_at` | `state`: started / succeeded / failed | — | UC §3 step 5; SRS FR-EXBOT-011 |
| F1-06 | Read D1 bot state | Operation | Light-Check Worker | `botId` | Runtime state loaded from D1 | `bot_runtime_state.last_known_hl_short_size`, `bots.lifecycle_state`, `hedge_legs.stop_price`, `hedge_legs.margin_status`, `hedge_legs.circuit_state`, `hedge_legs.stop_replacing_started_at` | — | — | UC §3 step 6 |
| F1-07 | Read MarketDataDO | Operation | Light-Check Worker | `botId` (pool context) | `sqrtPriceX96`, `currentTick`; fail-fast nếu snapshot stale > 5 phút hoặc unreachable → throw, skip tick | MarketDataDO cache fields | stale threshold = 5 phút | — | UC §3 step 7; SRS FR-EXBOT-093; confirmed code |
| F1-08 | Compute `lpEthAmount` | Operation | After F1-07 | `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick`, `wethIndex` | `lpEthAmount` (BigDecimal) | `positions.liquidity`, `positions.tick_lower`, `positions.tick_upper`, `positions.weth_index` | — | — | UC §3 step 8; SRS FR-EXBOT-020 |
| F1-09 | Evaluate RebalanceReason[] | Operation | After F1-08 | D1 state + MarketDataDO | `RebalanceReason[]` list | `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.lp_value_usd`, `hedge_legs.margin_status` | `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback` | — | UC §3 step 9; SRS FR-EXBOT-023 |
| F1-10 | Fan-out: engine gom reasons → 1 hedge-sync | Operation | Any non-empty RebalanceReason[] AND `circuit_state != 'open'` | `botId`, `decision.reason[]` (tất cả reasons), `stateVersion` | 1 hedge-sync message enqueued; `lifecycle_state='lp_rebalancing'` set downstream bởi hedge-sync handler | `bot_runtime_state.state_version`, `circuit_breakers.state` | `circuit_breakers.state`: closed / open / half_open | — | UC §3 step 10; confirmed code |
| F1-11 | Fan-out: circuit half_open probe | Operation | `circuit_state='half_open'` | `hedge_leg_id` | Atomically claim `half_open_probe_used`; enqueue ONE probe hedge-sync | `circuit_breakers.half_open_probe_used`, `circuit_breakers.state` | `half_open_probe_used`: 0 → 1 | — | UC §4 A2; SRS FR-EXBOT-040 |
| F1-12 | Read HlMarkDO for stop trigger | Operation | Each light-check pass (step 11) | `botId` (pool context) | `markPriceUsd`; fallback sang `bot_runtime_state.eth_price_usd` nếu stale > 120s → widen near-stop band 2%→4% | HlMarkDO.markPriceUsd, `bot_runtime_state.eth_price_usd` | stale threshold = 120s | — | UC §3 step 11; confirmed Tech Lead |
| F1-13 | Stop trigger detection | Operation | Each light-check pass | `hedge_legs.stop_price`, `hlMarkPrice` (từ F1-12) | Set `stop_trigger_crossed_at` (guarded, only if NULL); enqueue `price-near-stop-audit` | `hedge_legs.stop_trigger_crossed_at` | write-once (BR-EXBOT-005) | price-near-stop-audit enqueued | UC §3 step 11; SRS FR-EXBOT-032 |
| F1-14 | Stop replace overrun detection | Operation | Each light-check pass | `hedge_legs.stop_replacing_started_at`, `now` | If set AND age > 60s: set `bots.status='safe_mode'` AND `lifecycle_state='safe_mode'` atomic 1 UPDATE; enqueue `partial_repair(reason='stop_replacing_overrun')` | `hedge_legs.stop_replacing_started_at`, `bots.lifecycle_state`, `bots.status` | `lifecycle_state`: active → safe_mode; `status`: active → safe_mode | — | UC §3 step 12; SRS FR-EXBOT-033; confirmed code |
| F1-15 | Finalize idempotency | Operation | After all fan-out logic | `queue_idempotency` row | Update `state='succeeded'` | `queue_idempotency.state` | succeeded | — | UC §3 step 13 |
| F1-D1 | `bots` table | Data Object | D1 state_db_shard | — | — | `id`, `status`, `lifecycle_state`, `next_light_check_at` | `status`: active/paused/closing/closed/safe_mode/error; `lifecycle_state`: 18 states | — | SRS ERD; states.md |
| F1-D2 | `bot_runtime_state` table | Data Object | D1 hot state | — | — | `bot_id`, `state_version`, `last_known_hl_short_size`, `lp_value_usd`, `eth_price_usd`, `lp_eth_amount`, `current_tick`, `sqrt_price_x96` | — | — | SRS ERD |
| F1-D3 | `hedge_legs` table | Data Object | D1 | — | — | `stop_price`, `margin_status`, `circuit_state`, `stop_trigger_crossed_at`, `stop_replacing_started_at`, `stop_distance_pct` | `margin_status`: ok/warning/critical; `circuit_state`: closed/open/half_open | — | SRS ERD |
| F1-D4 | `circuit_breakers` table | Data Object | D1 | — | — | `state`, `half_open_probe_used`, `reset_at`, `failure_count` | `state`: closed/open/half_open | — | SRS ERD |
| F1-D5 | `queue_idempotency` table | Data Object | D1 | — | — | `message_id`, `kind`, `state`, `bot_id`, `created_at`, `expires_at` (TTL=1min, không NULL) | `state`: started/succeeded/failed/retryable | — | SRS ERD; confirmed code |
| F1-D6 | `funding_rolling_metrics` table | Data Object | D1 | — | — | `fundingApr7dPct` | — | — | confirmed code; SRS FR-EXBOT-012 |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Item (từ F.1) | Trạng thái / Preconditions | Validation / Business Rule | Dependencies | Messages / Events | Nguồn |
|---|---|---|---|---|---|
| F1-01 Cron fan-out | Cron schedule: mỗi 1 phút | Tất cả batch calls PHẢI dùng `chunkSendBatch()` — gọi `queue.sendBatch()` trực tiếp bị cấm | — | — | UC §3 step 1; SRS FR-EXBOT-010 |
| F1-02 Scan query | `bots.status='active'` AND `next_light_check_at <= now` | LIMIT 500 per shard; bot với `lifecycle_state IN ('lp_rebalancing','lp_closing')` hoặc `status='paused'` bị lọc ra — KHÔNG enqueue light-check, nhưng vẫn được update `next_light_check_at` trong F1-04 | D1 shard | — | UC §3 step 2; SRS FR-EXBOT-012; confirmed code |
| F1-02 LIMIT 500 | steady state | Jitter ±45s deterministic theo `hash(botId)` phân tán bots đều trong 5 phút → steady state không bao giờ overflow. Sau downtime, bots vượt LIMIT 500 xử lý ở cron tick tiếp theo (oldest first) — không mất bot | — | — | confirmed code |
| F1-04 Batch-update | Sau F1-03 | `next_light_check_at = now + 5min + random(−45s, +45s)`; 1 UPDATE per shard cho MỌI bot eligible (kể cả `lp_rebalancing`, `lp_closing`, `paused`) — không per-bot (NFR-EXBOT-005) | D1 shard | — | SRS FR-EXBOT-013; confirmed code |
| F1-05 Idempotency insert | Đầu mỗi Light-Check Worker execution | `queue_idempotency.message_id` UNIQUE constraint; `expires_at = now + 1min` (KHÔNG NULL); UNIQUE conflict = duplicate delivery → return ngay | `queue_idempotency` table | — | UC §3 step 5; SRS FR-EXBOT-011; confirmed code |
| F1-07 Read MarketDataDO | Sau F1-06 | Fail-fast: nếu snapshot stale > 5 phút HOẶC DO unreachable → throw ngay, skip tick hoàn toàn. Không dùng stale data, không chờ refresh. Zero HL calls | MarketDataDO (FR-EXBOT-093) | — | SRS FR-EXBOT-093; confirmed code |
| F1-08 Compute lpEthAmount | Sau F1-07 | Dùng Uniswap V3 AMM formula. Cấm dùng `depositedToken − withdrawnToken + collectedFees`. `wethIndex` đọc từ `positions.weth_index`, KHÔNG hardcode | `positions.weth_index`, `positions.tick_lower`, `positions.tick_upper` | — | SRS FR-EXBOT-020; FR-EXBOT-021 |
| F1-09 drift_threshold | — | `deltaErrorUsd > max($25, lpValueUsd × 3%)`. `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)`. `deltaErrorUsd = |targetShortEth − actualShortEth| × uniPoolPrice`. Dùng `uniPoolPrice` từ `sqrtPriceX96` via MarketDataDO — KHÔNG dùng hlMarkPrice hay hlOraclePrice | `bot_runtime_state.lp_value_usd` | — | SRS FR-EXBOT-012; confirmed code |
| F1-09 range_boundary_near | — | Price-based USD. Công thức: `nearestFraction = min(distToLower, distToUpper) / halfRange`. Fires khi `nearestFraction <= 0.9` (default). Ví dụ range $3,000–$3,400: trigger khi giá ≤ $3,020 hoặc ≥ $3,380 | MarketDataDO (currentPriceUsd) | — | confirmed code |
| F1-09 funding_alert | — | Fires khi 7d funding APR < −15%. Primary source: `fundingApr7dPct` từ `funding_rolling_metrics` — đọc trực tiếp. Fallback: `fundingRate × 8760` (annualize per-hour rate) | `funding_rolling_metrics` | — | confirmed code |
| F1-10 mixed reasons fan-out | Precondition: RebalanceReason[] non-empty | Engine gom tất cả reasons vào `decision.reason[]` và enqueue 1 hedge-sync duy nhất. Light-check KHÔNG tự set `lifecycle_state='lp_rebalancing'` — đó là việc của hedge-sync handler downstream | `circuit_breakers.state != 'open'` | — | confirmed code |
| F1-12 HlMarkDO staleness | Mỗi light-check pass | Primary: `HlMarkDO.markPriceUsd`. Khi stale > 120s: fallback = `bot_runtime_state.eth_price_usd` (last-known) + widen near-stop band 2%→4% + freeze hedge-sync. Detection latency tối đa ~7 phút | `bot_runtime_state.eth_price_usd` | — | confirmed Tech Lead |
| F1-13 Stop trigger | Mỗi pass; stop monitoring luôn chạy kể cả circuit open | `markPrice >= stop_price` → set `stop_trigger_crossed_at` chỉ nếu NULL (BR-EXBOT-005 — write-once). Enqueue price-near-stop-audit. KHÔNG enqueue hedge-sync | `hedge_legs.stop_trigger_crossed_at` | price-near-stop-audit enqueued | UC §3 step 11; SRS FR-EXBOT-032 |
| F1-14 Stop replace overrun | Mỗi pass | `stop_replacing_started_at IS NOT NULL AND age > 60s` → set `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` atomically trong 1 UPDATE, TRƯỚC KHI enqueue `partial_repair(reason='stop_replacing_overrun')`. Tester phải assert cả 2 fields | `hedge_legs.stop_replacing_started_at` | partial_repair enqueued | UC §3 step 12; SRS FR-EXBOT-033; confirmed code |

---

## §F.3 — Functional Logic & Workflow Decomposition

### F3.1 — Happy Path: Scan + Light-Check không cần action

| Bước | Actor | Trigger / Hành động | System response (happy path) | Alternate path | Exception path | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Cron Worker | Cron 1 min | Gọi `chunkSendBatch` tới bot-scan queue với shard windows | — | Cron lỗi → không có message → batch delayed đến chu kỳ sau | UC §3 step 1 |
| 2 | Scan Worker | Nhận bot-scan message | Query D1: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500`; lọc bỏ `lp_rebalancing`, `lp_closing`, `paused` | Không có bot eligible → không enqueue gì | D1 unreachable → không update | UC §3 step 2 |
| 3 | Scan Worker | Sau query | Enqueue per-bot messages tới light-check queue qua `chunkSendBatch` | — | — | UC §3 step 3 |
| 4 | Scan Worker | Sau enqueue | Batch-update `next_light_check_at = now + 5min + jitter(±45s)` cho MỌI bot eligible — 1 stmt/shard | — | — | UC §3 step 4 |
| 5 | Light-Check Worker | Nhận light-check message | Insert `message_id` vào `queue_idempotency` (state='started', expires_at=now+1min) | UNIQUE conflict → skip (duplicate delivery) | — | UC §3 step 5 |
| 6 | Light-Check Worker | Sau idempotency OK | Đọc D1: `bot_runtime_state`, `lifecycle_state`, `hedge_legs` fields | — | — | UC §3 step 6 |
| 7 | Light-Check Worker | Sau đọc D1 | Đọc MarketDataDO: `sqrtPriceX96`, `currentTick` (zero HL calls) | — | Stale > 5 phút hoặc unreachable → throw, skip tick hoàn toàn | UC §3 step 7 |
| 8 | Light-Check Worker | Sau đọc DO | Tính `lpEthAmount` local: TickMath + LiquidityAmounts (BigDecimal) | — | — | UC §3 step 8 |
| 9 | Light-Check Worker | Sau tính | Đánh giá `RebalanceReason[]` từ D1 + MarketDataDO state | — | — | UC §3 step 9 |
| 10 | Light-Check Worker | Không có reason | Không enqueue gì; tiếp tục bước 11 | Có reason → engine gom vào `decision.reason[]`, enqueue 1 hedge-sync (circuit != open) | — | UC §5 |
| 11 | Light-Check Worker | Mỗi pass | Đọc `HlMarkDO.markPriceUsd` (primary); fallback `eth_price_usd` nếu stale > 120s. Nếu `markPrice >= stop_price` → set `stop_trigger_crossed_at` (guarded) + enqueue price-near-stop-audit | `stop_trigger_crossed_at` đã set → chỉ enqueue price-near-stop-audit, không ghi đè | — | UC §3 step 11 |
| 12 | Light-Check Worker | Mỗi pass | Kiểm tra: `stop_replacing_started_at IS NOT NULL AND age > 60s` → set `bots.status='safe_mode'` AND `lifecycle_state='safe_mode'` atomic + enqueue partial_repair | — | — | UC §3 step 12 |
| 13 | Light-Check Worker | Cuối | Update `queue_idempotency.state='succeeded'` | — | — | UC §3 step 13 |

### F3.2 — Alternate Path A1: Circuit breaker open → suppress hedge-sync

Điều kiện: `circuit_breakers.state='open'`.
- Light-Check Worker đánh giá RebalanceReason[] bình thường.
- KHÔNG enqueue hedge-sync.
- Stop monitoring (step 11) TIẾP TỤC bình thường — price-near-stop-audit vẫn được enqueue nếu stop trigger phát hiện.
- Source: UC §4 A1; SRS FR-EXBOT-014; BR-EXBOT-003.

### F3.3 — Alternate Path A2: Circuit half_open → cho phép 1 probe hedge-sync

Điều kiện: `circuit_breakers.state='half_open'`.
- Light-Check Worker atomic claim `half_open_probe_used` (0→1).
- Nếu claim thành công: enqueue 1 probe hedge-sync.
- Nếu đã claimed (= 1): suppress như circuit open.
- Source: UC §4 A2; SRS FR-EXBOT-040.

### F3.4 — Alternate Path A3: stop_trigger_crossed_at đã set

Điều kiện: `hedge_legs.stop_trigger_crossed_at` đã non-NULL.
- KHÔNG ghi đè.
- Vẫn enqueue price-near-stop-audit.
- Source: UC §4 A3; SRS FR-EXBOT-032; BR-EXBOT-005.

### F3.5 — Alternate Path A4: range_boundary_near routing

Điều kiện: `range_boundary_near` trong `RebalanceReason[]`.
- Route sang hedge-sync (không phải price-near-stop-audit).
- price-near-stop-audit chỉ dành cho `stop_trigger_crossed`.
- Source: UC §4 A4.

### F3.6 — Alternate Path A5: HlMarkDO stale → fallback + widen band

Điều kiện: `HlMarkDO.markPriceUsd` stale > 120s.
- Fallback sang `bot_runtime_state.eth_price_usd` (last-known).
- Widen near-stop band: 2% → 4%.
- Freeze hedge-sync.
- Detection latency tối đa ~7 phút.
- Source: confirmed Tech Lead.

### F3.7 — Exception Path: lifecycle_state skip conditions

Điều kiện: `lifecycle_state IN ('lp_rebalancing', 'lp_closing')` hoặc `status='paused'`.
- Scan Worker KHÔNG gửi message light-check đến Light-Check Worker.
- Scan Worker VẪN update `next_light_check_at` cho các bot này.
- Bot bị skip hoàn toàn trong light-check processing.
- `lifecycle_state='hedge_stopped_cooldown'` KHÔNG bị skip — light-check chạy bình thường, chỉ hedge-sync bị suppress.
- Source: UC §2; SRS FR-EXBOT-012; confirmed code.

### F3.8 — Exception Path: MarketDataDO stale → skip tick

Điều kiện: snapshot stale > 5 phút hoặc DO unreachable.
- Fail-fast: throw ngay tại step 7.
- Skip tick hoàn toàn — không evaluate trigger nào.
- Không dùng stale data, không chờ refresh.
- Source: SRS FR-EXBOT-093; confirmed code.

---

## §F.4 — Functional Integration & Data Consistency

| Hành động kích hoạt | Ảnh hưởng downstream | Data consistency cần kiểm tra | Nguồn |
|---|---|---|---|
| `next_light_check_at` batch-update | D1 state_db_shard được update 1 stmt/shard — mọi eligible bot kể cả skip | Sau update: `bots.next_light_check_at` phải trong khoảng `[now + 4m15s, now + 5m45s]`. Không có unconditional per-bot UPDATE | UC §3 step 4; SRS FR-EXBOT-013 |
| hedge-sync enqueued | `uc-hedge-sync` consumer nhận `{botId, reasons, stateVersion}`; phải check stateVersion trước khi acquire UserLockDO | Nếu D1 state_version thay đổi → worker discard (SRS FR-EXBOT-027) | UC §3 step 10; SRS FR-EXBOT-027 |
| `stop_trigger_crossed_at` set | SAFE_MODE trigger nếu còn stuck sau 30 phút (`uc-deep-audit` backstop) | Giá trị phải là write-once (BR-EXBOT-005). Deep-audit kiểm tra stuck > 30 min → SAFE_MODE | SRS FR-EXBOT-033; BR-EXBOT-005 |
| `bots.status='safe_mode'` + `lifecycle_state='safe_mode'` set atomic (step 12) | Tất cả hedge mutation bị block; `uc-deep-audit` handle recovery | Cả 2 fields phải được set trong cùng 1 UPDATE — tester assert đồng thời. UPDATE phải hoàn tất TRƯỚC KHI partial_repair enqueued | SRS FR-EXBOT-050; states.md; confirmed code |
| `queue_idempotency` insert (expires_at=now+1min) | Ngăn duplicate processing; tự expire sau 1 phút | UNIQUE constraint trên `message_id`; `expires_at` không NULL. Note: không có cleanup job — table tích lũy rows expired (I-10 pending) | SRS FR-EXBOT-011; confirmed code |
| `half_open_probe_used` 0→1 | Chỉ 1 probe hedge-sync được enqueue | CAS atomic write — 2 workers đồng thời chỉ 1 claim thành công | UC §4 A2; SRS FR-EXBOT-040 |
| partial_repair(stop_replacing_overrun) enqueued | `partial_repair` worker nhận; sau 3 fail → `bot_safe_close` | `lifecycle_state='safe_mode'` block hedge-sync; `stop_replacing_started_at` phải được clear trong `finally` block INV-STOP | UC §3 step 12; SRS FR-EXBOT-033, 036 |
| MarketDataDO cache stale > 5 phút | Tick bị skip — không enqueue gì | Không có D1 mutation xảy ra khi stale; `queue_idempotency` state vẫn 'started' (không thể update 'succeeded') — tester phải account | SRS FR-EXBOT-093; confirmed code |
| HlMarkDO stale > 120s | Fallback `eth_price_usd` + widen band; hedge-sync frozen | Stop trigger vẫn có thể fire khi fallback active; `price-near-stop-audit` enqueue bình thường | confirmed Tech Lead |

---

## §F.5 — Acceptance Criteria Candidates

| AC # | Scenario | Given | When | Then | Nguồn / Ghi chú |
|---|---|---|---|---|---|
| AC-LC-01 | Happy path — zero HL calls | Bot active, RebalanceReason[] = [drift_threshold] | Light-check worker processes bot | RebalanceReason[] evaluated using only D1 + MarketDataDO; hedge-sync enqueued; HL API call count = 0 | SRS BR-EXBOT-003; AC-EXBOT-005-1 |
| AC-LC-02 | Idempotency — duplicate message | message_id đã có trong queue_idempotency (state='started') | Light-check message redelivered | Worker exits immediately; no hedge-sync enqueued; no D1 mutation | SRS FR-EXBOT-011 |
| AC-LC-03 | Skip — lp_rebalancing | lifecycle_state='lp_rebalancing' | Scan Worker encounters bot | Bot NOT included in light-check queue; `next_light_check_at` vẫn được update | SRS FR-EXBOT-012; confirmed code |
| AC-LC-04 | Skip — paused | status='paused' | Scan Worker encounters bot | Bot NOT included in light-check queue; `next_light_check_at` vẫn được update | SRS FR-EXBOT-003; confirmed code |
| AC-LC-05 | hedge_stopped_cooldown — not skipped | lifecycle_state='hedge_stopped_cooldown' | Light-check runs for bot | Light-check evaluates normally; hedge-sync suppressed; stop monitoring runs | UC §2 note; states.md |
| AC-LC-06 | Stop trigger detected — HlMarkDO primary | markPrice >= stop_price; stop_trigger_crossed_at IS NULL; HlMarkDO fresh | Light-check pass | stop_trigger_crossed_at set (write-once); price-near-stop-audit enqueued; NO hedge-sync enqueued | SRS FR-EXBOT-032; BR-EXBOT-005; confirmed Tech Lead |
| AC-LC-07 | Stop trigger already set | stop_trigger_crossed_at IS NOT NULL | Light-check pass with markPrice >= stop_price | stop_trigger_crossed_at NOT overwritten; price-near-stop-audit enqueued | SRS FR-EXBOT-032; AC-EXBOT-005-2 |
| AC-LC-08 | Circuit open — suppress hedge-sync | circuit_breakers.state='open' | Light-check evaluates reasons | hedge-sync NOT enqueued; stop monitoring continues; price-near-stop-audit enqueued if stop trigger met | SRS FR-EXBOT-014; AC-EXBOT-005-3 |
| AC-LC-09 | Circuit half_open — 1 probe only | circuit_breakers.state='half_open'; half_open_probe_used=0 | Light-check runs | Exactly 1 hedge-sync probe enqueued; half_open_probe_used set to 1 atomically | SRS FR-EXBOT-040; AC-EXBOT-008-2 |
| AC-LC-10 | Mixed reasons including range_out → 1 hedge-sync | range_out + drift_threshold in RebalanceReason[] | Light-check step 10 | Engine enqueues 1 hedge-sync với cả 2 reasons; `lifecycle_state='lp_rebalancing'` set downstream bởi hedge-sync handler | confirmed code |
| AC-LC-11 | range_boundary_near formula — price-based | range $3,000–$3,400; currentPriceUsd=$3,020 | Evaluate range_boundary_near | nearestFraction = (20/200) = 0.1 <= 0.9 → fires; hedge-sync enqueued (not price-near-stop-audit) | confirmed code; UC §4 A4 |
| AC-LC-12 | Stop replace overrun → SAFE_MODE (atomic) | stop_replacing_started_at IS NOT NULL; age > 60s | Light-check pass | `bots.status='safe_mode'` AND `lifecycle_state='safe_mode'` set atomically trong 1 UPDATE trước khi enqueue; partial_repair(reason='stop_replacing_overrun') enqueued sau | SRS FR-EXBOT-033; confirmed code |
| AC-LC-13 | next_light_check_at jitter | Bot processed by Scan Worker | Batch update | next_light_check_at in range [now+4m15s, now+5m45s]; 1 D1 stmt per shard (not per-bot) | SRS FR-EXBOT-013 |
| AC-LC-14 | drift_threshold formula | lpEthAmount=10ETH; currentPriceUsd=$3,000 | Evaluate drift_threshold | lpValueUsd = max(0, 10×3000) = $30,000; threshold = max($25, $30,000×3%) = $900; drift_threshold fires khi deltaErrorUsd > $900 | confirmed code |
| AC-LC-15 | MarketDataDO stale → skip tick | MarketDataDO snapshot stale > 5 phút | Light-check step 7 | Worker throws fail-fast; tick skipped; no triggers evaluated; no D1 mutation | SRS FR-EXBOT-093; confirmed code |
| AC-LC-16 | HlMarkDO stale → fallback + widen band | HlMarkDO stale > 120s | Stop trigger evaluation | Fallback to eth_price_usd; near-stop band widens 2%→4%; hedge-sync frozen | confirmed Tech Lead |
| AC-LC-17 | 7d funding_alert threshold | fundingApr7dPct=-16% | Evaluate funding_alert | funding_alert fires (< -15%); hedge-sync enqueued | confirmed code |
| AC-LC-18 | LIMIT 500 — steady state no overflow | 10,000 bots với jitter ±45s uniform | Scan cycle | Bots phân tán đều trong 5-min window; không có shard overflow trong steady state | confirmed code |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

Xem §F.3 (Functional Logic & Workflow Decomposition) ở trên.

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Hành động kích hoạt | UC / Module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| hedge-sync enqueued | `uc-hedge-sync` | Worker điều chỉnh delta hedge; reconcile sau khi fill; replace stop via INV-STOP | `stateVersion` trong message phải match tại thời điểm hedge-sync worker xử lý | SRS FR-EXBOT-027 |
| price-near-stop-audit enqueued | Stop-audit worker (out of scope) | Worker xử lý stop event | `stop_trigger_crossed_at` write-once; deep-audit backstop nếu stuck > 30 min | SRS FR-EXBOT-031, 033 |
| partial_repair(stop_replacing_overrun) | `uc-hedge-sync` (repair worker) | Repair worker xử lý overrun; sau 3 lần fail → `bot_safe_close` | `lifecycle_state='safe_mode'` block hedge-sync | SRS FR-EXBOT-033, 036 |
| `lifecycle_state='safe_mode'` + `status='safe_mode'` | Toàn bộ mutation operations | Hedge-sync, LP rebalance, change leverage đều bị block | Cả 2 fields phải đồng bộ — assert trong cùng 1 check | SRS FR-EXBOT-050 |
| MarketDataDO stale | Tất cả light-check workers trong CF region | Tick skip toàn bộ | Không có D1 mutation; queue_idempotency state không advance | SRS FR-EXBOT-093 |

---

## 8. Acceptance Criteria

Xem §F.5 ở trên — AC candidates AC-LC-01 đến AC-LC-18.

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance / Throughput | 10.000 bots / 5-min scan. Light-check KHÔNG fetch HL cho bất kỳ bot nào | Test: 1 light-check cycle đầy đủ không tiêu tốn HL rate-limit weight nào | NFR-EXBOT-001; BR-EXBOT-003 |
| D1 Write budget | `next_light_check_at` batch-update: 1 stmt/shard; không per-bot | Test: không có per-bot unconditional UPDATE | NFR-EXBOT-005 |
| Idempotency | `queue_idempotency` insert với expires_at=now+1min trước khi xử lý | Test: redelivery cùng message → chỉ 1 lần xử lý | NFR-EXBOT-007 |
| Precision | `lpEthAmount` và `deltaErrorUsd` tính bằng BigDecimal | Test: không có float arithmetic trong tính toán LP amount hoặc drift | NFR-EXBOT-008 |
| Multi-chain | `wethIndex` đọc từ D1 `positions.weth_index` — không hardcode | Test: bot trên Base và Optimism đều tính đúng `lpEthAmount` | NFR-EXBOT-009 |
| Concurrency | Max 6 outbound connections per CF Worker invocation | Test: không lỗi connection limit khi đọc D1 + MarketDataDO + HlMarkDO | NFR-EXBOT-011 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận — Issue Register

| ID | Mức ưu tiên | Severity | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề | Vì sao quan trọng | Owner | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| I-01 | Low | Minor | MISSING_INFO (UC chưa update) | UC §3 step 11; confirmed Tech Lead | `hlMarkPrice` source đã được xác nhận: primary `HlMarkDO.markPriceUsd`, fallback `eth_price_usd` khi stale > 120s, widen band 2%→4%, freeze hedge-sync. Tuy nhiên UC §3 step 11 chưa được cập nhật để reflect `HlMarkDO` là primary source và staleness policy. UC vẫn mô tả candidate là `eth_price_usd`. | UC text không phản ánh đúng behavior thực tế — tester đọc UC sẽ hiểu sai nếu không có notes này. Cần BA update UC §3 step 11. | BA | Open (UC needs update) |
| I-05 | Low | Minor | MISSING_INFO (UC chưa update) | UC §3 step 10; confirmed code | Mixed reasons behavior đã được xác nhận: engine gom tất cả reasons, enqueue 1 hedge-sync duy nhất, không tự set `lifecycle_state='lp_rebalancing'`. Tuy nhiên UC §3 step 10 vẫn mô tả "If reasons include range_out: set lifecycle_state='lp_rebalancing'" — mâu thuẫn với code behavior. | BA cần update UC step 10 để reflect đúng: lifecycle_state transition là downstream responsibility của hedge-sync handler. | BA | Open (UC needs update) |
| I-10 | Low | Minor | MISSING_INFO | UC §3 step 5; SRS ERD | `expires_at` được set (TTL = 1 phút, không NULL) — đã confirmed. Tuy nhiên không có cleanup job để purge expired rows. Table `queue_idempotency` sẽ tích lũy theo thời gian. | Dev team cần thêm scheduled purge. Ảnh hưởng đến long-running test scenarios. | Tech Lead | ⏳ Pending (cleanup solution) |

**Lưu ý:** Các issue I-02, I-03, I-04, I-07, I-08, I-09, I-11, I-12 đã được giải đáp đầy đủ và đóng trong version này. Chi tiết trong file questions v2.

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| UC §3 step 11 cần update: `HlMarkDO` là primary source, staleness policy | UC documentation | Tester đọc UC mà không đọc notes sẽ hiểu sai | BA | Open |
| UC §3 step 10 cần update: mixed reasons → 1 hedge-sync, `lifecycle_state` set downstream | UC documentation | Tester có thể assert sai khi test mixed reasons | BA | Open |
| `queue_idempotency` cleanup job | Dev task | Ảnh hưởng long-running test env | Dev / Tech Lead | Pending |
| `uc-deep-audit`: backstop detection `stop_trigger_crossed_at` > 30 min | UC dependency | Light-check chỉ là primary path | — | External |
| `uc-hedge-sync`: downstream consumer của hedge-sync queue | UC dependency | Test end-to-end phải kéo uc-hedge-sync | — | External |

---

### 10.3 Audit Summary — Scoring & Verdict

#### Scoring Table

| # | Scoring Area | Max | Score | Status | Lý do |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 19 | ✅ Clear | F.1 đầy đủ và atomic. `HlMarkDO` đã được thêm (F1-12), `funding_rolling_metrics` (F1-D6). Các source đều confirmed. Trừ 1 điểm: `lpValueUsd` field trong F1-D2 không có formula tường minh (dùng `max(0, lpEthAmount × currentPriceUsd)` nhưng ERD chưa reflect). |
| 2 | Data Object / State Attributes, BR, Validations & Messages | 25 | 23 | ✅ Clear | F.2 cover > 95% F.1 elements với formulas cụ thể: drift_threshold, range_boundary_near, funding_alert, HlMarkDO staleness, stop overrun atomic update đều confirmed. Trừ 2 điểm: I-10 (expires_at TTL confirmed nhưng cleanup gap); `HlMarkDO` stale + widen band behavior chưa có E-code/message khi freeze hedge-sync. |
| 3 | Functional Logic & Workflow Decomposition | 25 | 24 | ✅ Clear | 8 paths đầy đủ (F3.1–F3.8). Mixed reasons, LIMIT 500 jitter design, MarketDataDO fail-fast, HlMarkDO fallback đều được mô tả rõ. Trừ 1 điểm: UC §3 step 10/11 text chưa được update để reflect code behavior — tester đọc UC gốc sẽ cần notes này. |
| 4 | Functional Integration & Data Consistency | 15 | 14 | ✅ Clear | Atomic update `bots.status + lifecycle_state` trước enqueue confirmed; `next_light_check_at` update cho mọi bot kể cả skip confirmed; stale DO tick-skip behavior confirmed. Trừ 1 điểm: `queue_idempotency` cleanup gap (I-10) tạo data consistency risk cho long-running env. |
| 5 | UC / Spec Documentation Quality Issues | 15 | 12 | ⚠️ Partial | UC structure tốt, major behavioral questions đã được giải đáp. Trừ 3 điểm: UC §3 step 10/11 text cần update để reflect code (I-01, I-05 — minor documentation debt); `expires_at` cleanup gap (I-10); UC không mention `HlMarkDO` là source mới trong actor section. |
| **Total** | | **100** | **92** | ✅ | |

**Auto-cap check:**
- Không có Blocker nào còn open.
- Không có scoring area nào = 0.
- Không có contradiction thay đổi expected behavior cơ bản.
- Tất cả cap conditions không áp dụng.

**Final Score: 92 / 100**

#### Final Verdict: ✅ Ready

**Lý do:** Tổng điểm 92 đạt ngưỡng Ready (≥ 90). Tất cả 4 Blocker từ v1 (I-01 đến I-04) đã được giải đáp đầy đủ với formulas và behavior cụ thể confirmed từ code và Tech Lead. Không còn câu hỏi nào block test design.

**Còn lại là documentation debt nhỏ:**
1. **I-01 (Minor)**: BA cần update UC §3 step 11 để phản ánh `HlMarkDO` là primary source và staleness policy.
2. **I-05 (Minor)**: BA cần update UC §3 step 10 để phản ánh mixed reasons → 1 hedge-sync, `lifecycle_state` set downstream.
3. **I-10 (Minor/Pending)**: Dev team cần thêm cleanup job cho `queue_idempotency` expired rows.

**Khuyến nghị:** QC Lead có thể tiến hành thiết kế test scenarios và test cases ngay. Tester sử dụng report v2 này (không dùng UC gốc cho step 10/11) cho đến khi BA update UC.

---

## 11. Change Log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Exbot Agent | Tạo báo cáo audited lần đầu — SRS-first cross-check |
| v2 | 2026-07-03 | QC UC Read Exbot Agent | Cập nhật với câu trả lời từ BA/Tech Lead/code: 10/12 câu hỏi open đã đóng. `hlMarkPrice` source confirmed (HlMarkDO + staleness policy), formulas confirmed (range_boundary_near, lpValueUsd, funding_alert), mixed reasons behavior confirmed, LIMIT 500 design confirmed, atomic SAFE_MODE update confirmed, next_light_check_at skip behavior confirmed, MarketDataDO fail-fast confirmed. Score tăng từ 72 → 92. Verdict thay đổi từ Conditionally Ready → Ready. |
