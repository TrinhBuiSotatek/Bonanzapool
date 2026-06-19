# Báo cáo Rà soát Mức độ Sẵn sàng của Use Case

**Tên tài liệu:** UC Readiness Review — UC-EXBOT-hedge-sync  
**Ngày tạo:** 2026-06-18  
**Người thực hiện:** QC UC Read Exbot Agent  
**Phiên bản:** v1

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-hedge-sync mô tả luồng mà Hedge-Sync Worker thực hiện điều chỉnh vị thế bán khống (short) trên Hyperliquid (HL) theo phương thức **delta-only** — tức là chỉ gửi lệnh điều chỉnh đúng phần chênh lệch giữa kích thước short thực tế và kích thước mục tiêu, không bao giờ đóng toàn bộ rồi mở lại. Đây là hành vi bắt buộc nhằm tối thiểu hóa chi phí giao dịch và tiêu thụ hạn mức API của HL.

Worker nhận message từ hàng đợi `hedge-sync` (được `light-check` enqueue khi phát hiện cần rebalance). Trước khi thực hiện bất kỳ lệnh nào trên HL, worker phải: (1) kiểm tra idempotency qua bảng `queue_idempotency`, (2) đối chiếu `stateVersion` trong message với D1 để loại bỏ message cũ, (3) giành khóa độc quyền qua `UserLockDO` (TTL 90s) để ngăn xung đột song song. Sau khi gửi lệnh delta, worker thực hiện đặt/thay thế lệnh stop bảo vệ qua giao thức INV-STOP (§19.5 SPEC v5.2.6), rồi enqueue reconcile để xác minh kích thước thực tế trên HL trước khi ghi nhận thành công.

UC này liên kết chặt với `UC-EXBOT-light-check` (nguồn trigger), `UC-EXBOT-deep-audit` (phát hiện secondary khi stop replacement bị treo), và `UC-EXBOT-bot-safe-close` (luồng được kích hoạt khi circuit breaker kiệt sức sau nhiều lần hedge-sync thất bại). Các rule liên quan trực tiếp: `BR-EXBOT-004` (delta-only là bất biến mặc định), `FR-EXBOT-022` (delta-only), `FR-EXBOT-024` (cloid tất định), `FR-EXBOT-025` (post-order reconcile), `FR-EXBOT-026` (UserLockDO), `FR-EXBOT-027` (stateVersion optimistic concurrency), `FR-EXBOT-035` (INV-STOP protocol), `FR-EXBOT-040` (circuit breaker).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-hedge-sync | Execute Delta-Only Hedge Adjustment | draft (updated 2026-06-18) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-18 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-hedge-sync.md` | draft 2026-06-18 | UC — tài liệu chính được review | — |
| `userstories/us-006.md` | draft 2026-06-12 | US — delta-only hedge-sync | Linked story |
| `userstories/us-008.md` | draft 2026-06-12 | US — circuit breaker open/close | Linked story |
| `srs/spec.md` | draft 2026-06-18 (v5.2.6) | SRS — source of truth toàn bộ ExBot behavior | — |
| `srs/states.md` | draft 2026-06-18 | State diagram — lifecycle states + circuit breaker | — |
| `srs/flows.md` | draft 2026-06-12 | Flow diagram — F-02 Hedge-Sync Execution | — |
| `srs/erd.md` | draft 2026-06-12 | ERD — data objects, fields, types | — |
| `frd.md` | draft 2026-06-18 | FRD — FR-EXBOT-020 đến FR-EXBOT-040 | — |
| `02_backbone/common-rules.md` | draft 2026-06-17 | Common rules — BR-EXBOT-* | BR-EXBOT-004 được resolve |
| `02_backbone/message-list.md` | draft 2026-06-09 | Message list — E-EXBOT-* | E-EXBOT-007, 008, 011 được resolve |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này tồn tại để đảm bảo vị thế short trên HL luôn phản ánh đúng lượng ETH thực tế trong vị thế LP của bot (tính theo công thức Uniswap V3 AMM), bằng cách điều chỉnh delta tối thiểu sau mỗi lần light-check phát hiện drift. Mục tiêu là duy trì trạng thái delta-hedged liên tục, bảo vệ nhà đầu tư khỏi rủi ro biến động giá ETH, đồng thời tối thiểu hóa chi phí giao dịch và tiêu thụ HL API weight.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Kiểm tra idempotency | Insert `message_id` vào `queue_idempotency` với `state='started'`; xung đột UNIQUE → bỏ qua (duplicate delivery) | FR-EXBOT-011, SRS §FR-EXBOT-011 |
| Kiểm tra stateVersion | Đọc `bot_runtime_state.state_version` từ D1; mismatch → discard, ghi `status='skipped'` | FR-EXBOT-027 |
| Giành khóa UserLockDO | `acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})`; `acquired=false` → re-queue với delay | FR-EXBOT-026 |
| Fetch vị thế HL thực tế | Gọi `clearinghouseState` (weight=2) để lấy kích thước short hiện tại | FR-EXBOT-025, flows.md F-02 |
| Tính toán delta | `delta = BigDecimal(targetShortEth).sub(actualShortEth)`; dùng BigDecimal, không dùng float | FR-EXBOT-021, FR-EXBOT-022 |
| Gửi lệnh delta-only | `adjustShortDelta(delta, cloid)` — chỉ gửi phần chênh lệch, không đóng/mở toàn bộ | FR-EXBOT-022, BR-EXBOT-004 |
| INV-STOP protocol | Thay thế stop sau khi resize hedge: set `stop_replacing_started_at`, thực hiện cancel-then-place được bảo vệ, clear trong `finally` | FR-EXBOT-035 |
| Enqueue reconcile | Enqueue `{botId, attemptId, expectedAbsSize, hedgeLegId}` vào `reconcile` queue | FR-EXBOT-025 |
| Release UserLockDO | `release(holderToken, idempotencyKey, result)` trong `finally` block | FR-EXBOT-026 |
| Post-order reconcile | Reconcile Worker fetch vị thế HL thực tế, xác minh kích thước, extract `entry_price`, `liquidation_price`, `effective_leverage` | FR-EXBOT-025 |
| Cập nhật hedge_legs | Ghi `stop_price`, `entry_price`, `effective_leverage`, xóa `stop_replacing_started_at` | FR-EXBOT-025, FR-EXBOT-035 |
| Cập nhật bot_runtime_state | `last_known_hl_short_size = reconciled_size` | FR-EXBOT-025 |
| Ghi rebalance_attempts | Insert row với `status='success'` sau khi reconcile xác nhận | FR-EXBOT-025 |
| Cập nhật queue_idempotency | `state='succeeded'` | FR-EXBOT-011 |
| Xử lý lỗi HL order rejection | Ghi `status='failed'`, gọi `incrementCircuitBreaker`, enqueue notification | FR-EXBOT-040 |
| Xử lý partial fill | Reconcile phát hiện mismatch → enqueue `partial_repair` | FR-EXBOT-036 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| LP range rebalance (`lp_rebalancing`) | Được xử lý trong `partial_repair` queue / UC riêng | Không ảnh hưởng test UC này |
| Stop trigger detection (`markPrice >= stop_price`) | Thuộc UC-EXBOT-light-check; không phải trigger của hedge-sync | Không ảnh hưởng |
| SAFE_MODE entry do `stop_replacing_started_at` stuck | UC hedge-sync chỉ set/clear trường này; detection thuộc light-check (primary) và deep-audit (secondary) | Test SAFE_MODE entry ở UC-EXBOT-light-check / UC-EXBOT-deep-audit |
| bot_safe_close execution | Được trigger khi circuit breaker kiệt sức, nhưng execution nằm ở UC-EXBOT-bot-safe-close | Không ảnh hưởng |
| Margin status update | Chỉ xảy ra ở preflight hedge-sync và deep-audit; UC này không explicitly mô tả bước fetch `marginSummary` trước khi gửi lệnh delta | Xem Issue I-04 |
| Cloid formula cụ thể | FR-EXBOT-024 và srs/spec.md định nghĩa rõ cloid formula; UC chỉ đề cập `cloid` không giải thích — không ảnh hưởng vì SRS là nguồn gốc | Đọc từ SRS |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Hedge-Sync Worker) | Primary / System | Thực thi toàn bộ luồng hedge-sync từ khi nhận message đến khi ghi kết quả | Không có quyền user-facing; hoạt động hoàn toàn tự động qua queue | UC §1, US-006 |
| UserLockDO | Secondary / System (Durable Object) | Cung cấp mutex theo user — ngăn hai worker cùng mutate HL position cho cùng một user | TTL=90s; `acquired=false` → re-queue; heartbeat khi work > 30s | FR-EXBOT-026, FR-EXBOT-092 |
| Hyperliquid API | External | Nhận lệnh `adjustShortDelta`, trả về fill confirmation; cung cấp `clearinghouseState` cho reconcile | Rate limit budget 800 weight/min qua `HLRateLimitDO`; `clearinghouseState` weight=2 | FR-EXBOT-091, SRS §FR-EXBOT-091 |
| D1 (state_db_shard) | Secondary / System | Lưu trữ `bot_runtime_state`, `hedge_legs`, `rebalance_attempts`, `queue_idempotency` | Ghi atomically; không ghi `rebalance_attempts.status='success'` trước reconcile | FR-EXBOT-025 |
| Reconcile Worker | Secondary / System | Xác minh kích thước HL sau lệnh delta; cập nhật D1 | Chạy qua `reconcile` queue; là worker riêng | FR-EXBOT-025, flows.md F-02 |

**Nhận xét readiness:**  
Actor đủ rõ cho test design. Tuy nhiên UC không mô tả rõ `HLRateLimitDO` là bước kiểm tra trước khi gọi HL — nếu budget vượt ngưỡng (`allowed=false`) thì worker xử lý thế nào. SRS định nghĩa rõ tại FR-EXBOT-091 nhưng UC hoàn toàn bỏ qua interaction này. (Xem Issue I-05.)

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Message `hedge-sync` nhận được với payload `{botId, reasons: RebalanceReason[], stateVersion}` | Yes | UC §2 |
| 2 | `bots.status='active'` và `bots.lifecycle_state='active'` | Yes | UC §2 |
| 3 | `circuit_breakers.state IN ('closed', 'half_open')` | Yes | UC §2 |
| 4 | HL agent key `approval_status='approved'` và chưa hết hạn | Yes (implicit — cần để giải mã key khi gọi HL) | FR-EXBOT-080, FR-EXBOT-082 |
| 5 | `bot_runtime_state.state_version` tồn tại trong D1 | Yes | FR-EXBOT-027 |
| 6 | `hedge_legs` row tồn tại với `stop_price`, `entry_price` đã được populate (từ bot-start hoặc hedge-sync trước) | Yes | FR-EXBOT-031, FR-EXBOT-025 |

### 3.2 Kết quả sau khi hoàn tất (happy path)

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Delta adjustment thành công + reconcile xác nhận | `hedge_legs.stop_price`, `entry_price`, `effective_leverage` cập nhật; `stop_replacing_started_at=NULL`; `bot_runtime_state.last_known_hl_short_size` = reconciled size | UC §5, FR-EXBOT-025 |
| Ghi nhận attempt | `rebalance_attempts` row với `status='success'` được insert sau reconcile | FR-EXBOT-025 |
| Queue idempotency | `queue_idempotency.state='succeeded'` | FR-EXBOT-011 |
| Circuit breaker | Nếu đây là probe `half_open` thành công: `circuit_breakers.state='closed'`, `failure_count=0` | FR-EXBOT-040, US-008 AC-3 |
| stateVersion mismatch | `rebalance_attempts.status='skipped'`; không có lệnh HL nào | FR-EXBOT-027 |
| Lock không giành được | Message re-enqueue với delay; không có lệnh HL nào | FR-EXBOT-026 |
| HL order rejected | `rebalance_attempts.status='failed'`; `circuit_breakers.failure_count` tăng; notification enqueued | FR-EXBOT-040 |
| Partial fill | `partial_repair` message enqueued; `rebalance_attempts.status='partial'` | FR-EXBOT-036 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### §F.1 — Inventory (function / operation / data object)

| # | Loại | Tên / Operation | Trigger | Input | Output | Data Object / Field | Nguồn |
|---|---|---|---|---|---|---|---|
| F1-01 | Operation | Insert idempotency check | Message deliver | `message_id` | UNIQUE conflict → skip; else continue | `queue_idempotency.message_id`, `state` | FR-EXBOT-011 |
| F1-02 | Operation | stateVersion check | Post-idempotency | `bot_runtime_state.state_version`, message `stateVersion` | Match → continue; mismatch → discard | `bot_runtime_state.state_version`, `rebalance_attempts.status='skipped'` | FR-EXBOT-027 |
| F1-03 | Operation | UserLockDO.acquire | Post-stateVersion check | `holderToken` (UUID), `ttl=90s`, `idempotencyKey=hedge-sync:{botId}:{stateVersion}` | `{acquired: boolean, leaseId?}` | `UserLockDO` internal lease table | FR-EXBOT-026, FR-EXBOT-092 |
| F1-04 | Operation | Fetch actual HL position | Post-lock acquired | `botId`, `hl_account_address` | `actualShortEth` (từ `clearinghouseState`) | `hedge_legs.last_known_hl_short_size` (stale reference trước sync) | FR-EXBOT-025, flows.md F-02 |
| F1-05 | Operation | Compute delta | Post-fetch | `targetShortEth`, `actualShortEth` (BigDecimal) | `delta` (BigDecimal, có thể âm hoặc dương) | `bot_runtime_state.target_short_size` | FR-EXBOT-021, FR-EXBOT-022 |
| F1-06 | Operation | adjustShortDelta | Post-compute | `delta`, `cloid` (deterministic keccak256) | Fill confirmation từ HL | `rebalance_attempts.adjust_cloid` | FR-EXBOT-022, BR-EXBOT-004 |
| F1-07 | Operation | INV-STOP protocol — stop replacement | Post-delta-send | `stop_replacing_started_at` set, cancel current stop → place new stop với `stop_trigger_px` mới | `stop_cloid` mới, stop confirmed | `hedge_legs.stop_replacing_started_at`, `stop_cloid`, `stop_price`, `stop_size` | FR-EXBOT-035 |
| F1-08 | Operation | Enqueue reconcile | Post-INV-STOP | `{botId, attemptId, expectedAbsSize, hedgeLegId}` | Reconcile message trong `reconcile` queue | `queue_idempotency` cho reconcile message | FR-EXBOT-025 |
| F1-09 | Operation | UserLockDO.release | Post-enqueue (finally block) | `holderToken`, `idempotencyKey`, `result` | Lease released | `UserLockDO` internal | FR-EXBOT-026 |
| F1-10 | Operation | Post-order reconcile (Reconcile Worker) | `reconcile` queue message | `botId`, `attemptId`, `expectedAbsSize`, `hedgeLegId` | `reconciled_size`, `entry_price`, `liq_price`, `effective_leverage` | `hedge_legs`, `bot_runtime_state.last_known_hl_short_size` | FR-EXBOT-025 |
| F1-11 | Operation | Recompute stop_trigger_px | Post-reconcile | `entry_price`, `liquidation_price` (hoặc `effective_leverage`), `stopSafetyFactor=0.70` | `stop_trigger_px` (BigDecimal) | `hedge_legs.stop_price` | FR-EXBOT-030, SRS §FR-EXBOT-030 |
| F1-12 | Operation | Insert rebalance_attempts | Post-reconcile confirmed | `botId`, `status`, `reason`, `adjust_cloid`, `reconciled_short_size`, v.v. | Row inserted | `rebalance_attempts` | FR-EXBOT-025 |
| F1-13 | Operation | Update queue_idempotency | Post-success | `message_id`, `state='succeeded'` | Row updated | `queue_idempotency.state` | FR-EXBOT-011 |
| F1-14 | Operation | incrementCircuitBreaker | On HL order failure | `hedge_leg_id` | `failure_count++`; nếu ≥ 3 trong 24h → `circuit_breakers.state='open'` | `circuit_breakers.failure_count`, `state`, `reset_at` | FR-EXBOT-040 |
| F1-15 | Operation | Enqueue partial_repair | On partial fill detected | `{botId, reason='partial_fill', attemptId}` | Partial repair message trong `partial_repair` queue | `rebalance_attempts.status='partial'` | FR-EXBOT-036 |
| F1-16 | Event | Circuit breaker `closed→open` | 3 consecutive failures trong 24h | — | `circuit_breakers.state='open'`, `reset_at=now+1h` | `circuit_breakers.state`, `reset_at`, `failure_count` | FR-EXBOT-040 |
| F1-17 | Event | Circuit breaker `half_open→closed` | Probe hedge-sync thành công | — | `circuit_breakers.state='closed'`, `failure_count=0` | `circuit_breakers.state` | FR-EXBOT-040, US-008 AC-3 |
| F1-18 | Event | Circuit breaker `half_open→open` | Probe hedge-sync thất bại | — | `circuit_breakers.state='open'`, `reset_at=now+1h` | `circuit_breakers.state`, `reset_at` | FR-EXBOT-040, US-008 AC-4 |
| F1-19 | State (lifecycle) | `active` | Bot đang hoạt động bình thường khi nhận hedge-sync | — | — | `bots.lifecycle_state`, `bots.status='active'` | SRS states.md |
| F1-20 | State (circuit) | `closed` / `half_open` / `open` | Circuit breaker state | — | `closed`: hedge-sync allowed; `half_open`: 1 probe; `open`: suppressed | `circuit_breakers.state` | FR-EXBOT-040, SRS states.md |
| F1-21 | Data Object | `queue_idempotency` | Per message | `message_id`, `kind`, `state`, `bot_id` | UNIQUE constraint trên `message_id` | `queue_idempotency.key` PK, `message_id` UNIQUE INDEX | ERD |
| F1-22 | Data Object | `bot_runtime_state` | Per bot | `state_version`, `lp_eth_amount`, `target_short_size`, `last_known_hl_short_size` | Updated after reconcile | `bot_id` PK | ERD |
| F1-23 | Data Object | `hedge_legs` | Per bot | `stop_price`, `stop_cloid`, `entry_price`, `liq_price`, `effective_leverage`, `stop_replacing_started_at`, `margin_status` | Updated after reconcile | `hedge_legs.id` PK, `bot_id` FK | ERD |
| F1-24 | Data Object | `rebalance_attempts` | Per attempt | `status` enum: `success` / `failed` / `skipped` / `partial`; `reason` (canonical `RebalanceReason[]`) | Row per attempt | `rebalance_attempts.id` PK | ERD, FR-EXBOT-023 |
| F1-25 | Enum | `RebalanceReason[]` | Trong queue message | `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile` | Dùng làm `rebalance_attempts.reason` | `rebalance_attempts.reason` TEXT | FR-EXBOT-023 |
| F1-26 | Message (error) | `E-EXBOT-007` | HL order rejected — margin không đủ | — | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." (HTTP 502) | `rebalance_attempts.error_code` | SRS §5 Error Codes |
| F1-27 | Message (error) | `E-EXBOT-008` | HL API unreachable | — | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." (HTTP 503) | — | SRS §5 Error Codes |
| F1-28 | Message (error) | `E-EXBOT-011` | Reconcile mismatch | — | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." (internal) | — | SRS §5 Error Codes |

---

### §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Item | States / Điều kiện | Precondition | Validation / Business Rule | Dependency | Resolved Message | Nguồn |
|---|---|---|---|---|---|---|
| `queue_idempotency.message_id` | `started` → `succeeded` / `failed` / `retryable` | Message được deliver | UNIQUE constraint: xung đột → worker exit ngay, không xử lý | `queue_idempotency` table tồn tại | — | FR-EXBOT-011 |
| `bot_runtime_state.state_version` | INTEGER, tăng dần | D1 accessible | Nếu message `stateVersion` < D1 value → discard (`status='skipped'`). Không gửi lệnh HL nào | `bot_runtime_state` row tồn tại | — | FR-EXBOT-027 |
| `UserLockDO` lease | `acquired=true` / `acquired=false` | Bot user_id xác định | TTL=90s; nếu work > 30s → heartbeat gia hạn; release trong `finally` | `UserLockDO` Durable Object | — | FR-EXBOT-026, FR-EXBOT-092 |
| `delta` (BigDecimal) | dương (tăng short) / âm (giảm short) / zero | `targetShortEth`, `actualShortEth` có mặt | Bắt buộc dùng BigDecimal — `Number()` arithmetic là vi phạm. `target_ratio_bps` normalize qua `normalizeTargetRatioBps()` | `bot_runtime_state.target_short_size`, `lp_eth_amount`, `hedge_ratio` | — | FR-EXBOT-021, NFR-EXBOT-008 |
| `cloid` (deterministic) | Cố định với cùng `botId + attemptId + stage + version` | — | `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Retry cùng payload → cùng cloid. Payload khác → increment `version`. Duplicate cloid detected → reconcile trước, không retry mù | — | — | FR-EXBOT-024 |
| `adjustShortDelta` | Delta-only (increase hoặc reduce-only) | Lock acquired, delta computed | Full close → open là vi phạm trong normal hedge-sync. Cho phép full close/open CHỈ KHI: target=0 (close path), emergency reset, manual reset (Phase B+) | HL API available, budget không vượt ngưỡng | `E-EXBOT-007` nếu margin không đủ | BR-EXBOT-004, FR-EXBOT-022 |
| `stop_replacing_started_at` | Non-NULL trong khi thay thế stop; NULL khi không có replacement | Sau khi delta order confirmed | Phải set trước khi bắt đầu INV-STOP critical section; phải clear trong `finally`. Nếu stuck > 60s → light-check primary detection (≤5 min) → SAFE_MODE | `hedge_legs` row tồn tại | — | FR-EXBOT-035, FR-EXBOT-033 |
| `stop_trigger_px` | BigDecimal, luôn > `entry_price` | `entry_price`, `liquidation_price` hoặc `effective_leverage` có mặt | Công thức: `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`. `liq_distance_pct = (liq_price − entry_price) / entry_price` (ưu tiên HL value; fallback: `1 / effective_leverage`). Phase A `stopSafetyFactor = 0.70`. Bắt buộc BigDecimal | `hedge_legs.entry_price`, `hedge_legs.liquidation_price` | `E-EXBOT-009` nếu stop placement thất bại | FR-EXBOT-030 |
| `rebalance_attempts.status` | `success` / `failed` / `skipped` / `partial` | — | `status='success'` chỉ được ghi SAU KHI reconcile xác nhận. Không ghi trước reconcile | `rebalance_attempts` table | — | FR-EXBOT-025 |
| `circuit_breakers.state` | `closed` / `open` / `half_open` | — | Source of truth là column `circuit_breakers.state`, KHÔNG dynamic compute từ history. Reset về `closed` CHỈ khi probe thành công. Partial/failed không reset | `circuit_breakers` table | Notification khi `open` | FR-EXBOT-040, US-008 Notes |
| `circuit_breakers.failure_count` | INTEGER, 0 đến N | — | 3 consecutive failures trong 24h → `state='open'`. Reset = 0 khi `closed` | `circuit_breakers` table | — | FR-EXBOT-040 |
| `half_open_probe_used` | 0 (available) / 1 (used) | `circuit_breakers.state='half_open'` | Atomic claim 0→1; chỉ 1 probe được phép khi `half_open`. Nếu đã 1 → block thêm probe | `circuit_breakers` table | — | FR-EXBOT-040, SRS states.md |
| `hedge_legs.margin_status` | `ok` / `warning` / `critical` | — | Được đọc từ D1 (không fetch HL) trong light-check. **UC không mô tả** bước fetch `marginSummary` trước khi gửi delta — nhưng SRS FR-EXBOT-060 định nghĩa margin status được update "just before hedge-sync" | SRS §FR-EXBOT-060 | `E-EXBOT-007` nếu margin critical | FR-EXBOT-060 (xem Issue I-04) |

**Business Rule BR-EXBOT-004 (resolved):**  
Điều chỉnh hedge theo phương thức delta-only là bất biến mặc định. Full close → open trong normal hedge-sync là lỗi. (Nguồn: `common-rules.md` BR-EXBOT-004; nội dung gốc: "Delta-only hedge adjustment is the invariant default. Full close → open in normal hedge-sync is a bug.")

---

### §F.3 — Functional Logic & Workflow Decomposition

#### 6.1 Luồng chính — Delta-only hedge adjustment thành công

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Hedge-Sync Worker | Nhận `hedge-sync` message từ queue | Insert `queue_idempotency` với `state='started'` | — | UNIQUE conflict → exit immediately, không xử lý (duplicate delivery) | FR-EXBOT-011 |
| 2 | Worker | Đọc `bot_runtime_state.state_version` từ D1 | Đọc thành công | — | Message `stateVersion` ≠ D1 → ghi `status='skipped'`, không tiếp tục | FR-EXBOT-027 |
| 3 | Worker | Gọi `UserLockDO.acquire(holderToken, 90s, idempotencyKey)` | `{acquired: true, leaseId}` | `acquired=false` → re-queue message với delay | HL mutation không thể thực hiện khi `acquired=false` | FR-EXBOT-026 |
| 4 | Worker | Fetch vị thế HL: `clearinghouseState` (weight=2) | `actualShortEth` từ HL response | — | HL unreachable > 5 min → SAFE_MODE (`E-EXBOT-008`) | FR-EXBOT-025, FR-EXBOT-091 |
| 5 | Worker | Tính `delta = BigDecimal(targetShortEth).sub(actualShortEth)` | Delta computed (BigDecimal) | delta = 0 → không gửi lệnh (implicit; UC không nêu rõ — xem Issue I-01) | — | FR-EXBOT-021 |
| 6 | Worker | `adjustShortDelta(delta, cloid)` | Fill confirmation từ HL | — | HL order rejected → `status='failed'`, `incrementCircuitBreaker`, enqueue notification | FR-EXBOT-022 |
| 7 | Worker | INV-STOP: set `stop_replacing_started_at`, cancel current stop, place new stop với `stop_trigger_px` | Stop replaced; `stop_replacing_started_at` cleared trong `finally` | — | Stop placement fail → `E-EXBOT-009`; `stop_replacing_started_at` stuck > 60s → SAFE_MODE | FR-EXBOT-035, FR-EXBOT-033 |
| 8 | Worker | Enqueue `{botId, attemptId, expectedAbsSize, hedgeLegId}` → `reconcile` queue | Reconcile message enqueued | — | — | FR-EXBOT-025 |
| 9 | Worker | `UserLockDO.release(holderToken, idempotencyKey, result)` | Lease released | — | Không release → TTL 90s tự expire | FR-EXBOT-026 |
| 10 | Reconcile Worker | Fetch actual HL position; verify `size == expectedAbsSize` | Match → tiếp tục | — | Mismatch → `E-EXBOT-011`; enqueue `partial_repair` (A4); vào SAFE_MODE | FR-EXBOT-025 |
| 11 | Reconcile Worker | Extract `entry_price`, `liq_price`, `effective_leverage`; recompute `stop_trigger_px` | `hedge_legs` updated; `bot_runtime_state.last_known_hl_short_size` updated | — | — | FR-EXBOT-025, FR-EXBOT-030 |
| 12 | Reconcile Worker | Insert `rebalance_attempts` với `status='success'`; update `queue_idempotency.state='succeeded'` | Done | — | — | FR-EXBOT-025, FR-EXBOT-011 |

#### 6.2 Luồng A1 — Lock không giành được

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 3 | Worker | `UserLockDO.acquire` → `acquired=false` với `currentHolderExpiresAt` | Re-queue message với delay (không immediate retry) | FR-EXBOT-026, US-006 AC-3 |

#### 6.3 Luồng A2 — stateVersion mismatch

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 2 | Worker | `stateVersion` trong message < `state_version` trong D1 | Discard message; ghi `rebalance_attempts.status='skipped'`; không gửi lệnh HL | FR-EXBOT-027, US-006 AC-2 |

#### 6.4 Luồng A3 — HL order rejected

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 6 | Worker | HL trả về lỗi (ví dụ: insufficient margin) | Ghi `rebalance_attempts.status='failed'` + error details; gọi `incrementCircuitBreaker`; enqueue notification | FR-EXBOT-040, US-006 AC-4 |
| — | Worker | Sau 3 consecutive failures trong 24h | `circuit_breakers.state='open'`, `reset_at=now+1h` | FR-EXBOT-040 |

#### 6.5 Luồng A4 — Partial fill

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| 10 | Reconcile Worker | Reconcile phát hiện `|actual − expected| > tolerance` | Enqueue `partial_repair` với `reason='partial_fill'` | FR-EXBOT-036 |
| — | Partial Repair Worker | Fetch actual, compute remaining delta, resubmit với new cloid (incremented `version`) | Tối đa 3 lần; sau 3 thất bại → `bot_safe_close` | FR-EXBOT-036 |

#### 6.6 Luồng A5 — stop_replacing_started_at stuck (được mô tả trong UC)

| Bước | Actor | Hành động | Kết quả | Nguồn |
|---|---|---|---|---|
| — | Light-Check Worker (primary) | Phát hiện `stop_replacing_started_at IS NOT NULL AND age > 60s` trong lần light-check kế tiếp (≤5 min) | Enqueue `partial_repair(reason='stop_replacing_overrun')`; enter SAFE_MODE | FR-EXBOT-033 primary |
| — | Deep-Audit Worker (secondary) | Phát hiện cùng điều kiện nếu light-check miss | Enter SAFE_MODE (backstop) | FR-EXBOT-033 secondary, FR-EXBOT-016 |

**Lưu ý quan trọng về A5:** UC §A5 ghi nhãn sai khi cite `uc-deep-audit.md` là nơi xử lý A5, thay vì đề cập light-check là **primary** detection path theo FR-EXBOT-033. UC bỏ sót primary detection path. (Xem Issue I-02.)

---

### §F.4 — Functional Integration & Data Consistency

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| `adjustShortDelta` gửi lệnh thành công | `reconcile` queue → Reconcile Worker | Reconcile Worker phải xác nhận kích thước HL trước khi ghi `status='success'` | `rebalance_attempts.status` không được ghi trước reconcile confirm; `last_known_hl_short_size` trong D1 phải = giá trị reconciled | FR-EXBOT-025 |
| `stop_replacing_started_at` set | Light-Check Worker (≤5 min sau) | Nếu stuck > 60s, light-check enqueue `partial_repair` + SAFE_MODE | `stop_replacing_started_at` phải NULL sau khi INV-STOP hoàn tất (`finally` block) | FR-EXBOT-033, FR-EXBOT-035 |
| Circuit breaker `state='open'` | `UC-EXBOT-light-check` (suppress hedge-sync enqueue) | Light-check không enqueue `hedge-sync` khi `state='open'`; stop monitoring tiếp tục | `circuit_breakers.state` là canonical source; không compute động từ `rebalance_attempts` history | FR-EXBOT-040, FR-EXBOT-014 |
| Circuit breaker `state='half_open'` probe thành công | Light-Check tiếp theo resume bình thường | `failure_count` reset = 0; light-check resume enqueue hedge-sync | `circuit_breakers.state='closed'` atomic sau probe success | FR-EXBOT-040 |
| `rebalance_attempts.status='failed'` + `incrementCircuitBreaker` | `circuit_breakers` table | failure_count tăng; nếu ≥ 3 trong 24h → `state='open'` | Đếm "consecutive failures within 24h" — SRS không định nghĩa rõ window-exact logic (xem Issue I-03) | FR-EXBOT-040 |
| Partial fill → `partial_repair` queue | Partial Repair Worker | Worker fetch actual, compute remaining delta, resubmit với cloid version mới | Sau 3 thất bại partial repair → `close_operations` row cho `bot_safe_close` | FR-EXBOT-036, FR-EXBOT-072 |
| `UserLockDO` lease | Đảm bảo chỉ 1 hedge-sync worker mutate HL cho 1 user tại một thời điểm | Concurrent mutations bị block; worker thứ 2 re-queue | Khi lease expire (90s auto-release): worker tiếp theo acquire và reconcile TRƯỚC khi submit lệnh mới | FR-EXBOT-026, FR-EXBOT-092 |
| `bot_runtime_state.last_known_hl_short_size` | Light-Check Worker (lần sau) | Light-check dùng giá trị này để compute `deltaErrorUsd` (drift evaluation) | Nếu reconcile thất bại và `last_known_hl_short_size` không cập nhật, light-check drift eval lần sau sẽ sai | FR-EXBOT-012 |
| HL agent key (AES-GCM decrypt) khi gọi HL | `hl_agent_keys` table | Key phải `approval_status='approved'` và chưa hết hạn để decrypt; key bị revoke trong khi hedge-sync → SAFE_MODE | Plain key function-scope only; không log | FR-EXBOT-080, FR-EXBOT-082 |

---

### §F.5 — Acceptance Criteria Candidates

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — delta-only adjustment thành công | Bot `status='active'`, `lifecycle_state='active'`, `circuit_breakers.state='closed'`; message stateVersion khớp D1 | Worker acquire lock, fetch HL position, compute delta (BigDecimal), gửi `adjustShortDelta`, thực hiện INV-STOP, enqueue reconcile, release lock | Reconcile xác nhận size; `hedge_legs` cập nhật stop/entry/leverage; `rebalance_attempts.status='success'`; `queue_idempotency.state='succeeded'` | US-006 AC-1; SRS F-02 |
| AC-02 | stateVersion mismatch | Message `stateVersion=5`; D1 `state_version=6` | Worker kiểm tra trước khi acquire lock | `rebalance_attempts.status='skipped'`; không có lệnh HL nào; lock không được acquire | US-006 AC-2; FR-EXBOT-027 |
| AC-03 | Lock không giành được | Worker khác đang hold `UserLockDO` lease cho cùng user | Worker gọi `acquire` | `acquired=false`; message re-queue với delay; không có lệnh HL | US-006 AC-3; FR-EXBOT-026 |
| AC-04 | HL order rejected — insufficient margin | Delta order gửi đi; HL trả lỗi margin | HL rejection response | `rebalance_attempts.status='failed'`; `failure_count++`; notification enqueued | US-006 AC-4; E-EXBOT-007 |
| AC-05 | 3 consecutive failures → circuit open | 2 failure trước đó trong 24h; lần này failed lại | Failure thứ 3 được ghi | `circuit_breakers.state='open'`; `reset_at=now+1h`; light-check sau không enqueue hedge-sync; stop monitoring vẫn tiếp tục | US-008 AC-1; FR-EXBOT-040 |
| AC-06 | Probe `half_open` thành công | `circuit_breakers.state='half_open'`; probe hedge-sync hoàn tất | Reconcile confirm success | `circuit_breakers.state='closed'`; `failure_count=0`; `half_open_probe_used` không reset về 0 ngay | US-008 AC-3; FR-EXBOT-040 |
| AC-07 | Probe `half_open` thất bại | `circuit_breakers.state='half_open'` | Probe fail | `circuit_breakers.state='open'`; `reset_at=now+1h`; admin notification "Circuit re-opened after failed probe for bot {id}" | US-008 AC-4; FR-EXBOT-040 |
| AC-08 | Partial fill → partial_repair | Reconcile phát hiện actual size khác expected | `|actual − expected| > tolerance` | `partial_repair` enqueued; `rebalance_attempts.status='partial'`; sau 3 thất bại repair → `close_operations` cho `bot_safe_close` | FR-EXBOT-036 |
| AC-09 | INV-STOP overrun → SAFE_MODE (Suy luận cần xác nhận) | `stop_replacing_started_at` được set nhưng worker crash; light-check tiếp theo (≤5 min) phát hiện age > 60s | Light-check evaluate `stop_replacing_started_at` | `partial_repair(reason='stop_replacing_overrun')` enqueued; SAFE_MODE entry | FR-EXBOT-033 primary; UC A5 cite sai — cần BA xác nhận |
| AC-10 | Duplicate message delivery | Cùng `message_id` được deliver 2 lần | Lần 2: `queue_idempotency` UNIQUE conflict | Worker exit immediately; không có lệnh HL lần 2 | FR-EXBOT-011 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Hedge-sync hoàn tất → `last_known_hl_short_size` cập nhật | UC-EXBOT-light-check | Light-check lần sau dùng giá trị này để tính drift — nếu không cập nhật, drift eval sai | `bot_runtime_state.last_known_hl_short_size` phải = reconciled size sau mỗi hedge-sync thành công | FR-EXBOT-012 |
| Circuit breaker `open` | UC-EXBOT-light-check | Light-check suppress `hedge-sync` enqueue; stop monitoring vẫn chạy | `circuit_breakers.state` là canonical source; không tính động | FR-EXBOT-040, FR-EXBOT-014 |
| 3 consecutive failures → bot_safe_close trigger path | UC-EXBOT-bot-safe-close | Khi `circuit_breakers` bị extend 3+ lần mà probe không thành công → `bot_safe_close` | `close_operations` row với `trigger_reason='circuit_breaker_exhausted'` | FR-EXBOT-072 |
| Partial repair fail 3 lần | UC-EXBOT-bot-safe-close | `bot_safe_close` được kích hoạt | `close_operations` row | FR-EXBOT-036, FR-EXBOT-072 |
| `stop_replacing_started_at` stuck | UC-EXBOT-light-check, UC-EXBOT-deep-audit | SAFE_MODE entry | `bots.lifecycle_state` → `safe_mode` | FR-EXBOT-033 |
| Agent key decrypt khi gọi HL | `hl_agent_keys` table | Key phải approved + unexpired; revoke trong khi hedge-sync → SAFE_MODE | Không log raw key | FR-EXBOT-080, FR-EXBOT-082 |

---

## 8. Acceptance Criteria

*(Xem §F.5 phía trên — AC-01 đến AC-10)*

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Một hedge-sync hoàn chỉnh phải xong trong 30 giây trong điều kiện bình thường | Test scenario: đo thời gian từ khi message nhận đến khi ghi `status='success'` | NFR-EXBOT-002 |
| Rate Limit | HL API weight không được vượt 800/min; `clearinghouseState` weight=2; mọi call qua `HLRateLimitDO` | Test: khi budget vượt ngưỡng (`allowed=false`), worker không gửi lệnh | NFR-EXBOT-004, FR-EXBOT-091 |
| Precision | Mọi tính toán hedge, stop, margin dùng BigDecimal; không dùng float/number cho financial value | Test: cloid formula, delta computation, stop_trigger_px dùng BigDecimal | NFR-EXBOT-008 |
| Security | Agent key (AES-GCM) chỉ decrypt function-scope; không log raw key | Test: log audit không có raw key | NFR-EXBOT-006, FR-EXBOT-080 |
| Idempotency | `queue_idempotency.message_id` UNIQUE ngăn double execution; cloid deterministic ngăn double HL order | Test: deliver cùng message 2 lần → kết quả chỉ 1 lần | NFR-EXBOT-007 |
| Concurrency | Max 6 simultaneous outbound connections per CF Worker invocation | Không ảnh hưởng trực tiếp test hedge-sync đơn lẻ | NFR-EXBOT-011 |
| Reliability | `UserLockDO` TTL=90s auto-release; worker heartbeat khi work > 30s | Test: lease expire → worker tiếp theo reconcile trước khi submit | FR-EXBOT-026 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional requirement — yêu cầu chức năng cụ thể của module ExBot. Trong project, đây là source of truth chi tiết hơn FRD cho implementation | `srs/spec.md` |
| BR-EXBOT-* | Business rule — quy tắc nghiệp vụ bất biến của module ExBot | `02_backbone/common-rules.md` |
| E-EXBOT-* | Error/message code — API-layer error response của ExBot. Là canonical source cho error handling documentation | `srs/spec.md §5`, cross-ref `02_backbone/message-list.md` |
| INV-STOP | Invariant Stop — giao thức thay thế stop được bảo vệ (§19.5 SPEC v5.2.6), ngăn trạng thái không có stop trong khoảng thời gian giữa cancel và place | SRS §FR-EXBOT-035 |
| UserLockDO | Durable Object cung cấp mutex dạng lease per user — ngăn hai worker mutate HL position cho cùng user đồng thời | FR-EXBOT-026, FR-EXBOT-092 |
| cloid | Client Order ID — định danh lệnh tất định cho HL, tính từ keccak256 để đảm bảo idempotency | FR-EXBOT-024 |
| BigDecimal | Kiểu tính toán chính xác cho tài chính — không dùng JS Number/float | NFR-EXBOT-008 |
| stateVersion | Số phiên bản trạng thái bot trong D1 — dùng để phát hiện message cũ (optimistic concurrency) | FR-EXBOT-027 |

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 | High | MISSING_INFO | UC §3 Main Flow Bước 5-6; SRS FR-EXBOT-022 | UC không mô tả hành vi khi `delta = 0` (tức là kích thước short thực tế đã bằng kích thước mục tiêu). Theo logic delta-only, không có lệnh HL nào nên được gửi và worker nên ghi `status='skipped'` hoặc `status='no_action'`. Tuy nhiên UC không định nghĩa luồng này. BA/Tech Lead vui lòng xác nhận: khi delta = 0, worker ghi `rebalance_attempts` với status gì, và có update `queue_idempotency.state='succeeded'` không? | Tester không thể viết test case cho edge case delta = 0 vì expected result chưa được định nghĩa | BA / Tech Lead | Open |
| I-02 | High | CROSS_SOURCE_CONFLICT | UC §A5; SRS FR-EXBOT-033; FRD §FR-EXBOT-031 | UC §A5 mô tả luồng khi `stop_replacing_started_at` stuck > 60s như sau: "Enter SAFE_MODE (see uc-deep-audit.md — FR-EXBOT-016 secondary detection path)". Đây là mô tả **sai** và **thiếu** vì: (1) SRS FR-EXBOT-033 định nghĩa rõ **primary detection là light-check** (≤5 min), không phải deep-audit; (2) deep-audit chỉ là secondary backstop. UC hoàn toàn bỏ sót luồng primary (light-check detect và enter SAFE_MODE trong vòng 5 phút), tạo ra ấn tượng sai rằng chỉ deep-audit mới detect được. BA/Tech Lead vui lòng cập nhật A5 để: (a) mô tả primary path = light-check enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE trong ≤5 min, (b) đề cập secondary path = deep-audit. | Tester sẽ thiết kế test sai nếu chỉ kiểm tra deep-audit interval (6h/1h) thay vì light-check interval (5 min) cho scenario này — dẫn đến bỏ sót test case SLA quan trọng | BA | Open |
| I-03 | High | UNCLEAR_INFO | UC §A3; SRS FR-EXBOT-040; US-008 AC-1 | UC §A3 và SRS FR-EXBOT-040 đều ghi "3 consecutive failures within 24h" nhưng không định nghĩa rõ "consecutive" có nghĩa là gì trong ngữ cảnh này: (a) 3 lần thất bại liên tiếp bất kể thời gian giữa các lần, (b) 3 lần thất bại trong rolling window 24h không nhất thiết liên tiếp, hay (c) 3 lần thất bại liên tiếp mà không có lần thành công nào xen giữa, trong window 24h? US-008 AC-1 ghi "2 previous failed attempts within the last 24h → third fails → circuit opens" — ngụ ý rolling window, nhưng từ "consecutive" trong SRS mâu thuẫn với diễn đạt này. Tech Lead vui lòng xác nhận: khi nào failure_count reset về 0? Nếu có 1 lần success giữa 3 lần fail, circuit có mở không? | Tester cần biết chính xác điều kiện để viết test circuit breaker; nếu định nghĩa sai, test có thể pass/fail sai | Tech Lead | Open |
| I-04 | Medium | MISSING_INFO | SRS FR-EXBOT-060; UC §3 Main Flow; FRD §4.7 | SRS FR-EXBOT-060 định nghĩa: margin status được update "just before hedge-sync (fetch HL marginSummary)". UC hoàn toàn bỏ sót bước này. Không rõ: (a) bước fetch `marginSummary` xảy ra ở vị trí nào trong flow (trước hay sau khi acquire lock?), (b) nếu `margin_status='warning'` được phát hiện tại thời điểm này thì size-increase hedge adjustment bị chặn như thế nào (UC không mô tả), (c) nếu `margin_status='critical'` (×2 consecutive) thì hedge-sync abort và enter SAFE_MODE ngay không? | Tester không thể test các trường hợp `margin_warning` và `margin_critical` xảy ra ngay tại thời điểm hedge-sync mà không có flow rõ ràng trong UC | BA | Open |
| I-05 | Medium | MISSING_INFO | SRS FR-EXBOT-091; UC §3 Main Flow | UC không đề cập bất kỳ interaction nào với `HLRateLimitDO` trước khi gọi HL. Theo SRS FR-EXBOT-091, mọi HL API call phải khai báo weight trước và nhận `{allowed: boolean, retryAfterMs}`. Nếu `allowed=false`, caller phải re-queue với delay và không gửi lệnh. Hành vi này hoàn toàn vắng mặt trong UC. BA/Tech Lead vui lòng xác nhận: khi `HLRateLimitDO` trả `allowed=false` trong khi hedge-sync đang hold `UserLockDO` lease, worker có release lock trước khi re-queue không? | Thiếu test case quan trọng về rate limit behavior trong hedge-sync | BA / Tech Lead | Open |
| I-06 | Medium | MISSING_INFO | SRS FR-EXBOT-080, FR-EXBOT-082; UC §3 Main Flow | UC không đề cập bước giải mã HL agent key (AES-GCM decrypt) trước khi ký lệnh HL. Đây là bước bắt buộc theo FR-EXBOT-080. Không rõ: (a) decrypt xảy ra ở bước nào trong flow, (b) nếu key bị revoke trong khi hedge-sync đang chạy thì worker xử lý thế nào (FR-EXBOT-082 nói vào SAFE_MODE), (c) nếu `expires_at` đã qua thì worker xử lý thế nào. | Tester cần biết các failure path của agent key decryption để thiết kế test case bảo mật và SAFE_MODE | BA | Open |
| I-07 | Low | INTERNAL_INCONSISTENCY | UC §3 (§5 Postconditions) | UC có 2 mục `## Postconditions` — một ở §5 và một ngay sau §5 (dòng 62-66 trong file): mục thứ hai là placeholder template chưa được xóa ("System state reflects the completed operation", "NFR-ADM-005"). Nội dung này không liên quan đến ExBot (NFR-ADM-005 là NFR của module Admin, không phải ExBot). BA vui lòng dọn sạch phần placeholder này. | Gây nhầm lẫn khi đọc UC; Tester có thể nghĩ NFR-ADM-005 áp dụng cho ExBot | BA | Open |
| I-08 | Low | MISSING_INFO | UC §Trigger; SRS flows.md F-01 | UC §Trigger ghi: "User navigates to the relevant screen or initiates the described action." — đây là placeholder template chưa được cập nhật, không mô tả đúng trigger thực tế của UC này. Trigger thực tế là: light-check worker enqueue `hedge-sync` message khi phát hiện `RebalanceReason[]`. BA vui lòng cập nhật mô tả trigger cho đúng. | Khi đọc UC lần đầu, Tester có thể nhầm đây là UC có UI trigger | BA | Open |
| I-09 | Low | MISSING_INFO | UC §7 FR Trace; SRS FR-EXBOT-023 | UC §7 FR Trace liệt kê: `FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-036` — nhưng bỏ sót `FR-EXBOT-021` (LP position amount calculation — công thức tính `lpEthAmount` dùng Uniswap V3 AMM), `FR-EXBOT-023` (canonical RebalanceReason enum), `FR-EXBOT-030` (stop trigger price computation), `FR-EXBOT-035` (INV-STOP protocol), `FR-EXBOT-040` (circuit breaker), tất cả đều được mô tả trong Main Flow của UC. Trace không đầy đủ. | Trace không đầy đủ làm khó khăn cho QC khi cần tìm nguồn gốc rule | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| `OQ-EXBOT-02` — NV-3: HL có hỗ trợ place-before-cancel stop replacement không? | Integration | Quyết định INV-STOP protocol path (a) place-before-cancel vs (b) cancel-then-place với gap — ảnh hưởng test case cho INV-STOP | zen / SOTATEK | Open |
| `OQ-EXBOT-04` — NV-13: HL ETH-USD perp minimum order size / dust handling | Integration | Xác định ngưỡng delta tối thiểu để gửi lệnh — ảnh hưởng edge case test khi delta rất nhỏ | zen / SOTATEK | Open |
| `OQ-EXBOT-06` — Margin thresholds (0.55/0.75) | Configuration | Giá trị threshold cho `margin_status` computation — cần finalize trước khi test margin_warning/critical scenarios | zen | Open |
| `OQ-EXBOT-07` — stopSafetyFactor Phase B+ value | Configuration | Phase A = 0.70 confirmed; Phase B+ pending backtest | zen | Open |

---

## 10.3 Audit Summary

### Bảng điểm

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory (§F.1) | 20 | 15 | ⚠️ Partial | 28 items được liệt kê atomically, trace về SRS/FRD/ERD. Trừ điểm: UC bỏ sót `HLRateLimitDO` interaction (I-05), agent key decrypt step (I-06), marginSummary preflight (I-04). |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages (§F.2) | 25 | 18 | ⚠️ Partial | BR-EXBOT-004 resolved. States, validations, messages đầy đủ cho các operation chính. Trừ: margin_status update flow thiếu (I-04); delta=0 case thiếu (I-01). |
| 3 | Functional Logic & Workflow Decomposition (§F.3) | 25 | 19 | ⚠️ Partial | Happy path và 5 alternate flows rõ ràng. Trừ: A5 cite sai source (I-02) — UC bỏ sót primary detection path (light-check ≤5 min); delta=0 behavior thiếu; rate limit behavior thiếu. |
| 4 | Functional Integration & Data Consistency (§F.4) | 15 | 12 | ⚠️ Partial | Integration với light-check, deep-audit, partial_repair, bot_safe_close, UserLockDO rõ ràng. Trừ: không mô tả on-chain↔off-chain consistency cho agent key decrypt (I-06). |
| 5 | UC / Spec Documentation Quality Issues (§F.5 doc quality) | 15 | 9 | ⚠️ Partial | Placeholder trigger chưa update (I-08); double Postconditions với NFR-ADM-005 sai module (I-07); FR trace thiếu nhiều FR (I-09); A5 cite sai (I-02). |
| **Tổng** | | **100** | **73** | **⚠️ Conditionally Ready** | |

### Blockers

Không có blocker tuyệt đối — tất cả SRS/FRD/ERD đều accessible.

### Major Issues (cần fix trước khi thiết kế test đầy đủ)

1. **I-02 (High — CROSS_SOURCE_CONFLICT):** UC §A5 mô tả sai luồng `stop_replacing_started_at` stuck — bỏ sót primary detection path (light-check ≤5 min). Tester sẽ bỏ sót test SLA quan trọng.
2. **I-01 (High — MISSING_INFO):** Hành vi khi `delta = 0` chưa được định nghĩa.
3. **I-03 (High — UNCLEAR_INFO):** Định nghĩa "3 consecutive failures within 24h" không rõ ràng — mâu thuẫn giữa SRS (dùng từ "consecutive") và US-008 AC-1 (dùng rolling window phrasing).
4. **I-04 (Medium — MISSING_INFO):** Bước fetch `marginSummary` (FR-EXBOT-060) hoàn toàn thiếu trong UC flow.
5. **I-05 (Medium — MISSING_INFO):** `HLRateLimitDO` interaction hoàn toàn thiếu trong UC.

### Khuyến nghị

UC-EXBOT-hedge-sync đạt mức **Conditionally Ready** (73/100). Tester có thể bắt đầu thiết kế test cases cho happy path và các alternate flows A1–A4 dựa trên SRS/FRD làm bổ sung. Tuy nhiên, trước khi thiết kế test đầy đủ cho các scenario SAFE_MODE, margin management, và rate limiting, BA cần cập nhật UC để giải quyết các issue I-01, I-02, I-03, I-04, I-05. Đặc biệt I-02 (primary vs secondary SAFE_MODE detection) là ưu tiên cao nhất vì ảnh hưởng trực tiếp đến SLA test design.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-18 | QC UC Read Exbot Agent | Tạo báo cáo audited lần đầu — SRS-first cross-check |
