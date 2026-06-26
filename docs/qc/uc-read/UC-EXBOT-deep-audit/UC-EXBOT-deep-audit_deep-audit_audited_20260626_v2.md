# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tiêu đề tài liệu:** UC-EXBOT-deep-audit — Báo cáo rà soát độ sẵn sàng test
**Ngày tạo:** 2026-06-26
**Tác giả / Agent:** qc-uc-read-exbot
**Phiên bản:** v2

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-deep-audit mô tả luồng worker định kỳ (cron-driven) chạy kiểm tra toàn diện trạng thái bot trên Hyperliquid (HL) và D1, với vai trò là **backstop bảo vệ cuối cùng** — phát hiện các tình huống nguy hiểm mà light-check (vòng 5 phút, HL-weight=0) không thể nhìn thấy. Deep-audit gọi HL API (weight=2 cho `clearinghouseState`) và có thể kích hoạt SAFE_MODE thông qua ba detection path độc lập: (1) reconcile mismatch — kích thước short thực tế trên HL khác `last_known_hl_short_size` trong D1; (2) `stop_trigger_crossed_at` stuck > 30 phút; (3) `stop_replacing_started_at` stuck > 60 giây (secondary backstop, primary là light-check ≤5 phút per FR-EXBOT-033). Ngoài ba detection path chính, deep-audit còn cập nhật `margin_status` từ `marginSummary` HL tươi và kiểm tra sắp hết hạn agent key (≤7 ngày).

Cadence mặc định là 6 giờ/lần cho tất cả bot `status IN ('active', 'paused')`. Cadence chuyển sang **high-risk (1 giờ/lần)** khi `circuit_breakers.state != 'closed'` hoặc `margin_status IN ('warning', 'critical')`. Điều quan trọng: bot `status='paused'` **không được loại trừ** khỏi deep-audit — đây là quy tắc tường minh. Deep-audit được cho phép chạy ngay cả khi bot đang ở SAFE_MODE (khi HL đã phục hồi).

Phạm vi test: không có UI. Kiểm thử hoàn toàn qua Back-End (Cloudflare Worker, D1, Hyperliquid API, notification queue). Ba user stories liên kết: US-EXBOT-005 (light-check + HL-weight=0, liên quan vì FR-EXBOT-033 phân định primary/secondary path), US-EXBOT-008 (circuit breaker state machine), US-EXBOT-010 (margin warning/critical → SAFE_MODE).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-deep-audit | Periodic Deep Audit and Backstop SAFE_MODE Detection | Draft 2026-06-18 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-06-18 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-deep-audit.md` | Draft 2026-06-18 | UC chính | Nguồn input chính |
| `userstories/us-005.md` | Draft 2026-06-12 | US liên kết | Light-check no-HL |
| `userstories/us-008.md` | Draft 2026-06-12 | US liên kết | Circuit breaker state machine |
| `userstories/us-010.md` | Draft 2026-06-12 | US liên kết | Margin warning/critical → SAFE_MODE |
| `srs/spec.md` | SPEC v5.2.6, changelog 2026-06-20 | SRS — source of truth | FR-016, FR-033, FR-050, FR-060, FR-083, FR-091 |
| `srs/states.md` | Updated 2026-06-18 | State diagram | lifecycle, circuit breaker, margin states |
| `srs/flows.md` | Updated 2026-06-20 | Flow diagram | F-01 queue topology |
| `srs/erd.md` | Draft | ERD (D1 schema) | hedge_legs, bot_runtime_state, hl_agent_keys, bots |
| `frd.md` | Updated 2026-06-24 | FRD | FR-EXBOT-016, FR-EXBOT-033, FR-EXBOT-083 |
| `common-rules.md` | Draft | BR-EXBOT-001…010 | BR-EXBOT-005, BR-EXBOT-007 áp dụng |
| `message-list.md` | Updated 2026-06-09 | Error/Info messages | E-EXBOT-008, E-EXBOT-011 áp dụng |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-deep-audit tồn tại để cung cấp một lớp bảo vệ định kỳ toàn diện mà light-check không thể cung cấp — bằng cách gọi HL API thực sự và cross-check dữ liệu off-chain (D1) với on-chain (HL). Kết quả nghiệp vụ mong đợi: phát hiện sớm các tình huống nguy hiểm (reconcile mismatch, stuck stop markers, margin deterioration) và kích hoạt SAFE_MODE trước khi thiệt hại xảy ra, đồng thời gửi cảnh báo đến nhà đầu tư và admin.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Cron trigger | Deep-audit cron fires theo cadence 6h (normal) hoặc 1h (high-risk) | UC §2; SRS FR-EXBOT-016 |
| HL clearinghouseState fetch | Gọi HL API weight=2 qua HLRateLimitDO | UC §3 bước 2; SRS FR-EXBOT-091 |
| Reconcile mismatch detection (A3) | Actual short size ≠ `hedge_legs.last_known_hl_short_size` → SAFE_MODE + admin alert | UC §3 bước 3; UC §A3 |
| stuck `stop_trigger_crossed_at` detection (A4) | Stuck > 30 phút → SAFE_MODE + admin escalation | UC §3 bước 4; SRS FR-EXBOT-033; BR-EXBOT-005 |
| stuck `stop_replacing_started_at` detection (A4) | Stuck > 60 giây → SAFE_MODE (secondary backstop per FR-EXBOT-033) | UC §3 bước 5; SRS FR-EXBOT-033 |
| HL marginSummary fetch + update | Gọi HL API `marginSummary`; update `hedge_legs.margin_status` | UC §3 bước 6; SRS FR-EXBOT-060 |
| Agent key expiry check (step 7) | `expires_at - now <= 7 days` → notification queue | UC §3 bước 7; SRS FR-EXBOT-083 |
| Audit timestamp update | `bot_runtime_state.last_deep_audit_at` | UC §3 bước 8; erd.md |
| Queue idempotency | `queue_idempotency` row insert/update | UC §3 bước 9 |
| High-risk cadence switch | 6h → 1h khi circuit_breakers.state != 'closed' hoặc margin_status IN ('warning','critical') | UC §2; SRS FR-EXBOT-016 |
| HL unreachable handling (A1) | Skip HL-dependent steps; switch to high-risk; notify | UC §A1 |
| Paused bot audit (A2) | Bot paused vẫn được audit đầy đủ ở cadence 6h | UC §A2; SRS FR-EXBOT-016 |
| effective_leverage check | `effective_leverage > 4.5` → SAFE_MODE (per FR-050, US-010 AC-4) | FR-EXBOT-050; US-010 AC-4 |
| liquidation_price check | `liquidation_price within 5% of hlMarkPrice` → SAFE_MODE (per FR-050) | FR-EXBOT-050 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| SAFE_MODE auto-recovery | UC này chỉ trigger SAFE_MODE; recovery là UC riêng | Không ảnh hưởng |
| margin_status computation formula | Thuộc FR-EXBOT-060; deep-audit chỉ gọi `marginSummary` và update D1 | Tester không cần verify formula trong UC này |
| bot_safe_close trigger từ margin critical | Thuộc FR-EXBOT-072; deep-audit không trực tiếp khởi động bot_safe_close | Cần biết là SAFE_MODE có thể dẫn đến bot_safe_close downstream |
| UI / màn hình | ExBot là backend-only | Không áp dụng |
| uc-agent-key.md | Luồng submit/approve key là UC riêng | Chỉ cần test expiry check notification |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Deep-Audit Worker) | Primary | Cron kích hoạt; đọc D1, gọi HL, cập nhật D1, enqueue notification | Được phép gọi HL API (weight≠0, khác light-check); gated bởi HLRateLimitDO | UC §1; SRS FR-EXBOT-016; BR-EXBOT-003 note |
| D1 (control_db + state_db_shard) | System | Nguồn dữ liệu bot state; target write kết quả audit | — | erd.md |
| Hyperliquid (HL) | External | Nguồn dữ liệu `clearinghouseState` và `marginSummary` | Rate-limited; weight=2 per clearinghouseState call; HLRateLimitDO gating | SRS FR-EXBOT-091 |
| Notification Queue | System | Nhận agent key expiry notification, admin escalation, HL unreachable alert | `chunkSendBatch()` helper bắt buộc | UC §1; SRS FR-EXBOT-016 |
| Admin | Secondary | Nhận escalation notification khi SAFE_MODE triggered (A3, A4) | Read-only trong UC này | UC §A3, §A4 |
| USDC Investor | Secondary | Nhận notification khi agent key sắp hết hạn hoặc margin warning | Read-only trong UC này | UC §3 bước 7; SRS FR-EXBOT-083 |

**Nhận xét readiness:** Actor đủ rõ. Notification recipients cho A3/A4: admin notification (không phải investor) per UC §A3, §A4. Margin warning notification đi đến investor per US-010 AC-010-1.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Cron job kích hoạt theo cadence (`bots.next_deep_audit_at <= now`) | Yes | UC §2; erd.md `bots.next_deep_audit_at` |
| 2 | Bot `status IN ('active', 'paused')` — không phải `closed`, `error` | Yes | UC §2; SRS FR-EXBOT-016 |
| 3 | Cadence: 6h normal, hoặc 1h khi `circuit_breakers.state != 'closed'` OR `margin_status IN ('warning','critical')` | Yes | UC §2; SRS FR-EXBOT-016 |
| 4 | Bot trong SAFE_MODE vẫn có thể được audit khi HL phục hồi | Note | SRS FR-EXBOT-050 "deep-audit when HL recovers" |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Happy path (no issues) | `hedge_legs.margin_status` updated; `bot_runtime_state.last_deep_audit_at` set; `queue_idempotency.state='succeeded'` | UC §5; erd.md |
| Reconcile mismatch (A3) | SAFE_MODE triggered; mismatch ghi vào D1; admin notified | UC §A3; SRS FR-EXBOT-050 |
| Stuck stop marker (A4) | SAFE_MODE triggered; admin escalation với timestamp + reason | UC §A4 |
| HL unreachable (A1) | HL-dependent steps skipped; `next_deep_audit_at` shortened to 1h; notification enqueued | UC §A1 |
| Agent key expiring (step 7) | Notification enqueued: "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." | UC §3 bước 7; SRS FR-EXBOT-083 |
| Margin status updated | `hedge_legs.margin_status` ∈ {'ok','warning','critical'} per fresh marginSummary | UC §3 bước 6; SRS FR-EXBOT-060 |
| effective_leverage > 4.5 | SAFE_MODE triggered; admin alerted per US-010 AC-010-4 | FR-EXBOT-050; US-010 AC-010-4 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng chính: Deep-Audit cron execution

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Cron Scheduler | `next_deep_audit_at <= now` → fire worker | Worker khởi động cho tất cả bot trong scope | — | — | UC §2; erd.md |
| 2 | Deep-Audit Worker | Insert `message_id` vào `queue_idempotency` (state='started') | Row tạo → tiếp tục | — | UNIQUE conflict → skip (already processed) | SRS FR-EXBOT-016 (idempotency pattern) |
| 3 | Deep-Audit Worker | Gọi HLRateLimitDO: khai báo weight=2 (clearinghouseState) | `{allowed: true}` → tiếp tục | `{allowed: false}` → A1 | HL 5xx → A1 | UC §3 bước 2; SRS FR-EXBOT-091 |
| 4 | Deep-Audit Worker | Fetch `clearinghouseState` từ HL | Actual short size, effective_leverage, liquidation_price trả về | — | HL timeout/5xx → A1 | UC §3 bước 2 |
| 5 | Deep-Audit Worker | So sánh actual short size với `hedge_legs.last_known_hl_short_size` | Match → tiếp tục | — | Mismatch → A3 | UC §3 bước 3 |
| 6 | Deep-Audit Worker | Check `effective_leverage > 4.5` từ clearinghouseState | False → tiếp tục | True → SAFE_MODE + admin alert (per US-010 AC-4) | — | FR-EXBOT-050; US-010 AC-4 |
| 7 | Deep-Audit Worker | Check `liquidation_price within 5% of hlMarkPrice` | False → tiếp tục | True → SAFE_MODE (per FR-050) | — | FR-EXBOT-050 |
| 8 | Deep-Audit Worker | Check `stop_trigger_crossed_at IS NOT NULL AND (now - stop_trigger_crossed_at) > 30 min` | False → tiếp tục | True → A4 | — | UC §3 bước 4; SRS FR-EXBOT-033; BR-EXBOT-005 |
| 9 | Deep-Audit Worker | Check `stop_replacing_started_at IS NOT NULL AND (now - stop_replacing_started_at) > 60s` | False → tiếp tục | True → A4 (secondary backstop) | — | UC §3 bước 5; SRS FR-EXBOT-033 |
| 10 | Deep-Audit Worker | Gọi HLRateLimitDO: khai báo weight cho `marginSummary` | `{allowed: true}` → tiếp tục | `{allowed: false}` → A1 | — | SRS FR-EXBOT-091 |
| 11 | Deep-Audit Worker | Fetch `marginSummary` từ HL | margin data trả về | — | HL timeout/5xx → A1 | UC §3 bước 6 |
| 12 | Deep-Audit Worker | Update `hedge_legs.margin_status` từ fresh HL data | `margin_status` ∈ {'ok','warning','critical'} | — | — | UC §3 bước 6; SRS FR-EXBOT-060 |
| 13 | Deep-Audit Worker | Nếu margin chuyển từ ok → warning: enqueue margin warning notification | notification enqueued cho investor | — | — | US-010 AC-010-1 |
| 14 | Deep-Audit Worker | Check `hl_agent_keys.expires_at - now <= 7 days` (chỉ `approval_status='approved'`) | False → skip | True → enqueue notification "Your HL agent key expires in {N} days..." | — | UC §3 bước 7; SRS FR-EXBOT-083 |
| 15 | Deep-Audit Worker | Update `bot_runtime_state.last_deep_audit_at = now` | Timestamp set | — | — | UC §3 bước 8; erd.md |
| 16 | Deep-Audit Worker | Update `queue_idempotency.state='succeeded'` | Audit complete | — | — | UC §3 bước 9 |

#### B. Alternate flows

| ID | Trigger | Hành động hệ thống | Trạng thái cuối | Nguồn |
|---|---|---|---|---|
| A1 | HLRateLimitDO `allowed=false` hoặc HL 5xx | Skip HL-dependent steps (bước 4-13); update `next_deep_audit_at` sang 1h interval; enqueue "Hyperliquid API unreachable" | Audit partial; cadence = high-risk (1h) | UC §A1 |
| A2 | Bot `status='paused'` | Full audit vẫn chạy đầy đủ ở cadence 6h; không skip bất kỳ detection path nào | Same as happy path | UC §A2; SRS FR-EXBOT-016 |
| A3 | Actual short size ≠ `last_known_hl_short_size` | Record mismatch trong D1; trigger SAFE_MODE entry; enqueue admin notification với size delta | `bots.status='safe_mode'` | UC §A3; SRS FR-EXBOT-050; E-EXBOT-011 |
| A4 | `stop_trigger_crossed_at` stuck > 30 min HOẶC `stop_replacing_started_at` stuck > 60s | Trigger SAFE_MODE entry; enqueue admin escalation với timestamp + reason | `bots.status='safe_mode'` | UC §A4; SRS FR-EXBOT-033 |

---

## §F.1 — Inventory

| # | Function / Operation | Trigger | Input | Output | Data Object / Field | Kiểu | Source |
|---|---|---|---|---|---|---|---|
| F1.1 | Cron scheduling | `bots.next_deep_audit_at <= now` | — | Worker instance fired | `bots.next_deep_audit_at` | TEXT (timestamp) | erd.md; SRS FR-EXBOT-016 |
| F1.2 | D1 bot state read | Worker start | bot_id | `status`, `lifecycle_state`, `hedge_legs.*`, `circuit_breakers.state`, `margin_status` | `bots`, `hedge_legs`, `circuit_breakers` | — | UC §3 bước 1; erd.md |
| F1.3 | `queue_idempotency` insert | Worker start | `message_id` | UNIQUE conflict → skip; hoặc tiếp tục | `queue_idempotency.message_id`, `.state` | TEXT / ENUM | SRS FR-EXBOT-016 |
| F1.4 | HLRateLimitDO gating | Trước mỗi HL call | weight | `{allowed: boolean, retryAfterMs}` | — | — | SRS FR-EXBOT-091 |
| F1.5 | HL `clearinghouseState` fetch | Sau HLRateLimitDO allow | — | Actual short size, effective_leverage, liquidation_price | `hedge_legs.last_known_hl_short_size` | TEXT (DECIMAL) | UC §3 bước 2; SRS FR-EXBOT-016 |
| F1.6 | Reconcile mismatch check | Sau F1.5 | actual_size, `last_known_hl_short_size` | Match (continue) hoặc mismatch (A3) | `hedge_legs.last_known_hl_short_size` | TEXT (DECIMAL) | UC §3 bước 3 |
| F1.7 | effective_leverage check | Sau F1.6 | effective_leverage | ≤4.5 (continue) hoặc >4.5 (SAFE_MODE) | `hedge_legs.effective_leverage` | TEXT (DECIMAL) | FR-EXBOT-050; US-010 AC-4 |
| F1.8 | liquidation_price check | Sau F1.7 | liquidation_price, hlMarkPrice | within 5% (SAFE_MODE) hoặc not (continue) | `hedge_legs.liquidation_price` | TEXT (DECIMAL) | FR-EXBOT-050 |
| F1.9 | `stop_trigger_crossed_at` stuck check | Sau F1.8 | `hedge_legs.stop_trigger_crossed_at`, now | True (A4) hoặc False (continue) | `hedge_legs.stop_trigger_crossed_at` | TEXT (timestamp NULL) | UC §3 bước 4; FR-EXBOT-033; BR-EXBOT-005 |
| F1.10 | `stop_replacing_started_at` stuck check | Sau F1.9 | `hedge_legs.stop_replacing_started_at`, now | True (A4 secondary) hoặc False (continue) | `hedge_legs.stop_replacing_started_at` | TEXT (timestamp NULL) | UC §3 bước 5; FR-EXBOT-033 |
| F1.11 | HL `marginSummary` fetch | Sau F1.10 | — | marginUsage, marginBalanceUsd, marginRequiredUsd | `hedge_legs.margin_status`, `.margin_balance_usd`, `.margin_required_usd` | TEXT (DECIMAL/ENUM) | UC §3 bước 6; FR-EXBOT-060 |
| F1.12 | `margin_status` update | Sau F1.11 | marginUsage | `margin_status` ∈ {'ok','warning','critical'} | `hedge_legs.margin_status` | TEXT ENUM | SRS FR-EXBOT-060 |
| F1.13 | Margin warning notification | Khi margin chuyển ok → warning | — | Notification enqueued | — | — | US-010 AC-010-1 |
| F1.14 | Agent key expiry check | Sau F1.12 | `hl_agent_keys.expires_at`, now | Notification enqueued nếu ≤7 ngày và `approval_status='approved'` | `hl_agent_keys.expires_at`, `hl_agent_keys.approval_status` | TEXT | UC §3 bước 7; FR-EXBOT-083 |
| F1.15 | Audit timestamp write | Sau F1.14 | now | `last_deep_audit_at` set; `next_deep_audit_at` recalculated | `bot_runtime_state.last_deep_audit_at`; `bots.next_deep_audit_at` | TEXT (timestamp) | UC §3 bước 8; erd.md |
| F1.16 | SAFE_MODE entry (A3/A4) | Mismatch, stuck marker, effective_leverage, liquidation_price | detection reason | `bots.status='safe_mode'`; admin notification | `bots.status` | ENUM | SRS FR-EXBOT-050; UC §A3, §A4 |
| F1.17 | Admin notification (A3/A4) | SAFE_MODE triggered | reason, delta/timestamp | Notification enqueued | — | — | UC §A3, §A4 |
| F1.18 | HL unreachable handling (A1) | HL timeout/5xx hoặc rate deny | — | Skip HL steps; cadence → 1h; alert enqueued | `bots.next_deep_audit_at` shortened | TEXT | UC §A1 |

**Enum sets:**
- `bots.status` (relevant): `active`, `paused`, `safe_mode`
- `hedge_legs.margin_status`: `ok`, `warning`, `critical`
- `circuit_breakers.state`: `closed`, `open`, `half_open`
- `queue_idempotency.state`: `started`, `succeeded`, `failed`, `retryable`
- `hl_agent_keys.approval_status`: `pending`, `approved`, `revoked`, `superseded`

**Messages (deep-audit context):**
- Agent key expiry notification: "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." (SRS FR-EXBOT-083)
- Reconcile mismatch: E-EXBOT-011 — "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." (internal)
- HL unreachable: E-EXBOT-008 — "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." (503)
- Margin warning (US-010 AC-010-1): "Margin warning for your ExBot. Consider depositing additional margin to HL." (notification queue)
- Margin critical SAFE_MODE (US-010 AC-010-2): "Bot entered Safe Mode — Margin critical. Please deposit additional margin to HL." (investor + admin)

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Data object / Function | States / Transitions | Preconditions | Validations | Business rules | Dependencies | Error / Success messages | Nguồn |
|---|---|---|---|---|---|---|---|
| `bots.status` (deep-audit scope) | `active`/`paused` → `safe_mode` (khi detection triggered) | `status IN ('active','paused')` | — | BR-EXBOT-007: SAFE_MODE không phải terminal — phải dẫn đến auto-recovery hoặc bot_safe_close | `close_operations`, `hedge_legs` | — | SRS FR-EXBOT-050; BR-EXBOT-007 |
| `bots.next_deep_audit_at` | Recalculated sau mỗi audit cycle | — | Normal: now + 6h; High-risk: now + 1h | High-risk khi `circuit_breakers.state != 'closed'` OR `margin_status IN ('warning','critical')` | `circuit_breakers.state`, `margin_status` | — | UC §2; SRS FR-EXBOT-016 |
| `hedge_legs.stop_trigger_crossed_at` | Set once (write-once per stop event), NULL → timestamp | — | Write-once: chỉ set nếu currently NULL | BR-EXBOT-005: write-once — light-check KHÔNG được overwrite khi đã set | D1 guard | — | BR-EXBOT-005; FR-EXBOT-033 |
| `hedge_legs.stop_replacing_started_at` | Set at start of INV-STOP; cleared in finally | — | — | Primary detection (light-check ≤5 min); secondary (deep-audit ≤6h/1h) | INV-STOP §19.5 | — | FR-EXBOT-033 |
| `hedge_legs.margin_status` | `ok` ↔ `warning` ↔ `critical` | — | marginUsage < 0.55 = ok; 0.55 ≤ marginUsage < 0.75 = warning; ≥ 0.75 = critical | Chỉ update trong hedge-sync preflight VÀ deep-audit | HL marginSummary; thresholds pending OQ-EXBOT-06 | Margin warning notification; E-EXBOT-011 | FR-EXBOT-060; OQ-EXBOT-06 |
| `hedge_legs.effective_leverage` | Checked trong deep-audit | — | > 4.5 → SAFE_MODE | — | From HL clearinghouseState | — | FR-EXBOT-050; US-010 AC-4 |
| `hedge_legs.liquidation_price` | Checked trong deep-audit | — | within 5% of hlMarkPrice → SAFE_MODE | — | From HL clearinghouseState | — | FR-EXBOT-050 |
| `bot_runtime_state.last_deep_audit_at` | Set sau mỗi audit cycle thành công | — | — | — | — | — | UC §3 bước 8; erd.md |
| `hl_agent_keys.expires_at` | Read-only trong deep-audit | `approval_status='approved'` | `expires_at - now <= 7 days` → notification | Chỉ check `approval_status='approved'` | `hl_agent_keys.approval_status` | FR-EXBOT-083 message; E-EXBOT-004 | FR-EXBOT-083 |
| `queue_idempotency` | `started` → `succeeded` | `message_id` mới | UNIQUE trên `message_id` | Duplicate → skip ngay | Worker message | — | FR-EXBOT-016 (pattern) |
| HLRateLimitDO | — | Trước mỗi HL call | `{allowed: boolean, retryAfterMs}` | Nếu `allowed=false` → skip hoặc A1 | HL API | — | FR-EXBOT-091 |
| SAFE_MODE entry conditions (deep-audit) | — | — | Reconcile mismatch; effective_leverage > 4.5; liquidation_price within 5%; stuck stop_trigger > 30 min; stuck stop_replacing > 60s | Sau entry: hedge-sync, LP rebalance, leverage change bị cấm; deep-audit vẫn chạy khi HL phục hồi | `bots.status='safe_mode'` | E-EXBOT-011; E-EXBOT-008 | SRS FR-EXBOT-050 |

---

## §F.3 — Functional Logic & Workflow Decomposition

| Function | Happy path | Alternate path | Exception path | Trigger | Input | Output | Actor | System response | Nguồn |
|---|---|---|---|---|---|---|---|---|---|
| Cron + scope selection | Cron fires; bot trong scope processed | — | D1 read fail → abort | `next_deep_audit_at <= now` | — | Worker invocation per bot | Cron | Worker start | UC §2; FR-EXBOT-016 |
| Queue idempotency | Insert message_id → continue | — | UNIQUE conflict → return immediately | Worker start | message_id | Processing hoặc skip | Worker | D1 UNIQUE constraint | FR-EXBOT-016 |
| HL clearinghouseState fetch | weight=2 approved; fetch success | — | `allowed=false` hoặc 5xx → A1 | Sau idempotency check | — | Actual short size, effective_leverage, liquidation_price | Worker | HL API | UC §3 bước 2; FR-EXBOT-091 |
| Reconcile mismatch check | Sizes match → continue | — | Mismatch → SAFE_MODE + E-EXBOT-011 admin alert | Sau fetch | actual_size vs last_known | Match/Mismatch decision | Worker | D1 write + notification | UC §3 bước 3; §A3 |
| effective_leverage check | ≤ 4.5 → continue | — | > 4.5 → SAFE_MODE + admin alert | Sau reconcile | effective_leverage | Safe/Trigger decision | Worker | D1 + notification | FR-EXBOT-050; US-010 AC-4 |
| liquidation_price check | Not within 5% → continue | — | Within 5% → SAFE_MODE (per FR-050) | Sau leverage check | liquidation_price, hlMarkPrice | Safe/Trigger decision | Worker | D1 | FR-EXBOT-050 |
| stop_trigger_crossed_at stuck check | Not stuck → continue | — | Stuck > 30 min → SAFE_MODE + admin escalation | Sau liquidation check | stop_trigger_crossed_at, now | Safe/Stuck decision | Worker | D1 + notification | UC §3 bước 4; §A4; BR-EXBOT-005 |
| stop_replacing_started_at stuck check | Not stuck → continue | — | Stuck > 60s → SAFE_MODE (secondary backstop) | Sau stop_trigger check | stop_replacing_started_at, now | Safe/Stuck decision | Worker | D1 + notification | UC §3 bước 5; §A4; FR-EXBOT-033 |
| marginSummary fetch + update | Fetch success; margin_status updated | — | HL fail → A1 (skip update) | Sau stuck checks | — | margin_status ∈ {ok,warning,critical} | Worker | D1 write | UC §3 bước 6; FR-EXBOT-060 |
| Agent key expiry check | `expires_at > now + 7d` → skip | `expires_at - now <= 7d` → notification | — | Sau margin update | expires_at, approval_status | Notification hoặc skip | Worker | notification queue | UC §3 bước 7; FR-EXBOT-083 |
| HL unreachable (A1) | — | HL 5xx hoặc rate deny | — | HL API call | — | Skip HL steps; cadence = 1h; alert | Worker | Partial audit | UC §A1 |
| Paused bot audit (A2) | Full audit chạy bình thường | — | — | Cron | bot.status='paused' | Same as happy path | Worker | No skip | UC §A2 |

---

## §F.4 — Functional Integration & Data Consistency

| Integration point | Effect | Data consistency concern | Nguồn |
|---|---|---|
| D1 `last_known_hl_short_size` ↔ HL actual | Deep-audit cross-check phát hiện divergence sau khi hedge-sync fail silently | Source of truth là HL actual; D1 lệch sau crash/partial-fill | SRS FR-EXBOT-016 |
| `stop_trigger_crossed_at` write-once guard | Deep-audit chỉ check, không set (light-check set lần đầu) | Nếu light-check không clear sau stop resolved, stuck detection sẽ false-positive | BR-EXBOT-005; FR-EXBOT-033 |
| `stop_replacing_started_at` primary (light-check) vs secondary (deep-audit) | Nếu light-check primary missed, deep-audit phát hiện muộn hơn (≤6h/1h) | Khoảng lag giữa lúc stuck và lúc deep-audit detect có thể lớn (tối đa 6h) | FR-EXBOT-033 |
| `margin_status` update timing | Chỉ deep-audit và hedge-sync cập nhật; light-check đọc D1 stale | Giữa hai deep-audit cycles, margin_status có thể stale tới 6h trong normal mode | FR-EXBOT-060; FR-EXBOT-016 |
| HLRateLimitDO ↔ multiple HL calls | Deep-audit gọi cả clearinghouseState (weight=2) VÀ marginSummary (weight khác) — hai lần HLRateLimitDO | Nếu clearinghouseState allowed nhưng marginSummary denied, audit là partial | SRS FR-EXBOT-091 |
| `bots.next_deep_audit_at` recalculation | Sau A1 (HL unreachable), cadence switch sang 1h | Nếu HL unreachable kéo dài, deep-audit sẽ liên tục retry mỗi 1h và consume HLRateLimitDO budget | UC §A1; FR-EXBOT-016 |
| SAFE_MODE entry ↔ ongoing audit | Deep-audit vẫn chạy khi bot ở safe_mode (khi HL phục hồi) | Sau SAFE_MODE entry, audit cycle tiếp theo phải không re-trigger SAFE_MODE nếu condition đã resolve | SRS FR-EXBOT-050 |
| `hl_agent_keys.expires_at` ↔ `approval_status` | Chỉ check key với `approval_status='approved'`; revoked/pending không cần notify | Test design: chỉ test `approved` keys | SRS FR-EXBOT-083 |
| Multiple SAFE_MODE conditions trong cùng cycle | "ANY of" — nhiều conditions đều true → SAFE_MODE triggered nhiều lần (idempotent) | Worker tiếp tục check các bước còn lại sau mỗi SAFE_MODE entry | SRS FR-EXBOT-050 |

---

## §F.5 — Acceptance Criteria Candidates

| # | AC Candidate | Trace | Cần xác nhận? |
|---|---|---|---|
| AC-C1 | Bot `status='paused'` vẫn được deep-audit đầy đủ ở cadence 6h — không bị skip | UC §A2; SRS FR-EXBOT-016 | Không |
| AC-C2 | Khi actual short size ≠ `last_known_hl_short_size`, `bots.status='safe_mode'` được set và admin nhận E-EXBOT-011 | UC §A3; SRS FR-EXBOT-050 | Không |
| AC-C3 | Khi `effective_leverage > 4.5`, SAFE_MODE được trigger và admin được alert với giá trị effective_leverage | FR-EXBOT-050; US-010 AC-010-4 | Không |
| AC-C4 | Khi `liquidation_price within 5% of hlMarkPrice`, SAFE_MODE được trigger | FR-EXBOT-050 | Không |
| AC-C5 | Khi `stop_trigger_crossed_at` stuck > 30 phút, SAFE_MODE được trigger trong cùng audit cycle | UC §A4; FR-EXBOT-033 | Không |
| AC-C6 | Khi `stop_replacing_started_at` stuck > 60s, SAFE_MODE được trigger (secondary backstop — chậm hơn primary light-check) | UC §3 bước 5; FR-EXBOT-033 | Không |
| AC-C7 | Cadence chuyển sang 1h khi `circuit_breakers.state != 'closed'` HOẶC `margin_status IN ('warning','critical')` | UC §2; SRS FR-EXBOT-016 | Không |
| AC-C8 | Khi `hl_agent_keys.expires_at - now <= 7d` VÀ `approval_status='approved'`, notification "Your HL agent key expires in {N} days..." được enqueue | UC §3 bước 7; SRS FR-EXBOT-083 | Không |
| AC-C9 | Khi `hl_agent_keys.expires_at - now <= 7d` nhưng `approval_status='pending'`, notification KHÔNG được gửi | SRS FR-EXBOT-083 | Không |
| AC-C10 | `queue_idempotency` UNIQUE conflict → worker return immediately, không chạy lại | SRS FR-EXBOT-016 idempotency pattern | Không |
| AC-C11 | Margin_status 'warning' → notification gửi cho investor | US-010 AC-010-1 | Không |
| AC-C12 | Multiple SAFE_MODE conditions trong cùng cycle → SAFE_MODE triggered nhiều lần nhưng idempotent | FR-EXBOT-050 "ANY of" | Không |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 | Medium | UNCLEAR_INFO | UC §A1; SRS FR-EXBOT-016 | UC §A1 mô tả khi HL unreachable: "skip HL-dependent steps (2, 3, 4, 6, 7)". Tuy nhiên: (a) "step 4" trong UC là bước check `stop_trigger_crossed_at` — bước này chỉ đọc D1, không gọi HL, tại sao lại bị skip? (b) "step 7" là agent key expiry check — bước này chỉ đọc D1, không gọi HL, tại sao bị skip? Nếu D1-only steps bị skip khi HL unavailable, `margin_status` và agent key expiry sẽ không được check ngay cả khi dữ liệu D1 đã có. BA/Tech Lead xác nhận: khi HL unreachable trong A1, "skip HL-dependent steps" cụ thể bao gồm những bước nào? stop_trigger check và agent key check có bị skip không? | Tester không thể biết chính xác tập hợp operations nào vẫn chạy khi HL unreachable; bỏ sót test case quan trọng về partial audit behavior | BA / Tech Lead | Open |
| I-02 | Minor | INTERNAL_INCONSISTENCY | UC §5 Postconditions; UC §6 | UC có hai mục `## Postconditions` — mục §5 có nội dung đúng và cụ thể. Mục thứ hai (sau §5, trước §6) là placeholder template: "System state reflects the completed audit", "NFR-ADM-005". NFR-ADM-005 là NFR của module Admin, không phải ExBot. Cùng pattern với uc-hedge-sync và uc-user-redeem. | Gây nhầm lẫn; pattern nhất quán với các UC khác nên cần cleanup toàn bộ | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| Margin thresholds (0.55/0.75) | External — OQ-EXBOT-06 (zen backtest) | Test giá trị cụ thể của threshold chưa được finalize | zen | Open |
| `hlMarkPrice` data source trong A1 | Internal | Cần thiết để compute liquidation_price check | Tech Lead | Open |

### 10.3 Audit Summary

#### Bảng điểm

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 18 | ⚠️ Partial | Inventory đầy đủ cho các function chính; effective_leverage và liquidation_price checks được bổ sung từ US-010 và FR-050; các field đã được verify với erd.md |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 22 | ⚠️ Partial | BR-EXBOT-005 và BR-EXBOT-007 được áp dụng rõ; margin thresholds được note từ OQ-EXBOT-06; notification recipients cho margin warning đã rõ từ US-010 AC-1 |
| 3 | Functional Logic & Workflow Decomposition | 25 | 21 | ⚠️ Partial | 5 detection paths được mô tả rõ (reconcile mismatch, effective_leverage, liquidation_price, stop_trigger stuck, stop_replacing stuck); A1 skip logic không rõ (I-01) |
| 4 | Functional Integration & Data Consistency | 15 | 13 | ⚠️ Partial | HLRateLimitDO double-call được nhận biết; multiple SAFE_MODE conditions idempotent behavior được xác định từ "ANY of" trong FR-050 |
| 5 | UC / Spec Documentation Quality Issues | 15 | 13 | ⚠️ Partial | Double Postconditions (I-02). FR-012 (light-check zero HL calls) không liên quan trực tiếp đến deep-audit. Trigger section rõ ràng (cron-driven). |
| **Tổng** | | **100** | **87** | | |

**Auto-cap áp dụng:** Không có Blocker — không có auto-cap bắt buộc.

#### Verdict: **Conditionally Ready (87/100)**

Không có Blocker. UC-EXBOT-deep-audit có chất lượng tốt: trigger được định nghĩa rõ (cron, không phải placeholder), 5 detection paths được mô tả tường minh, BR-EXBOT-003 exception được ghi chú, notification recipients đã được xác định (admin cho A3/A4, investor cho margin warning). Có thể dùng cho test design với điều kiện I-01 được giải quyết.

#### Major issues cần giải quyết

1. **I-01**: Xác định chính xác tập hợp bước bị skip khi HL unreachable trong A1 — đặc biệt stop_trigger check (D1-only) và agent key check (D1-only).

#### Minor issues

2. **I-02**: Documentation cleanup — xóa duplicate Postconditions section.

#### Khuyến nghị

UC-EXBOT-deep-audit đủ tốt để bắt đầu viết test scenarios cho các happy paths và các detection paths đã được mô tả rõ. I-01 ảnh hưởng đến test case cho partial audit behavior khi HL unreachable — có thể test bằng cách giả định skip behavior và đợt BA confirm.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-19 | QC UC Read Agent | Tạo báo cáo audited lần đầu |
| v2 | 2026-06-26 | QC UC Read Agent | Re-audit sau BA response 2026-06-20; bổ sung effective_leverage và liquidation_price checks; làm rõ notification recipients; cập nhật inventory với 18 functions; sửa field name `last_audit_at` → `last_deep_audit_at` in `bot_runtime_state` |

---

*Report audited UC readiness - Vietnamese headings version*
