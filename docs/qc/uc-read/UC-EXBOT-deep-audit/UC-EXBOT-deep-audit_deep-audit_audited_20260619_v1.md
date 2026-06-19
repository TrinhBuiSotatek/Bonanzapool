# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tiêu đề tài liệu:** UC-EXBOT-deep-audit — Báo cáo rà soát độ sẵn sàng test  
**Ngày tạo:** 2026-06-19  
**Tác giả / Agent:** qc-uc-read-exbot (Trinh.Bui / MTS-978)  
**Phiên bản:** v1

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
| `srs/spec.md` | SPEC v5.2.6, changelog 2026-06-18 | SRS — source of truth | FR-016, FR-033, FR-050, FR-060, FR-083, FR-091 |
| `srs/states.md` | Updated 2026-06-18 | State diagram | lifecycle, circuit breaker, margin states |
| `srs/flows.md` | Updated 2026-06-18 | Flow diagram | F-01 queue topology |
| `srs/erd.md` | Draft | ERD (D1 schema) | hedge_legs, bot_runtime_state, hl_agent_keys, bots |
| `frd.md` | Updated 2026-06-18 | FRD | FR-EXBOT-016, FR-EXBOT-033, FR-EXBOT-083 |
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
| Audit timestamp update | `hedge_legs.last_audit_at` và `bot_runtime_state.last_deep_audit_at` | UC §3 bước 8; erd.md |
| Queue idempotency | `queue_idempotency` row insert/update | UC §3 bước 9 |
| High-risk cadence switch | 6h → 1h khi circuit_breakers.state != 'closed' hoặc margin_status IN ('warning','critical') | UC §2; SRS FR-EXBOT-016 |
| HL unreachable handling (A1) | Skip HL-dependent steps; switch to high-risk; notify | UC §A1 |
| Paused bot audit (A2) | Bot paused vẫn được audit đầy đủ ở cadence 6h | UC §A2; SRS FR-EXBOT-016 |

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
| Admin | Secondary | Nhận escalation notification khi SAFE_MODE triggered | Read-only trong UC này | UC §A3, §A4 |
| USDC Investor | Secondary | Nhận notification khi agent key sắp hết hạn hoặc SAFE_MODE entry | Read-only trong UC này | UC §3 bước 7; SRS FR-EXBOT-083 |

**Nhận xét readiness:** Actor đủ rõ. Tuy nhiên UC không phân biệt: khi SAFE_MODE triggered (A3, A4), notification đi đến admin, investor, hay cả hai? Spec FR-EXBOT-050 nói "alert user/admin" nhưng không chỉ rõ ai nhận gì trong deep-audit context.

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
| Happy path (no issues) | `hedge_legs.margin_status` updated; `hedge_legs.last_audit_at` set; `bot_runtime_state.last_deep_audit_at` set; `queue_idempotency.state='succeeded'` | UC §5; erd.md |
| Reconcile mismatch (A3) | SAFE_MODE triggered; mismatch ghi vào D1; admin notified | UC §A3; SRS FR-EXBOT-050 |
| Stuck stop marker (A4) | SAFE_MODE triggered; admin escalation với timestamp + reason | UC §A4 |
| HL unreachable (A1) | HL-dependent steps skipped; `next_deep_audit_at` shortened to 1h; notification enqueued | UC §A1 |
| Agent key expiring (step 7) | Notification enqueued: "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." | UC §3 bước 7; SRS FR-EXBOT-083 |
| Margin status updated | `hedge_legs.margin_status` ∈ {'ok','warning','critical'} per fresh marginSummary | UC §3 bước 6; SRS FR-EXBOT-060 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng chính: Deep-Audit cron execution

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Cron Scheduler | `next_deep_audit_at <= now` → fire worker | Worker khởi động cho tất cả bot trong scope | — | — | UC §2; erd.md |
| 2 | Deep-Audit Worker | Đọc bot state từ D1: `bots.status`, `bots.lifecycle_state`, `hedge_legs`, `circuit_breakers.state`, `margin_status` | Dữ liệu D1 được load | — | D1 unavailable → abort | UC §3 bước 1 |
| 3 | Deep-Audit Worker | Insert `message_id` vào `queue_idempotency` (state='started') | Row tạo → tiếp tục | — | UNIQUE conflict → skip (already processed) | SRS FR-EXBOT-016 (idempotency pattern) |
| 4 | Deep-Audit Worker | Gọi HLRateLimitDO: khai báo weight=2 (clearinghouseState) | `{allowed: true}` → tiếp tục | `{allowed: false}` → A1 | HL 5xx → A1 | UC §3 bước 2; SRS FR-EXBOT-091 |
| 5 | Deep-Audit Worker | Fetch `clearinghouseState` từ HL | Actual short size trả về | — | HL timeout/5xx → A1 | UC §3 bước 2 |
| 6 | Deep-Audit Worker | So sánh actual short size với `hedge_legs.last_known_hl_short_size` | Match → tiếp tục | — | Mismatch → A3 | UC §3 bước 3 |
| 7 | Deep-Audit Worker | Check `stop_trigger_crossed_at IS NOT NULL AND (now - stop_trigger_crossed_at) > 30 min` | False → tiếp tục | — | True → A4 | UC §3 bước 4; SRS FR-EXBOT-033; BR-EXBOT-005 |
| 8 | Deep-Audit Worker | Check `stop_replacing_started_at IS NOT NULL AND (now - stop_replacing_started_at) > 60s` | False → tiếp tục | — | True → A4 (secondary backstop) | UC §3 bước 5; SRS FR-EXBOT-033 |
| 9 | Deep-Audit Worker | Gọi HLRateLimitDO: khai báo weight cho `marginSummary` | `{allowed: true}` → tiếp tục | — | `{allowed: false}` → A1 | SRS FR-EXBOT-091 |
| 10 | Deep-Audit Worker | Fetch `marginSummary` từ HL | margin data trả về | — | HL timeout/5xx → A1 | UC §3 bước 6 |
| 11 | Deep-Audit Worker | Update `hedge_legs.margin_status` từ fresh HL data | `margin_status` ∈ {'ok','warning','critical'} | — | — | UC §3 bước 6; SRS FR-EXBOT-060 |
| 12 | Deep-Audit Worker | Check `hl_agent_keys.expires_at - now <= 7 days` | False → skip | True → enqueue notification "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." | — | UC §3 bước 7; SRS FR-EXBOT-083 |
| 13 | Deep-Audit Worker | Update `hedge_legs.last_audit_at = now`; `bot_runtime_state.last_deep_audit_at = now` | Timestamps set | — | — | UC §3 bước 8; erd.md |
| 14 | Deep-Audit Worker | Update `queue_idempotency.state='succeeded'` | Audit complete | — | — | UC §3 bước 9 |

#### B. Alternate flows

| ID | Trigger | Hành động hệ thống | Trạng thái cuối | Nguồn |
|---|---|---|---|---|
| A1 | HLRateLimitDO `allowed=false` hoặc HL 5xx | Skip HL-dependent steps (bước 5, 6, 10, 11, 12); update `next_deep_audit_at` sang 1h interval; enqueue "Hyperliquid API unreachable" | Audit partial; cadence = high-risk (1h) | UC §A1 |
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
| F1.5 | HL `clearinghouseState` fetch | Sau HLRateLimitDO allow | — | Actual short size, position data | `hedge_legs.last_known_hl_short_size` | TEXT (DECIMAL) | UC §3 bước 2; SRS FR-EXBOT-016 |
| F1.6 | Reconcile mismatch check | Sau F1.5 | actual_size, `last_known_hl_short_size` | Match (continue) hoặc mismatch (A3) | `hedge_legs.last_known_hl_short_size` | TEXT (DECIMAL) | UC §3 bước 3 |
| F1.7 | `stop_trigger_crossed_at` stuck check | Sau F1.6 | `hedge_legs.stop_trigger_crossed_at`, now | True (A4) hoặc False (continue) | `hedge_legs.stop_trigger_crossed_at` | TEXT (timestamp NULL) | UC §3 bước 4; SRS FR-EXBOT-033; BR-EXBOT-005 |
| F1.8 | `stop_replacing_started_at` stuck check | Sau F1.7 | `hedge_legs.stop_replacing_started_at`, now | True (A4 secondary) hoặc False (continue) | `hedge_legs.stop_replacing_started_at` | TEXT (timestamp NULL) | UC §3 bước 5; SRS FR-EXBOT-033 |
| F1.9 | HL `marginSummary` fetch | Sau F1.8 | — | marginUsage, marginBalanceUsd, marginRequiredUsd | `hedge_legs.margin_status`, `.margin_balance_usd`, `.margin_required_usd` | TEXT (DECIMAL/ENUM) | UC §3 bước 6; SRS FR-EXBOT-060 |
| F1.10 | `margin_status` update | Sau F1.9 | marginUsage | `margin_status` ∈ {'ok','warning','critical'} | `hedge_legs.margin_status` | TEXT ENUM | SRS FR-EXBOT-060 |
| F1.11 | Agent key expiry check | Sau F1.10 | `hl_agent_keys.expires_at`, now | Notification enqueued nếu ≤7 ngày | `hl_agent_keys.expires_at`, `hl_agent_keys.approval_status` | TEXT | UC §3 bước 7; SRS FR-EXBOT-083 |
| F1.12 | Audit timestamp write | Sau F1.11 | now | `last_audit_at` set; `last_deep_audit_at` set; `next_deep_audit_at` recalculated | `hedge_legs.last_audit_at`; `bot_runtime_state.last_deep_audit_at`; `bots.next_deep_audit_at` | TEXT (timestamp) | UC §3 bước 8; erd.md |
| F1.13 | SAFE_MODE entry (A3/A4) | Mismatch hoặc stuck marker | detection reason | `bots.status='safe_mode'`; admin notification | `bots.status` | ENUM | SRS FR-EXBOT-050; UC §A3, §A4 |
| F1.14 | Admin notification (A3/A4) | SAFE_MODE triggered | reason, delta/timestamp | Notification enqueued | — | — | UC §A3, §A4 |
| F1.15 | HL unreachable handling (A1) | HL timeout/5xx hoặc rate deny | — | Skip HL steps; cadence → 1h; alert enqueued | `bots.next_deep_audit_at` shortened | TEXT | UC §A1 |

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
| `hedge_legs.stop_trigger_crossed_at` | Set once (write-once per stop event), NULL → timestamp | — | Write-once: chỉ set nếu currently NULL | BR-EXBOT-005: write-once — light-check KHÔNG được overwrite khi đã set | D1 guard | — | BR-EXBOT-005; SRS FR-EXBOT-033 |
| `hedge_legs.stop_replacing_started_at` | Set at start of INV-STOP; cleared in finally | — | — | Primary detection (light-check ≤5 min); secondary (deep-audit ≤6h/1h) | INV-STOP §19.5 | — | SRS FR-EXBOT-033 |
| `hedge_legs.margin_status` | `ok` ↔ `warning` ↔ `critical` | — | marginUsage < 0.55 = ok; 0.55 ≤ marginUsage < 0.75 = warning; ≥ 0.75 = critical | Chỉ update trong hedge-sync preflight VÀ deep-audit — không trong light-check | HL marginSummary; OQ-EXBOT-06 (thresholds pending backtest) | Margin warning notification; E-EXBOT-011 | SRS FR-EXBOT-060; OQ-EXBOT-06 |
| `hedge_legs.last_audit_at` | Set sau mỗi audit cycle | — | — | — | — | — | UC §3 bước 8; erd.md |
| `bot_runtime_state.last_deep_audit_at` | Set sau mỗi audit cycle | — | — | — | — | — | erd.md |
| `hl_agent_keys.expires_at` | Read-only trong deep-audit | `approval_status='approved'` | `expires_at - now <= 7 days` → notification | Thông báo user trước 7 ngày; key hết hạn ở bot start bị block bởi E-EXBOT-004 | `hl_agent_keys.approval_status` | FR-EXBOT-083 message; E-EXBOT-004 | SRS FR-EXBOT-083 |
| `queue_idempotency` | `started` → `succeeded` | `message_id` mới | UNIQUE trên `message_id` | Duplicate → skip ngay | Worker message | — | SRS FR-EXBOT-016 (pattern) |
| HLRateLimitDO | — | Trước mỗi HL call | `{allowed: boolean, retryAfterMs}` | Nếu `allowed=false` → skip hoặc A1 | HL API | — | SRS FR-EXBOT-091 |
| SAFE_MODE entry conditions (deep-audit) | — | — | Reconcile mismatch; stuck stop_trigger > 30 min; stuck stop_replacing > 60s | Sau entry: hedge-sync, LP rebalance, leverage change bị cấm; deep-audit vẫn chạy khi HL phục hồi | `bots.status='safe_mode'` | E-EXBOT-011; E-EXBOT-008 | SRS FR-EXBOT-050 |

---

## §F.3 — Functional Logic & Workflow Decomposition

| Function | Happy path | Alternate path | Exception path | Trigger | Input | Output | Actor | System response | Nguồn |
|---|---|---|---|---|---|---|---|---|---|
| Cron + scope selection | Cron fires; bot trong scope processed | — | D1 read fail → abort | `next_deep_audit_at <= now` | — | Worker invocation per bot | Cron | Worker start | UC §2; SRS FR-EXBOT-016 |
| Queue idempotency | Insert message_id → continue | — | UNIQUE conflict → return immediately | Worker start | message_id | Processing hoặc skip | Worker | D1 UNIQUE constraint | SRS FR-EXBOT-016 |
| HL clearinghouseState fetch | weight=2 approved; fetch success | — | `allowed=false` hoặc 5xx → A1 | Sau idempotency check | — | Actual short size | Worker | HL API | UC §3 bước 2; SRS FR-EXBOT-091 |
| Reconcile mismatch check | Sizes match → continue | — | Mismatch → SAFE_MODE + E-EXBOT-011 admin alert | Sau fetch | actual_size vs last_known | Match/Mismatch decision | Worker | D1 write + notification | UC §3 bước 3; §A3 |
| stop_trigger_crossed_at stuck check | Not stuck → continue | — | Stuck > 30 min → SAFE_MODE + admin escalation | Sau reconcile | stop_trigger_crossed_at, now | Safe/Stuck decision | Worker | D1 + notification | UC §3 bước 4; §A4; BR-EXBOT-005 |
| stop_replacing_started_at stuck check | Not stuck → continue | — | Stuck > 60s → SAFE_MODE (secondary backstop) | Sau stop_trigger check | stop_replacing_started_at, now | Safe/Stuck decision | Worker | D1 + notification | UC §3 bước 5; §A4; SRS FR-EXBOT-033 |
| marginSummary fetch + update | Fetch success; margin_status updated | — | HL fail → A1 (skip update) | Sau stuck checks | — | margin_status ∈ {ok,warning,critical} | Worker | D1 write | UC §3 bước 6; SRS FR-EXBOT-060 |
| Agent key expiry check | `expires_at > now + 7d` → skip | `expires_at - now <= 7d` → notification | — | Sau margin update | expires_at, approval_status | Notification hoặc skip | Worker | notification queue | UC §3 bước 7; SRS FR-EXBOT-083 |
| HL unreachable (A1) | — | HL 5xx hoặc rate deny | — | HL API call | — | Skip HL steps; cadence = 1h; alert | Worker | Partial audit | UC §A1 |
| Paused bot audit (A2) | Full audit chạy bình thường | — | — | Cron | bot.status='paused' | Same as happy path | Worker | No skip | UC §A2 |

---

## §F.4 — Functional Integration & Data Consistency

| Integration point | Effect | Data consistency concern | Nguồn |
|---|---|---|---|
| D1 `last_known_hl_short_size` ↔ HL actual | Deep-audit cross-check phát hiện divergence sau khi hedge-sync fail silently | Source of truth là HL actual; D1 lệch sau crash/partial-fill | SRS FR-EXBOT-016 |
| `stop_trigger_crossed_at` write-once guard | Deep-audit chỉ check, không set (light-check set lần đầu) | Nếu light-check không clear sau stop resolved, stuck detection sẽ false-positive | BR-EXBOT-005; SRS FR-EXBOT-033 |
| `stop_replacing_started_at` primary (light-check) vs secondary (deep-audit) | Nếu light-check primary missed, deep-audit phát hiện muộn hơn (≤6h/1h) | Khoảng lag giữa lúc stuck và lúc deep-audit detect có thể lớn (tối đa 6h) | SRS FR-EXBOT-033 |
| `margin_status` update timing | Chỉ deep-audit và hedge-sync cập nhật; light-check đọc D1 stale | Giữa hai deep-audit cycles, margin_status có thể stale tới 6h trong normal mode | SRS FR-EXBOT-060; SRS FR-EXBOT-016 |
| HLRateLimitDO ↔ multiple HL calls | Deep-audit gọi cả clearinghouseState (weight=2) VÀ marginSummary — hai lần HLRateLimitDO | Nếu clearinghouseState allowed nhưng marginSummary denied, audit là partial | SRS FR-EXBOT-091 |
| `bots.next_deep_audit_at` recalculation | Sau A1 (HL unreachable), cadence switch sang 1h | Nếu HL unreachable kéo dài, deep-audit sẽ liên tục retry mỗi 1h và consume HLRateLimitDO budget | UC §A1; SRS FR-EXBOT-016 |
| SAFE_MODE entry ↔ ongoing audit | Deep-audit vẫn chạy khi bot ở safe_mode (khi HL phục hồi) | Sau SAFE_MODE entry, audit cycle tiếp theo phải không re-trigger SAFE_MODE nếu condition đã resolve | SRS FR-EXBOT-050 |
| `hl_agent_keys.expires_at` ↔ `approval_status` | Chỉ check key với `approval_status='approved'`; revoked/pending không cần notify | Nếu user có pending key đang chờ approve, expired notification có gửi cho old approved key không? | SRS FR-EXBOT-083 (không rõ — I-04) |

---

## §F.5 — Acceptance Criteria Candidates

| # | AC Candidate | Trace | Cần xác nhận? |
|---|---|---|---|
| AC-C1 | Bot `status='paused'` vẫn được deep-audit đầy đủ ở cadence 6h — không bị skip | UC §A2; SRS FR-EXBOT-016 | Không |
| AC-C2 | Khi actual short size ≠ `last_known_hl_short_size`, `bots.status='safe_mode'` được set và admin nhận E-EXBOT-011 | UC §A3; SRS FR-EXBOT-050 | Không |
| AC-C3 | Khi `stop_trigger_crossed_at` stuck > 30 phút, SAFE_MODE được trigger trong cùng audit cycle | UC §A4; SRS FR-EXBOT-033 | Không |
| AC-C4 | Khi `stop_replacing_started_at` stuck > 60s, SAFE_MODE được trigger (secondary backstop — chậm hơn primary light-check) | UC §3 bước 5; SRS FR-EXBOT-033 | Không |
| AC-C5 | Cadence chuyển sang 1h khi `circuit_breakers.state != 'closed'` HOẶC `margin_status IN ('warning','critical')` | UC §2; SRS FR-EXBOT-016 | Không |
| AC-C6 | Khi `hl_agent_keys.expires_at - now <= 7d`, notification "Your HL agent key expires in {N} days..." được enqueue | UC §3 bước 7; SRS FR-EXBOT-083 | Không |
| AC-C7 | Khi HL unreachable (5xx hoặc `allowed=false`), HL-dependent steps bị skip và `next_deep_audit_at` = now + 1h | UC §A1 | Cần xác nhận "skip" bao gồm bước nào (I-01) |
| AC-C8 | `queue_idempotency` UNIQUE conflict → worker return immediately, không chạy lại | SRS FR-EXBOT-016 idempotency pattern | Không |
| AC-C9 | Margin_status 'warning' → size-increase hedge-sync disabled; 'critical' (×2) → SAFE_MODE + admin + investor alert | US-010 AC-010-1, AC-010-2; SRS FR-EXBOT-060 | Thresholds pending OQ-EXBOT-06 |

---

## 10. Kết quả đánh giá

### 10.1 Issue Register — Unified Gap & Question Report

| Issue ID | Type | Severity | Affected area | Source trace | Finding | Impact on tester understanding | Suggested question or fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-01 | `MISSING_INFO` | Major | Area 3 (Logic) | UC §A1; SRS FR-EXBOT-016 | UC §A1 mô tả khi HL unreachable: "skip HL-dependent steps (2, 3, 4, 6, 7)". Tuy nhiên UC liệt kê step số, không liệt kê function name. Không rõ: (a) "step 4" trong UC là bước check stop_trigger_crossed_at — bước này không gọi HL, tại sao lại bị skip? (b) "step 7" là agent key expiry check — bước này chỉ đọc D1, không gọi HL, tại sao bị skip? (c) Nếu D1 reads bị skip nhưng không HL calls, `margin_status` và agent key expiry sẽ không được check ngay cả khi dữ liệu đã có trong D1. | Tester không thể biết chính xác tập hợp operations nào vẫn chạy khi HL unreachable; bỏ sót test case quan trọng | BA/Tech Lead xác nhận: khi HL unreachable trong A1, "skip HL-dependent steps" cụ thể bao gồm những bước nào? stop_trigger check (D1-only) và agent key check (D1-only) có bị skip không? | Open |
| I-02 | `MISSING_INFO` | Major | Area 2 (States), Area 3 (Logic) | UC §A3, §A4; SRS FR-EXBOT-050 | UC §A3 và §A4 đều ghi "trigger SAFE_MODE entry" nhưng không mô tả: (a) notification đi đến ai — investor, admin, hay cả hai? SRS FR-EXBOT-050 ghi "alert user/admin" nhưng deep-audit UC không phân biệt. US-010 AC-010-2 ghi rõ "both the investor and admin receive alerts" cho margin critical. Không rõ reconcile mismatch và stuck stop marker có cùng behavior không. (b) Sau SAFE_MODE entry bởi deep-audit, `bots.status='safe_mode'` được set ngay trong cùng worker invocation không? | Tester không thể viết expected result cho notification recipients trong A3/A4 test cases | BA/Tech Lead xác nhận: khi deep-audit trigger SAFE_MODE qua A3 (mismatch) và A4 (stuck marker), notification gửi đến ai — investor, admin, hay cả hai? | Open |
| I-03 | `MISSING_INFO` | Major | Area 3 (Logic) | UC §3 bước 6; SRS FR-EXBOT-060; US-010 | UC §3 bước 6 chỉ ghi "Fetch marginSummary from HL; update hedge_legs.margin_status from fresh HL data". UC không mô tả: (a) nếu `margin_status` chuyển từ `ok` → `warning`, notification "Margin warning for your ExBot. Consider depositing additional margin to HL." có được enqueue trong cùng deep-audit cycle này không? (b) Nếu `margin_status='critical'` được ghi, deep-audit có check "second consecutive critical" để trigger SAFE_MODE hay bước đó thuộc về logic khác? US-010 AC-010-2 yêu cầu "second consecutive critical reading" nhưng UC không mô tả counter hoặc field tracking consecutive reads. | Tester không thể test margin transition notifications và "consecutive critical" logic mà không biết luồng trong deep-audit | BA/Tech Lead làm rõ: trong deep-audit, sau khi update margin_status: (1) notification được enqueue ngay không? (2) "consecutive critical" được track bằng cơ chế nào (field trong D1 hay logic nội tại)? | Open |
| I-04 | `MISSING_INFO` | Minor | Area 3 (Logic) | UC §3 bước 7; SRS FR-EXBOT-083; erd.md | UC §3 bước 7 check `hl_agent_keys.expires_at - now <= 7 days` nhưng không chỉ rõ: (a) chỉ check key với `approval_status='approved'` hay check tất cả key? (b) Nếu user có một key `approved` sắp hết hạn VÀ một key `pending` đang chờ approve, notification có được gửi không? SRS FR-EXBOT-083 ghi "existing approved key remains active" trong window pending→approved, nhưng không nói về notification behavior trong trường hợp này. | Tester cần biết điều kiện chính xác để test edge case "pending replacement in progress" | BA/Tech Lead xác nhận: khi check agent key expiry, worker check tất cả key hay chỉ `approval_status='approved'`? Khi có pending replacement, notification có được gửi không? | Open |
| I-05 | `CROSS_SOURCE_CONFLICT` | Major | Area 5 (Doc quality), Area 3 (Logic) | UC §3 bước 8; UC §5 Postconditions; erd.md | UC §3 bước 8 ghi "Update D1 audit timestamp: `hedge_legs.last_audit_at = now`". Tuy nhiên erd.md cho thấy field này KHÔNG tồn tại trong `hedge_legs` schema — `hedge_legs` không có `last_audit_at`. ERD cho thấy: `hedge_legs` có `last_stop_audit_at` và `updated_at`; `bot_runtime_state` có `last_deep_audit_at`. UC §5 Postconditions ghi "`hedge_legs.last_audit_at` set to current timestamp" — confirm tên field này. Không rõ UC có typo không (`last_audit_at` → `last_deep_audit_at` trong `bot_runtime_state`?) | Tester không biết field nào thực sự được update; nếu test kiểm tra `hedge_legs.last_audit_at` sẽ fail vì field không tồn tại | BA vui lòng xác nhận: bước 8 update field nào trong schema — `bot_runtime_state.last_deep_audit_at`? Hay có field `hedge_legs.last_audit_at` không được định nghĩa trong erd.md? | Open |
| I-06 | `INTERNAL_INCONSISTENCY` | Minor | Area 5 (Doc quality) | UC §5 Postconditions; UC §3 | UC có hai mục `## Postconditions` — mục §5 (hợp lệ, cụ thể) và mục thứ hai (sau §5): "System state reflects the completed audit", "All three detection paths... are evaluated per audit cycle", "NFR-ADM-005". Mục thứ hai có nội dung liên quan hơn so với uc-hedge-sync và uc-user-redeem nhưng NFR-ADM-005 vẫn là NFR của module Admin. Cùng pattern với các UC trước. | Gây nhầm lẫn về postconditions; tester có thể nhầm NFR-ADM-005 áp dụng cho ExBot | BA vui lòng xóa phần placeholder Postconditions thứ hai hoặc merge nội dung vào §5. | Open |
| I-07 | `MISSING_INFO` | Major | Area 3 (Logic), Area 2 (States) | UC §3; SRS FR-EXBOT-050; states.md | UC mô tả 3 detection paths (A3, A4) có thể trigger SAFE_MODE nhưng không mô tả: (a) nếu nhiều detection paths đều true trong cùng một audit cycle (ví dụ: cả mismatch VÀ stuck stop marker), SAFE_MODE được triggered một lần hay nhiều lần? Có idempotency không? (b) Sau SAFE_MODE entry, các bước còn lại trong audit (margin update, agent key check, timestamp write) có tiếp tục chạy không? | Tester cần biết behavior khi nhiều conditions đồng thời xảy ra | BA/Tech Lead xác nhận: khi nhiều SAFE_MODE conditions đều true trong một cycle, behavior là gì? Audit có continue sau SAFE_MODE entry không? | Open |
| I-08 | `MISSING_INFO` | Minor | Area 4 (Integration) | UC §3; SRS FR-EXBOT-050 | SRS FR-EXBOT-050 liệt kê đầy đủ SAFE_MODE conditions: "HL API unreachable for more than 5 minutes; reconcile mismatch; margin_status='critical' twice; effective_leverage > 4.5; liquidation_price within 5% of hlMarkPrice; stop_trigger stuck > 30 min; stop_replacing stuck > 60s". Deep-audit UC chỉ cover 3 trong 7 conditions (reconcile mismatch, stop_trigger stuck, stop_replacing stuck). Không rõ: `effective_leverage > 4.5` và `liquidation_price within 5%` có được check trong deep-audit không? US-010 AC-010-4 mô tả effective_leverage trigger nhưng không chỉ rõ đây là trong deep-audit hay hedge-sync. | Tester có thể miss test cases cho effective_leverage và liquidation_price conditions nếu chúng thuộc deep-audit | BA/Tech Lead xác nhận: `effective_leverage > 4.5` và `liquidation_price within 5% of hlMarkPrice` có được check trong deep-audit không? | Open |

### 10.2 Dependencies

| # | Dependency | Loại | Ảnh hưởng đến test | Trạng thái |
|---|---|---|---|---|
| D1 | Margin thresholds (0.55/0.75) | External — OQ-EXBOT-06 (zen backtest) | Test giá trị cụ thể của threshold chưa được finalize | Open question (OQ-EXBOT-06) |
| D2 | `hedge_legs.last_audit_at` field — không tồn tại trong erd.md | Internal | I-05 — cần BA xác nhận field name đúng | Open question |
| D3 | "Consecutive critical" counting mechanism | Internal | I-03 — field/logic tracking chưa được định nghĩa | Open question |
| D4 | SAFE_MODE entry idempotency khi multiple conditions | Internal | I-07 — behavior chưa rõ | Open question |
| D5 | effective_leverage + liquidation_price check trong deep-audit scope | Internal | I-08 — có thể là missing coverage | Open question |

### 10.3 Audit Summary

#### Bảng điểm

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 17 | ⚠️ Partial | Inventory đầy đủ cho các function chính; field `last_audit_at` conflict với erd.md (I-05) gây traceability gap nhỏ; effective_leverage/liquidation_price conditions chưa rõ scope (I-08) |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 18 | ⚠️ Partial | BR-EXBOT-005 và BR-EXBOT-007 được áp dụng rõ; margin thresholds và consecutive critical tracking chưa định nghĩa trong UC (I-03); notification recipients chưa rõ (I-02) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 17 | ⚠️ Partial | 3 detection paths mô tả tốt; A1 skip logic không rõ (I-01); UC không mô tả margin warning notification và SAFE_MODE multi-trigger behavior (I-03, I-07) |
| 4 | Functional Integration & Data Consistency | 15 | 11 | ⚠️ Partial | HLRateLimitDO double-call được nhận biết; SAFE_MODE post-entry audit continuation không rõ (I-07); D1 field mismatch (I-05) |
| 5 | UC / Spec Documentation Quality Issues | 15 | 11 | ⚠️ Partial | Trigger section tốt (đây là UC duy nhất trong set có trigger rõ ràng). Double Postconditions (I-06). Field name conflict (I-05) là CROSS_SOURCE_CONFLICT nhẹ. |
| **Tổng** | | **100** | **74** | | |

**Auto-cap áp dụng:** Không có Blocker — không có auto-cap bắt buộc.

#### Verdict: **Conditionally Ready (74/100)**

Không có Blocker. UC-EXBOT-deep-audit có chất lượng tốt hơn đáng kể so với uc-hedge-sync (73) và uc-user-redeem (61): trigger được định nghĩa rõ (cron, không phải placeholder), luồng chính có Mermaid diagram, 3 detection paths được mô tả tường minh, BR-EXBOT-003 exception được ghi chú. Có thể dùng cho test design với điều kiện các Major issues được giải quyết song song.

#### Major issues cần giải quyết

1. **I-01**: Xác định chính xác tập hợp bước bị skip khi HL unreachable trong A1 — đặc biệt stop_trigger check (D1-only) và agent key check (D1-only).
2. **I-02**: Xác định notification recipients khi A3/A4 trigger SAFE_MODE — investor, admin, hay cả hai.
3. **I-03**: Mô tả margin transition notifications và "consecutive critical" tracking mechanism trong deep-audit context.
4. **I-05**: Xác nhận field name đúng — `hedge_legs.last_audit_at` hay `bot_runtime_state.last_deep_audit_at`?
5. **I-07**: Clarify behavior khi multiple SAFE_MODE conditions xảy ra trong cùng một audit cycle.
6. **I-08**: Xác nhận scope của `effective_leverage > 4.5` và `liquidation_price within 5%` — thuộc deep-audit hay hedge-sync?

#### Khuyến nghị

UC-EXBOT-deep-audit đủ tốt để bắt đầu viết test scenarios cho các happy paths và các detection paths đã được mô tả rõ (A2, A3, A4). Tuy nhiên trước khi viết test cases hoàn chỉnh, cần làm rõ I-01 (A1 skip scope) và I-05 (field name) vì hai issue này ảnh hưởng trực tiếp đến expected results. I-03 (margin notification + consecutive critical tracking) là quan trọng nhất về mặt nghiệp vụ vì liên quan đến SAFE_MODE trigger chain.

