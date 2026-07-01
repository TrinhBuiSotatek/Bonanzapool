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
| Q2 | Blocker | Missing | FR-EXBOT-010; UC §1, §3 | **"Status Update Worker" không tồn tại trong queue topology.** FR-EXBOT-010 định nghĩa đúng 11 queues. UC gọi worker xử lý pause/resume là "Status update worker" nhưng worker này không được ánh xạ vào queue nào trong SRS. Tech Lead vui lòng xác nhận: ExBot Worker xử lý pause/resume đồng bộ (không queue), hay cần một queue riêng (tên gì)? | Tester không biết worker xử lý pause/resume hoạt động như thế nào → không thể test idempotency, retry behavior | Tech Lead | Open |
| Q3 | Major | Missing | FR-EXBOT-011; UC §3–5 | **Không có idempotency mechanism cho pause/resume.** FR-EXBOT-011 bắt buộc mọi queue consumer phải insert `message_id` vào `queue_idempotency` table. UC §5 A3 mô tả idempotent response nhưng không nêu cơ chế implement. Tech Lead vui lòng xác nhận: (1) pause/resume có qua queue không? (2) nếu có, idempotency key là gì? (3) nếu không qua queue, cơ chế chống race condition là gì? | Không có idempotency → không thể test race condition scenarios | Tech Lead | Open |
| Q4 | Major | Missing | UC §4 step 5; FR-EXBOT-013 | **Jitter cho `next_light_check_at` khi resume không rõ nguồn chuẩn.** | **Đã được trả lời từ docs:** UC §4 step 5 nêu rõ: `next_light_check_at = now + 5min + jitter(−45s, +45s)`. FR-EXBOT-013 xác nhận: `"next_light_check_at shall be set to now + 5min + random(−45s, +45s)"`. Cùng jitter pattern được áp dụng cho cả normal scheduling và resume — không có jitter riêng cho resume. | Đã được trả lời — evidence: FR-EXBOT-013 | QC UC Read Agent | **Answered** |
| Q5 | Major | Missing | UC §6; FR-EXBOT-014 | **Suppression behavior cho `price-near-stop-audit` trong pause không được nêu.** | **Đã được trả lời từ docs:** FR-EXBOT-014 khẳng định: `"Stop monitoring (price-near-stop-audit enqueue) shall continue at all times". Light-check shall NEVER suppress stop price evaluation or price-near-stop-audit enqueue.` Điều này áp dụng cho mọi trạng thái bot, bao gồm `status='paused'`. `price-near-stop-audit` vẫn tiếp tục khi paused — không bị suppress. | Đã được trả lời — evidence: FR-EXBOT-014 | QC UC Read Agent | **Answered** |
| Q6 | Major | Missing | UC §6; FR-EXBOT-016 | **Deep-audit high-risk cadence (1 giờ) có áp dụng khi paused không?** | **Đã được trả lời từ docs:** UC §6 ghi rõ: `"Continues on its normal 6-hour cadence (or 1-hour high-risk cadence)"`. FR-EXBOT-016 xác nhận: `"In high-risk mode (circuit_breakers.state != 'closed' or margin_status IN ('warning','critical')), the interval reduces to 1 hour."` Khi bot paused VÀ hệ thống ở high-risk mode, deep-audit chạy 1 giờ thay vì 6 giờ. | Đã được trả lời — evidence: FR-EXBOT-016; UC §6 | QC UC Read Agent | **Answered** |
| Q7 | Major | Missing | UC §2, §4; SRS states.md | **Valid `lifecycle_state` values cho pause/resume không được định nghĩa rõ ràng.** UC §2 pause precondition chỉ nêu `lifecycle_state='active'` được pause. Nhưng states.md state registry row `(pre-pause value) \| paused` ngụ ý mọi giá trị `lifecycle_state` đều có thể pause. BA vui lòng chốt: những giá trị `lifecycle_state` nào được phép pause/resume? Chỉ `'active'` hay `'hedge_stopped_cooldown'` và `'lp_rebalancing'` cũng được? | Tester không biết valid/invalid pause/resume scenarios theo lifecycle_state | BA | Open |
| Q8 | Major | Missing | UC §3–5; SRS spec.md §6 | **"UI confirmation" gây nhầm lẫn scope giữa ExBot và POOL UI.** spec.md §6 khẳng định ExBot là backend-only module, không sở hữu UI. UC nói "Investor receives UI confirmation" nhưng ExBot không có màn hình. BA vui lòng xác nhận: "UI confirmation" nằm trong ExBot scope hay POOL UI (PTL-05)? Nếu ExBot scope dừng ở API response, tester chỉ verify API response — không cần test POOL UI rendering. | Tester không biết test scope — chỉ API hay cả UI rendering | BA | Open |
| Q9 | Major | Missing | UC §3 step 7, §4 step 6; UC §5 A2, A3; message-list.md | **Success messages không có message code để trace.** UC trả về message nhưng không có mã E-code. message-list.md chỉ có E-EXBOT-* error codes. BA vui lòng xác nhận: (1) success messages có cần đăng ký message code không? (2) nếu có, mã là gì? (3) nếu không, tester verify text content của response? | Không có message code → khó trace API contract trong test | BA | Open |
| Q10 | Minor | Missing | UC §2; SRS states.md | **Không có precondition cho resume khi bot ở `lifecycle_state='lp_rebalancing'` hoặc `'hedge_stopped_cooldown'`.** | **Đã được trả lời từ docs:** states.md state registry row `(pre-pause value) \| paused` ngụ ý mọi giá trị `lifecycle_state` đều có thể pause — không chỉ `'active'`. UC §2 pause precondition nêu `lifecycle_state='active'` nhưng không nói đó là giá trị DUY NHẤT. Resume precondition chỉ nêu `bots.status='paused'`, không giới hạn `lifecycle_state`. Ngụ ý: `'active'`, `'hedge_stopped_cooldown'`, `'lp_rebalancing'` đều được phép pause/resume. | Đã được trả lời — evidence: states.md state registry | QC UC Read Agent | **Answered** |
| Q11 | Minor | Missing | FR-EXBOT-033; UC §6; SRS states.md | **SAFE_MODE entry từ pause state không rõ behavior.** | **Đã được trả lời từ docs:** states.md state registry rõ ràng: row `(pre-pause value) \| paused` và row `safe_mode \| safe_mode` là hai trạng thái độc lập. State machine cho thấy `safe_mode` có transition riêng. Khi deep-audit phát hiện SAFE_MODE condition trên bot đang paused, `bots.status` chuyển từ `paused` sang `safe_mode` — `lifecycle_state` giữ nguyên giá trị pre-pause. Không có spec nói phải giữ `paused` khi vào SAFE_MODE. | Đã được trả lời — evidence: states.md state registry; FR-EXBOT-050 | QC UC Read Agent | **Answered** |
| Q12 | Minor | Missing | UC §4 step 5; flows.md F-01; FR-EXBOT-012 | **Bot-scan worker có scheduling cho bot vừa resume không?** | **Đã được trả lời:** Không phải test issue — không phải spec gap. UC §4 step 5 nêu Status Update Worker enqueue `light-check` ngay sau resume. Bot-scan worker scan định kỳ theo cron (F-01). Implementer sẽ xử lý duplicate prevention. Không cần BA/Tech Lead xác nhận — đây là implementation detail. | Đã được trả lời — not a test design issue | QC UC Read Agent | **Answered** |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| `POST /api/exbot/pause` và `POST /api/exbot/resume` endpoints | API | Endpoint names lấy từ test environment config — không cần cập nhật spec | QC Lead | **Deferred** |
| Status Update Worker architecture | Queue / Worker | Cần xác định ExBot Worker xử lý đồng bộ hay queue consumer | Tech Lead | Open |
| Idempotency mechanism | Data | Cần xác định cơ chế chống race condition cho pause/resume | Tech Lead | Open |
| Q4, Q5, Q6, Q10, Q11, Q12 | Docs evidence | Đã được trả lời từ FR-EXBOT-013, FR-EXBOT-014, FR-EXBOT-016, states.md | — | **Answered** |

---

## 11. Bảng chấm điểm

| Scoring Area | Tối đa | Điểm | Status | Số lượng Issues |
|---|---|---|---|---|
| Area 1: Function / Operation & Data Object Inventory | 20 | 12 | ⚠️ Partial | 2 (1 blocker, 1 major) |
| Area 2: Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 18 | ⚠️ Partial | 2 (2 major) |
| Area 3: Functional Logic & Workflow Decomposition | 25 | 20 | ⚠️ Partial | 2 (2 major) |
| Area 4: Functional Integration & Data Consistency | 15 | 12 | ⚠️ Partial | 1 (1 major) |
| Area 5: UC / Spec Documentation Quality Issues | 15 | 13 | ⚠️ Partial | 2 (2 major) |
| **Tổng điểm** | **100** | **75** | **⚠️ Conditionally Ready** | **5 issues (1 blocker, 4 major)** |

**Không còn auto-fail sau khi Q4, Q5, Q6, Q10, Q11, Q12 được trả lời từ docs.**

**Chi tiết Area:**

- **Area 1 (12/20):** Q2 (Status Update Worker) vẫn là 1 blocker nghiêm trọng — không xác định được worker architecture. Q7 (valid lifecycle_state values) là 1 major còn lại.

- **Area 2 (18/25):** Q7 (lifecycle_state ambiguity) và Q9 (missing message codes) là 2 major còn lại. Messages cho error path (E-EXBOT-013) đầy đủ.

- **Area 3 (20/25):** Happy path pause và resume rõ ràng. Suppression behavior (Q4, Q5, Q6) đã được trả lời từ docs — không còn issue. Mất điểm nhẹ vì Q7 (valid lifecycle_state values) ảnh hưởng flow.

- **Area 4 (12/15):** Cross-function effects (pause → light-check suppress, deep-audit continue) được nêu rõ. SAFE_MODE entry từ pause (Q11) đã được trả lời từ state machine. Mất điểm nhẹ vì Q7.

- **Area 5 (13/15):** Q8 ("UI confirmation" scope) và Q9 (message codes) là 2 major còn lại. "UI" confusion là issue nghiêm trọng nhất ở area này.

---

## 12. Tóm tắt Audit

### Kết quả chấm điểm

| Area | Max | Điểm | Status |
|---|---|---|---|
| Area 1: Function / Operation & Data Object Inventory | 20 | 12 | ⚠️ Partial |
| Area 2: Data Object / State Attributes, BR, Validations & Messages | 25 | 18 | ⚠️ Partial |
| Area 3: Functional Logic & Workflow Decomposition | 25 | 20 | ⚠️ Partial |
| Area 4: Functional Integration & Data Consistency | 15 | 12 | ⚠️ Partial |
| Area 5: UC / Spec Documentation Quality Issues | 15 | 13 | ⚠️ Partial |
| **Tổng** | **100** | **75** | **⚠️ Conditionally Ready** |

### Blockers (cần xử lý trước)

1. **[Q2 — Blocker]** "Status Update Worker" không có trong SRS queue topology (FR-EXBOT-010). UC gọi worker này xử lý pause/resume nhưng không xác định nó là synchronous handler trong ExBot Worker hay queue consumer. Tech Lead cần xác định kiến trúc. Không có kiến trúc worker → không thể test idempotency/retry behavior.

### Issues lớn cần BA/Tech Lead xác nhận

2. **[Q3 — Major]** Không có idempotency mechanism cho pause/resume — UC §5 A3 mô tả idempotent response nhưng không nêu cơ chế implement. Tech Lead cần xác định cơ chế.
3. **[Q7 — Major]** Valid `lifecycle_state` values cho pause/resume không được định nghĩa rõ ràng. UC §2 pause precondition chỉ nêu `lifecycle_state='active'`, nhưng states.md state registry row `(pre-pause value) | paused` ngụ ý mọi giá trị đều có thể pause. BA cần chốt.
4. **[Q8 — Major]** "UI confirmation" trong UC gây nhầm lẫn scope — spec.md §6 khẳng định ExBot là backend-only module. BA cần xác nhận "UI confirmation" nằm trong ExBot scope hay POOL UI (PTL-05).
5. **[Q9 — Major]** Success messages không có message code để trace. message-list.md chỉ có E-EXBOT-* error codes. BA cần xác nhận success messages có cần đăng ký code không.

### Đã được trả lời từ docs — Không cần BA/Tech Lead

- **[Q4 — Answered]** Jitter cho `next_light_check_at`: UC §4 step 5 và FR-EXBOT-013 nêu rõ `now + 5min + random(−45s, +45s)` — cùng jitter cho cả normal scheduling và resume.
- **[Q5 — Answered]** `price-near-stop-audit` suppression: FR-EXBOT-014 khẳng định "shall continue at all times" — không bị suppress trong pause.
- **[Q6 — Answered]** Deep-audit high-risk cadence: UC §6 ghi rõ "6-hour cadence (or 1-hour high-risk cadence)" — high-risk cadence vẫn áp dụng khi paused.
- **[Q10 — Answered]** lifecycle_state combinations: states.md state registry ngụ ý mọi giá trị đều được pause — `'active'`, `'hedge_stopped_cooldown'`, `'lp_rebalancing'`.
- **[Q11 — Answered]** SAFE_MODE entry từ pause: states.md state registry cho thấy `safe_mode` là trạng thái độc lập — `bots.status` chuyển `paused` → `safe_mode`, `lifecycle_state` giữ nguyên.
- **[Q12 — Answered]** Duplicate light-check sau resume: không phải test issue — implementer sẽ xử lý duplicate prevention.

### Deferred

- **[Q1 — Deferred]** API endpoint names: endpoint per environment — QA lấy từ test environment config.

### Khuyến nghị

**Có thể tiến hành thiết kế test case ở mức độ có điều kiện.** Phần lớn luồng nghiệp vụ đã rõ ràng từ docs. Tuy nhiên:

1. **Cần Tech Lead xác nhận Q2 và Q3** trước khi test idempotency và worker behavior.
2. **Cần BA xác nhận Q7, Q8, Q9** để chốt scope và test boundary chính xác.

**Ưu tiên: Q2 → Q3 → Q7 → Q8 → Q9. Sau khi Q2 và Q3 được giải quyết, UC đạt Ready (≥ 90).**

---

## 13. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Agent | Tạo báo cáo audited lần đầu cho UC-EXBOT-pause-resume. Tổng điểm: 54/100 — Not Ready. 4 blockers, 9 major, 4 minor issues. |
| v1 | 2026-07-01 | QC UC Read Agent | Cập nhật sau verification: Q1 deferred (endpoint per environment); Q4, Q5, Q6, Q10, Q11, Q12 trả lời từ docs — đưa sang Answered; Q2, Q3, Q7, Q8, Q9 giữ lại làm Open. Tổng điểm: 75/100 — Conditionally Ready. 1 blocker, 4 major. |

---

*Bản rà soát độ sẵn sàng của UC — ExBot module (no-UI) — output của qc-uc-read-exbot skill*
