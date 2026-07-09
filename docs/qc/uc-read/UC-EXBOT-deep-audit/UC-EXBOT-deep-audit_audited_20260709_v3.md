# UC-EXBOT-deep-audit: Periodic Deep Audit and Backstop SAFE_MODE Detection

**Document Title:** UC-EXBOT-deep-audit Readiness Review Report  
**Date Created:** 2026-06-30  
**Last Updated:** 2026-07-09  
**Author/Agent:** QC UC Read ExBot Agent  
**Version:** v3 (re-audit after BA responses 2026-07-04)

---

## Feature Brief - Tóm tắt nghiệp vụ

UC-EXBOT-deep-audit là một worker được kích hoạt theo lịch trình EventBridge Scheduler, thực hiện kiểm tra toàn diện trạng thái hedge của tất cả các bot đang active hoặc paused. Khác với light-check (chạy mỗi 5 phút, không gọi Hyperliquid API), deep-audit gọi Hyperliquid để lấy `clearinghouseState` và `marginSummary` nhằm phát hiện các vấn đề nghiêm trọng mà light-check không thể phát hiện: sai lệch hedge size giữa hệ thống và Hyperliquid, stop trigger bị kẹt quá 30 phút, hoặc stop replacement bị kẹt quá 60 giây. Khi phát hiện bất kỳ điều kiện nào trong số này, hệ thống sẽ kích hoạt SAFE_MODE.

Tần suất chạy mặc định là 6 giờ/lần. Khi `circuit_breakers.state != 'closed'` hoặc `margin_status` ở mức warning/critical, tần suất tăng lên 1 giờ/lần (high-risk mode). Điểm đặc biệt là deep-audit TIẾP TỤC chạy cho cả các bot đang paused — pause không được miễn audit.

Deep-audit là lớp phát hiện dự phòng (secondary backstop) cho `stop_replacing_started_at` overrun. Lớp phát hiện chính (primary) là light-check với chu kỳ 5 phút. Nếu light-check bị bỏ sót (ví dụ worker crash trước khi chạy), deep-audit sẽ phát hiện trong vòng 6 giờ (hoặc 1 giờ nếu ở high-risk mode).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-deep-audit | Periodic Deep Audit and Backstop SAFE_MODE Detection | draft (updated 2026-07-04) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-07-04 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `uc-deep-audit.md` | updated 2026-07-04 | UC under review — arc-migration: Cloudflare → AWS primitives | Primary source |
| `srs/spec.md` | updated 2026-07-04 | SRS baseline — FR-EXBOT-016, FR-EXBOT-033 | AWS arc-migration |
| `srs/states.md` | updated 2026-07-03 | State registry — paused bot note cho stuck marker (row 71) | Baseline |
| `srs/flows.md` | updated 2026-07-04 | Queue fan-out, hedge-sync, close flows | AWS arc-migration |
| `srs/erd.md` | updated 2026-07-04 | Aurora PostgreSQL ERD | AWS arc-migration |
| `frd.md` | updated 2026-07-04 | FRD — FR-EXBOT-016, FR-EXBOT-033, FR-EXBOT-050, FR-EXBOT-060 | AWS arc-migration |
| `us-005.md` | 2026-07-04 | User Story — light-check no HL | Linked story |
| `us-008.md` | 2026-06-12 | User Story — circuit breaker | Linked story |
| `us-010.md` | 2026-06-29 | User Story — margin warning SAFE_MODE | Linked story |
| `message-list.md` | 2026-07-01 | E-EXBOT-019, E-EXBOT-020 definitions | E-codes confirmed |
| `qc-responses-2026-07-04.md` | 2026-07-09 | BA responses to Q-DA-03, Q-DA-04, Q-DA-06, Q-DA-07 | BA confirmed |
| `common-rules.md` | NOT FOUND | spec.md §4 Business Rules | BR-EXBOT-* defined inline in spec |

| Nguồn cập nhật | Ngày | Thay đổi |
|---|---|---|
| BA arc-migration | 2026-07-04 | UC + SRS + flows + erd + frd: Cloudflare → AWS equivalents (D1→Aurora PostgreSQL, HLRateLimitDO→HL Rate Limiter (ElastiCache Redis), Cron scheduler→EventBridge Scheduler) |
| message-list.md | 2026-07-01 | E-EXBOT-019, E-EXBOT-020 added |
| states.md | 2026-07-03 | Row 71 updated với stuck marker note cho paused bots |
| qc-notes-temp.md | 2026-07-02 | BA trả lời Q-DA-01, Q-DA-02 |
| BA responses | 2026-07-09 | Q-DA-03, Q-DA-04, Q-DA-06, Q-DA-07 resolved via qc-responses-2026-07-04.md |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-deep-audit tồn tại để cung cấp một lớp kiểm tra dự phòng (backstop) cho trạng thái an toàn của ExBot. Trong khi light-check (FR-EXBOT-012) là lớp phát hiện nhanh chạy mỗi 5 phút với zero HL API call, deep-audit là lớp kiểm tra toàn diện chạy định kỳ mỗi 6 giờ (hoặc 1 giờ khi high-risk) sử dụng Hyperliquid API để xác nhận hedge position thực sự khớp với trạng thái trong Aurora PostgreSQL.

Hai detection path chính: (1) reconcile mismatch — phát hiện khi actual short size trên Hyperliquid khác với `last_known_hl_short_size` trong Aurora PostgreSQL; (2) stuck markers — phát hiện khi `stop_trigger_crossed_at` hoặc `stop_replacing_started_at` đã được set nhưng không được giải quyết trong thời gian cho phép (30 phút và 60 giây tương ứng).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| EventBridge Scheduler-triggered deep-audit worker | Worker được kích hoạt bởi EventBridge Scheduler, duyệt qua tất cả bot active/paused | UC §2 Preconditions |
| clearinghouseState reconcile | Gọi HL API lấy actual short size, so sánh với Aurora PostgreSQL `last_known_hl_short_size` | UC Step 3; FR-EXBOT-016 |
| stop_trigger_crossed_at stuck detection | Phát hiện marker đã set > 30 phút | UC Step 4; FR-EXBOT-033 |
| stop_replacing_started_at stuck detection | Phát hiện marker đã set > 60 giây | UC Step 5; FR-EXBOT-033 |
| marginStatus update | Gọi HL marginSummary, cập nhật `hedge_legs.margin_status` | UC Step 6; FR-EXBOT-016 |
| SAFE_MODE entry | Kích hoạt SAFE_MODE khi phát hiện bất kỳ condition nào | UC §5 Postconditions; FR-EXBOT-050 |
| Cadence switching | Chuyển 6h → 1h khi `circuit_breakers.state != 'closed'` hoặc `margin_status` warning/critical | UC §2 Preconditions; FR-EXBOT-016 |
| Paused bot audit — bao gồm stuck marker detection | Deep-audit chạy cho cả paused bot, bao gồm stuck marker detection (steps 4–5). Nếu triggered, bot chuyển `paused → safe_mode`. | UC A2; FR-EXBOT-005; states.md row 71 |
| HL Rate Limiter integration | Deep-audit calls HL via HL Rate Limiter (ElastiCache Redis) với weight=2 | UC Step 2; FR-EXBOT-091 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Light-check primary detection cho stop_replacing_started_at | Primary detection thuộc UC-EXBOT-light-check; deep-audit chỉ là secondary backstop | Tester cần hiểu 2-layer detection nhưng test deep-audit chỉ cần verify backstop path |
| Stop placement/replacement logic (INV-STOP protocol) | Thuộc UC-EXBOT-hedge-sync; deep-audit chỉ phát hiện khi stop bị kẹt | Test deep-audit không cần test INV-STOP internals |
| Auto-recovery from SAFE_MODE | Thuộc FR-EXBOT-050 recovery section; deep-audit chỉ trigger entry, không handle recovery | Test deep-audit chỉ verify entry trigger |
| Bot start/lifecycle initialization | Thuộc UC-EXBOT-bot-start | Không ảnh hưởng |
| HL Rate Limiter (Redis) + User Lock (Redis Redlock) interaction | OQ-EXBOT-15: xác định weight consumption ordering. **Not applicable cho v1** — deep-audit v1 là stub, không gọi HL thật. | Tech Lead decision — không ảnh hưởng deep-audit |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Deep-Audit Worker) | Primary | EventBridge Scheduler-triggered worker; đọc Aurora PostgreSQL, gọi HL, ghi Aurora PostgreSQL, trigger SAFE_MODE | Worker chỉ thực hiện read HL + update Aurora PostgreSQL; không thực hiện hedge mutation | UC §1 Actors |
| Aurora PostgreSQL | System | Nguồn dữ liệu trạng thái bot; đích ghi của audit results | — | UC Step 1, 3, 4, 5, 6, 7 |
| Hyperliquid (HL) | System | Nguồn truth cho hedge position và margin data | Gọi qua HL Rate Limiter (ElastiCache Redis) với weight=2 cho clearinghouseState và marginSummary | UC Step 2, 6 |
| Notification Queue | System | Nhận notification message khi phát hiện anomaly | — | UC A3, A4 |
| HL Rate Limiter (ElastiCache Redis) | System | Rate limiter ngăn deep-audit vượt HL API weight budget (800 weight/min) | Deep-audit gọi với weight=2; BR-EXBOT-003 exception applies | UC Step 2; FR-EXBOT-091 |

**Nhận xét readiness:**
Actor và role đã được định nghĩa rõ ràng. Không có UI actor — deep-audit là hoàn toàn backend/cron-driven. Mối quan hệ giữa Deep-Audit Worker và Hyperliquid qua HL Rate Limiter (ElastiCache Redis) đã được UC chỉ ra (BR-EXBOT-003 exception).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | EventBridge Scheduler fire theo schedule: 6 giờ (normal) hoặc 1 giờ (high-risk) | Yes | UC §2 Preconditions |
| 2 | Tồn tại ít nhất một bot với `status IN ('active', 'paused')` trong Aurora PostgreSQL | Yes (để worker có việc để làm) | UC §2 Preconditions |
| 3 | HL Rate Limiter (ElastiCache Redis) cho phép gọi HL API (weight budget còn) | Yes (cho Steps 2, 3, 4, 6) | UC A1; FR-EXBOT-091 |
| 4 | `circuit_breakers.state` và `hedge_legs.margin_status` có giá trị hợp lệ trong Aurora PostgreSQL | Yes (để evaluate cadence switching) | UC §2 Preconditions |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Mismatch detected (Step 3) | Aurora PostgreSQL record mismatch; `last_known_hl_short_size` updated to actual HL size; bot enters SAFE_MODE; admin notification queued | UC A3 |
| stop_trigger_crossed_at stuck > 30min (Step 4) | Bot enters SAFE_MODE; admin escalation notification queued với reason "stop_trigger_crossed_at stuck > 30min" (E-EXBOT-019) | UC A4 |
| stop_replacing_started_at stuck > 60s (Step 5) | Bot enters SAFE_MODE; admin escalation notification queued với reason "stop_replacing_started_at stuck > 60s" (E-EXBOT-020) | UC A4 |
| marginSummary fetched (Step 6) | `hedge_legs.margin_status` updated from fresh HL data | UC Step 6; FR-EXBOT-016 |
| Audit completed successfully | `hedge_legs.last_audit_at = now`; `queue_idempotency` row `state='succeeded'` | UC Step 7, 8 |
| HL unreachable (A1) | Bot ở lại trạng thái hiện tại; `next_deep_audit_at` updated to `now + 1h`; retry-pending state recorded | UC A1 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Tên chức năng / luồng: Deep-Audit Cycle

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Deep-Audit Worker | EventBridge Scheduler triggers worker | Worker reads bot state from Aurora PostgreSQL: `bots.status`, `bots.lifecycle_state`, `hedge_legs`, `circuit_breakers.state`, `margin_status` | — | — | UC Step 1 |
| 2 | Deep-Audit Worker | Gọi HL `clearinghouseState` | Worker calls HL via HL Rate Limiter (ElastiCache Redis) (weight=2); fetches actual short size | **A1 (HL unreachable):** Rate Limiter returns `{allowed: false}` hoặc HL returns 5xx → skip Steps 2,3,4,6,7; update `next_deep_audit_at` to `now + 1h`; enqueue notification | — | UC Step 2; FR-EXBOT-091 |
| 3 | Deep-Audit Worker | Verify hedge size match | Worker compares actual short size from HL với `hedge_legs.last_known_hl_short_size`; **always updates** `last_known_hl_short_size = actual HL size` and `last_hl_reconcile_at = now` before any decision | **A3 (mismatch):** actual ≠ last_known → record mismatch in Aurora PostgreSQL; trigger SAFE_MODE; enqueue admin notification với size delta | — | UC Step 3 |
| 4 | Deep-Audit Worker | Check `stop_trigger_crossed_at` stuck | Worker evaluates: `stop_trigger_crossed_at IS NOT NULL AND (now − stop_trigger_crossed_at) > 30 min` | **A4 (stuck):** condition true → trigger SAFE_MODE; enqueue admin escalation với timestamp và reason (E-EXBOT-019) | — | UC Step 4; FR-EXBOT-033 |
| 5 | Deep-Audit Worker | Check `stop_replacing_started_at` stuck | Worker evaluates: `stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60s` | **A4 (stuck):** condition true → trigger SAFE_MODE; enqueue admin escalation với timestamp và reason (E-EXBOT-020) | — | UC Step 5; FR-EXBOT-033 |
| 6 | Deep-Audit Worker | Fetch marginSummary | Worker calls HL `marginSummary`; updates `hedge_legs.margin_status` from fresh HL data | A1 (HL unreachable): step skipped | — | UC Step 6; FR-EXBOT-016 |
| 7 | Deep-Audit Worker | Update audit timestamp | Worker sets `hedge_legs.last_audit_at = now`; `next_deep_audit_at = now + 6h` (normal) hoặc `now + 1h` (high-risk) | — | — | UC Step 7 |
| 8 | Deep-Audit Worker | Idempotency marker | Worker inserts `queue_idempotency` row: `state='succeeded'` | — | — | UC Step 8 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| HL weight budget | Deep-audit calls HL với weight=2; BR-EXBOT-003 (HL weight = 0) không apply cho deep-audit | Yes | Gọi HL thành công | A1: HL Rate Limiter returns `{allowed: false}` → skip HL steps, update `next_deep_audit_at` to `now + 1h` | UC BR; FR-EXBOT-091 |
| Paused bot inclusion | Deep-audit chạy cho cả paused bot — pause không miễn audit | Yes | Worker vẫn thực hiện all detection paths (Steps 3–7) | N/A — không có exception | UC A2; FR-EXBOT-005 |
| Cadence switching logic | Worker update `bots.next_deep_audit_at`: Normal → `now + 6h`; HL unreachable / high-risk → `now + 1h`. Bot-scan query `WHERE status='active' AND next_deep_audit_at <= now` mỗi phút. | Yes | Worker chạy ở high-risk schedule | N/A | UC §2 Preconditions; FR-EXBOT-016 |
| `stop_trigger_crossed_at` write-once | BR-EXBOT-005: `stop_trigger_crossed_at` chỉ được set nếu hiện tại là NULL (guard) — deep-audit không set, chỉ check | N/A | Deep-audit chỉ kiểm tra timestamp đã set | N/A | BR-EXBOT-005; FR-EXBOT-033 |
| SAFE_MODE entry condition | UC định nghĩa 3 entry paths: mismatch (A3), `stop_trigger_crossed_at` stuck > 30min (A4, E-EXBOT-019), `stop_replacing_started_at` stuck > 60s (A4, E-EXBOT-020) | Yes | Bot enters `safe_mode`; admin notified | N/A | FR-EXBOT-050 |
| Secondary backstop role | Deep-audit là secondary detection cho `stop_replacing_started_at`; primary là light-check (≤5 min) | Yes (design intent) | Nếu light-check miss, deep-audit catch trong vòng 6h/1h | Light-check primary miss → max detection delay = 6h (normal) hoặc 1h (high-risk) | FR-EXBOT-033 |
| Bot scope: active + paused | UC §2 chỉ định `status IN ('active','paused')` | Yes | Worker đọc và xử lý các bot này | Bot closed/safe_mode/error/idle/preflight/etc. không được deep-audit (states.md registry shows "skip") | UC §2; states.md |
| `last_known_hl_short_size` update on mismatch | Worker update `bot_runtime_state.last_known_hl_short_size = actual HL size` và `last_hl_reconcile_at = now` **bất kể match hay mismatch** — trước khi trigger SAFE_MODE. Ngăn potential loop trong subsequent audits. | Yes | Field luôn sync với HL truth | N/A — worker luôn update | FR-EXBOT-016; confirmed 2026-07-09 |

#### C. Thông báo, lỗi và phản hồi hệ thống (API response / state change / event / message)

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Mismatch detected | State transition + Admin notification | Bot transitions to `safe_mode`; admin notification với size delta (actual − expected); `last_known_hl_short_size` updated to actual | E-EXBOT-011 (reconcile mismatch) | UC A3; spec.md E-EXBOT-011 |
| `stop_trigger_crossed_at` stuck | Admin escalation notification | E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." | E-EXBOT-019 | UC A4; message-list.md |
| `stop_replacing_started_at` stuck | Admin escalation notification | E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required." | E-EXBOT-020 | UC A4; message-list.md |
| HL API unreachable | State change + notification | `next_deep_audit_at` updated to `now + 1h`; retry-pending state recorded; notification "Hyperliquid API unreachable" | E-EXBOT-008 | UC A1; spec.md E-EXBOT-008 |
| Idempotency row | Aurora PostgreSQL insert | `queue_idempotency.key` = unique per audit run; `state='succeeded'` | FR-EXBOT-011 | UC Step 8 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Mismatch detected → SAFE_MODE entry | UC-EXBOT-bot-safe-close | SAFE_MODE entry trigger `bot_safe_close` flow (FR-EXBOT-072) | Tester cần verify `bot_safe_close` được trigger đúng sau SAFE_MODE entry | FR-EXBOT-050; FR-EXBOT-072 |
| Margin status update | US-EXBOT-010; FR-EXBOT-060 | Deep-audit update `hedge_legs.margin_status` → trigger warning/critical notification hoặc SAFE_MODE | Tester cần verify `margin_status` được update đúng từ HL `marginSummary` | FR-EXBOT-016; FR-EXBOT-060 |
| `stop_replacing_started_at` stuck → SAFE_MODE | UC-EXBOT-hedge-sync (stop replacement) | Backstop cho INV-STOP protocol failure | Tester cần hiểu: primary detection = light-check (≤5 min), secondary = deep-audit (≤6h) | FR-EXBOT-033 |
| Paused bot audit — bao gồm stuck marker detection | UC-EXBOT-pause-resume | Pause chỉ suppress light-check và hedge-sync, không suppress deep-audit; stuck marker detection (steps 4–5) vẫn chạy cho paused bot; nếu triggered, bot chuyển `paused → safe_mode` | Tester cần verify deep-audit vẫn chạy và check stuck markers cho paused bot; nếu triggered, bot chuyển `paused → safe_mode` | FR-EXBOT-005; states.md row 71 |
| Cadence switching to 1h | Light-check worker; circuit breaker | High-risk mode được trigger bởi `circuit_breakers.state` hoặc `margin_status`; Lambda ghi `bots.next_deep_audit_at` | Tester cần verify `next_deep_audit_at` được update đúng khi conditions thay đổi | FR-EXBOT-016 |
| `last_audit_at` update | Bot monitoring / status display | Investor và admin có thể xem last audit time | Tester cần verify field được update sau mỗi audit cycle | FR-EXBOT-016 |
| Queue idempotency | Queue system | Prevent duplicate audit processing | Tester cần verify UNIQUE constraint hoạt động đúng | FR-EXBOT-011 |
| `last_known_hl_short_size` sync | Recovery from SAFE_MODE | Worker luôn update `last_known_hl_short_size = actual HL size` bất kể match/mismatch — ngăn potential loop trong subsequent audits | Tester cần verify field updated ngay cả khi mismatch detected | FR-EXBOT-016; confirmed 2026-07-09 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-DA-01 | Happy path — audit completes without issues | Bot với `status='active'`, không có mismatch, không có stuck markers | Deep-audit worker processes bot | `hedge_legs.last_audit_at = now`; `margin_status` updated from HL; `queue_idempotency` `state='succeeded'` | UC Steps 1,6,7,8; FR-EXBOT-016 |
| AC-DA-02 | Mismatch detection → SAFE_MODE | Bot active; actual short size trên HL ≠ `hedge_legs.last_known_hl_short_size` | Deep-audit worker verifies size | Bot enters `safe_mode`; Aurora PostgreSQL records mismatch; `last_known_hl_short_size` updated to actual HL size; admin notification với size delta enqueued | UC A3; FR-EXBOT-050; E-EXBOT-011 |
| AC-DA-03 | `stop_trigger_crossed_at` stuck > 30min → SAFE_MODE | Bot active; `hedge_legs.stop_trigger_crossed_at` set và age > 30 min | Deep-audit worker checks timestamp | Bot enters `safe_mode`; admin escalation notification "stop_trigger_crossed_at stuck > 30min" (E-EXBOT-019) enqueued | UC A4; FR-EXBOT-033; FR-EXBOT-050 |
| AC-DA-04 | `stop_replacing_started_at` stuck > 60s → SAFE_MODE | Bot active; `hedge_legs.stop_replacing_started_at` set và age > 60s | Deep-audit worker checks timestamp | Bot enters `safe_mode`; admin escalation notification "stop_replacing_started_at stuck > 60s" (E-EXBOT-020) enqueued | UC A4; FR-EXBOT-033; FR-EXBOT-050 |
| AC-DA-05 | HL unreachable → graceful degradation | HL Rate Limiter returns `{allowed: false}` hoặc HL API returns 5xx | Deep-audit worker attempts HL call | Steps 2,3,4,6,7 skipped; `next_deep_audit_at` updated to `now + 1h`; notification "Hyperliquid API unreachable" (E-EXBOT-008) enqueued; retry-pending state recorded | UC A1; E-EXBOT-008 |
| AC-DA-06 | Paused bot still audited | Bot với `status='paused'` | Deep-audit EventBridge Scheduler fires | All detection paths (Steps 3–7) execute normally; pause does NOT skip deep-audit; stuck markers checked; if triggered, bot transitions `paused → safe_mode` | UC A2; FR-EXBOT-005 |
| AC-DA-07 | High-risk cadence switching | `circuit_breakers.state='open'` OR `margin_status='warning'` OR `margin_status='critical'` | Worker evaluates conditions | `next_deep_audit_at` updated to `now + 1h` | UC §2 Preconditions; FR-EXBOT-016 |
| AC-DA-08 | Idempotency prevents duplicate | Queue delivers same `message_id` twice | Worker processes first delivery | First: `state='started'` → processing → `state='succeeded'`; Second: UNIQUE conflict → return immediately | FR-EXBOT-011 |
| AC-DA-09 | `last_known_hl_short_size` always synced | Bot active; deep-audit detects mismatch | Worker compares and updates | `last_known_hl_short_size` updated to actual HL size **bất kể match hay mismatch**; `last_hl_reconcile_at = now`; subsequent audits will not re-detect same mismatch | FR-EXBOT-016; confirmed 2026-07-09 |
| AC-DA-10 | Phase A test deferred | v1 deep-audit là stub | `observeDeepAudit()` stub called | No HL API calls in v1; Phase A tests for deep-audit deferred to v1.1 | BA confirmed 2026-07-09 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Deep-audit chạy mỗi 6h/1h, không phải real-time. Không có throughput requirement cụ thể cho deep-audit trong NFR. | Tester không cần verify throughput như light-check (10k bots/5min) | NFR-EXBOT-001 chỉ áp dụng light-check |
| Rate Limit | Deep-audit sử dụng HL API weight = 2. BR-EXBOT-003 (HL weight=0) không apply — deep-audit có weight=2. **Note:** v1 deep-audit là stub, không gọi HL thật. | Phase A test không verify HL Rate Limiter. Phase A deep-audit tests deferred sang v1.1. | FR-EXBOT-091; BR-EXBOT-003 exception in UC BR |
| Idempotency | `queue_idempotency` đảm bảo duplicate message không được xử lý 2 lần | Tester cần verify UNIQUE constraint behavior khi message redelivered | FR-EXBOT-011; NFR-EXBOT-007 |
| Precision | Margin calculation và timestamp comparison phải dùng BigDecimal/time comparison đúng | Tester cần verify timestamp comparison logic (30 min, 60s) không bị float precision issue | NFR-EXBOT-008 (BigDecimal) |
| Reliability / Resilience | HL unreachable → graceful degradation, không crash worker | Tester cần verify A1 path hoạt động đúng khi HL unavailable | E-EXBOT-008 |
| Audit / Logging | `last_audit_at` updated; notification queued; mismatch recorded | Tester cần verify các field này được ghi sau mỗi cycle | FR-EXBOT-016 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q-DA-01 | ~~High~~ **Resolved** | ~~MISSING_INFO~~ | UC A4; spec.md §5; frd.md §4.6 | ~~Thiếu E-code và message content cho 2 stuck marker notifications~~ | ~~Tester không thể verify notification content~~ | ~~BA~~ | **Resolved (2026-07-01)** |
| Q-DA-02 | ~~Medium~~ **Resolved** | ~~UNCLEAR_INFO~~ | UC A2; states.md row 71 | ~~Không verify stuck marker detection cho paused bot~~ | ~~Tester cần biết stuck marker detection có hoạt động cho paused bot không~~ | ~~QC Lead~~ | **Resolved (2026-07-01)** |
| Q-DA-03 | ~~Medium~~ **Resolved** | ~~MISSING_INFO~~ | UC Step 1; NFR-EXBOT-012 | ~~Shard iteration strategy cho AWS Lambda deep-audit worker: không rõ Lambda đọc tất cả shards một lần rồi xử lý tuần tự, hay có một EventBridge Scheduler trigger per shard.~~ | ~~Multi-shard test design cho Phase B (4 shards) phụ thuộc vào shard iteration strategy. Phase A test không bị ảnh hưởng.~~ | ~~Tech Lead~~ | **Resolved (2026-07-09):** Kiến trúc v1: bot-scan fan-out per-bot SQS → deep-audit Lambda xử lý 1 `botId` per invocation. Phase A test defer sang v1.1. |
| Q-DA-04 | ~~Low~~ **Resolved** | ~~UNCLEAR_INFO~~ | UC A1; erd.md | ~~Cadence switching mechanism (6h→1h) được ghi vào đâu trong Aurora PostgreSQL chưa rõ.~~ | ~~Tester cần verify cadence switching mechanism để design test đúng behavior~~ | ~~Tech Lead~~ | **Resolved (2026-07-09):** Lambda ghi `bots.next_deep_audit_at`; EventBridge không tự switch schedule. v1.1 implementation. |
| Q-DA-05 | ~~Major~~ **Resolved** | ~~CROSS_SOURCE_CONFLICT~~ | UC; spec.md; flows.md; erd.md | ~~Cross-source conflict: UC và spec sử dụng "D1" và "HLRateLimitDO" (Cloudflare primitives) trong khi project context chuyển sang AWS architecture.~~ | ~~Tester có thể bị nhầm lẫn bởi mixed naming convention.~~ | ~~BA~~ | **Resolved (2026-07-04):** arc-migration update tất cả files để sử dụng AWS equivalents. |
| Q-DA-06 | ~~Medium~~ **Resolved** | ~~MISSING_INFO~~ | UC Step 2; FR-EXBOT-091; OQ-EXBOT-15 | ~~Deep-audit Step 2 gọi HL qua HL Rate Limiter với weight=2. OQ-EXBOT-15 xác định Tech Lead cần xác định: HL Rate Limiter weight consumption nên được thực hiện trước hay sau khi acquire Redis Redlock?~~ | ~~Tech Lead decision về rate limiter ordering ảnh hưởng đến system design tổng thể.~~ | ~~Tech Lead~~ | **Resolved (2026-07-09):** Not applicable cho v1 — deep-audit v1 là stub, không gọi HL thật. OQ-EXBOT-15 chỉ ảnh hưởng hedge-sync. |
| Q-DA-07 | ~~Low~~ **Resolved** | ~~MISSING_INFO~~ | UC Step 3; spec.md FR-EXBOT-016 | ~~UC Step 3 mismatch detection không mô tả rõ `last_known_hl_short_size` update behavior sau mismatch.~~ | ~~Tester cần biết state của `last_known_hl_short_size` sau mismatch detection để design recovery test đúng.~~ | ~~Tech Lead / BA~~ | **Resolved (2026-07-09):** Worker update `last_known_hl_short_size = actual HL size` bất kể match/mismatch, trước khi trigger SAFE_MODE. v1.1 planned. |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| FR-EXBOT-016 (Deep-Audit) | FR requirement | UC-EXBOT-deep-audit implements this FR. Nếu FR thay đổi, UC phải update. | BA | Draft |
| FR-EXBOT-033 (SAFE_MODE on stuck stop) | FR requirement | UC-EXBOT-deep-audit là secondary detection cho FR-EXBOT-033. Không có primary detection trong UC này. | BA | Draft |
| FR-EXBOT-050 (SAFE_MODE triggers) | FR requirement | Deep-audit triggers 3 trong 7 SAFE_MODE conditions. | BA | Draft |
| FR-EXBOT-060 (Margin status thresholds) | FR requirement | Deep-audit update `margin_status` từ HL `marginSummary`. Threshold values (0.55/0.75) pending Phase 0 backtest (OQ-EXBOT-06). | zen / BA | Open |
| HL Rate Limiter (ElastiCache Redis) (FR-EXBOT-091) | Infrastructure | Deep-audit v1 là stub, không sử dụng HL Rate Limiter. v1.1 sẽ integrate. | Tech Lead | Draft (v1.1) |
| `queue_idempotency` (FR-EXBOT-011) | Queue infrastructure | Deep-audit sử dụng idempotency pattern. | Tech Lead | Draft |
| OQ-EXBOT-06 (margin thresholds) | Open Question | 0.55/0.75 thresholds pending finalization | zen | Open |
| OQ-EXBOT-15 (HL Rate Limiter ordering) | Open Question | Weight consumption ordering — Tech Lead decision. **Not applicable cho deep-audit v1.** | Tech Lead | Open (not applicable) |
| common-rules.md | Common rule file | spec.md ghi "resolve cited BR-* to verbatim text from common-rules.md" — **common-rules.md không tồn tại** trong docs/BA. BR-EXBOT-* rules được định nghĩa inline trong spec.md §4 Business Rules. | BA | N/A (BR defined in spec) |

---

## 11. Issue Register (Updated 2026-07-09 - Re-audit v3)

### Issue Summary

| Issue ID | Type | Severity | Affected Area | Finding | Status |
|---|---|---|---|---|---|
| I-DA-01 | ~~MISSING_INFO~~ **Resolved** | ~~Major~~ **Resolved** | Area 2: Data Object Validation & Messages | ~~Admin notification messages cho stuck marker cases không được định nghĩa~~ **Đã resolved:** E-EXBOT-019 và E-EXBOT-020 đã được thêm vào message-list.md (2026-07-01). UC A4 đã updated với E-code references. | **Resolved** |
| I-DA-02 | ~~UNCLEAR_INFO~~ **Resolved** | ~~Medium~~ **Resolved** | Area 2: Business Rules | ~~Không verify stopped marker detection hoạt động đúng cho paused bot~~ **Đã resolved:** UC A2 và states.md row 71 đã updated. Stuck marker detection chạy cho paused bot; transition là `paused → safe_mode`. | **Resolved** |
| I-DA-03 | ~~MISSING_INFO~~ **Resolved** | ~~Medium~~ **Resolved** | Area 1: Function/Operation Inventory | ~~Shard iteration strategy cho AWS Lambda deep-audit worker không rõ.~~ **Đã resolved:** Kiến trúc v1: EventBridge trigger bot-scan → fan-out per-bot SQS → deep-audit Lambda xử lý 1 `botId` per invocation. Phase A test defer sang v1.1. | **Resolved (2026-07-09)** |
| I-DA-04 | ~~UNCLEAR_INFO~~ **Resolved** | ~~Low~~ **Resolved** | Area 2: Business Rules | ~~Cadence switching mechanism (6h→1h) được ghi vào đâu trong Aurora PostgreSQL chưa rõ.~~ **Đã resolved:** Lambda ghi `bots.next_deep_audit_at`. EventBridge không tự switch schedule. | **Resolved (2026-07-09)** |
| I-DA-05 | ~~CROSS_SOURCE_CONFLICT~~ **Resolved** | ~~Major~~ **Resolved** | Area 1: Architecture naming | ~~UC và spec sử dụng "D1" và "HLRateLimitDO" (Cloudflare primitives) trong khi project context chuyển sang AWS.~~ **Đã resolved:** BA 2026-07-04 arc-migration update tất cả files để sử dụng AWS equivalents. | **Resolved** |
| I-DA-06 | ~~MISSING_INFO~~ **Resolved** | ~~Medium~~ **Resolved** | Area 2: Business Rules | ~~OQ-EXBOT-15 (HL Rate Limiter + Redis Redlock ordering) vẫn Open trong spec.md §9.~~ **Đã resolved:** Not applicable cho v1 — deep-audit v1 là stub, không gọi HL thật. OQ-EXBOT-15 chỉ ảnh hưởng hedge-sync. | **Resolved (2026-07-09)** |
| I-DA-07 | ~~MISSING_INFO~~ **Resolved** | ~~Low~~ **Resolved** | Area 3: Functional Logic | ~~UC Step 3 mismatch detection không mô tả rõ `last_known_hl_short_size` update behavior sau mismatch.~~ **Đã resolved:** Worker update `last_known_hl_short_size = actual HL size` bất kể match/mismatch, trước khi trigger SAFE_MODE. v1.1 planned. | **Resolved (2026-07-09)** |

### Issue Details

**I-DA-01 — ~~MISSING_INFO~~ **RESOLVED** (Major)**

**Affected Area:** Area 2 (Data Object / State Attributes, Business Rules, Validations & Messages)

**Finding:** ~~UC A4 mô tả "enqueue admin escalation notification with timestamp and reason ('stop_trigger_crossed_at stuck > 30min' or 'stop_replacing_started_at stuck > 60s')" nhưng **không có nội dung message chính xác**.~~ **Đã resolved:** E-EXBOT-019 và E-EXBOT-020 đã được thêm vào message-list.md (2026-07-01). UC A4 đã updated với E-code references. E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required."

**Impact on tester understanding:** ~~Tester không thể verify expected notification content trong test case vì message không được define.~~ **Resolved — Tester có thể verify notification content với E-EXBOT-019 và E-EXBOT-020.**

**Suggested question/fix:** ~~BA cần định nghĩa: (1) E-code riêng cho mỗi stuck case (ví dụ: E-EXBOT-018, E-EXBOT-019), (2) Exact notification message content cho admin escalation.~~ **Resolved.**

**Status:** ~~Open~~ **Resolved**

---

**I-DA-02 — ~~UNCLEAR_INFO~~ **RESOLVED** (Medium)**

**Affected Area:** Area 2 (Data Object / State Attributes, Business Rules, Validations & Messages)

**Finding:** ~~UC A1 nói "update cadence to high-risk interval (1 hour)" nhưng không chỉ ra worker ghi thông tin này ở đâu.~~ **Đã resolved:** Tech Lead/BA xác nhận đây là Tech Lead decision về implementation. Phase A test không bị ảnh hưởng.

**Impact on tester understanding:** ~~Tester không biết cadence switching được implement bằng cách nào.~~ **Resolved — Phase A test không phụ thuộc vào implementation details.**

**Suggested question/fix:** ~~Tech Lead xác nhận: (1) Worker update `bots.next_deep_audit_at` khi cadence switch, hay (2) Cron worker tự switch schedule.~~ **Resolved.**

**Status:** ~~Open~~ **Resolved (Tech Lead decision)**

---

**I-DA-03 — ~~MISSING_INFO~~ **RESOLVED** (Medium)**

**Affected Area:** Area 1 (Function / Operation & Data Object Inventory)

**Finding:** ~~UC Step 1 đọc tất cả bots nhưng không specify shard iteration strategy. Deep-audit UC không nói rõ worker scan tất cả shards trong một execution hay có một cron trigger per shard.~~ **Đã resolved (2026-07-09):** Kiến trúc v1: EventBridge trigger bot-scan (`rate: 1 minute`) → bot-scan query `bots WHERE status='active'` → fan-out per-bot SQS message → deep-audit Lambda xử lý 1 `botId` duy nhất per invocation. Shard iteration là concern của bot-scan layer, không phải deep-audit. **Phase A test cho deep-audit defer sang v1.1.**

**Impact on tester understanding:** ~~Tester không thể design test cho multi-shard scenario (Phase B).~~ **Resolved — Phase A test defer sang v1.1; v1 deep-audit là stub.**

**Suggested question/fix:** ~~Tech Lead xác nhận shard iteration strategy.~~ **Resolved — BA confirmed 2026-07-09.**

**Status:** ~~Open~~ **Resolved (2026-07-09)**

---

**I-DA-04 — ~~UNCLEAR_INFO~~ **RESOLVED** (Low)**

**Affected Area:** Area 2 (Data Object / State Attributes, Business Rules, Validations & Messages)

**Finding:** ~~UC A1 nói "update cadence to high-risk interval (1 hour)" khi HL unreachable nhưng không rõ Lambda worker có update `bots.next_deep_audit_at` field không, hay EventBridge Scheduler tự switch schedule dựa trên state query.~~ **Đã resolved (2026-07-09):** Cadence switching dùng **Cách A — Lambda ghi `bots.next_deep_audit_at`**: Normal completion → `now + 6h`; HL unreachable (A1) → `now + 1h`; High-risk condition → `now + 1h`. Bot-scan query `WHERE status='active' AND next_deep_audit_at <= now` mỗi phút. EventBridge không tự switch schedule. **Mechanism này là v1.1 implementation.**

**Impact on tester understanding:** ~~Tester cần verify cadence switching mechanism để design test đúng behavior.~~ **Resolved — Phase A test defer sang v1.1.**

**Suggested question/fix:** ~~Tech Lead xác nhận cadence switching mechanism.~~ **Resolved — BA confirmed 2026-07-09.**

**Status:** ~~Open~~ **Resolved (2026-07-09)**

---

**I-DA-05 — ~~CROSS_SOURCE_CONFLICT~~ **RESOLVED** (Major)**

**Affected Area:** Area 5 (UC / Spec Documentation Quality Issues)

**Finding:** ~~UC và spec sử dụng "D1" và "HLRateLimitDO" (Cloudflare primitives) trong khi project context chuyển sang AWS architecture.~~ **Đã resolved:** BA 2026-07-04 arc-migration update tất cả files để sử dụng AWS equivalents:
- D1 → Aurora PostgreSQL
- HLRateLimitDO → HL Rate Limiter (ElastiCache Redis)
- Cron scheduler → EventBridge Scheduler

**Impact on tester understanding:** ~~Tester có thể bị nhầm lẫn bởi mixed naming convention.~~ **Resolved — Tất cả files đã updated với AWS naming convention.**

**Suggested question/fix:** ~~BA update tất cả UC và SRS files để sử dụng AWS naming convention.~~ **Resolved (2026-07-04).**

**Status:** ~~Open~~ **Resolved**

---

**I-DA-06 — ~~MISSING_INFO~~ **RESOLVED** (Medium)**

**Affected Area:** Area 2 (Data Object / State Attributes, Business Rules, Validations & Messages)

**Finding:** ~~UC Step 2 gọi HL qua HL Rate Limiter (ElastiCache Redis) với weight=2. OQ-EXBOT-15 trong spec.md §9 vẫn chưa được resolved: "HL Rate Limiter weight consumption ordering?"~~ **Đã resolved (2026-07-09):** Deep-audit v1 không gọi HL thật — `observeDeepAudit()` là stub, không có rate limiter hay Redlock implementation. Với v1.1: deep-audit không dùng Redlock (không có hedge mutation) nên không có ordering question — chỉ cần consume weight trước khi gọi HL. **OQ-EXBOT-15 chỉ ảnh hưởng hedge-sync, không ảnh hưởng deep-audit.**

**Impact on tester understanding:** ~~Tester không bị ảnh hưởng trực tiếp cho Phase A deep-audit tests.~~ **Resolved — Phase A deep-audit tests deferred sang v1.1.**

**Suggested question/fix:** ~~Tech Lead xác nhận OQ-EXBOT-15.~~ **Resolved — Not applicable cho deep-audit v1.**

**Status:** ~~Open~~ **Resolved (2026-07-09)**

---

**I-DA-07 — ~~MISSING_INFO~~ **RESOLVED** (Low)**

**Affected Area:** Area 3 (Functional Logic & Workflow Decomposition)

**Finding:** ~~UC Step 3 mismatch detection không mô tả rõ `last_known_hl_short_size` update behavior sau mismatch.~~ **Đã resolved (2026-07-09):** Worker update `bot_runtime_state.last_known_hl_short_size = actual HL size` và `last_hl_reconcile_at = now` **bất kể match hay mismatch** — trước khi trigger SAFE_MODE. UC đã được update (Step 3 + A3). Behavior này là v1.1 planned, consistent với pattern `§13.3`. **Recovery test:** Verify `bot_runtime_state.last_known_hl_short_size = actual HL size` trong DB ngay sau mismatch detection, trước khi test recovery path.

**Impact on tester understanding:** ~~Tester không biết state của `last_known_hl_short_size` sau mismatch detection để design recovery test đúng.~~ **Resolved — Tester biết field luôn được sync.**

**Suggested question/fix:** ~~Tech Lead xác nhận `last_known_hl_short_size` update behavior.~~ **Resolved — BA confirmed 2026-07-09.**

**Status:** ~~Open~~ **Resolved (2026-07-09)**

---

### Scoring Summary (Updated 2026-07-09 - Re-audit v3)

| Scoring Area | Max Points | Score v1 | Score v2 | Score v3 | Delta v2→v3 | Status |
|---|---|---|---|---|---|---|
| Area 1: Function / Operation & Data Object Inventory | 20 | 18/20 ✅ Clear | 18/20 ⚠️ Partial | **20/20 ✅ Clear** | +2 | I-DA-03 Resolved |
| Area 2: Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 23/25 ✅ Clear | 21/25 ⚠️ Partial | **25/25 ✅ Clear** | +4 | I-DA-04, I-DA-06 Resolved |
| Area 3: Functional Logic & Workflow Decomposition | 25 | 23/25 ✅ Clear | 22/25 ⚠️ Partial | **25/25 ✅ Clear** | +3 | I-DA-07 Resolved |
| Area 4: Functional Integration & Data Consistency | 15 | 13/15 ✅ Clear | 13/15 ✅ Clear | **13/15 ✅ Clear** | 0 | No new issues |
| Area 5: UC / Spec Documentation Quality Issues | 15 | 13/15 ✅ Clear | 15/15 ✅ Clear | **15/15 ✅ Clear** | 0 | I-DA-05 Resolved (v2) |
| **Total** | **100** | **90/100** | **89/100** | **98/100** | **+9** | — |
| **Verdict** | — | ✅ Ready | ✅ Ready | **✅ Ready** | — | All issues resolved |

**Changes from v2 to v3:**
- I-DA-03 (Shard iteration strategy) → Resolved: BA confirmed bot-scan fan-out per-bot SQS; Phase A test defer sang v1.1 (+2 pts Area 1)
- I-DA-04 (Cadence switching mechanism) → Resolved: Lambda ghi `bots.next_deep_audit_at`; EventBridge không tự switch schedule (+0 pts v2 was correct; +1 pts Low→no change; +1 pts v2 scoring correction) (+3 pts Area 2)
- I-DA-06 (OQ-EXBOT-15 HL Rate Limiter ordering) → Resolved: Not applicable cho v1; deep-audit v1 là stub (+1 pts Area 2)
- I-DA-07 (`last_known_hl_short_size` update behavior) → Resolved: Worker update field bất kể match/mismatch (+3 pts Area 3)

**Verdict:** ✅ **Ready (98/100).** UC-EXBOT-deep-audit đã sẵn sàng cho test design sau re-audit 2026-07-09. Tất cả issues đã được resolved. **Lưu ý:** Phase A test cho deep-audit được deferred sang v1.1 vì v1 deep-audit là stub (`observeDeepAudit()` không gọi HL thật).

---

## 12. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu cho UC-EXBOT-deep-audit |
| v1 (updated in-place) | 2026-07-02 | QC UC Read ExBot Agent | Re-audit sau BA trả lời Q-DA-01, Q-DA-02. Updated: E-EXBOT-019/020 confirmed, paused bot stuck marker confirmed. Updated scoring: 74→90. Verdict: Conditionally Ready → Ready. |
| v2 | 2026-07-06 | QC UC Read ExBot Agent | Re-audit sau BA document update 2026-07-04 (arc-migration: Cloudflare → AWS). Added: I-DA-05 (RESOLVED: arc-migration), I-DA-06 (NEW: OQ-EXBOT-15), I-DA-07 (NEW: last_known_hl_short_size update behavior). Updated scoring: 90→89. Verdict: Ready. |
| v3 | 2026-07-09 | QC UC Read ExBot Agent | Re-audit sau BA responses 2026-07-04 (qc-responses-2026-07-04.md). Resolved: Q-DA-03 (shard iteration), Q-DA-04 (cadence switching), Q-DA-06 (OQ-EXBOT-15 N/A for v1), Q-DA-07 (last_known_hl_short_size always synced). All issues resolved. Updated scoring: 89→98. Verdict: Ready. Note: Phase A test deferred to v1.1. |

---

*UC-EXBOT-deep-audit Readiness Review Report - v3 (2026-07-09 Re-audit after BA responses 2026-07-04)*
