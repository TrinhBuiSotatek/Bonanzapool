# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Use case:** UC-EXBOT-pause-resume | Tính năng: Pause and Resume Bot

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-pause-resume cho phép NĐT đang có ExBot đang hoạt động tạm dừng bot mà không đóng vị thế, sau đó khôi phục lại trạng thái hoạt động bình thường.

**Ai sử dụng:** NĐT USDC muốn tạm ngừng bot trong giai đoạn thị trường biến động mà không phải thanh lý LP hay hedge.

**Điều kiện trước chính:**
- Pause: bot phải tồn tại với `bots.status='active'` và `bots.lifecycle_state='active'`, đồng thời không ở `safe_mode`.
- Resume: bot phải có `bots.status='paused'`. Trường `bots.lifecycle_state` giữ nguyên giá trị trước khi pause (được bảo toàn trong D1).

**Nghiệp vụ chính:** Khi pause, hệ thống chỉ chuyển `bots.status` sang `'paused'` — không có thay đổi gì đến vị thế hedge trên Hyperliquid, không đóng LP NFT trên BnzaExVault. Khi resume, hệ thống khôi phục `bots.status='active'` và lên lịch light-check tiếp theo trong vòng 5 phút. Hai luồng worker bị chặn trong trạng thái paused: light-check (FR-EXBOT-012: skip hoàn toàn) và hedge-sync (suppressed). Deep-audit vẫn chạy đều đặn mỗi 6 giờ để giám sát trạng thái margin và phát hiện bất thường.

**Quy tắc quan trọng:** BR-EXBOT-002 quy định rõ ràng rằng Pause ≠ Close — Pause giữ nguyên hedge và LP; Close thanh lý toàn bộ. UC phải thể hiện sự khác biệt này qua messaging và API response.

**Module / UC liên quan:** US-EXBOT-003 (link trực tiếp), FR-EXBOT-005 (Pause/Resume Bot), FR-EXBOT-012 (Light-Check suppression), FR-EXBOT-016 (Deep-Audit tiếp tục), FR-EXBOT-090 (Operator Facade API — 4 endpoints).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-pause-resume | Pause and Resume Bot | draft (2026-06-18) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-06-18 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-pause-resume.md` | 2026-06-18 | UC chính được review | Linked: US-EXBOT-003 |
| `userstories/us-003.md` | 2026-06-12 | User story liên kết | P1, USDC Investor |
| `srs/spec.md` | 2026-06-29 | SRS baseline — nguồn chân lý | FR-EXBOT-005, 012, 090 |
| `srs/states.md` | 2026-06-18 | State registry + transitions | pause row in state table |
| `srs/flows.md` | 2026-06-29 | Flow diagrams | Không có flow riêng cho pause/resume |
| `srs/erd.md` | 2026-06-29 | D1 schema | bots, bot_runtime_state |
| `frd.md` | 2026-06-29 | FRD module | FR-EXBOT-003 Pause/Resume |
| `common-rules.md` | 2026-06-26 | BR-EXBOT-002 Pause ≠ Close | |
| `message-list.md` | 2026-06-26 | E-EXBOT-* codes | E-EXBOT-013 cho SAFE_MODE |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Cho phép NĐT tạm dừng hoạt động của ExBot mà không thanh lý vị thế LP trên Uniswap V3 cũng như vị thế short trên Hyperliquid. Hệ thống tiếp tục giám sát qua deep-audit để phát hiện bất thường margin nhưng không thực hiện hedge adjustment hay LP rebalance. Sau đó NĐT có thể resume bot để khôi phục hoạt động bình thường.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Pause bot | Chuyển `bots.status='paused'` giữ nguyên `lifecycle_state` | UC §3; FR-EXBOT-005 |
| Resume bot | Khôi phục `bots.status='active'`, lên lịch light-check trong 5 phút | UC §4; FR-EXBOT-005 AC |
| Light-check suppression | Skip hoàn toàn khi `status='paused'` | UC §6; FR-EXBOT-012 |
| Hedge-sync suppression | Không enqueue hedge-sync trong trạng thái paused | UC §6 |
| Deep-audit tiếp tục | Chạy mỗi 6 giờ trong pause, cập nhật margin status | UC §6; FR-EXBOT-016 |
| SAFE_MODE rejection | Pause bị từ chối khi bot đang ở safe_mode | UC §5 A1; E-EXBOT-013 |
| HL position preserved | Hedge short và LP NFT giữ nguyên trong pause | UC §3 step 4–6; BR-EXBOT-002 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Pause/Resume có ảnh hưởng gì đến `stop_replacing_started_at` không? | UC không nói; `stop_replacing_started_at` chỉ được đề cập trong FR-EXBOT-033 cho trường hợp SAFE_MODE. Nếu bot đang trong quá trình stop replacement mà NĐT pause thì sao? | Không thể thiết kế test cho edge case này |
| Pause khi bot đang ở `lifecycle_state='lp_rebalancing'` | SRS states.md cho biết `lp_rebalancing` là một runtime state. UC §2 preconditions không nói rõ resume từ `lp_rebalancing` có được phép không | Thiếu precondition rõ ràng |
| Price-near-stop-audit có bị suppress khi pause không? | FR-EXBOT-014 nói stop monitoring "continues at ALL times". UC §6 chỉ liệt kê light-check và hedge-sync bị suppress. Không nói rõ `price-near-stop-audit` | Tester không biết cần test trường hợp nào |
| Notification cho NĐT khi pause/resume thành công | Không có `queue=notification` trigger được định nghĩa trong UC | Không biết notification có được gửi hay không |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Initiator of pause/resume request via Operator API or UI | Chỉ có quyền pause/resume bot của chính mình; không thể pause bot đang ở safe_mode | UC §1 |
| Status Update Worker (ExBot Worker) | System | Xử lý pause/resume request, cập nhật D1, enqueue light-check | Worker này không có queue trong FR-EXBOT-010; chưa được định nghĩa rõ | UC §1 |
| Hyperliquid | System (read-only) | Không có tương tác trong pause/resume flow | Không có HL mutation trong luồng pause/resume | UC §3–4 |
| BnzaExVault | System (read-only) | Không có tương tác | Không có vault mutation | UC §3–4 |

**Nhận xét readiness:**

Có hai vấn đề nghiêm trọng ở cấp actor/role:

1. **Status Update Worker không tồn tại trong kiến trúc SRS.** FR-EXBOT-010 định nghĩa 11 queues (bot-scan, light-check, hedge-sync, reconcile, deep-audit, price-near-stop-audit, partial_repair, user_redeem, notification, metrics-rollup, key-provision). Không có queue nào cho "status update" hay "pause/resume". UC gọi worker này là "Status update worker" nhưng không xác định nó là queue consumer hay phần của ExBot Worker. Tester không biết worker này được triển khai như thế nào.

2. **Investor tương tác qua "UI" nhưng ExBot là backend-only module.** SRS spec.md §6 khẳng định "ExBot is a backend-only module. No UI screens are owned by this module." UC §1 và sequence diagram tham chiếu "Investor receives UI confirmation" và "UI: Bot paused" nhưng ExBot Worker không sở hữu UI. POOL UI (PTL-05) render dữ liệu từ Operator Facade API. Điều này có nghĩa "UI confirmation" trong UC thực chất là POOL UI, không phải ExBot scope. Tuy nhiên, việc trộn lẫn "UI" và "API" trong một UC của module backend tạo confusion cho tester.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot tồn tại trong D1 | Yes | UC §2; implied by `bots.status='active'` check |
| 2 | `bots.status='active'` (pause) | Yes | UC §2 Preconditions for Pause |
| 3 | `bots.lifecycle_state='active'` (pause) | Yes | UC §2 — không nêu giá trị nào khác có được phép không |
| 4 | Bot KHÔNG ở `status='safe_mode'` (pause) | Yes | UC §2; A1 alternate flow |
| 5 | `bots.status='paused'` (resume) | Yes | UC §2 Preconditions for Resume |
| 6 | `bots.lifecycle_state` giữ nguyên từ trước pause | Implicit | UC §2: "unchanged from its pre-pause value (preserved in D1)" |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Pause thành công | `bots.status='paused'`, `bots.lifecycle_state` không đổi, `hedge_legs.last_known_hl_short_size` giữ nguyên, `positions.token_id` giữ nguyên, audit log "Bot paused by investor" | UC §7 Postconditions |
| Resume thành công | `bots.status='active'`, `bots.lifecycle_state` xác nhận không đổi, `bot_runtime_state.next_light_check_at = now + 5min + jitter(±45s)`, `light-check` message enqueued, audit log "Bot resumed by investor" | UC §7 Postconditions |

**Lưu ý:** Nếu điều kiện trước hoặc kết quả sau được tham chiếu từ common rule / common function, phải resolve nội dung gốc và ghi rõ mã trong ngoặc.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Chức năng / luồng: Pause Bot

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Investor | Gửi `POST /api/exbot/pause` với `botId` | API tiếp nhận request | — | — | UC §3 step 1 |
| 2 | Status Update Worker | Query D1: kiểm tra `bots.status='active'` và `lifecycle_state='active'` | Xác nhận điều kiện thỏa mãn | Nếu `status='safe_mode'` → A1 | — | UC §3 step 2 |
| 3 | Status Update Worker | Set `bots.status='paused'`, persist atomically vào D1 | Ghi thành công | — | — | UC §3 step 3 |
| 4 | (không có thao tác) | Không modify `bots.lifecycle_state` | Giữ nguyên giá trị pre-pause | — | — | UC §3 step 4 |
| 5 | (không có thao tác) | Không chạm HL short position (`hedge_legs.last_known_hl_short_size`) | Position giữ nguyên | — | — | UC §3 step 5; BR-EXBOT-002 |
| 6 | (không có thao tác) | Không chạm LP NFT (`positions.token_id`) | NFT giữ nguyên | — | — | UC §3 step 6; BR-EXBOT-002 |
| 7 | Operator API | Trả response: `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }` | Response gửi về | — | — | UC §3 step 7 |
| 8 | Investor (UI) | Nhận confirmation | UI hiển thị "Bot paused. Hedge and LP are maintained." | — | — | UC §3 step 8 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.status` | Phải = `'active'` mới được pause | Yes | Chuyển sang `'paused'` | A1: từ chối HTTP 409, E-EXBOT-013 | UC §2; E-EXBOT-013 |
| `bots.lifecycle_state` | Phải = `'active'` khi pause | Yes | Giữ nguyên | Không nêu trong UC; có phải từ chối không? | UC §2 |
| `bots.status` | Phải KHÔNG = `'safe_mode'` | Yes | Cho phép pause | A1: HTTP 409, E-EXBOT-013 | UC §2; E-EXBOT-013 |
| Atomic persistence | Việc ghi `bots.status='paused'` phải atomic | Implied | — | Race condition nếu 2 request cùng lúc? Không nêu trong SRS/UC | UC §3 step 3 |
| BR-EXBOT-002 | Pause ≠ Close — chỉ suppress mutations mới, không thanh lý hedge hay LP | Yes | Hedge và LP giữ nguyên | Vi phạm nếu hệ thống thanh lý positions | BR-EXBOT-002; UC §3 step 4–6 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Pause thành công | API success response | `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }` | Không có E-code (không phải error) | UC §3 step 7 |
| Pause bị từ chối (safe_mode) | API error response | `"Bot is in Safe Mode. You can close the bot instead."` | `E-EXBOT-013` | UC §5 A1; message-list.md |
| Pause khi `status='paused'` rồi | API success (idempotent) | `"Bot already paused. No change needed."` | Không có E-code | UC §5 A3 |

**Lưu ý về E-code:** UC §3 step 7 trả về message nhưng không có mã E-code tương ứng trong message-list.md. Thành công thường không cần E-code, nhưng điều này gây khó khăn cho tester khi muốn trace contract. Message "Paused — hedge is maintained, LP is maintained" và "Bot already paused. No change needed." không có mã để tham chiếu.

---

### 6.2 Chức năng / luồng: Resume Bot

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Investor | Gửi `POST /api/exbot/resume` với `botId` | API tiếp nhận request | — | — | UC §4 step 1 |
| 2 | Status Update Worker | Query D1: kiểm tra `bots.status='paused'` | Xác nhận điều kiện thỏa mãn | Nếu `status='active'` → A2 | — | UC §4 step 2 |
| 3 | Status Update Worker | Khôi phục `bots.status='active'`, persist atomic vào D1 | Ghi thành công | — | — | UC §4 step 3 |
| 4 | Status Update Worker | Đọc `bots.lifecycle_state` từ D1 (không thay đổi), xác nhận giá trị hợp lệ | — | Nếu giá trị bất thường? Không nêu | UC §4 step 4 |
| 5 | Status Update Worker | Set `bot_runtime_state.next_light_check_at = now + 5min + jitter(−45s, +45s)`, enqueue `light-check` message | Message được queue | — | — | UC §4 step 5; FR-EXBOT-013 |
| 6 | Operator API | Trả response: `{ status: "active", message: "Bot resumed. Monitoring resumed." }` | Response gửi về | — | — | UC §4 step 6 |
| 7 | Investor (UI) | Nhận confirmation | UI hiển thị "Bot resumed. Monitoring will resume shortly." | — | — | UC §4 step 7 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.status` | Phải = `'paused'` mới được resume | Yes | Chuyển sang `'active'` | A2: thành công idempotent | UC §2; §5 A2 |
| `bot_runtime_state.next_light_check_at` | Phải được set khi resume | Yes | = `now + 5min + jitter(±45s)` | Nếu không set, bot sẽ không được scan? | UC §4 step 5 |
| Light-check message | Phải được enqueued sau resume | Yes | Worker tiếp nhận và xử lý | Không nêu retry/timeout | UC §4 step 5 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Resume thành công | API success response | `{ status: "active", message: "Bot resumed. Monitoring resumed." }` | Không có E-code | UC §4 step 6 |
| Resume khi `status='active'` | API success (idempotent) | `"Bot already active. No change needed."` | Không có E-code | UC §5 A2 |

---

### 6.3 Chức năng / luồng: Suppression Behavior During Pause

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Light-check Worker | Nhận `light-check` message cho bot `status='paused'` | Skip toàn bộ light-check (không đánh giá rebalance, không enqueue hedge-sync) | — | Không nêu trong UC | FR-EXBOT-012 |
| 2 | Hedge-sync Worker | Nhận `hedge-sync` message cho bot `status='paused'` | Không thực hiện hedge adjustment | — | Không nêu trong UC | UC §6 |
| 3 | Deep-audit Worker | Chạy audit theo cron 6 giờ cho bot `status='paused'` | Fetch HL state, cập nhật margin status, phát hiện bất thường | — | Không nêu behavior khi phát hiện bất thường trong pause | UC §6; FR-EXBOT-016 |
| 4 | Deep-audit Worker | Phát hiện anomaly (stop stuck > 30 phút) | Báo cáo, enter SAFE_MODE nếu điều kiện FR-EXBOT-033 thỏa mãn | — | Nếu bot đang paused mà vào SAFE_MODE thì `bots.status` chuyển thế nào? Không nêu | FR-EXBOT-033 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Light-check skip | Skip hoàn toàn khi `status='paused'` | Yes | Không enqueue hedge-sync, không đánh giá drift/range | Nếu không skip → hedge adjustments sai | FR-EXBOT-012 |
| Deep-audit tiếp tục | Deep-audit vẫn chạy cho paused bots | Yes | Cập nhật `hedge_legs.margin_status` | Không nêu | FR-EXBOT-016 |
| SAFE_MODE vẫn active trong pause | Entry conditions của SAFE_MODE vẫn được theo dõi | Yes | Có thể chuyển sang safe_mode ngay cả khi paused | Chuyển đổi `bots.status` khi vào SAFE_MODE từ pause không rõ | FR-EXBOT-050 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Pause → `bots.status='paused'` | Light-check worker | Worker skip light-check cho bot này (FR-EXBOT-012) | Cần xác minh light-check worker thực sự check `bots.status` trước khi xử lý | FR-EXBOT-012 |
| Pause → `bots.status='paused'` | Hedge-sync worker | Không enqueue hedge-sync | Cần xác minh hedge-sync có check `bots.status` không (UC §6 nói suppressed nhưng FR-EXBOT-012 không nói rõ hedge-sync có check `status='paused'` không) | UC §6; FR-EXBOT-023 |
| Pause → `bots.status='paused'` | Deep-audit cron | Cron vẫn schedule deep-audit cho bot này | Cần xác minh deep-audit schedule filter bao gồm `status='paused'` | FR-EXBOT-016 |
| Resume → `bots.status='active'` + enqueue light-check | Bot-scan worker | Scan worker phải pick up bot này trong lần scan tiếp theo | Cần xác minh scan worker không filter out `status='active'` bots, và `next_light_check_at` được set đúng | UC §4 step 5; flows.md F-01 |
| Deep-audit → phát hiện SAFE_MODE condition khi paused | SAFE_MODE entry | Bot vào SAFE_MODE ngay cả khi paused; `bots.status` chuyển thế nào? | Khi paused, nếu deep-audit phát hiện margin critical hoặc stop stuck → vào SAFE_MODE. UC không nêu rõ: `bots.status` chuyển thẳng sang `safe_mode` hay vẫn giữ `paused`? | FR-EXBOT-050; UC §6 |
| Pause/Resume audit log | Audit system | "Bot paused by investor" / "Bot resumed by investor" được ghi | Cần xác minh audit log có được ghi đúng cách | UC §7 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given — điều kiện | When — hành động | Then — kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path pause | Investor có ExBot `bots.status='active'` và `bots.lifecycle_state='active'` | Investor gửi `POST /api/exbot/pause` | Hệ thống set `bots.status='paused'`, giữ nguyên `hedge_legs.last_known_hl_short_size` và `positions.token_id`; API trả về `{status: "paused"}` | UC §3; US-EXBOT-003 AC-EXBOT-003-1 |
| AC-02 | Happy path resume | Investor có ExBot `bots.status='paused'` | Investor gửi `POST /api/exbot/resume` | Hệ thống khôi phục `bots.status='active'`, set `next_light_check_at = now + 5min + jitter(±45s)`, enqueue `light-check`; API trả về `{status: "active"}` | UC §4; US-EXBOT-003 AC-EXBOT-003-2 |
| AC-03 | SAFE_MODE rejection | Bot `bots.status='safe_mode'` | Investor gửi `POST /api/exbot/pause` | API trả HTTP 409, message E-EXBOT-013 "Bot is in Safe Mode. You can close the bot instead." | UC §5 A1; US-EXBOT-003 AC-EXBOT-003-4 |
| AC-04 | Idempotent pause | Bot `bots.status='paused'` | Investor gửi `POST /api/exbot/pause` lần 2 | API trả thành công "Bot already paused. No change needed." — không thay đổi D1 | UC §5 A3 |
| AC-05 | Idempotent resume | Bot `bots.status='active'` | Investor gửi `POST /api/exbot/resume` | API trả thành công "Bot already active. No change needed." — không thay đổi D1 | UC §5 A2 |
| AC-06 | Light-check suppressed trong pause | Bot `bots.status='paused'` | Cron schedule `light-check` message cho bot này | Light-check worker skip toàn bộ; không enqueue hedge-sync | FR-EXBOT-012; UC §6 |
| AC-07 | Deep-audit tiếp tục trong pause | Bot `bots.status='paused'` | Deep-audit cron chạy mỗi 6 giờ | Deep-audit worker fetch HL state, cập nhật margin status, phát hiện anomaly → báo cáo | FR-EXBOT-016; US-EXBOT-003 AC-EXBOT-003-3 |
| AC-08 | Audit log ghi nhận pause | Bot `bots.status='active'` | Investor pause thành công | Audit log có entry "Bot paused by investor" với timestamp | UC §7 Postconditions |
| AC-09 | Audit log ghi nhận resume | Bot `bots.status='paused'` | Investor resume thành công | Audit log có entry "Bot resumed by investor" với timestamp | UC §7 Postconditions |
| AC-10 | Hedge position không thay đổi khi pause | Bot đang có HL short position | Investor pause | `hedge_legs.last_known_hl_short_size` giữ nguyên; không có HL order nào được gửi | BR-EXBOT-002; UC §3 step 5 |
| AC-11 | LP NFT không thay đổi khi pause | Bot đang có LP NFT | Investor pause | `positions.token_id` giữ nguyên; không có vault transaction nào | BR-EXBOT-002; UC §3 step 6 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Pause/resume operation phải nhanh (không gọi HL API) | Test không cần mock HL trong pause/resume happy path | UC §3–4 (no HL calls mentioned) |
| Security | Investor chỉ pause/resume bot của chính mình | Cần test authorization — không thể pause bot của user khác | FR-EXBOT-001 one-bot policy (định nghĩa bot ownership) |
| Reliability / Resilience | Idempotency cho pause/resume (A2, A3 alternate flows) | Test idempotent behavior là bắt buộc | UC §5 A2, A3 |
| Audit / Logging | Audit log entries cho cả pause và resume | Test xác minh log entries tồn tại sau mỗi thao tác | UC §7 Postconditions |
| Compatibility / Integration | Pause/resume không ảnh hưởng Operator Facade endpoint list (FR-EXBOT-090 chỉ có 4 endpoints) | Endpoint names sẽ lấy từ test environment config (Q1 deferred). Không cần cập nhật spec. | FR-EXBOT-090; UC §3 step 1, §4 step 1 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q1 | Blocker | Missing | FR-EXBOT-090; UC §3 step 1, §4 step 1; spec.md §FM-XB-06 | **API endpoints pause/resume không có trong Operator Facade spec.** FR-EXBOT-090 chỉ liệt kê 4 endpoints. UC sử dụng `POST /api/exbot/pause` và `POST /api/exbot/resume` nhưng hai endpoints này không có trong spec. | Endpoint name khác nhau giữa các môi trường test — QA sẽ lấy endpoint thực tế từ test environment config. Không cần cập nhật spec. | QC Lead | **Deferred** |
| Q2 | Blocker | Missing | FR-EXBOT-010; UC §1, §3 | **"Status Update Worker" không tồn tại trong queue topology.** FR-EXBOT-010 định nghĩa đúng 11 queues. UC gọi worker xử lý pause/resume là "Status update worker" nhưng worker này không được ánh xạ vào queue nào trong SRS. Nó có phải là phần của ExBot Worker (xử lý trực tiếp API request mà không qua queue), hay là một queue consumer chưa được định nghĩa? Nếu là queue consumer, queue name là gì? Tech Lead vui lòng xác nhận kiến trúc worker: ExBot Worker xử lý pause/resume đồng bộ (không queue), hay cần một queue riêng (tên gì)? | Tester không biết worker xử lý pause/resume hoạt động như thế nào → không thể test idempotency, retry behavior | Tech Lead | Open |
| Q3 | Major | Missing | FR-EXBOT-011; UC §3–5; SRS spec.md §FR-EXBOT-011 | **Không có idempotency mechanism cho pause/resume.** FR-EXBOT-011 bắt buộc mọi queue consumer phải insert `message_id` vào `queue_idempotency` table. Tuy nhiên UC hoàn toàn không đề cập `queue_idempotency`, `message_id`, hay idempotency key cho pause/resume operation. Nếu pause/resume không qua queue mà là synchronous API handler, thì không cần queue idempotency — nhưng vẫn cần một idempotency key (ví dụ: investor gửi 2 request pause cùng lúc). UC §5 A3 mô tả idempotent response nhưng không nêu cơ chế implement. Tech Lead vui lòng xác nhận: (1) pause/resume có qua queue không? (2) nếu có, idempotency key là gì? (3) nếu không, cơ chế chống race condition là gì? | Không có idempotency → không thể test race condition scenarios | Tech Lead | Open |
| Q4 | Major | Missing | UC §4 step 5; FR-EXBOT-013; flows.md F-01 | **Jitter cho `next_light_check_at` khi resume không rõ nguồn chuẩn.** UC §4 step 5 nêu `next_light_check_at = now + 5min + jitter(−45s, +45s)`. Giá trị jitter này được tham chiếu từ FR-EXBOT-013 (light-check jitter, áp dụng cho normal scheduling). Tuy nhiên, FR-EXBOT-013 được thiết kế cho `next_light_check_at` set bởi bot-scan worker sau mỗi light-check cycle hoàn tất. Khi resume, `next_light_check_at` được set bởi Status Update Worker — cùng một jitter pattern có được áp dụng không? Có cần đặc biệt xử lý jitter khi resume (ví dụ: không có jitter, set chính xác 5 phút)? Tech Lead vui lòng xác nhận jitter value và cách tính khi resume. | Tester cần giá trị chính xác để viết test case cho timing | Tech Lead | Open |
| Q5 | Major | Missing | UC §6; FR-EXBOT-014 | **Suppression behavior cho `price-near-stop-audit` trong pause không được nêu.** UC §6 chỉ liệt kê light-check và hedge-sync bị suppress trong pause. FR-EXBOT-014 khẳng định "Stop monitoring (price-near-stop-audit enqueue) shall continue at all times — including when `circuit_breakers.state='open'`". FR-EXBOT-014 không đề cập `status='paused'`. Điều này ngụ ý `price-near-stop-audit` vẫn tiếp tục khi paused, nhưng UC không nói rõ. BA vui lòng xác nhận: khi bot đang paused, nếu giá ETH chạm `stop_price`, thì `price-near-stop-audit` message có được enqueue không? Nếu có, behavior tiếp theo là gì? | Tester không biết cần test stop monitoring behavior trong pause hay không | BA | Open |
| Q6 | Major | Missing | UC §6; FR-EXBOT-016 | **Deep-audit high-risk cadence (1 giờ) có áp dụng khi paused không?** FR-EXBOT-016 nói deep-audit chạy 1 giờ khi `circuit_breakers.state != 'closed'` hoặc `margin_status IN ('warning','critical')`. UC §6 chỉ nói "every 6-hour cadence" mà không đề cập high-risk 1 giờ. BA vui lòng xác nhận: khi bot đang paused VÀ hệ thống đang ở high-risk mode (circuit breaker open hoặc margin warning/critical), deep-audit có chạy 1 giờ thay vì 6 giờ không? | Tester không biết có cần test high-risk deep-audit frequency trong pause state | BA | Open |
| Q7 | Major | Missing | UC §2, §4; SRS states.md; UC §4 step 4 | **Valid `lifecycle_state` values cho resume không được định nghĩa.** UC §2 chỉ nói "Bot's `lifecycle_state` is unchanged from its pre-pause value (preserved in D1)" và §4 step 4 nói worker "confirms it matches expected state (e.g., 'active')". Điều này ngụ ý worker kiểm tra `lifecycle_state` giữ đúng giá trị pre-pause. Nhưng UC không nêu: (1) những giá trị nào của `lifecycle_state` được phép resume? Chỉ `'active'` hay `'hedge_stopped_cooldown'` cũng được? (2) nếu `lifecycle_state` bị corrupt/changed vì lý do nào đó, worker xử lý thế nào? Tech Lead vui lòng xác nhận valid `lifecycle_state` values cho resume. | Tester không biết valid/invalid resume scenarios | Tech Lead | Open |
| Q8 | Major | Missing | UC §3–5; BR-EXBOT-002; SRS spec.md §6 | **Branding/messaging "UI confirmation" gây nhầm lẫn với module scope.** UC nói "Investor receives UI confirmation: 'Bot paused. Hedge and LP are maintained.'" ở step 8 và "Investor receives UI confirmation: 'Bot resumed. Monitoring will resume shortly.'" ở step 7. spec.md §6 khẳng định ExBot là backend-only module, không sở hữu UI. Message này thực chất là POOL UI (PTL-05) hiển thị dữ liệu từ Operator Facade API response. Tuy nhiên, việc đưa "UI confirmation" vào UC của module backend gây confusion: tester cần test POOL UI (nằm ngoài ExBot scope) hay chỉ cần test API response? BA vui lòng xác nhận: (1) "UI confirmation" nằm trong ExBot scope hay POOL UI scope? (2) Nếu ExBot scope dừng ở API response, tester chỉ cần verify API response, không cần test POOL UI rendering. | Tester không biết scope của test — chỉ API hay cả UI | BA / QC Lead | Open |
| Q9 | Major | Missing | UC §3 step 7, §4 step 6; UC §5 A2, A3; message-list.md | **Success messages không có mã E-code hoặc message code.** UC §3 step 7 trả về "Paused — hedge is maintained, LP is maintained", §4 step 6 trả về "Bot resumed. Monitoring resumed.", A2 "Bot already active. No change needed.", A3 "Bot already paused. No change needed." Không có message code nào trong message-list.md. message-list.md chỉ có E-EXBOT-013 cho SAFE_MODE rejection. Việc thiếu message code gây khó khăn cho tester khi trace response và cho developer khi verify contract. BA vui lòng xác nhận: (1) success messages có cần message code không? (2) nếu có, mã là gì? (3) nếu không, tester chỉ verify text content của response? | Không có message code → khó trace API contract trong test | BA | Open |
| Q10 | Minor | Missing | UC §2; SRS states.md | **Không có precondition cho resume khi bot ở `lifecycle_state='lp_rebalancing'` hoặc `lifecycle_state='hedge_stopped_cooldown'`.** UC §2 chỉ nói `bots.status='paused'`. Nhưng `lifecycle_state` có thể là `'lp_rebalancing'` (bot paused giữa LP rebalance?) hoặc `'hedge_stopped_cooldown'` (bot paused sau khi stop fired). Những giá trị này được phép pause/resume không? BA vui lòng xác nhận. | Tester không biết valid lifecycle_state combinations | BA | Open |
| Q11 | Minor | Missing | FR-EXBOT-033; UC §6; SRS states.md | **SAFE_MODE entry từ pause state không rõ behavior.** UC §6 nói "SAFE_MODE entry conditions remain active" trong pause. Nhưng không nêu rõ: khi deep-audit phát hiện SAFE_MODE condition (ví dụ: `stop_trigger_crossed_at` stuck > 30 phút) trên bot đang paused, thì `bots.status` chuyển thế nào? Trực tiếp sang `safe_mode`? Hay vẫn giữ `paused` và thêm cờ safe_mode vào `lifecycle_state`? Tech Lead vui lòng xác nhận state transition khi SAFE_MODE entry từ paused. | Tester không biết state transition path khi SAFE_MODE entry từ paused | Tech Lead | Open |
| Q12 | Minor | Missing | UC §4 step 5; flows.md F-01; FR-EXBOT-012 | **Bot-scan worker có scheduling cho bot vừa resume không?** Luồng F-01 (flows.md) mô tả bot-scan worker scan `bots.status = active` và enqueue light-check messages. Khi resume, Status Update Worker set `next_light_check_at` và enqueue `light-check` trực tiếp (UC §4 step 5) — không qua bot-scan worker. Vấn đề: nếu bot-scan worker scan tất cả `status='active'` bots mỗi phút, bot vừa resume sẽ được pick up tự động. Tester cần xác nhận: sau resume, bot có được enqueue light-check ngay (UC §4 step 5) VÀ được bot-scan enqueue lần nữa không? Có duplicate message không? | Tester cần xác nhận không có duplicate light-check sau resume | Tech Lead | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| `POST /api/exbot/pause` và `POST /api/exbot/resume` endpoints | API | Endpoint names lấy từ test environment config — không cần cập nhật spec | QC Lead | **Deferred** |
| Status Update Worker architecture | Queue / Worker | Cần xác định là synchronous handler hay queue consumer | Tech Lead | Open |
| Idempotency mechanism | Data | Cần FR-EXBOT-011 compliance verification cho pause/resume | Tech Lead | Open |
| FR-EXBOT-012 light-check skip logic | Business Logic | Cần verify light-check worker check `bots.status='paused'` | Tech Lead | Open |
| FR-EXBOT-016 deep-audit pause scheduling | Business Logic | Cần verify deep-audit schedule filter bao gồm paused bots | Tech Lead | Open |
| OQ-EXBOT-13 (delta=0 behavior) | Open Question | Không ảnh hưởng trực tiếp pause/resume — chỉ liên quan hedge-sync | Tech Lead | Open |

---

## 11. Bảng chấm điểm

| Scoring Area | Tối đa | Điểm | Status | Số lượng Issues |
|---|---|---|---|---|
| Area 1: Function / Operation & Data Object Inventory | 20 | 12 | ⚠️ Partial | 4 (1 blocker, 3 major) |
| Area 2: Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 17 | ⚠️ Partial | 4 (1 major, 3 minor) |
| Area 3: Functional Logic & Workflow Decomposition | 25 | 13 | ⚠️ Partial | 5 (1 blocker, 3 major, 1 minor) |
| Area 4: Functional Integration & Data Consistency | 15 | 8 | ⚠️ Partial | 4 (1 major, 3 minor) |
| Area 5: UC / Spec Documentation Quality Issues | 15 | 8 | ⚠️ Partial | 2 (1 major, 1 minor) |
| **Tổng điểm** | **100** | **58** | **❌ Not Ready** | **11 issues (1 blocker, 8 major, 4 minor)** |

**Auto-fail triggered:** 1 blocker còn lại (Q2: Status Update Worker) ngăn Area 1 vượt cap.

**Chi tiết Area:**

- **Area 1 (12/20):** Q1 (endpoint names) đã được defer — endpoint sẽ lấy từ test environment config. Còn lại 1 blocker nghiêm trọng: Q2 — "Status Update Worker" không tồn tại trong SRS queue topology. Không xác định được worker architecture → không thể test idempotency/retry behavior. Atomic operations, emitted events, idempotency keys đều thiếu.

- **Area 2 (17/25):** Mất điểm ở missing state attributes: `next_light_check_at` jitter khi resume không rõ nguồn chuẩn; valid `lifecycle_state` values cho resume không định nghĩa; atomic persistence mechanism không nêu. Messages đầy đủ cho error path (E-EXBOT-013) nhưng success messages thiếu E-code.

- **Area 3 (13/25):** Luồng happy path pause và resume rõ ràng, suppress behavior được nêu. Mất điểm nghiêm trọng vì: thiếu idempotency mechanism (Q3), thiếu jitter spec (Q4), `price-near-stop-audit` suppression không rõ (Q5), deep-audit high-risk cadence không được nêu trong UC §6 (Q6).

- **Area 4 (8/15):** Điểm bị cap 7/15 theo rubric §8 vì F.4 generic, không identify concrete data/function impacts. Các cross-function effects (pause → light-check suppress, pause → deep-audit continue) được nêu nhưng không có chi tiết về safe_mode entry từ paused state.

- **Area 5 (8/15):** Auto-cap 8/15 từ rubric §8 vì repeated ambiguous wording và missing concrete info. Q1 defer giảm 1 blocker. Còn 1 major: "UI confirmation" references không phù hợp với ExBot backend-only scope (Q8).

---

## 12. Tóm tắt Audit

### Kết quả chấm điểm

| Area | Max | Điểm | Status |
|---|---|---|---|
| Area 1: Function / Operation & Data Object Inventory | 20 | 12 | ⚠️ Partial |
| Area 2: Data Object / State Attributes, BR, Validations & Messages | 25 | 17 | ⚠️ Partial |
| Area 3: Functional Logic & Workflow Decomposition | 25 | 13 | ⚠️ Partial |
| Area 4: Functional Integration & Data Consistency | 15 | 8 | ⚠️ Partial |
| Area 5: UC / Spec Documentation Quality Issues | 15 | 8 | ⚠️ Partial |
| **Tổng** | **100** | **58** | **❌ Not Ready** |

### Blockers (cần xử lý trước)

1. **[Q2 — Blocker]** "Status Update Worker" không có trong SRS queue topology (FR-EXBOT-010). UC gọi worker này xử lý pause/resume nhưng không xác định nó là synchronous handler trong ExBot Worker hay queue consumer. Tech Lead cần xác định kiến trúc. Không có kiến trúc worker → không thể test idempotency/retry behavior.

### Issues lớn

2. **[Q3 — Major]** Không có idempotency mechanism cho pause/resume — không biết implement như thế nào khi không qua queue.
3. **[Q4 — Major]** Jitter cho `next_light_check_at` khi resume không có nguồn chuẩn cụ thể.
4. **[Q5 — Major]** `price-near-stop-audit` suppression trong pause không được nêu trong UC §6.
5. **[Q6 — Major]** Deep-audit high-risk cadence (1 giờ) không được nêu trong UC §6.
6. **[Q7 — Major]** Valid `lifecycle_state` values cho resume không được định nghĩa.
7. **[Q8 — Major]** "UI confirmation" references gây nhầm lẫn scope giữa ExBot backend và POOL UI.

### Deferred

- **[Q1 — Blocker — Deferred]** API endpoint names không có trong FR-EXBOT-090. Endpoint name khác nhau giữa các môi trường test — QA sẽ lấy từ test environment config. Không cần cập nhật spec.

### Khuyến nghị

**Không nên tiến hành thiết kế scenario/test case cho UC-EXBOT-pause-resume cho đến khi:**

1. Tech Lead xác nhận Status Update Worker architecture — synchronous handler hay queue consumer (Q2).
2. Tech Lead xác nhận idempotency mechanism cho pause/resume (Q3).
3. BA xác nhận suppression scope cho `price-near-stop-audit` trong pause (Q5).
4. BA xác nhận deep-audit high-risk cadence có áp dụng khi paused không (Q6).
5. Tech Lead xác nhận jitter value cho `next_light_check_at` khi resume (Q4).

**Ưu tiên xử lý Q2 → Q3 → Q5 → Q6 → Q4 → Q7 → Q8. Sau khi blocker Q2 được giải quyết, UC có thể re-review và đạt điểm ≥ 70.**

**Điểm tích cực:** FR-EXBOT-005 và FR-EXBOT-012 requirements rõ ràng và nhất quán. US-EXBOT-003 AC coverage đầy đủ (happy path, deep-audit continue, SAFE_MODE rejection, idempotent responses). BR-EXBOT-002 Pause ≠ Close được tuân thủ. State suppression logic không có mâu thuẫn với SRS.

---

## 13. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Agent | Tạo báo cáo audited lần đầu cho UC-EXBOT-pause-resume. Tổng điểm: 54/100 — Not Ready. 4 blockers, 9 major, 4 minor issues. |

---

*Bản rà soát độ sẵn sàng của UC — ExBot module (no-UI) — output của qc-uc-read-exbot skill*
