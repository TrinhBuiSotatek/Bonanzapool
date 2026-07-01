# Question Backlog — UC-EXBOT-pause-resume

> Generated: 2026-06-30
> Source files: `docs/qc/uc-read/UC-EXBOT-pause-resume/UC-EXBOT-pause-resume_pause-resume_audited_20260630_v1.md`

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q2 | Blocker | FR-EXBOT-010; UC §1, §3 | **"Status Update Worker" không tồn tại trong queue topology.** FR-EXBOT-010 định nghĩa đúng 11 queues. UC gọi worker xử lý pause/resume là "Status update worker" nhưng worker này không được ánh xạ vào queue nào trong SRS. Nó có phải là phần của ExBot Worker (xử lý trực tiếp API request mà không qua queue), hay là một queue consumer chưa được định nghĩa? Tech Lead vui lòng xác nhận kiến trúc worker: ExBot Worker xử lý pause/resume đồng bộ (không queue), hay cần một queue riêng (tên gì)? | Tester không biết worker xử lý pause/resume hoạt động như thế nào → không thể test idempotency, retry behavior | Open |
| Q3 | Major | FR-EXBOT-011; UC §3–5; SRS spec.md §FR-EXBOT-011 | **Không có idempotency mechanism cho pause/resume.** FR-EXBOT-011 bắt buộc mọi queue consumer phải insert `message_id` vào `queue_idempotency` table. UC §5 A3 mô tả idempotent response nhưng không nêu cơ chế implement. Tech Lead vui lòng xác nhận: (1) pause/resume có qua queue không? (2) nếu có, idempotency key là gì? (3) nếu không qua queue, cơ chế chống race condition là gì? | Không có idempotency → không thể test race condition scenarios | Open |
| Q7 | Major | UC §2, §4; SRS states.md | **Valid `lifecycle_state` values cho pause/resume không được định nghĩa rõ ràng.** UC §2 pause precondition chỉ nêu `lifecycle_state='active'` được pause. Tuy nhiên states.md state registry row `(pre-pause value) \| paused` ngụ ý mọi giá trị `lifecycle_state` đều có thể pause (không chỉ `'active'`). BA vui lòng chốt: những giá trị `lifecycle_state` nào được phép pause/resume? Chỉ `'active'` hay `'hedge_stopped_cooldown'` và `'lp_rebalancing'` cũng được? | Tester không biết valid/invalid pause/resume scenarios theo lifecycle_state | Open |
| Q8 | Major | UC §3–5; SRS spec.md §6 | **"UI confirmation" gây nhầm lẫn scope giữa ExBot và POOL UI.** spec.md §6 khẳng định ExBot là backend-only module, không sở hữu UI. UC nói "Investor receives UI confirmation" nhưng ExBot không có màn hình. BA vui lòng xác nhận: "UI confirmation" nằm trong ExBot scope hay POOL UI (PTL-05)? Nếu ExBot scope dừng ở API response, tester chỉ verify API response — không cần test POOL UI rendering. | Tester không biết test scope — chỉ API hay cả UI rendering | Open |
| Q9 | Major | UC §3 step 7, §4 step 6; UC §5 A2, A3; message-list.md | **Success messages không có message code để trace.** UC §3 step 7 trả về message nhưng không có mã E-code. message-list.md chỉ có E-EXBOT-* error codes. BA vui lòng xác nhận: (1) success messages có cần đăng ký message code không? (2) nếu có, mã là gì? (3) nếu không, tester verify text content của response? | Không có message code → khó trace API contract trong test | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q4 | Major | UC §4 step 5; FR-EXBOT-013 | **Jitter cho `next_light_check_at` khi resume không rõ nguồn chuẩn.** | UC §4 step 5 nêu rõ: `next_light_check_at = now + 5min + jitter(−45s, +45s)`. FR-EXBOT-013 xác nhận: `"next_light_check_at shall be set to now + 5min + random(−45s, +45s)"`. Cùng jitter pattern được áp dụng cho cả normal scheduling và resume scheduling — không có jitter riêng cho resume. | QC UC Read Agent (docs evidence) | 2026-07-01 | Answered |
| Q5 | Major | UC §6; FR-EXBOT-014 | **Suppression behavior cho `price-near-stop-audit` trong pause không được nêu.** | FR-EXBOT-014 khẳng định: `"Stop monitoring (price-near-stop-audit enqueue) shall continue at all times — including when circuit_breakers.state='open'". Light-check shall NEVER suppress stop price evaluation or price-near-stop-audit enqueue.` Điều này áp dụng cho mọi trạng thái bot, bao gồm `status='paused'`. `price-near-stop-audit` vẫn tiếp tục khi paused — không bị suppress. | QC UC Read Agent (docs evidence) | 2026-07-01 | Answered |
| Q6 | Major | UC §6; FR-EXBOT-016 | **Deep-audit high-risk cadence (1 giờ) có áp dụng khi paused không?** | UC §6 ghi rõ: `"Continues on its normal 6-hour cadence (or 1-hour high-risk cadence)"`. FR-EXBOT-016 xác nhận: `"In high-risk mode (when circuit_breakers.state != 'closed' or margin_status IN ('warning','critical')), the interval reduces to 1 hour."` Khi bot paused VÀ hệ thống ở high-risk mode, deep-audit chạy 1 giờ thay vì 6 giờ. | QC UC Read Agent (docs evidence) | 2026-07-01 | Answered |
| Q10 | Minor | UC §2; SRS states.md | **Không có precondition cho resume khi bot ở `lifecycle_state='lp_rebalancing'` hoặc `'hedge_stopped_cooldown'`.** | states.md state registry row `(pre-pause value) \| paused` ngụ ý mọi giá trị `lifecycle_state` đều có thể pause — không chỉ `'active'`. UC §2 pause precondition nêu `lifecycle_state='active'` nhưng không nói đó là giá trị DUY NHẤT được phép. Resume precondition chỉ nêu `bots.status='paused'`, không giới hạn `lifecycle_state`. Ngụ ý: cả `'active'`, `'hedge_stopped_cooldown'`, `'lp_rebalancing'` đều được phép pause/resume. Không có spec nói ngược lại. | QC UC Read Agent (docs evidence) | 2026-07-01 | Answered |
| Q11 | Minor | FR-EXBOT-033; UC §6; SRS states.md | **SAFE_MODE entry từ pause state không rõ behavior.** | states.md state registry rõ ràng: row `(pre-pause value) \| paused` và row `safe_mode \| safe_mode` là hai trạng thái độc lập. State machine cho thấy `safe_mode` có transition riêng: `safe_mode → active` (auto-recovery) hoặc `safe_mode → closed` (bot_safe_close). Khi deep-audit phát hiện SAFE_MODE condition trên bot đang paused, `bots.status` chuyển từ `paused` sang `safe_mode` — `lifecycle_state` giữ nguyên giá trị pre-pause. Không có spec nào nói phải giữ `paused` khi vào SAFE_MODE. | QC UC Read Agent (docs evidence) | 2026-07-01 | Answered |
| Q12 | Minor | UC §4 step 5; flows.md F-01; FR-EXBOT-012 | **Bot-scan worker có scheduling cho bot vừa resume không?** | Không phải test issue — không phải spec gap. UC §4 step 5 nêu Status Update Worker enqueue `light-check` ngay sau resume. Bot-scan worker scan định kỳ theo cron (F-01). Implementer sẽ xử lý duplicate prevention (ví dụ: idempotency key trên message hoặc worker tự deduplicate). Không cần BA/Tech Lead xác nhận — đây là implementation detail. | QC UC Read Agent (not a test design issue) | 2026-07-01 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason for Deferral | Target Version | Status |
|----|----------|-----|----------|---------------------|---------------|--------|
| Q1 | Blocker | FR-EXBOT-090; UC §3 step 1, §4 step 1 | **API endpoint names không có trong FR-EXBOT-090.** | Endpoint name khác nhau giữa các môi trường test — QA sẽ lấy endpoint thực tế từ test environment config. Không cần cập nhật spec. | QC Lead | v2 | Deferred |

---

*Question Backlog — UC-EXBOT-pause-resume — updated by QC UC Read Agent (2026-07-01)*
