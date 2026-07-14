# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Document title:** UC-EXBOT-light-check — Light-Check Readiness Review  
**Date created:** 2026-07-14  
**Author/Agent:** QC UC Read Agent (qc-uc-read-exbot)  
**Version:** v4

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-light-check mô tả quy trình kiểm tra sức khoẻ định kỳ 5 phút cho mỗi bot delta-hedge trên hệ thống ExBot. Đây là use case backend-only, không có giao diện, chạy hoàn toàn trên AWS (EventBridge Scheduler → SQS → Lambda). Điểm đặc trưng kiến trúc quan trọng nhất: **mọi chu kỳ light-check đều có đúng 0 lần gọi Hyperliquid API** — giá pool được lấy từ Pool Slot0 Cache (ElastiCache Redis), giá mark ETH lấy từ HL Mark Price Cache (ElastiCache Redis), mọi tính toán còn lại dùng Aurora PostgreSQL.

Mỗi chu kỳ gồm hai giai đoạn độc lập về logic: (1) **Trigger evaluation** — đọc trạng thái bot từ Aurora PostgreSQL và Pool Slot0 Cache, tính toán `RebalanceReason[]` dựa trên công thức local, nếu có trigger và circuit_breaker không ở trạng thái `open` thì enqueue 1 tin nhắn hedge-sync; và (2) **Stop monitoring** — đọc `markPriceUsd` từ HL Mark Price Cache, đánh giá ngưỡng stop, guard ghi `stop_trigger_crossed_at`, enqueue `price-near-stop-audit` nếu cần. Giai đoạn stop monitoring luôn chạy kể cả khi circuit_breaker đang `open`.

UC này là điểm kích hoạt quan trọng trong toàn bộ vòng đời bot: nó quyết định khi nào cần rebalance LP, khi nào cần điều chỉnh hedge, khi nào cần kích hoạt safe_mode (qua overrun check ở step 12). Các use case phụ thuộc vào output của light-check bao gồm hedge-sync, LP rebalance (US-EXBOT-007), circuit breaker state machine (US-EXBOT-008), và stop-replace flow.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check | 2026-07-14 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | QC Lead | 2026-06-12 | 2026-07-14 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò | Ghi chú |
|---|---|---|---|
| `usecases/uc-light-check.md` | 2026-07-14 | UC | Source chính |
| `srs/spec.md` | 2026-07-14 | SRS | Baseline source of truth |
| `srs/states.md` | 2026-07-14 | SRS / State diagram | Lifecycle state registry |
| `srs/erd.md` | 2026-07-14 | ERD | Schema & table defs |
| `srs/flows.md` | 2026-07-14 | Flow diagram | F-01 queue fan-out |
| `frd.md` | 2026-07-14 | FRD | FR-EXBOT-* defs |
| `userstories/us-005.md` | 2026-07-14 | User Story | US-EXBOT-005 light-check worker |
| `userstories/us-006.md` | 2026-07-14 | User Story | US-EXBOT-006 scan worker |
| `userstories/us-007.md` | 2026-07-14 | User Story | US-EXBOT-007 LP range rebalance |
| `userstories/us-008.md` | 2026-07-14 | User Story | US-EXBOT-008 circuit breaker |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Light-check đảm bảo mỗi bot delta-hedge được kiểm tra định kỳ để phát hiện sớm các tình huống cần rebalance LP, điều chỉnh hedge, hoặc chuyển sang trạng thái an toàn — tất cả mà không tốn tải gọi HL API (BR-EXBOT-003). Mục tiêu: duy trì trạng thái bot chính xác, phát hiện ngưỡng stop trigger kịp thời, và fan-out sang các worker xử lý chuyên biệt (hedge-sync, price-near-stop-audit, partial_repair).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Scan & dispatch | EventBridge Scheduler → Scan Worker query bots eligible → enqueue per-bot light-check messages | UC §3 step 1-4; FR-EXBOT-011 |
| Idempotency guard | Insert `queue_idempotency` với expires_at=now+1min; skip nếu UNIQUE conflict | UC §3 step 5; FR-EXBOT-011 AC |
| Trigger evaluation | Đọc Pool Slot0 Cache, tính `RebalanceReason[]`, enqueue hedge-sync nếu cần | UC §3 step 6-10; FR-EXBOT-012, 013, 014, 015, 016, 023 |
| Stop monitoring | Đọc HL Mark Price Cache, đánh giá stop trigger, guard write-once, enqueue PSAQ | UC §3 step 11; FR-EXBOT-032 |
| Overrun check | Step 12: nếu stop_replacing_started_at overrun > 60s → atomically set safe_mode | UC §3 step 12; FR-EXBOT-033 |
| Circuit breaker integration | Suppress hedge-sync khi circuit `open`; probe hedge-sync khi `half_open` | UC §4 A2, A3; FR-EXBOT-040 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi | Ảnh hưởng đến test |
|---|---|---|
| Hedge-sync worker logic | UC riêng; light-check chỉ enqueue | Tester cần cross-check trigger với hedge-sync UC |
| LP rebalance execution | Thuộc US-EXBOT-007 / hedge-sync worker | Boundary test: light-check enqueue đúng message là đủ |
| `bnza-market-cron` worker | Chưa triển khai ở v1; cập nhật `funding_rolling_metrics` | AC-LC-09 (`funding_alert`) bị block ở v1 scope |
| Admin UI / dashboard | ExBot không có UI | N/A |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn | Nguồn |
|---|---|---|---|---|
| EventBridge Scheduler | System | Kích hoạt 1-minute schedule, gửi `bot-scan` message vào SQS | Chỉ trigger — không đọc/ghi DB | UC §1, §3 step 1 |
| Scan Worker (Lambda) | Primary | Query bots eligible, update `next_light_check_at`, enqueue light-check messages | Đọc/ghi Aurora PostgreSQL; ghi SQS | UC §3 step 2-4; FR-EXBOT-011 |
| Light-Check Worker (Lambda) | Primary | Đọc trạng thái bot, tính triggers, enqueue downstream messages | Đọc Aurora + Redis; ghi SQS; ghi `queue_idempotency` | UC §3 step 5-13; FR-EXBOT-012 |
| Aurora PostgreSQL (state_db_shard) | System | Nguồn dữ liệu trạng thái bot; nhận update `queue_idempotency`, `safe_mode` | Read/write theo worker | UC §1; ERD |
| Pool Slot0 Cache (ElastiCache Redis) | System | Cung cấp `sqrtPriceX96`, `currentTick` cho trigger evaluation | Read-only từ Light-Check Worker | UC §3 step 7; FR-EXBOT-093 |
| HL Mark Price Cache (ElastiCache Redis) | System | Cung cấp `markPriceUsd` cho stop monitoring | Read-only từ Light-Check Worker | UC §3 step 11 |

**Nhận xét readiness:** Actor đủ rõ để thiết kế test. Scan Worker và Light-Check Worker là hai Lambda riêng biệt — tester cần tách test scope giữa hai component này.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot `status = 'active'` và `next_light_check_at <= now` | Yes | UC §2 |
| 2 | `lifecycle_state NOT IN ('lp_rebalancing', 'lp_closing')` | Yes | UC §2 |
| 3 | `status != 'paused'` | Yes | UC §2 |
| 4 | Pool Slot0 Cache (ElastiCache Redis) accessible và snapshot không stale (> 5 min) | Yes (fail-fast nếu vi phạm) | UC §3 step 7; A1 |
| 5 | `lifecycle_state = 'hedge_stopped_cooldown'` KHÔNG là lý do skip — light-check chạy bình thường, chỉ hedge-sync bị suppress | Yes (note) | UC §2 note |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau | Nguồn |
|---|---|---|
| Không có trigger nào fired | `queue_idempotency.state = 'succeeded'`; `next_light_check_at` đã được update ở step 4 | UC §5 |
| Trigger evaluation fired | 1 hedge-sync message enqueued với `{botId, reasons[], stateVersion}`; `queue_idempotency.state = 'succeeded'` | UC §3 step 10 |
| Stop trigger crossed | `stop_trigger_crossed_at` set (write-once guard); `price-near-stop-audit` enqueued | UC §3 step 11 |
| Overrun check triggered | `bots.status = 'safe_mode'` AND `bots.lifecycle_state = 'safe_mode'` set atomically; `partial_repair(reason='stop_replacing_overrun')` enqueued | UC §3 step 12 |
| Pool Slot0 Cache stale / unreachable | Tick skipped hoàn toàn; không có trigger evaluation; `next_light_check_at` vẫn được update ở step 4 | UC §4 A1 |
| Idempotency conflict | Message skipped (UNIQUE conflict trên `queue_idempotency`) | UC §3 step 5 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Scan & Dispatch (Scan Worker)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | EventBridge Scheduler | Fires 1-minute schedule | `bot-scan` message enqueued vào SQS | — | EventBridge retry nếu SQS unavailable | UC §3 step 1 |
| 2 | Scan Worker | Query Aurora PostgreSQL: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now ORDER BY next_light_check_at LIMIT 500` | Trả về danh sách bots eligible (tối đa 500) | Nếu > 500 bots: phần vượt xử lý ở tick tiếp theo (oldest first); jitter ±45s ngăn overflow ở steady state | Aurora unavailable → Lambda error/retry | UC §3 step 2 |
| 3 | Scan Worker | Update `next_light_check_at = now + 5min + jitter(±45s)` cho **mọi** eligible bot (kể cả `lp_rebalancing`, `lp_closing`) | `next_light_check_at` updated trước khi enqueue | Bots bị skip bởi Light-Check Worker (vì `lifecycle_state`) vẫn được rescheduled đúng | — | UC §3 step 4 |
| 4 | Scan Worker | `chunkSendBatch` per-bot messages vào `light-check` queue | Mỗi bot có 1 SQS message với `botId` | — | SQS batch failure → partial retry | UC §3 step 3 |

#### B. Business rules và validations

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả hợp lệ | Kết quả không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `LIMIT 500` per shard | By design — jitter ±45s phân tán đều | Yes | Xử lý tuần tự, overflow sang tick tiếp theo | Không có — overflow là behavior by design | UC §3 step 2 |
| `next_light_check_at` update scope | **Mọi** eligible bot, kể cả bots sẽ bị skip | Yes | Bots không bị flood khi recovery | Nếu chỉ update bots được xử lý: bots skip sẽ bị enqueue liên tục khi recovery | UC §3 step 4 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| SQS batch partial failure | Lambda retry | Lambda function error; SQS visibility timeout xử lý retry | — | FR-EXBOT-011 |

---

### 6.2 Light-Check Worker — Idempotency Guard

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Nguồn |
|---|---|---|---|---|---|
| 1 | Light-Check Worker | Dequeue SQS message; insert `(message_id, state='started', expires_at=now+1min)` vào `queue_idempotency` | Insert thành công; tiếp tục xử lý | UNIQUE conflict → skip toàn bộ message (idempotency guard) | UC §3 step 5; FR-EXBOT-011 |
| 2 | EventBridge cron (hourly) | `DELETE FROM queue_idempotency WHERE expires_at < now` | Bảng được purge định kỳ | — | FR-EXBOT-011 AC; UC §3 step 5 note |

#### B. Business rules và validations

| Field | Constraint | Nguồn |
|---|---|---|
| `expires_at` | Luôn được set = now+1min khi insert; **không bao giờ** để NULL | FR-EXBOT-011 AC |
| UNIQUE conflict | Skip hoàn toàn — không retry, không log error | UC §3 step 5 |

---

### 6.3 Light-Check Worker — Trigger Evaluation

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Happy path | Luồng thay thế | Nguồn |
|---|---|---|---|---|---|
| 1 | Light-Check Worker | Đọc Aurora PostgreSQL: `bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs` (stop_price, margin_status), `circuit_breakers.state` | Dữ liệu đọc thành công | Aurora unavailable → Lambda error | UC §3 step 6 |
| 2 | Light-Check Worker | Đọc Pool Slot0 Cache: `sqrtPriceX96`, `currentTick` | Cache hit; snapshot fresh (age <= 5 min) | Stale (> 5 min) hoặc unreachable → **skip tick hoàn toàn** (A1) | UC §3 step 7; FR-EXBOT-093 |
| 3 | Light-Check Worker | Tính `lpEthAmount` qua TickMath + LiquidityAmounts (local, zero RPC) | `lpEthAmount` computed | — | UC §3 step 8 |
| 4 | Light-Check Worker | Evaluates `RebalanceReason[]` (7 trigger types từ FR-EXBOT-023) | `decision.reason[]` populated | Không trigger nào fired → `decision.action = HOLD` | UC §3 step 9; FR-EXBOT-023 |
| 5 | Light-Check Worker | Strategy engine: nếu `action = REBALANCE` AND `circuit_breakers.state != 'open'` → enqueue 1 hedge-sync message | hedge-sync enqueued với `{botId, reasons[], stateVersion}` | `circuit open` → suppress (A2); `circuit half_open` → probe hedge-sync (A3) | UC §3 step 10; FR-EXBOT-040 |

#### B. Business rules và validations — RebalanceReason triggers

| Trigger | Điều kiện fired | Formula / threshold | Nguồn |
|---|---|---|---|
| `range_out` | Price nằm ngoài LP tick range | `currentTick < tickLower OR currentTick > tickUpper` | FR-EXBOT-013 |
| `range_boundary_near` | Price gần boundary | `min(distToLower, distToUpper) / halfRange <= rangeBoundaryFraction` (default 0.9) | FR-EXBOT-014; UC step 9 |
| `drift_threshold` | Hedge drift vượt ngưỡng | `abs(actualShort - targetShort) >= max($25, lpValueUsd × 3%)` where `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)` | FR-EXBOT-015; UC step 9 |
| `drift_relative` | Drift tương đối | Defined in FR-EXBOT-016 (formula in SRS) | FR-EXBOT-016 |
| `range_boundary_near` (stop band) | Xem stop monitoring | Covered in §6.4 | FR-EXBOT-032 |
| `margin_warning` | Margin status critical | `margin_status = 'warning'` or below | FR-EXBOT-023 |
| `funding_alert` | 7d funding APR < -15% | Primary: `fundingApr7dPct` từ `funding_rolling_metrics`; Fallback: `fundingRate × 8760` | FR-EXBOT-023; UC step 9 |
| `time_fallback` | Thời gian từ last rebalance vượt threshold | Threshold in FR-EXBOT-023 | FR-EXBOT-023 |

**Note (v1 scope):** `funding_rolling_metrics` bảng tồn tại trong ERD nhưng `bnza-market-cron` worker chưa triển khai ở v1 → bảng trống → `funding_alert` luôn dùng fallback `fundingRate × 8760` ở v1.

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung | Nguồn |
|---|---|---|---|
| Circuit `open` | Suppress hedge-sync; continue to stop monitoring | hedge-sync không được enqueue | UC §4 A2 |
| Circuit `half_open` | Probe: claim `half_open_probe_used` atomically; enqueue 1 probe hedge-sync | Circuit half_open probe | UC §4 A3; FR-EXBOT-040 |
| Pool Slot0 Cache stale | Skip tick entirely | Không enqueue bất kỳ message nào; `next_light_check_at` đã updated ở Scan Worker | UC §4 A1 |

---

### 6.4 Light-Check Worker — Stop Monitoring

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Happy path | Luồng thay thế | Nguồn |
|---|---|---|---|---|---|
| 1 | Light-Check Worker | Đọc `markPriceUsd` từ HL Mark Price Cache (ElastiCache Redis) | Cache hit; `updatedAt <= 120s` → fresh | Stale (`updatedAt > 120s`): widen near-stop band 2%→4%; freeze routine hedge-sync; fallback `bot_runtime_state.eth_price_usd` | UC §3 step 11 |
| 2 | Light-Check Worker | So sánh `markPrice >= stop_price` | `markPrice < stop_price` → không action | `markPrice >= stop_price` → set `stop_trigger_crossed_at` (write-once guard per BR-EXBOT-005); enqueue `price-near-stop-audit` | UC §3 step 11 |
| 3 | Light-Check Worker | Check `stop_replacing_started_at`: nếu set và overrun > 60s | `stop_replacing_started_at` not set → không action | Overrun: atomically set `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` → enqueue `partial_repair(reason='stop_replacing_overrun')` | UC §3 step 12 |

#### B. Business rules và validations

| Rule | Nội dung | Nguồn |
|---|---|---|
| BR-EXBOT-003 | HL weight = 0 — mọi lần đọc HL data phải qua cache, không gọi HL API trực tiếp. Vi phạm BR-EXBOT-003 là lỗi kiến trúc. | UC §6; SRS BR-EXBOT-003 |
| BR-EXBOT-005 | `stop_trigger_crossed_at` là write-once field. Nếu đã set → không ghi đè, nhưng vẫn enqueue `price-near-stop-audit`. | UC §4 A4; SRS BR-EXBOT-005 |
| Stop monitoring scope | Stop monitoring **luôn chạy** kể cả khi circuit `open`. Chỉ hedge-sync bị suppress, không phải stop monitoring. | UC §4 A2 |
| Overrun atomicity | `bots.status` và `bots.lifecycle_state` phải được set trong 1 UPDATE duy nhất, **trước** khi enqueue `partial_repair` | UC §3 step 12; FR-EXBOT-033 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Enqueue hedge-sync (trigger fired) | Hedge-sync worker UC | Hedge-sync worker xử lý LP rebalance nếu `range_out` trong `reasons[]`; điều chỉnh hedge cho các trigger khác | `stateVersion` trong message phòng race condition; hedge-sync đọc lại trạng thái mới nhất | UC §3 step 10; US-EXBOT-007 |
| `lifecycle_state = 'lp_rebalancing'` | Light-check tự skip bot này ở precondition | Light-check không chạy khi bot đang rebalance LP — hedge-sync worker set trạng thái này | Tester verify: light-check KHÔNG enqueue khi `lp_rebalancing` | UC §2; US-EXBOT-007 AC-007-4 |
| Enqueue `price-near-stop-audit` | Stop monitoring / audit worker | Audit worker kiểm tra xem có cần trigger stop-replace không | `stop_trigger_crossed_at` là write-once — consistent reads | UC §3 step 11; FR-EXBOT-032 |
| Atomically set `safe_mode` + enqueue `partial_repair` | Bot lifecycle; partial_repair worker | Bot chuyển sang `safe_mode`; partial_repair worker nhận message để repair | Status + lifecycle_state phải nhất quán trong Aurora trước khi partial_repair dequeue | UC §3 step 12; FR-EXBOT-033 |
| Circuit breaker state (`open` / `half_open` / `closed`) | FR-EXBOT-040; US-EXBOT-008 | `open` → suppress hedge-sync; `half_open` → 1 probe hedge-sync | `circuit_breakers.state` là canonical state (ERD bảng riêng `circuit_breakers`, không phải field trong `hedge_legs`) | UC §4 A2-A3; SRS erd.md |
| `funding_rolling_metrics` (v1 empty) | `bnza-market-cron` worker (chưa deploy) | `funding_alert` ở v1 luôn dùng fallback; AC-LC-09 không test được với primary data source | Tester note: v1 = fallback path only | SRS erd.md; spec.md |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-LC-01 | Happy path — trigger fired, hedge-sync enqueued | Bot `status='active'`, `next_light_check_at <= now`, `lifecycle_state='active'`, circuit `closed`, Pool Slot0 Cache fresh | Light-check tick runs; `drift_threshold` fired | 1 hedge-sync message enqueued với `{botId, reasons:['drift_threshold'], stateVersion}`; `queue_idempotency.state='succeeded'` | UC §3 step 9-10, 13 |
| AC-LC-02 | No trigger — no action | Bot `status='active'`, tất cả triggers below threshold | Light-check tick runs | Không có message enqueued; `queue_idempotency.state='succeeded'` | UC §3 step 9-10 |
| AC-LC-03 | Idempotency guard | `message_id` đã có trong `queue_idempotency` (UNIQUE conflict) | Same SQS message delivered again | Message skipped hoàn toàn; không enqueue downstream | UC §3 step 5 |
| AC-LC-04 | Pool Slot0 Cache stale | Cache snapshot age > 5 min | Light-check tick starts | Tick skipped; không enqueue; `next_light_check_at` đã updated (Scan Worker step 4) | UC §4 A1; FR-EXBOT-093 |
| AC-LC-05 | Circuit open — hedge-sync suppressed, stop monitoring continues | Bot circuit_breakers.state='open' | Light-check tick; drift trigger fired | Hedge-sync NOT enqueued; stop monitoring still runs normally | UC §4 A2; FR-EXBOT-040 |
| AC-LC-06 | Circuit half_open — probe hedge-sync | Bot circuit_breakers.state='half_open' | Light-check tick; trigger fired | `half_open_probe_used` claimed atomically; 1 probe hedge-sync enqueued | UC §4 A3; FR-EXBOT-040 |
| AC-LC-07 | Stop trigger crossed | `markPriceUsd >= bot.stop_price`; `stop_trigger_crossed_at` is NULL | Light-check stop monitoring step | `stop_trigger_crossed_at` set; `price-near-stop-audit` enqueued | UC §3 step 11; BR-EXBOT-005 |
| AC-LC-08 | Stop trigger already set (write-once) | `stop_trigger_crossed_at` already set (not NULL) | Light-check stop monitoring step; price still >= stop_price | `stop_trigger_crossed_at` NOT overwritten; `price-near-stop-audit` still enqueued | UC §4 A4; BR-EXBOT-005 |
| AC-LC-09 | Funding alert trigger (v1: fallback path only) | `funding_rolling_metrics` empty (bnza-market-cron not deployed); `fundingRate × 8760 < -15%` | Light-check trigger evaluation | `funding_alert` included in `decision.reason[]`; hedge-sync enqueued | UC §3 step 9; **Blocked in v1 primary path** — chỉ test fallback |
| AC-LC-10 | Overrun check — safe_mode set | `stop_replacing_started_at` set và overrun > 60s | Light-check step 12 | `bots.status='safe_mode'` AND `bots.lifecycle_state='safe_mode'` set atomically; `partial_repair(reason='stop_replacing_overrun')` enqueued AFTER status change | UC §3 step 12; FR-EXBOT-033 |
| AC-LC-11 | HL Mark Price Cache stale — band widening | `markPriceUsd` cache `updatedAt > 120s` | Light-check stop monitoring | Near-stop band widens 2%→4%; routine hedge-sync frozen; fallback `bot_runtime_state.eth_price_usd` used | UC §3 step 11 |
| AC-LC-12 | `lp_rebalancing` bot skipped by Light-Check Worker | Bot `lifecycle_state='lp_rebalancing'` | Light-check message dequeued | Light-Check Worker skips processing; no enqueue | UC §2; US-EXBOT-007 AC-007-4 |
| AC-LC-13 | `hedge_stopped_cooldown` bot — light-check runs, hedge-sync suppressed | Bot `lifecycle_state='hedge_stopped_cooldown'` | Light-check tick | Light-check runs normally; trigger evaluation runs; hedge-sync suppressed for this bot | UC §2 note; SRS states.md |
| AC-LC-14 | `range_out` trigger — range_out in reasons[], LP rebalance handled downstream | `currentTick` outside `[tickLower, tickUpper]` | Light-check trigger evaluation | `range_out` in `decision.reason[]`; 1 hedge-sync enqueued; Light-Check Worker does NOT set `lifecycle_state='lp_rebalancing'` | UC §3 step 10; US-EXBOT-007 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Light-check phải hoàn thành trong Lambda timeout để xử lý 500 bots/tick | Test: verify không có Lambda timeout errors ở load | FR-EXBOT-011 |
| Reliability / Resilience | Idempotency guard via `queue_idempotency` UNIQUE constraint | Test: duplicate SQS message delivery phải bị skip | UC §3 step 5; FR-EXBOT-011 |
| Reliability / Resilience | `next_light_check_at` updated **trước** khi enqueue — Scan Worker step 4 | Test: verify order of operations; bot không bị flood sau crash | UC §3 step 4 |
| Reliability / Resilience | `queue_idempotency` table cần được purge định kỳ (hourly EventBridge cron) | Test: verify cron job tồn tại và xóa rows `expires_at < now` | FR-EXBOT-011 AC |
| Security | BR-EXBOT-003: zero HL API calls trong mọi light-check tick | Test: network trace / mock HL endpoint phải không có outbound HL API calls | BR-EXBOT-003; UC §5 |
| Audit / Logging | `queue_idempotency.state` transitions: `started` → `succeeded` | Test: verify state update sau khi processing hoàn tất | UC §3 step 5, 13 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Issue Register

| Issue ID | Type | Severity | Affected area | Source trace | Finding | Impact on tester understanding | Suggested fix | Status |
|---|---|---|---|---|---|---|---|---|
| v4-N-01 | `MISSING_INFO` | Minor | Area 1, Area 5 | UC step 9 vs SRS FR-EXBOT-023 | UC step 9 liệt kê 7 giá trị `RebalanceReason` nhưng FR-EXBOT-023 định nghĩa 9 giá trị canonical: `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile`. Hai giá trị **`manual_admin`** và **`recovery_reconcile`** hoàn toàn vắng mặt trong mô tả UC step 9. | Tester không biết light-check có thể fire `manual_admin` hoặc `recovery_reconcile` không — thiếu điều kiện trigger và expected behavior cho 2 reason này. | BA bổ sung điều kiện trigger và behavior cho `manual_admin` và `recovery_reconcile` vào UC step 9, hoặc xác nhận rõ 2 reason này không được fire bởi light-check. | Open |
| v4-N-02 | `CROSS_SOURCE_CONFLICT` | Minor | Area 1, Area 3 | UC step 6 vs SRS erd.md | UC step 6 ghi Light-Check Worker reads `hedge_legs (stop_price, margin_status, **circuit_state**)`. SRS erd.md cho thấy circuit state được lưu trong bảng riêng **`circuit_breakers.state`**, không phải field `circuit_state` trong `hedge_legs`. | Tester có thể query sai bảng khi kiểm tra circuit state; test case verify "circuit open suppresses hedge-sync" cần đọc đúng bảng. | BA/Dev xác nhận bảng nguồn đọc circuit state: `circuit_breakers.state` hay `hedge_legs.circuit_state`? Cập nhật UC step 6 cho nhất quán với ERD. | Open |
| v4-N-03 | `UNCLEAR_INFO` | Minor | Area 3 | UC step 9 funding fallback; BR-EXBOT-003 | UC step 9 mô tả fallback `fundingRate × 8760` khi `funding_rolling_metrics` trống nhưng nguồn của `fundingRate` không được ghi rõ. Nếu cần gọi HL API để lấy `fundingRate`, điều đó vi phạm BR-EXBOT-003 (HL weight = 0). | Tester không biết fallback `fundingRate × 8760` có vi phạm BR-EXBOT-003 không — ảnh hưởng trực tiếp đến test case "zero HL API calls". | BA xác nhận: `fundingRate` trong fallback lấy từ `bot_runtime_state` (cached field) hay source khác? Nếu từ HL API → đây là BR-EXBOT-003 violation. | Open |
| v4-N-04 | `AMBIGUOUS_WORDING` | Minor | Area 5 | UC step 11 vs SRS flows.md F-01 | UC step 11 viết "freeze routine hedge-sync" khi HL Mark Price Cache stale nhưng không có qualifier "this tick only". SRS flows.md F-01 chỉ rõ đây là freeze trong phạm vi 1 tick hiện tại. Thiếu qualifier dẫn đến có thể hiểu sai là freeze được persist. | Tester có thể thiết kế test case sai: verify hedge-sync bị suppress vĩnh viễn thay vì chỉ trong 1 tick. | BA thêm qualifier "this tick only" vào UC step 11. | Open |
| v4-N-05 | `UNCLEAR_INFO` | Minor | Area 3 | UC step 9 drift_threshold; SRS erd.md `bot_runtime_state.lp_value_usd`; SRS OQ-EXBOT-11 | UC step 9 ghi công thức `lpValueUsd = max(0, lpEthAmount × currentPriceUsd)` — ngụ ý real-time calculation. SRS erd.md có field `bot_runtime_state.lp_value_usd`. OQ-EXBOT-11 vẫn Open. Chưa rõ light-check đọc stored value hay tự tính lại. | Nếu có sai lệch giữa stored value và real-time calculation, tester cần biết cái nào là source of truth để viết expected result đúng cho `drift_threshold`. | Khi BA/zen close OQ-EXBOT-11: xác nhận stored vs real-time. | Open — Pending OQ-EXBOT-11 |

**Issues resolved (from v1–v3 audits):**

| Issue ID | Resolution | Date |
|---|---|---|
| I-01 | ✅ Resolved — hlMarkPrice source: HL Mark Price Cache; fallback: `bot_runtime_state.eth_price_usd`; stale 120s | 2026-07-03 |
| I-02 | ✅ Resolved — `range_boundary_near` formula confirmed | 2026-07-02 |
| I-03 | ✅ Resolved — `lpValueUsd` formula confirmed | 2026-07-03 |
| I-04 | ✅ Resolved — `funding_alert` 7d APR < -15% confirmed | 2026-07-03 |
| I-05 | ✅ Resolved — `range_out` routes to hedge-sync; no phantom lp_rebalancing queue | 2026-07-03 |
| I-07 | ✅ Resolved — step 12 overrun: both status+lifecycle_state set atomically | 2026-07-03 |
| I-08 | ✅ Resolved — `next_light_check_at` updated for all eligible bots | 2026-07-03 |
| I-09 | ✅ Resolved — LIMIT 500 overflow by design | 2026-07-03 |
| I-10 | ✅ Resolved — `expires_at` TTL=1min always set; hourly EventBridge cron cleanup | 2026-07-14 |
| I-11 | ✅ Resolved — diagram → F-01 reference | 2026-07-03 |
| I-12 | ✅ Resolved — Pool Slot0 Cache stale: fail-fast, skip tick | 2026-07-03 |
| I-13 | ✅ Resolved — BR-EXBOT-004 and BR-EXBOT-007 confirmed in scope | 2026-06-30 |
| v3-I-01 | ✅ Resolved — FR-EXBOT-012 and FR-EXBOT-040 added to UC §7 FR Trace | 2026-07-14 |
| v3-I-02 | ✅ Resolved — US-007 AC-007-1 corrected; `lp_rebalancing` set by hedge-sync not light-check | 2026-07-14 |
| v3-I-03 | ⚠️ Partially Resolved — ERD has `funding_rolling_metrics` schema; `bnza-market-cron` not in v1; AC-LC-09 primary blocked | 2026-07-14 |
| v3-I-07 | ✅ Resolved — F-01 updated with stop monitoring sub-flow and overrun check | 2026-07-14 |
| v3-I-08 | ✅ Resolved — US-008 confirmed platform-agnostic | 2026-07-14 |

---

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| `bnza-market-cron` worker (v1 not deployed) | Integration | AC-LC-09 (`funding_alert` primary path) không test được ở v1; fallback path vẫn test được | Dev/PM | Open — v2 scope |
| OQ-EXBOT-09: Pool Slot0 Cache refresh interval | UC / SRS | UC step 7 "5 min" vs FR-EXBOT-093 "2× refresh interval"; cần verify sau khi closed | BA / zen | Open |
| OQ-EXBOT-11: `lpValueUsd` stored vs real-time | SRS | Ảnh hưởng `drift_threshold` test case expected result | BA / zen | Open |
| OQ-EXBOT-12: 7d APR aggregation formula | SRS | `funding_alert` threshold confirmation | BA / zen | Open |

---

### 10.3 Audit Summary

#### Scoring

| # | Scoring Area | Max | Score | Status | Notes |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 18 | ✅ Clear | v4-N-01: 2 RebalanceReason values missing from UC step 9 (-2) |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 23 | ✅ Clear | v4-N-02: circuit_state source ambiguity (-2) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 22 | ✅ Clear | v4-N-03 (-1): funding fallback source; v4-N-04 (-1): freeze scope; v4-N-05 (-1): lpValueUsd read vs compute |
| 4 | Functional Integration & Data Consistency | 15 | 14 | ✅ Clear | v4-N-02 cross-ref: circuit_breakers table vs hedge_legs (-1) |
| 5 | UC / Spec Documentation Quality Issues | 15 | 13 | ✅ Clear | 5 minor issues; no blocker, no major conflict |
| **Total** | | **100** | **90** | ✅ | |

#### Verdict: **READY** (Score: 90/100)

Tất cả blocker và major issue từ v3 đã được giải quyết tính đến 2026-07-14. 5 issue mới phát sinh trong v4 đều là Minor — không có issue nào ngăn tester hiểu hành vi chính của UC.

**Blocker còn lại (v1 scope):** AC-LC-09 (`funding_alert` primary path) blocked vì `bnza-market-cron` chưa deploy ở v1 — fallback path vẫn test được.

**Open questions cần theo dõi trước khi finalize test cases:** v4-N-01 (manual_admin/recovery_reconcile triggers), v4-N-02 (circuit_breakers schema), v4-N-03 (fundingRate fallback source, BR-EXBOT-003 risk), v4-N-04 (freeze scope qualifier), v4-N-05 (lpValueUsd stored vs real-time).

**Khuyến nghị:** Tiến hành thiết kế test case cho AC-LC-01 → AC-LC-14 ngay (trừ AC-LC-09 primary path). Xử lý 5 open questions song song, ưu tiên v4-N-02 và v4-N-03 vì ảnh hưởng đến tính đúng đắn của test case.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Agent | Tạo báo cáo audited lần đầu |
| v2 | 2026-07-03 | QC UC Read Agent | Re-audit sau khi BA/Tech Lead trả lời I-01 → I-13; score 72 → 77 |
| v3 | 2026-07-06 | QC UC Read Agent | Re-audit sau arc-migration (Cloudflare → AWS); issue v3-I-01 → v3-I-08 |
| v4 | 2026-07-14 | QC UC Read Agent | Re-audit với tài liệu 2026-07-14; resolve v3-I-01, v3-I-02, v3-I-03 (partial), v3-I-07, v3-I-08; phát hiện 5 issue mới v4-N-01 → v4-N-05; score 77 → 90; verdict CONDITIONALLY READY → READY |

---

*Audited UC readiness report — UC-EXBOT-light-check v4 — 2026-07-14*
