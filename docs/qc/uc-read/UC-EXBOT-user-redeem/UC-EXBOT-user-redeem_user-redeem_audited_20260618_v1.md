# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tiêu đề:** UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)  
**Ngày tạo:** 2026-06-18  
**Tác giả:** QC UC Read ExBot Agent  
**Phiên bản:** v1

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-user-redeem mô tả luồng nhà đầu tư (USDC Investor) chủ động đóng ExBot và lấy lại vốn USDC. Đây là luồng "LP-first": nhà đầu tư gọi hàm `BnzaExVault.redeem(tokenId)` trực tiếp trên blockchain — BnzaExVault lập tức thanh lý toàn bộ LP NFT (giảm 100% liquidity, collect fees, swap sang USDC) và chuyển phần USDC tương ứng với LP về ví nhà đầu tư **ngay trong cùng giao dịch on-chain**. Đây là bảo đảm tuyệt đối (on-chain guarantee) — không phụ thuộc vào bất kỳ backend nào.

Song song với đó, hệ thống backend (Redeem Event Watcher) phát hiện sự kiện `RedemptionEvent` và đưa vào `user_redeem` queue (ưu tiên cao nhất, SLA 5 phút) để đóng vị thế short ETH-USD trên Hyperliquid. Phần USDC tương ứng với vị thế hedge (HL-portion) được gửi cho nhà đầu tư sau khi đóng hedge thành công. Nếu đóng hedge thất bại, hệ thống chuyển sang trạng thái `residual_hl_liability` và thông báo admin — **không bao giờ được đảo ngược việc trả LP-portion đã thực hiện on-chain**.

UC này quan trọng vì kết hợp hành động on-chain (không thể đảo ngược) với hành động backend (có thể thất bại) và có ràng buộc SLA nghiêm ngặt 5 phút. Nó liên quan trực tiếp đến `close_operations` ledger, `UserLockDO`, circuit breaker, và luồng `user_redeem` queue.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-user-redeem | User-Initiated Redemption (LP-First) | — | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-12 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-user-redeem.md` | 2026-06-12 | UC | Tài liệu chính được review |
| `userstories/us-004.md` | 2026-06-12 | US / AC | User story liên kết (US-EXBOT-004) |
| `srs/spec.md` | 2026-06-12 | SRS — source of truth | FR-EXBOT-070, 071, 011, 026 |
| `srs/states.md` | 2026-06-12 | State diagram | Bot lifecycle states; close_operations states |
| `srs/flows.md` | 2026-06-12 | Flow diagram | F-04 (user_redeem LP-First close flow) |
| `srs/erd.md` | 2026-06-12 | ERD | close_operations, queue_idempotency, bots, hedge_legs |
| `frd.md` | 2026-06-12 | FRD | FR-EXBOT-070, 071 |
| `02_backbone/common-rules.md` | 2026-06-09 | Common rule | BR-EXBOT-006 không có trong file này (xem Issue I-001) |
| `02_backbone/message-list.md` | 2026-06-09 | Message list | E-EXBOT-010 không có trong file này (xem Issue I-001) |
| `usecases/index.md` | 2026-06-12 | Index | UC-EXBOT-user-redeem confirmed, Linked Stories: US-EXBOT-004 |
| `userstories/index.md` | 2026-06-12 | Index | US-EXBOT-004 confirmed |

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement cho module BNZA-EXBOT — mô tả hành vi cụ thể hệ thống phải thực hiện. | `frd.md`, `srs/spec.md` |
| BR-EXBOT-006 | Business Rule: "LP repayment unconditional — never blocked by hedge close failure." Trong UC này, đây là ràng buộc cốt lõi: dù hedge close thành công hay thất bại, phần USDC từ LP đã được trả on-chain và không bao giờ được đảo ngược. | `srs/spec.md` §4 |
| E-EXBOT-010 | Error code: SLA breach — "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." Đây là alert nội bộ, không phải API response cho user. | `srs/spec.md` §5 |
| E-EXBOT-011 | Error code: Reconcile mismatch — "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | `srs/spec.md` §5 |
| E-EXBOT-012 | Error code: Close attempted on already-closed bot — "Bot is already closed. No action needed." | `srs/spec.md` §5 |
| BnzaExVault | Smart contract Solidity quản lý LP NFT và custody USDC. Trong UC này, hàm `redeem(tokenId)` thực hiện toàn bộ thanh lý LP và trả USDC về ví nhà đầu tư trong 1 giao dịch. | (Proper noun) |
| LP NFT | Non-Fungible Token đại diện cho vị thế LP Uniswap V3. Khi redeem, NFT bị đốt (burn) và liquidity được rút 100%. | (industry term) |
| HL | Hyperliquid — sàn perp phi tập trung; hedge leg cần được đóng sau khi LP đã thanh lý. | (Proper noun) |
| INV-STOP | Invariant-Stop Protocol §19.5 SPEC v5.2.6 — giao thức hủy lệnh stop bảo vệ, dùng khi đóng hoàn toàn vị thế (size=0). | `srs/spec.md` FR-EXBOT-035 |
| residual_hl_liability | Trạng thái trong `close_operations` khi hedge close thất bại sau khi LP đã thanh lý — còn tồn dư vị thế hedge chưa được đóng. Admin phải xử lý thủ công. | `srs/states.md`, `frd.md` |
| RedemptionQueue | Ledger theo dõi việc gửi HL-portion USDC cho nhà đầu tư sau khi hedge đóng thành công. | UC §3 step 13 |
| cloid | Client Order ID xác định (deterministic) — dùng để HL deduplicate lệnh đóng hedge. | `srs/spec.md` FR-EXBOT-024 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-user-redeem tồn tại để cho phép nhà đầu tư thoát hoàn toàn chiến lược ExBot và nhận lại toàn bộ vốn USDC. Mục tiêu nghiệp vụ quan trọng nhất: **phần vốn LP được đảm bảo trả lại on-chain bất kể backend có hoạt động không** — điều này bảo vệ nhà đầu tư khỏi rủi ro mất vốn do lỗi hệ thống.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| On-chain LP liquidation | Investor gọi `BnzaExVault.redeem(tokenId)` → LP thanh lý 100% + USDC trả về ví investor trong cùng tx | UC §3 step 1-4, FR-EXBOT-070 |
| Redeem event detection | Event Watcher phát hiện `RedemptionEvent`; enqueue vào `user_redeem` queue (highest priority) | UC §3 step 5, FR-EXBOT-070 |
| Queue idempotency | Insert `message_id` vào `queue_idempotency`; UNIQUE conflict → skip | UC §3 step 6, FR-EXBOT-011 |
| close_operations tracking | Tạo row `close_operations` (kind='user_redeem') theo dõi state machine của close flow | UC §3 step 7, ERD |
| UserLockDO lease acquisition | Acquire mutex để ngăn concurrent HL mutation | UC §3 step 8, FR-EXBOT-026 |
| HL full close (hedge-only) | Đóng toàn bộ short ETH-USD via `closeShortReduceOnlyIoc`; cancel stop via INV-STOP (size=0) | UC §3 step 9-10, FR-EXBOT-070 |
| Post-close reconcile | Verify HL position size = 0 | UC §3 step 11, FR-EXBOT-025 |
| HL-portion USDC transfer | Gửi HL-portion USDC cho investor sau reconcile | UC §3 step 13 |
| SLA monitoring (5 min) | Nếu hedge không đóng trong 5 phút → admin alert (E-EXBOT-010) | UC §4 A1, NFR-EXBOT-003 |
| residual_hl_liability handling | Khi hedge close thất bại: trạng thái `residual_hl_liability`; admin notified | UC §4 A2, FR-EXBOT-070 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| bot_safe_close (system-initiated) | Luồng riêng: hedge-first, covered bởi UC-EXBOT-bot-safe-close | Tester không test bot_safe_close trong UC này |
| Automatic re-entry sau user_redeem | FR-EXBOT-071 (re-entry) chỉ áp dụng cho bot_safe_close, không áp dụng cho user_redeem (lifecycle_state='closed', không phải 'cooldown') | Xác nhận lại: user_redeem có kích hoạt re-entry loop không? (xem Issue I-007) |
| Trading strategy / hedge math | Ngoài phạm vi SOTATEK | Không test công thức hedge |
| UI Close Bot flow | POOL UI (PTL-05) — ngoài scope ExBot module | Tester không kiểm tra UI confirmation dialog |
| BnzaExVault internal Solidity logic | zen-proprietary; SOTATEK integrates via ABI only | Không test contract internals |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Khởi tạo redeem bằng cách gọi `BnzaExVault.redeem(tokenId)` on-chain | Chỉ investor giữ LP NFT mới có quyền gọi redeem; giao dịch on-chain, không qua backend | UC §1, FR-EXBOT-070 |
| BnzaExVault (Solidity contract) | System / External | Thực thi thanh lý LP: rút 100% liquidity, collect fees, swap sang USDC, chuyển USDC cho investor ngay trong cùng tx | Địa chỉ contract (Base + Optimism) inject qua Cloudflare Secrets Store; ABI chưa final (OQ-EXBOT-08) | UC §1, IC-EXBOT-002 |
| Redeem Event Watcher | System | Lắng nghe `RedemptionEvent` trên blockchain; enqueue vào `user_redeem` queue | Phát hiện event và enqueue trong thời gian ngắn nhất để đảm bảo SLA 5 phút | UC §3 step 5, FR-EXBOT-070 |
| user_redeem Worker (Redeem Worker) | System | Xử lý message từ `user_redeem` queue; thực hiện HL hedge close + USDC transfer | Highest priority queue; SLA 5 phút từ event detection | UC §3, NFR-EXBOT-003 |
| UserLockDO | System / External | Mutex lease per-user để ngăn concurrent HL mutation | TTL=90s auto-release | FR-EXBOT-026, FR-EXBOT-092 |
| Hyperliquid API | External | Thực thi `closeShortReduceOnlyIoc` (đóng full hedge); `cancelStop` | Rate limit 800 weight/min; all calls qua HLRateLimitDO | FR-EXBOT-091 |
| Admin (zen) | Secondary | Nhận alert khi SLA breach hoặc `residual_hl_liability`; xử lý thủ công | Admin không thể đảo ngược LP-portion repayment đã on-chain | UC §4 A1, A2 |

**Nhận xét readiness:** Actor list đủ cho test design ở mức cơ bản. Tuy nhiên, UC không đề cập `HLRateLimitDO` và không mô tả behavior khi rate limit bị vượt trong quá trình đóng hedge — đây là gap cần confirm (Issue I-005).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot `status='active'` hoặc `'paused'` hoặc `'safe_mode'` (bất kỳ trạng thái non-closed) | Yes | UC §2 |
| 2 | Investor giữ LP NFT redemption rights qua BnzaExVault | Yes | UC §2 |
| 3 | `RedemptionEvent` đã được emit on-chain từ `BnzaExVault.redeem(tokenId)` | Yes (trigger) | UC §3 step 4 |
| 4 | BnzaExVault ABI đã được confirm và deploy (OQ-EXBOT-08) | Yes (blocked) | IC-EXBOT-002 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Redeem hoàn tất (happy path) | `bots.lifecycle_state='closed'`; LP-portion USDC đã trong ví investor (on-chain); HL-portion USDC đã gửi; `close_operations.state='done'`; `queue_idempotency.state='succeeded'` | UC §5 |
| Hedge close thất bại | `close_operations.state='residual_hl_liability'`; admin notified; LP-portion USDC vẫn đã trong ví investor (không đảo ngược) | UC §5, UC §4 A2 |

---

## 6. Phân tích chức năng

### §F.1 — Danh mục chức năng / thao tác

| # | Chức năng / thao tác | Trigger | Input | Output / side-effect | Actor | Nguồn |
|---|---|---|---|---|---|---|
| 1 | On-chain LP liquidation: investor gọi `BnzaExVault.redeem(tokenId)` | Investor chủ động (on-chain tx) | `tokenId` (LP NFT) | LP NFT bị burn; 100% liquidity rút; fees collected; USDC swap → ví investor; `RedemptionEvent` emit | USDC Investor | UC §3 step 1–4, FR-EXBOT-070 |
| 2 | `RedemptionEvent` detection: Event Watcher lắng nghe on-chain event | `RedemptionEvent` emit từ BnzaExVault | `tokenId`, `botId`, `lpAmountUsdc`, `txHash` | Message enqueue vào `user_redeem` queue (highest priority) | Redeem Event Watcher | UC §3 step 5, FR-EXBOT-070 |
| 3 | Queue idempotency check: insert `message_id` vào `queue_idempotency` | Message nhận từ queue | `message_id`, `queue_name='user_redeem'` | Nếu UNIQUE conflict → bỏ qua (dedup); nếu insert OK → tiếp tục | user_redeem Worker | UC §3 step 6, FR-EXBOT-011 |
| 4 | Tạo `close_operations` row: ghi nhận luồng close bắt đầu | Message nhận từ queue (sau idempotency OK) | `bot_id`, `kind='user_redeem'`, `lp_tx_hash`, `lp_amount_usdc` | Row `close_operations` mới với `state='requested'` (SRS F-04) / `state='lp_closed'` (UC §3 step 7 — xem Issue I-002) | user_redeem Worker | UC §3 step 7, srs/states.md, srs/flows.md F-04 |
| 5 | UserLockDO lease acquisition: acquire per-user mutex | Trước bất kỳ HL mutation nào | `userId` (từ `botId`) | Mutex lock với TTL=90s; nếu locked bởi process khác → queue lại / error | user_redeem Worker | UC §3 step 8, FR-EXBOT-026 |
| 6 | HL full hedge close: gửi `closeShortReduceOnlyIoc` để đóng 100% short ETH-USD | Sau khi UserLockDO acquired | `size=totalShortSize`, `cloid=deterministic(botId, attemptId, 'close', version)` | Lệnh đóng hedge gửi lên Hyperliquid; `hedge_legs.close_cloid` ghi nhận | user_redeem Worker | UC §3 step 9, FR-EXBOT-070, FR-EXBOT-024 |
| 7 | INV-STOP: hủy lệnh stop bảo vệ khi size=0 | Sau khi hedge close order submitted (size = 0) | `stop_cloid` hiện tại | Stop order hủy trên HL; `hedge_legs.stop_cloid` cleared | user_redeem Worker | UC §3 step 10, FR-EXBOT-035, OQ-EXBOT-02 |
| 8 | Post-close reconcile: verify HL position size = 0 | Sau khi hedge close order filled | `clearinghouseState` từ HL API | Xác nhận `actual_short_size=0`; nếu mismatch → xem Issue I-003 alt flow | user_redeem Worker | UC §3 step 11, FR-EXBOT-025 |
| 9 | `close_operations` state update: ghi nhận hedge đã đóng | Sau reconcile OK | `bot_id` | `close_operations.state='hedge_closed'`; `bots.lifecycle_state='closed'` | user_redeem Worker | UC §3 step 12, srs/states.md |
| 10 | HL-portion USDC transfer: gửi USDC cho investor | Sau hedge closed + reconcile | `hl_portion_usdc`, địa chỉ ví investor | USDC chuyển đến ví investor; `close_operations.state='done'` | user_redeem Worker | UC §3 step 13, FR-EXBOT-070 |
| 11 | SLA breach escalation: alert admin khi hedge không đóng trong 5 phút | Timer T+5 min kể từ event detection | SLA timestamp, `botId` | E-EXBOT-010 gửi đến admin; trạng thái escalated | SLA Monitor | UC §4 A1, NFR-EXBOT-003 |
| 12 | `residual_hl_liability` handling: ghi nhận hedge close thất bại | Hedge close fail không thể retry | Error context | `close_operations.state='residual_hl_liability'`; admin notified; LP-portion không bị đảo ngược | user_redeem Worker | UC §4 A2, BR-EXBOT-006 |
| 13 | Duplicate message handling: phát hiện idempotency conflict | `message_id` UNIQUE conflict trong `queue_idempotency` | `message_id` | Bỏ qua message; không tạo thêm `close_operations` row | user_redeem Worker | UC §4 A3, FR-EXBOT-011 |

---

### §F.2 — Trạng thái, tiền điều kiện, nghiệp vụ, xác thực

| # | Chức năng (ref §F.1) | Trạng thái bot / system khi bắt đầu | Tiền điều kiện bắt buộc | Business rule / ràng buộc | Kết quả trạng thái sau | Xác thực / validation | Nguồn |
|---|---|---|---|---|---|---|---|
| 1 | On-chain LP liquidation (§F.1.1) | `bots.lifecycle_state` = bất kỳ non-closed | Investor giữ LP NFT `tokenId`; BnzaExVault ABI deployed (OQ-EXBOT-08) | BR-EXBOT-006: LP repayment unconditional | On-chain: LP NFT burned, USDC → investor; Off-chain: chưa thay đổi | Chỉ owner LP NFT mới gọi được (on-chain guard) | FR-EXBOT-070, IC-EXBOT-002 |
| 2 | RedemptionEvent detection (§F.1.2) | — | `RedemptionEvent` đã emit on-chain | — | Message trong `user_redeem` queue | Event Watcher cần phát hiện đủ sớm để đảm bảo SLA 5 phút | FR-EXBOT-070, NFR-EXBOT-003 |
| 3 | Queue idempotency (§F.1.3) | — | Message có `message_id` | — | Insert OK → tiếp tục; UNIQUE conflict → skip | `queue_idempotency.message_id` UNIQUE constraint (D1) | FR-EXBOT-011, srs/erd.md |
| 4 | Tạo `close_operations` (§F.1.4) | Bot chưa có `close_operations.kind='user_redeem'` đang active | `message_id` insert thành công | — | `close_operations.state='requested'` (SRS) — xem Issue I-002 | Không có 2 close_operations active cùng `bot_id` | srs/states.md, srs/flows.md F-04 |
| 5 | UserLockDO acquisition (§F.1.5) | — | UserLockDO không bị lock bởi process khác cho cùng `userId` | TTL=90s; heartbeat nếu work > 30s (FR-EXBOT-026) | Mutex lock giữ trong suốt HL operation | Lock failure → re-queue message | FR-EXBOT-026, FR-EXBOT-092 |
| 6 | HL full hedge close (§F.1.6) | `hedge_legs.actual_short_size > 0` | UserLockDO acquired; HLRateLimitDO `allowed=true` | `cloid` deterministic = `keccak256("bnza:{botId}:{attemptId}:close:{version}")` (FR-EXBOT-024) | Lệnh gửi HL; `hedge_legs.close_cloid` ghi nhận | Verify `cloid` format | FR-EXBOT-070, FR-EXBOT-024 |
| 7 | INV-STOP (§F.1.7) | `hedge_legs.stop_cloid` not null | Hedge close order submitted | FR-EXBOT-035: INV-STOP khi size=0 | Stop order hủy trên HL | Verify stop canceled (OQ-EXBOT-02 còn open) | FR-EXBOT-035, OQ-EXBOT-02 |
| 8 | Post-close reconcile (§F.1.8) | Hedge close order expected filled | `closeShortReduceOnlyIoc` order sent | `\|actual - target\| = 0` (size=0 expected) | Reconcile OK → tiếp tục; mismatch → `residual_hl_liability` hoặc escalation | `clearinghouseState` weight=2, tính vào 800/min rate | FR-EXBOT-025, FR-EXBOT-091 |
| 9 | `close_operations` state update (§F.1.9) | Reconcile OK | — | — | `close_operations.state='hedge_closed'`; `bots.lifecycle_state='closed'` | `stateVersion` optimistic concurrency check | srs/states.md, srs/erd.md |
| 10 | HL-portion USDC transfer (§F.1.10) | `close_operations.state='hedge_closed'` | Hedge fully closed, reconciled | BR-EXBOT-006 ensures LP-portion already paid | USDC transferred; `close_operations.state='done'` | — | FR-EXBOT-070 |
| 11 | SLA breach (§F.1.11) | Hedge close chưa hoàn tất sau T+5 min | Event detected timestamp available | NFR-EXBOT-003: SLA = 5 phút | Admin alert gửi (E-EXBOT-010) | — | NFR-EXBOT-003, E-EXBOT-010 |
| 12 | residual_hl_liability (§F.1.12) | Hedge close thất bại, không retry | LP-portion đã on-chain không thể đảo ngược | BR-EXBOT-006 | `close_operations.state='residual_hl_liability'`; admin notified | — | BR-EXBOT-006, srs/states.md |
| 13 | Duplicate msg (§F.1.13) | — | `message_id` đã có trong `queue_idempotency` | — | Skip processing | UNIQUE constraint raise error → caught by worker | FR-EXBOT-011 |

---

### §F.3 — Phân tích luồng (happy path + alternate / exception)

#### §F.3.1 — Happy path: User-Initiated Redemption (LP-First)

| Bước | Actor | Hành động / sự kiện | Expected output / state change | Nguồn |
|---|---|---|---|---|
| 1 | USDC Investor | Gọi `BnzaExVault.redeem(tokenId)` on-chain | LP NFT burned; 100% liquidity withdrawn; fees collected; USDC swapped & transferred → investor wallet; `RedemptionEvent` emit | UC §3 step 1–4 |
| 2 | Redeem Event Watcher | Phát hiện `RedemptionEvent` | Message enqueue `user_redeem` queue (highest priority, SLA 5 min clock starts) | UC §3 step 5 |
| 3 | user_redeem Worker | Insert `message_id` vào `queue_idempotency` | OK — tiếp tục xử lý | UC §3 step 6 |
| 4 | user_redeem Worker | Tạo `close_operations(kind='user_redeem', state='requested')` | Row mới trong D1 `close_operations` | UC §3 step 7 (SRS flow F-04 — xem Issue I-002) |
| 5 | user_redeem Worker | Acquire `UserLockDO` lease (`userId`, TTL=90s) | Mutex lock acquired | UC §3 step 8 |
| 6 | user_redeem Worker | Gửi `closeShortReduceOnlyIoc(size=totalShort, cloid=deterministic)` lên Hyperliquid | HL order placed; `hedge_legs.close_cloid` recorded | UC §3 step 9 |
| 7 | user_redeem Worker | Execute INV-STOP: hủy stop order hiện tại (size=0 → stop không cần thiết) | Stop order canceled trên HL; `hedge_legs.stop_cloid` cleared | UC §3 step 10 |
| 8 | user_redeem Worker | Fetch `clearinghouseState` → verify position size = 0 | Reconcile OK: `actual_short_size = 0` | UC §3 step 11 |
| 9 | user_redeem Worker | Update `close_operations.state='hedge_closed'`; `bots.lifecycle_state='closed'` | D1 state updated; `stateVersion` incremented | UC §3 step 12 |
| 10 | user_redeem Worker | Transfer HL-portion USDC → investor wallet; update `close_operations.state='done'` | USDC sent; ledger updated; `queue_idempotency.state='succeeded'` | UC §3 step 13 |

#### §F.3.2 — Alternate A1: SLA breach (hedge not closed within 5 minutes)

| Bước | Actor | Hành động / sự kiện | Expected output / state change | Nguồn |
|---|---|---|---|---|
| 1 | SLA Monitor | T+5 min kể từ `RedemptionEvent` detected; hedge chưa đóng | E-EXBOT-010 alert gửi đến admin | UC §4 A1, NFR-EXBOT-003 |
| 2 | Admin (zen) | Nhận alert; xử lý thủ công | Admin quyết định tiếp tục retry hay đóng thủ công trên HL | UC §4 A1 |
| **Gap** | — | UC không mô tả: sau khi admin nhận alert, hệ thống có tiếp tục retry hedge close không? Retry tối đa mấy lần? Circuit breaker có được sử dụng không? | Chưa có expected behavior → Issue I-006 | UC §4 A1 thiếu |

#### §F.3.3 — Alternate A2: Hedge close fails permanently → `residual_hl_liability`

| Bước | Actor | Hành động / sự kiện | Expected output / state change | Nguồn |
|---|---|---|---|---|
| 1 | user_redeem Worker | Hedge close thất bại (retry exhausted hoặc unrecoverable error) | `close_operations.state='residual_hl_liability'`; admin notified | UC §4 A2 |
| 2 | System | LP-portion USDC đã trong ví investor (on-chain, không thể đảo ngược) | BR-EXBOT-006 — LP repayment unconditional | BR-EXBOT-006 |
| **Gap** | — | UC không nêu rõ: điều kiện nào kích hoạt A2 (fail sau bao nhiêu retry? circuit breaker open?) vs tiếp tục retry; `funds_parked` state trong SRS nhưng không xuất hiện trong UC | Issue I-003, I-004 | srs/states.md |

#### §F.3.4 — Alternate A3: Duplicate `RedemptionEvent` message

| Bước | Actor | Hành động / sự kiện | Expected output / state change | Nguồn |
|---|---|---|---|---|
| 1 | user_redeem Worker | `message_id` UNIQUE conflict trong `queue_idempotency` | Worker bắt exception; bỏ qua message; không tạo thêm `close_operations` row | UC §4 A3, FR-EXBOT-011 |

---

### §F.4 — Tác động liên chức năng, hàng đợi, và nhất quán dữ liệu

| Thao tác | Bảng / object bị ảnh hưởng | Cột / field thay đổi | Điều kiện nhất quán | Rủi ro nhất quán | Nguồn |
|---|---|---|---|---|---|
| Tạo `close_operations` | `close_operations` | `kind`, `state`, `bot_id`, `lp_tx_hash` | Không có 2 active rows cùng `bot_id` và `kind='user_redeem'` | Nếu message duplicate qua được idempotency (race condition) → 2 close_operations rows | FR-EXBOT-011, srs/erd.md |
| `bots.lifecycle_state='closed'` | `bots` | `lifecycle_state`, `state_version` | `state_version` phải match message `stateVersion` (optimistic concurrency) | Nếu `state_version` mismatch → worker phải retry hoặc vào error state | srs/erd.md, srs/spec.md |
| LP-portion transfer (on-chain) | BnzaExVault (on-chain) | LP NFT burned; USDC transferred | On-chain guarantee — không thể rollback | Không có rủi ro rollback; nhưng nếu backend chưa biết event → bot vẫn `active`, inconsistent với on-chain state | BR-EXBOT-006 |
| HL hedge close | `hedge_legs` | `close_cloid`, `actual_short_size` | Sau reconcile: `actual_short_size = 0` | Partial fill edge case: vị thế còn lại → `residual_hl_liability` | FR-EXBOT-025, srs/erd.md |
| `queue_idempotency` | `queue_idempotency` | `message_id`, `state` | UNIQUE `message_id` → dedup đảm bảo | Race condition nếu 2 workers xử lý cùng `message_id` đồng thời trước khi constraint raised | FR-EXBOT-011, srs/erd.md |
| `close_operations.state='done'` | `close_operations`, `bots` | `state`, `lifecycle_state` | Cả hai update trong cùng D1 transaction (không rõ — chưa documented) | Nếu `close_operations` = 'done' nhưng `bots.lifecycle_state` không updated → inconsistent | srs/erd.md (gap) |
| `RedemptionQueue` ledger (HL-portion) | Không có bảng `redemption_queue` trong ERD | — | **ERD không có bảng này** | UC §3 step 13 cite "RedemptionQueue ledger" nhưng ERD không define → Issue I-005 | UC §3 step 13, srs/erd.md |

---

### §F.5 — AC candidates (Acceptance Criteria ứng viên)

> Các AC đánh dấu *"Suy luận cần xác nhận"* là do QC suy luận từ SRS, chưa được UC/US xác nhận tường minh.

| # | AC candidate | Nguồn | Cần xác nhận? |
|---|---|---|---|
| AC-1 | Khi investor gọi `BnzaExVault.redeem(tokenId)`, LP NFT bị burn và USDC được trả về ví investor trong cùng giao dịch on-chain, trước khi backend nhận event. | UC §3 step 1–4, BR-EXBOT-006 | Không |
| AC-2 | Khi Event Watcher phát hiện `RedemptionEvent`, message được enqueue vào `user_redeem` queue với priority cao nhất trong vòng dưới 5 phút (SLA đảm bảo toàn bộ hedge close, không chỉ enqueue). | NFR-EXBOT-003, UC §4 A1 | Suy luận cần xác nhận — SLA 5 phút tính từ event detection hay từ giao dịch on-chain? |
| AC-3 | Khi cùng `message_id` xuất hiện lần 2 trong `user_redeem` queue, worker bỏ qua message mà không tạo thêm `close_operations` row và không gửi HL order mới. | FR-EXBOT-011, UC §4 A3 | Không |
| AC-4 | `close_operations(kind='user_redeem')` được tạo với `state='requested'` (SRS) ngay sau khi idempotency check pass, trước khi UserLockDO được acquire. | srs/flows.md F-04 | Suy luận cần xác nhận — UC §3 step 7 mô tả state khác (xem Issue I-002) |
| AC-5 | UserLockDO TTL=90s auto-release; nếu work > 30s, worker phải gọi heartbeat để gia hạn lease. | FR-EXBOT-026, FR-EXBOT-092 | Suy luận cần xác nhận — UC §3 step 8 không đề cập heartbeat |
| AC-6 | Lệnh đóng hedge gửi lên HL là `closeShortReduceOnlyIoc` với `cloid=keccak256("bnza:{botId}:{attemptId}:close:{version}")`. | FR-EXBOT-024, FR-EXBOT-070 | Không |
| AC-7 | Sau khi `closeShortReduceOnlyIoc` filled, hệ thống fetch `clearinghouseState` và xác nhận `actual_short_size = 0`. Nếu `actual_short_size ≠ 0` → hedge close thất bại → `residual_hl_liability`. | FR-EXBOT-025, UC §4 A2 | Suy luận cần xác nhận — ngưỡng mismatch cụ thể (ví dụ, tolerance dust?) chưa rõ |
| AC-8 | Dù hedge close thành công hay thất bại, LP-portion USDC không bao giờ được đảo ngược (đã on-chain). Admin chỉ xử lý phần HL còn tồn dư. | BR-EXBOT-006 | Không |
| AC-9 | Nếu hedge không đóng trong 5 phút kể từ khi Event Watcher phát hiện `RedemptionEvent`, E-EXBOT-010 được gửi đến admin. | NFR-EXBOT-003, E-EXBOT-010 | Suy luận cần xác nhận — cơ chế đo 5 phút chưa rõ (timer trong worker? cron job?) |
| AC-10 | US-EXBOT-004 AC-1 nêu "system triggers on-chain BnzaExVault.redeem(tokenId)" — **trái ngược** với UC §3 step 1 nơi investor chủ động gọi. Cần xác nhận ai là người khởi tạo giao dịch on-chain. | US-EXBOT-004 AC-1, UC §3 step 1 | **Xác nhận bắt buộc** — xem Issue I-001 |

---

## 7. Phân tích tác động liên chức năng

| Chức năng / Module | Loại tương tác | Mô tả tác động | Rủi ro nếu bị lỗi | Nguồn |
|---|---|---|---|---|
| BnzaExVault (on-chain contract) | Phụ thuộc vào event | Event Watcher phải lắng nghe đúng event `RedemptionEvent` từ đúng địa chỉ contract (Base + Optimism) | Nếu ABI chưa final (OQ-EXBOT-08) → Event Watcher có thể không decode được event → SLA breach | IC-EXBOT-002 |
| Hyperliquid API | External call | `closeShortReduceOnlyIoc` + `cancelStop` phải đi qua `HLRateLimitDO` (800 weight/min) | Rate limit vượt ngưỡng → HL call bị block → hedge close delay → SLA breach | FR-EXBOT-091 |
| UserLockDO | Distributed mutex | Bảo vệ concurrent HL mutation; TTL=90s | Nếu worker khác giữ lock → user_redeem Worker phải chờ hoặc re-queue → thêm delay | FR-EXBOT-026 |
| circuit_breakers | State machine | UC không đề cập circuit breaker trong user_redeem flow | Nếu circuit breaker đang `open` khi hedge close cần execute → behavior chưa defined | srs/states.md |
| hedge-sync Worker | Queue contention | Cả hedge-sync và user_redeem cùng cần `UserLockDO` và HLRateLimitDO | Race condition: hedge-sync đang giữ lock → user_redeem bị delay | FR-EXBOT-026, FR-EXBOT-091 |
| bot_safe_close | Separate UC | Hai close system độc lập; user_redeem là LP-first; bot_safe_close là hedge-first | Không được xử lý đồng thời (UserLockDO ngăn) | FR-EXBOT-070 |
| FR-EXBOT-071 (auto re-entry) | FR trace mismatch | UC FR Trace cite FR-EXBOT-071 nhưng re-entry chỉ áp dụng cho bot_safe_close (lifecycle_state='cooldown' → 'active'). user_redeem → 'closed' → re-entry không xảy ra | Tester có thể test sai scope nếu nhầm re-entry thuộc user_redeem | UC index, srs/spec.md |

---

## 8. Acceptance Criteria — Tóm tắt

> Xem đầy đủ AC candidates tại §F.5. Phần này tóm tắt các AC có thể viết test case ngay.

| AC ID | Mô tả ngắn | Trạng thái | Ghi chú |
|---|---|---|---|
| AC-1 | LP NFT burned + USDC trả về ví investor on-chain trong cùng tx | Có thể test | On-chain guarantee |
| AC-2 | SLA 5 phút: hedge close phải complete trong 5 phút từ event detection | Có thể test (cần làm rõ T0) | SLA measurement cơ chế chưa rõ |
| AC-3 | Duplicate message → skip, không tạo thêm close_operations | Có thể test | FR-EXBOT-011 |
| AC-6 | HL close order dùng `closeShortReduceOnlyIoc` với deterministic cloid | Có thể test | FR-EXBOT-024 |
| AC-7 | Reconcile: `actual_short_size = 0` sau close order filled | Có thể test | FR-EXBOT-025 |
| AC-8 | LP-portion không bị đảo ngược dù hedge close fail | Có thể test | BR-EXBOT-006 |
| AC-4, 5, 9, 10 | Cần xác nhận với BA trước khi viết test case | Blocked | Xem Issue Register §10.1 |

---

## 9. NFR liên quan

| NFR ID | Nội dung | Nguồn | Có thể test? | Ghi chú |
|---|---|---|---|---|
| NFR-EXBOT-003 | Hedge close for user_redeem phải hoàn tất trong 5 phút kể từ khi Event Watcher phát hiện `RedemptionEvent` | `srs/spec.md` NFR-EXBOT-003 | Có — cần mock delay hoặc inject SLA timer | Cơ chế đo SLA chưa mô tả trong UC (Issue I-006) |

---

## 10. Issue Register, Dependencies, và Audit Summary

### §10.1 — Issue Register

| Issue ID | Type | Severity | Affected area | Source trace | Finding | Impact on tester understanding | Suggested question or fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-001 | CROSS_SOURCE_CONFLICT | Major | Area 3 Workflow | US-EXBOT-004 AC-1 vs UC §3 step 1 | US-EXBOT-004 AC-1 mô tả "system triggers on-chain `BnzaExVault.redeem(tokenId)`" — nhưng UC §3 step 1 xác định investor chủ động gọi `BnzaExVault.redeem(tokenId)` on-chain. Hai nguồn mô tả ngược nhau về người khởi tạo giao dịch on-chain: US nói system trigger, UC nói investor trigger. | Tester không biết ai là actor khởi tạo: nếu system trigger → cần test backend call; nếu investor trigger → không cần test backend cho bước này. Sai actor = sai toàn bộ test scenario. | BA xác nhận: `BnzaExVault.redeem(tokenId)` do investor chủ động gọi (UC §3) hay do system backend trigger? Cập nhật US-EXBOT-004 AC-1 cho nhất quán với UC. | Open |
| I-002 | CROSS_SOURCE_CONFLICT | Major | Area 3 Workflow | UC §3 step 7 vs srs/states.md close_operations; srs/flows.md F-04 | UC §3 step 7 dùng `state='lp_closed→funds_returned'` — hai trạng thái gộp thành một giá trị. SRS states.md định nghĩa đây là hai trạng thái riêng biệt trong `close_operations`: `lp_closed` và `funds_returned`. Thêm vào đó, SRS flow F-04 chỉ rõ bước đầu tiên là tạo `close_operations(state='requested')`, nhưng UC §3 step 7 bỏ qua trạng thái `requested` hoàn toàn. | Tester không biết đâu là trạng thái D1 thực sự: (a) một string `'lp_closed→funds_returned'`, (b) hai trạng thái riêng `lp_closed` rồi `funds_returned`, hay (c) `requested` là trạng thái đầu tiên. Thiết kế test case cho D1 state sẽ sai nếu không xác nhận. | BA cập nhật UC §3 step 7 để: (1) mô tả `state='requested'` là trạng thái khởi tạo; (2) tách `lp_closed` và `funds_returned` thành hai bước riêng theo srs/states.md. | Open |
| I-003 | MISSING_INFO | Major | Area 3 Workflow | UC §4 A2; srs/states.md (`funds_parked`) | UC §4 A2 chỉ nêu "hedge close fails → `residual_hl_liability`" mà không mô tả: (a) điều kiện cụ thể kích hoạt A2 (fail sau bao nhiêu lần retry? circuit breaker open?); (b) trạng thái `funds_parked` xuất hiện trong SRS states.md nhưng không được đề cập trong UC flow. Không rõ `funds_parked` có được dùng trong user_redeem không và khác gì `residual_hl_liability`. | Tester không thể thiết kế test case cho nhánh "hedge close fail": không biết retry logic, không biết khi nào enter `residual_hl_liability` vs `funds_parked`. | BA làm rõ: (1) điều kiện trigger `residual_hl_liability` (số lần retry, circuit breaker state); (2) `funds_parked` có thuộc user_redeem flow không? Bổ sung vào UC §4 A2. | Open |
| I-004 | MISSING_INFO | Major | Area 2 Rules/States | UC §3 (missing); srs/flows.md F-04; FR-EXBOT-091 | UC không có alternate flow khi `HLRateLimitDO` trả về `{allowed: false, retryAfterMs}` trước khi gửi `closeShortReduceOnlyIoc`. FR-EXBOT-091 yêu cầu caller không proceed với HL call và phải re-queue. Thiếu hoàn toàn trong UC §3. | Tester không biết expected behavior khi HL rate limit vượt ngưỡng giữa user_redeem hedge close — đặc biệt nguy hiểm vì SLA 5 phút, delay thêm có thể gây SLA breach. | BA bổ sung alternate flow: "HLRateLimitDO returns `allowed=false` → worker re-queues message với `retryAfterMs` delay; không submit HL call; SLA timer tiếp tục chạy." | Open |
| I-005 | MISSING_INFO | Major | Area 4 Integration | UC §3 step 13; srs/erd.md | UC §3 step 13 cite "RedemptionQueue ledger" để theo dõi HL-portion USDC transfer cho investor, nhưng `srs/erd.md` không có bảng `redemption_queue`. Không có schema, không có `message_id` dedup, không có `state` tracking cho bước này. | Tester không thể verify D1 state sau HL-portion transfer vì không có bảng canonical. Nếu transfer fail → không rõ retry mechanism và idempotency đảm bảo thế nào. | BA xác nhận: (a) "RedemptionQueue ledger" là bảng D1 chưa được thêm vào ERD, hay là một cơ chế khác (ví dụ: Cloudflare Queue với idempotency riêng)? Bổ sung vào `srs/erd.md` nếu là D1 table. | Open |
| I-006 | MISSING_INFO | Minor | Area 3 Workflow | UC §4 A1; NFR-EXBOT-003 | UC §4 A1 mô tả SLA breach → alert admin, nhưng không nêu cơ chế đo thời gian 5 phút: timer nằm trong worker? cron job độc lập? dựa vào `close_operations.created_at`? Thiếu mô tả T0 (khi nào đồng hồ bắt đầu chạy). | Tester không thể viết test case cho "SLA breach at T+5min" nếu không biết T0 được lưu ở đâu và cơ chế timeout nằm ở component nào. | BA bổ sung vào UC §4 A1: T0 = timestamp khi Event Watcher enqueue message; SLA được đo bởi [component X]; timeout xử lý bởi [worker / cron / alarm]. | Open |
| I-007 | MISSING_INFO | Minor | Area 2 Rules/States | UC §1.3 Ngoài phạm vi; UC index; srs/spec.md FR-EXBOT-071 | UC FR Trace trong `usecases/index.md` cite FR-EXBOT-071 (automatic re-entry), nhưng §1.3 của UC này đã xác nhận re-entry không áp dụng cho user_redeem (lifecycle_state='closed', không phải 'cooldown'). Tuy nhiên, UC body không có đoạn giải thích tường minh lý do FR-EXBOT-071 bị loại trừ. | Nếu tester thấy FR-EXBOT-071 trong FR Trace của index, họ có thể test re-entry cho user_redeem — sẽ là false positive. | BA loại bỏ FR-EXBOT-071 khỏi FR Trace của UC-EXBOT-user-redeem trong `usecases/index.md`, hoặc thêm ghi chú tường minh: "FR-EXBOT-071 không áp dụng cho user_redeem — chỉ áp dụng cho bot_safe_close." | Open |
| I-008 | MISSING_INFO | Minor | Area 3 Workflow | UC §3 step 8; FR-EXBOT-026 | UC §3 step 8 mô tả "acquire UserLockDO" nhưng không có alternate flow khi: (a) lock đã bị giữ bởi process khác (hedge-sync đang chạy); (b) heartbeat fail khi work > 30s. FR-EXBOT-026 nêu heartbeat extension nhưng không được phản ánh trong UC. | Tester không biết expected behavior khi UserLockDO bị giữ bởi hedge-sync Worker → deadlock scenario không được cover. | BA bổ sung alternate flow: "UserLockDO already locked → re-queue sau [interval]; max retry [N]; heartbeat khi work > 30s." | Open |
| I-009 | AMBIGUOUS_WORDING | Note | Area 5 Doc Quality | UC §3 step 7 | UC §3 step 7 viết `state='lp_closed→funds_returned'` dùng ký hiệu mũi tên (→) trong giá trị string — không rõ đây là: (a) một string literal `'lp_closed→funds_returned'`, (b) transition từ `lp_closed` sang `funds_returned`, hay (c) ký hiệu viết tắt của hai trạng thái. | Tester có thể interpret sai string D1 field value, dẫn đến assertion sai trong automation test. | BA dùng ký hiệu rõ ràng: nếu là transition thì viết "state chuyển từ `lp_closed` sang `funds_returned`"; nếu là 2 bước riêng thì mô tả 2 dòng. | Open |

---

### §10.2 — Dependencies

| Dependency | Loại | Mô tả | Blocked items | Status |
|---|---|---|---|---|
| OQ-EXBOT-08: BnzaExVault ABI finalization | External (on-chain) | ABI chưa final → Event Watcher không thể decode `RedemptionEvent` chính xác; integration test không thể chạy trên testnet | Toàn bộ UC test design | Open |
| OQ-EXBOT-02: INV-STOP path resolution (NV-3) | Open question | INV-STOP có 2 path (place-before-cancel / cancel-then-place) — chưa xác định path nào dùng cho user_redeem | I-007 (INV-STOP test case) | Open |
| `srs/erd.md` thiếu `redemption_queue` table | Documentation gap | UC §3 step 13 cite "RedemptionQueue ledger" nhưng ERD không có | I-005; test case cho HL-portion transfer | Open |

---

### §10.3 — Audit Summary

#### Bảng điểm

| Khu vực đánh giá | Điểm tối đa | Điểm đạt | Ghi chú |
|---|---|---|---|
| Area 1: Inventory (§F.1) | 20 | 16 | §F.1 đầy đủ 13 operations; thiếu `funds_parked` state và `redemption_queue` data object |
| Area 2: Rules/States/Messages (§F.2) | 25 | 17 | BR-EXBOT-006 + E-EXBOT-010/011 present; thiếu HLRateLimitDO alternate flow; `close_operations` state machine không khớp SRS (-4); heartbeat missing (-4) |
| Area 3: Workflow (§F.3) | 25 | 14 | Happy path đủ; A1 SLA behavior after alert chưa rõ (-3); A2 retry/circuit breaker logic missing (-4); `requested` state missing from flow (-4) |
| Area 4: Integration (§F.4) | 15 | 9 | BnzaExVault ABI blocked; `redemption_queue` không có ERD; D1 transaction boundary chưa rõ (-6) |
| Area 5: Doc Quality (§F.5) | 15 | 10 | US-EXBOT-004 AC-1 mâu thuẫn trực tiếp với UC §3 step 1 (Major cross-source conflict); state notation ambiguous (-5) |
| **Tổng** | **100** | **66** | |

**Verdict: NOT READY (66/100)**

Ngưỡng: 90–100 = Ready; 70–89 = Conditionally Ready; 0–69 = Not Ready.

#### Blocker

Không có issue tự động fail (auto-fail), nhưng có 1 issue Major có tác động blocker thực tế:

- **I-001 (CROSS_SOURCE_CONFLICT — Major)**: US-EXBOT-004 AC-1 mâu thuẫn với UC §3 step 1 về actor khởi tạo `BnzaExVault.redeem(tokenId)`. Đây là mâu thuẫn fundamental ảnh hưởng đến toàn bộ actor model của UC — tester không thể xác định scope test đúng khi nguồn gốc giao dịch on-chain chưa thống nhất.

#### Các issues Major

| Issue ID | Severity | Tóm tắt |
|---|---|---|
| I-001 | Major | US vs UC mâu thuẫn: actor khởi tạo BnzaExVault.redeem(tokenId) |
| I-002 | Major | UC §3 step 7: `close_operations` state không khớp SRS (thiếu `requested`; notation sai) |
| I-003 | Major | UC §4 A2: điều kiện và retry logic cho `residual_hl_liability` chưa rõ; `funds_parked` missing |
| I-004 | Major | HLRateLimitDO alternate flow hoàn toàn vắng mặt trong user_redeem UC |
| I-005 | Major | "RedemptionQueue ledger" cite trong UC §3 step 13 không có trong ERD |

#### Khuyến nghị

UC-EXBOT-user-redeem chứa nhiều mâu thuẫn giữa US và UC, đặc biệt nghiêm trọng ở Issue I-001 (actor khởi tạo on-chain) và I-002 (close_operations state machine). Ngoài ra, hai integration gap quan trọng (I-004: HLRateLimitDO; I-005: RedemptionQueue ledger) cản trở hoàn toàn test design cho phần hedge close. BA cần resolve I-001 và I-002 trước, sau đó cập nhật UC để align với SRS flow F-04 và states.md. Sau khi BA cập nhật và OQ-EXBOT-08 (BnzaExVault ABI) được confirm, UC có thể đạt ngưỡng "Conditionally Ready" (70+) và QC có thể tiến hành viết test case.

---

## 11. Changelog

| Version | Ngày | Tác giả | Mô tả thay đổi |
|---|---|---|---|
| v1 | 2026-06-18 | QC UC Read ExBot Agent | Tạo mới — full SRS-first cross-check audit cho UC-EXBOT-user-redeem. Score: 66/100, Verdict: Not Ready. 9 issues (5 Major, 3 Minor, 1 Note). |
