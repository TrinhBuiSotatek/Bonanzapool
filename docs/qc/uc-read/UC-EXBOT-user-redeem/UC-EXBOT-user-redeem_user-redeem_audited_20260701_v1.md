# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tên tài liệu:** UC-EXBOT-user-redeem Readiness Review
**Ngày tạo:** 2026-07-01
**Người tạo / Agent:** QC UC Read ExBot Agent
**Version:** v1

---

## Feature Brief - Tóm tắt nghiệp vụ

UC-EXBOT-user-redeem mô tả luồng nhà đầu tư (Investor) tự đóng ExBot và rút vốn bằng cách gọi hàm `BnzaExVault.redeem(tokenId)` trực tiếp trên blockchain. Đây là luồng "LP-first" — vị thế LP trên Uniswap V3 được thanh lý ngay trong cùng transaction on-chain, và phần USDC từ LP (LP-portion) được trả lại cho nhà đầu tư ngay lập tức theo business rule bất điều kiện (BR-EXBOT-006). Phần USDC từ vị thế hedge trên Hyperliquid (HL-portion) được gửi về sau, sau khi Worker đóng vị thế hedge HL thành công.

Worker nhận sự kiện redeem qua event watcher, enqueue vào `user_redeem` queue (priority cao nhất), và phải hoàn thành đóng hedge trong vòng 5 phút kể từ thời điểm phát hiện sự kiện (NFR-EXBOT-003). Nếu quá SLA, admin được cảnh báo qua E-EXBOT-010. Nếu đóng hedge thất bại sau khi LP đã thanh lý, hệ thống chuyển sang trạng thái `residual_hl_liability` và thông báo admin — không được phép rollback hoặc block LP-portion đã trả.

UC này là một trong hai hệ thống đóng bot (FR-EXBOT-070): `user_redeem` (LP-first, do nhà đầu tư khởi tạo) và `bot_safe_close` (hedge-first, do hệ thống/operator khởi tạo). Cả hai đều được theo dõi qua bảng `close_operations` với `idempotency_key UNIQUE` để ngăn double settlement.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-user-redeem | User-Initiated LP-First Redemption | Draft | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-29 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| uc-user-redeem.md | 2026-06-29 | UC | File UC chính |
| us-004.md | 2026-06-12 | User Story | US-EXBOT-004, linked story |
| frd.md | 2026-06-29 | FRD | FR-EXBOT-070 (two close systems) |
| srs/spec.md | 2026-06-29 | SRS spec | FR-070 through FR-073, NFR-003, E-010, E-012 |
| srs/states.md | 2026-06-29 | State diagram | lp_closing, closed, close_operations states |
| srs/flows.md | 2026-06-29 | Flow diagram | F-04 user_redeem, F-05 bot_safe_close |
| srs/erd.md | 2026-06-29 | ERD | close_operations table schema |
| 02_backbone/common-rules.md | 2026-06-26 | Common rule | BR-EXBOT-006 verbatim |
| 02_backbone/message-list.md | 2026-06-26 | Message list | E-EXBOT-010, E-EXBOT-012 verbatim |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này tồn tại để đảm bảo nhà đầu tư có thể thoát ExBot bất kỳ lúc nào bằng một thao tác on-chain duy nhất (`redeem(tokenId)`), và nhận lại toàn bộ vốn (LP-portion ngay lập tức, HL-portion sau khi hedge đóng). Mục tiêu nghiệp vụ cốt lõi: bảo vệ vốn nhà đầu tư bất kể trạng thái của hệ thống hedge — LP-portion không bao giờ bị giữ lại hoặc rollback do lỗi hedge.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| On-chain redeem | Nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` → LP thanh lý, LP-portion USDC về ví nhà đầu tư ngay trong cùng tx | uc-user-redeem.md §3 step 1-2, FR-EXBOT-070(A) |
| Event detection & enqueue | Event watcher phát hiện `RedemptionEvent`, enqueue vào `user_redeem` queue (priority cao nhất) | uc-user-redeem.md §3 step 3-4, flows.md F-04 |
| close_operations record creation | Worker tạo bản ghi `close_operations` với `kind='user_redeem'`, trạng thái ban đầu `lp_closed→funds_returned` | uc-user-redeem.md §3 step 7, erd.md |
| HL hedge close | Worker đóng vị thế short HL bằng `closeShortReduceOnlyIoc` (full close, cloid), sau đó cancel stop qua `replaceStopProtected(size=0)` | uc-user-redeem.md §3 step 8-10, flows.md F-04 |
| Reconcile | Verify vị thế HL = 0 sau khi đóng | uc-user-redeem.md §3 step 11, flows.md F-04 |
| HL-portion USDC transfer | Sau khi hedge close xác nhận, gửi HL-portion USDC về nhà đầu tư qua RedemptionQueue ledger | uc-user-redeem.md §3 step 12-14 |
| SLA monitoring | SLA 5 phút từ lúc phát hiện event. Nếu quá → admin alert E-EXBOT-010 (alternate flow A1) | uc-user-redeem.md §4 A1, NFR-EXBOT-003 |
| Hedge close failure | Nếu đóng hedge thất bại sau khi LP đã thanh lý → `residual_hl_liability`, thông báo admin. LP-portion KHÔNG bị rollback | uc-user-redeem.md §4 A2, BR-EXBOT-006 |
| Duplicate message handling | Nếu Worker nhận message đã xử lý → detect qua `close_operations.idempotency_key UNIQUE` hoặc `queue_idempotency` → skip | uc-user-redeem.md §4 A3 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| bot_safe_close flow | FR-EXBOT-070(B), US-EXBOT riêng, không thuộc UC này | Không ảnh hưởng UC này |
| LP liquidation logic (Solidity) | zen-proprietary, SOTATEK chỉ tích hợp qua ABI | Tester không verify nội bộ contract |
| HL-portion USDC amount calculation | UC không mô tả công thức tính HL-portion (chỉ nói "HL-portion USDC") | Ảnh hưởng expected result khi test bước 12-14 — xem Issue Register |
| `residual_hl_liability` recovery flow | UC mention nhưng không mô tả luồng xử lý tiếp theo | Tester không biết bot chuyển sang trạng thái nào sau `residual_hl_liability` |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ACT-I — Investor (End User) | Primary | Gọi `BnzaExVault.redeem(tokenId)` on-chain để khởi tạo luồng. Không tương tác trực tiếp với Worker. | Chỉ có thể redeem tokenId thuộc sở hữu của mình. | uc-user-redeem.md §2, us-004.md, frd.md §2 ACT-I |
| ACT-O — OPERATOR (System / Worker) | System | Redeem event watcher phát hiện sự kiện; Redeem Worker thực hiện đóng hedge, ghi `close_operations`, gửi HL-portion | Worker hành động thay nhà đầu tư; không cần xác nhận thêm từ nhà đầu tư | uc-user-redeem.md §3, flows.md F-04 |
| ACT-A — Admin (zen) | Secondary | Nhận alert khi SLA bị vi phạm (E-EXBOT-010) hoặc khi hedge close thất bại (`residual_hl_liability`) | Không có action tự động trong UC này; chỉ nhận notification | uc-user-redeem.md §4 A1, A2, message-list.md |
| BnzaExVault (on-chain contract) | External | Thực hiện LP liquidation, phát `RedemptionEvent`, trả LP-portion USDC trong cùng tx | Contract do zen phát triển; SOTATEK tích hợp qua ABI | uc-user-redeem.md §3 step 1-2, frd.md §3 |
| Hyperliquid API | External | Đóng vị thế short, hủy stop order | HL rate limit budget: ≤800 weight/min (NFR-EXBOT-004) | flows.md F-04, frd.md §4.10 FR-EXBOT-090 |

**Nhận xét readiness:** Actor đủ rõ cho thiết kế test theo role. Tuy nhiên UC không mô tả ai là người nhận notification khi `residual_hl_liability` — chỉ nói "enqueue admin notification". Chi tiết này cần xác nhận cho test case kiểm tra A2.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot tồn tại và đang ở trạng thái `active` (lifecycle_state) | Yes | uc-user-redeem.md §2, states.md |
| 2 | `bots.status` không phải `closing` hoặc `closed` | Yes | states.md, E-EXBOT-012 |
| 3 | Nhà đầu tư sở hữu `tokenId` hợp lệ trên BnzaExVault | Yes | uc-user-redeem.md §2 |
| 4 | Event watcher đang hoạt động và có thể nhận `RedemptionEvent` từ on-chain | Yes | flows.md F-04, uc-user-redeem.md §3 step 3 |
| 5 | HL agent key có `key_status='active'` (cần thiết để Worker ký lệnh đóng hedge) | Yes (implicit) | frd.md FR-EXBOT-081, FR-EXBOT-001 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Happy path hoàn tất | `close_operations.state='done'`, `bots.lifecycle_state='closed'`, `bots.status='closed'`, LP-portion USDC đã trả on-chain, HL-portion USDC đã gửi qua RedemptionQueue | uc-user-redeem.md §5, flows.md F-04 |
| Hedge close thất bại (A2) | `close_operations.state='residual_hl_liability'`, LP-portion đã trả, admin notification đã enqueue, `lifecycle_state` chưa rõ (xem Issue I-06) | uc-user-redeem.md §4 A2, BR-EXBOT-006 |
| SLA breach (A1) | Admin alert E-EXBOT-010 đã gửi. Hedge close vẫn tiếp tục (SLA breach chỉ trigger alert, không abort) | uc-user-redeem.md §4 A1, message-list.md |
| Duplicate message (A3) | Không có hành động nào được thực hiện thêm; Worker trả về sớm | uc-user-redeem.md §4 A3 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng chính: User-Initiated LP-First Redemption

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ACT-I (Investor) | Gọi `BnzaExVault.redeem(tokenId)` on-chain | LP position được thanh lý ngay trong cùng tx; LP-portion USDC trả về ví nhà đầu tư on-chain | — | Tx bị reverted (ví dụ: tokenId không tồn tại hoặc không thuộc sở hữu) — ngoài phạm vi SOTATEK | uc-user-redeem.md §3 step 1-2 |
| 2 | BnzaExVault | Phát `RedemptionEvent(botId, redeemTxHash, userAddress)` | Event watcher nhận được event | — | Event watcher bỏ lỡ event — không có retry mô tả trong UC | uc-user-redeem.md §3 step 3, flows.md F-04 |
| 3 | Event watcher | Enqueue `{botId, redeemTxHash, userAddress}` vào `user_redeem` queue | Message được enqueue với priority cao nhất | — | — | uc-user-redeem.md §3 step 4, flows.md F-04 |
| 4 | Worker | Nhận message từ queue | SLA timer bắt đầu (5 phút từ lúc phát hiện) | A1: nếu SLA bị vi phạm → admin alert | A3: nếu duplicate message → detect qua idempotency → exit | uc-user-redeem.md §3 step 5-6, NFR-EXBOT-003 |
| 5 | Worker | Acquire `UserLockDO` lease (ttl=90s) để ngăn concurrent HL mutations | Lock acquired | — | Lock contention — không mô tả trong UC (xem Issue I-07) | uc-user-redeem.md §3 step 6 (inferred), FR-EXBOT-091 |
| 6 | Worker | Kiểm tra trạng thái bot — đảm bảo không phải `closing`/`closed` | Bot ở trạng thái hợp lệ | — | Bot đã `closed` → E-EXBOT-012 "Bot is already closed. No action needed." (409) | uc-user-redeem.md §3, E-EXBOT-012 |
| 7 | Worker | Tạo bản ghi `close_operations` với `kind='user_redeem'`, `state='lp_closed'→'funds_returned'`, `idempotency_key` UNIQUE | Bản ghi được tạo | — | `idempotency_key` đã tồn tại (duplicate) → skip | uc-user-redeem.md §3 step 7, erd.md |
| 8 | Worker | Gọi `closeShortReduceOnlyIoc` (full close, cloid) trên HL để đóng vị thế short | HL short position đóng thành công | — | A2: HL close thất bại → `residual_hl_liability` | uc-user-redeem.md §3 step 8, flows.md F-04 |
| 9 | Worker | Gọi `replaceStopProtected(size=0)` để hủy stop order hiện có (§19.5 INV-STOP protocol) | Stop order đã hủy | — | Stop cancel thất bại — không mô tả separate trong UC | uc-user-redeem.md §3 step 10, UC §3 step 10 |
| 10 | Worker | Reconcile — fetch `clearinghouseState` để verify vị thế HL = 0 | Vị thế xác nhận = 0 | — | Reconcile mismatch (vị thế ≠ 0) — không mô tả trong UC (xem Issue I-08) | uc-user-redeem.md §3 step 11, flows.md F-04 |
| 11 | Worker | Cập nhật `close_operations.state = 'hedge_closed'` | State updated | — | — | uc-user-redeem.md §3 step 11 (inferred from flows.md F-04) |
| 12 | Worker | Gửi HL-portion USDC về nhà đầu tư qua RedemptionQueue ledger | USDC transferred | — | Transfer thất bại — không mô tả trong UC | uc-user-redeem.md §3 step 12-13 |
| 13 | Worker | Cập nhật `close_operations.state = 'done'`, `bots.lifecycle_state = 'closed'` | Bot hoàn toàn đóng | — | — | uc-user-redeem.md §3 step 14-15, flows.md F-04 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| BR-EXBOT-006 — LP-portion repayment bất điều kiện | Hedge close failure không được block hoặc rollback LP-portion đã trả | Yes (P0) | LP-portion được giữ nguyên | Vi phạm nghiêm trọng: đây là business rule P0 | common-rules.md BR-EXBOT-006: "`user_redeem` LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user." |
| close_operations idempotency | `idempotency_key UNIQUE` trên bảng `close_operations` | Yes | Insert thành công → tiếp tục xử lý | UNIQUE constraint violation → duplicate delivery → skip | erd.md, FR-EXBOT-070 |
| SLA 5 phút | Hedge close phải hoàn tất ≤ 5 phút từ lúc phát hiện event | Yes (NFR) | Hoàn tất đúng hạn | SLA breach → E-EXBOT-010 admin alert (không abort hedge close) | NFR-EXBOT-003, message-list.md E-EXBOT-010 |
| INV-STOP protocol | Stop cancel phải qua `replaceStopProtected(size=0)` — direct cancel-then-place không được phép | Yes | Stop order hủy an toàn | Vi phạm INV-STOP invariant | uc-user-redeem.md §3 step 10, FR-EXBOT-032 |
| Full close (not delta-only) | user_redeem dùng `closeShortReduceOnlyIoc` (full close) — đây là ngoại lệ hợp lệ theo FR-EXBOT-020 | Yes | Toàn bộ vị thế short đóng | — | FR-EXBOT-020: "Full close/open is ONLY allowed for: 1. target size = 0 (bot close path)" |
| queue_idempotency | Consumer insert `message_id` vào `queue_idempotency` với `state='started'` tại đầu xử lý | Yes | Processing tiếp tục | UNIQUE conflict → duplicate delivery → return immediately | FR-EXBOT-010, erd.md |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| SLA 5 phút bị vi phạm | Admin notification (internal alert) | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | E-EXBOT-010 | message-list.md E-EXBOT-010 |
| Close attempted on already-closed bot | API error response | "Bot is already closed. No action needed." | E-EXBOT-012, HTTP 409 | message-list.md E-EXBOT-012 |
| Hedge close thất bại sau khi LP đã thanh lý | State transition + admin notification | `close_operations.state = 'residual_hl_liability'`; admin notification enqueue với outstanding liability amount | A2 flow, uc-user-redeem.md §4 A2 | uc-user-redeem.md §4 A2 — nội dung message cho admin chưa được định nghĩa (xem Issue I-05) |
| Bot lifecycle hoàn tất đóng | State transition | `bots.lifecycle_state = 'closed'`, `bots.status = 'closed'`, `close_operations.state = 'done'` | Happy path postcondition | uc-user-redeem.md §5, flows.md F-04 |


---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` on-chain | Event watcher (Fargate/chain indexer) → `user_redeem` queue | Sự kiện on-chain trigger toàn bộ luồng off-chain; nếu event watcher bỏ lỡ event, luồng không bắt đầu | On-chain: LP thanh lý, LP-portion USDC về ví. Off-chain: bản ghi `close_operations` được tạo sau khi Worker xử lý | uc-user-redeem.md §3, flows.md F-04 |
| `close_operations` record creation (`kind='user_redeem'`) | hedge-sync, light-check workers | Khi `lifecycle_state='lp_closing'`, light-check và hedge-sync bị skip (states.md). Ngăn hedge mutation đồng thời với close | `close_operations.idempotency_key UNIQUE` ngăn double settlement. Cần verify `bots.lifecycle_state` chuyển sang `lp_closing` khi tạo `close_operations` | states.md, erd.md |
| HL hedge close (`closeShortReduceOnlyIoc`) | `hedge_legs` table, `close_operations` | Vị thế short trên HL = 0; `close_operations.state` tiến tới `hedge_closed` | Cần reconcile confirm HL position = 0 trước khi cập nhật state | flows.md F-04, FR-EXBOT-023 |
| Stop cancel (`replaceStopProtected(size=0)`) | `hedge_legs.stop_order_id`, `stop_cloid` | Stop order trên HL bị hủy; INV-STOP invariant bảo vệ window 0-stop | Sau cancel, `hedge_legs.stop_cloid` và `stop_order_id` cần được clear hoặc marked as cancelled | FR-EXBOT-032, uc-user-redeem.md §3 step 10 |
| HL-portion USDC transfer qua RedemptionQueue | `close_operations.state` → `done`, `bots.lifecycle_state` → `closed` | Sau khi nhà đầu tư nhận HL-portion, bot hoàn toàn đóng. `bots.status='closed'` | Tổng USDC nhà đầu tư nhận = LP-portion (on-chain, ngay) + HL-portion (sau hedge close). Cần verify không có double payment | uc-user-redeem.md §3 step 12-15, erd.md close_operations.usdc_amount |
| `residual_hl_liability` state (A2) | Admin dashboard, future reconciliation | Bot bị kẹt với HL liability; trạng thái `bots.lifecycle_state` sau A2 chưa được mô tả rõ trong UC | `close_operations.residual_amount` ghi lại số tiền còn nợ; cần verify field này được populate đúng | uc-user-redeem.md §4 A2, erd.md |
| SLA breach alert (A1) | Admin notification system | Admin nhận thông báo nhưng hedge close vẫn tiếp tục; không có interrupt hay abort | UC không mô tả liệu SLA breach alert có được gửi một lần duy nhất hay có thể gửi lặp | uc-user-redeem.md §4 A1, E-EXBOT-010 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — hedge close thành công trong SLA | Bot đang `active`; nhà đầu tư sở hữu `tokenId` hợp lệ | Nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` on-chain | LP-portion USDC được trả trong cùng tx on-chain; Worker đóng hedge HL trong ≤5 phút; `close_operations.state='done'`; `bots.lifecycle_state='closed'`; HL-portion USDC được gửi qua RedemptionQueue | us-004.md AC-004-1, NFR-EXBOT-003 |
| AC-02 | SLA breach — hedge close quá 5 phút | Bot đang `active`; hedge close Worker bị chậm hoặc HL có sự cố | Nhà đầu tư redeem; hedge close kéo dài >5 phút | Admin nhận E-EXBOT-010 alert: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned."; hedge close vẫn tiếp tục (không abort) | us-004.md AC-004-2, message-list.md E-EXBOT-010 |
| AC-03 | Hedge close thất bại sau LP đã thanh lý | Bot đang `active`; LP-portion đã trả on-chain | Hedge close Worker gặp lỗi không khắc phục được từ HL | `close_operations.state='residual_hl_liability'`; LP-portion đã trả KHÔNG bị rollback hoặc block; admin nhận notification về outstanding liability | us-004.md AC-004-3, BR-EXBOT-006 |
| AC-04 | Duplicate message delivery | `close_operations` đã tồn tại với `idempotency_key` cho lần redeem này | Worker nhận lại cùng message từ queue | Worker phát hiện duplicate qua `idempotency_key UNIQUE` hoặc `queue_idempotency`; không thực hiện bất kỳ HL mutation nào; exit gracefully | uc-user-redeem.md §4 A3 |
| AC-05 | Redeem trên bot đã đóng | Bot đã có `bots.lifecycle_state='closed'` | Worker nhận message user_redeem | Worker trả E-EXBOT-012 (409): "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |
| AC-06 (Suy luận cần xác nhận) | LP-portion bất điều kiện khi HL API unavailable | HL API không phản hồi; LP-portion đã trả on-chain | Worker cố đóng hedge HL nhưng HL unreachable | LP-portion không bị block. Hedge close fail → `residual_hl_liability`. BR-EXBOT-006 được bảo đảm. | BR-EXBOT-006, suy luận từ AC-03 |
| AC-07 (Suy luận cần xác nhận) | Bot ở `lp_closing` state thì light-check bị skip | close_operations được tạo, `lifecycle_state` chuyển sang `lp_closing` | Light-check worker chạy cho bot này | Light-check worker bỏ qua bot vì `lifecycle_state='lp_closing'` — không enqueue hedge-sync | states.md: "light-check/hedge-sync skipped; activated by close request" |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance / SLA | Hedge close ≤ 5 phút từ lúc phát hiện event (NFR-EXBOT-003) | Test case cần có timer verification; cần môi trường simulate event detection timestamp | NFR-EXBOT-003, frd.md §5 |
| Reliability / Resilience | LP-portion repayment unconditional (BR-EXBOT-006) — hedge failure không block return | Test case cần verify LP-portion không bị rollback khi inject hedge failure sau on-chain redeem | BR-EXBOT-006 |
| Idempotency | `close_operations.idempotency_key UNIQUE`; `queue_idempotency` message dedup | Test case cần verify redelivery không tạo duplicate settlement | FR-EXBOT-010, erd.md |
| Security | HL agent key signing qua AWS KMS Signing Lambda; private key không lộ ra memory hay log | Tester verify không có key material trong log/response | NFR-EXBOT-006, IC-EXBOT-005 |
| Audit / Logging | `close_operations` ledger ghi lại toàn bộ trạng thái. `rebalance_attempts` không áp dụng cho user_redeem (không có hedge-sync attempt) | Test verify `close_operations` state transitions đầy đủ | erd.md, flows.md F-04 |
| Precision | HL-portion USDC amount tính bằng BigDecimal (no float) — không document rõ trong UC | Test verify amount không bị floating-point error | NFR-EXBOT-008 (inferred) |


---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận (Issue Register)

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 | High | MISSING_INFO | UC §7 FR Trace vs frd.md | UC §7 FR Trace liệt kê "FR-EXBOT-070, FR-EXBOT-071". FR-EXBOT-070 tồn tại trong frd.md (§4.8) và spec.md. FR-EXBOT-071 **không tồn tại** trong frd.md hay spec.md — không có bất kỳ định nghĩa nào cho mã này trong toàn bộ tài liệu đã đọc. BA vui lòng xác nhận: FR-EXBOT-071 là mã lỗi trong FR Trace (cần tạo FR mới), hay đây là lỗi đánh máy (cần sửa thành FR-EXBOT-072 hoặc mã khác)? | FR-EXBOT-071 được cite trong UC như một yêu cầu quan trọng của user_redeem. Nếu FR này không tồn tại, coverage của UC bị thiếu hoặc FR Trace sai — tester không thể trace test case về đúng FR. | BA | Open |
| I-02 | High | MISSING_INFO | uc-user-redeem.md §3 step 12-14; flows.md F-04 | UC mô tả Worker "gửi HL-portion USDC về nhà đầu tư qua RedemptionQueue ledger" nhưng không định nghĩa: (a) HL-portion được tính như thế nào (tổng số tiền từ HL closing position minus fees? minus funding?); (b) ai thực sự là người thực hiện on-chain transfer USDC (Worker gọi trực tiếp hay qua Operator Facade?); (c) transaction hash của HL-portion transfer có được lưu vào `close_operations.hedge_close_tx` không? | Không có công thức hoặc mô tả source of truth cho HL-portion amount → tester không thể verify số tiền nhà đầu tư nhận đúng không. | BA | Open |
| I-03 | High | MISSING_INFO | uc-user-redeem.md §3 step 5-6; UC §2 Preconditions | UC không mô tả liệu Worker có acquire `UserLockDO` lease trước khi thực hiện HL mutations hay không. flows.md F-04 cũng không hiện UserLockDO trong sequence diagram của user_redeem (khác với F-02 hedge-sync có UserLockDO rõ ràng). Nếu không có lock, concurrent hedge-sync và user_redeem có thể conflict. | Nếu không có UserLockDO trong user_redeem flow, race condition có thể xảy ra khi một hedge-sync đang chạy đồng thời với redeem. Tester không biết expected behavior khi hai luồng cạnh tranh HL mutations. | BA / Tech Lead | Open |
| I-04 | High | CROSS_SOURCE_CONFLICT | uc-user-redeem.md §3 step 7 vs states.md vs erd.md | UC step 7 mô tả tạo `close_operations` với state ban đầu là "lp_closed→funds_returned" (một notation kỳ lạ, dùng mũi tên trong một field state). states.md liệt kê state machine cho `close_operations` là: `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → ...`. erd.md định nghĩa `close_operations.state` là `TEXT` (một giá trị). Câu hỏi: (a) state ban đầu khi Worker tạo bản ghi là `'lp_closed'` hay `'funds_returned'` hay `'requested'`? (b) UC skip state `'requested'` và `'hedge_close_pending'` trong mô tả — có phải các state này không được sử dụng trong user_redeem path không? | State ban đầu xác định expected result của test case verify `close_operations` record được tạo đúng. Nếu initial state sai, test sẽ fail mà không phải do lỗi thực. | BA | Open |
| I-05 | Medium | MISSING_INFO | uc-user-redeem.md §4 A2 | Khi hedge close thất bại (A2), UC nói "enqueue admin notification (outstanding liability amount)" nhưng không chỉ định: (a) nội dung cụ thể của notification (message code là gì?); (b) outstanding liability amount được tính và lưu ở đâu (field `close_operations.residual_amount` trong ERD?). | Tester không thể verify expected result của admin notification trong test case cho A2. | BA | Open |
| I-06 | Medium | MISSING_INFO | uc-user-redeem.md §4 A2; states.md | Khi `close_operations.state = 'residual_hl_liability'` (A2 flow), `bots.lifecycle_state` và `bots.status` chuyển sang giá trị gì? UC §5 Postconditions (phần đầu) mô tả happy path. §5 không mô tả postconditions cho A2. states.md không có state `residual_hl_liability` trong `bots.lifecycle_state` enum. | Tester không biết bot ở trạng thái nào sau A2 — không thể verify state transition của `bots` table, chỉ verify được `close_operations`. | BA | Open |
| I-07 | Medium | MISSING_INFO | uc-user-redeem.md §3; flows.md F-04 | UC và flows.md F-04 không mô tả behavior khi `user_redeem` Worker không thể acquire `UserLockDO` (nếu lock được dùng). Trong hedge-sync flow (F-02), nếu lock không acquired được → re-queue with delay. Behavior tương tự cho user_redeem không được document. | Nếu user_redeem cần lock, hành vi khi lock bị tranh giành phải được test. | BA / Tech Lead | Open |
| I-08 | Medium | MISSING_INFO | uc-user-redeem.md §3 step 11; flows.md F-04 | Sau bước reconcile (verify HL position = 0), nếu reconcile thất bại (HL position ≠ 0 sau closeShortReduceOnlyIoc), UC không mô tả behavior. Trong hedge-sync, reconcile mismatch → SAFE_MODE. Trong user_redeem context (LP đã thanh lý), SAFE_MODE có được áp dụng không? | Không có expected behavior cho reconcile failure trong user_redeem → tester không thiết kế được test case cho trường hợp này. | BA | Open |
| I-09 | Medium | INTERNAL_INCONSISTENCY | uc-user-redeem.md §5 (Postconditions) | UC có hai phần Postconditions: phần đầu (§5 chính thức) và một phần không có header §5 lặp lại ở phía dưới. Hai phần này có nội dung khác nhau về `lifecycle_state` sau khi hoàn tất. Đây là lỗi cấu trúc tài liệu. | Gây nhầm lẫn cho tester về expected postcondition. BA cần merge hoặc xóa một phần. | BA | Open |
| I-10 | Medium | MISSING_INFO | flows.md F-05 vs uc-user-redeem.md | flows.md F-05 (bot_safe_close) vẫn hiển thị luồng cũ với `OperatorFacade → ExBotWorker → RedemptionQueue → Operator fulfillRequest` (hedge-first qua API, không phải qua on-chain event watcher). Tuy nhiên HLD 2026-06-18 ghi nhận "drop park/re-entry" và frd.md FR-EXBOT-070(B) mô tả bot_safe_close khác. F-05 có thể đã outdated sau HLD decision. Điều này không trực tiếp ảnh hưởng user_redeem nhưng gây nhầm lẫn về sự khác biệt giữa hai luồng. | Nếu tester đọc F-05 để so sánh hai close systems, họ sẽ hiểu sai bot_safe_close. | BA | Open |
| I-11 | Low | MISSING_INFO | uc-user-redeem.md §3 step 8 | UC nói Worker gọi `closeShortReduceOnlyIoc` nhưng không mô tả: cloid được tạo theo công thức nào (FR-EXBOT-022 áp dụng không?), và nếu HL từ chối lệnh (ví dụ: insufficient margin để close), behavior là gì. | Ảnh hưởng test case idempotency cho hedge close command và error handling. | BA | Open |
| I-12 | Low | AMBIGUOUS_WORDING | uc-user-redeem.md §3 step 3 "enqueue ... [highest priority queue]" | UC dùng notation "[highest priority queue]" (trong ngoặc vuông) — không rõ đây là tên queue hay chú thích độ ưu tiên. frd.md FR-EXBOT-010 và flows.md F-04 xác nhận đây là `user_redeem` queue. Tuy nhiên UC không viết tên queue rõ ràng. | Minor: tester có thể confused nhưng có thể resolve qua frd.md. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| FR-EXBOT-071 — không tìm thấy trong frd.md | FR | Nếu FR-071 thực sự cần được tạo, spec.md và frd.md cần được cập nhật trước khi test design tiếp tục | BA | Open |
| BnzaExVault ABI + `RedemptionEvent` schema | Integration | Tester cần ABI để verify on-chain event params (`botId`, `redeemTxHash`, `userAddress`) | zen / BA | Open |
| HL-portion USDC amount formula | Calculation | Cần có công thức hoặc spec để verify số tiền nhà đầu tư nhận | BA / zen | Open |
| `residual_hl_liability` recovery flow | UC dependency | Nếu bot rơi vào `residual_hl_liability`, luồng admin xử lý tiếp theo chưa được document | BA | Open |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-07-01 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu — SRS-first cross-check |


---

## §F.1 — Inventory

| # | Function / Operation | Trigger | Input | Output | Data Object / Field | Type | Enum / Valid Values | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | On-chain LP liquidation | `BnzaExVault.redeem(tokenId)` called by Investor | `tokenId` (uint256) | LP position liquidated, LP-portion USDC returned to investor in same tx, `RedemptionEvent` emitted | BnzaExVault (on-chain), LP NFT | on-chain | — | uc-user-redeem.md §3.1-2, FR-EXBOT-070(A) |
| 2 | Event detection & enqueue | `RedemptionEvent(botId, redeemTxHash, userAddress)` emitted on-chain | botId, redeemTxHash, userAddress | Message enqueued in `user_redeem` queue (highest priority) | queue message | queue | — | flows.md F-04, uc-user-redeem.md §3.3-4 |
| 3 | close_operations record creation | Worker dequeues message | botId, redeemTxHash, userAddress | `close_operations` row inserted | `close_operations.id`, `kind`, `state`, `idempotency_key`, `bot_id`, `created_at` | TEXT | `kind`: `user_redeem` \| `bot_safe_close`; initial `state`: see I-04 | uc-user-redeem.md §3.7, erd.md |
| 4 | HL short position full close | Worker executes after record creation | botId, cloid (deterministic) | HL short position closed; `close_operations.state` → `hedge_closed` | HL position (external), `close_operations.state`, `close_operations.hedge_close_tx` | external + TEXT | — | uc-user-redeem.md §3.8, flows.md F-04 |
| 5 | Stop order cancel | Worker after hedge close (or concurrently per UC step 10) | cloid, size=0 | Existing stop order cancelled via `replaceStopProtected(size=0)` INV-STOP protocol | `hedge_legs.stop_order_id`, `stop_cloid`, `stop_price`, `stop_size` | TEXT | — | uc-user-redeem.md §3.10, FR-EXBOT-032 |
| 6 | Post-close reconcile | After HL close order | botId | HL position verified = 0 | HL `clearinghouseState` (external) | external | actualSize = 0 expected | flows.md F-04, FR-EXBOT-023 |
| 7 | HL-portion USDC transfer | After reconcile confirms close | botId, userAddress, amount (unspecified — I-02) | HL-portion USDC sent to investor via RedemptionQueue ledger | `close_operations.usdc_amount` | TEXT (BigDecimal string) | — | uc-user-redeem.md §3.12-13, erd.md |
| 8 | Bot close finalization | After HL-portion transfer | botId | `close_operations.state='done'`; `bots.lifecycle_state='closed'`; `bots.status='closed'` | `close_operations.state`, `bots.lifecycle_state`, `bots.status`, `close_operations.updated_at` | TEXT | `state`: `done`; `lifecycle_state`: `closed` | uc-user-redeem.md §3.14-15, states.md |
| 9 | SLA monitoring | Continuous from event detection | SLA timer (5 min) | Admin alert E-EXBOT-010 if ≥5 min elapsed | — (admin notification queue) | — | threshold: 300s | NFR-EXBOT-003, message-list.md E-EXBOT-010 |
| 10 | Hedge close failure handling (A2) | HL close attempt fails | botId, failure reason | `close_operations.state='residual_hl_liability'`; admin notification enqueued | `close_operations.state`, `close_operations.residual_amount` | TEXT | `state`: `residual_hl_liability` | uc-user-redeem.md §4 A2, BR-EXBOT-006 |
| 11 | Duplicate message detection (A3) | Worker receives already-processed message | message_id | Skip processing; return early | `queue_idempotency.message_id` (UNIQUE), `close_operations.idempotency_key` (UNIQUE) | TEXT | — | uc-user-redeem.md §4 A3, erd.md |
| 12 | Already-closed bot check | Worker processes redeem for closed bot | bots.lifecycle_state | E-EXBOT-012 (409) | bots.lifecycle_state | TEXT | `closed` | message-list.md E-EXBOT-012 |
| 13 | close_operations state machine | close_operations lifecycle | Current state | Next state per transition | `close_operations.state` | TEXT | `requested` \| `lp_closed` \| `funds_returned` \| `hedge_close_pending` \| `hedge_closed` \| `residual_hl_liability` \| `done` | states.md |
| 14 | bots lifecycle transition during close | Close operation initiated | bots.lifecycle_state | `active` → `lp_closing` → `closed` | `bots.lifecycle_state`, `bots.status` | TEXT | `lp_closing`: light-check/hedge-sync skipped | states.md |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations

| # | Item | States / Lifecycle | Preconditions | Validation / Business Rule | Dependencies | Resolved Messages | Source |
|---|---|---|---|---|---|---|---|
| 1 | `close_operations` | `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done` (happy); `hedge_close_pending → residual_hl_liability` (A2) | Bot must be `active`; `idempotency_key` must be unique | `idempotency_key UNIQUE` — duplicate insert → skip. `kind` ∈ {`user_redeem`, `bot_safe_close`} | `bots.bot_id` FK | — | erd.md, states.md |
| 2 | `bots.lifecycle_state` during close | `active → lp_closing` (on close request); `lp_closing → closed` (on completion) | — | While `lp_closing`: light-check skipped; hedge-sync skipped | `bots.status` coarse field | — | states.md |
| 3 | BR-EXBOT-006 — unconditional LP-portion | Applies at all times during user_redeem | LP-portion already returned on-chain (in same tx as redeem) | Hedge close failure MUST NOT block or reverse LP-portion | BnzaExVault (on-chain tx is irreversible) | — | common-rules.md BR-EXBOT-006 |
| 4 | SLA 5 min (NFR-EXBOT-003) | From event detection to hedge close completion | Event detection timestamp must be captured | ≤ 5 minutes; breach → E-EXBOT-010 admin alert only (no abort) | E-EXBOT-010 | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | NFR-EXBOT-003, message-list.md E-EXBOT-010 |
| 5 | INV-STOP protocol (stop cancel) | During close operation | Existing stop order must exist on HL | `replaceStopProtected(size=0)` is the ONLY allowed stop cancel method | `hedge_legs.stop_cloid`, `stop_order_id` | — | FR-EXBOT-032, uc-user-redeem.md §3.10 |
| 6 | Full close exception | During user_redeem | Bot has active HL short position | `closeShortReduceOnlyIoc` full close is explicitly allowed for bot close path (FR-EXBOT-020 exception #1) | — | — | FR-EXBOT-020 |
| 7 | queue_idempotency | Message processing start | message_id available | Insert `message_id` at start; UNIQUE conflict → return immediately | `queue_idempotency.message_id` UNIQUE INDEX | — | FR-EXBOT-010, erd.md |
| 8 | `close_operations.residual_amount` (A2) | Set on hedge close failure | A2 path triggered | Outstanding HL liability amount stored | `close_operations.residual_amount` TEXT (BigDecimal) | Admin notification (content undefined — I-05) | erd.md, uc-user-redeem.md §4 A2 |

---

## §F.3 — Functional Logic & Workflow Decomposition

| Function | Path | Trigger | Input | Output | Actor/Permission | System Response | Source |
|---|---|---|---|---|---|---|---|
| User-initiated redeem | Happy path | `BnzaExVault.redeem(tokenId)` on-chain | tokenId (investor-owned) | LP-portion USDC returned on-chain immediately; close_operations created; hedge closed ≤5 min; HL-portion sent; bot closed | ACT-I initiates on-chain; ACT-O Worker executes off-chain | `close_operations.state='done'`; `bots.lifecycle_state='closed'` | uc-user-redeem.md §3, flows.md F-04 |
| User-initiated redeem | SLA breach (A1) | Hedge close not completed within 5 min | SLA timer expiry | Admin alert E-EXBOT-010 sent; hedge close continues | ACT-O (system), ACT-A (receives alert) | E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | uc-user-redeem.md §4 A1, NFR-EXBOT-003 |
| User-initiated redeem | Hedge close failure (A2) | HL close fails after LP already liquidated | Hedge close error | `residual_hl_liability` state; admin notified; LP-portion NOT reversed | ACT-O (system), ACT-A (notified) | `close_operations.state='residual_hl_liability'`; `close_operations.residual_amount` set | uc-user-redeem.md §4 A2, BR-EXBOT-006 |
| User-initiated redeem | Duplicate message (A3) | Queue redelivers already-processed message | Same message_id or idempotency_key | No action; Worker exits early | ACT-O (system) | Return early; no HL mutation; no state change | uc-user-redeem.md §4 A3 |
| Already-closed bot detection | Exception | Worker receives redeem for closed bot | bots.lifecycle_state = 'closed' | E-EXBOT-012 (409) | ACT-O (system) | "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |

---

## §F.4 — Functional Integration & Data Consistency

| Trigger | Cross-function Effect | On-chain / Off-chain Consistency | Data Verification | Source |
|---|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` on-chain | LP liquidated on-chain; LP-portion USDC at investor address; `RedemptionEvent` emitted → event watcher → queue | On-chain is source of truth for LP liquidation. Off-chain `close_operations` created AFTER event detection. Gap: if event watcher misses the event, off-chain never catches up. | Verify: `close_operations` created matches `redeemTxHash`; LP-portion amount matches on-chain tx | uc-user-redeem.md §3, flows.md F-04 |
| `close_operations` created with `kind='user_redeem'` | `bots.lifecycle_state` transitions to `lp_closing` → light-check worker skips bot → hedge-sync suppressed | Both `close_operations` and `bots.lifecycle_state` must be consistent. If `lifecycle_state` is not updated atomically with `close_operations` creation, race condition possible. | Verify: after `close_operations` insert, `bots.lifecycle_state='lp_closing'` within same transaction | states.md, erd.md |
| HL short `closeShortReduceOnlyIoc` | `close_operations.state` → `hedge_closed`; stop order cancelled; HL position = 0 | HL is source of truth for position. Off-chain `close_operations.hedge_close_tx` records the tx. | Verify: after reconcile, HL `clearinghouseState.size = 0`; `hedge_legs.stop_order_id` cleared | flows.md F-04, FR-EXBOT-023 |
| HL-portion USDC transfer via RedemptionQueue | `close_operations.state` → `done`; `bots.lifecycle_state` → `closed`; `bots.status` → `closed` | USDC transfer is the final off-chain event. Must not be processed twice. | Verify: `close_operations.usdc_amount` populated; `close_operations.state = 'done'`; no duplicate transfer on redelivery | uc-user-redeem.md §3.12-15, erd.md |
| `residual_hl_liability` (A2) | LP-portion already sent; HL-portion NOT sent; admin notified; `close_operations.residual_amount` set | On-chain: LP-portion irreversible. Off-chain: `close_operations.state='residual_hl_liability'` signals pending manual resolution. | Verify: `close_operations.residual_amount` = expected outstanding HL liability; admin notification enqueued | uc-user-redeem.md §4 A2, erd.md |


---

## §F.5 — AC Candidates

| AC # | Scenario | Given | When | Then | Source / Note |
|---|---|---|---|---|---|
| AC-F5-01 | Happy path hedge close | Bot active; investor owns tokenId; HL short open; stop order placed | Investor calls `redeem(tokenId)` | LP-portion USDC in investor wallet (same tx); `close_operations.state='done'` within ≤5 min; `bots.lifecycle_state='closed'`; HL position=0; stop cancelled | us-004.md AC-004-1 |
| AC-F5-02 | SLA breach alert | Bot active; HL close takes >5 min | Hedge close delayed beyond 5 min threshold | E-EXBOT-010 admin alert sent; hedge close continues after alert; LP-portion NOT reversed | us-004.md AC-004-2 |
| AC-F5-03 | Hedge close fails, LP already returned | Bot active; LP-portion returned on-chain | HL close worker encounters unrecoverable HL error | `close_operations.state='residual_hl_liability'`; `residual_amount` set; LP-portion NOT reverted; admin notified | us-004.md AC-004-3, BR-EXBOT-006 |
| AC-F5-04 | Duplicate queue delivery | close_operations with same idempotency_key already exists | Worker receives same user_redeem message again | No additional HL mutation; no duplicate `close_operations` row; Worker exits gracefully | uc-user-redeem.md §4 A3 |
| AC-F5-05 | Redeem on already-closed bot | bots.lifecycle_state='closed' | Worker processes user_redeem message | E-EXBOT-012 (409): "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |
| AC-F5-06 (Suy luận cần xác nhận) | light-check suppressed during lp_closing | close_operations created; bots.lifecycle_state='lp_closing' | Light-check worker evaluates this bot | Worker skips bot entirely; no hedge-sync enqueued | states.md |
| AC-F5-07 (Suy luận cần xác nhận) | INV-STOP: stop cancelled via replaceStopProtected | Active stop order exists on HL | Worker calls cancel as part of close flow | Stop cancelled via size=0 replace; `hedge_legs.stop_order_id` cleared; no naked stop removal | FR-EXBOT-032, UC §3 step 10 |

---

## Tổng quan đánh giá và điểm

### Bảng tham chiếu mã

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng của module ExBot. Mỗi FR mô tả một capability hoặc behavior cụ thể của Worker/Queue/DO. | frd.md |
| BR-EXBOT-* | Business Rule — ràng buộc kinh doanh không thay đổi, áp dụng toàn module. BR-EXBOT-006 là rule quan trọng nhất cho UC này. | 02_backbone/common-rules.md |
| E-EXBOT-* | Error / System Message — mã thông báo lỗi hoặc notification của ExBot Worker, canonical source là message-list.md. | 02_backbone/message-list.md |
| NFR-EXBOT-* | Non-Functional Requirement — yêu cầu phi chức năng (SLA, throughput, security, idempotency). | frd.md §5 |
| INV-STOP | Invariant Stop — giao thức protected stop replacement (cancel→place được bảo vệ). | frd.md FR-EXBOT-032, spec.md §19.5 |
| LP-portion | Phần USDC thu được từ thanh lý LP position. Được trả on-chain ngay trong cùng tx với `redeem()`. | uc-user-redeem.md, FR-EXBOT-070(A) |
| HL-portion | Phần USDC thu được từ đóng vị thế hedge trên Hyperliquid. Được gửi sau khi hedge close confirmed. | uc-user-redeem.md, FR-EXBOT-070(A) |
| RedemptionQueue | Sổ cái on-chain FIFO để thanh toán USDC cho nhà đầu tư sau khi hedge đóng (dùng cho cả user_redeem và bot_safe_close). | frd.md FR-EXBOT-070 |
| UserLockDO | Durable Object lease-based mutex ngăn concurrent HL mutations cho cùng một user. | frd.md FR-EXBOT-091 |
| SIWE | Sign-In With Ethereum — giao thức xác thực on-chain. Không áp dụng trực tiếp cho UC này nhưng là context auth chung. | (industry term) |

### Scoring Summary

| Scoring Area | Max | Score | Status | Key Issues |
|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 15 | ⚠️ Partial | I-02 (HL-portion amount formula missing), I-04 (initial close_operations state ambiguous), I-11 (cloid formula not stated) |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 17 | ⚠️ Partial | I-05 (residual_hl_liability admin notification message undefined), I-06 (bots.lifecycle_state after A2 undefined), I-08 (reconcile failure behavior undefined) |
| 3. Functional Logic & Workflow Decomposition | 25 | 16 | ⚠️ Partial | I-03 (UserLockDO not documented in user_redeem), I-07 (lock contention behavior), I-08 (reconcile mismatch path) |
| 4. Functional Integration & Data Consistency | 15 | 11 | ⚠️ Partial | I-03 (concurrent hedge-sync race condition not addressed), I-10 (F-05 outdated in flows.md) |
| 5. UC / Spec Documentation Quality Issues | 15 | 8 | ⚠️ Partial | I-01 (FR-EXBOT-071 missing — Blocker), I-09 (duplicate Postconditions section), I-12 (queue name ambiguous) |
| **Tổng điểm** | **100** | **67/100** | **Not Ready** | Auto-fail: Blocker I-01 (FR-EXBOT-071 not found) + multiple High issues unresolved |

> **Áp dụng auto-cap:** I-01 (FR-EXBOT-071 không tồn tại) là Blocker — FR Trace của UC bị sai hoặc thiếu FR definition. Theo rubric: "A blocker prevents understanding of a critical function → affected area max 40% of its max score. Final verdict = Not Ready."

### §10.3 Audit Summary

**Verdict: Not Ready (Score: 67/100)**

UC-EXBOT-user-redeem mô tả đúng luồng tổng thể LP-first redemption và tuân thủ BR-EXBOT-006 (LP-portion unconditional). SRS baseline (flows.md F-04, states.md, erd.md, frd.md FR-EXBOT-070) nhất quán với UC về flow chính. Tuy nhiên UC có một Blocker quan trọng: **FR-EXBOT-071 được cite trong FR Trace nhưng hoàn toàn không tồn tại trong frd.md hay spec.md** — BA cần xác nhận đây là lỗi đánh máy hay FR bị thiếu. Ngoài ra, 3 vấn đề High khác chặn thiết kế test case: (1) HL-portion USDC amount không có công thức, (2) initial state của `close_operations` khi tạo bất nhất giữa UC và states.md, (3) UserLockDO không được document trong user_redeem flow dẫn đến không rõ race condition behavior. Tester có thể thiết kế test case cho happy path và SLA breach, nhưng không thể viết expected result đầy đủ cho các alternate flows (A2 hedge failure, A3 duplicate) cho đến khi các câu hỏi Open được BA trả lời.

**Khuyến nghị:** BA giải quyết I-01 (FR-EXBOT-071) và I-02 (HL-portion formula) trước — đây là hai vấn đề có tác động nhất đến coverage và correctness của test design. Sau khi 4 câu hỏi High (I-01, I-02, I-03, I-04) được trả lời, UC có thể được re-audit và expected verdict là Conditionally Ready.

