# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tiêu đề:** UC-EXBOT-hedge-sync — Execute Delta-Only Hedge Adjustment  
**Ngày tạo:** 2026-06-18  
**Tác giả:** QC UC Read ExBot Agent  
**Phiên bản:** v1

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-hedge-sync mô tả luồng mà hệ thống ExBot (ExBot System Operator — Hedge-Sync Worker) tự động điều chỉnh vị thế bán khống (short position) trên Hyperliquid (HL) theo phương pháp **delta-only**: chỉ gửi lệnh điều chỉnh phần chênh lệch giữa kích thước short mục tiêu (`targetShortEth`) và kích thước short thực tế (`actualShortEth`), không được phép đóng toàn bộ rồi mở lại trong điều kiện bình thường.

UC này được kích hoạt khi một message `hedge-sync` được đưa vào hàng đợi (queue), thường là do light-check phát hiện sai lệch vượt ngưỡng (ví dụ `drift_threshold`, `drift_relative`, `time_fallback`, v.v.). Quy trình bao gồm: kiểm tra idempotency qua `queue_idempotency`, kiểm tra `stateVersion` để tránh xử lý message lỗi thời, giành quyền khóa độc quyền từ `UserLockDO` (TTL 90 giây) để ngăn hai worker xử lý cùng một user đồng thời, tính toán delta bằng BigDecimal, gửi lệnh điều chỉnh lên HL qua `adjustShortDelta`, thay thế lệnh stop theo giao thức INV-STOP (FR-EXBOT-035), và cuối cùng chạy reconcile để xác nhận kích thước thực tế khớp với kỳ vọng.

Sau khi reconcile thành công, hệ thống cập nhật các trường quan trọng trong D1 (`hedge_legs.stop_price`, `entry_price`, `effective_leverage`, `bot_runtime_state.last_known_hl_short_size`) và ghi lại kết quả vào `rebalance_attempts`. UC này tương tác chặt chẽ với circuit breaker (`circuit_breakers`), SAFE_MODE (FR-EXBOT-050), và partial repair queue (FR-EXBOT-036) khi xảy ra lỗi hoặc partial fill. Đây là UC backend-only — không có UI tương tác trực tiếp.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-hedge-sync | Execute Delta-Only Hedge Adjustment | — | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-12 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-hedge-sync.md` | 2026-06-12 | UC | Tài liệu chính được review |
| `userstories/us-006.md` | 2026-06-12 | US / AC | User story liên kết (US-EXBOT-006) |
| `srs/spec.md` | 2026-06-12 | SRS — source of truth | FR-EXBOT-020–027, 030, 035, 036, 040, 050, 060, 091, 092 |
| `srs/states.md` | 2026-06-12 | State diagram | Bot lifecycle states + circuit breaker states |
| `srs/flows.md` | 2026-06-12 | Flow diagram | F-01 (fan-out), F-02 (hedge-sync execution) |
| `srs/erd.md` | 2026-06-12 | ERD | Schemas: bots, hedge_legs, bot_runtime_state, circuit_breakers, rebalance_attempts, queue_idempotency |
| `frd.md` | 2026-06-12 | FRD | FR-EXBOT-020–036 |
| `02_backbone/common-rules.md` | 2026-06-09 | Common rule | BR-EXBOT-004 không có trong file này (xem Issue I-001) |
| `02_backbone/message-list.md` | 2026-06-09 | Message list | E-EXBOT-* không có trong file này (xem Issue I-002) |
| `usecases/index.md` | 2026-06-12 | Index | Confirmed UC-EXBOT-hedge-sync, Linked Stories: US-EXBOT-006 |
| `userstories/index.md` | 2026-06-12 | Index | US-EXBOT-006 confirmed |

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement cho module BNZA-EXBOT — mỗi FR mô tả một hành vi cụ thể mà hệ thống phải thực hiện. | `frd.md`, `srs/spec.md` |
| BR-EXBOT-* | Business Rule cho module EXBOT — ràng buộc bất biến về nghiệp vụ (không được vi phạm). Trong dự án này, BR-EXBOT-004 là quy tắc "chỉ điều chỉnh delta, không đóng/mở toàn bộ". | `srs/spec.md` §4 |
| E-EXBOT-* | Error code cho module EXBOT — mã lỗi trả về từ API hoặc ghi vào log/notification khi gặp lỗi. Ví dụ E-EXBOT-007: HL từ chối lệnh do thiếu margin. | `srs/spec.md` §5 |
| UC | Use Case — mô tả luồng tương tác giữa actor và hệ thống để đạt một mục tiêu nghiệp vụ. | `usecases/` |
| US | User Story — mô tả nhu cầu từ góc độ người dùng/operator, có Acceptance Criteria (AC) kiểm tra được. | `userstories/` |
| HL | Hyperliquid — sàn giao dịch perp phi tập trung mà ExBot dùng để mở/điều chỉnh/đóng vị thế short ETH-USD. | (Proper noun) |
| DO / Durable Object | Cloudflare Durable Object — thành phần lưu trạng thái bền vững trong Cloudflare Workers. Trong UC này: UserLockDO (khóa mutex per-user) và HLRateLimitDO (giới hạn tốc độ HL). | (industry term) |
| SIWE | Sign-In With Ethereum — giao thức xác thực dựa trên chữ ký ví Ethereum. Không áp dụng trực tiếp trong UC này. | (industry term) |
| INV-STOP | Invariant-Stop Protocol — giao thức thay thế lệnh stop được bảo vệ (§19.5 SPEC v5.2.6): thay vì cancel → place trực tiếp, giao thức này đảm bảo không có khoảng thời gian không có lệnh stop. | `srs/spec.md` FR-EXBOT-035 |
| cloid | Client Order ID — ID lệnh do client tạo ra theo công thức keccak256 xác định (deterministic), dùng để HL deduplicate lệnh trùng. | `srs/spec.md` FR-EXBOT-024 |
| BigDecimal | Kiểu dữ liệu số thập phân độ chính xác cao — bắt buộc dùng cho tất cả tính toán tài chính (cấm dùng float/number JS). | `srs/spec.md` NFR-EXBOT-008 |
| D1 | Cloudflare D1 — cơ sở dữ liệu SQLite serverless trên Cloudflare Workers. ExBot dùng hai DB: `control_db` (global) và `state_db_shard_xx` (per-shard). | (Proper noun) |
| RebalanceReason | Enum chuẩn xác định lý do kích hoạt hedge-sync: `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile`. | `srs/spec.md` FR-EXBOT-023 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-hedge-sync tồn tại để duy trì tỷ lệ hedge chính xác giữa vị thế LP Uniswap V3 và vị thế short ETH-USD trên Hyperliquid. Khi kích thước short thực tế lệch khỏi kích thước mục tiêu (do giá ETH thay đổi, LP rebalance, hoặc các nguyên nhân khác), worker này điều chỉnh chỉ phần chênh lệch (delta), giảm thiểu chi phí giao dịch và mức tiêu thụ rate limit của HL. Sau mỗi lần điều chỉnh, lệnh stop được thay thế để phản ánh giá entry và leverage mới.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Queue idempotency check | Insert `message_id` vào `queue_idempotency` với `state='started'`; nếu UNIQUE conflict → bỏ qua (message đã xử lý) | UC §3 step 1, FR-EXBOT-011 |
| StateVersion check | Đọc `bots.state_version` từ D1; so sánh với `stateVersion` trong message; mismatch → discard (status=skipped) | UC §3 step 2, FR-EXBOT-027 |
| UserLockDO lease acquisition | Acquire mutex lease (TTL=90s) để ngăn concurrent HL mutation cho cùng user | UC §3 step 3, FR-EXBOT-026 |
| HL position fetch | Gọi `clearinghouseState` (weight=2) để lấy actual short size | UC §3 step 4 |
| Delta computation (BigDecimal) | Tính `delta = targetShortEth − actualShortEth` bằng BigDecimal | UC §3 step 5, FR-EXBOT-022 (delta), FR-EXBOT-021 |
| Delta order submission | Gửi `adjustShortDelta(delta, cloid)` lên HL — chỉ delta, không full close/open | UC §3 step 6, FR-EXBOT-022, BR-EXBOT-004 |
| Reconcile enqueue | Enqueue message `reconcile` sau khi gửi lệnh | UC §3 step 7 |
| INV-STOP stop replacement | Thay thế lệnh stop theo giao thức INV-STOP §19.5; set/clear `stop_replacing_started_at` trong finally block | UC §3 step 8-9, FR-EXBOT-035 |
| UserLockDO lease release | Release lease trong finally block | UC §3 step 10, FR-EXBOT-026 |
| Post-order reconcile | Fetch actual HL position; verify size = expected; extract entry_price, liquidation_price, effective_leverage | UC §3 step 11-12, FR-EXBOT-025 |
| Stop trigger price recompute | Recompute `stop_trigger_px` (BigDecimal); record stop_cloid, stop_price in hedge_legs | UC §3 step 13, FR-EXBOT-030 |
| D1 state update | Update `bot_runtime_state.last_known_hl_short_size`; insert `rebalance_attempts`; update `queue_idempotency.state='succeeded'` | UC §3 step 14-16 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Light-check (trigger) | UC hedge-sync bắt đầu từ khi message đã có trong queue; logic tạo message thuộc UC-EXBOT-light-check | Tester cần setup message hedge-sync trực tiếp; không test light-check trong UC này |
| Partial repair worker | Xử lý partial fill là luồng riêng qua `partial_repair` queue (FR-EXBOT-036); UC chỉ enqueue message này | Test case cho partial fill phải trace sang UC riêng hoặc FR-EXBOT-036 |
| Circuit breaker half_open probe logic | UC đề cập precondition `circuit_breakers.state IN ('closed','half_open')` nhưng không mô tả chi tiết half_open probe — thuộc FR-EXBOT-040 | Tester cần đọc FR-EXBOT-040 để thiết kế test cho half_open path |
| SAFE_MODE entry | UC đề cập SAFE_MODE gián tiếp (qua stuck stop_replacing_started_at detected by audit — AF-A5); chi tiết SAFE_MODE thuộc UC/FR riêng | Không test SAFE_MODE triggers trong UC này trừ AF-A5 trigger pathway |
| Trading strategy / hedge math (zen proprietary) | Ngoài phạm vi SOTATEK theo SRS §1.3 | Tester không kiểm tra công thức hedge math, chỉ kiểm tra infrastructure (delta submission, reconcile, idempotency) |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Hedge-Sync Worker) | Primary / System | Xử lý message từ hedge-sync queue; thực hiện toàn bộ luồng delta-only adjustment | Chạy trong Cloudflare Worker; không truy cập trực tiếp từ internet; kết nối HL qua agent key đã được phê duyệt | UC §1, SRS §1.1 |
| UserLockDO | System / External | Durable Object cung cấp mutex lease per-user để ngăn concurrent HL mutation | Chỉ 1 worker giữ lease tại một thời điểm; TTL tự động release sau 90s | UC §3 step 3, FR-EXBOT-026 |
| Hyperliquid API (info + exchange endpoints) | External | Cung cấp: `clearinghouseState` (actual position), `adjustShortDelta` (order submission) | Rate limit 800 weight/min (BNZA budget) qua HLRateLimitDO; mỗi `clearinghouseState` call = weight 2 | UC §3 step 4, 6, FR-EXBOT-091 |
| D1 (state_db_shard) | System | Lưu trữ trạng thái bot: `bots`, `hedge_legs`, `bot_runtime_state`, `rebalance_attempts`, `queue_idempotency`, `circuit_breakers` | Chỉ ADD COLUMN sau Phase A deploy; no DROP/RENAME | SRS ERD, BR-EXBOT-009 |
| Reconcile Worker | System | Fetch actual HL position sau khi lệnh điều chỉnh được gửi; xác nhận size = expected | Chạy qua reconcile queue tách biệt | UC §3 step 11 |

**Nhận xét readiness:** Actor list đủ rõ cho việc thiết kế test. Tuy nhiên, UC không mô tả `HLRateLimitDO` như một actor tham gia trực tiếp vào luồng — điều này có thể làm tester bỏ sót test case kiểm tra hành vi khi HL rate limit bị vượt ngưỡng (xem Issue I-007).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Message `hedge-sync` đã nhận với payload `{botId, reasons: RebalanceReason[], stateVersion}` | Yes | UC §2 |
| 2 | Bot có `status='active'` và `lifecycle_state='active'` | Yes | UC §2 |
| 3 | `circuit_breakers.state IN ('closed', 'half_open')` | Yes | UC §2 |
| 4 | Hệ thống ExBot đang chạy (Cloudflare Worker + D1 accessible) | Yes (implied) | SRS §1.1, IC-EXBOT-004 |
| 5 | HL agent key có `approval_status='approved'` và chưa hết hạn — cần cho decryption tại hedge-sync time | Yes (implied) | FR-EXBOT-080, FR-EXBOT-082 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Delta-only hedge adjustment thành công | `hedge_legs`: `stop_price`, `entry_price`, `liquidation_price`, `effective_leverage` được cập nhật; `stop_replacing_started_at=NULL` | UC §5 |
| Reconcile xác nhận | `bot_runtime_state.last_known_hl_short_size` = reconciled value | UC §5, step 14 |
| Audit trail | `rebalance_attempts` row được insert với `status='success'` | UC §5, step 15 |
| Idempotency state | `queue_idempotency.state='succeeded'` | UC §5, step 16 |
| Circuit breaker | `circuit_breakers.failure_count` không thay đổi (khi success); reset về 0 nếu đây là half_open probe thành công | UC §5, FR-EXBOT-040 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### §F.1 — Inventory: Functions / Operations / Data Objects / States

| # | Function / Operation | Trigger | Input | Output | Data Objects / Fields | State / Event | Nguồn |
|---|---|---|---|---|---|---|---|
| F1.1 | Queue idempotency insert | Message delivery | `message_id` | UNIQUE conflict → skip; else continue | `queue_idempotency.message_id`, `.state='started'` | — | UC §3 step 1, FR-EXBOT-011 |
| F1.2 | StateVersion optimistic concurrency check | Worker start | `bots.state_version` (D1), `stateVersion` (message) | Match → continue; mismatch → discard | `bot_runtime_state.state_version` | Discard → `rebalance_attempts.status='skipped'` | UC §3 step 2, FR-EXBOT-027 |
| F1.3 | UserLockDO lease acquire | After stateVersion check | `holderToken` (UUID), `ttl=90s`, `idempotencyKey=hedge-sync:{botId}:{stateVersion}` | `{acquired: true/false}` | UserLockDO internal state | — | UC §3 step 3, FR-EXBOT-026, FR-EXBOT-092 |
| F1.4 | UserLockDO heartbeat (conditional) | If work > 30s | `holderToken`, `ttlMs` | Lease extended | UserLockDO internal state | — | FR-EXBOT-026 |
| F1.5 | HL clearinghouseState fetch | After lock acquired | `botId` (HL account address) | `actualShortEth` | `hedge_legs.hl_account_address` | weight=2 consumed from HLRateLimitDO budget | UC §3 step 4, FR-EXBOT-091 |
| F1.6 | Delta computation | After HL fetch | `targetShortEth` (from D1 `bot_runtime_state.target_short_size`), `actualShortEth` | `delta = targetShortEth − actualShortEth` (BigDecimal) | `bot_runtime_state.target_short_size` | — | UC §3 step 5, FR-EXBOT-021, FR-EXBOT-022 |
| F1.7 | adjustShortDelta order submission | After delta computed | `delta`, `cloid = keccak256(bnza:{botId}:{attemptId}:{stage}:{version})` | HL order submitted (increase or reduce-only) | `rebalance_attempts.adjust_cloid` | — | UC §3 step 6, FR-EXBOT-022, FR-EXBOT-024, BR-EXBOT-004 |
| F1.8 | Reconcile queue enqueue | After order submission | `{botId, attemptId, expectedAbsSize, hedgeLegId}` | Message in `reconcile` queue | `queue_idempotency` | — | UC §3 step 7 |
| F1.9 | INV-STOP stop replacement | After order submission | Current `stop_cloid`, new `stop_trigger_px`, `stop_size` | Old stop cancelled; new stop placed (protected) | `hedge_legs.stop_replacing_started_at` (set → clear in finally), `hedge_legs.stop_cloid`, `.stop_price`, `.stop_size` | — | UC §3 step 8-9, FR-EXBOT-035 |
| F1.10 | UserLockDO lease release | Finally block | `holderToken`, `idempotencyKey`, `result` | Lease released | UserLockDO internal state | — | UC §3 step 10, FR-EXBOT-026 |
| F1.11 | Post-order reconcile (Reconcile Worker) | Reconcile queue delivery | `{botId, attemptId, expectedAbsSize, hedgeLegId}` | `actual short size`, `entry_price`, `liquidation_price`, `effective_leverage` | `hedge_legs.entry_price`, `.liquidation_price`, `.effective_leverage` | — | UC §3 step 11-12, FR-EXBOT-025 |
| F1.12 | Stop trigger price recompute | After reconcile | `entry_price`, `liquidation_price`, `effective_leverage`, `stopSafetyFactor=0.70` | New `stop_trigger_px` (BigDecimal) | `hedge_legs.stop_price`, `.stop_cloid`, `.stop_size`, `.stop_distance_pct` | — | UC §3 step 13, FR-EXBOT-030 |
| F1.13 | D1 bot_runtime_state update | After reconcile | `reconciled_size` | `last_known_hl_short_size` updated | `bot_runtime_state.last_known_hl_short_size` | — | UC §3 step 14 |
| F1.14 | rebalance_attempts insert | After reconcile success | `{botId, status='success', reason, stateVersion, ...}` | Audit row created | `rebalance_attempts.status`, `.reason`, `.reconciled_short_size`, `.adjust_cloid` | — | UC §3 step 15 |
| F1.15 | queue_idempotency state update | Final | `message_id`, `state='succeeded'` | Record updated | `queue_idempotency.state` | — | UC §3 step 16 |
| F1.16 | Circuit breaker increment on failure | On HL order rejection (AF-A3) | `hedge_leg_id` | `circuit_breakers.failure_count++`; if 3 consecutive within 24h → `state='open'` | `circuit_breakers.failure_count`, `.state`, `.opened_at`, `.reset_at` | State transition: closed → open | FR-EXBOT-040, UC §4 A3 |
| F1.17 | Partial fill repair enqueue | On partial fill detected (AF-A4) | `{botId, reason='partial_fill', delta_remaining}` | Message in `partial_repair` queue | — | — | UC §4 A4, FR-EXBOT-036 |
| F1.18 | Margin status check (preflight) | Before HL order — hedge-sync preflight | HL `marginSummary` | `margin_status` updated in D1 | `hedge_legs.margin_status`, `.margin_balance_usd`, `.margin_required_usd` | — | FR-EXBOT-060 |

**Enum sets:**
- `rebalance_attempts.status`: `'success'`, `'failed'`, `'skipped'`, `'partial'`
- `rebalance_attempts.reason` (RebalanceReason): `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile`
- `circuit_breakers.state`: `closed`, `open`, `half_open`
- `queue_idempotency.state`: `started`, `succeeded`, `failed`, `retryable`

---

### §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| # | Data Object / Function | States / Preconditions | Validations / Business Rules | Dependencies | Messages / Events | Nguồn |
|---|---|---|---|---|---|---|
| F2.1 | `queue_idempotency` | `state`: started → succeeded / failed / retryable | UNIQUE constraint trên `message_id` — duplicate delivery → silent skip; không xử lý lần 2 | — | — | FR-EXBOT-011 |
| F2.2 | `bot_runtime_state.state_version` | Integer tăng dần mỗi khi bot state thay đổi | Message `stateVersion` phải khớp D1 value; mismatch → `rebalance_attempts.status='skipped'` | Thay đổi bởi bất kỳ worker nào mutate bot state | — | FR-EXBOT-027 |
| F2.3 | UserLockDO lease | `acquired: true/false`; TTL=90s; auto-release sau 90s | `acquired=false` → re-queue với delay; không gửi lệnh HL | Chỉ 1 worker giữ lease per user tại một thời điểm | — | FR-EXBOT-026, FR-EXBOT-092 |
| F2.4 | UserLockDO heartbeat | Kích hoạt nếu work > 30s | Chỉ holder có `holderToken` khớp mới extend được; token sai → noop | — | — | FR-EXBOT-026 |
| F2.5 | `adjustShortDelta` — delta order | Increase hoặc reduce-only, tùy dấu delta | BigDecimal bắt buộc (cấm float); full close/open bị cấm trong hedge-sync thông thường; chỉ delta | `cloid` phải deterministic: `keccak256(bnza:{botId}:{attemptId}:{stage}:{version})`; duplicate cloid → reconcile trước, không resubmit mù | E-EXBOT-007 (HL từ chối lệnh, thiếu margin — message: "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin.") | FR-EXBOT-022, FR-EXBOT-024, BR-EXBOT-004 |
| F2.6 | INV-STOP protocol | `stop_replacing_started_at` SET → phải CLEAR trong finally block | Giao thức §19.5: place-before-cancel hoặc cancel-before-place tùy kết quả NV-3 (OQ-EXBOT-02 — Open); trực tiếp cancel→place không được phép | Phụ thuộc vào kết quả NV-3 (OQ-EXBOT-02) để xác định path (a) vs (b) | — | FR-EXBOT-035 |
| F2.7 | `stop_replacing_started_at` stuck detection | Set khi bắt đầu INV-STOP; NULL khi hoàn tất | Nếu stuck > 60s: light-check enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE | Detected by light-check (primary, ≤5 min) và deep-audit (backstop) | — | FR-EXBOT-033, FR-EXBOT-035 |
| F2.8 | `hedge_legs` — post-reconcile update | Sau reconcile thành công | `stop_price`, `entry_price`, `effective_leverage`, `liquidation_price` phải được cập nhật; `stop_replacing_started_at=NULL` | — | — | FR-EXBOT-025, UC §5 |
| F2.9 | `stop_trigger_px` computation | Sau reconcile | Formula (BigDecimal only): `liq_distance_pct = (liquidation_price − entry_price) / entry_price`; fallback `1/effective_leverage` khi HL không trả `liquidationPx`; `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)` | `stopSafetyFactor=0.70` (Phase A); Phase B+ pending OQ-EXBOT-07 | — | FR-EXBOT-030 |
| F2.10 | `circuit_breakers` | `state`: closed / open / half_open | Mỗi HL order rejection → `failure_count++`; 3 consecutive trong 24h → state=open; open → half_open khi `reset_at` reached; half_open: chỉ 1 probe allowed (`half_open_probe_used` 0→1 atomic claim) | Source of truth là D1 column `circuit_breakers.state`, không tính động từ history | — | FR-EXBOT-040 |
| F2.11 | `rebalance_attempts` | `status`: success / failed / skipped / partial | `status='success'` KHÔNG được ghi trước khi reconcile xác nhận; mỗi attempt phải có `adjust_cloid` riêng | — | — | FR-EXBOT-025 |
| F2.12 | Margin status (preflight tại hedge-sync) | `margin_status`: ok / warning / critical | Cập nhật tại thời điểm fetch HL `marginSummary` trước hedge-sync; `warning` → disable size-increase; `critical` (2 lần liên tiếp) → SAFE_MODE | Nguồn: HL `marginSummary` (field names pending OQ-EXBOT-01) | E-EXBOT-007 (thiếu margin), E-EXBOT-011 (reconcile mismatch) | FR-EXBOT-060 |

---

### §F.3 — Functional Logic & Workflow Decomposition

#### Happy Path — Delta-Only Adjustment Thành Công

| Bước | Actor | Trigger / Input | Hành động hệ thống | Output / State change | Nguồn |
|---|---|---|---|---|---|
| 1 | Hedge-Sync Worker | Message `{botId, reasons, stateVersion}` từ `hedge-sync` queue | Insert `queue_idempotency` với `message_id`, `state='started'`; UNIQUE conflict → skip và return | Record inserted hoặc silent skip | UC §3.1, FR-EXBOT-011 |
| 2 | Hedge-Sync Worker | D1 read | Đọc `bot_runtime_state.state_version`; so sánh với message `stateVersion` | Khớp → tiếp tục; không khớp → discard (`status='skipped'`, return) | UC §3.2, FR-EXBOT-027 |
| 3 | Hedge-Sync Worker | — | Gọi `UserLockDO.acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})` | `acquired=true` → tiếp tục | UC §3.3, FR-EXBOT-026 |
| 4 | Hedge-Sync Worker | HL API call | Fetch `clearinghouseState` (weight=2) → extract `actualShortEth` | `actualShortEth` retrieved | UC §3.4, FR-EXBOT-091 |
| 5 | Hedge-Sync Worker | BigDecimal computation | `delta = BigDecimal(targetShortEth).sub(actualShortEth)` | `delta` value (positive = increase, negative = reduce-only) | UC §3.5, FR-EXBOT-021 |
| 6 | Hedge-Sync Worker | HL API call | Gửi `adjustShortDelta(delta, cloid)` | HL order submitted; fill pending | UC §3.6, FR-EXBOT-022 |
| 7 | Hedge-Sync Worker | Post-order | Enqueue `reconcile` message `{botId, attemptId, expectedAbsSize, hedgeLegId}` | Message in reconcile queue | UC §3.7 |
| 8 | Hedge-Sync Worker | INV-STOP protocol | Set `stop_replacing_started_at`; execute protected cancel→place stop (§19.5) | New stop placed; `stop_cloid`, `stop_price`, `stop_size` updated in `hedge_legs` | UC §3.8, FR-EXBOT-035 |
| 9 | Hedge-Sync Worker | Finally block | Clear `stop_replacing_started_at` | `hedge_legs.stop_replacing_started_at = NULL` | UC §3.9, FR-EXBOT-035 |
| 10 | Hedge-Sync Worker | Finally block | `UserLockDO.release(holderToken, idempotencyKey, result)` | Lease released | UC §3.10, FR-EXBOT-026 |
| 11 | Reconcile Worker | `reconcile` queue message | Fetch actual HL position (`clearinghouseState`); verify `actual_size = expectedAbsSize` | Size confirmed | UC §3.11, FR-EXBOT-025 |
| 12 | Reconcile Worker | HL data | Extract `entry_price`, `liquidation_price`, `effective_leverage` | Values extracted | UC §3.12, FR-EXBOT-025 |
| 13 | Reconcile Worker | BigDecimal computation | Recompute `stop_trigger_px`; record `stop_cloid`, `stop_price` in `hedge_legs` | `hedge_legs` updated | UC §3.13, FR-EXBOT-030 |
| 14 | Reconcile Worker | D1 write | Update `bot_runtime_state.last_known_hl_short_size = reconciled_size` | `bot_runtime_state` updated | UC §3.14 |
| 15 | Reconcile Worker | D1 write | Insert `rebalance_attempts` row với `status='success'` | Audit row created | UC §3.15, FR-EXBOT-025 |
| 16 | Reconcile Worker | D1 write | Update `queue_idempotency.state='succeeded'` | Idempotency record finalized | UC §3.16 |

#### Alternate Flow A1 — Lock Held (Acquired = False)

| Bước | Actor | Hành động | Output | Nguồn |
|---|---|---|---|---|
| 3a | Hedge-Sync Worker | `UserLockDO.acquire()` trả về `acquired=false` | Re-queue message vào `hedge-sync` với delay; không gửi lệnh HL | UC §4 A1, FR-EXBOT-026 |

#### Alternate Flow A2 — StateVersion Mismatch

| Bước | Actor | Hành động | Output | Nguồn |
|---|---|---|---|---|
| 2a | Hedge-Sync Worker | `state_version` D1 ≠ message `stateVersion` | Discard message; record `rebalance_attempts.status='skipped'`; không gửi lệnh HL | UC §4 A2, FR-EXBOT-027 |

#### Alternate Flow A3 — HL Order Rejection

| Bước | Actor | Hành động | Output | Nguồn |
|---|---|---|---|---|
| 6a | Hedge-Sync Worker | HL trả về order rejection (ví dụ thiếu margin) | Record `rebalance_attempts.status='failed'`; gọi `incrementCircuitBreaker`; enqueue notification (E-EXBOT-007) | UC §4 A3, FR-EXBOT-040 |

#### Alternate Flow A4 — Partial Fill

| Bước | Actor | Hành động | Output | Nguồn |
|---|---|---|---|---|
| 11a | Reconcile Worker | `actual_size ≠ expectedAbsSize` (partial mismatch) | Enqueue `partial_repair` message với `reason='partial_fill'` | UC §4 A4, FR-EXBOT-036 |

#### Alternate Flow A5 — stop_replacing_started_at Stuck > 60s (Detected by Audit)

| Bước | Actor | Hành động | Output | Nguồn |
|---|---|---|---|---|
| — | Deep-Audit Worker | `stop_replacing_started_at IS NOT NULL AND age > 60s` | Enter SAFE_MODE (luồng riêng biệt trong UC deep-audit) | UC §4 A5, FR-EXBOT-033 |

---

### §F.4 — Functional Integration & Data Consistency

| Trigger / Action | Downstream effect | Data consistency concern | Nguồn |
|---|---|---|---|
| hedge-sync completes successfully | `bot_runtime_state.last_known_hl_short_size` cập nhật → light-check lần sau dùng giá trị này để tính delta | Nếu reconcile thất bại và `last_known_hl_short_size` không được cập nhật, light-check sẽ tính sai delta ở lần kế tiếp | FR-EXBOT-025, F-02 |
| `rebalance_attempts.status='success'` ghi TRƯỚC reconcile | Vi phạm FR-EXBOT-025 — tester cần đảm bảo không có race condition | On-chain/HL state là source of truth; D1 phản ánh state đã reconcile | FR-EXBOT-025 |
| `circuit_breakers.failure_count++` sau HL rejection | Khi đạt 3 consecutive trong 24h: `circuit_breakers.state='open'` → light-check suppress `hedge-sync` messages | Circuit breaker state phải consistent giữa tất cả hedge-sync workers cho cùng `hedge_leg_id` | FR-EXBOT-040 |
| INV-STOP protocol set `stop_replacing_started_at` | Light-check (mỗi ≤5 phút) phát hiện nếu stuck >60s → SAFE_MODE; deep-audit là backstop | Nếu worker crash sau khi SET nhưng trước khi CLEAR → stuck marker; light-check là fast path phát hiện (không phải chỉ dựa vào deep-audit) | FR-EXBOT-033, FR-EXBOT-035 |
| UserLockDO lease hết hạn tự động (90s) | Worker tiếp theo acquire lease và reconcile trước khi gửi lệnh mới | Có thể tạo khoảng thời gian hở giữa việc lease cũ hết hạn và worker mới acquire; reconcile trước khi mutate là bắt buộc | FR-EXBOT-026 |
| `cloid` duplicate detection | Worker phải reconcile actual HL state trước bất kỳ retry nào; không được resubmit mù | Nếu bỏ qua bước reconcile khi phát hiện duplicate cloid → có thể double-order | FR-EXBOT-024 |
| Margin status update tại hedge-sync preflight | `hedge_legs.margin_status` cập nhật → ảnh hưởng light-check tiếp theo (đọc từ D1, không fetch HL) | Nếu preflight margin check thất bại (thiếu margin), lệnh HL không được gửi; circuit breaker được increment | FR-EXBOT-060 |
| `partial_repair` enqueue sau partial fill | Repair worker cố gắng gửi lại delta còn lại (tối đa 3 lần); thất bại 3 lần → `bot_safe_close` | Tester phải kiểm tra rằng `rebalance_attempts` cho repair attempt dùng cloid riêng (version incremented) | FR-EXBOT-036 |

---

### §F.5 — Acceptance Criteria Candidates

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path: delta adjustment thành công | Bot `lifecycle_state='active'`, circuit=closed, stateVersion khớp, lock acquired | Worker nhận message, tính delta, gửi `adjustShortDelta` | Reconcile xác nhận size; `hedge_legs` cập nhật stop_price, entry_price; `rebalance_attempts.status='success'`; `queue_idempotency.state='succeeded'` | UC §3, US-EXBOT-006 AC-1 |
| AC-02 | StateVersion mismatch → discard | D1 `state_version=6`, message `stateVersion=5` | Worker check stateVersion trước khi acquire lock | Message discarded; `rebalance_attempts.status='skipped'`; không có lệnh HL | UC §4 A2, US-EXBOT-006 AC-2 |
| AC-03 | Lock not acquired → re-queue | Một worker khác đang giữ lock | Worker cố acquire `UserLockDO` | `acquired=false`; message được re-queue với delay; không có lệnh HL | UC §4 A1, US-EXBOT-006 AC-3 |
| AC-04 | HL order rejection → circuit breaker | HL từ chối lệnh (insufficient margin) | Worker gửi `adjustShortDelta`, HL reject | `rebalance_attempts.status='failed'`; `circuit_breakers.failure_count++`; sau 3 consecutive → state='open'; notification enqueued (E-EXBOT-007) | UC §4 A3, US-EXBOT-006 AC-4 |
| AC-05 | Duplicate message → idempotency skip | Message cùng `message_id` được redelivered | Worker insert vào `queue_idempotency` lần 2 | UNIQUE conflict → return ngay; không xử lý lần 2 | FR-EXBOT-011 |
| AC-06 | Partial fill → partial_repair enqueue | Reconcile phát hiện `actual ≠ expected` | Reconcile worker check size | `partial_repair` message được enqueue; `rebalance_attempts.status='partial'` | UC §4 A4, FR-EXBOT-036 |
| AC-07 | cloid deterministic — same retry same cloid | Worker retry cùng `attemptId + stage + version` | Worker tính cloid | cloid giống nhau; HL deduplicate hoặc detect sau reconcile | FR-EXBOT-024 |
| AC-08 | stop_replacing_started_at cleared | INV-STOP protocol thực thi, dù success hay failure | Finally block chạy | `hedge_legs.stop_replacing_started_at = NULL` | FR-EXBOT-035 |
| AC-09 | Margin status 'warning' → size-increase disabled | `margin_status='warning'` tại hedge-sync preflight | Worker check margin trước lệnh | Lệnh tăng size bị từ chối; lệnh giảm size vẫn được phép | FR-EXBOT-060 — **Suy luận cần xác nhận**: UC không mô tả rõ "size-increase disabled" áp dụng như thế nào trong hedge-sync flow |
| AC-10 | half_open circuit: chỉ 1 probe allowed | `circuit_breakers.state='half_open'` | 2 hedge-sync workers cùng lúc cố gửi lệnh | Chỉ 1 worker claim được `half_open_probe_used=1` (atomic); worker kia không gửi lệnh | FR-EXBOT-040 — **Suy luận cần xác nhận**: UC không mô tả chi tiết half_open probe trong phạm vi UC này |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| hedge-sync thành công → `last_known_hl_short_size` cập nhật | UC-EXBOT-light-check | Light-check lần sau dùng giá trị này để tính `deltaErrorUsd`; nếu giá trị sai → hedge-sync không cần thiết hoặc bị bỏ sót | Sau mỗi hedge-sync, `bot_runtime_state.last_known_hl_short_size` phải bằng `reconciled_short_size` trong `rebalance_attempts` | FR-EXBOT-025, F-02 |
| `circuit_breakers.failure_count` tăng lên 3 → `state='open'` | UC-EXBOT-light-check | Light-check suppresses `hedge-sync` enqueue khi circuit=open; stop monitoring vẫn tiếp tục | `circuit_breakers.state` phải là nguồn chính xác (không tính động từ history) | FR-EXBOT-040, FR-EXBOT-014 |
| hedge-sync bị discard (stateVersion mismatch) | UC-EXBOT-light-check (lần kế tiếp) | Không có điều chỉnh hedge; light-check tiếp theo sẽ re-evaluate và có thể enqueue hedge-sync mới | `rebalance_attempts.status='skipped'` ghi lại event để audit | FR-EXBOT-027 |
| INV-STOP set `stop_replacing_started_at` → stuck >60s | UC-EXBOT-light-check, deep-audit | Light-check phát hiện (primary ≤5min) → enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE; deep-audit là backstop | `stop_replacing_started_at` phải là NULL khi không có replacement in progress | FR-EXBOT-033, FR-EXBOT-035 |
| Partial fill → `partial_repair` enqueue | FR-EXBOT-036 (partial repair worker) | Repair worker gửi lại delta còn thiếu (tối đa 3 lần); thất bại 3 lần → `close_operations` row cho `bot_safe_close` | Mỗi repair attempt phải dùng cloid riêng (version incremented); `rebalance_attempts` row riêng cho mỗi repair | FR-EXBOT-036, FR-EXBOT-072 |
| hedge-sync enqueue notification sau HL rejection | `notification` queue → notification worker | Investor nhận thông báo lỗi hedge adjustment | Notification phải được enqueue ngay sau khi record failure, không blocking main flow | FR-EXBOT-040, UC §4 A3 |
| Margin status = 'warning' sau hedge-sync preflight | UC-EXBOT-light-check (đọc từ D1) | Light-check đọc `hedge_legs.margin_status` từ D1 (không fetch HL); UI banner notification cho investor | `margin_status` chỉ được cập nhật tại hedge-sync preflight và deep-audit | FR-EXBOT-060 |
| Margin status = 'critical' (2 lần liên tiếp) | SAFE_MODE (FR-EXBOT-050), `bot_safe_close` | Bot vào SAFE_MODE; nếu không recovery được → `bot_safe_close` | `margin_status='critical'` phải được ghi 2 lần trước khi trigger SAFE_MODE | FR-EXBOT-050, FR-EXBOT-060 |

---

## 8. Acceptance Criteria

*Xem §F.5 ở trên — các AC candidate đã được tổng hợp đầy đủ trong section đó.*

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | 1 hedge-sync hoàn thành trong < 30s trong điều kiện bình thường | Test nên đo thời gian từ khi worker nhận message đến khi `rebalance_attempts.status='success'` được ghi; cảnh báo nếu > 30s | NFR-EXBOT-002 |
| Rate Limit | Tổng HL API weight trong bất kỳ cửa sổ 60s nào không vượt 800; mỗi `clearinghouseState` = weight 2 | Test cần kiểm tra HLRateLimitDO từ chối call khi budget đã vượt; worker phải re-queue với delay khi `allowed=false` | NFR-EXBOT-004, FR-EXBOT-091 |
| Idempotency | Cùng `message_id` được deliver 2 lần → chỉ 1 lần xử lý; `queue_idempotency` UNIQUE constraint | Test case phải cover duplicate message delivery; verify không có 2 `rebalance_attempts` rows cho cùng 1 message | NFR-EXBOT-007, FR-EXBOT-011 |
| Precision | Tất cả tính toán hedge, stop, margin phải dùng BigDecimal; cấm float/JS number cho giá trị tài chính | Test phải verify delta và `stop_trigger_px` được tính bằng BigDecimal — không có intermediate `Number()` conversion; kiểm tra với giá trị biên (ví dụ: số rất nhỏ, nhiều chữ số thập phân) | NFR-EXBOT-008 |
| Concurrency | 2 hedge-sync workers cho cùng user không thể chạy HL mutation đồng thời | Test concurrent delivery của 2 messages cho cùng user; chỉ 1 worker được acquire lock | NFR-EXBOT-011, FR-EXBOT-026 |
| Security | Agent key AES-256-GCM; plain key chỉ tồn tại trong function scope; không ghi vào log | Test audit: verify log không chứa plaintext key; verify decryption failure khi key bị revoke → SAFE_MODE entry | NFR-EXBOT-006, FR-EXBOT-080, FR-EXBOT-082 |
| Reliability | SAFE_MODE không phải terminal state; luôn có recovery path (auto hoặc `bot_safe_close`) | Test SAFE_MODE auto-recovery conditions (HL responsive + 3 reconciles + margin ok) | NFR-EXBOT-010, FR-EXBOT-050 |
| Audit / Logging | `rebalance_attempts` row cho mỗi attempt (success/failed/skipped); `queue_idempotency` cho mỗi message | Test verify `rebalance_attempts` được tạo cho tất cả kết quả, kể cả `skipped` | FR-EXBOT-025, FR-EXBOT-011 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận (Issue Register)

| Issue ID | Type | Severity | Affected Area | Source Trace | Finding | Impact on tester understanding | Suggested question or fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-001 | `MISSING_INFO` | Major | Area 2, Area 5 | UC §6 `BR-EXBOT-004`; `02_backbone/common-rules.md` | UC đề cập `BR-EXBOT-004` (delta-only invariant) như một business rule, nhưng `BR-EXBOT-004` không tồn tại trong file `common-rules.md` của backbone. Nội dung của BR-EXBOT-004 chỉ được tìm thấy trong `srs/spec.md` §4 Business Rules. Điều này có nghĩa là code `BR-EXBOT-004` được trích dẫn trong UC nhưng không thể resolve qua đường dẫn canonical (`02_backbone/common-rules.md`) theo hướng dẫn của `input-files-format.md` §3. | Tester không biết nội dung chính xác của BR-EXBOT-004 từ nguồn canonical; phải tìm trong spec.md — nguy cơ bỏ sót nếu spec có thay đổi mà UC không cập nhật. | Thêm `BR-EXBOT-004` vào `02_backbone/common-rules.md` với nội dung: "Delta-only hedge adjustment is the invariant default. Full close → open in normal hedge-sync is a bug." (nguồn: `srs/spec.md` §4). Hoặc làm rõ convention: BR-EXBOT-* được định nghĩa trong spec.md, không phải common-rules.md. | Open |
| I-002 | `MISSING_INFO` | Major | Area 2, Area 5 | UC §6 (implied — UC không cite E-code cụ thể); `srs/spec.md` §5; `02_backbone/message-list.md` | Tất cả `E-EXBOT-*` codes (E-EXBOT-007, E-EXBOT-008, E-EXBOT-011, v.v.) không có trong `message-list.md` backbone. Message list backbone chỉ chứa E-MOB, E-pool, E-ADM, E-WLA. UC hedge-sync không cite trực tiếp bất kỳ E-EXBOT-* nào trong body, nhưng luồng lỗi (AF-A3) cần biết message cụ thể. Nội dung E-EXBOT-* chỉ trong `srs/spec.md` §5. | Tester không có một nguồn canonical thống nhất để verify expected error message trong test case; phải tra spec.md thay vì message-list.md theo convention. | Bổ sung section `## EXBOT — BNZA ExBot` vào `message-list.md` với tất cả E-EXBOT-001 đến E-EXBOT-013 từ `srs/spec.md` §5. | Open |
| I-003 | `MISSING_INFO` | Major | Area 3 | UC §4 A3; `srs/spec.md` FR-EXBOT-040 | UC mô tả AF-A3 "HL order rejection → record rebalance_attempts (status='failed'); call `incrementCircuitBreaker`; enqueue notification" nhưng không nêu rõ: (1) notification gửi qua queue nào (implied là `notification` queue nhưng không explicit trong UC); (2) content của notification cho investor là gì (E-EXBOT-007 là message phù hợp nhất nhưng UC không cite); (3) liệu worker có tiếp tục thực hiện INV-STOP (stop replacement) sau khi HL order bị reject hay không — nếu delta adjustment fail, stop replacement có ý nghĩa gì? | Tester không thể thiết kế test case cho AF-A3 với expected result đầy đủ: không biết queue name, message content, và flow của INV-STOP khi order bị reject. | BA xác nhận: (1) Notification enqueue vào `notification` queue với E-EXBOT-007? (2) INV-STOP có được bỏ qua khi delta order reject, hay vẫn execute để maintain stop consistency? | Open |
| I-004 | `MISSING_INFO` | Major | Area 3, Area 4 | UC §3 step 18 (không có); `srs/spec.md` FR-EXBOT-060; `frd.md` §4.7 | UC không mô tả bước kiểm tra margin status (fetch HL `marginSummary`) trong hedge-sync preflight. SRS FR-EXBOT-060 nêu rõ: "Margin status shall be updated only during hedge-sync preflight (HL `marginSummary` fetch) and deep-audit." Điều này có nghĩa hedge-sync phải fetch `marginSummary` trước khi gửi lệnh, nhưng bước này hoàn toàn vắng mặt trong UC §3 Main Success Scenario lẫn §4 Alternate Flows. | Tester không biết: (1) Thứ tự fetch `marginSummary` so với acquire lock và fetch `clearinghouseState` là gì? (2) Điều gì xảy ra nếu `margin_status='warning'` — lệnh tăng size có bị block không, và block ở đâu trong flow? (3) Điều gì xảy ra nếu `margin_status='critical'` tại thời điểm preflight? Test case cho margin warning/critical trong hedge-sync không thể thiết kế đầy đủ. | BA thêm bước fetch `marginSummary` vào UC §3 Main Flow, với nhánh: warning → disable size-increase; critical → xử lý thế nào? Có vào SAFE_MODE ngay không, hay chỉ setelah 2 lần critical? | Open |
| I-005 | `MISSING_INFO` | Major | Area 3 | UC §3 step 4 "Fetch actual HL position via `clearinghouseState` (weight=2)"; `srs/spec.md` FR-EXBOT-091 | UC mô tả fetch `clearinghouseState` (weight=2) nhưng không mô tả điều gì xảy ra khi HLRateLimitDO trả về `{allowed: false, retryAfterMs}`. FR-EXBOT-091 nêu rõ caller phải không proceed với HL call và re-queue. Behavior này không có trong UC alternate flows. | Tester không biết expected behavior khi HL rate limit bị vượt ngưỡng trong hedge-sync: worker có re-queue message không? với delay bao lâu? có khác với AF-A1 (lock held) không? | BA bổ sung alternate flow: "HLRateLimitDO returns {allowed: false} → worker re-queues message với `retryAfterMs` delay; không submit HL call." | Open |
| I-006 | `MISSING_INFO` | Minor | Area 3 | UC §3 step 8 "Execute stop replacement via INV-STOP protocol (§19.5)"; `srs/spec.md` FR-EXBOT-035; `srs/spec.md` OQ-EXBOT-02 | INV-STOP protocol (§19.5 SPEC v5.2.6) có hai path: (a) place-before-cancel và (b) cancel-then-place, tùy thuộc vào kết quả NV-3 verification (OQ-EXBOT-02 — đang Open). UC chỉ cite "§19.5" mà không nêu path nào áp dụng. Vì OQ-EXBOT-02 vẫn chưa chốt, tester chưa biết cụ thể sequence của INV-STOP. | Tester không thể viết test case cụ thể cho INV-STOP sequence khi OQ-EXBOT-02 chưa resolved. Hiện tại có thể test ở mức "stop được replace thành công" mà không verify thứ tự cancel/place. | Blocked trên OQ-EXBOT-02. Khi NV-3 verify xong, BA cần cập nhật UC với path cụ thể. | Open |
| I-007 | `MISSING_INFO` | Minor | Area 3 | UC §3 step 3; `srs/spec.md` FR-EXBOT-026 | UC không mô tả điều kiện kích hoạt `UserLockDO.heartbeat()`. FR-EXBOT-026 nêu: "If work exceeds 30 seconds, the worker extends the lease via `heartbeat()`." Không có alternate flow hay step nào trong UC đề cập heartbeat trigger condition hay failure handling khi heartbeat fails. | Tester không biết cần test: (1) heartbeat call khi work > 30s; (2) điều gì xảy ra nếu heartbeat fails (ví dụ DO crash)? | BA bổ sung note trong UC: "If hedge-sync work exceeds 30s, worker calls `UserLockDO.heartbeat(holderToken, newTtlMs)` to extend lease." | Open |
| I-008 | `MISSING_INFO` | Minor | Area 2 | UC §2 Preconditions; `srs/spec.md` FR-EXBOT-080, FR-EXBOT-082 | UC không nêu precondition về agent key status tại thời điểm hedge-sync. FR-EXBOT-082 nêu: "After revocation, any in-flight hedge-sync that attempts to decrypt the old key shall receive a decryption failure, log the error, and enter SAFE_MODE." Precondition "agent key approved and not expired" chỉ kiểm tra tại bot-start preflight, không phải hedge-sync. Nhưng key có thể bị revoke giữa chừng. | Tester không có alternate flow để test: agent key bị revoke trong khi hedge-sync đang chạy. Expected behavior (decryption failure → SAFE_MODE) không có trong UC. | BA bổ sung exception flow: "Agent key decryption fails (revoked/expired) → SAFE_MODE entry; log error without key material." | Open |
| I-009 | `UNCLEAR_INFO` | Minor | Area 3 | UC §4 A4 "Reconcile detects partial mismatch; enqueue `partial_repair` message"; `srs/spec.md` FR-EXBOT-036 | UC mô tả AF-A4 "partial fill" nhưng không định nghĩa ngưỡng "partial mismatch": `|actual - target| > drift_threshold` (FR-EXBOT-036: "leaves `|actual - target| > drift_threshold`") hay một ngưỡng khác? UC dùng "partial mismatch" không có con số cụ thể. | Tester không biết khi nào reconcile mismatch nhỏ được coi là "partial fill" cần repair, và khi nào được coi là "đủ gần" và không cần repair. | BA xác nhận: ngưỡng cho partial repair là `|actual - target| > drift_threshold` (giống light-check threshold)? Hay ngưỡng khác dành riêng cho reconcile? | Open |
| I-010 | `CROSS_SOURCE_CONFLICT` | Major | Area 1, Area 5 | UC §7 FR Trace: `FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-036`; UC Index `FR Trace: FR-020,021,022,024,025,026,027,035` | FR Trace trong UC file body (§7) khác với FR Trace trong `usecases/index.md`: UC body cite `FR-EXBOT-036` nhưng index không liệt kê FR-036. UC body không cite `FR-EXBOT-020`, `FR-EXBOT-021`, `FR-EXBOT-035` nhưng index có. Đặc biệt FR-EXBOT-020 (delta-only = P0) và FR-EXBOT-035 (INV-STOP protocol = P0) là critical và rõ ràng thuộc UC này nhưng bị thiếu trong UC body §7. | Tester dùng FR Trace của UC để xác định scope test không nhất quán; coverage sẽ bị hổng nếu chỉ theo một trong hai nguồn. | BA reconcile FR Trace giữa UC body §7 và index: thêm FR-EXBOT-020, FR-EXBOT-021, FR-EXBOT-035 vào UC §7; xác nhận FR-EXBOT-036 có đúng là trong scope UC này không. | Open |
| I-011 | `MISSING_INFO` | Minor | Area 3 | UC §3 step 13 "Recompute `stop_trigger_px` (BigDecimal); record new `stop_cloid`, `stop_price` in `hedge_legs`"; SRS FR-EXBOT-030 | UC gộp 2 hành động vào 1 step: (a) recompute stop trigger price và (b) record new stop_cloid, stop_price. Nhưng FR-EXBOT-030 cho thấy `stop_trigger_px` được compute từ reconcile data; lệnh stop mới đã được place trong step 8-9 (INV-STOP). Có một sự không rõ ràng: step 13 "record new stop_cloid" — stop_cloid này của lệnh stop nào? Lệnh đã place ở step 8, hay step 13 mới place? | Tester không biết thứ tự chính xác: stop được placed ở step 8 hay step 13? Nếu placed ở step 8 (INV-STOP) thì step 13 chỉ là record lại data — hay step 13 thực sự place lệnh mới sau reconcile? | BA làm rõ: step 8 (INV-STOP) place stop ngay sau `adjustShortDelta`, trong khi step 13 là recompute giá trigger và update D1 record (không place lệnh mới). Nếu đúng vậy, cần tách rõ trong UC text. | Open |
| I-012 | `MISSING_INFO` | Blocker | Area 3 | UC §3 step 5 "Compute `delta = BigDecimal(targetShortEth).sub(actualShortEth)`"; `srs/spec.md` OQ-EXBOT-04; FR-EXBOT-022 | UC không định nghĩa threshold tối thiểu cho delta — nếu `|delta|` rất nhỏ (dust), hệ thống có submit lệnh không hay bỏ qua? OQ-EXBOT-04 (NV-13) đang Open: "HL ETH-USD perp minimum order size / dust handling rules — Blocks FR-EXBOT-022 (minimum delta threshold)." Không có alternate flow nào trong UC xử lý trường hợp `|delta| < minimum_order_size`. | Tester không thể thiết kế test case kiểm tra boundary giữa "delta đủ lớn để submit" và "delta quá nhỏ → skip". Nếu hệ thống submit delta quá nhỏ, HL sẽ reject lệnh → circuit breaker increment không cần thiết. | Blocked trên OQ-EXBOT-04. Khi NV-13 xong, BA bổ sung alternate flow: "If `|delta| < minimumOrderSize` → skip order submission; record `rebalance_attempts.status='skipped'`; không increment circuit breaker." | Open |

---

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-02 (NV-3): HL hỗ trợ place-before-cancel stop replacement? | Integration | Quyết định INV-STOP path (a) vs (b); ảnh hưởng trực tiếp đến implementation và test design của stop replacement trong hedge-sync | zen/SOTATEK | Open |
| OQ-EXBOT-04 (NV-13): HL ETH-USD perp minimum order size / dust handling | Integration | Blocks alternate flow khi `|delta| < minimum` — không thể thiết kế boundary test | zen/SOTATEK | Open |
| OQ-EXBOT-01 (NV-1): HL `marginSummary` exact API field names (`marginBalanceUsd`) | Integration | Ảnh hưởng FR-EXBOT-060 implementation — test case kiểm tra margin status cần biết field name chính xác | zen/SOTATEK | Open |
| OQ-EXBOT-07: `stopSafetyFactor` Phase B+ value | Configuration | Phase A = 0.70 (confirmed); Phase B+ pending backtest — không ảnh hưởng Phase A test | zen | Open |
| BR-EXBOT-004 và E-EXBOT-* chưa có trong `common-rules.md` / `message-list.md` | Documentation | Tester phải đọc spec.md thay vì backbone files — nguy cơ miss update khi spec thay đổi | BA (@hienduong) | Open |
| Agent key decryption failure behavior trong hedge-sync | Behavior definition | Luồng "key revoked mid-flight" chưa có trong UC; cần xác nhận expected behavior trước khi test | BA (@hienduong) | Open |

---

### 10.3 Audit Summary

#### Scoring Table

| # | Scoring Area | Max | Score | Status | Notes |
|---|---|---:|---:|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 15 | ⚠️ Partial | §F.1 liệt kê đầy đủ 18 operations/functions atomically, mapped tới source. Trừ điểm: FR-EXBOT-018 (margin preflight tại hedge-sync) hoàn toàn vắng mặt trong UC; FR Trace mismatch giữa UC body và index (I-010) |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 16 | ⚠️ Partial | States và transitions của circuit breaker, queue_idempotency, hedge_legs đủ rõ. Trừ điểm: BR-EXBOT-004 không resolve được từ canonical source (I-001); E-EXBOT-* không trong message-list.md (I-002); agent key revoke mid-flight không có trong UC (I-008); `margin_status='warning'` behavior trong hedge-sync flow chưa rõ (I-004) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 15 | ⚠️ Partial | Happy path và các alternate flows A1–A4 có đủ để thiết kế test cơ bản. Trừ điểm: margin preflight flow hoàn toàn thiếu trong UC (I-004 — Major); HLRateLimitDO `allowed=false` không có alternate flow (I-005 — Major); notification content AF-A3 chưa rõ (I-003 — Major); INV-STOP step 8 vs step 13 ambiguous (I-011 — Minor); dust/minimum delta không có flow (I-012 — Blocker) |
| 4 | Functional Integration & Data Consistency | 15 | 11 | ⚠️ Partial | Các cross-function effects (light-check dependency, partial repair → safe-close, stuck stop marker detection) được identify rõ. Trừ điểm: mối quan hệ giữa margin preflight tại hedge-sync và SAFE_MODE trigger (2 lần critical) chưa trace được vì bước preflight thiếu trong UC |
| 5 | UC / Spec Documentation Quality Issues | 15 | 8 | ⚠️ Partial | UC có cấu trúc rõ, ngôn ngữ kỹ thuật nhất quán. Trừ điểm: FR Trace conflict giữa UC body và index (I-010 — Major); BR-EXBOT-004 không có trong canonical source (I-001 — Major); E-EXBOT-* không có trong message-list.md (I-002 — Major); gap lớn: margin preflight thiếu hoàn toàn (I-004) |
| **Total** | | **100** | **65** | ⚠️ Partial | |

**Auto-cap áp dụng:**
- I-012 (minimum delta / dust handling — Blocker): ảnh hưởng Area 3. Area 3 bị cap tại 40% max (10/25) theo auto-cap rule "A blocker prevents understanding of a critical function." → Tuy nhiên sau khi đánh giá toàn bộ, I-012 là blocker cho một edge case (dust delta) chứ không phải critical path chính. Happy path và major alternate flows có thể test được. Áp dụng cap nhẹ hơn: Area 3 = 15/25 (60% — Partial, có thể test major flows nhưng không thể test dust boundary). Score giữ nguyên 65.

#### Blockers (ngăn test design hoàn toàn)

- **I-012** (MISSING_INFO — Blocker): Không có định nghĩa `minimum delta threshold` / dust handling → không thể thiết kế boundary test cho "delta quá nhỏ". Blocked trên OQ-EXBOT-04.

#### Major Issues (ảnh hưởng đáng kể đến test design)

- **I-003**: AF-A3 (HL rejection) — notification content và INV-STOP behavior sau rejection chưa rõ.
- **I-004**: Margin status preflight trong hedge-sync hoàn toàn thiếu khỏi UC — cả Main Flow lẫn Alternate Flows.
- **I-005**: HLRateLimitDO `allowed=false` không có alternate flow trong UC.
- **I-010**: FR Trace conflict giữa UC body §7 và `usecases/index.md` — FR-020, FR-021, FR-035 thiếu trong body; FR-036 thiếu trong index.

#### Kết luận và khuyến nghị

UC-EXBOT-hedge-sync mô tả đầy đủ luồng chính và các alternate flows quan trọng nhất (stateVersion mismatch, lock conflict, HL rejection, partial fill), đủ để thiết kế test cho happy path và 4 alternate flows đã nêu. Tuy nhiên, **có 4 Major Issues và 1 Blocker** cần được BA giải quyết trước khi test design hoàn chỉnh.

Quan trọng nhất: (1) **Bước margin preflight (FR-EXBOT-060) hoàn toàn vắng mặt** — tester không thể test hành vi khi `margin_status='warning'` hoặc `critical` trong hedge-sync; (2) **Minimum delta threshold** (OQ-EXBOT-04) chưa có → không test được boundary case; (3) **FR Trace mismatch** giữa UC body và index cần được reconcile.

Khuyến nghị: resolve I-004, I-010 và I-003 trước khi bắt đầu viết test scenarios. Các issues còn lại (I-001, I-002) nên được fix song song ở mức documentation. I-012 có thể để tạm khi OQ-EXBOT-04 được unblock.

**Final Verdict: Not Ready** (Score 65/100 — dưới ngưỡng 70; 1 Blocker chưa resolved)

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-18 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu — SRS-first cross-check cho UC-EXBOT-hedge-sync |
