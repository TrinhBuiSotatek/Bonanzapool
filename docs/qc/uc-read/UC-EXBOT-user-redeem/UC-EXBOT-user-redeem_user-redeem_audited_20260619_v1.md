# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tiêu đề tài liệu:** UC-EXBOT-user-redeem — Báo cáo rà soát độ sẵn sàng test  
**Ngày tạo:** 2026-06-19  
**Tác giả / Agent:** qc-uc-read-exbot (Trinh.Bui / MTS-978)  
**Phiên bản:** v1

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-user-redeem mô tả luồng nhà đầu tư tự đóng vị thế ExBot và rút USDC về ví. Đây là cơ chế **LP-first close**: nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` trực tiếp trên blockchain; hợp đồng thông minh thanh lý toàn bộ vị thế LP, hoán đổi sang USDC và chuyển **phần LP-USDC về ví nhà đầu tư ngay trong cùng một giao dịch on-chain** — đây là bảo đảm on-chain, không thể bị hoàn lại. Sau khi sự kiện `RedemptionEvent` được phát hiện, worker `user_redeem` (hàng đợi ưu tiên cao nhất, SLA 5 phút) tiến hành đóng vị thế short trên Hyperliquid (HL), thu hồi phần USDC của HL, và cập nhật trạng thái bot về `closed`.

Hai hệ thống đóng bot tồn tại song song trong ExBot: `user_redeem` (luồng này, nhà đầu tư chủ động khởi tạo, LP đóng trước) và `bot_safe_close` (hệ thống khởi tạo, hedge đóng trước). UC này chỉ bao gồm `user_redeem`. Rule nền tảng quan trọng nhất là **BR-EXBOT-006**: việc hoàn trả LP-portion USDC là vô điều kiện — lỗi đóng hedge trên HL không được chặn hoặc hoàn lại khoản tiền đã trả. Khi hedge đóng thất bại, hệ thống ghi nhận `residual_hl_liability` và thông báo admin để xử lý thủ công.

Phạm vi test: không có UI. Toàn bộ luồng được kiểm thử qua Back-End (Cloudflare Worker, D1, on-chain event, Hyperliquid API) và quan sát qua Admin site. Ba điểm tích hợp quan trọng cần bao phủ khi thiết kế test: (1) on-chain `BnzaExVault.redeem()` và sự kiện `RedemptionEvent`, (2) queue `user_redeem` và idempotency, (3) Hyperliquid full close + `UserLockDO` lease + `INV-STOP` §19.5 protocol.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-user-redeem | User-Initiated Redemption (LP-First) | Draft 2026-06-12 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-12 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-user-redeem.md` | Draft 2026-06-12 | UC chính | Nguồn input chính |
| `userstories/us-004.md` | Draft 2026-06-12 | User Story liên kết | US-EXBOT-004 |
| `srs/spec.md` | SPEC v5.2.6, changelog 2026-06-18 | SRS — source of truth | FR-EXBOT-001…FR-EXBOT-093 |
| `srs/states.md` | Updated 2026-06-18 | State diagram | Đã xóa cooldown/parked |
| `srs/flows.md` | Updated 2026-06-18 | Flow diagram | F-05 có thể stale (xem I-08) |
| `srs/erd.md` | Draft | ERD (D1 schema) | close_operations, bots, queue_idempotency |
| `frd.md` | Updated 2026-06-18 | FRD | FR-EXBOT-070, 071, 072, 073 |
| `common-rules.md` | Draft | BR-EXBOT-001…BR-EXBOT-010 | BR-EXBOT-006 áp dụng |
| `message-list.md` | Updated 2026-06-09 | Error/Info messages | E-EXBOT-010 áp dụng |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-user-redeem tồn tại để cho phép nhà đầu tư USDC tự chủ thoát khỏi vị thế ExBot và nhận lại USDC mà không cần thực hiện thủ công các bước on-chain phức tạp. Đây là con đường thoát vị thế chủ động của người dùng — đối lập với `bot_safe_close` là luồng hệ thống tự khởi tạo. Kết quả nghiệp vụ mong đợi: toàn bộ vốn (phần LP + phần HL) được hoàn trả, bot chuyển về trạng thái `closed`, mọi ngoại lệ (SLA vi phạm, hedge đóng thất bại) được ghi nhận và leo thang đến admin.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Trigger on-chain | Nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` | UC §3 bước 1; SRS FR-EXBOT-070 |
| LP liquidation (on-chain) | `decreaseLiquidity` 100% + `collect` + swap sang USDC; LP-portion về ví trong cùng tx | UC §3 bước 2-3; SRS FR-EXBOT-070 |
| RedemptionEvent detection | Redeem Event Watcher phát hiện sự kiện, enqueue vào `user_redeem` | UC §3 bước 4-5 |
| Queue idempotency | UNIQUE constraint trên `queue_idempotency.message_id` ngăn xử lý trùng | UC §3 bước 6; SRS FR-EXBOT-070 |
| close_operations record | Tạo row với `kind='user_redeem'`, trạng thái tuần tự | UC §3 bước 7; states.md |
| UserLockDO lease | Lấy lease cho user trước khi thao tác HL | UC §3 bước 8 |
| HL hedge full close | `closeShortReduceOnlyIoc` với deterministic cloid | UC §3 bước 9 |
| INV-STOP cancel | §19.5 `replaceStopProtected` với size=0 | UC §3 bước 10; SRS §19.5 |
| Reconcile | Xác nhận HL position size = 0 sau close | UC §3 bước 11 |
| HL-portion USDC transfer | Gửi HL-portion USDC về ví nhà đầu tư qua RedemptionQueue | UC §3 bước 13 |
| Lifecycle close | `bots.lifecycle_state='closed'` | UC §3 bước 14; states.md |
| SLA monitoring (A1) | 5 phút không đóng được hedge → admin alert E-EXBOT-010 | UC §A1; SRS NFR-EXBOT-003 |
| Hedge close failure (A2) | Hedge đóng thất bại → `residual_hl_liability` + admin alert | UC §A2; SRS FR-EXBOT-070 |
| Duplicate message (A3) | `queue_idempotency` UNIQUE conflict → skip | UC §A3 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| `bot_safe_close` | Luồng riêng biệt, UC riêng (`uc-bot-safe-close`) | Không ảnh hưởng — chỉ cần biết hai hệ thống tồn tại song song |
| RedemptionQueue.fulfillRequest | Bot_safe_close đặc trưng; user_redeem gửi HL-portion trực tiếp | Tester không cần test fulfillRequest cho luồng này |
| UI / màn hình | ExBot là backend-only; không có UI screen | Không áp dụng |
| Smart contract internals | Ngoài phạm vi SOTATEK (zen cung cấp ABI — IC-EXBOT-002) | Không penalize UC |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Gọi `BnzaExVault.redeem(tokenId)` on-chain; nắm LP NFT redemption rights | Chỉ owner của tokenId mới có thể redeem; `bot.status` phải không phải `closed` | UC §1, §2 |
| BnzaExVault (Solidity) | System | Thanh lý LP, swap USDC, chuyển LP-portion trong cùng giao dịch | Bảo đảm on-chain — không thể hoàn lại; ABI do zen cung cấp (IC-EXBOT-002) | SRS FR-EXBOT-070; IC-EXBOT-002 |
| Redeem Event Watcher | System | Lắng nghe `RedemptionEvent`; enqueue vào `user_redeem` queue | Phụ thuộc on-chain event finality | UC §3 bước 4-5 |
| user_redeem Worker | System | Thực thi toàn bộ hedge-close flow; quản lý `close_operations` | Phải acquire `UserLockDO` trước khi thao tác HL; SLA 5 phút | UC §3; SRS NFR-EXBOT-003 |
| Hyperliquid (HL) | External | Sàn giao dịch hedge — nhận lệnh đóng short | Rate-limited (HLRateLimitDO); API có thể unreachable | SRS FR-EXBOT-091 |
| Admin (hệ thống) | Secondary | Nhận alert khi SLA vi phạm hoặc hedge đóng thất bại; xử lý `residual_hl_liability` | Read-only trong UC này; xử lý thủ công là ngoài phạm vi | UC §A1, §A2 |

**Nhận xét readiness:** Actor đủ rõ để thiết kế test theo role. Tuy nhiên UC không mô tả quyền xác thực của Redeem Event Watcher (làm sao Watcher biết event là authentic, không phải replay). Đây là điểm cần xác nhận cho test bảo mật.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | `bots.status = 'active'` (hoặc `paused` / `safe_mode`) — bot phải chưa ở trạng thái `closed` | Yes | UC §2 |
| 2 | Nhà đầu tư nắm LP NFT redemption rights thông qua `BnzaExVault` | Yes | UC §2 |
| 3 | `bots.lifecycle_state` ∈ `{active, lp_rebalancing, hedge_stopped_cooldown, safe_mode}` — không phải `lp_closing` hoặc `closed` | Yes (suy luận từ states.md) | states.md §lifecycle |
| 4 | `circuit_breakers.state` có thể ở bất kỳ giá trị nào — user_redeem không bị circuit breaker chặn (khác hedge-sync) | Note | SRS FR-EXBOT-070 (suy luận) |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Happy path hoàn chỉnh | `bots.lifecycle_state='closed'`; `close_operations.state='done'`; LP-portion USDC trong ví nhà đầu tư (on-chain); HL-portion USDC đã gửi | UC §5; states.md |
| Hedge close thất bại | `bots.lifecycle_state='closed'`; `close_operations.state='residual_hl_liability'`; LP-portion USDC vẫn trong ví nhà đầu tư (không bị hoàn lại); admin được thông báo | UC §5; BR-EXBOT-006 |
| SLA vi phạm (hedge vẫn chạy) | LP-portion USDC đã trả; `close_operations.state` còn ở `hedge_close_pending` hoặc `hedge_closed`; admin alert E-EXBOT-010 đã gửi | UC §A1; SRS NFR-EXBOT-003 |
| Duplicate message | `queue_idempotency.state` không đổi; không tạo row `close_operations` thứ hai | UC §A3 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng chính: user_redeem LP-first close

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | USDC Investor | Gọi `BnzaExVault.redeem(tokenId)` on-chain | BnzaExVault thực thi `decreaseLiquidity` 100% + `collect` + swap toàn bộ sang USDC | — | Giao dịch on-chain thất bại → revert, LP không bị thanh lý | UC §3 bước 1-2; SRS FR-EXBOT-070 |
| 2 | BnzaExVault | LP-portion USDC chuyển về ví nhà đầu tư trong cùng giao dịch | Nhà đầu tư nhận USDC; `RedemptionEvent(botId, redeemTxHash, userAddress)` phát | — | On-chain failure → revert | UC §3 bước 3-4; BR-EXBOT-006 |
| 3 | Redeem Event Watcher | Phát hiện `RedemptionEvent` on-chain | Enqueue message vào `user_redeem` queue (highest priority) | — | Watcher lag: event được phát hiện muộn → SLA đồng hồ bắt đầu từ lúc detect | UC §3 bước 5; SRS NFR-EXBOT-003 |
| 4 | user_redeem Worker | Nhận message từ queue; insert `message_id` vào `queue_idempotency` (state='started') | Row tạo thành công → tiếp tục xử lý | — | UNIQUE conflict → message đã xử lý trước đó → return immediately (A3) | UC §3 bước 6; UC §A3 |
| 5 | user_redeem Worker | Tạo row `close_operations (kind='user_redeem', state='lp_closed')` | Row tạo với `idempotency_key UNIQUE` | — | UNIQUE conflict trên `idempotency_key` → duplicate settlement bị chặn | UC §3 bước 7; SRS FR-EXBOT-070; erd.md |
| 6 | user_redeem Worker | Update `close_operations.state='funds_returned'` (LP-portion đã trả on-chain) | Ghi nhận LP-portion đã hoàn trả | — | — | states.md §close_operations; I-01 |
| 7 | user_redeem Worker | Acquire `UserLockDO` lease cho user | Lease được cấp (TTL=90s) | — | Lease đang giữ bởi worker khác → wait hoặc timeout | UC §3 bước 8; SRS (UserLockDO) |
| 8 | user_redeem Worker | Gọi `closeShortReduceOnlyIoc` trên HL với deterministic cloid | HL nhận lệnh đóng short | — | HL API unreachable → retry; sau max retries → A2 | UC §3 bước 9 |
| 9 | user_redeem Worker | `replaceStopProtected` (§19.5 INV-STOP) với size=0 để hủy stop | Stop hủy thành công; `stop_replacing_started_at` cleared in finally | — | INV-STOP fail → stop không bị hủy | UC §3 bước 10; SRS §19.5 |
| 10 | user_redeem Worker | Update `close_operations.state='hedge_close_pending'` | — | — | — | states.md §close_operations |
| 11 | user_redeem Worker | Reconcile: verify HL position size = 0 | Size = 0 confirmed | SLA breach: 5 phút trôi qua → A1 | Reconcile thất bại → retry; max retries → A2 | UC §3 bước 11; SRS NFR-EXBOT-003 |
| 12 | user_redeem Worker | Update `close_operations.state='hedge_closed'` | — | — | — | UC §3 bước 12; states.md |
| 13 | user_redeem Worker | Gửi HL-portion USDC về nhà đầu tư; ghi vào RedemptionQueue ledger | USDC chuyển; ledger cập nhật | — | Transfer thất bại → admin alert | UC §3 bước 13; I-07 |
| 14 | user_redeem Worker | Update `close_operations.state='done'`; `bots.lifecycle_state='closed'` | Bot đã đóng hoàn toàn | — | — | UC §3 bước 14; states.md |
| 15 | user_redeem Worker | Update `queue_idempotency.state='succeeded'` | Message hoàn tất | — | — | UC §3 bước 15 |

#### B. Alternate flows

| ID | Trigger | Hành động hệ thống | Trạng thái cuối | Nguồn |
|---|---|---|---|---|
| A1 | 5 phút trôi qua từ event detect mà hedge chưa đóng | Gửi admin alert E-EXBOT-010; LP-portion KHÔNG bị hoàn lại | close_operations.state giữ nguyên; bot chưa closed | UC §A1; SRS NFR-EXBOT-003; E-EXBOT-010 |
| A2 | HL hedge close thất bại sau max retries | `close_operations.state='residual_hl_liability'`; admin được thông báo với bot_id, hedge size, USD value; LP KHÔNG bị hoàn lại | `close_operations.state='residual_hl_liability'`; lifecycle_state không rõ (I-02) | UC §A2; BR-EXBOT-006; US-004 AC-004-3 |
| A3 | Message trùng lặp | `queue_idempotency` UNIQUE conflict → return immediately | Không thay đổi trạng thái | UC §A3 |

---

## §F.1 — Inventory

| # | Function / Operation | Trigger | Input | Output | Data Object / Field | Kiểu | Source |
|---|---|---|---|---|---|---|---|
| F1.1 | `BnzaExVault.redeem(tokenId)` | Nhà đầu tư gọi on-chain | `tokenId` (LP NFT ID) | LP-portion USDC về ví; `RedemptionEvent` phát | `close_operations.lp_close_tx` | TEXT (tx hash) | SRS FR-EXBOT-070; UC §3 bước 1-3 |
| F1.2 | `RedemptionEvent` detection | On-chain event | `botId`, `redeemTxHash`, `userAddress` | Message vào `user_redeem` queue | — | — | UC §3 bước 4-5 |
| F1.3 | `queue_idempotency` insert | Worker nhận message | `message_id` | UNIQUE conflict → skip; hoặc tiếp tục | `queue_idempotency.message_id` | TEXT UNIQUE | UC §3 bước 6 |
| F1.4 | `close_operations` create | Worker sau idempotency check | `bot_id`, `kind='user_redeem'`, `idempotency_key` | Row created với `state='lp_closed'` | `close_operations`: id PK, bot_id FK, kind, state, idempotency_key UNIQUE, hedge_close_tx, lp_close_tx, usdc_amount, residual_amount | — | erd.md; states.md |
| F1.5 | `UserLockDO` lease acquire | Trước khi thao tác HL | `userId` | Lease (TTL=90s) hoặc block | — | — | UC §3 bước 8; SRS |
| F1.6 | HL full close `closeShortReduceOnlyIoc` | Worker sau acquire lock | `cloid` (deterministic), position size | HL lệnh đóng short | `close_operations.hedge_close_tx` | TEXT | UC §3 bước 9 |
| F1.7 | `INV-STOP replaceStopProtected` (size=0) | Sau lệnh HL close | size=0 | Stop hủy; `stop_replacing_started_at` cleared in finally | `hedge_legs.stop_replacing_started_at` | TIMESTAMP NULL | UC §3 bước 10; SRS §19.5 |
| F1.8 | Reconcile HL position | Sau close attempt | — | position size = 0 confirmed | `positions.size` | DECIMAL | UC §3 bước 11 |
| F1.9 | `close_operations.state` transitions | Worker tại mỗi bước | — | Sequential state changes | `close_operations.state` | ENUM | states.md |
| F1.10 | HL-portion USDC transfer | Sau hedge_closed | `usdc_amount` | USDC gửi về nhà đầu tư | `close_operations.usdc_amount` | DECIMAL | UC §3 bước 13; I-07 |
| F1.11 | `bots.lifecycle_state` → `closed` | Sau done | — | `lifecycle_state='closed'` | `bots.lifecycle_state` | ENUM | UC §3 bước 14; states.md |
| F1.12 | SLA monitoring | Timer từ event detect | elapsed time | Admin alert nếu > 5 phút | — | — | SRS NFR-EXBOT-003; E-EXBOT-010 |
| F1.13 | `residual_hl_liability` ghi nhận | Hedge close fail | bot_id, hedge size, USD value | `close_operations.state='residual_hl_liability'`; admin alert | `close_operations.residual_amount` | DECIMAL | UC §A2; BR-EXBOT-006 |

**Enum sets (user_redeem path):**
- `close_operations.kind`: `'user_redeem'` | `'bot_safe_close'`
- `close_operations.state`: `requested` → `lp_closed` → `funds_returned` → `hedge_close_pending` → `hedge_closed` → `done` | `residual_hl_liability`
- `bots.lifecycle_state`: `active` → `lp_closing` → `closed`
- `bots.status` (precondition): `active` | `paused` | `safe_mode`

**Emitted events / messages:**
- `RedemptionEvent(botId, redeemTxHash, userAddress)` — on-chain
**Emitted events / messages:**
- `RedemptionEvent(botId, redeemTxHash, userAddress)` — on-chain
- `E-EXBOT-010`: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." — internal alert

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Data object / Function | States / Transitions | Preconditions | Validations | Business rules | Dependencies | Error / Success messages | Nguồn |
|---|---|---|---|---|---|---|---|
| `close_operations` (user_redeem) | `requested` → `lp_closed` → `funds_returned` → `hedge_close_pending` → `hedge_closed` → `done` \| `residual_hl_liability` | `bot_id` tồn tại; `idempotency_key UNIQUE` | UNIQUE constraint ngăn double settlement | BR-EXBOT-006: LP-portion unconditional | `bots.bot_id` FK; `queue_idempotency` | — | erd.md; states.md; SRS FR-EXBOT-070 |
| `bots.lifecycle_state` (close path) | `active` → `lp_closing` → `closed` | Bot không phải `closed` | — | — | `close_operations.state` | — | states.md |
| `queue_idempotency` | `started` → `succeeded` | `message_id` mới hoặc đã có → skip | UNIQUE trên `message_id` | — | Worker message | — | UC §3 bước 6, 15 |
| `UserLockDO` lease | Không giữ → giữ (TTL=90s) → release | — | TTL=90s; một lease per user | Bắt buộc trước HL ops | User identity | — | SRS (UserLockDO) |
| HL hedge close | pending → closed \| failed | `UserLockDO` đang giữ | `closeShortReduceOnlyIoc` deterministic cloid | — | `HLRateLimitDO`; HL API | — | UC §3 bước 9 |
| INV-STOP §19.5 | `stop_replacing_started_at` set → cleared (finally) | Hedge close đã gọi | size=0 | Phải clear trong `finally` block | `hedge_legs.stop_id` | — | SRS §19.5 |
| SLA 5 phút | Timer từ event detect → hedge closed hoặc timeout | — | NFR-EXBOT-003 | Overrun → admin escalation; LP không bị đảo ngược | SLA timer | `E-EXBOT-010` | SRS NFR-EXBOT-003; E-EXBOT-010 |
| LP-portion repayment | On-chain, unconditional | — | On-chain guarantee | BR-EXBOT-006: không bao giờ bị block hoặc hoàn lại | `BnzaExVault.redeem()` | — | BR-EXBOT-006 |
| `residual_hl_liability` | — | Hedge close fail sau max retries | — | Admin phải được thông báo với bot_id, hedge size, USD value | `close_operations.residual_amount` | Admin alert | UC §A2; US-004 AC-004-3 |
| BigDecimal arithmetic | — | — | Bắt buộc cho tất cả phép tính tài chính | Float/Number arithmetic bị cấm | `usdc_amount`, `residual_amount` | — | SRS BigDecimal mandate |
| `HLRateLimitDO` | — | Trước mỗi HL API call | `{allowed: boolean, retryAfterMs}` | Nếu `allowed=false` → không gửi lệnh; re-queue với delay | HL API calls | — | SRS FR-EXBOT-091 |

---

## §F.3 — Functional Logic & Workflow Decomposition

| Function | Happy path | Alternate path | Exception path | Trigger | Input | Output | Actor | System response | Nguồn |
|---|---|---|---|---|---|---|---|---|---|
| LP liquidation (on-chain) | `BnzaExVault.redeem()` → LP 100% thanh lý → USDC về ví trong cùng tx | — | On-chain revert → LP không bị ảnh hưởng | Investor gọi contract | tokenId | LP-portion USDC; RedemptionEvent | USDC Investor | Bảo đảm on-chain | SRS FR-EXBOT-070 |
| Queue enqueue + idempotency | Watcher detect → enqueue; Worker insert message_id → continue | — | UNIQUE conflict → return immediately | RedemptionEvent | message_id | Processing hoặc skip | user_redeem Worker | Duplicate prevention | UC §3 bước 5-6; §A3 |
| close_operations create | Row với state='lp_closed' + 'funds_returned' | — | UNIQUE idempotency_key → reject duplicate | Worker sau idempotency check | bot_id, kind, idempotency_key | Row created | user_redeem Worker | D1 insert | SRS FR-EXBOT-070; erd.md |
| UserLockDO acquire | Lease cấp (TTL=90s) | Lease bận → wait/timeout | Timeout → worker không thể tiếp tục | Worker trước HL ops | userId | Lease | user_redeem Worker | DO lock | SRS (UserLockDO) |
| HL hedge full close | `closeShortReduceOnlyIoc` → confirmed close → size=0 | SLA 5 phút → A1 alert | HL fail sau max retries → A2 residual_hl_liability | Worker sau lock | cloid, position | hedge_closed state | user_redeem Worker | HL API response | UC §3 bước 9, 11; §A1, §A2 |
| INV-STOP cancel | `replaceStopProtected` size=0 → stop hủy; `stop_replacing_started_at` cleared finally | — | INV-STOP fail → stop tồn tại; xử lý thủ công | Sau lệnh HL close | size=0 | Stop cancelled | user_redeem Worker | D1 + HL | SRS §19.5 |
| Reconcile | HL position size = 0 confirmed | — | Mismatch → retry | Sau close attempt | — | Xác nhận size=0 | user_redeem Worker | HL query | UC §3 bước 11 |
| HL-portion USDC transfer | Gửi HL-portion về nhà đầu tư; ghi RedemptionQueue ledger | — | Transfer fail → admin alert | Sau hedge_closed | usdc_amount | USDC transferred | user_redeem Worker | On-chain + D1 | UC §3 bước 13; I-07 |
| SLA monitoring | Hedge close trong 5 phút → no alert | — | > 5 phút → E-EXBOT-010 admin alert | Timer từ event detect | elapsed time | Alert hoặc không | Hệ thống | Admin notification | SRS NFR-EXBOT-003; E-EXBOT-010 |

---

## §F.4 — Functional Integration & Data Consistency

| Integration point | Effect | Data consistency concern | Nguồn |
|---|---|---|---|
| On-chain `BnzaExVault.redeem()` ↔ off-chain Worker | On-chain: LP-portion USDC trả ngay; off-chain: hedge close async | Source of truth cho LP-portion là on-chain | SRS FR-EXBOT-070; IC-EXBOT-002 |
| `RedemptionEvent` Watcher lag | SLA đồng hồ từ lúc detect, không phải lúc tx confirmed | Watcher lag lớn → SLA tính sai | SRS NFR-EXBOT-003 |
| `queue_idempotency` ↔ `close_operations` UNIQUE | Hai lớp bảo vệ double-settlement | Cả hai phải được kiểm tra | SRS FR-EXBOT-070; erd.md |
| `UserLockDO` lease (TTL=90s) ↔ HL API calls | Lease ngăn concurrent HL mutations | TTL hết giữa flow → potential race condition | SRS (UserLockDO) |
| `close_operations.state` sequential transitions | State không được bỏ bước | Worker crash → resume đúng bước không restart | states.md; SRS FR-EXBOT-073 AC |
| HL hedge close ↔ INV-STOP §19.5 | INV-STOP phải complete trước release lock | Stop tồn tại sau hedge đóng | SRS §19.5 |
| `residual_hl_liability` ↔ `bots.lifecycle_state` | Khi state='residual_hl_liability', lifecycle_state không được định nghĩa | Xem I-02 | UC §A2; states.md |
| `HLRateLimitDO` ↔ `UserLockDO` | Rate limit deny trong khi giữ lock | Release lock trước re-queue không rõ (I-05) | SRS FR-EXBOT-091 |
| HL-portion USDC transfer ↔ RedemptionQueue ledger | user_redeem gửi trực tiếp, không qua Operator fulfillRequest | Cơ chế gửi không rõ (I-07) | UC §3 bước 13; SRS FR-EXBOT-070 |

---

## §F.5 — Acceptance Criteria Candidates

| # | AC Candidate | Trace | Cần xác nhận? |
|---|---|---|---|
| AC-C1 | LP-portion USDC về ví nhà đầu tư trong cùng giao dịch `BnzaExVault.redeem()` | UC §3 bước 3; BR-EXBOT-006; SRS FR-EXBOT-070 | Không |
| AC-C2 | Duplicate `message_id` → worker return immediately, không tạo row thứ hai | UC §A3 | Không |
| AC-C3 | `close_operations.state` tiến tuần tự, không bỏ bước | states.md; SRS FR-EXBOT-073 AC pattern | Cần xác nhận atomicity (I-01) |
| AC-C4 | Hedge close fail → `residual_hl_liability`, LP không bị hoàn lại | UC §A2; BR-EXBOT-006; US-004 AC-004-3 | Không |
| AC-C5 | SLA 5 phút vi phạm → admin alert E-EXBOT-010, LP không bị hoàn lại | UC §A1; SRS NFR-EXBOT-003; E-EXBOT-010 | Không |
| AC-C6 | `stop_replacing_started_at` cleared trong `finally` block | SRS §19.5 | Suy luận cần xác nhận |
| AC-C7 | BigDecimal cho `usdc_amount` và `residual_amount` | SRS BigDecimal mandate | Cần xác nhận |

---

## 10. Kết quả đánh giá

### 10.1 Issue Register — Unified Gap & Question Report

| Issue ID | Type | Severity | Affected area | Source trace | Finding | Impact on tester understanding | Suggested question or fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-01 | `MISSING_INFO` | Blocker | Area 3, Area 2 | UC §3 bước 7; states.md §close_operations | UC §3 bước 7 ghi `state='lp_closed→funds_returned'` như hai trạng thái xảy ra đồng thời. States.md định nghĩa `lp_closed` và `funds_returned` là hai state riêng biệt trong user_redeem path. Không rõ: (a) hai update riêng biệt hay một D1 transaction? (b) khi worker crash giữa `lp_closed` và `funds_returned`, resume strategy là gì? | Tester không thể viết test crash recovery cho close_operations state machine | BA/Tech Lead làm rõ: `lp_closed` và `funds_returned` là hai update riêng biệt hay một transaction? Resume strategy khi crash tại `lp_closed` là gì? | Open |
| I-02 | `MISSING_INFO` | Major | Area 2, Area 3 | UC §A2; states.md §lifecycle; SRS FR-EXBOT-070 | Khi hedge close thất bại và ghi `residual_hl_liability`, `bots.lifecycle_state` không được định nghĩa trong UC hoặc states.md. UC §5 Postconditions không mô tả lifecycle_state khi `residual_hl_liability`. | Tester không biết expected result cho lifecycle_state trong AC của A2; nếu bot không ở `closed` các worker khác có thể tiếp tục xử lý | BA/Tech Lead xác nhận: khi `close_operations.state='residual_hl_liability'`, `bots.lifecycle_state` là gì? `closed` hay `lp_closing`? | Open |
| I-03 | `MISSING_INFO` | Major | Area 3, Area 1 | UC §3 bước 5; states.md §lifecycle | UC không mô tả bước chuyển `bots.lifecycle_state` từ `active`/`paused`/`safe_mode` sang `lp_closing`. States.md §lifecycle chỉ rõ transition `active → lp_closing` xảy ra khi "close request". Không rõ bước nào trong worker set `lifecycle_state='lp_closing'`. | Tester không thể test xem `lp_closing` được set đúng thời điểm; light-check skip bots trong `lp_closing` (SRS) | BA/Tech Lead xác nhận: `bots.lifecycle_state='lp_closing'` được set ở bước nào trong user_redeem worker? | Open |
| I-04 | `CROSS_SOURCE_CONFLICT` | Blocker | Area 5, Area 1 | UC §7 FR Trace; SRS spec.md | UC §7 FR Trace liệt kê `FR-EXBOT-071` nhưng FR này không tồn tại như một section riêng trong spec.md (spec nhảy từ FR-EXBOT-070 sang FR-EXBOT-072). FRD cũng không có entry FR-EXBOT-071. | Tester không thể verify compliance với FR-EXBOT-071; traceability bị gián đoạn | BA xác nhận: FR-EXBOT-071 có phải typo? Nếu không, nó được định nghĩa ở đâu? Cập nhật FR Trace. | Open |
| I-05 | `MISSING_INFO` | Major | Area 4, Area 3 | UC §3; SRS FR-EXBOT-091 | UC không đề cập `HLRateLimitDO` trước khi gọi HL full close. Khi `HLRateLimitDO` trả `allowed=false` và worker đang giữ `UserLockDO` lease, không rõ worker có release lock trước re-queue không. | Thiếu test case rate limit behavior trong user_redeem; lock không release có thể block concurrent operations | BA/Tech Lead xác nhận: khi `HLRateLimitDO` từ chối, worker release `UserLockDO` trước re-queue không? Re-queue delay strategy là gì? | Open |
| I-06 | `MISSING_INFO` | Major | Area 3, Area 5 | UC §3; SRS FR-EXBOT-080, FR-EXBOT-082 | UC không mô tả bước giải mã HL agent key (AES-GCM decrypt) trước khi ký lệnh HL. Không rõ trong user_redeem: nếu agent key revoked hoặc expired khi worker cần ký, hành vi là gì — SAFE_MODE hay `residual_hl_liability`? | Tester cần failure path của key decryption để test bảo mật; user_redeem là P0 flow | BA/Tech Lead xác nhận: trong user_redeem, nếu agent key bị revoke/expired, hành vi là gì? | Open |
| I-07 | `MISSING_INFO` | Major | Area 3 | UC §3 bước 13; SRS FR-EXBOT-070; erd.md | UC §3 bước 13 ghi "tracked in RedemptionQueue ledger" nhưng không định nghĩa rõ cơ chế: worker gọi contract function nào để gửi HL-portion USDC? SRS FR-EXBOT-070 mô tả user_redeem không dùng `RedemptionQueue.createRequest/fulfillRequest` (đó là bot_safe_close), nhưng UC vẫn nói "RedemptionQueue ledger" — có thể mâu thuẫn. | Tester không thể test bước transfer HL-portion mà không biết cơ chế; nếu dùng fulfillRequest phải include Operator action | BA/Tech Lead làm rõ: user_redeem gửi HL-portion bằng cơ chế nào? Có dùng `RedemptionQueue.createRequest` không? | Open |
| I-08 | `INTERNAL_INCONSISTENCY` | Minor | Area 5 | UC §5 Postconditions; UC §3 | UC có hai mục `## Postconditions` — §5 có nội dung đúng; mục thứ hai là placeholder template chưa xóa ("System state reflects the completed operation", "NFR-ADM-005"). NFR-ADM-005 là NFR của module Admin, không phải ExBot. Cùng issue với uc-hedge-sync. | Gây nhầm lẫn; Tester có thể hiểu nhầm NFR-ADM-005 áp dụng cho ExBot | BA xóa phần placeholder Postconditions thứ hai. | Open |
| I-09 | `AMBIGUOUS_WORDING` | Minor | Area 5 | UC §Trigger | UC §Trigger ghi placeholder: "User navigates to the relevant screen or initiates the described action." Trigger thực tế là on-chain event `RedemptionEvent` → Watcher enqueue → user_redeem queue. Cùng issue với uc-hedge-sync. | Tester có thể nhầm đây là UC có UI trigger thay vì on-chain event trigger | BA cập nhật §Trigger mô tả đúng trigger on-chain. | Open |
| I-10 | `MISSING_INFO` | Major | Area 3 | UC §3 bước 9; SRS FR-EXBOT-070 | UC không định nghĩa behavior khi `closeShortReduceOnlyIoc` chỉ partial fill — worker có re-submit với size còn lại không? Giới hạn retry là gì? Partial fill có thể khiến reconcile (bước 11) fail và trigger A2 sai cách. | Tester cần partial fill behavior để test hedge close không hoàn chỉnh | BA/Tech Lead xác nhận: khi closeShortReduceOnlyIoc partial fill, worker xử lý thế nào? Re-submit hay count as failure? | Open |

### 10.2 Dependencies

| # | Dependency | Loại | Ảnh hưởng đến test | Trạng thái |
|---|---|---|---|---|
| D1 | `BnzaExVault` ABI (IC-EXBOT-002) | External — zen cung cấp | ABI xác nhận khi zen deploy Phase 0 (OQ-EXBOT-08); vault calls là stubbed đến lúc đó | Pending (chờ zen) |
| D2 | Contract address (Base + Optimism) | External | Inject qua Cloudflare Secrets Store; ảnh hưởng test environment setup | Pending |
| D3 | `HLRateLimitDO` behavior trong user_redeem context | Internal | Chưa được UC mô tả (I-05) | Open question |
| D4 | FR-EXBOT-071 — không tồn tại trong spec/FRD | Internal | Traceability gap (I-04) | Open question |
| D5 | HL-portion USDC transfer mechanism | Internal | Cơ chế gửi không rõ (I-07) | Open question |

### 10.3 Audit Summary

#### Bảng điểm

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 16 | ⚠️ Partial | Inventory đầy đủ cho function chính; `lp_closing` lifecycle transition thiếu (I-03), FR-EXBOT-071 không tồn tại (I-04) ảnh hưởng traceability |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 17 | ⚠️ Partial | BR-EXBOT-006 rõ; states.md cho close_operations đầy đủ. Tuy nhiên `lifecycle_state` khi `residual_hl_liability` không rõ (I-02), agent key failure path thiếu (I-06) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 10 | ⚠️ Partial — Blocker cap | Blocker I-01 áp dụng auto-cap (Area 3 max 40% = 10/25). HLRateLimitDO thiếu (I-05), partial fill thiếu (I-10), HL-portion transfer không rõ (I-07) |
| 4 | Functional Integration & Data Consistency | 15 | 10 | ⚠️ Partial | On-chain ↔ off-chain integration nhận biết tốt; UserLockDO ↔ HLRateLimitDO gap (I-05); lifecycle_state consistency gap (I-02, I-03) |
| 5 | UC / Spec Documentation Quality Issues | 15 | 8 | ⚠️ Partial — capped | I-04 CROSS_SOURCE_CONFLICT unresolved → Area 5 max 8/15 per auto-cap |
| **Tổng** | | **100** | **61** | | |

**Auto-cap áp dụng:**
- I-01 (Blocker — Area 3): Area 3 max 40% = 10/25.
- I-04 (CROSS_SOURCE_CONFLICT unresolved): Area 5 max 8/15.

#### Verdict: **Not Ready (61/100)**

Điểm 61 dưới ngưỡng Conditionally Ready (70). Thêm vào đó, hai Blocker chưa được giải quyết (I-01: atomicity của close_operations state transitions; I-04: FR-EXBOT-071 không tồn tại trong spec/FRD) — per scoring rubric, verdict = Not Ready khi có Blocker chưa giải quyết.

#### Blockers

| Issue | Lý do là Blocker |
|---|---|
| I-01 — Atomicity `lp_closed` → `funds_returned` | Tester không thể thiết kế test crash-recovery cho close_operations state machine P0 mà không biết atomicity và thứ tự hai state transitions. |
| I-04 — FR-EXBOT-071 không tồn tại | UC trích dẫn FR-EXBOT-071 trong FR Trace nhưng FR không tồn tại trong spec.md hoặc FRD. Traceability bị gián đoạn. |

#### Major issues cần giải quyết trước khi thiết kế test

I-02 (`lifecycle_state` khi `residual_hl_liability`), I-03 (`lp_closing` transition không được mô tả), I-05 (`HLRateLimitDO` behavior không rõ), I-06 (agent key failure path), I-07 (HL-portion transfer mechanism), I-10 (partial fill behavior).

#### Khuyến nghị

UC-EXBOT-user-redeem có nền tảng tốt: BR-EXBOT-006 được áp dụng nhất quán, alternate flows A1/A2/A3 được định nghĩa, và hai lớp idempotency protection được mô tả. UC cần được bổ sung trước khi QC có thể thiết kế test case đầy đủ. Ưu tiên: (1) I-04 — làm rõ hoặc xóa FR-EXBOT-071 khỏi FR Trace; (2) I-01 — định nghĩa atomicity của `lp_closed`/`funds_returned`; (3) I-07 — làm rõ cơ chế gửi HL-portion USDC; (4) I-02+I-03 — định nghĩa `lifecycle_state` consistency cho toàn bộ close flow. Sau khi các Blocker và Major issues được giải quyết, UC có thể đạt Conditionally Ready.
