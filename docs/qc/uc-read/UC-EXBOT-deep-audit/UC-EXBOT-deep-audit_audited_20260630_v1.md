# UC-EXBOT-deep-audit: Periodic Deep Audit and Backstop SAFE_MODE Detection

**Document Title:** UC-EXBOT-deep-audit Readiness Review Report  
**Date Created:** 2026-06-30  
**Author/Agent:** QC UC Read ExBot Agent  
**Version:** v1  

---

## Feature Brief - Tóm tắt nghiệp vụ

UC-EXBOT-deep-audit là một worker được kích hoạt theo lịch trình cron, thực hiện kiểm tra toàn diện trạng thái hedge của tất cả các bot đang active hoặc paused. Khác với light-check (chạy mỗi 5 phút, không gọi Hyperliquid API), deep-audit gọi Hyperliquid để lấy `clearinghouseState` và `marginSummary` nhằm phát hiện các vấn đề nghiêm trọng mà light-check không thể phát hiện: sai lệch hedge size giữa hệ thống và Hyperliquid, stop trigger bị kẹt quá 30 phút, hoặc stop replacement bị kẹt quá 60 giây. Khi phát hiện bất kỳ điều kiện nào trong số này, hệ thống sẽ kích hoạt SAFE_MODE.

Tần suất chạy mặc định là 6 giờ/lần. Khi circuit_breakers.state != 'closed' hoặc margin_status ở mức warning/critical, tần suất tăng lên 1 giờ/lần (high-risk mode). Điểm đặc biệt là deep-audit TIẾP TỤC chạy cho cả các bot đang paused — pause không được miễn audit.

Deep-audit là lớp phát hiện dự phòng (secondary backstop) cho `stop_replacing_started_at` overrun. Lớp phát hiện chính (primary) là light-check với chu kỳ 5 phút. Nếu light-check bị bỏ sót (ví dụ worker crash trước khi chạy), deep-audit sẽ phát hiện trong vòng 6 giờ (hoặc 1 giờ nếu ở high-risk mode).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-deep-audit | Periodic Deep Audit and Backstop SAFE_MODE Detection | draft (updated 2026-06-29) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-06-29 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `uc-deep-audit.md` | updated 2026-06-29 | UC under review | Primary source |
| `srs/spec.md` | updated 2026-06-29 | SRS baseline — FR-EXBOT-016, FR-EXBOT-033 | Source of truth for deep-audit |
| `srs/states.md` | updated 2026-06-18 | State registry — bot lifecycle, circuit breaker, margin status | Baseline |
| `srs/flows.md` | updated 2026-06-29 | Queue fan-out, hedge-sync, close flows | Baseline |
| `srs/erd.md` | updated 2026-06-29 | D1 ERD — hedge_legs, queue_idempotency fields | Baseline |
| `frd.md` | updated 2026-06-29 | FRD — FR-EXBOT-016, FR-EXBOT-033, FR-EXBOT-050, FR-EXBOT-060 | Baseline |
| `us-005.md` | 2026-06-12 | User Story — light-check no HL | Linked story |
| `us-008.md` | 2026-06-12 | User Story — circuit breaker | Linked story |
| `us-010.md` | 2026-06-29 | User Story — margin warning SAFE_MODE | Linked story |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-deep-audit tồn tại để cung cấp một lớp kiểm tra dự phòng (backstop) cho trạng thái an toàn của ExBot. Trong khi light-check (FR-EXBOT-012) là lớp phát hiện nhanh chạy mỗi 5 phút với zero HL API call, deep-audit là lớp kiểm tra toàn diện chạy định kỳ mỗi 6 giờ (hoặc 1 giờ khi high-risk) sử dụng Hyperliquid API để xác nhận hedge position thực sự khớp với trạng thái trong D1.

Hai detection path chính: (1) reconcile mismatch — phát hiện khi actual short size trên Hyperliquid khác với last_known_hl_short_size trong D1; (2) stuck markers — phát hiện khi stop_trigger_crossed_at hoặc stop_replacing_started_at đã được set nhưng không được giải quyết trong thời gian cho phép (30 phút và 60 giây tương ứng).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Cron-triggered deep-audit worker | Worker được kích hoạt bởi cron schedule, duyệt qua tất cả bot active/paused | UC §2 Preconditions |
| clearinghouseState reconcile | Gọi HL API lấy actual short size, so sánh với D1 last_known_hl_short_size | UC Step 3; FR-EXBOT-016 |
| stop_trigger_crossed_at stuck detection | Phát hiện marker đã set > 30 phút | UC Step 4; FR-EXBOT-033 |
| stop_replacing_started_at stuck detection | Phát hiện marker đã set > 60 giây | UC Step 5; FR-EXBOT-033 |
| marginStatus update | Gọi HL marginSummary, cập nhật hedge_legs.margin_status | UC Step 6; FR-EXBOT-016 |
| SAFE_MODE entry | Kích hoạt SAFE_MODE khi phát hiện bất kỳ condition nào | UC §5 Postconditions; FR-EXBOT-050 |
| Cadence switching | Chuyển 6h → 1h khi circuit_breakers.state != 'closed' hoặc margin_status warning/critical | UC §2 Preconditions; FR-EXBOT-016 |
| Paused bot audit | Deep-audit chạy cho cả paused bot | UC A2; FR-EXBOT-005 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Light-check primary detection cho stop_replacing_started_at | Primary detection thuộc UC-EXBOT-light-check; deep-audit chỉ là secondary backstop | Tester cần hiểu 2-layer detection nhưng test deep-audit chỉ cần verify backstop path |
| Stop placement/replacement logic (INV-STOP protocol) | Thuộc UC-EXBOT-hedge-sync; deep-audit chỉ phát hiện khi stop bị kẹt | Test deep-audit không cần test INV-STOP internals |
| Auto-recovery from SAFE_MODE | Thuộc FR-EXBOT-050 recovery section; deep-audit chỉ trigger entry, không handle recovery | Test deep-audit chỉ verify entry trigger |
| Bot start/lifecycle initialization | Thuộc UC-EXBOT-bot-start | Không ảnh hưởng |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Deep-Audit Worker) | Primary | Cron-triggered worker; đọc D1, gọi HL, ghi D1, trigger SAFE_MODE | Worker chỉ thực hiện read HL + update D1; không thực hiện hedge mutation | UC §1 Actors |
| D1 (database) | System | Nguồn dữ liệu trạng thái bot; đích ghi của audit results | — | UC Step 1, 3, 4, 5, 6, 7 |
| Hyperliquid (HL) | System | Nguồn truth cho hedge position và margin data | Gọi qua HLRateLimitDO với weight=2 cho clearinghouseState | UC Step 2, 6 |
| Notification Queue | System | Nhận notification message khi phát hiện anomaly | — | UC A3, A4 |

**Nhận xét readiness:**
Actor và role đã được định nghĩa rõ ràng. Không có UI actor — deep-audit là hoàn toàn backend/cron-driven. Mối quan hệ giữa Deep-Audit Worker và Hyperliquid qua HLRateLimitDO đã được UC chỉ ra (BR-EXBOT-003 exception).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Cron scheduler fire theo schedule: 6 giờ (normal) hoặc 1 giờ (high-risk) | Yes | UC §2 Preconditions |
| 2 | Tồn tại ít nhất một bot với status IN ('active', 'paused') trong D1 | Yes (để worker có việc để làm) | UC §2 Preconditions |
| 3 | HLRateLimitDO cho phép gọi HL API (weight budget còn) | Yes (cho Steps 2, 3, 4, 6) | UC A1; FR-EXBOT-091 |
| 4 | circuit_breakers.state và hedge_legs.margin_status có giá trị hợp lệ trong D1 | Yes (để evaluate cadence switching) | UC §2 Preconditions |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Mismatch detected (Step 3) | D1 record mismatch; bot enters SAFE_MODE; admin notification queued | UC A3 |
| stop_trigger_crossed_at stuck > 30min (Step 4) | Bot enters SAFE_MODE; admin escalation notification queued với reason "stop_trigger_crossed_at stuck > 30min" | UC A4 |
| stop_replacing_started_at stuck > 60s (Step 5) | Bot enters SAFE_MODE; admin escalation notification queued với reason "stop_replacing_started_at stuck > 60s" | UC A4 |
| marginSummary fetched (Step 6) | hedge_legs.margin_status updated from fresh HL data | UC Step 6; FR-EXBOT-016 |
| Audit completed successfully | hedge_legs.last_audit_at = now; queue_idempotency row state='succeeded' | UC Step 7, 8 |
| HL unreachable (A1) | Bot ở lại trạng thái hiện tại; cadence chuyển sang high-risk (1h); retry-pending state recorded | UC A1 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Tên chức năng / luồng: Deep-Audit Cycle

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Deep-Audit Worker | Cron triggers worker | Worker reads bot state from D1: bots.status, bots.lifecycle_state, hedge_legs, circuit_breakers.state, margin_status | — | — | UC Step 1 |
| 2 | Deep-Audit Worker | Gọi HL clearinghouseState | Worker calls HL via HLRateLimitDO (weight=2); fetches actual short size | **A1 (HL unreachable):** HLRateLimitDO returns {allowed: false} hoặc HL returns 5xx → skip Steps 2,3,4,6,7; update cadence to 1h; enqueue notification | — | UC Step 2 |
| 3 | Deep-Audit Worker | Verify hedge size match | Worker compares actual short size from HL với hedge_legs.last_known_hl_short_size | **A3 (mismatch):** actual ≠ last_known → record mismatch in D1; trigger SAFE_MODE; enqueue admin notification với size delta | — | UC Step 3 |
| 4 | Deep-Audit Worker | Check stop_trigger_crossed_at stuck | Worker evaluates: stop_trigger_crossed_at IS NOT NULL AND (now − stop_trigger_crossed_at) > 30 min | **A4 (stuck):** condition true → trigger SAFE_MODE; enqueue admin escalation với timestamp và reason | — | UC Step 4 |
| 5 | Deep-Audit Worker | Check stop_replacing_started_at stuck | Worker evaluates: stop_replacing_started_at IS NOT NULL AND (now − stop_replacing_started_at) > 60s | **A4 (stuck):** condition true → trigger SAFE_MODE; enqueue admin escalation với timestamp và reason | — | UC Step 5 |
| 6 | Deep-Audit Worker | Fetch marginSummary | Worker calls HL marginSummary; updates hedge_legs.margin_status from fresh HL data | A1 (HL unreachable): step skipped | — | UC Step 6 |
| 7 | Deep-Audit Worker | Update audit timestamp | Worker sets hedge_legs.last_audit_at = now | — | — | UC Step 7 |
| 8 | Deep-Audit Worker | Idempotency marker | Worker inserts queue_idempotency row: state='succeeded' | — | — | UC Step 8 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| HL weight budget | Deep-audit calls HL với weight=2; BR-EXBOT-003 (HL weight = 0) không apply cho deep-audit | Yes | Gọi HL thành công | A1: HLRateLimitDO returns {allowed: false} → skip HL steps, switch to 1h cadence | UC BR; FR-EXBOT-091 |
| Paused bot inclusion | Deep-audit chạy cho cả paused bot — pause không miễn audit | Yes | Worker vẫn thực hiện all detection paths (Steps 3–7) | N/A — không có exception | UC A2; FR-EXBOT-005 |
| Cadence switching logic | Cron cadence chuyển 6h → 1h khi ANY of: circuit_breakers.state != 'closed', margin_status='warning', margin_status='critical' | Yes | Worker chạy ở high-risk schedule | N/A | UC §2 Preconditions |
| stop_trigger_crossed_at write-once | BR-EXBOT-005: stop_trigger_crossed_at chỉ được set nếu hiện tại là NULL (guard) — deep-audit không set, chỉ check | N/A | Deep-audit chỉ kiểm tra timestamp đã set | N/A | BR-EXBOT-005; FR-EXBOT-033 |
| SAFE_MODE entry condition | UC định nghĩa 3 entry paths: mismatch (A3), stop_trigger_crossed_at stuck > 30min (A4), stop_replacing_started_at stuck > 60s (A4) | Yes | Bot enters safe_mode; admin notified | N/A | FR-EXBOT-050 |
| Secondary backstop role | Deep-audit là secondary detection cho stop_replacing_started_at; primary là light-check (≤5 min) | Yes (design intent) | Nếu light-check miss, deep-audit catch trong vòng 6h/1h | Light-check primary miss → max detection delay = 6h (normal) hoặc 1h (high-risk) | FR-EXBOT-033 |
| Bot scope: active + paused | UC §2 chỉ định status IN ('active','paused') | Yes | Worker đọc và xử lý các bot này | Bot closed/safe_mode/error/idle/preflight/etc. không được deep-audit (states.md registry shows "skip") | UC §2; states.md |

#### C. Thông báo, lỗi và phản hồi hệ thống (API response / state change / event / message)

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Mismatch detected | State transition + Admin notification | Bot transitions to safe_mode; admin notification với size delta (actual − expected) | E-EXBOT-011 (reconcile mismatch) | UC A3; spec.md E-EXBOT-011 |
| stop_trigger_crossed_at stuck | Admin escalation notification | "stop_trigger_crossed_at stuck > 30min" notification với timestamp và reason | N/A — message content not defined in UC or common files | UC A4 |
| stop_replacing_started_at stuck | Admin escalation notification | "stop_replacing_started_at stuck > 60s" notification với timestamp và reason | N/A — message content not defined in UC or common files | UC A4 |
| HL API unreachable | State change + notification | Cadence chuyển sang 1h; retry-pending state recorded; notification "Hyperliquid API unreachable" | E-EXBOT-008 | UC A1; spec.md E-EXBOT-008 |
| Idempotency row | D1 insert | queue_idempotency.key = unique per audit run; state='succeeded' | FR-EXBOT-011 | UC Step 8 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Mismatch detected → SAFE_MODE entry | UC-EXBOT-bot-safe-close | SAFE_MODE entry trigger bot_safe_close flow (FR-EXBOT-072) | Tester cần verify bot_safe_close được trigger đúng sau SAFE_MODE entry | FR-EXBOT-050; FR-EXBOT-072 |
| Margin status update | US-EXBOT-010; FR-EXBOT-060 | Deep-audit update hedge_legs.margin_status → trigger warning/critical notification hoặc SAFE_MODE | Tester cần verify margin_status được update đúng từ HL marginSummary | FR-EXBOT-016; FR-EXBOT-060 |
| stop_replacing_started_at stuck → SAFE_MODE | UC-EXBOT-hedge-sync (stop replacement) | Backstop cho INV-STOP protocol failure | Tester cần hiểu: primary detection = light-check (≤5 min), secondary = deep-audit (≤6h) | FR-EXBOT-033 |
| Paused bot audit continues | UC-EXBOT-pause-resume | Pause chỉ suppress light-check và hedge-sync, không suppress deep-audit | Tester cần verify deep-audit vẫn chạy cho paused bot | FR-EXBOT-005; states.md |
| Cadence switching to 1h | Light-check worker; circuit breaker | High-risk mode được trigger bởi circuit_breakers.state hoặc margin_status | Tester cần verify cadence switching logic khi conditions thay đổi | FR-EXBOT-016 |
| last_audit_at update | Bot monitoring / status display | Investor và admin có thể xem last audit time | Tester cần verify field được update sau mỗi audit cycle | FR-EXBOT-016 |
| Queue idempotency | Queue system | Prevent duplicate audit processing | Tester cần verify UNIQUE constraint hoạt động đúng | FR-EXBOT-011 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-DA-01 | Happy path — audit completes without issues | Bot với status='active', không có mismatch, không có stuck markers | Deep-audit worker processes bot | hedge_legs.last_audit_at = now; margin_status updated from HL; queue_idempotency state='succeeded' | UC Steps 1,6,7,8; FR-EXBOT-016 |
| AC-DA-02 | Mismatch detection → SAFE_MODE | Bot active; actual short size trên HL ≠ hedge_legs.last_known_hl_short_size | Deep-audit worker verifies size | Bot enters safe_mode; D1 records mismatch; admin notification với size delta enqueued | UC A3; FR-EXBOT-050; E-EXBOT-011 |
| AC-DA-03 | stop_trigger_crossed_at stuck > 30min → SAFE_MODE | Bot active; hedge_legs.stop_trigger_crossed_at set và age > 30 min | Deep-audit worker checks timestamp | Bot enters safe_mode; admin escalation notification "stop_trigger_crossed_at stuck > 30min" enqueued | UC A4; FR-EXBOT-033; FR-EXBOT-050 |
| AC-DA-04 | stop_replacing_started_at stuck > 60s → SAFE_MODE | Bot active; hedge_legs.stop_replacing_started_at set và age > 60s | Deep-audit worker checks timestamp | Bot enters safe_mode; admin escalation notification "stop_replacing_started_at stuck > 60s" enqueued | UC A4; FR-EXBOT-033; FR-EXBOT-050 |
| AC-DA-05 | HL unreachable → graceful degradation | HLRateLimitDO returns {allowed: false} hoặc HL API returns 5xx | Deep-audit worker attempts HL call | Steps 2,3,4,6,7 skipped; cadence chuyển 1h; notification "Hyperliquid API unreachable" enqueued; retry-pending state recorded | UC A1; E-EXBOT-008 |
| AC-DA-06 | Paused bot still audited | Bot với status='paused' | Deep-audit cron fires | All detection paths (Steps 3–7) execute normally; pause does NOT skip deep-audit | UC A2; FR-EXBOT-005 |
| AC-DA-07 | High-risk cadence switching | circuit_breakers.state='open' OR margin_status='warning' OR margin_status='critical' | Cron evaluates conditions | Deep-audit schedule switches from 6h to 1h | UC §2 Preconditions; FR-EXBOT-016 |
| AC-DA-08 | Idempotency prevents duplicate | Queue delivers same message_id twice | Worker processes first delivery | First: state='started' → processing → state='succeeded'; Second: UNIQUE conflict → return immediately | FR-EXBOT-011 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Deep-audit chạy mỗi 6h/1h, không phải real-time. Không có throughput requirement cụ thể cho deep-audit trong NFR. | Tester không cần verify throughput như light-check (10k bots/5min) | NFR-EXBOT-001 chỉ áp dụng light-check |
| Rate Limit | Deep-audit sử dụng HL API weight. BR-EXBOT-003 (HL weight=0) không apply — deep-audit có weight=2. | Tester cần verify HLRateLimitDO được gọi đúng với weight=2 | FR-EXBOT-091; BR-EXBOT-003 exception in UC BR |
| Idempotency | queue_idempotency đảm bảo duplicate message không được xử lý 2 lần | Tester cần verify UNIQUE constraint behavior khi message redelivered | FR-EXBOT-011; NFR-EXBOT-007 |
| Precision | Margin calculation và timestamp comparison phải dùng BigDecimal/time comparison đúng | Tester cần verify timestamp comparison logic (30 min, 60s) không bị float precision issue | NFR-EXBOT-008 (BigDecimal) |
| Reliability / Resilience | HL unreachable → graceful degradation, không crash worker | Tester cần verify A1 path hoạt động đúng khi HL unavailable | E-EXBOT-008 |
| Audit / Logging | last_audit_at updated; notification queued; mismatch recorded | Tester cần verify các field này được ghi sau mỗi cycle | FR-EXBOT-016 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q-DA-01 | High | MISSING_INFO | UC A4; spec.md §5 Error Codes; frd.md §4.6 | UC A4 mô tả admin escalation notification được enqueue khi stuck marker detected, nhưng **không có nội dung message cụ thể** được định nghĩa trong UC hoặc trong spec.md error codes. spec.md E-EXBOT-008 (HL unreachable) và E-EXBOT-011 (reconcile mismatch) có nội dung, nhưng **không có E-code tương ứng cho hai stuck marker cases**. BA vui lòng xác định: (1) Admin notification message cho "stop_trigger_crossed_at stuck > 30min" có nội dung chính xác là gì? (2) Admin notification message cho "stop_replacing_started_at stuck > 60s" có nội dung chính xác là gì? (3) Có cần E-code riêng cho các notification này không? Nếu không có message chính xác, tester không thể verify expected notification content trong test case. | Test case không thể verify expected notification content khi không có message definition chính xác. | BA / QC Lead | Open |
| Q-DA-02 | Medium | UNTRACEABLE_SYNTHESIS | UC §6 Business Rules; FR-EXBOT-033 | UC BR §6 nói "Deep-audit continues for paused bots — pause ≠ skip audit". Tuy nhiên, spec.md FR-EXBOT-005 (Pause/Resume) nói "Deep-audit shall continue every 6 hours during pause." Đây là **confirm đúng**, không phải vấn đề. Tuy nhiên, **không rõ ràng** deep-audit cho paused bot có check `stop_trigger_crossed_at` và `stop_replacing_started_at` stuck markers không — vì stopped marker chỉ được set khi stop trigger fires (trong light-check), và stopped bot thường không ở trạng thái paused. Vấn đề: **stop markers có thể bị set trên active bot, sau đó user pause bot, rồi marker bị stuck trên paused bot — deep-audit có xử lý đúng path này không?** UC A2 nói "all detection paths execute normally" nhưng không verify cụ thể. | Tester cần biết liệu stuck marker detection hoạt động cho paused bot hay không để design test đúng scope. | QC Lead | Open |
| Q-DA-03 | Medium | MISSING_INFO | UC Step 1; erd.md | UC Step 1 nói worker reads `bots.status`, `bots.lifecycle_state`, `hedge_legs`, `circuit_breakers.state`, `margin_status` từ D1. Tuy nhiên, **không rõ ràng** deep-audit worker đọc tất cả bots một lần rồi xử lý tuần tự, hay đọc theo shard. spec.md NFR-EXBOT-012 đề cập D1 sharding nhưng deep-audit UC không specify shard iteration strategy. BA vui lòng xác nhận: Deep-audit worker đọc bots theo cách nào — scan tất cả shards, hay một cron trigger per shard? Điều này ảnh hưởng đến test design cho multi-shard scenario. | Multi-shard test design phụ thuộc vào shard iteration strategy. Nếu không rõ, tester không thể design test cho Phase B (4 shards). | BA / Tech Lead | Open |
| Q-DA-04 | Low | UNCLEAR_INFO | UC A1; spec.md E-EXBOT-008 | UC A1 nói "update cadence to high-risk interval (1 hour)" khi HL unreachable. Tuy nhiên, **không rõ** điều này được ghi vào đâu trong D1 — có phải `bots.next_deep_audit_at` không? erd.md có `bots.next_deep_audit_at` field. Nhưng UC không specify writer. BA vui lòng xác nhận: Khi cadence switch 6h → 1h, worker có update `bots.next_deep_audit_at` để reflect 1h interval không, hay cron schedule tự handle switching dựa trên current state? | Tester cần verify cadence switching mechanism để design test đúng behavior. | Tech Lead | Open |
| Q-DA-05 | Low | OUT_OF_SCOPE | UC §6 BR | UC BR §6 nói "Deep-audit is the backstop; light-check (primary ≤5 min detection, FR-EXBOT-012) is the fast path for stop_replacing_started_at overrun." **Đây là design note rõ ràng**, nhưng UC không mô tả notification/message khi backstop actually catches something. Vấn đề này đã được cover trong Q-DA-01 (missing admin notification messages). | N/A | — | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| FR-EXBOT-016 (Deep-Audit) | FR requirement | UC-EXBOT-deep-audit implements this FR. Nếu FR thay đổi, UC phải update. | BA | Draft |
| FR-EXBOT-033 (SAFE_MODE on stuck stop) | FR requirement | UC-EXBOT-deep-audit là secondary detection cho FR-EXBOT-033. Không có primary detection trong UC này. | BA | Draft |
| FR-EXBOT-050 (SAFE_MODE triggers) | FR requirement | Deep-audit triggers 3 trong 7 SAFE_MODE conditions. | BA | Draft |
| FR-EXBOT-060 (Margin status thresholds) | FR requirement | Deep-audit update margin_status từ HL marginSummary. Threshold values (0.55/0.75) pending Phase 0 backtest (OQ-EXBOT-06). | zen / BA | Open |
| HLRateLimitDO (FR-EXBOT-091) | Durable Object | Deep-audit sử dụng HLRateLimitDO. Weight budget phải được config đúng. | Tech Lead | Draft |
| queue_idempotency (FR-EXBOT-011) | Queue infrastructure | Deep-audit sử dụng idempotency pattern. | Tech Lead | Draft |
| OQ-EXBOT-06 (margin thresholds) | Open Question | 0.55/0.75 thresholds pending finalization | zen | Open |
| common-rules.md | Common rule file | spec.md ghi "resolve cited BR-* to verbatim text from common-rules.md" — **nhưng common-rules.md không tồn tại** trong docs/BA. BR-EXBOT-* rules được định nghĩa inline trong spec.md §4. Không tìm thấy artifact riêng. | BA | N/A (BR defined in spec) |

---

## 11. Issue Register

### Issue Summary

| Issue ID | Type | Severity | Affected Area | Finding |
|---|---|---|---|---|
| I-DA-01 | MISSING_INFO | Major | Area 2: Data Object Validation & Messages | Admin notification messages cho stuck marker cases không được định nghĩa — no E-code, no message content |
| I-DA-02 | MISSING_INFO | Medium | Area 2: Data Object Validation & Messages | Không rõ cadence switching (6h→1h) được ghi vào đâu trong D1 |
| I-DA-03 | MISSING_INFO | Medium | Area 1: Function/Operation Inventory | Không rõ deep-audit shard iteration strategy cho multi-shard Phase B |
| I-DA-04 | UNCLEAR_INFO | Medium | Area 2: Business Rules | Không verify stopped marker detection hoạt động đúng cho paused bot (edge case: active→pause→stuck) |

### Issue Details

**I-DA-01 — MISSING_INFO (Major)**

**Affected Area:** Area 2 (Data Object / State Attributes, Business Rules, Validations & Messages)

**Finding:** UC A4 mô tả "enqueue admin escalation notification with timestamp and reason ('stop_trigger_crossed_at stuck > 30min' or 'stop_replacing_started_at stuck > 60s')" nhưng **không có nội dung message chính xác**. spec.md §5 Error Codes có E-EXBOT-008 và E-EXBOT-011 nhưng không có E-code cho hai stuck marker cases.

**Impact on tester understanding:** Tester không thể verify expected notification content trong test case vì message không được define. Không có E-code để trace.

**Suggested question/fix:** BA cần định nghĩa: (1) E-code riêng cho mỗi stuck case (ví dụ: E-EXBOT-018, E-EXBOT-019), (2) Exact notification message content cho admin escalation.

**Status:** Open

---

**I-DA-02 — MISSING_INFO (Medium)**

**Affected Area:** Area 2 (Data Object / State Attributes, Business Rules, Validations & Messages)

**Finding:** UC A1 nói "update cadence to high-risk interval (1 hour)" nhưng không chỉ ra worker ghi thông tin này ở đâu. erd.md có `bots.next_deep_audit_at` nhưng không có spec entry nào nói worker update field này.

**Impact on tester understanding:** Tester không biết cadence switching được implement bằng cách nào — cron tự switch dựa trên current state, hay worker update next_deep_audit_at field.

**Suggested question/fix:** Tech Lead xác nhận: (1) Worker update `bots.next_deep_audit_at` khi cadence switch, hay (2) Cron worker tự switch schedule dựa trên state query mà không cần ghi D1.

**Status:** Open

---

**I-DA-03 — MISSING_INFO (Medium)**

**Affected Area:** Area 1 (Function / Operation & Data Object Inventory)

**Finding:** UC Step 1 đọc tất cả bots nhưng không specify shard iteration strategy. spec.md NFR-EXBOT-012 đề cập Phase A = 1 shard, Phase B = 4 shards. Deep-audit UC không nói rõ worker scan tất cả shards trong một execution hay có một cron trigger per shard.

**Impact on tester understanding:** Tester không thể design test cho multi-shard scenario (Phase B). Nếu có 4 shards, deep-audit worker cần iterate qua tất cả để audit tất cả bots.

**Suggested question/fix:** Tech Lead xác nhận: Deep-audit cron trigger một worker cho tất cả shards, hay một worker per shard? Nếu per-shard, có 4 cron triggers hay 1 cron fan-out to 4 workers.

**Status:** Open

---

**I-DA-04 — UNCLEAR_INFO (Medium)**

**Affected Area:** Area 3 (Functional Logic & Workflow Decomposition)

**Finding:** UC A2 nói "Full audit still runs at 6-hour cadence — pause does NOT skip deep-audit scheduling. All detection paths (steps 3–7) execute normally." Tuy nhiên, không có verify rõ ràng rằng stopped marker detection hoạt động cho paused bot. **Edge case:** Active bot → stop trigger fires → light-check sets `stop_trigger_crossed_at` → user pauses bot → marker stuck > 30 min trên paused bot. Deep-audit A2 path nói "all detection paths execute" nhưng UC không verify stopped marker detection được include.

**Impact on tester understanding:** Tester có thể bỏ sót test case cho edge case này. Nếu marker detection không apply cho paused bot, test case sẽ sai.

**Suggested question/fix:** Tech Lead xác nhận: Deep-audit có check `stop_trigger_crossed_at` và `stop_replacing_started_at` cho paused bots không? Nếu có, UC nên make it explicit trong A2.

**Status:** Open

---

### Scoring Summary

| Scoring Area | Max Points | Score | Status |
|---|---|---|---|
| Area 1: Function / Operation & Data Object Inventory | 20 | 15/20 | ⚠️ Partial |
| Area 2: Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 17/25 | ⚠️ Partial |
| Area 3: Functional Logic & Workflow Decomposition | 25 | 20/25 | ⚠️ Partial |
| Area 4: Functional Integration & Data Consistency | 15 | 12/15 | ✅ Clear |
| Area 5: UC / Spec Documentation Quality Issues | 15 | 10/15 | ⚠️ Partial |
| **Total** | **100** | **74/100** | **⚠️ Conditionally Ready** |

**Auto-cap rules applied:** No auto-caps triggered.

**Verdict:** Conditionally Ready (70-89). UC có thể sử dụng được cho test design ở những phần rõ ràng. Tuy nhiên, 4 issues cần được giải quyết trước khi có thể design test đầy đủ:
- Q-DA-01 (High): Admin notification messages không được định nghĩa — **Blocker cho notification testing**
- Q-DA-02 (Medium): Cadence switching mechanism không rõ ràng
- Q-DA-03 (Medium): Shard iteration strategy không defined cho Phase B
- Q-DA-04 (Medium): Stopped marker detection cho paused bot không explicit

---

## 12. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu cho UC-EXBOT-deep-audit |

---

*UC-EXBOT-deep-audit Readiness Review Report - v1*
