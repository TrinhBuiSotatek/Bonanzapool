---
title: "Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-pause-resume"
date: 2026-06-18
author: qc-uc-read-exbot
version: v1
---

# Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-pause-resume

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-pause-resume mô tả hai hành động do nhà đầu tư USDC thực hiện trực tiếp: tạm dừng bot (`pause`) và tiếp tục bot (`resume`). Khác với đóng bot hoàn toàn (`bot_safe_close`), tạm dừng không thanh lý vị thế hedge hay LP NFT — bot vẫn giữ nguyên trạng thái trên Hyperliquid và trong BnzaExVault, chỉ ngừng thực hiện các tác vụ tự động mới như light-check và hedge-sync. Deep-audit vẫn tiếp tục mỗi 6 giờ. Mục đích nghiệp vụ là cho phép nhà đầu tư tạm dừng hoạt động trong điều kiện thị trường ngắn hạn mà không cần đóng và mở lại vị thế.

Điều kiện tiên quyết để tạm dừng là bot phải đang ở `bots.status='active'`. Điều kiện tiên quyết để tiếp tục là bot phải đang ở `bots.status='paused'`. Bot ở trạng thái `safe_mode` không thể tạm dừng — hệ thống trả về lỗi E-EXBOT-013 (HTTP 409). Đây là ranh giới quan trọng: `BR-EXBOT-002` yêu cầu UI phân biệt rõ "Pause" (giữ hedge + LP) và "Close" (thanh lý tất cả), bao gồm label và nội dung thông báo khác nhau.

Điểm quan trọng cho thiết kế test: (1) UC chỉ thay đổi `bots.status` — `bots.lifecycle_state` không được chỉnh sửa trong suốt vòng đời pause/resume; (2) sau khi resume, `bots.next_light_check_at` được lên lịch trong 5 phút với jitter `±45s` và một message `light-check` được đưa vào queue; (3) UC-EXBOT-pause-resume liên quan đến UC-EXBOT-light-check (light-check skip logic) và UC-EXBOT-bot-safe-close (phân biệt hai hành động).

---

## Bảng mã viết tắt

> **Lưu ý về đánh số FR:** frd.md dùng `FR-EXBOT-003` cho tính năng Pause/Resume; srs/spec.md dùng `FR-EXBOT-005` cho cùng tính năng này. UC §9 cite FR-EXBOT-005 (đúng với spec.md là nguồn sự thật); US-EXBOT-003 §Trace cite FR-EXBOT-003 (theo frd.md). Báo cáo này dùng số theo spec.md: FR-EXBOT-005. Xem I-006.


| Mã / Tiền tố | Ý nghĩa và vai trò trong dự án | Nguồn |
|---|---|---|
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng của module ExBot. Là nguồn sự thật về hành vi hệ thống. | srs/spec.md |
| BR-EXBOT-* | Business Rule — quy tắc nghiệp vụ bắt buộc toàn module. | srs/spec.md §4 |
| E-EXBOT-* | Error Code — mã lỗi chuẩn của ExBot, được resolve thành nội dung message và HTTP status cụ thể. | srs/spec.md §5 |
| UC-EXBOT-* | Use Case — tài liệu mô tả luồng xử lý của một tính năng cụ thể trong module ExBot. | usecases/ |
| US-EXBOT-* | User Story — câu chuyện người dùng kèm Acceptance Criteria. | userstories/ |
| D1 | Cloudflare D1 — cơ sở dữ liệu SQLite serverless dùng làm off-chain state store của ExBot. | srs/erd.md |
| HL | Hyperliquid — sàn giao dịch perpetual nơi ExBot mở/duy trì vị thế short ETH-USD. | srs/spec.md |
| LP NFT | Liquidity Provider Non-Fungible Token — token đại diện cho vị thế thanh khoản Uniswap V3, được giữ trong BnzaExVault. | srs/erd.md |

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-pause-resume | Pause and Resume Bot | v1 (2026-06-18) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | QC Lead | 2026-06-18 | 2026-06-18 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| usecases/uc-pause-resume.md | 2026-06-18 | UC chính | |
| userstories/us-003.md | 2026-06-12 | User Story liên kết | |
| srs/spec.md | 2026-06-18 | SRS — nguồn sự thật | FR-EXBOT-005, BR-EXBOT-002, E-EXBOT-013 |
| srs/states.md | 2026-06-18 | State diagram | Xác nhận trạng thái paused |
| srs/erd.md | 2026-06-12 | ERD | Xác nhận cấu trúc bảng bots, bot_runtime_state |
| srs/flows.md | 2026-06-12 | Flow diagram | Không có flow riêng cho pause/resume |
| frd.md | 2026-06-18 | FRD | FR-EXBOT-003 (frd numbering) |
| usecases/index.md | 2026-06-12 | UC index | |


---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-pause-resume cho phép nhà đầu tư USDC tạm dừng hoạt động tự động của bot mà không đóng vị thế, nhằm tránh các tác động không mong muốn từ biến động thị trường ngắn hạn. Sau khi tình hình ổn định, nhà đầu tư có thể tiếp tục bot và hệ thống tự động lên lịch lại light-check trong vòng 5 phút.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Tạm dừng bot (pause) | Đặt `bots.status='paused'`, không thay đổi `lifecycle_state`, không đóng hedge hoặc LP | UC §3, FR-EXBOT-005 |
| Tiếp tục bot (resume) | Đặt `bots.status='active'`, lên lịch light-check trong 5 phút, enqueue `light-check` message | UC §4, FR-EXBOT-005 |
| Từ chối tạm dừng trong SAFE_MODE | HTTP 409, E-EXBOT-013 | UC §5 A1, E-EXBOT-013 |
| Xử lý idempotent | Tạm dừng bot đã paused → thành công không thay đổi; tiếp tục bot đã active → thành công không thay đổi | UC §5 A2, A3 |
| Hành vi suppression trong pause | Light-check và hedge-sync bị tắt; deep-audit tiếp tục mỗi 6h | UC §6, FR-EXBOT-012 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Đóng bot (bot_safe_close, user_redeem) | UC riêng biệt | Không ảnh hưởng |
| Deep-audit logic chi tiết | UC riêng (chưa có uc-deep-audit) | Tester không cần test logic deep-audit ở đây |
| UI/Screen rendering | ExBot là backend-only, không có UI scope | Không ảnh hưởng đến backend test |
| Admin force-pause | UC §1 chỉ liệt kê Investor là Primary actor | Chưa rõ admin có thể pause không — xem I-003 |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Gửi request pause/resume qua POOL UI → Operator API | Chỉ được pause/resume bot của chính mình; không thể pause trong safe_mode | UC §1, BR-EXBOT-002 |
| ExBot System Operator / Status Worker | Secondary | Nhận request từ Operator Facade, truy vấn D1, cập nhật `bots.status`, lên lịch light-check | Không có giới hạn đặc biệt | UC §1 |
| Hyperliquid (HL) | System | Không bị gọi trong pause/resume — HL short được duy trì nguyên trạng | Read-only theo UC §1; thực tế không có HL call nào | UC §1 |
| BnzaExVault | System | Không bị gọi trong pause/resume — LP NFT được duy trì nguyên trạng | Read-only theo UC §1 | UC §1 |
| D1 | System | Lưu trữ `bots.status`, `bots.lifecycle_state`, `bots.next_light_check_at` | — | srs/erd.md |

**Nhận xét readiness:** Actor đã đủ rõ. Tuy nhiên, chưa xác định rõ Operator Admin có thể thực hiện force-pause/resume không — điều này ảnh hưởng đến test design quyền hạn (xem I-003).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot tồn tại và thuộc về nhà đầu tư đang request | Yes | UC §2 |
| 2 | **Pause:** `bots.status='active'` | Yes | UC §2 |
| 3 | **Pause:** `bots.lifecycle_state='active'` (UC yêu cầu) | ⚠️ Chưa xác nhận (xem I-001) | UC §2 — nhưng SRS FR-EXBOT-005 không có ràng buộc này |
| 4 | **Pause:** Bot KHÔNG ở `status='safe_mode'` | Yes | UC §2, E-EXBOT-013 |
| 5 | **Resume:** `bots.status='paused'` | Yes | UC §2 |
| 6 | **Resume:** `bots.lifecycle_state` không thay đổi kể từ lúc pause (vẫn lưu trong D1) | Yes | UC §2, FR-EXBOT-005 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống sau khi hoàn tất | Nguồn |
|---|---|---|
| Pause thành công | `bots.status='paused'` trong D1; `bots.lifecycle_state` không thay đổi; HL short giữ nguyên; LP NFT giữ nguyên; API trả về `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }` | UC §3, FR-EXBOT-005 |
| Resume thành công | `bots.status='active'` trong D1; `lifecycle_state` không thay đổi; `bots.next_light_check_at` được đặt trong 5 phút ± 45 giây; message `light-check` được enqueue; API trả về `{ status: "active", message: "Bot resumed. Monitoring resumed." }` | UC §4, FR-EXBOT-005 |
| Pause bị từ chối (SAFE_MODE) | Không có thay đổi trạng thái; API trả về HTTP 409, E-EXBOT-013 | UC §5 A1 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng tạm dừng bot (Pause Flow)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Investor | Gửi `POST /api/exbot/pause` với `botId` | Operator Facade nhận và chuyển tiếp qua service binding đến ExBot Worker | — | Bot không tồn tại hoặc không thuộc user: chưa được mô tả (xem I-004) | UC §3 bước 1 |
| 2 | Status Worker | Truy vấn D1: xác minh `bots.status='active'` và `lifecycle_state='active'` | D1 trả về bản ghi bot | `status='safe_mode'` → A1; `status='paused'` → A3 | `status='closing'` hoặc `status='error'`: chưa được mô tả (xem I-005) | UC §3 bước 2 |
| 3 | Status Worker | Đặt `bots.status='paused'`, lưu vào D1 theo kiểu atomic | `bots.status='paused'` được ghi | — | D1 write failure: chưa mô tả | UC §3 bước 3 |
| 4 | Status Worker | Không chỉnh sửa `bots.lifecycle_state` | `lifecycle_state` giữ nguyên giá trị trước khi pause (ví dụ `'active'`) | — | — | UC §3 bước 4, FR-EXBOT-005 |
| 5 | System | HL short position (`hedge_legs`) không bị thay đổi | Giá trị `last_known_hl_short_size` giữ nguyên | — | — | UC §3 bước 5 |
| 6 | System | LP NFT (`positions.token_id`) không bị thay đổi | Token ID trong D1 giữ nguyên | — | — | UC §3 bước 6 |
| 7 | Status Worker | Trả về response thành công | `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }` | — | — | UC §3 bước 7 |
| 8 | Investor | Nhận xác nhận qua UI | UI hiển thị "Bot paused. Hedge and LP are maintained." | — | — | UC §3 bước 8 |

**A1 — Pause bị từ chối vì SAFE_MODE:**
- Tiền điều kiện: `bots.status='safe_mode'`
- Worker truy vấn D1, phát hiện `safe_mode`
- Trả về HTTP 409, E-EXBOT-013: "Bot is in Safe Mode. You can close the bot instead."
- Không có thay đổi trạng thái

**A3 — Pause idempotent (đã paused):**
- Tiền điều kiện: `bots.status='paused'`
- Worker trả về thành công: "Bot already paused. No change needed."
- Không có thay đổi trạng thái

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.status` | Phải là `'active'` tại thời điểm pause | Yes | Tiếp tục luồng | Tùy giá trị: `safe_mode` → E-EXBOT-013; `paused` → idempotent; trạng thái khác → chưa xác định (I-005) | UC §2, UC §5 |
| `bots.lifecycle_state` | UC §2 yêu cầu phải là `'active'`; SRS FR-EXBOT-005 không có ràng buộc này | ⚠️ Cần xác nhận (I-001) | — | — | UC §2, FR-EXBOT-005 |
| BR-EXBOT-002 | Pause ≠ Close. Pause giữ hedge và LP; chỉ ngừng mutation mới. Close thanh lý tất cả. UI phải dùng label riêng biệt. (Nguồn: srs/spec.md §4 BR-EXBOT-002) | P0 | Label "Pause Bot (hedge is maintained)" | Nếu UI dùng cùng label với Close → vi phạm BR-EXBOT-002 | BR-EXBOT-002 |
| `bots.status` write | Phải là atomic (không cho phép race condition giữa hai pause requests) | Yes | Một trong hai requests thắng; request còn lại nhận idempotent response | Race condition chưa được mô tả trong UC | UC §3 bước 3 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Pause thành công | API success response | `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }` | FR-EXBOT-005 AC | srs/spec.md FR-EXBOT-005 |
| Pause trong SAFE_MODE | API error response HTTP 409 | "Bot is in Safe Mode. You can close the bot instead." | E-EXBOT-013 | srs/spec.md §5 |
| Pause idempotent (đã paused) | API success response | "Bot already paused. No change needed." | UC §5 A3 | uc-pause-resume.md §5 |
| UI confirmation sau pause | Thông báo hiển thị trên UI | "Bot paused. Hedge and LP are maintained." | UC §3 bước 8 | uc-pause-resume.md §3 |

---

### 6.2 Luồng tiếp tục bot (Resume Flow)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Investor | Gửi `POST /api/exbot/resume` với `botId` | Operator Facade nhận và chuyển tiếp đến ExBot Worker | — | Bot không tồn tại: chưa mô tả (I-004) | UC §4 bước 1 |
| 2 | Status Worker | Truy vấn D1: xác minh `bots.status='paused'` | D1 trả về bản ghi bot | `status='active'` → A2 (idempotent) | Trạng thái khác: chưa mô tả (I-005) | UC §4 bước 2 |
| 3 | Status Worker | Khôi phục `bots.status='active'`, lưu atomic vào D1 | `bots.status='active'` được ghi | — | D1 write failure: chưa mô tả | UC §4 bước 3 |
| 4 | Status Worker | Đọc `lifecycle_state` hiện tại từ D1, xác nhận chưa thay đổi | `lifecycle_state` vẫn là giá trị trước khi pause | — | Nếu `lifecycle_state` khác expected: chưa mô tả xử lý tiếp theo (I-002) | UC §4 bước 4 |
| 5 | Status Worker | Lên lịch `bots.next_light_check_at = now + 5min + jitter(−45s, +45s)`; enqueue message `light-check` | D1 được cập nhật; light-check queue nhận message | — | Enqueue failure: chưa mô tả | UC §4 bước 5 — **Lưu ý: column sai, xem I-007** |
| 6 | Status Worker | Trả về response thành công | `{ status: "active", message: "Bot resumed. Monitoring resumed." }` | — | — | UC §4 bước 6 |
| 7 | Investor | Nhận xác nhận qua UI | UI hiển thị "Bot resumed. Monitoring will resume shortly." | — | — | UC §4 bước 7 |

**A2 — Resume idempotent (đã active):**
- Tiền điều kiện: `bots.status='active'`
- Worker trả về thành công: "Bot already active. No change needed."
- Không có thay đổi trạng thái, không enqueue light-check

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.status` | Phải là `'paused'` tại thời điểm resume | Yes | Tiếp tục luồng | `status='active'` → idempotent; trạng thái khác → chưa xác định (I-005) | UC §2, UC §5 |
| `bots.lifecycle_state` | Phải giữ nguyên giá trị kể từ khi pause | Yes | Không cần thay đổi | Nếu `lifecycle_state` thay đổi trong khi pause: hành vi hệ thống chưa được mô tả (I-002) | UC §4 bước 4 |
| next_light_check_at scheduling | `now + 5min + random(−45s, +45s)` | Yes | Light-check được lên lịch, message enqueued | Không có fallback nếu jitter tạo ra giá trị âm | FR-EXBOT-005 AC, FR-EXBOT-013 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Resume thành công | API success response | `{ status: "active", message: "Bot resumed. Monitoring resumed." }` | FR-EXBOT-005 AC | srs/spec.md FR-EXBOT-005 |
| Resume idempotent (đã active) | API success response | "Bot already active. No change needed." | UC §5 A2 | uc-pause-resume.md §5 |
| UI confirmation sau resume | Thông báo hiển thị trên UI | "Bot resumed. Monitoring will resume shortly." | UC §4 bước 7 | uc-pause-resume.md §4 |

---

### 6.3 Hành vi suppression trong khi pause

| Tác vụ tự động | Hành vi khi `status='paused'` | Nguồn |
|---|---|---|
| Light-check | Bị bỏ qua hoàn toàn — không chạy, không enqueue hedge-sync | FR-EXBOT-012 ("skip entirely when status='paused'") |
| Hedge-sync | Không được trigger hoặc xử lý — vì light-check đã bị skip | UC §6, FR-EXBOT-012 |
| Đánh giá RebalanceReason | Không được thực hiện (drift_threshold, range_out, v.v.) | UC §6 |
| Deep-audit | Tiếp tục theo chu kỳ 6 giờ bình thường (hoặc 1 giờ khi có rủi ro cao) | UC §6, FR-EXBOT-005 |
| SAFE_MODE detection | Vẫn hoạt động trong deep-audit — bất thường như stop stuck > 30 phút vẫn được phát hiện | UC §6 |
| Stop monitoring (price-near-stop-audit) | UC §6 không đề cập rõ — xem I-008 | UC §6, FR-EXBOT-014 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Đặt `bots.status='paused'` | UC-EXBOT-light-check | Light-check worker phải skip bot này — đọc `bots.status` và bỏ qua nếu là `paused` | Kiểm tra: sau khi pause, bot không xuất hiện trong danh sách được enqueue light-check | FR-EXBOT-012 |
| Đặt `bots.status='paused'` | Cron scan worker (bot-scan) | Scan worker đọc `bots WHERE status='active'` — bot đã paused không còn trong kết quả | Kiểm tra: `bot-scan` không enqueue light-check cho bot paused | srs/flows.md F-01, frd.md FR-EXBOT-010 |
| Đặt `bots.status='paused'` | Deep-audit cron (mỗi 6h) | Deep-audit vẫn chạy cho bot paused | Kiểm tra: deep-audit queue vẫn nhận bot paused | FR-EXBOT-005, UC §6 |
| Đặt `bots.status='active'` + enqueue light-check (resume) | UC-EXBOT-light-check | Light-check worker sẽ nhận và xử lý bot resumed trong chu kỳ tiếp theo | Kiểm tra: `bots.next_light_check_at` được set đúng, message trong light-check queue | FR-EXBOT-005, FR-EXBOT-013 |
| Bot ở `status='paused'` khi deep-audit phát hiện SAFE_MODE condition | UC-EXBOT-bot-safe-close (tiềm năng) | Deep-audit vẫn có thể kích hoạt SAFE_MODE kể cả khi bot đang paused | Kiểm tra: SAFE_MODE detection không bị block bởi trạng thái paused | UC §6, FR-EXBOT-005 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given — điều kiện | When — hành động | Then — kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Pause thành công | Bot có `status='active'`, `lifecycle_state='active'`, không ở safe_mode | Investor gửi `POST /api/exbot/pause` với botId hợp lệ | `bots.status='paused'` trong D1; `lifecycle_state` không thay đổi; API trả về `{ status: "paused", message: "Paused — hedge is maintained, LP is maintained" }` | UC §3, FR-EXBOT-005 AC |
| AC-02 | Resume thành công | Bot có `status='paused'` | Investor gửi `POST /api/exbot/resume` với botId hợp lệ | `bots.status='active'` trong D1; `bots.next_light_check_at` set trong 5 phút ± 45 giây; message `light-check` được enqueue; API trả về `{ status: "active", message: "Bot resumed. Monitoring resumed." }` | UC §4, FR-EXBOT-005 AC |
| AC-03 | Pause bị từ chối trong SAFE_MODE | Bot có `status='safe_mode'` | Investor gửi `POST /api/exbot/pause` | HTTP 409; message: "Bot is in Safe Mode. You can close the bot instead."; không có thay đổi trạng thái | E-EXBOT-013; Lưu ý: US-003 AC-003-4 dùng "already in Safe Mode" — sai với message gốc (I-009) |
| AC-04 | Pause idempotent | Bot đã có `status='paused'` | Investor gửi `POST /api/exbot/pause` lần thứ hai | Trả về thành công; "Bot already paused. No change needed."; không thay đổi trạng thái | UC §5 A3 |
| AC-05 | Resume idempotent | Bot có `status='active'` | Investor gửi `POST /api/exbot/resume` | Trả về thành công; "Bot already active. No change needed."; không enqueue light-check | UC §5 A2 |
| AC-06 | Deep-audit tiếp tục trong pause | Bot có `status='paused'`; thời điểm deep-audit đến | Cron deep-audit chạy | Deep-audit worker xử lý bot này; bất thường được báo cáo vào notification queue | US-003 AC-003-3, FR-EXBOT-005 |
| AC-07 | Light-check bị skip trong pause | Bot có `status='paused'` | Cron scan chạy và enqueue light-check cycle | Bot paused KHÔNG xuất hiện trong light-check queue | FR-EXBOT-012 |
| AC-08 | HL short không bị thay đổi sau pause | Bot có `status='paused'`; HL short đang mở tại size X | Hệ thống kiểm tra sau khi pause | `hedge_legs.last_known_hl_short_size` vẫn = X; không có order HL nào được gửi | UC §3 bước 5 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Pause/Resume là D1 write đơn giản — không có SLA riêng trong tài liệu | Không cần test SLA đặc biệt | Không tìm thấy NFR riêng cho pause/resume |
| Security | Investor chỉ được pause/resume bot của chính mình | Test: pause bot của user khác phải bị từ chối | UC §2 (implied); không có NFR rõ ràng trong tài liệu |
| Reliability / Resilience | Atomic write cho `bots.status` | Test: không có race condition khi nhiều requests đến cùng lúc | UC §3 bước 3 |
| Audit / Logging | UC §7 đề cập "Audit log entry recorded" nhưng không có column D1 hay FR nào hỗ trợ | Tester không thể verify audit log — xem I-003 | UC §7 Postconditions |
| Privacy / Compliance | N/A — không có PII trong luồng pause/resume | — | — |
| Compatibility / Integration | Resume phải enqueue light-check message tương thích với light-check queue consumer | Test: light-check consumer xử lý được message sau resume | FR-EXBOT-010, FR-EXBOT-012 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-001 | High | CROSS_SOURCE_CONFLICT | UC §2 Preconditions vs srs/spec.md FR-EXBOT-005 | UC §2 yêu cầu `bots.lifecycle_state='active'` là điều kiện tiên quyết để pause. Tuy nhiên, SRS FR-EXBOT-005 chỉ nêu "set `bots.status='paused'` while leaving `lifecycle_state` at its pre-pause value" — không có ràng buộc `lifecycle_state` phải là `'active'`. Một bot hợp lệ có thể có `status='active'` nhưng `lifecycle_state='hedge_stopped_cooldown'` (đang trong thời gian chờ sau khi stop kích hoạt). BA cần xác nhận: pause có cho phép khi `lifecycle_state != 'active'` không? Nếu có, UC §2 cần bỏ ràng buộc này. Nếu không, FR-EXBOT-005 cần bổ sung. | Tester không thể thiết kế test case cho trạng thái `lifecycle_state='hedge_stopped_cooldown'` + `status='active'` mà biết kết quả mong đợi là gì. | BA | Open |
| I-002 | High | UNCLEAR_INFO | UC §4 Resume bước 4 | UC §4 bước 4 ghi: "Worker reads pre-pause `lifecycle_state` from D1 (unchanged) — confirms it matches expected state (e.g., `'active'`)". Cụm "confirms it matches expected state" không rõ ràng: hệ thống kiểm tra với giá trị nào? Nếu `lifecycle_state` bị thay đổi trong khi bot đang pause (ví dụ deep-audit gây ra transition), hành vi tiếp theo là gì? Có block resume không? Có throw error không? | Tester không thể viết test case với expected result rõ ràng cho bước xác nhận `lifecycle_state`. | BA / Tech Lead | Open |
| I-003 | Medium | MISSING_INFO | UC §7 Postconditions vs srs/erd.md | UC §7 Postconditions ghi "Audit log entry recorded: 'Bot paused by investor'" và "Bot resumed by investor". Tuy nhiên, `srs/erd.md` không có bảng audit log nào trong ERD, và không có FR nào trong SRS/FRD định nghĩa việc ghi audit log cho pause/resume. BA/Tech Lead cần xác nhận: audit log được ghi vào bảng nào? Nếu chưa có schema, cần thêm bảng audit_log vào ERD. | Tester không thể verify expected result về audit log. | BA / Tech Lead | Open |
| I-004 | High | MISSING_INFO | UC §3 bước 1, UC §4 bước 1 | Cả hai luồng (pause và resume) không có alternate flow cho trường hợp `botId` không tồn tại hoặc bot thuộc về user khác. BA cần xác nhận: HTTP status và message khi botId không hợp lệ hoặc không thuộc sở hữu của investor? Đây là bảo vệ authorization cơ bản. | Tester không thể thiết kế test case bảo mật (tấn công IDOR — Insecure Direct Object Reference) mà không biết expected response. | BA / Tech Lead | Open |
| I-005 | Medium | MISSING_INFO | UC §5 Alternate Flows | UC §5 chỉ mô tả 3 alternate flow: A1 (pause trong safe_mode), A2 (resume bot đã active), A3 (pause bot đã paused). Chưa có alternate flow cho các trường hợp: pause/resume bot có `status='closing'`; pause/resume bot có `status='error'`. BA cần xác nhận hành vi cho các trường hợp này. | Tester không có expected result cho trạng thái `closing` và `error`. | BA | Open |
| I-006 | High | CROSS_SOURCE_CONFLICT | frd.md FR-EXBOT-003 vs srs/spec.md FR-EXBOT-005 | `frd.md` định nghĩa tính năng Pause/Resume tại `FR-EXBOT-003`, trong khi `srs/spec.md` định nghĩa cùng tính năng tại `FR-EXBOT-005`. UC §9 FR Trace cite `FR-EXBOT-005` (đúng với spec.md); US-EXBOT-003 §Trace cite `FR-EXBOT-003` (theo frd.md). Hai nguồn dùng số FR khác nhau cho cùng một tính năng gây nhầm lẫn traceability. BA cần đồng bộ số FR giữa frd.md và spec.md. | Tester tìm kiếm "FR-EXBOT-005" trong frd.md sẽ không thấy, gây hiểu nhầm tính năng không có FR. | BA | Open |
| I-007 | High | CROSS_SOURCE_CONFLICT | UC §4 Resume bước 5 vs srs/erd.md bảng bots | UC §4 bước 5 ghi: "set `bot_runtime_state.next_light_check_at` to `now + 5min + jitter(−45s, +45s)`". Tuy nhiên, `srs/erd.md` cho thấy `next_light_check_at` là column của bảng `bots`, không phải `bot_runtime_state`. Bảng `bot_runtime_state` không có column này. Column của `bot_runtime_state` liên quan đến thời gian là `last_light_check_at` (lần cuối chạy), không phải lần tiếp theo. BA cần xác nhận: UC §4 bước 5 nên đọc là "set `bots.next_light_check_at`" thay vì `bot_runtime_state.next_light_check_at`. | Tester sẽ kiểm tra sai bảng D1 nếu theo UC. | BA | Open |
| I-008 | Medium | MISSING_INFO | UC §6 Suppression Behavior vs FR-EXBOT-014 | UC §6 nêu rõ light-check và hedge-sync bị tắt khi pause, deep-audit tiếp tục. Nhưng không đề cập `stop monitoring` (`price-near-stop-audit` queue). Theo FR-EXBOT-014: "Stop monitoring continues at ALL times including when `circuit_breakers.state='open'`." Câu hỏi: stop monitoring có tiếp tục khi bot ở `status='paused'` không? Nếu có, UC §6 cần bổ sung mục này. | Tester không biết có cần test stop monitoring khi bot paused không. | BA | Open |
| I-009 | Low | INTERNAL_INCONSISTENCY | US-EXBOT-003 AC-003-4 vs srs/spec.md E-EXBOT-013 | US-EXBOT-003 AC-003-4 mô tả message từ chối pause trong SAFE_MODE là: "Bot is already in Safe Mode. You can close the bot instead." Nhưng E-EXBOT-013 verbatim trong spec.md §5 là: "Bot is in Safe Mode. You can close the bot instead." (không có chữ "already"). Hai nguồn mâu thuẫn về nội dung message. BA cần xác nhận message chính xác cần implement. | Tester sẽ không biết expected message nào là đúng khi viết assertion. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| FR-EXBOT-005 (spec.md) vs FR-EXBOT-003 (frd.md) đồng bộ số FR | UC | Traceability bị gãy giữa hai nguồn | BA | Open |
| srs/erd.md cần xác nhận column `bots.next_light_check_at` (không phải `bot_runtime_state`) | Data / UC | Tester kiểm tra sai bảng nếu không xác nhận | BA / Tech Lead | Open |
| Schema audit log chưa tồn tại trong ERD | Data | Tester không thể verify postcondition về audit log | BA / Tech Lead | Open |
| OQ-EXBOT-04 (frd.md §9): HL ETH-USD perp minimum order size — ảnh hưởng đến hedge behavior trong UC liên quan | Integration | Không ảnh hưởng trực tiếp pause/resume (không có HL call) | BA / zen | Open |

---

## 10.3 Tóm tắt đánh giá mức độ sẵn sàng

### Bảng điểm

| # | Khu vực đánh giá | Điểm tối đa | Điểm đánh giá | Trạng thái | Lý do |
|---:|---|---:|---:|---|---|
| 1 | Inventory chức năng, API, trigger, data object, state, event | 20 | 16 | ⚠️ Partial | Các chức năng, trigger, state, message đã được liệt kê đầy đủ. Trừ điểm: column D1 bị cite sai (I-007); flows.md không có flow riêng cho pause/resume |
| 2 | Business rules, validation, precondition, messages | 25 | 18 | ⚠️ Partial | BR-EXBOT-002 và E-EXBOT-013 được resolve đúng. Trừ điểm: precondition `lifecycle_state='active'` mâu thuẫn với SRS (I-001); message I-009 mâu thuẫn giữa US-003 và spec.md; missing alternate flows cho closing/error states (I-005) |
| 3 | Luồng xử lý (happy, alternate, exception) | 25 | 17 | ⚠️ Partial | Happy path và các idempotent flow được mô tả rõ. Trừ điểm: không có alternate flow cho botId không tồn tại/không thuộc sở hữu (I-004); không có error handling cho D1 write failure; stop monitoring behavior trong pause chưa xác định (I-008) |
| 4 | Tích hợp và nhất quán dữ liệu | 15 | 12 | ⚠️ Partial | Ảnh hưởng đến light-check, cron scan, deep-audit được phân tích rõ. Trừ điểm: audit log không có backing schema (I-003) |
| 5 | Chất lượng tài liệu UC / Spec | 15 | 9 | ⚠️ Partial | Cấu trúc UC tốt, BR và E code được cite đúng. Trừ điểm: mâu thuẫn đánh số FR (I-006); precondition sai so với SRS (I-001); column D1 sai (I-007); message mâu thuẫn (I-009) |
| **Tổng** | | **100** | **72** | | |

### Kết luận

**Verdict: ⚠️ Conditionally Ready (72/100)**

UC-EXBOT-pause-resume có cấu trúc rõ ràng, happy path và các idempotent path được mô tả đủ để bắt đầu thiết kế test cho các kịch bản chính. Tuy nhiên, có **4 vấn đề mức High** cần được BA giải quyết trước khi thiết kế test case hoàn chỉnh:

- **I-001**: Mâu thuẫn precondition `lifecycle_state='active'` với SRS — ảnh hưởng đến test case với lifecycle state khác
- **I-004**: Thiếu alternate flow cho botId không hợp lệ / không thuộc sở hữu — thiếu test case bảo mật IDOR
- **I-006**: Mâu thuẫn đánh số FR giữa frd.md và spec.md — ảnh hưởng traceability
- **I-007**: Column D1 bị cite sai (`bot_runtime_state` vs `bots`) — ảnh hưởng trực tiếp đến test assertion

Không có Blocker. Tester có thể bắt đầu với AC-01 đến AC-08 trong khi BA xử lý các câu hỏi mở trên.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-18 | qc-uc-read-exbot | Tạo báo cáo audited lần đầu |
