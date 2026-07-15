---
title: "UC Readiness Review — UC-EXBOT-user-redeem (User-Initiated Redemption)"
date_created: 2026-07-15
author: QC UC Read ExBot Agent
version: v5
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-user-redeem.md (updated 2026-07-14)
prior_report: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260707_v4.md
---

# UC Readiness Review — UC-EXBOT-user-redeem v5

## Feature Brief

**UC-EXBOT-user-redeem** mô tả luồng đổi thưởng do nhà đầu tư khởi tạo cho ExBot managed LP-hedge bot. Đây là luồng LP-first với bảo đảm trên chuỗi: nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` trực tiếp trên chuỗi, lập tức thanh lý LP và hoàn trả LP-portion USDC trong cùng một giao dịch. Sau đó, Redeem Worker ngoài chuỗi đóng vị thế short hedge trên HL một cách độc lập theo SLA 5 phút. HL-portion USDC được gửi cho nhà đầu tư sau khi hedge đóng thành công. Nếu hedge close thất bại (sau 3 lần thử trong cùng Lambda invocation hoặc reconcile không khớp), bot chuyển sang `residual_hl_liability` và admin được thông báo qua E-EXBOT-024. LP-portion repayment là vô điều kiện và không bao giờ bị đảo ngược (BR-EXBOT-006).

**Thay đổi trong phiên bản này (audit v5 — 2026-07-15):** BA đã cập nhật tài liệu vào ngày 2026-07-14 với nhiều fix đáng kể: (1) Thêm step 9 mới (`hedge_close_pending`) vào UC main flow; (2) Đánh số lại steps 10–15 → 11–16; (3) Mở rộng preconditions liệt kê đủ 6 `lifecycle_state` được phép; (4) Làm rõ retry strategy là in-invocation; (5) Thêm reference F-04 với Redlock participant đầy đủ; (6) Đồng bộ số FR: FR-EXBOT-091 (Rate Limiter), FR-EXBOT-092 (User Lock), FR-EXBOT-093 (Pool Slot0 Cache). Đồng thời, BA và Tech Lead đã trả lời các câu hỏi mở trong `qc-responses-2026-07-14.md`, đóng 6 issues (I-02bc, I-03, I-N1, I-N2, I-N3, I-N4). Câu hỏi I-02a (công thức tính HL-portion amount) vẫn Open.

**Score v4: 80/100 — Conditionally Ready.** Re-audit này đánh giá toàn bộ tác động của các cập nhật tài liệu 2026-07-14 và BA responses.

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case ID — module ExBot | usecases/index.md |
| FR-EXBOT-* | Functional Requirement — ExBot SRS spec | srs/spec.md |
| BR-EXBOT-* | Business Rule — module ExBot | srs/spec.md §4 Business Rules |
| E-EXBOT-* | Mã lỗi / thông báo — ExBot | backbone/message-list.md |
| SLA | Service Level Agreement — ràng buộc thời gian cho thao tác bất đồng bộ. Trong UC này: hedge close ≤ 5 phút từ khi phát hiện sự kiện (NFR-EXBOT-003). | industry term |
| HL | Hyperliquid — sàn perpetual DEX bên ngoài dùng để mở vị thế short delta-hedge | proper noun |
| LP | Liquidity Provider — vị thế Uniswap V3 do BnzaExVault quản lý; khi redeem, LP bị thanh lý on-chain | industry term |
| IOC | Immediate-or-Cancel — loại lệnh HL dùng cho hedge close (`closeShortReduceOnlyIoc`) | industry term |
| Redlock | Redis Redlock — thuật toán distributed mutex, ngăn nhiều worker cùng thực hiện HL mutation cho một bot | industry term |
| ElastiCache | AWS ElastiCache Redis — cụm Redis dùng cho User Lock (Redlock) và các cache khác | proper noun |
| SQS | AWS Simple Queue Service — hàng đợi FIFO cho user_redeem queue (độ ưu tiên cao nhất) | proper noun |
| SAFE_MODE | Trạng thái bot khi mọi mutation bị chặn; giám sát tiếp tục. Trong user_redeem (A2 — LP đã thanh lý), SAFE_MODE không áp dụng vì không còn LP để bảo vệ. | defined in spec.md |

---

## §0 Scope & Linked Artifacts

| Item | Value |
|---|---|
| UC ID | UC-EXBOT-user-redeem |
| Linked User Story | US-EXBOT-004 |
| FR Trace (UC §7 — updated 2026-07-14) | FR-EXBOT-070 |
| SRS Baseline | srs/spec.md, srs/states.md, srs/flows.md, srs/erd.md (as of 2026-07-14) |
| FRD Baseline | frd.md (as of 2026-07-14 — FR renumbering: 091=Rate Limiter, 092=User Lock, 093=Pool Slot0 Cache) |
| BA Responses | docs/BA/qc-responses-2026-07-14.md |
| Prior audit | UC-EXBOT-user-redeem_user-redeem_audited_20260707_v4.md (Conditionally Ready, 80/100) |

---

## §1 Summary of Changes (2026-07-14 Updates)

### A. UC file changes (2026-07-14)

| Location | Before | After | Impact |
|---|---|---|---|
| §2 Preconditions | "Bot status='active' (or paused/safe_mode — user may redeem from any non-closed state)" | Liệt kê đủ 6 `lifecycle_state` được phép: `active`, `paused`, `hedge_stopped_cooldown`, `lp_rebalancing`, `safe_mode`, `error` | **I-N1 resolved** — preconditions rõ ràng, có thể test |
| §3 step 8 (cũ) | Không có bước chuyển sang `hedge_close_pending` | Thêm step 9 mới: "Worker cập nhật `close_operations.state` → `hedge_close_pending` sau khi acquire lock, trước khi gọi `closeShortReduceOnlyIoc`" | **I-N3 resolved** — state transition đầy đủ trong flow |
| §3 steps 9–14 (cũ) | Steps 9–14 | Đánh số lại thành steps 10–16 (do step 9 mới được thêm) | Không thay đổi logic |
| §3 step 9 (mới, retry) | "retries up to 3 times on reject/timeout" | "3 lần retry xảy ra trong cùng Lambda invocation, bên trong Redlock-acquired block (TTL=90s); không có SQS re-queue theo từng lần retry" | **I-N2 resolved** — retry strategy rõ ràng |
| §7 FR Trace | FR-EXBOT-070, FR-EXBOT-071 (không tồn tại) | FR-EXBOT-070 only (FR-071 đã xóa — thuộc uc-bot-safe-close) | Đã fix từ v2; xác nhận nhất quán |

### B. SRS/FRD document updates (2026-07-14)

| Document | Change | Impact on user-redeem |
|---|---|---|
| frd.md | FR renumbering: FR-091 (User Lock) → FR-092; FR-092 (Pool Slot0 Cache) → FR-093 | **I-N4 resolved** — spec.md và frd.md giờ đồng bộ: FR-EXBOT-092 = User Lock |
| spec.md | FR renumbering aligned; thêm FR-EXBOT-091 (Rate Limiter) trước FR-092 | Xác nhận FR-EXBOT-092 = User Lock (Redlock), TTL=90s |
| flows.md F-04 | Thêm `User Lock (Redis Redlock)` participant; sửa notation `close_operations` thành `requested → lp_closed → funds_returned`; thêm `hedge_close_pending` transition sau lock acquire; ghi chú SLA breach khi re-queue | **I-03 resolved** — F-04 đầy đủ, tester có thể trace lock contention scenario |
| states.md | Thêm cột `user_redeem` vào State Registry với 6 states được phép và on-chain rationale | **I-N1 resolved (supporting evidence)** — verified vs RedeemStrategyV1.sol và BnzaExVaultImpl.sol |

### C. BA/Tech Lead responses (qc-responses-2026-07-14.md)

| Question | Trả lời | Impact |
|---|---|---|
| I-02bc (High — sub-questions b và c) | **(b)** Người thực hiện on-chain USDC transfer HL-portion là **Worker và Operator address** — không qua facade trung gian riêng. **(c)** Transaction hash **không** được lưu vào `close_operations.hedge_close_tx` | I-02bc **closed** — mechanism rõ ràng. Sub-question **(a)** (công thức tính HL-portion amount) → I-02a, vẫn **Open** |
| I-03 (Medium) | F-04 đã cập nhật: thêm Redlock participant; lock acquire sau tạo `close_operations` row (idempotency first); `acquired=false` → re-queue with delay; SLA tiếp tục chạy; lock release sau reconcile size=0 hoặc trước `residual_hl_liability` | I-03 **closed** |
| I-N1 (Medium) | Cả 3 states bổ sung đều Allowed: `hedge_stopped_cooldown` (LP NFT vẫn trong vault, contract không check lifecycle_state), `lp_rebalancing` (RedeemStrategyV1 chỉ validate tokenId ownership; `redeem(oldTokenId)` revert an toàn), `error` (LP NFT vẫn trong vault). UC preconditions đã cập nhật. | I-N1 **closed** |
| I-N2 (Low) | In-invocation — 3 retries trong cùng Lambda invocation, bên trong Redlock-acquired block. Không có SQS re-queue per retry. Backoff là implementation detail không được BA specify. | I-N2 **closed** |
| I-N3 (Medium) | `hedge_close_pending` thêm vào UC step 9 (sau lock acquire, trước `closeShortReduceOnlyIoc`). Full transition: `funds_returned → hedge_close_pending → hedge_closed`. Recovery checkpoint: nếu Lambda crash sau lock acquire, recovery worker xác định hedge close đang in-progress. | I-N3 **closed** |
| I-N4 (Low) | Lỗi đánh số được xác nhận và đã sửa: frd.md FR-EXBOT-091 (User Lock) → FR-EXBOT-092; FR-EXBOT-092 (Pool Slot0 Cache) → FR-EXBOT-093. Không có content conflict — chỉ là số FR. | I-N4 **closed** |

---

## §2 Cross-Check: UC vs SRS (v5 delta)

### 2.1 Issues resolved in this audit pass

| ID | Resolution |
|---|---|
| I-02bc | BA + Tech Lead xác nhận: (b) Worker + Operator address thực hiện USDC transfer; (c) tx hash không lưu vào `close_operations.hedge_close_tx`. **Closed.** |
| I-03 | F-04 đã cập nhật đầy đủ với Redlock participant, lock ordering (idempotency first), SLA breach note. **Closed.** |
| I-N1 | BA xác nhận cả 6 `lifecycle_state` được phép; UC preconditions cập nhật; states.md cập nhật với on-chain rationale. **Closed.** |
| I-N2 | BA xác nhận retry là in-invocation (3 retries trong Redlock block); không có SQS re-queue per retry. UC step 9 cập nhật. **Closed.** |
| I-N3 | `hedge_close_pending` thêm vào UC step 9. Full transition: `funds_returned → hedge_close_pending → hedge_closed`. **Closed.** |
| I-N4 | frd.md renumbered: FR-092 = User Lock, FR-093 = Pool Slot0. spec.md và frd.md đồng bộ. **Closed.** |

### 2.2 Remaining open issue

| Issue ID | Type | Severity | Affected area | Source trace | Finding | Impact on tester | Suggested fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-02a | MISSING_INFO | High | Area 2, Area 3 | uc-user-redeem.md §3 step 13 (sau renumber); flows.md F-04; spec.md | **Công thức tính HL-portion amount chưa được định nghĩa.** UC step 13 mô tả "send HL-portion USDC to user via RedemptionQueue ledger" nhưng không xác định: (a) HL-portion được tính như thế nào — là toàn bộ số tiền từ đóng vị thế HL, hay trừ funding fee, trading fee, hay một phần khác? Không có công thức hay mô tả source of truth trong bất kỳ tài liệu nào (UC, FRD, SRS, common rules). | Tester không thể xác minh số tiền nhà đầu tư nhận đúng trong expected result của step 13. Không thể viết test case boundary/negative cho HL-portion amount. **Chặn hoàn toàn** test case cho happy path step 13 và A2 residual amount. | BA/Tech Lead xác định công thức: HL-portion = (closing USDC received from HL) − (trading fee) − (funding fee accrued), hay công thức khác. Cần có source of truth trong spec.md hoặc UC. | Open — ⏳ Pending BA/team confirm |

### 2.3 Cross-check: §F.1–§F.5 vs SRS updates 2026-07-14

Các phần §F.1–§F.5 từ v3 (đã được v4 kế thừa) vẫn còn hiệu lực. Nội dung bổ sung/cập nhật dưới đây phản ánh SRS delta 2026-07-14:

**Preconditions mở rộng (§F.2, §F.3):** UC §2 giờ liệt kê đủ 6 `lifecycle_state` được phép cho user_redeem: `active`, `paused`, `hedge_stopped_cooldown`, `lp_rebalancing`, `safe_mode`, `error`. On-chain contract `RedeemStrategyV1` chỉ validate tokenId ownership — không có `lifecycle_state` gate. `BnzaExVaultImpl` không kiểm tra `lifecycle_state` khi xử lý redeem. Tester có thể thiết kế test case cho cả 6 trạng thái này.

**close_operations full state machine (§F.2):** Transition đầy đủ sau v5: `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done`. Nhánh lỗi: `funds_returned → hedge_close_pending → residual_hl_liability` (khi hedge close fails sau 3 retries hoặc reconcile mismatch).

**Lock ordering (§F.3):** Idempotency first — `close_operations` row được tạo tại `requested` TRƯỚC khi acquire User Lock. Lock được acquire SAU row creation. `acquired=false` → re-queue với delay; SLA clock tiếp tục chạy; tổng delay > 5 phút trigger A1 SLA breach alert (E-EXBOT-010).

**Retry strategy (§F.3):** 3 retries xảy ra trong cùng Lambda invocation, bên trong Redlock-acquired block (TTL=90s). Không có SQS re-queue per retry. Sau 3 lần thất bại: `close_operations.state = residual_hl_liability`, `bots.lifecycle_state = error`, admin nhận E-EXBOT-024.

**SAFE_MODE không áp dụng trong A2 (§F.3):** Khi LP đã được thanh lý on-chain và hedge close thất bại, SAFE_MODE không được kích hoạt — không còn LP để bảo vệ. Trực tiếp chuyển sang `residual_hl_liability` + `error` state.

---

## §F.1 — Inventory (Functions, Operations, Data Objects, Messages)

*(Kế thừa từ v3; cập nhật delta v5)*

| # | Loại | Tên / ID | Trigger | Input | Output / Effect | Source |
|---|---|---|---|---|---|---|
| F1-01 | On-chain operation | `BnzaExVault.redeem(tokenId)` | Nhà đầu tư gọi trực tiếp on-chain | `tokenId` (LP NFT) | LP liquidated; LP-portion USDC trả về investor trong cùng tx; emit `RedemptionEvent` | uc-user-redeem §3 step 1–2; FR-EXBOT-070 |
| F1-02 | Event watcher | Redeem Event Watcher (Fargate/Lambda) | `RedemptionEvent` on-chain emit | `botId`, `redeemTxHash`, `userAddress` | Enqueue `user_redeem` message vào SQS FIFO queue (độ ưu tiên cao nhất) | flows.md F-04 |
| F1-03 | Queue processing | Redeem Worker (AWS Lambda) | SQS FIFO delivery (SLA: 5 min) | `{botId, redeemTxHash, userAddress}` | Thực hiện toàn bộ luồng hedge close | uc-user-redeem §3; flows.md F-04 |
| F1-04 | DB write (idempotency) | INSERT `close_operations` | Trước lock acquire | `kind=user_redeem`, `state=requested` | Row được tạo; idempotency đảm bảo không duplicate nếu SQS redelivery | uc-user-redeem §3 step 3; flows.md F-04 |
| F1-05 | DB write | UPDATE `close_operations.state` | Sau F1-04 | — | `state: requested → lp_closed → funds_returned` (trước lock) | flows.md F-04 |
| F1-06 | Distributed lock acquire | `User Lock (Redis Redlock)` acquire | Sau F1-05 | `holderToken`, `ttl=90s`, `idempotencyKey=user-redeem:{botId}:{redeemTxHash}` | `acquired=true` hoặc `acquired=false`; nếu false → re-queue | FR-EXBOT-092; flows.md F-04 |
| F1-07 | DB write | UPDATE `close_operations.state = hedge_close_pending` | Sau lock acquired (step 9 mới) | — | Recovery checkpoint; nếu Lambda crash sau lock acquire, recovery worker biết hedge close đang in-progress | uc-user-redeem §3 step 9 (v5); flows.md F-04; qc-responses-2026-07-14.md I-N3 |
| F1-08 | HL operation | `closeShortReduceOnlyIoc` (full close, target=0) | Trong Redlock block | `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | HL position đóng (toàn bộ); retry up to 3 lần trong invocation | uc-user-redeem §3 step 10 (v5, sau renumber); FR-EXBOT-022 |
| F1-09 | HL operation | `cancelStop` via §19.5 replaceStopProtected (size=0) | Trong Redlock block, sau F1-08 | `size=0` | Stop order bị hủy trên HL | uc-user-redeem §3 step 11 (v5) |
| F1-10 | HL operation | `reconcilePosition` | Trong Redlock block, sau F1-09 | — | Verify HL position size = 0 | uc-user-redeem §3 step 12 (v5) |
| F1-11 | DB write | UPDATE `close_operations.state = hedge_closed` | Sau reconcile confirms size=0 | — | Xác nhận hedge đã đóng | flows.md F-04 |
| F1-12 | Distributed lock release | `User Lock` release | Sau F1-11 hoặc khi hedge close fails | — | Lock released | FR-EXBOT-092 |
| F1-13 | Off-chain payment | Send HL-portion USDC to investor | Sau lock release, hedge_closed | Worker + Operator address thực hiện | HL-portion USDC gửi qua RedemptionQueue ledger; tx hash KHÔNG lưu vào `close_operations.hedge_close_tx` | uc-user-redeem §3 step 13–14 (v5); qc-responses-2026-07-14.md I-02bc |
| F1-14 | DB write | UPDATE `close_operations.state = done`, `bots.lifecycle_state = closed` | Sau F1-13 | — | Bot đóng hoàn toàn | uc-user-redeem §5 |
| F1-15 | Exception path | hedge close fails → `residual_hl_liability` | Sau 3 retries thất bại hoặc reconcile mismatch | — | `close_operations.state = residual_hl_liability`; `bots.lifecycle_state = error`; admin notified (E-EXBOT-024); LP-portion NOT reversed | uc-user-redeem §4 A2; BR-EXBOT-006 |
| F1-16 | SLA breach alert | A1: hedge close exceeds 5 min SLA | Khi `requeue_delay > 5 min total` | — | Admin + Investor nhận E-EXBOT-010; LP-portion funds already returned | uc-user-redeem §4 A1; NFR-EXBOT-003 |
| MSG-01 | Admin message | E-EXBOT-024 | A2/reconcile failure | `residual_amount` | "User redemption hedge close failed. Manual intervention required." | message-list.md |
| MSG-02 | Admin+Investor message | E-EXBOT-010 | A1 SLA breach | — | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | message-list.md |
| BR-01 | Business rule | BR-EXBOT-006 | Luôn áp dụng | — | LP-portion repayment vô điều kiện — không bao giờ bị đảo ngược hoặc block bởi hedge close failure | srs/spec.md BR-EXBOT-006 |
| BR-02 | Business rule | BR-EXBOT-007 | Khi LP đã liquidated | — | SAFE_MODE không áp dụng trong A2 user_redeem — LP đã thanh lý, không còn gì để bảo vệ | srs/spec.md BR-EXBOT-007; qc-responses-2026-07-14.md I-08 |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations

*(Kế thừa từ v3; cập nhật delta v5)*

### close_operations

| Field | Type | Valid values / Constraints | Business rule | Source |
|---|---|---|---|---|
| `id` | TEXT PK | UUID | — | erd.md |
| `kind` | TEXT | `user_redeem`, `bot_safe_close` | — | erd.md; states.md |
| `state` | TEXT | `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done`; nhánh lỗi: `→ residual_hl_liability` | Transition forward-only; không rollback lp_closed sau khi on-chain confirmed | states.md close_operations; flows.md F-04 |
| `residual_amount` | TEXT | Nullable; set khi `state = residual_hl_liability` | Lưu outstanding HL liability amount | erd.md; I-05-B |
| `hedge_close_tx` | TEXT | **KHÔNG** lưu tx hash của HL-portion transfer | Tech Lead confirmed (I-02bc) | qc-responses-2026-07-14.md |

### bots.lifecycle_state (user_redeem relevant)

| lifecycle_state | bots.status | user_redeem allowed | On-chain rationale |
|---|---|---|---|
| `active` | active | ✓ | — |
| `paused` | paused | ✓ | — |
| `hedge_stopped_cooldown` | active | ✓ | LP NFT vẫn trong BnzaExVault; contract không check lifecycle_state |
| `lp_rebalancing` | active | ✓ | `RedeemStrategyV1` chỉ validate tokenId ownership; `redeem(oldTokenId)` revert an toàn mid-rebalance |
| `safe_mode` | safe_mode | ✓ | LP NFT vẫn trong vault |
| `error` | error | ✓ | LP NFT vẫn trong vault; user có quyền redeem |
| `lp_closing` | closing | ✗ — Already closing | — |
| `closed` | closed | ✗ — Already closed | — |

### User Lock (Redis Redlock)

| Attribute | Value | Source |
|---|---|---|
| TTL | 90s | FR-EXBOT-092 |
| `idempotencyKey` pattern | `user-redeem:{botId}:{redeemTxHash}` | FR-EXBOT-092; flows.md F-04 |
| Lock ordering | Sau INSERT `close_operations` (idempotency first); trước mọi HL operation | qc-responses-2026-07-14.md I-03 |
| `acquired=false` behavior | Re-queue với delay; SLA clock tiếp tục; > 5 min tổng → A1 SLA breach | flows.md F-04 |
| Release | Sau reconcile confirms size=0, hoặc trước `residual_hl_liability` khi fails | qc-responses-2026-07-14.md I-03 |

### Business Rules summary

| BR | Nội dung | Applies to | Source |
|---|---|---|---|
| BR-EXBOT-006 | LP-portion repayment vô điều kiện — không bao giờ bị block hoặc đảo ngược | user_redeem luôn | srs/spec.md |
| BR-EXBOT-007 | SAFE_MODE không áp dụng khi LP đã liquidated (A2 path) | user_redeem A2 | srs/spec.md |
| NFR-EXBOT-003 | hedge close SLA: ≤ 5 phút từ event detection | user_redeem | srs/spec.md |

---

## §F.3 — Functional Logic & Workflow Decomposition

### Happy Path (F-04 main flow)

| Bước | Actor | Hành động | System response | Source |
|---|---|---|---|---|
| 1 | Investor | Gọi `BnzaExVault.redeem(tokenId)` on-chain | LP liquidated; LP-portion USDC trả về cùng tx; emit `RedemptionEvent` | uc §3 step 1–2 |
| 2 | Event Watcher | Detect `RedemptionEvent` | Enqueue `{botId, redeemTxHash, userAddress}` vào user_redeem SQS FIFO queue | flows.md F-04 |
| 3 | Redeem Worker | Deliver message (SLA: 5 min từ detection) | INSERT `close_operations` (state=requested) — idempotency checkpoint | uc §3 step 3; F-04 |
| 4 | Redeem Worker | UPDATE `close_operations` | state: requested → lp_closed → funds_returned | flows.md F-04 |
| 5 | Redeem Worker | Acquire User Lock | `idempotencyKey=user-redeem:{botId}:{redeemTxHash}`, TTL=90s | FR-EXBOT-092; F-04 |
| 6 | Redeem Worker | UPDATE `close_operations.state = hedge_close_pending` | Recovery checkpoint được đặt trước bất kỳ HL call nào | uc §3 step 9 (v5); F-04 |
| 7 | Redeem Worker | Gọi `closeShortReduceOnlyIoc` (full close, target=0) | HL position đóng; cloid per FR-EXBOT-022; retry up to 3 lần in-invocation | uc §3 step 10 (v5); FR-EXBOT-022 |
| 8 | Redeem Worker | Gọi `cancelStop` via §19.5 | Stop order hủy trên HL | uc §3 step 11 (v5) |
| 9 | Redeem Worker | `reconcilePosition` — verify size=0 | Xác nhận HL position = 0 | uc §3 step 12 (v5) |
| 10 | Redeem Worker | UPDATE `close_operations.state = hedge_closed`; release lock | Lock được giải phóng sau xác nhận | flows.md F-04 |
| 11 | Worker + Operator | Send HL-portion USDC to investor via RedemptionQueue ledger | HL-portion gửi; tx hash KHÔNG lưu vào close_operations | uc §3 step 13–14 (v5); I-02bc |
| 12 | Redeem Worker | UPDATE `close_operations.state = done`, `bots.lifecycle_state = closed` | Bot đóng hoàn toàn | uc §5 |

### Alternative Path A1 — SLA breach (lock contention delay)

| Điều kiện | Hành động | Kết quả |
|---|---|---|
| Lock held by hedge-sync worker → `acquired=false` | Re-queue với delay | SLA clock tiếp tục; tổng delay > 5 min → A1 |
| Tổng thời gian từ detection > 5 min | Admin + Investor notified | E-EXBOT-010 ("Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned.") |
| LP-portion | Không bị ảnh hưởng | BR-EXBOT-006: đã trả, không đảo ngược |

### Alternative Path A2 — hedge close failure

| Điều kiện | Hành động | Kết quả |
|---|---|---|
| `closeShortReduceOnlyIoc` fails 3 lần in-invocation, HOẶC reconcile mismatch (size ≠ 0) | Release lock; UPDATE `close_operations.state = residual_hl_liability` | `bots.lifecycle_state = error` |
| Admin notification | E-EXBOT-024 | "User redemption hedge close failed. Manual intervention required." |
| SAFE_MODE | Không áp dụng | LP đã liquidated — không còn gì để bảo vệ |
| LP-portion | Không bị đảo ngược | BR-EXBOT-006 |

### Pre-states cho user_redeem (6 lifecycle_state được phép — v5 update)

Bot có thể ở bất kỳ lifecycle_state nào trong 6 trạng thái sau khi redeem được gọi on-chain:
- `active`, `paused` — trạng thái thông thường
- `hedge_stopped_cooldown` — LP NFT vẫn trong BnzaExVault; contract không block
- `lp_rebalancing` — `redeem(oldTokenId)` revert an toàn mid-rebalance; `redeem(newTokenId)` thành công sau rebalance
- `safe_mode`, `error` — LP NFT vẫn trong vault

---

## §F.4 — Functional Integration & Data Consistency

| Hành động | Downstream effect | Data consistency check | Source |
|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` on-chain | LP liquidated on-chain; LP-portion USDC trả về in-tx; emit `RedemptionEvent` | Off-chain phải detect event và enqueue trong SLA window | flows.md F-04; UC §3 |
| INSERT `close_operations` (idempotency) | Nếu SQS redelivery: duplicate INSERT bị reject bởi idempotency check | `close_operations` row tồn tại → worker bỏ qua message | qc-responses-2026-07-14.md I-03 |
| User Lock acquire (idempotencyKey `user-redeem:{botId}:{redeemTxHash}`) | Ngăn hedge-sync worker can thiệp trong khi user_redeem đang trong critical section | Nếu lock contention → re-queue → SLA clock tiếp tục | FR-EXBOT-092; flows.md F-04 |
| `hedge_close_pending` checkpoint | Nếu Lambda crash sau lock acquire, recovery worker detect in-progress và có thể resume | Không bỏ sót state | uc §3 step 9 (v5) |
| `closeShortReduceOnlyIoc` + `reconcilePosition` | HL position size = 0 confirmed before `close_operations.state = hedge_closed` | Off-chain state chỉ advance sau on-chain/HL confirmation | flows.md F-04 |
| HL-portion USDC send | Worker + Operator address thực hiện; ledger updated | tx hash không lưu trong DB — không có audit trail on-chain | qc-responses-2026-07-14.md I-02bc |
| A2: `residual_hl_liability` | `bots.lifecycle_state = error`; admin nhận E-EXBOT-024 | LP-portion đã trả (BR-EXBOT-006); HL residual cần xử lý manual | uc §4 A2; spec.md |
| `bots.lifecycle_state = closed` | Bot không còn trong queue scan; hedge-sync suppressed | states.md: `closed` → skip mọi operations | states.md; uc §5 |

---

## §F.5 — Acceptance Criteria Candidates

*(Kế thừa từ v3; cập nhật delta v5)*

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-001 | Happy path — LP-first, hedge close thành công | Bot ở `lifecycle_state IN (active, paused, hedge_stopped_cooldown, lp_rebalancing, safe_mode, error)`, LP NFT trong vault | Investor gọi `redeem(tokenId)` on-chain | LP liquidated; LP-portion USDC trả về trong cùng tx; `close_operations` đi qua đủ: requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done; `bots.lifecycle_state = closed`; HL-portion USDC gửi cho investor | uc §3 main flow; US-EXBOT-004 AC-004-1 |
| AC-002 | SLA breach — lock contention | Lock held bởi hedge-sync worker khi user_redeem cố acquire | Tổng delay > 5 phút từ event detection | Admin + Investor nhận E-EXBOT-010; LP-portion không bị đảo ngược (BR-EXBOT-006) | uc §4 A1; NFR-EXBOT-003 |
| AC-003 | hedge close failure — residual HL liability | HL API từ chối `closeShortReduceOnlyIoc` 3 lần liên tiếp in-invocation | Sau 3 retries thất bại | `close_operations.state = residual_hl_liability`; `bots.lifecycle_state = error`; admin nhận E-EXBOT-024; LP-portion không bị đảo ngược | uc §4 A2; BR-EXBOT-006; US-EXBOT-004 AC-004-3 |
| AC-004 | Idempotency — SQS redelivery | SQS redelivers message sau khi `close_operations` đã được INSERT | Redeem Worker xử lý message lần 2 | Worker phát hiện idempotency row và bỏ qua; không tạo duplicate close; final state không thay đổi | flows.md F-04; FR-EXBOT-070 |
| AC-005 | Precondition: `lp_rebalancing` | Bot ở `lp_rebalancing`, đang rebalance với `oldTokenId` | Investor gọi `redeem(oldTokenId)` on-chain | Tx revert an toàn (LP NFT đã burn); investor gọi `redeem(newTokenId)` sau rebalance thành công | qc-responses-2026-07-14.md I-N1 |
| AC-006 | Lock ordering: idempotency before lock | Normal redemption flow | Worker tạo `close_operations` row TRƯỚC khi acquire User Lock | `close_operations` row tồn tại kể cả khi lock acquire fails; không có orphan lock | qc-responses-2026-07-14.md I-03 |
| AC-007 | hedge_close_pending recovery checkpoint | Lambda crash sau khi acquire lock nhưng trước khi `closeShortReduceOnlyIoc` gọi | Recovery worker chạy sau crash | `close_operations.state = hedge_close_pending` → recovery worker biết hedge close đang in-progress và có thể resume; không bỏ qua hedge close | uc §3 step 9 (v5); I-N3 |
| AC-008 | HL-portion transfer: tx hash không lưu | Hedge close thành công; HL-portion USDC gửi cho investor | Worker hoàn tất transfer | `close_operations.hedge_close_tx` KHÔNG được cập nhật với tx hash; HL-portion transfer hoàn tất | qc-responses-2026-07-14.md I-02bc |
| AC-009 | HL-portion amount formula | Hedge close thành công | Worker tính HL-portion amount | **⚠️ Suy luận cần xác nhận** — Công thức tính chưa được định nghĩa (I-02a Open). Không thể viết expected result cụ thể. | I-02a — Open |

---

## §10.1 Issue Register

| ID | Type | Severity | Area | Source trace | Finding | Impact on tester | Suggested fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-02a | MISSING_INFO | High | Area 2, 3 | uc §3 step 13–14 (v5); flows.md F-04 | Công thức tính HL-portion amount chưa được định nghĩa trong bất kỳ tài liệu nào. UC mô tả "send HL-portion USDC" nhưng không có công thức hay nguồn tham chiếu cho cách tính số tiền. | Tester không thể viết expected result cho step 13 happy path và A2 residual amount. **Chặn hoàn toàn** test case boundary/negative cho HL-portion. | BA/Tech Lead định nghĩa công thức: (closing USDC from HL) − fees, hay toàn bộ? Cần thêm vào spec.md hoặc UC. | Open — ⏳ Pending BA/team confirm |
| I-02bc | MISSING_INFO | High (resolved) | Area 2, 3 | uc §3 step 13; flows.md F-04 | (b) Ai thực hiện on-chain USDC transfer; (c) tx hash có lưu không. | — | — | Answered 2026-07-14 (Tech Lead): (b) Worker + Operator; (c) KHÔNG lưu tx hash |
| I-03 | UNCLEAR_INFO | Medium (resolved) | Area 4 | flows.md F-04; FR-EXBOT-092 | F-04 thiếu Redlock participant; lock ordering không rõ. | — | — | Answered 2026-07-14 (BA): F-04 updated với Redlock; idempotency first |
| I-N1 | MISSING_INFO | Medium (resolved) | Area 2, 3 | uc §2 Preconditions; states.md | 6 lifecycle_state được phép chưa liệt kê đủ trong UC. | — | — | Answered 2026-07-14 (BA): UC và states.md cập nhật; tất cả 6 states confirmed |
| I-N2 | UNCLEAR_INFO | Low (resolved) | Area 3 | uc step 9 (v5) | Retry strategy (in-invocation vs re-queue) chưa rõ. | — | — | Answered 2026-07-14 (BA): in-invocation, trong Redlock block |
| I-N3 | MISSING_INFO | Medium (resolved) | Area 2, 3 | uc main flow; states.md | `hedge_close_pending` vắng mặt trong UC main flow. | — | — | Answered 2026-07-14 (BA): step 9 thêm vào UC; full transition documented |
| I-N4 | CROSS_SOURCE_CONFLICT | Low (resolved) | Area 5 | spec.md FR-092; frd.md FR-091 | FR numbering mismatch cho Redlock giữa spec.md và frd.md. | — | — | Answered 2026-07-14 (BA): frd.md renumbered; now spec.md = frd.md = FR-092 |

---

## §10.2 Dependency

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| I-02a: Công thức HL-portion amount | MISSING_INFO | Chặn test case happy path step 13 và A2 residual amount | BA / Tech Lead | Open |
| US-EXBOT-004 AC-004-1/2/3 | UC | Linked story đã đọc; AC confirmed nhất quán với UC v5 | BA | Resolved |
| NFR-EXBOT-003: SLA 5 min | NFR | Test case cho A1 phải verify SLA boundary | BA | Resolved — định nghĩa rõ trong spec.md |

---

## §10.3 Audit Summary

### Scoring Table

| Area | Max | v1 Score | v2 Score | v3 Score | v4 Score | v5 Score | Delta v4→v5 | Notes |
|---|---|---|---|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 14 | 16 | 18 | 18 | **19** | +1 | I-N3 closed: F1-07 (`hedge_close_pending` checkpoint) và F1-07 lock ordering đã có đủ trace. I-02a vẫn open nhưng là sub-question nhỏ — HL-portion transfer mechanism đã xác nhận (I-02bc). Inventory gần đầy đủ; chỉ còn HL-portion formula chưa rõ. |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 12 | 16 | 16 | 16 | **20** | +4 | I-N1 closed (+1 preconditions), I-N2 closed (+1 retry strategy), I-N3 closed (+1 hedge_close_pending state), I-N4 closed (+0.5 FR consistency), I-02bc closed (+1.5 lock mechanism rõ). I-02a (High) vẫn open: trừ 2 điểm vì không biết formula HL-portion → Area 2 max bị giới hạn. Cap: blocker chỉ áp dụng cho một sub-formula, không chặn toàn bộ area. |
| 3. Functional Logic & Workflow Decomposition | 25 | 14 | 16 | 16 | 16 | **20** | +4 | I-N1 closed (+1 pre-states), I-N3 closed (+2 full state transition), I-03 closed (+1 F-04 complete). I-02a (High) trừ 2 điểm: expected result step 13 vẫn không thể verify. Cap: blocker tập trung ở một bước (step 13), không chặn main flow test. |
| 4. Functional Integration & Data Consistency | 15 | 12 | 13 | 13 | 13 | **14** | +1 | I-03 fully closed: F-04 có Redlock participant, lock ordering, SLA breach note, `hedge_close_pending` checkpoint đầy đủ. I-02bc closed: HL-portion mechanism rõ. Trừ 1 điểm: tx hash không lưu — không có audit trail on-chain cho HL-portion transfer (thiếu traceability). |
| 5. UC / Spec Documentation Quality Issues | 15 | 14 | 16 | 17 | 17 | **14** | -3 | I-N4 closed (+0). Tuy nhiên, UC §7 FR Trace vẫn chỉ cite FR-EXBOT-070 — trong khi FR-EXBOT-092 (User Lock) được dùng trực tiếp trong main flow (lock acquire/release/TTL), FR-EXBOT-022 (cloid) áp dụng cho `closeShortReduceOnlyIoc`, và FR-EXBOT-070 mô tả "Two close systems" ở mức tổng quan. FR Trace thiếu FR-092 và FR-022 là documentation gap Minor (tester phải lookup spec.md để tìm Redlock và cloid behavior). Trừ 3 điểm so với v4 vì v5 đã close I-N4 nhưng phát hiện FR Trace vẫn thiếu 2 FRs quan trọng cho luồng user_redeem. |
| **Total** | **100** | **66** | **77** | **80** | **80** | **87** | **+7** | |

**Score: 87/100 — Conditionally Ready** (score tăng +7 từ v4; verdict cải thiện đáng kể nhờ BA responses đóng 6 issues; I-02a High còn open nhưng chỉ block test case cho step 13)

### Verdict: CONDITIONALLY READY (87/100)

**Cải thiện trong v5:**
- I-02bc (High) closed: HL-portion transfer mechanism rõ ràng — Worker + Operator address thực hiện; tx hash không lưu.
- I-03 (Medium) closed: F-04 đầy đủ với Redlock participant; idempotency-first ordering; SLA breach note.
- I-N1 (Medium) closed: 6 lifecycle_state được phép liệt kê đủ; verified vs on-chain contracts.
- I-N2 (Low) closed: retry strategy xác nhận in-invocation (3 retries trong Redlock block).
- I-N3 (Medium) closed: `hedge_close_pending` thêm vào UC step 9; full state transition `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done`.
- I-N4 (Low) closed: frd.md renumbered để đồng bộ với spec.md (FR-092 = User Lock).

**Remaining blocker:**
- **I-02a (High):** Công thức tính HL-portion amount chưa được định nghĩa. Chặn test case cho UC step 13 (happy path) và A2 residual amount. Tester không thể xác minh expected result cho phần HL-portion.

**New minor documentation gap (phát hiện trong v5):**
- **FR Trace §7:** UC §7 chỉ cite FR-EXBOT-070. Tuy nhiên, luồng user_redeem trực tiếp sử dụng: FR-EXBOT-092 (User Lock — acquire/extend/release, TTL=90s, idempotencyKey pattern) và FR-EXBOT-022 (cloid cho `closeShortReduceOnlyIoc`). Minor — behavior được mô tả trong UC prose; tester phải tự lookup spec.md.

**Recommendation:**
87/100 — Tiến hành thiết kế test scenario và test case cho tất cả luồng đã xác nhận (happy path steps 1–12 + 14–16, A1 SLA breach, A2 hedge failure, idempotency, lock contention, pre-state variants, `hedge_close_pending` recovery). Giữ test case cho step 13 (HL-portion amount verification) đến khi I-02a được BA/Tech Lead giải quyết. BA nên bổ sung FR-EXBOT-092 và FR-EXBOT-022 vào UC §7 FR Trace.

---

## §11 Change Log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-28 | QC UC Read ExBot Agent | Initial audit; score 66/100 |
| v2 | 2026-07-03 | QC UC Read ExBot Agent | Re-audit sau BA Q&A (qc-responses-2026-07-03.md): các issue I-01/I-04/I-05/I-06/I-08/I-09/I-10/I-11 closed; score 77/100 |
| v3 | 2026-07-04 | QC UC Read ExBot Agent | Re-audit sau BA arc-migration update (2026-07-04): UserLockDO → Redis Redlock terminology sync; I-03 partially resolved; I-N1/I-N2/I-N3 new issues; score 80/100 |
| v4 | 2026-07-07 | QC UC Read ExBot Agent | Re-audit sau commit 2026-07-06 (c9a4682): xác nhận thay đổi commit là terminology-only; phát hiện I-N4 (Low — FR numbering mismatch); score không đổi 80/100 |
| v5 | 2026-07-15 | QC UC Read ExBot Agent | Re-audit sau BA updates 2026-07-14 + BA responses (qc-responses-2026-07-14.md): I-02bc/I-03/I-N1/I-N2/I-N3/I-N4 closed; step 9 hedge_close_pending thêm vào UC; 6 lifecycle_state confirmed; retry in-invocation; F-04 hoàn chỉnh; I-02a vẫn Open; score tăng 80→87/100 |

---

*Report generated by: QC UC Read ExBot Agent | Device: MTS-978 | Run ID: run-20260715-000004-trinhbui*
