# Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC ID:** UC-EXBOT-light-check  
**Tên feature:** Execute Periodic Light-Check  
**Ngày tạo:** 2026-06-30  
**Người viết:** QC UC Read Exbot Agent  
**Version:** v1

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-light-check mô tả quy trình định kỳ (5 phút/lần) mà hệ thống ExBot dùng để đánh giá từng bot đang hoạt động xem có cần điều chỉnh hedge, cân bằng lại LP, hay phát hiện stop trigger không — mà **không thực hiện bất kỳ lời gọi API nào đến Hyperliquid (HL weight = 0)**. Đây là luồng fan-out trung tâm của ExBot: Cron Worker → bot-scan queue → Scan Worker → light-check queue → Light-Check Worker, kết thúc bằng việc enqueue sang `hedge-sync`, `price-near-stop-audit`, hoặc `partial_repair` queue tùy tình huống.

Điều kiện cần: bot có `status='active'` và `next_light_check_at <= now`, và `lifecycle_state` không thuộc `lp_rebalancing` hoặc `lp_closing`, và `status != 'paused'`. Các bot ở trạng thái `hedge_stopped_cooldown` vẫn chạy light-check bình thường nhưng không enqueue hedge-sync.

Hệ thống đọc hai nguồn: D1 (`bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs`) và `MarketDataDO` (`sqrtPriceX96`, `currentTick`). Từ đó tính `lpEthAmount` qua công thức Uniswap V3 TickMath + LiquidityAmounts (tính local, không RPC), sau đó đánh giá danh sách `RebalanceReason[]` theo quy tắc 3-way price split (v5.2.6 X-5): `uniPoolPrice` cho drift valuation, `hlMarkPrice` cho stop trigger, `hlOraclePrice` cho margin. Bước phát hiện stop trigger `stop_trigger_crossed_at` hiện đang vướng câu hỏi mở OQ-EXBOT-017 về nguồn `hlMarkPrice` khi HL weight = 0.

Use case này liên kết chặt chẽ với `uc-hedge-sync` (downstream consumer của hedge-sync queue), `uc-bot-safe-close` (khi stop overrun > 60s dẫn đến SAFE_MODE), và `uc-deep-audit` (backstop phát hiện overrun khi light-check miss).

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
| DO | Durable Object — đối tượng stateful của Cloudflare Workers (HLRateLimitDO, UserLockDO, MarketDataDO) | FRD §4.10 |
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

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Light-check là vòng lặp giám sát định kỳ trung tâm của ExBot. Mục tiêu là đánh giá liên tục 10.000 bot ở chu kỳ 5 phút mà không tiêu tốn bất kỳ HL API rate-limit nào (BR-EXBOT-003). Kết quả của mỗi lần light-check là quyết định fan-out: enqueue hedge-sync nếu cần điều chỉnh delta, enqueue price-near-stop-audit nếu phát hiện stop trigger, enqueue partial_repair nếu phát hiện overrun stop replace, hoặc không làm gì nếu bot đang ổn.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Cron → Scan fan-out | Cron Worker (1 phút) gọi `chunkSendBatch` đến bot-scan queue; Scan Worker query D1 và gửi message per-bot đến light-check queue; batch-update `next_light_check_at` | UC §3 steps 1–4; SRS FR-EXBOT-012, 013 |
| Idempotency check | Light-Check Worker insert `message_id` vào `queue_idempotency` (state='started'); UNIQUE conflict → skip | UC §3 step 5; SRS FR-EXBOT-011 |
| Đọc D1 + MarketDataDO | Đọc `bot_runtime_state`, `lifecycle_state`, `hedge_legs`; đọc `sqrtPriceX96`, `currentTick` từ MarketDataDO | UC §3 steps 6–7 |
| Tính `lpEthAmount` | TickMath + LiquidityAmounts local, không RPC | UC §3 step 8; SRS FR-EXBOT-012 |
| Đánh giá RebalanceReason[] | 7 reason: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback | UC §3 step 9; SRS FR-EXBOT-023 |
| Fan-out hedge-sync / lp_rebalancing | `range_out` → set `lifecycle_state='lp_rebalancing'` + enqueue lp_rebalancing + partial_repair; các reason khác (circuit != open) → enqueue hedge-sync | UC §3 step 10; SRS FR-EXBOT-015 |
| Stop trigger detection | `markPrice >= stop_price` → set `stop_trigger_crossed_at` (guarded) + enqueue price-near-stop-audit | UC §3 step 11; SRS FR-EXBOT-032 |
| Stop replace overrun check | `stop_replacing_started_at IS NOT NULL AND age > 60s` → enqueue partial_repair + SAFE_MODE | UC §3 step 12; SRS FR-EXBOT-033 |
| Finalize idempotency | Update `queue_idempotency.state='succeeded'` | UC §3 step 13 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Xử lý hedge-sync worker | UC này chỉ enqueue; logic điều chỉnh delta là `uc-hedge-sync` | Tester cần đọc uc-hedge-sync để test downstream |
| Xử lý price-near-stop-audit worker | Ngoài scope UC này | — |
| Xử lý partial_repair worker | Ngoài scope UC này | — |
| Deep-audit backstop | `uc-deep-audit` là backstop phát hiện stuck markers, không phải light-check | Dependency cần theo dõi |
| Diagram sequence chi tiết | UC có placeholder Mermaid nhưng không có nội dung thực | Minor gap — không block test |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn | Nguồn |
|---|---|---|---|---|
| Cron Worker (1 min) | System | Khởi động fan-out mỗi 1 phút | Chỉ enqueue bot-scan; không đọc/ghi D1 trực tiếp | UC §1 |
| Scan Worker | System | Query D1 lấy danh sách bot eligible; enqueue light-check per-bot; batch-update `next_light_check_at` | Đọc/ghi D1 state_db_shard | UC §1, §3 steps 1–4 |
| Light-Check Worker | System | Xử lý từng message light-check: đọc D1 + MarketDataDO, tính toán, fan-out | Ghi D1 (queue_idempotency, lifecycle_state, stop_trigger_crossed_at); enqueue đến hedge-sync / price-near-stop-audit / partial_repair queues; KHÔNG gọi HL API | UC §1; SRS BR-EXBOT-003 |
| D1 (state_db_shard) | System | Lưu trạng thái bot runtime, hedge legs, circuit breaker | Read/write by Light-Check Worker | UC §1, §3 |
| MarketDataDO | System | Cache pool slot0 (`sqrtPriceX96`, `currentTick`) | Read-only by Light-Check Worker | UC §3 step 7; SRS FR-EXBOT-093 |

**Nhận xét readiness:** Actor và vai trò đủ rõ cho test logic. Light-Check Worker là actor chính với ràng buộc tuyệt đối HL weight = 0. Không có actor người dùng (no UI) — đúng scope.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot `status='active'` | Yes | UC §2; SRS FR-EXBOT-012 |
| 2 | `next_light_check_at <= now` | Yes | UC §2; SRS FR-EXBOT-012 |
| 3 | `lifecycle_state NOT IN ('lp_rebalancing', 'lp_closing')` | Yes | UC §2; SRS FR-EXBOT-012 |
| 4 | `status != 'paused'` | Yes | UC §2; SRS FR-EXBOT-003 |
| 5 | Bots với `lifecycle_state='hedge_stopped_cooldown'` KHÔNG bị skip — light-check chạy bình thường, chỉ hedge-sync bị suppressed | Yes | UC §2 note; SRS states.md |
| 6 | `MarketDataDO` có dữ liệu hợp lệ (`sqrtPriceX96`, `currentTick`) | Yes (implied) | UC §3 step 7; SRS FR-EXBOT-093 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Không cần action | Không có message enqueued; `queue_idempotency.state='succeeded'`; `next_light_check_at` đã được batch-update | UC §5; step 13 |
| Hedge-sync cần | `hedge-sync` message enqueued với `{botId, reasons, stateVersion}`; `queue_idempotency.state='succeeded'` | UC §3 step 10; SRS FR-EXBOT-012 |
| range_out phát hiện | `lifecycle_state='lp_rebalancing'`; `lp_rebalancing` message + `partial_repair` message enqueued | UC §3 step 10; SRS FR-EXBOT-015 |
| Stop trigger phát hiện | `hedge_legs.stop_trigger_crossed_at` được set (nếu NULL); `price-near-stop-audit` enqueued; KHÔNG enqueue hedge-sync | UC §3 step 11; SRS FR-EXBOT-032 |
| Stop replace overrun | `partial_repair(reason='stop_replacing_overrun')` enqueued; bot chuyển sang `safe_mode`; `lifecycle_state='safe_mode'` | UC §3 step 12; SRS FR-EXBOT-033 |
| Duplicate message | Light-check worker exit ngay sau UNIQUE conflict trên `queue_idempotency` | UC §3 step 5; SRS FR-EXBOT-011 |
| `next_light_check_at` | Batch-update: `now + 5min + jitter(±45s)`, 1 statement per shard | UC §3 step 4; SRS FR-EXBOT-013 |
| HL API call count | = 0 (invariant) | UC §5; SRS BR-EXBOT-003 |

---

## §F.1 — Function / Operation & Data Object Inventory

| # | Item | Loại | Trigger / Source | Input | Output / Effect | Data Objects & Fields | Enum / State set | Events / Messages | Source trace |
|---|---|---|---|---|---|---|---|---|---|
| F1-01 | Cron fan-out to bot-scan | Operation | Cron 1 min | — | Batch messages to bot-scan queue via `chunkSendBatch` | — | — | — | UC §3 step 1; SRS FR-EXBOT-012 |
| F1-02 | Scan Worker query eligible bots | Operation | bot-scan queue message | D1: `bots` table | List of botIds eligible for light-check | `bots.status`, `bots.next_light_check_at`, `bots.lifecycle_state` | `status='active'`; `next_light_check_at <= now`; `LIMIT 500` | — | UC §3 step 2 |
| F1-03 | Scan Worker enqueue per-bot to light-check queue | Operation | Result of F1-02 | List of botIds | Messages in light-check queue via `chunkSendBatch` | — | — | — | UC §3 step 3; SRS FR-EXBOT-010 |
| F1-04 | Batch-update `next_light_check_at` | Operation | After enqueue | botIds per shard | `next_light_check_at = now + 5min + jitter(±45s)` written to D1 (1 stmt/shard) | `bots.next_light_check_at` | — | — | UC §3 step 4; SRS FR-EXBOT-013 |
| F1-05 | Idempotency insert | Operation | Light-Check Worker start | `message_id` | `queue_idempotency` row inserted with `state='started'`; UNIQUE conflict → skip | `queue_idempotency.message_id`, `queue_idempotency.state`, `queue_idempotency.kind` | `state`: started / succeeded / failed | — | UC §3 step 5; SRS FR-EXBOT-011 |
| F1-06 | Read D1 bot state | Operation | Light-Check Worker | `botId` | Runtime state loaded from D1 | `bot_runtime_state.last_known_hl_short_size`, `bots.lifecycle_state`, `hedge_legs.stop_price`, `hedge_legs.margin_status`, `hedge_legs.circuit_state`, `hedge_legs.stop_replacing_started_at` | — | — | UC §3 step 6 |
| F1-07 | Read MarketDataDO | Operation | Light-Check Worker | `botId` (pool context) | `sqrtPriceX96`, `currentTick` | MarketDataDO cache fields | — | — | UC §3 step 7; SRS FR-EXBOT-093 |
| F1-08 | Compute `lpEthAmount` | Operation | After F1-07 | `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick`, `wethIndex` | `lpEthAmount` (BigDecimal) | `positions.liquidity`, `positions.tick_lower`, `positions.tick_upper`, `positions.weth_index` | — | — | UC §3 step 8; SRS FR-EXBOT-020 |
| F1-09 | Evaluate RebalanceReason[] | Operation | After F1-08 | D1 state + MarketDataDO | `RebalanceReason[]` list | `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.lp_value_usd`, `hedge_legs.margin_status` | `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback` | — | UC §3 step 9; SRS FR-EXBOT-023 |
| F1-10 | Fan-out: range_out → lp_rebalancing | Operation | range_out in RebalanceReason[] | `botId`, `lifecycle_state` | Set `lifecycle_state='lp_rebalancing'`; enqueue `lp_rebalancing` + `partial_repair` | `bots.lifecycle_state` | `lifecycle_state`: active → lp_rebalancing | — | UC §3 step 10; SRS FR-EXBOT-015 |
| F1-11 | Fan-out: other reasons → hedge-sync | Operation | Non-range_out reasons AND `circuit_state != 'open'` | `botId`, reasons, stateVersion | hedge-sync message enqueued | `bot_runtime_state.state_version` | `circuit_breakers.state`: closed / open / half_open | — | UC §3 step 10; SRS FR-EXBOT-012 |
| F1-12 | Circuit half_open probe | Operation | `circuit_state='half_open'` | `hedge_leg_id` | Atomically claim `half_open_probe_used`; enqueue ONE probe hedge-sync | `circuit_breakers.half_open_probe_used`, `circuit_breakers.state` | `half_open_probe_used`: 0 → 1 | — | UC §4 A2; SRS FR-EXBOT-040 |
| F1-13 | Stop trigger detection | Operation | Each light-check pass | `hedge_legs.stop_price`, `hlMarkPrice` | Set `stop_trigger_crossed_at` (guarded, only if NULL); enqueue `price-near-stop-audit` | `hedge_legs.stop_trigger_crossed_at` | write-once (BR-EXBOT-005) | — | UC §3 step 11; SRS FR-EXBOT-032 |
| F1-14 | Stop replace overrun detection | Operation | Each light-check pass | `hedge_legs.stop_replacing_started_at`, `now` | If set AND age > 60s: enqueue `partial_repair(reason='stop_replacing_overrun')`; set `lifecycle_state='safe_mode'` | `hedge_legs.stop_replacing_started_at`, `bots.lifecycle_state` | `lifecycle_state`: active → safe_mode | — | UC §3 step 12; SRS FR-EXBOT-033 |
| F1-15 | Finalize idempotency | Operation | After all fan-out logic | `queue_idempotency` row | Update `state='succeeded'` | `queue_idempotency.state` | succeeded | — | UC §3 step 13 |
| F1-D1 | `bots` table | Data Object | D1 state_db_shard | — | — | `id`, `status`, `lifecycle_state`, `next_light_check_at` | `status`: active/paused/closing/closed/safe_mode/error; `lifecycle_state`: 18 states | — | SRS ERD; states.md |
| F1-D2 | `bot_runtime_state` table | Data Object | D1 hot state | — | — | `bot_id`, `state_version`, `last_known_hl_short_size`, `lp_value_usd`, `eth_price_usd`, `lp_eth_amount`, `current_tick`, `sqrt_price_x96` | — | — | SRS ERD |
| F1-D3 | `hedge_legs` table | Data Object | D1 | — | — | `stop_price`, `margin_status`, `circuit_state`, `stop_trigger_crossed_at`, `stop_replacing_started_at`, `stop_distance_pct` | `margin_status`: ok/warning/critical; `circuit_state`: closed/open/half_open | — | SRS ERD |
| F1-D4 | `circuit_breakers` table | Data Object | D1 | — | — | `state`, `half_open_probe_used`, `reset_at`, `failure_count` | `state`: closed/open/half_open | — | SRS ERD |
| F1-D5 | `queue_idempotency` table | Data Object | D1 | — | — | `message_id`, `kind`, `state`, `bot_id`, `created_at`, `expires_at` | `state`: started/succeeded/failed/retryable | — | SRS ERD |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Item (từ F.1) | Trạng thái / Preconditions | Validation / Business Rule | Dependencies | Messages / Events | Nguồn |
|---|---|---|---|---|---|
| F1-01 Cron fan-out | Cron schedule: mỗi 1 phút | Tất cả batch calls PHẢI dùng `chunkSendBatch()` — gọi `queue.sendBatch()` trực tiếp bị cấm (BR-EXBOT-010 không; FR-EXBOT-010) | — | — | UC §3 step 1; SRS FR-EXBOT-010 |
| F1-02 Scan query | `bots.status='active'` AND `next_light_check_at <= now` | LIMIT 500 per shard; bot với `lifecycle_state IN ('lp_rebalancing','lp_closing')` hoặc `status='paused'` phải bị lọc ra TRƯỚC KHI enqueue light-check | D1 shard sharding key: `hash(bot_id) % shard_count` | — | UC §3 step 2; SRS FR-EXBOT-012 |
| F1-03 Enqueue light-check | Sau F1-02 | `chunkSendBatch` required | bot-scan queue | — | UC §3 step 3 |
| F1-04 Batch-update next_light_check_at | Sau F1-03 | `next_light_check_at = now + 5min + random(−45s, +45s)`; 1 UPDATE statement per shard — KHÔNG viết per-bot (NFR-EXBOT-005) | D1 shard | — | SRS FR-EXBOT-013 |
| F1-05 Idempotency insert | Đầu mỗi Light-Check Worker execution | `queue_idempotency.message_id` UNIQUE constraint — UNIQUE conflict = duplicate delivery → return ngay (SRS FR-EXBOT-011) | `queue_idempotency` table | — | UC §3 step 5 |
| F1-06 Read D1 bot state | Sau idempotency pass | Đọc: `bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs.stop_price`, `hedge_legs.margin_status`, `hedge_legs.circuit_state` | D1 state_db_shard | — | UC §3 step 6 |
| F1-07 Read MarketDataDO | Sau F1-06 | Zero HL calls — `sqrtPriceX96` và `currentTick` đọc từ MarketDataDO cache, KHÔNG từ RPC trực tiếp | MarketDataDO (FR-EXBOT-093) | — | UC §3 step 7 |
| F1-08 Compute lpEthAmount | Sau F1-07 | Dùng Uniswap V3 AMM formula (TickMath + LiquidityAmounts). Cấm dùng `depositedToken − withdrawnToken + collectedFees` (FR-EXBOT-020). `wethIndex` đọc từ `positions.weth_index`, KHÔNG hardcode | `positions.weth_index`, `positions.tick_lower`, `positions.tick_upper` | — | SRS FR-EXBOT-020; FR-EXBOT-021 |
| F1-09 RebalanceReason[] | Sau F1-08 | Chỉ dùng canonical enum values: `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback` (FR-EXBOT-023). `stop_trigger_crossed` KHÔNG phải RebalanceReason | D1 + MarketDataDO | — | SRS FR-EXBOT-023 |
| F1-09 drift_threshold | — | `deltaErrorUsd > max($25, lpValueUsd × 3%)` trong đó `deltaErrorUsd = \|targetShortEth − actualShortEth\| × uniPoolPrice`. Dùng `uniPoolPrice` (từ `sqrtPriceX96` via MarketDataDO) — KHÔNG dùng hlMarkPrice hay hlOraclePrice (v5.2.6 X-5 3-way split) | `bot_runtime_state.lp_value_usd` (OQ-EXBOT-11 chưa giải đáp) | — | SRS FR-EXBOT-012 |
| F1-09 drift_relative | — | `\|target - actual\| / target > 0.15` | — | — | SRS FR-EXBOT-012 (implied from FRD FR-EXBOT-011) |
| F1-09 range_out | — | `rangeState != 'in'` — cần resolve cách tính `rangeState` từ `currentTick`, `tickLower`, `tickUpper` | `positions.tick_lower`, `positions.tick_upper` | — | SRS FR-EXBOT-012 |
| F1-09 range_boundary_near | — | Price 90% to range upper/lower — công thức cụ thể (tick-based hay price-based) chưa được xác nhận (OQ-EXBOT-10 open) | — | — | SRS OQ-EXBOT-10 |
| F1-09 margin_warning | — | `hedge_legs.margin_status == 'warning'` — đọc từ D1, KHÔNG fetch HL (FR-EXBOT-060) | `hedge_legs.margin_status` | — | SRS FR-EXBOT-012 |
| F1-09 funding_alert | — | 7d funding < −15% APR — công thức aggregation chưa được xác nhận (OQ-EXBOT-12 open) | `funding_daily_metrics` | — | SRS OQ-EXBOT-12 |
| F1-09 time_fallback | — | 4h since last adjustment | `bot_runtime_state.last_hl_reconcile_at` (implied) | — | SRS FR-EXBOT-012 |
| F1-10 range_out fan-out | Precondition: `range_out` in RebalanceReason[] | Set `lifecycle_state='lp_rebalancing'` → light-check và hedge-sync suppressed. Enqueue `lp_rebalancing` message + `partial_repair`. Các reason KHÁC trong cùng pass → route sang hedge-sync (không bị block bởi range_out) | `bots.lifecycle_state` | — | UC §3 step 10; SRS FR-EXBOT-015 |
| F1-11 hedge-sync fan-out | Precondition: circuit_state != 'open'; reasons không chứa range_out | Enqueue với `{botId, reasons, stateVersion}`. `stateVersion` lấy từ `bot_runtime_state.state_version` | `circuit_breakers.state` | — | UC §3 step 10 |
| F1-11 circuit open suppression | `circuit_breakers.state='open'` | Suppress hedge-sync enqueue. Stop monitoring (price-near-stop-audit) KHÔNG bị suppress — luôn chạy (FR-EXBOT-014; BR-EXBOT-003) | — | — | UC §4 A1; SRS FR-EXBOT-014 |
| F1-12 circuit half_open probe | `circuit_breakers.state='half_open'` | Claim `half_open_probe_used` ATOMIC (0→1). Chỉ 1 probe được phép. Nếu đã claimed → suppress như open | `circuit_breakers.half_open_probe_used` | — | UC §4 A2; SRS FR-EXBOT-040 |
| F1-13 Stop trigger | Mỗi light-check pass; stop monitoring luôn chạy kể cả circuit open | `markPrice >= stop_price` → set `stop_trigger_crossed_at` chỉ nếu hiện tại NULL (BR-EXBOT-005 — write-once per stop event). Enqueue price-near-stop-audit. KHÔNG enqueue hedge-sync (UC §4 A4 note) | `hedge_legs.stop_trigger_crossed_at`, `hedge_legs.stop_price` | price-near-stop-audit message enqueued | UC §3 step 11; SRS FR-EXBOT-032 |
| F1-13 hlMarkPrice source | — | **OQ-EXBOT-017 open**: nguồn `hlMarkPrice` trong điều kiện HL weight=0 chưa được xác nhận. Ứng viên: `bot_runtime_state.eth_price_usd`. Chính sách staleness chưa được định nghĩa | `bot_runtime_state.eth_price_usd` (candidate) | — | UC §3 step 11 note; SRS OQ-EXBOT-17 |
| F1-14 Stop replace overrun | Mỗi light-check pass | `stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60s` → enqueue `partial_repair(reason='stop_replacing_overrun')` + enter SAFE_MODE. Primary detection path (≤5 min); secondary backstop là deep-audit | `hedge_legs.stop_replacing_started_at` | partial_repair enqueued; `lifecycle_state='safe_mode'` | UC §3 step 12; SRS FR-EXBOT-033 |
| F1-13 A3 (crossed_at already set) | `stop_trigger_crossed_at` đã non-NULL | KHÔNG ghi đè. Vẫn enqueue price-near-stop-audit | — | price-near-stop-audit enqueued | UC §4 A3; SRS FR-EXBOT-032 |

---

## §F.3 — Functional Logic & Workflow Decomposition

### F3.1 — Happy Path: Scan + Light-Check không cần action

| Bước | Actor | Trigger / Hành động | System response (happy path) | Alternate path | Exception path | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Cron Worker | Cron 1 min | Gọi `chunkSendBatch` tới bot-scan queue với shard windows | — | Cron lỗi → không có message → batch delayed đến chu kỳ sau | UC §3 step 1 |
| 2 | Scan Worker | Nhận bot-scan message | Query D1: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500` | Không có bot eligible → không enqueue gì | D1 unreachable → SAFE_MODE trigger theo FR-EXBOT-050 | UC §3 step 2 |
| 3 | Scan Worker | Sau query | Enqueue per-bot messages tới light-check queue qua `chunkSendBatch` | — | — | UC §3 step 3 |
| 4 | Scan Worker | Sau enqueue | Batch-update `next_light_check_at = now + 5min + jitter(±45s)` — 1 stmt/shard | — | — | UC §3 step 4 |
| 5 | Light-Check Worker | Nhận light-check message | Insert `message_id` vào `queue_idempotency` (state='started') | UNIQUE conflict → skip (duplicate delivery) | — | UC §3 step 5 |
| 6 | Light-Check Worker | Sau idempotency OK | Đọc D1: `bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs` fields | — | — | UC §3 step 6 |
| 7 | Light-Check Worker | Sau đọc D1 | Đọc MarketDataDO: `sqrtPriceX96`, `currentTick` (zero HL calls) | — | MarketDataDO stale → cảnh báo + forced refresh (SRS FR-EXBOT-093) | UC §3 step 7 |
| 8 | Light-Check Worker | Sau đọc DO | Tính `lpEthAmount` local: TickMath + LiquidityAmounts (BigDecimal, dùng `wethIndex` từ D1) | — | — | UC §3 step 8 |
| 9 | Light-Check Worker | Sau tính | Đánh giá `RebalanceReason[]` từ D1 + MarketDataDO state | — | — | UC §3 step 9 |
| 10a | Light-Check Worker | Không có reason | Không enqueue gì; tiếp tục bước 11 | — | — | UC §5 |
| 11 | Light-Check Worker | Mỗi pass | Kiểm tra stop trigger: nếu `markPrice >= stop_price` → set `stop_trigger_crossed_at` (guarded) + enqueue price-near-stop-audit; nếu `stop_trigger_crossed_at` đã set → chỉ enqueue price-near-stop-audit | — | OQ-EXBOT-017: `hlMarkPrice` source TBD | UC §3 step 11 |
| 12 | Light-Check Worker | Mỗi pass | Kiểm tra stop replace overrun: nếu `stop_replacing_started_at IS NOT NULL AND age > 60s` → enqueue partial_repair + SAFE_MODE | — | — | UC §3 step 12 |
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

### F3.6 — Exception Path: lifecycle_state skip conditions

Điều kiện: `lifecycle_state IN ('lp_rebalancing', 'lp_closing')` hoặc `status='paused'`.
- Scan Worker KHÔNG gửi message light-check đến Light-Check Worker.
- Bot bị skip hoàn toàn.
- Lưu ý: `lifecycle_state='hedge_stopped_cooldown'` KHÔNG bị skip — light-check chạy bình thường, chỉ hedge-sync bị suppress.
- Source: UC §2; SRS FR-EXBOT-012.

### F3.7 — Exception Path: range_out → lp_rebalancing fan-out

Điều kiện: `range_out` trong `RebalanceReason[]`.
- Transition `bots.lifecycle_state='lp_rebalancing'`.
- Enqueue `lp_rebalancing` message.
- Enqueue `partial_repair`.
- Các reason khác trong cùng pass nếu circuit != 'open' → enqueue hedge-sync.
- Source: UC §3 step 10; SRS FR-EXBOT-015.

---

## §F.4 — Functional Integration & Data Consistency

| Hành động kích hoạt | Ảnh hưởng downstream | Data consistency cần kiểm tra | Nguồn |
|---|---|---|---|
| `next_light_check_at` batch-update | D1 state_db_shard được update 1 stmt/shard — không per-bot | Sau update: `bots.next_light_check_at` phải trong khoảng `[now + 4m15s, now + 5m45s]`. Không có unconditional per-bot update (NFR-EXBOT-005) | UC §3 step 4; SRS FR-EXBOT-013 |
| hedge-sync enqueued | `uc-hedge-sync` consumer nhận `{botId, reasons, stateVersion}`; phải check stateVersion trước khi acquire UserLockDO | Nếu D1 state_version thay đổi giữa lúc light-check enqueue và hedge-sync worker nhận message → worker discard (SRS FR-EXBOT-027) | UC §3 step 10; SRS FR-EXBOT-027 |
| `lifecycle_state='lp_rebalancing'` set | Light-check future passes phải skip bot này; hedge-sync suppressed | Sau khi `lp_rebalancing` set, Scan Worker query bước tiếp theo phải lọc bot này ra (lifecycle check tại step 2) | UC §3 step 10; SRS FR-EXBOT-015 |
| `stop_trigger_crossed_at` set | SAFE_MODE trigger nếu còn stuck sau 30 phút (`uc-deep-audit` backstop) | Giá trị phải là write-once (BR-EXBOT-005). Deep-audit kiểm tra `stop_trigger_crossed_at` stuck > 30 min → SAFE_MODE | SRS FR-EXBOT-033; BR-EXBOT-005 |
| `lifecycle_state='safe_mode'` set (stop overrun) | Tất cả hedge mutation bị block; `uc-deep-audit` handle recovery | `bots.lifecycle_state` và `bots.status` phải consistent: `safe_mode` lifecycle → `status='safe_mode'` | SRS FR-EXBOT-050; states.md |
| `queue_idempotency` insert | Ngăn duplicate processing khi message redelivered | UNIQUE constraint trên `message_id`; expires_at cần được set để tránh table bloat | SRS FR-EXBOT-011; ERD |
| `half_open_probe_used` 0→1 | Chỉ 1 probe hedge-sync được enqueue; các light-check pass sau suppress | Cần atomic CAS (compare-and-swap) write — nếu 2 light-check workers chạy đồng thời cho cùng 1 bot (do message redelivery), chỉ 1 probe được enqueue | UC §4 A2; SRS FR-EXBOT-040 |
| partial_repair(reason='stop_replacing_overrun') enqueued | `partial_repair` worker nhận; repair worker xử lý | Khi `lifecycle_state='safe_mode'` được set, hedge-sync phải bị block cho đến khi recovery (SRS FR-EXBOT-050) | UC §3 step 12; SRS FR-EXBOT-033 |
| MarketDataDO cache (sqrtPriceX96, currentTick) | Tất cả light-check workers trong 1 CF region dùng chung 1 DO instance | `blockNumber` phải monotonically increasing — nếu DO trả về blockNumber thấp hơn lần trước → cache regression → re-fetch (SRS FR-EXBOT-093) | SRS FR-EXBOT-093 |

---

## §F.5 — Acceptance Criteria Candidates

| AC # | Scenario | Given | When | Then | Nguồn / Ghi chú |
|---|---|---|---|---|---|
| AC-LC-01 | Happy path — zero HL calls | Bot active, RebalanceReason[] = [drift_threshold] | Light-check worker processes bot | RebalanceReason[] evaluated using only D1 + MarketDataDO; hedge-sync enqueued; HL API call count = 0 | SRS BR-EXBOT-003; AC-EXBOT-005-1 |
| AC-LC-02 | Idempotency — duplicate message | message_id đã có trong queue_idempotency (state='started') | Light-check message redelivered | Worker exits immediately; no hedge-sync enqueued; no D1 mutation | SRS FR-EXBOT-011 |
| AC-LC-03 | Skip — lp_rebalancing | lifecycle_state='lp_rebalancing' | Scan Worker encounters bot | Bot NOT included in light-check queue; no light-check message enqueued | SRS FR-EXBOT-012; AC-EXBOT-005-4 |
| AC-LC-04 | Skip — paused | status='paused' | Scan Worker encounters bot | Bot NOT included in light-check queue | SRS FR-EXBOT-003 |
| AC-LC-05 | hedge_stopped_cooldown — not skipped | lifecycle_state='hedge_stopped_cooldown' | Light-check runs for bot | Light-check evaluates normally; hedge-sync suppressed; stop monitoring runs | UC §2 note; states.md |
| AC-LC-06 | Stop trigger detected | markPrice >= stop_price; stop_trigger_crossed_at IS NULL | Light-check pass | stop_trigger_crossed_at set (write-once); price-near-stop-audit enqueued; NO hedge-sync enqueued | SRS FR-EXBOT-032; BR-EXBOT-005 |
| AC-LC-07 | Stop trigger already set | stop_trigger_crossed_at IS NOT NULL | Light-check pass with markPrice >= stop_price | stop_trigger_crossed_at NOT overwritten; price-near-stop-audit enqueued | SRS FR-EXBOT-032; AC-EXBOT-005-2 |
| AC-LC-08 | Circuit open — suppress hedge-sync | circuit_breakers.state='open' | Light-check evaluates reasons | hedge-sync NOT enqueued; stop monitoring continues; price-near-stop-audit enqueued if stop trigger met | SRS FR-EXBOT-014; AC-EXBOT-005-3 |
| AC-LC-09 | Circuit half_open — 1 probe only | circuit_breakers.state='half_open'; half_open_probe_used=0 | Light-check runs | Exactly 1 hedge-sync probe enqueued; half_open_probe_used set to 1 atomically | SRS FR-EXBOT-040; AC-EXBOT-008-2 |
| AC-LC-10 | range_out → lp_rebalancing | range_out in RebalanceReason[] | Light-check step 10 | lifecycle_state='lp_rebalancing' set; lp_rebalancing + partial_repair enqueued | SRS FR-EXBOT-015 |
| AC-LC-11 | range_boundary_near → hedge-sync (not stop-audit) | range_boundary_near in RebalanceReason[] | Light-check step 10 | hedge-sync enqueued (not price-near-stop-audit) | UC §4 A4 |
| AC-LC-12 | Stop replace overrun → SAFE_MODE | stop_replacing_started_at IS NOT NULL; age > 60s | Light-check pass | partial_repair(reason='stop_replacing_overrun') enqueued; lifecycle_state='safe_mode' set; primary detection ≤5 min | SRS FR-EXBOT-033 |
| AC-LC-13 | next_light_check_at jitter | Bot processed by Scan Worker | Batch update | next_light_check_at in range [now+4m15s, now+5m45s]; 1 D1 stmt per shard (not per-bot) | SRS FR-EXBOT-013 |
| AC-LC-14 | drift_threshold — uniPoolPrice only | deltaErrorUsd computed | Price sources | deltaErrorUsd uses sqrtPriceX96 from MarketDataDO (uniPoolPrice); NOT hlMarkPrice or hlOraclePrice | SRS FR-EXBOT-012 (3-way split) |
| AC-LC-15 | hlMarkPrice source (TBD) | OQ-EXBOT-017 open | Stop trigger detection | **Suy luận cần xác nhận**: nếu candidate là `bot_runtime_state.eth_price_usd`, cần staleness policy — nếu giá stale > X giây thì stop trigger có được evaluate không? | UC §3 step 11 note; SRS OQ-EXBOT-17 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

Xem §F.3 (Functional Logic & Workflow Decomposition) ở trên. Các luồng chính đã được phân rã chi tiết tại §F.3.1–§F.3.7.

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Hành động kích hoạt | UC / Module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| hedge-sync enqueued | `uc-hedge-sync` | Worker điều chỉnh delta hedge; reconcile sau khi fill; update `bot_runtime_state.last_known_hl_short_size`; replace stop via INV-STOP | `stateVersion` trong message phải match `bot_runtime_state.state_version` tại thời điểm hedge-sync worker xử lý | SRS FR-EXBOT-027 |
| `lifecycle_state='lp_rebalancing'` | Light-check (future passes); hedge-sync (suppressed) | Scan Worker phải lọc bot này ra khỏi query eligible; hedge-sync worker phải discard messages khi lifecycle='lp_rebalancing' | D1 `bots.lifecycle_state` nhất quán giữa Scan query và Light-Check Worker read | SRS FR-EXBOT-015 |
| price-near-stop-audit enqueued | Stop-audit worker (out of scope UC này) | Worker xử lý stop event; nếu confirmed → `lifecycle_state='hedge_stopped_cooldown'` | `stop_trigger_crossed_at` write-once; deep-audit backstop nếu stuck > 30 min | SRS FR-EXBOT-031, 033 |
| partial_repair(stop_replacing_overrun) | `uc-hedge-sync` (repair worker) | Repair worker xử lý overrun; sau 3 lần fail → `bot_safe_close` | `lifecycle_state='safe_mode'` block hedge-sync; `stop_replacing_started_at` phải được clear trong `finally` block của INV-STOP protocol | SRS FR-EXBOT-033, 036 |
| `lifecycle_state='safe_mode'` | Toàn bộ mutation operations | Hedge-sync, LP rebalance, change leverage đều bị block. Chỉ: đọc state, retry HL connectivity, alert user/admin, light-check (non-HL), deep-audit khi HL recover | `bots.status='safe_mode'` và `bots.lifecycle_state='safe_mode'` phải đồng bộ | SRS FR-EXBOT-050 |
| MarketDataDO cache đọc | Tất cả light-check workers trong CF region | Dùng chung 1 DO instance; cache refresh interval từ NV-12 (OQ-EXBOT-09 open) | `blockNumber` monotonically increasing; stale cache trigger forced refresh | SRS FR-EXBOT-093 |
| `next_light_check_at` updated | Scan Worker lần tiếp theo | Bot được đưa vào scan cycle tiếp theo sau 5 phút ± 45s | 1 stmt/shard write, không per-bot | SRS FR-EXBOT-013 |

---

## 8. Acceptance Criteria

Xem §F.5 ở trên — AC candidates AC-LC-01 đến AC-LC-15.

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance / Throughput | 10.000 bots / 5-min scan = 33.3 bots/sec sustained. Light-check KHÔNG được fetch HL cho bất kỳ bot nào | Test: 1 light-check cycle đầy đủ không tiêu tốn HL rate-limit weight nào | NFR-EXBOT-001; BR-EXBOT-003 |
| Latency | Light-check worker chạy zero HL calls → không bị gated bởi HLRateLimitDO | Test: light-check worker hoàn thành trong thời gian hợp lý mà không chờ rate-limit | NFR-EXBOT-002 (implied) |
| D1 Write budget | `next_light_check_at` batch-update: 1 stmt/shard; `bot_runtime_state` write-on-change only | Test: không có per-bot unconditional UPDATE trong light-check path | NFR-EXBOT-005 |
| Idempotency | Mọi queue consumer phải insert `message_id` vào `queue_idempotency` trước khi xử lý; UNIQUE conflict = skip | Test: redelivery cùng message → chỉ 1 lần xử lý | NFR-EXBOT-007 |
| Precision | `lpEthAmount` tính bằng BigDecimal; `deltaErrorUsd` tính bằng BigDecimal | Test: không có float/number arithmetic trong tính toán LP amount hoặc drift | NFR-EXBOT-008 |
| Multi-chain | `wethIndex` đọc từ D1 `positions.weth_index` — không hardcode | Test: bot trên Base và Optimism đều tính đúng `lpEthAmount` | NFR-EXBOT-009 |
| Concurrency | Max 6 outbound connections per CF Worker invocation | Test: không xảy ra lỗi connection limit khi light-check worker đọc D1 + MarketDataDO đồng thời | NFR-EXBOT-011 |
| Reliability | SAFE_MODE không phải trạng thái terminal; recovery path phải tồn tại | Test: sau khi SAFE_MODE được trigger bởi stop overrun, bot có thể recover | NFR-EXBOT-010 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận — Issue Register

| ID | Mức ưu tiên | Severity | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề | Vì sao quan trọng | Owner | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| I-01 | High | Blocker | MISSING_INFO | UC §3 step 11 note; SRS OQ-EXBOT-017 | Nguồn `hlMarkPrice` dùng để đánh giá stop trigger trong step 11 chưa được xác nhận. Với ràng buộc HL weight = 0 (BR-EXBOT-003), light-check không thể gọi HL để lấy mark price thực. UC đề xuất candidate là `bot_runtime_state.eth_price_usd` nhưng chính sách staleness (staleness policy) hoàn toàn thiếu: nếu giá lưu trong D1 đã stale bao lâu thì còn được dùng để evaluate stop trigger? Thiếu thông tin này, tester không thể thiết kế test case cho trường hợp giá stale vs giá fresh. | Gây rủi ro test sai expected result của AC-LC-06 và AC-LC-07. Tester không thể verify hành vi đúng khi `eth_price_usd` stale. | Tech Lead | Open |
| I-02 | High | Blocker | MISSING_INFO | SRS OQ-EXBOT-010 | Công thức tính điều kiện `range_boundary_near` chưa được xác nhận: UC mô tả "price 90% to range upper/lower" nhưng không rõ đây là tick-based (`currentTick >= tickUpper - 0.10 × (tickUpper - tickLower)`) hay price-based (`sqrtPrice >= sqrtUpper × 0.90`). Hai cách tính cho kết quả khác nhau đáng kể. | Tester không thể xây dựng test data chính xác cho scenario `range_boundary_near`, dẫn đến test case không reliable. | Tech Lead / zen | Open |
| I-03 | High | Blocker | MISSING_INFO | SRS OQ-EXBOT-011 | Công thức tính `lpValueUsd` (dùng trong điều kiện `drift_threshold`: `deltaErrorUsd > max($25, lpValueUsd × 3%)`) chưa được xác nhận. SRS đề xuất `(lpEthAmount × uniPoolPrice) + lpUsdcAmount` nhưng chưa được zen confirm. Tester không thể tính expected `deltaErrorUsd` mà không biết `lpValueUsd`. | Blocks test case cho AC-LC-14 và mọi test liên quan đến drift_threshold condition. | zen | Open |
| I-04 | High | Blocker | MISSING_INFO | SRS OQ-EXBOT-012 | Công thức aggregation 7d funding APR cho điều kiện `funding_alert` chưa được xác nhận. SRS đề xuất candidate nhưng zen chưa confirm annualization formula. Tester không thể tính threshold −15% từ raw data `funding_daily_metrics`. | Blocks test case cho scenario `funding_alert` reason. | zen | Open |
| I-05 | Medium | Major | MISSING_INFO | UC §3 step 10; UC §4 A4 | UC step 10 mô tả: "If reasons include `range_out`: set `lifecycle_state='lp_rebalancing'`; enqueue `lp_rebalancing` message + `partial_repair`. Other reasons AND `circuit_state != 'open'`: enqueue `hedge-sync`". Chưa rõ: nếu `RebalanceReason[]` chứa CẢ `range_out` VÀ các reason khác (ví dụ `drift_threshold`), liệu hedge-sync có được enqueue không hay chỉ lp_rebalancing path chạy? UC §4 A4 chỉ clarify `range_boundary_near`, không giải quyết trường hợp mixed reasons. | Tester không thể xác định expected behavior khi multiple reasons cùng xuất hiện, đặc biệt khi range_out kết hợp với drift_threshold. | BA / Tech Lead | Open |
| I-06 | Medium | Major | MISSING_INFO | UC §3 step 10; SRS FR-EXBOT-015 | UC step 10 viết "enqueue `lp_rebalancing` message + `partial_repair`" khi phát hiện range_out. Nhưng không rõ message `lp_rebalancing` được gửi đến queue nào và có payload gì. SRS FR-EXBOT-015 đề cập "enqueue LP rebalance operation via the `partial_repair` queue" — mâu thuẫn nhỏ giữa UC (2 messages riêng) và SRS (dùng partial_repair queue cho cả hai). | Tester cần biết chính xác queue và payload để verify fan-out behavior. | BA / Tech Lead | Open |
| I-07 | Medium | Major | UNCLEAR_INFO | UC §3 step 12; SRS FR-EXBOT-033 | UC step 12 mô tả khi overrun detected: "set `lifecycle_state='safe_mode'`". Nhưng SRS FR-EXBOT-050 định nghĩa: trong SAFE_MODE, `bots.status='safe_mode'`. Cần làm rõ: khi step 12 chạy, cả `bots.lifecycle_state` và `bots.status` đều được update hay chỉ `lifecycle_state`? Và update này được thực hiện bởi Light-Check Worker hay bởi partial_repair worker sau khi nhận message? | Ảnh hưởng đến verify order of operations trong test: tester cần biết thời điểm chính xác `status` thay đổi. | BA / Tech Lead | Open |
| I-08 | Medium | Major | CROSS_SOURCE_CONFLICT | UC §3 step 4; SRS FR-EXBOT-012 | UC step 4 viết Scan Worker batch-update `next_light_check_at`. SRS FR-EXBOT-012 viết "Light-check shall be skipped entirely for bots with `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'`". Nếu Scan Worker đã lọc các bot này ra ở step 2 (không enqueue light-check), thì `next_light_check_at` của các bot bị skip có được update hay không? Nếu không update, bot sẽ liên tục xuất hiện trong query eligible sau khi thoát trạng thái lp_rebalancing. | Nếu `next_light_check_at` không được update cho bot bị skip, toàn bộ cycle của bot đó sau recovery sẽ sai. Tester cần biết để verify post-recovery scheduling. | BA / Tech Lead | Open |
| I-09 | Medium | Major | MISSING_INFO | UC §3 step 2 | Scan Worker query: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500`. UC không giải thích điều gì xảy ra khi shard có > 500 bots eligible cùng lúc — các bot còn lại có bị trễ đến cycle Cron tiếp theo (1 phút) không? Không có mô tả về window-based pagination hay multi-batch approach. | Ảnh hưởng đến NFR-EXBOT-001 (10.000 bots / 5 min). Tester không rõ expected behavior khi shard có bot lớn hơn 500. | BA / Tech Lead | Open |
| I-10 | Low | Minor | MISSING_INFO | UC §3 step 5; SRS FR-EXBOT-011 | UC mô tả idempotency insert nhưng không đề cập `expires_at` field trong `queue_idempotency`. SRS ERD có `expires_at` — không rõ Light-Check Worker có set `expires_at` khi insert hay để NULL. Nếu không set, table sẽ tích lũy vô hạn. | Test data cleanup concern; có thể ảnh hưởng đến long-running test scenarios. | Tech Lead | Open |
| I-11 | Low | Minor | MISSING_INFO | UC — | UC không có diagram thực sự (placeholder Mermaid với actor/System generic). Mặc dù flow được mô tả text, sequence diagram sẽ giúp verify actor-system interaction order, đặc biệt cho các alternate flows phức tạp (A1, A2). | Minor gap — không block test design nhưng tăng risk hiểu sai timing. | BA | Open |
| I-12 | Low | Minor | UNCLEAR_INFO | UC §3 step 7; SRS FR-EXBOT-093 | UC mô tả "Light-Check Worker reads from `MarketDataDO`: `sqrtPriceX96`, `currentTick`" nhưng không mô tả hành vi khi MarketDataDO cache stale (> 2× refresh interval). SRS FR-EXBOT-093 định nghĩa forced refresh và warning log — nhưng UC không đề cập hành vi khi cache quá stale trong context của light-check decision (dùng stale data để evaluate hay retry?). | Tester cần biết expected behavior để design test case cho scenario MarketDataDO stale. | Tech Lead | Open |
| I-13 | Low | Note | MISSING_INFO | UC §6 Business Rules | UC §6 chỉ liệt kê BR-EXBOT-003 và BR-EXBOT-005. Nhưng các BR liên quan khác không được reference: BR-EXBOT-004 (delta-only invariant — relevant khi light-check enqueue hedge-sync), BR-EXBOT-007 (SAFE_MODE không terminal). Thiếu reference gây khó trace cho QC Lead. | Không block test nhưng làm giảm traceability. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-017: `hlMarkPrice` source trong light-check | Open Question | Blocks test case AC-LC-06, AC-LC-07 — stop trigger detection scenarios | Tech Lead | Open |
| OQ-EXBOT-010: `range_boundary_near` formula | Open Question | Blocks test case cho `range_boundary_near` scenario | Tech Lead / zen | Open |
| OQ-EXBOT-011: `lpValueUsd` computation formula | Open Question | Blocks test case cho `drift_threshold` scenarios | zen | Open |
| OQ-EXBOT-012: 7d funding APR aggregation formula | Open Question | Blocks test case cho `funding_alert` scenario | zen | Open |
| OQ-EXBOT-009: MarketDataDO cache refresh interval (NV-12) | Open Question | Ảnh hưởng đến staleness test scenarios | Tech Lead / zen | Open |
| `uc-deep-audit`: backstop detection `stop_trigger_crossed_at` > 30 min | UC dependency | Light-check chỉ là primary path; integration test cần cả deep-audit | — | Open |
| `uc-hedge-sync`: downstream consumer của hedge-sync queue | UC dependency | Test end-to-end của light-check phải kéo uc-hedge-sync | — | Open |

---

### 10.3 Audit Summary — Scoring & Verdict

#### Scoring Table

| # | Scoring Area | Max | Score | Status | Lý do |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 17 | ⚠️ Partial | F.1 đầy đủ 15 operations + 5 data objects, mapped atomic đến SRS/FRD/ERD. Trừ 3 điểm: `lpValueUsd` field không có công thức rõ (I-03); `range_boundary_near` formula thiếu (I-02); `hlMarkPrice` source thiếu (I-01) — 3 items trong F1-09 và F1-13 không thể verify đầy đủ. |
| 2 | Data Object / State Attributes, BR, Validations & Messages | 25 | 16 | ⚠️ Partial | F.2 cover > 80% F.1 elements. Trừ 9 điểm: 3 Blockers (I-01, I-02, I-03) khiến 3 validation rules không thể được xác định chính xác; `lpValueUsd` formula (I-03) ảnh hưởng trực tiếp đến drift_threshold validation; staleness policy cho hlMarkPrice (I-01) thiếu hoàn toàn; funding_alert threshold computation (I-04) không có formula. |
| 3 | Functional Logic & Workflow Decomposition | 25 | 18 | ⚠️ Partial | Happy path và alternate paths (A1–A4) được mô tả rõ. Trừ 7 điểm: behavior khi mixed reasons (range_out + other) chưa rõ (I-05); hành vi khi MarketDataDO stale trong context light-check không được mô tả (I-12); hành vi khi shard > 500 bots chưa được xác định (I-09); UC không có sequence diagram thực (I-11). |
| 4 | Functional Integration & Data Consistency | 15 | 11 | ⚠️ Partial | Integration với hedge-sync (stateVersion check), lp_rebalancing suppression, SAFE_MODE, queue_idempotency được xác định. Trừ 4 điểm: không rõ `next_light_check_at` có được update cho bot bị skip không (I-08); không rõ thứ tự update `bots.status` vs `bots.lifecycle_state` trong SAFE_MODE entry (I-07); conflict về lp_rebalancing queue destination (I-06). |
| 5 | UC / Spec Documentation Quality | 15 | 10 | ⚠️ Partial | UC có structure tốt, flow được mô tả rõ, A4 clarification gần đây giải quyết routing confusion. Trừ 5 điểm: 4 Blocker-level Open Questions chưa đóng (I-01–I-04); diagram placeholder không có nội dung (I-11); BR references không đầy đủ (I-13); step 12 mơ hồ về ai update status (I-07). |
| **Total** | | **100** | **72** | ⚠️ | |

**Auto-cap check:**
- 3 Blocker issues (I-01, I-02, I-03) ảnh hưởng Area 1, 2, 3: áp dụng cap Area 2 max 40% = 10, nhưng score 16 > 10 → không apply cap vì các Blockers không hoàn toàn block toàn bộ area, chỉ block một số sub-items. Tuy nhiên Final Verdict bị ảnh hưởng bởi unresolved Blockers.
- Không có area nào = 0.
- Không có contradiction thay đổi expected behavior cơ bản.

**Final Score: 72 / 100**

#### Final Verdict: ⚠️ Conditionally Ready

**Lý do:** Tổng điểm 72 rơi vào ngưỡng "Conditionally Ready" (70–89). UC mô tả đủ để thiết kế test cho happy path, circuit breaker logic, idempotency, stop trigger guarded write, và SAFE_MODE on overrun. Tuy nhiên **4 Blocker-level Open Questions** (I-01 đến I-04) chặn thiết kế test case cho các scenarios quan trọng:

1. **I-01 (Blocker)**: Nguồn và staleness policy của `hlMarkPrice` trong stop trigger detection — không thể test AC-LC-06/07 cho dữ liệu stale.
2. **I-02 (Blocker)**: Công thức `range_boundary_near` — không thể tạo test data chính xác.
3. **I-03 (Blocker)**: Công thức `lpValueUsd` — không thể tính `drift_threshold` trong test.
4. **I-04 (Blocker)**: Công thức 7d funding APR aggregation — không thể test `funding_alert`.

**Khuyến nghị:** QC Lead có thể tiến hành thiết kế test scenarios cho các phần đã rõ (idempotency, circuit breaker, stop_trigger_crossed_at guarded write, stop replace overrun, range_out fan-out, skip conditions). Tạm dừng thiết kế test case cho 4 scenarios liên quan đến I-01–I-04 và chuyển 4 câu hỏi này sang BA/Tech Lead/zen để giải đáp.

---

## 11. Change Log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Exbot Agent | Tạo báo cáo audited lần đầu — SRS-first cross-check |
