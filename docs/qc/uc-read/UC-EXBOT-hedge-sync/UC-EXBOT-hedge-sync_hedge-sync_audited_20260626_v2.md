# Báo cáo Rà soát Mức độ Sẵn sàng của Use Case

**Tên tài liệu:** UC Readiness Review — UC-EXBOT-hedge-sync  
**Ngày tạo:** 2026-06-26  
**Người thực hiện:** qc-uc-read-exbot agent (Trinh.Bui)  
**Phiên bản:** v2

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-hedge-sync mô tả luồng mà Hedge-Sync Worker thực hiện điều chỉnh vị thế bán khống (short) trên Hyperliquid (HL) theo phương thức **delta-only** — tức là chỉ gửi lệnh điều chỉnh đúng phần chênh lệch giữa kích thước short thực tế và kích thước mục tiêu, không bao giờ đóng toàn bộ rồi mở lại. Đây là hành vi bắt buộc nhằm tối thiểu hóa chi phí giao dịch và tiêu thụ hạn mức API của HL.

Worker nhận message từ hàng đợi `hedge-sync` (được `light-check` enqueue khi phát hiện cần rebalance). Trước khi thực hiện bất kỳ lệnh nào trên HL, worker phải: (1) kiểm tra idempotency qua bảng `queue_idempotency`, (2) đối chiếu `stateVersion` trong message với D1 để loại bỏ message cũ, (3) giành khóa độc quyền qua `UserLockDO` (TTL 90s) để ngăn xung đột song song. Sau khi gửi lệnh delta, worker thực hiện đặt/thay thế lệnh stop bảo vệ qua giao thức INV-STOP (§19.5 SPEC v5.2.6), rồi enqueue reconcile để xác minh kích thước thực tế trên HL trước khi ghi nhận thành công.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-hedge-sync | Execute Delta-Only Hedge Adjustment | draft (updated 2026-06-20) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-20 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-hedge-sync.md` | draft 2026-06-20 | UC — tài liệu chính được review | Updated: A5 fixed, A6 added, BR consecutive clarified, trigger fixed |
| `userstories/us-006.md` | draft 2026-06-12 | US — delta-only hedge-sync | Linked story |
| `userstories/us-008.md` | draft 2026-06-12 | US — circuit breaker open/close | Linked story |
| `srs/spec.md` | draft 2026-06-20 (v5.2.6) | SRS — source of truth toàn bộ ExBot behavior | OQ-EXBOT-013/014/015 added |
| `srs/states.md` | draft 2026-06-18 | State diagram — lifecycle states + circuit breaker | — |
| `srs/flows.md` | draft 2026-06-20 | Flow diagram — F-02 Hedge-Sync Execution | F-05 rewritten |
| `srs/erd.md` | draft 2026-06-12 | ERD — data objects, fields, types | — |
| `frd.md` | draft 2026-06-24 | FRD — FR-EXBOT-020 đến FR-EXBOT-040 | §7 OQs migrated to SRS §9 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này tồn tại để đảm bảo vị thế short trên HL luôn phản ánh đúng lượng ETH thực tế trong vị thế LP của bot (tính theo công thức Uniswap V3 AMM), bằng cách điều chỉnh delta tối thiểu sau mỗi lần light-check phát hiện drift. Mục tiêu là duy trì trạng thái delta-hedged liên tục, bảo vệ nhà đầu tư khỏi rủi ro biến động giá ETH, đồng thời tối thiểu hóa chi phí giao dịch và tiêu thụ HL API weight.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Kiểm tra idempotency | Insert `message_id` vào `queue_idempotency` với `state='started'`; xung đột UNIQUE → bỏ qua | FR-EXBOT-011 |
| Kiểm tra stateVersion | Đọc `bot_runtime_state.state_version` từ D1; mismatch → discard, `status='skipped'` | FR-EXBOT-027 |
| Giành khóa UserLockDO | `acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})` | FR-EXBOT-026 |
| Fetch vị thế HL thực tế | Gọi `clearinghouseState` (weight=2) để lấy kích thước short hiện tại | FR-EXBOT-025 |
| Tính toán delta | `delta = BigDecimal(targetShortEth).sub(actualShortEth)`; BigDecimal only | FR-EXBOT-021, FR-EXBOT-022 |
| Gửi lệnh delta-only | `adjustShortDelta(delta, cloid)` — chỉ gửi phần chênh lệch | FR-EXBOT-022, BR-EXBOT-004 |
| Xử lý delta=0 | Skip HL order; tiếp tục stop replacement; ghi lý do trong `rebalance_attempts` | UC §4 A6; OQ-EXBOT-013 |
| INV-STOP protocol | Set `stop_replacing_started_at`, cancel-then-place bảo vệ, clear trong `finally` | FR-EXBOT-035 |
| Enqueue reconcile | Enqueue `{botId, attemptId, expectedAbsSize, hedgeLegId}` | FR-EXBOT-025 |
| Release UserLockDO | `release(holderToken, idempotencyKey, result)` trong `finally` | FR-EXBOT-026 |
| Post-order reconcile | Reconcile Worker fetch vị thế HL, xác minh kích thước, extract metrics | FR-EXBOT-025 |
| Recompute stop_trigger_px | `entry_price × (1 + liq_distance_pct × stopSafetyFactor=0.70)` (BigDecimal) | FR-EXBOT-030 |
| Cập nhật hedge_legs | `stop_price`, `entry_price`, `effective_leverage`, xóa `stop_replacing_started_at` | FR-EXBOT-025, FR-EXBOT-035 |
| Ghi rebalance_attempts | Insert row với status sau reconcile | FR-EXBOT-025 |
| Xử lý HL order rejection | `status='failed'`, `incrementCircuitBreaker`, enqueue notification | FR-EXBOT-040 |
| Xử lý partial fill | Reconcile phát hiện mismatch → enqueue `partial_repair` | FR-EXBOT-036 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| LP range rebalance (`lp_rebalancing`) | Xử lý trong `partial_repair` queue / UC riêng | Không ảnh hưởng |
| Stop trigger detection (`markPrice >= stop_price`) | Thuộc UC-EXBOT-light-check | Không ảnh hưởng |
| SAFE_MODE entry do `stop_replacing_started_at` stuck | UC hedge-sync chỉ set/clear trường này; detection thuộc light-check (primary) và deep-audit (secondary) | Test SAFE_MODE ở UC-EXBOT-light-check / deep-audit |
| bot_safe_close execution | Trigger khi circuit breaker kiệt sức; execution nằm ở UC-EXBOT-bot-safe-close | Không ảnh hưởng |
| marginSummary preflight | SRS FR-EXBOT-060 định nghĩa update "just before hedge-sync" nhưng UC không mô tả; BA xác nhận là implementation detail (OQ-EXBOT-014) | Xem Issue I-04 |
| HLRateLimitDO interaction | SRS FR-EXBOT-091 quy định nhưng UC không mô tả; BA xác nhận là implementation detail (OQ-EXBOT-015) | Xem Issue I-05 |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Hedge-Sync Worker) | Primary / System | Thực thi toàn bộ luồng hedge-sync từ khi nhận message đến khi ghi kết quả | Hoạt động hoàn toàn tự động qua queue | UC §1, US-006 |
| UserLockDO | Secondary / System (Durable Object) | Cung cấp mutex theo user | TTL=90s; heartbeat khi work > 30s | FR-EXBOT-026, FR-EXBOT-092 |
| Hyperliquid API | External | Nhận lệnh `adjustShortDelta`, trả fill confirmation; cung cấp `clearinghouseState` | Rate limit budget 800 weight/min; weight=2 per call | FR-EXBOT-091 |
| D1 (state_db_shard) | Secondary / System | Lưu trữ `bot_runtime_state`, `hedge_legs`, `rebalance_attempts`, `queue_idempotency` | Ghi atomically | FR-EXBOT-025 |
| Reconcile Worker | Secondary / System | Xác minh kích thước HL sau lệnh delta; cập nhật D1 | Chạy qua `reconcile` queue | FR-EXBOT-025 |

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Message `hedge-sync` nhận được với payload `{botId, reasons: RebalanceReason[], stateVersion}` | Yes | UC §2 |
| 2 | `bots.status='active'`, `bots.lifecycle_state='active'` | Yes | UC §2 |
| 3 | `circuit_breakers.state IN ('closed', 'half_open')` | Yes | UC §2 |
| 4 | HL agent key `approval_status='approved'` và chưa hết hạn (implicit — cần để decrypt khi gọi HL) | Yes (implicit) | FR-EXBOT-080, FR-EXBOT-082 |
| 5 | `bot_runtime_state.state_version` tồn tại trong D1 | Yes | FR-EXBOT-027 |
| 6 | `hedge_legs` row tồn tại với `stop_price`, `entry_price` đã được populate | Yes | FR-EXBOT-031 |

### 3.2 Kết quả sau khi hoàn tất (happy path)

| Thao tác | Trạng thái hệ thống / dữ liệu sau | Nguồn |
|---|---|---|
| Delta adjustment thành công + reconcile xác nhận | `hedge_legs.stop_price`, `entry_price`, `effective_leverage` cập nhật; `stop_replacing_started_at=NULL`; `bot_runtime_state.last_known_hl_short_size` = reconciled size | UC §5, FR-EXBOT-025 |
| Ghi nhận attempt | `rebalance_attempts` row với `status='success'` insert sau reconcile | FR-EXBOT-025 |
| Queue idempotency | `queue_idempotency.state='succeeded'` | FR-EXBOT-011 |
| Circuit breaker (probe half_open thành công) | `circuit_breakers.state='closed'`, `failure_count=0` | FR-EXBOT-040, US-008 AC-3 |
| stateVersion mismatch | `rebalance_attempts.status='skipped'`; không có lệnh HL | FR-EXBOT-027 |
| Lock không giành được | Message re-enqueue với delay; không có lệnh HL | FR-EXBOT-026 |
| HL order rejected | `rebalance_attempts.status='failed'`; `failure_count++`; notification enqueued | FR-EXBOT-040 |
| Partial fill | `partial_repair` message enqueued; `rebalance_attempts.status='partial'` | FR-EXBOT-036 |
| delta=0 | Skip HL order; tiếp tục stop replacement; ghi lý do trong `rebalance_attempts` (status TBD — OQ-EXBOT-013) | UC §4 A6 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### §F.1 — Inventory (function / operation / data object)

| # | Loại | Tên / Operation | Trigger | Input | Output | Data Object / Field | Nguồn |
|---|---|---|---|---|---|---|---|
| F1-01 | Operation | Insert idempotency check | Message deliver | `message_id` | UNIQUE conflict → skip; else continue | `queue_idempotency.message_id`, `state` | FR-EXBOT-011 |
| F1-02 | Operation | stateVersion check | Post-idempotency | `bot_runtime_state.state_version`, message `stateVersion` | Match → continue; mismatch → discard | `rebalance_attempts.status='skipped'` | FR-EXBOT-027 |
| F1-03 | Operation | UserLockDO.acquire | Post-stateVersion | `holderToken`, `ttl=90s`, `idempotencyKey=hedge-sync:{botId}:{stateVersion}` | `{acquired, leaseId?}` | `UserLockDO` internal | FR-EXBOT-026, FR-EXBOT-092 |
| F1-04 | Operation | Fetch actual HL position | Post-lock | `botId`, `hl_account_address` | `actualShortEth` from `clearinghouseState` | `hedge_legs.last_known_hl_short_size` (stale pre-sync) | FR-EXBOT-025 |
| F1-05 | Operation | Compute delta | Post-fetch | `targetShortEth`, `actualShortEth` (BigDecimal) | `delta` (BigDecimal, positive/negative/zero) | `bot_runtime_state.target_short_size` | FR-EXBOT-021, FR-EXBOT-022 |
| F1-06 | Operation | adjustShortDelta | Post-compute, delta≠0 | `delta`, `cloid` (deterministic keccak256) | Fill confirmation from HL | `rebalance_attempts.adjust_cloid` | FR-EXBOT-022, BR-EXBOT-004 |
| F1-07 | Operation | INV-STOP — stop replacement | Post-delta (or post-compute if delta=0) | `stop_replacing_started_at` set, cancel current stop → place new stop | `stop_cloid` mới, stop confirmed | `hedge_legs.stop_replacing_started_at`, `stop_cloid`, `stop_price`, `stop_size` | FR-EXBOT-035 |
| F1-08 | Operation | Enqueue reconcile | Post-INV-STOP | `{botId, attemptId, expectedAbsSize, hedgeLegId}` | Message in `reconcile` queue | `queue_idempotency` | FR-EXBOT-025 |
| F1-09 | Operation | UserLockDO.release | Post-enqueue (finally) | `holderToken`, `idempotencyKey`, `result` | Lease released | `UserLockDO` | FR-EXBOT-026 |
| F1-10 | Operation | Post-order reconcile | `reconcile` queue message | `botId`, `attemptId`, `expectedAbsSize`, `hedgeLegId` | `reconciled_size`, `entry_price`, `liq_price`, `effective_leverage` | `hedge_legs`, `bot_runtime_state.last_known_hl_short_size` | FR-EXBOT-025 |
| F1-11 | Operation | Recompute stop_trigger_px | Post-reconcile | `entry_price`, `liquidation_price` (or `effective_leverage`), `stopSafetyFactor=0.70` | `stop_trigger_px` (BigDecimal) | `hedge_legs.stop_price` | FR-EXBOT-030 |
| F1-12 | Operation | Insert rebalance_attempts | Post-reconcile | `botId`, `status`, `reason`, `adjust_cloid`, `reconciled_short_size` | Row inserted | `rebalance_attempts` | FR-EXBOT-025 |
| F1-13 | Operation | Update queue_idempotency | Post-success | `message_id`, `state='succeeded'` | Row updated | `queue_idempotency.state` | FR-EXBOT-011 |
| F1-14 | Operation | incrementCircuitBreaker | On HL order failure | `hedge_leg_id` | `failure_count++`; ≥3 in 24h → `state='open'` | `circuit_breakers.failure_count`, `state`, `reset_at` | FR-EXBOT-040 |
| F1-15 | Operation | Enqueue partial_repair | On partial fill | `{botId, reason='partial_fill', attemptId}` | Message in `partial_repair` queue | `rebalance_attempts.status='partial'` | FR-EXBOT-036 |
| F1-16 | Event | Circuit breaker `closed→open` | 3 consecutive failures in 24h | — | `state='open'`, `reset_at=now+1h` | `circuit_breakers` | FR-EXBOT-040 |
| F1-17 | Event | Circuit breaker `half_open→closed` | Probe hedge-sync success | — | `state='closed'`, `failure_count=0` | `circuit_breakers` | FR-EXBOT-040, US-008 AC-3 |
| F1-18 | Event | Circuit breaker `half_open→open` | Probe fails | — | `state='open'`, `reset_at=now+1h` | `circuit_breakers` | FR-EXBOT-040, US-008 AC-4 |
| F1-19 | State (lifecycle) | `active` | Normal bot state | — | hedge-sync allowed | `bots.lifecycle_state`, `bots.status='active'` | SRS states.md |
| F1-20 | State (circuit) | `closed` / `half_open` / `open` | Circuit state machine | — | `closed`: allowed; `half_open`: 1 probe; `open`: suppressed | `circuit_breakers.state` | FR-EXBOT-040 |
| F1-21 | Data Object | `queue_idempotency` | Per message | `message_id`, `kind`, `state`, `bot_id` | UNIQUE on `message_id` | `queue_idempotency.key` PK | ERD |
| F1-22 | Data Object | `bot_runtime_state` | Per bot | `state_version`, `lp_eth_amount`, `target_short_size`, `last_known_hl_short_size` | Updated after reconcile | `bot_id` PK | ERD |
| F1-23 | Data Object | `hedge_legs` | Per bot | `stop_price`, `stop_cloid`, `entry_price`, `liq_price`, `effective_leverage`, `stop_replacing_started_at`, `margin_status` | Updated after reconcile | `hedge_legs.id` PK | ERD |
| F1-24 | Data Object | `rebalance_attempts` | Per attempt | `status` enum: `success`/`failed`/`skipped`/`partial`; `reason` (canonical `RebalanceReason[]`) | Row per attempt | `rebalance_attempts.id` PK | ERD, FR-EXBOT-023 |
| F1-25 | Enum | `RebalanceReason[]` | In queue message | `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile` | Used as `rebalance_attempts.reason` | `rebalance_attempts.reason` TEXT | FR-EXBOT-023 |
| F1-26 | Message (error) | `E-EXBOT-007` | HL order rejected — margin insufficient | — | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." (HTTP 502) | `rebalance_attempts.error_code` | SRS §5 |
| F1-27 | Message (error) | `E-EXBOT-008` | HL API unreachable | — | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." (HTTP 503) | — | SRS §5 |
| F1-28 | Message (error) | `E-EXBOT-011` | Reconcile mismatch | — | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." (internal) | — | SRS §5 |

---

### §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Item | States / Điều kiện | Precondition | Validation / Business Rule | Dependency | Resolved Message | Nguồn |
|---|---|---|---|---|---|---|
| `queue_idempotency.message_id` | `started` → `succeeded`/`failed`/`retryable` | Message delivered | UNIQUE: conflict → exit immediately | `queue_idempotency` table | — | FR-EXBOT-011 |
| `bot_runtime_state.state_version` | INTEGER, tăng dần | D1 accessible | message `stateVersion` ≠ D1 → discard (`status='skipped'`) | `bot_runtime_state` row | — | FR-EXBOT-027 |
| `UserLockDO` lease | `acquired=true` / `acquired=false` | Bot user_id identified | TTL=90s; work >30s → heartbeat; release in `finally` | `UserLockDO` Durable Object | — | FR-EXBOT-026, FR-EXBOT-092 |
| `delta` (BigDecimal) | positive/negative/zero | `targetShortEth`, `actualShortEth` present | BigDecimal only — `Number()` arithmetic is a violation. `target_ratio_bps` via `normalizeTargetRatioBps()` | `bot_runtime_state.target_short_size`, `lp_eth_amount`, `hedge_ratio` | — | FR-EXBOT-021, NFR-EXBOT-008 |
| `cloid` (deterministic) | Fixed for same `botId+attemptId+stage+version` | — | `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Retry same payload → same cloid. Changed payload → increment `version`. Duplicate cloid → reconcile first, never blind resubmit | — | — | FR-EXBOT-024 |
| `adjustShortDelta` | Delta-only (increase or reduce-only) | Lock acquired, delta≠0 | Full close→open forbidden in normal hedge-sync. Allowed ONLY: target=0, emergency reset, manual reset (Phase B+) | HL API available | `E-EXBOT-007` margin insufficient | BR-EXBOT-004, FR-EXBOT-022 |
| `stop_replacing_started_at` | Non-NULL during replacement; NULL otherwise | After delta order confirmed (or skipped when delta=0) | Set before INV-STOP critical section; clear in `finally`. Stuck >60s → light-check primary detection (≤5 min) → SAFE_MODE | `hedge_legs` row | — | FR-EXBOT-035, FR-EXBOT-033 |
| `stop_trigger_px` | BigDecimal, > `entry_price` | `entry_price`, `liquidation_price` or `effective_leverage` present | Formula: `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`. `liq_distance_pct = (liq_price − entry_price) / entry_price` (HL value priority; fallback `1/effective_leverage`). Phase A `stopSafetyFactor=0.70`. BigDecimal required | `hedge_legs.entry_price` | `E-EXBOT-009` stop placement fail | FR-EXBOT-030 |
| `rebalance_attempts.status` | `success`/`failed`/`skipped`/`partial` | — | `status='success'` only after reconcile confirmed. Must not write before reconcile | `rebalance_attempts` table | — | FR-EXBOT-025 |
| `circuit_breakers.state` | `closed`/`open`/`half_open` | — | Source of truth = column; NOT dynamic compute from history. Reset to `closed` ONLY on probe success | `circuit_breakers` table | Notification on `open` | FR-EXBOT-040, US-008 Notes |
| `circuit_breakers.failure_count` | INTEGER 0…N | — | 3 consecutive failures in rolling 24h window (no intervening success) → `state='open'`. Reset=0 when `closed` | `circuit_breakers` table | — | FR-EXBOT-040, UC §6 BR |
| `half_open_probe_used` | 0 (available) / 1 (used) | `state='half_open'` | Atomic claim 0→1; only 1 probe permitted | `circuit_breakers` table | — | FR-EXBOT-040 |

**Business Rule BR-EXBOT-004 (resolved):**
Điều chỉnh hedge delta-only là bất biến mặc định. Full close→open trong normal hedge-sync là lỗi. (Nguồn: `srs/spec.md` §4 BR-EXBOT-004)

---

### §F.3 — Functional Logic & Workflow Decomposition

#### 6.1 Luồng chính — Delta-only hedge adjustment thành công

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Hedge-Sync Worker | Nhận `hedge-sync` message | Insert `queue_idempotency` `state='started'` | — | UNIQUE conflict → exit, duplicate delivery | FR-EXBOT-011 |
| 2 | Worker | Đọc `bot_runtime_state.state_version` | Match | — | stateVersion mismatch → `status='skipped'`, exit | FR-EXBOT-027 |
| 3 | Worker | `UserLockDO.acquire(holderToken, 90s, idempotencyKey)` | `{acquired: true}` | `acquired=false` → re-queue with delay | — | FR-EXBOT-026 |
| 4 | Worker | Fetch HL position: `clearinghouseState` (weight=2) | `actualShortEth` | — | HL unreachable >5 min → SAFE_MODE (E-EXBOT-008) | FR-EXBOT-025, FR-EXBOT-091 |
| 5 | Worker | `delta = BigDecimal(targetShortEth).sub(actualShortEth)` | Delta computed | delta=0 → A6: skip HL order, proceed to step 8 | — | FR-EXBOT-021; UC §4 A6 |
| 6 | Worker | `adjustShortDelta(delta, cloid)` | Fill confirmation from HL | — | HL rejected → `status='failed'`, `incrementCircuitBreaker`, notification | FR-EXBOT-022 |
| 7 | Worker | (Implicit) Recompute `stop_trigger_px` (BigDecimal) before stop replacement | `stop_trigger_px` computed | — | — | FR-EXBOT-030 (see Issue I-02) |
| 8 | Worker | INV-STOP: set `stop_replacing_started_at`, cancel stop → place new stop | Stop replaced; `stop_replacing_started_at` cleared in `finally` | — | Stop fail → `E-EXBOT-009`; stuck >60s → light-check SAFE_MODE | FR-EXBOT-035, FR-EXBOT-033 |
| 9 | Worker | Enqueue `{botId, attemptId, expectedAbsSize, hedgeLegId}` → `reconcile` queue | Message enqueued | — | — | FR-EXBOT-025 |
| 10 | Worker | `UserLockDO.release(holderToken, idempotencyKey, result)` | Lease released | — | TTL 90s auto-release if missed | FR-EXBOT-026 |
| 11 | Reconcile Worker | Fetch actual HL position; verify `size == expectedAbsSize` | Match → continue | — | Mismatch → E-EXBOT-011, enqueue `partial_repair`, SAFE_MODE | FR-EXBOT-025 |
| 12 | Reconcile Worker | Extract `entry_price`, `liq_price`, `effective_leverage`; recompute `stop_trigger_px` | `hedge_legs` updated; `bot_runtime_state.last_known_hl_short_size` updated | — | — | FR-EXBOT-025, FR-EXBOT-030 |
| 13 | Reconcile Worker | Insert `rebalance_attempts` `status='success'`; update `queue_idempotency.state='succeeded'` | Done | — | — | FR-EXBOT-025, FR-EXBOT-011 |

#### 6.2 Luồng A1 — Lock không giành được

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 3 | Worker | `UserLockDO.acquire` → `acquired=false` | Re-queue với delay | FR-EXBOT-026, US-006 AC-3 |

#### 6.3 Luồng A2 — stateVersion mismatch

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 2 | Worker | stateVersion message < D1 | Discard; `rebalance_attempts.status='skipped'`; không gửi lệnh HL | FR-EXBOT-027, US-006 AC-2 |

#### 6.4 Luồng A3 — HL order rejected

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 6 | Worker | HL rejection (insufficient margin) | `rebalance_attempts.status='failed'`; `incrementCircuitBreaker`; notification enqueued | FR-EXBOT-040, US-006 AC-4 |
| — | Worker | 3 consecutive failures trong rolling 24h window | `circuit_breakers.state='open'`, `reset_at=now+1h` | FR-EXBOT-040, UC §6 BR |

#### 6.5 Luồng A4 — Partial fill

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 11 | Reconcile Worker | `|actual − expected| > tolerance` | Enqueue `partial_repair(reason='partial_fill')` | FR-EXBOT-036 |
| — | Partial Repair Worker | Fetch actual, compute remaining delta, resubmit với new cloid | Tối đa 3 lần; sau 3 thất bại → `bot_safe_close` | FR-EXBOT-036 |

#### 6.6 Luồng A5 — stop_replacing_started_at stuck

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| — | Light-Check Worker (primary) | Detect `stop_replacing_started_at IS NOT NULL AND age > 60s` (≤5 min cadence) | Enqueue `partial_repair(reason='stop_replacing_overrun')`; SAFE_MODE | FR-EXBOT-033 primary |
| — | Deep-Audit Worker (secondary) | Cùng điều kiện nếu light-check miss | SAFE_MODE (backstop) | FR-EXBOT-033 secondary |

#### 6.7 Luồng A6 — delta=0 (newly documented in UC §4)

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 5 | Worker | `delta = 0` computed | Skip HL order entirely | UC §4 A6 |
| 8 | Worker | Proceed directly to stop replacement (INV-STOP) | Stop replaced normally | UC §4 A6 |
| — | Worker | Log in `rebalance_attempts` | Status value TBD — pending OQ-EXBOT-013 | UC §4 A6, OQ-EXBOT-013 |

---

### §F.4 — Functional Integration & Data Consistency

| Hành động | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| `adjustShortDelta` thành công | `reconcile` queue → Reconcile Worker | Reconcile phải xác nhận trước khi ghi `status='success'` | `rebalance_attempts.status` không ghi trước reconcile confirm; `last_known_hl_short_size` = reconciled value | FR-EXBOT-025 |
| `stop_replacing_started_at` set | Light-Check Worker (≤5 min sau) | Stuck >60s: light-check enqueue `partial_repair` + SAFE_MODE | `stop_replacing_started_at` phải NULL sau INV-STOP hoàn tất (`finally`) | FR-EXBOT-033, FR-EXBOT-035 |
| Circuit breaker `state='open'` | `UC-EXBOT-light-check` | Suppress `hedge-sync` enqueue; stop monitoring tiếp tục | `circuit_breakers.state` là canonical source | FR-EXBOT-040, FR-EXBOT-014 |
| Circuit breaker `state='half_open'` probe thành công | Light-Check tiếp theo resume | `failure_count=0`; resume enqueue hedge-sync | `circuit_breakers.state='closed'` atomic sau probe success | FR-EXBOT-040 |
| 3 consecutive failures → `circuit_breakers` extend 3+ lần | `UC-EXBOT-bot-safe-close` | `bot_safe_close` triggered | `close_operations` row với `trigger_reason='circuit_breaker_exhausted'` | FR-EXBOT-072 |
| Partial repair fail 3 lần | `UC-EXBOT-bot-safe-close` | `bot_safe_close` triggered | `close_operations` row | FR-EXBOT-036, FR-EXBOT-072 |
| `bot_runtime_state.last_known_hl_short_size` updated | `UC-EXBOT-light-check` (lần sau) | Light-check dùng giá trị này để compute `deltaErrorUsd` | Nếu không cập nhật, drift eval lần sau sẽ sai | FR-EXBOT-012 |
| HL agent key decrypt khi gọi HL | `hl_agent_keys` table | Key phải `approved` + unexpired; revoked mid-flight → SAFE_MODE | Plain key function-scope only; không log | FR-EXBOT-080, FR-EXBOT-082 |

---

### §F.5 — Acceptance Criteria Candidates

| AC # | Scenario | Given | When | Then | Nguồn |
|---|---|---|---|---|---|
| AC-01 | Happy path — delta-only thành công | `status='active'`, `lifecycle_state='active'`, `circuit='closed'`, stateVersion match | Acquire lock, fetch HL, compute delta (BigDecimal), `adjustShortDelta`, INV-STOP, enqueue reconcile | Reconcile xác nhận; `hedge_legs` updated; `rebalance_attempts.status='success'`; `queue_idempotency.state='succeeded'` | US-006 AC-1 |
| AC-02 | stateVersion mismatch | Message `stateVersion=5`; D1 `state_version=6` | Worker kiểm tra trước acquire | `status='skipped'`; không có lệnh HL | US-006 AC-2; FR-EXBOT-027 |
| AC-03 | Lock không giành được | Khác worker hold lease | Worker gọi `acquire` | `acquired=false`; re-queue; không có lệnh HL | US-006 AC-3; FR-EXBOT-026 |
| AC-04 | HL rejected — insufficient margin | Delta gửi đi; HL trả lỗi | HL rejection | `status='failed'`; `failure_count++`; notification enqueued | US-006 AC-4; E-EXBOT-007 |
| AC-05 | 3 consecutive failures → circuit open | 2 failure trước trong 24h | Failure thứ 3 | `circuit_breakers.state='open'`; `reset_at=now+1h`; stop monitoring tiếp tục | US-008 AC-1; FR-EXBOT-040 |
| AC-06 | Probe `half_open` thành công | `state='half_open'`; probe done | Reconcile success | `state='closed'`; `failure_count=0` | US-008 AC-3 |
| AC-07 | Probe `half_open` thất bại | `state='half_open'` | Probe fail | `state='open'`; `reset_at=now+1h`; admin notification | US-008 AC-4 |
| AC-08 | Partial fill → partial_repair | Reconcile `|actual − expected| > tolerance` | — | `partial_repair` enqueued; `status='partial'`; sau 3 fail repair → `bot_safe_close` | FR-EXBOT-036 |
| AC-09 | delta=0 → skip HL, stop replacement vẫn chạy | delta computed = 0 | — | Không gửi lệnh HL; INV-STOP protocol vẫn chạy; `rebalance_attempts` logged (status TBD) | UC §4 A6; OQ-EXBOT-013 |
| AC-10 | Duplicate message delivery | Cùng `message_id` deliver 2 lần | Lần 2 UNIQUE conflict | Worker exit immediately; không có lệnh HL lần 2 | FR-EXBOT-011 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

*(Xem §F.4 — Functional Integration & Data Consistency)*

---

## 8. Acceptance Criteria

*(Xem §F.5 — AC-01 đến AC-10)*

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Hedge-sync hoàn tất trong 30 giây (điều kiện bình thường) | Đo thời gian từ message nhận đến `status='success'` | NFR-EXBOT-002 |
| Rate Limit | HL weight ≤800/min; `clearinghouseState` weight=2; mọi call qua `HLRateLimitDO` | Khi `allowed=false`, worker không gửi lệnh | NFR-EXBOT-004, FR-EXBOT-091 |
| Precision | Mọi tính toán hedge, stop, margin dùng BigDecimal | Cloid, delta, `stop_trigger_px` dùng BigDecimal | NFR-EXBOT-008 |
| Security | Agent key AES-GCM; decrypt function-scope only; không log raw key | Log audit không có raw key | NFR-EXBOT-006, FR-EXBOT-080 |
| Idempotency | `queue_idempotency.message_id` UNIQUE; cloid deterministic | Deliver cùng message 2 lần → 1 lần thực thi | NFR-EXBOT-007 |
| Concurrency | Max 6 simultaneous outbound connections per CF Worker invocation | — | NFR-EXBOT-011 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional requirement — yêu cầu chức năng của module ExBot; canonical source cho implementation | `srs/spec.md` |
| BR-EXBOT-* | Business rule — quy tắc nghiệp vụ bất biến | `srs/spec.md §4`, cross-ref `common-rules.md` |
| E-EXBOT-* | Error code — API-layer error response của ExBot | `srs/spec.md §5` |
| INV-STOP | Invariant Stop — giao thức thay thế stop được bảo vệ (§19.5 SPEC v5.2.6): cancel → place với `stop_replacing_started_at` guard | SRS §FR-EXBOT-035 |
| UserLockDO | Durable Object cung cấp mutex dạng lease per user | FR-EXBOT-026, FR-EXBOT-092 |
| cloid | Client Order ID — định danh lệnh tất định (keccak256) | FR-EXBOT-024 |
| BigDecimal | Kiểu tính toán chính xác cho tài chính | NFR-EXBOT-008 |
| stateVersion | Số phiên bản trạng thái bot trong D1 — phát hiện message cũ | FR-EXBOT-027 |
| OQ-EXBOT-* | Open question — câu hỏi mở đang chờ chốt | `srs/spec.md §9` |

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 | Medium | MISSING_INFO | UC §3 step 5, UC §4 A6; OQ-EXBOT-013 | UC §4 A6 đã định nghĩa hành vi delta=0: skip HL order, tiếp tục stop replacement. Tuy nhiên `rebalance_attempts` status ghi gì khi delta=0 vẫn chưa được định nghĩa — A6 chỉ nói "Log reason in rebalance_attempts" mà không nêu status value. OQ-EXBOT-013 (owner: Tech Lead) đang chờ chốt. | Tester cần biết expected value của `rebalance_attempts.status` khi delta=0 để viết test assertion | Tech Lead | Deferred (OQ-EXBOT-013) |
| I-04 | Medium | MISSING_INFO | SRS FR-EXBOT-060; UC §3 Main Flow | SRS FR-EXBOT-060 định nghĩa margin status được update "during hedge-sync preflight (HL `marginSummary` fetch)". UC không mô tả bước này — không rõ: vị trí trong flow, hành vi khi `margin_status='warning'` (size-increase bị chặn), hành vi khi `margin_status='critical'` (×2 → SAFE_MODE). BA đã xác nhận đây là implementation ordering detail, không thuộc BA UC scope. OQ-EXBOT-014 đang chờ Tech Lead. | Tester không thể test margin_warning và margin_critical scenarios tại thời điểm hedge-sync mà không có flow rõ ràng | Tech Lead | Deferred (OQ-EXBOT-014) |
| I-05 | Medium | MISSING_INFO | SRS FR-EXBOT-091; UC §3 Main Flow | UC không đề cập interaction với `HLRateLimitDO` trước khi gọi HL. Theo FR-EXBOT-091, khi `allowed=false`, caller phải re-queue với delay và không gửi lệnh. Hành vi khi `allowed=false` trong khi đang hold `UserLockDO` lease (release lock trước re-queue?) hoàn toàn vắng mặt trong UC. BA đã xác nhận là implementation detail. OQ-EXBOT-015 đang chờ Tech Lead. | Thiếu test case rate limit behavior khi lock đang được held | Tech Lead | Deferred (OQ-EXBOT-015) |
| I-06 | Medium | MISSING_INFO | FR-EXBOT-080, FR-EXBOT-082; UC §3 Main Flow | UC §3 step 4 mô tả "Fetch actual HL position via `clearinghouseState`" nhưng không đề cập bước giải mã HL agent key (AES-GCM decrypt) trước khi ký lệnh HL. BA response (2026-06-20) xác nhận step 4 "already documents this" nhưng trong file UC updated 2026-06-20, step 4 chỉ ghi fetch clearinghouseState, không có decrypt step. Failure path khi key bị revoke mid-flight (FR-EXBOT-082: SAFE_MODE) và khi `expires_at` đã qua cũng không có trong UC flow. | Tester cần failure path của agent key decryption để thiết kế test case bảo mật và SAFE_MODE | BA | Open |
| I-09 | Low | MISSING_INFO | UC §7 FR Trace; SRS spec.md | UC §7 FR Trace liệt kê: `FR-EXBOT-022, 024, 025, 026, 027, 036` — bỏ sót `FR-EXBOT-021` (LP position amount calculation), `FR-EXBOT-023` (canonical RebalanceReason enum), `FR-EXBOT-030` (stop trigger price computation), `FR-EXBOT-035` (INV-STOP protocol), `FR-EXBOT-040` (circuit breaker). Tất cả đều được mô tả trong Main Flow của UC. | Trace không đầy đủ khó khăn khi trace test case về nguồn gốc rule | BA | Open |
| I-10 | Low | INTERNAL_INCONSISTENCY | UC §3 step 5 note; UC §4 A6 | UC §3 step 5 có note "behavior pending OQ-EXBOT-013" nhưng UC §4 A6 đã định nghĩa hành vi rõ ràng: "skip HL order entirely; proceed directly to stop replacement (step 8)". Hai phần trong cùng UC mâu thuẫn nhau: step 5 nói "pending" trong khi A6 đã có behavior. BA cần xóa note "pending OQ-EXBOT-013" ở step 5 hoặc giữ nhất quán với A6, và chốt `rebalance_attempts.status` để A6 hoàn chỉnh. | Gây nhầm lẫn khi đọc UC — tester không biết nên follow step 5 note hay A6 | BA | Open |
| I-11 | Low | UNCLEAR_INFO | UC §3 step 8; SRS FR-EXBOT-030, FR-EXBOT-035 | UC §3 step 8 mô tả "Execute stop replacement via INV-STOP protocol: protected cancel→place". Stop mới được đặt ở step 8, nhưng `stop_trigger_px` chỉ được recompute ở step 13 (sau reconcile, dùng `entry_price` mới). Điều này có nghĩa: (a) stop được đặt ở step 8 dùng giá nào — giá cũ từ `hedge_legs.stop_price` như placeholder, rồi replace lại sau reconcile? Hay (b) reconcile cung cấp `entry_price` rồi mới recompute, sau đó mới một lần thay stop? UC không làm rõ thứ tự này. | Tester không thể xác định expected `stop_price` value ở bước 8 vs bước 13 | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-013: delta=0 behavior — skip HL và proceed, hay abort sync? | UC behavior | Blocks `rebalance_attempts` status definition; A6 có behavior nhưng thiếu status value | Tech Lead | Open |
| OQ-EXBOT-014: `marginSummary` fetch ordering trong hedge-sync preflight | Implementation | Ordering affects lock TTL design; không có trong UC | Tech Lead | Open |
| OQ-EXBOT-015: HLRateLimitDO + UserLockDO interaction — rate-limit weight trước hay sau lock? | Implementation | Retry behavior khi rate-limit hit while lock held | Tech Lead | Open |
| OQ-EXBOT-02: NV-3 — HL có hỗ trợ place-before-cancel stop replacement không? | Integration | Quyết định INV-STOP protocol path (a) vs (b) | zen / SOTATEK | Open |
| OQ-EXBOT-04: NV-13 — HL ETH-USD perp minimum order size / dust handling | Integration | Xác định ngưỡng delta tối thiểu để gửi lệnh | zen / SOTATEK | Open |

---

## 10.3 Audit Summary

### Scoring

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 17 | ⚠️ Partial | 28 items atomically listed. A6 (delta=0) added, circuit breaker states, error messages đầy đủ. Trừ: agent key decrypt step không có trong §3 Main Flow (I-06); `stop_trigger_px` recompute timing mơ hồ (I-11). |
| 2 | Data Object / State Attributes, BR, Validations & Messages | 25 | 19 | ⚠️ Partial | BR consecutive định nghĩa rõ (rolling 24h, no intervening success). Main validations và messages resolved. Trừ: delta=0 `rebalance_attempts` status TBD (I-01 deferred); marginSummary missing (I-04 deferred); HLRateLimitDO missing (I-05 deferred). |
| 3 | Functional Logic & Workflow Decomposition | 25 | 22 | ⚠️ Partial | A5 (primary/secondary detection) đã FIXED. A6 (delta=0) added. 7 alternate flows rõ ràng. Trừ: timing stop_trigger_px recompute vs INV-STOP step 8 không rõ (I-11 minor). |
| 4 | Functional Integration & Data Consistency | 15 | 13 | ⚠️ Partial | Integration với light-check, deep-audit, partial_repair, bot_safe_close, UserLockDO documented. Agent key decrypt mid-flow referenced. Trừ: failure path khi key revoked mid-flight không có trong UC flow (I-06). |
| 5 | UC / Spec Documentation Quality Issues | 15 | 10 | ⚠️ Partial | Trigger fixed, duplicate Postconditions fixed, A5 fixed. Còn: FR Trace §7 thiếu 5 FRs (I-09); Mermaid placeholder vẫn có; INTERNAL_INCONSISTENCY step 5 note vs A6 (I-10); UNCLEAR_INFO stop price timing (I-11). |
| **Total** | | **100** | **81** | **⚠️ Conditionally Ready** | |

**Verdict: Conditionally Ready**

Không có blocker. Tất cả SRS/FRD/ERD đều accessible. Các issue I-01, I-04, I-05 là implementation details đã được BA xác nhận là không thuộc BA UC scope và được theo dõi qua OQ-EXBOT-013/014/015.

### Major Issues (cần fix hoặc confirm trước khi thiết kế test đầy đủ)

| ID | Finding |
|---|---|
| I-06 | Agent key decrypt step vắng mặt trong UC §3 Main Flow. Failure path khi key revoked mid-flight không documented trong UC (chỉ có trong SRS FR-EXBOT-082). |
| I-04 | marginSummary preflight step không có trong UC — deferred OQ-EXBOT-014 (Tech Lead). |
| I-05 | HLRateLimitDO interaction không có trong UC — deferred OQ-EXBOT-015 (Tech Lead). |

### Recommendation

UC-EXBOT-hedge-sync đã được cải thiện đáng kể so với v1 (score tăng từ 73 → 81, nhờ BA fix I-02, I-03, I-07, I-08 và thêm A6). Tester có thể bắt đầu thiết kế test case cho happy path và alternate flows A1–A6 dựa trên SRS làm bổ sung cho UC. Các scenario cần thêm BA/Tech Lead clarify trước khi viết test: (1) agent key decrypt failure path trong hedge-sync (I-06 — đề nghị BA thêm decrypt step vào UC §3 và mô tả failure path); (2) delta=0 `rebalance_attempts.status` sau khi OQ-EXBOT-013 được chốt (I-01); (3) stop price timing trong INV-STOP step 8 vs reconcile step 13 (I-11 — cần BA làm rõ sequence).

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v2 | 2026-06-26 | qc-uc-read-exbot agent (Trinh.Bui) | Re-audit sau khi BA cập nhật UC (2026-06-20): A5 fixed, A6 added, BR consecutive clarified, trigger fixed, double Postconditions removed. I-02/03/07/08 closed. I-01/04/05 deferred (OQ-EXBOT-013/014/015). New issues I-06 (Open), I-09 (Open), I-10 (Low), I-11 (Low). Score 81/100 Conditionally Ready. |
| v1 | 2026-06-18 | qc-uc-read-exbot agent (Trinh.Bui) | Tạo báo cáo audited lần đầu — SRS-first cross-check. Score 73/100 Conditionally Ready. |
